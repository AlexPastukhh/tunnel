# Project Checker — действующий хендофф личной Windows V1

Дата контекста: 25.10.2026. Основной Repo: /workspace/repos/tunnel.
Исходники: runtime/userscript-updater/. Это вход в текущую работу, не старый
HANDOFF.md и не свидетельство установки/Windows PASS.

## Чтение и владельцы фактов

1. AGENTS.md, README.md, docs/README.md, действующий
   [протокол документации](../agent-workflow/README.md).
2. [PLAN](PLAN.md) целиком — текущие этапы, gate и ближайший шаг.
3. [Полная reading copy A4/v4](CANDIDATE_PREWORK_V4_READING_COPY.md) —
   сохранённое направление, historical candidate, не формальный baseline commit.
4. [IMPLEMENTATION_LOG](IMPLEMENTATION_LOG.md) — только здесь актуальные
   выполненные прогоны, ошибки/исправления, платформы, receipts и bundle path.
5. [Runtime README](../../runtime/userscript-updater/README.md) — запуск/build;
   [PROMOTION_CORE](PROMOTION_CORE.md) — контракты;
   [WINDOWS_TRUST_BOUNDARY](WINDOWS_TRUST_BOUNDARY.md) — независимая установка;
   [Windows package procedure](../../runtime/userscript-updater/release/WINDOWS_ACCEPTANCE.md) —
   конкретные ручные действия владельца.

Не копировать счётчики тестов/версии/next в несколько сводок. Старые HANDOFF и
PLAN_LEGACY_USERSCRIPTS_20261025 — история узкого кейса. Notifier/Helper —
необязательные поздние потребители, не приказ менять их сейчас.

## Полномочия

Разрешены разработка, зависимости, сборка/тесты внутри Fortis Repo/Docker и
осмысленные локальные Git-коммиты только своих файлов после проверки индекса.
Не спрашивать это повторно и не возвращаться в pre-work из старого A4.

Windows install/ACL/agent-route/GUI/Loader/реальные external copies выполняет
владелец отдельно вручную. Агент готовит reviewed package/probes, исправляет
native FAIL после обратной связи. Не делать push, host/runtime deployment,
изменение mounts/общего Tunnel, профилей/GM secrets и чужих workstreams.

F-U-01–05 уже приняты: полная личная V1; check-only; file/files/folder/mixed с
явными mappings; общие пакеты редактируются на месте, копия для варианта;
раздельные Проверить/Обновить; перед consent полный actual-target
create/modify/delete/unchanged/preserve, diff или binary hashes/sizes.
Исчезнувший прежний managed source предлагает только просмотренное удаление;
первый импорт чужих existing files требует явного scope. Auto-update нет.

## Контекст продолжения

Development Check/registry/shared packs реализованы. В текущем source candidate
есть confirmation/apply/result/history/recovery GUI, folder/empty/missing-source/
resource/data contracts, native handle I/O, installed closure/ACL/receipt verifier
и отдельный issuer. Development profile по-прежнему не даёт права записи;
QA writers ограничены новой temporary fixture и отсутствуют в app import path.

Текущий source/Docker/offline candidate уже зафиксирован и собран; точный
receipt — в журнале. Следовать PLAN: ближайший gate — ручная Windows-приёмка
владельца. Не повторять завершённую разработку без новых изменений/FAIL.
Не объявлять source implementation доказательством native совместимости,
изоляции write routes, power-loss durability или OWNER_ACCEPTED.

Перед каждой новой мутацией проверить live Git/status/index и фактический
результат предыдущего timeout. HEAD может включать параллельные коммиты:
не откатывать его к старому checker hash, не захватывать чужой staged work.
