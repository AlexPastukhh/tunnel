# Fortis G2 + Repo — хендофф новому чату

> **Архивный срез, до E44.** Это датированный хендофф, а не инструкция на сегодня. Упоминания отложенной актуализации документации и запрета commit/push описывают прежний этап. Сейчас документация E44 опубликована, а действующие границы — в [руководстве](ISOLATION_GUIDE.md), [CURRENT_STATE](CURRENT_STATE.md) и [E43](G3_G2_SCOPE_ACCEPTANCE_AND_HOST_RETIREMENT_2026-10-16.md). Git-публикация сама по себе не меняет Windows runtime.

Дата:16 октября2026, после09:12 Asia/Bangkok. Язык работы — русский.

## Сначала прочитать это

Пользователь попросил отложить полную актуализацию документации и подготовить этот хендофф из-за обрыва соединения/конца контекста. Полную актуализацию продолжать позже по его запросу. Сейчас не нужны новый security audit, runtime migration, restart или изменение прав.

Операционный переход уже завершён и документирован E43: G2 стал Windows-инструментом вместо прежнего owner HOST; Repo продолжает работать. Начальный scope принят с явными ограничениями. Последняя работа — привести общую документацию к этому результату и сохранить процесс для повторной настройки. Она НЕ завершена.

После последнего прерывания успешный read-only Repo вызов подтвердил: docs/ISOLATION_GUIDE.md, docs/G3_DOCS_CONSOLIDATION_AND_REPO_BOUNDARY_2026-10-16.md и .json НЕ существуют. Не считать E44 применённым или включённым в канонический реестр. Перед будущей записью снова проверить effect/чужие изменения.

## 1. Цель и принятое решение

G2 должен выполнять разрешённые Windows-задачи через отдельного обычного пользователя/отдельный Windows login: PowerShell, Python, Node, Git, установленные программы, необходимые API, собственные GUI/экран/clipboard, Edge/CDP, рабочие профили/state/results, сеть и собственные scoped credentials.

Защищаемая область — owner private data/credentials, ВСЯ GUI/clipboard alexa, включая обычные окна без elevation, shared runtime и опасные owner control interfaces. Не вводить запрет на собственную guest GUI/clipboard, headless-only, удаление полезного browser state или всей сети.

Ежедневный ручной вход в FortisHostG1 → local start → switch back в alexa с сохранённым guest login принят пользователем. Несколько минут в день допустимы, числового time gate нет. Autologon/SYSTEM broker/новый supervisor/Job/universal ACL manager не обязательны.

E41/P01 предложил bounded baseline: переиспользовать достаточные selected Windows/session/ACL/API/broker evidence и явно сохранить неизвестную полноту IPC/handles/bridges/services. E42 конкретизировал scope/runbook. В08:33:06 пользователь ответил «давай» на предложение принять scope и отдельно остановить общий old owner HOST. Это исполнено E43.

Статусы E43:
- G3 bounded baseline ACCEPTED(scope), не universal PASS.
- G4 initial Workspace policy ACCEPTED(scope), новые grants не выдавались.
- G5 selected assets PASS(scope); полная personal-security/backup программа не принята.
- G6 manual daily/normal stop/recovery ACCEPTED(scope) по E20/E28/E29/E42; arbitrary crash/logoff/descendants не приняты.
- Whole-chat1.4 PENDING для полной гарантии. Independent Repo RW и другие connectors сохраняют полномочия; @G2/инструкция модели не policy gate.

## 2. Контуры и обязательные рабочие правила

Основная разработка, поиск, рефакторинг, Git и docs — Fortis Repo. HOST/G2 только для необходимой адресной Windows-операции/приёмки. Не переносить bulk development на Windows из-за большого проекта или единичного MCP сбоя.

Проверенные пути:
- Windows checkout C:\Users\alexa\Repos\tunnel
- Repo checkout /workspace/repos/tunnel
- /workspace/repos — Windows Repos RW; /workspace/files — Windows Workfiles RW.
- /workspace/repo — отдельный internal Docker volume.
Запись в первые два сразу меняет Windows-файлы. Не путать пути, не создавать дубликат проекта/новые mounts.

