# Черновик C-05: временная проверка прямого MCP через существующий Fortis Repo

**НЕ ГОТОВО К ЗАПУСКУ.** Сохранено для продолжения другим чатом. Helper содержит блокирующий throw; ручные команды ниже не оформлены. Сначала закончить review и Windows AST/preflight-проверку, затем подготовить точные команды теста и независимого возврата.

25 октября 2026 года, Asia/Bangkok. Пользователь попросил проверить прямое подключение и объяснить смысл. **Начата подготовка ограниченной ручной проверки; реальное переключение ещё не выполнялось.** Это не принятие постоянного удаления Bridge, сетевых правил или всей C-04.

## Что значит «прямое»

Меняется только программа MCP, запускаемая существующим Windows runtime через docker exec:

| Режим | MCP entry в том же контейнере |
| --- | --- |
| Сейчас / Restore | /usr/local/bin/node /workspace/repo/.fortis/mcp-bridge.mjs |
| TestDirect | /usr/local/bin/node /opt/dc/node_modules/@wonderwhy-er/desktop-commander/dist/index.js |

В обоих режимах используются прежние repo-mode/profile/auth references, узкий pinned Windows runtime и тот же контейнер, UID, данные/mounts/ресурсы/сеть. Не создаются новая регистрация, профиль, ключ, Windows-учётка или контейнер; постоянные launcher/probe/profile не редактируются.

Bridge не строит Windows GUI/Observatory. Он меняет MCP presentation и **скрывает** UI-метаданные DC. В установленном server.js get_config связан с config-editor resource, read_file — с file-preview. Поэтому «делает что-то с UI» не доказывает обязательность Bridge: реальный вопрос — работает ли клиент с исходными metadata/resources без адаптера.

[Предыдущий isolated comparison](repo-network-and-mcp-bridge-20261025.md) подтвердил по26 одинаковых tools/input schemas, resources2/0 и UI tool metadata5/0. Но это ещё не Windows tunnel/ChatGPT UI acceptance.

## Граница и последствия

- Временно переподключается **общее** Fortis Repo, используемое другими чатами. Делать тест, когда нет важных активных Repo-команд: MCP terminal sessions могут оборваться.
- Docker container не останавливается. Нет команды StopContainer/docker stop или изменения Windows ACL/network/mounts.
- TestDirect/Restore меняют только текущий runtime invocation через CLI override; источник и saved profile остаются прежними. Обычные runtime/DC counters/cache могут обновляться при старте.
- Не запускается старый probe.mjs: он исполняет Bridge, пишет markers и настройки. Вместо него helper проверяет необходимые baseline constraints read-only до остановки связи.
- Runtime console stdout/stderr подавлены, чтобы не пересылать profile/doctor/payload. Ключ читает штатный runtime по прежнему reference; helper содержимое ключа не читает.
- Junction отложены; тест не обходит их и не меняет размещение проектов. Не принимаются PR-A-07/09/13 авансом.

## Состав C-05

Проверочный subset PR-A-13, WR-T01–06 и EA-T01–05 ниже. User authorization относится к временной проверке; постоянное применение — отдельная единица.

| WR | Критерий |
| --- | --- |
| WR-T01 | Тот же repo-mode/tunnel, owner alexa, pinned runtime/control, immutable container ID и прежние restrictions |
| WR-T02 | До Stop проверены protected direct module и исходный Bridge hashes, current allowed roots/shell/telemetry; неожиданный drift прекращает действие |
| WR-T03 | Останавливается только подтверждённый Repo ID/PID/creation/owner; дубликаты/неизвестная identity не останавливаются |
| WR-T04 | Через реальный клиент проверены serving process chain без Bridge, metadata, чтение известного файла и readonly terminal operation |
| WR-T05 | UI наблюдается пользователем: лишние cards/errors, file preview/config editor; настройки через UI не применяются. Cache/необновлённые metadata ограничивают вывод |
| WR-T06 | Есть независимый ручной Restore без работающего MCP; после него подтверждается прежняя цепочка. Нет постоянных config/permission changes |

