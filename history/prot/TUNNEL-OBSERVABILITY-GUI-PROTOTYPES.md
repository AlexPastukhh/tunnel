# Прототипы GUI для observability

Статус: Prototype 0 реализован; Prototype 1 следующий
Дата: 2026-10-07

## Главный принцип

Observability GUI нужно разрабатывать так, чтобы рабочие чаты продолжали пользоваться текущим tunnel без изменений.

Поэтому до отдельного canary-этапа запрещено:
- менять stdio command текущего tunnel;
- вставлять proxy в рабочий путь;
- перезапускать tunnel-client ради разработки GUI;
- менять Desktop Commander wrapper;
- занимать порт 8080;
- писать в runtime key/profile текущего tunnel.

Разработка идёт out-of-band:
- отдельный процесс;
- отдельный localhost port;
- отдельный data directory;
- read-only чтение `/health` и `/metrics`;
- fixtures/replay для UI и parser tests.

## Prototype 0 — UI shell на fixtures

Цель: быстро выбрать интерфейс без зависимости от живого tunnel.

Источник данных:
- сохранённые JSON/Prometheus fixtures;
- synthetic events.

Показывать:
- Tunnel / MCP / Sessions cards;
- latency timeline;
- inflight table;
- error/interference feed;
- session liveness states.

Риск для рабочих чатов: нулевой.

## Prototype 1 — live shadow dashboard

Отдельный collector читает только:
- `http://127.0.0.1:8080/health`;
- `http://127.0.0.1:8080/metrics`.

Предлагаемый dashboard endpoint:
- `http://127.0.0.1:8091/`.

Collector не вызывает MCP tools и не подключается к stdio Desktop Commander.

Частота:
- health: 1–2 s;
- metrics: 2–5 s.

Нужно ограничить polling и не создавать лишнюю нагрузку.

GUI:
- live/ready/uptime;
- poll/response counters;
- error/status counters;
- latency p50/p95/p99;
- histogram/history;
- reconnect/409 markers.

Риск для рабочих чатов: очень низкий.
Критерий успеха: несколько часов работы без влияния на latency текущих чатов.

## Prototype 2 — history + diagnostics

Добавить локальное хранение:
- SQLite или append-only JSONL;
- только timestamps, metric values, status/error classes.

Добавить:
- график latency во времени;
- baseline vs anomaly;
- markers для tunnel restart;
- derived alerts: latency spike, poll gap, 409 burst.

Рабочий tunnel всё ещё не меняется.

## Prototype 3 — offline MCP proxy simulator

До подключения к живому tunnel proxy разрабатывается отдельно:
- stdin/stdout fixtures;
- recorded/replayed JSON-RPC sequences;
- fake MCP server;
- synthetic slow/error cases.

Проверяется:
- request/response correlation;
- inflight tracking;
- duration accounting;
- disconnect/restart handling;
- redaction policy.

Рабочие чаты не проходят через этот proxy.

## Prototype 4 — canary tunnel

Только после стабильности Prototype 3 создаётся отдельный тестовый контур:

```text
Test Chat
  -> отдельный custom MCP/plugin
  -> отдельный Secure MCP Tunnel profile/ID
  -> Observability Proxy
  -> Desktop Commander test target
```

Production/current tunnel остаётся прямым и продолжает обслуживать рабочие чаты.

На canary проверяются:
- реальные tool calls;
- local MCP duration;
- proxy overhead;
- restart/reconnect;
- Kaspersky/EPERM behavior;
- session registration/heartbeat.

Нельзя переключать существующие рабочие чаты на canary автоматически.

## Prototype 5 — heartbeat canary

В canary MCP surface добавить:
- `monitor_register`;
- `monitor_heartbeat`;
- `monitor_finish`.

Правило для тестового чата:
- обычный tool call обновляет last activity;
- если активная работа продолжается и tool calls нет 60–120 s, отправляется heartbeat;
- waiting-user/finished отмечаются явно, когда это возможно.

Сначала проверять только на отдельном test chat.

## Prototype 6 — controlled production rollout

Только после canary acceptance tests:
1. сравнить latency current tunnel vs canary;
2. убедиться, что proxy overhead приемлем;
3. убедиться, что AV не реагирует хуже на proxy;
4. сохранить rollback на прямой stdio path;
5. переключать production только в короткое согласованное окно.

Даже после rollout dashboard остаётся отдельным процессом и не должен быть обязательным для работы tunnel.
Если dashboard упал, tunnel должен продолжить работать.

