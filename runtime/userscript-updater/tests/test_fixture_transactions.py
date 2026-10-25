"""Transaction failures and recovery restricted to disposable synthetic data."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from devtools.fixture_transactions import (
    CANARY, SimulatedInterruption, apply_fixture_transaction,
    fixture_scope, prepare_fixture_transaction, recover_fixture_transaction,
)
from checker.inventory import make_snapshot
from checker.model import ContractError, Registration, Selection
from checker.policies import PolicyPack, PolicyStore
from checker.preview import build_target_preview


class FixtureTransactionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="checker-fixture-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / ".synthetic-only").write_text(CANARY)
        self.source = self.root / "src"
        self.source.mkdir()
        self.approved = self.root / "approved"
        self.approved.mkdir()
        self.a = self.source / "a.js"
        self.a.write_text("const a=2;\n")
        self.b = self.source / "b.py"
        self.b.write_text("b=3\n")
        self.registration = Registration(
            "synthetic", "Test", (
                Selection("file", str(self.a), "a.js"),
                Selection("file", str(self.b), "sub/b.py"),
            ), ("shared",), str(self.approved),
        )
        self.policy_store = PolicyStore(self.root / "policy")
        self.policy = PolicyPack("shared", "Test only", {"no-eval": "error"})
        self.policy_store.create(self.policy)
        self.captured = self.policy_store.capture(self.registration)
        self.snap = make_snapshot(self.registration, (self.root,), self.root / "snapshots")

    def prepare(self, previously_managed=(), preview=None):
        preview = preview or build_target_preview(self.snap, self.approved, previously_managed)
        operation = prepare_fixture_transaction(
            self.root, self.registration, (self.root,), self.snap,
            self.policy_store, self.captured, preview, previously_managed,
            test_only_approval_fingerprint=preview.fingerprint,
        )
        return preview, operation

    def apply(self, preview, operation, **kwargs):
        return apply_fixture_transaction(
            self.root, operation, self.registration, (self.root,), self.snap,
            self.policy_store, self.captured, approved_preview_fingerprint=preview.fingerprint,
            **kwargs,
        )

    def test_confirm_creates_exact_staged_bytes_with_journal_and_backup(self):
        (self.approved / "other-owner.txt").write_text("preserve")
        preview, operation = self.prepare()
        self.assertEqual(list(self.approved.iterdir()), [self.approved / "other-owner.txt"])
        self.assertEqual(self.apply(preview, operation), "COMPLETED")
        self.assertEqual((self.approved / "a.js").read_bytes(), self.a.read_bytes())
        self.assertEqual((self.approved / "sub" / "b.py").read_bytes(), self.b.read_bytes())
        self.assertEqual((self.approved / "other-owner.txt").read_text(), "preserve")
        journal = json.loads((operation.operation_directory / "journal.json").read_text())
        self.assertEqual(journal["state"], "COMPLETED")
        self.assertEqual(journal["applied_count"], 2)
        with self.assertRaisesRegex(ContractError, "already started"):
            self.apply(preview, operation)
        self.assertEqual(recover_fixture_transaction(self.root, operation), "COMPLETED")
        self.assertEqual(recover_fixture_transaction(self.root, operation, rollback_completed=True), "ROLLED_BACK")
        self.assertFalse((self.approved / "a.js").exists())
        self.assertFalse((self.approved / "sub").exists())
        self.assertEqual((self.approved / "other-owner.txt").read_text(), "preserve")

    def test_successful_delete_is_confined_to_previously_managed_paths(self):
        (self.approved / "a.js").write_text("old managed")
        (self.approved / "removed.py").write_text("old managed and deleted in source")
        (self.approved / "keep-user.txt").write_text("independent")
        preview, op = self.prepare(("a.js", "removed.py"))
        self.assertEqual(self.apply(preview, op), "COMPLETED")
        self.assertEqual((self.approved / "a.js").read_bytes(), self.a.read_bytes())
        self.assertFalse((self.approved / "removed.py").exists())
        self.assertEqual((self.approved / "keep-user.txt").read_text(), "independent")
        self.assertEqual(recover_fixture_transaction(self.root, op, rollback_completed=True),
                         "ROLLED_BACK")
        self.assertEqual((self.approved / "a.js").read_text(), "old managed")
        self.assertEqual((self.approved / "removed.py").read_text(),
                         "old managed and deleted in source")
        self.assertEqual((self.approved / "keep-user.txt").read_text(), "independent")

    def test_crash_after_synthetic_delete_is_recovered(self):
        (self.approved / "a.js").write_text("old managed")
        (self.approved / "old-delete.txt").write_text("old-delete")
        preview, op = self.prepare(("a.js", "old-delete.txt"))
        with self.assertRaises(SimulatedInterruption):
            self.apply(preview, op, inject_crash_after=3)
        self.assertFalse((self.approved / "old-delete.txt").exists())
        self.assertEqual(recover_fixture_transaction(self.root, op), "ROLLED_BACK")
        self.assertEqual((self.approved / "a.js").read_text(), "old managed")
        self.assertEqual((self.approved / "old-delete.txt").read_text(), "old-delete")

    def test_transaction_engine_not_shipped_in_checker_package(self):
        self.assertFalse((Path(__file__).resolve().parent.parent / "checker" / "fixture_transactions.py").exists())
        self.assertTrue((Path(__file__).resolve().parent.parent / "devtools" / "fixture_transactions.py").is_file())

    def test_approved_modify_and_delete_recovered_after_fault(self):
        (self.approved / "a.js").write_text("const a=1;\n")
        (self.approved / "removed.py").write_text("important previous")
        preview, operation = self.prepare(("a.js", "removed.py"))
        self.assertIn("delete", [change.kind for change in preview.changes])
        with self.assertRaisesRegex(OSError, "Synthetic I/O failure"):
            self.apply(preview, operation, inject_error_after=3)
        self.assertEqual((self.approved / "a.js").read_text(), "const a=1;\n")
        self.assertEqual((self.approved / "removed.py").read_text(), "important previous")
        self.assertFalse((self.approved / "sub" / "b.py").exists())
        state = json.loads((operation.operation_directory / "journal.json").read_text())["state"]
        self.assertEqual(state, "ROLLED_BACK")

    def test_crash_mid_operation_requires_explicit_recovery(self):
        preview, operation = self.prepare()
        with self.assertRaises(SimulatedInterruption):
            self.apply(preview, operation, inject_crash_after=1)
        self.assertTrue((self.approved / "a.js").exists())
        self.assertFalse((self.approved / "sub" / "b.py").exists())
        self.assertEqual(recover_fixture_transaction(self.root, operation), "ROLLED_BACK")
        self.assertFalse((self.approved / "a.js").exists())
        self.assertEqual(recover_fixture_transaction(self.root, operation), "ROLLED_BACK")

    def test_target_change_before_apply_refuses(self):
        preview, operation = self.prepare()
        (self.approved / "owner.txt").write_text("owner data")
        with self.assertRaisesRegex(ContractError, "target changed"):
            self.apply(preview, operation)
        self.assertFalse((self.approved / "a.js").exists())
        self.assertEqual((self.approved / "owner.txt").read_text(), "owner data")

    def test_source_change_before_prepare_or_apply_refuses(self):
        preview = build_target_preview(self.snap, self.approved, ())
        self.a.write_text("const a=9;\n")
        with self.assertRaisesRegex(ContractError, "Source differs"):
            self.prepare(preview=preview)
        self.a.write_text("const a=2;\n")
        _, operation = self.prepare(preview=preview)
        self.a.write_text("const a=9;\n")
        with self.assertRaisesRegex(ContractError, "Source, registration or policy stale"):
            self.apply(preview, operation)
        self.assertFalse((self.approved / "a.js").exists())

    def test_policy_change_before_apply_refuses(self):
        preview, operation = self.prepare()
        self.policy_store.update(PolicyPack("shared", "New", {"no-eval": "error", "no-implied-eval": "error"}),
                                 self.policy.fingerprint())
        with self.assertRaisesRegex(ContractError, "Source, registration or policy stale"):
            self.apply(preview, operation)
        self.assertFalse((self.approved / "a.js").exists())

    def test_wrong_approval_fingerprint_refuses_before_staging(self):
        preview = build_target_preview(self.snap, self.approved, ())
        with self.assertRaisesRegex(ContractError, "fingerprint"):
            prepare_fixture_transaction(self.root, self.registration, (self.root,), self.snap,
                                        self.policy_store, self.captured, preview, (),
                                        test_only_approval_fingerprint="not approved")
        self.assertFalse((self.root / "_fixture_transactions").exists())

    def test_snapshot_tampering_refuses(self):
        preview = build_target_preview(self.snap, self.approved, ())
        (self.snap.root / self.snap.records[0].snapshot_relative).write_text("evil")
        with self.assertRaises(ContractError):
            self.prepare(preview=preview)

    def test_recovery_blocked_if_third_party_modified_touched_file(self):
        preview, operation = self.prepare()
        with self.assertRaises(SimulatedInterruption):
            self.apply(preview, operation, inject_crash_after=1)
        (self.approved / "a.js").write_text("third-party change")
        self.assertEqual(recover_fixture_transaction(self.root, operation), "RECOVERY_BLOCKED")
        self.assertEqual((self.approved / "a.js").read_text(), "third-party change")
        self.assertEqual(json.loads((operation.operation_directory / "journal.json").read_text())["state"],
                         "RECOVERY_BLOCKED")

    def test_original_existing_empty_folder_stays_after_rollback(self):
        (self.approved / "owner-empty").mkdir()
        preview, operation = self.prepare()
        self.apply(preview, operation)
        self.assertEqual(recover_fixture_transaction(self.root, operation, rollback_completed=True), "ROLLED_BACK")
        self.assertTrue((self.approved / "owner-empty").is_dir())

    def test_refuses_real_nonfixture_location(self):
        with tempfile.TemporaryDirectory() as other:
            other_dir = Path(other)
            (other_dir / ".synthetic-only").write_text(CANARY)
            with self.assertRaisesRegex(ContractError, "Only named Python TemporaryDirectory"):
                fixture_scope(other_dir)
        with self.assertRaises(ContractError):
            fixture_scope(self.root, target=Path("/workspace/repos/tunnel"))

    def test_crash_between_file_replace_and_journal_persist_is_recoverable(self):
        preview, operation = self.prepare()
        from devtools import fixture_transactions as tx
        actual_save = tx._save_journal
        def interrupt_journal(op, doc):
            if doc["state"] == "APPLYING" and doc["applied_count"] == 1:
                raise SimulatedInterruption("Hard stop while checkpointing")
            return actual_save(op, doc)

        with patch.object(tx, "_save_journal", side_effect=interrupt_journal):
            with self.assertRaises(SimulatedInterruption):
                self.apply(preview, operation)
        self.assertTrue((self.approved / "a.js").is_file())
        self.assertFalse((self.approved / "sub" / "b.py").is_file())
        self.assertEqual(recover_fixture_transaction(self.root, operation), "ROLLED_BACK")
        self.assertFalse((self.approved / "a.js").exists())

    def test_unmanaged_data_changed_during_apply_aborts_with_rollback(self):
        other = self.approved / "owner-only.txt"
        other.write_text("owner-before")
        preview, operation = self.prepare()
        from devtools import fixture_transactions as tx
        original = tx._apply_item
        touched = []

        def update_and_touch(target, operation_dir, item):
            original(target, operation_dir, item)
            if not touched:
                other.write_text("owner-after")
                touched.append(True)

        with patch.object(tx, "_apply_item", side_effect=update_and_touch):
            with self.assertRaisesRegex(ContractError, "Full destination inventory"):
                self.apply(preview, operation)
        self.assertFalse((self.approved / "a.js").exists())
        self.assertFalse((self.approved / "sub" / "b.py").exists())
        # A third-party change is not deleted or rewritten during recovery.
        self.assertEqual(other.read_text(), "owner-after")
        self.assertEqual(recover_fixture_transaction(self.root, operation), "ROLLED_BACK_WITH_EXTERNAL_DRIFT")

    def test_prepared_transaction_does_not_rollback_independent_owner_edit(self):
        (self.approved / "a.js").write_text("original")
        preview, operation = self.prepare(("a.js",))
        # Independent actor writes EXACTLY the proposed candidate bytes.
        (self.approved / "a.js").write_bytes(self.a.read_bytes())
        self.assertEqual(recover_fixture_transaction(self.root, operation), "RECOVERY_BLOCKED")
        self.assertEqual((self.approved / "a.js").read_bytes(), self.a.read_bytes())

    def test_tampered_backup_blocks_apply_and_recovery(self):
        (self.approved / "a.js").write_text("original")
        preview, operation = self.prepare(("a.js",))
        (operation.operation_directory / "before" / "00000.before").write_text("bad backup")
        with self.assertRaisesRegex(ContractError, "Backup digest mismatch"):
            self.apply(preview, operation)
        with self.assertRaisesRegex(ContractError, "Backup digest mismatch"):
            recover_fixture_transaction(self.root, operation)
        self.assertEqual((self.approved / "a.js").read_text(), "original")

    def test_wrong_destination_or_mismatched_review_cannot_apply(self):
        preview, operation = self.prepare()
        with self.assertRaisesRegex(ContractError, "approval"):
            apply_fixture_transaction(
                self.root, operation, self.registration, (self.root,), self.snap,
                self.policy_store, self.captured, approved_preview_fingerprint="other",
            )
        self.assertFalse((self.approved / "a.js").exists())
        other_target = self.root / "other"
        other_target.mkdir()
        fixture_scope(self.root, target=other_target)
        with self.assertRaisesRegex(ContractError, "inside synthetic root"):
            fixture_scope(self.root, target=Path("/etc"))

    def test_approval_rejects_unrelated_source_root_even_when_snapshot_exists(self):
        preview, operation = self.prepare()
        with self.assertRaisesRegex(ContractError, "Synthetic source outside"):
            apply_fixture_transaction(
                self.root, operation, self.registration, (Path("/workspace/repo"),), self.snap,
                self.policy_store, self.captured, approved_preview_fingerprint=preview.fingerprint,
            )
        self.assertFalse((self.approved / "a.js").exists())

    def test_fixture_marker_symlink_is_refused(self):
        with tempfile.TemporaryDirectory() as elsewhere:
            link_target = Path(elsewhere) / "token.txt"
            link_target.write_text(CANARY)
            marker = self.root / ".synthetic-only"
            marker.unlink()
            marker.symlink_to(link_target)
            with self.assertRaisesRegex(ContractError, "Link/reparse"):
                fixture_scope(self.root)

    def test_prepared_snapshot_has_backups_not_target_writes(self):
        (self.approved / "a.js").write_text("old")
        preview, operation = self.prepare(("a.js",))
        self.assertEqual((self.approved / "a.js").read_text(), "old")
        backup = operation.operation_directory / "before" / "00000.before"
        self.assertEqual(backup.read_bytes(), b"old")
        self.assertTrue((operation.operation_directory / "after" / "00000.after").is_file())
        self.assertEqual(recover_fixture_transaction(self.root, operation), "ROLLED_BACK")
        self.assertEqual((self.approved / "a.js").read_text(), "old")


if __name__ == "__main__":
    unittest.main()
