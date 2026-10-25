"""End-to-end persisted project -> actual compilers/scanners -> local report."""
import json
import os
import tempfile
import time
import unittest
from dataclasses import replace
from pathlib import Path

from checker.engines import EngineConfig
from checker.inventory import digest
from checker.jobs import CheckJobs
from checker.model import ContractError, Registration, Selection
from checker.policies import PolicyPack, PolicyStore
from checker.policy_service import PolicyService
from checker.processes import RunControl
from checker.registry import RegistrySession, RegistryStore
from checker.settings import DevelopmentSettings
from checker.ui_model import ReviewPresenter
from checker.gui import DesktopApp


class FakeWidget:
    def __init__(self):
        self.value = ""
    def set(self, value):
        self.value = value
    def configure(self, **_kwargs):
        pass
    def after(self, *_args):
        pass


def present_event(jobs, event, presenter):
    app = DesktopApp.__new__(DesktopApp)
    app.jobs = jobs
    app.presenter = presenter
    app.active_ticket = event.job_id
    app.active_check_project = event.project_id
    app.policy_editor = None
    app.registry_error = ""
    app.selected = event.project_id
    app.status = FakeWidget()
    app.root = FakeWidget()
    app.check_button = FakeWidget()
    app.cancel_button = FakeWidget()
    app.policy_buttons = []
    app.pack_choice = FakeWidget()
    app.refresh = lambda: None
    jobs.events.put(event)
    app._poll_jobs()
    return app


RULES = """rules:
  - id: js-no-eval
    languages: [javascript]
    severity: ERROR
    message: eval prohibited in fixture
    pattern: eval(...)
  - id: py-no-eval
    languages: [python]
    severity: ERROR
    message: eval prohibited in fixture
    pattern: eval(...)
"""


@unittest.skipUnless(os.environ.get("UPDATER_DEV_ESLINT") and os.environ.get("UPDATER_DEV_SEMGREP"),
                     "Both real Docker engines required")
class CheckWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="checker-job-tests-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        self.js = self.source / "пример.js"
        self.py = self.source / "пример.py"
        self.js.write_text("const answer = 42;\n", encoding="utf-8")
        self.py.write_text("answer = 42\n", encoding="utf-8")
        tools = []
        for kind in ("eslint", "semgrep"):
            cli = Path(os.environ[f"UPDATER_DEV_{kind.upper()}"])
            cfg = Path(os.environ[f"UPDATER_DEV_{kind.upper()}_CONFIG"])
            tools.append(EngineConfig(kind, cli, digest(cli.read_bytes()), cfg,
                digest(cfg.read_bytes()), Path("/usr/local/bin/node") if kind == "eslint" else None))
        self.settings = DevelopmentSettings(self.root / "state", self.root / "policies",
            (self.source,), tuple(tools), {".js": ("eslint", "semgrep"), ".py": ("semgrep",)}, 60)
        self.store = PolicyStore(self.settings.policy_root)
        self.pack = PolicyPack("shared", "Общие", {"no-eval": "error"}, RULES)
        self.store.create(self.pack)
        self.project = Registration("one", "Проект", (Selection("file", str(self.js)),
            Selection("file", str(self.py))), ("shared",))
        self.jobs = CheckJobs(self.settings)
        self.addCleanup(self.cleanup_job)

    def cleanup_job(self):
        self.jobs.cancel()
        if self.jobs.thread:
            self.jobs.thread.join(6)

    def wait(self, on_event=lambda _event: None):
        deadline = time.monotonic() + 70
        seen = []
        while time.monotonic() < deadline:
            for event in self.jobs.drain():
                seen.append(event.phase)
                on_event(event)
                if event.terminal:
                    self.jobs.thread.join(2)
                    return event, seen
            time.sleep(0.02)
        self.fail("Job did not terminate")

    def test_persist_restart_actual_check_report_and_unchanged_target(self):
        presenter = ReviewPresenter()
        session = RegistrySession(presenter, RegistryStore(self.root / "projects.json"))
        target = self.root / "approved"
        target.mkdir()
        (target / "keep.txt").write_text("external data")
        project = replace(self.project, target_root=str(target), selections=(
            Selection("file", str(self.js), "script.js"), Selection("file", str(self.py), "script.py")))
        session.put(project)
        restored = ReviewPresenter()
        RegistrySession(restored, RegistryStore(self.root / "projects.json"))
        self.jobs.start(restored.registrations["one"])
        with self.assertRaises(ContractError):
            self.jobs.start(project)
        event, phases = self.wait()
        self.assertEqual(event.phase, "COMPLETE_DEVELOPMENT", event.detail)
        result = event.result
        self.assertEqual(result.scan.status, "NOT_AUTHORIZED")
        self.assertTrue({"capture", "snapshot", "policy", "eslint", "semgrep", "freshness"}.issubset(phases))
        app = present_event(self.jobs, event, restored)
        self.assertIn("NOT_AUTHORIZED", app.status.value)
        self.assertEqual(len(restored.coverage_table("one").rows), 2)
        self.assertEqual(len(restored.rules_table("one").rows), 3)
        self.assertFalse(restored.can_apply("one"))
        self.assertEqual(list(target.iterdir()), [target / "keep.txt"])
        self.assertEqual((target / "keep.txt").read_text(), "external data")
        saved = json.loads((result.evidence_dir / "report.json").read_text())
        self.assertEqual(saved["scan"]["status"], "NOT_AUTHORIZED")
        self.assertTrue((result.evidence_dir / "eslint.json").exists())
        self.assertTrue((result.evidence_dir / "semgrep.json").exists())

    def test_real_findings_have_rule_path_and_location(self):
        self.js.write_text('/* eslint-disable */ eval("2+2");\n')
        self.py.write_text('eval("2+2")\n')
        self.jobs.start(self.project)
        event, _ = self.wait()
        self.assertEqual(event.phase, "COMPLETE_DEVELOPMENT", event.detail)
        self.assertEqual(event.result.scan.status, "FINDINGS")
        for report in event.result.scan.reports:
            self.assertGreater(len(report.issues), 0)
            self.assertTrue(all(issue.rule_id and issue.line > 0 and issue.path for issue in report.issues))

    def test_file_coverage_keeps_clean_files_distinct_from_finding_files(self):
        self.py.write_text('eval("2+2")\n')
        self.jobs.start(self.project)
        event, _ = self.wait()
        self.assertEqual(event.phase, "COMPLETE_DEVELOPMENT", event.detail)
        rows = {r.source_path: r.status for r in event.result.coverage.files}
        self.assertEqual(rows[str(self.js)], "NOT_AUTHORIZED")
        self.assertEqual(rows[str(self.py)], "FINDINGS")

    def test_source_edit_during_scan_is_stale_and_snapshot_stays_original(self):
        original = self.js.read_bytes()
        self.jobs.start(self.project)
        def edit(event):
            if event.phase == "eslint":
                self.js.write_text('eval("changed-after-capture");\n')
        event, _ = self.wait(edit)
        self.assertEqual(event.phase, "STALE", event.detail)
        record = next(r for r in event.result.snapshot.records if r.source_path == str(self.js))
        self.assertEqual(record.sha256, digest(original))
        self.assertEqual((event.result.snapshot.root / record.snapshot_relative).read_bytes(), original)

    def test_shared_pack_edit_during_job_does_not_change_captured_rules(self):
        old_hash = self.pack.fingerprint()
        self.jobs.start(self.project)
        def edit(event):
            if event.phase == "eslint":
                self.store.update(replace(self.pack, eslint_core_rules={"no-eval": "warn"}), old_hash)
        event, _ = self.wait(edit)
        self.assertEqual(event.phase, "STALE", event.detail)
        self.assertEqual(event.result.captured.packs[0][1], old_hash)
        self.assertIn('"no-eval": "error"', event.result.effective.configs[0].config.read_text())

    def test_missing_engine_and_unsupported_file_are_visible_nonclear(self):
        self.jobs = CheckJobs(replace(self.settings, tools=(self.settings.tools[0],)))
        self.jobs.start(self.project)
        event, _ = self.wait()
        self.assertEqual(event.phase, "ERROR")
        self.assertIn("Missing required engine", event.detail)
        unknown = self.source / "unknown.bin"
        unknown.write_bytes(b"fixture")
        self.jobs = CheckJobs(self.settings)
        self.jobs.start(replace(self.project, selections=(*self.project.selections, Selection("file", str(unknown)))))
        event, _ = self.wait()
        self.assertEqual(event.result.scan.status, "INCOMPLETE")
        self.assertEqual(next(r for r in event.result.coverage.files if r.source_path == str(unknown)).status, "UNSUPPORTED")

    def test_cancel_during_real_job_and_timeout(self):
        self.jobs.start(self.project)
        event, _ = self.wait(lambda e: self.jobs.cancel() if e.phase == "semgrep" else None)
        self.assertEqual(event.phase, "CANCELLED", event.detail)
        self.assertIsNone(event.result)
        self.jobs = CheckJobs(replace(self.settings, timeout_seconds=0.001))
        self.jobs.start(self.project)
        event, _ = self.wait()
        self.assertEqual(event.phase, "TIMEOUT", event.detail)

    def test_late_result_rejected_after_registration_or_policy_change(self):
        self.jobs.start(self.project)
        event, _ = self.wait()
        self.assertTrue(self.jobs.is_current(event.result, self.project))
        changed = replace(self.project, name="Changed")
        self.assertFalse(self.jobs.is_current(event.result, changed))
        presenter = ReviewPresenter()
        presenter.register(changed)
        app = present_event(self.jobs, event, presenter)
        self.assertIn("STALE", app.status.value)
        self.assertNotIn("one", presenter.scan_reports)
        self.store.update(replace(self.pack, name="Edited shared pack"), self.pack.fingerprint())
        self.assertFalse(self.jobs.is_current(event.result, self.project))

    def test_invalid_direct_edit_keeps_old_pack_and_copy_is_independent(self):
        service = PolicyService(self.settings)
        original = self.store.load("shared").serialize()
        with self.assertRaises(ContractError):
            service.save(replace(self.pack, eslint_core_rules={"not-real-rule": "error"}),
                         self.pack.fingerprint(), (self.project,), RunControl(30))
        self.assertEqual(self.store.load("shared").serialize(), original)
        second = replace(self.project, registration_id="two", name="Second")
        saved = service.save(replace(self.pack, name="Changed for both"), self.pack.fingerprint(),
                             (self.project, second), RunControl(45))
        self.assertEqual(saved.affected_projects, ("one", "two"))
        clone = replace(self.store.load("shared"), pack_id="copy", name="Independent")
        service.save(clone, None, (self.project, second), RunControl(30))
        self.assertEqual(self.store.load("copy").name, "Independent")
        self.assertEqual(self.store.load("shared").name, "Changed for both")

    def test_conflicting_consumer_prevents_shared_save(self):
        self.store.create(PolicyPack("other", "Other", {"no-eval": "error"}))
        project = replace(self.project, policy_pack_ids=("shared", "other"))
        with self.assertRaisesRegex(ContractError, "Conflicting ESLint"):
            PolicyService(self.settings).save(replace(self.pack, eslint_core_rules={"no-eval": "warn"}),
                self.pack.fingerprint(), (project,), RunControl(40))
        self.assertEqual(self.store.load("shared"), self.pack)
