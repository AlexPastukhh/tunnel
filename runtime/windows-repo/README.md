# Repo1/Repo2 Windows Git-clone source mirror

**Historical owner report (2026-11-02): GO-3C SHARED GUARD POLICY was published in `tunnel/main`.** Owner-provided Windows output reported manifest `8036348F69BB37F94F5E6FDE529BF44A292F4EB91977CE91A491E9860AADBFCA`, paired-source/static preflight PASS, Windows PowerShell/WinForms compilation PASS, both Guard Previews PASS, and the Script Catalog shortcut switched to the Git clone. The owner then reported that both Repo1 and Repo2 had reconnected and were working. This is a date-bounded owner report, not current acceptance for a later container baseline.

**Runtime evidence ownership:** the 2026-11-04 pre-cutover GO3 report is a dated
baseline, not today's container ID or reconnect verdict. Subsequent path-guidance
and MCP-UI-headless deployment/owner reconnect results are recorded in
[Fortis Container evidence](https://github.com/AlexPastukhh/fortis-container/blob/main/patches/desktop-commander-0.2.52-mcp-ui-headless/README.md).
Before a new operation, run the current shared Guard Preview against the actual
runtime. An unidentified process in a fresh preflight is STOP; do not infer one
from an old report. Pending acceptance lives only in the
[Tunnel backlog](../../docs/BACKLOG-IMPROVEMENTS.md).

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
  `tunnel-client-runtime.exe` v0.0.21 is the source target. These binaries are not copied into Git.
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

Publish reviewed source through task worktree → Gateway → PR/CI → owner GitHub
UI merge under UC-CONT-002; do not push directly to main. The Windows paired
update order is Tunnel first, Script Center second. Its command, manifest/clone
checks and shortcut handling have one owner:
[Script Center Windows update runbook](https://github.com/AlexPastukhh/script-control-center/blob/main/docs/GIT-WINDOWS-SOURCE-OF-TRUTH.md).
This source publication does not start workers or reconnect MCP. Any runtime
reconnect is a separate owner operation, one profile at a time, keeping the
other connection and recovery path available. Preserve dirty/wrong-branch
clones; do not reset, clean or stash to force the updater past its gate.

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
observable from this Docker session. Remaining acceptance is tracked only in
[BACKLOG-IMPROVEMENTS](../../docs/BACKLOG-IMPROVEMENTS.md).

## Runtime resilience v0.0.21

Both launchers use the shared runtime/logging helper and pinned v0.0.21 with explicit stdio restart. Install the verified EXE side-by-side before applying paired source pins; switch one Repo at a time. Source publication does not update running Windows processes. Artifact validation, fault tests, bootstrap, rollout and rollback: [runtime resilience runbook](../../docs/REPO-RUNTIME-RESILIENCE.md).
