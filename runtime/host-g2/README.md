# G2 — исходники и датированные результаты

## Current G2 после E43

Guest Windows login/non-admin bounded scope принят, old owner HOST остановлен.
Current [entry](runtime-api-migration/start-g2-guest-session.ps1) с default Preview
и [E42 runbook](../../docs/G3_G2_INITIAL_SCOPE_AND_RUNBOOK_2026-10-16.md).
Own GUI/clipboard/browser/state разрешены; private-station prototypes — исторические.
Machine-specific ACL source не универсальный installer.
[Итог](../../docs/ISOLATION_GUIDE.md).

## Датированная история (сохранена без удаления)

> Продолжение 2026-10-16: после user reboot G2 вручную запущен в guest Session2; MCP/CLI SID1009/non-admin подтверждены. В 02:36 approved corrected browser repeat PASS(scope): CDP/DOM/storage/reload, default sandbox и temporary cleanup. Own window и authorized guest clipboard marker/cleanup PASS(scope), E22; E21 fresh-open owner GUI scope и E22 selected owner DUP_HANDLE DENY подтверждены; E23/E24: selected G2 handle walk и launch/inheritance review завершены; 2.6 PARTIAL, concrete brokers/owner API и G2 stop остаются. Уточнение 03:35: G2 заменяет owner HOST; отдельная HOST runtime-only migration/helper NOT REQUIRED NOW. E26 current ACL regression PASS(scope); E28 normal stop/restart и E29 controlled peer failure PASS(scope), real G2 unchanged. Exit0 runtime не доказывает MCP task success. E30 selected service metadata/source review: 5.4 PARTIAL, live controls не отправлялись. Next — relevant boundary/protected paths/final G2 takeover; без повторения пройденных tests. Прежний HOST пока не остановлен, Repo остаётся отдельным. Для актуального NEXT и границ см. [рабочий порядок](../../docs/G3_GUEST_MCP_WORKFLOW_2026-10-15.md). Старые PID и тогдашние NEXT ниже — датированная история.


### Актуальная точка входа

[План G2](../../docs/G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md) → [CURRENT_STATE](../../docs/CURRENT_STATE.md) →
[операции](../../docs/OPERATIONS.md). Этот каталог содержит исходники-копии; сохранение Markdown не развёртывает runtime.

Прежний narrow G2 MCP PASS и UI metadata suppression относятся к описанному ниже scope.
Конечная chain в отдельной guest session ещё не принята. UI metadata disabled не запрещает guest OS GUI.
Ручной daily login допустим; private station/supervisor/Job/broker нужны только по критериям плана.
Не выполнять старый owner-session Launch или all-three migration Apply из датированной записи.

История до approved browser repeat 02:36 (актуальный итог выше):
2026-10-16: [E20 own GUI/browser smoke](../../docs/G3_GUEST_GUI_BROWSER_POSITIVE_2026-10-16.json) частичный;
own window PASS, clipboard untouched/nonempty, browser retest blocked by spawn EPERM.
Текущие diagnostic sources — в window-isolation; продолжение по рабочему порядку/CURRENT_STATE.

### Исторические записи — scope и дата обязательны

Ниже сохранён прежний текст после заголовка; слова current/latest относятся к времени записи,
а старые NEXT/PENDING/pins не заменяют актуальный план. Native код и JSON evidence этой правкой не менялись.

Дата проверки: 2026-10-13. Это тестовый native HOST под `FortisHostG1`; production migration не выполнена.

### Установленное изменение

- Live wrapper: `C:\Users\Public\Documents\FortisHostG1Probe\RW\g2-stdio-gate.py`.
- Резервная копия: `g2-stdio-gate.before-headless-20261013.py.bak` рядом с wrapper.
- `child_environment()` сохраняет прежний allowlist и принудительно добавляет `DESKTOP_COMMANDER_DISABLE_MCP_UI=1`.
- Ключи `CONTROL_PLANE_API_KEY`, `OPENAI_API_KEY`, `OPENAI_ADMIN_KEY` не передаются Node; self-test это проверяет вместе с флагом UI.
- Эта переменная поддерживается текущим установленным Desktop Commander 0.2.52 через `headless-mode.js` / `server.js`.

### Проверено до перезапуска

