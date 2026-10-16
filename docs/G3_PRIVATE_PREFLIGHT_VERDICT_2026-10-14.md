# G3 — detailed preflight verdict, 2026-10-14

Срез 2026-10-13T17:10:10.1393719Z / 00:10 Asia/Bangkok. **DIAGNOSTIC_SOURCE_STAGED; FAILURE NOT YET IDENTIFIED.** [JSON](G3_PRIVATE_PREFLIGHT_VERDICT_2026-10-14.json). Предыдущая [transport точка](G3_PRIVATE_LAUNCHER_PREFLIGHT_TRANSPORT_2026-10-13.md) прошла в actual guest до всех трёх progress stages; затем final predicate отказал.

Old operator 0CF2… не печатал testResult: generic failure не различала child exit, SID/admin/visible/station mismatch и Node.pass=false. Старый payload уже не сохранён. Новый operator **только выводит synthetic report перед тем же predicate**: expected/actual SID/station, admin/visible, child/Node exit и Node CLI/Edge/cleanup fields. Password/key не передаются child test и отсутствуют в отчёте. No permission expansion or checks bypass.

Windows SHA/component capture/compile/AST/Preview PASS. Original owner WinSta0/default hashes unchanged; ACL writes=0; credentials prompted=false. Supervisor F619… unchanged. Actual guest failure condition remains unknown until a local report; не объявлять исправление Edge или descendant isolation по этому диагностическому patch.

Следующий local шаг: fresh elevated owner PowerShell alexa, pinned command ниже. Windows password FortisHostG1 только local masked prompt; вернуть JSON после **Private preflight report (synthetic test only)**. HOST/Repo не закрывать. Existing preflight-before-key/backup/main-ACL ordering preserved.

```powershell
$script = 'C:\Users\alexa\Repos\tunnel\runtime\host-g2\window-isolation\Start-G2PrivateWindow.ps1'
$bytes = [IO.File]::ReadAllBytes($script)
$sha = [Security.Cryptography.SHA256]::Create()
try { $hash = ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '') }
finally { $sha.Dispose() }
if ($hash -ne '2CB5D5063DDD9F67743A5DAAF31F1A1A2A56A224619B8385FC69FC499B051ABC') {
    throw 'Скрипт изменился — запуск остановлен'
}
& ([scriptblock]::Create([Text.Encoding]::UTF8.GetString($bytes))) -Mode Launch
```

| Source | SHA256 |
|---|---|
| Start-G2PrivateWindow.ps1 | 2CB5D5063DDD9F67743A5DAAF31F1A1A2A56A224619B8385FC69FC499B051ABC |
| G2WindowSupervisor.cs | F61983384AFF51CCC007586DA614C710306FDCC52981C5C0A3B77AD98202045D |

Live main-window ACL/runtime not applied/accepted. Runtime/services/tasks/Docker/Sites и ключевые файлы не менялись; commit/push нет. G3 OPEN / G4 NOT_ACCEPTED. Следующие gates: determine exact failed report field, targeted compatibility/isolation fix, actual guest/private runtime/window deny acceptance; owner APIs/whole-chat/service/SMB/persistence/interactive path residuals remain open.
