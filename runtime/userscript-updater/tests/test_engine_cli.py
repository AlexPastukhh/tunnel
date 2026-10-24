"""Optional real CLI integration; only synthetic fixtures, never owner projects."""
import os
import tempfile
import unittest
from pathlib import Path

from checker.engines import EngineConfig, build_argv, run_dev_engine
from checker.inventory import digest, make_snapshot
from checker.model import Registration, Selection
from checker.reports import summarize


@unittest.skipUnless(os.environ.get("UPDATER_DEV_ESLINT"), "No pinned Docker fixture tool configured")
class ESLintIntegration(unittest.TestCase):
    def test_clean_and_eval_finding(self):
        cli = Path(os.environ["UPDATER_DEV_ESLINT"])
        cfg = Path(os.environ["UPDATER_DEV_ESLINT_CONFIG"])
        config = EngineConfig("eslint", cli, digest(cli.read_bytes()),
                              cfg, digest(cfg.read_bytes()), Path("/usr/local/bin/node"))
        with tempfile.TemporaryDirectory(prefix="updater-eslint-test-") as tmp:
            root = Path(tmp)
            source = root / "fixture.js"
            for code, expect in (("const answer = 42;", "STRUCTURAL_CLEAR"),
                                 ('eval("2+2");', "FINDINGS")):
                with self.subTest(expect=expect):
                    source.write_text(code)
                    reg = Registration("demo", "demo", (Selection("file", str(source)),), ("demo",))
                    snap = make_snapshot(reg, (root,), root / "review")
                    report = run_dev_engine(snap, config)
                    self.assertEqual(report.status, expect, report.detail)
                    argv = build_argv(config, (snap.root / snap.records[0].snapshot_relative,))
                    self.assertIn("--no-inline-config", argv)
                    self.assertIn("--no-config-lookup", argv)
                    self.assertIn("--no-ignore", argv)
                    self.assertNotIn("--fix", argv)
                    self.assertNotIn("--fix-dry-run", argv)
                    if expect == "STRUCTURAL_CLEAR":
                        self.assertEqual(summarize(snap, cfg.name, (report,)).status, "NOT_AUTHORIZED")


if __name__ == "__main__":
    unittest.main()
