# Repo1/Repo2 Windows Git-clone source mirror

**Historical owner report (2026-11-02): GO-3C SHARED GUARD POLICY was published in `tunnel/main`.** Owner-provided Windows output reported manifest `8036348F69BB37F94F5E6FDE529BF44A292F4EB91977CE91A491E9860AADBFCA`, paired-source/static preflight PASS, Windows PowerShell/WinForms compilation PASS, both Guard Previews PASS, and the Script Catalog shortcut switched to the Git clone. The owner then reported that both Repo1 and Repo2 had reconnected and were working. This is a date-bounded owner report, not current acceptance for a later container baseline.

**Current GO3 baseline (2026-11-04):** both read-only Guard Previews and the image/mount release verifier PASS against container `04fed7b7...`, but the verifier ends `REPO_RECONNECT_PENDING`. Repo1 inventory reports zero recognized tunnel listeners and one process matching the `repo-mode` profile pattern. That process has not yet been identified; do not invoke Repo1 Start, restart or Stop until a Windows-side read-only process/port inventory explains it. Current Repo1/Repo2 reconnect and functional acceptance therefore remain pending. Cold boot/reboot, alternate startup order, long-duration stability and an exercised rollback also remain unverified.

`current/` is now the canonical Repo1/Repo2 worker chain. Both profiles consume
one shared Windows/Docker/Linux security policy at
`current/launchers/shared/FortisContainerPolicy.ps1`; profile, key/ACL, tunnel
and quiet-log behavior remains Repo-specific. The nine executable files are
pinned by `current/source-manifest.json`, whose inventory hash is pinned by the
Windows dispatcher and Script Center resolver.

## Components

- `current/` — both workers, Repo1 quiet launcher/control, Repo2
  `Start-Fortis.ps1` / `Common.ps1`, Repo2 quiet launcher/Direct Guard, and the
  shared policy module.
- `Invoke-FortisRepo.ps1` — Windows Git-clone-only dispatcher. Default is
  read-only Preview; explicit Start requires the canonical clean, synchronized
  `main` clone, approved GitHub origin and typed owner confirmation.
- `repo1/`, `repo2/`, and root `release-manifest.json` — retained four-file
  direct-launcher candidate from an earlier staging attempt. They are not used
  by the current dispatcher.
- `test_release_contract.py` — offline release and source-mirror contract.
- `test_shared_policy_contract.py` and `test_fortis_container_policy.ps1` —
  shared-policy and runtime repair-gating tests.
- `Preview-WindowsRepoInventory.ps1` — read-only comparison against known
  candidate legacy Windows file paths; it does not prove the active shortcut.
- `DEFENDER-AND-INSTALLED-INVENTORY.md` — Windows-local dependency and Defender
  inventory; no Defender settings are changed by this release.

## Shared Guard design

The common module owns Windows owner SID/non-elevated checks, container identity,
Docker effective/requested mounts, network membership, published-port
prohibition, namespace/device/group restrictions, capabilities,
`no-new-privileges`, seccomp, read-only rootfs, Linux UID/GID, Direct entrypoint
availability, inherited `NODE_OPTIONS`, resource ceilings, workspace roots and
the narrowly scoped Desktop Commander tmpfs repair. A single self-integrity
anchor is maintained inside the shared module; it is not duplicated across
four entrypoints.

Docker mounts are matched by destination, not array order: every required
workspace target must appear exactly once, the optional client target at most
once, and every unknown target or bind mount is rejected. There is no separate
hard-coded total-mount count. Docker inspect is requested as a single JSON
object (`--format '{{json .}}'`) so Windows PowerShell 5.1 cannot accidentally
wrap a one-container top-level JSON array and hide the `Mounts` property. Node
`-e` probes are UTF-8/Base64 wrapped before crossing the Windows native-process
boundary, avoiding PowerShell 5.1 rewriting embedded JavaScript quotes.

The policy intentionally validates the effective isolation contract rather
than exact Docker image ID or Desktop Commander module SHA. The image ID is
reported for operator visibility. This is not signed-image supply-chain
attestation: malicious code in a selected image still has the container's
allowed workspace and egress. The Windows Tunnel Runtime executable remains
SHA-256 pinned in the shared policy. CPU, memory and PID limits are ceilings;
stricter values pass. A new persistent mount/network or expanded capability
still requires a shared-policy change and tests.

Repo1 and Repo2 remain separate profiles. Repo2 passes the inspected full
Container ID from `Start-Fortis.ps1` through its launcher and Docker exec path;
it does not resolve the reusable name again.

## Runtime placement and boundaries

- **Windows host:** PowerShell launchers, `docker.exe`, Tunnel Client and
  `tunnel-client-runtime.exe` v0.0.15. These binaries are not copied into Git.
- **Docker/Linux:** `/usr/local/bin/node` and the Direct Desktop Commander entry
  under `/opt/dc`; the policy verifies effective runtime isolation and entry
  file availability, not an exact image/module digest.
- **Windows-local state:** Repo1/Repo2 profiles, separate keys, ACLs, logs,
  shortcuts and catalog data remain on Windows and outside Git.
- The existing `fortis-repo-test` container, image, volume, networks and runtime
  configuration are not recreated or modified by this source publication.

The dispatcher and paired Windows updater do not stop/restart Fortis, Docker or
either tunnel. The Repo2 launcher may start the already-existing container if
it is already stopped; that behavior is not invoked by this release. The
separate Repo1 `control.ps1` retains an explicit manual StopContainer action,
but the worker/dispatcher does not call it. The later owner-reported Repo1/Repo2
reconnect was a separate Windows action; no Docker container stop/recreate was
reported in the provided evidence.

## Paired delivery and Windows update

1. Push the reviewed `tunnel/main` source release first.
2. Push the matching Script Center resolver/adapters/tests/docs to
   `script-control-center/main` second.
3. On Windows, after both canonical sibling clones are clean `main` and fetched
   from their approved origins, run `tools/Update-Windows-ControlCenter.ps1
   -Apply` from the Script Center clone. It pulls `tunnel` first and Script
   Center second, validates the manifest and all nine hashes, parses PowerShell,
   compiles WinForms, runs read-only Repo1/Repo2 Previews and repairs the
   existing Script Catalog shortcut. It does not start a worker, stop a tunnel
   or stop/recreate Docker.
4. Keep the existing live tunnels and recovery route untouched. A successful
   pull/Preview is not a live MCP reconnect acceptance. Any later reconnect is
   a separate owner-controlled maintenance action, one profile at a time.

The paired updater refuses dirty or wrong-branch clones. If a future update
stops at that gate, preserve and review the local changes first; do not reset,
clean or stash them merely to force `-Apply`.

## Validation

Run from the tunnel repository:

```bash
python3 -B runtime/windows-repo/test_release_contract.py
python3 -B runtime/windows-repo/test_shared_policy_contract.py
DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1 /workspace/repo/Workfiles/rdg-ci-pwsh-7.6.9/pwsh -NoLogo -NoProfile -File runtime/windows-repo/test_fortis_container_policy.ps1
```

Docker offline results checked 2026-11-02: release contract **6/6 PASS**,
shared-policy contract **6/6 PASS**, PowerShell policy matrix **43/43 PASS**.
The bundled `pwsh` needs `DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1` in this
container because ICU is not installed; this affects the test host, not the
Guard source. Owner-provided Windows output reports PowerShell/WinForms compile,
both read-only Previews and shortcut switch PASS; the owner reports both live
Repo1/Repo2 reconnects working. These Windows/live results are not independently
observable from this Docker session. Cold boot, alternate startup order,
long-duration stability and an exercised rollback remain open.
