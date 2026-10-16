# Fortis G2 — evidence G2-E / G2-F, 2026-10-13

**Итог:** G2-E PASS по совокупности переданных файловых MCP-тестов и новых PowerShell/Python проверок. G2-F: карта маршрутов подтверждена; эта сессия НЕ изолирована. G2-G stop/rollback выполнен в scoped проверке, см. G2_G_EVIDENCE_2026-10-13.md; production acceptance отсутствует.

## Происхождение доказательств

PowerShell/.NET, Python, child token, cleanup, marker metadata и route inventory ниже получены непосредственно в этой ветке 2026-10-13 через реальные MCP. Ранее успешная матрица MCP file read/write передана пользователем в истории основной ветки; она не выдаётся за повторный тест этой ветки. Чтение RW marker через текущий G2 также подтверждено при проверке отключения UI.

Тестовый root: `C:\Users\Public\Documents\FortisHostG1Probe\`. Только synthetic markers и новые уникальные probe-файлы.

## G2-E: caller и матрица

PowerShell: `FORTIS_M\FortisHostG1`, SID `S-1-5-21-303538662-3368424508-2654684973-1009`, non-admin, UI_DISABLED=true.
Python: собственный Windows token имеет тот же SID, TokenElevation=false; дочерний `whoami /user` подтвердил тот же SID.

| Средство | RW read/write | RO read/write | DENY read/write | Итог |
|---|---|---|---|---|
| MCP file tools, переданная история | ALLOW / ALLOW | ALLOW / DENY | DENY / DENY | PASS, происхождение указано выше |
| MCP PowerShell/.NET | ALLOW / ALLOW | ALLOW / DENY | DENY / DENY | PASS |
| MCP Python direct file I/O | ALLOW / ALLOW | ALLOW / DENY | DENY / DENY | PASS |

PowerShell: отказ `System.UnauthorizedAccessException:80070005`.
Python: отказ `PermissionError`, errno=13.
Это прямой filesystem отказ в shell/Python; запрет не объясняется одним MCP allowedDirectories.
В обеих реализациях RW запись прочитана обратно и совпала с synthetic payload.
При неожиданном результате тест остановился бы до продолжения по другим каталогам; неожиданных ALLOW не было.

## Cleanup и отсутствие запрещённых изменений

Nonce: `20261013-1791869898156-ot5omq`.
Имена: `probe-g2e-ps-<nonce>.txt` и `probe-g2e-python-<nonce>.txt`.
Открытие только CreateNew / Python x: существующие файлы не перезаписывались.
Два RW файла удалены теми же restricted MCP child процессами после readback.
Независимый observer через старый HOST, `FORTIS_M\alexa`, проверял только metadata выбранных synthetic paths, а не выполнял за G2 запрещённые операции.
Все шесть probe-путей отсутствуют после теста, включая RO/DENY.
У исходных marker-файлов сохранились Length и LastWriteTimeUtc:
- RW: 23 байта; 2026-10-12T13:30:35.1744508Z.
- RO: 23 байта; 2026-10-12T13:30:35.3931000Z.
- DENY: 25 байт; 2026-10-12T13:30:35.4084159Z.
Проверка времени/размера — scoped metadata evidence, не глобальный hash-аудит всего Windows.

## G2-F: фактически доступные маршруты этой сессии

| Маршрут | Проверенная identity / область | Текущий результат |
|---|---|---|
| Restricted G2 | tunnel PID 27324, owner SID 1009; test profile fortis-host-g2-test | MCP работает; healthz/readyz HTTP 200, loopback 60267 |
| Native HOST | tunnel PID 5580, owner alexa / SID 1001; profile desktop-commander | MCP observer реально вызван; healthz/readyz HTTP 200, loopback 8080 |
| Native Repo | tunnel PID 23904 на Windows под alexa; MCP executor Linux uid/gid 1000:1000 | Реальный shell вызов прошёл; healthz/readyz HTTP 200, loopback 58122 |
| Repo Site | Fortis · Repo Mode | configured=false, accessEnabled=false, connected=false; только диагностика |

Docker inspect подтвердил RW bind mounts `/workspace/repos` ↔ Windows Repos и `/workspace/files` ↔ Windows Workfiles, плюс RW internal volume `/workspace/repo`. Реальный Repo shell подтвердил эти три каталога и R/W access.
Старые HOST/Repo PID совпадают с ранее зафиксированными; тесты их не перезапускали.

**Граница:** OS token boundary G2 и его synthetic ACL доказаны. Это не session route isolation: в этом чате реально вызван старый HOST под alexa, а также отдельный Repo с собственным scope.
Выбор G2 через @ не удалил эти инструменты из сессии. Другие альтернативы/system brokers относятся к G3; полный аудит всех коннекторов здесь не заявляется.

## Настройки приложений и ограничения проверки

Plugin Management нашёл G2 и Fortis Repo: оба Use my default; global Allow low-risk actions.
Доступные режимы permissions управляют подтверждениями, а не задают per-chat deny для конкретного маршрута.
Имя старого tool surface `Туннель` не разрешилось в каталоге permissions (not_installed), хотя прямой MCP вызов этого surface прошёл. Это неопределённость canonical app reference, а не доказательство отсутствия маршрута.
Никакие app permissions, установки, аудитории, credentials и регистрации не менялись.

## Открытый closeout / следующий gate

G2-G: свои текущие probe-файлы убраны. Backup восстановлен и проверен на отдельной копии; live wrapper не менялась. G2 остановлен, исходные три процесса и listener отсутствуют; HOST/Repo PID/CreationDate и HTTP 200 сохранены. См. [G2-G evidence](G2_G_EVIDENCE_2026-10-13.md). Исторические fixtures и reusable runtime сохранены.
UI change source и backup описаны в `../runtime/host-g2/README.md`; рабочее отключение UI сохраняется.
Следующее: снова запустить G2 для G3 и определить проверяемый режим отдельной restricted сессии с недоступным owner HOST. Любые более широкие отключения требуют точного app reference и решения владельца; не удалять плагины попутно.
G3 → G4 остаются отдельными gates; production ACL/mounts/profile migration не выполнялась.
