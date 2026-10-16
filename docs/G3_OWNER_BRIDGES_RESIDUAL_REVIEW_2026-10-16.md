# E41 — остаток owner-процессов, служб и Broker, 16 октября 2026

> Последующее решение [E43](G3_G2_SCOPE_ACCEPTANCE_AND_HOST_RETIREMENT_2026-10-16.md): E41/P01 → E42/P01 принят(scope), old HOST закрыт. Ниже результаты и Candidate-статус на дату E41; completeness limits не превращены в universal PASS.

**Известный Snapshot Broker: PASS(scope) для проверенного G2 доступа.**
**Исправлено описание MySQL account. Итоговая приёмка baseline — Candidate.**
[JSON](G3_OWNER_BRIDGES_RESIDUAL_REVIEW_2026-10-16.json) · [План](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md).
G3 BLOCKED; G4–G6 не приняты. Никакие разрешения или службы не менялись.

## Что решали и зачем понадобилась новая проверка

E21/E22/E24 уже закрыли fresh-open owner station, выбранный guest pull-DUP_HANDLE и ordinary
launch/inheritance path в своих scopes.184 неназванных PSS entries не являются сами по себе
доказательством owner capability и не требуют автоматически полного Native audit.

Оставался конкретный встроенный посредник: Snapshot Broker. Его shared file queue не проверяет
identity отправителя, что принято для разрешённого Repo workflow. Отказ G2 читать/запускать Task
из E03 не доказывает отказ отправить запрос через очередь. Поэтому вместо общего port/pipe scan
проверены известная очередь и защищённые файлы её управляющей цепочки.

## Findings

### F1 — неточное описание service account в E30

Actual G2 SID1009/Session2 read-only Win32_Service query, 07:55:39:

| Служба | Состояние | StartName |
|---|---|---|
| MySQL80 | Running / Auto | NT AUTHORITY\NetworkService |
| GoodbyeDPI | Stopped / Auto | LocalSystem |

В raw E30 было только SystemAccount=true. Оно не устанавливает именно LocalSystem.
E03 также сохраняет NetworkService для MySQL. Прежнее изложение E30 исправлено;
его raw observations остаются неизменными. Изменение service account или новый отказ службы
не наблюдались. Управляющих codes отправлено0; PathName/arguments здесь не читались.

Matching-version MySQL handler source E30 остаётся прежним: custom branch сообщает статус,
arbitrary command execution в нём не найден. GoodbyeDPI сейчас Stopped, G2 standard start/config
rights ранее DENY. Installed-source binding остаётся неполным, особенно для GoodbyeDPI.
Нет основания по одному SERVICE_USER_DEFINED_CONTROL ALLOW отправлять128–255 codes,
менять service ACL или требовать воспроизводимую сборку всех Windows services.

### F2 — известный Snapshot Broker проверен как отдельный маршрут

Windows Task FortisRepoBridgeBrokerV1 в08:00:34: Ready, Enabled.
Task principal соответствует owner SID1001; RunLevel0, trigger collection0, --once не указан.
Task не запускалась/не останавливалась. Это датированный срез, не гарантия будущего состояния.

Первый CIM wrapper выдал TriggerCount1 через @($t.Triggers).Count; такой подсчёт может включать
скалярный null. Независимая COM enumeration дважды вернула0. Это ограничение metadata wrapper,
не доказанная смена расписания. Runbook manual-start не меняли.

Installed worker SHA совпал с runtime/broker/worker.py:
EB4D10122F707375AC36D768BE439B3C679CA69B0F65F713DAA9AF001F0BA176.
Просмотренный worker разрешает только list/preview/snapshot/status/recover, проверяет наборы полей,
UUID/alias и standing/one-shot snapshot permission, вызывает фиксированный Bridge через argv list.
В queue API нет apply/register/grant/универсального shell. Полная Bridge implementation и
актуальные permits/registry contents не читались и не переаудировались.

Проверены существующие обычные queue/control objects:

| Область | Какие права запрошены |
|---|---|
| Inbox / Outbox в Workfiles\.fortis-bridge-broker-v1 | LIST, CREATE_FILE, CREATE_DIRECTORY, DELETE_CHILD, WRITE_DAC, WRITE_OWNER |
| worker.py, bridge.py, repos.json | WRITE, APPEND, DELETE, WRITE_DAC, WRITE_OWNER |
| Broker worker parent / Bridge parent | CREATE_FILE, CREATE_DIRECTORY, DELETE_CHILD, DELETE, WRITE_DAC, WRITE_OWNER |

