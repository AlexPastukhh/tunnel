"""Actual Check -> review -> synthetic target transaction, never owner authorization."""
import os
import tempfile
import time
import unittest
from dataclasses import replace
from pathlib import Path

from checker.engines import EngineConfig
from checker.inventory import digest
from checker.jobs import CheckJobs
from checker.model import Registration, Selection
from checker.policies import PolicyPack, PolicyStore
from checker.promotion import PromotionService
from checker.settings import DevelopmentSettings
from promotion_support import SyntheticTarget


@unittest.skipUnless(os.environ.get("UPDATER_DEV_ESLINT") and os.environ.get("UPDATER_DEV_SEMGREP"),
                     "Both actual Docker CLIs required")
class ActualPromotionIntegration(unittest.TestCase):
    def test_real_mixed_scan_review_apply_delete_and_rollback(self):
        with tempfile.TemporaryDirectory(prefix="checker-promotion-test-") as temporary:
            root = Path(temporary)
            source = root / "source"
            folder = source / "project"
            folder.mkdir(parents=True)
            (folder / "empty").mkdir()
            a, b, extra = folder / "a.js", folder / "b.py", source / "extra.js"
            a.write_text("const a = 1;\n")
            b.write_text("answer = 1\n")
            extra.write_text("const extra = true;\n")
            target = root / "target"
            target.mkdir()
            (target / "owner.bin").write_bytes(b"\x00owner data")
            configs = []
            for kind in ("eslint", "semgrep"):
                cli = Path(os.environ[f"UPDATER_DEV_{kind.upper()}"])
                cfg = Path(os.environ[f"UPDATER_DEV_{kind.upper()}_CONFIG"])
                configs.append(EngineConfig(kind, cli, digest(cli.read_bytes()), cfg, digest(cfg.read_bytes()),
                    Path("/usr/local/bin/node") if kind == "eslint" else None))
            settings = DevelopmentSettings(root / "state", root / "policies", (source,), tuple(configs),
                {".js": ("eslint", "semgrep"), ".py": ("semgrep",)}, 90)
            rules = Path(os.environ["UPDATER_DEV_SEMGREP_CONFIG"]).read_text()
            PolicyStore(settings.policy_root).create(PolicyPack("pack", "Fixture rules", {"no-eval": "error"}, rules))
            project = Registration("mixed", "Folder + file", (
                Selection("directory", str(folder), "app"), Selection("file", str(extra), "extra.js")),
                ("pack",), str(target))
            service = PromotionService(settings, SyntheticTarget(root))
            def check():
                jobs = CheckJobs(settings)
                jobs.start(project)
                deadline = time.monotonic() + 100
                try:
                    while time.monotonic() < deadline:
                        for event in jobs.drain():
                            if event.terminal:
                                jobs.thread.join(2)
                                self.assertEqual(event.phase, "COMPLETE_DEVELOPMENT", event.detail)
                                self.assertEqual(event.result.scan.status, "NOT_AUTHORIZED")
                                return event.result
                        time.sleep(0.02)
                    self.fail("Actual CLI job did not finish")
                finally:
                    jobs.cancel()
                    jobs.thread.join(5)
            first = service.review(check(), project)
            self.assertEqual(set(c.kind for c in first.preview.changes), {"create"})
            result = service.apply(service.confirm(first.review_id, first.fingerprint, project), project)
            self.assertEqual(result.state, "COMPLETED")
            self.assertEqual(result.scope, "SYNTHETIC_TEST")
            a.unlink()
            b.write_text("answer = 2\n")
            second = service.review(check(), project)
            self.assertEqual(set(c.kind for c in second.preview.changes), {"delete", "modify", "unchanged"})
            result = service.apply(service.confirm(second.review_id, second.fingerprint, project), project)
            self.assertEqual(result.state, "COMPLETED")
            self.assertFalse((target / "app/a.js").exists())
            self.assertEqual((target / "app/b.py").read_bytes(), b.read_bytes())
            self.assertEqual((target / "owner.bin").read_bytes(), b"\x00owner data")
            review = service.review_rollback(result.operation_id)
            self.assertEqual(service.rollback(result.operation_id, review).state, "ROLLED_BACK")
            self.assertEqual((target / "app/a.js").read_text(), "const a = 1;\n")
            self.assertEqual((target / "app/b.py").read_text(), "answer = 1\n")
            self.assertTrue((target / "app/empty").is_dir())
            # A resource-only/delete-only continuation still validates both real configs,
            # makes no claim of code analysis for the resource, and deletes only prior managed code.
            logo = source / "logo.png"
            logo.write_bytes(b"\x89PNG\r\nfixture")
            project = replace(project, selections=(Selection("directory", str(folder), "app"),
                Selection("file", str(logo), "logo.png", "resource")))
            third = service.review(check(), project)
            outcome = service.apply(service.confirm(third.review_id, third.fingerprint, project), project)
            self.assertEqual(outcome.state, "COMPLETED")
            b.unlink()
            resource_only = check()
            self.assertEqual(resource_only.scan.reports, ())
            self.assertEqual(resource_only.coverage.files[0].required_engines, ())
            final = service.review(resource_only, project)
            self.assertIn(("delete", "app/b.py"), [(c.kind, c.relative_path) for c in final.preview.changes])
            outcome = service.apply(service.confirm(final.review_id, final.fingerprint, project), project)
            self.assertEqual(outcome.state, "COMPLETED")
            self.assertEqual((target / "logo.png").read_bytes(), logo.read_bytes())
            self.assertEqual((target / "owner.bin").read_bytes(), b"\x00owner data")
            self.assertFalse((target / "app/b.py").exists())
            self.assertFalse(service.native_update_available)
