"""File-first, opt-in Fortis Observatory V1.

Owner archive contains Markdown as the only user-facing history. A small
receipt index only prevents stale inbox replays; it contains event IDs,
not message text. Writers control only their independently authorized inbox.
"""
from __future__ import annotations

from datetime import datetime, timezone
import heapq
import hashlib
import json
import math
import os
from pathlib import Path
import re
import secrets
import stat
import time
import uuid
from urllib.parse import urlsplit

EVENTS = frozenset(("started", "progress", "checkpoint", "blocked", "completed", "failed"))
MESSAGE_EVENTS = frozenset(("user_message", "assistant_message"))
ALL_EVENTS = EVENTS | MESSAGE_EVENTS
MESSAGE_SUMMARIES = {"user_message": "Получено сообщение пользователя",
                     "assistant_message": "Ответ ChatGPT заявлен отправителем"}
STAGES = frozenset(("planning", "editing", "testing", "waiting_tool", "reviewing", "other"))
ROUTES = frozenset(("repo", "g2"))
META_PREFIX = "<!-- fortis-v1 "
MAX_INPUT_BYTES = 2048
MAX_MARKDOWN_BYTES = 16384
MAX_EVENT_DETAIL_BYTES = 8192
MAX_USER_TEXT_BYTES = 512 * 1024
MAX_USER_MESSAGE_FILE_BYTES = 4 * 1024 * 1024
MAX_INPUT_FILES = 512
MAX_SESSIONS = 200
MAX_EVENTS_PER_SESSION = 2000
ID_RE = re.compile(r"^[a-z][a-z0-9_]{2,64}$")
UUID_RE = re.compile(r"^[0-9a-f]{32}$")
SAFE_TEXT_RE = re.compile(r"^[\w .,;:!?()\-–]+$", re.UNICODE)
SENSITIVE_TEXT_RE = re.compile(r"(?i)(?:\b(?:password|secret|bearer|token|api.?key)\b|\bsk-[a-z0-9]+)")


def _safe_text(value, limit):
    if not isinstance(value, str) or not 1 <= len(value) <= limit:
        raise ValueError("invalid_text")
    if not SAFE_TEXT_RE.fullmatch(value) or value != value.strip() or SENSITIVE_TEXT_RE.search(value):
        raise ValueError("unsafe_text")
    return value


def chat_id(url):
    if not isinstance(url, str) or len(url) > 300:
        raise ValueError("invalid_chat_url")
    parsed = urlsplit(url.strip())
    if parsed.scheme != "https" or parsed.netloc.casefold() != "chatgpt.com":
        raise ValueError("unsupported_chat_host")
    parts = parsed.path.strip("/").split("/")
    if len(parts) != 2 or parts[0] != "c" or not re.fullmatch(r"[A-Za-z0-9-]{8,100}", parts[1]):
        raise ValueError("missing_conversation_id")
    return parts[1]


def validate_event(value):
    """V1 legacy events and V2 per-message task correlation (sender-claimed)."""
    common = {"version", "event_id", "reporting_session_id", "task_id",
              "sequence", "route", "event", "stage", "summary"}
    if not isinstance(value, dict) or type(value.get("version")) is not int or value["version"] not in (1, 2):
        raise ValueError("invalid_schema")
    version = value["version"]
    fields = common if version == 1 else common | {"session_task_id"}
    if set(value) != fields:
        raise ValueError("invalid_schema")
    if not isinstance(value["event_id"], str) or not UUID_RE.fullmatch(value["event_id"]):
        raise ValueError("bad_event_id")
    if not isinstance(value["reporting_session_id"], str) or not ID_RE.fullmatch(value["reporting_session_id"]):
        raise ValueError("bad_session_id")
    if not isinstance(value["task_id"], str) or not ID_RE.fullmatch(value["task_id"]):
        raise ValueError("bad_task_id")
    if version == 2:
        if (not re.fullmatch(r"task_[0-9a-f]{32}", value["task_id"]) or
                not isinstance(value["session_task_id"], str) or
                not ID_RE.fullmatch(value["session_task_id"])):
            raise ValueError("bad_v2_identity")
    if type(value["sequence"]) is not int or not 0 <= value["sequence"] <= 999999:
        raise ValueError("bad_sequence")
    if (not isinstance(value["route"], str) or value["route"] not in ROUTES or
            not isinstance(value["event"], str) or
            value["event"] not in (EVENTS if version == 1 else ALL_EVENTS) or
            not isinstance(value["stage"], str) or value["stage"] not in STAGES):
        raise ValueError("bad_enum")
    _safe_text(value["summary"], 140)
    if version == 2 and value["event"] in MESSAGE_EVENTS:
        if value["summary"] != MESSAGE_SUMMARIES[value["event"]] or value["stage"] != "other":
            raise ValueError("unsafe_message_marker")
    return value