Actual G2 non-admin Session2, 08:04:39: normal и localhost C$ paths,
78/78 requests получили Win325;6 own Workspace controls ALLOW. Handles закрыты.
Только OPEN_EXISTING + immediate close. В очередь не записано ни одного сообщения,
entries не перечислялись, contents не читались, snapshot/export не создавался.
Это effective access evidence, не отдельное установление SMB authenticated identity.

Source Test-G2BrokerQueueBoundary.ps1:
4511bytes, SHA94B18201B37432D8EBE7C4C6D421CC2122F93CD8C197672F21A2334D0EB587AD.
Доставлен в own G2 Workspace\e41-broker-boundary; pin/readback, Windows AST, C# и native checks PASS.
Live worker/Bridge, private state и ACL не менялись. Source copy остаётся для воспроизведения.
Логические4511bytes доставки ниже лимита; protected data не переносились.

Это не полный recursive audit queue files/permits/claims, всего Bridge/dependencies или любых IPC.
Independent Repo имеет намеренный RW доступ к очереди; G2 DENY его не отменяет (whole-chat1.4).

### F3 — конкретный незакрытый широкий маршрут уже известен

Прежний owner HOST пока работает и доступен в чате. Его полномочия и full API не исчезают
от запуска G2. Repo уже исправлен E38; мигрировать retiring HOST на другой EXE не требуется.
Нужны отдельно согласованный retirement и после него проверка прекращения процесса/listener.
Этот этап HOST не останавливал и не менял.

## Решение о достаточном дальнейшем объёме

| Остаток | Статус после E41 | Соразмерное действие |
|---|---|---|
| Обычное межсессионное наследование | Ограничено контрактом Windows и просмотренным запуском E24 | Не повторять session switch/launcher тест |
| Selected guest pull-DUP_HANDLE | DENY E22 | Не повторять ту же матрицу без drift |
|184 unknown PSS entries, relative desktop names | Evidence Limitations, не доказанный обход | Новая углублённая проверка только при конкретном признаке owner capability |
| Clipboard bridges/NOT_CONFIGURED flags | Полное отсутствие и effective disabled policy не доказаны | Не переименовывать NOT_CONFIGURED в disabled; не запрещать own GUI/clipboard; новый test при конкретном bridge/противоречии |
| Snapshot Broker queue/control route | Новый PASS(scope), E41 | Не отправлять пробный snapshot и не менять права ради подтверждения отказа |
| Service custom controls | Небезопасный эффект не доказан; source/version ограничения перечислены | Адресная проверка при конкретном важном version/path/handler изменении; не live fuzzing |
| Прежний owner HOST | Реальный широкий transitional route остаётся | Подготовить конкретный retirement после решения о G2 baseline, затем проверить закрытие |

### Proposal P01 — Candidate, не принятое изменение требований

Принять ограниченный baseline G2 на основе проверенных Windows user/session boundaries,
ordinary launch/inheritance и выбранных relevant handles/API/broker/file controls,
с явно сохранёнными Evidence Limitations. Не требовать доказательства отсутствия вообще
всех неизвестных IPC/handles/services: конечный scan такой гарантии всё равно не даёт.
При новой конкретной существенной поверхности выполнять адресную проверку до расширения scope.

Польза Proposal — завершить проверяемый рабочий сценарий; цена отказа — неопределённый объём
дополнительного аудита без установленного нового решения. Стоимость нового полного аудита
не оценивалась; сроки/проценты уверенности не выдумываются.
Proposal не закрывает автоматически2.5/2.6/5.4/5.8, не меняет committed цель и не объявляет
production acceptance. Рабочий scope/baseline и итоговый operation runbook ещё должны быть приняты.
Retirement HOST и whole-chat route restriction — самостоятельные решения.

## Доставка и пределы

Разработан малый probe в Repo; Windows component/native проверка выполнена через actual G2.
Исправлены только отчётные формулировки и current pointers; source runtime/службы/tasks/ACL/mounts/
сеть/credentials/автозапуск не менялись, existing tunnel/container restart0.
E30 raw JSON не переписан; исправлен его производный assessment с явным дополнением.
Commit/push, snapshot/export, смена архитектуры или installation dashboard не выполнялись.