## Разделение процессов и портов

Рекомендуемая схема для разработки:
- current tunnel admin/metrics: `127.0.0.1:8080`;
- observability GUI/API dev: `127.0.0.1:8091`;
- optional dev WebSocket: тот же 8091;
- canary tunnel health/metrics: отдельный порт, например `127.0.0.1:8081`;
- test proxy diagnostics: отдельный localhost port.

Порты должны быть configurable, не hardcoded.

## Независимость разработки

Можно отдельно разрабатывать GUI, parser, storage и alert rules, пока другие чаты активно работают через текущий tunnel.

Безопасные параллельные работы:
- UI/layout;
- Prometheus parser;
- health parser;
- local charts/history;
- SQLite schema;
- alert logic;
- fixtures/replay;
- proxy simulator.

Работы, требующие отдельного окна согласования:
- изменение current tunnel profile;
- restart current tunnel-client;
- изменение Desktop Commander wrapper;
- вставка proxy в production path;
- экспериментальные heartbeat tools в production plugin.

## Критерий «не мешает рабочим чатам»

Prototype 0–2 считаются безопасными для параллельной разработки, если:
- текущий tunnel profile не меняется;
- collector делает только localhost GET;
- polling bounded;
- CPU/RAM collector умеренные;
- нет влияния на p50/p95 tunnel latency;
- остановка collector никак не влияет на tunnel.

## Пользовательская спецификация прототипов

Начиная с этого раздела каждый прототип описывается не только через технический состав, но и через пользовательскую ценность.

### Формат сценария

Каждый сценарий должен отвечать на четыре вопроса:
1. **Мотивация** — зачем пользователь открыл/использует эту часть GUI и какую задачу хочет решить.
2. **Взаимодействие** — что пользователь делает: открывает экран, нажимает кнопку, выбирает период, раскрывает строку, запускает replay и т. п.
3. **Фичи как требования к программе** — каждая фича внутри сценария описывается через желаемое поведение программы.
4. **Результат для пользователя** — что пользователь должен понять, получить или сделать после взаимодействия.

Формат описания фичи:
- **Действие пользователя:** что именно делает пользователь.
- **Поведение программы:** что программа обязана сделать в ответ.
- **Связь с целью:** почему это поведение помогает выполнить сценарий.

Фича не считается описанной только названием вроде «список сессий» или «график latency». Нужно описать, что пользователь видит/делает и какое состояние программы после этого ожидается.

## Prototype 0 — UI shell на fixtures

### Задачи пользователя
- Быстро понять, полезен ли вообще такой observability dashboard.
- За несколько секунд увидеть общее состояние tunnel, MCP и рабочих sessions.
- Разобрать типовые проблемные состояния на безопасных синтетических данных.
- Понять, как от общей сводки перейти к конкретному запросу или событию.

### Сценарий P0-S1 — Быстрый обзор состояния

**Мотивация:** пользователь хочет открыть dashboard и сразу понять, всё ли выглядит нормально.

**Взаимодействие:** пользователь открывает dashboard и ничего дополнительно не настраивает.

**Фичи / желаемое поведение:**
- **Status cards.** Программа показывает Tunnel, MCP target, Active sessions и Inflight отдельными карточками. Каждая карточка содержит текущее состояние, короткое пояснение и время/возраст состояния.
- **Цвет состояния.** Программа использует одинаковую семантику green/amber/red/gray во всех разделах, чтобы пользователь не расшифровывал каждый компонент отдельно.
- **Обновление времени.** Возраст состояния и uptime должны быть понятны без ручного обновления страницы.

**Результат:** пользователь может быстро ответить «система жива / есть работа / есть потенциальная проблема».

### Сценарий P0-S2 — Разобрать типовую проблему

**Мотивация:** пользователь хочет увидеть, как dashboard будет помогать при проблеме, но рабочий tunnel пока нельзя подключать.

**Взаимодействие:** пользователь нажимает на `AV / EPERM`, `Latency spike` или `Tunnel down`.

**Фичи / желаемое поведение:**
- **Scenario selector.** Нажатие на сценарий мгновенно заменяет fixture state и все связанные данные согласованным набором событий.
- **Event timeline.** Программа показывает последовательность событий, а не только итоговый красный статус.
- **Risk indicator.** Для сценария с потенциальным вмешательством программа явно показывает уровень проблемы и не выдаёт предположение за подтверждённый факт.

**Результат:** пользователь понимает причинную цепочку и может оценить, хватает ли интерфейса для будущей диагностики.