Owner alexa SID:
S-1-5-21-303538662-3368424508-2654684973-1001
Guest FortisHostG1 SID:
S-1-5-21-303538662-3368424508-2654684973-1009
Последние owner Session1/guest Session2; номера динамические, не переносить как обязательные на новый login.

Перед правками — точный path/mounts, README/AGENTS, Git status. В checkout уже больше120 tracked/untracked изменений, включая удалённый старый configure-tunnel.ps1. Не reset/clean/stage/commit/push всё дерево; чужое сохранять. Commit/push не запрошены.

Не автоматизировать основной owner Windows desktop: screenshots, input, clipboard, windows/UIA и т.п. не разрешены. Собственные guest GUI/clipboard были явно разрешены в соответствующем scope.
Не читать secrets/private contents/upstream URLs без необходимости. Не переносить owner credentials в G2/Docker/GitHub.
Не менять ACL/mounts/network/AV/tasks/services/autostart и не запускать новые tunnels без отдельного решения.
Не перезапускать shared tunnel без согласования. Old HOST намеренно остановлен; не восстанавливать его для удобства docs.
Прямая передача целых файлов HOST↔ChatGPT максимум1,000,000bytes на логический набор в обе стороны, без обхода нарезкой. Обработка в Repo mounts на месте не ограничена этим лимитом.
No PASS без evidence; distinction source/Repo/native Windows/installed/published обязателен.
После timeout/обрыва/неясной мутации сначала effect check.
Не создавать subagents без явного запроса пользователя/применимых инструкций.

## 3. Что уже сделано и чем доказано

Канонический реестр сейчас E01–E43,58 decision rows:
docs/G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md
Current pointers уже обновлялись после E43, но общие ARCHITECTURE/ACCESS/OPERATIONS/runtime README местами всё ещё устарели.

| Evidence | Фактический результат / предел |
|---|---|
| E01–E06 | Initial G2 native/file/CLI/route baseline. Обнаруженный writable shared runtime исправлен owner: четыре scoped DACL; поздние effective checks PASS(scope). Старые FAIL сохранены как история |
| E07–E17 | Private-station/window prototypes, separate session и narrow runtime/source исследования. Private owner-session launch не решил Local mutex/Edge проблему; ordinary guest login выбран. Failed methods не обязательные повторные шаги |
| E18/E19 | Actual G2 Session2/SID1009/non-admin MCP/files/CLI, source iteration Repo→guest Workspace, gate argv/path/hash, synthetic local Git и scoped TCP/GET |
| E20 | Own window и corrected approved Edge/CDP DOM/storage/reload/default sandbox/temp cleanup PASS(scope). Initial EPERM/PDM/failed smoke сохранены |
| E21 | Four fresh-open owner station rights DENY5; six desktop paths blocked at station root,10 own positives. Не индивидуальная DACL каждого desktop |
| E22 | Authorized own clipboard marker/cleanup PASS; selected three owner DUP_HANDLE DENY с fingerprints. Bridge metadata не универсальное исключение |
| E23/E24 | Calibrated selected PSS handle walk;184 entries без type names/relative desktop names — limits. Ordinary cross-session handle inheritance unsupported по Windows contract; Python close_fds/source path reviewed. Не требовать полного Native audit без конкретной угрозы |
| E26 | Current runtime ACL:48 mutation DENY5/16 read ALLOW/12 own controls |
| E28 | Actual normal G2 stop/restart: old runtime/Python/Node и listener gone, новая pinned chain/MCP работает; owner neighbours сохранены |
| E29 | Один controlled synthetic MCP peer failure exit37; actual runtime exit0/cleanup. Не все failures, exit0 не означает успех задачи |
| E30/E41 | Selected service metadata/source review. MySQL80 реально NetworkService, не LocalSystem; E30 inference исправлен, raw сохранён. Matching MySQL handler custom branch status-only; GoodbyeDPI Stopped/LocalSystem, binding limits. Не live fuzzing |
| E31/E32 | Synthetic namespace135 expected opens; selected real-runtime8objects:24 read ALLOW/104 mutation DENY5 normal/extended/localhost C$. Не все personal files |
| E33 | Selected owner cmd/Node без TCP listeners, не все IPC |
| E35–E38 | Repo stdio source review, guarded two-file apply/recovery, shape preflight; actual approved Repo narrow rollout, native MCP/control/health/metrics, selected guest admin GET404 |
| E39 | Monitor discovery причина timeout3s; source deadline15/name filter/redacted reasons fix,11 tests PASS; actual automatic Windows UP/initialized5.594s без OBS_REPO_URL. Installed old dashboard не обновлялся |
| E40 | Seven existing owner assets/key-reference/launchers/backups/Edge Local State +two backup parents:130 normal/C$ DENY5;15 own positives/cleanup. Secret/browser/backup bytes не читались. Missing AWS slot не DENY |
| E41 | Known Snapshot Broker queue/control/parents78 denied opens/6 positives; worker source/live hash match; task owner Ready/Enabled/RunLevel0/no triggers. Queue requests/snapshot/task controls0. Repo намеренный route сохраняется |
| E42 | Concrete initial scope и exact entry/stop/recovery, source/Public pins, legacy HOST recovery подготовлены; после E43 помечены принятыми |
| E43 | Explicit user decision, selected old HOST Stop once, after-check через G2/Repo. Три old PIDs/8080 gone; G2/Repo fingerprints/listeners и native MCP/CLI сохранились |

