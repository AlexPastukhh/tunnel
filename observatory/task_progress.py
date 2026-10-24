"""Optional low-trust chat task progress spool for Fortis Observatory.

The sender writes a bounded JSON event into an explicitly authorized shared
directory. The owner collector READS these files and imports only validated
metadata into its existing local SQLite archive. This is not an owner API,
an authenticated chat identity, or a delivery acknowledgment from Observatory.
"""
from __future__ import annotations

import argparse
from contextlib import closing
import json
import os
from pathlib import Path
import re
import sqlite3
import stat
import time
import uuid

KINDS = frozenset(("started", "progress", "checkpoint", "blocked", "completed", "failed"))
ROUTES = frozenset(("repo", "g2", "both"))
STAGES = frozenset(("planning", "editing", "testing", "waiting_tool", "reviewing", "other"))
IDENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
FILE_NAME = re.compile(r"^[0-9a-f]{32}\.json$")
# The short human descriptions are deliberately NOT free-form chat excerpts.
BAD_MARKERS = re.compile(r"(?i)(?:password|passwd|secret|bearer|api.?key|token|"
                         r"sk-[a-z0-9]|https?://|[a-z]:\\|/home/|/users/|\\\\)")
MAX_BYTES = 2048
MAX_FILES = 512
RETENTION_DAYS = 30
DEFAULT_SILENCE_SECONDS = 900  # conservative provisional threshold, adjust after observation


def _label(value: object, max_len: int) -> str:
    if not isinstance(value, str) or not 1 <= len(value) <= max_len:
        raise ValueError("invalid_description")
    if value != value.strip() or "  " in value:
        raise ValueError("invalid_description")
    # No URLs, file paths, control characters, Markdown or command syntax.
    if BAD_MARKERS.search(value) or any(
        not (c.isalnum() or c == " " or c in ".,:;!?()-") for c in value
    ):
        raise ValueError("unsafe_description")
    return value


def validate(payload: object) -> dict:
    if not isinstance(payload, dict) or set(payload) != {
        "schema_version", "event_id", "task_id", "sequence", "event",
        "stage", "route", "title", "summary"
    }:
        raise ValueError("invalid_event_schema")
    if type(payload["schema_version"]) is not int or payload["schema_version"] != 1:
        raise ValueError("unsupported_schema")
    try:
        ident = str(uuid.UUID(payload["event_id"]))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("invalid_event_id") from exc
    if ident != payload["event_id"] or not IDENT.fullmatch(payload["task_id"]):
        raise ValueError("invalid_ids")
    if type(payload["sequence"]) is not int or not 0 <= payload["sequence"] <= 1_000_000:
        raise ValueError("invalid_sequence")
    if payload["event"] not in KINDS or payload["stage"] not in STAGES or payload["route"] not in ROUTES:
        raise ValueError("invalid_enum")
    result = dict(payload)
    result["title"] = _label(payload["title"], 80)
    result["summary"] = _label(payload["summary"], 140)
    return result


def _connection(db: Path):
    # Same physical archive as native metrics: no second database.
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db), timeout=5.0)
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("""CREATE TABLE IF NOT EXISTS task_events (
        event_id TEXT PRIMARY KEY,
        task_id TEXT NOT NULL,
        sequence INTEGER NOT NULL,
        received_at REAL NOT NULL,
        kind TEXT NOT NULL,
        stage TEXT NOT NULL,
        route_claim TEXT NOT NULL,
        title TEXT NOT NULL,
        summary TEXT NOT NULL,
        UNIQUE(task_id, sequence)
    )""")
    conn.execute("CREATE INDEX IF NOT EXISTS task_events_task ON task_events(task_id, sequence)")
    conn.execute("CREATE INDEX IF NOT EXISTS task_events_received ON task_events(received_at)")
    return conn


