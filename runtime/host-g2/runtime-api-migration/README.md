# G2/Repo runtime — deployed source и история

Текущие E38/E42/E43 status/pins в [guide](../../../docs/ISOLATION_GUIDE.md).
Guest entry default Preview; Repo run/control в этом каталоге — deployed AFTER,
old owner HOST retired. One-shot Stop helper нельзя повторять без новой оценки.
Нижние Candidate/NEXT/BLOCKED относятся к датам прототипов.

## E43 — scope принят, legacy HOST закрыт

[Итог E43](../../../docs/G3_G2_SCOPE_ACCEPTANCE_AND_HOST_RETIREMENT_2026-10-16.md).
[Stop-LegacyOwnerHost.ps1](Stop-LegacyOwnerHost.ps1),3127bytes/SHA557C3AEC…:
default Preview, exact SID/process/native timestamps/profile/EXE+launcher hashes, held original handles.
Actual Stop выполнен один раз; journal guard запрещает повтор. Это не migration HOST на другой EXE.
Old three PIDs/8080 gone; actual G2/Repo MCP/CLI работают. Runtime/config/ACL/AV/network не менялись.
E42 scope/runbook принят(scope). Candidate/BLOCKED/NEXT ниже — история стадий.

## Concrete scope и final runbook, E42

[Начальный scope/entry/stop/recovery](../../../docs/G3_G2_INITIAL_SCOPE_AND_RUNBOOK_2026-10-16.md)
подготовлены. Source/Public launcher SHA0638D14A…, gate146E60B0… и actual G2 EXE/chain pins совпали.
Default Preview и LaunchTest labels не менялись; runtime/config/ACL/restart0.
E42/P01 Candidate не принят; old HOST13520:8080 ещё работает. Next — решение по scope и отдельный
shared HOST retirement/after-check. Отдельная HOST runtime-only migration/helper не нужна.
E39 закрыл automatic discovery source gap; старые UNKNOWN/NEXT ниже — история, не текущая задача.

## Known Snapshot Broker boundary, 16 октября

[Test-G2BrokerQueueBoundary.ps1](Test-G2BrokerQueueBoundary.ps1), SHA94B18201…/4511bytes:
[E41](../../../docs/G3_OWNER_BRIDGES_RESIDUAL_REVIEW_2026-10-16.md). Actual G2 Windows AST/C#/probe PASS(scope):78 normal/C$ DENY5,6 own positives. No queue entries read/written, no snapshot/task/service/tunnel changes. Broker worker source/live hash match; user route stays outside independent Repo guarantee. P01 baseline Candidate не принят.

## Selected owner asset capabilities, 16 октября

[Test-G2SelectedOwnerAssets.ps1](Test-G2SelectedOwnerAssets.ps1), SHA805EF368…/6144bytes:
[E40](../../../docs/G3_SELECTED_OWNER_ASSETS_2026-10-16.md). Windows AST/C# and actual G2 probe PASS(scope):130 normal/C$ DENY5,15 own positive controls/cleanup. Seven selected files/two backup parents; no protected content or ACL writes, no restart.7.6 remains PARTIAL overall; avoid repeating existing root/runtime matrices.

## Repo live rollout, 16 октября

[E38](../../../docs/G3_REPO_RUNTIME_CUTOVER_2026-10-16.md): Repo run/control AFTER, backup identity сохранена; selected old stop и pinned narrow start выполнены. Actual MCP/control/health/metrics и guest selected admin GET404 проверены. HOST/G2/container не перезапускались. Source collector explicit listener UP/initialized, auto-discovery UNKNOWN; installed dashboard не проверен. Старые Preview-only/NOT_APPLIED ниже — история соответствующих стадий. Новый Apply/restart без причины не нужен.

## Actual Repo profile shape preflight, 16 октября

