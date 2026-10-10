# Fortis_M workspace

Этот каталог — рабочая зона для инфраструктуры доступа ChatGPT к Fortis_M, observability GUI, изоляции и будущего Sandbox plugin.

## Документация

Главная точка входа: [docs/README.md](docs/README.md)

Там разделены четыре независимых направления:
- Secure MCP Tunnel;
- Tunnel Observability GUI;
- isolation / access control;
- Sandbox GUI plugin.

Подробные исторические планы пока остаются в корне проекта и используются как source-of-truth для проектирования. В `docs/` лежит короткая эксплуатационная база и навигация по ним.

## Важно

Текущий нативный Desktop Commander имеет широкий доступ к HOST и не считается security boundary.
Observability GUI разрабатывается отдельно и не должен становиться обязательной частью рабочего tunnel path.
Sandbox GUI plugin — отдельный будущий capability surface и не должен автоматически давать HOST GUI access.