Под SID `S-1-5-21-303538662-3368424508-2654684973-1009`:
- Self-test: PASS — secret-related names absent; MCP UI disabled.
- MCP discovery с обновлённым окружением: 26 инструментов, 0 UI metadata, 0 ресурсов.
- Read-only `start_process: whoami`: `fortis_m\\fortishostg1`, без UI metadata в ответе.
- Эти проверки выполнялись до перезапуска в отдельном диагностическом запуске; результаты действующего маршрута приведены ниже.

### Применено и проверено по действующему маршруту

Перезапуск подтверждён 2026-10-13 в 12:27 Asia/Bangkok через действующий G2 MCP. Цепочка: tunnel-client PID 27324 → Python PID 16160 → Node PID 14112. Вызов команды исполняется как `FORTIS_M\FortisHostG1`, SID 1009, Administrator=false, `UI_DISABLED=true`, присутствующих имён secret env variables=0. Ответы команды и чтения `RW/marker.txt` не содержат UI metadata; synthetic marker прочитан успешно. Изменение применено к действующему G2. Уже сохранённые карточки истории этим не удаляются; при устаревшем tool inventory использовать Refresh существующего G2-плагина.

Проверен исходник установленного tunnel-client v0.0.15 (commit `a390c168ff1b2d14e73a95991c186c6aba3ff5a0`): EOF/выход stdio child инициирует остановку всего клиента; автоматический restart одного MCP child не предусмотрен. Поэтому child не завершали.

Откат: после остановки G2 восстановить только его wrapper из указанной резервной копии и снова запустить тестовый профиль. Старые HOST/Repo и их ключи не затрагиваются. G2 PASS и изоляция всей сессии этим изменением не объявляются.


G2-G завершён 2026-10-13: test process остановлен, headless source сохранён. Backup проверен на временной копии, live source не откатывали. Для продолжения G3 нужен новый локальный запуск с отдельным runtime-ключом. Подробности: ../../docs/G2_G_EVIDENCE_2026-10-13.md.

### G3 — 2026-10-13

G2 повторно запущен (tunnel 8452 / Python 5152 / Node 23140), UI disabled. До применения ACL G3 был остановлен на writable shared runtime C:\Tools; после применения runtime gate PASS. См. ../../docs/G3_READONLY_EVIDENCE_2026-10-13.md.
protect-shared-runtime.ps1 — скрипт согласованного ACL исправления, default Preview, syntax/Preview PASS. Apply выполнен вручную владельцем после согласия; live Rollback не выполнялся. Script сам не повышает права.
g3-readonly-access-check.cs содержит использованный helper для OpenService/CreateFile/AccessCheck без операций изменения.

### G3 — применение ACL и проверка 2026-10-13

protect-shared-runtime.ps1 -Mode Apply выполнен вручную владельцем после согласия. Четыре live DACL совпадают с backup After; G2 runtime mutation handles DENY, read/execute ALLOW; AccessCheck 22 758 objects без writable exceptions/errors. Live rollback не выполнялся.
g3-junction-probe.ps1 — архив успешного synthetic junction теста, cleanup подтверждён. g3-namespace-probe.py — own-token и extended/localhost UNC read probe; PermissionError errno 13 классифицируется как DENY.
G3 overall OPEN: owner localhost administrative API и прочие residual routes. Подробности: ../../docs/G3_POST_ACL_VERIFICATION_2026-10-13.md. Headless UI setting сохранён.

### Подготовленный local API переход, 2026-10-13 16:06 Asia/Bangkok

Официальный narrow runtime установлен side-by-side в защищённом tunnel-client дереве и проверен isolated stdio MCP / G2 HTTP / ACL тестами. [План и evidence](../../docs/G3_LOCAL_API_RUNTIME_2026-10-13.md); [bundle](runtime-api-migration/README.md). Default Preview PASS; live launchers, profiles и работающие туннели не переключены. UI cards остаются отключёнными через wrapper; whole-chat isolation и G3 OPEN.

### G2-only переключение, 2026-10-13 18:06 Asia/Bangkok

[Local handoff и evidence](../../docs/G3_G2_ONLY_SWITCH_2026-10-13.md): проверенный standalone launcher помещён в Public RW, duplicate guard исправлен и тестирован под SID 1009. Actual runtime switch PENDING local user key. HOST/Repo сохраняются. G2 — основа будущего итогового HOST, production acceptance отсутствует.

