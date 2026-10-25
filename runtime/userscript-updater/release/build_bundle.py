"""Build an offline Windows candidate from reviewed source and pinned downloads.

Runs only in Docker; never invokes the Windows installer or executes wheel code.
"""
import argparse
import base64
import csv
import email
import hashlib
import io
import json
import re
import shutil
import stat
import subprocess
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


def sha(path):
    hashed = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            hashed.update(block)
    return hashed.hexdigest()


def safe_name(name):
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or "\\" in name or ":" in name:
        raise ValueError("Unsafe archive path: " + name)


def inspect_wheel(path, allowed_hashes):
    if sha(path) not in allowed_hashes:
        raise ValueError("Wheel is not pinned by the lock: " + path.name)
    if not path.name.endswith(("-any.whl", "-win_amd64.whl")):
        raise ValueError("Non-Windows wheel: " + path.name)
    with zipfile.ZipFile(path) as wheel:
        names = wheel.namelist()
        if len(set(names)) != len(names):
            raise ValueError("Duplicate wheel entries")
        for entry in wheel.infolist():
            safe_name(entry.filename)
            if stat.S_ISLNK(entry.external_attr >> 16):
                raise ValueError("Wheel symlink")
        metadata_name, = [name for name in names if name.endswith(".dist-info/METADATA")]
        record_name, = [name for name in names if name.endswith(".dist-info/RECORD")]
        metadata = email.message_from_bytes(wheel.read(metadata_name))
        accounted = set()
        for name, expected, size in csv.reader(io.StringIO(wheel.read(record_name).decode())):
            safe_name(name)
            accounted.add(name)
            if expected:
                algorithm, value = expected.split("=", 1)
                if algorithm != "sha256":
                    raise ValueError("Unexpected wheel RECORD digest")
                hashed, length = hashlib.sha256(), 0
                with wheel.open(name) as member:
                    for block in iter(lambda: member.read(1024 * 1024), b""):
                        hashed.update(block)
                        length += len(block)
                digest = base64.urlsafe_b64encode(hashed.digest()).rstrip(b"=").decode()
                if digest != value or length != int(size):
                    raise ValueError("Wheel RECORD mismatch: " + name)
            elif name != record_name:
                raise ValueError("Unhashed wheel member: " + name)
        if {n for n in names if not n.endswith("/")} != accounted:
            raise ValueError("Wheel has unaccounted files")
        return dict(name=metadata["Name"], version=metadata["Version"], file=path.name,
                    sha256=sha(path), size=path.stat().st_size,
                    requires_dist=metadata.get_all("Requires-Dist", []))


def copy_tree(source, target, *, exclude=()):
    target.mkdir(parents=True, exist_ok=True)
    for path in sorted(source.iterdir()):
        if path.name in exclude:
            continue
        if path.is_symlink():
            raise ValueError("Source symlink: " + str(path))
        destination = target / path.name
        if path.is_dir():
            copy_tree(path, destination, exclude=exclude)
        else:
            shutil.copyfile(path, destination)


def files_manifest(root):
    result = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("Bundle symlink")
        if path.is_file():
            result.append(dict(path=path.relative_to(root).as_posix(), sha256=sha(path), size=path.stat().st_size))
    return result


