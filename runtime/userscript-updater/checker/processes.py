"""Bounded development commands with cancellation and child-tree cleanup.

POSIX process groups are tested in Docker. Windows Job Object source is not native-tested.
No project code/config is imported by the isolated Python handshake process.
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path


class Cancelled(RuntimeError):
    pass


class DeadlineExceeded(RuntimeError):
    pass


class _WindowsJob:
    def __init__(self, process):
        import ctypes as c
        from ctypes import wintypes as w

        class Basic(c.Structure):
            _fields_ = [("user", c.c_int64), ("job", c.c_int64), ("flags", w.DWORD),
                        ("minimum", c.c_size_t), ("maximum", c.c_size_t),
                        ("active", w.DWORD), ("affinity", c.c_size_t),
                        ("priority", w.DWORD), ("scheduling", w.DWORD)]

        class IO(c.Structure):
            _fields_ = [(name, c.c_uint64) for name in
                        ("read_ops", "write_ops", "other_ops", "read_bytes", "write_bytes", "other_bytes")]

        class Extended(c.Structure):
            _fields_ = [("basic", Basic), ("io", IO), ("process_memory", c.c_size_t),
                        ("job_memory", c.c_size_t), ("peak_process", c.c_size_t), ("peak_job", c.c_size_t)]

        self.kernel = c.WinDLL("kernel32", use_last_error=True)
        self.kernel.CreateJobObjectW.argtypes = [c.c_void_p, w.LPCWSTR]
        self.kernel.CreateJobObjectW.restype = w.HANDLE
        self.kernel.SetInformationJobObject.argtypes = [w.HANDLE, c.c_int, c.c_void_p, w.DWORD]
        self.kernel.SetInformationJobObject.restype = w.BOOL
        self.kernel.AssignProcessToJobObject.argtypes = [w.HANDLE, w.HANDLE]
        self.kernel.AssignProcessToJobObject.restype = w.BOOL
        self.kernel.CloseHandle.argtypes = [w.HANDLE]
        self.kernel.CloseHandle.restype = w.BOOL
        self.handle = self.kernel.CreateJobObjectW(None, None)
        if not self.handle:
            raise c.WinError(c.get_last_error())
        info = Extended()
        info.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE, no breakaway
        if (not self.kernel.SetInformationJobObject(self.handle, 9, c.byref(info), c.sizeof(info))
                or not self.kernel.AssignProcessToJobObject(self.handle, int(process._handle))):
            error = c.get_last_error()
            self.close()
            raise c.WinError(error)

    def close(self):
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None


class RunControl:
    def __init__(self, timeout: float = 120):
        if timeout <= 0:
            raise ValueError("Positive job timeout required")
        self.deadline = time.monotonic() + timeout
        self.cancelled = threading.Event()

    def cancel(self):
        self.cancelled.set()

    def check(self):
        if self.cancelled.is_set():
            raise Cancelled("Cancelled by user")
        if time.monotonic() >= self.deadline:
            raise DeadlineExceeded("Job deadline exceeded")

    def run(self, argv, *, cwd, env, timeout=30, **_kwargs):
        self.check()
        command_deadline = min(self.deadline, time.monotonic() + timeout)
        gate = Path(__file__).with_name("process_gate.py").resolve()
        job = None
        process = None
        with tempfile.TemporaryFile(dir=cwd) as out, tempfile.TemporaryFile(dir=cwd) as err:
            try:
                gate_env = dict(env)
                process = subprocess.Popen([sys.executable, "-I", "-B", "-S", str(gate)],
                    stdin=subprocess.PIPE, stdout=out, stderr=err, cwd=cwd, env=gate_env,
                    shell=False, start_new_session=os.name == "posix")
                if os.name == "nt":
                    # The gate is waiting for stdin: no CLI child exists before job assignment.
                    job = _WindowsJob(process)
                payload = json.dumps({"argv": argv, "cwd": str(cwd), "env": gate_env}).encode("utf-8")
                if len(payload) >= 8 * 1024 * 1024:
                    raise ValueError("Command request exceeds size limit")
                process.stdin.write(payload)
                process.stdin.close()
                while process.poll() is None:
                    self.check()
                    if time.monotonic() >= command_deadline:
                        raise DeadlineExceeded("Analyzer deadline exceeded")
                    if os.fstat(out.fileno()).st_size + os.fstat(err.fileno()).st_size > 16 * 1024 * 1024:
                        raise ValueError("Analyzer output exceeds explicit limit")
                    self.cancelled.wait(0.04)
                self.check()
                if os.fstat(out.fileno()).st_size + os.fstat(err.fileno()).st_size > 16 * 1024 * 1024:
                    raise ValueError("Analyzer output exceeds explicit limit")
                out.seek(0)
                err.seek(0)
                return subprocess.CompletedProcess(argv, process.returncode,
                    out.read().decode("utf-8", errors="replace"), err.read().decode("utf-8", errors="replace"))
            finally:
                # Kill children even if the leader has already exited, so a leftover helper cannot survive.
                if process is not None:
                    if os.name == "posix":
                        try:
                            os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                    elif job is not None:
                        job.close()
                    elif process.poll() is None:
                        process.kill()  # gate never received its request if job assignment failed
                    if process.stdin and not process.stdin.closed:
                        process.stdin.close()
                    process.wait(timeout=5)


def execute(argv, *, control: RunControl | None = None, **kwargs):
    if kwargs.get("text"):
        kwargs.setdefault("encoding", "utf-8")
    return control.run(argv, **kwargs) if control else subprocess.run(argv, **kwargs)
