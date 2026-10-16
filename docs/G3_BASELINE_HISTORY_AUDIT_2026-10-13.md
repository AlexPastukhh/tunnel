# G3 — базовая рабочая область и аудит истории, 2026-10-13

> Продолжение: [E40](G3_SELECTED_OWNER_ASSETS_2026-10-16.md) проверил direct-file access для семи выбранных owner assets и двух backup parents:130 normal/C$ DENY5,15 own controls/cleanup PASS. E05 root evidence ниже сохранено. Общий current scope/status — в плане; старые GUI/lifecycle blockers этого среза не являются новыми командами или потерей позднейших PASS.

**FILE GUARD / WORKSPACE APPLIED. Общий G3 OPEN; G4 production не принят.**
[JSON evidence](G3_BASELINE_HISTORY_AUDIT_2026-10-13.json) · [policy source](../runtime/host-g2/baseline-policy.json) · [предложение доступа](G4_ACCESS_POLICY_PROPOSAL_2026-10-13.md).

## Что изменено и проверено

Созданы scratch, browser-profiles и results внутри C:\Users\FortisHostG1\AppData\Local\FortisHostG2\Workspace.
Live G2 allowedDirectories сначала сужен с [] до Workspace, затем по проверке совместимости расширен до Workspace + C:\Tools\tunnel-client, C:\Tools\desktop-commander-runtime, C:\Tools\desktop-commander. Readback совпал. Три runtime дерева эффективно RO за счёт ранее применённого Windows ACL, не списка allowedDirectories; повторные actual G2 root handle checks read/traverse ALLOW, write/delete/WRITE_DAC/WRITE_OWNER DENY 5. Публичная LICENSE прочитана native file tool. Workspace RW. Это file-tool guardrail: arbitrary shell всё ещё ограничен реальными Windows правами, не этим списком. blockedCommands/defaultShell/line limits/telemetry сохранены, restart не выполнялся.
Actual native write/readback в собственной probe-папке PASS. Файловый вызов вне Workspace к прежнему synthetic RW marker получил реальный Path not allowed; существующий marker не менялся. Проверка на simulation/package.json была отклонена automatic approval review до выполнения из-за приватного закрытого проекта; замена synthetic тестом завершила проверку без чтения проекта.
Реальный Windows Edge 155.0.4283.45 запущен headless под G2, с отдельным временным профилем внутри Workspace и стандартным browser sandbox. Synthetic localStorage/DOM проверка PASS; основной профиль владельца не использовался. Своя страница, browser profile и probe directory удалены; собственный Edge PID больше не найден.
На 2026-10-13T13:18:17.1671844Z HOST 5580, Repo 23904 и G2 28148 сохранили прежние CreationDate, healthz/readyz 200/200. Owner launchers, ACL личных каталогов, Docker, services/tasks/shares и Sites не менялись.

## Текущие файловые границы

Под actual SID 1009, non-admin: read/write handles к owner home, Repos, simulation, Workfiles, AppData, Documents, Desktop, Downloads, .ssh, .aws и tunnel-client key directory получили Win32 5. Отсутствующие Pictures/.azure/.kube/.git-credentials помечены как отсутствие, а не DENY.
Workspace/G2 LocalAppData доступен RW. Installed Edge executable читается, write access отклоняется. Это адресные access checks без чтения содержимого; они не являются полным рекурсивным аудитом child ACL и всех личных активов.
Новых project grants нет. Согласованный базовый принцип: default closed, расширение для конкретного Windows случая после exact path/actions/dependencies preview. Не открывать весь AppData/Repos ради одной зависимости.
baseline-policy.json — документированный snapshot/дизайн в Git, не обязательный enforcement engine. Конфиг G2 этого SID изменяем самим SID; file guard не считать защитой от malicious client. Универсальный ACL Apply/Rollback менеджер из предложения ещё не реализован.

## Доступная история обычного Туннеля

Источник — owner Desktop Commander JSONL, прочитан локально напрямую, без импорта logger-модуля и его pruning side effects. 1 847 сохранённых вызовов; earliest 2026-10-11T08:56:55.269Z, latest snapshot 2026-10-13T12:41:29.899Z (11 октября 15:56 — 13 октября 19:41 Asia/Bangkok). Общий log owner Windows, не надёжная привязка к отдельному чату.
866 file/project operations, 771 start_process, 193 read_process_output; остальные config/search/support. Прямые file arguments включали 446 ссылок на simulation и 326 на другие Repos, 42 на tunnel source/docs.
В command arguments найдены маркеры npm test/build/lint, Git, Vite, Windows process/port diagnostics, headless/Edge/CDP и tunnel/ACL инфраструктуры. Это не количество успешных тестов и не проверка результатов всех заданий.
Исторические Edge/headless аргументы 11 октября и Edge/CDP/localStorage 13 октября содержали --user-data-dir и temporary markers, без явной ссылки на личный Edge/Chrome User Data. Ещё один generic headless marker не доказывает запуск Edge или изоляцию профиля. Сам audit command исключён из historical headless списка.
PowerShell AST различает реальные command nodes и строки документации: встречались Set-Acl (3), Register-ScheduledTask (1), Stop-Process (1), Start-ScheduledTask (2), Stop-ScheduledTask (3). AST/markers не доказывают выполнение/успех; embedded scripts требуют отдельной интерпретации. Явных Get-Clipboard/Set-Clipboard command nodes и screen-capture API markers не найдено в сохранённом срезе.
Logger ограничивает memory до 1 000 entries, outputs до 4 KiB и file до 5 MiB с pruning. Полнота до earliest и вне этого logger не доказана. Raw arguments, outputs и личные payload в отчёт не экспортировались.

