"""Ephemeral owner-local one-shot commands to an explicitly paired ChatGPT tab.

Nothing persisted on disk, no queue for closed tabs, no automatic retries.
Observer and original-writer keys NEVER authorize execution commands.
"""
from __future__ import annotations

import secrets
import threading
import time
import uuid
import re
from datetime import datetime, timezone

SID = re.compile(r"rs_[0-9a-f]{32}\Z")
CID = re.compile(r"[A-Za-z0-9-]{8,100}\Z")
KEY = re.compile(r"[A-Za-z0-9_-]{40,70}\Z")
DID = re.compile(r"dispatch_[0-9a-f]{32}\Z")
MAX_TEXT_BYTES = 512 * 1024
MODULE_ID = re.compile(r"[a-z0-9][a-z0-9._-]{0,79}\Z")
MAX_MODULES = 100
EVENT_CODES = {"queued","claimed","expired","unconfirmed","inserted",
               "file_attached","send_initiated","refused","preparing",
               "attachment_only","attachment_unconfirmed"}
REFUSAL_REASONS = {"busy","no_composer","native_draft_occupied",
                   "prepared_missing","context_mismatch","attachment_missing",
                   "send_button_not_ready","upload_unconfirmed","duplicate",
                   "modules_unavailable","not_confirmed","unknown"}

# Full owner-readable Notifier diagnostics are a closed allowlist, not an
# arbitrary browser string. They contain NO source message, file names,
# secret keys, raw DOM or arbitrary error text. This preserves privacy while
# showing exactly the same contextual failure as the Notifier toast.
SAFE_FILE_INSERT_REASONS = frozenset({
    "Нет текста для добавления.",
    "Другая передача уже выполняется.",
    "Редактор ChatGPT недоступен.",
    "Штатный черновик изменился; текст не заменён.",
    "Беседа или редактор изменились. Send не нажимался.",
    "Редактор не принял дополнение. Send не нажимался.",
    "После добавления черновик отличается посимвольно. Send не нажимался.",
    "Не удалось добавить текст.",
    "Нет текста для вставки.",
    "Штатное поле ChatGPT недоступно.",
    "Штатное поле уже содержит текст. Ничего не заменено.",
    "Вкладка или редактор изменились. Вставка остановлена, Send не нажимался.",
    "Редактор изменил часть текста (пробелы, переносы или символы). Исходник сохранён; Send не нажимался.",
    "Редактор ChatGPT не принял часть текста. Send не нажимался.",
    "Вставка не совпала с исходником посимвольно. Исходник сохранён; Send не нажимался.",
    "Не удалось вставить текст.",
})
FILE_FAILURE_PREFIX = "Файл прикреплён, но контекст не добавлен: "
FILE_FAILURE_SUFFIX = " Не отправляй до ручной проверки."
STATIC_FILE_DETAILS = frozenset({
    "Файл прикреплён, модули и Fortis task context добавлены без замены существующего текста. SHA-256 записан, Send НЕ нажат.",
    "Файл прикреплён, но нативный редактор недоступен. Исходник сохранён, Send не нажат.",
    "Не удалось сохранить task_id. Файл прикреплён, Send не нажат.",
    "Модули/контекст слишком длинны для безопасного добавления. Файл прикреплён, но текст не вставлен. Send не нажат.",
    "Карточка файла обнаружена, но Fortis-контекст не подтверждён. Не отправляй сообщение и не прикрепляй файл повторно.",
    "Этот же исходник уже прикреплялся/проверялся подряд (SHA-256 совпал). Повтор не выполняю, независимо от текста или вложений в ChatGPT.",
})
ATTEMPT_DETAIL = re.compile(
    r"Одна попытка прикрепления \((?:input|menu-input|drop)\) выполнена, "
    r"но ChatGPT не подтвердил карточку\. Возможно, файл уже добавлен\. "
    r"Второй попытки НЕ делаю; проверь вложения вручную\. Send не нажат\.\Z"
)

def valid_notifier_file_detail(detail):
    if not isinstance(detail, str) or len(detail) > 512:
        return False
    if detail in STATIC_FILE_DETAILS:
        return True
    if any(detail == FILE_FAILURE_PREFIX + reason + FILE_FAILURE_SUFFIX
           for reason in SAFE_FILE_INSERT_REASONS):
        return True
    return ATTEMPT_DETAIL.fullmatch(detail) is not None

