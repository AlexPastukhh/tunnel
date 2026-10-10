# Fortis_M — общий roadmap среды

Статус: рабочий
Дата: 2026-10-07

Короткая эксплуатационная документация и навигация: `docs/README.md`.

Этот каталог хранит четыре связанные, но независимые линии работы.

## 1. Изоляция доступа
Файл: `SECURE-ACCESS-CONTROL-PLAN.md`

Цель:
- обычная работа ChatGPT только с репозиториями;
- реальная boundary через Docker/VM, а не только allowedDirectories;
- отдельный Maintenance Mode для полного HOST;
- временный доступ к дополнительным папкам только после локального действия пользователя.

## 2. Перенос репозиториев
Файл: `REPOSITORY-MIGRATION-PLAN.md`

Цель:
- собрать рабочие репозитории в `C:\Users\alexa\Documents\Repos`;
- не сломать Git worktrees, Tampermonkey loaders и абсолютные пути;
- после переноса иметь единый постоянный repo root для Repo Mode.

## 3. Параллельный GUI
Файл: `SANDBOX-GUI-PLAN.md`

Цель:
- дать ChatGPT отдельную GUI-среду на том же физическом ПК;
- screenshots, мышь и клавиатура только внутри Windows Sandbox/VM;
- не вмешиваться в основной Windows desktop пользователя.

## 4. Наблюдаемость туннеля и рабочих чатов
Файлы: `TUNNEL-OBSERVABILITY-PLAN.md` и `TUNNEL-OBSERVABILITY-GUI-PROTOTYPES.md`

Цель:
- локальный dashboard состояния tunnel/MCP/sessions;
- latency и error telemetry по tool calls;
- heartbeat для подтверждения активности длинных run;
- диагностика зависаний, `spawn EPERM`, reconnects и возможного вмешательства антивируса;
- общий monitoring для REPO / SANDBOX GUI / HOST MAINTENANCE.

## Порядок
1. Phase 1 observability можно начать сразу: read-only dashboard поверх `/health` и `/metrics`.
2. Параллельно привести репозитории к понятной структуре и перенести их.
3. Затем реализовать Repo Mode на новом едином корне и подключить его к monitoring.
4. После baseline monitoring добавить MCP proxy + heartbeat.
5. GUI Sandbox внедрять отдельным контуром и также подключить к monitoring.
6. Нативный HOST оставить только как ручной Maintenance fallback.