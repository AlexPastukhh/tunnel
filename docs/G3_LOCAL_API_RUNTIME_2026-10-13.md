# G3: localhost API — проверенный runtime и план переключения

> **HISTORICAL SNAPSHOT — 2026-10-13.** Этот runtime review и все предположения о Windows mounts/owner HOST относятся к старой конфигурации. Не применять их к текущему Fortis Repo; mountinfo от 2026-11-03 описывает общий ext4 `fortis-repo-workspace` volume. Текущая карта: `/workspace/repos/fortis-container/docs/`.

Срез 2026-10-13 16:06 Asia/Bangkok (2026-10-13T09:06:04.4413853Z). **Изолированные тесты PASS; production-переключение PENDING; общий G3 OPEN.**
Подробные наблюдения: [JSON evidence](G3_LOCAL_API_RUNTIME_2026-10-13.json). Предыдущий этап: [проверка после ACL](G3_POST_ACL_VERIFICATION_2026-10-13.md).

## Что сделано

Официальный OpenAI tunnel-client-runtime v0.0.15 скачан, сверён с SHA256 GitHub release asset и scan manifest и установлен рядом с full client:
`C:\Tools\tunnel-client\runtime\v0.0.15\tunnel-client-runtime.exe`.

Полный клиент сохранён для doctor/init и отката. Действующие HOST, Repo и G2 не переключались; три live-лаунчера имеют исходные hashes. Owner profiles, ключи, ACL, services, shares, mounts и Sites не менялись. Git commit/push не выполнялись.

Новый каталог расположен внутри C:\\Tools\\tunnel-client, где наследуется deny SID 1009. У C:\\Tools deny действует только на саму папку: устанавливать новый runtime в соседний каталог было бы недостаточно.

## Артефакт и граница

| Проверка | Значение |
|---|---|
| Tag / source commit | v0.0.15 / a390c168ff1b2d14e73a95991c186c6aba3ff5a0 |
| ZIP SHA256 | AA5DDB14DDDD602FA59F3E6F4401AA8A79A218E341466226B7434127DFF65DBC |
| EXE SHA256 | A922D372D6BE0649156FBC1C8A040597F1F4BB5B4356890151D7875602593B1A |
| Scan manifest SHA256 | 9C711A47A09325939E8C486A8C3805C74AACE7B58E3699EB51B1756AFA18ACEF |
| Flavor | runtime |

Источник runtime graph исключает adminui, Codex, plugins и local proxy. Диагностические health/metrics сохраняются. Дополнительный Harpoon HTTP transport — отдельная возможность runtime; её явно отключают все подготовленные команды run аргументом `--harpoon.additional-transport=`. Пустой аргумент имеет приоритет над YAML/env и даёт пустой список дополнительных transports; in-memory Harpoon и обычная доставка MCP по туннелю сохраняются.

Проверены hashes, состав архива, manifest и реальные capability-тесты. Подпись/attestation и отдельный vulnerability scan не проверялись. Это не свидетельство полного аудита зависимостей.

