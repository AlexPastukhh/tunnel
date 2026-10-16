# Repo runtime-only — локальное восстановление, 16 октября 2026

## Фактическая recovery identity после E38

Пользователь разрешил переход в 06:50:25; Apply и selected Repo restart выполнены.
[E38](G3_REPO_RUNTIME_CUTOVER_2026-10-16.md): оба файла AFTER, новый runtime PID24720.
BackupPath: C:\Users\alexa\AppData\Local\FortisRepoApiMigration\a6d1e489e8b74a6dbbcc17978070641b\backup.json
BackupSHA256: 7234D724730813F5E50F8A7215054B851B3323C4A4759DD65C5E383F1B14766C
Не выполнять Apply повторно. Live rollback не выполнялся; E36 fixtures переиспользуются.
Команды ниже — общий порядок, а не новая инструкция остановить исправно работающий Repo.
Старые слова «будущий/не выполнялся» описывают подготовку E36; фактическая доставка — E38.


**Repo-only live переход выполнен E38; инструкция восстановления остаётся локально доступной.**
[E36](G3_REPO_GUARDED_MIGRATION_2026-10-16.md) · [Текущий план](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md).
Эти файлы доступны на Windows и после остановки Repo tunnel; Docker mount не нужен для локального чтения.

## До согласованного переключения

[E37](G3_REPO_PROFILE_PREFLIGHT_2026-10-16.md) завершил bounded named-profile shape preflight в observer context; native Go validation/реальное подключение остаются. Не выдавать этот результат за полный effective config. Для будущего запуска использовать проверенный owner context либо адресно сверить отличия окружения. Согласовать два Repo файла и окно возможного прерывания общего Repo.
Подготовить PowerShell под alexa: elevation не требуется. Сохранить эту инструкцию и две исходные
helper files локально доступными. HOST/G2 и контейнер не останавливать.
Runtime-only меняет OpenPanel с /ui на /health; source monitor compatibility не равна native acceptance.

Проверка wrapper и загрузка pinned bytes (сама ничего не применяет):

```powershell
$ErrorActionPreference='Stop'
$p='C:\Users\alexa\Repos\tunnel\runtime\host-g2\runtime-api-migration\Invoke-RepoRouteMigration.ps1'
$b=[IO.File]::ReadAllBytes($p)
$sha=[Security.Cryptography.SHA256]::Create()
try { $h=([BitConverter]::ToString($sha.ComputeHash($b))).Replace('-','') }
finally { $sha.Dispose() }
if($h -cne 'AE249350C3C0A6E6F3169F213D73094431D4F1C38EB3F2565F94C6ECB142A2A4'){throw 'Wrapper source hash drift'}
$invoke=[scriptblock]::Create([Text.Encoding]::UTF8.GetString($b))
& $invoke
```

До первого Apply E36 default Preview показывал оба BEFORE. После E38 ожидаются оба AFTER; Preview не пишет файлы. BEFORE/AFTER сверять с фактической стадией, не повторять Apply ради старого ожидания.
Wrapper сам проверяет core SHA `46CEE432DE4460F744517FD2F0A49073DF41B28BB1BFE68F597877DA62856BF8`.
При drift не применять force и не переписывать hashes под текущие bytes.

## Будущий Apply и сохранение recovery identity

Только после отдельного решения о двух live файлах и Repo interruption.
Этап не выполнялся в E36; команда ниже приведена как закомментированный Candidate:

```powershell
# $receipt = (& $invoke -Mode Apply) | ConvertFrom-Json
# $receipt.FileResult | Format-List State,BackupPath,BackupSHA256,JournalPath
```

До StopAccess/перезапуска сохранить **BackupPath и BackupSHA256** из результата в доступной локальной
консоли/записи. Production backup появляется только при реальном Apply.
После файла STATE=APPLIED старый процесс может ещё работать: это не переключённый runtime и не исправленная live API граница.

Helper не перезапускает Repo. Запуск narrow runtime — отдельный согласованный шаг с native MCP,
monitor/control и effective read-surface acceptance. Нулевой exit code либо readyz200 не заменяет MCP вызов.

## Если после согласованного запуска Repo не восстановился

1. Установить фактический процесс/состояние. Остановить только выбранный Repo через его
   проверенный control StopAccess либо вручную Ctrl+C в той консоли, где был запущен
   `C:\Users\alexa\chatgpt-repo-mode\run-tunnel.ps1`.
   StopContainer и остановка процессов по общему имени не входят в recovery.
   Если ownership/identity не ясны — сначала metadata; HOST/G2 не останавливать.
2. В owner PowerShell заново проверить wrapper pin и загрузить `$invoke` командой выше.
   Выполнить rollback с **ранее записанными** значениями, не с придуманным или вновь доверенным hash:

```powershell
# После подтверждения recorded identity:
# & $invoke -Mode Rollback -BackupPath '<recorded backup.json>' -ExpectedBackupSHA256 '<recorded SHA256>'
```

3. Убедиться, что восстановлены BEFORE hashes ниже. Rollback не требует candidate/narrow runtime,
   но требует доверенного wrapper/core. Если оба файла уже BEFORE — ALREADY_BEFORE; backup сохраняется.
4. После подтверждения отсутствия второго poller запустить восстановленный обычный
   `C:\Users\alexa\chatgpt-repo-mode\run-tunnel.ps1` под alexa. Прежний profile и key file остаются на месте;
   credentials не копировать и повторно provision не делать.
5. Подтвердить actual Repo MCP/CLI и состояние monitor отдельно. Записать: что восстановлено,
   какой executable реально работает и какую безопасность он предоставляет.
   Откат к full client возвращает прежнюю exposed owner API, а не исправляет её.

| Файл | BEFORE SHA256 |
|---|---|
| run-tunnel.ps1 | 3877266C3C97BECC82045BE16D994981EB4F8973353B285236DF9CAAC158A5A3 |
| control.ps1 | E80E209B4758B194D2BCC7DCAFDFB83D296289E29A543F192E6726538641AE34 |

## Неопределённое или частичное состояние

AFTER/BEFORE — проверенный случай: Apply откажется, recorded rollback восстановит только AFTER.
Unknown DRIFT, изменённый backup, неверный scope или source pin — остановка без перезаписи.
Сначала прочитать фактические hashes/journal и сопоставить с backup. Не делать слепой повтор,
force-copy или массовое восстановление. Сбой внутри одной записи/потеря питания не тестировались.

Local backup не является полной защитой личных активов/backups7.6. Эта инструкция не даёт разрешения
на live применение, остановку общего туннеля, изменение ACL/mount/network или отдельную migration HOST.
