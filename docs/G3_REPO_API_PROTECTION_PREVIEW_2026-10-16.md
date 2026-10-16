# G3 — Preview защиты Repo API, 16 октября 2026

> Продолжение [E35](G3_REPO_STDIO_READ_SURFACE_2026-10-16.md): stdio source review завершён; предполагаемый raw MCP/Docker error→readyz путь исключён для main stdio, reviewed metrics без params/results. Unresolved в Preview/helper ниже — датированный E34 snapshot. Current queue — в плане; ReadyForApply=false сохраняется из-за подготовки guarded rollout/native acceptance.

**Candidate: Preview выполнен; ReadyForApply=false. Переключение не выполнялось.**
[Структурированный E34](G3_REPO_API_PROTECTION_PREVIEW_2026-10-16.json).
G3 BLOCKED; G4–G6 не приняты. Итоговый HOST — G2; отдельной migration прежнего HOST здесь нет.

## Что проверено на Windows

Preview 2026-10-15T22:21:44.2688410Z подтвердил exact Repo PID22488/SID1001/Session1/creation fingerprint,
full EXE SHA1946DE55… и listener127.0.0.1:59183.
Narrow runtime SHA A922D372… совпал. Profile mapping переиспользует E25 по неизменному fingerprint.
Содержимое profiles/keys/argv/env и HTTP bodies не читалось. Разрешённые launcher/control файлы
прочитаны локально для hashes и parser; их текст в отчёт не экспортировался.

| Назначение | Live файл под C:\Users\alexa\chatgpt-repo-mode | BEFORE SHA256 | Candidate SHA256 |
|---|---|---|---|
| Запуск | run-tunnel.ps1 | 3877266C3C97BECC82045BE16D994981EB4F8973353B285236DF9CAAC158A5A3 | 52848CDA49FECB4D78589E9979781A28D114A92F694CF75BC66EA6D4412EB93B |
| Управление | control.ps1 | E80E209B4758B194D2BCC7DCAFDFB83D296289E29A543F192E6726538641AE34 | 605F9D54A0A35FF3011DC44356A733F975A8993F1225FF53378A6B7880A193C5 |

Оба live файла BEFORE; Windows parser прошёл для live и candidate файлов.
Candidates лежат в `runtime/host-g2/runtime-api-migration/repo-run-tunnel.ps1` и `repo-control.ps1`.
Они не менялись в этом этапе. Preview не создавал backup и не менял live-файлы, runtime,
ACL, mounts, profiles, процессы или настройки защиты. HTTP requests=0.

## Что изменил бы уже существующий Candidate

| Компонент | Поведение Candidate | Приёмка и ограничения |
|---|---|---|
| Repo run | doctor остаётся full client; run использует установленный pinned runtime; additional Harpoon HTTP явно очищен | Удаление admin-модуля и stdio MCP проверены E08/E15. Actual retained Repo profile+Docker/MCP compatibility пока не проверена |
| Profile/key | Прежний repo-mode, прежний локальный файл ключа; Docker/MCP command сохраняется | Никаких credentials в Docker/GitHub и нового ежедневного ввода ключа этим вариантом не предусмотрено |
| Repo control | Распознаёт оба EXE; выбирает Repo по ID в metrics; stop сверяет PID/creation | При закрытии metrics новым gate/transport потребуется адаптация discovery/Start/StopAccess, иначе кандидат нельзя переносить без изменений |
| OpenPanel | Вместо full /ui открывает /health | Это изменение пользовательской функции. Нужность full UI пока неизвестна |
| Repo monitor | Source использует /metrics для Repo identity и /health?details=true для live/ready/uptime/mcp_state | Plain narrow runtime сохраняет эти routes. Source compatibility есть; installed monitor/native compatibility не приняты |
| HOST/G2/container | Этот Preview и будущий two-file scope их не изменяют | StopAccess останавливает Repo tunnel; StopContainer — отдельная операция и в этот переход не входит |

Monitor source `observatory/repo_monitor.py`: SHA9B15F9FD….
Его текущая Windows installation этим source review не доказана.
Сбой/UNKNOWN мониторинга после изменения API нельзя выдавать за сбой самого Repo tunnel.

## Проверка чтения: что удалось сузить

Narrow runtime удаляет admin UI/Codex/local управляющие routes из graph; это переиспользует
E08/E15. Но сохранение health TCP listener не устанавливает Windows identity.
В pinned исходнике `health.show-details=false` — default: `?details=true` его переопределяет,
а `/health/<component>` возвращает отдельный snapshot.

Health details имеют типизированные bounded projections: runtime identity/version/lifecycle,
MCP server name/version/capabilities/tool names и состояния/счётчики/время наблюдений.
В просмотренных healthstate shapes нет произвольных config maps, raw request/response payload,
ключей или полных upstream URL. Polling failure classification отдельно заменяет raw error категорией.
Это **не основание автоматически запрещать все health details**. Source shapes и поля нужно
оценивать по конкретным данным; bounded длина сама по себе не делает произвольную строку безопасной.

Остались два конкретных вопроса:

1. `/readyz` в ряде error branches добавляет `err.Error()`; sanitizer лишь TrimSpace.
   Возможность появления чувствительного error text именно у retained stdio Repo не установлена.
   Это source Risk/Evidence Gap, не подтверждённая утечка личных данных.
2. HTTP metrics helper сохраняет `URL.EscapedPath()` в `http.route`, без query.
   Другие labels включают tunnel ID, operation/status и Harpoon label. Состав фактических
   reachable metrics и чувствительность путей/labels для этого profile не доказаны целиком.
   Нельзя объявить ни «все metrics опасны», ни «все metrics безопасны» по имени endpoint.

