# G3 — Repo stdio: readyz и metrics, 16 октября 2026

> Продолжение: [E36](G3_REPO_GUARDED_MIGRATION_2026-10-16.md) реализовал Repo-only guarded helper и local recovery; fixtures/Preview проверены, live Apply/Rollback отсутствуют. Current queue — в плане; source выводы ниже сохранены.

**Адресный source review завершён. Прежний риск переноса Docker/MCP error в readyz
не подтверждается для проверенного stdio пути. Candidate не применён.**
[Доказательства E35](G3_REPO_STDIO_READ_SURFACE_2026-10-16.json).
G3 BLOCKED; G4–G6 не приняты. Windows-туннели, ACL и live launcher files не менялись.

## Что именно проверено

Разобран pinned commit `a390c168ff1b2d14e73a95991c186c6aba3ff5a0` для обычного runtime graph и
существующей команды Repo `docker exec -i fortis-repo-test node /workspace/repo/.fortis/mcp-bridge.mjs`.
Это продолжение E34, а не новый аудит всего клиента или Windows.

В Repo сверены source bridge `runtime/repo-mode/fortis-mcp-bridge.mjs` и установленная копия
`/workspace/repo/.fortis/mcp-bridge.mjs`: SHA256 обоих
`8389436658E22F213D9865A78872159E027CA33094999DB64CA96B5A7C79FC21`.
Файлы не менялись. Это привязка к текущему bridge в контейнере, не новая Windows acceptance.

## readyz: снятый предполагаемый путь

| Ветка | Что делает проверенный source | Вывод для Repo stdio |
|---|---|---|
| MCP startup probe | Для транспорта кроме HTTP-streamable устанавливает ProbeState без ошибки и возвращается до HTTP handshake | Ошибки Docker child, stdio responses и private tool results через этот probe в readyz не передаются |
| OAuth discovery | Для stdio discovery не запускается; записывается фиксированная причина disabled | Произвольного upstream error в этой ветке нет |
| OAuth readiness classification | Причина disabled распознаётся как optional failure | Она не становится raw sensitive readiness error |
| Обычный runtime CLI graph | Загружает normal runtime modules; CLI добавляет writer/logger, не новый readiness gate | Вывод ограничен этим graph; не переносить на HTTP MCP, cloudflared flavor или embedder extensions |

E34 верно заметил: общий sanitizer readyz лишь обрезает пробелы в error text.
Но для вывода об угрозе важна достижимость соответствующей error ветки.
Для разобранного stdio сценария source исключает указанный путь переноса Docker/MCP ошибки.
Отдельный synthetic error/marker test ради подтверждения той же ветки теперь не требуется.

Readyz200 всё равно не доказывает успешную MCP-операцию или живой stdio child.
Это ограничение диагностики, а не новая privacy проблема; E29 уже показал runtime exit0 после peer failure.
При native acceptance нужен настоящий MCP вызов, а не один health status.

## Metrics: что проецируют проверенные producers

| Источник | Поля/значения в metrics | Что не найдено в этой проекции |
|---|---|---|
| Control-plane HTTP | EscapedPath: известные routes с tunnel ID и возможным config prefix; HTTP statuses/timings | Request/response body и query через этот path helper не передаются |
| Dispatcher | Request kind/method, channel, tunnel ID, status, counters/latencies | Params и results MCP не берутся как metric labels в разобранной ветке |
| Repo main MCP | Docker stdio, без HTTP main transport | Содержимое читаемых файлов и tool arguments не превращается в HTTP route главного канала |
| Harpoon | Target label, status class, outcome, count/size/latency | CallEvent имеет URL/body/error, но рассмотренный metric recorder их не использует |
| Component health | Переиспользуется E34: typed bounded states/identity/tool-name projection | Не произвольная выгрузка config, key или call payload |

В source есть произвольное имя request method и настраиваемые prefix/labels.
Поэтому это не доказательство безопасности любого будущего profile и не полный аудит всех
OpenTelemetry/Prometheus dependency attributes. Нестандартные HTTP bindings и конфиденциальные
config/metric resource values нужно учитывать в действительной конфигурации, если они есть.
Private profile/environment/URL values в этом этапе не читались.

