# G2 — рабочий порядок через guest MCP

## Действующий G2 workflow после E43

Guest-local Preview → pinned LaunchTest → switch-back; normal Ctrl+C, recover по
[E42](G3_G2_INITIAL_SCOPE_AND_RUNBOOK_2026-10-16.md). Основная разработка/документы —
Fortis Repo, адресные Windows operations — G2. Own GUI/clipboard/browser/state разрешены.
Source iteration: Repo → согласованный файл в own guest Workspace → guest CLI/test →
result read-back. Old HOST/private-station/all-three migration ниже — история.
[Полный итог](ISOLATION_GUIDE.md).

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

### Guest clipboard и текущие DUP_HANDLE gates, 2026-10-16 02:52–02:57

[E22](G3_G2_CLIPBOARD_AND_HANDLE_GATES_2026-10-16.json): пользователь явно разрешил замену
содержимого только guest clipboard. SID1009/non-admin/Session2 и own WinSta0/Default проверены.
В 02:52:57 marker roundtrip exact и EMPTIED_OWN_MARKER PASS; guest test window create/visible/destroy PASS.
Прежнее содержимое guest buffer не читалось; оно заменено с разрешения пользователя. Owner content/
capture/input/ACL/switch operations=0. Пункт 2.8 PASS(scope); повторять clipboard smoke не требуется.

В 02:56 current G2 self PROCESS_DUP_HANDLE ALLOW, выбранные owner PID13520/24724/22488 DENY5.
HOST подтвердил совпадение name/PID/SID1001/Session1/creation fingerprints до и после. Реального
DuplicateHandle не выполняли. Это актуальная negative regression трёх процессов, не inventory
существующих/inherited handles и не защита всех процессов владельца.
В guest Session2 не обнаружены выбранные rdpclip.exe/rdp.exe/mstsc.exe/vmconnect.exe; три выбранных
HKCU clipboard flags NOT_CONFIGURED. Значения по умолчанию/политики не выведены из отсутствия values;
все возможные clipboard bridges этим не исключены. Пункт 2.6 остаётся PARTIAL.

Текущий остаток: existing/inherited handles и relevant bridges, owner API protection, нужная ACL
regression, scoped G2 stop/descendants cleanup/recovery. G3 BLOCKED; G4–G6 не приняты.
Проверки ниже с SKIPPED_NONEMPTY — история до разрешённого marker roundtrip, не текущий blocker.

### Fresh-open owner GUI capabilities, 2026-10-16 02:46–02:49

[E21](G3_G2_OWNER_GUI_CAPABILITIES_2026-10-16.json): actual G2 SID1009/Session2; owner HOST
подтвердил SID1001/Session1 и реальные WinSta0/Default metadata до и после guest проверки.
Все 10 own-positive NativeOpen controls прошли. Для owner station ACCESSCLIPBOARD/READSCREEN/
WRITE_DAC/WRITE_OWNER — Win32 ACCESS_DENIED5. Шесть desktop paths заблокированы уже при
открытии station root: это не шесть отдельных desktop DACL DENY. Все открытые handles закрыты.
Owner pixels/clipboard/window contents не читались, capture/input/switch/ACL changes=0.

[Новый wrapper](../runtime/host-g2/window-isolation/Test-G2GuestOwnerGuiCapabilities.ps1),
SHA023EF3F2... (4 428 bytes), использует прежний pinned native helper8F1BC80C... только в Validate/NativeOpen.
Он не требует foreign-process QUERY_LIMITED_INFORMATION: цель — session GUI objects, а не witness
PowerShell PID. Owner channel independently corroborates object names/identity до и после; lifecycle
самого witness PowerShell не служит критерием существования GUI target. Непрерывная идентичность
объекта между наблюдениями не утверждается. Исходник AST проверен и доставлен в guest Workspace
как g2-owner-gui-capabilities-023EF3F2.ps1, exact SHA read-back совпал.

