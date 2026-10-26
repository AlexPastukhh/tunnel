"""Explicit owner preparation of an offline runtime for the Windows working copy.

This uses current repository sources. It never creates an installed acceptance receipt.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
import zipfile
from pathlib import Path, PurePosixPath

from .inventory import check_plain_chain, under
from .model import ContractError
from .policies import PolicyPack, PolicyStore
from .registry import unique_object

BUNDLE_NAME = "project-checker-v1-candidate-20261025.zip"
BUNDLE_SHA256 = "ecb89592bb8a6abad0f36383c838d7802d5b95edf4589404a87e05858720acad"
SOURCE_ROOT = Path(__file__).resolve().parent.parent
BUNDLE_PREFIX = "project-checker-v1-candidate/"
SETUP_HINT = "Анализаторы не подготовлены. Закройте окно и выполните: py -3 -m checker.gui --prepare-source-runtime"


def file_hash(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def seed_policies(root):
    """Add the bundled starter once; preserve all owner edits, including invalid files."""
    store = PolicyStore(root)
    path = root / "starter.json"
    if not path.exists() and not path.is_symlink():
        pack = PolicyPack.parse((SOURCE_ROOT / "release/starter-pack.json").read_bytes())
        try:
            store.create(pack)
        except FileExistsError:
            pass
    return root


def default_registry():
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        raise ContractError("LOCALAPPDATA is unavailable; pass an absolute --registry")
    return Path(local) / "ProjectChecker-Test/projects.json"


def safe_member(name):
    rel = PurePosixPath(name)
    if (not name or "\\" in name or ":" in name or rel.is_absolute()
            or any(p in ("", ".", "..") for p in name.split("/"))):
        raise ContractError("Unsafe archive member")
    return rel


def extract_bundle(archive, destination, expected_sha256=BUNDLE_SHA256):
    """Bounded streaming validation, then extraction into a new temporary directory."""
    if file_hash(archive) != expected_sha256:
        raise ContractError("Offline dependency archive SHA-256 mismatch")
    with zipfile.ZipFile(archive) as bundle:
        entries = {}
        for info in bundle.infolist():
            if info.is_dir():
                safe_member(info.filename.rstrip("/"))
                continue
            safe_member(info.filename)
            if not info.filename.startswith(BUNDLE_PREFIX) or (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise ContractError("Unexpected archive root or symlink")
            key = info.filename[len(BUNDLE_PREFIX):]
            if key.casefold() in entries:
                raise ContractError("Duplicate/case-colliding archive member")
            entries[key.casefold()] = (key, info)
        manifest_name = "bundle-manifest.json"
        if manifest_name not in entries or entries[manifest_name][1].file_size > 1024 * 1024:
            raise ContractError("Missing/oversize dependency manifest")
        manifest = json.loads(bundle.read(entries[manifest_name][1]), object_pairs_hook=unique_object)
        if manifest.get("schema_version") != 1 or not isinstance(manifest.get("files"), list):
            raise ContractError("Unsupported dependency manifest")
        expected = {}
        for item in manifest["files"]:
            safe_member(item["path"])
            key = item["path"].casefold()
            if key in expected or key == manifest_name:
                raise ContractError("Duplicate manifest member")
            expected[key] = item
        if set(entries) != set(expected) | {manifest_name}:
            raise ContractError("Dependency manifest/file closure mismatch")
        if sum(i.file_size for _, i in entries.values()) > 1024 * 1024 * 1024:
            raise ContractError("Dependency archive exceeds extraction limit")
        for key, item in expected.items():
            name, info = entries[key]
            if name != item["path"] or info.file_size != item["size"]:
                raise ContractError("Dependency file name/size mismatch")
            target = destination.joinpath(*safe_member(name).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            h = hashlib.sha256()
            with bundle.open(info) as source, target.open("xb") as output:
                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                    h.update(chunk)
                    output.write(chunk)
            if h.hexdigest() != item["sha256"]:
                raise ContractError("Dependency member SHA-256 mismatch: " + name)


def write_profile(runtime, data_root):
    tools = []
    for kind, exe, cfg, node in (
        ("eslint", runtime / "eslint/node_modules/eslint/bin/eslint.js",
         runtime / "profiles/base-eslint.cjs", runtime / "node/node.exe"),
        ("semgrep", runtime / "python/python.exe", runtime / "profiles/base-semgrep.json", None),
    ):
        tools.append(dict(kind=kind, executable=str(exe), executable_sha256=file_hash(exe),
                          config=str(cfg), config_sha256=file_hash(cfg), node=str(node) if node else None))
    profile = dict(schema_version=1, state_root=str(data_root / "state"),
                   policy_root=str(data_root / "policies"), source_roots=[str(data_root / "sources")],
                   tools=tools, required_for_suffix={s: ["eslint", "semgrep"] for s in (".js", ".cjs", ".mjs")}
                   | {".py": ["semgrep"]}, timeout_seconds=180)
    path = runtime / "source-profile.json"
    path.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def runtime_for(registry):
    pointer = registry.parent / "source-runtime.json"
    if not pointer.exists():
        return None
    if pointer.stat().st_size > 16384:
        raise ContractError("Source runtime pointer exceeds size limit")
    data = json.loads(pointer.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    if set(data) != {"schema_version", "source_root", "runtime_root"} or data["schema_version"] != 1:
        raise ContractError("Invalid source runtime pointer")
    runtime = Path(data["runtime_root"])
    if (Path(data["source_root"]) != SOURCE_ROOT or not runtime.is_absolute()
            or runtime.parent != registry.parent / "runtimes"):
        raise ContractError("Source runtime belongs to a different working folder; prepare it again")
    check_plain_chain(runtime)
    if not (runtime / "python/python.exe").is_file() or not (runtime / "source-profile.json").is_file():
        raise ContractError("Source runtime is incomplete; prepare a new runtime")
    return runtime


def prepare_runtime(registry, archive=None):
    from .working import require_windows_owner
    require_windows_owner()
    if not registry.is_absolute():
        raise ContractError("Absolute registry path required")
    data_root = registry.parent
    if under(data_root, SOURCE_ROOT) or under(SOURCE_ROOT, data_root):
        raise ContractError("Runtime/data directory must be outside the working source folder")
    ancestor = data_root
    while not ancestor.exists():
        ancestor = ancestor.parent
    check_plain_chain(ancestor)
    data_root.mkdir(parents=True, exist_ok=True)
    seed_policies(data_root / "policies")
    lock = data_root / ".source-runtime-setup.lock"
    try:
        handle = lock.open("x")
    except FileExistsError as exc:
        raise ContractError("Another setup is running or was interrupted; inspect " + str(lock)) from exc
    try:
        handle.close()
        runtimes = data_root / "runtimes"
        runtimes.mkdir(exist_ok=True)
        runtime = runtimes / uuid.uuid4().hex
        runtime.mkdir()
        print("Preparing runtime: " + str(runtime), flush=True)
        env = {k: v for k, v in os.environ.items()
               if k.upper() not in {"NODE_OPTIONS", "NODE_PATH", "PYTHONPATH", "PYTHONHOME"}}
        def run(args):
            print("Preparing: " + Path(str(args[0])).name, flush=True)
            subprocess.run([str(a) for a in args], cwd=runtime, env=env, check=True)
        with tempfile.TemporaryDirectory(prefix="checker-offline-", dir=data_root) as tmp:
            payload = Path(tmp)
            extract_bundle(archive or SOURCE_ROOT / ".artifacts" / BUNDLE_NAME, payload)
            installer = payload / "python-3.13.17-amd64.exe"
            powershell = Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
            script = ("$s=Get-AuthenticodeSignature -LiteralPath $env:CHECKER_PYTHON_INSTALLER;"
                      "if($s.Status -ne 'Valid' -or $s.SignerCertificate.Subject -notmatch "
                      "'Python Software Foundation'){exit 1}")
            env["CHECKER_PYTHON_INSTALLER"] = str(installer)
            run([powershell, "-NoProfile", "-NonInteractive", "-Command", script])
            run([installer, "/quiet", "InstallAllUsers=0", "TargetDir=" + str(runtime / "python"),
                 "Include_launcher=0", "Include_pip=1", "Include_tcltk=1", "Include_test=0",
                 "Include_doc=0", "Include_dev=0", "PrependPath=0", "Shortcuts=0",
                 "CompileAll=0", "AssociateFiles=0"])
            python = runtime / "python/python.exe"
            run([python, "-I", "-B", "-c", "import sys; assert sys.version_info[:2]==(3,13) and sys.maxsize>2**32"])
            run([python, "-I", "-B", "-m", "pip", "--isolated", "--disable-pip-version-check",
                 "install", "--no-index", "--no-compile", "--no-warn-script-location",
                 "--require-hashes", "--find-links", payload / "wheelhouse",
                 "--target", runtime / "pydeps", "-r", payload / "requirements-windows.lock"])
            with zipfile.ZipFile(payload / "node-v22.23.3-win-x64.zip") as node_zip:
                for info in node_zip.infolist():
                    safe_member(info.filename.rstrip("/"))
                    if (info.external_attr >> 16) & 0o170000 == 0o120000:
                        raise ContractError("Node archive symlink")
                node_zip.extractall(runtime)
            (runtime / "node-v22.23.3-win-x64").rename(runtime / "node")
            eslint = runtime / "eslint"
            eslint.mkdir()
            shutil.copyfile(payload / "npm-package.json", eslint / "package.json")
            shutil.copyfile(payload / "npm-package-lock.json", eslint / "package-lock.json")
            userconfig, globalconfig = runtime / "empty-user.npmrc", runtime / "empty-global.npmrc"
            userconfig.write_text("")
            globalconfig.write_text("")
            run([runtime / "node/node.exe", runtime / "node/node_modules/npm/bin/npm-cli.js",
                 "ci", "--offline", "--ignore-scripts", "--audit=false", "--fund=false",
                 "--cache", payload / "npm-cache", "--userconfig", userconfig,
                 "--globalconfig", globalconfig, "--prefix", eslint])
            shutil.copytree(payload / "profiles", runtime / "profiles")
        paths = isolated_python_paths()
        (runtime / "python/python313._pth").write_text("\n".join(paths) + "\n", encoding="utf-8")
        write_profile(runtime, data_root)
        return finish_runtime(runtime, registry, env)
    finally:
        lock.unlink(missing_ok=True)


def isolated_python_paths():
    return [".", "Lib", "DLLs", str(SOURCE_ROOT), "../pydeps", "../pydeps/win32",
            "../pydeps/win32/lib", "../pydeps/Pythonwin", "../pydeps/pywin32_system32"]


def finish_runtime(runtime, registry, environment):
    """Validate the existing staged runtime before publishing its ready pointer."""
    from .settings import DevelopmentSettings
    if (not registry.is_absolute() or not runtime.is_absolute() or ".." in runtime.parts
            or runtime.parent != registry.parent / "runtimes"):
        raise ContractError("Resume requires an existing runtime under this registry's runtimes directory")
    check_plain_chain(runtime)
    profile = runtime / "source-profile.json"
    settings = DevelopmentSettings.load(profile)
    if (settings.state_root != registry.parent / "state"
            or settings.policy_root != registry.parent / "policies"
            or settings.source_roots != (registry.parent / "sources",)):
        raise ContractError("Staged runtime profile belongs to different data paths")
    expected = {
        "eslint": (runtime / "eslint/node_modules/eslint/bin/eslint.js",
                   runtime / "profiles/base-eslint.cjs", runtime / "node/node.exe"),
        "semgrep": (runtime / "python/python.exe", runtime / "profiles/base-semgrep.json", None),
    }
    if {tool.kind for tool in settings.tools} != set(expected):
        raise ContractError("Staged runtime must contain both analyzers")
    for tool in settings.tools:
        if (tool.executable, tool.config, tool.node) != expected[tool.kind]:
            raise ContractError("Staged analyzer paths do not belong to this runtime")
        tool.validate()  # Verify stored pins; never re-pin a partial installation.
    if (runtime / "python/python313._pth").read_text(encoding="utf-8").splitlines() != isolated_python_paths():
        raise ContractError("Staged runtime uses different Python/source paths")
    python = runtime / "python/python.exe"
    print("Validating existing runtime: " + str(runtime), flush=True)
    subprocess.run([str(python), "-I", "-S", "-B", "-c",
        "from pathlib import Path; from checker.source_bootstrap import validate_runtime; "
        "validate_runtime(Path(" + repr(str(profile)) + "))"],
        cwd=runtime, env=environment, check=True)
    pointer = registry.parent / "source-runtime.json"
    staged = registry.parent / (".source-runtime-" + uuid.uuid4().hex + ".json")
    try:
        staged.write_text(json.dumps(dict(schema_version=1, source_root=str(SOURCE_ROOT),
                              runtime_root=str(runtime)), ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(staged, pointer)
    finally:
        staged.unlink(missing_ok=True)
    print("Ready. Launch checker.gui with --registry only.\nProfile: " + str(profile), flush=True)
    return runtime


def resume_runtime(registry, runtime):
    """Owner explicitly retries only validation; no installers or dependency changes."""
    from .working import require_windows_owner
    require_windows_owner()
    if not registry.is_absolute():
        raise ContractError("Absolute registry path required")
    lock = registry.parent / ".source-runtime-setup.lock"
    try:
        handle = lock.open("x")
    except FileExistsError as exc:
        raise ContractError("Another setup is running or was interrupted; inspect " + str(lock)) from exc
    try:
        handle.close()
        environment = {k: v for k, v in os.environ.items()
                       if k.upper() not in {"NODE_OPTIONS", "NODE_PATH", "PYTHONPATH", "PYTHONHOME"}}
        return finish_runtime(runtime, registry, environment)
    finally:
        lock.unlink(missing_ok=True)


def validate_runtime(profile):
    """Run real compilers with safe JS/Python fixtures before marking setup ready."""
    from .environment import configure_gui_environment
    from .settings import DevelopmentSettings
    from .policy_service import capture_pack_values
    from .policy_validation import prepare_effective_policy
    from .processes import RunControl
    configure_gui_environment(profile.parent)
    import tkinter
    import yaml
    import semgrep
    settings = DevelopmentSettings.load(profile)
    settings.check_storage_paths()
    settings.state_root.mkdir(parents=True, exist_ok=True)
    captured = capture_pack_values((PolicyStore(settings.policy_root).load("starter"),))
    import time
    started = time.monotonic()
    command_timeout, job_timeout = 30, 180
    report = dict(schema_version=1, scope="SOURCE_RUNTIME_DIAGNOSTIC", status="ERROR", phases=[],
                  command_timeout_seconds=command_timeout, job_timeout_seconds=job_timeout,
                  temporary_parent=str(settings.state_root))
    def progress(kind, phase):
        report["phases"].append(dict(engine=kind, phase=phase, elapsed_seconds=round(time.monotonic() - started, 3)))
        print("Config validation: " + kind + " " + phase, flush=True)
    try:
        with tempfile.TemporaryDirectory(prefix="setup-validation-", dir=settings.state_root) as tmp:
            prepare_effective_policy(captured, settings.tools, Path(tmp) / "effective",
                                     timeout=command_timeout, control=RunControl(job_timeout),
                                     diagnostics=True, progress=progress,
                                     temporary_parent=settings.state_root)
        report["status"] = "VALIDATED"
    except Exception as exc:
        report["error"] = dict(type=type(exc).__name__, message=str(exc),
                              engine=getattr(exc, "engine", ""),
                              stdout_tail=getattr(exc, "stdout", "")[-8192:],
                              stderr_tail=getattr(exc, "stderr", "")[-8192:])
        raise
    finally:
        report["elapsed_seconds"] = round(time.monotonic() - started, 3)
        path = settings.state_root / "setup-validation-report.json"
        staged = settings.state_root / (".setup-report-" + uuid.uuid4().hex)
        try:
            staged.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(staged, path)
            print("Diagnostic report: " + str(path), flush=True)
        except OSError as exc:
            print("Cannot save setup diagnostic report: " + str(exc), flush=True)
        finally:
            try:
                staged.unlink(missing_ok=True)
            except OSError:
                pass
    print("Actual ESLint/Semgrep configuration validation completed", flush=True)


def launch_runtime(runtime, registry):
    command = [str(runtime / "python/python.exe"), "-I", "-S", "-B", "-m", "checker.gui",
               "--registry", str(registry), "--source-profile", str(runtime / "source-profile.json")]
    return subprocess.call(command, cwd=SOURCE_ROOT)


def load_context(profile, registry):
    from .settings import DevelopmentSettings
    from .working import WorkingContext, require_windows_owner
    require_windows_owner()
    runtime = runtime_for(registry)
    if (runtime is None or profile != runtime / "source-profile.json"
            or Path(sys.executable).resolve() != (runtime / "python/python.exe").resolve()
            or not sys.flags.isolated or not sys.flags.no_site):
        raise ContractError("Use the prepared source runtime")
    return WorkingContext(DevelopmentSettings.load(profile), registry, runtime)
