"""Metadata-only local-save claims, separate from AI events and original archive.

Callers serialize access with Application.lock. Send observations are separate
metadata claims, never platform delivery receipts or accepted AI activity.
"""
import itertools
import json
import math
import re
import secrets
import time

from store import (_atomic, _is_link, _md, _read_md, META_PREFIX,
                   MAX_EVENTS_PER_SESSION)

SID = re.compile(r"rs_[0-9a-f]{32}\Z")
TASK = re.compile(r"task_[0-9a-f]{32}\Z")
KEY = re.compile(r"[A-Za-z0-9_-]{40,70}\Z")
EVENT_FILE = re.compile(r"\d{6}-[0-9a-f]{32}\.md\Z")
MAX_INTENTS = 256
MAX_RECORD_BYTES = 2048
FIELDS = {"version", "reporting_session_id", "conversation_id", "task_id",
          "prepared_at_client_ms"}
RECORD_FIELDS = FIELDS | {"type", "registered_at_unix", "provenance"}
PROVENANCE = "notifier_local_save_claim"
WORK = {"started", "progress", "checkpoint"}
TERMINAL = {"completed", "failed"}
SEND_FIELDS = {"version", "reporting_session_id", "conversation_id", "task_id",
               "revision", "phase", "observed_at_client_ms"}
SEND_PHASES = {"send_requested", "send_unconfirmed", "send_observed", "send_not_attempted"}
STATES = ("prepared", "waiting_ai", "activity_observed", "working", "silent", "unknown",
          "completed", "failed", "blocked")


def strict_object(pairs):
    """Reject duplicate JSON fields rather than silently accepting the last."""
    obj = {}
    for name, value in pairs:
        if name in obj:
            raise ValueError("duplicate_field")
        obj[name] = value
    return obj


def _unsafe(path, directory=False):
    return path.is_symlink() or (path.exists() and (
        _is_link(path) or (not path.is_dir() if directory else not path.is_file())))