### Сценарий P0-S3 — Найти активную работу

**Мотивация:** пользователь хочет понять, какой чат/сессия сейчас создаёт нагрузку и чем именно занят tunnel.

**Взаимодействие:** пользователь просматривает таблицу Sessions и список Inflight requests; при необходимости раскрывает интересующую строку.

**Фичи / желаемое поведение:**
- **Sessions table.** Программа показывает session id, capability boundary, state, last activity и количество requests.
- **Inflight list.** Программа показывает текущий tool, связанную session, elapsed time и прогресс/ожидаемое состояние.
- **Correlation.** При выборе session программа фильтрует или подсвечивает относящиеся к ней requests и events.

**Результат:** пользователь может перейти от «что сейчас происходит?» к конкретной session и конкретному запросу.

## Prototype 1 — live shadow dashboard

### Задачи пользователя
- Узнать, жив ли реальный tunnel прямо сейчас.
- Отличить проблему tunnel от проблемы MCP target или временного отсутствия работы.
- Видеть текущую latency и признаки reconnect/409.
- Проверять состояние, не вмешиваясь в рабочие чаты.

### Сценарий P1-S1 — Проверить tunnel перед началом работы

**Мотивация:** пользователь собирается запускать работу через tunnel и хочет заранее убедиться, что транспорт доступен.

**Взаимодействие:** пользователь открывает dashboard.

**Фичи / желаемое поведение:**
- **Live/ready state.** Программа регулярно читает `/health` и отдельно показывает live и ready, не сводя их к одному boolean.
- **Uptime.** Программа показывает uptime текущего tunnel instance и момент последнего успешного health response.
- **Staleness.** Если polling давно не получал ответ, программа показывает возраст последнего ответа и переводит состояние в stale, а не мгновенно в «tunnel down».

**Результат:** пользователь понимает, можно ли рассчитывать на tunnel в данный момент.

### Сценарий P1-S2 — Понять, где возникла деградация

**Мотивация:** пользователь замечает, что команды через tunnel стали медленнее, и хочет понять, это транспорт или локальная система.

**Взаимодействие:** пользователь смотрит latency metrics и раскрывает период/аномалию.

**Фичи / желаемое поведение:**
- **Latency stats.** Программа показывает p50/p95/p99 за текущий rolling window и явно указывает окно расчёта.
- **Latency history.** График показывает изменение latency во времени, а не только последнее значение.
- **Transport markers.** Reconnect, HTTP 409 и другие доступные transport events отображаются на той же временной шкале.

**Результат:** пользователь может сопоставить скачок latency с reconnect/409 или увидеть, что деградация появилась без transport event.

### Сценарий P1-S3 — Убедиться, что мониторинг не мешает чатам

**Мотивация:** пользователь хочет использовать dashboard параллельно с рабочими чатами и не хочет добавлять заметную нагрузку.

**Взаимодействие:** пользователь оставляет dashboard открытым и продолжает работу в чатах.

**Фичи / желаемое поведение:**
- **Bounded polling.** Collector использует фиксированный умеренный интервал и не создаёт лавину запросов при ошибках.
- **Collector health.** GUI показывает собственное состояние collector отдельно от tunnel state.
- **Independent failure.** Если GUI/collector остановился, tunnel продолжает работать, а после возврата GUI показывает gap в telemetry.

**Результат:** пользователь получает наблюдаемость без зависимости рабочего tunnel от dashboard.

## Prototype 2 — history + diagnostics

### Задачи пользователя
- Разобрать проблему, которая уже произошла и сейчас не воспроизводится.
- Сравнить нормальный baseline с аномальным периодом.
- Найти события, совпавшие по времени с деградацией.
- Получить компактное доказательное описание инцидента без чтения сырых логов целиком.

### Сценарий P2-S1 — Расследовать прошлый инцидент

**Мотивация:** пользователь получил сообщение «команды были медленными около 14:30», но сейчас всё нормально.

**Взаимодействие:** пользователь выбирает временной диапазон и приближает интересующий участок графика.

**Фичи / желаемое поведение:**
- **Time range.** Программа позволяет выбрать абсолютный период и запоминает выбранный диапазон при переходе между диагностическими панелями.
- **Zoom/selection.** Пользователь может выделить участок графика; остальные панели переходят на тот же временной диапазон.
- **Baseline comparison.** Программа показывает baseline рядом с выбранным периодом и явно объясняет, откуда взят baseline.

