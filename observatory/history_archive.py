"""Long-term, privacy-minimizing local Observatory export archive.

Keeps only explicitly allowlisted aggregate telemetry and Desktop Commander
metadata, never raw tool arguments, commands, outputs, credentials or guest
files. An export covers AVAILABLE records, not all historical AI operations.
"""
from __future__ import annotations

import csv
from contextlib import closing
from datetime import datetime, timezone
import io
import json
import math
from pathlib import Path
import sqlite3
import time
from zipfile import ZIP_DEFLATED, ZipFile

RETENTION_DAYS = 90
RETENTION_SECONDS = RETENTION_DAYS * 86400
ROUTES = ("g2", "repo")
MAX_EXPORT_ROWS = 300_000
METRIC_COLUMNS = (
    "polled_total", "enqueued_total", "poll_cycles_total", "poll_last_success_at",
    "queue_length", "queue_capacity", "dispatcher_active", "dispatcher_capacity",
    "command_latency_count", "command_latency_avg_ms",
)
TELEMETRY_COLUMNS = ("time_utc", "route", "state", "verified", "mcp_state") + METRIC_COLUMNS
ACTIVITY_COLUMNS = ("time_utc", "route", "tool", "kind", "duration_ms", "outcome", "command_present")
STATE = frozenset(("UP", "DOWN", "UNKNOWN", "STALE"))
MCP_STATE = frozenset(("initialized", "starting", "stopped", "failed", "unknown", "not_initialized", "degraded"))
TOOL_KINDS = frozenset(("terminal", "files", "search", "config", "other"))
OUTCOMES = frozenset(("error", "unverified"))


def timestamp(value):
    if not isinstance(value, str) or len(value) > 40:
        raise ValueError("Use ISO8601 UTC timestamp with timezone")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Invalid ISO8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError("Timestamp must include a timezone")
    return parsed.timestamp()


def _iso(ts):
    return datetime.fromtimestamp(ts, timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _number(value):
    if type(value) not in (int, float):
        return None
    val = float(value)
    return val if math.isfinite(val) and val >= 0 else None


def _metrics(row):
    values = row.get("metrics") if isinstance(row.get("metrics"), dict) else {}
    return {key: _number(values.get(key)) for key in METRIC_COLUMNS}


def _connect(db: Path):
    db.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(db), timeout=6.0)
    connection.execute("PRAGMA busy_timeout=6000")
    connection.executescript("""
        CREATE TABLE IF NOT EXISTS telemetry (
            route TEXT NOT NULL, minute INTEGER NOT NULL, timestamp REAL NOT NULL,
            state TEXT NOT NULL, verified INTEGER NOT NULL, mcp_state TEXT NOT NULL,
            metrics TEXT NOT NULL, PRIMARY KEY(route, minute)
        );
        CREATE INDEX IF NOT EXISTS telemetry_time ON telemetry(timestamp);
        CREATE TABLE IF NOT EXISTS activity (
            route TEXT NOT NULL, event_id TEXT NOT NULL, timestamp REAL NOT NULL,
            tool TEXT NOT NULL, kind TEXT NOT NULL, duration_ms REAL,
            outcome TEXT NOT NULL, command_present INTEGER NOT NULL,
            PRIMARY KEY(route, event_id)
        );
        CREATE INDEX IF NOT EXISTS activity_time ON activity(timestamp);
    """)
    return connection