Пункт 2.5 теперь PARTIAL с доказанным fresh-open scope. 2.6 existing/inherited/duplicated handles и
clipboard bridges остаётся; тот же fresh-open тест повторять без нового вопроса не требуется.
Clipboard повтор 02:41:33: SKIPPED_NONEMPTY, содержимое не читалось/не заменялось; 2.8 остаётся PARTIAL.
Для marker roundtrip нужен пустой guest buffer либо отдельное разрешение заменить только guest contents.
Owner clipboard не является целью такого разрешения. Owner API и long-lived G2 stop/cleanup остаются.
G3 BLOCKED; G4–G6 не приняты. Runtime/ACL/AV/mount settings и общий HOST/Repo не перезапускались.

### Продолжение после перезагрузки и восстановления доступа, 2026-10-16

Пользователь сообщил о перезагрузке Windows. Существующий HOST вновь ответил get_config.
В 02:13–02:14 restricted G2 ответил get_config и выполнил обычный read-only PowerShell:
FORTIS_M\FortisHostG1 / SID1009 / Session2, Administrators group absent, AdminEffective=false.
Публичный launcher 0638D14A... повторно сверен; пользователь вручную запустил его в guest logon.
G2 Node PID32496; это датированные process IDs, не параметры будущего запуска.
Позднее Fortis Repo снова ответил: подтверждены exact checkout, UID1000 и реальные RW mounts.
Состояние маршрутов не означает устойчивость соединения или full G3 acceptance.

Отложенные own GUI/browser результаты теперь сохранены как [E20](G3_GUEST_GUI_BROWSER_POSITIVE_2026-10-16.json).
Собственное window PASS; clipboard SKIPPED_NONEMPTY. После явного разрешения пользователя
повторная доставка pinned sources 9E3FA703... / 16BCAE4F... и browser smoke выполнены в G2:
2026-10-16 02:36:41 Asia/Bangkok, SID1009/Session2, exit0/PASS(scope). CDP DOM query, exact synthetic
DOM/localStorage и новый document после reload с сохранённым storage подтверждены. Edge default sandbox
сохранён; browser exited, temporary Job active0, Node stopped, profile/scratch удалены.
Worker Node23908/Edge25816 и PS22616 — только датированные IDs. Owner profile/page не использовались.
Результат закрывает 3.5 в указанном scope, но не owner boundary, clipboard или long-lived G2 stop.
PDM:Exploit.Win32.Generic для guest Node/PowerShell подтверждён; precise triggering operation и
true/false positive не установлены. Само старое событие и отсутствие полного отчёта Касперского
не являются отдельным G3 gate и не блокируют документацию или независимые безопасные проверки.
Допустимость конкретного повтора отделять от критериев изоляции; не обходить актуальный отказ другим маршрутом.
Запрос Windows Event Log не обнаружил Kaspersky providers; это отсутствие сведений в выбранном
канале, а не отсутствие события. Полный AV report/вывод производителя может понадобиться отдельно.
Read-only проверка process metadata Касперского не раскрыла executable path/version; наличие
доступного штатного CLI экспорта не установлено. Не читать внутренние AV-хранилища и не включать
трассировку попутно. Экспорт существующего отчёта Мониторинга активности за 00:02–00:06
2026-10-16 Asia/Bangkok — дополнительная диагностика, не единственный обязательный следующий шаг.
Operation/process chain/command полезны, если они есть в отчёте; уже присланные detection
name/path/severity повторно запрашивать не требуется. Отсутствие подробностей сохранять как Evidence Gap.
В 02:31–02:33 попытка доставки двух pinned browser sources через G2 start_process отклонена
автоматической проверкой риска до выполнения Windows-команды. Причина: повтор прежней
заблокированной доставки другим маршрутом без разбора инцидента. Это actual tool auto-review refusal,
не новое PDM detection и не критерий G3. Через другие инструменты/кодировки не повторять.
Пользователь дал явное разрешение «повтори» в 02:34:58. Та же операция через G2 start_process
прошла новую проверку; обе записи завершены с exact SHA read-back, затем один browser test PASS.
Проверка ChatGPT до инструмента, Windows/Kaspersky events и фактический результат разделены в E20.
Закрывать инцидент в AV для снятия этой tool-проверки не требовалось; обход и изменение защиты не выполнялись.
Обычные read-only MCP/identity/artifact проверки после ручного старта уже допускаются и выполнены.

