# Handoff — intermittent Tunnel timeouts + Observability P1

Дата: 2026-10-08.
Назначение: передать следующей ветке/чату все фактические наблюдения, текущие артефакты и следующий план без повторного расследования.

## Короткий вывод

Глобальный Secure MCP Tunnel **не выглядит постоянно падающим**. Несколько раз отдельные чаты сообщали `get_config не ответил за 25 секунд`, в то время как другой чат почти одновременно успешно работал через тот же Tunnel.

На момент последних проверок Tunnel отвечал через сам MCP path, локальный daemon был `live=true`, `ready=true`, а Desktop Commander отвечал как `openai-mcp`.

Наиболее вероятный класс проблемы сейчас: **per-chat / per-session / request lifecycle + длинный latency tail**, а не постоянное падение всего daemon.

Глобальный restart нельзя делать first-line recovery для одного проблемного чата: он затрагивает все активные чаты и может скрыть корень проблемы.

## Текущая рабочая архитектура

```text
ChatGPT
  -> custom MCP connector
  -> OpenAI Secure MCP Tunnel
  -> tunnel-client on Fortis_M
  -> stdio
  -> desktop-commander-trusted.cmd
  -> Desktop Commander 0.2.52
```

Tunnel ID: `tunnel_6ac4a7249a4081918eb0881c870acf07`.
tunnel-client: `0.0.15+a390c168ff1b2d14e73a95991c186c6aba3ff5a0`.
Runtime key был ротирован 2026-10-07 и после ротации подтверждён end-to-end.
## Последнее подтверждённое состояние daemon

Проверка через Tunnel/PC показала:
- `tunnel-client.exe` PID 13956, запущен 2026-10-07 17:27:26;
- child `cmd.exe` PID 17860;
- Desktop Commander `node.exe` PID 22196, запущен 17:27:27;
- процесс не перезапускался между несколькими проблемными эпизодами;
- `/health`: `live=true`, `ready=true`, `lifecycle=running`;
- на снимке около 00:28 uptime был ~25265 s (~7 h);
- Desktop Commander `get_config` из этого чата успешно отвечал через Tunnel.

Это сильный контраргумент гипотезе «при каждом 25s timeout падает весь tunnel-client».

## Наблюдавшийся симптом

Другой чат несколько раз писал примерно:

```text
get_config не ответил за 25 секунд — ожидание остановил.
Доступность туннеля пока не подтверждена.
Файлы не менял.
```

Корректная формулировка после такого события:
`доступность Tunnel для этого chat/session path сейчас не подтверждена`.

Один timeout **не доказывает**, что daemon глобально down.

## Реальные latency observations

Из `/metrics` на одном снимке:

### tools/call, status=200, poll_to_response
- count: 416;
- sum: 3,396,909 ms;
- average: ~8,166 ms;
- <=5 s: 207;
- <=7.5 s: 294;
- <=10 s: 332;
- >10 s: 84, то есть ~20.2%.

Гистограмма после 10 s сразу имеет `+Inf`, поэтому по этому снимку нельзя вычислить, сколько именно запросов было >25 s. Но тяжёлый хвост реальный, поэтому client-side timeout около 25 s принципиально возможен без смерти daemon.
### initialize, status=200, enqueue_to_response
- count: 486;
- sum: 1,497,925 ms;
- average: ~3,082 ms;
- <=5 s: 403;
- <=7.5 s: 435;
- <=10 s: 456;
- >10 s: 30 (~6.2%).

Число initialize большое относительно tools/call. Само по себе это не доказывает reconnect bug, но делает lifecycle/session churn важным объектом исследования.

### resources/read, status=200, enqueue_to_response
- count: 24;
- sum: 417,152 ms;
- average: ~17,381 ms;
- <=5 s: 1;
- <=7.5 s: 5;
- <=10 s: 7;
- >10 s: 17 (~70.8%).

Также были `resources/read` status 409:
- count: 5;
- enqueue_to_response sum: 21,335 ms (~4,267 ms avg);
- poll_to_response sum: 16,920 ms (~3,384 ms avg).

Семантику конкретного 409 нельзя угадывать только по счётчику. Нужна корреляция по времени с логом/request lifecycle.

## Recent Desktop Commander tool history

В локальной истории были успешные `get_config` с сильно разным временем:
- один около 4.6 s;
- следующий около 0.36 s;
- позже около 2.5 s.

То есть даже лёгкий read-only вызов имеет заметный variance.

