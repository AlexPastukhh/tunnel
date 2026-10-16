from __future__ import annotations

import io
import json
import os
import re
import threading
import time
import zipfile
from collections import deque
from datetime import datetime, timezone
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from activity_audit import records as safe_activity_records
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from repo_monitor import collect_repo

ROOT = Path(__file__).resolve().parent
TUNNEL = "http://127.0.0.1:8080"
LISTEN = ("127.0.0.1", int(os.getenv("P1_PORT", "8092")))
FETCH_TIMEOUT = 2.0
SAMPLE_INTERVAL_SECONDS = 5.0
HISTORY_RETENTION_SECONDS = 3600
HISTORY_MAX_SAMPLES = 1000
POST_EVENT_SECONDS = max(5.0, float(os.getenv("P1_POST_EVENT_SECONDS", "120")))
DATA_DIR = Path(os.getenv("P1_DATA_DIR", str(ROOT / "data")))
HISTORY_FILE = DATA_DIR / "history.jsonl"
INCIDENTS_DIR = DATA_DIR / "incidents"

COLLECTOR_LOCK = threading.Lock()
HISTORY_LOCK = threading.Lock()
HISTORY_FILE_LOCK = threading.Lock()
LATEST_LOCK = threading.Lock()
INCIDENT_LOCK = threading.RLock()
HISTORY = deque(maxlen=HISTORY_MAX_SAMPLES)
LATEST_SNAPSHOT = None
LATEST_REPO = None
REPO_LOCK = threading.Lock()
REPO_HISTORY = deque(maxlen=HISTORY_MAX_SAMPLES)
REPO_HISTORY_FILE = DATA_DIR / "repo-history.jsonl"
# Opt-in existing local histories only. An owner process MUST NOT bypass G2 ACLs.
# A path is reported unavailable if the current Windows/Linux user cannot read it.
AUDIT_SOURCES = {
    route: Path(value).expanduser()
    for route, value in (
        ("repo", os.getenv("FORTIS_AUDIT_REPO_HISTORY", "")),
        ("g2", os.getenv("FORTIS_AUDIT_G2_HISTORY", "")),
    )
    if value
}

def activity_feed(limit: int = 50) -> dict:
    limit = min(100, max(1, int(limit)))
    feeds = {}
    for route in ("repo", "g2"):
        if route not in AUDIT_SOURCES:
            feeds[route] = {"route": route, "source_state": "unconfigured",
                            "events": [], "returned": 0,
                            "source_recent_window_incomplete": True}
            continue
        try:
            feeds[route] = safe_activity_records(AUDIT_SOURCES[route], route, limit)
        except (OSError, ValueError):
            feeds[route] = {"route": route, "source_state": "unavailable",
                            "events": [], "returned": 0,
                            "source_recent_window_incomplete": True}
    events = sorted((event for feed in feeds.values() for event in feed["events"]),
                    key=lambda event: event["timestamp"] or "", reverse=True)
    return {"ok": True, "feeds": feeds, "events": events[:limit],
            "coverage": "recent Desktop Commander calls only; commands/arguments/outputs are never sent to web",
            "chat_prompt_visibility": "not available"}

STOP_EVENT = threading.Event()
COLLECTOR = {
    "samples": 0,
    "successes": 0,
    "failures": 0,
    "consecutive_failures": 0,
    "last_success_at": None,
    "last_error_at": None,
    "last_error": None,
}

METRIC_RE = re.compile(r'^([a-zA-Z_:][a-zA-Z0-9_:]*)(?:\{(.*)\})?\s+([^\s]+)$')
LABEL_RE = re.compile(r'([a-zA-Z_][a-zA-Z0-9_]*)="((?:\\.|[^"])*)"')


def fetch(path: str) -> str:
    req = urllib.request.Request(TUNNEL + path, headers={"User-Agent": "tunnel-observatory-p1"})
    with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as response:
        return response.read().decode("utf-8", "replace")


def fetch_json(path: str) -> dict:
    return json.loads(fetch(path))