Отдельно: tunnel-client.exe был помещён в Слабые ограничения уже в 00:22:41; пользователь изменил
группу доверия, но немедленного восстановления не наблюдал. HOST/Repo получали503/504,
затем network_error/timeout; HOST polling и MCP позже восстановились. Связь восстановления с AV
настройкой не доказана. Не переносить этот результат на PDM-событие guest Node/PowerShell.
Тест curl без credentials дал401 в elevated и503 в ordinary окне (уточнение пользователя);
стабильность зависимости от elevation не проверена. npm ECOMPROMISED при отдельной попытке
Remote Desktop Commander относится к установке npm11.6.2/Node24, а не к приёмке G2.
Новый Remote Device не принят вместо существующих маршрутов.

Первый ручной старт после фактической user reboot подтверждён в scope MCP/guest CLI.
8.5 теперь PARTIAL, не full G6 PASS: отдельная проверка stop/descendants cleanup и остальные gates остаются.
Для живого G2 новый LaunchTest не нужен. При следующем reboot/relogon нужен один обычный guest-local
старт по прежней pinned команде; keys/passwords в документацию не переносятся.

Датированные дополнения ниже фиксируют хронологию инцидента. Их тогдашний PENDING delivery и NEXT
не заменяют эту точку продолжения. G3 BLOCKED; G4–G6 не приняты; commit/push не выполнялись.

### Решение и границы

Пользователь принял порядок и поручил сохранить его, затем начать шаг 1 — подготовку launcher.
Разработка ведётся в Fortis Repo. Один ручной guest login/start должен позволить дальнейшие
file/CLI итерации через существующий G2 без переключения профилей и переноса исходников по почте.
Это принятый порядок работы; изменение критериев security acceptance из Proposal P01 остаётся
Candidate. **G3 BLOCKED; G4–G6 не приняты.** Нет разрешения объявить недоказанные свойства PASS.

Политика/evidence/gates: [основной план](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md).
Обоснование достаточности проверок: [review P01](G3_GUI_BOUNDARY_METHOD_REVIEW_2026-10-15.md).
Последнее состояние: [CURRENT_STATE](CURRENT_STATE.md).

### Шаги

| Шаг | Кто и что делает | Польза / критерий | Статус |
|---|---|---|---|
| 1 | Ассистент готовит и проверяет минимальный launcher в Repo | Точный SID1009, non-admin token, собственная Windows session и runtime pin; чужая process metadata не блокирует запуск. Существующие auth/profile сохраняются | Источник подготовлен; Repo и Windows HOST component checks пройдены; guest Preview PASS по выводу пользователя |
| 2 | Пользователь один раз входит в FortisHostG1 и выполняет проверенный guest-local старт | Устанавливает runtime в правильный контекст. Separate G2 key вводится локально. Затем switch back в alexa без guest logoff | User-local старт выполнен; G2 отвечает в Session2 при active console Session1; stop/cleanup PENDING |
| 3 | Ассистент проверяет существующий G2 после switch-back | Реальные SID/session/descendants, безопасные file/CLI вызовы; доказывает доступ к тому же guest runtime из owner desktop | MCP/file/CLI, SID/session/ancestry и gate full path/hash подтверждены; TCP/GET smoke пройден в scope; полная приёмка PENDING |
| 4 | Ассистент проводит разработку Repo → G2 Workspace → guest CLI/test → JSON | Убирает ручную почту/copy-paste и повторный logon на каждой правке. Передаются только нужные файлы | Repo source → pinned G2 Workspace → Windows CLI/JSON PASS; локальный synthetic Git PASS с cleanup |
| 5 | Выполняется компактная приёмка конечной chain | Собственные GUI/clipboard, нужные CLI/browser функции, cleanup/stop; отдельно relevant owner API/IPC/files/bridges. Прежние достаточные scoped PASS сохраняются | Own window PASS; clipboard exact marker/cleanup PASS(scope), E22; corrected browser CDP/DOM/storage/reload и temporary Job/profile cleanup PASS(scope), E20; owner boundary и G2 stop/cleanup остаются |

