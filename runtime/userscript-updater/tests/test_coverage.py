import tempfile
import unittest
from pathlib import Path

from checker.coverage import build_coverage_matrix
from checker.inventory import make_snapshot
from checker.model import Registration, Selection
from checker.reports import EngineReport


class CoverageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in ("a.js", "b.py", "assets.dat"):
            (self.root / name).write_bytes(b"content")
        selections = tuple(Selection("file", str(self.root / name))
                           for name in ("a.js", "b.py", "assets.dat"))
        self.reg = Registration("m", "Mixed", selections, ("pack",))
        self.snap = make_snapshot(self.reg, (self.root,), self.root / "reviews")
        self.by_suffix = {".js": ("eslint", "semgrep"), ".py": ("semgrep",)}

    def report(self, name, *suffixes):
        files = tuple(str(self.snap.root / record.snapshot_relative)
                      for record in self.snap.records
                      if Path(record.source_path).suffix in suffixes)
        return EngineReport(name, "STRUCTURAL_CLEAR", files, files, 0, "fixture")

    def test_unknown_data_file_cannot_disappear(self):
        matrix = build_coverage_matrix(self.snap, (self.report("eslint", ".js"),
                                                   self.report("semgrep", ".js", ".py")),
                                       self.by_suffix)
        self.assertEqual(matrix.status, "UNSUPPORTED")
        self.assertEqual([item.status for item in matrix.files],
                         ["NOT_AUTHORIZED", "NOT_AUTHORIZED", "UNSUPPORTED"])

    def test_required_semgrep_missing_for_js(self):
        matrix = build_coverage_matrix(self.snap, (self.report("eslint", ".js"),),
                                       {**self.by_suffix, ".dat": ("semgrep",)})
        self.assertEqual(matrix.status, "INCOMPLETE")
        self.assertIn("Missing required scanner", matrix.files[0].reason)

    def test_unexpected_scanner_path_is_error(self):
        bad = EngineReport("eslint", "STRUCTURAL_CLEAR", ("fake",), ("fake",), 0, "bad")
        matrix = build_coverage_matrix(self.snap, (bad,), self.by_suffix)
        self.assertEqual(matrix.status, "ERROR")
        self.assertIn("fake", matrix.unexpected_scanned)

    def test_known_only_never_authorizes(self):
        limited = Registration("js", "JS", (Selection("file", str(self.root / "a.js")),), ("pack",))
        snap = make_snapshot(limited, (self.root,), self.root / "reviews")
        expected = (str(snap.root / snap.records[0].snapshot_relative),)
        clean = (EngineReport("eslint", "STRUCTURAL_CLEAR", expected, expected, 0, "clear"),
                 EngineReport("semgrep", "STRUCTURAL_CLEAR", expected, expected, 0, "clear"))
        matrix = build_coverage_matrix(snap, clean, self.by_suffix)
        self.assertEqual(matrix.status, "NOT_AUTHORIZED")


if __name__ == "__main__":
    unittest.main()