def parse_labels(raw: str | None) -> dict[str, str]:
    if not raw:
        return {}
    result = {}
    for key, value in LABEL_RE.findall(raw):
        result[key] = bytes(value, "utf-8").decode("unicode_escape")
    return result


def parse_metrics(text: str) -> list[dict]:
    rows = []
    for raw in text.splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        match = METRIC_RE.match(raw)
        if not match:
            continue
        name, label_text, value_text = match.groups()
        try:
            value = float(value_text)
        except ValueError:
            continue
        rows.append({"name": name, "labels": parse_labels(label_text), "value": value})
    return rows


def select(rows: list[dict], name: str, **labels: str) -> list[dict]:
    return [
        row for row in rows
        if row["name"] == name and all(row["labels"].get(k) == v for k, v in labels.items())
    ]


def scalar(rows: list[dict], name: str, default: float = 0.0, **labels: str) -> float:
    found = select(rows, name, **labels)
    return found[0]["value"] if found else default


def command_latency(rows: list[dict], latency_type: str, status: str = "200") -> dict:
    common = {
        "request_method": "tools/call",
        "latency_type": latency_type,
        "tunnel_service_status": status,
    }
    count = scalar(rows, "command_end_to_end_latency_milliseconds_count", **common)
    total = scalar(rows, "command_end_to_end_latency_milliseconds_sum", **common)
    buckets = {}
    for row in select(rows, "command_end_to_end_latency_milliseconds_bucket", **common):
        buckets[row["labels"].get("le", "?")] = row["value"]
    return {
        "count": count,
        "sum_ms": total,
        "avg_ms": (total / count) if count else None,
        "buckets": buckets,
    }


