"""Transaction model tests. Receipts here are synthetic; real CLI integration is separate."""
import json
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from checker.coverage import build_coverage_matrix
from checker.engines import EngineConfig
from checker.inventory import digest, make_snapshot
from checker.jobs import CheckResult
from checker.model import ContractError, Registration, Selection
from checker.policies import PolicyPack, PolicyStore
from checker.policy_validation import EffectivePolicy, EnginePolicyValidation
from checker.promotion import PromotionService
from checker.promotion_state import load_json
from checker.reports import EngineReport, summarize
from checker.settings import DevelopmentSettings
from promotion_support import SyntheticTarget


class Interrupted(BaseException):
    pass


class PromotionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="checker-promotion-test-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        self.js = self.source / "пример.js"
        self.js.write_text("const value = 1;\n", encoding="utf-8")
        self.target = self.root / "target"
        self.target.mkdir()
        tools = self.root / "tools/eslint/bin"
        tools.mkdir(parents=True)
        exe, cfg = tools / "eslint.js", self.root / "tools/base.cjs"
        exe.write_text("// SYNTHETIC, never executed\n")
        cfg.write_text('module.exports=[{rules:{"no-eval":"error"}}];\n')
        engine = EngineConfig("eslint", exe, digest(exe.read_bytes()), cfg, digest(cfg.read_bytes()), Path(sys.executable))
        self.settings = DevelopmentSettings(self.root / "state", self.root / "policies", (self.source,),
                                            (engine,), {".js": ("eslint",)}, 30)
        self.policies = PolicyStore(self.settings.policy_root)
        self.pack = PolicyPack("pack", "Synthetic", {"no-eval": "error"})
        self.policies.create(self.pack)
        self.project = Registration("one", "Первый", (Selection("file", str(self.js), "пример.js"),),
                                    ("pack",), str(self.target))
        self.backend = SyntheticTarget(self.root)
        self.service = PromotionService(self.settings, self.backend)

    def check(self, project=None):
        project = project or self.project
        snapshot = make_snapshot(project, self.settings.source_roots, self.settings.state_root / "checks")
        paths = tuple(str(snapshot.root / r.snapshot_relative) for r in snapshot.records)
        report = EngineReport("eslint", "STRUCTURAL_CLEAR", paths, paths, 0, "SYNTHETIC TEST RECEIPT")
        captured = self.policies.capture(project)
        config = self.settings.tools[0]
        validation = EnginePolicyValidation("eslint", "VALIDATED_DEVELOPMENT", ("no-eval",),
                                             config.fingerprint(), "Synthetic, not a real compiler")
        effective = EffectivePolicy(captured.combined_sha256, (config,), (("eslint", ("no-eval",)),), (validation,))
        scan = summarize(snapshot, captured.combined_sha256, (report,))
        coverage = build_coverage_matrix(snapshot, (report,), self.settings.required_for_suffix)
        return CheckResult(project, captured, snapshot, effective, scan, coverage, snapshot.root,
                           self.settings.tool_identities(), ())

    def ready(self, project=None, **kwargs):
        project = project or self.project
        review = self.service.review(self.check(project), project, **kwargs)
        return review, self.service.confirm(review.review_id, review.fingerprint, project)

    def test_empty_source_directories_apply_and_exact_rollback(self):
        empty = self.source / "folder" / "empty" / "nested"
        empty.mkdir(parents=True)
        project = replace(self.project, selections=(Selection("directory", str(empty.parent), "empty"),))
        review, confirmation = self.ready(project)
        self.assertEqual(set(review.preview.created_directories), {"empty", "empty/nested"})
        outcome = self.service.apply(confirmation, project)
        self.assertEqual(outcome.state, "COMPLETED")
        self.assertTrue((self.target / "empty/nested").is_dir())
        inverse = self.service.restoration_review(outcome.operation_id)
        self.assertFalse(inverse.changes)
        self.assertEqual(self.service.rollback(outcome.operation_id, inverse.fingerprint).state, "ROLLED_BACK")
        self.assertFalse((self.target / "empty").exists())

    def test_delete_only_after_last_source_file_removed(self):
        folder = self.source / "folder"
        folder.mkdir()
        (folder / "last.js").write_text("const value = 1;")
        project = replace(self.project, selections=(Selection("directory", str(folder), "app"),))
        _, confirmation = self.ready(project)
        self.assertEqual(self.service.apply(confirmation, project).state, "COMPLETED")
        (folder / "last.js").unlink()
        review, confirmation = self.ready(project)
        self.assertEqual([(c.kind, c.relative_path) for c in review.preview.changes], [("delete", "app/last.js")])
        outcome = self.service.apply(confirmation, project)
        self.assertEqual(outcome.state, "COMPLETED")
        self.assertFalse((self.target / "app/last.js").exists())
        self.assertTrue((self.target / "app").is_dir())

    def test_reviewed_restoration_is_exact_and_one_shot(self):
        _, confirmation = self.ready()
        outcome = self.service.apply(confirmation, self.project)
        inverse = self.service.restoration_review(outcome.operation_id)
        self.assertEqual(inverse.changes[0].kind, "delete")
        (self.target / "owner.txt").write_text("new")
        with self.assertRaisesRegex(ContractError, "changed"):
            self.service.rollback(outcome.operation_id, inverse.fingerprint)
        self.assertTrue((self.target / "пример.js").exists())
        history = self.service.history()
        self.assertEqual(history[0].operation_id, outcome.operation_id)

    def test_explicit_partial_recovery_preserves_conflicting_bytes(self):
        (self.target / "пример.js").write_text("old external")
        review, confirmation = self.ready(adopted_existing=("пример.js",))
        def partial(kind, target, relative):
            if kind == "replace":
                (target / relative).write_bytes(b"partial or owner edit")
                raise Interrupted()
        self.backend.hook = partial
        with self.assertRaises(Interrupted):
            self.service.apply(confirmation, self.project)
        self.backend.hook = None
        key = self.service.pending()[0][0]
        self.assertEqual(self.service.recover(key).state, "RECOVERY_BLOCKED")
        with self.assertRaisesRegex(ContractError, "separate conflict"):
            self.service.restoration_review(key, recovery=True)
        plan = self.service.restoration_review(key, recovery=True, include_conflicts=True)
        self.assertEqual(len(plan.observed_conflicts), 1)
        self.assertEqual(self.service.recover_reviewed(plan).state, "ROLLED_BACK")
        self.assertEqual((self.target / "пример.js").read_text(), "old external")
        doc = load_json(self.service._op(key) / "journal.json")
        kept = doc["preserved_conflicts"][0]
        self.assertEqual((self.service._op(key) / kept["blob"]).read_bytes(), b"partial or owner edit")
        with self.assertRaises(ContractError):
            self.service.recover_reviewed(plan)

    def test_same_byte_target_replacement_stales_exact_preview(self):
        (self.target / "пример.js").write_text("old external")
        review = self.service.review(self.check(), self.project, adopted_existing=("пример.js",))
        replacement = self.target / "replacement"
        replacement.write_text("old external")
        replacement.replace(self.target / "пример.js")
        with self.assertRaisesRegex(ContractError, "Target"):
            self.service.confirm(review.review_id, review.fingerprint, self.project)

    def test_missing_last_selected_file_can_delete_only_its_previous_managed_target(self):
        _, confirmation = self.ready()
        self.assertEqual(self.service.apply(confirmation, self.project).state, "COMPLETED")
        self.js.unlink()
        review, confirmation = self.ready()
        self.assertEqual(review.preview.changes[0].kind, "delete")
        self.assertEqual(len(review.preview.missing_sources), 1)
        outcome = self.service.apply(confirmation, self.project)
        self.assertEqual(outcome.state, "COMPLETED")
        self.assertFalse((self.target / "пример.js").exists())
        plan = self.service.restoration_review(outcome.operation_id)
        self.assertEqual(self.service.rollback(outcome.operation_id, plan.fingerprint).state, "ROLLED_BACK")
        self.assertEqual((self.target / "пример.js").read_text(), "const value = 1;\n")

    def test_default_service_cannot_write_even_with_confirmation(self):
        service = PromotionService(self.settings)
        review = service.review(self.check(), self.project)
        confirmation = service.confirm(review.review_id, review.fingerprint, self.project)
        with self.assertRaisesRegex(ContractError, "backend"):
            service.apply(confirmation, self.project)
        self.assertEqual(list(self.target.iterdir()), [])
        self.assertFalse(service.native_update_available)

    def test_create_exact_bytes_then_one_shot_and_explicit_rollback(self):
        (self.target / "keep.txt").write_text("external data")
        review, confirmation = self.ready()
        self.assertEqual(review.preview.preserved, ("keep.txt",))
        result = self.service.apply(confirmation, self.project)
        self.assertEqual(result.state, "COMPLETED")
        self.assertEqual(result.scope, "SYNTHETIC_TEST")
        self.assertEqual((self.target / "пример.js").read_bytes(), self.js.read_bytes())
        self.assertEqual((self.target / "keep.txt").read_text(), "external data")
        with self.assertRaises(ContractError):
            self.service.apply(confirmation, self.project)
        journal = load_json(self.service._op(result.operation_id) / "journal.json")
        self.assertEqual(journal["state"], "COMPLETED")
        self.assertTrue(journal["operations"][0]["done"])
        self.assertEqual(self.service.recover(result.operation_id).state, "COMPLETED")
        fingerprint = self.service.review_rollback(result.operation_id)
        rollback = self.service.rollback(result.operation_id, fingerprint)
        self.assertEqual(rollback.state, "ROLLED_BACK")
        self.assertFalse((self.target / "пример.js").exists())
        self.assertEqual((self.target / "keep.txt").read_text(), "external data")

    def test_update_and_managed_delete_preserve_unmanaged_data(self):
        old = self.source / "obsolete.js"
        old.write_text("const obsolete = 1;\n")
        initial = replace(self.project, selections=(*self.project.selections, Selection("file", str(old), "obsolete.js")))
        _, confirmation = self.ready(initial)
        self.assertEqual(self.service.apply(confirmation, initial).state, "COMPLETED")
        (self.target / "keep.bin").write_bytes(b"\x00owner-data")
        old.unlink()
        self.js.write_text("const value = 2;\n")
        review, confirmation = self.ready()
        self.assertEqual({c.kind for c in review.preview.changes}, {"modify", "delete"})
        outcome = self.service.apply(confirmation, self.project)
        self.assertEqual(outcome.state, "COMPLETED")
        self.assertFalse((self.target / "obsolete.js").exists())
        self.assertEqual((self.target / "keep.bin").read_bytes(), b"\x00owner-data")
        self.assertEqual((self.target / "пример.js").read_bytes(), self.js.read_bytes())

    def test_adoption_is_explicit_and_does_not_claim_other_files(self):
        (self.target / "пример.js").write_text("old external bytes")
        (self.target / "other.txt").write_text("keep")
        with self.assertRaisesRegex(ContractError, "adoption"):
            self.ready()
        review, confirmation = self.ready(adopted_existing=("пример.js",))
        self.assertEqual(review.preview.adopted_existing, ("пример.js",))
        self.assertEqual(review.preview.changes[0].kind, "modify")
        self.assertEqual(self.service.apply(confirmation, self.project).state, "COMPLETED")
        document, _ = self.service.store.read()
        self.assertEqual(document["entries"][0]["files"], ["пример.js"])
        self.assertEqual((self.target / "other.txt").read_text(), "keep")

    def test_source_policy_registration_target_and_managed_drift_refuse(self):
        for change in ("source", "policy", "registration", "target", "managed"):
            with self.subTest(change=change):
                # Each case gets a fresh review and a stable reset afterwards.
                check = self.check()
                review = self.service.review(check, self.project)
                confirmation = self.service.confirm(review.review_id, review.fingerprint, self.project)
                current = self.project
                if change == "source":
                    self.js.write_text("const changed = 3;\n")
                elif change == "policy":
                    self.policies.update(replace(self.pack, name="Changed"), self.pack.fingerprint())
                elif change == "registration":
                    current = replace(self.project, name="Renamed")
                elif change == "target":
                    (self.target / "new-owner-data.txt").write_text("owner")
                else:
                    self.service.store.write({"schema_version": 1, "entries": [
                        {"project_id": "other", "target_root": str(self.target), "files": ["missing.js"]}]})
                with self.assertRaises(ContractError):
                    self.service.apply(confirmation, current)
                self.assertFalse((self.target / "пример.js").exists())
                self.js.write_text("const value = 1;\n")
                pack = self.policies.load("pack")
                if pack != self.pack:
                    self.policies.update(self.pack, pack.fingerprint())
                (self.target / "new-owner-data.txt").unlink(missing_ok=True)
                self.service.store.write({"schema_version": 1, "entries": []})

    def test_new_review_invalidates_previous_confirmation(self):
        _, old = self.ready()
        self.service.review(self.check(), self.project)
        with self.assertRaises(ContractError):
            self.service.apply(old, self.project)

    def test_finding_or_unsupported_check_cannot_be_acknowledged(self):
        check = self.check()
        for status in ("FINDINGS", "ERROR", "INCOMPLETE", "UNSUPPORTED"):
            with self.subTest(status=status), self.assertRaises(ContractError):
                self.service.review(replace(check, scan=replace(check.scan, status=status)), self.project)

    def test_other_project_cannot_claim_same_file_but_disjoint_shared_root_works(self):
        _, confirmation = self.ready()
        self.service.apply(confirmation, self.project)
        second = replace(self.project, registration_id="two", name="Second")
        with self.assertRaisesRegex(ContractError, "another project"):
            self.ready(second)
        second = replace(second, selections=(Selection("file", str(self.js), "second.js"),))
        _, confirmation = self.ready(second)
        self.assertEqual(self.service.apply(confirmation, second).state, "COMPLETED")
        document, _ = self.service.store.read()
        self.assertEqual(len(document["entries"]), 2)

    def test_crash_after_replace_before_journal_is_recovered_on_new_service(self):
        original = b"const old = 1;\n"
        (self.target / "пример.js").write_bytes(original)
        _, confirmation = self.ready(adopted_existing=("пример.js",))
        def crash(*_args):
            self.backend.hook = None
            raise Interrupted()
        self.backend.hook = crash
        with self.assertRaises(Interrupted):
            self.service.apply(confirmation, self.project)
        pending = self.service.pending()
        self.assertEqual(pending[0][1], "APPLYING")
        restarted = PromotionService(self.settings, self.backend)
        result = restarted.recover(pending[0][0])
        self.assertEqual(result.state, "ROLLED_BACK")
        self.assertEqual((self.target / "пример.js").read_bytes(), original)
        self.assertEqual(restarted.recover(result.operation_id).state, "ROLLED_BACK")

    def test_third_party_touched_file_blocks_recovery_without_clobber(self):
        _, confirmation = self.ready()
        def crash(*_args):
            self.backend.hook = None
            raise Interrupted()
        self.backend.hook = crash
        with self.assertRaises(Interrupted):
            self.service.apply(confirmation, self.project)
        operation_id = self.service.pending()[0][0]
        (self.target / "пример.js").write_text("third-party bytes")
        outcome = self.service.recover(operation_id)
        self.assertEqual(outcome.state, "RECOVERY_BLOCKED")
        self.assertEqual((self.target / "пример.js").read_text(), "third-party bytes")

    def test_foreign_edit_during_apply_is_preserved_and_rollback_is_honest(self):
        _, confirmation = self.ready()
        def foreign(*_args):
            self.backend.hook = None
            (self.target / "foreign.txt").write_text("owner data")
        self.backend.hook = foreign
        outcome = self.service.apply(confirmation, self.project)
        self.assertEqual(outcome.state, "ROLLED_BACK_WITH_EXTERNAL_DRIFT")
        self.assertFalse((self.target / "пример.js").exists())
        self.assertEqual((self.target / "foreign.txt").read_text(), "owner data")

    def test_nested_mapping_creation_and_rollback_remove_only_owned_empty_dirs(self):
        project = replace(self.project, selections=(Selection("file", str(self.js), "nested/deeper/script.js"),))
        _, confirmation = self.ready(project)
        outcome = self.service.apply(confirmation, project)
        self.assertEqual(outcome.state, "COMPLETED")
        fingerprint = self.service.review_rollback(outcome.operation_id)
        self.assertEqual(self.service.rollback(outcome.operation_id, fingerprint).state, "ROLLED_BACK")
        self.assertFalse((self.target / "nested").exists())

    def test_missing_target_root_and_existing_empty_owner_dir(self):
        self.target.rmdir()
        _, confirmation = self.ready()
        outcome = self.service.apply(confirmation, self.project)
        self.assertEqual(outcome.state, "COMPLETED")
        rollback = self.service.review_rollback(outcome.operation_id)
        self.assertEqual(self.service.rollback(outcome.operation_id, rollback).state, "ROLLED_BACK")
        self.assertFalse(self.target.exists())

    def test_staged_tamper_never_copies_unchecked_bytes(self):
        other = self.source / "b.js"
        other.write_text("const second = 1;\n")
        project = replace(self.project, selections=(Selection("file", str(self.js), "a.js"),
                                                    Selection("file", str(other), "b.js")))
        review, confirmation = self.ready(project)
        def tamper(*_args):
            self.backend.hook = None
            op_id = self.service.pending()[0][0]
            (self.service._op(op_id) / "after-1.bin").write_bytes(b"unscanned-payload")
        self.backend.hook = tamper
        outcome = self.service.apply(confirmation, project)
        self.assertEqual(outcome.state, "RECOVERY_BLOCKED")
        self.assertFalse((self.target / "b.js").exists())
        self.assertNotIn(b"unscanned-payload", [raw for _, raw in self.backend.writes])
        (self.service._op(outcome.operation_id) / "after-1.bin").write_bytes(other.read_bytes())
        self.assertEqual(self.service.recover(outcome.operation_id).state, "ROLLED_BACK")

    def test_source_edit_after_final_precheck_never_supplies_new_source_bytes(self):
        checked = self.js.read_bytes()
        _, confirmation = self.ready()
        def edit(*_args):
            self.backend.hook = None
            self.js.write_bytes(b"unscanned-new-source")
        self.backend.hook = edit
        outcome = self.service.apply(confirmation, self.project)
        self.assertEqual(outcome.state, "ROLLED_BACK")
        self.assertEqual(self.backend.writes[0][1], checked)
        self.assertFalse((self.target / "пример.js").exists())

    def test_completed_rollback_preserves_another_projects_commit(self):
        _, confirmation = self.ready()
        first = self.service.apply(confirmation, self.project)
        second = replace(self.project, registration_id="two", name="Second",
                         selections=(Selection("file", str(self.js), "second.js"),))
        _, confirmation = self.ready(second)
        self.service.apply(confirmation, second)
        fingerprint = self.service.review_rollback(first.operation_id)
        outcome = self.service.rollback(first.operation_id, fingerprint)
        self.assertEqual(outcome.state, "ROLLED_BACK_WITH_EXTERNAL_DRIFT")
        self.assertTrue((self.target / "second.js").is_file())
        self.assertFalse((self.target / "пример.js").exists())
        document, _ = self.service.store.read()
        self.assertEqual([row["project_id"] for row in document["entries"]], ["two"])

    def test_rollback_target_drift_requires_new_review(self):
        _, confirmation = self.ready()
        outcome = self.service.apply(confirmation, self.project)
        fingerprint = self.service.review_rollback(outcome.operation_id)
        (self.target / "owner.txt").write_text("new owner file")
        with self.assertRaisesRegex(ContractError, "changed"):
            self.service.rollback(outcome.operation_id, fingerprint)
        self.assertTrue((self.target / "пример.js").exists())
        self.assertEqual((self.target / "owner.txt").read_text(), "new owner file")

    def test_missing_and_present_empty_target_roots_have_different_preview(self):
        check = self.check()
        self.target.rmdir()
        review = self.service.review(check, self.project)
        self.target.mkdir()
        with self.assertRaises(ContractError):
            self.service.confirm(review.review_id, review.fingerprint, self.project)

    def test_corrupt_journal_cannot_direct_recovery_to_source(self):
        _, confirmation = self.ready()
        def crash(*_args):
            self.backend.hook = None
            raise Interrupted()
        self.backend.hook = crash
        with self.assertRaises(Interrupted):
            self.service.apply(confirmation, self.project)
        op = self.service._op(self.service.pending()[0][0])
        journal = load_json(op / "journal.json")
        journal["target_root"] = str(self.source)
        (op / "journal.json").write_text(json.dumps(journal))
        before = self.js.read_bytes()
        with self.assertRaises(ContractError):
            self.service.recover(journal["operation_id"])
        self.assertEqual(self.js.read_bytes(), before)

    def test_existing_managed_file_is_not_counted_as_first_import(self):
        _, confirmation = self.ready()
        self.service.apply(confirmation, self.project)
        review = self.service.review(self.check(), self.project, adopted_existing=("пример.js",))
        self.assertEqual(review.preview.adopted_existing, ())
        self.assertEqual(review.preview.changes[0].kind, "unchanged")