Daily login остаётся принятым условием. Windows password или ключ не сохраняются автоматически.
Новый tunnel/plugin, SYSTEM broker, service/task, autologon и новые mounts/ACL не требуются этим порядком.
Длительность ежедневного цикла ещё не измерена. Code preparation и пользовательский готовый цикл — разные затраты.

### Шаг 1 — конкретный результат

Подготавливается отдельный исходник
[start-g2-guest-session.ps1](../runtime/host-g2/runtime-api-migration/start-g2-guest-session.ps1).
Старый `start-g2-runtime.ps1` и его исторические pins не переписываются.

- `Validate`: проверка загрузки C# без Windows API и без runtime.
- `Preview` по умолчанию: own SID/groups/impersonation/session owner, WinSta0/Default, pinned EXE,
  наличие собственного profile и Workspace, basic process metadata только своей session. Без key prompt,
  runtime start, directory/lock writes или чтения содержимого profile.
- `LaunchTest`: после тех же guards — только существующий `fortis-host-g2-test` и pinned runtime v0.0.15.
  Separate G2 key вводится локально и передаётся через environment только дочернего процесса.
  Пустой Harpoon additional transport и UI metadata setting сохраняются.
- Session owner определяется через WTS текущей process session и разрешается в SID. Само имя WinSta0
  недостаточно: alternate-user процесс в alexa session должен быть отвергнут.
- После switch-back guest может быть неактивным; launcher не требует, чтобы session оставалась
  active console. Номера session 1/2/3 не зашиты.
- Текущая guest session проверяется на существующие tunnel-client processes без owner SID queries.
  Между новыми launchers одного account/profile удерживается отдельный own-state file lock.

### Ограничения и приёмка запуска

Cooperative file lock не обнаруживает старый launcher в другой session, который lock не использует.
Другие sessions не перечисляются и не исследуются ради duplicate guard. Preview явно сообщает эту
неопределённость. Существующий legacy G2 не завершать по догадке; при признаках его работы сначала
адресно установить фактическое состояние. Этот launcher не обещает глобальный singleton.

Содержимое profile/ключей не выводится. Наличие profile не доказывает нужную командную chain;
её фактические descendants/stdio gate/env/files и transport проверяются после контролируемого старта.
Guest Preview на Windows пройден по выводу пользователя; реальный duplicate lock, authentication,
запуск и работа при active console Session1 теперь подтверждены MCP smoke ниже; cleanup/stop PENDING. Ctrl+C/закрытие G2 console — запрос остановки, а не уже проверенный
успех удаления всех descendants. Job/supervisor рассматривается лишь при доказанной потребности.

Исходники `runtime/` не развёртываются автоматически. Путь guest-visible копии, pin и точная команда
задаются после подготовки; owner Repos не открывается guest. Возможен точечный Windows file copy
или доступный G2 file route после проверки. Shared tunnel не перезапускается ради доставки.
Для прямой передачи HOST↔ChatGPT сохраняется лимит 1 000 000 байт на логический набор;
credentials в Repo/Docker/GitHub не передаются.

### Проверка и доставка шага 1

Исходник подготовлен и сохранён в checkout. SHA-256:
`0638D14A92F78006526281BEC98C391FAD96F6C0F3F70D9C02475DA3A56C481D`.
[Машиночитаемое evidence](G3_GUEST_MCP_ENTRY_PREPARATION_2026-10-15.json) фиксирует точный scope.