def http_status_counts(rows: list[dict], method: str, route_suffix: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for row in select(rows, "http_client_request_duration_seconds_count"):
        labels = row["labels"]
        if labels.get("http_request_method") != method:
            continue
        if not labels.get("http_route", "").endswith(route_suffix):
            continue
        status = labels.get("http_response_status_code", "unknown")
        result[status] = int(row["value"])
    return result


def summarize_metrics(rows: list[dict]) -> dict:
    e2e = command_latency(rows, "enqueue_to_response", "200")
    poll = command_latency(rows, "poll_to_response", "200")
    conflict = command_latency(rows, "enqueue_to_response", "409")
    over_10s = None
    if e2e["count"]:
        at_10s = e2e["buckets"].get("10000")
        if at_10s is not None:
            over_10s = int(e2e["count"] - at_10s)
    return {
        "tools_call_200": e2e,
        "tools_call_409": conflict,
        "tools_call_poll_to_response_200": poll,
        "tools_call_over_10s_200": over_10s,
        "poll_http": http_status_counts(rows, "GET", "/poll"),
        "response_http": http_status_counts(rows, "POST", "/response"),
        "poll_cycles": int(scalar(rows, "commands_poll_cycles_total")),
        "poll_errors_timeout": int(scalar(rows, "commands_poll_errors_total", error_kind="timeout")),
        "poll_errors_other": int(scalar(rows, "commands_poll_errors_total", error_kind="other")),
        "commands_polled": int(scalar(rows, "commands_polled_total")),
        "queue_length": int(scalar(rows, "commands_queue_length")),
        "queue_capacity": int(scalar(rows, "commands_queue_capacity")),
        "dispatcher_occupancy": int(scalar(rows, "dispatcher_worker_pool_occupancy")),
        "dispatcher_capacity": int(scalar(rows, "dispatcher_worker_pool_capacity")),
        "liveness": scalar(rows, "liveness"),
        "readiness": scalar(rows, "readiness"),
    }


def seconds_since(iso_value: str | None) -> float | None:
    if not iso_value:
        return None
    try:
        from datetime import datetime, timezone
        value = iso_value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(value)
        return (datetime.now(timezone.utc) - dt).total_seconds()
    except Exception:
        return None


def recent_tunnel_events(limit: int = 1000) -> list[dict]:
    try:
        payload = fetch_json(f"/api/logs?limit={limit}")
    except Exception:
        return []
    result = []
    for event in payload.get("events") or []:
        level = str(event.get("level") or "").upper()
        if level not in {"WARN", "ERROR"}:
            continue
        attrs = event.get("attrs") or {}
        error = str(attrs.get("error") or "")
        if len(error) > 400:
            error = error[:397] + "..."
        result.append({
            "seq": event.get("seq"),
            "time": event.get("time"),
            "level": level,
            "message": str(event.get("message") or ""),
            "error_code": attrs.get("error_code"),
            "status_code": attrs.get("status_code"),
            "retry_in_ms": attrs.get("retry_in_ms"),
            "error": error,
        })
    return result[-40:]


def diagnose(health: dict, metrics: dict, tunnel_events: list[dict]) -> dict:
    components = health.get("components") or {}
    evidence: list[str] = []
    severity = "ok"
    title = "Tunnel path looks healthy"

    if not health.get("live"):
        return {"severity": "bad", "title": "Tunnel process is not live", "evidence": ["health.live=false"]}

    if not health.get("ready"):
        severity, title = "bad", "Tunnel is live but not ready"
        evidence.append("health.ready=false")

    cp = components.get("control-plane", {})
    cpd = cp.get("details") or {}
    if cp.get("status") != "ok" or cpd.get("consecutive_failures", 0):
        severity, title = "warn", "Control-plane polling is degraded"
        evidence.append(f"control-plane={cp.get('state')} failures={cpd.get('consecutive_failures', 0)}")
    else:
        age = seconds_since(cpd.get("last_error"))
        if age is not None and age < 300:
            severity, title = "warn", "Control plane recovered from a recent error"
            evidence.append(f"last control-plane error {int(age)}s ago")

    mcp = components.get("mcp", {})
    mcpd = mcp.get("details") or {}
    init = mcpd.get("initialize") or {}
    if mcp.get("status") != "ok" or mcpd.get("child_state") != "running" or init.get("ok") is False:
        severity, title = "bad", "Local MCP child is degraded"
        evidence.append(f"mcp={mcp.get('state')} child={mcpd.get('child_state')} init={init.get('ok')}")


    queue = components.get("queue", {})
    qd = queue.get("details") or {}
    if qd.get("utilization", 0) >= 0.75 or qd.get("backpressure_seconds", 0) > 0:
        severity, title = "warn", "Local tunnel queue is under backpressure"
        evidence.append(f"queue={qd.get('depth')}/{qd.get('capacity')} backpressure={qd.get('backpressure_seconds')}s")

    dispatcher = components.get("dispatcher", {})
    dd = dispatcher.get("details") or {}
    if dd.get("oldest_active_age_seconds", 0) >= 20:
        severity, title = "warn", "A local MCP operation is taking a long time"
        evidence.append(f"oldest active={dd.get('oldest_active_age_seconds'):.1f}s")

    delivery = components.get("response-delivery", {})
    rd = delivery.get("details") or {}
    delivery_age = seconds_since(rd.get("last_failure"))
    if delivery_age is not None and delivery_age < 300:
        severity, title = "warn", "Response delivery recovered from a recent failure"
        evidence.append(f"last response-delivery failure {int(delivery_age)}s ago")

    recent_network = [
        event for event in tunnel_events
        if event.get("error_code") == "tunnel_transport_unavailable"
        or "network_error" in (event.get("error") or "")
        or "unexpected EOF" in (event.get("error") or "")
    ]
    if recent_network:
        age = seconds_since(recent_network[-1].get("time"))
        if age is not None and age < 300:
            severity, title = "warn", "Recent control-plane transport failure"
            evidence.append(f"transport error {int(age)}s ago: {recent_network[-1].get('message')}")

    if not evidence and severity == "ok":
        evidence.append("live+ready, control-plane ok, MCP child running, queue not backpressured")

    hypothesis = (
        "A 25s chat timeout does not prove the whole tunnel is down. "
        "If local health stays green, check recent transport errors, 409 deltas and whether the request reached the dispatcher."
    )
    return {"severity": severity, "title": title, "evidence": evidence, "hypothesis": hypothesis}


def history_summary(snapshot: dict) -> dict:
    health = snapshot.get("health") or {}
    components = health.get("components") or {}
    cp = components.get("control-plane") or {}
    cpd = cp.get("details") or {}
    mcp = components.get("mcp") or {}
    mcpd = mcp.get("details") or {}
    queue = components.get("queue") or {}
    qd = queue.get("details") or {}
    dispatcher = components.get("dispatcher") or {}
    dd = dispatcher.get("details") or {}
    delivery = components.get("response-delivery") or {}
    rd = delivery.get("details") or {}
    metrics = snapshot.get("metrics") or {}
    calls = metrics.get("tools_call_200") or {}
    poll_calls = metrics.get("tools_call_poll_to_response_200") or {}
    conflicts = metrics.get("tools_call_409") or {}
    diagnosis = snapshot.get("diagnosis") or {}
    return {
        "captured_at": snapshot.get("captured_at"), "ok": bool(snapshot.get("ok")),
        "collector_ms": snapshot.get("collector_ms"),
        "tunnel": {"live": health.get("live"), "ready": health.get("ready")},
        "control_plane": {"status": cp.get("status"), "state": cp.get("state"), "consecutive_failures": cpd.get("consecutive_failures"), "current_poll_age_seconds": cpd.get("current_poll_age_seconds"), "last_error": cpd.get("last_error")},
        "mcp": {"status": mcp.get("status"), "state": mcp.get("state"), "child_state": mcpd.get("child_state"), "initialized": (mcpd.get("initialize") or {}).get("ok"), "initialize_epoch": mcpd.get("initialize_epoch")},
        "queue": {"depth": qd.get("depth"), "capacity": qd.get("capacity"), "backpressure_seconds": qd.get("backpressure_seconds")},
        "dispatcher": {"active": dd.get("active"), "pool_limit": dd.get("pool_limit"), "oldest_active_age_seconds": dd.get("oldest_active_age_seconds"), "failures": dd.get("failures")},
        "response_delivery": {"status": delivery.get("status"), "state": delivery.get("state"), "retries": rd.get("retries"), "terminal_failures": rd.get("terminal_failures"), "last_failure": rd.get("last_failure")},
        "metrics": {"tools_call_200_count": calls.get("count"), "tools_call_200_sum_ms": calls.get("sum_ms"), "tools_call_poll_200_count": poll_calls.get("count"), "tools_call_poll_200_sum_ms": poll_calls.get("sum_ms"), "tools_call_409_count": conflicts.get("count"), "tools_call_over_10s_200": metrics.get("tools_call_over_10s_200"), "poll_errors_timeout": metrics.get("poll_errors_timeout"), "poll_errors_other": metrics.get("poll_errors_other"), "queue_length": metrics.get("queue_length"), "dispatcher_occupancy": metrics.get("dispatcher_occupancy")},
        "diagnosis": {"severity": diagnosis.get("severity"), "title": diagnosis.get("title")},
    }


def prune_history(now: float | None = None) -> list[dict]:
    cutoff = (now or time.time()) - HISTORY_RETENTION_SECONDS
    with HISTORY_LOCK:
        retained = [row for row in HISTORY if (row.get("captured_at") or 0) >= cutoff]
        HISTORY.clear()
        HISTORY.extend(retained[-HISTORY_MAX_SAMPLES:])
        return list(HISTORY)


def rewrite_history_file() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    rows = prune_history()
    tmp = HISTORY_FILE.with_suffix(".jsonl.tmp")
    with HISTORY_FILE_LOCK:
        with tmp.open("w", encoding="utf-8", newline="\n") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
        tmp.replace(HISTORY_FILE)


def load_history() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    INCIDENTS_DIR.mkdir(parents=True, exist_ok=True)
    if not HISTORY_FILE.exists():
        return
    cutoff = time.time() - HISTORY_RETENTION_SECONDS
    loaded = []
    try:
        with HISTORY_FILE.open("r", encoding="utf-8") as fh:
            for line in fh:
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if (row.get("captured_at") or 0) >= cutoff:
                    loaded.append(row)
    except OSError:
        return
    with HISTORY_LOCK:
        HISTORY.clear()
        HISTORY.extend(loaded[-HISTORY_MAX_SAMPLES:])
    rewrite_history_file()


def collector_record(ok: bool, error: str | None = None) -> dict:
    now = time.time()
    with COLLECTOR_LOCK:
        COLLECTOR["samples"] += 1
        if ok:
            COLLECTOR["successes"] += 1
            COLLECTOR["consecutive_failures"] = 0
            COLLECTOR["last_success_at"] = now
        else:
            COLLECTOR["failures"] += 1
            COLLECTOR["consecutive_failures"] += 1
            COLLECTOR["last_error_at"] = now
            COLLECTOR["last_error"] = error
        return dict(COLLECTOR)


def build_snapshot() -> dict:
    started = time.perf_counter()
    try:
        health = fetch_json("/health?details=true")
        mcp = fetch_json("/health/mcp")
        rows = parse_metrics(fetch("/metrics"))
        metrics = summarize_metrics(rows)
        tunnel_events = recent_tunnel_events()
        collector = collector_record(True)
        return {
            "ok": True,
            "captured_at": time.time(),
            "collector_ms": round((time.perf_counter() - started) * 1000, 1),
            "collector": collector,
            "health": health,
            "mcp": mcp,
            "metrics": metrics,
            "tunnel_events": tunnel_events,
            "diagnosis": diagnose(health, metrics, tunnel_events),
        }
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        collector = collector_record(False, error)
        return {
            "ok": False,
            "captured_at": time.time(),
            "collector_ms": round((time.perf_counter() - started) * 1000, 1),
            "collector": collector,
            "error": error,
            "diagnosis": {
                "severity": "bad",
                "title": "Local tunnel telemetry is unreachable",
                "evidence": [f"collector error: {type(exc).__name__}"],
            },
        }


def append_history(snapshot: dict) -> dict:
    row = history_summary(snapshot)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with HISTORY_LOCK:
        HISTORY.append(row)
    try:
        with HISTORY_FILE_LOCK:
            with HISTORY_FILE.open("a", encoding="utf-8", newline="\n") as fh:
                fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    except OSError:
        pass
    if (snapshot.get("collector") or {}).get("samples", 0) % 120 == 0:
        try:
            rewrite_history_file()
        except OSError:
            pass
    return row


def history_rows(minutes: float = 60.0) -> list[dict]:
    minutes = max(1.0, min(float(minutes), 60.0))
    cutoff = time.time() - minutes * 60.0
    with HISTORY_LOCK:
        return [row for row in HISTORY if (row.get("captured_at") or 0) >= cutoff]


def latest_snapshot() -> dict | None:
    with LATEST_LOCK:
        return LATEST_SNAPSHOT


def capture_and_store() -> dict:
    global LATEST_SNAPSHOT
    snapshot = build_snapshot()
    append_history(snapshot)
    with LATEST_LOCK:
        LATEST_SNAPSHOT = snapshot
    return snapshot


def capture_repo() -> dict:
    global LATEST_REPO
    result = collect_repo()
    safe = {k: result[k] for k in ("state", "sampled_at", "verified", "mcp_state") if k in result}
    with REPO_LOCK:
        LATEST_REPO = result
        REPO_HISTORY.append(safe)
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with REPO_HISTORY_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(safe, separators=(",", ":")) + "\n")
    except OSError:
        pass
    if len(REPO_HISTORY) % 120 == 0:
        rewrite_repo_history()
    return result


