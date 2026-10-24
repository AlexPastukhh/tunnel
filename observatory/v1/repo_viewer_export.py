"""Read-only, bounded Observatory export for an approved owner-local viewer.

Executes inside the same Fortis Repo Docker container as the Observatory.
No owner bearer is printed or accepted on argv. No mutations, writer keys,
session registration, pairing code, or browser/Windows network listener.
"""
import argparse
import json
from datetime import datetime, timezone
import re
import sys
from pathlib import Path

from repo_service import api_call, DEFAULT_ROOT, DEFAULT_PORT

SID = re.compile(r"rs_[0-9a-f]{32}\Z")
TASK = re.compile(r"task_[0-9a-f]{32}\Z")
MAX_OUTPUT = 10 * 1024 * 1024
MAX_TASK_CARDS = 2256


def lifecycle(session, root):
    """Read only: never instantiate Store's directory/key/receipt writer paths."""
    from store import Store, _dir
    from task_intents import TaskIntents, session_overview
    try:
        sessions = _dir(Path(root) / "archive" / "sessions")
        if not sessions.is_dir():
            raise ValueError("missing_sessions")
        reader = Store.__new__(Store)
        reader.sessions_path = sessions
        snapshot = TaskIntents(reader).snapshot(session)
        return snapshot, session_overview(snapshot)
    except (ValueError, OSError, UnicodeError, TypeError, KeyError):
        # A damaged metadata file must not erase the old archive task list.
        return None, {"version": 2, "basis": "latest_task", "available": False, "reason": "task_status_unavailable"}



def session_tasks(session, state, root=None):
    """Sorted archive task cards, with genuine user-original previews only.

    Fallback time comes from the earliest accepted event or assistant record.
    Never manufacture a user original from event summary or AI text.
    """
    if not SID.fullmatch(session or ""):
        raise ValueError("bad_session")
    info = next((item for item in state.get("sessions", []) if
                 item.get("reporting_session_id") == session and
                 item.get("route") == "repo"), None)
    if info is None:
        raise ValueError("session_unavailable")
    root = Path(DEFAULT_ROOT if root is None else root)
    session_dir = root / "archive" / "sessions" / session
    if not session_dir.is_dir() or session_dir.is_symlink():
        raise ValueError("unsafe_session_dir")
    entries = {}
    snapshot, overview = lifecycle(session, root)

    def add(task_id, accepted_at=None, original=None):
        if not isinstance(task_id, str) or not TASK.fullmatch(task_id):
            return
        item = entries.setdefault(task_id, {
            "task_id": task_id, "first_seen_at": None,
            "original_preview": None, "original_received": False})
        if isinstance(accepted_at, (int, float)) and 0 < accepted_at < 4102444800:
            accepted_at = datetime.fromtimestamp(
                accepted_at, timezone.utc).isoformat(timespec="seconds")
        if isinstance(accepted_at, str):
            try:
                parsed = datetime.fromisoformat(accepted_at.replace("Z", "+00:00"))
                if parsed.tzinfo is None:
                    raise ValueError("timezone_required")
                timestamp = parsed.astimezone(timezone.utc).isoformat(timespec="seconds")
                if item["first_seen_at"] is None or timestamp < item["first_seen_at"]:
                    item["first_seen_at"] = timestamp
            except ValueError:
                pass
        if original is not None:
            # Preview is only from the verified *stored exact user original*.
            # The full immutable original remains retrievable in history.
            clean = " ".join(original.split())
            item["original_preview"] = clean[:105] + ("…" if len(clean) > 105 else "")
            item["original_received"] = True

    for event in info.get("events", []):
        add(event.get("task_id"), event.get("accepted_at"))

    user_dir = session_dir / "user_messages"
    if user_dir.exists():
        if not user_dir.is_dir() or user_dir.is_symlink():
            raise ValueError("unsafe_user_messages")
        from store import Store
        # This code is always called inside the authorized Docker archive.
        reader = Store.__new__(Store)
        for path in user_dir.glob("task_*.md"):
            if path.is_symlink():
                raise ValueError("unsafe_user_message_link")
            if not TASK.fullmatch(path.stem):
                continue
            try:
                meta, original = reader._read_user_message(path)
                if (meta.get("reporting_session_id") == session and
                        meta.get("task_id") == path.stem):
                    add(path.stem, meta.get("first_activity_at"), original)
                    if entries[path.stem]["first_seen_at"] is None:
                        add(path.stem, meta.get("archived_at"))
            except (ValueError, OSError, UnicodeError, TypeError):
                continue

    ai_dir = session_dir / "assistant_messages"
    if ai_dir.exists():
        if not ai_dir.is_dir() or ai_dir.is_symlink():
            raise ValueError("unsafe_assistant_messages")
        for path in ai_dir.glob("msg_*.md"):
            if path.is_symlink() or not path.is_file() or path.stat().st_size > 700 * 1024:
                continue
            try:
                with path.open("r", encoding="ascii") as src:
                    header = src.readline(1600)
                marker = "<!-- fortis-repo-message "
                if not header.startswith(marker) or not header.rstrip("\n").endswith(" -->"):
                    continue
                meta = json.loads(header[len(marker):].rstrip("\n")[:-4])
                if meta.get("reporting_session_id") == session:
                    add(meta.get("task_id"), meta.get("accepted_at"))
            except (ValueError, OSError, UnicodeError, TypeError):
                continue
    from task_intents import task_display, task_order
    status_by_task = {}
    if snapshot is not None:
        status_by_task = {item["task_id"]: item for item in snapshot["tasks"]}
        for task_id, item in status_by_task.items():
            add(task_id, item.get("registered_at_unix") or item.get("first_activity_at"))
    for task_id, card in entries.items():
        item = status_by_task.get(task_id, {"state": "untracked"})
        card.update({name: item.get(name) for name in (
            "state", "send_phase", "waiting_overdue", "preparation_recorded",
            "first_work_at", "last_work_at", "terminal_event")})
        card.update(task_display(item))
        card["status_checked_at_unix"] = snapshot["checked_at_unix"] if snapshot else None
    # Use the same message order as the session, without promoting a task on
    # later activity. Archive-only cards retain their old fallback order.
    def card_order(entry):
        order = (task_order(status_by_task[entry["task_id"]])
                 if entry["task_id"] in status_by_task else
                 (datetime.fromisoformat(entry["first_seen_at"]).timestamp()
                  if entry["first_seen_at"] else 0, 0, entry["task_id"]))
        return (order[0] <= 0, *order)  # Missing dates remain after known dates.
    tasks = sorted(entries.values(), key=card_order)
    truncated = len(tasks) > MAX_TASK_CARDS or bool(snapshot and snapshot["truncated_events"])
    tasks = tasks[-MAX_TASK_CARDS:]
    return {"ok": True, "session": session, "tasks": tasks,
            "task_ids": [item["task_id"] for item in tasks], "truncated": truncated,
            "task_status_available": snapshot is not None, "task_overview": overview}


