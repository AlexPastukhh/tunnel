# Observatory V1 — unified textbox and session tabs candidate

**SOURCE-ONLY CANDIDATE. NOT INSTALLED IN WINDOWS OWNER VIEWER.** Prepared 2026-10-24 from committed Observatory source `38f705be33a7eb4123b0fc73f1fafc8b98da6e29`. Neither Windows Viewer, Docker, G2 nor the two Repo tunnels was restarted or modified by this package.

## Included

- `owner_viewer.py`, `owner_dispatch.py`: new Viewer UI and bounded dispatch protocol.
- `viewer-unified-workflow.patch`, tests and `manifest.json` with SHA-256.
- The earlier horizontal tabs candidate is included in this package's full `owner_viewer.py` and patch; it is **not** assumed installed.

## Behavior

Top header has horizontal session tabs. Drag/drop (same registered session IDs only) and Alt+ArrowLeft/Right change their order; owner browser `localStorage` stores user order and reads it back. Active session, tasks and archive ordering are not changed. Tabs have horizontal scroll and ordinary arrow-key navigation.

The Observatory textbox exposes `Файл`, `Вставить`, `Нажать Send`, `Файл + Send`. File+Send is **one scoped dispatch**, not two separate requests; delay choices are 500/1000/2000/3000/5000/10000 ms and apply only *after* verified attachment. The Notifier must check the draft/card/task again just before clicking. The broker validates the bounded integer and forwards the value only to a `send` command, preserving at-most-once dispatch and short TTLs.

Exact unsent draft text is saved/read back in **the owner Edge profile localStorage**, scoped by reporting_session_id; it does not go to the Docker archive merely by typing. A separate restore control is available. On a matching `dispatch_id` and a Notifier `send_initiated` ACK with valid `task_id`, the textbox becomes empty only if its contents have not changed. The locally persisted previous original remains recoverable; after browser reload an already sent draft **does not automatically repopulate** the editor. A queued, refused or ambiguous command never triggers automatic clearing or retry. An unavailable owner-local store prevents unsafe clearing and dispatch of a new original.

## Verification

- `python3 -m unittest -q test_owner_dispatch.py test_owner_viewer.py`: **44/44 PASS**, source-only.
- Node `test_owner_viewer_ui.mjs`: PASS for existing archive interaction, tabs, keyboard, localStorage draft, sent recovery and reorder.
- `git apply --check observatory/v1/candidates/unified-workflow-20261024/viewer-unified-workflow.patch`: PASS against committed V1 source.
- Installed Windows Viewer ACL/SID hash, Edge Clipboard, real dispatch receipt and ChatGPT delivery: **NOT VERIFIED**.

## Application (source only, not yet advised for live Windows Viewer)

From `tunnel` root, review `manifest.json` and run `git apply --check observatory/v1/candidates/unified-workflow-20261024/viewer-unified-workflow.patch`. Apply the patch **only with the matching Notifier v5.7.33 update and an owner-controlled backup/rollback**. After source application, test with `python3 -m unittest` on the two affected modules and `node observatory/v1/test_owner_viewer_ui.mjs`. Do not overwrite the protected installed Viewer by replacing only `owner_viewer.py`: `owner_dispatch.py` and the installed source version must also match.

**Not yet included:** binary file transport from Viewer to Notifier, Windows Explorer copied-file support, real Edge guest-negative tests. An unverified path string must never grant arbitrary filesystem access. No HTTP pairing, G2 relay or new token was added by this candidate.