def load_repo_history() -> None:
    if not REPO_HISTORY_FILE.exists():
        return
    cutoff = time.time() - HISTORY_RETENTION_SECONDS
    try:
        lines = REPO_HISTORY_FILE.read_text(encoding="utf-8").splitlines()[-HISTORY_MAX_SAMPLES:]
        with REPO_LOCK:
            for line in lines:
                try:
                    row = json.loads(line)
                    if cutoff <= row.get("sampled_at", 0) <= time.time() + 60:
                        REPO_HISTORY.append(row)
                except (ValueError, TypeError):
                    continue
    except OSError:
        pass


def rewrite_repo_history() -> None:
    cutoff = time.time() - HISTORY_RETENTION_SECONDS
    with REPO_LOCK:
        rows = [r for r in REPO_HISTORY if r.get("sampled_at", 0) >= cutoff]
        REPO_HISTORY.clear()
        REPO_HISTORY.extend(rows)
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        temp = REPO_HISTORY_FILE.with_suffix(".tmp")
        temp.write_text("".join(json.dumps(r, separators=(",", ":")) + "\n" for r in rows), encoding="utf-8")
        temp.replace(REPO_HISTORY_FILE)
    except OSError:
        pass


def repo_history(minutes: float = 60.0) -> dict:
    cutoff = time.time() - max(1.0, min(float(minutes), 60.0)) * 60
    with REPO_LOCK:
        rows = [r for r in REPO_HISTORY if r.get("sampled_at", 0) >= cutoff]
    return {"ok": True, "samples": len(rows), "history": rows}


