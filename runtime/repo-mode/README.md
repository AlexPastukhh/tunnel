# Legacy Repo Mode reference

> **HISTORICAL / NOT CURRENT TOPOLOGY.** This folder contains the earlier Docker Repo-mode packaging and probe. Do not infer current Fortis Repo mounts from `workspace-config.example.json`.

The example records an older Windows bind-mount model:
- `C:\\Users\\alexa\\Repos` → `/workspace/repos`;
- `C:\\Users\\alexa\\Workfiles` → `/workspace/files`.

The current Fortis Repo process inspected on 2026-11-03 shows a different arrangement: `/workspace/repo`, `/workspace/repos` and `/workspace/files` are mountpoints/subpaths of the same ext4 `fortis-repo-workspace` volume. See the sibling `fortis-container` documentation project, especially `docs/CONTAINERS-AND-VOLUMES.md` and `docs/CURRENT-STATE.md`.

`workspace-config.example.json` contains a historical container ID and backup path. It is not a current runtime config, must not be copied into a live `workspace-config.json`, and must not be used to start, recreate or inspect a container without a fresh owner-side review.

`linux-tools.json` is a generated tool-definition snapshot written by `probe.mjs`; it is not the source of the live tool descriptions and still contains the superseded Windows bind-mount wording. Do not use it as current MCP metadata. `expected-schemas.json` is a separate schema reference used by `check-schemas.mjs`.

The current Repo1/Repo2 Windows worker source is under `runtime/windows-repo/current`; the `runtime/repo-mode` Dockerfile and probe are not the canonical source of those Windows workers.

## MCP bridge guidance follow-up — 2026-11-03

`fortis-mcp-bridge.mjs` is a legacy Repo-mode wrapper. It rewrites `initialize` guidance and `tools/list` descriptions only when a profile explicitly launches that bridge. Current Repo1/Repo2 worker source launches the direct Desktop Commander entry point and does not invoke this wrapper.

The Tunnel source candidate was corrected to describe the observed shared ext4 `fortis-repo-workspace` paths without asserting that they are Windows bind mounts. Its `test-fortis-mcp-bridge.mjs` passed 4/4 source-level unit tests; `node check-schemas.mjs` reported 19 expected schemas matched against a 26-tool generated snapshot.

### What the 4/4 unit tests do — and do not — establish

1. Check that the source guidance string describes the shared workspace paths and excludes stale/unverified claims.
2. Exercise a synthetic `initialize` response through the presentation function.
3. Exercise a synthetic `tools/list` response and verify the replacement of legacy path guidance.
4. Check that a synthetic `tools/call` response passes through unchanged.

These are source-level tests only. They do not launch Desktop Commander, connect to the current ChatGPT MCP connection or verify the tool schema supplied to a live chat.

**Source only — not deployed:** corrected source SHA-256 is `863fd54cf49995adc94d9b5d41b00f36d8872d89d32d1864c0ce4fe405caefca`. The installed legacy wrapper `/workspace/repo/.fortis/mcp-bridge.mjs` remains at SHA-256 `8389436658e22f213d9865a78872159e027ca33094999db64ca96b5a7c79fc21` and still contains the old Windows-path claim. It was not copied or changed because current Repo1/Repo2 workers do not use it.

`linux-tools.json` is a generated `probe.mjs` snapshot, not the source of live tool descriptions. The supplied Fortis Repo app screenshot shows the per-tool `Read` description, which corresponds to the correct dynamic `PATH_GUIDANCE`. Current connected metadata also exposes `start_process`, whose description includes a different `OS_GUIDANCE` block with generic Windows/Linux-to-`/home/...` translation. Its source is established in the installed Desktop Commander package: `server.js:8-10` builds the guidance strings; `server.js:791-798` injects `OS_GUIDANCE` into `start_process`; `system-info.js:585-593` contains the obsolete `/home` mapping; `system-info.js:699-711` builds the correct mounted-path guidance used by `read_file`. The old exact `C:\\Users\\alexa` statement remains in the installed legacy wrapper but is absent from the current connected schema. Current Repo1/Repo2 workers use the direct Desktop Commander entry point, not this wrapper. No active runtime file was changed. The owner approved a narrow correction on 2026-11-04, but it is not deployed: the installed `system-info.js` is root-owned and the connected MCP process runs as UID 1000 without write permission. No active package file was changed and no process was killed because no safe in-container restart path was identified. Root-level deployment followed by reconnecting only the ChatGPT Fortis Repo MCP instance and checking both tool descriptions in the app UI remains outstanding.
