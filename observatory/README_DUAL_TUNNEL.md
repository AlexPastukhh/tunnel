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