[repo-profile-shape-preflight.mjs](repo-profile-shape-preflight.mjs) и
[test-repo-profile-shape-preflight.mjs](test-repo-profile-shape-preflight.mjs):
[E37](../../../docs/G3_REPO_PROFILE_PREFLIGHT_2026-10-16.md), pins и ограничения в evidence.
Шесть synthetic cases PASS; actual Windows profile разобран локально без credentials resolution.
Проверенные conflicts не выявлены; fixed CLI command precedence подтверждён source.
Это не native validation или live rollout. Current Next — согласие на два Repo файла/Repo-only
interruption, затем E36 guarded Apply и native acceptance. HOST/G2 не менять.

> Продолжение 2026-10-16: после user reboot G2 вручную запущен в guest Session2; MCP/CLI SID1009/non-admin подтверждены. В 02:36 approved corrected browser repeat PASS(scope): CDP/DOM/storage/reload, default sandbox и temporary cleanup. Own window и authorized guest clipboard marker/cleanup PASS(scope), E22; E21 fresh-open owner GUI scope и E22 selected owner DUP_HANDLE DENY подтверждены; E23/E24: selected G2 handle walk и launch/inheritance review завершены; 2.6 PARTIAL, concrete brokers/owner API остаются; stop/recovery позднее закрыт E28. Уточнение 03:35: G2 заменяет owner HOST; отдельная HOST runtime-only migration/helper NOT REQUIRED NOW. E26 current ACL regression PASS(scope); E28 normal stop/restart и E29 controlled peer failure PASS(scope), real G2 unchanged. Exit0 runtime не доказывает MCP task success. E30 selected service metadata/source review: 5.4 PARTIAL, live controls не отправлялись. E31: synthetic namespace5.6 PASS(scope). E32: восемь runtime объектов, 24 read ALLOW/104 mutation DENY5 через alternate paths; 5.7 PASS(scope), owner assets/backups7.6 отдельно. E33: selected owner cmd/Node без TCP listeners; known owner HOST/Repo APIs остаются, 5.8 PARTIAL. E34 Repo-only Preview выполнен: два BEFORE файла/pins/parser PASS, ReadyForApply=false. E35 stdio source review завершён: предполагаемый raw MCP/Docker error→readyz путь снят, reviewed metric producers без stdio params/results; bridge hashes match. E36 Repo-only guarded wrapper/core и recovery готовы, Windows fixtures32/32 PASS и actual owner default Preview BEFORE; live Apply/Rollback/restart нет. Next — bounded effective-config/compatibility preflight и согласованный Repo-only cutover; final G2 takeover отдельно; без повторения пройденных tests. Прежний HOST пока не остановлен, Repo остаётся отдельным. Для актуального NEXT и границ см. [рабочий порядок](../../../docs/G3_GUEST_MCP_WORKFLOW_2026-10-15.md). Старые PID и тогдашние NEXT ниже — датированная история.


## Repo-only guarded migration, 16 октября

[Invoke-RepoRouteMigration.ps1](Invoke-RepoRouteMigration.ps1), SHA AE249350…; [RepoRouteMigration.Core.ps1](RepoRouteMigration.Core.ps1), SHA46CEE432…; [Test-RepoRouteMigration.ps1](Test-RepoRouteMigration.ps1), SHAD202109B….
[E36](../../../docs/G3_REPO_GUARDED_MIGRATION_2026-10-16.md): Windows32/32 fixture assertions, partial recovery/contention PASS; actual default owner Preview BEFORE/zero writes. [Local recovery](../../../docs/G3_REPO_RUNTIME_ONLY_RECOVERY_2026-10-16.md). Core принимает fixture paths для тестов; production wrapper фиксирует два Repo targets и owner SID. Live Apply/Rollback не выполнялись. Не применять all-three helper.

## Repo stdio read-surface review, 16 октября

[E35](../../../docs/G3_REPO_STDIO_READ_SURFACE_2026-10-16.md): main stdio skips startup/OAuth HTTP probes; reviewed metrics без stdio params/results; bridge source/installed hashes совпали. Source-only, не Windows rollout. Позднее E36 реализовал two-file helper; native compatibility/preflight остаётся.

## Repo-only protection Preview, 16 октября

