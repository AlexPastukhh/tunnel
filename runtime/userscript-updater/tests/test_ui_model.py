import tempfile
import unittest
from pathlib import Path

from checker.inventory import make_snapshot
from checker.model import ContractError, Registration, Selection
from checker.preview import build_target_preview
from checker.reports import ScanReport
from checker.ui_model import ReviewPresenter, BLOCK_REASON
from checker.windows_layout import RootSpec, review_windows_layout


class PresentationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.file = self.base / "safe.js"
        self.file.write_text("const good = true;\n")
        self.reg = Registration("one", "Первый", (Selection("file", str(self.file)),),
                                ("rule-alpha",))
        self.presenter = ReviewPresenter()
        self.presenter.register(self.reg)

    def test_check_only_visible(self):
        self.assertEqual(self.presenter.projects_table().rows[0].columns[-1], "Только проверка")
        self.assertIn("Без назначения", self.presenter.bindings_table("one").rows[0].columns[-1])

    def test_cached_scan_invalidated_on_registration_change(self):
        snap = make_snapshot(self.reg, (self.base,), self.base / "reviews")
        scan = ScanReport("NOT_AUTHORIZED", self.reg.fingerprint(), snap.snapshot_id, "demo", 1, (), ())
        self.presenter.set_reports("one", scan=scan)
        self.assertIn("NOT_AUTHORIZED", self.presenter.scan_table("one").footer)
        self.presenter.register(Registration("one", "Changed", self.reg.selections, ("different",)))
        self.assertIn("не выполнялась", self.presenter.scan_table("one").footer)

    def test_foreign_report_refused(self):
        bad = ScanReport("NOT_AUTHORIZED", "fake", "fake", "fake", 1, (), ())
        with self.assertRaisesRegex(ContractError, "different registration"):
            self.presenter.set_reports("one", scan=bad)

    def test_preview_renders_deletion_and_create_without_permission(self):
        target = self.base / "approved"
        target.mkdir()
        (target / "old.js").write_text("old")
        reg = Registration("two", "Two", (Selection("file", str(self.file), "new.js"),),
                           ("pack",), str(target))
        self.presenter.register(reg)
        snap = make_snapshot(reg, (self.base,), self.base / "reviews")
        plan = build_target_preview(snap, target, ("old.js",))
        self.presenter.set_reports("two", preview=plan)
        self.assertEqual({r.columns[0] for r in self.presenter.preview_table("two").rows},
                         {"create", "delete"})
        self.assertFalse(self.presenter.can_apply("two"))

    def test_foreign_target_preview_rejected(self):
        reg = Registration("two", "Two", (Selection("file", str(self.file), "new.js"),),
                           ("pack",), str(self.base / "approved"))
        self.presenter.register(reg)
        snap = make_snapshot(reg, (self.base,), self.base / "reviews")
        plan = build_target_preview(snap, self.base / "elsewhere", ())
        with self.assertRaisesRegex(ContractError, "destination differs"):
            self.presenter.set_reports("two", preview=plan)

    def test_layout_no_host_authorization(self):
        plan = review_windows_layout((
            RootSpec("app", r"C:\Owner\App"),
            RootSpec("tools", r"C:\Owner\Tools"),
            RootSpec("policies", r"C:\Owner\Rules"),
            RootSpec("state", r"C:\Owner\State"),
            RootSpec("approved", r"C:\Owner\Approved"),
            RootSpec("source", r"C:\AI\Repos\Project"),
            RootSpec("agent_write", r"C:\AI\Repos"),
        ))
        self.assertIn("NEEDS_NATIVE_WINDOWS_VERIFICATION",
                      self.presenter.layout_table(plan).footer)
        self.assertFalse(self.presenter.can_apply())
        self.assertIn("заблокировано", BLOCK_REASON)

    def test_shared_policy_edit_invalidates_all_consumers(self):
        second = Registration("two", "Second", self.reg.selections, ("rule-alpha",))
        third = Registration("three", "Different", self.reg.selections, ("other",))
        self.presenter.register(second)
        self.presenter.register(third)
        for project in (self.reg, second, third):
            self.presenter.set_reports(project.registration_id, scan=ScanReport(
                "NOT_AUTHORIZED", project.fingerprint(), "snap", "policy", 1, (), ()))
        affected = self.presenter.invalidate_shared_pack("rule-alpha")
        self.assertEqual(affected, ("one", "two"))
        self.assertIn("не выполнялась", self.presenter.scan_table("one").footer)
        self.assertIn("не выполнялась", self.presenter.scan_table("two").footer)
        self.assertIn("NOT_AUTHORIZED", self.presenter.scan_table("three").footer)

    def test_preview_shows_unmanaged_files_and_empty_directories(self):
        target = self.base / "approved"
        target.mkdir()
        (target / "keep.txt").write_text("independent")
        (target / "keep-dir").mkdir()
        reg = Registration("two", "Two", (Selection("file", str(self.file), "new.js"),),
                           ("pack",), str(target))
        self.presenter.register(reg)
        snap = make_snapshot(reg, (self.base,), self.base / "reviews")
        plan = build_target_preview(snap, target, ())
        self.presenter.set_reports("two", preview=plan)
        names = {row.columns[0] for row in self.presenter.preview_table("two").rows}
        self.assertEqual(names, {"create", "preserve", "preserve-dir"})

    def test_delete_clears_cached_results(self):
        self.presenter.remove("one")
        self.assertEqual(self.presenter.projects_table().rows, ())
        self.assertEqual(self.presenter.scan_table("one").rows, ())

    def test_json_import_is_data(self):
        loaded = self.presenter.register_json(self.reg.to_json())
        self.assertEqual(loaded.fingerprint(), self.reg.fingerprint())
        self.assertFalse(self.presenter.can_apply("one"))


if __name__ == "__main__":
    unittest.main()