В Repo прошли PowerShell AST, C#5 compilation, два Validate в одном процессе, 10 context cases
(включая Run-as mismatch, admin/impersonation/session0/wrong objects), scoped CIM fixture,
синтетическая child-env/argv проверка и file-lock deny/release. Runtime не запускался.
Через существующий HOST прошли compilation в Windows PowerShell 5.1.26100.9711, own-session WTS
и WinSta0/Default metadata под owner SID1001/Session1, Windows file-lock deny/release и cleanup fixture.
Это component checks этапа подготовки. Позднее guest Preview и scoped MCP/file/CLI smoke пройдены (ниже); полная приёмка chain PENDING.

Новая копия 10 355 байт создана в `C:\Users\Public\Documents\Fortis-G2-GuestEntry-0638D14A.ps1`;
SHA-256 после записи совпал. Старые launchers/профили/ACL не менялись. В адресном снимке двух
именованных tunnel-client процессов обнаружены только owner SID1001/Session1 (PID21172/16632).
Это снимок, не глобальная гарантия отсутствия legacy G2; новые guard limitations остаются.
На этапе подготовки G2 не запускался. Позднейший user-local старт и MCP smoke описаны ниже.
Owner процессы/network/services/tasks не менялись; commit/push не выполнялись.

### Пройденный локальный шаг: Preview

В ordinary FortisHostG1 PowerShell вставить блок целиком. Он сам читает и проверяет байты;
не зависит от прежних переменных, не запрашивает key, не запускает runtime и не пишет lock/state.
Сначала оценить JSON/точную ошибку. `LaunchTest` выполняется отдельным конкретным шагом после Preview.

```powershell
& {
    $ErrorActionPreference='Stop'
    $p=Join-Path $env:PUBLIC 'Documents\Fortis-G2-GuestEntry-0638D14A.ps1'
    $bytes=[IO.File]::ReadAllBytes($p)
    $sha=[Security.Cryptography.SHA256]::Create()
    try { $hash=([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-','') } finally { $sha.Dispose() }
    if($hash -cne '0638D14A92F78006526281BEC98C391FAD96F6C0F3F70D9C02475DA3A56C481D'){throw 'Launcher SHA256 mismatch'}
    & ([scriptblock]::Create([Text.Encoding]::UTF8.GetString($bytes))) -Mode Preview -CapturedSHA256 $hash
}
```


### Пройденный локальный шаг: Preview и контролируемый LaunchTest

Источник: JSON, присланный пользователем 2026-10-15 около 23:03 Asia/Bangkok.
Это user-local evidence, не независимый вызов guest MCP и не точное время выполнения.
Полный результат сохранён в поле `user_local_guest_preview` [evidence](G3_GUEST_MCP_ENTRY_PREPARATION_2026-10-15.json).

Preview PASS: source/runtime SHA-256 совпали; SID1009, non-admin/no impersonation, session 2
с owner SID1009, visible WinSta0/Default; profile/Workspace найдены; в своей session tunnel processes нет.
Guest readback Public копии подтверждён. Ключ/profile contents не читались; runtime не запускался.
Legacy G2 в других sessions не исключён. G3 BLOCKED; G4–G6 не приняты.

В той же обычной FortisHostG1 PowerShell выполнить блок целиком. Он повторяет guards,
берёт own-state lock, запрашивает только separate G2 runtime key локально и запускает existing G2.
Не вводить owner/Repo key, Windows password; ключ не отправлять в чат.
Новый профиль, service/task или права не создаются. OwnerWitness не нужен.

```powershell
& {
    $ErrorActionPreference='Stop'
    $p=Join-Path $env:PUBLIC 'Documents\Fortis-G2-GuestEntry-0638D14A.ps1'
    $bytes=[IO.File]::ReadAllBytes($p)
    $sha=[Security.Cryptography.SHA256]::Create()
    try { $hash=([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-','') } finally { $sha.Dispose() }
    if($hash -cne '0638D14A92F78006526281BEC98C391FAD96F6C0F3F70D9C02475DA3A56C481D'){throw 'Launcher SHA256 mismatch'}
    & ([scriptblock]::Create([Text.Encoding]::UTF8.GetString($bytes))) -Mode LaunchTest -CapturedSHA256 $hash
}
```