def _utc(value=None):
    return datetime.fromtimestamp(time.time() if value is None else value, timezone.utc).isoformat(timespec="seconds")


def _is_link(path):
    info = path.lstat()
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    )


def _dir(path):
    path = Path(path).absolute()
    for parent in reversed([path, *path.parents]):
        if parent.exists() and _is_link(parent):
            raise ValueError("linked_directory_refused")
    return path


def _atomic(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path = Path(path)
    temp = path.with_name(f".{path.name}.{secrets.token_hex(8)}.tmp")
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(payload)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def _event_body(summary, detail=None):
    if detail is None:
        return summary
    # One JSON line keeps arbitrary newlines/Markdown inert in the event file.
    payload = json.dumps({"detail": detail}, ensure_ascii=True, separators=(",", ":"))
    return summary + "\n\n~~~fortis-event-detail-json\n" + payload + "\n~~~"


def _event_text(body, summary):
    marker = "\n\n~~~fortis-event-detail-json\n"
    if not body.startswith(summary + marker):
        # Legacy events are plain Markdown summaries. Preserve their previous
        # read behavior, including explicit edits in an archive Markdown file.
        return body, None
    encoded = body[len(summary + marker):]
    if not encoded.endswith("\n~~~"):
        raise ValueError("bad_event_detail_fence")
    decoded = json.loads(encoded[:-4])
    if not isinstance(decoded, dict) or set(decoded) != {"detail"}:
        raise ValueError("bad_event_detail_structure")
    detail = decoded["detail"]
    if not isinstance(detail, str) or not detail.strip() or len(detail.encode("utf-8")) > MAX_EVENT_DETAIL_BYTES:
        raise ValueError("bad_event_detail")
    return summary, detail


def _md(meta, title, body):
    return (META_PREFIX + json.dumps(meta, ensure_ascii=False, separators=(",", ":"))
            + " -->\n# " + title + "\n\n" + body + "\n").encode("utf-8")


def _validate_archive_meta(meta, expected_type):
    versions = (1, 2) if expected_type == "event" else (1,)
    if type(meta.get("version")) is not int or meta["version"] not in versions:
        raise ValueError("bad_archive_version")
    if expected_type == "event":
        fields = {"version", "event_id", "reporting_session_id", "task_id",
                  "sequence", "route", "event", "stage", "summary"}
        if meta["version"] == 2:
            fields.add("session_task_id")
        validate_event({key: meta.get(key) for key in fields})
        if ("sender_sequence" in meta and
                (meta["version"] != 2 or type(meta["sender_sequence"]) is not int or
                 not 0 <= meta["sender_sequence"] <= 999999)):
            raise ValueError("bad_sender_sequence")
        if (type(meta.get("accepted_unix")) not in (int, float) or
                not math.isfinite(meta["accepted_unix"]) or
                not isinstance(meta.get("accepted_at"), str) or
                not isinstance(meta.get("provenance"), str) or
                meta.get("status") != "accepted"):
            raise ValueError("bad_archive_event")
        try:
            parsed = datetime.fromisoformat(meta["accepted_at"])
        except ValueError as exc:
            raise ValueError("bad_archive_timestamp") from exc
        if parsed.tzinfo is None:
            raise ValueError("missing_archive_timezone")
    elif expected_type == "session":
        if (not isinstance(meta.get("reporting_session_id"), str) or
                not ID_RE.fullmatch(meta["reporting_session_id"]) or
                not isinstance(meta.get("task_id"), str) or
                not ID_RE.fullmatch(meta["task_id"]) or
                not isinstance(meta.get("route"), str) or meta["route"] not in ROUTES or
                not isinstance(meta.get("title"), str) or
                not isinstance(meta.get("conversation_id"), str) or
                not re.fullmatch(r"[A-Za-z0-9-]{8,100}", meta["conversation_id"]) or
                meta.get("chat_url") != "https://chatgpt.com/c/" + meta["conversation_id"]):
            raise ValueError("bad_archive_session")


def _read_md(path, expected_type):
    if _is_link(path) or path.stat().st_size > MAX_MARKDOWN_BYTES:
        raise ValueError("unsafe_markdown_file")
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if len(lines) < 4 or not lines[0].startswith(META_PREFIX) or not lines[0].endswith(" -->"):
        raise ValueError("bad_markdown_metadata")
    meta = json.loads(lines[0][len(META_PREFIX):-4])
    if not isinstance(meta, dict) or meta.get("type") != expected_type:
        raise ValueError("wrong_record_type")
    _validate_archive_meta(meta, expected_type)
    if not lines[1].startswith("# "):
        raise ValueError("missing_title")
    return meta, "\n".join(lines[3:]).strip()[:12288 if expected_type == "event" else 4096]


class Store:
    def __init__(self, archive, inboxes=None):
        self.archive = _dir(archive)
        self.archive.mkdir(parents=True, exist_ok=True)
        self.sessions_path = self.archive / "sessions"
        if self.sessions_path.exists() and _is_link(self.sessions_path):
            raise ValueError("linked_sessions_directory_refused")
        self.sessions_path.mkdir(exist_ok=True)
        self.receipts_path = self.archive / ".imported-ids.jsonl"
        self.inboxes = {route: _dir(directory) for route, directory in (inboxes or {}).items()
                        if route in ROUTES}
        self.recent_ingest = {"state": "not_checked", "accepted": 0, "rejected": 0,
                              "duplicate": 0, "unknown_session": 0, "deferred_session": 0,
                              "retryable": 0, "error": 0}
        self._seen = set()
        self._cursor = {}  # Fair per-route rotation when some inputs need a retry.
        self.user_message_ids = self.archive / ".user-message-ids.jsonl"
        self._stored_user_tasks = set()
        if self.user_message_ids.is_symlink() or (self.user_message_ids.exists() and
                not self.user_message_ids.is_file()):
            raise ValueError("unsafe_user_message_receipts")
        if self.user_message_ids.is_file():
            if _is_link(self.user_message_ids) or self.user_message_ids.stat().st_size > 16 * 1024 * 1024:
                raise ValueError("unsafe_user_message_receipts")
            for line in self.user_message_ids.read_text(encoding="ascii").splitlines():
                parts = line.split(" ")
                if (len(parts) != 2 or not re.fullmatch(r"rs_[0-9a-f]{32}", parts[0]) or
                        not re.fullmatch(r"task_[0-9a-f]{32}", parts[1])):
                    raise ValueError("bad_user_message_receipts")
                self._stored_user_tasks.add((parts[0], parts[1]))
        if self.receipts_path.is_file():
            if _is_link(self.receipts_path) or self.receipts_path.stat().st_size > 16 * 1024 * 1024:
                raise ValueError("unsafe_receipts")
            for line in self.receipts_path.read_text(encoding="ascii").splitlines():
                if UUID_RE.fullmatch(line):
                    self._seen.add(line)
                else:
                    raise ValueError("bad_receipts")

    def _session_dir(self, session_id):
        if not isinstance(session_id, str) or not ID_RE.fullmatch(session_id):
            raise ValueError("bad_session_id")
        return self.sessions_path / session_id

    def _session(self, session_id):
        folder = self._session_dir(session_id)
        if folder.exists() and _is_link(folder):
            raise ValueError("linked_session_refused")
        path = folder / "session.md"
        if not path.is_file():
            return None
        meta, body = _read_md(path, "session")
        if meta.get("reporting_session_id") != session_id:
            raise ValueError("session_mismatch")
        return meta

    def observer_key(self, session_id):
        if self._session(session_id) is None:
            raise ValueError("unknown_session")
        target = self._session_dir(session_id) / ".observer-key"
        if target.is_file():
            if _is_link(target) or target.stat().st_size > 100:
                raise ValueError("unsafe_observer_key")
            key = target.read_text(encoding="ascii")
            if not 40 <= len(key) <= 70:
                raise ValueError("bad_observer_key")
            return key
        key = secrets.token_urlsafe(32)
        _atomic(target, key.encode("ascii"))
        return key

    def message_writer_key(self, session_id):
        """Owner-panel-issued, per-session write capability; distinct from observer key."""
        if self._session(session_id) is None:
            raise ValueError("unknown_session")
        target = self._session_dir(session_id) / ".message-writer-key"
        if target.is_file():
            if _is_link(target) or target.stat().st_size > 100:
                raise ValueError("unsafe_message_writer_key")
            value = target.read_text(encoding="ascii")
            if not 40 <= len(value) <= 70:
                raise ValueError("bad_message_writer_key")
            return value
        value = secrets.token_urlsafe(32)
        _atomic(target, value.encode("ascii"))
        return value

    def _verified_writer_session(self, session_id, writer_key):
        session = self._session(session_id)
        if session is None:
            raise ValueError("unknown_session")
        target = self._session_dir(session_id) / ".message-writer-key"
        if not target.is_file() or _is_link(target):
            raise PermissionError("message_writer_not_enabled")
        if not isinstance(writer_key, str) or not secrets.compare_digest(writer_key, self.message_writer_key(session_id)):
            raise PermissionError("message_writer_capability_required")
        return session

    def _user_message_path(self, session_id, task_id):
        folder = self._session_dir(session_id) / "user_messages"
        if folder.exists() and (not folder.is_dir() or _is_link(folder)):
            raise ValueError("unsafe_user_messages_directory")
        return folder / (task_id + ".md")

    def _read_user_message(self, path):
        if not path.is_file() or _is_link(path) or path.stat().st_size > MAX_USER_MESSAGE_FILE_BYTES:
            raise ValueError("unsafe_user_message_file")
        data = path.read_text(encoding="utf-8")
        lines = data.splitlines()
        if len(lines) != 6 or not lines[0].startswith(META_PREFIX) or not lines[0].endswith(" -->") or \
                lines[1:4] != ["# USER MESSAGE", "", "~~~json"] or lines[-1:] != ["~~~"]:
            raise ValueError("bad_user_message_markdown")
        meta = json.loads(lines[0][len(META_PREFIX):-4])
        payload = json.loads(lines[4])
        if (not isinstance(meta, dict) or meta.get("type") != "user_message" or
                meta.get("version") != 1 or not isinstance(payload, dict) or
                set(payload) != {"original_text"} or not isinstance(payload["original_text"], str)):
            raise ValueError("invalid_user_message_archive")
        original = payload["original_text"]
        if (not original or len(original.encode("utf-8")) > MAX_USER_TEXT_BYTES or
                hashlib.sha256(original.encode("utf-8")).hexdigest() != meta.get("sha256")):
            raise ValueError("bad_user_message_hash")
        return meta, original

    def write_user_message(self, session_id, writer_key, task_id, conversation_id, original_text):
        """One immutable full-text record per accepted task, never via Repo inbox."""
        session = self._verified_writer_session(session_id, writer_key)
        if (not isinstance(task_id, str) or not re.fullmatch(r"task_[0-9a-f]{32}", task_id) or
                not isinstance(conversation_id, str) or conversation_id != session["conversation_id"] or
                not isinstance(original_text, str) or not original_text.strip()):
            raise ValueError("invalid_user_message")
        raw = original_text.encode("utf-8")
        if len(raw) > MAX_USER_TEXT_BYTES:
            raise ValueError("user_message_too_long")
        # Read-only activity verifies an already accepted V2 signal, not staged.
        signal = self.task_activity(session_id, self.observer_key(session_id), task_id)
        if not signal["found"]:
            raise ValueError("first_activity_not_accepted")
        path = self._user_message_path(session_id, task_id)
        index_key = (session_id, task_id)
        digest = hashlib.sha256(raw).hexdigest()
        if path.exists() or index_key in self._stored_user_tasks:
            if not path.is_file():
                raise ValueError("user_message_deleted_or_conflicted")
            meta, existing = self._read_user_message(path)
            if (meta.get("reporting_session_id") != session_id or meta.get("task_id") != task_id or
                    meta.get("conversation_id") != conversation_id or existing != original_text):
                raise ValueError("user_message_conflict")
            status = "existing"
        else:
            meta = {"type": "user_message", "version": 1,
                    "reporting_session_id": session_id, "task_id": task_id,
                    "conversation_id": conversation_id, "sha256": digest,
                    "first_activity_at": signal["accepted_unix"],
                    "archived_at": _utc(), "provenance": "notifier_original"}
            payload = {"original_text": original_text}
            # JSON-escaped one-line payload prevents embedded Markdown/HTML
            # from changing file structure. Read-back restores exact Unicode.
            body = (META_PREFIX + json.dumps(meta, ensure_ascii=True, separators=(",", ":")) +
                    " -->\n# USER MESSAGE\n\n~~~json\n" +
                    json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
                    .replace("<", "\\u003c").replace(">", "\\u003e") + "\n~~~\n")
            encoded = body.encode("utf-8")
            if len(encoded) > MAX_USER_MESSAGE_FILE_BYTES:
                raise ValueError("user_message_archive_too_large")
            path.parent.mkdir(exist_ok=True)
            _atomic(path, encoded)
            saved_meta, saved_text = self._read_user_message(path)
            if saved_meta != meta or saved_text != original_text:
                raise ValueError("user_message_readback_failed")
            status = "created"
        if index_key not in self._stored_user_tasks:
            if self.user_message_ids.exists() and _is_link(self.user_message_ids):
                raise ValueError("unsafe_user_message_receipts")
            with self.user_message_ids.open("a", encoding="ascii") as output:
                output.write(session_id + " " + task_id + "\n")
                output.flush()
                os.fsync(output.fileno())
            self._stored_user_tasks.add(index_key)
        return {"version": 1, "reporting_session_id": session_id,
                "conversation_id": conversation_id, "task_id": task_id,
                "archived": True, "sha256": digest,
                "archived_at": saved_meta["archived_at"] if status == "created" else meta["archived_at"],
                "status": status}

    def _verified_observer_session(self, session_id, key):
        """Authorize session-scoped, read-only observer capability."""
        session = self._session(session_id)
        if session is None:
            raise ValueError("unknown_session")
        key_file = self._session_dir(session_id) / ".observer-key"
        if not key_file.is_file() or _is_link(key_file):
            raise PermissionError("observer_not_paired")
        if not isinstance(key, str) or not secrets.compare_digest(key, self.observer_key(session_id)):
            raise PermissionError("read_capability_required")
        return session

    def observer_status(self, session_id, key):
        """Read-only, per-session latest work event; not per-task activity."""
        session = self._verified_observer_session(session_id, key)
        newest = None
        events_dir = self._session_dir(session_id) / "events"
        if events_dir.is_dir() and not _is_link(events_dir):
            for f in events_dir.iterdir():
                if not f.is_file() or _is_link(f) or not re.fullmatch(r"\d{6}-[0-9a-f]{32}\.md", f.name):
                    continue
                try:
                    meta, _ = _read_md(f, "event")
                    if meta["reporting_session_id"] != session_id:
                        continue
                    if f.name != f'{meta["sequence"]:06d}-{meta["event_id"]}.md':
                        continue
                    if meta["event"] in MESSAGE_EVENTS:
                        continue  # Tab Notifier only consumes work start/end, not message markers.
                    if newest is None or (meta["sequence"], meta["accepted_unix"]) > (
                            newest["sequence"], newest["accepted_unix"]):
                        newest = meta
                except (OSError, ValueError, UnicodeError, json.JSONDecodeError):
                    continue
        return {
            "version": 1, "conversation_id": session["conversation_id"],
            "reporting_session_id": session_id,
            "sequence": newest["sequence"] if newest else -1,
            "event": newest["event"] if newest else "none",
            "task_id": newest["task_id"] if newest else None,
            "accepted_unix": newest["accepted_unix"] if newest else None,
            "source": "chat_reported_event",
        }

    def task_activity(self, session_id, key, task_id):
        """First accepted V2 signal for this task, read from owner Markdown.

        Includes sender-claimed work events and message markers. No chat body,
        summary, token, or owner authority is returned. Absence is not proof
        that ChatGPT did not receive the user's message.
        """
        session = self._verified_observer_session(session_id, key)
        if not isinstance(task_id, str) or not re.fullmatch(r"task_[0-9a-f]{32}", task_id):
            raise ValueError("bad_message_task_id")
        first = None
        events_dir = self._session_dir(session_id) / "events"
        if events_dir.exists() and (not events_dir.is_dir() or _is_link(events_dir)):
            raise ValueError("unsafe_events_directory")
        if events_dir.is_dir():
            for f in events_dir.iterdir():
                if not f.is_file() or _is_link(f) or not re.fullmatch(r"\d{6}-[0-9a-f]{32}\.md", f.name):
                    continue
                try:
                    meta, _ = _read_md(f, "event")
                    if (meta["version"] != 2 or meta["reporting_session_id"] != session_id or
                            meta["task_id"] != task_id or
                            meta["session_task_id"] != session["task_id"] or
                            meta["route"] != session["route"] or
                            f.name != f'{meta["sequence"]:06d}-{meta["event_id"]}.md'):
                        continue
                    if first is None or (meta["accepted_unix"], meta["sequence"], meta["event_id"]) < (
                            first["accepted_unix"], first["sequence"], first["event_id"]):
                        first = meta
                except (OSError, ValueError, UnicodeError, json.JSONDecodeError):
                    continue
        return {
            "version": 1, "conversation_id": session["conversation_id"],
            "reporting_session_id": session_id, "task_id": task_id,
            "found": first is not None,
            "sequence": first["sequence"] if first else None,
            "event": first["event"] if first else None,
            "accepted_unix": first["accepted_unix"] if first else None,
            "provenance": "sender_claim" if first else None,
        }

    def register(self, url, route, title):
        if route not in self.inboxes or not self.inboxes[route].is_dir() or _is_link(self.inboxes[route]):
            raise ValueError("route_not_available")
        cid = chat_id(url)
        title = _safe_text(title, 80)
        if len([p for p in self.sessions_path.iterdir() if p.is_dir()]) >= MAX_SESSIONS:
            raise ValueError("session_limit")
        sid = "rs_" + uuid.uuid4().hex
        task = "task_" + uuid.uuid4().hex
        meta = {"type": "session", "version": 1, "conversation_id": cid,
                "chat_url": "https://chatgpt.com/c/" + cid,
                "reporting_session_id": sid, "task_id": task,
                "route": route, "title": title, "created_at": _utc(),
                "tab_session_id": None, "provenance": "manual_registration"}
        folder = self._session_dir(sid)
        folder.mkdir()
        (folder / "events").mkdir()
        _atomic(folder / "session.md", _md(meta, title, "Вручную подключённая сессия."))
        return meta

    def sessions(self):
        results = []
        for folder in sorted(self.sessions_path.iterdir()):
            if len(results) >= MAX_SESSIONS:
                break
            if not folder.is_dir() or _is_link(folder) or not ID_RE.fullmatch(folder.name):
                continue
            try:
                meta = self._session(folder.name)
                if not meta:
                    continue  # deletion of session.md means absent from viewer
                ev_dir = folder / "events"
                events = []
                invalid_files = 0
                truncated_events = False
                if ev_dir.is_dir() and not _is_link(ev_dir):
                    for f in sorted(ev_dir.iterdir()):
                        if len(events) >= MAX_EVENTS_PER_SESSION:
                            truncated_events = True
                            break
                        if not f.is_file() or _is_link(f) or not re.fullmatch(r"\d{6}-[0-9a-f]{32}\.md", f.name):
                            if f.name.endswith(".md"):
                                invalid_files += 1
                            continue
                        try:
                            item, body = _read_md(f, "event")
                            if (item["reporting_session_id"] != folder.name or
                                    f.name != f'{item["sequence"]:06d}-{item["event_id"]}.md'):
                                raise ValueError("archive_identity_mismatch")
                            short, detail = _event_text(body, item["summary"])
                            # Do not inflate /api/state with kilobytes of
                            # long explanations for every historic event.
                            events.append({**item, "summary": short,
                                           "has_detail": detail is not None})
                        except (OSError, ValueError, UnicodeError, json.JSONDecodeError):
                            invalid_files += 1
                            continue
                events.sort(key=lambda item: (item["sequence"], item["accepted_at"]))
                missing = 0
                previous = -1
                for item in events:
                    missing += max(0, item["sequence"] - previous - 1)
                    previous = item["sequence"]
                work_events = [item for item in events if item["event"] in EVENTS]
                logical_last = work_events[-1] if work_events else None
                received_last = max(work_events, key=lambda item: item["accepted_unix"]) if work_events else None
                state = "WAITING"
                if logical_last:
                    state = {"completed": "REPORTED_COMPLETED", "failed": "REPORTED_FAILED",
                             "blocked": "REPORTED_BLOCKED"}.get(logical_last["event"], "WORKING")
                    if state == "WORKING":
                        age = time.time() - received_last["accepted_unix"]
                        factor = 2 if logical_last["stage"] == "waiting_tool" else 1
                        if age >= 3600 * factor:
                            state = "UNKNOWN"
                        elif age >= 900 * factor:
                            state = "SILENT"
                results.append({**meta, "events": events, "last_signal_at": received_last["accepted_at"] if received_last else None,
                                "state": state, "events_count": len(events),
                                "last_task_id": logical_last["task_id"] if logical_last else None,
                                "missing_sequences": missing,
                                "invalid_files": invalid_files,
                                "truncated_events": truncated_events})
            except (OSError, ValueError, UnicodeError, json.JSONDecodeError):
                continue
        return results

    def _receipt(self, event_id):
        # Receipt is replay protection only, never the source of user history.
        with self.receipts_path.open("a", encoding="ascii") as output:
            output.write(event_id + "\n")
            output.flush()
            os.fsync(output.fileno())
        self._seen.add(event_id)

    def _import_one(self, route, candidate):
        if candidate.is_symlink() or _is_link(candidate) or candidate.stat().st_size > MAX_INPUT_BYTES:
            return "rejected"
        raw = candidate.read_bytes()
        if len(raw) > MAX_INPUT_BYTES:
            return "rejected"
        try:
            event = validate_event(json.loads(raw.decode("utf-8")))
        except (ValueError, UnicodeError, TypeError):
            return "rejected"  # Bad sender data is permanent, not a retryable failure.
        if event["route"] != route:
            return "rejected"
        sid = event["reporting_session_id"]
        session = self._session(sid)
        if session is None:
            # Missing enrollment metadata may become available after recovery.
            # Retain the staged file; never call it accepted and never trust it.
            return "deferred_session"
        if session["route"] != route:
            return "unknown_session"  # Existing session, but wrong route: permanently invalid.
        # Legacy V1 keeps the original 1:1 task check. V2 uses that same
        # enrollment value as a sender claim, while task_id identifies a message.
        claimed_enrollment = (event["task_id"] if event["version"] == 1
                              else event["session_task_id"])
        if session["task_id"] != claimed_enrollment:
            return "unknown_session"
        if event["event_id"] in self._seen:
            candidate.unlink(missing_ok=True)
            return "duplicate"
        events_dir = self._session_dir(sid) / "events"
        if not events_dir.is_dir() or _is_link(events_dir):
            return "rejected"
        assigned_sequence = event["sequence"]
        target = events_dir / f'{assigned_sequence:06d}-{event["event_id"]}.md'
        prior = list(events_dir.glob(f'{assigned_sequence:06d}-*.md'))
        if not target.exists() and sum(1 for p in events_dir.iterdir() if p.name.endswith(".md")) >= MAX_EVENTS_PER_SESSION:
            return "rejected"
        if prior and not target.exists():
            if event["version"] == 1:
                return "rejected"  # Strict legacy V1 semantics unchanged.
            # V2 sender-side hints can collide when multiple files accumulate
            # while Observatory is offline. Preserve all distinct event IDs.
            # The receiver owns the *archive* sequence, not the sender.
            assigned_sequence = max(
                (int(f.name[:6]) for f in events_dir.iterdir()
                 if re.fullmatch(r"\d{6}-[0-9a-f]{32}\.md", f.name)),
                default=-1
            ) + 1
            if assigned_sequence > 999999:
                return "rejected"
            target = events_dir / f'{assigned_sequence:06d}-{event["event_id"]}.md'
            if target.exists() or list(events_dir.glob(f'{assigned_sequence:06d}-*.md')):
                return "retryable"
        # New compound event files always require a corresponding sidecar.
        # Legacy root inbox entries remain valid without it.
        compound = route == "repo" and candidate.parent.name == ".event_bundle"
        detail_dir = _dir(self.inboxes[route] / ".event_details")
        detail_path = detail_dir / (event["event_id"] + ".txt")
        detail = None
        if compound and not detail_path.is_file():
            return "retryable"  # No receipt or silent downgrade of detail.
        if detail_path.exists() and compound:
            if (_is_link(detail_path) or not detail_path.is_file() or
                    detail_path.stat().st_size > MAX_EVENT_DETAIL_BYTES):
                return "rejected"
            detail = detail_path.read_text(encoding="utf-8")
            if (not detail.strip() or SENSITIVE_TEXT_RE.search(detail) or
                    len(detail.encode("utf-8")) > MAX_EVENT_DETAIL_BYTES or
                    event["event"] in MESSAGE_EVENTS):
                return "rejected"
        if detail is not None and len(_event_body(event["summary"], detail).encode("utf-8")) > 11000:
            return "rejected"
        if not target.exists():
            accepted = time.time()
            meta = {"type": "event", **event, "sequence": assigned_sequence,
                    **({"sender_sequence": event["sequence"]} if event["version"] == 2 else {}),
                    "accepted_at": _utc(accepted), "accepted_unix": accepted,
                    "provenance": "sender_claim", "status": "accepted"}
            _atomic(target, _md(meta, event["event"].upper(),
                                     _event_body(event["summary"], detail)))
        if target.is_file() and not _is_link(target):
            read_meta, read_body = _read_md(target, "event")
            short, archived_detail = _event_text(read_body, read_meta["summary"])
            if short != event["summary"] or archived_detail != detail:
                return "retryable"
            self._receipt(event["event_id"])
            if detail_path.exists():
                detail_path.unlink(missing_ok=True)
            candidate.unlink(missing_ok=True)
            return "accepted"
        return "rejected"

    def poll(self):
        count = {"state": "available", "accepted": 0, "rejected": 0,
                 "duplicate": 0, "unknown_session": 0, "deferred_session": 0,
                 "retryable": 0, "error": 0}
        for route, inbox in self.inboxes.items():
            try:
                if not inbox.is_dir() or _is_link(inbox):
                    count["state"] = "unavailable"
                    continue
                # Observe at most N+1 names in memory; always drain up to N.
                cursor = self._cursor.get(route, "")
                folders = [inbox]
                if route == "repo":
                    bundles = inbox / ".event_bundle"
                    if bundles.exists():
                        if not bundles.is_dir() or _is_link(bundles):
                            raise ValueError("unsafe_event_bundle_directory")
                        folders.append(bundles)
                paths = heapq.nsmallest(
                    MAX_INPUT_FILES + 1,
                    (p for folder in folders for p in folder.iterdir()
                     if re.fullmatch(r"(?:[0-9]{20}-)?[0-9a-f]{32}\.json", p.name)),
                    key=lambda p: (p.name <= cursor, p.name),
                )
            except (OSError, ValueError):
                count["state"] = "unavailable"
                continue
            if len(paths) > MAX_INPUT_FILES:
                count["state"] = "capacity_exceeded"
            batch = paths[:MAX_INPUT_FILES]
            if batch:
                self._cursor[route] = batch[-1].name
            for path in batch:
                try:
                    result = self._import_one(route, path)
                except (OSError, ValueError, UnicodeError):
                    result = "retryable"  # Leave file for later after repair of archive/disk.
                except Exception:
                    result = "error"  # Per-file isolation, without exposing payload in logs.
                if result in ("rejected", "unknown_session"):
                    # Only permanently invalid files are deleted. Unknown
                    # enrollment is deferred and retained for a future poll.
                    try:
                        path.unlink(missing_ok=True)
                    except OSError:
                        count["state"] = "degraded"
                count[result] += 1
                if result == "deferred_session" and count["state"] == "available":
                    count["state"] = "pending_sessions"
                if result in ("retryable", "error") and count["state"] == "available":
                    count["state"] = "degraded"
        self.recent_ingest = count
        return count


def stage(inbox, event):
    validate_event(event)
    inbox = _dir(inbox)
    if not inbox.is_dir():
        raise ValueError("inbox_not_created")
    if len(list(inbox.glob("*.json"))) >= MAX_INPUT_FILES:
        raise ValueError("inbox_full")
    raw = json.dumps(event, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(raw) > MAX_INPUT_BYTES:
        raise ValueError("event_too_large")
    # Sort by local stage time on import, not by a random UUID. Keep the old
    # UUID-only filename format readable for pre-upgrade accumulated files.
    path = inbox / (f"{time.time_ns():020d}-" + uuid.uuid4().hex + ".json")
    _atomic(path, raw)
    return path
