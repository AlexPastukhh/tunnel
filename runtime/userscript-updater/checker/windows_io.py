"""Native Windows handle I/O. Source candidate; run native acceptance before authority.

CreateFileW pins each ancestor without delete/write sharing; final-path + file-ID
and single-link checks reject aliases. Existing writes use the held file handle
and preserve its DACL/identity; they are journaled, not claimed atomic.
Microsoft: CreateFileW, GetFinalPathNameByHandleW, SetFileInformationByHandle.
"""
from __future__ import annotations

import base64
import ctypes as C
import os
from contextlib import contextmanager, ExitStack
from pathlib import Path

from .model import ContractError

U32, U64, HANDLE = C.c_uint32, C.c_uint64, C.c_void_p
INVALID = C.c_void_p(-1).value
READ, WRITE, DELETE = 0x80000000, 0x40000000, 0x10000
DIRECTORY, REPARSE = 0x10, 0x400
OPEN_EXISTING, CREATE_NEW = 3, 1


class FileTime(C.Structure):
    _fields_ = [("low", U32), ("high", U32)]


class Info(C.Structure):
    _fields_ = [("attributes", U32), ("creation", FileTime), ("access", FileTime),
                ("write", FileTime), ("volume", U32), ("size_high", U32), ("size_low", U32),
                ("links", U32), ("index_high", U32), ("index_low", U32)]


def _time(t):
    return (int(t.high) << 32) | int(t.low)


def _ft(value):
    return FileTime(value & 0xffffffff, value >> 32)


def _identity(info):
    return [int(info.volume), int(info.index_high), int(info.index_low)]


