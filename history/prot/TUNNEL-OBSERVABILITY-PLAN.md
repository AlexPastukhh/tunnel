# План наблюдаемости туннеля и рабочих чатов

Статус: проектирование
Дата: 2026-10-07

## Цель

Сделать локальный GUI, где видно:
- жив ли tunnel-client и его MCP target;
- есть ли сейчас активные ChatGPT/MCP сессии;
- какие tool calls идут через туннель;
- сколько времени занимает каждый этап;
- какие команды зависли или завершились ошибкой;
- есть ли признаки вмешательства антивируса, firewall или другого host software;
- когда в последний раз конкретная активная сессия подавала признаки жизни.

GUI должен работать локально на HOST и не открываться наружу.

## Что уже есть

Текущий Secure MCP Tunnel уже отдаёт:
- `http://127.0.0.1:8080/health`;
- `http://127.0.0.1:8080/metrics`.

Проверено 2026-10-07: health возвращает `live=true`, `ready=true`, runtime instance/version/uptime.
Metrics уже содержат histogram `command_end_to_end_latency_milliseconds`,
HTTP poll/response counters и статусы control-plane запросов.

Это хороший базовый слой, но его недостаточно для ответа «какой чат что делает сейчас».
## Нужные уровни liveness

Не смешивать разные понятия «жив».

1. Tunnel process alive:
   tunnel-client запущен, /health отвечает.

2. Control-plane link alive:
   идут poll/response запросы, нет длительного разрыва соединения.

3. MCP server alive:
   stdio target запущен и отвечает на initialize/tool calls.

4. Active request alive:
   конкретный MCP request принят, выполняется и ещё не завершён.

5. Child command alive:
   start_process/другая команда породила локальный процесс, известны PID, start, exit/output.

6. Chat/run alive:
   активный ChatGPT run периодически вызывает heartbeat или другие MCP tools.

Последний пункт нельзя надёжно вывести только из /health:
живой туннель не означает, что конкретный чат всё ещё работает.

Важно: когда ChatGPT реально ждёт пользователя или run уже остановлен,
он не может автономно продолжать слать heartbeat.
Поэтому отсутствие heartbeat означает «нет подтверждённой активности», а не автоматически «чат умер».

## Главная архитектурная идея

Добавить прозрачный host-side MCP observability proxy между tunnel-client и Desktop Commander.
## Proxy

```text
ChatGPT
  -> Secure MCP Tunnel
  -> tunnel-client
  -> MCP Observability Proxy
  -> Desktop Commander / другой MCP server
```

Proxy должен:
- прозрачно проксировать JSON-RPC stdin/stdout;
- назначать request/session correlation IDs;
- записывать request start / response / error / duration;
- знать method/tool name;
- отдельно измерять local MCP handling time;
- отслеживать дочерние process sessions там, где это возможно;
- добавлять локальный `monitor_heartbeat` tool;
- отдавать собственный localhost API/WebSocket для dashboard;
- не логировать содержимое файлов, shell args и secrets по умолчанию.

Raw arguments можно включать только отдельным debug-флагом с redaction.

## Почему proxy полезен

Tunnel metrics показывают end-to-end и transport слой.
Proxy даёт локальную границу измерения.

Тогда можно различить:
- долго до proxy -> сеть/control plane/tunnel;
- proxy получил запрос быстро, а response долго нет -> MCP server/локальная команда/AV;
- child process стартовал, но внезапно исчез -> возможный AV/OS kill;
- response готов локально, но долго не доставляется -> tunnel/control plane;
- initialize/stdio регулярно рвётся -> server restart, AV или protocol problem.
## Heartbeat contract

Для активной длинной работы можно добавить правило для чатов:

- любой обычный MCP tool call считается признаком жизни;
- если активный run долго не делает tool calls, он вызывает `monitor_heartbeat`;
- heartbeat ничего не меняет на HOST и должен быть очень дешёвым;
- рекомендуемый интервал для прототипа: 60–120 секунд без другой MCP-активности;
- heartbeat несёт session/run label, phase и optional short status;
- heartbeat не должен содержать пользовательские данные, secrets или содержимое файлов.

