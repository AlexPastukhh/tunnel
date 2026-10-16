# Dual-tunnel GUI working copy

## Repo discovery fix — 2026-10-16

[E39 evidence](../docs/G3_REPO_MONITOR_DISCOVERY_2026-10-16.md): the original 3-second Windows discovery deadline expired; the unchanged query completed in 6.516 seconds with a 15-second deadline. The collector now allows up to 15 seconds, restricts CIM queries to the two tunnel-client executable names, and reports separate redacted failure reasons. Native Windows automatic discovery passed in 5.594 seconds, with verified Repo UP/MCP initialized and no OBS_REPO_URL override. Eleven unit/API/regression tests passed. The known legacy P1 folder has no repo_monitor.py; it was not replaced or started. This source check is not a dashboard deployment or GUI acceptance.

## Dual-tunnel extension (working copy; 2026-10-12)

This folder is a source-only copy of Observatory P1, not a replacement for the installed Windows P1. Only five original source files were copied; data, logs, incidents and credentials were excluded.

Added read-only API:
- GET /api/repo-status — verified Repo tunnel state or UNKNOWN/STALE.
- GET /api/repo-history?minutes=60 — separate sanitized rolling Repo history.

The sampler waits five seconds between collection rounds and persists data/repo-history.jsonl (excluded from Git). Actual sample spacing includes HOST/Repo collection time; five seconds is not a fixed cadence. Windows discovery selects a loopback listener by process command line (tunnel-client and repo-mode). It additionally requires the known native Repo Tunnel ID to be present in /metrics before reporting UP or DOWN. Identity failure reports UNKNOWN. Native Windows verification of this identity signal passed in E39 for this source collector.

For synthetic testing, OBS_REPO_URL=http://127.0.0.1:PORT provides a loopback candidate but does not skip identity verification.

Checks:
- python -m unittest -v test_repo_monitor.py
- python -m py_compile server.py repo_monitor.py
- node --check app.js

Eleven automated tests now pass, including the existing two HTTP route checks and new discovery regression cases. Unit tests alone do not prove Windows integration; the separate E39 native collector check does. Browser rendering and dashboard installation remain unverified.

Do not replace the existing P1 automatically. Before installation test on an unused loopback port with isolated P1_DATA_DIR, verify the native Repo identity in live telemetry and retain rollback. Full MCP audit and privileged controls remain out of scope.

## Activity Audit — metadata-only opt-in

Это source MVP от 16.10.2026, не автообновление Windows P1. Использует
существующую rolling историю Desktop Commander. Не читает промпты,
не перехватывает все дочерние команды и не читает пути другого Windows SID.

Repo Docker, чтение только метаданных, не создаёт новый журнал:

    cd /workspace/repos/tunnel
    python3 observatory/activity_audit.py --route repo --limit 30
    python3 observatory/activity_audit.py --route repo --tool start_process --limit 30

G2 Windows guest, после размещения копии CLI в собственном Workspace:

    python .\activity_audit.py --route g2 --limit 30

Для точных команд (могут содержать секреты) только trusted local
interactive terminal, не MCP/chat/screenshot/redirect:

    python3 observatory/activity_audit.py --route repo --unsafe-show-commands-local --limit 5

Unsafe-режим откажет при перенаправленном stdout; --json всегда метаданные.

Dashboard /api/activity?limit=40 работает только с opt-in локальными
источниками, явно указанными владельцем процесса: переменные
FORTIS_AUDIT_REPO_HISTORY и FORTIS_AUDIT_G2_HISTORY. Например,
если dashboard запущен **как G2** (его собственный пользователь):

    $env:FORTIS_AUDIT_G2_HISTORY = "$env:USERPROFILE\.claude-server-commander\tool-history.jsonl"
    python .\server.py

Owner dashboard не должен открывать guest-only history через смену ACL:
оставить G2 unconfigured до отдельного утверждённого collector.
Repo Docker сейчас без published ports: исходный dashboard из контейнера
сам собой не становится доступным из Windows. Не публиковать localhost
внешним слушателем. Не путать source с installed Windows P1.

ИСТОЧНИКИ / ГРАНИЦЫ: rolling 1000 recent calls; truncated large outputs;
нет полного chat ID и всех prompts, Site/другие плагины вне контура;
выводные команды скриптов/процессов не фиксируются этим логом;
нет tamper-proof archive, pre-execution ALLOW/DENY и единого retention.
Для полного forensic audit нужны раздельные approved adapters на
native G2 и native Repo, owner-protected event storage, data-minimization,
согласованный срок хранения и отдельная приёмка — [AUDIT](../docs/AUDIT.md).