На другом snapshot Desktop Commander показывал примерно 4099 total tool calls, 4026 successful и 73 failed. Это локальная статистика Desktop Commander, а не полный tunnel error rate, но она подтверждает, что ошибки не нулевые и при этом сервис в целом продолжает работать.
## Уже зафиксированные error classes

В существующем runbook отмечены реальные наблюдения:
- HTTP 503 `tunnel_transport_unavailable`;
- `poll transport failed (network_error)`;
- POST response с `unexpected EOF`;
- автоматическое восстановление polling после transport errors;
- `MCP server is not initialized; send initialize and notifications/initialized before operational requests`;
- ненулевые `tools/call` / другие запросы со status 409.

Особенно важна initialization error: после неё новый лёгкий вызов иногда снова успешно проходил. Это похоже на lifecycle/session failure, а не обязательно на смерть daemon.

## Рабочие гипотезы, по приоритету

### H1 — per-chat / connector session lifecycle
Поддерживается тем, что один чат fail/timeout, а другой одновременно работает; также наблюдалась `MCP server is not initialized`.

Проверять: initialize timeline, session/reconnect state, 409 delta, affected chat refresh/reconnect.

### H2 — long-tail latency + client timeout
Поддерживается метриками: ~20% успешных tools/call >10 s, среднее около 8 s. Нужна история с точным bucket/trace около 25 s.

### H3 — transient control-plane/network transport
Поддерживается зафиксированными 503/network_error/unexpected EOF с последующим recovery.

### H4 — stdio initialization race / initialized notification
tunnel-client имеет опцию `mcp.stdio-send-initialized-notification`.
Это релевантно observed init errors, но включать production вслепую нельзя. Нужен canary A/B.

### H5 — concurrency/backpressure
CLI defaults: control-plane max inflight 20, MCP max concurrent requests 10, connection max TTL 10m.
Профиль эти параметры явно не задаёт; environment overrides ещё надо исключить.
Уменьшение concurrency может помочь stateful stdio, но может ухудшить queue latency. Только canary + измерения.

### H6 — Kaspersky / host interference
Исторически Kaspersky уже блокировал node/Desktop Commander, поэтому гипотеза допустима.
Но для конкретных 25s timeout прямого AV evidence пока нет. Не объявлять Kaspersky причиной без timestamp/PID/event correlation.
## Что НЕ является хорошим first-line fix

- Не перезапускать глобальный tunnel-client после одного timeout одного чата.
- Не ротировать runtime key из-за latency/session timeout.
- Не менять connector/tunnel_id без evidence.
- Не увеличивать Kaspersky exclusions вслепую.
- Не менять concurrency или stdio lifecycle flags сразу в production.
- Не считать `doctor RESULT ok` доказательством отсутствия runtime/session problem: doctor валидирует config/prerequisites.

## Recovery ladder для проблемного чата

1. Не делать mutations после timeout, пока read-only доступность не подтверждена.
2. Сделать ровно один лёгкий retry, предпочтительно `get_config`.
3. Если получено `mcp_initialization_required` / `MCP server is not initialized`, трактовать как lifecycle/session failure.
4. Сделать новый лёгкий вызов после нового handshake/lifecycle.
5. Если retry успешен — продолжить и отметить transient failure.
6. Если второй retry fail/timeout — сказать, что именно этот chat/session path не подтверждён.
7. Проверить Observatory P1 / локальные health details.
8. Если Tunnel healthy и другие чаты работают — refresh/reconnect app/connector именно проблемного чата.
9. Глобальный restart только при устойчивом локальном unhealthy/dead evidence.

## Когда global restart оправдан

- `/healthz` недоступен;
- process tunnel-client отсутствует;
- `ready=false` держится устойчиво;
- MCP child не running/initialized и не восстанавливается;
- control-plane consecutive failures продолжаются;
- queue/dispatcher реально застрял;
- есть evidence process kill / AV interference.

Safe restart:
`stop launcher -> убедиться, что второго экземпляра нет -> doctor --profile desktop-commander --explain -> обычный launcher -> local health/ready -> один read-only ChatGPT tool call`.

В CLI v0.0.15 нет универсальной команды `repair` для текущего foreground profile. Есть `doctor`, `health`, admin/runtimes workflows. Managed runtimes имеют отдельные status/repair capabilities, но миграция туда — архитектурное изменение, не быстрый hotfix.
## Observability GUI — фактическое состояние

### P0
`C:\Users\alexa\Documents\prot\observability-ui-prototype-0`
Synthetic fixture UI. Не читает live Tunnel.

### P1
`C:\Users\alexa\Documents\prot\observability-ui-prototype-1`