PDM/AV trigger/true-false-positive не установлен.503/504 control-plane errors и AV события не доказаны одной причиной. Не открывать старый инцидент как отдельный обязательный G3 gate и не отключать Kaspersky.

## 4. Что сейчас запущено и что остановлено

Последний E43 after-check01:38:02Z (08:38:02 Bangkok):
- G2 runtime25920, created2026-10-15T21:01:23.7848810Z
- Python gate18956, parent25920, created21:01:24.1300680Z
- Node32272, parent18956, created21:01:24.3527150Z
- Все guest SID1009/Session2/non-admin. Runtime listener127.0.0.1:54647.
- Repo runtime31420, owner Session1, created2026-10-16T00:06:04.3124340Z, listener50385.
- Old owner HOST13520 → cmd16092 → Node24724 отсутствуют;8080 не слушает.
- Stop helper worker25304 завершился. Stop выполнен адресным Process.Kill, не Ctrl+C.
- Repo/G2/container не перезапускались этим Stop.

Old HOST profile desktop-commander, native ID tunnel_6ac4a7249a4081918eb0881c870acf07.
Repo native ID tunnel_6ac9e4dc9e688191ae1838e858424e8d.
Не требовать ID от пользователя, не создавать новые registration/Sites/tunnels.

Old HOST recovery:
C:\Users\alexa\Documents\prot\Start-Desktop-Commander-Secure-Tunnel.ps1
SHA0F644D4239E60886354EB83B6438CC888D8BDF3202B944B0304508E7C1336DFE
Full EXE C:\Tools\tunnel-client\tunnel-client.exe
SHA1946DE55A038313A9B9B2458D05FE1719FA9CF1F20A94DD5F38FC26A98BFDD42
Сохранены launcher/profile/key/connector; permanent revoke/невозможность relaunch не заявляются.
Не запускать его без осознанного решения владельца.

Stop source:
runtime/host-g2/runtime-api-migration/Stop-LegacyOwnerHost.ps1
3127bytes, SHA557C3AEC158C82CD0C1FFA63797F4A5A8FC1487A5920FEB422B012CF85264742.
Журнал docs/G3_LEGACY_HOST_STOP_ATTEMPT_2026-10-16.json Completed=true.
Exact PID/name/native-time/parent/SID/profile/EXE+launcher guards, held original handles; one-shot journal guard.
НЕ повторять/не удалять journal и не переносить скрипт вслепую на другую машину.
Первый Preview отказал до мутаций: CIM microseconds vs native100ns. Pins исправлены на реальные native timestamps, без ослабления equality.

## 5. Действующие source/deployment pins

