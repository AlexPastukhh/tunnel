import tempfile
import unittest
from pathlib import Path
from checker.model import Registration, Selection, ContractError
from checker.inventory import make_snapshot, unchanged_since_snapshot, selected_files

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "src").mkdir()
        (self.root / "src" / "проверка.js").write_text("const x=1;")
        self.reg = Registration("r1", "Тест", (Selection("directory", str(self.root / "src"), "bundle"),), ("js-baseline",), str(self.root / "approved"))
    def test_manifest_add(self):
        snap = make_snapshot(self.reg, (self.root,), self.root / "reviews")
        self.assertTrue(unchanged_since_snapshot(self.reg, (self.root,), snap))
        self.assertEqual(snap.records[0].target_relative, "bundle/проверка.js")
        (self.root / "src" / "other.js").write_text("hello")
        self.assertFalse(unchanged_since_snapshot(self.reg, (self.root,), snap))
    def test_edit_remove_stale(self):
        snap = make_snapshot(self.reg, (self.root,), self.root / "reviews")
        (self.root / "src" / "проверка.js").write_text("changed")
        self.assertFalse(unchanged_since_snapshot(self.reg, (self.root,), snap))
        (self.root / "src" / "проверка.js").unlink()
        self.assertFalse(unchanged_since_snapshot(self.reg, (self.root,), snap))
    def test_check_only(self):
        reg = Registration("r2", "No target", (Selection("file", str(self.root / "src" / "проверка.js")),), ("p",))
        self.assertEqual(Registration.from_json(reg.to_json()), reg)
        self.assertIsNone(make_snapshot(reg, (self.root,), self.root / "reviews").records[0].target_relative)
    def test_overlap_denied(self):
        reg = Registration("r3", "Duplicate", (Selection("directory", str(self.root / "src"), "bundle"), Selection("file", str(self.root / "src" / "проверка.js"), "other.js")), ("p",), str(self.root / "approved"))
        with self.assertRaises(ContractError):
            list(selected_files(reg, (self.root,)))
    def test_link_denied(self):
        (self.root / "link.js").symlink_to(self.root / "src" / "проверка.js")
        reg = Registration("r4", "Link", (Selection("file", str(self.root / "link.js")),), ("p",))
        with self.assertRaises(ContractError):
            list(selected_files(reg, (self.root,)))
    def test_target_collision(self):
        (self.root / "src" / "other.js").write_text("hello")
        reg = Registration("r5", "collision", (Selection("file", str(self.root / "src" / "проверка.js"), "SAME.js"), Selection("file", str(self.root / "src" / "other.js"), "same.js")), ("p",), str(self.root / "approved"))
        with self.assertRaises(ContractError):
            list(selected_files(reg, (self.root,)))
    def test_mapping_traversal(self):
        reg = Registration("r6", "Escape", (Selection("file", str(self.root / "src" / "проверка.js"), "../escape.js"),), ("p",), str(self.root / "approved"))
        with self.assertRaises(ContractError):
            reg.validate()
    def test_outside_source(self):
        reg = Registration("r7", "outside", (Selection("file", str(self.root / "src" / "проверка.js")),), ("p",))
        with self.assertRaises(ContractError):
            list(selected_files(reg, (self.root / "reviews",)))

if __name__ == "__main__":
    unittest.main()
