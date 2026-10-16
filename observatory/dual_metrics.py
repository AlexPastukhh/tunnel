"""Read-only, minimal native G2 tunnel telemetry and redacted metric summaries.

No credentials or guest profile files are read. The G2 Windows discovery is
anchored to process owner SID + the expected command-line profile token. A
loopback listener alone, or a healthy *other* tunnel, never proves G2.
"""
from __future__ import annotations

import json
import math
import os
import re
import subprocess
import sys
import time
import urllib.request

G2_USER_SID = "S-1-5-21-303538662-3368424508-2654684973-1009"
G2_PROFILE = "fortis-host-g2-test"
DISCOVERY_TIMEOUT = 15
METRIC_NAMES = frozenset((
    "commands_polled_total",
    "commands_enqueued_total",
    "commands_poll_cycles_total",
    "commands_poll_last_successful_timestamp_seconds",
    "commands_queue_length",
    "commands_queue_capacity",
    "dispatcher_worker_pool_occupancy",
    "dispatcher_worker_pool_capacity",
    "command_end_to_end_latency_milliseconds_sum",
    "command_end_to_end_latency_milliseconds_count",
))
METRIC_LINE = re.compile(r"^([a-zA-Z_:][a-zA-Z0-9_:]*)(?:\{[^}\r\n]{0,1600}\})?\s+([^\s#]+)\s*$")


def summarize(text: str) -> dict:
    """Return allowlisted numeric aggregates only (no labels, tokens, URLs)."""
    if len(text) > 500_000:
        raise ValueError("metrics payload too large")
    values: dict[str, list[float]] = {}
    for line in text.splitlines():
        match = METRIC_LINE.fullmatch(line.strip())
        if not match or match[1] not in METRIC_NAMES:
            continue
        try:
            number = float(match[2])
        except ValueError:
            continue
        if math.isfinite(number) and number >= 0:
            values.setdefault(match[1], []).append(number)
    def one(name: str):
        samples = values.get(name, [])
        return samples[0] if len(samples) == 1 else None
    def total(name: str):
        samples = values.get(name)
        return sum(samples) if samples else None

    count = total("command_end_to_end_latency_milliseconds_count")
    millis = total("command_end_to_end_latency_milliseconds_sum")
    return {
        "polled_total": one("commands_polled_total"),
        "enqueued_total": one("commands_enqueued_total"),
        "poll_cycles_total": one("commands_poll_cycles_total"),
        "poll_last_success_at": one("commands_poll_last_successful_timestamp_seconds"),
        "queue_length": one("commands_queue_length"),
        "queue_capacity": one("commands_queue_capacity"),
        "dispatcher_active": one("dispatcher_worker_pool_occupancy"),
        "dispatcher_capacity": one("dispatcher_worker_pool_capacity"),
        "command_latency_count": count,
        "command_latency_avg_ms": round(millis / count, 2) if count and millis is not None else None,
        "latency_mean_scope": "lifetime histogram mean, not p95 or last call",
    }


# Single quoted inline PS query with no secret values. Returns only listener
# port numbers for G2-owned runtime; no command lines or owner data printed.
G2_DISCOVERY_PS = r"""$ErrorActionPreference='Stop'; $sid='S-1-5-21-303538662-3368424508-2654684973-1009'; $names=@('tunnel-client.exe','tunnel-client-runtime.exe'); $targets=@(Get-CimInstance Win32_Process -Filter "Name='tunnel-client.exe' OR Name='tunnel-client-runtime.exe'" | Where-Object { $_.CommandLine -match '(?i)(^|\s)--profile\s+fortis-host-g2-test(?=\s|$)' }); $pids=@(foreach($p in $targets){$identity=Invoke-CimMethod -InputObject $p -MethodName GetOwnerSid -ErrorAction Stop; if($identity.ReturnValue -eq 0 -and $identity.Sid -ceq $sid){$p.ProcessId}}); @(Get-NetTCPConnection -State Listen -LocalAddress '127.0.0.1' -ErrorAction Stop | Where-Object { $pids -contains $_.OwningProcess } | Select-Object -ExpandProperty LocalPort | Sort-Object -Unique) | ConvertTo-Json -Compress"""


def discover_g2() -> tuple[list[str], str | None]:
    if sys.platform != "win32":
        return [], "Native G2 listener discovery requires owner Windows"
    try:
        proc = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", G2_DISCOVERY_PS],
            capture_output=True, text=True, check=True, timeout=DISCOVERY_TIMEOUT,
        )
        raw = proc.stdout.strip()
        if not raw:
            return [], "No listener matched G2 process profile and owner SID"
        ports = json.loads(raw)
        if isinstance(ports, int):
            ports = [ports]
        if not isinstance(ports, list) or len(ports) > 10:
            return [], "Unexpected G2 listener discovery result"
        unique = set()
        for value in ports:
            if type(value) is not int or not 1 <= value <= 65535:
                return [], "Invalid G2 listener port"
            unique.add(value)
        if not unique:
            return [], "No loopback listener for identified G2 process"
        return [f"http://127.0.0.1:{p}" for p in sorted(unique)], None
    except (OSError, subprocess.TimeoutExpired, subprocess.CalledProcessError, ValueError, TypeError):
        return [], "G2 listener discovery failed or could not verify owner SID"


def _local_get(base: str, path: str) -> str:
    # Base is ONLY generated by discover_g2 from verified loopback ports.
    req = urllib.request.Request(base + path, headers={"User-Agent": "fortis-observatory-readonly"})
    with urllib.request.urlopen(req, timeout=1.5) as resp:
        return resp.read(500_001).decode("utf-8", "replace")


def collect_g2() -> dict:
    now = time.time()
    addresses, error = discover_g2()
    if error:
        return {"state": "UNKNOWN", "verified": False, "sampled_at": now, "reason": error}
    for address in addresses:
        try:
            health = json.loads(_local_get(address, "/health?details=true"))
            if not isinstance(health, dict) or not all(isinstance(health.get(k), bool) for k in ("live", "ready")):
                continue
            metrics = summarize(_local_get(address, "/metrics"))
            components = health.get("components") or {}
            mcp = components.get("mcp") or {}
            return {"state": "UP" if health["live"] and health["ready"] else "DOWN",
                    "verified": True, "sampled_at": now, "identity": "G2 SID + profile + loopback listener",
                    "listener": address, "live": health["live"], "ready": health["ready"],
                    "mcp_state": mcp.get("state", "unknown"),
                    "uptime_seconds": (health.get("runtime") or {}).get("uptime_seconds"),
                    "metrics": metrics}
        except (OSError, ValueError, TypeError, KeyError):
            continue
    return {"state": "UNKNOWN", "verified": False, "sampled_at": now,
            "reason": "G2 identity matched but local telemetry did not respond"}