Из рассмотренного пути не следует необходимость запретить всю diagnostics поверхность.
Для обычного Repo stdio не найден источник автоматической публикации owner file contents,
MCP params/results или Docker stderr через разобранные readyz/metric producers.
Это source-scope вывод, не live leak test и не обещание для всех режимов.

## Решение о следующем объёме

Сохраняем меньший Candidate: официальный pinned runtime с допустимой диагностикой и существующими
Repo run/control candidates. Новый broker, auth-gate, custom build или Unix transport **не становятся
обязательными** по результатам этого review. Они остаются Conditional при конкретной доказанной потребности.

Следующий самостоятельный этап — подготовить Repo-only guarded apply/rollback для двух файлов:
`C:\Users\alexa\chatgpt-repo-mode\run-tunnel.ps1` и `control.ps1`.
Default — Preview; exact pins, отдельный private backup, drift refusal и проверка read-back.
Автоматические restart и общий all-three Apply не нужны. Перед реальным cutover должна быть
локальная инструкция восстановления при потере Repo connection.

В уже необходимый compatibility/preflight включить:
main stdio, отсутствие непроверенных дополнительных HTTP bindings, оценку нестандартных
route prefixes/labels/resource attributes при наличии, pinned normal graph и Harpoon override.
Это не новая самостоятельная серия аудитов. Если обнаружится конкретное отличие, оценить именно его.

Actual retained profile/Docker/MCP и monitor/control compatibility остаются непроверенными на narrow
runtime. E34 ReadyForApply=false сохраняется; source review E35 не разрешает live rollout.
Прежний HOST не переделывается; его согласованный retirement после G2 acceptance — отдельная операция.
Independent Repo RW mounts и owner data/backups7.6 не закрываются защитой этого API.

## Первичные исходники и ограничения

Все новые ссылки закреплены на одном commit; blob IDs — в JSON. Общие health/metric shapes
из E34 переиспользованы. Review не изменяет bytecode Windows binary и не является его attestation.

- [pkg/mcpclient/fxmodule.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/mcpclient/fxmodule.go), blob `a64c973ee1cc31af053768a858f59d12665e0023`.
- [pkg/mcpclient/transport_provider.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/mcpclient/transport_provider.go), blob `771fe3362238ed068d2e4e62cd5550b9ed0e9b08`.
- [pkg/mcpclient/channel_transport_factory.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/mcpclient/channel_transport_factory.go), blob `38262239efb7411a158e4828815e1db1ffc0cf5d`.
- [pkg/oauth/module.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/oauth/module.go), blob `8a1deed4e9a7c4b90be949a3ff2ae4fb3a00f806`.
- [pkg/oauth/discovery_failure.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/oauth/discovery_failure.go), blob `48379c6c6e3d8a86d2623b85a9a86fe0299950ef`.
- [pkg/controlplane/internal/tunnel_service_client.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/controlplane/internal/tunnel_service_client.go), blob `88d4b64d966159eb649675f07dae37762b00c026`.
- [pkg/dispatcher/internal/processor.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/dispatcher/internal/processor.go), blob `f22424ff353ca31ed31ea1a04415bf628f1811e4`.
- [pkg/runtimeapp/app.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/runtimeapp/app.go), blob `8dbaba54c0339da3ca2af54cf921164c835d9c48`.
- [cmd/client-runtime/root_command.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/cmd/client-runtime/root_command.go), blob `162a87b83d1a134d8f29f411d2c98009147473d4`.
- [pkg/runtimeharpoon/shared_wiring.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/runtimeharpoon/shared_wiring.go), blob `5c6496d7fa476c345859414492ffdd2cec8ba0c7`.
- [pkg/runtimeharpoon/fxmodule.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/runtimeharpoon/fxmodule.go), blob `79486e03ffe282b5f8092307ce30e444762d38c0`.
- [pkg/runtimeconfig/profile.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/runtimeconfig/profile.go), blob `ad80cdaca362bbdded5f712370351592d146bfe6`.
- [pkg/runtimeconfig/file_config.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/runtimeconfig/file_config.go), blob `fe27bd5f9f791a19a06bf164e1b89dbc7f099659`.

Не выполнялись новый Windows runtime fixture, owner HTTP calls, private body reads, deployment,
commit/push или изменения profiles/keys/ACL/network. Достаточные E08/E29/E34 tests не повторялись.