def latest_repo() -> dict:
    with REPO_LOCK:
        result = LATEST_REPO
    if result is None:
        return {"state": "UNKNOWN", "reason": "Waiting for first Repo sample", "verified": False}
    if time.time() - result.get("sampled_at", 0) > SAMPLE_INTERVAL_SECONDS * 3:
        return {**result, "state": "STALE"}
    return result


def sampler_loop() -> None:
    while not STOP_EVENT.wait(SAMPLE_INTERVAL_SECONDS):
        capture_and_store()
        capture_repo()


INCIDENT_ID_RE = re.compile(r"^timeout-\d{8}T\d{6}\.\d{6}Z$")


def history_between(start_at: float, end_at: float) -> list[dict]:
    with HISTORY_LOCK:
        return [row for row in HISTORY if start_at <= (row.get("captured_at") or 0) <= end_at]


def incident_path(incident_id: str) -> Path | None:
    if not INCIDENT_ID_RE.match(incident_id):
        return None
    return INCIDENTS_DIR / f"{incident_id}.json"


def write_incident(incident: dict) -> Path:
    INCIDENTS_DIR.mkdir(parents=True, exist_ok=True)
    target = incident_path(str(incident.get("incident_id") or ""))
    if target is None:
        raise ValueError("invalid incident id")
    tmp = target.with_suffix(".json.tmp")
    with INCIDENT_LOCK:
        tmp.write_text(json.dumps(incident, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(target)
    return target


def read_incident(incident_id: str) -> dict | None:
    target = incident_path(incident_id)
    if target is None or not target.exists():
        return None
    try:
        with INCIDENT_LOCK:
            return json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def incident_summary(incident: dict) -> dict:
    snapshot = incident.get("snapshot") or {}
    health = snapshot.get("health") or {}
    mcpd = ((health.get("components") or {}).get("mcp") or {}).get("details") or {}
    return {
        "incident_id": incident.get("incident_id"),
        "type": incident.get("type"),
        "status": incident.get("status", "complete"),
        "marked_at": incident.get("marked_at"),
        "post_capture_due_at": incident.get("post_capture_due_at"),
        "post_event_complete_at": incident.get("post_event_complete_at"),
        "history_before_samples": len(incident.get("history_before") or []),
        "history_after_samples": len(incident.get("history_after") or []),
        "tunnel_live": health.get("live"),
        "tunnel_ready": health.get("ready"),
        "mcp_initialized": (mcpd.get("initialize") or {}).get("ok"),
        "diagnosis": (snapshot.get("diagnosis") or {}).get("title"),
        "note": incident.get("note") or "",
    }


def list_incidents(limit: int = 100) -> list[dict]:
    INCIDENTS_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for path in INCIDENTS_DIR.glob("timeout-*.json"):
        incident = read_incident(path.stem)
        if incident:
            rows.append(incident_summary(incident))
    rows.sort(key=lambda row: row.get("marked_at") or 0, reverse=True)
    return rows[:max(1, min(limit, 100))]


def finalize_incident(incident_id: str) -> None:
    incident = read_incident(incident_id)
    if not incident or incident.get("status") == "complete":
        return
    snapshot_after = capture_and_store()
    completed_at = time.time()
    marked_at = float(incident.get("marked_at") or completed_at)
    incident["snapshot_after"] = snapshot_after
    incident["history_after"] = history_between(marked_at, completed_at)
    incident["post_event_complete_at"] = completed_at
    incident["status"] = "complete"
    incident["limitation"] = "P1 correlates sanitized tunnel telemetry around the mark; exact request-level attribution still requires the later canary proxy."
    write_incident(incident)


def schedule_incident_finalization(incident: dict) -> None:
    if incident.get("status") == "complete":
        return
    due_at = float(incident.get("post_capture_due_at") or time.time())
    delay = max(0.0, due_at - time.time())
    timer = threading.Timer(delay, finalize_incident, args=(str(incident.get("incident_id")),))
    timer.daemon = True
    timer.start()


def resume_pending_incidents() -> None:
    INCIDENTS_DIR.mkdir(parents=True, exist_ok=True)
    for path in INCIDENTS_DIR.glob("timeout-*.json"):
        incident = read_incident(path.stem)
        if incident and incident.get("status") != "complete":
            schedule_incident_finalization(incident)


def create_incident(note: str = "") -> dict:
    marked_at = time.time()
    snapshot = capture_and_store()
    stamp = datetime.fromtimestamp(marked_at, timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    incident_id = f"timeout-{stamp}"
    history_before = history_between(marked_at - 120.0, time.time())
    due_at = marked_at + POST_EVENT_SECONDS
    incident = {
        "schema_version": 2,
        "incident_id": incident_id,
        "type": "chat_25s_timeout",
        "status": "collecting",
        "marked_at": marked_at,
        "note": note[:300],
        "snapshot": snapshot,
        "snapshot_after": None,
        "history_before": history_before,
        "history_before_seconds": 120,
        "history_after": [],
        "post_event_seconds": POST_EVENT_SECONDS,
        "post_capture_due_at": due_at,
        "post_event_complete_at": None,
        "data_boundary": {
            "runtime_key": "not_collected",
            "tool_payloads": "not_collected",
            "prompts_transcripts": "not_collected",
            "tunnel_logs": "sanitized_warn_error_only",
        },
        "limitation": "Post-event telemetry is still collecting.",
    }
    target = write_incident(incident)
    schedule_incident_finalization(incident)
    return {
        "ok": True,
        "incident_id": incident_id,
        "marked_at": marked_at,
        "status": "collecting",
        "post_capture_due_at": due_at,
        "history_samples": len(history_before),
        "file": target.name,
    }


def export_incident(incident: dict) -> bytes:
    buf = io.BytesIO()
    manifest = (
        "Tunnel Observatory incident export\n"
        f"incident_id: {incident.get('incident_id')}\n"
        f"status: {incident.get('status')}\n"
        "Data boundary: no runtime key, tool payloads, prompts or transcripts.\n"
        "Logs: sanitized WARN/ERROR fields only.\n"
        "Interpretation: telemetry evidence is distinct from diagnostic hypotheses.\n"
    )
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("incident.json", json.dumps(incident, ensure_ascii=False, indent=2))
        archive.writestr("README.txt", manifest)
    return buf.getvalue()


def send_json(handler: SimpleHTTPRequestHandler, payload: dict, status: int = 200) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def send_bytes(handler: SimpleHTTPRequestHandler, body: bytes, content_type: str, filename: str | None = None) -> None:
    handler.send_response(200)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Cache-Control", "no-store")
    if filename:
        handler.send_header("Content-Disposition", f'attachment; filename="{filename}"')
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        clean = urlparse(path).path.lstrip("/")
        return str(ROOT / clean)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/activity":
            query = parse_qs(parsed.query)
            try:
                limit = int((query.get("limit") or ["50"])[0])
            except ValueError:
                limit = 50
            send_json(self, activity_feed(limit))
            return
        if parsed.path == "/api/repo-history":
            query = parse_qs(parsed.query)
            try:
                minutes = float((query.get("minutes") or ["60"])[0])
            except ValueError:
                minutes = 60.0
            send_json(self, repo_history(minutes))
            return
        if parsed.path == "/api/repo-status":
            send_json(self, latest_repo())
            return
        if parsed.path == "/api/snapshot":
            send_json(self, latest_snapshot() or capture_and_store())
            return
        if parsed.path == "/api/history":
            query = parse_qs(parsed.query)
            try:
                minutes = float((query.get("minutes") or ["60"])[0])
            except ValueError:
                minutes = 60.0
            rows = history_rows(minutes)
            send_json(self, {"ok": True, "minutes": max(1.0, min(minutes, 60.0)), "samples": len(rows), "history": rows})
            return
        if parsed.path == "/api/incidents":
            query = parse_qs(parsed.query)
            try:
                limit = int((query.get("limit") or ["100"])[0])
            except ValueError:
                limit = 100
            send_json(self, {"ok": True, "incidents": list_incidents(limit)})
            return
        if parsed.path.startswith("/api/incidents/"):
            parts = [part for part in parsed.path.split("/") if part]
            if len(parts) not in {3, 4}:
                send_json(self, {"ok": False, "error": "not_found"}, 404)
                return
            incident_id = parts[2]
            incident = read_incident(incident_id)
            if incident is None:
                send_json(self, {"ok": False, "error": "incident_not_found"}, 404)
                return
            if len(parts) == 4 and parts[3] == "export":
                send_bytes(self, export_incident(incident), "application/zip", f"{incident_id}.zip")
                return
            if len(parts) == 3:
                send_json(self, {"ok": True, "incident": incident})
                return
            send_json(self, {"ok": False, "error": "not_found"}, 404)
            return
        return super().do_GET()

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/incidents":
            send_json(self, {"ok": False, "error": "not_found"}, 404)
            return
        try:
            length = min(int(self.headers.get("Content-Length") or "0"), 4096)
            raw = self.rfile.read(length) if length else b"{}"
            payload = json.loads(raw.decode("utf-8", "replace")) if raw else {}
            note = str(payload.get("note") or "")
            send_json(self, create_incident(note), 201)
        except Exception as exc:
            send_json(self, {"ok": False, "error": f"{type(exc).__name__}: {exc}"}, 500)

    def log_message(self, fmt: str, *args) -> None:
        # Logging must never be able to break HTTP responses. P1 is often
        # launched from an MCP-managed shell whose stdout pipe can disappear
        # while the detached HTTP process keeps running.
        try:
            print(f"[p1] {self.address_string()} {fmt % args}", flush=True)
        except (BrokenPipeError, OSError, ValueError):
            pass


def main() -> None:
    STOP_EVENT.clear()
    load_history()
    load_repo_history()
    capture_and_store()
    capture_repo()
    resume_pending_incidents()
    sampler = threading.Thread(target=sampler_loop, name="p1-sampler", daemon=True)
    sampler.start()
    server = ThreadingHTTPServer(LISTEN, Handler)
    print(f"Tunnel Observatory P1: http://{LISTEN[0]}:{LISTEN[1]}/", flush=True)
    print(f"Read-only source: {TUNNEL}", flush=True)
    print(f"History: {HISTORY_FILE} | retention={HISTORY_RETENTION_SECONDS // 60}m", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        STOP_EVENT.set()
        server.server_close()


if __name__ == "__main__":
    main()
