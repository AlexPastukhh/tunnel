# Текущее состояние — датированный срез

> **HISTORICAL SNAPSHOT — 2026-10-16.** Дальнейшие разделы фиксируют E43/E44 на указанную дату. Они не являются текущим состоянием Fortis Repo на 2026-11-03 и не подтверждают нынешние Docker mounts, credentials или R7 deployment. Вход в действующую документацию:
[главный реестр Fortis](https://github.com/AlexPastukhh/fortis-container/blob/main/docs/use-cases/README.md).
Текущий Guard/source owner — [Windows Repo runbook](../runtime/windows-repo/README.md);
перед действием проверять live runtime.

## Текущее резюме E43/E44

**Принято E43:** G3 bounded, G4 initial, G6 manual; selected G5 PASS(scope).
Old owner HOST остановлен, native G2 и Repo в E43 after-check отвечали.
**Не принято:** full G5 и whole-chat1.4; unknown IPC/handle/clipboard/service completeness.
**Проверено E44:** Linux Repo UID1000/caps0/NoNewPrivs1/seccomp2,
Windows Repos/Workfiles RW, отдельный volume, Bridge source/live hash.
Не новый Windows security/daemon audit. [Итог](ISOLATION_GUIDE.md);
[E44 receipt](G3_DOCS_CONSOLIDATION_AND_REPO_BOUNDARY_2026-10-16.md).

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

### Начальный scope и итоговая инструкция подготовлены, 2026-10-16

[E42](G3_G2_INITIAL_SCOPE_AND_RUNBOOK_2026-10-16.md): конкретный Candidate scope — Workspace,
own GUI/clipboard/browser/persistent state/network и CLI; новые owner grants не нужны для старта.
Pinned guest entry/normal stop/recovery и отдельный retirement/recovery прежнего HOST записаны.
Actual G2 SID1009/non-admin/Session2, chain/pins совпали; profile/Workspace существуют.
Old HOST13520:8080 и recovery launcher прежние. G2 может читать selected process/listener metadata
для after-check без owner content/argv. Туннели/config/ACL не менялись и не перезапускались.
E42/P01 ещё не принят. Next — решение о scope, отдельно согласованный old HOST retirement,
after-check и scoped итог. Independent Repo RW/whole-chat остаются отдельными.
G3 BLOCKED; G4–G6 не приняты. Ниже — датированные результаты предыдущих стадий.

### Известный Broker проверен; остаток сведён к baseline decision, 2026-10-16

[E41](G3_OWNER_BRIDGES_RESIDUAL_REVIEW_2026-10-16.md): G2 non-admin/Session2,
known Snapshot Broker queue/control/parent78 normal/C$ opens DENY5,6 own positives ALLOW.
Queue messages/snapshot/service controls/task starts/restarts0. Installed worker/source hash match,
task owner SID1001 Ready/Enabled/RunLevel0/no triggers. Independent Repo queue route сохраняется.
Actual MySQL NetworkService; E30 LocalSystem inference исправлен, raw metadata сохранены.
Неустановленный installed-source binding и полнота всех IPC/handles/clipboard bridges — Limitations,
не основание автоматически делать universal scan/fuzzing. P01 bounded baseline — Candidate,
не новая accepted гарантия. Next — конкретный начальный scope/final runbook и решение о приёмке,
затем отдельно согласованный retirement старого HOST/after-check. G3 BLOCKED; G4–G6 не приняты.

### Выбранные личные assets и backup проверены, 2026-10-16 07:45

[E40](G3_SELECTED_OWNER_ASSETS_2026-10-16.md): actual G2 SID1009/Session2/non-admin.
Семь конкретных owner файлов: Repo profile/runtime key/run/control, backup E38, runtime ACL backup
и Edge Local State; два backup parents.130 normal/C$ capability opens DENY5, включая
parent DELETE_CHILD.15 own synthetic positive controls ALLOW; cleanup PASS.
Owner existence metadata и profile file-reference получены отдельно; key/browser/backup bytes
не читались и не хешировались. Стандартный .aws credentials slot отсутствует, не DENY.
ACL/grants/mounts/runtime не менялись; root/runtime проверки E05/E26/E32 не повторялись.
7.6 PARTIAL overall: selected scope принят, остальные private assets/backups и independent Repo
этим не принимаются. Для выбранных объектов ACL correction не требуется.
Далее — применимые конкретные owner IPC/broker/service остатки и достаточность baseline;
не добавлять произвольный private scan/restore audit без конкретного scope. G3 BLOCKED; G4–G6 не приняты.

### Автоматический поиск Repo исправлен, 2026-10-16

[E39](G3_REPO_MONITOR_DISCOVERY_2026-10-16.md): причина UNKNOWN подтверждена — Windows query
не успевал за3s; при diagnostic deadline15s тот же запрос завершился за6.516s.
Source collector теперь использует deadline15s, CIM filter только двух EXE names и отдельные
redacted failure reasons. Repo11 tests PASS; actual Windows automatic discovery5.594s:
UP, verified, MCP initialized, без OBS_REPO_URL.
Известная старая P1 копия repo_monitor.py не содержит; её installation/GUI не менялись.
Туннели/контейнеры не перезапускались. E38 source discovery gap закрыт; старые UNKNOWN ниже —
датированный baseline. Далее применимые G2 boundary/private-assets остатки по плану.
Установка панели/постоянные журналы — отдельные Proposals, не автоматические gates.
G3 BLOCKED; G4–G6 не приняты.

> После ручного перезапуска пользователя: проверка 2026-10-16 07:19 Asia/Bangkok подтвердила Repo PID31420, creation 2026-10-16T00:06:04.3124340Z, Session1, тот же pinned narrow artifact; listener127.0.0.1:50385, live/ready=true, MCP initialized и actual native Repo CLI UID1000. Проверяющий ничего не перезапускал. Старые PID24720/port65202 ниже — срез первого перехода. Auto-discovery мониторинга повторно не проверялся.

### Repo заменён и проверен, 2026-10-16 06:51–06:59

[E38](G3_REPO_RUNTIME_CUTOVER_2026-10-16.md): по явному разрешению пользователя применены два
Repo launcher/control файла с guarded backup, затем остановлен только старый Repo PID22488.
Новый pinned runtime PID24720/Session1 работает; actual Repo MCP/CLI UID1000 пройден.
Control Status находит новый процесс; health/metrics доступны, guest selected admin GET404.
Профиль SHA unchanged; HOST13520/G2runtime25920/container сохранили fingerprints/StartedAt.
Live rollback не выполнялся; recovery identity сохранена в E38 и локальном runbook.
Source collector на Windows: explicit verified listener UP/initialized, automatic discovery UNKNOWN.
Installed dashboard/GUI не проверены; причина discovery отдельно не выделена.
Следующий мониторинговый шаг — адресная диагностика используемого collector, без нового runtime switch.
Прежний HOST остаётся full; final G2 takeover и остальные применимые boundary/assets gaps остаются.
G3 BLOCKED; G4–G6 не приняты. Ниже — датированные результаты предыдущих стадий.

### Профиль Repo проверен перед переходом, 2026-10-16 06:29–06:31

[E37](G3_REPO_PROFILE_PREFLIGHT_2026-10-16.md): actual named-profile shape preflight выполнен
локально на owner Windows. HTTP bindings/Harpoon targets0, проверенные full-only conflicts
не выявлены; выбранные observer env overrides отсутствуют. Команда в профиле отличается,
но fixed CLI command override имеет приоритет по закреплённым исходникам.
Файлов ключей открыто0; значения профиля/окружения не выведены. Repo PID22488 и оба BEFORE
launcher/control файла сохранили expected fingerprints. Live Apply/Rollback/restart нет.
Это не полный effective config или native Go validation. Следующее решение — согласовать
два Repo файла и временное прерывание только Repo; затем E36 guarded Apply, сохранить
backup identity, selected restart и native MCP/monitor/control acceptance.
HOST/G2 не менять и не останавливать. G3 BLOCKED; G4–G6 не приняты.

### Repo-only apply/rollback подготовлен, 2026-10-16

[E36](G3_REPO_GUARDED_MIGRATION_2026-10-16.md): Repo-only wrapper/core/test реализованы.
Default Preview, exact two targets/pins, backup before writes, held target handles, journal и guarded rollback.
Repo PS7.4.6: 28 assertions PASS/одна Windows-specific SKIP; G2 Windows PS5.1: 32/32 PASS, без SKIP,
включая concurrent writer и fault после первой записи; final fixture cleanup подтверждён.
Actual owner default Preview05:51: оба live файла BEFORE, candidate pins match, zero writes/backup/restart.
Live Apply/Rollback и narrow Repo native compatibility не выполнялись. [Локальное recovery](G3_REPO_RUNTIME_ONLY_RECOVERY_2026-10-16.md)
подготовлено; two-file операция не атомарна, unknown DRIFT не затирается. Next — effective-config/
compatibility preflight и отдельно согласованный Repo-only cutover. HOST migration не нужна.
G3 BLOCKED; G4–G6 не приняты.


### Repo stdio read-surface source review завершён, 2026-10-16

[E35](G3_REPO_STDIO_READ_SURFACE_2026-10-16.md): source review pinned normal runtime/Repo main stdio
завершён. MCP startup probe для stdio Set(nil)/return; OAuth discovery disabled с фиксированной
optional причиной. Предполагаемый raw Docker/MCP error→readyz путь снят в этом scope.
Reviewed metrics producers не проецируют stdio params/results; остаются method/kind/channel/ID,
statuses/counters/timing, control-plane route и Harpoon label. Repo source/installed bridge hashes
совпали. Это source-scope вывод, без нового Windows fixture или owner HTTP/body reads.
Меньший Candidate — официальный narrow runtime с обоснованной диагностикой; новый auth/broker
не требуется по этому evidence. Нестандартные bindings/prefix/labels/resource values учитывать
в existing native compatibility/preflight, без нового полного аудита. Next — независимый Repo-only
default-Preview two-file apply/rollback и локальное recovery. ReadyForApply=false; live changes/restart
не выполнены. HOST migration не нужна. G3 BLOCKED; G4–G6 не приняты.


### Repo-only Preview выполнен, 2026-10-16 05:21

[E34](G3_REPO_API_PROTECTION_PREVIEW_2026-10-16.md): actual Windows Repo-only PreviewComplete=true,
ReadyForApply=false. Два live launcher/control файла BEFORE, candidate/runtime pins совпали,
Windows parser PASS. Repo PID22488/SID1001/Session1/listener59183 сохранил expected fingerprint.
Применение/backup/restart не выполнялись. Plain narrow Candidate удаляет admin graph, но privacy
оставшихся read routes ещё не принята. Typed healthstate projections сузили scope: не запрещать
всю диагностику автоматически. Остаток — readyz raw error text и reachable metric paths/labels
для retained stdio Repo; затем выбрать достаточный вариант и подготовить two-file apply/rollback.
Source monitor compatibility есть; installed/native acceptance нет. HOST migration не нужна.
G3 BLOCKED; G4–G6 не приняты.


### Owner TCP поверхность уточнена, 2026-10-16 05:02–05:03

[E33](G3_SELECTED_OWNER_IPC_SURFACE_2026-10-16.md): owner metadata подтверждает прежние
HOST13520:8080 и Repo22488:59183 с ожидаемыми fingerprints/public EXE hashes.
В выбранной цепочке HOST→cmd16092→Node24724 у cmd/Node TCP listeners нет.
HTTP/owner contents/argv/env не читались, live изменения/stop не выполнялись.
5.8 PARTIAL: нет нового selected TCP debug пути; это не полный IPC аудит и не закрытие owner API.
Следующая полезная работа — отдельный Repo protection/compatibility Preview с учётом private
health/metrics и monitor, без all-three switch. Прежний HOST выводится после достаточной G2
acceptance; отдельная его runtime-only migration не требуется. G3 BLOCKED; G4–G6 не приняты.


### Выбранный runtime защищён через alternate paths, 2026-10-16 04:54

[E32](G3_G2_PROTECTED_NAMESPACE_CAPABILITIES_2026-10-16.md): actual G2 SID1009/Session2/non-admin,
восемь выбранных runtime объектов, 128/128 expected opens: 24 read/list ALLOW и 104 mutation DENY5.
Extended и localhost C$ не дали дополнительных mutation rights; normal controls подтверждают
доступность объектов. Content/ACL writes, directory listing, runtime/owner HOST изменения и restart
не выполнялись. 5.7 PASS(scope) для synthetic E31 и этих восьми объектов; личные assets/backups
7.6 и relevant owner IPC/API 5.8 остаются. SMB identity отдельно не установлена, но не нужна для
этого вывода об effective rights. Не повторять матрицу без drift. G3 BLOCKED; G4–G6 не приняты.


### Права через варианты пути проверены, 2026-10-16 04:49

[E31](G3_G2_NAMESPACE_CAPABILITIES_2026-10-16.md): Windows G2 SID1009/Session2/non-admin,
135 capability opens через normal, extended и localhost C$ дали ожидаемую одинаковую матрицу
RW/RO/DENY. Содержимое и ACL не менялись. RW имеет Modify,Synchronize, не FullControl;
первоначальная ошибка ожиданий исправлена и raw первого запуска сохранён. 5.6 PASS(scope),
5.7 PARTIAL для конкретных реальных protected targets/SMB identity; не повторять synthetic matrix.
G3 BLOCKED; G4–G6 не приняты. Runtime не менялся и не перезапускался.


### Selected service handlers уточнены, 2026-10-16 04:33

[E30](G3_SELECTED_SERVICE_HANDLERS_2026-10-16.md): selected Windows metadata и первичные исходники
прочитаны без control codes. MySQL80 Running, SystemAccount=true без точного StartName в E30 (E41: NetworkService), installed executable8.0.44.0;
в matching-version source custom codes идут в обновление статуса. GoodbyeDPI Stopped/Auto;
его private/nonstandard executable path не читался, installed version/source binding неизвестны.
Raw ExecutableExists=false у GoodbyeDPI нормализовано как unknown: проверки file existence не было.
5.4 PARTIAL с суженным остатком, не доказательство live exploit или полной безопасности binary.
Не отправлять live controls и не менять service ACL только из-за USER_DEFINED_CONTROL ALLOW.
E29 failure case принят в scope; новый stop/reboot не требуется. Остаток — relevant boundary/
protected paths и final G2 takeover. G3 BLOCKED; G4–G6 не приняты.

### Один аварийный MCP-peer сценарий принят, 2026-10-16 04:30

[E29](G3_G2_SYNTHETIC_PEER_FAILURE_2026-10-16.md): actual pinned runtime под guest SID1009/Session2
работал с local synthetic control plane/key/peer. После echo тестовый peer вышел37, runtime завершился
сам с кодом0; Job ActiveBeforeStop/AfterStop0, TerminateRequested=false, fixture cleanup PASS.
Real G2 chain25920→18956→32272 exact fingerprints до/после совпали; G2 не прерывался.
8.4 PASS(scope) controlled peer failure, recovery переиспользует E28. Это не actual Python/DC crash,
runtime kill или все failure modes. Нулевой runtime exit code не доказывает успех MCP-задачи.
Normal stop/reboot/ACL/browser проверки не повторять без нового gap. Остаток — применимые owner
GUI/bridges/API/services/protected paths и final takeover. G3 BLOCKED; G4–G6 не приняты.
Отдельная migration retiring owner HOST не требуется.

### Обычный G2 stop/recovery принят в scope, 2026-10-16 04:02–04:19

[E28](G3_G2_NORMAL_STOP_RECOVERY_2026-10-16.md): пользователь выполнил ручной цикл. Пinned Verify
подтвердил ORIGINAL_GONE для runtime23896/Python32480/Node32496; новая chain25920→18956→32272,
SID1009/non-admin/Session2, expected EXE pins и actual MCP/CLI/baseline read PASS.
Port59393 закрыт; selected new chain listener — runtime127.0.0.1:54647.
Owner HOST13520/Repo22488 SID1001/Session1/creation fingerprints совпали с E25 в отдельном after-check,
active console1; Repo read-only MCP ответил. Это scoped samples, не continuous uptime.
6.4/8.1/8.3 PASS(scope); 8.5 PASS(scope) с переиспользованием reboot/start E20.
8.4 PARTIAL: forced-failure case не испытан. Normal stop/restart и reboot не повторять без нового gap.
Итоговый HOST — G2; старый owner HOST ещё не выведен, отдельная его migration не нужна.
G3 BLOCKED; G4–G6 не приняты. Остаток — применимые boundary/owner paths, failure case и final takeover.

### G2 ACL regression и готовность stop/recovery, 2026-10-16 03:49

[E26](G3_G2_CURRENT_ACL_REGRESSION_2026-10-16.json): current SID1009/Session2 chain, 48 runtime
mutation opens DENY5, 16 read/execute ALLOW; 12 own positives, Workspace exact roundtrip/cleanup PASS.
Никаких shared-content/ACL writes. Адресная ACL regression для 6.5 пройдена; общий 6.5 PARTIAL.
[E27](G3_G2_LIFECYCLE_PREPARATION_2026-10-16.json): pinned Capture и отрицательный Verify до stop
выполнены. Три original processes ещё alive; Passed=false — ожидаемый контроль. Реальная остановка
и повторный запуск не выполнялись. [Точный следующий ручной цикл](G3_G2_STOP_RECOVERY_2026-10-16.md):
guest console Ctrl+C, pinned прежний LaunchTest с локальным ключом, затем assistant Verify.
Logout/reboot/email transfer не нужны. HOST/Repo не являются целями остановки этого теста.
Итоговый HOST — G2; отдельная migration прежнего HOST не требуется. G3 BLOCKED; G4–G6 не приняты.

### Целевая замена HOST на G2 — уточнение 2026-10-16 03:35

Пользователь подтвердил: итоговый Windows HOST-инструмент — G2 под отдельным non-admin SID.
Прежний owner HOST не требуется сохранять как постоянно работающий параллельный инструмент.
Сохранение прежних чатов и переходного доступа не означает постоянного сохранения owner HOST runtime.

Отдельная миграция прежнего owner HOST на runtime-only и helper её применения — NOT REQUIRED NOW.
Подготовка этого helper прекращена до записи исходников; live HOST не менялся и не останавливался.
E24/E25 сохраняются как source/metadata evidence; их прежний NEXT о HOST migration заменён этим решением.
Порядок: завершить оставшуюся приёмку G2; подготовить согласованный переход на G2 и восстановление;
затем отдельно согласовать остановку прежнего owner HOST и проверить фактическое отсутствие его
listener/обходного route. Сам запуск G2 не останавливает старый процесс. До фактического вывода
прежнего HOST его поверхность остаётся открытым риском; общий G3 PASS не объявляется.

Fortis Repo остаётся основным контуром разработки. Его сохраняющийся owner-side API оценивается
отдельно по применимому scope; из этой оценки не следует автоматическая миграция HOST или Repo.
Адресная ACL regression позднее закрыта E26; далее actual lifecycle/stop-recovery по E27. Изменения live routes и остановки этим уточнением ещё не выполнены.
G3 BLOCKED; G4–G6 не приняты.

### Owner route compatibility, 2026-10-16 03:23

[E25](G3_OWNER_ROUTE_COMPATIBILITY_2026-10-16.md): HOST profile desktop-commander PID13520/port8080,
Repo profile repo-mode PID22488/port59183, оба owner SID1001/Session1/full client. Selected launchers
BEFORE и pinned narrow runtime совпали по SHA. Profiles/secret argv/env не выводились; HTTP calls=0.
Source review выявил full-only /api/logs dependency HOST monitor и необходимость менять Repo control
вместе с Repo run launcher. Это preparation, не native compatibility или remediation.
4.8 PARTIAL; 4.9/4.10 PENDING. Далее — независимый one-route Preview/backup/apply/rollback helper,
без автоматического restart. Actual full-only needs и monitor behavior уточняются до cutover.
G3 BLOCKED; G4–G6 не приняты. Live launcher/runtime/network/ACL/AV не менялись.

### Запуск и наследование handles, 2026-10-16 03:18

[E24](G3_G2_LAUNCH_INHERITANCE_2026-10-16.md): source review и адресная Windows metadata-проверка
подтвердили guest launcher → runtime → Python → Node в SID1009/Session2, совпадение source/artifact pins,
Python3.13.16 close_fds=True и штатную передачу standard streams.
Обычное CreateProcess inheritance между разными Windows-сессиями не поддерживается; это documented
Windows guarantee, не новый практический тест. Explicit duplication, brokers и owner API им не исключены.
E23 metadata gaps сохранены. Полную классификацию всех 184 entries не назначать обязательным
следующим тестом без конкретного пути обхода. 2.6 PARTIAL; G3 BLOCKED; G4–G6 не приняты.
Следующая работа — owner API compatibility и one-route подготовка по пункту 4, переиспользуя E14/E15.
Никакого owner restart/cutover, изменения launcher/runtime/ACL/network/AV на этом этапе не было.

### Существующие GUI-handles G2, 2026-10-16 03:12

[E23](G3_G2_HANDLE_INVENTORY_2026-10-16.json): документированный Process Snapshot API сначала
проверен на собственных открытых station/desktop/event. Затем завершён обход runtime PID23896
(415 handles), Python PID32480 (76) и Node PID32496 (245); SID1009/Session2 и fingerprints до/после
совпали. Все распознанные WindowStation names относятся к Session2; owner station path не обнаружен.
Снимки, markers и открытые process handles освобождены; память процессов и owner GUI contents не читались.

Это частичное evidence: 184 entries не имеют type name; desktop names возвращены как относительное
\Default и не доказывают parent station/session каждого handle. Снимок выбранных процессов не исключает
все bridges или будущие handles. 2.6 PARTIAL; G3 BLOCKED; G4–G6 не приняты.
Следующая адресная работа для 2.6 — сопоставить этот gap с launch/handle-inheritance source и
применимыми bridge channels. Не повторять достаточные clipboard/browser positives и не превращать
полный перебор Native API в новый обязательный gate.

### Guest clipboard и owner-process access, 2026-10-16

[E22](G3_G2_CLIPBOARD_AND_HANDLE_GATES_2026-10-16.json): с явного разрешения пользователя guest
clipboard SID1009/Session2 заменён своим synthetic marker, exact roundtrip и cleanup PASS; prior
contents не читались, owner contents не затронуты. 2.8 PASS(scope). Current G2 self DUP_HANDLE ALLOW,
три выбранных owner processes DENY5, PID/SID/session/creation fingerprints before/after совпали.
Selected bridge process names отсутствуют, selected own-user flags NOT_CONFIGURED; не считать это
exhaustive bridge exclusion или effective disabled policy. 2.6 PARTIAL; existing/inherited handles,
owner API, targeted ACL regression и G2 stop/cleanup остаются. G3 BLOCKED; G4–G6 не приняты.

### Owner GUI fresh-open boundary, 2026-10-16

[E21](G3_G2_OWNER_GUI_CAPABILITIES_2026-10-16.json): guest SID1009/Session2, owner SID1001/Session1
metadata corroborated through HOST before/after. 10 own-positive controls PASS; owner station four
requested rights DENY5, six desktop paths BLOCKED_AT_STATION_ROOT5. Owner content/capture/input/
ACL/switch operations=0. 2.5 PARTIAL: это scoped fresh-open evidence, не direct desktop DACL matrix,
не inventory existing handles/bridges и не полный G3 PASS. Guest clipboard повтор SKIPPED_NONEMPTY;
не читался/не заменялся. Исторический остаток E21: 2.8 roundtrip позднее закрыт E22; текущий остаток — 2.6 handles/bridges, relevant owner API,
ACL regression и G2 stop/cleanup. G3 BLOCKED; G4–G6 не приняты.

### Продолжение G2 после восстановления, 2026-10-16

[E20](G3_GUEST_GUI_BROWSER_POSITIVE_2026-10-16.json) и [рабочий порядок](G3_GUEST_MCP_WORKFLOW_2026-10-15.md)
сохраняют результаты: own window PASS, clipboard SKIPPED_NONEMPTY. В 02:36:41 после явного
разрешения пользователя corrected browser repeat PASS(scope): CDP/DOM/localStorage/reload, default
sandbox и temporary Job/profile cleanup подтверждены; exit0. Owner profile/page не использовались.
HOST/Repo MCP снова ответили; пользователь после reboot вручную запустил прежний G2 launcher.
G2 get_config/CLI подтвердили SID1009/non-admin/Session2, NodePID32496, AdminEffective=false.
Это startup/recovery evidence; 8.5 PARTIAL, owner boundary и stop/cleanup не приняты.
Старое PDM и отсутствие подробного AV отчёта сами по себе не являются G3 gate.
Первая попытка продолжить доставку была отклонена tool auto-review до Windows исполнения.
После явного разрешения «повтори» та же G2 операция принята: source delivery/read-back и browser
test выполнены. Закрывать AV incident для этого не требовалось; AV settings не менялись.
В Windows Event Log Kaspersky providers не найдены, precise triggering operation не установлена.
Причина transport recovery и достаточность AV rules не доказаны. G3 BLOCKED; G4–G6 не приняты.
Датированные разделы ниже — scoped результаты и история, не новая команда повторного запуска.

### Fortis G2 — актуальная точка, 2026-10-15

**G3 BLOCKED; G4–G6 не приняты.** Это последний документированный результат, а не новая live Windows проверка.

- [Актуальный план, разрешения, подпункты и evidence E01–E30](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md) — владелец текущих условий и следующей работы.
- [Архитектурное решение](G3_SESSION_BOUNDARY_OUTCOME_DECISION_2026-10-15.md) объясняет выбор отдельной guest Windows-сессии.
- [Предыдущие датированные G2/G3 заметки](G2_G3_SUPERSEDED_GUIDANCE_2026-10-15.md#current_state) сохранены как история; их NEXT/PENDING/current и команды не задают актуальный порядок.

| Область | Последний доказанный результат | Что остаётся |
|---|---|---|
| Identity и MCP | SID1009/non-admin/Session2 и MCP/file/CLI цепочка подтверждены; runtime hash совпал | Gate path/hash совпал с Repo; TCP/GET smoke пройден в scope; полная функциональная и owner-boundary приёмка остаются |
| Runtime/files | Четыре DACL применены; 22 758 runtime AccessCheck, writable=0/errors=0; synthetic file/bypass checks и выбранные owner-root DENY получены | Конечная chain требует адресной regression; реальные protected assets/G4–G5 acceptance не завершены |
| Guest session | Прежний Session3 startup/mutex evidence; новая Session2 own window PASS, temporary browser Job/profile cleanup PASS, E20 | Authorized clipboard marker/cleanup PASS(scope), E22; corrected browser CDP/DOM/storage/reload PASS(scope), E20; owner boundary и long-lived G2 stop/cleanup остаются |
| Owner API | Guest Session3 GET200 на двух owner listeners без credentials/body reads подтверждён; owner launchers Preview BEFORE | Защита опасных owner функций/чувствительных данных и owner-specific compatibility не приняты; owner migration не применена |
| Services/IPC/SMB | Четыре task ACL, два Docker pipes и часть service rights DENY; synthetic junction/namespace results есть | User-defined service handlers, применимые owner endpoints/SMB paths остаются открытыми |
| Routes и operation | Прежний чат имел owner HOST/Repo; scoped G2 stop и wrapper restore на копии проверены | Whole-chat guarantee отдельно от OS-изоляции; полный ручной ежедневный цикл и G6 recovery не приняты |

Разрешения и принятые пользователем условия поддерживаются в [плане](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md#целевая-политика-что-разрешено-и-что-защищаем).
Ручной guest login принят. Исторический admin-GET-DENY FAIL не означает запрет безопасной диагностики
и не доказывает owner write/RCE. Соответствие текущего full EXE reviewed source заново не установлено.

### Принят guest MCP рабочий порядок; G2 Session2 file/CLI smoke пройден, 2026-10-15

[Рабочий порядок и точная Preview команда](G3_GUEST_MCP_WORKFLOW_2026-10-15.md) приняты пользователем для source preparation.
Подготовлен отдельный `start-g2-guest-session.ps1`, default Preview, с own WTS/SID/session guard,
scoped duplicate check и cooperative own-state lock; старый launcher не переписан.
Repo: AST/C#5, 10 context cases, env/argv/CIM/lock fixtures пройдены.
HOST: Windows PowerShell 5.1 compilation и own owner-session metadata, lock fixture пройдены;
новая Public копия 10 355 байт создана и SHA-256 перечитан. [Evidence](G3_GUEST_MCP_ENTRY_PREPARATION_2026-10-15.json).
2026-10-15 около 23:03 Asia/Bangkok получен user-local Preview: SID1009/non-admin/no impersonation,
Session2 принадлежит SID1009, visible WinSta0/Default; source/runtime pins совпали, profile/Workspace есть,
own-session tunnels отсутствуют. Public copy прочитана guest. Это не независимая MCP проверка.
Пользователь выполнил контролируемый старт. В 23:15–23:17 Asia/Bangkok restricted G2 MCP отвечает:
CLI SID1009/non-admin/Session2; runtime PID19888 → Python34508 → Node21540 → PowerShell35256,
наблюдаемая ancestry SID1009/Session2; runtime pin совпал. Active console Session1, G2 работает в Session2.
MCP write → exact CLI read → cleanup собственного synthetic файла PASS; launcher lock удерживается (Win32 32).
[Первый smoke](G3_GUEST_MCP_SESSION2_SMOKE_2026-10-15.json) сохранён без переписывания.
В 23:38–23:46 подтверждены [source iteration/gate/Git/TCP-GET](G3_GUEST_MCP_ITERATION_2026-10-15.json):
Repo source → pinned own Workspace → Windows CLI/JSON PASS. Полный Public gate path установлен
CommandLineToArgvW; SHA146E... совпал с Repo. Локальный synthetic Git PASS; обе fixture cleanup завершены.
Runtime TCP127.0.0.1:57494 — healthz/readyz200; пять выбранных GET routes404; Python/Node LISTEN нет.
Это scoped evidence, не exhaustive audit. Последующий own GUI/browser smoke частичный (ниже);
owner boundary и final stop/cleanup остаются. Повторный ручной LaunchTest не нужен.
Installed binaries/profile/ACL не менялись; стартовал существующий guest G2. G3 BLOCKED; G4–G6 не приняты.
Прежний recovery/Native цикл ниже — датированная история на паузе; следующий шаг определяется рабочим порядком.

### История первой GUI/browser попытки и прежнего блокера, 2026-10-16

Дополнение 00:22: скриншоты пользователя подтверждают события защиты Запрещено для Node/PowerShell
в 00:04:25, согласующиеся с EPERM. Exact rule/operation/object пока не видны; runtime notification
описывает legitimate dual-use application, не является сама по себе proof of malware.
Подробная карточка получена: PDM:Exploit.Win32.Generic, высокая угроза, PowerShell process,
Мониторинг активности, FortisHostG1. Следующий шаг — разбор точной команды/причины срабатывания;
true/false positive не установлен. Без изменения защиты/исключений и без повторного Windows исполнения.

[E20: точные результаты и pins](G3_GUEST_GUI_BROWSER_POSITIVE_2026-10-16.json).
Own window SID1009/Session2 создано/visible/destroyed PASS; guest clipboard SKIPPED_NONEMPTY, contents untouched.
Первый Edge/CDP smoke: initial DOM/storage asserts=false из-за test readiness, post-reload marker=true;
полный browser PASS не принят. Browser.close, test Job active=0, Node stopped и profile/scratch cleanup PASS.
Исправленный worker/window-wrapper подготовлены в Repo, AST/C#5/Node syntax PASS; на Windows не выполнялись.
G2 start_process delivery получил spawn EPERM, оба новых файла ENOENT; get_config PID21540 отвечает.
На момент smoke причина EPERM неизвестна; позднее user event подтвердил PDM:Exploit.Win32.Generic.
Точная операция и true/false positive неизвестны. HOST event triage timeout; native log contents не прочитаны.
До Windows повтора установить причину отказа; не обходить другим маршрутом и не менять защиту/ACL.
При недоступном HOST — ручной просмотр конкретного события защиты. Clipboard/browser retest остаются.
G3 BLOCKED; G4–G6 не приняты. Runtime/network/task/service/ACL/mount settings не менялись.

### Подготовлена следующая диагностика G3, 2026-10-15

Сохранён [GUI/clipboard диагностический сценарий](G3_SESSION_GUI_BOUNDARY_DIAGNOSTIC_2026-10-15.md) с единственным pinned PS1.
В Repo прошли PowerShell AST, C# language version 5, captured-bytes Validate и шесть desktop-name guard checks без Windows API вызовов.
Первый user-local Windows OwnerWitness предыдущего pin скомпилировался, но остановился на ошибочном ожидании полного desktop path.
Пользователь сообщил owner Session1 / WinSta0 / сырое desktop name `\Default`; witness не выдан, GuestProbe не запускался.
Ошибка исправлена: station-bound relative desktop lookup, witness schema 2.
2026-10-15 21:51:41 Asia/Bangkok пользователь получил OwnerWitness текущего pin: owner SID1001, Session1, PID28260/creation time, WinSta0 и относительный Default подтверждены.
Windows compilation и owner metadata этап пройдены; owner DENY этим не проверен.
GuestProbe запущен пользователем, но остановился на HoldProcess / QUERY_LIMITED_INFORMATION; точный Win32 и caller stage пока неизвестны.
Последующий inline diagnostic зависел от прежних переменных и завершился до результата; source-file drift не доказан.
Следующий шаг — автономный guest identity/process-open/own GUI block из диагностической инструкции; Windows outcome PENDING.
Owner GUI/clipboard DENY и конечная chain не приняты; текущий C# pin не менялся.
Подготовка не является Windows acceptance: 2.5/2.8 PENDING, 2.6 PARTIAL; G3 BLOCKED.
Source-only работа не меняла установленный runtime, ACL, launchers, services/network или подключения.
Owner Public copy блок текущего pin прошёл без сообщённой ошибки; guest read-back ещё не проверен. Commit/push не выполнялись.

### Review необходимости дальнейших ручных тестов, 2026-10-15

[Review и Candidate Proposal P01](G3_GUI_BOUNDARY_METHOD_REVIEW_2026-10-15.md): общий механизм Windows session/window-station
подтверждён Microsoft; локальная final-chain acceptance и реальные owner API/bridges остаются открытыми.
Предложено сначала принять один guest-local запуск существующего G2, затем итерации file/CLI через него
и один компактный функциональный/regression smoke вместо ручного перехода на каждом изменении.
G2 get_config проверен дважды: gateway/SSE probe HTTP429; live SID/session/runtime этим не установлены.
Старый entry source проверяет SID/role, но не SessionId и требует foreign-process owner metadata.
Runtime/права/инфраструктура не менялись; Proposal не применён; G3 BLOCKED.

### Фактическая доставка документации, 2026-10-15

Документы сохранены в checkout `/workspace/repos/tunnel`.
Fortis Repo read-only проверка подтвердила Windows Repos → `/workspace/repos`,
Workfiles → `/workspace/files` и отдельный Docker volume → `/workspace/repo`.
Это не проверка Windows G3 gates. В этой документационной работе native Windows команды,
runtime/launcher/ACL/network/task/service изменения, restart, Site deployment и Git push не выполнялись.
Git commit/push и публикация remote state — отдельные факты; физическая запись в checkout их не подтверждает.

### Другие контуры — сохранённые датированные результаты

**Последняя предметная проверка Broker/Bridge: 2026-10-11.** Это запись наблюдений, **не динамический список допусков**; перед новым snapshot сверять live `list/preview` и состояние Windows Task. Для действий: [SNAPSHOT.md](SNAPSHOT.md) → [Broker runbook](../runtime/broker/README.md). Для объяснения архитектуры, всех этапов и E2E evidence: [BROKER_V2_PLAN.md](BROKER_V2_PLAN.md).

### Windows Bridge/Broker V2 — подтверждённые факты

| Что | Проверенный срез |
|---|---|
| Broker Task `FortisRepoBridgeBrokerV1` | **Enabled, Ready (остановлена)**; ручной start/stop, без logon trigger и RestartOnFailure |
| Windows `repos.json` | **20 alias**; **17** standing `broker_snapshot_enabled=true` для приватного транспорта, `selection_mode=all`, `respect_gitignore=true`, без пользовательских `.snapshotignore` |
| Не включены | `obs`: ~59 тыс. Git-кандидатов, более 719 МБ до ошибки пути, превышены лимиты; `theory-conspects-and-banks`: 15 файлов с сигнатурами возможных OpenAI-ключей; публичный synthetic `test` |
| Исправления | Windows long path в Bridge (`research-and-bank`: 1 307 файлов / 31 059 466 байт, total limit 35 МБ); `obs-planning-docs`: 1 183 файла / 13 143 358 байт; оба full preview проходят |
| Тесты | Python compile, Bridge selection tests, Broker offline **12/12**; для 17 разрешённых alias — read-only preflight, **не 17 реальных GitHub E2E** |
| Реальные V2 E2E | **2 на `test-private`**: Actions run `38130685868` / Artifact `11697988578` и run `38130962007` / Artifact `11698538347`; оба 8 файлов, 13 510 байт, независимо сверены SHA-256/manifest в ChatGPT |
| Известное восстановление | Второй Git push прервался из-за сети: повторно отправлен **ранее созданный commit**, не новый snapshot; `recover` вернул прежний запрос/Artifact |
| Текущий экспорт | Транспорт `AlexPastukhh/chatgpt-snapshot-transfer` **private**. Право на будущие snapshot **не означает**, что данные 17 проектов уже опубликованы. Новых ZIP при широком включении не создавалось |
| Хранение исходников | Windows worker/Bridge — live вне Docker RW; `runtime/broker/` в локальном `tunnel` — исходник, **не автодеплой**. Git рабочий каталог ранее содержал чужие несвязанные правки/untracked V2; push исходников не подтверждён |

**Границы безопасности:** любые будущие Git-видимые подходящие файлы 17 alias могут оказаться в ZIP во время manual Broker-on. Mandatory excludes, size/secret/path/SHA256 checks сохранены; проверка сигнатур не исключает неизвестные секреты. Очередь Workfiles не аутентифицирует sender (ранее явно принятый риск). Ограничение ZIP **не** скрывает директории `Repos` от Fortis Repo, которому они смонтированы. ZIP в приватной Git history не удаляется вместе со сроком Artifact.

**Нерешённое:** снять реальные блокировки `obs` и `theory-conspects-and-banks` только после отдельной технической проверки; integration fault-injection на остановке в середине публикации не завершён; не утверждать, что live E2E выполнен на всех 17. Старый `bridge-v2-windows.patch` не устанавливать поверх живого исправленного Bridge.

### Другие контуры — срез 2026-10-10 (исторический)

Ниже сохранён **исторический срез от 2026-10-10**. Его статусы процессов, прав и подключений **не заменяют** живую проверку; актуальные документы по snapshot приведены выше.

| Контур | Идентичность | Назначение и граница |
|---|---|---|
| Native HOST | profile desktop-commander; tunnel_6ac4a7249a4081918eb0881c870acf07 | Windows Desktop Commander, широкий доступ HOST; не sandbox |
| Native Repo | profile repo-mode; tunnel_6ac9e4dc9e688191ae1838e858424e8d | Desktop Commander внутри fortis-repo-test |
| HOST Site | Desktop Commander · prot, версия 4 | Отдельный HTTP MCP proxy к upstream; Site-аудитория — отдельная граница |
| Repo Site | Fortis · Repo Mode, версия 7 | Отдельный диагностический Site; его file/terminal gate ещё не активирован |

Native Repo работает независимо от настройки Site. Нельзя заключать «Docker-туннель не работает» по ответу не настроенного Site.

#### Docker на срезе 2026-10-10

| Windows | Linux | Доступ |
|---|---|---|
| C:\Users\alexa\Repos | /workspace/repos | bind, чтение и запись |
| C:\Users\alexa\Workfiles | /workspace/files | bind, чтение и запись |
| Docker volume fortis-repo-workspace | /workspace/repo | внутреннее хранилище |

Контейнер **fortis-repo-test**, ID **c6d7be9fe6eb4138a9dc47db3f82c32c377007c2d461c1f03ad37fe9bb3d074a**. Рабочий каталог /workspace/repos. Сеть **fortis-repo-egress**, исходящий интернет включён; опубликованных портов нет. uid/gid 1000:1000, root filesystem read-only, cap-drop ALL, no-new-privileges, без Docker socket, 2 CPU, 1 GiB RAM, pids limit 256, restart policy no.

HOME и /tmp — временные tmpfs. Git safe.directory добавляется для конкретных Git-корней, не глобальным wildcard; core.autocrlf=true соответствует HOST. Настройки и ограничения проверяет probe.mjs перед запуском.

На проверке в ходе переноса документации контейнер **running=true**, но Repo Tunnel не был найден локальным control.ps1. Это не постоянная настройка; актуальный ответ даёт Status.

Старый контейнер **fortis-repo-test-before-access-20261010t112331268z** оставлен остановленным для отката. Данные volume сохранены.

#### Проверено 2026-10-10

Двусторонние тестовые записи в обоих bind-каталогах; чтение Git-корней; HTTPS GitHub/NPM; схемы и MCP presentation; запрет файлового чтения вне разрешённых каталогов. Контрольные файлы удалены. Это не доказательство невозможности доступа shell к сетевым службам HOST.

Windows Git credentials в контейнер не перенесены. Для private push нужна отдельная настройка авторизации.

#### Было не реализовано на срезе 2026-10-10

- Repo Site ещё не подключён к подходящему upstream endpoint и не разблокирован.
- Sandbox GUI / Windows VM — планы, не установленная возможность.
- Нет отдельной изоляции каждого чата и универсальной веб-панели управления разрешениями.
- Site Repo README/deployment snapshot и некоторые его тексты отстают от текущих Windows mounts / интернета / saved key. Их нельзя использовать для восстановления текущего контейнера. В этом изменении Site не перепубликовывался.

[Управление](OPERATIONS.md) · [Site и версии](SITES.md) · [Обновление слоёв](INSTRUCTIONS.md)

**Где история V2:** в [плане V2](BROKER_V2_PLAN.md), разделы Implementation Log и E2E; там сохранены промежуточные состояния с прежними цифрами и ограничениями. Они **не актуальные инструкции**.


Дополнение 2026-10-13 23:57 Asia/Bangkok: limited client GW fixture denied connect (exit94), GRGW fixture result/PID binding PASS. Production pipe guest grant changed only GW→GRGW on random diagnostic channel; no key/password data, filesystem/window scope unchanged. Final operator 0CF2… pinned Preview PASS; actual guest transport/runtime/window ACL acceptance pending.
