"""Headless source and permission checks, NOT a Windows visual GUI test."""
import ast
import sys
import unittest
from pathlib import Path


class GuiSourceTests(unittest.TestCase):
    def test_gui_model_smoke_without_tk(self):
        from checker.gui import main
        self.assertEqual(main(["--model-smoke"]), 0)

    def test_no_active_promoter_button_or_fixture_lab_import(self):
        source = (Path(__file__).resolve().parent.parent / "checker" / "gui.py").read_text()
        self.assertIn('state="disabled"', source)
        self.assertIn("Обновить (недоступно)", source)
        self.assertIn("Проверить (тестовая среда)", source)
        self.assertIn("--development-settings", source)
        self.assertIn("def _poll_jobs", source)
        self.assertNotIn("devtools", source)
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.ImportFrom):
                self.assertFalse(node.module and node.module.startswith("devtools"))

    def test_import_model_does_not_require_tkinter(self):
        import checker.ui_model
        self.assertNotIn("tkinter", sys.modules)


if __name__ == "__main__":
    unittest.main()
