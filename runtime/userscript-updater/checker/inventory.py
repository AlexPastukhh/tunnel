"""Conservative source inventory and review snapshots; NOT a Windows OS security boundary."""
from __future__ import annotations

import hashlib
import json
import os
import stat
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path

from .model import ContractError, Registration, relative_target

# Candidate defaults: an oversized/unhandled selection is ERROR, never silently skipped.
MAX_FILES = 10000
MAX_FILE_BYTES = 50 * 1024 * 1024
MAX_TOTAL_BYTES = 250 * 1024 * 1024


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def is_reparse(meta: os.stat_result) -> bool:
    return bool(getattr(meta, "st_file_attributes", 0) & 0x400)


def check_plain_chain(path: Path) -> None:
    if os.name == "nt":
        from .windows_io import native_io
        native_io().validate(path)
        return
    if not path.is_absolute() or ".." in path.parts:
        raise ContractError("Paths must be absolute and have no traversal components")
    for ancestor in [*reversed(path.parents), path]:
        try:
            meta = ancestor.lstat()
        except OSError as exc:
            raise ContractError(f"Cannot inspect path: {ancestor}: {exc}") from exc
        if stat.S_ISLNK(meta.st_mode) or is_reparse(meta):
            raise ContractError(f"Link/reparse point refused: {ancestor}")


def under(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def validate_source(path: Path, source_roots: tuple[Path, ...]) -> None:
    if not source_roots or not any(under(path, root) for root in source_roots):
        raise ContractError(f"Source outside trusted source roots: {path}")
    check_plain_chain(path)


def _same_or_child(a: str, b: str) -> bool:
    """Case-insensitive Windows-oriented target collision/ancestor check."""
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")


RESOURCE_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".bmp",
                     ".woff", ".woff2", ".ttf", ".txt", ".md", ".csv"}


@dataclass(frozen=True)
class DirectoryRecord:
    selection_index: int
    source_path: str
    source_relative: str
    target_relative: str | None


@dataclass(frozen=True)
class ExcludedRecord:
    selection_index: int
    source_path: str
    target_relative: str | None
    reason: str


@dataclass(frozen=True)
class MissingRecord:
    selection_index: int
    source_path: str
    target_relative: str | None
    kind: str


