# E39 — автоматический поиск Repo монитором, 16 октября 2026

**SOURCE FIX + REPO TESTS + WINDOWS AUTOMATIC DISCOVERY PASS(scope).**
[JSON](G3_REPO_MONITOR_DISCOVERY_2026-10-16.json) · [План](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md) · [E38](G3_REPO_RUNTIME_CUTOVER_2026-10-16.md).

## Причина и минимальное исправление

Старый collector ограничивал запуск PowerShell, CIM process query и TCP query общим timeout3s.
Фактический baseline без override: TimeoutExpired после3.047s, UNKNOWN.
Тот же неизменённый запрос при диагностическом deadline15s вернул правильный Repo listener
за6.516s. Это подтверждает конкретную причину прежнего UNKNOWN, а не отказ туннеля.

Исправлен observatory/repo_monitor.py:

- deadline увеличен до15s, чтобы штатный Windows provider успевал завершиться;
- CIM выборка ограничена tunnel-client.exe и tunnel-client-runtime.exe;
- UNKNOWN различает timeout, невозможность запустить PowerShell, ошибку команды и некорректный output;
- причины фиксированы: stderr, partial output и raw command line не публикуются.

Loopback restriction, Repo identity в metrics и отсутствие управляющих запросов сохранены.
Нет нового постоянного порта, cache, environment override, сервиса или supervisor.
Не требуются новый tunnel, restart, права, mount или библиотека.
Deadline15s — ограничение ожидания, не гарантия времени ответа.
Nominal sampler wait5s сохраняется; реальный интервал включает collection time.
Не обещать точные5s между всеми samples.

## Что проверено

| Уровень | Доказательство |
|---|---|
| Repo | Syntax compile и11 unittest/API/regression tests PASS, errors0/failures0 |
| Windows | Owner Python312 исполнил pinned исправленный source; automatic discovery5.594s, returncode0 |
| Результат native collector | UP, verified=true, live=true, ready=true, MCP initialized |
| Адрес | Автоматически найден127.0.0.1:50385; OBS_REPO_URL отсутствует |
| Установка панели | Не выполнялась; installed dashboard/GUI не приняты |

Сводные JSON baseline/native сохранены без private owner data.
Native sample Unix1792110755.2403235; uptime1596.58s.
Repo tests используют synthetic данные и temporary P1_DATA_DIR; исходные данные панели не читались.
Новые cases покрывают slow provider, failure classification и отсутствие private exception output.
Первый запуск тестов имел два TypeError в mock helper: CompletedProcess ошибочно передан
как side_effect. Исправлено на return_value; production collector из-за этого не менялся.
Только final11/11 считается успешной проверкой.

## Где находится реально проверенный код

Исправлен существующий файл в Windows Repos через разрешённый Repo mount.
Windows проверка загрузила именно этот файл после SHA256 guard:

| Файл | SHA256 / bytes |
|---|---|
| observatory/repo_monitor.py | 2F0D337774F487B6D8575A5BA15969737EA986625760EA6BDEEBBF0EF632D4C8 /4220 |
| observatory/test_repo_monitor.py | D5837E718408A487D493E563086F1D96D35ACE3A906343ADAC95DA074767CCB6 /5553 |

До исправления collector SHA9B15F9FD…; read-back diff восстановлен и сверен с полным BEFORE SHA.
Чужие существующие tracked/untracked изменения сохранены. Commit/push не выполнялись.

## Известная старая панель и предел вывода

Адресная metadata-проверка в00:31:25 UTC:
C:\Users\alexa\Documents\prot\observability-ui-prototype-1\server.py существует,
repo_monitor.py в этой папке отсутствует.
Обычные python/pythonw processes, чья command line соответствует известным P1/Repo-observatory
server.py путям, не найдены. Другие installation paths, службы и способы запуска не перечислялись.
Нельзя из этого утверждать отсутствие вообще любого монитора.

Старая панель не заменялась и не запускалась. Исправление standalone Repo collector не является
автоматической установкой dual-tunnel dashboard. Если нужна постоянно работающая панель,
её запуск/обновление — отдельный конкретный scope с existing runbook; не делать это автоматически.

## Итог для плана

E38 auto-discovery gap закрыт для проверенного source collector на Windows без ручного адреса.
Не повторять runtime switch, MCP/GUI/clipboard/ACL/lifecycle tests ради этого gap.
Старые E38 UNKNOWN observations сохраняются как baseline и не переписываются.
Никакие туннели и контейнеры не перезапускались; ACL, сеть, profiles, credentials и logging config
не менялись. G3 BLOCKED; G4–G6 не приняты.
Далее — оставшиеся применимые G2 owner-boundary/private-assets вопросы по плану.
Полная установка панели и постоянное хранение журналов не являются автоматически новыми gates.
