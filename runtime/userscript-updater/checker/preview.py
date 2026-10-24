"""Read-only target change preview. Never writes destination files.

Dev-only / synthetic trees. Trust-boundary and approval/recovery must be
provided by a future independently installed Windows application.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path

from .inventory import Snapshot, check_plain_chain, digest, read_stable_file
from .model import ContractError, relative_target

MAX_DIFF_BYTES = 512 * 1024
TEXT_SUFFIXES = {".js", ".jsx", ".ts", ".tsx", ".py", ".json",
                 ".txt", ".md", ".css", ".html", ".yaml", ".yml"}


@dataclass(frozen=True)
class Change:
    kind: str  # create, modify, delete, unchanged
    relative_path: str
    before_sha256: str | None
    after_sha256: str | None
    before_size: int | None
    after_size: int | None
    text_diff: str | None
    diff_note: str | None


@dataclass(frozen=True)
class TargetPreview:
    target_root: str
    changes: tuple[Change, ...]
    preserved: tuple[str, ...]
    target_inventory_sha256: str
    fingerprint: str
    # A preview has NO approval power and cannot be passed to a promoter.


def _read_tree(root: Path) -> dict[str, bytes]:
    if not root.exists() and not root.is_symlink():
        parent = root.parent
        while not parent.exists():
            if parent == parent.parent:
                raise ContractError("No inspectable target root ancestor")
            parent = parent.parent
        check_plain_chain(parent)
        return {}
    check_plain_chain(root)
    if not root.is_dir():
        raise ContractError("Target root must be a directory")
    files: dict[str, bytes] = {}

    def onerror(exc: OSError) -> None:
        raise ContractError(f"Target listing failed: {exc}") from exc

    for base, folders, names in os.walk(root, followlinks=False, topdown=True, onerror=onerror):
        current = Path(base)
        check_plain_chain(current)
        for name in folders:
            check_plain_chain(current / name)
        for name in names:
            file = current / name
            check_plain_chain(file)
            info = file.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise ContractError(f"Non-regular/hardlinked target file: {file}")
            rel = relative_target(file.relative_to(root).as_posix())
            key = rel.casefold()
            if any(old.casefold() == key for old in files):
                raise ContractError("Case-folded target path collision")
            files[rel] = read_stable_file(file)
    return files


def _text_diff(relative_path: str, old: bytes | None, new: bytes | None) -> tuple[str | None, str | None]:
    if Path(relative_path).suffix.lower() not in TEXT_SUFFIXES:
        return None, "Non-text or unknown suffix; compare sizes and hashes"
    if max(len(old or b""), len(new or b"")) > MAX_DIFF_BYTES:
        return None, "Text too large for in-app diff; inspect hashes and content separately"
    try:
        a = (old or b"").decode("utf-8").splitlines(keepends=True)
        b = (new or b"").decode("utf-8").splitlines(keepends=True)
    except UnicodeDecodeError:
        return None, "Not valid UTF-8; compare sizes and hashes"
    return "".join(difflib.unified_diff(a, b, fromfile="approved-before", tofile="candidate-after")), None


def _change(kind: str, rel: str, before: bytes | None, after: bytes | None) -> Change:
    diff, note = _text_diff(rel, before, after) if kind != "unchanged" else (None, None)
    return Change(kind, rel, digest(before) if before is not None else None,
                  digest(after) if after is not None else None,
                  len(before) if before is not None else None,
                  len(after) if after is not None else None, diff, note)


def build_target_preview(
    snapshot: Snapshot, target_root: Path, previously_managed: tuple[str, ...]
) -> TargetPreview:
    """Prepare complete read-only plan for one destination root.

    Deletions limited to explicitly previously managed paths. Existing data
    outside that scope remains untouched. A new registration must not silently
    adopt an existing unmanaged target path. Snapshot source bytes are read only.
    """
    if not target_root.is_absolute() or ".." in target_root.parts:
        raise ContractError("Target root must be absolute without traversal")
    earlier = [relative_target(path) for path in previously_managed]
    if len({name.casefold() for name in earlier}) != len(earlier):
        raise ContractError("Duplicate previously managed paths")
    actual = _read_tree(target_root)
    keys = {name.casefold(): name for name in actual}
    desired: dict[str, bytes] = {}
    for record in snapshot.records:
        if record.target_relative is None:
            raise ContractError("Check-only snapshot cannot be updated")
        rel = relative_target(record.target_relative)
        if any(other.casefold() == rel.casefold() for other in desired):
            raise ContractError(f"Duplicate desired destination: {rel}")
        path = snapshot.root / record.snapshot_relative
        check_plain_chain(path)
        data = read_stable_file(path)
        if digest(data) != record.sha256 or len(data) != record.size:
            raise ContractError(f"Tampered review snapshot: {path}")
        desired[rel] = data

    old_managed = {name.casefold() for name in earlier}
    for path in desired:
        if path.casefold() in keys and path.casefold() not in old_managed:
            raise ContractError(f"Unmanaged target collision requires explicit adoption: {path}")
    # A file cannot be both a target and a parent directory for another file.
    union = [*desired, *actual]
    for path in desired:
        for other in union:
            if path.casefold() != other.casefold() and (
                other.casefold().startswith(path.casefold() + "/")
                or (other in actual and path.casefold().startswith(other.casefold() + "/"))
            ):
                raise ContractError(f"File/directory overlap in target plan: {path}, {other}")

    changes: list[Change] = []
    for rel in sorted(desired, key=str.casefold):
        before = actual.get(keys[rel.casefold()]) if rel.casefold() in keys else None
        new = desired[rel]
        status = "create" if before is None else ("unchanged" if before == new else "modify")
        changes.append(_change(status, rel, before, new))
    for old in sorted(earlier, key=str.casefold):
        if old.casefold() not in {name.casefold() for name in desired} and old.casefold() in keys:
            real_name = keys[old.casefold()]
            changes.append(_change("delete", real_name, actual[real_name], None))

    managed_now = {name.casefold() for name in earlier} | {name.casefold() for name in desired}
    preserved = tuple(sorted((name for name in actual if name.casefold() not in managed_now),
                             key=str.casefold))
    target_manifest = [(name, digest(content), len(content))
                       for name, content in sorted(actual.items(), key=lambda entry: entry[0].casefold())]
    target_digest = digest(json.dumps(target_manifest, ensure_ascii=False, sort_keys=True).encode("utf-8"))
    action_fields = [
        (item.kind, item.relative_path, item.before_sha256, item.after_sha256, item.before_size, item.after_size)
        for item in changes
    ]
    fingerprint = hashlib.sha256(json.dumps(
        [snapshot.snapshot_id, snapshot.registration_sha256, str(target_root),
         target_digest, action_fields, preserved], ensure_ascii=False,
        sort_keys=True).encode("utf-8")).hexdigest()
    return TargetPreview(str(target_root), tuple(changes), preserved, target_digest, fingerprint)
