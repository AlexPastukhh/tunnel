# Текущее состояние и следующие действия

Обновление документации: 26.10.2026, WF-052. Новых Windows/Linux runtime-проверок этим шагом нет. Фактические границы, даты наблюдений и риски — в [security-реестре](TUNNEL_SECURITY_ISOLATION.md); эта страница владеет рабочими задачами.

## Цель и ближайший шаг

Сохранить два работающих Direct Repo и подготовить контролируемое обновление Tunnel через независимый Project Checker. Решение владельца: **без ручного переноса Tunnel, запуска/удаления legacy Bridge, изменения ACL и остановки общего контейнера сейчас**.

Следующая безопасная единица: подготовить адресный owner-only read-only план проверки установленной цепочки, второго key/profile по метаданным, effective ACL/предков/aliases и host API/network. Уточнить готовность Checker и поддержанный review всей Tunnel-поставки до регистрации/обновления. Новые Windows-действия и реальный cutover выполняются только в согласованном scope и с независимым восстановлением.

## Задачи Repo/Tunnel

| ID | Состояние | Следующий gate / источник |
| --- | --- | --- |
| RP-01 | Исходное исследование завершено в ограниченном scope | [Аудит](reviews/repo-protection-20261025.md); оставшиеся риски ведутся в security |
| RP-02 | Функциональная миграция Direct проверена; cold reboot двух профилей открыт | V-01/V-15 и P-10; независимый Direct recovery, порядок/гонки холодного старта |
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

Решения и выполненные действия — [JOURNAL](JOURNAL.md), включая WF-050/051 и текущую правку WF-052. Детальное исследование передачи — [отчёт WF-050](reviews/security-handoff-verification-20261026.md).

[Прежний полный STATE](STATE_HISTORY_20261026.md) сохранён как история; его старые NEXT не исполнять. Новые хронологические блоки сюда не дописывать: текущую задачу обновлять на месте по [протоколу](README.md).