def insert_telemetry(db: Path, route: str, row: dict):
    if route not in ROUTES or not isinstance(row, dict):
        raise ValueError("Unknown route/telemetry type")
    ts = _number(row.get("sampled_at"))
    if ts is None or not 0 < ts <= time.time() + 120:
        return
    state = row.get("state") if row.get("state") in STATE else "UNKNOWN"
    mcp = row.get("mcp_state") if row.get("mcp_state") in MCP_STATE else "unknown"
    metrics = json.dumps(_metrics(row), separators=(",", ":"), allow_nan=False)
    with closing(_connect(db)) as conn, conn:
        conn.execute("""INSERT OR IGNORE INTO telemetry
            (route,minute,timestamp,state,verified,mcp_state,metrics)
            VALUES(?,?,?,?,?,?,?)""",
            (route, int(ts // 60), ts, state, int(row.get("verified") is True), mcp, metrics))


def insert_activity(db: Path, events: list[dict]):
    rows = []
    for item in events:
        if not isinstance(item, dict) or item.get("route") not in ROUTES:
            continue
        ident = item.get("event_id")
        tool = item.get("tool")
        if not isinstance(ident, str) or len(ident) != 16 or any(c not in "0123456789abcdef" for c in ident):
            continue
        if not isinstance(tool, str) or not tool.isidentifier() or len(tool) > 96:
            continue
        try:
            ts = timestamp(item["timestamp"])
        except (KeyError, TypeError, ValueError, OverflowError):
            continue
        if ts > time.time() + 120 or ts < time.time() - RETENTION_SECONDS:
            continue
        kind = item.get("kind") if item.get("kind") in TOOL_KINDS else "other"
        outcome = item.get("outcome") if item.get("outcome") in OUTCOMES else "unverified"
        duration = _number(item.get("duration_ms"))
        rows.append((item["route"], ident, ts, tool, kind, duration, outcome,
                     int(item.get("command_present") is True)))
    if not rows:
        return
    with closing(_connect(db)) as conn, conn:
        conn.executemany("""INSERT OR IGNORE INTO activity
            (route,event_id,timestamp,tool,kind,duration_ms,outcome,command_present)
            VALUES(?,?,?,?,?,?,?,?)""", rows)


def prune(db: Path, now: float | None = None):
    cutoff = (now or time.time()) - RETENTION_SECONDS
    with closing(_connect(db)) as conn, conn:
        conn.execute("DELETE FROM telemetry WHERE timestamp < ?", (cutoff,))
        conn.execute("DELETE FROM activity WHERE timestamp < ?", (cutoff,))


def coverage(db: Path):
    if not db.is_file():
        return {"telemetry": {"count": 0, "first": None, "last": None},
                "activity": {"count": 0, "first": None, "last": None},
                "retention_days": RETENTION_DAYS,
                "note": "Coverage begins when this collector starts, plus any imported recent rollups"}
    with closing(_connect(db)) as conn:
        result = {}
        for table in ("telemetry", "activity"):
            count, begin, end = conn.execute(
                f"SELECT COUNT(*), MIN(timestamp), MAX(timestamp) FROM {table}").fetchone()
            result[table] = {"count": count, "first": _iso(begin) if begin else None,
                             "last": _iso(end) if end else None}
    result["retention_days"] = RETENTION_DAYS
    result["note"] = "Available records only, not all chats, commands or missing intervals"
    return result


def _query(conn, table, start, end, routes):
    # Values are parameterized; table names are pinned by callers.
    placeholders = ",".join("?" for _ in routes)
    sql = (f"SELECT * FROM {table} WHERE timestamp >= ? AND timestamp <= ? "
           f"AND route IN ({placeholders}) ORDER BY timestamp,route LIMIT ?")
    return conn.execute(sql, (start, end, *routes, MAX_EXPORT_ROWS + 1)).fetchall()


def _csv_bytes(columns, rows):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\r\n")
    writer.writerow(columns)
    writer.writerows(rows)
    return ("\ufeff" + stream.getvalue()).encode("utf-8")


def export_zip(db: Path, start: float | None, end: float | None,
               routes: tuple[str, ...], fmt: str = "csv", source_states: dict | None = None):
    if not routes or any(route not in ROUTES for route in routes):
        raise ValueError("Select G2, Repo or both")
    if fmt not in ("csv", "json"):
        raise ValueError("Format must be csv or json")
    now = time.time()
    begin = start if start is not None else now - RETENTION_SECONDS
    finish = end if end is not None else now
    if not (math.isfinite(begin) and math.isfinite(finish)) or begin > finish:
        raise ValueError("Start must be at or before end")
    if finish - begin > RETENTION_SECONDS + 120:
        # All available archive spans at most 90 days, not unlimited.
        raise ValueError("Requested interval exceeds 90-day retention")
    with closing(_connect(db)) as conn:
        raw_metrics = _query(conn, "telemetry", begin, finish, routes)
        raw_activity = _query(conn, "activity", begin, finish, routes)
    clipped = len(raw_metrics) > MAX_EXPORT_ROWS or len(raw_activity) > MAX_EXPORT_ROWS
    raw_metrics,raw_activity = raw_metrics[:MAX_EXPORT_ROWS],raw_activity[:MAX_EXPORT_ROWS]
    metrics = []
    for route,minute,at,state,verified,mcp,fields in raw_metrics:
        try:
            numeric = _metrics({"metrics": json.loads(fields)})
        except (json.JSONDecodeError, TypeError):
            numeric = _metrics({})
        metrics.append([_iso(at), route, state if state in STATE else "UNKNOWN",
                        bool(verified), mcp if mcp in MCP_STATE else "unknown"] +
                       [numeric[name] for name in METRIC_COLUMNS])
    activity = []
    for route,event_id,at,tool,kind,duration,outcome,present in raw_activity:
        if not isinstance(tool,str) or not tool.isidentifier() or len(tool)>96:
            continue
        activity.append([_iso(at),route,tool,kind if kind in TOOL_KINDS else "other",
                         _number(duration),outcome if outcome in OUTCOMES else "unverified",
                         bool(present)])
    available = {}
    for route in routes:
        available[route] = {}
        for kind, records in (("metrics", metrics), ("tool_activity", activity)):
            timestamps = [r[0] for r in records if r[1] == route]
            available[route][kind] = {
                "count": len(timestamps),
                "first": min(timestamps) if timestamps else None,
                "last": max(timestamps) if timestamps else None,
            }
    manifest = {
        "available_by_route": available,
        "schema": "fortis-observatory-safe-export-v1",
        "generated_at": _iso(now),
        "requested_from": _iso(begin), "requested_to": _iso(finish),
        "selected_routes": list(routes),
        "telemetry_samples": len(metrics), "activity_events": len(activity),
        "truncated_by_export_limit": clipped,
        "retention_days": RETENTION_DAYS,
        "metric_granularity": "at most one sample per route per UTC minute",
        "activity_sources": source_states or {},
        "completeness": "Only recorded data. Empty or gapped periods do not indicate zero operations.",
        "tool_data": "Desktop Commander metadata only, and only if separately configured and readable.",
        "excluded": ["raw commands", "tool arguments", "tool outputs", "API keys",
                     "full chat prompts", "chat IDs", "child processes", "guest-only files"],
        "security": "Export is a local download; protect downloaded files yourself.",
    }
    archive = io.BytesIO()
    with ZipFile(archive, "w", compression=ZIP_DEFLATED, compresslevel=6) as zipfile:
        zipfile.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        for filename, columns, rows in (("metrics", TELEMETRY_COLUMNS, metrics),
                                        ("tool_activity", ACTIVITY_COLUMNS, activity)):
            if fmt == "csv":
                zipfile.writestr(filename + ".csv", _csv_bytes(columns, rows))
            else:
                zipfile.writestr(filename + ".json", json.dumps(
                    [dict(zip(columns, row)) for row in rows], ensure_ascii=False, separators=(",", ":")))
    return archive.getvalue(), manifest