[Get-RepoApiProtectionPreview.ps1](Get-RepoApiProtectionPreview.ps1), SHA424250FC…: [E34](../../../docs/G3_REPO_API_PROTECTION_PREVIEW_2026-10-16.md).
Actual Windows PreviewComplete=true, ReadyForApply=false: hashes/parser двух файлов проверены. Только Preview; Apply/Rollback отсутствуют. Поля Unresolved этого helper фиксируют E34; stdio source-classification позднее завершена E35. Этот helper не является current security acceptance/Apply. Native compatibility и подготовка two-file apply/rollback остаются.

## Selected owner TCP metadata, 16 октября

[Test-G3SelectedOwnerTcpListeners.ps1](Test-G3SelectedOwnerTcpListeners.ps1), SHA0DEAF24A…: [E33](../../../docs/G3_SELECTED_OWNER_IPC_SURFACE_2026-10-16.md).
Exact owner fingerprints/hash metadata only; companion cmd witness в JSON. Known full API routes не исправлены; HTTP/owner writes/restart отсутствуют.

## Protected runtime namespace probe, 16 октября

[Test-G2ProtectedNamespaceCapabilities.ps1](Test-G2ProtectedNamespaceCapabilities.ps1), SHA40876E94…: [E32](../../../docs/G3_G2_PROTECTED_NAMESPACE_CAPABILITIES_2026-10-16.md).
Windows128/128 expected opens на восьми объектах. Shared-content/ACL writes и restart отсутствуют. 5.7 PASS(scope); personal assets/backups7.6 остаются.

## Namespace capability probe, 16 октября

[Test-G2NamespaceCapabilities.ps1](Test-G2NamespaceCapabilities.ps1), SHA8861428F…: [E31](../../../docs/G3_G2_NAMESPACE_CAPABILITIES_2026-10-16.md).
Windows135/135 expected opens; no content/ACL writes. Synthetic5.6 PASS(scope); real-target5.7 PARTIAL.

## Current synthetic failure case, 16 октября

[Test-G2SyntheticPeerFailure.ps1](Test-G2SyntheticPeerFailure.ps1), SHAE2CF3D49… и
[guest-runtime-peer-failure.js](guest-runtime-peer-failure.js), SHAFB8FD712…: [E29](../../../docs/G3_G2_SYNTHETIC_PEER_FAILURE_2026-10-16.md)
PASS(scope): synthetic MCP peer exit37, actual runtime exits0, Job fallback не потребовался, cleanup выполнен;
real G2 не менялся. Это одноразовый synthetic тест, не production launcher или новый transport.

## Подготовленные current-chain probes, 16 октября

[Test-G2CurrentRuntimeAcl.ps1](Test-G2CurrentRuntimeAcl.ps1): SHA5F5C5BC5…, actual G2 scoped runtime ACL regression PASS.
[Test-G2Lifecycle.ps1](Test-G2Lifecycle.ps1): SHA99482C33…, Capture/negative Verify и actual normal stop/restart Verify пройдены, E28; отдельный controlled peer-failure case принят E29, остальные failure modes этим probe не проверяются.
[Точный runbook и baseline](../../../docs/G3_G2_STOP_RECOVERY_2026-10-16.md). Оба probe не меняют runtime/ACL и не останавливают процессы.

## Актуальный scope

[План G2](../../../docs/G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md) и [CURRENT_STATE](../../../docs/CURRENT_STATE.md)
определяют оставшуюся работу и статусы. Runtime v0.0.15 уже установлен/испытан в документированном scope;
реальный прежний G2-only переход принят, owner HOST/Repo migration не применена.

`switch-launchers.ps1 -Mode Apply` меняет сразу три launcher files. Его нельзя использовать как
независимый one-route rollout. Actual Preview BEFORE уже получен; повторять его без drift/нового вопроса не нужно.
Перед consequential owner change требуется отдельный single-route Preview/backup/rollback и решение владельца.
Старый `start-g2-runtime.ps1` не доказывает принятие новой guest-session chain.

## Новый guest-session source, 15 октября

