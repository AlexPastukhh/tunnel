#!/usr/bin/env python3
"""Fortis Repo client for fixed-operation Windows Bridge Broker (no Windows shell)."""
import argparse
import json
import os
from pathlib import Path
import re
import sys
import time
import uuid

SHARED = Path("/workspace/files/.fortis-bridge-broker-v1")
INBOX = SHARED / "in"
OUTBOX = SHARED / "out"
ALIAS = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,70}\Z")
SNAPID = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_-]{5,100}\Z")

def request_id(text):
    try:
        v = uuid.UUID(text)
        if str(v) != text:
            raise ValueError("non-canonical uuid")
        return text
    except (ValueError, AttributeError):
        raise ValueError("expected lowercase canonical request UUID")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("op", choices=["list", "preview", "snapshot", "status", "recover", "receive"])
    parser.add_argument("value", nargs="?")
    parser.add_argument("--submit-only", action="store_true")
    parser.add_argument("--timeout", type=int, default=60)
    ns = parser.parse_args()
    if not 1 <= ns.timeout <= 240:
        parser.error("timeout must be in [1,240] seconds")
    if ns.op == "receive":
        try:
            rid = request_id(ns.value)
        except ValueError as exc:
            parser.error(str(exc))
    else:
        if ns.op == "list" and ns.value:
            parser.error("list takes no arguments")
        if ns.op in ("preview", "snapshot") and (not ns.value or not ALIAS.fullmatch(ns.value)):
            parser.error("registered alias required")
        if ns.op == "status" and (not ns.value or not SNAPID.fullmatch(ns.value)):
            parser.error("snapshot ID required")
        if ns.op == "recover":
            try:
                request_id(ns.value)
            except ValueError as exc:
                parser.error(str(exc))
        if not INBOX.is_dir() or not OUTBOX.is_dir():
            parser.error("Windows Broker queue is not mounted")
        rid = str(uuid.uuid4())
        req = {"version": 1, "id": rid, "op": ns.op}
        if ns.op in ("preview", "snapshot"):
            req["repo"] = ns.value
        elif ns.op == "status":
            req["snapshot_id"] = ns.value
        elif ns.op == "recover":
            req["request_id"] = ns.value
        temp = INBOX / (rid + ".tmp")
        dest = INBOX / (rid + ".json")
        with temp.open("x", encoding="utf-8") as file:
            json.dump(req, file, separators=(",", ":"))
            file.write("\n")
        os.replace(temp, dest)
        if ns.submit_only:
            print(rid)
            return
    limit = time.monotonic() + ns.timeout
    response = OUTBOX / (rid + ".json")
    while not response.is_file():
        if time.monotonic() >= limit:
            print(json.dumps({"status": "timeout", "request_id": rid,
                              "next": "Do not resubmit snapshot. Run: broker client recover "
                              + rid}, ensure_ascii=False))
            sys.exit(2)
        time.sleep(0.4)
    payload = json.loads(response.read_text(encoding="utf-8"))
    if payload.get("id") != rid or payload.get("version") != 1:
        print("response identity mismatch; independently verify result", file=sys.stderr)
        sys.exit(3)
    response.unlink(missing_ok=True)
    # A writable shared response is NOT authoritative proof. Verify private
    # GitHub Artifact plus signed-bytes manifest before claiming completion.
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if not payload.get("ok"):
        sys.exit(1)

if __name__ == "__main__":
    main()
