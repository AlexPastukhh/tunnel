# Tunnel Observatory - Prototype 1

> This page preserves the original P1 runbook. The current repository copy and Repo collector status are described in [README_DUAL_TUNNEL.md](README_DUAL_TUNNEL.md). E39 fixed and tested automatic Repo discovery on Windows; the known legacy P1 installation was not replaced or started.

Status: working live shadow prototype.
Date: 2026-10-08.

## Purpose

P1 reads the current tunnel's local operator surfaces without changing the MCP path.
It is intended to distinguish a global tunnel outage from a per-chat/session/request failure.

Sources:
- `http://127.0.0.1:8080/health?details=true`
- `http://127.0.0.1:8080/health/mcp`
- `http://127.0.0.1:8080/metrics`
- sanitized WARN/ERROR events from `/api/logs`

P1 never reads the runtime key and does not collect tool payloads.

## Run

```powershell
python C:\Users\alexa\Documents\prot\observability-ui-prototype-1\server.py
```

Open manually:
`http://127.0.0.1:8092/`

The collector polls locally every 5 seconds. Closing P1 does not stop or modify the working tunnel.

## Current panels

- Tunnel, control-plane, MCP target and local work summary.
- Recent and cumulative tools/call latency.
- Component health layers: control-plane, MCP, queue, dispatcher, response delivery.
- Transport counters and tools/call 200/409 counts.
- Sanitized tunnel WARN/ERROR timeline.
- Incident triage with evidence vs hypothesis.
- Manual "Mark 25s timeout" snapshot in browser memory.

## Interpretation

A chat-side 25 second timeout does not by itself mean the whole tunnel is down.
If P1 remains live/ready with an initialized MCP child and empty queue, investigate the affected chat/connector session and recent control-plane transport events before restarting the global tunnel.

## Validation

- `python -m py_compile server.py`
- `node --check app.js`
- root, JS, CSS and `/api/snapshot` return HTTP 200
- snapshot reports current live/ready state

## Reliability update — 2026-10-08

P1 previously could leave port 8092 listening while requests returned an empty reply. Root cause was in the sidecar itself: `SimpleHTTPRequestHandler` request logging could raise when the process stdout pipe had disappeared, aborting the handler before headers were sent.

`log_message` is now non-fatal and the server is started with redirected stdout/stderr. Validation after the fix: 30 consecutive `/api/snapshot` requests returned HTTP 200; after adding collector counters another 20/20 returned HTTP 200.

P1 now exposes its own collector counters in each snapshot: samples, successes, failures, consecutive failures and last success/error timestamps. These counters are intentionally separate from Tunnel health.

Next: server-side rolling history and persistent sanitized incident snapshots for `Mark 25s timeout`.

## Rolling history + persistent incidents — 2026-10-08

P1 now samples the local tunnel every 5 seconds independently of browser refresh and keeps a rolling 60-minute history.
History is persisted locally in `data/history.jsonl` and is reloaded after P1 restart; old samples are pruned to the 60-minute retention window.

New local API:
- `GET /api/history?minutes=60` — sanitized rolling history;
- `POST /api/incidents` — create a persistent timeout incident snapshot.

`Mark 25s timeout` now calls the incident API. The saved JSON contains a fresh snapshot plus the preceding 2 minutes of sanitized history. It does not collect runtime keys, tool payloads, prompts or transcripts.

Validated after restart: history survived restart, 30/30 `/api/snapshot` requests returned HTTP 200, background sampling advanced history, and a test incident was created successfully and then deleted.

## Incident diagnostics increment — 2026-10-08

P1/P2 incident handling now captures both sides of a marked timeout.

When `Mark 25s timeout` is pressed:
- a fresh snapshot is captured immediately;
- the preceding 2 minutes of sanitized rolling history are attached;
- the incident is saved with `status=collecting`;
- P1 continues collecting for 120 seconds by default;
- the incident is finalized with a fresh post-event snapshot and the collected post-event history.

Pending incidents survive P1 restart: on startup the sidecar resumes/finalizes unfinished captures.

New incident API/UI:
- `GET /api/incidents` — list persisted incidents;
- `GET /api/incidents/<id>` — incident detail;
- `GET /api/incidents/<id>/export` — redacted ZIP (`incident.json` + `README.txt`);
- GUI incident list, status (`collecting` / `complete`), before/after sample counts, key Tunnel/MCP state and export action.

The export intentionally excludes runtime keys, tool payloads, prompts and transcripts. Exact request-level attribution still requires the later canary proxy.

Validation used an isolated test server/data directory with a 5-second post window: normal finalize passed, ZIP contained only the expected files, no `sk-`/`Bearer ` strings were present, and a pending incident finalized correctly after sidecar restart. Production P1 was then restarted on `127.0.0.1:8092`; root and APIs are healthy.

## Activity Audit (source-only)

Read-only [инспектор инструментов и opt-in dashboard](README_DUAL_TUNNEL.md)
для ограниченных Desktop Commander историй G2/Repo. GUI содержит только
метаданные, точный командный текст только в локальном интерактивном CLI.
Новая версия Windows P1 не устанавливалась и не перезапускалась.
