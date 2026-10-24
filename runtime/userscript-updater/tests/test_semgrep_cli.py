"""Real Semgrep CE JSON integration against isolated, synthetic fixtures only."""
import os
import tempfile
import unittest
from pathlib import Path

from checker.engines import EngineConfig, build_argv, run_dev_engine
from checker.inventory import digest, make_snapshot
from checker.model import Registration, Selection
from checker.reports import summarize


@unittest.skipUnless(os.environ.get("UPDATER_DEV_SEMGREP"), "No pinned Docker fixture Semgrep configured")
class SemgrepIntegration(unittest.TestCase):
    def test_js_and_python_fixtures(self):
        engine = Path(os.environ["UPDATER_DEV_SEMGREP"])
        rules = Path(os.environ["UPDATER_DEV_SEMGREP_CONFIG"])
        config = EngineConfig("semgrep", engine, digest(engine.read_bytes()),
                              rules, digest(rules.read_bytes()))
        with tempfile.TemporaryDirectory(prefix="updater-semgrep-test-") as tmp:
            root = Path(tmp)
            js = root / "safe.js"
            py = root / "unsafe.py"
            js.write_text("const answer = 42;\n")
            py.write_text("result = eval('2+2')\n")
            reg = Registration("scan", "JS + Python", (
                Selection("file", str(js)),
                Selection("file", str(py)),
            ), ("semgrep-demo",))
            snap = make_snapshot(reg, (root,), root / "reviews")
            argv = build_argv(config, tuple(snap.root / record.snapshot_relative for record in snap.records))
            for flag in ("--no-git-ignore", "--disable-nosem", "--metrics=off", "--no-autofix", "--oss-only"):
                self.assertIn(flag, argv)
            report = run_dev_engine(snap, config, timeout=90)
            self.assertEqual(report.status, "FINDINGS", report.detail)
            self.assertGreaterEqual(report.findings, 1)
            self.assertEqual(set(report.scanned), set(report.expected))
            self.assertEqual(summarize(snap, config.config_sha256, (report,)).status, "FINDINGS")

    def test_empty_finding_is_not_approval(self):
        engine = Path(os.environ["UPDATER_DEV_SEMGREP"])
        rules = Path(os.environ["UPDATER_DEV_SEMGREP_CONFIG"])
        config = EngineConfig("semgrep", engine, digest(engine.read_bytes()),
                              rules, digest(rules.read_bytes()))
        with tempfile.TemporaryDirectory(prefix="updater-semgrep-clean-") as tmp:
            root = Path(tmp)
            sample = root / "safe.py"
            sample.write_text("answer = 42\n")
            reg = Registration("clean", "Clean fixture", (Selection("file", str(sample)),), ("semgrep-demo",))
            snap = make_snapshot(reg, (root,), root / "reviews")
            report = run_dev_engine(snap, config, timeout=90)
            self.assertEqual(report.status, "STRUCTURAL_CLEAR", report.detail)
            self.assertEqual(summarize(snap, config.config_sha256, (report,)).status, "NOT_AUTHORIZED")


if __name__ == "__main__":
    unittest.main()
