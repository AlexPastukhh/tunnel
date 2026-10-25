"""Headless source and permission checks, NOT a Windows visual GUI test."""
import ast
import sys
import unittest
from pathlib import Path


class GuiSourceTests(unittest.TestCase):
    def test_gui_model_smoke_without_tk(self):
        from checker.gui import main
        self.assertEqual(main(["--model-smoke"]), 0)

    def test_application_cannot_import_fixture_writers(self):
        root = Path(__file__).resolve().parent.parent / "checker"
        for file in root.glob("*.py"):
            for node in ast.walk(ast.parse(file.read_text())):
                modules = ([node.module] if isinstance(node, ast.ImportFrom) else
                           [n.name for n in node.names] if isinstance(node, ast.Import) else [])
                self.assertFalse(any(m and m.split(".")[0] in
                    ("devtools", "tests", "promotion_support", "native_acceptance") for m in modules), str(file))

    def test_import_model_does_not_require_tkinter(self):
        import checker.ui_model
        self.assertNotIn("tkinter", sys.modules)


if __name__ == "__main__":
    unittest.main()