README говорит: working live shadow prototype.
Он читает read-only:
- `/health?details=true`;
- `/health/mcp`;
- `/metrics`;
- sanitized WARN/ERROR из `/api/logs`.

Рабочий MCP path не меняет.
Локальный URL: `http://127.0.0.1:8092/`.
На последней проверке порт 8092 слушал PID 30260.

P1 уже имеет панели:
- Tunnel / control-plane / MCP target / local work;
- recent/cumulative tools/call latency;
- component layers;
- transport + 200/409;
- sanitized WARN/ERROR timeline;
- incident triage evidence vs hypothesis;
- manual `Mark 25s timeout`.

Важный новый дефект P1: при одном probe `http://127.0.0.1:8092/api/snapshot` соединение было неожиданно закрыто сервером, хотя listener 8092 существовал. Это отдельная проблема sidecar GUI/collector; она не доказывает проблему Tunnel и должна быть исправлена, чтобы Observatory сам был надёжным свидетелем.

## Built-in tunnel-client diagnostics

`tunnel-client help troubleshooting` рекомендует сначала локальные operator surfaces:
- `/healthz` — только liveness;
- `/readyz` — readiness/startup gates;
- `/health?details=true` — MCP, polling, uploads, queues, active work;
- `/health/mcp` — observed stdio discovery;
- embedded `/ui`;
- `doctor --profile ... --explain/json`.

Есть redacted log export:
`http://127.0.0.1:8080/api/logs/export?minutes=30`.
Архив включает recent logs, point-in-time metrics, runtime status, system details и OAuth discovery state.

Это очень полезно: при следующем реальном 25s timeout надо сразу делать timestamped snapshot/export, а не расследовать постфактум.
## Следующая работа для P1/P2

1. Исправить неожиданное закрытие P1 `/api/snapshot`; добавить собственный collector health/error counter.
2. Хранить rolling history хотя бы 30–60 минут локально.
3. При `Mark 25s timeout` сохранять immutable incident snapshot:
   - local timestamp;
   - tunnel live/ready;
   - MCP child initialized/state;
   - control-plane last success/failure;
   - queue depth;
   - dispatcher active/oldest age;
   - response upload failures/retries;
   - tools/call 200/409 deltas;
   - latency histogram delta;
   - sanitized WARN/ERROR ±2 min.
4. Добавить кнопку/export incident bundle без secrets/payloads.
5. Отдельно отображать `global tunnel healthy` vs `specific chat/session unknown/failing`.
6. Добавить persistent history (P2), чтобы видеть correlation с 25s timeout.
7. Для точного request-level ответа нужен canary proxy/P4: выяснять `request не дошёл` / `дошёл и выполнялся` / `response не доставился`.
8. Heartbeat (P5) нужен только после proxy/canary, чтобы различать chat active/stale/waiting-user/finished.

## Canary experiments, но НЕ production hotfix

A. `mcp.stdio_send_initialized_notification` on/off — сравнить init errors, 409, latency.
B. MCP concurrency variants — например текущий default против более низкого значения, только на canary.
C. Controlled tunnel restart — измерить, лечит ли только старые sessions или реально меняет transport errors.
D. Connector/chat reconnect without daemon restart — проверить, лечит ли affected chat при green daemon.
E. AV correlation — timestamp/PID событий Kaspersky против MCP request failures.

Критерий: любое изменение делать только если P1/P2 даёт before/after evidence.

## Уже существующие документы

- `docs/observability/README.md`
- `docs/observability/TROUBLESHOOTING-TUNNEL-CHAT-TIMEOUTS.md`
- `docs/observability/CHAT-TUNNEL-RECOVERY-PROMPT.md`
- `TUNNEL-OBSERVABILITY-PLAN.md`
- `TUNNEL-OBSERVABILITY-GUI-PROTOTYPES.md`
- `observability-ui-prototype-1/README.md`

Короткий recovery prompt для рабочих чатов уже написан. Его имеет смысл добавить в инструкции чатам, работающим через Fortis_M Tunnel.

## Следующему чату / ветке

Начни с чтения этого файла и перечисленных документов. Не повторяй базовое расследование с нуля.

Приоритет:
1. стабилизировать P1 collector/`api/snapshot`;
2. воспроизвести или дождаться следующего 25s timeout;
3. в момент timeout сохранить incident snapshot + redacted tunnel log export;
4. определить layer: chat/connector, control-plane, MCP lifecycle, local handler, response delivery;
5. только затем выбирать fix/canary experiment.

Не трогать runtime key, tunnel_id и production concurrency/stdio flags без нового evidence.
