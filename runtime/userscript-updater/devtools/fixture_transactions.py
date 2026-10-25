"""Synthetic transaction/rollback laboratory. ABSOLUTELY NOT an installed updater.

Writes are limited to test-only TemporaryDirectory roots with a canary marker.
The callable does not accept a trusted scanner PASS or secure user approval.
It intentionally cannot be wired to an external Windows target or real owner
application; harden/reimplement independently for the installed trust boundary.
"""
from __future__ import annotations

import json
import os
import shutil
import stat
import tempfile
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path

from checker.inventory import Snapshot, check_plain_chain, digest, read_stable_file, unchanged_since_snapshot
from checker.model import ContractError, Registration, relative_target
from checker.policies import CapturedPolicies, PolicyStore
from checker.preview import TargetPreview, build_target_preview, _read_tree

CANARY = "PROJECT_CHECKER_SYNTHETIC_FIXTURE_ONLY\n"
STATUSES = {"PREPARED", "APPLYING", "COMPLETED", "ABORTED",
            "ROLLED_BACK", "ROLLED_BACK_WITH_EXTERNAL_DRIFT", "RECOVERY_BLOCKED"}


class SimulatedInterruption(BaseException):
    """Test-only crash: skip in-process recovery to exercise next-run recovery."""


@dataclass(frozen=True)
class FixtureTransaction:
    operation_id: str
    operation_directory: Path
    fingerprint: str


def fixture_scope(root: Path, source: Snapshot | None = None, target: Path | None = None) -> None:
    """Hard restriction preventing accidental use as an external promoter.

    This is only a guardrail for tests. It is not a production trust boundary:
    an agent can create an arbitrary synthetic root and is already trusted to
    execute anything inside that sandbox.
    """
    temp_root = Path(tempfile.gettempdir()).absolute()
    if (not root.is_absolute() or root.parent != temp_root
            or not root.name.startswith("checker-fixture-")):
        raise ContractError("Only named Python TemporaryDirectory fixture roots allowed")
    check_plain_chain(root)
    marker = root / ".synthetic-only"
    check_plain_chain(marker)
    if not marker.is_file() or marker.read_text(encoding="utf-8") != CANARY:
        raise ContractError("Missing exact synthetic-fixture canary")
    paths = [p for p in (target, source.root if source else None) if p is not None]
    if source is not None and target is not None and (
        source.root.is_relative_to(target) or target.is_relative_to(source.root)
    ):
        raise ContractError("Review snapshot and target must be disjoint")
    for path in paths:
        if not path.is_absolute() or not path.is_relative_to(root) or path == root:
            raise ContractError("Source, review and destination must stay inside synthetic root")
        check_plain_chain(path)


def _write_fsynced(path: Path, data: bytes) -> None:
    with path.open("xb") as fd:
        fd.write(data)
        fd.flush()
        os.fsync(fd.fileno())


def _journal_path(operation_directory: Path) -> Path:
    return operation_directory / "journal.json"