class TaskIntents:
    def __init__(self, store):
        self.store = store

    def session(self, sid, conversation_id=None):
        if not isinstance(sid, str) or not SID.fullmatch(sid):
            raise ValueError("bad_intent_session")
        session = self.store._session(sid)
        if session is None or session["route"] != "repo":
            raise ValueError("intent_session_unavailable")
        if conversation_id is not None and conversation_id != session["conversation_id"]:
            raise ValueError("intent_conversation_mismatch")
        return session

    def issue_key(self, sid, conversation_id):
        if not isinstance(conversation_id, str):
            raise ValueError("invalid_intent_conversation")
        self.session(sid, conversation_id)
        path = self.store._session_dir(sid) / ".task-intent-key"
        if _unsafe(path):
            raise ValueError("unsafe_intent_key")
        if path.exists():
            return self._key(path)
        key = secrets.token_urlsafe(32)
        _atomic(path, key.encode("ascii"))
        if self._key(path) != key:
            raise OSError("intent_key_readback_failed")
        return key

    def _key(self, path):
        if _unsafe(path) or not path.is_file() or path.stat().st_size > 70:
            raise PermissionError("intent_key_not_enabled")
        key = path.read_text(encoding="ascii")
        if not KEY.fullmatch(key):
            raise PermissionError("invalid_intent_key")
        return key

    def _authorize(self, sid, key):
        self.session(sid)
        expected = self._key(self.store._session_dir(sid) / ".task-intent-key")
        if not isinstance(key, str) or not secrets.compare_digest(key, expected):
            raise PermissionError("intent_capability_required")

    def _folder(self, sid):
        folder = self.store._session_dir(sid) / "task_intents"
        if _unsafe(folder, directory=True):
            raise ValueError("unsafe_intents_directory")
        return folder

    def _validate(self, body, session, now, existing=False):
        if (not isinstance(body, dict) or set(body) != FIELDS or
                type(body.get("version")) is not int or body["version"] != 1 or
                body["reporting_session_id"] != session["reporting_session_id"] or
                body["conversation_id"] != session["conversation_id"] or
                not isinstance(body["task_id"], str) or not TASK.fullmatch(body["task_id"]) or
                body["task_id"] == session["task_id"] or
                type(body["prepared_at_client_ms"]) is not int or
                not 0 < body["prepared_at_client_ms"] < 4102444800000):
            raise ValueError("invalid_intent")
        # Offline drafts may be old. Client time never determines AI liveness.
        if not existing and body["prepared_at_client_ms"] > now * 1000 + 30000:
            raise ValueError("intent_client_time_in_future")

    def _read(self, path, session):
        if _unsafe(path) or not path.is_file() or path.stat().st_size > MAX_RECORD_BYTES:
            raise ValueError("unsafe_intent_record")
        lines = path.read_text(encoding="utf-8").splitlines()
        if (len(lines) != 4 or not lines[0].startswith(META_PREFIX) or
                not lines[0].endswith(" -->") or lines[1:] != [
                    "# TASK INTENT", "", "Local-save claim; no delivery receipt."]):
            raise ValueError("bad_intent_record")
        record = json.loads(lines[0][len(META_PREFIX):-4], object_pairs_hook=strict_object)
        if (not isinstance(record, dict) or set(record) != RECORD_FIELDS or
                record["type"] != "task_intent" or record["provenance"] != PROVENANCE or
                type(record["registered_at_unix"]) not in (int, float) or
                not math.isfinite(record["registered_at_unix"]) or
                not 0 < record["registered_at_unix"] < 4102444800):
            raise ValueError("invalid_intent_record")
        self._validate({k: record[k] for k in FIELDS}, session, 0, existing=True)
        if path.name != record["task_id"] + ".md":
            raise ValueError("intent_identity_mismatch")
        return record

    def register(self, body, key):
        if not isinstance(body, dict):
            raise ValueError("invalid_intent")
        sid = body.get("reporting_session_id")
        self._authorize(sid, key)
        session = self.session(sid)
        now = time.time()
        self._validate(body, session, now, existing=True)
        folder = self._folder(sid)
        path = folder / (body["task_id"] + ".md")
        if path.exists() or path.is_symlink():
            record = self._read(path, session)
            if any(record[k] != body[k] for k in FIELDS):
                raise ValueError("intent_conflict")
            status = "existing"
        else:
            self._validate(body, session, now)
            if folder.exists() and len(list(itertools.islice(folder.iterdir(), MAX_INTENTS))) >= MAX_INTENTS:
                raise ValueError("intent_limit")
            record = {"type": "task_intent", **body,
                      "registered_at_unix": now, "provenance": PROVENANCE}
            _atomic(path, _md(record, "TASK INTENT", "Local-save claim; no delivery receipt."))
            if self._read(path, session) != record:
                raise OSError("intent_readback_failed")
            status = "created"
        return {"version": 1, "reporting_session_id": sid,
                "conversation_id": session["conversation_id"],
                "task_id": body["task_id"], "registered": True,
                "registered_at_unix": record["registered_at_unix"], "status": status,
                "provenance": PROVENANCE}

    def _send_path(self, sid, task):
        folder = self.store._session_dir(sid) / "task_send_state"
        if _unsafe(folder, directory=True):
            raise ValueError("unsafe_send_directory")
        return folder / (task + ".md")

    def _validate_send(self, body, session):
        if (not isinstance(body, dict) or set(body) != SEND_FIELDS or
                type(body.get("version")) is not int or body["version"] != 1 or
                body["reporting_session_id"] != session["reporting_session_id"] or
                body["conversation_id"] != session["conversation_id"] or
                not isinstance(body["task_id"], str) or not TASK.fullmatch(body["task_id"]) or
                body["task_id"] == session["task_id"] or
                type(body["revision"]) is not int or not 1 <= body["revision"] <= 1000000 or
                not isinstance(body["phase"], str) or body["phase"] not in SEND_PHASES or
                type(body["observed_at_client_ms"]) is not int or
                not 0 < body["observed_at_client_ms"] < 4102444800000):
            raise ValueError("invalid_send_state")

    def _read_send(self, path, session):
        if _unsafe(path) or not path.is_file() or path.stat().st_size > MAX_RECORD_BYTES:
            raise ValueError("unsafe_send_record")
        lines = path.read_text(encoding="utf-8").splitlines()
        if (len(lines) != 4 or not lines[0].startswith(META_PREFIX) or
                not lines[0].endswith(" -->") or lines[1:] != [
                    "# SEND STATE", "", "Notifier observation; no delivery receipt."]):
            raise ValueError("bad_send_record")
        record = json.loads(lines[0][len(META_PREFIX):-4], object_pairs_hook=strict_object)
        extra = {"type", "provenance", "accepted_at_unix", "first_requested_at_unix"}
        if (not isinstance(record, dict) or set(record) != SEND_FIELDS | extra or
                record["type"] != "task_send_state" or record["provenance"] != "notifier_send_claim"):
            raise ValueError("invalid_send_record")
        self._validate_send({k: record[k] for k in SEND_FIELDS}, session)
        for field in ("accepted_at_unix", "first_requested_at_unix"):
            value = record[field]
            if field == "first_requested_at_unix" and value is None:
                continue
            if type(value) not in (int, float) or not math.isfinite(value) or not 0 < value < 4102444800:
                raise ValueError("invalid_send_time")
        if path.name != record["task_id"] + ".md":
            raise ValueError("send_identity_mismatch")
        return record

    def send_state(self, body, key):
        if not isinstance(body, dict):
            raise ValueError("invalid_send_state")
        sid = body.get("reporting_session_id")
        self._authorize(sid, key)
        session = self.session(sid)
        self._validate_send(body, session)
        # Registration must be durably accepted first. A Send claim is not activity.
        self._read(self._folder(sid) / (body["task_id"] + ".md"), session)
        path = self._send_path(sid, body["task_id"])
        prior = self._read_send(path, session) if path.exists() or path.is_symlink() else None
        now = time.time()
        if prior and body["revision"] <= prior["revision"]:
            if body["revision"] == prior["revision"] and any(prior[k] != body[k] for k in SEND_FIELDS):
                raise ValueError("send_revision_conflict")
            record = prior
            status = "existing" if body["revision"] == prior["revision"] else "stale"
        else:
            if body["observed_at_client_ms"] > now * 1000 + 30000:
                raise ValueError("send_client_time_in_future")
            if (prior and prior["phase"] in {"send_unconfirmed", "send_observed"} and
                    body["phase"] == "send_not_attempted"):
                raise ValueError("send_attempt_cannot_be_erased")
            first = prior["first_requested_at_unix"] if prior else None
            if body["phase"] == "send_not_attempted":
                first = None  # A new explicit retry starts its own waiting interval.
            if first is None and body["phase"] != "send_not_attempted":
                first = now
            record = {"type": "task_send_state", **body, "accepted_at_unix": now,
                      "first_requested_at_unix": first, "provenance": "notifier_send_claim"}
            _atomic(path, _md(record, "SEND STATE", "Notifier observation; no delivery receipt."))
            if self._read_send(path, session) != record:
                raise OSError("send_readback_failed")
            status = "updated" if prior else "created"
        return {"version": 1, "reporting_session_id": sid,
                "conversation_id": session["conversation_id"], "task_id": body["task_id"],
                "revision": body["revision"], "stored_revision": record["revision"],
                "phase": record["phase"], "status": status, "recorded": True,
                "provenance": "notifier_send_claim"}

    def snapshot(self, sid):
        session = self.session(sid)
        folder = self._folder(sid)
        records = {}
        if folder.exists():
            paths = list(itertools.islice(folder.iterdir(), MAX_INTENTS + 1))
            if len(paths) > MAX_INTENTS:
                raise ValueError("intent_limit")
            for path in paths:
                # Corruption is explicit, never a silent disappearance of a draft.
                record = self._read(path, session)
                records[record["task_id"]] = record
        by_task = {task: [] for task in records}
        events_dir = self.store._session_dir(sid) / "events"
        if _unsafe(events_dir, directory=True):
            raise ValueError("unsafe_events_directory")
        invalid = 0
        truncated = False
        if events_dir.is_dir():
            paths = sorted(events_dir.iterdir())
            for index, path in enumerate(paths):
                if index >= MAX_EVENTS_PER_SESSION:
                    truncated = True
                    break
                if not EVENT_FILE.fullmatch(path.name):
                    invalid += 1
                    continue
                try:
                    event, _ = _read_md(path, "event")
                    if (event["reporting_session_id"] != sid or
                            event["route"] != session["route"] or
                            path.name != f'{event["sequence"]:06d}-{event["event_id"]}.md'):
                        raise ValueError("event_identity_mismatch")
                    if event["version"] != 2:
                        continue  # Legacy session task is not a per-message task.
                    if event["session_task_id"] != session["task_id"]:
                        raise ValueError("event_enrollment_mismatch")
                    by_task.setdefault(event["task_id"], []).append(event)
                except (OSError, ValueError, UnicodeError, TypeError, KeyError):
                    invalid += 1
        tasks = []
        now = time.time()
        for task, events in sorted(by_task.items()):
            events.sort(key=lambda e: (e["sequence"], e["event_id"]))
            work = [e for e in events if e["event"] in WORK]
            control = [e for e in events if e["event"] in WORK | {"blocked"}]
            terminal = next((e for e in events if e["event"] in TERMINAL), None)
            send_path = self._send_path(sid, task)
            send = self._read_send(send_path, session) if send_path.exists() or send_path.is_symlink() else None
            state = "activity_observed" if events else "prepared"
            if send and send["phase"] != "send_not_attempted":
                state = "waiting_ai"
            if terminal:
                state = terminal["event"]
            elif control:
                state = "blocked" if control[-1]["event"] == "blocked" else "working"
                if state == "working":
                    age = now - max(e["accepted_unix"] for e in work)
                    factor = 2 if control[-1]["stage"] == "waiting_tool" else 1
                    if age >= 3600 * factor:
                        state = "unknown"
                    elif age >= 900 * factor:
                        state = "silent"
            record = records.get(task)
            tasks.append({"task_id": task, "state": state,
                          "send_phase": send["phase"] if send else None,
                          "send_revision": send["revision"] if send else 0,
                          "send_provenance": "notifier_send_claim" if send else None,
                          "waiting_overdue": bool(state == "waiting_ai" and send and
                              send["first_requested_at_unix"] is not None and
                              now - send["first_requested_at_unix"] >= 900),
                          "preparation_recorded": record is not None,
                          "prepared_at_client_ms": record["prepared_at_client_ms"] if record else None,
                          "registered_at_unix": record["registered_at_unix"] if record else None,
                          "first_activity_at": min((e["accepted_unix"] for e in events), default=None),
                          "first_work_at": min((e["accepted_unix"] for e in work), default=None),
                          "last_work_at": max((e["accepted_unix"] for e in work), default=None),
                          "terminal_event": terminal["event"] if terminal else None,
                          "preparation_provenance": PROVENANCE if record else None,
                          "activity_provenance": "sender_claim" if events else None})
        return {"version": 1, "reporting_session_id": sid,
                "conversation_id": session["conversation_id"], "tasks": tasks,
                "counts": {state: sum(t["state"] == state for t in tasks) for state in STATES},
                "checked_at_unix": now, "invalid_event_files": invalid,
                "truncated_events": truncated}