def accept(db: Path, payload: object, received_at: float | None = None) -> bool:
    event = validate(payload)
    now = time.time() if received_at is None else received_at
    with closing(_connection(db)) as conn, conn:
        cur = conn.execute("""INSERT OR IGNORE INTO task_events
            (event_id,task_id,sequence,received_at,kind,stage,route_claim,title,summary)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (event["event_id"], event["task_id"], event["sequence"], now,
             event["event"], event["stage"], event["route"], event["title"], event["summary"]))
        return cur.rowcount == 1


def prune(db: Path, now: float | None = None) -> None:
    with closing(_connection(db)) as conn, conn:
        conn.execute("DELETE FROM task_events WHERE received_at < ?",
                     ((time.time() if now is None else now) - RETENTION_DAYS * 86400,))


def tasks(db: Path, now: float | None = None, silence_seconds: int = DEFAULT_SILENCE_SECONDS) -> dict:
    clock = time.time() if now is None else now
    if not db.is_file():
        return {"tasks": [], "coverage": "no_events_recorded"}
    with closing(_connection(db)) as conn:
        rows = conn.execute("""SELECT event_id,task_id,sequence,received_at,
            kind,stage,route_claim,title,summary FROM task_events
            ORDER BY task_id, sequence, received_at""").fetchall()
    grouped = {}
    for event_id, task_id, sequence, received_at, kind, stage, route, title, summary in rows:
        grouped.setdefault(task_id, []).append({
            "event_id": event_id, "sequence": sequence, "received_at": received_at,
            "event": kind, "stage": stage, "route_claim": route,
            "title": title, "summary": summary,
        })
    results = []
    for task_id, history in grouped.items():
        current = history[-1]  # highest sender sequence, NOT latest arrival
        age = max(0, clock - current["received_at"])
        if current["event"] == "completed":
            state = "COMPLETED"
        elif current["event"] == "failed":
            state = "FAILED"
        elif current["event"] == "blocked":
            state = "BLOCKED"
        elif history[0]["event"] != "started":
            state = "UNKNOWN"
        else:
            # A waiting tool is not evidence that the chat is still executing.
            threshold = silence_seconds * (2 if current["stage"] == "waiting_tool" else 1)
            state = ("WORKING" if age < threshold else
                     "SILENT" if age < threshold * 4 else "UNKNOWN")
        results.append({
            "task_id": task_id, "title": current["title"], "stage": current["stage"],
            "route_claim": current["route_claim"], "state": state,
            "last_signal_at": current["received_at"], "silence_seconds": round(age),
            "events_count": len(history), "history": history[-40:],
            "observation": "untrusted_sender_claim",
            "history_truncated": len(history) > 40,
        })
    results.sort(key=lambda row: row["last_signal_at"], reverse=True)
    return {"tasks": results[:100], "coverage": "voluntary_events_only",
            "tasks_truncated": len(results) > 100}


def _read_regular_file(directory: Path, name: str) -> bytes:
    path = directory / name
    if path.is_symlink():
        raise ValueError("symlink_rejected")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_BYTES:
            raise ValueError("oversize_or_nonregular")
        with os.fdopen(fd, "rb", closefd=False) as stream:
            contents = stream.read(MAX_BYTES + 1)
        if len(contents) > MAX_BYTES:
            raise ValueError("oversize")
        return contents
    finally:
        os.close(fd)


def ingest(db: Path, inbox: Path) -> dict:
    """Read-only import; NEVER execute/delete attacker-provided content.

    The owner must approve this inbox separately. Shared files are untrusted;
    Linux O_NOFOLLOW is used where available. Windows reparse point handling
    requires additional owner-side deployment review before enabling live.
    """
    if inbox.is_symlink() or not inbox.is_dir():
        raise OSError("inbox_unavailable")
    items = []
    with os.scandir(inbox) as entries:
        for entry in entries:
            if FILE_NAME.fullmatch(entry.name):
                items.append(entry.name)
                if len(items) > MAX_FILES:
                    raise ValueError("inbox_capacity_exceeded")
    added = rejected = duplicates = 0
    for name in sorted(items):
        try:
            raw = _read_regular_file(inbox, name)
            event = json.loads(raw.decode("utf-8"))
            # Filename is a content-independent UUID; file name is not an identity proof.
            if accept(db, event):
                added += 1
            else:
                duplicates += 1
        except (ValueError, OSError, UnicodeError, json.JSONDecodeError, sqlite3.IntegrityError):
            rejected += 1
    return {"scanned": len(items), "added": added, "duplicate": duplicates, "rejected": rejected}


def queue(inbox: Path, payload: object) -> Path:
    event = validate(payload)
    if inbox.is_symlink() or not inbox.is_dir():
        raise OSError("inbox_must_exist_and_be_authorized")
    if len(list(inbox.glob("*.json"))) >= MAX_FILES:
        raise ValueError("inbox_capacity_exceeded")
    data = (json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    if len(data) > MAX_BYTES:
        raise ValueError("event_too_large")
    name = uuid.uuid4().hex
    temp = inbox / (name + ".part")
    final = inbox / (name + ".json")
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.rename(temp, final)
    finally:
        if temp.exists():
            temp.unlink()
    return final


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Stage an untrusted task event; no delivery receipt")
    parser.add_argument("--inbox", type=Path, required=True)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--sequence", type=int, required=True)
    parser.add_argument("--event", choices=sorted(KINDS), required=True)
    parser.add_argument("--stage", choices=sorted(STAGES), required=True)
    parser.add_argument("--route", choices=sorted(ROUTES), required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--summary", required=True)
    args = parser.parse_args(argv)
    try:
        path = queue(args.inbox, {
            "schema_version": 1, "event_id": str(uuid.uuid4()),
            "task_id": args.task_id, "sequence": args.sequence,
            "event": args.event, "stage": args.stage, "route": args.route,
            "title": args.title, "summary": args.summary,
        })
    except (ValueError, OSError) as exc:
        print(f"NOT_QUEUED: {type(exc).__name__}", flush=True)
        return 1
    print(f"STAGED_ONLY: {path.name}; Observatory acceptance not confirmed", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