| Артефакт | SHA256 |
|---|---|
| Guest entry start-g2-guest-session.ps1 |0638D14A92F78006526281BEC98C391FAD96F6C0F3F70D9C02475DA3A56C481D|
| Gate g2-stdio-gate.py |146E60B028276F871353A113571306002942461F0446E519A63B28DCC068418D|
| Narrow runtime v0.0.15 |A922D372D6BE0649156FBC1C8A040597F1F4BB5B4356890151D7875602593B1A|
| Guest Python3.13 |31FE10B4ED82A2F960AF0EF9931F46A4B84FF286F8B6FFD9DEE098CF4F10F17F|
| Windows Node |2FFE3ACC0458FDDE999F50D11809BBE7C9B7EF204DCF17094E325D26ACE101D8|
| Current Repo run-tunnel.ps1 |52848CDA49FECB4D78589E9979781A28D114A92F694CF75BC66EA6D4412EB93B|
| Current Repo control.ps1 |605F9D54A0A35FF3011DC44356A733F975A8993F1225FF53378A6B7880A193C5|
| Linux Bridge source/live |8389436658E22F213D9865A78872159E027CA33094999DB64CA96B5A7C79FC21|
| ACL source protect-shared-runtime.ps1 |0A7E0F496F314A7A5C272FEA9032DC6E4F274147E6E1AAEE3D2937E428CF5B76|

Guest Public entry:
C:\Users\Public\Documents\Fortis-G2-GuestEntry-0638D14A.ps1
Own gate:
C:\Users\Public\Documents\FortisHostG1Probe\RW\g2-stdio-gate.py
Own profile dir:
C:\Users\FortisHostG1\AppData\Local\FortisHostG2\profiles
Profile fortis-host-g2-test.yaml, Workspace рядом.
Narrow EXE:
C:\Tools\tunnel-client\runtime\v0.0.15\tunnel-client-runtime.exe
Node C:\Tools\desktop-commander-runtime\node.exe.

Current source Repo run/control находятся в runtime/host-g2/runtime-api-migration/repo-run-tunnel.ps1 и repo-control.ps1. runtime/repo-mode/run-tunnel.ps1/control.ps1 — older BEFORE copies, не deployed current!
Live Windows Repo C:\Users\alexa\chatgpt-repo-mode.
Bridge source runtime/repo-mode/fortis-mcp-bridge.mjs → live /workspace/repo/.fortis/mcp-bridge.mjs.
E38 recovery backup identity:
C:\Users\alexa\AppData\Local\FortisRepoApiMigration\a6d1e489e8b74a6dbbcc17978070641b\backup.json
SHA7234D724730813F5E50F8A7215054B851B3323C4A4759DD65C5E383F1B14766C
Exact recovery docs/G3_REPO_RUNTIME_ONLY_RECOVERY_2026-10-16.md. Live rollback не выполнялся; fixtures проверены.
Исторический all-three switch-launchers Apply НЕ использовать.

Current launcher default Preview, LaunchTest starts existing profile only; token/session-owner/WinSta0/Default/duplicate/lock checks. Key SecureString вводится локально; не provision заново. Keep guest console/login открытыми, normal stop Ctrl+C.
Source labels WindowsAcceptance=PENDING/ProductionAccepted=false фиксированные исторические labels, не dynamic acceptance registry. Не менять их ради вида PASS.
ВАЖНО: gate убирает OS env var. Preview current launcher нельзя выполнять через sanitized G2 MCP и объявлять Windows failure: он должен запускаться из local guest PowerShell. Для MCP platform probe использована [Environment]::OSVersion.Platform.
Same-SID gate/env hygiene не скрывает собственный G2 key от любого кода того же SID и не OS sandbox.

## 6. Repo под alexa: объяснение, уже данное пользователю

Docker — основная граница Repo. Windows launcher под alexa не выдаёт Linux-командам весь Windows token.
Repo narrow API уже применён E38, повторная аналогичная G2 migration не нужна.
RW Repos/Workfiles намеренно допускают изменение/удаление Windows-файлов; owner может позже запустить изменённый script. Это отдельный обычный файловый риск без container escape.
Возможные Windows-runtime/Docker vulnerabilities не исключены, но обязательная причина переносить Repo в guest не установлена. Полный Docker version/network/vulnerability audit не проводился.

