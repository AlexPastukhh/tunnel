# Обновление инструкций после изменений

## Навигация по повторяемым задачам

Guard/reconnect сценарии — [локальный реестр](use-cases/README.md), общий
workflow — главный реестр Fortis из `/workspace/repo/README.md`.
Документационные изменения сами по себе не требуют Windows copy/restart,
image build или повторного запуска Guards; применение runtime — отдельный шаг.

## Текущая карта source/deployed (2026-11-02)

Для Repo1/Repo2 актуальная Windows worker chain и общая Guard policy находятся в [`runtime/windows-repo/current/`](../runtime/windows-repo/README.md); общий policy module — `current/launchers/shared/FortisContainerPolicy.ps1`. `tunnel` владеет workers и Guards. `script-control-center` владеет UI, thin adapters, resolver и paired Windows updater — см. его [README](https://github.com/AlexPastukhh/script-control-center/blob/main/README.md) и [Windows update runbook](https://github.com/AlexPastukhh/script-control-center/blob/main/docs/GIT-WINDOWS-SOURCE-OF-TRUTH.md).

Windows profiles, keys, ACLs, Tunnel Client binaries, shortcuts and logs остаются вне Git. Публикация source не равна установке, Preview не равен live reconnect, а pull не перезапускает workers. Для Docker/worker restart trigger checklist — [FORTIS_GIT_WINDOWS_LAUNCHER_WORKFLOW](FORTIS_GIT_WINDOWS_LAUNCHER_WORKFLOW.md).

Следующие ниже датированные записи E38/E44, G2 и Bridge сохранены как история прежних этапов; **не использовать их Repo launcher paths и статусы как текущую Repo1/Repo2 инструкцию**.

## Repo1/Repo2 runtime resilience (2026-11-16; source-only)

The canonical shared policy targets narrow runtime v0.0.21; both launchers use the same diagnostic/runtime helper. The old response-POST EOF shutdown was reproduced with v0.0.15 and the corresponding v0.0.21 path passed in an isolated loopback fixture. Windows installation and live reconnect are separate from source changes. Binary verification, paired delivery, staged rollout and rollback: [runtime resilience](REPO-RUNTIME-RESILIENCE.md).

## Repo1 runtime diagnostics (2026-11-15; source-only)

Repo1 launcher source now exposes runtime stdout/stderr to Script Catalog and prints `RuntimeLog=` beside `RunId=`. Debug JSONL and `--log.http-raw-unsafe=false` remain enabled. The MCP logging-notification filter and shared Guard are unchanged. The paired Script Center resolver pins the updated manifest. Neither Windows source nor running workers was updated or restarted from Docker. Investigation and owner-local log readback: [Repo1 diagnostics](REPO1-RUNTIME-DIAGNOSTICS.md).

## Repo MCP guidance follow-up (2026-11-04; source-only)

`runtime/repo-mode/fortis-mcp-bridge.mjs` — legacy wrapper. Текущие Repo1/Repo2 workers запускают прямой Desktop Commander entry point и этот wrapper не вызывают. Исправление guidance в этом source mirror не меняет активные MCP descriptions и не требует Repo Tunnel restart. Unit tests: 4/4 PASS; schema check: 19 expected schemas matched.

Описание `start_process` формируется отдельно установленным Desktop Commander package: `server.js` добавляет `OS_GUIDANCE`, а `dist/utils/system-info.js` содержит generic path translation. Поэтому изменения legacy bridge не исправляют текущее описание `start_process`. Для этого нужен отдельный package-level candidate/deployment, затем reconnect Fortis Repo MCP и проверка live `tools/list` в ChatGPT. Подробности и source/installed hashes — [`runtime/repo-mode/README.md`](../runtime/repo-mode/README.md). Ни package deployment, ни runtime restart этой source-only правкой не выполнялись.

## Repo key rotation source-only (2026-10-16)

Добавлен `runtime/repo-mode/Rotate-RepoRuntimeKey.ps1` с owner-only Preview/Install/Rollback; PowerShell AST разобран без ошибок на Windows G2, но owner Preview/Install и rollback live не выполнялись. Старый ключ/файл/profiles/ACL/runtime не читались и не менялись в этом task. Новый ключ и отзыв — отдельно на OpenAI API Platform; `Install` нужен только после Preview и согласования Repo-only restart. Процедура [ACCESS](ACCESS.md), [OPERATIONS](OPERATIONS.md). G2 имеет отдельный ввод ключа при штатном ручном старте.

## Source-only audit reader (2026-10-16; не live deployment)

Изменения исходников observatory/activity_audit.py, server.py, app.js,
index.html, styles.css и тесты добавляют opt-in metadata-only наблюдение
для локального Desktop Commander tool-history.jsonl. Никакие persistent
credentials, mounts, ACL, G2 launcher и Repo Tunnel не меняются.
Точный командный текст только через интерактивный локальный CLI, не HTTP.
Порядок и ограничения: [observatory runbook](../observatory/README_DUAL_TUNNEL.md).
Mandatory JSON-RPC audit/writer, trusted chat correlation и long-term
retention ещё не реализованы. Не считать исходники установленным P1.

## Датированная история (сохранена без удаления)

### Scope принят, прежний owner HOST остановлен — E43, 2026-10-16

[E43](G3_G2_SCOPE_ACCEPTANCE_AND_HOST_RETIREMENT_2026-10-16.md): пользователь принял E42/P01
и разрешил выбранный old HOST Stop.13520/16092/24724 завершились,8080 не слушает.
After-check actual G2 SID1009/non-admin/Session2 и Repo MCP/CLI PASS; их process/listener
fingerprints сохранены, G2/Repo не перезапускались.
G3 bounded baseline ACCEPTED(scope); G4 initial Workspace policy ACCEPTED(scope); G5 полная personal-security программа не принята; G6 manual daily/normal recovery ACCEPTED(scope). Whole-chat1.4 PENDING; universal PASS не заявляется.
Credentials/connector не отозваны; local owner recovery сохранён, ручной relaunch снова откроет
широкий route. Новых ACL/mount/network/AV/task/service/автозапуск изменений нет.
Далее обычная работа G2/Repo; новые scopes/существенные изменения проверять адресно.
[Действующая инструкция E42](G3_G2_INITIAL_SCOPE_AND_RUNBOOK_2026-10-16.md).
Candidate/BLOCKED/NEXT ниже — датированная история стадий до E43.

> E42: [конкретный scope и final runbook](G3_G2_INITIAL_SCOPE_AND_RUNBOOK_2026-10-16.md) подготовлены, Candidate не принят. G2 chain/pins и old HOST recovery metadata сверены. Runtime/config/ACL/restart не менялись. Далее — решение о scope и отдельное согласование shared old HOST retirement, затем actual after-check. Не повторять достаточные E18–E41 tests; whole-chat/Repo RW отдельно.

> E41: [known Snapshot Broker boundary](G3_OWNER_BRIDGES_RESIDUAL_REVIEW_2026-10-16.md) PASS(scope):78 G2 DENY5,6 own positives, no messages/snapshot/controls/restart. MySQL NetworkService correction внесена без изменения raw E30. Residual P01 baseline — Candidate; next — конкретные scope/runbook/acceptance, затем согласованный old HOST retirement. Не автоматически universal IPC/service audit.

> E40: [selected owner assets проверены](G3_SELECTED_OWNER_ASSETS_2026-10-16.md):130 normal/C$ opens DENY5 на семи файлах/двух backup parents,15 own positives/cleanup PASS. Protected contents/ACL не менялись; actual key reference resolved only to path metadata, key bytes не читались.7.6 PARTIAL overall, root/runtime/lifecycle evidence не обнуляется. Далее — конкретные applicable IPC/broker/service остатки, без автоматического полного private/backup audit.

> E39: [source collector исправлен и проверен](G3_REPO_MONITOR_DISCOVERY_2026-10-16.md), Repo11 tests и Windows automatic UP/initialized без ручного адреса. Старый P1 не обновлялся/не запускался; tunnel restart не нужен. Исторический E38 auto-discovery UNKNOWN ниже больше не текущий статус проверенного source collector. Далее — применимые boundary/assets остатки по плану.

> Актуальная доставка E38, 2026-10-16: Repo live launcher/control применены, selected restart выполнен; actual narrow MCP/control/health/metrics и guest selected admin GET404 проверены. Backup identity — в [E38](G3_REPO_RUNTIME_CUTOVER_2026-10-16.md) и [recovery](G3_REPO_RUNTIME_ONLY_RECOVERY_2026-10-16.md). Monitor source collector explicit listener UP/initialized; auto-discovery UNKNOWN, installed dashboard не проверен. HOST/G2/container не перезапускались. Следующее — адресный monitor gap и применимые G2 boundary/assets остатки по плану. Более ранние утверждения «live Apply/restart нет» ниже относятся к E36/E37.

> Продолжение 2026-10-16: после user reboot G2 вручную запущен в guest Session2; MCP/CLI SID1009/non-admin подтверждены. В 02:36 approved corrected browser repeat PASS(scope): CDP/DOM/storage/reload, default sandbox и temporary cleanup. Own window и authorized guest clipboard marker/cleanup PASS(scope), E22; E21 fresh-open owner GUI scope и E22 selected owner DUP_HANDLE DENY подтверждены; E23/E24: selected G2 handle walk и launch/inheritance review завершены; 2.6 PARTIAL, concrete brokers/owner API остаются; stop/recovery позднее закрыт E28. Уточнение 03:35: G2 заменяет owner HOST; отдельная HOST runtime-only migration/helper NOT REQUIRED NOW. E26 current ACL regression PASS(scope); E28 normal stop/restart и E29 controlled peer failure PASS(scope), real G2 unchanged. Exit0 runtime не доказывает MCP task success. E30 selected service metadata/source review: 5.4 PARTIAL, live controls не отправлялись. E31: synthetic namespace5.6 PASS(scope). E32: восемь runtime объектов, 24 read ALLOW/104 mutation DENY5 через alternate paths; 5.7 PASS(scope), owner assets/backups7.6 отдельно. E33: selected owner cmd/Node без TCP listeners; known owner HOST/Repo APIs остаются, 5.8 PARTIAL. E34 Repo-only Preview выполнен: два BEFORE файла/pins/parser PASS, ReadyForApply=false. E35 stdio source review завершён: предполагаемый raw MCP/Docker error→readyz путь снят, reviewed metric producers без stdio params/results; bridge hashes match. E36 Repo-only guarded wrapper/core и recovery готовы, Windows fixtures32/32 PASS и actual owner default Preview BEFORE; live Apply/Rollback/restart нет. E37: actual named-profile shape preflight без выявленных conflicts, selected observer env overrides отсутствуют; fixed CLI command precedence source-reviewed. Профиль/ключи/live файлы не менялись; это не native Go validation. Next — конкретное согласие на два Repo файла и временное прерывание только Repo, затем guarded Apply/save backup identity, selected restart и native MCP/monitor/control acceptance. Final G2 takeover отдельно; без повторения пройденных tests. Прежний HOST пока не остановлен, Repo остаётся отдельным. Для актуального NEXT и границ см. [рабочий порядок](G3_GUEST_MCP_WORKFLOW_2026-10-15.md). Старые PID и тогдашние NEXT ниже — датированная история.


### Актуальный порядок для G2, 2026-10-15

Использовать [Candidate Execution / Verification Plan](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md) и [CURRENT_STATE](CURRENT_STATE.md).
Принятые пользовательские условия в плане действуют; незавершённые проверки не становятся PASS от сохранения документа.

| Сведения | Где поддерживать |
|---|---|
| Цель G2, разрешения гостя, защищаемая граница, подпункты/evidence и критерии | [Актуальный план](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md) |
| Последнее подтверждённое состояние и фактическая доставка | [CURRENT_STATE](CURRENT_STATE.md) |
| Причина выбора отдельной Windows-сессии | [Session decision](G3_SESSION_BOUNDARY_OUTCOME_DECISION_2026-10-15.md) |
| Общие auth/mount/key границы | [ACCESS](ACCESS.md) |
| Эксплуатация контуров и статус G2 entry | [OPERATIONS](OPERATIONS.md) |
| Предыдущие G2/G3 указания | [Архив](G2_G3_SUPERSEDED_GUIDANCE_2026-10-15.md#instructions) и датированные evidence |

- Правка только Markdown не требует native copy/restart, Site deployment или новых security tests.
- Не начинать G1/G2 заново; закрытые scoped PASS повторять только при drift/новом Evidence Gap.
- Проверочный user-local запуск конечной chain — испытание, production acceptance принимается отдельно.
- [Подготовленный GUI/clipboard diagnostic](G3_SESSION_GUI_BOUNDARY_DIAGNOSTIC_2026-10-15.md) имеет отдельный source pin и captured-bytes команды.
  OwnerWitness читает только metadata; GuestProbe создаёт свои test objects. Первый owner metadata запуск выявил ошибку desktop-name guard.
  Исправленный station-bound lookup/schema 2 с текущим pin прошёл Windows OwnerWitness; GuestProbe остановился на process-query prerequisite.
  Автономный recovery block в диагностической инструкции заново сверяет bytes и не зависит от переменных прошлого запуска; запускать целиком в свежей guest PowerShell.
  Действующий owner witness не повторять без истечения/изменения; конечная chain ещё не принята.
  Передача одного исходника через Public Documents не даёт guest доступ к owner Repos и не требует изменения ACL.
- Runtime/README и датированные scripts/pins — исходники/история, не разрешение выполнить старый Launch либо all-three Apply.
- Scope owner launcher/restart, ACL/mount/network/task/service изменений оформляется конкретно; сохранение документа не применяет их.
- JSON evidence, реальные outputs и hashes не исправлять ради нового статуса; новые выводы привязывать к прежнему результату и его scope.
- [Прежний G2/G3 preface и update log](G2_G3_SUPERSEDED_GUIDANCE_2026-10-15.md#instructions) перенесены из этой страницы без потери текста.

- [Принятый guest MCP рабочий порядок](G3_GUEST_MCP_WORKFLOW_2026-10-15.md): source подготовлен, guest Preview и user-local старт выполнены.
  Restricted G2 MCP/file/CLI smoke пройден: SID1009/Session2, active console Session1; точные pins/evidence — в рабочем порядке.
  Repo → G2 source/test итерация, gate full path/hash, локальный synthetic Git и scoped TCP/GET smoke пройдены.
История до approved browser repeat 02:36 (актуальный итог выше):
  Own window PASS; clipboard SKIPPED_NONEMPTY; browser smoke частичный, corrected source в Repo.
  E20 фиксирует spawn EPERM при доставке и ENOENT новых файлов; причина неизвестна, HOST event triage timeout.
  До Windows повтора установить причину отказа; не обходить другим маршрутом, не расширять env/права/защиту.
  Далее закончить 2.8/3.5; stop/owner boundary/full functional acceptance остаются.
  Изменение security acceptance методики остаётся Candidate; незакрытые gates не становятся PASS.
- [Review метода и Candidate Proposal P01](G3_GUI_BOUNDARY_METHOD_REVIEW_2026-10-15.md): ручной recovery/Native цикл на паузе по запросу пользователя.
  Сначала оценить достаточность verification и существующий guest G2 route; новые privileges/broker/autologon не подразумеваются.
  Это не отмена owner boundary и не PASS незакрытых G3 gates.

Не существует одной универсальной «инструкции плагина»: несколько слоёв принадлежат разным источникам. Менять источник нужного слоя и проверять доставленную версию.

| Изменение | Где править | Как доставить |
|---|---|---|
| Docker folders/network/identity | Фактический контейнер, workspace-config.json, probe.mjs | Проверенный recreate/config update, затем native Repo restart |
| Legacy Repo-mode bridge guidance | `runtime/repo-mode/fortis-mcp-bridge.mjs`, installed `/workspace/repo/.fortis/mcp-bridge.mjs` | Только если профиль явно запускает legacy bridge. Текущие Repo1/Repo2 workers используют direct Desktop Commander entry point; этот wrapper не участвует и его source update не требует Repo restart. |
| Current Desktop Commander `start_process` guidance | Installed package `server.js` (`OS_GUIDANCE`) и `dist/utils/system-info.js` | Отдельный package-level candidate/deployment, затем Fortis Repo MCP reconnect и live `tools/list` verification. Bridge source update это описание не меняет. См. [`runtime/repo-mode/README.md`](../runtime/repo-mode/README.md). |
| Native HOST launcher/env | trusted.cmd, profile, HOST launcher | Локальная проверка и restart HOST при необходимости |
| Native G2 / отключение встроенного UI | `runtime/host-g2/g2-stdio-gate.py` → тестовая Windows-обёртка | Self-test + MCP discovery; перезапуск только G2 с локальным вводом отдельного ключа, затем refresh tools. См. `runtime/host-g2/README.md` |
| Site MCP инструкции/tools/UI | Worker initialize.instructions, schemas/descriptions/_meta/resources, page/status | Existing Site source workflow → version → deploy |
| Site snapshot README/deployment/ | В том же Sites Git | Согласовать с runtime и опубликовать нужную Site version |
| App skills/onboarding/keywords | Plugin-owned files / metadata, точный canonical plugin | По update-plugin skill, не через случайный Site HTML |
| Текущая эксплуатационная документация | Этот checkout; актуальные определения у владельцев ниже | Сохранение + read-back/diff; при Git-публикации — отобранные commit/push и проверка remote HEAD |
| Snapshot workflow/policy | `docs/SNAPSHOT.md` — сценарий; `runtime/broker/README.md` — операции; Bridge runtime — исполнение | При смене поведения обновить эти источники и только затронутые подсказки в private snapshot-transfer. Не дублировать текущие разрешения/статусы между файлами; затем проверить опубликованные ссылки и readback |

### Порядок на нашей установке

1. Определить точные затронутые контуры и текущие версии. Не менять HOST при исправлении Repo. Не менять audience/export permissions попутно.
2. Обновить источник поведения и все зависимые утверждения: пути, доступ к internet, key reference, cwd, «что готово / что выключено». Удалить необоснованные default website/project предположения из onboarding, skills и runtime guidance.
3. Для native сравнить runtime/ копию с live path, сохранить backup вне Git, применить выбранные файлы и проверить gate. Внутренний volume не обновляется просто от изменения Windows исходника.
4. Для Site следовать Sites skill на существующем project_id; сохранить/развернуть точный source commit. Для App skills применять update-plugin только к реально поддерживаемому типу plugin.
5. При account-backed skill package update использовать текущий release, semantic version и expected_release_id (CAS); сохранять существующие App configs. После конфликта перечитать release, не перезаписывать чужие изменения. Это не замена процесса обновления native managed server.
6. Перезапустить нужный native child/Tunnel или дождаться Site deployment. Обновление Site не меняет native MCP; GitHub docs push не меняет ни один runtime.
7. Обновить подключение/инвентарь tools в ChatGPT при необходимости. Старые UI cards в истории чата могут сохраниться. Если новый tools/list всё ещё содержит старый outputTemplate/resourceUri — исправлять фактический источник presentation, а не только текст страницы.
8. Проверить доставленную версию: instructions, tools/list, schemas, отсутствие legacy UI attachments, status/один безопасный read-only вызов. Для owner HOST/Repo проверить прежний saved-key startup; G2 использует отдельную auth и принятый guest-local key workflow, без копирования owner key. После неопределённой мутации сначала inspect state.
9. Записать проверенный HEAD/version, чего не применяли, оставшиеся ограничения; обновить CURRENT_STATE/SITES/OPERATIONS и соответствующие source readme. Commit/push только намеренных файлов.

### Важный текущий долг

Repo Site версия 7 содержит прежние claims о /workspace/repo и deployment snapshot. При будущей публикации исправить их по CURRENT_STATE.md, не выдавая обновление native за активированный Site upstream.

Устаревший одноразовый `configure-tunnel.ps1` удалён 2026-10-11 из действующей установки и runtime/ после проверки отсутствия вызовов из активных скриптов. Уже зарегистрированный `repo-mode` продолжает использовать сохранённый `file:` key reference; обычный запуск выполняет `run-tunnel.ps1`. Новую регистрацию при необходимости оформлять отдельной проверенной процедурой, не перезаписывая существующий профиль. Ротация общего ключа HOST/Repo — отдельная операция по ACCESS.md, а не повторный `init`. Для удаления туннели не перезапускались.

### Как найти стандартную инструкцию

Использовать **sites:sites → site-mcp-server.md**, **plugin-creator:update-plugin → account-updates.md** и **plugin-creator:create-plugin → extensions.md**. Открыть текущую установленную версию перед операцией; команды и schemas из этих skills здесь намеренно не скопированы.

### История G2/G3

Прежние датированные updates сохранены [в архиве](G2_G3_SUPERSEDED_GUIDANCE_2026-10-15.md#instructions).
Актуальные указания и неисполненные шаги находятся в [плане](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md); не брать старый next-command из журнала.
