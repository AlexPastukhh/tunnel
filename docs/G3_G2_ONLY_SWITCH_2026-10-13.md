**Обновление 2026-10-13 18:32 Asia/Bangkok:** пользователь запустил новый G2; post-start acceptance PASS в scope. [Текущее evidence](G3_G2_RUNTIME_ACCEPTANCE_2026-10-13.md). Ниже сохранена историческая подготовленная точка 18:06; WAITING/PENDING в ней больше не являются текущим статусом. Общий G3 OPEN, G4 не принят.

# G3 — переключение только G2, подготовленная точка 2026-10-13 18:06 Asia/Bangkok

**STAGED / WAITING LOCAL START. Новый G2 runtime ещё не запущен.** [JSON evidence](G3_G2_ONLY_SWITCH_2026-10-13.json).

## Решение пользователя

Переключать только тестовый G2; существующие owner HOST и Fortis Repo сохраняются работающими. Общий helper switch-launchers.ps1 не применялся и для этого шага не нужен. G2 можно использовать как основу итогового limited HOST; это не принятие G4. До итогового режима остаются G3 routes/bypass, реальные production RO/RW папки и отдельная приёмка.

Repo Docker подтверждён live: user 1000:1000, rootfs read-only, cap drop ALL, no-new-privileges, published ports отсутствуют. Repos и Workfiles — RW bind mounts; внутренний repo volume RW. Windows-процесс tunnel Repo работает как owner SID 1001. Изоляция контейнера не закрывает admin API этого Windows transport и не ограничивает файлы внутри RW mounts. Repo и его launchers/config не менялись.

## Подготовка и исправление

Source: `C:\Users\alexa\Repos\tunnel\runtime\host-g2\runtime-api-migration\start-g2-runtime.ps1`.
Доступная G2 копия: `C:\Users\Public\Documents\FortisHostG1Probe\RW\start-g2-runtime.ps1`.
Текущий SHA256: `A0680EB311B1BE2C0F7C3B1F9A0362DAC9F69C59A01C0AC293C3F08626ECF8F4`.
Runtime: C:\\Tools\\tunnel-client\\runtime\\v0.0.15\\tunnel-client-runtime.exe, SHA256 A922D372D6BE0649156FBC1C8A040597F1F4BB5B4356890151D7875602593B1A.

Исходная G2 duplicate guard с hash 416DE2EB01708B81EF4C645F46D4FDB80D2C58FC0C96EFC28FDD2DD7802F9110 оказалась недостаточной: она ожидала --profile сразу после run, а реальная команда содержит перед ним --profile-dir. Preflight с заглушкой Read-Host остановился до настоящего prompt; ключ не запрашивался, новый tunnel не запускался.
Исправление проверяет Windows owner SID каждого running full/runtime tunnel; SID 1009 выделен G2. Неизвестный owner вызывает отказ. Рабочие owner tunnels SID 1001 не мешают; любой существующий tunnel SID 1009 блокирует дублирование независимо от argv. Сохранён точный backup исходника: `C:\Users\alexa\Repos\tunnel\runtime\host-g2\runtime-api-migration\start-g2-runtime.before-sid-guard-20261013.ps1.bak`.

Parser PASS. Настоящий G2 preflight исполнил verified bytes под SID 1009: existing-process guard PASS, credential gate не достигнут, restart отсутствует. SHA256 источника и staged copy совпали. Hash 416DE2… из прежнего snapshot относится к версии до исправления; старое evidence не переписывалось.

## Действие пользователя локально

1. В существующей консоли **FortisHostG1, из которой запускался G2**, остановить только старый G2 через Ctrl+C и дождаться PowerShell prompt. Не закрывать owner HOST/Repo. При неожиданном состоянии не запускать второй poller того же profile.
2. В той же non-admin консоли выполнить команду ниже. Она читает и проверяет одни и те же bytes перед исполнением; ExecutionPolicy и системные настройки не изменяются. Wrong SID/admin, wrong EXE hash, missing G2 profile или живой G2 приводят к отказу до key prompt.
3. Ввести **отдельный G2 runtime key локально** в masked SecureString prompt. Не передавать его в чат. Оставить окно работающим; после запуска сообщить факт запуска или redacted ошибку.

```powershell
$g2Launcher = 'C:\Users\Public\Documents\FortisHostG1Probe\RW\start-g2-runtime.ps1'
$g2Bytes = [IO.File]::ReadAllBytes($g2Launcher)
$g2SHA = [Security.Cryptography.SHA256]::Create()
try { $g2Hash = ([BitConverter]::ToString($g2SHA.ComputeHash($g2Bytes))).Replace('-', '') } finally { $g2SHA.Dispose() }
if ($g2Hash -ne 'A0680EB311B1BE2C0F7C3B1F9A0362DAC9F69C59A01C0AC293C3F08626ECF8F4') { throw 'G2 launcher changed' }
& ([scriptblock]::Create([Text.Encoding]::UTF8.GetString($g2Bytes)))
```

Новый launcher использует прежний G2 profile/state/tunnel ID, env-reference для отдельного key, retained headless stdio gate и --harpoon.additional-transport=. Сам ключ только вводит пользователь; MCP Node не имеет CONTROL_PLANE_API_KEY. В restricted MCP process подтверждено отсутствие этого key env, поэтому запуск нельзя завершить из MCP без локального ввода.
Автоматического fallback на full client нет. Если новый запуск не проходит — фиксировать redacted failure и восстановить прежний test-only запуск full client под SID 1009 по согласованной процедуре; owner HOST/Repo не трогать.

## Проверка после запуска — ещё PENDING

Проверить новый runtime PID/CreationDate/EXE hash/SID 1009, wrapper/Node и child token, native MCP handshake и RW/RO/DENY через file tools и PowerShell/Python, отсутствие UI metadata и key в Node environment. Новый health port выявлять по новому PID; не считать прежний порт 65069 неизменным. Healthz/readyz/metrics должны дать 200, admin routes и GET/POST Harpoon — 404. Проверить сохранность marker metadata и прежних HOST/Repo PID/CreationDate/health.

## Что остаётся открытым

G2-only переключение закрывает собственный admin API G2 после подтверждения тестов. Owner HOST/Repo пока остаются full client с ранее обнаруженной local API поверхностью. Whole-chat route isolation, выбранные service user-defined handlers и SMB/network boundary остаются OPEN. Не заявлять общий G3 PASS либо production limited HOST только после этой смены binary.

## Последний observer

2026-10-13T11:06:18.5547221Z: HOST 5580 / Repo 23904 / G2 8452 сохраняют прежние CreationDate; healthz/readyz 200/200 на всех трёх. G2 всё ещё old full client. Staged helper готов. Только G2 launcher source и его Public RW копия изменены; live owner launchers, credentials, profiles, ACL, Docker, services и Sites не менялись.
