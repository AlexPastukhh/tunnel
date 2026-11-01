# Current Repo1 / Repo2 worker chain — exact source mirror

This directory preserves the active `script-control-center` Repo1/Repo2 worker
chain with the original relative layout. The eight PowerShell files were copied
byte-for-byte from `script-control-center:main` at
`001ddff9b0ece358e5cfa1b336a104c7d66bee68`; `source-manifest.json` records their
SHA-256 hashes and source revision. No script logic, parameters, guards,
profiles, keys, Docker settings or tunnel runtime were changed by this copy.

## Entrypoints

- `Repo1-Worker.ps1` → `launchers/chatgpt-repo-mode/run-tunnel-quiet-logs.ps1`
  → adjacent `control.ps1`.
- `Repo2-Worker.ps1` → `launchers/FortisRDGLauncherV2/Start-Fortis.ps1`
  → `Common.ps1` → adjacent `Repo2DirectGuard.ps1`; then
  `launchers/FortisRepoPlus2/FortisRepo2-quiet-logs.ps1`.

Keep this relative directory structure intact: the existing workers and
launchers resolve dependencies through `$PSScriptRoot`. Windows-local profiles,
keys, ACLs, runtime logs, Docker state and installed Tunnel Client binaries
remain outside this source tree.

This is a source mirror, not proof of Windows installation, shortcut binding,
PowerShell execution, live MCP reconnect, or cold-boot acceptance. Do not
switch the active Control Center shortcuts until the owner separately accepts
the Windows Git-clone path and rollback.
