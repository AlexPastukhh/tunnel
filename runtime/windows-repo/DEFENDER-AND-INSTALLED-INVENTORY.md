# Windows installed Tunnel + Defender exclusions — сверка

**Статус: PARTIAL / 2026-11-02. Owner-confirmed: G2 больше не используется и не актуален.** В Docker собраны исходники двух quiet Repo launchers, Repo1 control, Repo2 guard и SHA manifest; **живую Windows и её исключения Defender из Docker прочитать нельзя**. G2-специфичные Windows Node/Desktop Commander — legacy, не текущие зависимости Fortis Repo. Ниже — источник для **read-only** Windows-проверки, не процедура изменения AV или переключения Tunnel.

## Что проверено в Docker

- Четыре source PS1 в `runtime/windows-repo/` сопоставлены по SHA с `release-manifest.json` и с отслеживаемыми в `script-control-center/launchers/` копиями. Установленные Windows-байты не проверены.
- `tunnel` и `script-control-center` содержат **0 отслеживаемых .exe/.dll/.msi**. В документах клиент/Runtime установлены в `C:\Tools\tunnel-client\`, но **их EXE, происхождение, официальная загрузка, лицензия и текущая установленная SHA подлежат отдельной проверке**; не копировать сомнительные/неподписанные EXE автоматически в Git.
- Repo1 `control.ps1` содержит **историческое действие `Start`**, которое ссылается на соседний `run-tunnel.ps1`; этого файла в новом quiet-only bundle нет. `Invoke-FortisRepo.ps1` использует только `Get-RepoTunnel` из dot-source control и запускает `run-tunnel-quiet-logs.ps1` напрямую. **Пока не вызывать `control.ps1 -Action Start` из нового Windows bundle.** При переходе на единственный источник потребуется отдельная ревизия control/пина с Windows приёмкой.
- Repo2 quiet startup использует Windows-local `FortisRepoPlus2\profiles`, `secrets`, и соседний pinned Guard. Setup намеренно отключён. Ключи, profile-файлы, Windows shortcut и runtime-логи не должны попадать в Git.
- Общий Docker, pinned image/container, Direct DC и 2 разных профиля — инфраструктура, а не переносимые версии PS1; Windows Windows-clone + README не воспроизводят чистую машину без этих зависимостей.
- G2 — **retired / не используется по текущему подтверждению владельца от 2026-11-02**. Его Windows Node/Desktop Commander не являются зависимостями текущего Fortis Repo и не входят в этот bundle. Прежняя E43-приёмка от 2026-10-16 — историческое состояние, не свидетельство текущего использования. Project Checker, Observatory и hosted Sites — отдельные контуры.
- В репозитории не нашлось актуальной таблицы локальных Defender ExclusionPath/Process/Extension. Наличие или отсутствие фактических исключений неизвестно.

## Windows PowerShell: только просмотр исключений

В собственной обычной Windows PowerShell (при отказе в чтении — сообщить об ошибке, не менять политики):

```powershell
$p = Get-MpPreference -ErrorAction Stop
'ExclusionPath','ExclusionProcess','ExclusionExtension' | ForEach-Object {
    $kind = $_
    @($p.$kind) | Where-Object { $null -ne $_ -and $_ -ne '' } |
        ForEach-Object { [pscustomobject]@{Type=$kind;Value=[string]$_} }
} | Format-List
```

**Не присылать секреты, полные конфигурации ключей или содержимое файлов.** Строки путей/пользовательские имена можно маскировать, сохраняя имя самого скрипта/EXE. Никаких `Add-MpPreference`, `Remove-MpPreference`, `Set-MpPreference`, `Set-MpComputerStatus` или действий с Windows Security. Даже исключение процесса влияет на **сканирование открываемых им файлов**, а не просто на сканирование EXE (см. Microsoft Learn).

После получения списка:
1. Сгруппировать только tunnel-related исключения по точным файлам, директориям и процессам, отделить устаревшее и широкое покрытие.
2. Для каждого относящегося к Tunnel файла — read-only `Test-Path` и `Get-FileHash -Algorithm SHA256`; каталогов — сначала только имена верхнего уровня, без рекурсивного чтения документов/секретов.
3. Сопоставить с Git bundle, отдельно пометить `MATCH / DIFFERENT / MISSING IN GIT / OUT OF SCOPE / UNVERIFIED`.
4. Уточнить старую причину обнаружения через Windows Security Protection History **без** изменения исключений или отправки файла в VirusTotal.
5. Подготовить owner-reviewed Windows cutover и rollback, не ломая два работающих подключения.

### Известные кандидаты для Windows hash inventory (без чтения содержимого)

```powershell
$paths = @(
    "$env:USERPROFILE\chatgpt-repo-mode\control.ps1",
    "$env:USERPROFILE\chatgpt-repo-mode\run-tunnel.ps1",
    "$env:USERPROFILE\chatgpt-repo-mode\run-tunnel-quiet-logs.ps1",
    "$env:LOCALAPPDATA\FortisRepoPlus2\FortisRepo2.ps1",
    "$env:LOCALAPPDATA\FortisRepoPlus2\FortisRepo2-quiet-logs.ps1",
    "$env:LOCALAPPDATA\FortisRepoPlus2\Repo2DirectGuard.ps1",
    'C:\Tools\tunnel-client\tunnel-client.exe',
    'C:\Tools\tunnel-client\runtime\v0.0.15\tunnel-client-runtime.exe'
)
foreach ($path in $paths) {
    if (Test-Path -LiteralPath $path -PathType Leaf) {
        [pscustomobject]@{
            Path=$path
            Exists=$true
            SHA256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
        }
    } else {
        [pscustomobject]@{Path=$path;Exists=$false;SHA256=$null}
    }
}
```

Windows команды пока не запускались в рамках этого аудита.

## Сверка фактически присланных Defender exclusions (2026-11-02)

Это сопоставление **по исходникам/докам Docker**, не readback Windows-файлов и не доказательство, что исключённые файлы сейчас существуют.

| Windows path / exclusion | Роль по репозиторию | Есть ли эквивалент в Docker Git/runtime? | Вывод |
|---|---|---|---|
| `ExclusionPath C:\Tools\desktop-commander-runtime\node.exe` | Исторический Windows Node для G2/старой Windows DC цепочки. Исторический G2 evidence 2026-10-13 фиксировал SHA256 `2FFE3ACC0458FDDE999F50D11809BBE7C9B7EF204DCF17094E325D26ACE101D8`. | **Windows node.exe отсутствует** в Git. Docker использует Linux Node `/usr/local/bin/node` v22.23.3. | **Legacy / не нужен текущему Fortis Repo** по подтверждению владельца. Кандидат на удаление из Defender exclusions после read-only проверки точного типа исключения и наличия других потребителей этого файла. |
| `ExclusionPath C:\Tools\desktop-commander\` | Исторический Windows-пакет Desktop Commander для G2. | Для текущего Repo в Docker установлен отдельный Linux-пакет `@wonderwhy-er/desktop-commander@0.2.52` в `/opt/dc/node_modules/@wonderwhy-er/desktop-commander`; entry SHA256 `A4145198DC75CD34E7C7452C2054B4CC0D29E199AE1459961A17E4DA25A13500`. Он совпал с историческим SHA G2 `dist/index.js`. | **Windows-каталог G2 не нужен текущему Fortis Repo.** Совпадение одного entry-файла не означает, что Windows-каталог нужен Docker или является его копией. Кандидат на удаление из Defender exclusions после проверки, что в каталоге нет других действующих потребителей. |
| `ExclusionPath C:\Tools\tunnel-client\runtime\v0.0.15\tunnel-client-runtime.exe` | Windows runtime v0.0.15 для действующих Repo1/Repo2 launchers. | EXE в Git намеренно отсутствует. В Git есть точная версия, официальный release URL, ZIP SHA256 `AA5DDB14DDDD602FA59F3E6F4401AA8A79A218E341466226B7434127DFF65DBC` и EXE SHA256 `A922D372D6BE0649156FBC1C8A040597F1F4BB5B4356890151D7875602593B1A`. | **Нужная внешняя Windows-зависимость для Repo**, не Docker Linux-компонент. Должна быть установлена/сверена на Windows; не добавлять EXE в Git. |
| `ExclusionPath C:\Tools\tunnel-client\tunnel-client.exe` | Полный Windows Client: Repo2 source использует его для `doctor`; исторический Repo launcher также использовал full client. | EXE отсутствует в Git. Документация содержит исторический локальный SHA256 `1946DE55A038313A9B9B2458D05FE1719FA9CF1F20A94DD5F38FC26A98BFDD42`. | Внешняя Windows-зависимость для Repo2. В security register указано, что Authenticode status был `NotSigned`; исторический SHA не доказывает вендорское происхождение. Repo2 launcher проверяет наличие Client, но его startup hash pin — отдельный gap. Не считать полностью аттестованным. |
| `FortisG3ApiTest\runtime-empty-transport-...\artifact\tunnel-client-runtime.exe` | Копия runtime для отдельного синтетического G3 local-API теста с synthetic YAML/key и loopback control plane. | В Git есть исторические fixture source, инструкция и evidence; конкретные временные каталоги/EXE не являются tracked source. | **Тестовый временный артефакт, не production Repo.** В Docker не нужен. Не переносить в Windows release bundle. Проверить, существуют ли каталоги сейчас. |
| `FortisG3ApiTest\runtime-v0.0.15-...\artifact\tunnel-client-runtime.exe` | Второй synthetic fixture — runtime v0.0.15 для отдельного теста transport/API. | Исторические fixture source и документация находятся в Git; точная временная копия не tracked. | **Тестовый временный артефакт**, не текущий Repo launcher/profile. В Docker не нужен. |

### Ключевые уточнения

- E43 от 2026-10-16 — историческая приёмка ограниченного G2 scope. Она не описывает текущее использование. Актуальное подтверждение владельца от 2026-11-02: G2 не используется и не актуален; его Windows Node/Desktop Commander относятся к legacy.
- Repo1/Repo2 Direct используют Windows Tunnel Client/Runtime как транспорт, но сам Desktop Commander работает в Linux-контейнере из `/opt/dc`. Windows Node и Windows Desktop Commander package не являются обязательными для текущего Direct Repo path.
- Windows EXE не должны лежать в Docker Git только ради совпадения исключений Defender. Git хранит исходники, версии, проверочные SHA, ссылки и установочные/rollback инструкции; бинарники устанавливаются на соответствующем Windows host из проверенного источника.
- Текущая проверка Docker entry-файла DC установила SHA совпадение с историческим G2 evidence. Это лишь сравнение одного файла; Windows Node, весь npm tree, окружение и установленные Windows ACL не сравнивались.
- `C:\Tools\desktop-commander\` — широкое directory exclusion. Последний readback владельца показал `ExclusionProcess` пустым, а `node.exe` находится именно в `ExclusionPath`; process-wide исключения для него в этом readback нет. `ExclusionExtension` в присланном выводе не показывался.
- Две папки `FortisG3ApiTest` похожи на остатки временных fixtures по имени и source design. Сам факт существования/удаления на Windows ещё не проверен.

**Применение/решение:** никаких изменений Defender, профилей, ACL, Windows runtime, Docker, общих Volumes, Git push или переключения ярлыков.

## Windows readback — 2026-11-02

- **Docker → Windows HTML transfer passed.** On Windows, `docker inspect` confirmed `fortis-repo-test` was running (otherwise the script would have stopped); `docker cp` copied `fortis-mirror-compact-prototype.html` to the user's Downloads folder; SHA256 matched the expected value `8ae9ceb9cab6278a3e266e3fe030c83295828fbafe6ef8e3f71b4f23d2ae96d5`. `Start-Process` was invoked without a reported error. This confirms file transfer/integrity, not a visual/browser rendering acceptance.
- **Defender exclusions remain UNVERIFIED.** `Get-MpPreference` was run in a non-elevated PowerShell session. Both `ExclusionProcess` and `ExclusionPath` returned `N/A: Must be an administrator to view exclusions`. This is an access limitation, not evidence that the lists are empty. Repeat read-only retrieval in an elevated PowerShell session; do not change exclusions.
- **Windows file existence/hash inventory remains UNVERIFIED.** The pasted implicit table output wrapped/truncated columns, so `Exists`, `Type`, and `SHA256` values cannot be reliably read. Do not infer file presence or absence from that output. Re-run the same `$paths` loop and pipe the result to `Format-List Path,Exists,Type,SHA256` (or export a CSV) so every value is visible.
- No Defender settings, files, tunnel processes, profiles, shortcuts, Docker state, or Git state were changed by these checks. No deployment or cutover was performed.

### Safe Windows follow-up commands

Run the Defender query in **PowerShell as Administrator** (read-only):

```powershell
$p = Get-MpPreference -ErrorAction Stop
[pscustomobject]@{
    ExclusionProcess = (@($p.ExclusionProcess) -join '; ')
    ExclusionPath = (@($p.ExclusionPath) -join '; ')
    ExclusionExtension = (@($p.ExclusionExtension) -join '; ')
} | Format-List
```

For the existing `$paths` array, re-render the file inventory without table truncation:

```powershell
$results = foreach ($path in $paths) {
    if (Test-Path -LiteralPath $path) {
        $item = Get-Item -LiteralPath $path
        [pscustomobject]@{
            Path = $path
            Exists = $true
            Type = if ($item.PSIsContainer) { 'Directory' } else { 'File' }
            SHA256 = if (-not $item.PSIsContainer) {
                (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
            } else { $null }
        }
    } else {
        [pscustomobject]@{ Path=$path; Exists=$false; Type=$null; SHA256=$null }
    }
}
$results | Format-List Path,Exists,Type,SHA256
```


## Elevated Windows Defender and file inventory — 2026-11-02

### Defender exclusions readback

- `Get-MpPreference` returned a readable result in the user's latest PowerShell session.
- `ExclusionProcess` is empty. In particular, `C:\Tools\desktop-commander-runtime\node.exe` is **not** listed as a process exclusion in this readback; it is listed under `ExclusionPath`.
- `ExclusionPath` contains the following relevant entries:
  - `C:\Tools\desktop-commander-runtime\node.exe`
  - `C:\Tools\desktop-commander\`
  - `C:\Tools\tunnel-client\runtime\v0.0.15\tunnel-client-runtime.exe`
  - `C:\Tools\tunnel-client\tunnel-client.exe`
  - `C:\Users\alexa\AppData\Local\FortisG3ApiTest\runtime-empty-transport-1791882037414\artifact\tunnel-client-runtime.exe`
  - `C:\Users\alexa\AppData\Local\FortisG3ApiTest\runtime-v0.0.15-1791880600365\artifact\tunnel-client-runtime.exe`
- Other observed exclusions, not classified as tunnel dependencies: `C:\gd-cap\windows-app\app\build\audio-helper\gd-cap-audio.exe`, three Kaspersky WebView2 data directories (`AVP21.23`, `AVP21.24`, `AVP21.25`), and `C:\Users\alexa\Downloads\Telegram Desktop\shadowlos_windows\throne\`. Do not alter these as part of tunnel cleanup.

### File existence and hash readback

The user reran `Test-Path` / `Get-Item` / `Get-FileHash` for all six tracked Windows paths. All six returned `Exists=True`, `Type=File`:

| Windows file | Observed SHA256 prefix in console | Assessment |
|---|---|---|
| `C:\Tools\desktop-commander-runtime\node.exe` | `2FFE3ACC045...` | Prefix matches historical G2 evidence; full value was truncated in the pasted table. |
| `C:\Tools\desktop-commander\node_modules\@wonderwhy-er\desktop-commander\dist\index.js` | `A4145198DC7...` | Prefix matches Docker/current register and historical G2 entry evidence; full value was truncated. |
| `C:\Tools\tunnel-client\tunnel-client.exe` | `1946DE55A03...` | Prefix matches historical local hash; full value was truncated. |
| `C:\Tools\tunnel-client\runtime\v0.0.15\tunnel-client-runtime.exe` | `A922D372D6B...` | Prefix matches registered runtime hash; full value was truncated. |
| `...FortisG3ApiTest\runtime-empty-transport-...\tunnel-client-runtime.exe` | `A922D372D6B...` | Same displayed prefix as the installed v0.0.15 runtime; full value was truncated. |
| `...FortisG3ApiTest\runtime-v0.0.15-...\tunnel-client-runtime.exe` | `A922D372D6B...` | Same displayed prefix as the installed v0.0.15 runtime; full value was truncated. |

**Hash verification status:** visually consistent prefixes only. The pasted `Format-Table` output truncated SHA256 strings, so exact full-hash equality is not yet proven. Request `Format-List Path,Exists,Type,SHA256` (or CSV) for conclusive comparison.

### Classification and cleanup boundary

- The two `C:\Tools\tunnel-client\...` files are present and their exclusions are relevant to the current Windows transport dependency. Preserve these exclusions pending any separate security review.
- `C:\Tools\desktop-commander-runtime\node.exe` and `C:\Tools\desktop-commander\` are legacy Windows G2/DC artifacts per current owner confirmation that G2 is unused. They are not required by the current Docker Fortis Repo Direct path. The directory exclusion is broader than a single-file exclusion. They are **cleanup candidates**, not automatically safe to delete: verify no other Windows application depends on them before changing anything.
- Both `FortisG3ApiTest` fixture runtime files exist and have the same displayed SHA prefix as v0.0.15. They remain test-fixture artifacts, not production tunnel dependencies. Verify whether the corresponding test directories/processes are still needed before removing the files or exclusions.
- No exclusions, files, services, profiles, shortcuts, Docker containers, or Git state were changed during this read-only inventory.

### Next verification

1. Re-run the file inventory with `Format-List Path,Exists,Type,SHA256` to capture full SHA256 values and compare exact strings against this register.
2. Before any cleanup, inspect whether the legacy G2 Windows directories and temporary G3 fixture directories are referenced by any active Windows service, scheduled task, process, launcher, or test workflow.
3. Do not remove the two current Tunnel Client exclusions. Do not modify Defender until the dependency check and owner approval are complete.
## Fortis Repo1/Repo2 dependency placement audit — 2026-11-02

This section answers the actual completeness question: which files belong in the Docker/Linux runtime, which source files belong in the Tunnel Git repo, and which Windows files must stay on the host.

### Verified in Docker / Tunnel workspace

- The paths `/workspace/repo/Repos/tunnel` and `/workspace/repos/tunnel` resolve to the same directory/inode and Git HEAD `6bc81c9279cfa46ac89454b2f061ff0cb748ad44`.
- `runtime/windows-repo/` contains the Windows Git-clone source mirror, `Invoke-FortisRepo.ps1`, `Preview-WindowsRepoInventory.ps1`, manifests, tests, README and inventory. The complete byte-exact current worker chain is under `current/`; the separate `repo1/` + `repo2/` four-file direct-launcher candidate is superseded and not used by Start.
- The four manifest PS1 hashes match the corresponding tracked `script-control-center/launchers` files byte-for-byte:
  - Repo1 control: `62A93BFA5F4C957C5A89267AC3416CE09BB28FAB71EBD87DB976F20E21092D58`.
  - Repo1 quiet launcher: `406881F20495B28A5EB97CE5F852801A21D02A9CC3220D35E7DB6BDD0FEDEAD9`.
  - Repo2 quiet launcher: `027F421B5B43F3EE0A3051AD734B9FA1E2FE3120FFDB259804A9DAF1D3B1E707`.
  - Repo2 Direct Guard: `08AB2A7B3051E6899A47AF8CD09FC2FFE6E560CD7638B8160D1B2C3A40402241`.
- The running Linux environment has Node v22.23.3 at `/usr/local/bin/node` (SHA256 `FDE6A4BF8D0562F7751D1A2D6CB9B417C4CFE107BBBC0AA3E9A24E125E348F48`) and Desktop Commander 0.2.52 at `/opt/dc/node_modules/@wonderwhy-er/desktop-commander`; its `dist/index.js` SHA256 is `A4145198DC75CD34E7C7452C2054B4CC0D29E199AE1459961A17E4DA25A13500`.
- The current DC config is present and reports exactly `/workspace/repos`, `/workspace/files`, `/workspace/repo`, shell `/bin/bash`, telemetry disabled. No key/profile content was read.
- The tracked `runtime/repo-mode/Dockerfile` describes Node 22 + Desktop Commander 0.2.52; the running versions match. It has no npm lockfile, so a fresh rebuild may resolve different transitive dependencies even though the current container runtime is installed and pinned separately.
- A read-only search across Docker mounted roots `/workspace/repo`, `/workspace/repos`, and `/workspace/files` found no `tunnel-client.exe`, `tunnel-client-runtime.exe`, or Windows `node.exe`; no tracked `.exe/.dll/.msi` exists in Tunnel or Control Center source.

### Windows-host dependencies — intentionally not Docker executables

- Repo1 calls `C:\Tools\tunnel-client\runtime\v0.0.15\tunnel-client-runtime.exe` to start profile `repo-mode`; its launcher pins SHA256 `A922D372D6BE0649156FBC1C8A040597F1F4BB5B4356890151D7875602593B1A`.
- Repo2 calls the same Windows Runtime v0.0.15 to start `repo-mode-plus2`; it also calls `C:\Tools\tunnel-client\tunnel-client.exe doctor`. The full Client is a Windows-side doctor prerequisite, not a Linux-container binary. Its historical local SHA is `1946DE55A038313A9B9B2458D05FE1719FA9CF1F20A94DD5F38FC26A98BFDD42`; it is documented as Authenticode `NotSigned` and currently has no startup SHA pin.
- The user's Windows inventory confirms both active EXEs exist. Their console table truncated SHA values, so the visible prefixes match the registered historical hashes but full equality remains UNVERIFIED until printed without table formatting.
- Windows `docker.exe`, PowerShell/WMI, local Repo1/Repo2 profiles, runtime keys, ACLs and logs are host-side requirements/state. They are not missing Docker source files and must not be copied into Git or Linux.
- The two `FortisG3ApiTest` EXEs are fixture copies of the same runtime version (the displayed SHA prefix matches v0.0.15); they are not production Repo1/Repo2 dependencies. G2 Windows Node/Desktop Commander are retired and not required.
### Source ownership / what is not yet complete

- The active Control Center worker chain is now mirrored under `runtime/windows-repo/current/` with its original relative layout: Repo1/Repo2 workers, Repo1 control + quiet launcher, and Repo2 `Start-Fortis.ps1` + `Common.ps1` + Guard + quiet launcher. The eight files are copied byte-for-byte from tracked `script-control-center` source and pinned in `current/source-manifest.json`.
- `Invoke-FortisRepo.ps1` validates the pinned eight-file manifest. Preview calls the existing read-only Repo1 launcher / Repo2 Guard + Status. Start dispatches to the unchanged `current/Repo1-Worker.ps1` or `current/Repo2-Worker.ps1`; it no longer bypasses Repo2 `Start-Fortis.ps1` / `Common.ps1`.
- The earlier four-file direct-launcher tree under `repo1/` and `repo2/` is retained only as a superseded staging candidate. It is not the active worker chain and is not used by the current Start dispatcher.
- The existing Control Center GUI still launches its own current Git-clone worker paths. It has **not yet been changed to delegate to Tunnel**; therefore the Windows single-source migration is NOT complete and this mirror is not yet the active Windows launch source.
- The current mirror is exact against tracked Control Center source, but differs from the archived `windows-installed-sources/20261101-085708-2d7ce467` snapshot. That snapshot is historical, not live Windows state. No current installed Windows launcher hashes were supplied, so do not claim installed-byte equality.
- `runtime/windows-repo/` is still untracked in the Tunnel working tree. The files exist in Docker, but they are not yet in a Tunnel Git commit and will not transfer to the Windows clone through `git pull` until reviewed and committed/pushed.
- `current/source-manifest.json` is pinned by the dispatcher; the offline tests verify all eight source hashes, worker dependencies, and the existing four-file candidate. Windows PowerShell parser/Preview and live reconnect still require separate owner acceptance.
- Preserve Repo1 `control.ps1` byte-for-byte, including its dormant historical `Start` action referencing `run-tunnel.ps1`; the worker continues to invoke the quiet launcher directly, exactly as the current Control Center worker does.

### Result and safe boundary

**Docker/Linux execution dependencies and the four new Repo source files are present.** The Windows Tunnel Client/Runtime are intentionally absent from Docker because they execute on Windows; their presence there is not a missing Linux component. The remaining work is source-of-truth migration, release-manifest hardening, and exact full-hash verification of the two Windows EXEs—not copying Windows binaries into the container.

The later owner readback supersedes the earlier provisional notes above: `ExclusionProcess` was empty; the listed Node path is an `ExclusionPath`; all six Windows paths in the owner's final inventory returned `Exists=True`; the two G3 fixture files also exist. The table's SHA values were truncated, so only prefixes were visible. The owner's `ExclusionExtension` list was not included.

No Windows files, profiles, keys, ACLs, Defender settings, Docker image/container, active tunnel, or Git history were changed in this audit. Only Tunnel documentation was updated in the Docker working tree.
