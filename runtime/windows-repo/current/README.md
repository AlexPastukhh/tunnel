# Current Repo1 / Repo2 worker chain — shared Guard policy

This is the canonical Windows worker source for both Fortis Repo profiles. The
nine executable PowerShell files are pinned by `source-manifest.json`; the
manifest inventory hash is itself pinned by the Windows dispatcher and the
Script Center resolver.

## Shared policy

`launchers/shared/FortisContainerPolicy.ps1` owns the common Windows identity,
Docker container, Linux runtime, network, mount, namespace, capability,
seccomp, resource-ceiling, `NODE_OPTIONS`, workspace and guarded config-repair
checks. Repo1 and Repo2 retain their separate profile, key/ACL, tunnel and
quiet-log behavior. A single self-integrity anchor lives in the shared module;
there are no four duplicated policy hashes in the entrypoints.

The guard checks effective container isolation rather than pinning a particular
Docker image ID or Desktop Commander module SHA. The image ID remains visible
in Preview. This is a container-isolation guard, not signed-image provenance:
a malicious image still has the container's allowed workspace and egress.
The Windows Tunnel Runtime executable remains SHA-256 pinned in the shared
policy.

## Entrypoints

- `Repo1-Worker.ps1` → Repo1 quiet launcher → adjacent Repo1 `control.ps1`.
- `Repo2-Worker.ps1` → `Start-Fortis.ps1` → `Common.ps1` / shared policy →
  Repo2 quiet launcher → Repo2 Direct Guard.
- Repo2 passes the inspected full Docker Container ID through its worker,
  launcher and Docker exec calls; it does not resolve the reusable name again.

The dispatcher defaults to read-only Preview. Start requires the canonical
Windows `Repos\tunnel` clone, approved origin, clean/synchronized `main`, and
an explicit typed owner confirmation. The dispatcher does not stop or recreate
the Fortis container or stop the other tunnel. Repo2 may start the already
existing container only if it is already stopped; this release process does
not invoke Start. The separate Repo1 `control.ps1` retains its explicit manual
control actions, but the worker/dispatcher does not call its Stop actions.

Windows-local profiles, keys, ACLs, runtime logs, installed Tunnel Client
binaries, Docker state and the existing container remain outside Git.

## Shared runtime diagnostics

The source targets narrow runtime v0.0.21. Both launchers call `Invoke-FortisRepoRuntime` in the shared policy for explicit restart, loopback health, per-run console/JSONL mirroring and runtime PID evidence. Profiles, keys and Docker isolation remain separate concerns. Installation and staged verification: [runtime resilience](../../../docs/REPO-RUNTIME-RESILIENCE.md).
