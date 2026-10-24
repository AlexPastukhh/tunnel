# Fortis Unified Workflow 2026-10-24 — Windows owner installation / Edge smoke

**Status: Repo sources deployed and source tests PASS; owner-protected Windows installation and Edge smoke need the owner's action.** Do not run on G2 or as Administrator. No Docker/tunnel changes.

## What has been updated in Repo

- Main Notifier source in `C:\Users\alexa\Repos\tabnotifier-fileautosend-autochat\` — 5.7.33. The generated `chatgpt-tab-notifier.user.js` was rebuilt from 22 local modules and `npm run verify` passed **288/288**. Build readback SHA-256 `c304559a8d8dcec44031140d6c62b8fdad363944026acb7adaf34143e028d540`. The candidate's prebuilt copy differs only in CRLF/LF encoding, not semantic content.
- Main Observatory V1 source in `C:\Users\alexa\Repos\tunnel\observatory\v1\`: `owner_viewer.py` SHA-256 `f3230cb531d89d9cc4f60bea52fd5722b1b1e82a724759dede6636aabf806c8a`; `owner_dispatch.py` SHA-256 `9da1bc2a223804660c2a9ea9033b86889dca7119d3a1b1dab18c85565360fea5`.
- Prior Repo bytes were backed up inside container at `/workspace/repo/fortis-install-unified-20261024`, and existing Git commits provide another restore source.
- Python Viewer 44/44 PASS and Node UI synthetic tests PASS.

## Owner-side secure staging (non-elevated PowerShell as alexa)

Do not execute `.ps1` directly from the Repo RW directory. Copy a SHA-pinned copy into the already-approved, private owner Viewer directory:

```powershell
$ErrorActionPreference = 'Stop'
$installerSource = 'C:\Users\alexa\Repos\tunnel\observatory\v1\candidates\unified-workflow-20261024\Apply-FortisUnifiedWorkflow.ps1'
$installerSha = 'c9d436cae433036a190d96b2a5568190425929c5b3f090ea4a238dcd6fd4a1e6'
$who = [Security.Principal.WindowsIdentity]::GetCurrent()
if (($who.Name.Split([char]92)[-1]) -ine 'alexa') { throw 'Run under the approved Windows account' }
if (((Get-Item -LiteralPath $installerSource -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Linked source refused' }
if ((Get-FileHash -LiteralPath $installerSource -Algorithm SHA256).Hash.ToLowerInvariant() -cne $installerSha) { throw 'Repo installer SHA mismatch' }
$ownerDir = Join-Path $env:LOCALAPPDATA 'FortisObservatoryV1\Viewer'
if (-not (Test-Path -LiteralPath (Join-Path $ownerDir 'approved-owner.json'))) { throw 'The protected installed Viewer is missing' }
$installer = Join-Path $ownerDir 'Apply-FortisUnifiedWorkflow.ps1'
if (Test-Path -LiteralPath $installer) {
  if (((Get-Item -LiteralPath $installer -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Linked destination refused' }
}
Copy-Item -LiteralPath $installerSource -Destination $installer -Force
if ((Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash.ToLowerInvariant() -cne $installerSha) { throw 'Private copy SHA mismatch' }
& $installer -Action Preview
```

Expected: `PREVIEW_OK=True`. This checks exact source/install hashes, protected ACLs, owner SID and whether the installed version is known. **If it refuses, do not bypass the check or replace files manually**; provide the error and hash to review.

## Install

Stop **only the Observatory Viewer** window via Ctrl+C or its normal close action. Do not stop Docker, tunnels or G2. On the same owner PowerShell:

```powershell
& $installer -Action Install
```

Expected: `INSTALL_OK=True` and `BACKUP_ID=...`. Preserve BACKUP_ID. Two separate .bak files are saved in the protected owner directory. Restart Viewer **with its existing owner shortcut**, not from Repo.

## Tampermonkey / Edge

Notifier source 5.7.33 is already in the main Repo, **not necessarily active in Edge**. Check the existing Tampermonkey Loader `@require` still points to the permitted local `chatgpt-tab-notifier.user.js`; do not create a second userscript. The loader's own `@version` may be older and does not prove actual runtime code version. Refresh the intended ChatGPT tab to reload the local file, then verify that the Notifier panel shows `Нажать Send`, `Файл` and `Вставить`. If it still shows ➤, stop and verify `@require` and file URL permission instead of changing the Loader blindly.

## Safe Edge smoke

1. Confirm Viewer works under the same owner profile and the session tabs appear on the lower header row.
2. Move a tab with drag-and-drop or Alt+Left/Right; refresh Viewer; check order and selected session.
3. Type a *harmless test prompt* in Observatory, then reload **before Send**. Verify text reappears as a draft. Clearing browser storage is outside the recovery promise.
4. In Notifier, use `Вставить`, confirm the ChatGPT native composer is populated **without** Send. Then use `Нажать Send` once. Confirm no duplicate task/file and original is available in local history.
5. In Observatory, test `Файл` (no Send), then explicitly `Нажать Send`. Observe dispatch status; `send_initiated` is not a ChatGPT receipt. Check that original can be restored, and new typing isn't deleted.
6. For `Файл + Send`, use an ordinary short test prompt; select 1 second; verify file card exists before delay and exactly one click occurs. Check accepted task_id/session in Observatory only after the archive actually received it.
7. Test an intentional canceled Send (change chat during delay) **without automatic replay**. If unsure of previous result, do not retry blindly.

Real binary attachments from Viewer, Explorer Ctrl+C/Ctrl+V files and actual Windows Clipboard transfer **are not implemented** in this release. Do not test by typing absolute Windows paths into dispatch.

## Rollback if needed

Stop only Viewer; with the original `BACKUP_ID` from installation run:

```powershell
& $installer -Action Rollback -BackupId 'yyyyMMdd-HHmmss-32hex'
```

The command restores **both** old Viewer files and checks readback. Restart Viewer with the existing shortcut. For the Notifier source, use the pre-change Git commit `b74aa80` or the isolated backup; **do not reset unrelated work**, and do not force-push. Revert only the ten files listed in `candidates/unified-workflow-5.7.33-20261024/manifest.json` after checking no newer edits were made.

**Limits:** Linux Fortis Repo cannot operate the owner's protected Windows Viewer or browser UI. Passing synthetic tests does not imply Edge test PASS. Report the Preview/Install/Edge results before claiming end-to-end success.