PROFILE_ID = re.compile(r"[a-z0-9][a-z0-9_-]{0,55}\Z")
HEARTBEAT_TTL = 15.0
PENDING_TTL = 20.0
CLAIM_TTL = 40.0


class DispatchBoard:
    """One command in flight per connected session, at-most-once claim."""

    def __init__(self, clock=time.monotonic):
        self._clock = clock
        self._lock = threading.RLock()
        self._sessions = {}

    @staticmethod
    def _log(entry, code, command=None, reason=None, detail=None):
        if code not in EVENT_CODES: raise ValueError("bad_event_code")
        entry.setdefault("history", []).append({
            "event": code, "mode": command.get("mode") if command else None,
            "dispatch_id": command.get("id") if command else None,
            "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            **({"reason": reason} if reason else {}),
            **({"detail": detail} if detail else {}),
            **({"task_id": command["task_id"]} if command and command.get("task_id") else {})
        })
        del entry["history"][:-30]

    @classmethod
    def _expire_command(cls, entry, now):
        command = entry.get("command")
        if not command:
            return
        if command["status"] == "pending" and now - command["created"] > PENDING_TTL:
            command["status"] = "expired"
        elif (command["status"] == "claimed" and
              now - command.get("claimed_at", now) > CLAIM_TTL):
            command["status"] = "unconfirmed"
            cls._log(entry,"unconfirmed",command)
        if command["status"] not in ("pending", "claimed"):
            command.pop("text", None)
            command.pop("module_ids", None)  # Clear expired message, even during polling.
            command.pop("profile_id", None)

    def pair(self, sid, chat):
        if not SID.fullmatch(sid or "") or not CID.fullmatch(chat or ""):
            raise ValueError("bad_session")
        with self._lock:
            entry = self._sessions.get(sid)
            if entry is None or entry["chat"] != chat:
                entry = {"chat": chat, "key": secrets.token_urlsafe(32),
                         "last_seen": 0, "command": None}
                self._sessions[sid] = entry
            return entry["key"]

    def revoke(self, sid):
        if not SID.fullmatch(sid or ""):
            raise ValueError("bad_session")
        with self._lock:
            existed = self._sessions.pop(sid, None) is not None
            return {"ok": True, "revoked": existed}

    def _authorized(self, sid, chat, key):
        entry = self._sessions.get(sid)
        if (entry is None or entry["chat"] != chat or
                not KEY.fullmatch(key or "") or
                not secrets.compare_digest(entry["key"], key)):
            raise PermissionError("dispatch_capability_denied")
        return entry

    def poll(self, sid, chat, key):
        with self._lock:
            entry = self._authorized(sid, chat, key)
            now = self._clock()
            entry["last_seen"] = now
            self._expire_command(entry, now)
            item = entry["command"]
            if item and item["status"] == "pending":
                item["status"] = "claimed"
                item["claimed_at"] = now
                self._log(entry,"claimed",item)
                return {"ok": True, "session": sid, "chat": chat,
                        "command": {"dispatch_id": item["id"],
                                    "mode": item["mode"], "text": item["text"],
                                    "module_ids": item.get("module_ids"),
                                    "profile_id": item.get("profile_id"),
                                    **({"delay_ms":item["delay_ms"]} if "delay_ms" in item else {})}}
            return {"ok": True, "session": sid, "chat": chat, "command": None}

    def status(self, sid):
        if not SID.fullmatch(sid or ""):
            raise ValueError("bad_session")
        with self._lock:
            item = self._sessions.get(sid)
            if item is None:
                return {"ok": True, "available": False, "paired": False,
                        "ever_seen": False, "last_seen_seconds_ago": None,
                        "dispatch": None, "history": []}
            now = self._clock()
            ever_seen = item["last_seen"] > 0
            age = max(0, int(now - item["last_seen"])) if ever_seen else None
            available = ever_seen and now - item["last_seen"] <= HEARTBEAT_TTL
            self._expire_command(item, now)
            command = item["command"]
            result = None if not command else {
                "dispatch_id": command["id"], "mode": command["mode"],
                "status": command["status"],
                **({"task_id": command["task_id"]} if command.get("task_id") else {})}
            return {"ok": True, "available": available,
                    "paired": True, "ever_seen": ever_seen,
                    "last_seen_seconds_ago": age, "dispatch": result,
                    "history": list(item.get("history", [])),
                "modules": item.get("modules", []),
                "default_module_ids": item.get("default_module_ids", []),
                "modules_synced": "modules" in item,
                "profiles": item.get("profiles", []),
                "active_profile_id": item.get("active_profile_id"),
                "profiles_synced": "profiles" in item}

    def update_modules(self, sid, chat, key, modules, default_module_ids=None,
                       profiles=None, active_profile_id=None):
        if default_module_ids is None: default_module_ids=[]
        if profiles is not None:
            if (not isinstance(profiles,list) or not 1<=len(profiles)<=40 or
                not isinstance(active_profile_id,str) or
                not PROFILE_ID.fullmatch(active_profile_id) or
                any(not isinstance(p,dict) or
                    set(p)!={"id","name","module_ids"} or
                    not isinstance(p["id"],str) or not PROFILE_ID.fullmatch(p["id"]) or
                    not isinstance(p["name"],str) or not p["name"].strip() or
                    len(p["name"])>70 or
                    not isinstance(p["module_ids"],list) or len(p["module_ids"])>MAX_MODULES or
                    any(not isinstance(mid,str) or not MODULE_ID.fullmatch(mid)
                        for mid in p["module_ids"]) or
                    len(set(p["module_ids"]))!=len(p["module_ids"])
                    for p in profiles) or
                len({p["id"] for p in profiles})!=len(profiles) or
                active_profile_id not in {p["id"] for p in profiles}):
                raise ValueError("invalid_profiles")
        if (not isinstance(default_module_ids,list) or len(default_module_ids)>MAX_MODULES or
                any(not isinstance(mid,str) or not MODULE_ID.fullmatch(mid)
                    for mid in default_module_ids) or
                len(set(default_module_ids))!=len(default_module_ids) or
                not isinstance(modules,list) or len(modules)>200 or
                any(not isinstance(m,dict) or set(m)!={"id","title"} or
                    not isinstance(m["id"],str) or not MODULE_ID.fullmatch(m["id"]) or
                    not isinstance(m["title"],str) or len(m["title"])>140
                    for m in modules) or
                len({m["id"] for m in modules})!=len(modules)):
            raise ValueError("invalid_module_catalog")
        with self._lock:
            entry=self._authorized(sid,chat,key)
            if not set(default_module_ids).issubset({m["id"] for m in modules}):
                raise ValueError("unknown_default_modules")
            entry["modules"]=[{"id":m["id"],"title":m["title"]} for m in modules]
            entry["default_module_ids"]=list(default_module_ids)
            if profiles is not None:
                entry["profiles"]=[{"id":p["id"],"name":p["name"],
                                    "module_ids":list(p["module_ids"])} for p in profiles]
                entry["active_profile_id"]=active_profile_id
            else:
                # An older Notifier cannot execute selected profile IDs.
                # Do not expose stale profile metadata from a previous client.
                entry.pop("profiles",None)
                entry.pop("active_profile_id",None)
            return {"ok":True,"count":len(modules)}

    def enqueue(self, sid, chat, mode, text, module_ids=None, profile_id=None,
                delay_ms=None):
        if (not SID.fullmatch(sid or "") or not CID.fullmatch(chat or "") or
                (profile_id is not None and
                 (not isinstance(profile_id,str) or not PROFILE_ID.fullmatch(profile_id))) or
                mode not in ("insert", "send", "file", "send_prepared") or not isinstance(text, str) or
                (delay_ms is not None and (mode != "send" or
                 type(delay_ms) is not int or delay_ms not in (500,1000,2000,3000,5000,10000))) or
                (mode != "send_prepared" and not text.strip()) or
                (mode == "send_prepared" and (text or profile_id is not None or module_ids is not None)) or len(text.encode("utf-8")) > MAX_TEXT_BYTES or
                (module_ids is not None and
                 (not isinstance(module_ids,list) or len(module_ids)>MAX_MODULES or
                  any(not isinstance(mid,str) or not MODULE_ID.fullmatch(mid)
                      for mid in module_ids) or len(set(module_ids))!=len(module_ids)))):
            raise ValueError("invalid_dispatch")
        with self._lock:
            entry = self._sessions.get(sid)
            if entry is None or entry["chat"] != chat:
                raise ValueError("session_not_paired_for_dispatch")
            now = self._clock()
            if entry["last_seen"] <= 0 or now - entry["last_seen"] > HEARTBEAT_TTL:
                raise ValueError("tab_not_connected")
            self._expire_command(entry, now)
            previous = entry["command"]
            if previous and previous["status"] in ("pending", "claimed"):
                raise ValueError("dispatch_already_in_flight")
            if profile_id is not None and profile_id not in {
                    p["id"] for p in entry.get("profiles",[])}:
                raise ValueError("unknown_dispatch_profile")
            if module_ids and not set(module_ids).issubset({
                    m["id"] for m in entry.get("modules", [])}):
                raise ValueError("unknown_dispatch_modules")
            item = {"id": "dispatch_" + uuid.uuid4().hex,
                    "mode": mode, "text": text,
                    "module_ids":None if module_ids is None else list(module_ids),
                    "profile_id":profile_id,
                    **({"delay_ms": delay_ms} if delay_ms is not None else {}),
                    "status": "pending", "created": now}
            entry["command"] = item
            self._log(entry,"queued",item)
            return {"ok": True, "dispatch_id": item["id"], "status": "pending"}

    def ack(self, sid, chat, key, dispatch_id, status, task_id=None, reason=None,
            detail=None):
        if (not DID.fullmatch(dispatch_id or "") or
                status not in ("inserted", "file_attached", "send_initiated", "refused",
                               "attachment_only", "attachment_unconfirmed") or
                (task_id is not None and not re.fullmatch(r"task_[0-9a-f]{32}", task_id)) or
                (reason is not None and reason not in REFUSAL_REASONS) or
                (detail is not None and not valid_notifier_file_detail(detail))):
            raise ValueError("invalid_ack")
        if reason is not None and status not in (
                "refused", "attachment_only", "attachment_unconfirmed"):
            raise ValueError("invalid_ack_reason")
        if status in ("attachment_only", "attachment_unconfirmed") and (
                reason is None or task_id is not None):
            raise ValueError("invalid_partial_ack")
        if status == "refused" and task_id is not None:
            raise ValueError("invalid_ack_task")
        if status == "send_initiated" and task_id is None:
            raise ValueError("invalid_ack_task")
        with self._lock:
            entry = self._authorized(sid, chat, key)
            self._expire_command(entry, self._clock())
            command = entry["command"]
            if not command or command["id"] != dispatch_id:
                raise ValueError("unknown_dispatch")
            # Late authentic ACK may resolve an unconfirmed command if
            # its dispatch_id has not been replaced; never replay a Send.
            if command["status"] not in ("claimed", "unconfirmed"):
                raise ValueError("already_acknowledged")
            if detail is not None and (command["mode"] != "file" or status not in
                ("refused", "attachment_only", "attachment_unconfirmed", "file_attached")):
                raise ValueError("invalid_detail_mode")
            if (status == "inserted" and command["mode"] != "insert") or (
                    status in ("file_attached", "attachment_only", "attachment_unconfirmed")
                    and command["mode"] != "file") or (
                    status == "send_initiated" and command["mode"] not in ("send","send_prepared")):
                raise ValueError("ack_mode_mismatch")
            if task_id is not None and status in ("inserted","file_attached") and (
                    command.get("profile_id") is None and command.get("module_ids") is None):
                raise ValueError("invalid_ack_task")
            if status in ("inserted","file_attached") and (
                    command.get("profile_id") is not None) and task_id is None:
                raise ValueError("missing_prepared_task_id")
            command["status"] = status
            command.pop("text", None)
            command.pop("module_ids", None)
            command.pop("profile_id", None)
            if task_id:
                command["task_id"] = task_id
            self._log(entry,status,command,reason,detail)
            return {"ok": True, "status": status}

