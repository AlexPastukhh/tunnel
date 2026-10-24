"""Private Repo outbox awaiting an unambiguous current-chat registration.

No network, credentials, new registration or user-original migration.
Unbound records never enter the normal metadata/message importers.
"""
import json
import re
import time
import uuid

from store import (_atomic, _dir, _is_link, stage, validate_event,
                   MESSAGE_EVENTS, SENSITIVE_TEXT_RE, _event_body)
from repo_messages import _check_message, stage_assistant

LIMIT = 512
MAX_ENVELOPE = 350 * 1024
NAME = re.compile(r"[0-9]{20}-[0-9a-f]{32}\.json")
# Syntax-only validation adapters, never saved or sent as routing identities.
VALIDATION_SESSION = "rs_" + "0" * 32
VALIDATION_TASK = "task_" + "0" * 32


def folder(root, action):
    if action not in ("event", "message"):
        raise ValueError("bad_pending_action")
    path = _dir(root / "inbox" / "pending-context" / action)
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    # Parents and leaves must all remain within the private Repo state.
    for part in (path.parent, path):
        part.chmod(0o700)
    return path


def check_detail(item, detail):
    if detail is None:
        return
    if (item["event"] in MESSAGE_EVENTS or not isinstance(detail, str) or
            not detail.strip() or len(detail.encode("utf-8")) > 8192 or
            SENSITIVE_TEXT_RE.search(detail) or
            len(_event_body(item["summary"], detail).encode("utf-8")) > 11000):
        raise ValueError("bad_event_detail")


def event_payload(record, session, enrollment):
    return {"version": 2, "event_id": record["record_id"],
            "reporting_session_id": session, "session_task_id": enrollment,
            "task_id": record["task_id"], "route": "repo",
            **{k: record["data"][k] for k in ("sequence", "event", "stage", "summary")}}


def message_payload(record, session, enrollment):
    return {"version": 1, "message_id": "msg_" + record["record_id"],
            "reporting_session_id": session, "session_task_id": enrollment,
            "task_id": record["task_id"], "role": "assistant",
            **record["data"]}


def validate(record):
    if (not isinstance(record, dict) or set(record) != {
            "version", "action", "conversation_id", "task_id", "record_id",
            "created_ns", "data", "binding"} or type(record["version"]) is not int or
            record["version"] != 1 or record["action"] not in ("event", "message") or
            not isinstance(record["conversation_id"], str) or
            not re.fullmatch(r"[A-Za-z0-9-]{8,100}", record["conversation_id"]) or
            not isinstance(record["task_id"], str) or
            not re.fullmatch(r"task_[0-9a-f]{32}", record["task_id"]) or
            not isinstance(record["record_id"], str) or
            not re.fullmatch(r"[0-9a-f]{32}", record["record_id"]) or
            type(record["created_ns"]) is not int or
            not 0 < record["created_ns"] < 10**20 or
            not isinstance(record["data"], dict)):
        raise ValueError("invalid_pending_record")
    binding = record["binding"]
    if binding is not None:
        if (not isinstance(binding, dict) or set(binding) != {"session", "enrollment"} or
                not isinstance(binding["session"], str) or
                not re.fullmatch(r"rs_[0-9a-f]{32}", binding["session"]) or
                not isinstance(binding["enrollment"], str) or
                not re.fullmatch(r"task_[0-9a-f]{32}", binding["enrollment"])):
            raise ValueError("invalid_pending_binding")
    if record["action"] == "event":
        if set(record["data"]) != {"sequence", "event", "stage", "summary", "detail"}:
            raise ValueError("invalid_pending_event")
        item = event_payload(record, VALIDATION_SESSION, VALIDATION_TASK)
        validate_event(item)
        check_detail(item, record["data"]["detail"])
    else:
        if set(record["data"]) != {"kind", "body"}:
            raise ValueError("invalid_pending_message")
        _check_message(message_payload(record, VALIDATION_SESSION, VALIDATION_TASK))
    return record