### G2 runtime принят в тестовом scope, 2026-10-13 18:32 Asia/Bangkok

[Post-start acceptance](../../docs/G3_G2_RUNTIME_ACCEPTANCE_2026-10-13.md): пользователь локально запустил runtime v0.0.15; PID 28148 → Python 19376 → Node 21812 под SID 1009. Native MCP, PS/Python/file RW/RO/DENY PASS; headless env и key stripping сохранены, own admin API/Harpoon отсутствуют в проверках. HOST/Repo процессы/launchers сохранены. Предыдущие PENDING statements — датированные исторические точки; текущий G2 работает. Общий G3 OPEN и G4 не принят.


### G3 baseline и совместимость, 2026-10-13 20:18 Asia/Bangkok

G2 file guard hot-applied: own Workspace RW plus C:\Tools\tunnel-client, C:\Tools\desktop-commander-runtime, C:\Tools\desktop-commander; runtime effective RO is enforced by existing Windows ACL, not this list. New temporary-profile headless Edge PASS; owner HOST/Repo unchanged, no restart. baseline-policy.json records scopes and limits; it does not apply ACL automatically. [History audit / matrix / extension procedure](../../docs/G3_BASELINE_HISTORY_AUDIT_2026-10-13.md).
G3 OPEN: G2 shares WinSta0 and currently has clipboard/screen/WRITE_DAC rights. No clipboard/screen data or live desktop ACL were touched. Whole-chat routes/owner local APIs/service/SMB gates remain separate pending acceptance; G4 production not accepted.


### G3 private window station prototype, 2026-10-13 21:13 Asia/Bangkok

[Evidence / local Preview](../../docs/G3_WINDOW_ISOLATION_PROTOTYPE_2026-10-13.md) · [prototype source](window-isolation/README.md). Synthetic non-admin private station, PS/Node/Edge-CDP and fresh handle deny PASS. Live owner WinSta0/default ACL unchanged; current G2 remains interactive. Preview-only source is staged, local elevated metadata inventory pending; no production private launcher/ACL Apply/Rollback implemented or accepted. HOST/Repo/G2 not restarted; G3 OPEN, G4 not accepted.


### G3 private launcher staged, 2026-10-13 22:35 Asia/Bangkok

[Evidence/local transition](../../docs/G3_PRIVATE_LAUNCHER_STAGING_2026-10-13.md) · [source](window-isolation/README.md). User elevated Preview complete; owner-controlled Start-G2PrivateWindow.ps1, protected preflight/pipe and owner-only CAS backup/rollback staged. Source parse/Preview and synthetic policy/env/job/pipe PASS. Credentialed cross-account launch/private runtime and actual main-window deny pending local password/key; no live ACL applied/restart/publication. Owner HOST/Repo preserved. Earlier prototype-only/pending inventory statements are historical. G3 OPEN, G4 not accepted.


### G3 Attach correction, 2026-10-13 23:00 Asia/Bangkok

[New pins/evidence/local retry](../../docs/G3_PRIVATE_LAUNCHER_ATTACH_FIX_2026-10-13.md). Caller-only scoped SeDebugPrivilege restored before resume fixes a source omission in cross-account Attach token inspection; native stage errors now explicit. First local attempt failed before key/ACL writes. Windows compile/AST/Preview and missing-privilege fail-closed test PASS, actual credentialed retry still local pending. HOST/Repo preserved; G3 OPEN, G4 NOT_ACCEPTED.


### G3 query-only token validator, 2026-10-13 23:19 Asia/Bangkok

[New pins/local retry/evidence](../../docs/G3_PRIVATE_LAUNCHER_QUERY_ONLY_2026-10-13.md). SeDebug fix retry still denied OpenProcessToken with unnecessary TOKEN_DUPLICATE. Query-only native SID/groups/elevation/primary/session checks staged and tested on actual current token without duplication; admin membership rejection strengthened. Actual credentialed SID1009 open/private runtime acceptance remains local pending; no owner window ACL applied. HOST/Repo preserved, G3 OPEN/G4 not accepted.


### G3 early preflight transport, 2026-10-13 23:43 Asia/Bangkok

