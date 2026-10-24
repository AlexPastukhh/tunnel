"""Read-only effect previews on synthetic trees. No target update API exists."""
import tempfile
import unittest
from pathlib import Path

from checker.inventory import make_snapshot
from checker.model import ContractError, Registration, Selection
from checker.preview import build_target_preview


class PreviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.src = self.root / "source"
        self.src.mkdir()
        self.out = self.root / "approved"
        self.out.mkdir()
        (self.src / "main.js").write_text("const answer = 42;\n")
        self.registration = Registration(
            "r", "source", (Selection("file", str(self.src / "main.js"), "main.js"),),
            ("p",), str(self.out))

    def snapshot(self):
        return make_snapshot(self.registration, (self.root,), self.root / "review")

    def test_create_file_without_any_write(self):
        snap = self.snapshot()
        preview = build_target_preview(snap, self.out, ())
        self.assertEqual([change.kind for change in preview.changes], ["create"])
        self.assertEqual(list(self.out.iterdir()), [])
        self.assertIn("+const answer", preview.changes[0].text_diff)

    def test_modify_preview_diff_leaves_old_bytes_untouched(self):
        current = self.out / "main.js"
        current.write_text("const answer = 1;\n")
        preview = build_target_preview(self.snapshot(), self.out, ("main.js",))
        self.assertEqual(preview.changes[0].kind, "modify")
        self.assertIn("-const answer = 1;", preview.changes[0].text_diff)
        self.assertIn("+const answer = 42;", preview.changes[0].text_diff)
        self.assertEqual(current.read_text(), "const answer = 1;\n")

    def test_source_delete_proposes_managed_delete_preserves_unmanaged(self):
        (self.out / "old.js").write_text("old")
        (self.out / "notes.txt").write_text("user data")
        preview = build_target_preview(self.snapshot(), self.out, ("old.js",))
        self.assertEqual({change.relative_path: change.kind for change in preview.changes},
                         {"main.js": "create", "old.js": "delete"})
        self.assertEqual(preview.preserved, ("notes.txt",))
        self.assertTrue((self.out / "old.js").exists())

    def test_existing_unmanaged_destination_requires_adoption(self):
        (self.out / "main.js").write_text("existing owner")
        with self.assertRaisesRegex(ContractError, "explicit adoption"):
            build_target_preview(self.snapshot(), self.out, ())

    def test_target_change_invalidates_plan_fingerprint(self):
        target = self.out / "main.js"
        target.write_text("before")
        snap = self.snapshot()
        old = build_target_preview(snap, self.out, ("main.js",))
        target.write_text("after")
        fresh = build_target_preview(snap, self.out, ("main.js",))
        self.assertNotEqual(old.fingerprint, fresh.fingerprint)
        self.assertNotEqual(old.target_inventory_sha256, fresh.target_inventory_sha256)

    def test_target_symlink_is_refused(self):
        (self.out / "main.js").symlink_to(self.src / "main.js")
        with self.assertRaisesRegex(ContractError, "Link/reparse"):
            build_target_preview(self.snapshot(), self.out, ("main.js",))

    def test_check_only_cannot_plan_promotion(self):
        src = self.src / "main.js"
        reg = Registration("check", "check", (Selection("file", str(src)),), ("p",))
        snap = make_snapshot(reg, (self.root,), self.root / "review")
        with self.assertRaisesRegex(ContractError, "Check-only"):
            build_target_preview(snap, self.out, ())

    def test_binary_diff_only_hashes(self):
        binary = self.src / "blob.dat"
        binary.write_bytes(b"new\0binary")
        reg = Registration("binary", "binary", (Selection("file", str(binary), "blob.dat"),),
                           ("p",), str(self.out))
        snap = make_snapshot(reg, (self.root,), self.root / "review")
        (self.out / "blob.dat").write_bytes(b"old\0binary")
        preview = build_target_preview(snap, self.out, ("blob.dat",))
        self.assertEqual(preview.changes[0].kind, "modify")
        self.assertIsNone(preview.changes[0].text_diff)
        self.assertIsNotNone(preview.changes[0].diff_note)
        self.assertNotEqual(preview.changes[0].before_sha256, preview.changes[0].after_sha256)

    def test_directory_over_file_refused(self):
        (self.out / "sub").write_text("owner note")
        src = self.src / "main.js"
        reg = Registration("bad", "bad", (Selection("file", str(src), "sub/main.js"),),
                           ("p",), str(self.out))
        snap = make_snapshot(reg, (self.root,), self.root / "review")
        with self.assertRaisesRegex(ContractError, "overlap"):
            build_target_preview(snap, self.out, ())


if __name__ == "__main__":
    unittest.main()
