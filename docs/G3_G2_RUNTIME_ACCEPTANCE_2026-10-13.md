# G3 — приёмка переключения только G2, 2026-10-13 18:32 Asia/Bangkok

**G2 runtime switch: PASS в проверенном scope. Общий G3: OPEN; G4 не принят.**
[Structured evidence](G3_G2_RUNTIME_ACCEPTANCE_2026-10-13.json) · [Историческая подготовка и команда](G3_G2_ONLY_SWITCH_2026-10-13.md).

## Что действительно переключено

Пользователь локально остановил прежний тестовый G2 и запустил проверенный standalone launcher с отдельным ключом. Новый процесс создан в 2026-10-13T11:19:05.6815740Z (18:19 Asia/Bangkok).
Цепочка: runtime PID 28148 → Python 19376 → Node 21812, все SID S-1-5-21-303538662-3368424508-2654684973-1009; FortisHostG1, non-admin. Старый G2 PID 8452 завершён.
Runtime: C:\Tools\tunnel-client\runtime\v0.0.15\tunnel-client-runtime.exe, SHA256 A922D372D6BE0649156FBC1C8A040597F1F4BB5B4356890151D7875602593B1A.
Source/Public launcher SHA256 A0680EB311B1BE2C0F7C3B1F9A0362DAC9F69C59A01C0AC293C3F08626ECF8F4. Existing profile/state сохранены; реальный native G2 MCP работает. Общий switch-launchers.ps1 не применялся.

## Функциональная проверка

- Live health port установлен по новому PID: 127.0.0.1:54045. GET healthz/readyz/metrics — 200.
- 17 выбранных UI/admin/Codex/Harpoon/MCP/SSE запросов — 404; включая PUT /api/log-level, POST /api/restart, GET/POST /harpoon и /mcp. Запросы направлялись только новому G2 после проверки PID/SID/CreationDate/listener. Изменяющих запросов старым owner endpoints не было.
- Actual G2 file tools: RW create/write/readback ALLOW; RO read ALLOW/write DENY; DENY read/write DENY (EPERM). PowerShell/.NET и Python отдельно подтвердили ту же матрицу, RW readback совпал; Python token SID 1009, elevated=false.
- 14 выбранных shared/new runtime объектов: 76 mutation handle opens получили Win32 5, read/execute ALLOW. Данные runtime не записывались; handles закрыты. Полный старый скан 22 758 объектов не повторялся.
- Probe nonce: probe-g2-runtime-1791890620188-8xi6o4. Собственные MCP/PowerShell/Python файлы удалены. Owner observer независимо обнаружил 0 leftovers; original marker size/mtime совпали с исходными значениями.

## UI и key boundary

Live wrapper SHA256 146E60B028276F871353A113571306002942461F0446E519A63B28DCC068418D; shared Node SHA256 2FFE3ACC0458FDDE999F50D11809BBE7C9B7EF204DCF17094E325D26ACE101D8.
В реальном MCP child/терминальном окружении DESKTOP_COMMANDER_DISABLE_MCP_UI=1, имён CONTROL_PLANE_API_KEY / OPENAI_API_KEY / OPENAI_ADMIN_KEY присутствует 0; значения ключей не читались и не выводились. Gate self-test PASS.
Отдельный diagnostic child той же установленной версии с child_environment() живого gate: initialize + tools/list + resources/list PASS, 26 tools, 0 UI metadata, 0 resources. Он завершён. Это отдельный discovery, а не прямой tools/list проксированного native маршрута; ответы actual G2 command/file calls также без UI metadata. Основной Windows GUI не автоматизировался; визуальное отсутствие карточки не проверялось скриншотом.

Несколько ранних native RPC дали 409 initialization required после переключения; безопасные чтения повторены успешно, туннели не перезапускались и неопределённые мутации не повторялись. Первый Python -c получил SyntaxError из-за кавычек до выполнения кода; передача через base64 исправлена, полный повтор PASS.

## Сохранность общих маршрутов

На 2026-10-13T11:32:20.4790620Z: HOST PID 5580 / created 02:59:43.4833490Z и Repo PID 23904 / created 03:00:34.2137140Z сохранены, healthz/readyz 200/200.
Три live owner launcher/control SHA256 совпали с baseline. G2 28148 и его creation time также сохранены после тестов, healthz/readyz 200/200.
Owner HOST/Repo launchers, credentials, profiles, ACL, Docker, services, tasks, shares и Sites на этом переключении не менялись. Публикация/commit/push не выполнялись.

## Что не закрыто этой приёмкой

Собственный local admin API G2 отсутствует в проверенных маршрутах. Owner HOST/Repo остаются full client с ранее подтверждённой localhost API поверхностью; в этой сессии остаются оба широких MCP route. Service user-defined handlers и SMB/network boundary всё ещё OPEN.
G2 можно использовать как основу будущего итогового limited HOST, но не объявлять общий G3 PASS или G4 production acceptance. Следующая работа — G3 routes/bypass с сохранением текущих owner чатов; реальные production RO/RW папки и отдельная приёмка относятся к G4.
Не повторять локальный launcher, пока G2 работает, и не применять общий switch helper ради завершения этой G2-only приёмки.