[New operator/evidence/local retry](../../docs/G3_PRIVATE_LAUNCHER_PREFLIGHT_TRANSPORT_2026-10-13.md). Query-only Attach now returned in user retry; opaque pipe timeout prompted process-only Bypass and early PID-bound stage/error transport plus native exit polling. Same-account transport/Restricted/BYPASS/early-exit fixtures and Preview PASS; actual guest startup/CLI/Edge remain local pending, no main ACL applied. HOST/Repo preserved, G3 OPEN/G4 not accepted.


Дополнение 2026-10-13 23:57 Asia/Bangkok: limited client GW fixture denied connect (exit94), GRGW fixture result/PID binding PASS. Production pipe guest grant changed only GW→GRGW on random diagnostic channel; no key/password data, filesystem/window scope unchanged. Final operator 0CF2… pinned Preview PASS; actual guest transport/runtime/window ACL acceptance pending.


### Detailed verdict, 2026-10-14 00:10 Asia/Bangkok

[Diagnostic operator 2CB5…/local report](../../docs/G3_PRIVATE_PREFLIGHT_VERDICT_2026-10-14.md). Actual guest now reached Connected/WindowMetadata/NodeCliEdge but final predicate failed; report was hidden. Diagnostic-only report output added, guards/permissions/Supervisor unchanged; Windows Preview PASS. Exact failure pending local report; no live main ACL/runtime acceptance.


### Edge startup diagnostic — 2026-10-14 00:46 Asia/Bangkok

[Current exact pins/evidence/local retry](../../docs/G3_EDGE_STARTUP_DIAGNOSTIC_2026-10-14.md). User report isolates failure to Edge exit21 before CDP; guest SID1009/private station/CLI descendant/Workspace/runtime protection/cleanup pass in that synthetic scope. New D5ED… operator pins diagnostic Node 4A58…: own fresh-profile Edge stderr max4096, early exit, native profile-lock test and LABEL-only station/desktop plus own token integrity metadata. Default sandbox, Supervisor F619… and all permissions/guards unchanged.
Windows syntax/AST/metadata compile/owner synthetic lock test/pinned Preview PASS; main owner DACL hashes unchanged. Actual G2 diagnosis still requires fresh elevated local owner retry and masked credential, before runtime-key/main ACL stage. Owner HOST/Repo left running. Do not claim exit21 cause, live clipboard protection or accepted private runtime. G3/G4 remain open.


### Private object compatibility — 2026-10-14 01:11 Asia/Bangkok

[Current exact pins/evidence/local launch](../../docs/G3_PRIVATE_OBJECT_COMPATIBILITY_2026-10-14.md): operator 05B6…, supervisor E63C…, Node BE06… supersede D5ED…/F619…/4A58…. Actual report: ProcessSingleton failure, lock probe0, guest Medium; installed Edge cause still not proven. Staged guest private object masks restored to full 0xf037f/0xf01ff only inside new noninteractive private environment, correcting Chromium desktop-ACL clone compatibility and matching prior successful prototype. Guest can mutate these private object ACLs; main owner deny/CAS/job/identity/session guards and Edge sandbox unchanged.
Windows combined compile/AST/Node/Preview + memory ACL matrix PASS; main DACL hashes unchanged. Node now reports read-only existing startup-mutex open, own random mutex create and own private message-window Win32 errors. Main-station message-window guard tested=-1; no owner GUI/clipboard/screen or existing mutex modification.
Actual local credentialed G2 Edge preflight, main Apply and private runtime acceptance still pending; fresh elevated owner console required. Owner HOST/Repo preserved; no service/task/common runtime restart/publication/commit/push. G3 OPEN/G4 NOT_ACCEPTED.


### Handoff / latest named-mutex blocker — 2026-10-14 01:30 Asia/Bangkok

[Latest actual verdict and continuation](../../docs/G3_NAMED_MUTEX_BLOCKER_2026-10-14.md). 05B6… / E63C… / BE06… pins still current. Private message window0 and lock0; new own Local mutex5, startup mutex5, Edge21. Full private rights did not resolve blocker; exact namespace/token cause unproved. Main owner DACL still original in fresh Preview, no main Apply or private runtime acceptance. UI hiding already separate/completed; screen/clipboard false fields are no-read, not DENY.
Next: read-only named-object/token diagnosis and bounded demonstrated remedy before credentialed retry; keep owner HOST/Repo. Continue remaining G3 then G4–G6. No source, ACL, runtime, service/task, Docker/Site changes, restart, publication, commit or push for this handoff.