| EA | Механизм и проверка |
| --- | --- |
| EA-T01 | Перепутан PID/другой туннель → остановка чужого процесса. Используется pinned controller discovery по Repo ID и fresh PID/creation/owner/exe checks |
| EA-T02 | Старый startup probe выполнен перед direct test → уже исполнен RW Bridge. Helper его не вызывает; preflight — отдельный read-only Node metadata code |
| EA-T03 | Cached metadata/старый процесс принят за direct → ложный PASS. Проверять get_config serving PID и реальную /proc parent/module chain |
| EA-T04 | UI action/feedback/onboarding меняет scope → лишние действия. Только выбранные readonly tools; не нажимать Apply/Send/feedback и не открывать предложенные внешние страницы |
| EA-T05 | После сбоя MCP нет канала отката. Mode Restore и запасные штатные Windows команды доступны локально без Repo tool access |

## Подготовленный helper и проверки кода

[Switch-RepoMcpTest.draft.ps1](../tools/Switch-RepoMcpTest.draft.ps1) имеет Preview (default), TestDirect и Restore. Он сверяет control/runtime hashes, Docker ID/user/readonly root/cap-drop/NNP/ресурсы/network/mounts, actual Linux flags, direct+Bridge hashes и выбранные DC config fields. Не читает raw profiles/key/env, не делает registration/doctor и не пишет конфигурацию.

Для Stop импортируется только hash-совпавший существующий controller; Menu/Start/StopContainer не вызываются. Перед запуском проверено отсутствие lingering repo-mode process. Для обоих backend runtime работает в foreground; окно нужно оставить открытым. Mode Restore также использует временный override на прежний Bridge entry; штатный launcher остаётся нетронутым.

Inline read-only JavaScript preflight реально исполнен в нынешнем Repo и вернул baseline PASS; marker/tools calls не выполнялись. Проверены code/scope и source fingerprints. **Windows PowerShell AST и фактическое выполнение этого нового switch helper ещё не проверены.** Парсинг файла и весь preflight идут до Stop. Если они завершаются ошибкой — текущая связь не останавливается.

### Запуск теста

Обычный, не elevated Windows PowerShell под FORTIS_M\alexa, когда важные Repo-команды завершены:

__TEST_COMMAND__

После сообщений Starting TestDirect / Leave this PowerShell window open вернуться в чат и написать **«direct запущен»**. Если сразу получен exit code или ошибка — прислать только эту ошибку/код, не raw runtime/doctor/profile logs.

### Проверка через ChatGPT

Агент делает readonly get_config, сверяет PID/parent/module с direct path, читает небольшой фрагмент уже выданного README и запускает readonly UID/platform metadata. Пользователь сообщает о новых карточках/ошибках/preview. Никакие UI settings/apply/send не нужны.

PASS ограничен реально проверенными tool/transport/UI outcomes. Если клиентские metadata не обновились, отсутствие карточки не доказывает UI-совместимость. Если инструменты работают, но UI ломается, Bridge может быть полезен как адаптер; если direct работает достаточно, можно отдельно подготовить постоянный вариант без него.

### Возврат к прежнему Bridge

В **другом обычном PowerShell** запустить:

__RESTORE_COMMAND__

Это остановит только тестовый Repo runtime и запустит прежний Bridge entry. Новое окно тоже оставить открытым. Старый TestDirect runtime завершится; код остановки в его окне ожидаем. После этого сообщить **«Bridge восстановлен»** — агент проверит цепочку через реальный MCP.

Запасной локальный путь, если helper не удаётся применить, — существующие control.ps1 -Action StopAccess и run-tunnel.ps1 из C:\Users\alexa\chatgpt-repo-mode. Штатный launcher выполняет свои обычные startup probes/DC/Git настройки и диагностические записи; не пересылать его полный doctor output. Не обходить новую ошибку identity/pin и не останавливать процессы по одному имени.

## Текущий статус

C-05 остаётся черновиком, preflight JavaScript PASS(scope), реальная временная смена/actual-client outcomes/Restore не выполнены. Исходники/profiles/runtime/mounts/network пока не менялись. Сетевой collector из предыдущего этапа остаётся отдельным следующим входом; junction отложены.