def selected_inventory(reg: Registration, source_roots: tuple[Path, ...]):
    """Inventory explicit owner selections, including empty dirs and exclusions."""
    reg.validate()
    candidates, directories, exclusions, missing = [], [], [], []
    seen_sources, target_keys, directory_keys = set(), [], set()
    for i, entry in enumerate(reg.selections):
        source = Path(entry.source)
        try:
            source.lstat()
        except FileNotFoundError:
            roots = [root for root in source_roots if under(source, root)]
            if not roots:
                raise ContractError("Missing source is outside declared source roots")
            for root in roots:
                check_plain_chain(root)  # A missing/unavailable whole source root is an error.
            ancestor = source.parent
            while True:
                try:
                    ancestor.lstat()
                    break
                except FileNotFoundError:
                    ancestor = ancestor.parent
            validate_source(ancestor, source_roots)
            if entry.content == "data":
                exclusions.append(ExcludedRecord(i, str(source), entry.target, "declared data; never copied/deleted"))
            else:
                missing.append(MissingRecord(i, str(source), entry.target, entry.kind))
            continue
        validate_source(source, source_roots)
        if entry.content == "data":
            exclusions.append(ExcludedRecord(i, str(source), entry.target, "declared data; never copied/deleted"))
            continue
        exclusions.extend(ExcludedRecord(i, str(source / rel),
            f"{entry.target}/{rel}" if reg.target_root else None, "explicit owner exclusion")
            for rel in entry.excluded_paths)
        source_files = []
        if entry.kind == "file":
            if not source.is_file():
                raise ContractError(f"Selected file not regular: {source}")
            source_files = [(source, source.name)]
        else:
            if not source.is_dir():
                raise ContractError(f"Selected directory not a directory: {source}")

            def walk_error(exc):
                raise ContractError(f"Cannot enumerate {exc.filename}: {exc}") from exc

            for base, dirs, files in os.walk(source, topdown=True, followlinks=False, onerror=walk_error):
                base_path = Path(base)
                check_plain_chain(base_path)
                relative_dir = base_path.relative_to(source).as_posix()
                mapped_dir = (entry.target if relative_dir == "." else f"{entry.target}/{relative_dir}") if reg.target_root else None
                key = os.path.normcase(str(base_path))
                if key in directory_keys:
                    raise ContractError(f"Overlapping selected directories: {base_path}")
                directory_keys.add(key)
                directories.append(DirectoryRecord(i, str(base_path), relative_dir, mapped_dir))
                if len(directories) + len(candidates) > MAX_FILES:
                    raise ContractError("Selection exceeds explicit entry-count limit")
                for name in sorted([*dirs, *files]):
                    path = base_path / name
                    relative = path.relative_to(source).as_posix()
                    if relative in entry.excluded_paths:
                        # The omission is explicit and fingerprinted, never treated as scanned.
                        if name in dirs:
                            dirs.remove(name)
                        continue
                    check_plain_chain(path)
                    if name in files:
                        source_files.append((path, relative))
        for path, relative in sorted(source_files, key=lambda item: str(item[0])):
            check_plain_chain(path)
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise ContractError(f"Non-regular file or hardlink refused: {path}")
            if entry.content == "resource" and path.suffix.lower() not in RESOURCE_SUFFIXES:
                raise ContractError(f"Resource type is not in the inert-resource profile: {path}")
            key_source = os.path.normcase(str(path))
            if key_source in seen_sources:
                raise ContractError(f"Overlapping selections: {path}")
            seen_sources.add(key_source)
            target = None
            if reg.target_root is not None:
                target = relative_target(entry.target if entry.kind == "file" else f"{entry.target}/{relative}")
                key_target = target.casefold()
                if any(_same_or_child(key_target, previous) for previous in target_keys):
                    raise ContractError(f"Target collision/ancestor conflict: {target}")
                target_keys.append(key_target)
            candidates.append((i, path, relative, target))
            if len(candidates) + len(directories) > MAX_FILES:
                raise ContractError("Selection exceeds explicit entry-count limit")
        if len(directories) > MAX_FILES:
            raise ContractError("Selection exceeds explicit directory-count limit")
    mapped_dirs = [relative_target(d.target_relative) for d in directories if d.target_relative]
    if len({d.casefold() for d in mapped_dirs}) != len(mapped_dirs):
        raise ContractError("Duplicate mapped directory")
    for d in mapped_dirs:
        if any(d.casefold() == f or d.casefold().startswith(f + "/") for f in target_keys):
            raise ContractError("Mapped directory collides with a target file")
    return candidates, tuple(directories), tuple(exclusions), tuple(missing)


def selected_files(reg: Registration, source_roots: tuple[Path, ...]):
    yield from selected_inventory(reg, source_roots)[0]


def read_stable_file(path: Path) -> bytes:
    """No-follow where OS supports it; inode + metadata check; not an OS-level race guarantee."""
    if os.name == "nt":
        from .windows_io import native_io
        return native_io().read(path)
    check_plain_chain(path)
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise ContractError(f"Not a plain single-link file: {path}")
    if before.st_size > MAX_FILE_BYTES:
        raise ContractError(f"File exceeds limit: {path}")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise ContractError(f"File open failed: {path}: {exc}") from exc
    with os.fdopen(fd, "rb") as stream:
        opened = os.fstat(stream.fileno())
        if (not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1
                or (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino)):
            raise ContractError(f"File changed before open: {path}")
        data = stream.read(MAX_FILE_BYTES + 1)
        after = os.fstat(stream.fileno())
    last = path.lstat()
    relevant = lambda info: (
        info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns
    )
    if len(data) > MAX_FILE_BYTES or relevant(before) != relevant(after) or relevant(before) != relevant(last):
        raise ContractError(f"File changed while reading: {path}")
    return data


@dataclass(frozen=True)
class FileRecord:
    selection_index: int
    source_path: str
    source_relative: str
    target_relative: str | None
    sha256: str
    size: int
    snapshot_relative: str
    content: str = "code"