def _save_journal(op_dir: Path, document: dict) -> None:
    path = _journal_path(op_dir)
    tmp = op_dir / "journal.pending"
    with tmp.open("wb") as handle:
        handle.write(json.dumps(document, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8"))
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)
    _sync_directory(op_dir)


def _sync_directory(path: Path) -> None:
    if os.name != "posix":
        return
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _load_journal(operation_directory: Path) -> dict:
    doc = json.loads(_journal_path(operation_directory).read_text(encoding="utf-8"))
    if doc.get("state") not in STATUSES:
        raise ContractError("Invalid fixture journal state")
    if not isinstance(doc.get("changes"), list) or not isinstance(doc.get("operation_id"), str):
        raise ContractError("Invalid fixture journal")
    return doc


def _current_bytes(path: Path) -> bytes | None:
    if path.is_symlink():
        raise ContractError(f"Link refused during transaction: {path}")
    if not path.exists():
        return None
    check_plain_chain(path)
    if not path.is_file():
        raise ContractError(f"Destination no longer a file: {path}")
    return read_stable_file(path)


def _atomic_write(path: Path, data: bytes, mode: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    check_plain_chain(path.parent)
    temporary = path.parent / (".checker-fixture-" + uuid.uuid4().hex)
    try:
        _write_fsynced(temporary, data)
        if mode is not None:
            temporary.chmod(mode)
        os.replace(temporary, path)
        _sync_directory(path.parent)
    finally:
        temporary.unlink(missing_ok=True)


def prepare_fixture_transaction(
    fixture_root: Path, registration: Registration,
    source_roots: tuple[Path, ...], snapshot: Snapshot,
    policy_store: PolicyStore, captured_policies: CapturedPolicies,
    preview: TargetPreview, previously_managed: tuple[str, ...],
    *, test_only_approval_fingerprint: str,
) -> FixtureTransaction:
    """Prepare bytes and backups; no target modifications. NO production approval.

    Input has to be explicitly reviewed test preview fingerprint; stale source,
    policies, target, snapshots and conflicting coverage all refuse.
    """
    target = Path(preview.target_root)
    fixture_scope(fixture_root, source=snapshot, target=target)
    if (not policy_store.root.is_relative_to(fixture_root)
            or policy_store.root.is_relative_to(target)):
        raise ContractError("Fixture policy store must be independent and inside test root")
    if not registration.target_root or registration.target_root != str(target):
        raise ContractError("Wrong registration / destination")
    if not isinstance(test_only_approval_fingerprint, str) or test_only_approval_fingerprint != preview.fingerprint:
        raise ContractError("Synthetic review fingerprint not explicitly matched")
    if (not source_roots or any(
            not p.is_absolute() or not p.is_relative_to(fixture_root) for p in source_roots
        ) or any(not Path(sel.source).is_relative_to(fixture_root) for sel in registration.selections)):
        raise ContractError("Synthetic source roots/selections must remain inside fixture")
    if not unchanged_since_snapshot(registration, source_roots, snapshot):
        raise ContractError("Source differs from reviewed bytes")
    if not policy_store.still_current(registration, captured_policies):
        raise ContractError("Policy/registration changed after review")
    fresh = build_target_preview(snapshot, target, previously_managed)
    if fresh != preview:
        raise ContractError("Destination/approved plan changed since preview")

    txroot = fixture_root / "_fixture_transactions"
    if (target.is_relative_to(txroot) or snapshot.root.is_relative_to(txroot)
            or txroot.is_relative_to(target)):
        raise ContractError("Transaction staging overlaps fixture target/review")
    txroot.mkdir(exist_ok=True)
    check_plain_chain(txroot)
    operation_id = uuid.uuid4().hex
    op = txroot / operation_id
    op.mkdir(exist_ok=False)
    try:
        (op / "before").mkdir()
        (op / "after").mkdir()
        records = []
        before_files, before_directories = _read_tree(target)
        before_manifest = {path: digest(data) for path, data in before_files.items()}
        before_dirs = set(before_directories)
        for idx, change in enumerate(preview.changes):
            relative_target(change.relative_path)
            item = {
                "kind": change.kind,
                "relative_path": change.relative_path,
                "before_sha256": change.before_sha256,
                "after_sha256": change.after_sha256,
                "before_size": change.before_size,
                "after_size": change.after_size,
                "before_backup": None,
                "after_stage": None,
                "mode": None,
            }
            current = _current_bytes(target / change.relative_path)
            if (digest(current) if current is not None else None) != change.before_sha256:
                raise ContractError("Preimage no longer matches preview")
            if current is not None:
                item["mode"] = stat.S_IMODE((target / change.relative_path).stat().st_mode)
            if change.kind in ("delete", "modify"):
                backup = f"{idx:05d}.before"
                assert current is not None
                _write_fsynced(op / "before" / backup, current)
                item["before_backup"] = backup
            if change.kind in ("create", "modify"):
                record = next((record for record in snapshot.records
                               if record.target_relative == change.relative_path), None)
                if record is None:
                    raise ContractError("Missing source snapshot for planned destination")
                candidate_bytes = read_stable_file(snapshot.root / record.snapshot_relative)
                if digest(candidate_bytes) != change.after_sha256:
                    raise ContractError("Snapshot diverged while preparing transaction")
                stage = f"{idx:05d}.after"
                _write_fsynced(op / "after" / stage, candidate_bytes)
                item["after_stage"] = stage
            records.append(item)
        _sync_directory(op / "before")
        _sync_directory(op / "after")
        _save_journal(op, {
            "operation_id": operation_id, "state": "PREPARED", "applied_count": 0,
            "target": str(target), "preview_fingerprint": preview.fingerprint,
            "source_snapshot_id": snapshot.snapshot_id, "source_fingerprint": snapshot.registration_sha256,
            "policy_fingerprint": captured_policies.combined_sha256,
            "target_preimage_sha256": preview.target_inventory_sha256,
            "previously_managed": list(previously_managed), "changes": records,
            "original_directories": sorted(before_dirs),
            "original_files_sha256": before_manifest,
        })
        return FixtureTransaction(operation_id, op, preview.fingerprint)
    except BaseException:
        shutil.rmtree(op)
        raise


def _verify_record(op: Path, item: dict) -> None:
    before = item["before_backup"]
    after = item["after_stage"]
    if before:
        data = read_stable_file(op / "before" / before)
        if digest(data) != item["before_sha256"]:
            raise ContractError("Backup digest mismatch")
    if after:
        data = read_stable_file(op / "after" / after)
        if digest(data) != item["after_sha256"]:
            raise ContractError("Staged digest mismatch")


def _check_preimage(target: Path, item: dict) -> None:
    current = _current_bytes(target / item["relative_path"])
    if (digest(current) if current is not None else None) != item["before_sha256"]:
        raise ContractError("Target changed since synthetic approval")


def _apply_item(target: Path, op: Path, item: dict) -> None:
    path = target / item["relative_path"]
    _check_preimage(target, item)
    kind = item["kind"]
    if kind == "unchanged":
        return
    if kind in ("create", "modify"):
        data = read_stable_file(op / "after" / item["after_stage"])
        _atomic_write(path, data, item["mode"])
    elif kind == "delete":
        path.unlink()
        _sync_directory(path.parent)
    else:
        raise ContractError(f"Invalid change kind: {kind}")
    value = _current_bytes(path)
    if (digest(value) if value is not None else None) != item["after_sha256"]:
        raise ContractError("Target readback differs from staged approved bytes")


def _remove_new_empty_directories(target: Path, journal: dict) -> None:
    originals = set(journal["original_directories"])
    parents = set()
    for item in journal["changes"]:
        relative = Path(item["relative_path"])
        for parent in relative.parents:
            if parent != Path("."):
                parents.add(parent.as_posix())
    for rel in sorted(parents, key=lambda p: (-p.count("/"), -len(p))):
        if rel in originals:
            continue
        path = target / rel
        if path.is_dir() and not path.is_symlink():
            try:
                path.rmdir()
            except OSError:
                pass  # Might contain owner files; never force-delete.


def recover_fixture_transaction(fixture_root: Path, operation: FixtureTransaction,
                                *, rollback_completed: bool = False) -> str:
    """Rollback from durable preimages. Unexpected third-party edits => BLOCKED."""
    op = operation.operation_directory
    fixture_scope(fixture_root)
    if (op.parent != fixture_root / "_fixture_transactions"
            or op.name != operation.operation_id):
        raise ContractError("Operation identity mismatch")
    check_plain_chain(op)
    doc = _load_journal(op)
    target = Path(doc["target"])
    fixture_scope(fixture_root, target=target)
    if doc["operation_id"] != operation.operation_id:
        raise ContractError("Operation identity mismatch")
    if doc["state"] in ("ROLLED_BACK", "ROLLED_BACK_WITH_EXTERNAL_DRIFT"):
        return doc["state"]
    if doc["state"] == "COMPLETED" and not rollback_completed:
        return "COMPLETED"
    if doc["state"] not in ("PREPARED", "APPLYING", "COMPLETED", "RECOVERY_BLOCKED"):
        raise ContractError("Cannot recover this transaction state")

    # Validate all paths, preimages and backup files BEFORE modifying any target.
    for item in doc["changes"]:
        relative_target(item["relative_path"])
        _verify_record(op, item)
        current = _current_bytes(target / item["relative_path"])
        now = digest(current) if current is not None else None
        if (doc["state"] == "PREPARED" and now != item["before_sha256"]):
            # No target write can be attributed to this operation yet.
            # Never turn an independent owner edit into our own rollback.
            doc["state"] = "RECOVERY_BLOCKED"
            _save_journal(op, doc)
            return "RECOVERY_BLOCKED"
        if now not in (item["before_sha256"], item["after_sha256"]):
            doc["state"] = "RECOVERY_BLOCKED"
            _save_journal(op, doc)
            return "RECOVERY_BLOCKED"
    try:
        for item in reversed(doc["changes"]):
            path = target / item["relative_path"]
            current = _current_bytes(path)
            now = digest(current) if current is not None else None
            if now == item["before_sha256"]:
                continue
            if item["before_sha256"] is None:
                path.unlink()
                _sync_directory(path.parent)
            else:
                data = read_stable_file(op / "before" / item["before_backup"])
                _atomic_write(path, data, item["mode"])
            original = _current_bytes(path)
            if (digest(original) if original is not None else None) != item["before_sha256"]:
                raise ContractError("Recovery readback failure")
        _remove_new_empty_directories(target, doc)
        final_files, final_dirs = _read_tree(target)
        # Never delete unrelated owner modifications to make the full
        # destination look equal to the original. Report residual drift.
        full_restore = (
            {name: digest(data) for name, data in final_files.items()}
            == doc["original_files_sha256"]
            and set(final_dirs) == set(doc["original_directories"])
        )
        doc["state"] = "ROLLED_BACK" if full_restore else "ROLLED_BACK_WITH_EXTERNAL_DRIFT"
        _save_journal(op, doc)
        return doc["state"]
    except Exception:
        doc["state"] = "RECOVERY_BLOCKED"
        _save_journal(op, doc)
        raise


def apply_fixture_transaction(
    fixture_root: Path, operation: FixtureTransaction, registration: Registration,
    source_roots: tuple[Path, ...], snapshot: Snapshot,
    policy_store: PolicyStore, captured_policies: CapturedPolicies,
    *, approved_preview_fingerprint: str,
    inject_error_after: int | None = None,
    inject_crash_after: int | None = None,
) -> str:
    """Synthetic fixture only; no trusted run is ever emitted or authorized."""
    fixture_scope(fixture_root)
    if (operation.operation_directory.parent != fixture_root / "_fixture_transactions"
            or operation.operation_directory.name != operation.operation_id):
        raise ContractError("Operation identity mismatch")
    check_plain_chain(operation.operation_directory)
    doc = _load_journal(operation.operation_directory)
    target = Path(doc["target"])
    fixture_scope(fixture_root, source=snapshot, target=target)
    if doc["state"] != "PREPARED":
        raise ContractError("Transaction already started or terminal")
    if (doc["operation_id"] != operation.operation_id
            or doc["preview_fingerprint"] != operation.fingerprint
            or approved_preview_fingerprint != operation.fingerprint):
        raise ContractError("Test approval not bound to prepared transaction")
    if (not source_roots
            or any(not root.is_absolute() or not root.is_relative_to(fixture_root) for root in source_roots)
            or any(not Path(item.source).is_relative_to(fixture_root) for item in registration.selections)):
        raise ContractError("Synthetic source outside the fixture")
    if (doc["source_snapshot_id"] != snapshot.snapshot_id
            or doc["source_fingerprint"] != registration.fingerprint()
            or doc["policy_fingerprint"] != captured_policies.combined_sha256
            or not unchanged_since_snapshot(registration, source_roots, snapshot)
            or not policy_store.still_current(registration, captured_policies)):
        raise ContractError("Source, registration or policy stale before synthetic apply")

    for item in doc["changes"]:
        _verify_record(operation.operation_directory, item)
    current = build_target_preview(snapshot, target, tuple(doc["previously_managed"]))
    if current.fingerprint != approved_preview_fingerprint:
        raise ContractError("Real target changed after preview")

    doc["state"] = "APPLYING"
    _save_journal(operation.operation_directory, doc)
    try:
        for number, item in enumerate(doc["changes"], 1):
            _apply_item(target, operation.operation_directory, item)
            # Checkpoints are durable; recovery inspects all touched paths anyway,
            # including a crash between OS replacement and journal update.
            doc["applied_count"] = number
            _save_journal(operation.operation_directory, doc)
            if inject_crash_after == number:
                raise SimulatedInterruption("Simulated hard crash between operations")
            if inject_error_after == number:
                raise OSError("Synthetic I/O failure after applying change")
        # Verify the complete target inventory. Not just changed files: owner-only
        # data must still have identical bytes and empty folders must remain.
        final_files, final_dirs = _read_tree(target)
        expected_files = dict(doc["original_files_sha256"])
        expected_dirs = set(doc["original_directories"])
        for item in doc["changes"]:
            rel = item["relative_path"]
            if item["after_sha256"] is None:
                expected_files.pop(rel, None)
            else:
                expected_files[rel] = item["after_sha256"]
            if item["kind"] in ("create", "modify"):
                for parent in Path(rel).parents:
                    if parent != Path("."):
                        expected_dirs.add(parent.as_posix())
        if ({name: digest(payload) for name, payload in final_files.items()} != expected_files
                or set(final_dirs) != expected_dirs):
            raise ContractError("Full destination inventory differs from approved plan")
        doc["state"] = "COMPLETED"
        _save_journal(operation.operation_directory, doc)
        return "COMPLETED"
    except Exception:
        result = recover_fixture_transaction(fixture_root, operation)
        if result not in ("ROLLED_BACK", "ROLLED_BACK_WITH_EXTERNAL_DRIFT"):
            raise ContractError("Fixture update failed AND recovery is blocked") from None
        raise
