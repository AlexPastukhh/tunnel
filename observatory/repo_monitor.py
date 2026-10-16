"""Read-only native Repo telemetry, separate from the legacy HOST collector."""
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

from dual_metrics import summarize

# Explicit address is accepted only on loopback. Never proxy arbitrary URLs.
REPO_ID = "tunnel_6ac9e4dc9e688191ae1838e858424e8d"
ENV_URL = "OBS_REPO_URL"
# Windows CIM/TCP provider startup exceeded 3s in the observed native baseline.
DISCOVERY_TIMEOUT_SECONDS = 15


def _endpoint(port):
    port = int(port)
    if not 1 <= port <= 65535:
        raise ValueError("invalid port")
    return f"http://127.0.0.1:{port}"


def candidates():
    configured = os.environ.get(ENV_URL, "").strip()
    if configured:
        match = re.fullmatch(r"http://127\.0\.0\.1:(\d{1,5})/?", configured)
        if not match:
            return [], "OBS_REPO_URL must be an http://127.0.0.1:PORT address"
        return [_endpoint(match.group(1))], None
    if sys.platform != "win32":
        return [], "Automatic listener discovery requires Windows; set OBS_REPO_URL for local tests"
    # Select listener by process command line, not by guessing previous dynamic ports.
    ps = r"""$ErrorActionPreference='Stop'; $targets=@(Get-CimInstance Win32_Process -Filter "Name='tunnel-client.exe' OR Name='tunnel-client-runtime.exe'" | Where-Object { $_.CommandLine -match 'tunnel-client' -and $_.CommandLine -match 'repo-mode' }); $pids=@($targets | Select-Object -ExpandProperty ProcessId); @(Get-NetTCPConnection -State Listen -LocalAddress '127.0.0.1' | Where-Object { $pids -contains $_.OwningProcess } | Select-Object -ExpandProperty LocalPort | Sort-Object -Unique) | ConvertTo-Json -Compress"""
    try:
        proc = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps],
                              timeout=DISCOVERY_TIMEOUT_SECONDS, capture_output=True, text=True, check=True)
        raw = proc.stdout.strip()
        if not raw:
            return [], "No native Repo listener matched its process identity"
        ports = json.loads(raw)
        if isinstance(ports, int):
            ports = [ports]
        return [_endpoint(p) for p in ports], None
    except subprocess.TimeoutExpired:
        return [], "Native Repo listener discovery timed out"
    except OSError:
        return [], "Native Repo listener discovery could not start"
    except ValueError:
        return [], "Native Repo listener discovery returned invalid output"
    except subprocess.SubprocessError:
        return [], "Native Repo listener discovery command failed"


def _request(base, path):
    with urllib.request.urlopen(
        urllib.request.Request(base + path, headers={"User-Agent": "observatory-readonly"}),
        timeout=1.2,
    ) as response:
        return response.read(500_000).decode("utf-8", "replace")


def collect_repo():
    now = time.time()
    addresses, error = candidates()
    if error:
        return {"state": "UNKNOWN", "sampled_at": now, "reason": error, "verified": False}
    for address in addresses:
        try:
            metrics = _request(address, "/metrics")
            # A matching process alone is insufficient: verify the expected tunnel identity.
            if REPO_ID not in metrics:
                continue
            health = json.loads(_request(address, "/health?details=true"))
            if not isinstance(health, dict):
                continue
            state = "UP" if health.get("live") and health.get("ready") else "DOWN"
            if health.get("live") and not health.get("ready"):
                state = "DOWN"
            return {"state": state, "sampled_at": now, "verified": True,
                    "listener": address, "live": bool(health.get("live")),
                    "ready": bool(health.get("ready")),
                    "uptime_seconds": (health.get("runtime") or {}).get("uptime_seconds"),
                    "mcp_state": (health.get("components") or {}).get("mcp", {}).get("state", "unknown"),
                    "metrics": summarize(metrics)}
        except (OSError, ValueError, urllib.error.URLError):
            continue
    return {"state": "UNKNOWN", "sampled_at": now, "verified": False,
            "reason": "No listener with verified Repo tunnel identity responded"}