После `LaunchTestStarted` оставить консоль открытой. Если runtime завершился или сообщил ошибку —
сначала сообщить это, не повторять запуск вслепую. При работающем runtime переключиться в alexa
без guest logoff и сообщить PID/GuestSession из JSON либо ошибку без ключей.
Затем ассистент проверяет существующий G2 connector и реальную chain; успешный Process.Start сам по себе
не доказывает MCP/auth/transport, непрерывную работу после switch-back или owner boundary.

### Текущее состояние: G2 Session2 MCP/file/CLI smoke пройден

2026-10-15 в 23:15–23:17 Asia/Bangkok restricted G2 connector ответил на get_config и выполнил PowerShell.
[Полное evidence](G3_GUEST_MCP_SESSION2_SMOKE_2026-10-15.json).

- CLI: SID1009, Administrators group absent, Session2, own Workspace; exit code 0.
- Наблюдаемая ancestry: runtime PID19888 → Python PID34508 → Node PID21540 → PowerShell PID35256;
  также parent launcher PID31096/WindowsTerminal PID33936. Все обнаруженные процессы SID1009/Session2.
- Runtime v0.0.15 имеет ожидаемый A922... pin; Node executable hash зафиксирован в evidence.
- Active console session 1, guest process session 2; G2 продолжает отвечать. Сам console ID не доказывает owner SID.
- MCP write собственного synthetic файла → CLI exact read/hash → удаление только этого файла пройдены.
- Launcher lock удерживается: sharing violation Win32 32 при own-state probe; duplicate runtime не запускался.
- Runtime arguments: expected profile, env key reference и empty additional transport присутствуют;
  MCP UI environment = 1; Node entrypoint marker присутствует. Raw command lines/ключи/profile contents не выводились.
- На этом этапе был найден только basename `g2-stdio-gate.py`; первые pattern checks не установили full path/hash.
  Последующая CommandLineToArgvW проверка ниже закрыла этот gap; прежнее evidence сохранено без переписывания.

Route пригоден для адресных собственных file/CLI итераций без нового login/email на каждой правке.
Последующая source/test итерация и gate/TCP/GET smoke выполнены (ниже).
Текущий остаток: owner protection, existing handles/bridges и scoped G2 stop/cleanup.
2.8 guest clipboard PASS(scope), E22; browser repeat 3.5 PASS(scope), E20. Прежние failed/skipped
результаты и EPERM ниже сохранены как история, повторять их ради старого вывода не нужно.
Пользователю повторять LaunchTest или переключать профили сейчас не требуется; гостевую консоль оставить открытой.
Полная transport/discovery/owner boundary и descendant cleanup не приняты. G3 BLOCKED; G4–G6 не приняты.

### Выполнена source/test итерация; gate, Git и TCP/GET smoke

[Evidence](G3_GUEST_MCP_ITERATION_2026-10-15.json) фиксирует реальные результаты 2026-10-15 23:38–23:46 Asia/Bangkok.

В Repo подготовлен [Test-G2OwnEntryArtifacts.ps1](../runtime/host-g2/runtime-api-migration/Test-G2OwnEntryArtifacts.ps1).
AST/C#5 пройдены; для Linux validator применён process-only globalization invariant после ошибки ICU.
Источник 3 400 байт передан существующим G2 file tool в собственный Workspace. Проверка SHA-256
перед выполнением совпала: `B454946153807F61F3BB2992135DA6BB0A9C080EF20F4B50B8D4CE1ADD1B7DFF`.
Windows execution exit 0 под SID1009/Session2. Для тестовых правок не понадобились login/email/новый tunnel.

CommandLineToArgvW установил аргумент gate:
`C:\Users\Public\Documents\FortisHostG1Probe\RW\g2-stdio-gate.py`,
2 564 байта, SHA-256 `146E60B028276F871353A113571306002942461F0446E519A63B28DCC068418D`.
Он совпал с Repo source. Исходник фильтрует child environment по allowlist и задаёт MCP UI flag.
Это source/file identity, не attestation уже загруженного Python кода и не OS policy gate для того же SID.