## Native G2 + Repo metrics — source preview (2026-10-16)

Verified live health and metrics on the two separate Windows loopback listeners
via guest G2 read-only access: both G2 and Repo live=true, ready=true,
MCP initialized, queue 0/20 in one snapshot. Listener ports are dynamic.
This is LOCAL tunnel health, NOT end-to-end ChatGPT request delivery.

Source additions:
- GET /api/tunnels: separate G2/Repo health and allowlisted numeric aggregates;
  excludes raw Prometheus labels, tool arguments, commands and credentials.
- GET /api/g2-history?minutes=60: rolling owner-local redacted G2 counters;
  Repo history likewise includes safe numeric aggregates.
- Native route cards and rolling 60-minute received-command graph; retired
  owner HOST panels are now collapsed in a historical disclosure.
- G2 Windows discovery: read-only CIM process identity, exact guest SID,
  pinned fortis-host-g2-test profile and process-owned loopback listener.
  Does not inspect guest profile contents or cross guest ACL boundaries.
  If Windows owner cannot prove the G2 identity, status is UNKNOWN.
- Metrics: polled/enqueued totals, poll count/age, queue and dispatcher
  occupancy, cumulative mean command latency. Mean is NOT p95/p99. Historical
  samples cover only up to 60 minutes (sampler wait + Windows discovery time).

Windows owner preview, after pulling source, in a NEW PowerShell window:
    cd C:\Users\alexa\Repos\tunnel\observatory
    $env:P1_PORT = '8093'
    $env:P1_DATA_DIR = Join-Path $env:LOCALAPPDATA 'FortisObservatoryV2Preview'
    py -3 .\server.py

Open http://127.0.0.1:8093/. Port 8093 is separate from any existing 8092
Observatory. Ctrl+C stops preview ONLY. Do not restart native Repo/G2, modify
ACLs, change mount layout or enable raw logging to make a status green.
Running Windows owner collector and actual browser layout still require
acceptance; synthetic Linux API/unit/HTML checks do not replace it.
Moving preview to the installed dashboard requires a separate approval.

## Download history / 90-day safe archive (source feature, 2026-10-16)

Under native G2/Repo metrics, a new "Скачать историю наблюдения" area
offers all available history or selected local start/end datetimes,
checkboxes G2 and/or Repo, CSV or JSON, and "Скачать ZIP".

The ZIP includes manifest.json, metrics.csv or metrics.json, and
tool_activity.csv or tool_activity.json. The manifest lists actual coverage
times and counts by route and explicitly marks incomplete coverage. The
contents are deliberately minimized: only health/MCP state and allowlisted
numeric counters, plus recent Desktop Commander metadata if the source
was explicitly configured and readable. No raw command, arguments, output,
personal paths, prompts, credentials, or full chat transcript are exported.
The separate E43 legacy HOST incidents are not exported through this panel.
ZIP files downloaded by the browser should be kept privately.

The long-term archive is SQLite at
P1_DATA_DIR/native-archive.sqlite3, one aggregate metric sample per
route per UTC minute, retained up to 90 days. It begins with the available
existing RECENT g2-history.jsonl and repo-history.jsonl samples when
restarting the source server, then collects in the future. Expired/never
recorded history cannot be recovered. Recent DC calls are archived about
every 30s ONLY for explicitly configured sources; an owner process cannot
read guest-only G2 Desktop Commander history, and Repo Docker history has no
owner-mapped file by default. Empty tool_activity does not imply zero calls.

New owner-local endpoints:
- GET /api/archive-coverage: metadata counts/time spans, no payloads.
- GET /api/export-history?mode=all&routes=repo,g2&format=csv: ZIP.
- GET /api/export-history?mode=range&routes=repo&format=json&from=...&to=...
  ZIP for a specific inclusive timezone-aware interval, max 90 days.

Export requires a local Host header and same-origin fetch headers; it
is never exposed remotely. The archive is not tamper-proof or a
privileged forensic capture. It does not track child processes or
full command texts and must not be treated as such. All new writes stay
inside the selected OWNER-local P1_DATA_DIR; no tunnel runtime restart,
ACL/mount change, secret rotation, or guest-directory access is required.

This is a source change. For the active Windows preview on port 8093:
stop only the Observatory process (Ctrl+C), git pull --ff-only origin main,
and run the exact same preview command (P1_DATA_DIR unchanged).
The prior rolling 60m JSONL is backfilled where available. The existing
dashboard on port 8092 and native Repo/G2 tunnels are not modified.
Linux source/unit/HTTP tests do not substitute Windows browser acceptance.
