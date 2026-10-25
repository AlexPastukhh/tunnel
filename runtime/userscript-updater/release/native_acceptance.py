"""Owner-run native tests. Creates only a new private directory below DataRoot.

No acceptance receipt/authority is issued by these tests. The fixture writer is
defined here outside the application's import path and cannot target owner copies.
"""
import argparse
import ctypes as C
import json
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
dll_handles = []
if os.name == "nt":
    for folder in (ROOT / "python/DLLs", ROOT / "pydeps/pywin32_system32"):
        if folder.is_dir():
            dll_handles.append(os.add_dll_directory(str(folder)))

from checker.environment import analyzer_environment
from checker.inventory import digest, make_snapshot
from checker.jobs import CheckJobs
from checker.model import Registration, Selection, ContractError
from checker.policies import PolicyPack, PolicyStore
from checker.promotion import PromotionService
from checker.processes import RunControl, DeadlineExceeded
from checker.settings import DevelopmentSettings
from checker.windows_io import native_io, READ, WRITE

class Interrupted(BaseException):
    pass


class NativeFixtureTarget:
    scope = "NATIVE_ACCEPTANCE_FIXTURE"
    def __init__(self, fixture):
        self.fixture, self.io, self.interrupt = fixture, native_io(), False
    def authorize(self, target, settings):
        if not target.is_relative_to(self.fixture) or not self.fixture.name.startswith("native-acceptance-"):
            raise ContractError("Only the private acceptance fixture is writable")
    def path(self, root, relative):
        from checker.model import relative_target
        path = root / relative_target(relative) if relative else root
        if not path.is_relative_to(self.fixture):
            raise ContractError("Fixture escape")
        return path
    def read(self, root, relative):
        try:
            return self.io.read(self.path(root, relative))
        except OSError as exc:
            if exc.errno in (2, 3):
                return None
            raise
    def metadata(self, root, relative):
        return self.io.metadata(self.path(root, relative))
    def replace(self, root, relative, data, metadata, *, expected_sha256):
        self.io.write(self.path(root, relative), data, metadata, expected_sha256)
        if self.interrupt:
            self.interrupt = False
            raise Interrupted()
    def remove(self, root, relative, *, expected_sha256, expected_metadata=None):
        self.io.remove(self.path(root, relative), expected_sha256, expected_metadata)
    def mkdir(self, root, relative):
        return self.io.mkdir(self.path(root, relative))
    def rmdir_if_owned_empty(self, root, relative, identity):
        self.io.rmdir_if_owned_empty(self.path(root, relative), identity)


def junction(io, path, target):
    path.mkdir()
    substitute = ("\\??\\" + str(target)).encode("utf-16-le")
    printed = str(target).encode("utf-16-le")
    names = substitute + b"\0\0" + printed + b"\0\0"
    import struct
    payload = struct.pack("<IHHHHHH", 0xa0000003, 8 + len(names), 0,
                          0, len(substitute), len(substitute) + 2, len(printed)) + names
    io.k.DeviceIoControl.argtypes = [C.c_void_p, C.c_uint32, C.c_void_p, C.c_uint32,
                                     C.c_void_p, C.c_uint32, C.POINTER(C.c_uint32), C.c_void_p]
    io.k.DeviceIoControl.restype = C.c_int
    with io.ancestors(path):
        with io.open(path, WRITE, directory=True) as (handle, _):
            count = C.c_uint32()
            io.checked(io.k.DeviceIoControl(handle, 0x900a4, C.create_string_buffer(payload),
                       len(payload), None, 0, C.byref(count), None), "Create fixture junction")


def check_job(settings, project):
    jobs = CheckJobs(settings)
    jobs.start(project)
    try:
        deadline = time.monotonic() + settings.timeout_seconds + 5
        while time.monotonic() < deadline:
            for event in jobs.drain():
                if event.terminal:
                    jobs.thread.join(5)
                    if event.phase != "COMPLETE_DEVELOPMENT":
                        raise AssertionError(event.phase + ": " + event.detail)
                    return event.result
            time.sleep(.02)
        raise AssertionError("Native Check timeout")
    finally:
        jobs.cancel()
        jobs.thread.join(5)