**Результат:** пользователь видит, насколько инцидент действительно отличался от нормальной работы.

### Сценарий P2-S2 — Найти вероятную причину

**Мотивация:** пользователь хочет не просто увидеть скачок latency, а найти события, которые могли его объяснить.

**Взаимодействие:** пользователь кликает на anomaly или event marker.

**Фичи / желаемое поведение:**
- **Correlated events.** Программа фильтрует timeline по выбранному времени и показывает связанные reconnect, 409, process failure и другие telemetry events.
- **Event details.** Раскрытие события показывает timestamp, category, request/session reference и безопасное описание причины.
- **Evidence vs inference.** Программа разделяет фактически наблюдаемое событие и диагностическую гипотезу.

**Результат:** пользователь получает проверяемую цепочку «аномалия → события рядом с ней → возможная причина».

### Сценарий P2-S3 — Получить диагностический итог

**Мотивация:** пользователь хочет быстро сообщить результат себе или другому человеку.

**Взаимодействие:** пользователь выбирает период и нажимает действие вроде `Copy diagnostic summary`.

**Фичи / желаемое поведение:**
- **Diagnostic summary.** Программа формирует краткую сводку выбранного периода: состояние, latency, ошибки, reconnects и связанные события.
- **Redaction.** В сводку не попадают prompts, полные arguments, содержимое файлов, runtime key и другие secrets.
- **Stable identifiers.** Request/session IDs сохраняются, чтобы можно было сопоставить сводку с локальными логами.

**Результат:** пользователь получает безопасный диагностический артефакт, пригодный для дальнейшего разбора.

## Prototype 3 — offline MCP proxy simulator

### Задачи пользователя
- Проверить будущий proxy до подключения к реальному tunnel.
- Воспроизводить сложные ошибки детерминированно.
- Убедиться, что request correlation и redaction работают правильно.

### Сценарий P3-S1 — Воспроизвести проблемный обмен

**Мотивация:** пользователь хочет проверить исправление proxy на конкретной последовательности JSON-RPC, не рискуя рабочими чатами.

**Взаимодействие:** пользователь выбирает fixture/replay и нажимает `Replay`.

**Фичи / желаемое поведение:**
- **Replay selector.** Программа показывает доступные recorded sequences с кратким описанием сценария.
- **Replay controls.** `Replay`, `Pause`, `Reset` управляют только симулятором и не запускают реальные MCP tools.
- **Trace viewer.** Каждый request/response получает correlation ID и отображается в правильном порядке.

**Результат:** пользователь может повторить один и тот же сценарий сколько угодно раз и сравнить поведение proxy.

### Сценарий P3-S2 — Проверить ошибочные условия

**Мотивация:** пользователь хочет убедиться, что proxy корректно переживает timeout, disconnect, slow response или malformed response.

**Взаимодействие:** пользователь выбирает error injection и запускает replay.

**Фичи / желаемое поведение:**
- **Fault injection.** Программа применяет выбранную ошибку только к simulator input.
- **State transitions.** GUI показывает, как request переходит `queued → inflight → failed/retried/completed`.
- **No host side effect.** Simulator не имеет возможности выполнить выбранную команду на HOST.

**Результат:** пользователь проверяет отказоустойчивость до реального canary.

## Prototype 4 — canary tunnel

### Задачи пользователя
- Проверить observability на реальном tool traffic без риска для рабочих чатов.
- Увидеть фактический путь request через canary proxy.
- Сравнить поведение прямого и proxy path.
- Найти проблемы restart/reconnect и локального process handling.

### Сценарий P4-S1 — Запустить безопасный тестовый прогон

**Мотивация:** пользователь хочет проверить новый observability path на реальной команде, но не хочет переводить рабочие чаты.

**Взаимодействие:** пользователь явно выбирает `CANARY` и запускает тестовый chat/run.

**Фичи / желаемое поведение:**
- **Environment selector.** Программа явно показывает, что session принадлежит CANARY, и не позволяет принять production session за canary.
- **Live request trace.** Для реального request программа показывает timestamps основных этапов proxy.
- **Rollback indicator.** GUI показывает, что production/current tunnel остаётся на прямом path.

**Результат:** пользователь получает реальную telemetry без изменения рабочего traffic.

### Сценарий P4-S2 — Сравнить overhead proxy

**Мотивация:** пользователь хочет понять, добавляет ли observability proxy заметную задержку.

**Взаимодействие:** пользователь запускает несколько одинаковых тестовых calls и открывает comparison view.