# One classifier for the owner export and the future scoped favicon summary.
# Color absence is represented by None, never by a gray state.
DISPLAY = {
    "prepared": (None, "Черновик сохранён · Send не зафиксирован"),
    "waiting_ai": ("yellow", "Ожидает начала работы AI"),
    "activity_observed": ("yellow", "Принят сигнал · начало работы AI не зафиксировано"),
    "working": ("blue", "AI в работе"),
    "silent": ("purple", "Долгое отсутствие активности"),
    "unknown": ("purple", "Длительная тишина · текущее состояние неизвестно"),
    "completed": ("green", "Завершено (сообщено AI)"),
    "failed": ("red", "Ошибка (сообщено AI)"),
    "blocked": (None, "Приостановлено (сообщено AI)"),
}
SEND_LABELS = {
    "send_requested": "Попытка Send подготовлена; факт доставки неизвестен",
    "send_unconfirmed": "Отправка инициирована; подтверждение неизвестно",
    "send_observed": "Наблюдался признак отправки в DOM; это не квитанция ChatGPT",
    "send_not_attempted": "Отказ до нажатия Send; черновик сохранён",
}


def task_display(task):
    state = task.get("state")
    color, label = DISPLAY.get(state, (None, "Нет сведений о состоянии задачи"))
    phase = task.get("send_phase")
    if state == "prepared" and phase == "send_not_attempted":
        label = "Не отправлено · черновик сохранён"
    if state == "waiting_ai" and task.get("waiting_overdue") is True:
        label += " · длительное ожидание (не ошибка)"
    return {"status_color": color, "status_label": label,
            "send_label": SEND_LABELS.get(phase)}