Локальный synthetic Git под guest: init/add/commit/status/rev-parse PASS, clean worktree, одна commit,
без remote/network/auth и без project commit/push. Первая очистка Directory.Delete остановилась на
трёх read-only Git objects; после адресной проверки остатки удалены Remove-Item -Force.
Повторная проверка с корректной own-fixture очисткой PASS, оба временных каталога удалены.

Из трёх известных chain PIDs только runtime19888 слушал TCP127.0.0.1:57494; Python34508/Node21540 LISTEN не имели.
PID/SID/creation/listener перед HTTP повторно проверены. GET healthz/readyz=200;
GET api/status, api/restart, harpoon, mcp, sse=404. Ответные bodies не читались, HTTP mutations=0,
owner endpoints не запрашивались. Это scoped наблюдение, не exhaustive method/endpoint audit.

Runtime/profile/ACL/mount/network/tasks/services не менялись; G2 не перезапускался.
Последующая проверка 2.8/3.5 описана ниже; owner protection и final cleanup остаются открытыми. G3 BLOCKED; G4–G6 не приняты.

### История первой попытки own GUI/browser до успешного повтора, 2026-10-16

[Evidence E20](G3_GUEST_GUI_BROWSER_POSITIVE_2026-10-16.json) сохраняет частичный результат и ошибки без подмены PASS.

2026-10-15 23:57 Asia/Bangkok: SID1009/Session2, WinSta0/Default. Собственное test window
создано, visible=true, уничтожено. Guest clipboard уже содержал formats: SKIPPED_NONEMPTY;
contents не читались и не заменялись. Clipboard roundtrip PENDING, это не DENY. Owner probes/capture/input=0.
[Positive wrapper](../runtime/host-g2/window-isolation/Test-G2GuestGuiPositive.ps1), SHA075B...,
использует pinned helper8F1B... только в Validate и GuestGui(false). OwnerWitness не нужен.
Первая попытка остановилась до GUI на отсутствующей PUBLIC env; исправлено Known Folder CommonDocuments,
без расширения child env allowlist.

2026-10-16 00:02: первый browser smoke через G2 запустил own Node/Edge с default sandbox,
fresh profile и synthetic loopback page. CDP подключился, но initial DOM/storage asserts=false:
test запросил DOM до document readiness. Post-reload marker=true не принят за полный PASS.
Browser.close прошёл; test Job active processes до/после stop=0, Node stopped, profile/scratch удалены.
Это cleanup только временного browser test Job, не приёмка остановки G2.

В Repo исправлено ожидание initial page readiness и добавлена проверка нового performance.timeOrigin
после reload. [PS wrapper](../runtime/host-g2/window-isolation/Test-G2GuestBrowserFunctional.ps1)
SHA9E3FA703... (8 140 bytes), [Node worker](../runtime/host-g2/window-isolation/guest-browser-functional.js)
SHA16BCAE4F... (6 099 bytes). AST/C#5/Node syntax PASS; исправленная версия на Windows не выполнена.

Попытка доставки исправления через G2 start_process получила spawn EPERM.
Read-only G2 get_config отвечает (Node PID21540); оба новых destination файла get_file_info=ENOENT.
Первоначально причина отказа не была установлена. Позднее пользователь подтвердил security denial
PDM:Exploit.Win32.Generic (ниже); точная операция/true-vs-false positive всё ещё неизвестны.
Запуск/доставка не повторены другим способом, права/защита не менялись.
Адресное чтение событий через existing HOST не дало данных: interruption, затем UNAVAILABLE/timeout.
Это отдельный сбой диагностики, не доказательство остановки G2 или блокировки конкретным антивирусом.

Исторический диагностический шаг после первого process spawn refusal при недоступном HOST:
посмотреть в отчёте защиты события после 00:02 2026-10-16 Asia/Bangkok — время, объект,
название обнаружения/правила и действие. Защиту не отключать и исключения не добавлять.
После диагноза выбрать допустимый повтор исправленного теста. Clipboard roundtrip потребует пустого
guest clipboard либо отдельно согласованного сохранения/замены; сейчас непустой буфер не изменять.
Owner protection, ACL regression и long-lived G2 stop/recovery остаются. G3 BLOCKED; G4–G6 не приняты.