**Фичи / желаемое поведение:**
- **Direct vs canary comparison.** Программа показывает сопоставимые latency measurements для двух путей, если для них есть валидные данные.
- **Proxy overhead.** Программа рассчитывает дополнительное время proxy отдельно от общей latency.
- **Sample count.** Программа показывает количество измерений и не делает выводы по одному случайному sample.

**Результат:** пользователь может принять решение, приемлем ли overhead.

### Сценарий P4-S3 — Разобрать реальную ошибку

**Мотивация:** пользователь хочет проверить, как canary показывает реальный EPERM, disconnect или restart.

**Взаимодействие:** пользователь открывает event и переходит из него в request/session trace.

**Фичи / желаемое поведение:**
- **Incident timeline.** Программа связывает error event, request ID, session и child process, если такие данные реально доступны.
- **Process evidence.** PID/exit code показываются только когда они подтверждены collector/proxy.
- **No false attribution.** GUI не называет конкретный AV причиной без прямого доказательства.

**Результат:** пользователь видит фактическую цепочку сбоя и отдельно — диагностические предположения.

## Prototype 5 — heartbeat canary

### Задачи пользователя
- Отличать «чат действительно работает» от «туннель просто жив».
- Видеть, что длинный run всё ещё активен, даже если между tool calls есть длинная пауза.
- Отличать active, waiting-user, stale и finished.
- Проверять, что heartbeat не выполняет никаких host actions.

### Сценарий P5-S1 — Посмотреть liveness конкретного run

**Мотивация:** пользователь запустил долгую задачу и хочет понять, продолжает ли чат работу.

**Взаимодействие:** пользователь открывает session/run details.

**Фичи / желаемое поведение:**
- **Liveness state.** Программа показывает `active`, `waiting-user`, `stale`, `finished` и время последнего сигнала.
- **Last activity.** Программа отдельно показывает последний обычный tool call и последний heartbeat.
- **Reason/status text.** Если run помечен waiting-user или finished, GUI показывает это как состояние, а не как ошибку.

**Результат:** пользователь не путает отсутствие tool calls с падением чата.

### Сценарий P5-S2 — Обнаружить зависший run

**Мотивация:** пользователь подозревает, что длинная задача перестала работать.

**Взаимодействие:** пользователь смотрит session list и открывает stale session.

**Фичи / желаемое поведение:**
- **Stale threshold.** Программа переводит session в stale только после заданного периода без activity/heartbeat.
- **Threshold visibility.** Текущее правило stale отображается пользователю, чтобы статус не выглядел магическим.
- **Timeline.** GUI показывает последний известный сигнал и gap после него.

**Результат:** пользователь получает основание решить, ждать дальше, проверить чат или вмешаться вручную.

### Сценарий P5-S3 — Проверить heartbeat механизм

**Мотивация:** пользователь хочет убедиться, что heartbeat только сообщает liveness и не имеет скрытых полномочий.

**Взаимодействие:** пользователь наблюдает test run и смотрит heartbeat events.

**Фичи / желаемое поведение:**
- **Heartbeat event.** Каждый heartbeat отображается как отдельное telemetry событие с timestamp.
- **Capability boundary.** GUI явно показывает heartbeat как monitoring-only signal без shell/filesystem action.
- **Failure handling.** Если heartbeat не дошёл, программа отмечает missing signal и не пытается самостоятельно выполнять host repair.

**Результат:** пользователь видит работу liveness без расширения capability boundary.

## Prototype 6 — controlled production rollout

### Задачи пользователя
- Безопасно решить, готов ли observability path для production.
- Контролировать rollout и иметь понятный rollback.
- Видеть production health, не делая dashboard обязательной частью tunnel.

### Сценарий P6-S1 — Принять решение о rollout

**Мотивация:** пользователь хочет перейти от canary к production только при наличии достаточных доказательств.

**Взаимодействие:** пользователь открывает rollout view и сравнивает acceptance metrics.

**Фичи / желаемое поведение:**
- **Acceptance checklist.** Программа показывает, выполнены ли latency, reliability, AV/interference и rollback criteria.
- **Comparison view.** Canary и current production metrics показываются рядом за сопоставимый период.
- **Explicit decision.** GUI не переключает production автоматически только потому, что все метрики зелёные; пользователь должен явно подтвердить rollout.

**Результат:** пользователь принимает осознанное решение, основанное на измерениях.

### Сценарий P6-S2 — Контролировать production после rollout

**Мотивация:** пользователь уже выполнил rollout и хочет убедиться, что рабочие чаты не деградировали.

