"""Temporary target adapter used ONLY by transaction unit tests, never imported by checker."""
import errno
import os
import stat
import tempfile
import uuid
from pathlib import Path

from checker.inventory import check_plain_chain, digest, read_stable_file
from checker.model import ContractError, relative_target
from checker.promotion_state import sync_directory


class SyntheticTarget:
    scope = "SYNTHETIC_TEST"

    def __init__(self, root):
        if root.parent != Path(tempfile.gettempdir()) or not root.name.startswith("checker-promotion-test-"):
            raise ContractError("Only named temporary test roots")
        self.root = root
        self.writes = []
        self.hook = None

    def authorize(self, target, settings):
        check_plain_chain(self.root)
        if target == self.root or not target.is_relative_to(self.root):
            raise ContractError("Synthetic adapter refuses nonfixture target")
        settings.check_target_isolation(str(target))
        if not settings.state_root.is_relative_to(self.root):
            raise ContractError("Synthetic state must share the private test root")

    def path(self, target, relative):
        path = target / relative_target(relative) if relative else target
        parent = path if path.exists() else path.parent
        while not parent.exists():
            parent = parent.parent
        check_plain_chain(parent)
        return path

    def read(self, target, relative):
        path = self.path(target, relative)
        return read_stable_file(path) if path.exists() or path.is_symlink() else None

    def metadata(self, target, relative):
        info = self.path(target, relative).stat()
        return dict(mode=stat.S_IMODE(info.st_mode), atime=info.st_atime_ns, mtime=info.st_mtime_ns)

    def replace(self, target, relative, data, metadata, *, expected_sha256):
        old = self.read(target, relative)
        if (digest(old) if old is not None else None) != expected_sha256:
            raise ContractError("Target compare-and-swap mismatch")
        path = self.path(target, relative)
        temporary = path.parent / (".promotion-test-" + uuid.uuid4().hex)
        try:
            with temporary.open("xb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            if metadata:
                temporary.chmod(metadata["mode"])
                os.utime(temporary, ns=(metadata["atime"], metadata["mtime"]))
            os.replace(temporary, path)
            sync_directory(path.parent)
        finally:
            temporary.unlink(missing_ok=True)
        self.writes.append((relative, bytes(data)))
        if self.hook:
            self.hook("replace", target, relative)

    def remove(self, target, relative, *, expected_sha256, expected_metadata=None):
        old = self.read(target, relative)
        if (digest(old) if old is not None else None) != expected_sha256:
            raise ContractError("Delete compare-and-swap mismatch")
        path = self.path(target, relative)
        path.unlink()
        sync_directory(path.parent)
        if self.hook:
            self.hook("remove", target, relative)

    def mkdir(self, target, relative):
        path = self.path(target, relative)
        path.mkdir()
        sync_directory(path.parent)
        info = path.stat()
        return [info.st_dev, info.st_ino]

    def rmdir_if_owned_empty(self, target, relative, identity):
        path = self.path(target, relative)
        if not path.exists():
            return
        info = path.stat()
        if [info.st_dev, info.st_ino] != identity:
            return
        try:
            path.rmdir()
            sync_directory(path.parent)
        except OSError as exc:
            if exc.errno not in (errno.ENOTEMPTY, errno.EEXIST):
                raise