def task_order(task):
    """Message creation order, never last progress or terminal arrival order."""
    prepared = task.get("prepared_at_client_ms")
    first = task.get("first_activity_at")
    registered = task.get("registered_at_unix")
    def valid(value):
        return type(value) in (int, float) and math.isfinite(value) and value > 0
    created = prepared / 1000 if valid(prepared) else first if valid(first) else registered
    return (created if valid(created) else 0,
            registered if valid(registered) else 0, str(task.get("task_id", "")))


def session_overview(snapshot):
    counts = {state: sum(t.get("state") == state for t in snapshot["tasks"]) for state in STATES}
    # A session describes the latest user task. Old open tasks retain their own
    # states but never override it, including after late progress/completion.
    current = max(snapshot["tasks"], key=task_order, default=None)
    primary = current.get("state") if current else None
    view = task_display(current) if current else {
        "status_label": "Нет известных задач", "status_color": None}
    return {"version": 2, "basis": "latest_task", "available": True, "primary_state": primary,
            "primary_label": view["status_label"], "primary_color": view["status_color"],
            "counts": counts, "pending_count": counts["waiting_ai"] + counts["activity_observed"],
            "working_count": counts["working"], "silent_count": counts["silent"] + counts["unknown"],
            "blocked_count": counts["blocked"], "draft_count": counts["prepared"],
            "completed_count": counts["completed"], "failed_count": counts["failed"],
            "checked_at_unix": snapshot["checked_at_unix"],
            "incomplete": bool(snapshot["invalid_event_files"] or snapshot["truncated_events"])}