**Взаимодействие:** пользователь открывает dashboard и смотрит production health, latency и error events.

**Фичи / желаемое поведение:**
- **Production status.** Программа явно показывает текущий environment и версию path.
- **Regression alerts.** При росте latency/error rate GUI выделяет отклонение от baseline.
- **Independent dashboard.** Остановка GUI не останавливает tunnel и не меняет его state.

**Результат:** пользователь может мониторить production без создания новой точки отказа.

### Сценарий P6-S3 — Выполнить rollback

**Мотивация:** после rollout пользователь видит существенную деградацию и хочет вернуться на прямой path.

**Взаимодействие:** пользователь открывает rollout controls, проверяет причину и явно подтверждает rollback.

**Фичи / желаемое поведение:**
- **Rollback status.** Программа показывает доступный fallback path и его актуальность.
- **Confirmation.** Rollback требует явного пользовательского подтверждения и показывает, что именно будет изменено.
- **Post-rollback verification.** После rollback GUI проверяет health/latency и показывает результат отдельно от самого факта переключения.

**Результат:** пользователь получает контролируемый возврат к безопасному path и доказательство его состояния.

## Правило для всех следующих прототипов

При добавлении новой GUI-фичи сначала описывается пользовательская задача и сценарий, затем ожидаемое поведение программы. Не наоборот.

Минимальная цепочка:

`задача пользователя → мотивация → действие пользователя → реакция программы → результат → критерий успеха`.

Если фича не помогает решить конкретную задачу пользователя или её поведение нельзя однозначно описать внутри сценария, её не добавлять в прототип только потому, что технически она доступна.

## P1 status update — 2026-10-08

P1 уже является live shadow dashboard на `127.0.0.1:8092`, а не только планом.
Он читает `/health?details=true`, `/health/mcp`, `/metrics` и sanitized WARN/ERROR, не меняя production MCP path.

Выявлен и исправлен дефект самого sidecar: HTTP listener оставался жив, но handler мог отдавать empty reply, если стандартный output процесса уже был недоступен и `SimpleHTTPRequestHandler` падал во время request logging.
`log_message` сделан non-fatal, P1 перезапущен с redirected logs; после исправления серия из 30, затем 20 запросов `/api/snapshot` прошла HTTP 200 без ошибок.

Добавлен собственный collector state: samples, successes, failures, consecutive failures, last success/error. GUI показывает эти counters рядом с временем последнего sample.

Следующий пользовательский сценарий P1/P2: при очередном 25s timeout пользователь нажимает `Mark 25s timeout`, а программа сохраняет не только browser-memory отметку, но и устойчивый incident snapshot с tunnel/MCP/control-plane/queue/dispatcher/response-delivery deltas и окном sanitized logs.

## P1/P2 implementation update — rolling history

The P1 collector now samples every 5 seconds in the sidecar process and persists a sanitized 60-minute rolling history to JSONL. History is loaded after P1 restart, so a browser reload or sidecar restart no longer erases the baseline.

The `Mark 25s timeout` action now creates a persistent incident artifact server-side instead of only adding a browser-memory event. The artifact contains a fresh snapshot and the preceding 2-minute history window. Current limitation: the post-event window is not yet attached automatically; that remains the next P2 increment.

Acceptance evidence: syntax checks pass, history survives restart, background sampling advances without browser requests, and repeated `/api/snapshot` reads do not create additional samples or affect the production tunnel path.

## P2 incident diagnostics checkpoint — 2026-10-08

The persistent incident workflow now has a real lifecycle rather than a point-in-time mark:
`pre-event history -> mark snapshot -> collecting -> post-event snapshot/history -> complete`.

User-visible behavior:
- pressing `Mark 25s timeout` creates one persisted incident;
- the incident list immediately shows `collecting` and the remaining post-window time;
- after the default 120-second window it becomes `complete`;
- selecting it shows marked time, Tunnel live/ready, MCP initialized state, pre/post sample counts and the diagnosis recorded at the mark;
- `Export redacted ZIP` exports only the sanitized incident artifact and its boundary manifest.

Restart resilience is part of the behavior: an unfinished post-event capture is resumed/finalized after P1 restarts. This prevents a sidecar restart from silently destroying the most useful part of an incident.

Next scenario: derive before/after deltas (409, transport errors, queue/dispatcher activity, latency and MCP initialize epoch) and present a concise evidence-first diagnostic summary without claiming a root cause that the available telemetry cannot prove.
