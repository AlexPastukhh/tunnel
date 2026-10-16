# G2 — контролируемый аварийный выход MCP-процесса, 2026-10-16 04:30

**8.4 PASS(scope): один обоснованный failure case проверен. G3 BLOCKED; G4–G6 не приняты.**
[Structured evidence E29](G3_G2_SYNTHETIC_PEER_FAILURE_2026-10-16.json).

## Сценарий и польза

E02 завершал test Node с bounded wait/fallback termination; E28 проверил normal manual stop/restart.
Оставался вопрос: завершится ли установленный runtime сам, если его MCP-процесс неожиданно выйдет.
Проверка выполнена в guest SID1009/non-admin/Session2 на pinned runtime A922D372…:
локальный synthetic control plane, вымышленный ID/key, synthetic MCP Node.
Настоящие G2 profiles/keys/Desktop Commander не использовались в fixture.
Новый туннель/подключение не создавались; файлы или настройки работающего G2 не менялись.

Тест сначала выполнил initialize/list/echo, затем тестовый MCP намеренно завершился с кодом37.
Runtime должен был завершиться самостоятельно. Kill-on-close Job охватывала только новые test processes
как bounded cleanup fallback. Успешная принудительная cleanup не засчитывалась бы как runtime PASS.

## Наблюдения

| Свойство | Результат |
|---|---|
| Synthetic echo до failure | PASS |
| MCP peer PID19520 | Exit37 |
| Runtime PID23188 | Самостоятельный exit0 |
| Fixture Node PID19468 | Exit0 |
| Job перед cleanup / после | Active0 / Active0 |
| Принудительная остановка Job | Не запрашивалась |
| Записанный control port64049 после | Не слушает |
| Временный fixture root | Удалён после проверки marker/reparse/bounded scope |
| Работающий G2 25920→18956→32272 | Exact SID/session/creation fingerprints до/после совпали |

Health URL file был уже удалён runtime к моменту exit; health port отдельно не записан.
Не выдавать проверку control port за отдельный health-port probe. Завершение всего test Job подтверждено.

## Finding и практическое последствие

При аварийном peer exit37 runtime вернул exit0. Нулевой код runtime сам по себе не означает, что
MCP-задача выполнена успешно. При неожиданном завершении проверить ответ самой задачи и доступность
G2; для ручного восстановления использовать уже проверенный pinned launcher.
Это не основание менять установленный runtime, owner HOST, AV или добавлять restart engine.

## Принятый scope и ограничения

Вместе с E28 закрыт normal stop/manual recovery и один controlled MCP-peer failure case (8.4).
Это не аварийное завершение actual Python/Desktop Commander или самого runtime.
Все возможные descendants, logoff и произвольные длительные workloads этим не проверены.
Дополнительный fault test нужен при конкретной оставшейся угрозе, а не ради полного перебора.

Sources: [PowerShell wrapper](../runtime/host-g2/runtime-api-migration/Test-G2SyntheticPeerFailure.ps1),
SHAE2CF3D49… (9983 bytes); [worker](../runtime/host-g2/runtime-api-migration/guest-runtime-peer-failure.js),
SHAFB8FD712… (8023 bytes). Repo syntax/AST/C# compile и exact delivery/readback прошли.
Рабочий G2 не прерывался, повторный ввод ключа или ручной вход не понадобились.