Read-only metadata02:00:14.445750Z (09:00:14 Bangkok), НЕ новый security regression:
- UID/GID1000, CapInh/Prm/Eff/Bnd=0, NoNewPrivs1, Seccomp2.
- /var/run/docker.sock, /run/docker.sock, /dev/kvm absent. Не исключает все engine/network endpoints.
- /workspace/repos root /Users/alexa/Repos,9p,RW.
- /workspace/files root /Users/alexa/Workfiles,9p,RW.
- /workspace/repo ext4 volume, RW.
- Linux Bridge source/live hashes совпали.
Сохранено пока только /tmp/fortis-e44-container-metadata.json в Repo container и embedded в неприменённом пакете; канонического E44 ещё нет.

Официальные основания уже просмотрены:
https://docs.docker.com/engine/storage/bind-mounts/
https://docs.docker.com/desktop/setup/install/windows-permission-requirements/
https://docs.docker.com/engine/security/
Документация механизма не заменяет actual-machine evidence.

## 7. Задача актуализации документации — отложена, подготовка сохранена

Пользователь хотел:
1. Ясно описать результат, реальные изменения и проверки с пределами.
2. Исправить текущие pages, чтобы старые Candidate/BLOCKED/NEXT не выглядели действующим заданием.
3. Сохранить весь путь/обоснования/failed approaches и дать порядок повторной настройки похожей системы.
4. Не делать ради docs новые runtime/security changes, полный audit, restart или commit/push.

Выявленные конкретные дефекты:
- docs/ARCHITECTURE.md ещё пишет, что конечный guest G2 не принят; показывает исходный широкий HOST как current.
- docs/ACCESS.md требует при key rotation перезапустить оба owner профиля, хотя old HOST retired. Нужно проверять active Repo и НЕ запускать old HOST ради ротации.
- docs/OPERATIONS.md одновременно содержит E43 preface и старый непринятый G2/old browser failures; Repo /ui paragraph вводит в заблуждение. Current Repo OpenPanel=/health.
- runtime/README.md не различает deployed AFTER run/control и older BEFORE source copies.
- runtime/host-g2/README.md и window-isolation/README.md держат старый current BLOCKED/NEXT.
- docs/README.md reading order — огромная устаревшая лента до E41.
- CURRENT_STATE/workflow — append logs около53/66KiB. Нужно current summary + явно отделённая история, не потеря raw.
- INSTRUCTIONS — текущие instructions смешаны с историческими OwnerWitness/old blocks. Нужны ясное current owner facts/source table и отдельный historical section.
- FORTIS_G2_FULL_HANDOFF_2026-10-15.md исторический: требует сохранять old HOST, запрещает remote Windows checks той фазы. Добавить явный superseded banner, не переписывать старые результаты.
- OBSERVABILITY: old HOST offline теперь ожидаемо; source monitor≠installed panel.

Подготовленные локальные файлы прежнего чата (новый чат НЕ должен считать эти пути автоматически доступными):
/workspace/scratch/ba354ea2ca73/fortis-docs-staging/ISOLATION_GUIDE.md — ранний явно помеченный draft.
/workspace/scratch/ba354ea2ca73/fortis-docs-staging/ISOLATION_GUIDE.ready.md — candidate ready content, НЕ repo-applied.
/workspace/scratch/ba354ea2ca73/fortis-docs-staging/apply_docs_update.py — полный НЕПРИМЕНЁННЫЙ пакет правок,67731bytes.
Bundle SHA04a73bebb1a05b703e009c1f512941c964c60e7547ca3fc2b0349900a353aef7.
Python ast.parse PASS; выполнение на Repo и semantic/link validation ещё НЕ прошли.
.template.py — источник сборки пакета, не самостоятельный runnable updater.
Копии guide/bundle приложены к handoff ZIP; для нового чата пользователь должен прикрепить ZIP/файлы.
Не полагаться на functions.store/load предыдущего чата: они могут исчезнуть.

