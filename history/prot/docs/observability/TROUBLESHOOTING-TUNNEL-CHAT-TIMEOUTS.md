# Troubleshooting — chat timeout vs tunnel failure

Дата: 2026-10-08.
Статус: рабочий runbook на основе фактической телеметрии Fortis_M.

## Симптом

Отдельный ChatGPT-чат сообщает примерно следующее:

```text
get_config не ответил за 25 секунд.
Доступность туннеля пока не подтверждена.
```

Такой timeout **не доказывает**, что весь Secure MCP Tunnel остановлен.

## Что уже наблюдалось на Fortis_M

При подобных проблемах другой чат одновременно продолжал успешно вызывать Desktop Commander.
Локальный tunnel-client оставался `live=true`, `ready=true`, MCP child — `running/initialized`, queue — пустой.

Также реально зафиксированы transient control-plane ошибки:
- HTTP 503 `tunnel_transport_unavailable`;
- `poll transport failed (network_error)`;
- POST response с `unexpected EOF`;
- автоматическое восстановление polling после ошибок.
Отдельно в рабочих вызовах несколько раз наблюдалась ошибка:

```text
MCP server is not initialized;
send initialize and notifications/initialized before operational requests
```

После нового лёгкого вызова `get_config` MCP снова отвечал.

Метрики также показывают ненулевые `tools/call` с status 409.
Не каждый 409 обязательно имеет одну и ту же причину, поэтому GUI должен показывать delta и корреляцию по времени, а не объявлять причину только по счётчику.

## Что показывают latency metrics

На одном из замеров успешных `tools/call`:
- около 20% были дольше 10 секунд;
- cumulative average был около 8–9 секунд;
- `resources/read` имел особенно тяжёлый хвост.

Поэтому client-side timeout около 25 секунд принципиально возможен даже без глобального падения daemon.

## Recovery ladder для одного чата

1. Не объявлять tunnel down после одного timeout.
2. Не делать mutations, пока доступность не подтверждена.
3. Сделать **один** лёгкий read-only retry, предпочтительно `get_config`.
4. Если пришёл `mcp_initialization_required` / `MCP server is not initialized`, сделать новый лёгкий вызов после нового MCP lifecycle/handshake.
5. Если второй лёгкий вызов не проходит, формулировать проблему как:
   `этот chat/session path сейчас не подтверждён`, а не `туннель выключен`.
6. Проверить P1 dashboard:
   - Tunnel live/ready;
   - control-plane failures / recent transport errors;
   - MCP child running/initialized;
   - queue depth/backpressure;
   - dispatcher active/oldest request;
   - response-delivery failures/retries;
   - новый delta `tools/call 409`.
7. Если P1 зелёный, другие чаты работают, а конкретный чат продолжает fail — сначала refresh/reconnect именно этого ChatGPT app/chat binding.
8. Глобальный tunnel-client не перезапускать только из-за одного проблемного чата.

## Когда перезапуск tunnel-client оправдан

Перезапускать общий tunnel имеет смысл, если есть устойчивый локальный признак:
- `/healthz` недоступен;
- process tunnel-client отсутствует;
- `ready=false` держится, а не мелькает кратковременно;
- MCP child не running/initialized и сам не восстанавливается;
- control-plane consecutive failures сохраняются;
- queue/backpressure или dispatcher явно застряли;
- есть evidence process kill / AV interference.

Restart затронет все активные чаты, поэтому это не first-line recovery.

## Safe restart

1. Остановить старый launcher/process.
2. Убедиться, что не осталось второго экземпляра с тем же tunnel ID.
3. При сомнениях выполнить:
   `tunnel-client doctor --profile desktop-commander --explain`.
4. Запустить обычный launcher.
5. Проверить local health/ready.
6. Проверить один read-only tool call из ChatGPT.
## Что считать "repair"

Для текущего ручного profile нет универсальной команды, которая чинит любой зависший ChatGPT session.

`doctor` валидирует конфигурацию и prerequisites, но не ремонтирует уже зависшую hosted chat session.

В v0.0.15 есть managed `runtimes` workflow со status/repair actions, но текущий Desktop Commander tunnel запускается нашим foreground launcher, поэтому перенос на managed runtime — отдельное изменение архитектуры, а не быстрый repair.

## Возможные controlled experiments

### Initialized-notification shim
tunnel-client поддерживает `mcp.stdio_send_initialized_notification`.
Он может отправлять `notifications/initialized` после успешного stdio initialize.

Это релевантно наблюдаемым initialization errors, но включать его в production вслепую нельзя.
Сначала нужен canary/измерение: сравнить 409/init failures до и после.

### MCP concurrency
Текущий default `mcp.max_concurrent_requests` — 10.
Уменьшение concurrency потенциально может снизить конкуренцию на stateful stdio child, но может ухудшить latency и создать очередь.

Поэтому менять concurrency только через canary и измерения P1/P4, а не как догадочный hotfix.

## Следующее улучшение observability

P1 должен фиксировать состояние в момент пользовательского `Mark 25s timeout`.
P2/P4 должны добавить persistent history и correlation, чтобы определить:
`request не дошёл до tunnel` vs `дошёл, но долго выполнялся` vs `response не доставился`.

## Новое подтверждение 2026-10-08

Во время дальнейшей работы тот же текущий chat/session несколько раз получил `MCP server is not initialized` на обычных Desktop Commander calls; повторный вызов затем снова проходил. Это прямое дополнительное наблюдение lifecycle/init failure с recovery без обязательного global restart.

Одновременно Observatory P1 имел независимый sidecar-дефект `empty reply from server`. Он оказался не evidence проблемы Tunnel: HTTP handler P1 мог падать на собственном request logging при закрытом stdout. После non-fatal logging fix и перезапуска P1 `/api/snapshot` прошёл 30 + 20 последовательных HTTP 200.

При расследовании поэтому всегда различать:
- chat/connector/MCP lifecycle failure;
- production Tunnel health;
- Observatory collector health.
