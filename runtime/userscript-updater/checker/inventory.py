"""Strict no-follow source inventory and immutable bytes snapshot for scanning."""
from __future__ import annotations

import hashlib
import json
import os
import stat
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path

from .model import ContractError, Registration, relative_target


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def is_reparse(meta: os.stat_result) -> bool:
    return bool(getattr(meta, "st_file_attributes", 0) & 0x400)


def check_plain_chain(path: Path) -> None:
    # Reject symlinks, Windows junctions/reparse points along selected path.
    for ancestor in [*reversed(path.parents), path]:
        try:
            meta = ancestor.lstat()
        except FileNotFoundError as exc:
            raise ContractError(f"Missing path: {ancestor}") from exc
        if stat.S_ISLNK(meta.st_mode) or is_reparse(meta):
            raise ContractError(f"Link/reparse point refused: {ancestor}")


def under(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def validate_source(path: Path, source_roots: tuple[Path, ...]) -> None:
    if not any(under(path, root) for root in source_roots):
        raise ContractError(f"Source outside allowlisted roots: {path}")
    check_plain_chain(path)


def selected_files(reg: Registration, source_roots: tuple[Path, ...]):
    reg.validate()
    seen_destinations: set[str] = set()
    seen_sources: set[str] = set()
    for i, entry in enumerate(reg.selections):
        source = Path(entry.source)
        validate_source(source, source_roots)
        if entry.kind == "file":
            if not source.is_file():
                raise ContractError("Selected file is not a regular file")
            candidates = [(source, Path(source.name))]
        else:
            if not source.is_dir():
                raise ContractError("Selected directory is not a directory")
            candidates = []
            for base, dirs, files in os.walk(source, followlinks=False):
                base_path = Path(base)
                check_plain_chain(base_path)
                for child in sorted(dirs):
                    check_plain_chain(base_path / child)
                for child in sorted(files):
                    candidates.append((base_path / child, (base_path / child).relative_to(source)))
        if not candidates:
            raise ContractError(f"Empty selection: {source}")
        for path, relative in sorted(candidates):
            check_plain_chain(path)
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_nlink > 1:
                raise ContractError(f"Non-regular file or hardlink refused: {path}")
            if str(path) in seen_sources:
                raise ContractError(f"Overlapping selections: {path}")
            seen_sources.add(str(path))
            destination = None
            if reg.target_root is not None:
                if entry.kind == "file":
                    destination = relative_target(entry.target or "")
                else:
                    destination = relative_target((entry.target or "") + "/" + relative.as_posix())
                key = destination.casefold()
                if key in seen_destinations:
                    raise ContractError(f"Duplicate target: {destination}")
                seen_destinations.add(key)
            yield i, path, relative.as_posix(), destination


@dataclass(frozen=True)
class FileRecord:
    selection_index: int
    source_path: str
    source_relative: str
    target_relative: str | None
    sha256: str
    size: int
    snapshot_relative: str


@dataclass(frozen=True)
class Snapshot:
    snapshot_id: str
    root: Path
    records: tuple[FileRecord, ...]

    def manifest(self) -> list[dict]:
        return [asdict(record) for record in self.records]


def make_snapshot(reg: Registration, source_roots: tuple[Path, ...], review_dir: Path) -> Snapshot:
    """Review dir must be protected in the installed application (NOT protected in Repo)."""
    review_dir.mkdir(parents=True, exist_ok=True)
    uid = str(uuid.uuid4())
    destination = review_dir / uid
    destination.mkdir(mode=0o700)
    records = []
    try:
        for i, path, rel, target in selected_files(reg, source_roots):
            # Snapshot names do not include untrusted project path components.
            saved_rel = f"{len(records):06d}.bin"
            with path.open("rb") as handle:
                data = handle.read()
            recorded = FileRecord(i, str(path), rel, target, digest(data), len(data), saved_rel)
            (destination / saved_rel).write_bytes(data)
            records.append(recorded)
        manifest_bytes = json.dumps([asdict(r) for r in records], sort_keys=True, ensure_ascii=False).encode()
        (destination / "manifest.json").write_bytes(manifest_bytes)
        return Snapshot(uid, destination, tuple(records))
    except BaseException:
        import shutil
        shutil.rmtree(destination)
        raise


def manifest_current(reg: Registration, source_roots: tuple[Path, ...]) -> list[dict]:
    current = []
    for i, path, rel, target in selected_files(reg, source_roots):
        with path.open("rb") as handle:
            data = handle.read()
        current.append(dict(selection_index=i, source_path=str(path), source_relative=rel,
                            target_relative=target, sha256=digest(data), size=len(data)))
    return current


def unchanged_since_snapshot(reg: Registration, source_roots: tuple[Path, ...], snap: Snapshot) -> bool:
    try:
        current = manifest_current(reg, source_roots)
        stored = [{k: v for k, v in asdict(r).items() if k != "snapshot_relative"} for r in snap.records]
        return current == stored
    except (OSError, ContractError):
        return False