Пакет содержит:
- New docs/ISOLATION_GUIDE.md: результат, evidence map, chronology,10 reproduction steps, source links, limits, отсутствие universal one-command installer.
- New E44 MD/JSON: dated Repo process/mount metadata и docs consolidation receipt.
- Targeted current-page updates, historical content сохраняется/заголовки понижаются вне code fences.
- Canonical plan сохраняет58 rows и добавляет E44 только при реальном успешном apply.
- Cwd/UID/mount guard, drift guards expected single text, отказ при existing target/partial effect, pre-validation new links, snapshots /tmp, read-back и git diff --check.
- JSON verification receipt/hashes после фактического выполнения.

ВАЖНО: updater — подготовленный code candidate, не уже проверенный инструмент. Новому чату прочитать его и текущие inputs, проверить новые ссылки/терминологию. Если любой target уже существует — сначала effect/diff review, не снимать guard/не перезаписывать.
Без request продолжить не запускать полную актуализацию: пользователь сейчас её отложил.
У final guide формулировки «документы записаны» верны только ПОСЛЕ успешного apply, до этого файл candidate.

## 8. Проблема MCP-сессии — не чинить инфраструктуру вслепую

Repo иногда409 mcp_initialization_required: server требует initialize/notifications initialized текущего чата.
Один safe read retry не всегда помогает. Tool schemas сами operational initialize не предоставляют.
В01:52:19Z адресный G2 metadata query видел живой Repo31420/creation00:06:04.3124340Z и listener50385.
Пользователь повторно выбрал тот же Fortis Repo plugin в08:58; несколько Repo calls прошли.
При попытке большой docs write409 повторился, effect read тоже409. Потом пользователь прервал следующий exec.
ПОСЛЕ этого успешный Repo read показал все три new guide/E44 targets отсутствующими.
Техническая причина повторения не установлена. Не утверждать связь с размером payload, AV, Docker crash или выводом old HOST.
Не restart/reconnect всё, не менять plugin/architecture/privileges, не запускать old HOST.
Если Repo работает — обычные authorized операции. После error uncertain write сначала check actual file effect.

## 9. Быстрая навигация новому чату

Через существующий Fortis Repo проверить точный /workspace/repos/tunnel и прочитать:
1. README.md + AGENTS.md; docs/README.md; текущий верх docs/CURRENT_STATE.md.
2. docs/G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md — canonical criteria/status/evidence E01–E43.
3. docs/G3_G2_SCOPE_ACCEPTANCE_AND_HOST_RETIREMENT_2026-10-16.md + .json — latest completed operation.
4. docs/G3_G2_INITIAL_SCOPE_AND_RUNBOOK_2026-10-16.md — exact usable daily/recovery.
5. Для Repo: E38 G3_REPO_RUNTIME_CUTOVER и E39 G3_REPO_MONITOR_DISCOVERY.
6. Для нового вопроса — конкретный E-ID; не перечитывать все giant logs и не повторять весь audit.
7. При продолжении docs — attached guide/updater candidate и актуальные pages выше; проверить effect прежде apply.

Доступные tools находятся через functions ALL_TOOLS:
- mcp__codex_apps__fortis_repo_start_process, read_process_output — основной Linux Repo.
- mcp__codex_apps__fortis_host_g2___restricted_test__fortis_host_g2_restricted_test_start_process — guest Windows адресно.
- mcp__codex_apps__app_* — old owner HOST namespace может ещё отображаться, но runtime намеренно offline; не использовать его как active.
- fortis___repo_mode — отдельный Site, не fallback native Repo и не обязательная диагностика.
Fortis repo skill: c2/fortis-repo-workspace (или актуальный catalog alias); skill уже читался в старом чате.
Metadata tools иногда утверждают /workspace/repo only/noWindows mapping; это устарело, проверять реальные mounts.

## 10. Отчёт при завершении будущей актуализации

Указать: что записано в Repo/Windows checkout; что сохранено исторически; какие ссылки/status/read-back проверены;
что runtime/security settings не менялись; commit/push/deploy были или нет.
Не объявлять новый whole-chat/G5/universal security PASS.
Не создавать GLOSSARY/Work Context/новые планы или десятки повторных тестов без реальной потребности.