## Матрица совместимости и решения

| Историческая задача | Что станет недоступно в G2 по умолчанию | Базовое решение |
|---|---|---|
| Код, документация, Git, npm test/build/lint в Repos | Прямой доступ G2 к owner project folders | Основная разработка остаётся Repo. Windows-specific case получает один выбранный root, без расширения на соседние проекты. |
| Зависимости Windows пользователя alexa | Private AppData/npm caches и owner credentials | Своё проверенное окружение G2/Workspace либо защищённые общие tools; owner AppData не открывать. |
| Windows Edge headless/CDP | Личный профиль и авторизованные сессии владельца | Сохранить installed Edge, свой temporary profile, собственный loopback CDP и synthetic проверки. |
| Vite/Windows localhost | Использование уже запущенного owner сервера и управление его процессом | По case запускать собственный сервер G2; Windows и Docker localhost различаются. |
| Windows paths/processes/ports | Изменение/завершение посторонних процессов | Оставить нужную read-only диагностику, управление своими процессами с PID/CreationDate guard. |
| Runtime/профили/ACL/tasks/services | Административное изменение общей инфраструктуры | Отдельный owner workflow, не обычный доступ G2 для разработки. |
| Общий clipboard/owner screen/main GUI | Требуется реальный OS запрет, которого сейчас нет | Не добавлять capability по умолчанию; выбранный фрагмент передаёт пользователь. Приёмка OS изоляции — следующий G3 gate. |

## Новый существенный G3 blocker: общая оконная станция

Owner SID 1001 и G2 SID 1009 используют Session 1 / WinSta0; owner station SID S-1-5-32-544, group SYSTEM. AccessCheck actual G2 token: WINSTA_ACCESSCLIPBOARD ALLOW, WINSTA_READSCREEN ALLOW, WRITE_DAC ALLOW.
Это подтверждённые разрешения объекта, не демонстрация чтения буфера/съёмки экрана или изменения DACL. Clipboard/screen данные не читались, SetUserObjectSecurity не вызывался.
Первый запрос SD содержал только DACL и дал ERROR 1338; он INVALID, не DENY. После запроса Owner+Group+DACL (7) получен валидный ALLOW.
Файловые DENY не закрывают эту поверхность. Простая декларация «clipboard по разрешению» или отдельный user/browser profile не являются OS enforcement. Даже отдельный desktop в одной window station не создаёт отдельный буфер.
Дальнейшую изоляцию выбирать и проверять в synthetic/private window-station/session: защита owner station/desktop, отсутствие права G2 менять эти ACL, отсутствие retained owner handles, сохранение CLI и headless Edge. Live объект общей сессии сейчас не меняли. Не предоставлять новые личные/GUI полномочия до закрытия этого gate.

## Следующая точка

Сохранить текущие owner чаты. До дальнейшего расширения G2: закрыть WinSta0/owner GUI capability и owner local APIs, определить реальное разделение широких chat routes, проверить service/SMB остаток. Затем case-based project scopes и G4 acceptance с backup/rollback.
Секреты в уже доступных Repo mounts остаются доступными через Repo независимо от G2 deny; .gitignore не закрывает read access. G5 личные активы/backups остаются отдельной работой.
GitHub SECURITY.md сверён через выбранный GitHub plugin, blob 8646b7e2951a426706ae3a17359afdaab6868cd0: [официальная policy](https://github.com/wonderwhy-er/DesktopCommanderMCP/blob/main/SECURITY.md). Built-in controls — guardrails, OS isolation — необходимая граница containment.

## Расширение доступа для конкретной задачи

Выбрать один Windows project root и необходимые действия (RO либо RW), определить свои temp/output/dependency пути. До выдачи прав показать exact-path preview и backup/rollback; после применения проверить actual G2 token, sibling DENY и сохранность owner процессов. Внести root в G2 file guard только после OS проверки. baseline-policy.json сохраняет согласованные scopes, но сам не применяет ACL; универсальный Apply/Rollback менеджер ещё не создан.
Для Windows npm/Git использовать свой user/cache/temp: scripts могут требовать Windows native dependencies и записи вне project root, их проверять адресно. Не расширять весь owner AppData/Repos. CDP — только собственный тестовый браузер/профиль; owner sessions не входят в baseline.
