"""Persistent promotion state; OS-bound target I/O is supplied separately.

Portable persistence is Docker-tested, not native Windows durable/ACL evidence.
"""
from __future__ import annotations

import json
import os
import uuid
from contextlib import contextmanager
from pathlib import Path

from .inventory import check_plain_chain, digest, read_stable_file
from .model import ContractError, relative_target


def encoded(value) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def token(value) -> str:
    return digest(encoded(value))


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ContractError("Duplicate promotion-state JSON key")
        result[key] = value
    return result


def load_json(path):
    if path.stat().st_size > 16 * 1024 * 1024:
        raise ContractError("Promotion state exceeds limit")
    return json.loads(read_stable_file(path), object_pairs_hook=_unique)


def sync_directory(path):
    if os.name == "posix":
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def atomic_bytes(path, raw):
    parent = path.parent
    ancestor = parent
    while not ancestor.exists():
        ancestor = ancestor.parent
    check_plain_chain(ancestor)
    parent.mkdir(parents=True, exist_ok=True)
    check_plain_chain(parent)
    if path.exists() or path.is_symlink():
        read_stable_file(path)
    temporary = parent / (".pending-" + uuid.uuid4().hex)
    try:
        with temporary.open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        sync_directory(parent)
    finally:
        temporary.unlink(missing_ok=True)


class ManagedStore:
    def __init__(self, root: Path):
        self.root = root
        self.path = root / "managed.json"

    def read(self):
        if not self.path.exists() and not self.path.is_symlink():
            return {"schema_version": 1, "entries": []}, None
        raw = read_stable_file(self.path)
        if len(raw) > 16 * 1024 * 1024:
            raise ContractError("Managed state exceeds limit")
        value = json.loads(raw, object_pairs_hook=_unique)
        self.validate(value)
        return value, digest(raw)

    @staticmethod
    def validate(value):
        if (not isinstance(value, dict) or set(value) != {"schema_version", "entries"}
                or value["schema_version"] != 1 or not isinstance(value["entries"], list)):
            raise ContractError("Invalid managed-state schema")
        seen = set()
        for row in value["entries"]:
            if (not isinstance(row, dict) or set(row) != {"project_id", "target_root", "files"}
                    or not isinstance(row["project_id"], str) or not row["project_id"]
                    or not Path(row["target_root"]).is_absolute() or ".." in Path(row["target_root"]).parts
                    or not isinstance(row["files"], list)):
                raise ContractError("Invalid managed-state entry")
            key = (row["project_id"], row["target_root"].casefold())
            if key in seen:
                raise ContractError("Duplicate managed-state entry")
            seen.add(key)
            paths = [relative_target(p) for p in row["files"]]
            if len({p.casefold() for p in paths}) != len(paths):
                raise ContractError("Duplicate managed paths")

    @contextmanager
    def lock(self):
        ancestor = self.root
        while not ancestor.exists():
            ancestor = ancestor.parent
        check_plain_chain(ancestor)
        self.root.mkdir(parents=True, exist_ok=True)
        check_plain_chain(self.root)
        path = self.root / "promotion.lock"
        if path.exists() or path.is_symlink():
            read_stable_file(path)
        fd = os.open(path, os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0), 0o600)
        try:
            if os.fstat(fd).st_nlink != 1:
                raise ContractError("Linked promotion lock refused")
            if os.fstat(fd).st_size == 0:
                os.write(fd, b"0")
            os.lseek(fd, 0, os.SEEK_SET)
            if os.name == "posix":
                import fcntl
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError as exc:
                    raise ContractError("Another promotion/recovery is active") from exc
            else:
                import msvcrt
                try:
                    msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                except OSError as exc:
                    raise ContractError("Another promotion/recovery is active") from exc
            yield
        finally:
            os.close(fd)  # OS releases the lock even after process termination.

    def write(self, value):
        self.validate(value)
        atomic_bytes(self.path, encoded(value))