### Дополнение по скриншотам защиты, 2026-10-16 00:22 Asia/Bangkok

Пользователь прислал два скриншота. Activity report содержит три видимых события Запрещено
в 00:04:25: Node.js/node.exe, Windows PowerShell/powershell.exe, Node.js/node.exe.
Node directory: C:\Tools\desktop-commander-runtime. Это совпадает по времени с spawn EPERM.
Точная запрещённая операция, правило, инициатор и объект в общем списке не видны.
Уведомление для installed narrow runtime от 2026-10-15 23:13 классифицирует его как легальное
приложение, которое может использоваться злоумышленником; само по себе это не доказательство malware.
Карточка получена в 00:25: PDM:Exploit.Win32.Generic, тип Троянское приложение, высокая угроза;
компонент Мониторинг активности, объект process powershell.exe под FortisHostG1. Windows tests на паузе;
исключения/защиту не менять. Repo read-back снова timeout: каноническая доставка ещё не подтверждена.

### Уточнение причины общей недоступности, 2026-10-16 00:36 Asia/Bangkok

Пользователь предоставил HOST/Repo control-plane poll logs: 00:28:58/00:31:42, HTTP504,
Cloudflare origin timeout, retry_in_ms=60000. Клиенты работали в моменты записей.
Гипотеза, что все туннели завершены Kaspersky, этим не подтверждается.
На status.openai.com активен Widespread feature degradation (Monitoring); native Tunnel impact отдельно не указан.
PDM behavior detection для guest Node/PowerShell подтверждён как отдельное событие.
На скриншоте exact node.exe trusted rule содержит do-not-monitor activity/children; рекурсивность выключена.
Folder exclusion desktop-commander охватывает Scan/File AV; PDM-specific rule имеет другой truncated path/fixed hash.
Настройки и событие требуют отдельного анализа, не расширения исключений для исправления control-plane504.
Существующие клиенты уже назначают автоматический повтор; инфраструктура и защита не менялись.

### Свежие control-plane логи, 2026-10-16 00:53 Asia/Bangkok

HOST briefly polling operational 00:50:16, request req_55a9c2df22f14bfbaca8374974bd304a;
далее вновь503/504. Repo 00:51:27 получил503 tunnel_transport_unavailable,
request req_c6c839298f9f4377a45a1dc4caf0bd1e, затем504. Metadata fetch также timeout/504.
Клиенты работают и получают ответы; недоступность Tunnel transport подтверждена ответом сервиса.
Это отдельный инцидент от Kaspersky PDM. Причина backend outage неизвестна; изменение AV rules
или массовый restart не обоснованы этими логами. Сохранять auto retry и request IDs для поддержки.
Дополнительные локальные скриншоты для классификации transport отказа сейчас не требуются.
Windows security tests остаются на паузе; каноническая запись ожидает read-back доступного Repo.

### Источники нового session guard

- [WTSQuerySessionInformationW](https://learn.microsoft.com/en-us/windows/win32/api/wtsapi32/nf-wtsapi32-wtsquerysessioninformationw): запрос своей session; чужая query permission не prerequisite.
- [WTS_INFO_CLASS](https://learn.microsoft.com/en-us/windows/win32/api/wtsapi32/ne-wtsapi32-wts_info_class): WTSUserName/WTSDomainName; WTSWinStationName не является именем GUI station.
- [WindowsIdentity.GetCurrent](https://learn.microsoft.com/en-us/dotnet/api/system.security.principal.windowsidentity.getcurrent?view=netframework-4.8.1): primary/effective context и проверка impersonation.
- [ProcessStartInfo.EnvironmentVariables](https://learn.microsoft.com/en-us/dotnet/api/system.diagnostics.processstartinfo.environmentvariables?view=netframework-4.8.1): environment дочернего процесса.