def build(source, downloads, npm, output):
    output.mkdir(parents=True, exist_ok=True)
    release = source / "release"
    lock = (release / "requirements-windows.lock").read_text()
    allowed = set(re.findall(r"--hash=sha256:([0-9a-f]{64})", lock))
    wheels = [inspect_wheel(path, allowed) for path in sorted((downloads / "wheelhouse").glob("*.whl"))]
    locked = {re.sub(r"[-_.]+", "-", n).lower(): v
              for n, v in re.findall(r"^([A-Za-z0-9_.-]+)==([^\s;\\]+)", lock, re.M)}
    actual = {re.sub(r"[-_.]+", "-", row["name"]).lower(): row["version"] for row in wheels}
    if locked != actual or len(actual) != len(wheels):
        raise ValueError("The wheelhouse is not the complete exact lock closure")
    binaries = json.loads((release / "downloads.lock.json").read_text())
    if json.loads((downloads / "downloads.json").read_text()) != binaries:
        raise ValueError("Download receipts differ from the committed binary lock")
    npm_lock = json.loads((release / "npm-package-lock.json").read_text())
    if json.loads((npm.parent / "package-lock.json").read_text()) != npm_lock:
        raise ValueError("Npm closure differs from the committed npm lock")
    for row in binaries:
        path = downloads / row["file"]
        if sha(path) != row["sha256"] or path.stat().st_size != row["size"]:
            raise ValueError("Pinned binary download changed")
    package = json.loads((npm / "eslint/package.json").read_text())
    if package["version"] != "10.13.0":
        raise ValueError("Unexpected ESLint version")
    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=source, check=True,
                              capture_output=True, text=True).stdout.strip()
    with tempfile.TemporaryDirectory(prefix="checker-package-", dir=output) as temporary:
        root = Path(temporary) / "project-checker-v1-candidate"
        root.mkdir()
        copy_tree(source / "checker", root / "app/checker", exclude=("__pycache__",))
        copy_tree(downloads / "npm-cache/_cacache", root / "npm-cache/_cacache")
        copy_tree(downloads / "wheelhouse", root / "wheelhouse")
        (root / "qa").mkdir()
        for name in ("native_acceptance.py", "gui_acceptance.py", "accept_install.py"):
            shutil.copyfile(release / name, root / "qa" / name)
        for name in ("Install-Checker.ps1", "Accept-Checker.ps1", "Start-Checker.cmd", "run_installed.py",
                     "requirements-windows.lock", "WINDOWS_ACCEPTANCE.md", "ROLLBACK_INSTALL.md", "routes.example.json"):
            shutil.copyfile(release / name, root / name)
        (root / "profiles").mkdir()
        for name in ("base-eslint.cjs", "base-semgrep.json", "starter-pack.json"):
            shutil.copyfile(release / name, root / "profiles" / name)
        for row in binaries:
            shutil.copyfile(downloads / row["file"], root / row["file"])
        shutil.copyfile(release / "npm-package-lock.json", root / "npm-package-lock.json")
        shutil.copyfile(release / "npm-package.json", root / "npm-package.json")
        shutil.copyfile(release / "downloads.lock.json", root / "downloads.lock.json")
        (root / "dependency-inventory.json").write_text(json.dumps(
            dict(schema_version=1, wheels=wheels, binaries=binaries, eslint="10.13.0", npm_lock_sha256=sha(release / "npm-package-lock.json")), indent=2))
        (root / "release.json").write_text(json.dumps(dict(schema_version=1,
            release="personal-v1-candidate-20261025", source_revision=revision,
            status="SOURCE_CANDIDATE_WINDOWS_NOT_RUN", platforms=["Windows x64 NTFS"],
            python="3.13.17", node="22.23.3", eslint="10.13.0", semgrep="1.182.1"), indent=2))
        (root / "bundle-manifest.json").write_text(json.dumps(dict(schema_version=1, files=files_manifest(root)), indent=2))
        archive = output / "project-checker-v1-candidate-20261025.zip"
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zipped:
            for path in sorted(root.rglob("*")):
                if path.is_file():
                    entry = zipfile.ZipInfo(path.relative_to(root.parent).as_posix(), (2026, 10, 25, 0, 0, 0))
                    entry.compress_type = zipfile.ZIP_DEFLATED
                    entry.external_attr = 0o100644 << 16
                    with path.open("rb") as source_file, zipped.open(entry, "w") as destination:
                        shutil.copyfileobj(source_file, destination, 1024 * 1024)
        summary = dict(file=str(archive), sha256=sha(archive), size=archive.stat().st_size,
                       wheels=len(wheels), source_revision=revision, status="WINDOWS_NOT_RUN")
        (output / "package-summary.json").write_text(json.dumps(summary, indent=2))
        (output / (archive.name + ".sha256")).write_text(summary["sha256"] + "  " + archive.name + "\n")
        return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ("source", "downloads", "npm", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.source, args.downloads, args.npm, args.output), indent=2))
