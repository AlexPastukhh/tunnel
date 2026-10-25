import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from checker.inventory import make_snapshot
from checker.model import ContractError, Registration, Selection
from checker.preview import build_target_preview
from checker.ui_model import ReviewPresenter
from checker.reports import summarize


class V1ReviewRegressionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "данные.bin"
        self.source.write_bytes(b"\x00new-bytes")
        self.target = self.root / "approved"
        self.target.mkdir()
        (self.target / "данные.bin").write_bytes(b"\x00old")
        self.reg = Registration("one", "Первый", (
            Selection("file", str(self.source), "данные.bin"),), ("pack",), str(self.target))
        self.presenter = ReviewPresenter()
        self.presenter.register(self.reg)
        self.snap = make_snapshot(self.reg, (self.root,), self.root / "reviews")
        self.binding = self.presenter.begin_review("one", self.snap, "policy",
            (("eslint", "tool-v1"),), ("данные.bin",))

    def test_same_target_foreign_project_preview_is_refused(self):
        other = Registration("two", "Второй", self.reg.selections, ("pack",), str(self.target))
        self.presenter.register(other)
        plan = build_target_preview(self.snap, self.target, ("данные.bin",), binding=self.binding)
        with self.assertRaises(ContractError):
            self.presenter.set_reports("two", preview=plan)

    def test_binary_before_and_after_byte_sizes_are_visible(self):
        plan = build_target_preview(self.snap, self.target, ("данные.bin",), binding=self.binding)
        self.presenter.set_reports("one", preview=plan)
        table = self.presenter.preview_table("one")
        self.assertIn("До, байт", table.columns)
        self.assertIn("После, байт", table.columns)
        row = table.rows[0]
        self.assertEqual(row.columns[table.columns.index("До, байт")], "4")
        self.assertEqual(row.columns[table.columns.index("После, байт")], "10")

    def test_stale_snapshot_policy_tools_managed_set_and_job_are_refused(self):
        plan = build_target_preview(self.snap, self.target, ("данные.bin",), binding=self.binding)
        variants = (
            replace(self.binding, snapshot_id="another"),
            replace(self.binding, manifest_sha256="changed"),
            replace(self.binding, policy_sha256="new-policy"),
            replace(self.binding, tool_fingerprints=(("eslint", "tool-v2"),)),
            replace(self.binding, previously_managed=("missing.bin",)),
            replace(self.binding, job_id="old-job"),
        )
        for binding in variants:
            with self.subTest(binding=binding), self.assertRaises(ContractError):
                self.presenter.set_reports("one", preview=replace(plan, binding=binding))
        self.assertEqual(self.presenter.preview_table("one").rows, ())

    def test_new_job_and_cancel_refuse_old_callback_even_for_identical_inputs(self):
        plan = build_target_preview(self.snap, self.target, ("данные.bin",), binding=self.binding)
        self.presenter.begin_review("one", self.snap, "policy", (("eslint", "tool-v1"),), ("данные.bin",))
        with self.assertRaises(ContractError):
            self.presenter.set_reports("one", preview=plan)
        self.presenter.cancel_review("one")
        with self.assertRaises(ContractError):
            self.presenter.set_reports("one", preview=plan)

    def test_policy_edit_cannot_restore_cached_preview_with_delayed_callback(self):
        plan = build_target_preview(self.snap, self.target, ("данные.bin",), binding=self.binding)
        self.presenter.set_reports("one", preview=plan)
        self.presenter.invalidate_shared_pack("pack")
        with self.assertRaises(ContractError):
            self.presenter.set_reports("one", preview=plan)
        self.assertEqual(self.presenter.preview_table("one").rows, ())

    def test_wrong_preview_does_not_partially_publish_good_scan(self):
        scan = summarize(self.snap, "policy", (), binding=self.binding)
        plan = build_target_preview(self.snap, self.target, ("данные.bin",), binding=self.binding)
        with self.assertRaises(ContractError):
            self.presenter.set_reports("one", scan=scan,
                preview=replace(plan, binding=replace(self.binding, job_id="old")))
        self.assertNotIn("one", self.presenter.scan_reports)

    def test_plan_builder_refuses_snapshot_or_managed_set_mismatch(self):
        for snapshot, paths in ((replace(self.snap, snapshot_id="old"), ("данные.bin",)),
                                (self.snap, ("данные.bin", "missing.bin"))):
            with self.subTest(paths=paths), self.assertRaises(ContractError):
                build_target_preview(snapshot, self.target, paths, binding=self.binding)

    def test_missing_and_empty_binary_sizes_are_distinct(self):
        self.source.write_bytes(b"")
        snap = make_snapshot(self.reg, (self.root,), self.root / "reviews")
        (self.target / "данные.bin").unlink()
        (self.target / "удалён.bin").write_bytes(b"")
        binding = self.presenter.begin_review("one", snap, "policy",
            previously_managed=("удалён.bin",))
        plan = build_target_preview(snap, self.target, ("удалён.bin",), binding=binding)
        self.presenter.set_reports("one", preview=plan)
        table = self.presenter.preview_table("one")
        rows = {r.columns[0]: r.columns for r in table.rows}
        self.assertEqual(rows["create"][-2:], ("—", "0"))
        self.assertEqual(rows["delete"][-2:], ("0", "—"))
        self.assertFalse(self.presenter.can_apply("one"))

    def test_scan_binding_must_match_payload(self):
        scan = summarize(self.snap, "policy", (), binding=self.binding)
        for changed in (replace(scan, snapshot_id="other"),
                        replace(scan, policy_sha256="changed"),
                        replace(scan, source_files=999), replace(scan, binding=None)):
            with self.subTest(changed=changed), self.assertRaises(ContractError):
                self.presenter.set_reports("one", scan=changed)
