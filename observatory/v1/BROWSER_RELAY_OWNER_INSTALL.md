# Fortis Observatory v8 — narrow Windows↔Docker relay (SOURCE-ONLY)

**Current status:** relay code prepared and tested in isolated synthetic
processes, **NOT deployed or started in Windows**. The existing Docker
Observatory remains the only archive and listens on container loopback
§127.0.0.1:18754§.

## Function and boundaries

§owner_browser_relay.py§ is a *Windows-local forwarding endpoint* on
Windows §127.0.0.1:18754§. It is NOT another Observatory and it stores
no separate conversation archive. It allows only these three browser calls:

- §GET /api/observer-status?session=...§ with scoped observer key;
- §GET /api/task-activity?session=...&task=...§ with scoped observer key;
- §POST /api/user-messages§ with scoped writer key; original accepted only
  after an already accepted event under the same task ID.

Full archive/history, pairing administration, registration, owner bearer,
other URLs and HTTP OPTIONS are never exposed. Only exact
§Host: 127.0.0.1:18754§ is accepted; untrusted Origin, missing capability,
invalid requests, cookies, Authorization and POST without bounded body
are rejected. No CORS permission is returned. It does not open a Docker
port, publish §0.0.0.0§ or add a tunnel.

For each permitted call it runs fixed-argument
§docker.exe exec -i APPROVED_CONTAINER python3
/workspace/repos/tunnel/observatory/v1/browser_relay_dispatch.py§.
The original, the scoped key and query are conveyed **through stdin only**,
not command-line args, logs or Repo event summary. Dispatcher inside Docker
uses localhost §127.0.0.1:18754§, validates exact allowed route and per-task
IDs and returns bounded JSON. There is no shell command interpolation.

§repo_browser_pair.py§ is a separate **explicit owner-console-only**
pairing command. §owner_browser_relay.py pair§ asks the Docker service for
the selected session's observer or (only with §--writer§) writer capability.
These secrets are shown **only to the owner at the local Windows console**;
never call that mode through ChatGPT/Fortis Repo tools, never paste its
output into chat, GitHub, shell logs or screenshots.

## Gates before owner installation

1. Owner must independently review/pin **all** source files, copy the
   relay to their ACL-private §%LOCALAPPDATA%\FortisObservatoryV1\Relay§,
   and verify Windows SID ownership, NTFS ACL, reparse points and hashes.
   The script refuses start from writable §Repos§ / §Workfiles§ checkouts
   by requiring this installation directory. Source SHA alone is not
   approval or a substitute for ACL acceptance.
2. Owner must independently identify exactly which Fortis Repo Docker
   container to use. Windows §docker.exe§ presence in a guest test
   confirms neither container permissions nor owner identity. Check
   that the target is the **existing** Repo Observatory instance with
   its internal volume; do not create or expose another daemon.
3. Perform owner-positive **and** Windows guest-negative tests, including
   untrusted origins, guessed or missing capabilities and Docker CLI/daemon
   permissions. If guest has Docker exec/full-volume access, address that
   explicitly before enabling live conversation transport.
4. Test safe pairing for a selected/synthetic conversation in a real
   owner browser, normal native ChatGPT Send, accepted task activity,
   exact original sha256/read-back, offline retries and guest failure.
   Do not assume Tab Notifier is installed just because source tests pass.
5. No changes to §netsh§, Docker published ports, owner ACL, Windows
   startup tasks, browsers or installed user scripts happened in this step.

### Illustrative owner commands AFTER those approvals — NOT executed

~~~powershell
# Already reviewed and installed in a protected owner directory:
$relay = Join-Path $env:LOCALAPPDATA 'FortisObservatoryV1\Relay\owner_browser_relay.py'
# Approved real container identity; this placeholder is not runnable:
$container = 'APPROVED_REPO_CONTAINER_NAME'
python $relay serve --container $container

# In a SECOND protected owner console, with an approved session:
python $relay pair --container $container --session 'rs_32HEX_SESSION_ID' --writer
~~~

The pairing JSON produced in the second console must be pasted only into
Notifier's pairing dialog for that exact conversation. The browser has
no owner bearer token. The client origin §http://127.0.0.1:18754§
is present in Notifier SOURCE but is **not** a real Windows-reachable
endpoint until the owner relay has passed these gates and been started.

## Evidence and open items

§python3 -m unittest -q test_browser_relay.py§ — **6/6 PASS** in
separate ephemeral Linux servers without exposing any Windows port.
Tests cover per-task receipt, exact Unicode original and idempotent write,
admin/history/pairing route denial, origin/Host/key and CORS preflight
denial, body+key absent from Docker command argv and private-console
pairing separation. Live Windows owner/Edge/guest access remains UNVERIFIED.

Docker Observatory stays running and no real conversations or capabilities
were staged into its persistent archive by these tests.

## Additional fail-closed gate: owner SID and exact container

The Windows relay now REQUIRES a reviewed owner-private file named
§approved-owner.json§ next to the installed §owner_browser_relay.py§.
It must contain **exactly** two JSON string fields:
§owner_sid§ and §container§. The owner obtains their real Windows SID
locally using §whoami /user§, identifies the exact approved Repo Docker
container, and independently protects this file with NTFS owner ACL.
Do **not** share SID/config in chat and do not use placeholder values.

The relay refuses startup when the config is missing, malformed,
the current process Windows SID differs, or §--container§ differs.
This is an additional accidental-mismatch guard, **NOT a substitute**
for proper owner ACL, guest-negative Docker permissions and reviewed
source pin. No §approved-owner.json§ was created by this work,
and no owner relay listener has been started.
