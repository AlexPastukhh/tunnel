# Prompt fragment — tunnel timeout recovery

Добавлять в инструкции чатам, которые работают через Fortis_M Secure MCP Tunnel.

```text
Если вызов инструмента через Tunnel не ответил или был остановлен по timeout, не делай вывод, что весь Tunnel недоступен, только на основании одного вызова.

Recovery policy:
1. Не выполняй записи/изменения, пока доступность не подтверждена.
2. Повтори ровно один лёгкий read-only вызов через Tunnel, предпочтительно get_config.
3. Если получена ошибка mcp_initialization_required / "MCP server is not initialized", считай это lifecycle/session failure, а не доказательством падения daemon. Сделай новый лёгкий read-only вызов после нового MCP handshake.
4. Если retry успешен — продолжай задачу и отметь, что был transient failure.
5. Если retry снова timeout/fail — сообщи: "доступность Tunnel для этого chat/session сейчас не подтверждена". Не называй глобальный Tunnel down без отдельного evidence.
6. Не перезапускай общий tunnel-client из-за ошибки одного чата, особенно если другие чаты продолжают работать.
7. Если доступен Tunnel Observatory, используй/запроси его состояние: live/ready, control-plane, MCP child, queue, dispatcher, response delivery, recent transport errors и 409 delta.
8. Если локальный Tunnel healthy, но этот чат не может вызывать tools, попроси пользователя refresh/reconnect именно app/connector в этом чате.
9. Глобальный restart Tunnel предлагай только при устойчивом локальном unhealthy/dead состоянии.
10. Не изображай успешное выполнение mutations, если tool result не был получен.
```
