# Текущее состояние и следующие действия

Обновление приоритетов: 26.10.2026, WF-055–058. Текущий приоритет — сбой обоих Repo; source archive и owner-диагностика не являются восстановлением. Фактические границы, даты наблюдений и риски — в [security-реестре](TUNNEL_SECURITY_ISOLATION.md); эта страница владеет рабочими задачами.

## Цель и ближайший шаг

Восстановить работу двух Direct Repo, сохранив их границы и незавершённую работу. Затем продолжить подготовку контролируемого обновления Tunnel через независимый Project Checker. Решение владельца сохраняется: **без ручного переноса Tunnel, запуска/удаления legacy Bridge, изменения ACL и остановки общего контейнера сейчас**; остановка любого Tunnel также требует отдельного согласования.

Следующая единица RP-07: owner read-only SHA/AST metadata Repo2 получены (тот же pinned SHA, Action=Setup/Start/Status, точного Direct literal нет, binding/guard lines 181/209/212). Следующий owner read-only gate: структурный AST второго запуска показал одинаковую форму девяти элементов на строках 209/212 (последний — expandable string), но скрыл имена переменных и значения аргументов. Нужна адресная allowlist AST-проекция переменных/типов/CLI-маркеров без текстов строк, после неё — reviewed Repo2 quiet candidate, owner Preview/Run и live smoke. **Repo1 side-by-side canary прошёл live command/file/output smoke WF-058**, прежний срыв повторного echo не воспроизвёлся. Длительная эксплуатация, свежий notification-count exporter и второй профиль ещё не проверены.

Owner уже запустил Repo1 через run-tunnel-quiet-logs.ps1 -Mode Run, RunId7027db02148f4c02a47a3da045d3c2a0. Обычный control Start пока ведёт на старый run-tunnel.ps1; после обоих canary требуется отдельно согласованный постоянный default/rollback с точными pins. Пока не объявлять оба Repo восстановленными и не запускать старые wrappers как исправленные.

После восстановления вернуться к security-приоритету WF-054: данные/ключи → host/API действия → независимый enforcement. Проверки по метаданным и фактическим read routes; содержимое секретов не читать/не выводить. Downloads/development сохраняются по [REQUIREMENTS](REQUIREMENTS.md). Readiness Checker и review всей Tunnel-поставки остаются отдельным gate перед production update.

## Задачи Repo/Tunnel

| ID | Состояние | Следующий gate / источник |
| --- | --- | --- |
| RP-07 | **ACTIVE: Repo1 live quiet canary PASS(scope); Repo2 и постоянный default ожидают** | F-R-15/V-16; [WF-055 evidence и owner-план](reviews/repo-tunnel-outage-20261026.md), затем проверка обоих клиентов |
| RP-01 | Исходное исследование завершено в ограниченном scope | [Аудит](reviews/repo-protection-20261025.md); оставшиеся риски ведутся в security |
| RP-02 | Историческая миграция Direct проверена; текущая доступность — RP-07; cold reboot двух профилей открыт | V-01/V-15 и P-10; независимый Direct recovery, порядок/гонки холодного старта |
| RP-03 | Aliases/фактические Windows пути ещё не аттестованы | F-R-08; no-follow metadata и effective access перед изменениями |
| RP-04 | Host/LAN/API policy не завершена | F-R-06/P-09; узкая read-only инвентаризация, затем отдельно санкционированные controls |
| RP-05 | Ручной перенос и cleanup отложены | P-10/P-11: сначала Bridge-free recovery и приёмка, затем отдельное решение владельца |
| RP-06 | Trusted promotion/Windows boundary не приняты | F-R-12 и P-01–P-12; начать с регистрации без update после достаточной готовности |

Для F-R-13 допустимо спокойное read-only наблюдение дельт ресурсов, без stress/kill/restart. Для F-R-14 нужна проверка сохранённых Git bytes; причины обоих наблюдений остаются в реестре, здесь не дублируются.

## Владельцы связанных работ

- [Project Checker PLAN](../userscript-updater/PLAN.md), [implementation log](../userscript-updater/IMPLEMENTATION_LOG.md), [Windows boundary](../userscript-updater/WINDOWS_TRUST_BOUNDARY.md): реализация, конкретные тестовые прогоны и готовность Windows. Общая сводка не поддерживает вторую копию его milestone/числа тестов.
- [G2 plan](../G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md) и [E42 runbook](../G3_G2_INITIAL_SCOPE_AND_RUNBOOK_2026-10-16.md): отдельный Windows-контур; результаты G2 не закрывают Repo risks.
- [REQUIREMENTS](REQUIREMENTS.md): S-01–S-07 и I-01–I-15. Godot/игры, media/3D/audio, CI и local AI (N-02–N-08) проверяются по выбранному проекту; не prerequisites текущей защиты Tunnel. N-01 — исторический scoped файловый тест, см. JOURNAL WF-004/005.
- [Observatory V1](../../observatory/v1/README.md): его source/установка/API/evidence; это отдельная работа.

## История и сопровождение

Решения и выполненные действия — [JOURNAL](JOURNAL.md), включая WF-050–058. Детальное исследование передачи — [отчёт WF-050](reviews/security-handoff-verification-20261026.md).

[Прежний полный STATE](STATE_HISTORY_20261026.md) сохранён как история; его старые NEXT не исполнять. Новые хронологические блоки сюда не дописывать: текущую задачу обновлять на месте по [протоколу](README.md).
