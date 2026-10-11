#!/usr/bin/env python3
"""Validate a downloaded Snapshot Bridge Actions ZIP before local deep analysis.

Never trust the response from the writable Broker queue as proof of a GitHub
artifact. Confirm the GitHub repository, run, artifact ID and expected
snapshot ID through the connected GitHub service before running this verifier.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tempfile
import zipfile

HEX = re.compile(r"[0-9a-f]{64}\Z")
MAX_FILES = 50000
MAX_TOTAL = 600_000_000
MAX_FILE = 50_000_000

def safe_name(value):
    if (not isinstance(value, str) or not value or "\\" in value or
            "\x00" in value or ":" in value or "//" in value):
        raise ValueError("unsafe ZIP member path")
    p = PurePosixPath(value)
    if p.is_absolute() or any(s in ("", ".", "..") for s in value.split("/")):
        raise ValueError("unsafe ZIP member path")
    return value

def stream_hash(fileobj):
    h, total = hashlib.sha256(), 0
    while True:
        chunk = fileobj.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_FILE:
            raise ValueError("uncompressed file exceeds per-file limit")
        h.update(chunk)
    return h.hexdigest(), total

def verify(archive, dest, expected_snapshot=None, expected_selection=None):
    archive, dest = Path(archive).resolve(), Path(dest).absolute()
    if dest.exists():
        raise ValueError("destination already exists: refusal to overwrite")
    with zipfile.ZipFile(archive, "r") as z:
        infos = z.infolist()
        if len(infos) > MAX_FILES + 2:
            raise ValueError("too many entries")
        by_name, folded, total_size = {}, set(), 0
        for info in infos:
            name = safe_name(info.filename)
            if info.is_dir() or (info.external_attr >> 16) and stat.S_ISLNK(info.external_attr >> 16):
                raise ValueError("directories/symlinks are not allowed")
            if name in by_name or name.casefold() in folded:
                raise ValueError("duplicate archive path")
            if info.flag_bits & 1:
                raise ValueError("encrypted member")
            if info.file_size > MAX_FILE:
                raise ValueError("entry over file-size limit")
            total_size += info.file_size
            if total_size > MAX_TOTAL:
                raise ValueError("entry totals exceed size limit")
            by_name[name] = info
            folded.add(name.casefold())
        if "_bridge/manifest.json" not in by_name:
            raise ValueError("missing _bridge/manifest.json")
        with z.open("_bridge/manifest.json") as handle:
            manifest = json.loads(handle.read(MAX_FILE + 1))
        if type(manifest) is not dict or type(manifest.get("files")) is not list:
            raise ValueError("invalid manifest")
        sid = manifest.get("snapshot_id")
        if not isinstance(sid, str) or not sid:
            raise ValueError("invalid snapshot ID")
        if expected_snapshot is not None and sid != expected_snapshot:
            raise ValueError("snapshot ID does not match requested operation")
        entry_list = manifest["files"]
        if not entry_list or len(entry_list) > MAX_FILES:
            raise ValueError("invalid manifest file count")
        allowed = {"_bridge/manifest.json"}
        for entry in entry_list:
            if type(entry) is not dict:
                raise ValueError("invalid manifest file record")
            relative = safe_name(entry.get("path"))
            name = safe_name("repo/" + relative)
            if name in allowed or name not in by_name:
                raise ValueError("missing/duplicate manifest file")
            sha, size = entry.get("sha256"), entry.get("bytes")
            if type(sha) is not str or not HEX.fullmatch(sha) or type(size) is not int or size < 0:
                raise ValueError("invalid SHA256/byte size in manifest")
            allowed.add(name)
        if set(by_name) != allowed:
            raise ValueError("extra files not present in manifest")
        # Bind archive contents to the reviewed preview, not merely to a
        # self-consistent (possibly unexpected) ZIP manifest.
        entries = [(e["path"], e["sha256"], e["bytes"]) for e in entry_list]
        footprint = hashlib.sha256(json.dumps(
            entries, ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")).hexdigest()
        if manifest.get("selection_sha256") != footprint:
            raise ValueError("selection fingerprint is inconsistent with manifest")
        if expected_selection is not None and expected_selection != footprint:
            raise ValueError("archive differs from approved preview selection")
        # Hash all bytes before extraction, without trusting ZIP metadata.
        for entry in entry_list:
            with z.open("repo/" + entry["path"]) as stream:
                digest, size = stream_hash(stream)
            if digest != entry["sha256"] or size != entry["bytes"]:
                raise ValueError("manifest SHA256/size mismatch: " + entry["path"])
        dest.parent.mkdir(parents=True, exist_ok=True)
        scratch = Path(tempfile.mkdtemp(prefix=".snapshot-verified-", dir=dest.parent))
        try:
            for name in sorted(allowed):
                output = scratch.joinpath(*name.split("/"))
                output.parent.mkdir(parents=True, exist_ok=True)
                with z.open(name) as source, output.open("xb") as target:
                    shutil.copyfileobj(source, target, length=1024 * 1024)
            scratch.rename(dest)
        except Exception:
            shutil.rmtree(scratch, ignore_errors=True)
            raise
    return {"status": "verified", "snapshot_id": sid, "files": len(entry_list),
            "bytes": sum(e["bytes"] for e in entry_list), "destination": str(dest)}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("zip_path")
    parser.add_argument("output_directory")
    parser.add_argument("--snapshot-id", required=True)
    parser.add_argument("--selection-sha256", required=True)
    ns = parser.parse_args()
    print(json.dumps(verify(ns.zip_path, ns.output_directory, ns.snapshot_id, ns.selection_sha256), ensure_ascii=False))

if __name__ == "__main__":
    main()
