# G3 — Repo-only guarded apply/rollback, 16 октября 2026

> Продолжение: [E37](G3_REPO_PROFILE_PREFLIGHT_2026-10-16.md) завершил bounded actual named-profile shape preflight; conflicts не выявлены, native compatibility и согласованный Repo-only cutover остаются. Live Apply/Rollback/restart не выполнялись. Актуальный Next — в плане.

**Разработано и проверено на fixtures. Live Apply/Rollback не выполнялись.**
[E36 JSON](G3_REPO_GUARDED_MIGRATION_2026-10-16.json) ·
[Локальное восстановление](G3_REPO_RUNTIME_ONLY_RECOVERY_2026-10-16.md).
G3 BLOCKED; G4–G6 не приняты. Это подготовка файлового перехода, не принятие narrow Repo runtime.

## Реализованный scope

Production wrapper изменяет только два файла под `C:\Users\alexa\chatgpt-repo-mode`:
`run-tunnel.ps1` и `control.ps1`. Default — Preview.
Wrapper требует Windows по системному API и owner SID1001, сверяет core/candidate pins;
для Preview/Apply также проверяет установленный runtime и синтаксис кандидатов.
Runtime, HOST/G2, контейнер, profiles/keys, ACL/network и автозапуск он не меняет.
Никакой режим helper не запускает и не останавливает процессы.

| Файл в runtime/host-g2/runtime-api-migration | SHA256 | Байты |
|---|---|---:|
| [RepoRouteMigration.Core.ps1](../runtime/host-g2/runtime-api-migration/RepoRouteMigration.Core.ps1) | 46CEE432DE4460F744517FD2F0A49073DF41B28BB1BFE68F597877DA62856BF8 | 9260 |
| [Invoke-RepoRouteMigration.ps1](../runtime/host-g2/runtime-api-migration/Invoke-RepoRouteMigration.ps1) | AE249350C3C0A6E6F3169F213D73094431D4F1C38EB3F2565F94C6ECB142A2A4 | 3094 |
| [Test-RepoRouteMigration.ps1](../runtime/host-g2/runtime-api-migration/Test-RepoRouteMigration.ps1) | D202109B2F8DE6B5CBE67E34D0EE159E050C81E1F771E7D5EFE5E84A25DF9925 | 10518 |

## От чего защищают проверки

| Механизм | Проверенный результат / назначение |
|---|---|
| Exact two-file scope и before/after/candidate hashes | Отказ при другом числе целей, изменённом candidate, неизвестной live правке и подмене target в backup |
| Оба target handles удерживаются от preflight до read-back | На Windows конкурентный writer блокирует Apply до записи; при ошибке ранее взятый handle освобождается |
| Backup до первой target записи | Сохраняются exact BEFORE bytes двух файлов, фиксированные targets/hashes, Schema/Plan; CreateNew, flush/read-back и hash |
| Отдельный durable journal | PREPARED, verified file stages, COMPLETE либо STOPPED; помогает установить частичное состояние |
| Откат по exact BackupPath + recorded SHA256 | Проверяются manifest, scope и BEFORE bytes; восстанавливаются только известные AFTER файлы, посторонние edits не затираются |
| AFTER/BEFORE после прерывания | Повтор Apply отклоняется; rollback восстанавливает один изменённый файл и сохраняет второй BEFORE |
| Независимость rollback от candidate/runtime | Восстановление не требует доступного candidate файла или narrow runtime; требуется доверенный wrapper/core |
| Reparse path guard | Код отклоняет reparse components; отдельный новый Windows reparse negative fixture не выполнялся |

Backup root — `%LOCALAPPDATA%\FortisRepoApiMigration\<nonce>`, production backup ещё не создан.
Неизменяемость manifest здесь — правило helper и проверка pins/hash, не WORM или запрет owner менять файл.
128 KiB на выбранный script/record — предел engine; текущие файлы значительно меньше.
Общий all-three switch не используется.

## Проверено

- Repo: AST трёх sources; PowerShell7.4.6 — 28 assertions PASS, одна Windows-specific отметка SKIP.
- Windows: G2 SID1009/non-admin/Session2, PowerShell5.1.26100.9711 — **32/32 assertions PASS, без SKIP**.
  Применение/откат выполнялись только на собственных synthetic fixture files в guest Workspace.
- Проверены default Preview, exact Apply/rollback, candidate/backup/live drift, scope tamper,
  чужой edit, повтор, отказ конкурентному writer, освобождение handles и fault после первой target записи.
- Все final fixtures удалены после проверки marker, размера дерева и отсутствия reparse entries.
- Actual owner wrapper Preview, 2026-10-15T22:51:28.0973485Z: оба реальных файла BEFORE,
  candidate pins совпали, FilesChanged=0, BackupCreated=false, RuntimeRestarted=false.

Точное UTC финального Windows test не осталось в сокращённом console result; JSON содержит
подтверждённые сводные outputs, а не полный raw transcript. Это не новый тест на момент будущего Apply.
Windows source проверялся hash перед исполнением. Финальные pinned test/core copies остаются в guest Workspace.

## Исправления при проверке

Первый Linux contention case показал различие FileShare semantics: synthetic файлы стали AFTER/AFTER,
а отказ Windows writer не был доказан. Фактический эффект проверен, старый собственный fixture удалён.
Linux не используется как доказательство этой Windows-гарантии; финальный Windows case прошёл.

Первый Windows запуск runner из памяти остановился на script-variable scope до изменения targets:
BEFORE/BEFORE, backup отсутствует. Исправлена область assertions, fixture проверен и удалён.
Далее переменная OS оказалась очищена G2 gate, и Windows branch ошибочно пропустился.
В runner и wrapper выбор платформы заменён на Environment.OSVersion.Platform.
Только финальный прогон32/32 без SKIP считается Windows contention evidence. Engine bytes при этих
исправлениях runner не менялись.

## Ограничения и следующий шаг

Пара файлов не является одной атомарной транзакцией. Проверен сбой после завершённой первой записи,
а не отключение питания или mid-file failure. Неизвестный DRIFT helper не затирает даже при rollback:
нужны inspection и отдельное точное решение. Journal не отменяет это ограничение.
Hardlinks, все filesystem races и защита от owner/privileged attacker не проверялись.

Нужны effective-config/native compatibility preflight, последствия OpenPanel/monitor и отдельно
согласованный Repo-only cutover. Реальный runtime-only Repo ещё не принят; helper success не закрывает 4.10.
Пройденную fixture suite не повторять без изменения/нового gap. Прежний HOST не переделывается.