Live owner bodies, exports/streams и mutating methods для этого не вызывались.
Нет основания повторять весь MCP/browser/clipboard/ACL fixture или делать полный аудит Windows.

## Развилка и следующий достаточный объём

| Вариант | Польза | Цена/условия | Статус |
|---|---|---|---|
| Официальный runtime + допустимая диагностика по существующему TCP | Убирает admin-модуль; сохраняет прежний monitor/control с небольшим two-file изменением | Сначала адресно завершить оценку readyz/metrics в этом stdio сценарии и native compatibility. Safe diagnostic ALLOW допустим | Меньший Candidate; не готов к Apply |
| Защищённый local health channel/auth gate при доказанно чувствительных ответах | Может закрыть чтение чувствительных ответов для guest | Windows compatibility и реальная граница ещё не доказаны; меняются launcher/control/monitor. Unix-socket option существует в source, но его Windows ACL protection этим не проверена | Conditional; не выбран и не внедряется автоматически |

Первым действием остаётся адресный разбор происхождения startup errors и metric labels для
существующей Repo stdio цепочки. Если исходника недостаточно — один synthetic error/marker test,
без настоящего profile/key и private owner payload. Затем выбрать меньший достаточный вариант.
При безопасном составе не добавлять новый broker/build/auth только ради полного запрета диагностики.
При чувствительных ответах нельзя принимать простой runtime swap за полную privacy protection.

## Candidate Execution / Verification Plan

1. Закрыть указанные read-surface вопросы, переиспользуя E08/E15 и просмотренные typed health fields.
2. После выбора варианта подготовить независимый Repo-only apply/rollback для точного набора файлов.
   Текущий all-three helper не использовать. Новый apply/rollback в E34 ещё не реализован.
3. До первой записи сверить live/candidate/runtime pins и private owner-local backup двух файлов.
   Proposed backup root: `%LOCALAPPDATA%\FortisRepoApiMigration\<nonce>`.
   Сохранить exact bytes/hashes и manifest стадий; backup сейчас не создан.
4. При drift либо частичной записи прекратить переход, отразить фактическое состояние.
   Rollback должен восстанавливать только эти два файла, проверять backup bytes и before/after hash,
   не затирать посторонние изменения и ничего не перезапускать автоматически.
5. До согласованного прерывания иметь локальную инструкцию восстановления: только StopAccess
   выбранного Repo, проверенный launcher либо восстановленные два файла. Контейнер и HOST/G2 не останавливать.
6. После отдельно согласованного single-route перехода проверить actual Windows runtime/profile/Docker/MCP,
   выбранную границу dangerous routes/read surface и monitor/control. Общий full tests × methods повтор не нужен.
   Native Repo compatibility и rollback acceptance пока не проверены.

Нельзя обещать длительность interruption или считать обычный runtime exit0 успехом MCP (E29).
Новый mount, Site, tunnel, supervisor, ACL/network/автозапуск и owner HOST migration не входят в этот Preview.
Защита Repo API не ограничивает independent Repo RW mounts; whole-chat guarantee остаётся отдельным 1.4.

## Воспроизводимость

[Get-RepoApiProtectionPreview.ps1](../runtime/host-g2/runtime-api-migration/Get-RepoApiProtectionPreview.ps1),
4058 байт, SHA256 `424250FC7F2240CBC5F35AF47E82746DF3323193B74828DCBE779A319C98BF23`.
Только Preview, без Apply/Rollback. Repo AST PASS; actual Windows PreviewComplete=true.
Source проверен SHA в памяти, owner disk copy не создавалась.
Повтор нужен только после drift/нового Candidate либо непосредственно перед выбранным изменением.

## Первичные исходники

Все исходники закреплены на commit a390c168ff1b2d14e73a95991c186c6aba3ff5a0.
Blob IDs и ссылки сохранены также в JSON; это source review, не attestation установленного binary.

- [pkg/runtimeconfig/config.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/runtimeconfig/config.go), blob `a724464b28ed9684da6c8f6573474afd82c0e559`.
- [pkg/runtimehealth/health.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/runtimehealth/health.go), blob `dac598f1c816adf81261255c295d2a3ee30f89bc`.
- [pkg/runtimehealth/components.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/runtimehealth/components.go), blob `d05674e821cf1c7e71a5874908a38a42693d8333`.
- [pkg/healthstate/health.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/healthstate/health.go), blob `4164b16b43913dc7b28bf1ac7da1f3c428643d73`.
- [pkg/healthstate/mcp.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/healthstate/mcp.go), blob `7ce260efc99af280d20a285bb26ffbd2a2749638`.
- [pkg/healthstate/operations.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/healthstate/operations.go), blob `a2b48c1e85754766cb54e72e37fa4efd4da68ba9`.
- [pkg/healthstate/optional.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/healthstate/optional.go), blob `b15234d1bba53098461a75c210c004ab2f71fdf3`.
- [pkg/controlplane/internal/health.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/controlplane/internal/health.go), blob `b1f69dc5307a8f0018a42e3bf744125e7ed3e03b`.
- [pkg/metrics/http_attributes.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/metrics/http_attributes.go), blob `c68f20413b96c6942e7ff572e83c42f43f234de8`.
- [pkg/metrics/fxmodule.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/metrics/fxmodule.go), blob `1dfe3ebf096910428ce675510e0e3b6d23af414b`.
- [pkg/runtimeharpoon/metrics.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/runtimeharpoon/metrics.go), blob `360b3cb6d4b06207e67695f159f13a8b132aaf51`.
- [pkg/mcpclient/probe_state.go](https://github.com/openai/tunnel-client/blob/a390c168ff1b2d14e73a95991c186c6aba3ff5a0/pkg/mcpclient/probe_state.go), blob `543ecafee7b3ebe454359f3b297a1fee788fa487`.