def read_only(action, session=None, task=None):
    if action == "state":
        if session is not None or task is not None:
            raise ValueError("unexpected_id")
        result = api_call(DEFAULT_ROOT, DEFAULT_PORT, "/api/state")
        if not isinstance(result, dict) or result.get("ok") is not True:
            raise ValueError("bad_state")
        # Additive metadata: legacy state stays available for diagnostics.
        result = {**result, "sessions": [{**session, "task_overview":
            lifecycle(session.get("reporting_session_id"), DEFAULT_ROOT)[1]}
            for session in result.get("sessions", []) if isinstance(session, dict)]}
        # No tokens/writer capabilities in the ordinary state response.
        return {"ok": True, "sessions": result.get("sessions", []),
                "ingest": result.get("ingest", {}),
                "messages_ingest": result.get("messages_ingest", {})}
    if action == "tasks":
        if not SID.fullmatch(session or "") or task is not None:
            raise ValueError("invalid_task_listing")
        state = api_call(DEFAULT_ROOT, DEFAULT_PORT, "/api/state")
        return session_tasks(session, state)
    if action == "history":
        if not SID.fullmatch(session or "") or not TASK.fullmatch(task or ""):
            raise ValueError("invalid_ids")
        from urllib.parse import quote
        result = api_call(DEFAULT_ROOT, DEFAULT_PORT,
                          "/api/repo-history?session=" + quote(session) +
                          "&task=" + quote(task))
        if not isinstance(result, dict) or result.get("ok") is not True:
            raise ValueError("bad_history")
        return result
    raise ValueError("forbidden_export_action")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("state", "tasks", "history"))
    parser.add_argument("--session")
    parser.add_argument("--task")
    args = parser.parse_args(argv)
    try:
        result = read_only(args.action, args.session, args.task)
        raw = json.dumps(result, ensure_ascii=True, separators=(",", ":")).encode("ascii")
        if len(raw) > MAX_OUTPUT:
            raise ValueError("response_too_large")
    except (ValueError, OSError, KeyError, TypeError, ConnectionError):
        print('{"ok":false,"error":"read_unavailable"}')
        return 1
    sys.stdout.buffer.write(raw + b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
