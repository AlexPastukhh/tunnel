"""Negative report-shape and coverage-integrity tests."""
import json
import tempfile
import unittest
from pathlib import Path

from checker.inventory import make_snapshot
from checker.model import Registration, Selection
from checker.reports import EngineReport, parse_eslint, parse_semgrep, summarize


class StrictReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "clean.js"
        self.source.write_text("const x = 1;")
        registration = Registration("r", "demo", (Selection("file", str(self.source)),), ("pack",))
        self.snap = make_snapshot(registration, (self.root,), self.root / "review")
        self.expected = (self.snap.root / self.snap.records[0].snapshot_relative,)

    def test_semgrep_skipped_field_is_optional(self):
        payload = {"results": [], "errors": [], "paths": {"scanned": [str(self.expected[0])]}}
        report = parse_semgrep(json.dumps(payload), 0, self.expected, self.snap.root)
        self.assertEqual(report.status, "STRUCTURAL_CLEAR")
        self.assertEqual(summarize(self.snap, "policy", (report,)).status, "NOT_AUTHORIZED")

    def test_eslint_suppressed_findings_are_not_clear(self):
        payload = [{"filePath": str(self.expected[0]), "messages": [],
                    "suppressedMessages": [{"ruleId": "no-eval", "message": "suppressed"}]}]
        report = parse_eslint(json.dumps(payload), 0, self.expected, self.snap.root)
        self.assertEqual(report.status, "ERROR")

    def test_unexpected_engine_is_error(self):
        file = str(self.expected[0])
        forged = EngineReport("unknown", "STRUCTURAL_CLEAR", (file,), (file,), 0, "")
        self.assertEqual(summarize(self.snap, "policy", (forged,)).status, "ERROR")

    def test_forged_structural_clear_with_no_actual_scan_is_error(self):
        file = str(self.expected[0])
        forged = EngineReport("semgrep", "STRUCTURAL_CLEAR", (file,), (), 0, "")
        self.assertEqual(summarize(self.snap, "policy", (forged,)).status, "ERROR")


if __name__ == "__main__":
    unittest.main()
