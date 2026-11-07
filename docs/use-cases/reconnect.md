# Tunnel reconnect

## UC-TUN-002

**Когда:** необходимо переподключить/восстановить native Tunnel или Windows worker.

**Цель:** вернуть разрешённое native соединение без новой незапланированной среды.

**Как:** owner инструкции — [Tunnel operations](../OPERATIONS.md),
[Guarded Windows source](../../runtime/windows-repo/README.md).
[Current State](../CURRENT_STATE.md) — исторический срез, не текущий адрес/процесс.
Сначала read-only preflight exact identity и verification environment;
только отдельный owner-run authorised action меняет Windows/Tunnel. Не
выводить состояние Docker Gateway из исторических Tunnel logs.

**Готово:** соответствующие соединения и Guard identity подтверждены в их
реальной среде; возможные UNKNOWN названы явно.