Пример статусов:
- `working`;
- `waiting-local-process`;
- `verifying`;
- `waiting-user`;
- `finished`.

Dashboard не должен объявлять chat dead только по timeout.
Предлагаемые состояния:
- green: activity/heartbeat недавно;
- yellow: heartbeat просрочен, но tunnel/server живы;
- gray: session idle/finished/unknown;
- red: active request завис, transport/server умер или зафиксирована ошибка.

## Correlation

Нельзя предполагать, что Secure MCP Tunnel сам даёт удобный ChatGPT conversation ID.
Если request metadata не содержит стабильного run/session ID,
proxy должен создавать локальный session ID при MCP initialize.

Дополнительно чат может один раз вызвать `monitor_register` с короткой меткой задачи.
Не хранить полный prompt или transcript.
## GUI

Минимальный dashboard:
- общий статус Tunnel / MCP target / proxy;
- uptime и время последнего успешного poll/response;
- список активных sessions;
- last activity / last heartbeat / state;
- inflight requests;
- tool name, start time, elapsed, result/error;
- rolling p50/p95/p99 latency;
- error rate и последние protocol/transport ошибки;
- список локальных child processes, связанных с tool calls;
- отдельный блок «AV / OS interference signals».

Для каждой команды желательно строить timeline:

```text
control plane enqueue
-> tunnel poll receive
-> proxy request receive
-> MCP server handling
-> child process start/exit
-> proxy response
-> tunnel response upload
```

Не все точки доступны сразу.
MVP может показывать tunnel end-to-end + proxy local duration,
а более глубокую process instrumentation добавить позже.

## Признаки вмешательства AV

Сам dashboard не должен утверждать «это Kaspersky», если нет прямого события.

Сильные косвенные сигналы:
- `spawn EPERM`;
- child process исчез сразу после запуска;
- stdio server неожиданно завершился;
- request завис после local dispatch;
- series of initialize/409/reconnect;
- tunnel health остаётся green, но локальные shell calls начинают массово падать;
- резкий рост local handling latency без роста transport latency.

При наличии стабильного локального источника событий Kaspersky
можно добавить optional collector и коррелировать AV event timestamp/PID/path с MCP request.
## Хранение данных

Для MVP достаточно локальной SQLite DB или append-only JSONL:
- session id;
- request id;
- tool/method;
- timestamps;
- duration;
- status/error class;
- child PID/exit code, если известно;
- heartbeat state.

Не хранить:
- runtime key;
- полные tool arguments;
- stdout/stderr целиком;
- содержимое файлов;
- пользовательские prompts/transcripts.

Retention по умолчанию: 7–14 дней с автоматической ротацией.

## Этапы реализации

### Phase 1 — dashboard поверх существующих endpoints
1. Collector читает `/health` и `/metrics`.
2. Локальный GUI показывает tunnel alive/ready, uptime, latency, HTTP status/error counters.
3. Добавить latency history и простые alerts.
4. Никак не менять текущий MCP path.

### Phase 2 — transparent MCP proxy
5. Вставить proxy между tunnel-client и Desktop Commander.
6. Проверить, что tool behavior не изменился.
7. Добавить request/response timing, inflight state и local errors.
8. Сопоставить proxy timings с tunnel metrics.

### Phase 3 — session heartbeat
9. Добавить `monitor_register` и `monitor_heartbeat`.
10. Добавить prompt rule для активных tunnel workflows.
11. Проверить states active/stale/idle/finished.

### Phase 4 — process/AV correlation
12. Связать start_process с PID и completion.
13. Выявлять EPERM/abrupt exit/restart patterns.
14. При возможности добавить read-only Kaspersky event collector.
## Security boundary observability

Monitoring не должен становиться новым privileged control plane.

Требования:
- dashboard/API только на `127.0.0.1`;
- collector read-only там, где возможно;
- proxy не должен иметь больше filesystem/OS прав, чем proxied MCP server;
- heartbeat tools не дают shell/filesystem capability;
- UI не должен уметь silently расширять mounts/grants;
- runtime key не отображать и не сохранять;
- debug logging с raw args выключен по умолчанию.