@dataclass(frozen=True)
class Snapshot:
    snapshot_id: str
    root: Path
    registration_sha256: str
    records: tuple[FileRecord, ...]
    directories: tuple[DirectoryRecord, ...] = ()
    exclusions: tuple[ExcludedRecord, ...] = ()
    missing: tuple[MissingRecord, ...] = ()

    def manifest(self) -> list[dict]:
        return ([asdict(record) for record in self.records]
                + [dict(entry_type="directory", **asdict(d)) for d in self.directories]
                + [dict(entry_type="excluded", **asdict(e)) for e in self.exclusions]
                + [dict(entry_type="missing", **asdict(m)) for m in self.missing])


def source_records(reg: Registration, source_roots: tuple[Path, ...]):
    """Complete current inventory; caller must enforce machine-specific secure handles."""
    records = []
    total_size = 0
    for i, path, relative, target in selected_files(reg, source_roots):
        data = read_stable_file(path)
        total_size += len(data)
        if total_size > MAX_TOTAL_BYTES:
            raise ContractError("Selected bytes exceed explicit total-size limit")
        records.append((i, path, relative, target, data))
    return records


def make_snapshot(reg: Registration, source_roots: tuple[Path, ...], review_dir: Path) -> Snapshot:
    """Provisional Linux fixture snapshot. Installed protected store/ACL still required."""
    for selection in reg.selections:
        if selection.kind == "directory" and under(review_dir, Path(selection.source)):
            raise ContractError("Review directory must not be within selected source")
    review_dir.mkdir(parents=True, exist_ok=True)
    check_plain_chain(review_dir)
    uid = str(uuid.uuid4())
    destination = review_dir / uid
    destination.mkdir(mode=0o700, exist_ok=False)
    records: list[FileRecord] = []
    _, directories, exclusions, missing = selected_inventory(reg, source_roots)
    try:
        total = 0
        for i, path, relative, target, data in source_records(reg, source_roots):
            total += len(data)
            if total > MAX_TOTAL_BYTES:
                raise ContractError("Snapshot too large")
            suffix = path.suffix.lower()
            # Original suffix is preserved for language recognition by scanners.
            if not suffix or len(suffix) > 12 or not suffix[1:].isascii() or not suffix[1:].isalnum():
                suffix = ".bin"
            saved = f"{len(records):06d}{suffix}"
            with (destination / saved).open("xb") as stream:
                stream.write(data)
            if digest((destination / saved).read_bytes()) != digest(data):
                raise ContractError("Snapshot readback mismatch")
            records.append(FileRecord(i, str(path), relative, target, digest(data), len(data), saved, reg.selections[i].content))
        snap = Snapshot(uid, destination, reg.fingerprint(), tuple(records), directories, exclusions, missing)
        manifest_bytes = json.dumps(snap.manifest(), sort_keys=True, ensure_ascii=False).encode()
        with (destination / "manifest.json").open("xb") as stream:
            stream.write(manifest_bytes)
        # Changes during enumeration/copy invalidate snapshot, not silently PASS.
        if not unchanged_since_snapshot(reg, source_roots, snap):
            raise ContractError("Source inventory changed during snapshot")
        return snap
    except BaseException:
        import shutil
        shutil.rmtree(destination)
        raise


def manifest_current(reg: Registration, source_roots: tuple[Path, ...]) -> list[dict]:
    files = [
        dict(selection_index=i, source_path=str(path), source_relative=rel,
             target_relative=target, sha256=digest(data), size=len(data), content=reg.selections[i].content)
        for i, path, rel, target, data in source_records(reg, source_roots)
    ]
    _, directories, exclusions, missing = selected_inventory(reg, source_roots)
    return (files + [dict(entry_type="directory", **asdict(d)) for d in directories]
            + [dict(entry_type="excluded", **asdict(e)) for e in exclusions]
            + [dict(entry_type="missing", **asdict(m)) for m in missing])


def unchanged_since_snapshot(reg: Registration, source_roots: tuple[Path, ...], snap: Snapshot) -> bool:
    if reg.fingerprint() != snap.registration_sha256:
        return False
    try:
        current = manifest_current(reg, source_roots)
        stored = [{k: v for k, v in row.items() if k != "snapshot_relative"} for row in snap.manifest()]
        return current == stored
    except (OSError, ContractError):
        return False
