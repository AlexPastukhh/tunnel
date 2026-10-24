"""Docker Repo assistant text spool and archived conversation reader.

Full text intentionally stays in Fortis Repo's private internal volume, never
in the shared Workfiles/Repo metadata event inbox or Git. Any authorized Repo
tool process can access this volume; this is NOT Windows-owner-only isolation.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import stat
import time
import uuid

from store import Store, _atomic, _dir, _is_link, _utc

MAX_MESSAGE_BYTES = 256 * 1024
MAX_SPOOL_FILES = 512
ID_RE = re.compile(r"^(?:rs|task|msg)_[0-9a-f]{32}$")
NAME_RE = re.compile(r"^(?:[0-9]{20}-)?[0-9a-f]{32}\.json$")


def _check_message(value):
    if not isinstance(value, dict) or set(value) != {
            "version", "message_id", "reporting_session_id", "session_task_id",
            "task_id", "role", "kind", "body"} or value["version"] != 1:
        raise ValueError("message_invalid_schema")
    for key, kind in (("message_id", "msg"), ("reporting_session_id", "rs"),
                      ("session_task_id", "task"), ("task_id", "task")):
        if not isinstance(value[key], str) or not re.fullmatch(kind + r"_[0-9a-f]{32}", value[key]):
            raise ValueError("message_invalid_id")
    if value["role"] != "assistant" or value["kind"] not in ("interim", "final"):
        raise ValueError("message_invalid_role_or_kind")
    body = value["body"]
    if not isinstance(body, str) or not body.strip() or len(body.encode("utf-8")) > MAX_MESSAGE_BYTES:
        raise ValueError("message_invalid_body")
    return value


def stage_assistant(inbox, message):
    """Atomic file, when collector is stopped. Caller must be authorized Repo."""
    _check_message(message)
    inbox = _dir(inbox)
    if not inbox.is_dir() or _is_link(inbox):
        raise ValueError("message_inbox_missing")
    if sum(1 for p in inbox.iterdir() if NAME_RE.fullmatch(p.name)) >= MAX_SPOOL_FILES:
        raise ValueError("message_spool_full")
    raw = json.dumps(message, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    if len(raw) > 350 * 1024:
        raise ValueError("message_envelope_too_large")
    name = f"{time.time_ns():020d}-{uuid.uuid4().hex}.json"
    path = inbox / name
    _atomic(path, raw)
    return path


class RepoMessages:
    def __init__(self, store: Store, inbox: Path, quarantine: Path):
        self.store = store
        self.inbox = _dir(inbox)
        self.quarantine = _dir(quarantine)
        self.last_import = {"accepted": 0, "duplicate": 0, "deferred": 0,
                            "quarantined": 0, "retryable": 0, "capacity": False}

    def _archive_path(self, session_id, message_id):
        return self.store._session_dir(session_id) / "assistant_messages" / (message_id + ".md")

    def _read(self, path):
        if (not path.is_file() or _is_link(path) or
                path.stat().st_size > 700 * 1024):
            raise ValueError("unsafe_assistant_archive")
        lines = path.read_text(encoding="ascii").splitlines()
        if (len(lines) != 6 or not lines[0].startswith("<!-- fortis-repo-message ") or
                not lines[0].endswith(" -->") or
                lines[1:4] != ["# ASSISTANT MESSAGE", "", "~~~json"] or
                lines[5] != "~~~"):
            raise ValueError("bad_assistant_markdown")
        meta = json.loads(lines[0][len("<!-- fortis-repo-message "):-4])
        payload = json.loads(lines[4])
        if not isinstance(payload, dict) or set(payload) != {"body"}:
            raise ValueError("bad_assistant_payload")
        reconstructed = {k: meta.get(k) for k in (
            "version", "message_id", "reporting_session_id", "session_task_id",
            "task_id", "role", "kind")}
        reconstructed["body"] = payload["body"]
        _check_message(reconstructed)
        if meta.get("sha256") != hashlib.sha256(reconstructed["body"].encode("utf-8")).hexdigest():
            raise ValueError("assistant_digest_mismatch")
        if meta.get("provenance") != "sender_claim":
            raise ValueError("assistant_provenance_invalid")
        return meta, reconstructed["body"]

    def _import_one(self, path):
        if _is_link(path) or path.stat().st_size > 350 * 1024:
            return "quarantined"
        obj = _check_message(json.loads(path.read_text(encoding="utf-8")))
        session = self.store._session(obj["reporting_session_id"])
        if session is None:
            return "deferred"
        if session["route"] != "repo" or obj["session_task_id"] != session["task_id"]:
            return "quarantined"
        archive_path = self._archive_path(obj["reporting_session_id"], obj["message_id"])
        if archive_path.parent.exists() and _is_link(archive_path.parent):
            return "retryable"
        sha = hashlib.sha256(obj["body"].encode("utf-8")).hexdigest()
        if archive_path.exists():
            meta, body = self._read(archive_path)
            if (meta.get("reporting_session_id") == obj["reporting_session_id"] and
                    meta.get("task_id") == obj["task_id"] and
                    meta.get("session_task_id") == obj["session_task_id"] and
                    meta.get("kind") == obj["kind"] and body == obj["body"]):
                path.unlink()
                return "duplicate"
            return "quarantined"
        meta = {k: obj[k] for k in (
            "version", "message_id", "reporting_session_id", "session_task_id",
            "task_id", "role", "kind")}
        meta.update({"sha256": sha, "provenance": "sender_claim",
                     "accepted_at": _utc()})
        body = ( "<!-- fortis-repo-message " +
                 json.dumps(meta, ensure_ascii=True, separators=(",", ":")) +
                 " -->\n# ASSISTANT MESSAGE\n\n~~~json\n" +
                 json.dumps({"body": obj["body"]}, ensure_ascii=True,
                            separators=(",", ":")).replace("<", "\\u003c").replace(">", "\\u003e") +
                 "\n~~~\n").encode("ascii")
        archive_path.parent.mkdir(mode=0o700, exist_ok=True)
        _atomic(archive_path, body)
        found, readback = self._read(archive_path)
        if found != meta or readback != obj["body"]:
            raise ValueError("assistant_readback_failed")
        path.unlink()
        return "accepted"

    def poll(self):
        report = {"accepted": 0, "duplicate": 0, "deferred": 0,
                  "quarantined": 0, "retryable": 0, "capacity": False}
        paths = sorted(p for p in self.inbox.iterdir() if NAME_RE.fullmatch(p.name))
        if len(paths) > MAX_SPOOL_FILES:
            report["capacity"] = True
        for file in paths[:MAX_SPOOL_FILES]:
            try:
                result = self._import_one(file)
            except (ValueError, UnicodeError, json.JSONDecodeError, TypeError):
                result = "quarantined"
            except OSError:
                result = "retryable"
            if result == "quarantined":
                target = self.quarantine / file.name
                try:
                    if target.exists() or _is_link(file):
                        # Don't overwrite prior/quarantined messages or follow symlinks.
                        result = "retryable"
                    else:
                        os.replace(file, target)
                except OSError:
                    result = "retryable"
            report[result] += 1
        self.last_import = report
        return report

    def history(self, session_id, task_id):
        if not isinstance(session_id, str) or not re.fullmatch(r"rs_[0-9a-f]{32}", session_id):
            raise ValueError("invalid_session")
        if not isinstance(task_id, str) or not re.fullmatch(r"task_[0-9a-f]{32}", task_id):
            raise ValueError("invalid_task")
        session = self.store._session(session_id)
        if not session or session["route"] != "repo":
            raise ValueError("session_not_found")
        folder = self.store._session_dir(session_id)
        assistant = []
        msgs = folder / "assistant_messages"
        if msgs.exists():
            if not msgs.is_dir() or _is_link(msgs):
                raise ValueError("unsafe_assistant_folder")
            for path in sorted(msgs.glob("msg_*.md")):
                meta, body = self._read(path)
                if meta["reporting_session_id"] == session_id and meta["task_id"] == task_id:
                    assistant.append({
                        "message_id": meta["message_id"], "kind": meta["kind"],
                        "role": "assistant", "body": body,
                        "accepted_at": meta["accepted_at"], "provenance": "sender_claim"})
        original = None
        original_path = self.store._user_message_path(session_id, task_id)
        if original_path.exists():
            meta, body = self.store._read_user_message(original_path)
            if meta["reporting_session_id"] != session_id or meta["task_id"] != task_id:
                raise ValueError("user_original_identity_mismatch")
            original = body
        # Event detail is read on demand for the selected task, not copied
        # wholesale into /api/state's list of every session.
        from store import _read_md, _event_text
        event_items = []
        events_dir = folder / "events"
        if events_dir.is_dir() and not _is_link(events_dir):
            for path in sorted(events_dir.glob("*.md")):
                if _is_link(path):
                    raise ValueError("unsafe_event_history")
                if not re.fullmatch(r"\d{6}-[0-9a-f]{32}\.md", path.name):
                    continue
                try:
                    meta, text = _read_md(path, "event")
                    if (meta["reporting_session_id"] != session_id or
                            path.name != f'{meta["sequence"]:06d}-{meta["event_id"]}.md' or
                            meta["task_id"] != task_id):
                        continue
                    _, detail = _event_text(text, meta["summary"])
                except (ValueError, OSError, UnicodeError):
                    continue  # Legacy behavior: one damaged event must not hide all history.
                event_items.append({
                    "event": meta["event"], "sequence": meta["sequence"],
                    "event_id": meta["event_id"], "provenance": "sender_claim",
                    **({"detail": detail} if detail is not None else {})})
        return {"version": 1, "session": session_id, "task_id": task_id,
                "original_text": original, "assistant_messages": assistant,
                "events": event_items}
