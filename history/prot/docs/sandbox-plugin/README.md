# Sandbox GUI plugin

Статус: planned / documentation placeholder.

Это отдельный будущий plugin/broker для автономной GUI-работы ChatGPT внутри Windows Sandbox или, при необходимости, отдельной VM.

Он не является частью Tunnel Observability GUI.

## Цель

Дать ChatGPT отдельный GUI capability surface:
- открыть приложение внутри Sandbox;
- inspect/UIA;
- click/type;
- screenshot/record;
- запускать Sandbox-targeted процессы;
- при этом не предоставлять произвольный HOST GUI или unrestricted HOST shell.

## Целевая схема

```text
ChatGPT
  -> Sandbox Control plugin
  -> Secure MCP Tunnel / restricted host broker
  -> Sandbox-targeted automation
  -> Windows Sandbox
```

Runtime key остаётся на HOST.

## Текущие source documents

- [../../SANDBOX-GUI-PLAN.md](../../SANDBOX-GUI-PLAN.md)
- [../isolation/README.md](../isolation/README.md)

## Документация, которая появится здесь

По мере реализации добавить:
- `ARCHITECTURE.md` — компоненты и trust boundaries;
- `CAPABILITIES.md` — разрешённые plugin tools;
- `SECURITY.md` — threat model и host/sandbox boundary;
- `OPERATIONS.md` — start/stop/recovery;
- `TESTING.md` — UIA/input/focus/isolation acceptance tests;
- `RUNBOOKS/` — восстановление, upgrade, credential rotation при необходимости.

До реализации эти файлы не создаём с выдуманным содержимым.

## Правило перехода к HOST

После выполнения Sandbox-capable части работа останавливается.
Если нужен обычный HOST, ChatGPT объясняет зачем и просит отдельное разрешение.

HOST CLI/filesystem permission не означает HOST GUI permission.