Для будущего Repo Mode и Sandbox GUI мониторинг должен быть общий,
но показывать capability boundary каждой сессии:
- `REPO`;
- `SANDBOX GUI`;
- `HOST MAINTENANCE`.

HOST MAINTENANCE должен быть визуально выделен как более высокий риск.

## Acceptance tests

План считается рабочим, если:
- выключенный tunnel отображается как down без ложного «chat dead»;
- живой idle tunnel отличается от активной chat session;
- active request появляется в GUI до завершения;
- после response видны duration/result;
- зависший request становится stale по таймеру;
- heartbeat обновляет только session liveness и не выполняет host action;
- restart MCP target виден отдельно от restart tunnel-client;
- `spawn EPERM` и abrupt process failure попадают в диагностический timeline;
- latency можно разделить хотя бы на tunnel end-to-end и local proxy duration;
- dashboard не содержит secrets/tool payloads по умолчанию;
- мониторинг не ломает существующий Secure MCP Tunnel.

## GUI prototype track

Подробный безопасный план параллельной разработки GUI находится в `TUNNEL-OBSERVABILITY-GUI-PROTOTYPES.md`.
Prototype 0–2 разрабатываются out-of-band и не меняют рабочий tunnel; proxy/heartbeat сначала идут только через отдельный canary tunnel.

## Первое практическое действие

Начать с Phase 1: отдельный read-only collector/dashboard поверх уже существующих
`127.0.0.1:8080/health` и `/metrics`.

Это даёт пользу сразу и почти не рискует рабочим туннелем.
Proxy и heartbeat добавлять только после того, как baseline dashboard стабилен.

## Update 2026-10-08 — intermittent chat/session failures

Новые наблюдения усиливают гипотезу, что 25s timeout одного чата не равен глобальному падению tunnel-client.
В нескольких эпизодах локальный daemon оставался live/ready, Desktop Commander продолжал отвечать из другого chat/session path, а проблемный чат получал timeout или `MCP server is not initialized`.

Наблюдаемая latency также имеет длинный хвост: на одном snapshot около 20% успешных `tools/call` были >10s. Текущих histogram buckets недостаточно, чтобы доказать долю >25s.

Приоритет диагностики теперь такой:
1. chat/connector session lifecycle;
2. request long-tail latency / queueing;
3. transient control-plane transport;
4. stdio initialize/initialized race;
5. concurrency/backpressure;
6. AV/host interference только при прямом timestamp/PID evidence.

Global restart не является first-line recovery для одного проблемного чата. Сначала нужен лёгкий read-only retry и reconnect конкретного chat/app binding при green local health.
Production `runtime key`, `tunnel_id`, concurrency и stdio lifecycle flags не менять без before/after evidence.

P1 должен быть независимым свидетелем: собственный collector health/error counter, rolling history и immutable incident snapshot важнее новых визуальных панелей.

## Implementation checkpoint — 2026-10-08

Phase 1 now includes a sidecar-owned 5-second sampler, persistent sanitized JSONL history with 60-minute retention, and persistent incident creation from the GUI.
The incident mark captures a fresh live snapshot and a 2-minute pre-event history window. This is sufficient to stop relying on post-hoc reconstruction for the next real 25s timeout.

Next diagnostic increment: add a delayed post-event capture window, incident list/detail view and redacted export bundle. Request-level attribution (`did not reach tunnel` / `local execution` / `response delivery`) still requires the later canary proxy stage.

## Incident diagnostics checkpoint — 2026-10-08

The out-of-band observability path now persists a complete timeout observation window: two minutes before the user mark and two minutes after it by default. Incidents have a durable `collecting -> complete` lifecycle and unfinished captures resume after sidecar restart.

The localhost API now exposes incident list/detail and a redacted ZIP export. The GUI shows persistent incidents and key mark-time evidence while keeping evidence separate from hypotheses.

This closes the basic data-capture gap for the next real timeout. The next increment is automated delta/correlation analysis across the pre/mark/post windows. It still cannot prove whether a request never reached the tunnel versus reached local execution versus failed during response delivery; that boundary requires the planned canary MCP proxy.