class WindowsIO:
    def __init__(self):
        if os.name != "nt":
            raise ContractError("Native Windows I/O is unavailable on this platform")
        self.k = C.WinDLL("kernel32", use_last_error=True)
        declarations = {
            "CreateFileW": ([C.c_wchar_p, U32, U32, HANDLE, U32, U32, HANDLE], HANDLE),
            "CloseHandle": ([HANDLE], C.c_int),
            "GetFileInformationByHandle": ([HANDLE, C.POINTER(Info)], C.c_int),
            "GetFinalPathNameByHandleW": ([HANDLE, C.c_wchar_p, U32, U32], U32),
            "ReadFile": ([HANDLE, C.c_void_p, U32, C.POINTER(U32), HANDLE], C.c_int),
            "WriteFile": ([HANDLE, C.c_void_p, U32, C.POINTER(U32), HANDLE], C.c_int),
            "SetFilePointerEx": ([HANDLE, C.c_int64, C.POINTER(C.c_int64), U32], C.c_int),
            "SetEndOfFile": ([HANDLE], C.c_int),
            "FlushFileBuffers": ([HANDLE], C.c_int),
            "SetFileTime": ([HANDLE, C.POINTER(FileTime), C.POINTER(FileTime), C.POINTER(FileTime)], C.c_int),
            "SetFileInformationByHandle": ([HANDLE, C.c_int, C.c_void_p, U32], C.c_int),
            "GetDriveTypeW": ([C.c_wchar_p], U32),
            "GetVolumeInformationW": ([C.c_wchar_p, C.c_wchar_p, U32, C.POINTER(U32),
                                      C.POINTER(U32), C.POINTER(U32), C.c_wchar_p, U32], C.c_int),
        }
        declarations["GetFileInformationByHandleEx"] = ([HANDLE, C.c_int, C.c_void_p, U32], C.c_int)
        self.a = C.WinDLL("advapi32", use_last_error=True)
        self.a.GetKernelObjectSecurity.argtypes = [HANDLE, U32, C.c_void_p, U32, C.POINTER(U32)]
        self.a.GetKernelObjectSecurity.restype = C.c_int
        self.a.SetKernelObjectSecurity.argtypes = [HANDLE, U32, C.c_void_p]
        self.a.SetKernelObjectSecurity.restype = C.c_int
        for name, (args, result) in declarations.items():
            function = getattr(self.k, name)
            function.argtypes, function.restype = args, result

    def checked(self, value, operation):
        if not value:
            raise ContractError(f"{operation}: {C.WinError(C.get_last_error())}")
        return value

    @staticmethod
    def path(path):
        value = str(path)
        if (not path.is_absolute() or not path.drive or len(path.drive) != 2
                or path.drive[1] != ":" or ".." in path.parts
                or value.startswith(("\\\\", "//"))):
            raise ContractError("Only absolute local Windows drive paths are supported")
        return "\\\\?\\" + value

    def _info(self, handle, path, *, directory=None):
        info = Info()
        self.checked(self.k.GetFileInformationByHandle(handle, C.byref(info)), "File identity")
        if info.attributes & REPARSE:
            raise ContractError(f"Reparse point refused: {path}")
        is_directory = bool(info.attributes & DIRECTORY)
        if directory is not None and is_directory != directory:
            raise ContractError(f"Unexpected file/directory type: {path}")
        if not is_directory and info.links != 1:
            raise ContractError(f"Hardlink refused: {path}")
        result = C.create_unicode_buffer(32768)
        size = self.k.GetFinalPathNameByHandleW(handle, result, len(result), 0)
        if not size or size >= len(result):
            raise ContractError("Cannot resolve final path")
        normalize = lambda s: s.rstrip("\\/").casefold()
        if normalize(result.value) != normalize(self.path(path)):
            raise ContractError(f"Final path/alias differs: {path}")
        return info

    @contextmanager
    def open(self, path, access=READ, disposition=OPEN_EXISTING, *, directory=None):
        handle = self.k.CreateFileW(self.path(path), access, 1, None, disposition,
                                    0x00200000 | 0x02000000, None)
        if handle == INVALID:
            error = C.get_last_error()
            raise OSError(error, str(C.WinError(error)), str(path))
        try:
            info = self._info(handle, path, directory=directory)
            if not info.attributes & DIRECTORY:
                self._streams(handle)
            yield handle, info
        finally:
            self.k.CloseHandle(handle)

    def _streams(self, handle):
        buffer = C.create_string_buffer(65536)
        self.checked(self.k.GetFileInformationByHandleEx(handle, 7, buffer, len(buffer)), "Inspect streams")
        offset = 0
        while True:
            next_offset = U32.from_buffer(buffer, offset).value
            name_bytes = U32.from_buffer(buffer, offset + 4).value
            if name_bytes % 2 or offset + 24 + name_bytes > len(buffer):
                raise ContractError("Invalid file stream information")
            name = buffer.raw[offset + 24:offset + 24 + name_bytes].decode("utf-16-le")
            if name != "::$DATA":
                raise ContractError("Alternate data streams are outside the accepted file profile")
            if not next_offset:
                break
            if next_offset < 24 or offset + next_offset >= len(buffer):
                raise ContractError("Invalid stream offset")
            offset += next_offset

    def security(self, handle):
        size = U32()
        self.a.GetKernelObjectSecurity(handle, 7, None, 0, C.byref(size))
        if not size.value or size.value > 65536:
            raise ContractError("Cannot inspect bounded file security descriptor")
        buffer = C.create_string_buffer(size.value)
        self.checked(self.a.GetKernelObjectSecurity(handle, 7, buffer, len(buffer), C.byref(size)),
                     "Capture file security")
        return base64.b64encode(buffer.raw[:size.value]).decode("ascii")

    @contextmanager
    def ancestors(self, path, *, include_leaf=False):
        path = Path(path)
        self.path(path)
        root = path.anchor
        if self.k.GetDriveTypeW(root) != 3:
            raise ContractError("Only fixed local volumes are supported")
        fs = C.create_unicode_buffer(64)
        self.checked(self.k.GetVolumeInformationW(root, None, 0, None, None, None, fs, len(fs)),
                     "Volume information")
        if fs.value != "NTFS":
            raise ContractError("Native update profile requires NTFS")
        directories = [*reversed(path.parents)]
        if include_leaf:
            directories.append(path)
        with ExitStack() as stack:
            for directory in directories:
                # FILE_LIST_DIRECTORY participates in share-mode protection.
                stack.enter_context(self.open(directory, 1 | 0x80, directory=True))
            yield

    def validate(self, path):
        path = Path(path)
        with self.ancestors(path):
            with self.open(path):
                pass

    def read_handle(self, handle, path):
        from .inventory import MAX_FILE_BYTES
        before = self._info(handle, path, directory=False)
        size = (int(before.size_high) << 32) | int(before.size_low)
        if size > MAX_FILE_BYTES:
            raise ContractError("File exceeds explicit size limit")
        self.checked(self.k.SetFilePointerEx(handle, 0, None, 0), "Seek")
        chunks, total = [], 0
        while True:
            buffer, count = C.create_string_buffer(1024 * 1024), U32()
            self.checked(self.k.ReadFile(handle, buffer, len(buffer), C.byref(count), None), "Read")
            if not count.value:
                break
            total += count.value
            if total > MAX_FILE_BYTES:
                raise ContractError("File exceeds explicit size limit")
            chunks.append(buffer.raw[:count.value])
        after = self._info(handle, path, directory=False)
        signature = lambda i: (_identity(i), i.size_high, i.size_low, _time(i.write), i.attributes)
        if signature(before) != signature(after) or total != size:
            raise ContractError("File changed during held-handle read")
        return b"".join(chunks)

    def hash(self, path, maximum=1024 * 1024 * 1024):
        import hashlib
        path = Path(path)
        with self.ancestors(path):
            with self.open(path, directory=False) as (handle, before):
                size = (int(before.size_high) << 32) | int(before.size_low)
                if size > maximum:
                    raise ContractError("Installed binary exceeds closure limit")
                hashed, total = hashlib.sha256(), 0
                while True:
                    buffer, count = C.create_string_buffer(1024 * 1024), U32()
                    self.checked(self.k.ReadFile(handle, buffer, len(buffer), C.byref(count), None), "Hash read")
                    if not count.value:
                        break
                    total += count.value
                    if total > maximum:
                        raise ContractError("Installed binary grew beyond closure limit")
                    hashed.update(buffer.raw[:count.value])
                after = self._info(handle, path, directory=False)
                if (_identity(before) != _identity(after) or _time(before.write) != _time(after.write)
                        or size != total or size != (int(after.size_high) << 32) | int(after.size_low)):
                    raise ContractError("Installed binary changed during hashing")
                return hashed.hexdigest(), total

    def read(self, path):
        path = Path(path)
        with self.ancestors(path):
            with self.open(path, directory=False) as (handle, _):
                return self.read_handle(handle, path)

    def metadata(self, path):
        path = Path(path)
        with self.ancestors(path):
            with self.open(path, directory=False) as (handle, info):
                if info.attributes & ~(0x27 | 0x80):
                    raise ContractError("Target attributes outside the supported metadata profile")
                return dict(identity=_identity(info), attributes=int(info.attributes),
                            creation=_time(info.creation), access=_time(info.access), write=_time(info.write), security=self.security(handle))

    def write(self, path, data, metadata, expected_sha256):
        from .inventory import digest
        path = Path(path)
        with self.ancestors(path):
            disposition = CREATE_NEW if expected_sha256 is None else OPEN_EXISTING
            access = READ | WRITE
            if metadata and expected_sha256 is None:
                access |= 0x40000 | 0x80000  # WRITE_DAC | WRITE_OWNER for deleted-file restoration
            with self.open(path, access, disposition, directory=False) as (handle, info):
                if expected_sha256 is not None and digest(self.read_handle(handle, path)) != expected_sha256:
                    raise ContractError("Native target compare-and-swap mismatch")
                if metadata and expected_sha256 is not None and (
                        _identity(info) != metadata["identity"] or int(info.attributes) != metadata["attributes"]
                        or _time(info.write) != metadata["write"]):
                    raise ContractError("Target identity/metadata changed after staging")
                if metadata and expected_sha256 is not None and self.security(handle) != metadata["security"]:
                    raise ContractError("Target security changed")
                self.checked(self.k.SetFilePointerEx(handle, 0, None, 0), "Seek for write")
                offset = 0
                while offset < len(data):
                    chunk, count = data[offset:offset + 1024 * 1024], U32()
                    buffer = C.create_string_buffer(chunk)
                    self.checked(self.k.WriteFile(handle, buffer, len(chunk), C.byref(count), None), "Write")
                    if count.value != len(chunk):
                        raise ContractError("Short native write; journal recovery required")
                    offset += count.value
                self.checked(self.k.SetEndOfFile(handle), "Truncate")
                if metadata and expected_sha256 is None and self.security(handle) != metadata["security"]:
                    descriptor = base64.b64decode(metadata["security"], validate=True)
                    self.checked(self.a.SetKernelObjectSecurity(handle, 7, C.create_string_buffer(descriptor)),
                                 "Restore original file security")
                if metadata:
                    # Identity and DACL remain on the existing object. Restore original timestamps.
                    times = [_ft(metadata[name]) for name in ("creation", "access", "write")]
                    self.checked(self.k.SetFileTime(handle, *(C.byref(t) for t in times)), "Restore file times")
                    class Basic(C.Structure):
                        _fields_ = [("creation", C.c_int64), ("access", C.c_int64), ("write", C.c_int64),
                                    ("change", C.c_int64), ("attributes", U32)]
                    basic = Basic(metadata["creation"], metadata["access"], metadata["write"], 0,
                                  metadata["attributes"])
                    self.checked(self.k.SetFileInformationByHandle(handle, 0, C.byref(basic), C.sizeof(basic)),
                                 "Restore file attributes")
                self.checked(self.k.FlushFileBuffers(handle), "Flush target")
                if self.read_handle(handle, path) != data:
                    raise ContractError("Native held-handle readback mismatch")
                if metadata and self.security(handle) != metadata["security"]:
                    raise ContractError("Native security-descriptor readback mismatch")

    def remove(self, path, expected_sha256, expected_metadata=None):
        from .inventory import digest
        path = Path(path)
        with self.ancestors(path):
            with self.open(path, READ | DELETE, directory=False) as (handle, info):
                if digest(self.read_handle(handle, path)) != expected_sha256:
                    raise ContractError("Native delete compare-and-swap mismatch")
                if expected_metadata and (
                        _identity(info) != expected_metadata["identity"]
                        or self.security(handle) != expected_metadata["security"]
                        or int(info.attributes) != expected_metadata["attributes"]
                        or _time(info.write) != expected_metadata["write"]):
                    raise ContractError("Delete target identity/metadata changed")
                delete = C.c_ubyte(1)
                self.checked(self.k.SetFileInformationByHandle(handle, 4, C.byref(delete), C.sizeof(delete)),
                             "Delete held target")

    def mkdir(self, path):
        path = Path(path)
        with self.ancestors(path):
            path.mkdir()
            with self.open(path, 1 | 0x80, directory=True) as (_, info):
                return _identity(info)

    def rmdir_if_owned_empty(self, path, identity):
        path = Path(path)
        try:
            with self.ancestors(path):
                with self.open(path, 1 | 0x80 | DELETE, directory=True) as (handle, info):
                    if _identity(info) != identity or any(path.iterdir()):
                        return
                    delete = C.c_ubyte(1)
                    if not self.k.SetFileInformationByHandle(handle, 4, C.byref(delete), C.sizeof(delete)):
                        if C.get_last_error() != 145:  # raced nonempty directory: preserve it
                            self.checked(False, "Remove created empty directory")
        except OSError as exc:
            if exc.errno not in (2, 3):
                raise


_instance = None


def native_io():
    global _instance
    if _instance is None:
        _instance = WindowsIO()
    return _instance