def run(root, profile, report):
    result = dict(schema_version=1, platform=sys.platform, python=sys.version,
                  passed=[], failures=[], installation_profile_sha256=digest(profile.read_bytes()))
    if os.name != "nt":
        result["failures"].append("Native Windows is required; no emulation/skip is PASS")
        report.write_text(json.dumps(result, indent=2))
        return 2
    result["platform"] = "Windows"
    settings = DevelopmentSettings.load(profile)
    data_root = settings.state_root.parent
    data_root.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="native-acceptance-", dir=data_root) as temporary:
        fixture = Path(temporary)
        io = native_io()
        def test(name, function):
            try:
                function()
                result["passed"].append(name)
                print(name + ": PASS", flush=True)
            except Exception as exc:
                result["failures"].append(name + ": " + str(exc))
                print(name + ": FAIL: " + str(exc), flush=True)
        file = fixture / "пример.bin"
        file.write_bytes(b"old")
        def handles():
            assert io.read(file) == b"old"
            assert io.hash(file) == (digest(b"old"), 3)
            assert io.metadata(file)["identity"]
        test("handles", handles)
        def reparse():
            outside = fixture / "outside";outside.mkdir()
            (outside / "secret.bin").write_bytes(b"fixture only")
            link = fixture / "junction"
            junction(io, link, outside)
            try:
                try:
                    io.read(link / "secret.bin")
                except ContractError:
                    return
                raise AssertionError("Junction followed")
            finally:
                link.rmdir()
        test("reparse", reparse)
        def hardlink():
            alias = fixture / "hardlink.bin"
            os.link(file, alias)
            try:
                try:
                    io.read(file)
                except ContractError:
                    return
                raise AssertionError("Hardlink accepted")
            finally:
                alias.unlink()
        test("hardlink", hardlink)
        def ads():
            stream = str(file) + ":canary"
            with open(stream, "wb") as output:
                output.write(b"fixture")
            try:
                try:
                    io.read(file)
                except ContractError:
                    return
                raise AssertionError("ADS accepted")
            finally:
                os.unlink(stream)
        test("ads", ads)
        def sharing():
            with io.ancestors(file):
                with io.open(file, READ | WRITE, directory=False):
                    try:
                        io.write(file, b"blocked", None, digest(b"old"))
                    except OSError:
                        return
                    raise AssertionError("Concurrent writer was not refused")
        test("sharing", sharing)
        def metadata():
            before = io.metadata(file)
            io.write(file, b"new", before, digest(b"old"))
            after = io.metadata(file)
            for key in ("identity", "security", "attributes", "creation", "write"):
                assert after[key] == before[key], key
            io.remove(file, digest(b"new"))
            io.write(file, b"old", before, None)
            restored = io.metadata(file)
            assert restored["security"] == before["security"]
        test("metadata", metadata)
        source, target = fixture / "source", fixture / "target"
        source.mkdir();target.mkdir()
        (source / "a.js").write_text("const answer = 42;\n", encoding="utf-8")
        (source / "b.py").write_text("answer = 42\n", encoding="utf-8")
        (source / "empty").mkdir()
        (target / "owner.bin").write_bytes(b"owner")
        local = DevelopmentSettings(fixture / "state", fixture / "policies", (source,),
                                    settings.tools, settings.required_for_suffix, 180)
        pack = PolicyPack.parse((root / "profiles/starter-pack.json").read_bytes())
        PolicyStore(local.policy_root).create(pack)
        project = Registration("native-fixture", "Native fixture", (
            Selection("directory", str(source), "app"),), ("starter",), str(target))
        backend = NativeFixtureTarget(fixture)
        service = PromotionService(local, backend)
        checked = None
        def analyzers():
            nonlocal checked
            checked = check_job(local, project)
            assert checked.scan.status == "NOT_AUTHORIZED", checked.scan.status
            (source / "a.js").write_text("eval('1');\n", encoding="utf-8")
            violation = check_job(local, project)
            assert violation.scan.status == "FINDINGS", violation.scan.status
            (source / "a.js").write_text("const answer = 42;\n", encoding="utf-8")
            checked = check_job(local, project)
        test("real-analyzers", analyzers)
        def isolation():
            from checker.engines import run_dev_engine
            from checker.policy_validation import prepare_effective_policy
            limited = replace(project, selections=(Selection("file", str(source / "a.js"), "a.js"),
                                                   Selection("file", str(source / "b.py"), "b.py")))
            snapshot = make_snapshot(limited, (source,), fixture / "canary-snapshots")
            marker = fixture / "canary-executed"
            poison = fixture / "canary-modules";poison.mkdir()
            (poison / "sitecustomize.py").write_text(
                "from pathlib import Path;Path(" + repr(str(marker)) + ").write_text('python canary')")
            script = "require('node:fs').writeFileSync(" + json.dumps(str(marker)) + ",'node canary');"
            (poison / "evil.cjs").write_text(script)
            (snapshot.root / ".eslintrc.cjs").write_text(script)
            (snapshot.root / "semgrep.py").write_text(
                "from pathlib import Path;Path(" + repr(str(marker)) + ").write_text('cwd import')")
            (snapshot.root / ".semgrepignore").write_text("*")
            previous = {key: os.environ.get(key) for key in ("PYTHONPATH", "NODE_OPTIONS")}
            try:
                os.environ["PYTHONPATH"] = str(poison)
                os.environ["NODE_OPTIONS"] = "--require=" + str(poison / "evil.cjs")
                effective = prepare_effective_policy(PolicyStore(local.policy_root).capture(limited),
                    local.tools, fixture / "canary-policy")
                for config in effective.configs:
                    report = run_dev_engine(snapshot, config,
                        validation=next(v for v in effective.validations if v.engine == config.kind))
                    # Ignore/config canaries may make a tool refuse; they must never execute.
                    assert report.status in ("STRUCTURAL_CLEAR", "INCOMPLETE", "UNSUPPORTED", "ERROR"), report
                assert not marker.exists(), "Candidate startup/config code executed"
            finally:
                for key, value in previous.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value
        test("isolation-canaries", isolation)
        def transaction():
            assert checked is not None
            review = service.review(checked, project)
            outcome = service.apply(service.confirm(review.review_id, review.fingerprint, project), project)
            assert outcome.state == "COMPLETED", outcome
            assert (target / "app/empty").is_dir()
            assert (target / "owner.bin").read_bytes() == b"owner"
            inverse = service.restoration_review(outcome.operation_id)
            assert service.rollback(outcome.operation_id, inverse.fingerprint).state == "ROLLED_BACK"
            assert not (target / "app").exists()
        test("transaction", transaction)
        def interrupted():
            review = service.review(checked, project)
            backend.interrupt = True
            try:
                service.apply(service.confirm(review.review_id, review.fingerprint, project), project)
            except Interrupted:
                pass
            else:
                raise AssertionError("Injected interruption did not occur")
            operation = service.pending()[0][0]
            restarted = PromotionService(local, NativeFixtureTarget(fixture))
            plan = restarted.restoration_review(operation, recovery=True)
            assert restarted.recover_reviewed(plan).state == "ROLLED_BACK"
            assert (target / "owner.bin").read_bytes() == b"owner"
        test("interrupted-recovery", interrupted)
        def containment():
            marker = fixture / "escaped-child"
            child = f"import time;from pathlib import Path;time.sleep(2);Path({str(marker)!r}).write_text('escaped')"
            code = f"import subprocess,sys,time;subprocess.Popen([sys.executable,'-I','-S','-c',{child!r}]);time.sleep(10)"
            try:
                RunControl(.8).run([sys.executable, "-I", "-S", "-c", code],
                    cwd=fixture, env=analyzer_environment(fixture), timeout=.8)
            except DeadlineExceeded:
                pass
            else:
                raise AssertionError("Deadline did not stop process")
            time.sleep(2.5)
            assert not marker.exists(), "Grandchild survived Job Object close"
        test("child-containment", containment)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if not result["failures"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(run(ROOT, args.profile, args.report))
