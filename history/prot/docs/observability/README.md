# Tunnel Observability GUI

Статус: Prototype 0 готов; Prototype 1 live shadow запущен и читает tunnel telemetry read-only.

## Цель

Локально видеть:
- tunnel/MCP health;
- активные sessions и inflight requests;
- latency и ошибки;
- heartbeat/liveness длинных run;
- диагностические признаки AV/OS interference.

Monitoring не должен становиться обязательной точкой отказа для рабочего tunnel.

## Текущие прототипы

P0: [../../observability-ui-prototype-0](../../observability-ui-prototype-0) — synthetic fixtures, UI shell.

P1: [../../observability-ui-prototype-1](../../observability-ui-prototype-1) — live read-only shadow dashboard.

P1 читает локальные `/health?details=true`, `/health/mcp`, `/metrics` и только санитизированные WARN/ERROR из admin logs. Рабочий MCP path не меняется.

Практический runbook по периодическим timeout отдельных чатов:
[TROUBLESHOOTING-TUNNEL-CHAT-TIMEOUTS.md](TROUBLESHOOTING-TUNNEL-CHAT-TIMEOUTS.md)

Короткая инструкция для рабочих чатов:
[CHAT-TUNNEL-RECOVERY-PROMPT.md](CHAT-TUNNEL-RECOVERY-PROMPT.md)

## Подробные планы

- [../../TUNNEL-OBSERVABILITY-PLAN.md](../../TUNNEL-OBSERVABILITY-PLAN.md)
- [../../TUNNEL-OBSERVABILITY-GUI-PROTOTYPES.md](../../TUNNEL-OBSERVABILITY-GUI-PROTOTYPES.md)

## Ближайшая последовательность

1. P0 — UI shell на fixtures.
2. P1 — read-only shadow dashboard поверх live `/health` и `/metrics`.
3. P2 — история и diagnostics.
4. P3 — offline MCP proxy simulator.
5. P4 — отдельный canary tunnel.
6. P5 — heartbeat canary.
7. P6 — только после измерений controlled production rollout.

## Boundary

Observability GUI:
- не хранит runtime key;
- не получает полномочий расширять host mounts/grants;
- не должен автоматически управлять HOST GUI;
- не должен выдавать гипотезу «это Kaspersky» как факт без прямого evidence;
- должен явно показывать, к какому capability mode относится session.

Изоляция и observability связаны телеметрией, но являются разными слоями. См. [../isolation/README.md](../isolation/README.md).
## Состояние на 2026-10-08

P1 стабилизирован после найденного sidecar-дефекта: request logging больше не может оборвать HTTP response при недоступном stdout.
После исправления `/api/snapshot` выдержал две серии проверок: 30 и 20 последовательных HTTP 200.

Collector теперь ведёт собственные counters `samples/successes/failures/consecutive_failures`, чтобы отличать проблему Observatory от проблемы Tunnel.

Новые runtime-наблюдения: отдельные MCP calls в текущем chat/session также периодически получали `MCP server is not initialized`, после чего следующий вызов снова проходил. Это добавляет evidence в пользу session/lifecycle-класса проблемы, но пока не локализует точный слой.

Ближайшая работа: persistent rolling history 30–60 минут и immutable incident snapshot/export по `Mark 25s timeout`.

## P1 persistent history implemented

P1 now owns a background 5-second sampler with a 60-minute rolling retention window. Browser refresh is no longer the mechanism that creates samples.
The history lives in `observability-ui-prototype-1/data/history.jsonl` and survives P1 restarts.

`Mark 25s timeout` now persists an incident JSON under `data/incidents/`, including a fresh telemetry snapshot and the preceding 2 minutes of sanitized history. Test incident artifacts are removed after validation.

This moves the next priority from "add rolling history" to capturing a useful post-event window and building an incident viewer/export while keeping the production MCP path unchanged.

## Incident viewer/export implemented

The live sidecar now keeps persistent incident records with a two-minute pre-event window and a two-minute post-event window by default. New incidents are visibly `collecting` until the post window closes, then become `complete`.

The GUI now lists incidents, opens their key before/after evidence and provides a redacted ZIP export. Unfinished incident collection is resumed after a P1 restart.

Current boundary remains unchanged: the sidecar is localhost-only and out-of-band; it does not alter production MCP traffic and does not collect runtime keys, tool payloads, prompts or transcripts.

Next P2 work should focus on automatic incident comparison/deltas and a compact diagnostic summary over the before/mark/after windows. Request-level path attribution remains deferred to the canary proxy stage.
