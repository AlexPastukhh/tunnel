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
from contextlib import contextmanager


class Cancelled(RuntimeError):
    pass


class DeadlineExceeded(RuntimeError):
    # Bounded output is attached after child-tree cleanup, before temp files close.
    stdout = ""
    stderr = ""
    command = ()
    engine = ""
    parent_phase = ""
    phase_markers = ()


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

    def run(self, argv, *, cwd, env, timeout=30, trace_phases=False, **_kwargs):
        self.check()
        command_deadline = min(self.deadline, time.monotonic() + timeout)
        gate = Path(__file__).with_name("process_gate.py").resolve()
        job = None
        process = None
        failure = None
        parent_phase = "before_gate"
        with tempfile.TemporaryFile(dir=cwd) as out, tempfile.TemporaryFile(dir=cwd) as err:
            try:
                gate_env = dict(env)
                process = subprocess.Popen([sys.executable, "-I", "-B", "-S", str(gate)],
                    stdin=subprocess.PIPE, stdout=out, stderr=err, cwd=cwd, env=gate_env,
                    shell=False, start_new_session=os.name == "posix")
                parent_phase = "gate_spawned"
                if os.name == "nt":
                    # The gate is waiting for stdin: no CLI child exists before job assignment.
                    job = _WindowsJob(process)
                parent_phase = "gate_contained"
                payload = json.dumps({"argv": argv, "cwd": str(cwd), "env": gate_env,
                                      "trace_phases": trace_phases is True}).encode("utf-8")
                if len(payload) >= 8 * 1024 * 1024:
                    raise ValueError("Command request exceeds size limit")
                process.stdin.write(payload)
                process.stdin.close()
                parent_phase = "request_sent"
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
            except DeadlineExceeded as exc:
                failure = exc
                raise
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
                if failure is not None:
                    failure.command = tuple(map(str, argv))
                    failure.parent_phase = parent_phase
                    for name, stream in (("stdout", out), ("stderr", err)):
                        try:
                            size = os.fstat(stream.fileno()).st_size
                            stream.seek(max(0, size - 8192))
                            setattr(failure, name, stream.read(8192).decode("utf-8", errors="replace"))
                        except OSError:
                            pass  # Preserve the original deadline failure.
                    if trace_phases:
                        # Read only fixed labels from a bounded prefix; do not
                        # copy CLI debug output into the structured report.
                        try:
                            err.seek(0)
                            prefix = err.read(65536).decode("utf-8", errors="replace")
                            labels = ("checker-gate:request_received", "checker-gate:child_launch",
                                      "checker-semgrep:import_start", "checker-semgrep:cli_start",
                                      "checker-gate:child_exited")
                            failure.phase_markers = tuple(label for label in labels if label in prefix)
                        except OSError:
                            pass


# OCaml's Windows socketpair uses a UTF-8 pathname in a 108-byte sun_path.
# Leave room for the generated socket name, separator and terminator.
WINDOWS_IPC_TEMP_MAX_BYTES = 80
_WINDOWS = os.name == "nt"


def check_windows_socket_temp(path):
    size = len(str(path).encode("utf-8"))
    if size > WINDOWS_IPC_TEMP_MAX_BYTES:
        raise ValueError(
            f"Windows analyzer TEMP is too long ({size} UTF-8 bytes; maximum "
            f"{WINDOWS_IPC_TEMP_MAX_BYTES}). Choose a shorter protected state directory.")


@contextmanager
def command_environment(environment, temporary_parent):
    """One private temporary directory per command, inside authorized state."""
    if temporary_parent is None:
        yield environment
        return
    if environment is None:
        raise ValueError("An explicit analyzer environment is required")
    parent = Path(temporary_parent)
    if not parent.is_absolute() or ".." in parent.parts:
        raise ValueError("Absolute temporary parent without traversal required")
    from .inventory import check_plain_chain
    ancestor = parent
    while not ancestor.exists():
        ancestor = ancestor.parent
    check_plain_chain(ancestor)
    parent.mkdir(parents=True, exist_ok=True)
    check_plain_chain(parent)
    with tempfile.TemporaryDirectory(prefix="", dir=parent) as temporary:
        if _WINDOWS:
            check_windows_socket_temp(temporary)
        # Do not mutate parent/system environment or fall back to global TEMP.
        child = dict(environment, TEMP=temporary, TMP=temporary, TMPDIR=temporary)
        yield child


def execute(argv, *, control: RunControl | None = None, temporary_parent: Path | None = None,
            trace_phases: bool = False, **kwargs):
    if kwargs.get("text"):
        kwargs.setdefault("encoding", "utf-8")
    if trace_phases and control is None:
        raise ValueError("Phase tracing requires contained RunControl execution")
    with command_environment(kwargs.get("env"), temporary_parent) as environment:
        kwargs["env"] = environment
        return (control.run(argv, trace_phases=trace_phases, **kwargs)
                if control else subprocess.run(argv, **kwargs))
