#!/usr/bin/env python3
"""Windows-only Fortis Broker: narrow, reviewable fixed operations and one-use export grants."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import uuid

ROOT = Path(__file__).resolve().parent
USER = Path.home()
SHARED = USER / "Workfiles" / ".fortis-bridge-broker-v1"
INBOX, OUTBOX = SHARED / "in", SHARED / "out"
CLAIMS, JOURNAL = ROOT / "claims", ROOT / "requests"
PERMITS, STATE = ROOT / "permits.json", ROOT / "issued-snapshots.json"
BRIDGE, REGISTRY = USER / "chatgpt-bridge" / "bridge.py", USER / "chatgpt-bridge" / "repos.json"
REPO_ROOT = (USER / "Repos").resolve()
ID = re.compile(r"[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}\Z")
ALIAS = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,70}\Z")
SNAPID = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_-]{5,100}\Z")
DIGEST = re.compile(r"[a-f0-9]{64}\Z")
OPS = frozenset(("list", "preview", "snapshot", "status", "recover"))

def now():
    return dt.datetime.now(dt.timezone.utc)

def read_json(path, default=None):
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else default

def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".broker-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(value, file, ensure_ascii=False, separators=(",", ":"))
            file.write("\n")
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)

def check_dirs():
    for path in (SHARED, INBOX, OUTBOX):
        if not path.is_dir() or path.is_symlink():
            raise RuntimeError("shared_broker_directory_unavailable")
        if getattr(path.stat(follow_symlinks=False), "st_file_attributes", 0) & 1024:
            raise RuntimeError("shared_broker_directory_is_reparse_point")
    for private in (ROOT, CLAIMS, JOURNAL):
        private.mkdir(parents=True, exist_ok=True)

def registry():
    cfg = read_json(REGISTRY, {})
    result = {}
    for alias, entry in cfg.get("repositories", {}).items():
        try:
            p = Path(os.path.expandvars(entry["path"])).resolve(strict=True)
            if p != REPO_ROOT and p.is_relative_to(REPO_ROOT):
                result[alias] = entry
        except (KeyError, ValueError, OSError):
            pass
    return result

def bridge(action, **args):
    argv = [sys.executable, str(BRIDGE), action]
    for key, value in args.items():
        if value is True:
            argv.append("--" + key.replace("_", "-"))
        elif value is not False and value is not None:
            argv.extend(["--" + key.replace("_", "-"), str(value)])
    proc = subprocess.run(argv, cwd=BRIDGE.parent, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=175)
    if proc.returncode:
        raise RuntimeError("bridge_rejected_exit_" + str(proc.returncode))
    if len(proc.stdout) > 65536:
        raise RuntimeError("bridge_response_too_large")
    value = json.loads(proc.stdout)
    if value.get("status") == "error":
        raise RuntimeError("bridge_reported_error")
    return value

def private_entry(alias, entries):
    if alias not in entries:
        raise PermissionError("repo_not_allowed")
    entry = entries[alias]
    if entry.get("transport") != "private_bridge":
        raise PermissionError("broker_requires_private_transport")
    if entry.get("transport_repository") != "AlexPastukhh/chatgpt-snapshot-transfer":
        raise PermissionError("unknown_private_transport")
    if entry.get("export_enabled", entry.get("classification") == "synthetic") is not True:
        raise PermissionError("bridge_export_disabled")
    # Never silently ignore a configured export policy.
    if entry.get("snapshot_ignore_file") and entry.get("selection_mode", "include") != "exclude":
        raise PermissionError("snapshot_ignore_requires_exclude_mode")
    return entry


def standing_approved(entry):
    """Windows-only per-alias opt-in; legacy export_enabled is NOT approval."""
    approval = entry.get("broker_snapshot_enabled", False)
    if type(approval) is not bool:
        raise PermissionError("invalid_broker_snapshot_enabled")
    return approval

def verified_preview(alias):
    pv = bridge("preview", repo=alias, fingerprint=True)
    if pv.get("status") != "preview" or pv.get("repo_alias") != alias:
        raise RuntimeError("invalid_preview")
    if pv.get("transport_repository") != "AlexPastukhh/chatgpt-snapshot-transfer":
        raise PermissionError("wrong_private_transport")
    sha = pv.get("selection_sha256")
    if type(sha) is not str or not DIGEST.fullmatch(sha):
        raise RuntimeError("missing_selection_fingerprint")
    if pv.get("over_file_limit") or pv.get("over_total_limit") or not pv.get("selected_files"):
        raise PermissionError("preview_out_of_limits")
    return pv

def preview_response(alias, pv):
    keys = ("status", "repo_alias", "mode", "export_enabled", "selected_files",
            "selected_bytes", "excluded_files", "over_file_limit",
            "over_total_limit", "selected_sample", "selection_sha256", "published",
            "transport_repository")
    return {k: pv.get(k) for k in keys}

def grant(alias, minutes, expected_selection):
    if type(alias) is not str or not ALIAS.fullmatch(alias):
        raise ValueError("invalid_alias")
    if type(expected_selection) is not str or not DIGEST.fullmatch(expected_selection):
        raise ValueError("reviewed_selection_sha256_required")
    if not 1 <= minutes <= 30:
        raise ValueError("invalid_expiry_minutes")
    private_entry(alias, registry())
    pv = verified_preview(alias)
    if pv["selection_sha256"] != expected_selection:
        raise PermissionError("selection_changed_since_user_review")
    # Explicit Windows action: this function is never invoked from the shared queue.
    # Approval must refer to current, user-reviewed content/scope.
    permits = read_json(PERMITS, [])
    if not isinstance(permits, list):
        raise RuntimeError("invalid_private_permits")
    for permit in permits:
        if permit.get("repo") == alias and permit.get("state") == "available":
            if now() < dt.datetime.fromisoformat(permit["expires_at"]):
                raise PermissionError("existing_available_permit")
            permit["state"] = "expired"
    permit = dict(id=str(uuid.uuid4()), repo=alias,
                  selection_sha256=pv["selection_sha256"],
                  expires_at=(now() + dt.timedelta(minutes=minutes)).isoformat(),
                  state="available")
    permits.append(permit)
    atomic_json(PERMITS, permits)
    return {"status": "permit_created", "permit_id": permit["id"], "repo": alias,
            "expires_at": permit["expires_at"], "selection_sha256": permit["selection_sha256"],
            "selected_files": pv["selected_files"], "selected_bytes": pv["selected_bytes"],
            "selected_sample": pv.get("selected_sample", [])}

def use_grant(alias, selection, request_id):
    permits = read_json(PERMITS, [])
    if not isinstance(permits, list):
        raise RuntimeError("invalid_private_permits")
    for permit in permits:
        if permit.get("repo") != alias or permit.get("state") != "available":
            continue
        if now() >= dt.datetime.fromisoformat(permit["expires_at"]):
            continue
        if permit["selection_sha256"] != selection:
            raise PermissionError("approved_content_changed")
        # Consume before any GitHub side effect. Fail closed after a crash.
        permit["state"], permit["request_id"] = "consumed", request_id
        atomic_json(PERMITS, permits)
        return permit["id"]
    raise PermissionError("snapshot_requires_single_use_windows_approval")

def read_journal(request_id):
    return read_json(JOURNAL / (request_id + ".json"))

def update_journal(request_id, record):
    atomic_json(JOURNAL / (request_id + ".json"), record)

def recover(request_id):
    if type(request_id) is not str or not ID.fullmatch(request_id):
        raise ValueError("invalid_request_id")
    record = read_journal(request_id)
    if record is None:
        raise ValueError("unknown_request_id")
    if record.get("op") == "snapshot":
        sid = record["snapshot_id"]
        # A crashed worker may have completed publication without writing a
        # reply. Ask Bridge using the stable ID; do not re-run snapshot.
        try:
            result = bridge("status", snapshot_id=sid, wait_seconds=4)
        except Exception:
            result = {"status": "unknown_or_not_started", "snapshot_id": sid}
        return {"request_id": request_id, "snapshot_id": sid,
                "operation": "snapshot", "result": result}
    return {"request_id": request_id, "status": record.get("state", "unknown"),
            "result": record.get("result")}

def handle(message):
    if type(message) is not dict or message.get("version") != 1:
        raise ValueError("invalid_protocol")
    if set(message) - {"version", "id", "op", "repo", "snapshot_id", "request_id"}:
        raise ValueError("unsupported_fields")
    rid = message.get("id")
    if type(rid) is not str or not ID.fullmatch(rid):
        raise ValueError("invalid_request_id")
    op = message.get("op")
    if op not in OPS:
        raise ValueError("operation_not_allowed")
    entries = registry()
    if op == "list":
        if set(message) != {"version", "id", "op"}:
            raise ValueError("extra_arguments")
        data = bridge("list")
        return {"status": "ok", "aliases": [
            {"alias": r["alias"], "export_enabled": bool(r.get("export_enabled")),
             "broker_private": entries[r["alias"]].get("transport") == "private_bridge",
             "broker_snapshot_enabled": entries[r["alias"]].get("broker_snapshot_enabled") is True}
            for r in data.get("repositories", []) if r.get("alias") in entries
        ]}
    if op == "recover":
        if set(message) != {"version", "id", "op", "request_id"}:
            raise ValueError("extra_arguments")
        return recover(message["request_id"])
    if op in ("preview", "snapshot"):
        if set(message) != {"version", "id", "op", "repo"}:
            raise ValueError("extra_arguments")
        alias = message["repo"]
        if type(alias) is not str or not ALIAS.fullmatch(alias) or alias not in entries:
            raise ValueError("repo_not_allowed")
        if op == "preview":
            pv = bridge("preview", repo=alias, fingerprint=True)
            return preview_response(alias, pv)
        entry = private_entry(alias, entries)
        # Reusing a request UUID must never launch the same mutation twice.
        prior = read_journal(rid)
        if prior:
            return recover(rid)
        # Only an explicit Windows-only per-alias opt-in permits repeat exports.
        # Otherwise keep the original V1 one-use content-bound permit gate.
        pv = verified_preview(alias)
        if standing_approved(entry):
            permit_id, authorization = None, "standing_alias"
        else:
            permit_id = use_grant(alias, pv["selection_sha256"], rid)
            authorization = "one_shot"
        stamp = now()
        sid = alias + "-" + stamp.strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
        record = dict(op="snapshot", repo=alias, snapshot_id=sid,
                      permit_id=permit_id, authorization=authorization,
                      state="reserved", created_at=stamp.isoformat())
        update_journal(rid, record)
        issued = read_json(STATE, {})
        issued[sid] = {"repo": alias, "request_id": rid, "created_at": stamp.isoformat()}
        atomic_json(STATE, issued)
        # Bridge independently verifies actual file bytes against permit digest.
        try:
            result = bridge("snapshot", repo=alias, snapshot_id=sid,
                            expected_selection_sha256=pv["selection_sha256"],
                            wait_seconds=0)
            record.update(state="submitted", result=result)
            update_journal(rid, record)
            return result
        except Exception:
            record["state"] = "uncertain"
            update_journal(rid, record)
            raise
    if op == "status":
        if set(message) != {"version", "id", "op", "snapshot_id"}:
            raise ValueError("extra_arguments")
        sid = message["snapshot_id"]
        if type(sid) is not str or not SNAPID.fullmatch(sid):
            raise ValueError("invalid_snapshot_id")
        if sid not in read_json(STATE, {}):
            raise PermissionError("snapshot_id_not_issued_by_broker")
        return bridge("status", snapshot_id=sid, wait_seconds=4)

def run_once():
    # Attempt recovery of previous private claims. Never execute a snapshot
    # request again after restart: journal contains stable operation identity.
    for claim in sorted(CLAIMS.glob("*.json"))[:20]:
        if not ID.fullmatch(claim.stem) or claim.is_symlink():
            continue
        try:
            request = read_json(claim)
            answer = {"version": 1, "id": claim.stem, "ok": True,
                      "result": recover(claim.stem)}
        except Exception:
            answer = {"version": 1, "id": claim.stem, "ok": False,
                      "error": "request_interrupted_check_state"}
        atomic_json(OUTBOX / (claim.stem + ".json"), answer)
        claim.unlink(missing_ok=True)
    for incoming in sorted(INBOX.glob("*.json"))[:20]:
        if not ID.fullmatch(incoming.stem) or incoming.is_symlink() or not incoming.is_file():
            continue
        rid = incoming.stem
        claim = CLAIMS / incoming.name
        if claim.exists() or claim.is_symlink():
            # Do not delete a pre-existing claim that belongs to a previous
            # attempt. Leave new request for human diagnostic/recovery.
            continue
        try:
            os.replace(incoming, claim)
        except OSError:
            continue
        try:
            if claim.is_symlink() or not claim.is_file() or claim.stat().st_size > 4096:
                raise ValueError("unsafe_request")
            request = read_json(claim)
            if request.get("id") != rid:
                raise ValueError("mismatched_request_id")
            result = handle(request)
            answer = {"version": 1, "id": rid, "ok": True, "result": result}
        except (ValueError, PermissionError) as exc:
            answer = {"version": 1, "id": rid, "ok": False, "error": str(exc)[:160]}
        except Exception:
            answer = {"version": 1, "id": rid, "ok": False,
                      "error": "operation_failed_inspect_recovery"}
        atomic_json(OUTBOX / (rid + ".json"), answer)
        claim.unlink(missing_ok=True)
        print("handled " + rid + " ok=" + str(answer["ok"]), flush=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--grant-repo")
    parser.add_argument("--expected-selection-sha256")
    parser.add_argument("--minutes", type=int, default=10)
    args = parser.parse_args()
    check_dirs()
    if args.grant_repo:
        print(json.dumps(grant(args.grant_repo, args.minutes, args.expected_selection_sha256), ensure_ascii=False))
        return
    if args.once:
        run_once()
        return
    while True:
        run_once()
        time.sleep(1)

if __name__ == "__main__":
    main()