[start-g2-guest-session.ps1](start-g2-guest-session.ps1) — отдельный staged entry существующего G2,
с default Preview и отдельным LaunchTest. [Принятый рабочий порядок, pin, evidence и точный Preview](../../../docs/G3_GUEST_MCP_WORKFLOW_2026-10-15.md).
Repo проверки и Windows HOST compilation/own-session component checks пройдены; Public копия создана.
User-local guest Preview пройден: SID1009/Session2; точная LaunchTest команда — в рабочем порядке.
User-local старт выполнен; restricted G2 MCP/file/CLI в SID1009/Session2 при active console Session1 подтверждён.
Gate full path/hash совпал с Repo; source/test iteration, synthetic Git и scoped TCP/GET smoke пройдены.
История до approved browser repeat 02:36 (актуальный итог выше):
Own window PASS; clipboard SKIPPED_NONEMPTY, browser smoke частичный; corrected retest blocked by spawn EPERM, E20.
Точные current window-isolation sources/pins и следующий диагностический шаг — в рабочем порядке.
Owner boundary и long-lived G2 stop/descendants cleanup PENDING. Повторный LaunchTest не нужен.
[Test-G2OwnEntryArtifacts.ps1](Test-G2OwnEntryArtifacts.ps1) — read-only own-ancestry argv/artifact probe;
source pin, проверки и доставка описаны в рабочем порядке. Он не меняет runtime и не является owner boundary test.
Не использовать исторический all-three Apply для этого запуска.

## Историческое описание bundle, 13 октября

Ниже сохранены состав, hashes и результаты той стадии. Старые инструкции применения и «текущий»
PID описывают датированный scope, а не разрешение на новый запуск или широкий переход.

**ISOLATED TEST PASS / PRODUCTION PENDING.** Полный scope, hashes, ограничения и порядок применения: [G3 evidence](../../../docs/G3_LOCAL_API_RUNTIME_2026-10-13.md).

Default `switch-launchers.ps1 -Mode Preview` не пишет файлы. Apply меняет ровно три pinned live-лаунчера, создаёт owner-private backup и не перезапускает туннели. Rollback требует recorded BackupPath; live Apply/rollback не тестировались. Существующие owner profiles и ключи не копируются.

Все команды runtime run включают пустой `--harpoon.additional-transport=`; doctor/init используют full client. Новый G2 launcher запускается только под SID 1009 non-admin; отдельный key вводит пользователь локально.

Synthetic fixture запускать из нового owner-private каталога с проверенным EXE в `artifact/tunnel-client-runtime.exe`. Он использует выдуманный key, synthetic YAML, loopback control plane и фиксированный echo, не читает реальные профили/секреты и завершает себя через 8 минут. В тесте inherited Harpoon transport намеренно включён, CLI flag его отключает. Fixture hash и реальные наблюдения сохранены в evidence JSON.

Owner HOST/Repo candidates не перенесены в live launchers. Standalone G2 launcher применён локальным запуском пользователя; текущая приёмка приведена ниже. Runtime установлен side-by-side, full binary сохранён. UI cards отключены прежним MCP wrapper; это отдельно от runtime admin UI/API.

## Актуальный G2-only scope, 2026-10-13 18:06 Asia/Bangkok

[G2-only handoff](../../../docs/G3_G2_ONLY_SWITCH_2026-10-13.md). Owner launchers не применять. Standalone G2 launcher исправлен: existing tunnel проверяется по SID, не порядку CLI flags. Старый hash 416DE2… — historical snapshot; current source/staged hash A0680EB311B1BE2C0F7C3B1F9A0362DAC9F69C59A01C0AC293C3F08626ECF8F4. Новый запуск ждёт локальный separate key; other routes не менялись.

## Actual G2-only switch, 2026-10-13 18:32 Asia/Bangkok

[Acceptance](../../../docs/G3_G2_RUNTIME_ACCEPTANCE_2026-10-13.md): standalone source/staged launcher A0680EB… выполнен пользователем, actual G2 runtime PID 28148 и native MCP работают; post-start acceptance PASS в scope. Owner HOST/Repo candidates не применялись, общий helper не запускался. G3 OPEN, G4 PENDING. Старые PENDING statements выше — историческая подготовка.