Официальные источники: [release](https://github.com/openai/tunnel-client/releases/tag/v0.0.15), [runtime graph](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/runtimeapp/app.go), [transport parser](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/runtimeconfig/config.go), [ZIP](https://persistent.oaistatic.com/tunnel-client/v0.0.15/tunnel-client-runtime-v0.0.15-windows-amd64.zip).

## Что реально проверено

Два отдельных Windows экземпляра runtime работали под owner SID 1001 с synthetic YAML, выдуманным ключом, отдельным loopback control plane и stdio MCP echo. Код выполнялся из owner-private test-каталога; G2 получил DENY read/write handles на первый fixture. Реальные профили/ключи не использовались и наружу не отправлялись.

| Проверка | Результат |
|---|---|
| initialize, notifications/initialized, tools/list, tools/call | PASS в обоих тестах; echo FORTIS_G3_SYNTHETIC_OK |
| GET healthz / readyz / health / metrics | 200 |
| 20 запросов к UI/admin/Codex/Harpoon, включая PUT/POST | 404; проверено локально в обоих тестах |
| Реальный G2 SID 1009 → первый runtime | 24/24 ожидаемых HTTP-ответа |
| Второй runtime с inherited HARPOON_ADDITIONAL_TRANSPORTS=http-streamable и пустым flag | MCP PASS, local Harpoon 404 |
| G2 → второй runtime: диагностика, GET/POST Harpoon, PUT log-level | 6/6 ожидаемых ответов |
| Установленная папка и пять файлов: read handles | 6/6 ALLOW |
| Write/append/delete/writeDac/writeOwner handles | 30/30 Win32 5 DENY |
| Запуск установленного EXE --version из G2 | PASS, flavor runtime |
| Пять PowerShell scripts | Parser PASS; helper Preview: три live-файла BEFORE |
| G2 launcher запущен из owner account | Блокируется SID guard до profile/key prompt |
| Cleanup | Оба теста остановлены; test processes и четыре listener-порта отсутствуют |

Проверки scope: stdio MCP и local endpoints. Полная совместимость действующих трёх профилей, production control plane, OAuth/HTTP targets и rollout/rollback ещё не подтверждены. Runtime не должен автоматически заменяться full client при ошибке.

## Подготовленные файлы

Bundle: `C:\Users\alexa\Repos\tunnel\runtime\host-g2\runtime-api-migration`.

| Кандидат | Live-файл после применения |
|---|---|
| host-launcher.ps1 | `C:\Users\alexa\Documents\prot\Start-Desktop-Commander-Secure-Tunnel.ps1` |
| repo-run-tunnel.ps1 | `C:\Users\alexa\chatgpt-repo-mode\run-tunnel.ps1` |
| repo-control.ps1 | `C:\Users\alexa\chatgpt-repo-mode\control.ps1` |

- host-launcher.ps1: pinned runtime EXE, поиск обоих имён процессов, health URL вместо admin UI.
- repo-run-tunnel.ps1: doctor остаётся на full client, только run переходит на runtime.
- repo-control.ps1: оба имени процесса; сохранён выбор по точному Repo tunnel ID в metrics; stop сверяет PID и CreationDate; OpenPanel открывает read-only health.
- start-g2-runtime.ps1: только SID 1009 non-admin, существующий G2 profile, отдельный ключ вводится локально через SecureString и очищается после run. В owner account запуск отвергается.
- switch-launchers.ps1: default Preview; Apply меняет только три перечисленных лаунчера с backup; Rollback восстанавливает их из recorded backup. Hash drift блокирует запись. Никаких автоматических restart/elevation.
- migration-plan.json: exact before/after hashes и scope.
- synthetic-runtime-fixture.js: проверенный тестовый код; для повторения скопировать с проверенным EXE в новый owner-private каталог с artifact/tunnel-client-runtime.exe. Только synthetic YAML, ключ и localhost; TTL 8 минут.

Helper SHA256: `0D68581ADD6F0126D1E8A0F6DF993C92D52096F7E13028CA9A79D3F602BC2612`. Plan SHA256: `9EB03A985E71FDC32944DCDD8D327008C989C3091E0A0BB46B90EA4A8A0773D8`.

## Порядок применения после отдельного согласия на переключение

1. Под owner alexa проверить helper hash и Preview. После согласованного перехода выполнить Apply и сохранить выведенный BackupPath. Administrator не требуется. Apply/production rollback ещё не выполнялись.
2. Переключать по одному: Repo → G2 → HOST. Для Repo остановить только tunnel через StopAccess, сохранить контейнер, запустить обычный Repo launcher. Для G2 пользователь закрывает существующую FortisHostG1-консоль и запускает новый G2 launcher под тем же SID, вводя отдельный test key локально. Если script недоступен G2 из owner repo, владелец может скопировать только этот проверенный launcher в ранее разрешённый Public RW каталог и сверить его hash; owner-executed код туда не помещать.
3. Общий HOST переключать последним, после подтверждения Repo/G2. Пользователь закрывает прежнюю HOST launcher-консоль и запускает свой обычный HOST launcher. На время рестарта этого маршрута соединение с owner HOST прервётся; ACL/services/containers не перезапускаются.
4. После каждого перехода подтвердить EXE hash/name, owner SID и новый PID/CreationDate, healthz/readyz/metrics 200, проверенные admin routes 404 и GET/POST /harpoon/mcp 404. Проверить native MCP чтение и synthetic команду; для G2 повторить RW/RO/DENY и отсутствие UI metadata. Только после этого идти к следующему маршруту. Observatory проверить отдельно: его process discovery может требовать нового имени EXE, хотя health/metrics сохранились.

```powershell
$switch = 'C:\Users\alexa\Repos\tunnel\runtime\host-g2\runtime-api-migration\switch-launchers.ps1'
$expected = '0D68581ADD6F0126D1E8A0F6DF993C92D52096F7E13028CA9A79D3F602BC2612'
if ((Get-FileHash -LiteralPath $switch -Algorithm SHA256).Hash -ne $expected) {
    throw 'Migration script changed'
}
& $switch -Mode Preview
# После согласованного перехода:
# & $switch -Mode Apply
```

## Откат

Backup трёх лаунчеров создаётся под owner LOCALAPPDATA\\FortisG3ApiMigration\\<nonce>\\launchers-before.json до первой записи. Скрипт выводит точный путь. Rollback сверяет scope, before/after hashes, backup bytes и отсутствие постороннего drift; backup сохраняется.

```powershell
# Под owner alexa, с точным recorded backup:
# & $switch -Mode Rollback -BackupPath '<recorded BackupPath>'
```

Сам rollback ничего не перезапускает. Для возврата поведения остановить только переключённый маршрут и затем запустить исходный full-client launcher. G2: закрыть новый G2 процесс и восстановить прежнюю команду запуска full client под SID 1009 с локальным вводом test key. Не запускать одновременно два poller одного tunnel ID. При неизвестном/частично записанном hash скрипт останавливается; разбирать и восстанавливать только выбранный launcher из backup.

## Реальная граница чата

В этой сессии доступны owner HOST и native Repo с writable Windows mounts. Выбор @G2 и отключение UI не удаляют эти полномочия. Runtime закрывает localhost admin поверхность конкретного процесса; он не изолирует весь чат и не ограничивает альтернативный owner plugin.

Для проверки route isolation нужна отдельная сессия, где owner HOST/Repo и альтернативные owner file/shell plugins не предоставлены модели, а tools inventory содержит только согласованный G2 scope. Глобальное отключение старых plugins не выполнялось: оно затронуло бы другие чаты. До подтверждения отсутствия альтернативных полномочий whole-chat isolation остаётся OPEN.

Общий G3 также сохраняет ранее открытые пункты service user-defined controls и SMB/network boundary. Их этим переходом не закрывали; см. [post-ACL evidence](G3_POST_ACL_VERIFICATION_2026-10-13.md).

## Последний observer

2026-10-13T09:06:04.4413853Z: HOST 5580, Repo 23904, G2 8452 сохранили прежние CreationDate; все шесть healthz/readyz ответов 200. Synthetic listeners/processes отсутствуют. RW/RO/DENY marker sizes и LastWriteUTC прежние. Это датированный срез, не live dashboard.

## Scope update — 2026-10-13 18:06 Asia/Bangkok

Пользователь выбрал сейчас только G2, сохраняя работающие owner HOST/Repo. Порядок широкого rollout выше — прежнее предложение, не разрешение применить три owner launcher changes. [Актуальный handoff](G3_G2_ONLY_SWITCH_2026-10-13.md). G2 standalone duplicate guard исправлен: SID вместо argv order; hash 416DE2… superseded на A0680EB311B1BE2C0F7C3B1F9A0362DAC9F69C59A01C0AC293C3F08626ECF8F4. Historical JSON относится к состоянию 16:06; использовать новые records для текущего candidate. Actual G2 start ещё PENDING local key; G3/G4 security acceptance не получена.
