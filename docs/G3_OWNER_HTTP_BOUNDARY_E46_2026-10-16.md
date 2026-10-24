# E46 - G2 and owner HTTP boundary, 2026-10-16

## Actual guest-side read-only evidence

G2 identity FORTIS_M\FortisHostG1, SID ending -1009, Session2, nonadmin.
Guest MCP confirmed 127.0.0.1:8093 TCP OPEN and earlier
/api/archive-coverage HTTP200. Against pre-fix still-running Observatory:
HEAD /server.py returned 200; HEAD /../README.md returned 200.
Only HTTP status lines, no response bodies or private file contents.
No owner keys, guest credentials, backups or private files were read.
No Windows files, ACLs, tunnels, services or processes were altered.

These HEAD results confirm that owner Observatory, without cross-SID
authentication, exposed static source and out-of-root path routing.
It runs with alexa rights, allowing higher-privilege file disclosures
to lower-privileged HTTP callers. This does not prove an exfiltration
already occurred, nor owner token takeover, admin rights or RCE.

## Prior G2 tests and scope

Old tests for OS ACLs, selected protected assets, GUI station,
handles, known Broker and services remain PASS in stated scopes.
E13/E15/E19 already identified owner localhost cross-session GET200.
Old owner HOST retired at E43; Repo cutover E38 removed selected
admin interfaces. Universal owner IPC/API 5.8 remained PARTIAL.
New owner Observatory was created later and NOT covered by previous
native G2 network and API acceptance.

## Surfaces (bounded, no broad port scan)

- Old owner HOST: retired; listener8080 absent in E43 dated evidence.
- Repo runtime-only: selected admin GET404, has health/metrics;
  not a promise of all diagnostic bodies being safe forever.
- Selected Broker: E41 scoped denies; not a universal new-broker proof.
- Observatory8093: confirmed accessible from G2, unsafe in live
  pre-fix process; owner auth missing before this source candidate.
- Observatory8092: not evaluated as live/healthy by these probes.

## Source-only hardening prepared (not deployed)

E45 already added static asset allowlist. E46 adds:
- all API GET/HEAD/POST routes protected by a 256-bit random bearer token;
- token exists only in owner Windows interactive console and
  Python process memory, not in repo files, argv or URL;
- browser unlock form keeps token in volatile JS memory and sends
  Authorization header; no cookies/localStorage; downloads use fetch;
- CSP, no-referrer, nosniff, anti-framing headers;
- Windows GetUserNameW startup check and terminal-only owner launch;
- synthetic untrusted guest negative and owner positive HTTP tests.

This is APPLICATION bearer authorization, NOT direct Windows SID
authentication. Token theft would bypass it. Moreover owner execution
directly from a source checkout writable by Fortis Repo introduces a
code supply-chain/TOCTOU risk. Future deployment should use reviewed
pinned bytes copied into an owner-protected application location.
Source changes do not patch the already-running Python process.

## Gate before considering a new Windows run

1. Owner stops ONLY preview8093 via Ctrl+C in its PowerShell.
   Leave G2/Repo/Docker/other services intact.
2. Confirm 8093 no longer listens using one read-only connection check.
3. Review and independently pin source in owner-protected location.
   Obtain separate consent before native install or start.
4. Owner-positive local HTTP tests with hidden token (no screenshots,
   chat, transcripts or guest exposure) must succeed.
5. Guest-negative calls without token to selected API GET/HEAD/POST
   must return 401. Restricted static requests must return 404.
   Do NOT issue a guest mutating call with the valid owner token.
6. Unexpected success/different source hash -> owner stops preview.
7. Later, review existing sanitized logs for possible historical
   access if owner approves. No log entries is not evidence of
   no historical exfiltration.

Windows localhost is machine-local, not Windows-SID-private.
True per-SID IPC would use named pipes with protected DACL or equivalent,
not merely an HTTP Host or Sec-Fetch-Site header.