def encoded(record):
    validate(record)
    raw = json.dumps(record, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    if len(raw) > MAX_ENVELOPE:
        raise ValueError("pending_envelope_too_large")
    return raw


def stage_pending(root, action, chat, task, data, record_id=None):
    record = {"version": 1, "action": action, "conversation_id": chat,
              "task_id": task, "record_id": record_id or uuid.uuid4().hex,
              "created_ns": time.time_ns(), "data": data, "binding": None}
    raw = encoded(record)
    inbox = folder(root, action)
    if sum(1 for p in inbox.iterdir() if NAME.fullmatch(p.name)) >= LIMIT:
        raise ValueError("pending_capacity")
    path = inbox / (f'{record["created_ns"]:020d}-{record["record_id"]}.json')
    _atomic(path, raw)
    if path.read_bytes() != raw:
        raise ValueError("pending_readback_failed")
    return path


def stage_event(root, item, detail=None):
    validate_event(item)
    check_detail(item, detail)
    inbox = _dir(root / "inbox" / "repo")
    if detail is None:
        return stage(inbox, item)
    sidecars = _dir(inbox / ".event_details")
    sidecars.mkdir(mode=0o700, exist_ok=True)
    sidecar = sidecars / (item["event_id"] + ".txt")
    raw = detail.encode("utf-8")
    if sidecar.exists():
        if _is_link(sidecar) or sidecar.read_bytes() != raw:
            raise ValueError("event_detail_conflict")
    else:
        _atomic(sidecar, raw)
    bundle = _dir(inbox / ".event_bundle")
    bundle.mkdir(mode=0o700, exist_ok=True)
    # Leave a harmless sidecar on capacity failure: another retry may need it.
    return stage(bundle, item)


def matching_session(store, chat):
    # Read only registration metadata, not snapshots, events or user text.
    matches = []
    for path in store.sessions_path.iterdir():
        if not path.is_dir() or _is_link(path) or not re.fullmatch(r"rs_[0-9a-f]{32}", path.name):
            continue
        entry = store._session(path.name)
        if entry and entry["route"] == "repo" and entry["conversation_id"] == chat:
            matches.append(entry)
    return matches[0] if len(matches) == 1 else None


def poll_pending(root, store):
    report = {"staged": 0, "waiting_context": 0, "retryable": 0, "refused": 0}
    for action in ("event", "message"):
        inbox = folder(root, action)
        for path in sorted(inbox.iterdir())[:LIMIT]:
            if not NAME.fullmatch(path.name):
                continue
            try:
                if _is_link(path) or not path.is_file() or path.stat().st_size > MAX_ENVELOPE:
                    raise ValueError("unsafe_pending_file")
                record = validate(json.loads(path.read_text(encoding="ascii")))
                if record["action"] != action:
                    raise ValueError("pending_action_mismatch")
                if path.name != f'{record["created_ns"]:020d}-{record["record_id"]}.json':
                    raise ValueError("pending_filename_mismatch")
                binding = record["binding"]
                if binding is None:
                    entry = matching_session(store, record["conversation_id"])
                    if entry is None:
                        report["waiting_context"] += 1
                        continue
                    binding = {"session": entry["reporting_session_id"], "enrollment": entry["task_id"]}
                    # Pin before forwarding: retries never choose another session.
                    record["binding"] = binding
                    _atomic(path, encoded(record))
                entry = store._session(binding["session"])
                if (not entry or entry["route"] != "repo" or
                        entry["conversation_id"] != record["conversation_id"] or
                        entry["task_id"] != binding["enrollment"] or
                        record["task_id"] == entry["task_id"]):
                    report["waiting_context"] += 1
                    continue
                if action == "event":
                    stage_event(root, event_payload(record, binding["session"], binding["enrollment"]),
                                record["data"]["detail"])
                else:
                    stage_assistant(root / "inbox" / "messages",
                                    message_payload(record, binding["session"], binding["enrollment"]))
                # Forwarding is durable staging, not archive acceptance.
                path.unlink()
                report["staged"] += 1
            except OSError:
                report["retryable"] += 1
            except (ValueError, UnicodeError, TypeError, KeyError):
                # Retain malformed/capacity-blocked data; never expose body in logs.
                report["refused"] += 1
    return report
