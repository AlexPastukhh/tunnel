# Fortis Repo: Guard review before Docker or worker restart

This is the **trigger checklist** for changes that can affect Repo1/Repo2 startup. The canonical source map and detailed assertions live in [the Tunnel Windows Repo runbook](../runtime/windows-repo/README.md); the paired Windows updater procedure lives in [Script Center's runbook](https://github.com/AlexPastukhh/script-control-center/blob/main/docs/GIT-WINDOWS-SOURCE-OF-TRUTH.md). Do not copy their full procedures here.

## Ownership

- **`tunnel/main`** owns both Repo worker chains and the shared policy: `runtime/windows-repo/current/launchers/shared/FortisContainerPolicy.ps1`. Repo-specific profile, key/ACL and quiet-launch behavior remains in the corresponding Repo1/Repo2 launchers.
- **`script-control-center/main`** owns the Script Catalog/Control Center UI, thin worker adapters, resolver, paired updater and Windows UI tests. Its old `launchers/` tree is not the active Guard source.
- Windows profiles, keys, ACLs, Tunnel Client binaries, Docker state and logs remain Windows/runtime-local; never copy them into Git.

## What requires a Guard review

Review the shared policy if a change affects effective mounts or their source/access, networks or published ports, Windows owner identity, Linux user/UID, namespaces, devices/groups, capabilities, seccomp, `no-new-privileges`, rootfs, inherited `NODE_OPTIONS`, allowed workspace roots or guarded tmpfs repair.

A new project inside an already allowed workspace root does not by itself require a Guard change. A different image ID or stricter CPU/RAM/PID values within the policy ceilings are not automatically a reason to rewrite Guards. GO-3C checks the effective isolation contract rather than exact image ID or Desktop Commander module SHA; this is **not** signed-image supply-chain attestation. The Windows Tunnel Runtime executable remains pinned.

## Required sequence before applying a risky change

1. Prepare source/config changes without touching the running container. Read-only inspect the actual container and compare the proposed effective configuration with the shared policy.
2. Run Repo1 and Repo2 Guard Preview. Any FAIL, unknown value or requested/effective mismatch is STOP. Do not disable a check to make Preview pass and do not stop the last working MCP connection.
3. If a security invariant really changes, update `FortisContainerPolicy.ps1` **once**, keep profile-specific checks in their own launchers, run the offline release/shared-policy/PowerShell tests, regenerate `current/source-manifest.json`, and update its pins in `Invoke-FortisRepo.ps1` and the Script Center resolver.
4. Review the scoped diff and secrets, then publish the paired commits: `tunnel/main` first, matching `script-control-center/main` second. On Windows use the documented Preview/Apply updater; it validates source and shortcut but does not start/stop workers or Docker.
5. Treat worker reconnect and Docker stop/restart/recreate as separate owner-controlled operations. Reconnect one Repo at a time, keep the other route and recovery path available, and verify real MCP responses. A successful Preview is not a reconnect test.

Never recreate the shared `fortis-repo-test` container as part of an ordinary Windows source update. If the container itself must be restarted or recreated, plan backup/recovery and verify both Guards against the target configuration **before** the operation; verify both MCP routes afterwards.
