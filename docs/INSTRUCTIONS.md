# Обновление инструкций после изменений

## 25.10.2026 — PR-A-13: прямой MCP launcher, исходник для ручного Windows gate

Подготовлен [source-кандидат постоянного Repo launcher](../runtime/host-g2/runtime-api-migration/repo-run-tunnel-direct.candidate.ps1) с прямым DC из защищённого контейнерного image path, read-only preflight и fail-closed checks; он не исполняет нынешний Bridge и не запускает mutating `probe.mjs`. [Windows AST/Preview, backup/install/rollback и критерии](agent-workflow/reviews/permanent-direct-mcp-rollout-20261025.md). **Это только Git source, не установленная конфигурация**: текущий Windows `run-tunnel.ps1`, runtime/profile, Docker, firewall/ACL/mounts, UID, network не изменены, процессы не перезапускались. До выполнения ручного gate и отдельного owner-controlled deployment другие чаты продолжают работу через восстановленный Bridge. Legacy probe больше не будет автоматически приводить Git/DC к нужному состоянию после такой будущей замены; drift требует отдельного решения. PR-A-07 остаётся альтернативой, F-R-05 ещё unresolved. Push не выполнялся.

## 25.10.2026 — Project Checker: read-only preview prototype

В исходниках runtime/userscript-updater добавлен только расчёт плана изменений для безопасных тестовых деревьев; файл-назначение никогда не записывается. 49/49 тестов PASS с реальными Docker-only ESLint и Semgrep. Этот код не гарантирует защищённое Windows-чтение target, approvals, backup или promotion. Подробнее — [implementation log](userscript-updater/IMPLEMENTATION_LOG.md). Реальные внешние копии не менять до отдельной owner manual установки и приёмки.

## 25.10.2026 — Project Checker: Docker-only analyzer validation

ESLint 10.13.0 и Semgrep CE 1.182.1 проверены на синтетических JS/Python в Fortis Repo Docker, 40/40 тестов PASS без skips. Development-only политики находятся в runtime/userscript-updater/policies/demo; Docker-копии совпадают по SHA-256. Нет trusted Windows installation или external update; сведения и границы проверки — в [журнале реализации](userscript-updater/IMPLEMENTATION_LOG.md). Не запускать source/CLI в Docker как доверенный Windows-checker.

## 25.10.2026 — Project Checker: исходники, не установленный runtime

Новые исходники: [runtime/userscript-updater](../runtime/userscript-updater/README.md). ESLint 10.13.0 для синтетических тестов установлен только во внутреннем volume Docker, путь /workspace/repo/project-checker-devtools. Действующий Windows-компонент, Loader, внешние назначения, политики, права и mounts не менялись. Факты, недоказанные гарантии и следующий gate — в [журнале реализации](userscript-updater/IMPLEMENTATION_LOG.md). Для настоящего использования необходим отдельный ручной перенос и независимая проверка границы доверия.

## 25.10.2026 — план защищённого обновления userscripts

Требования, этапы и контекст для следующего чата — в [userscript-updater](userscript-updater/README.md). Последний выбранный UX: лёгкая оболочка, сохранённые пары файлов, две отдельные кнопки «Проверить» и «Обновить», результаты и подтверждаемая замена в одном доверенном Windows-окне. Это документированный план, не установленный updater или подключённые анализаторы; Windows/runtime/Loader этим этапом не менялись.

## 25.10.2026 — где поддерживать Observatory и как применять обновление

- Владелец текущих фактов Observatory — [README V1](../observatory/v1/README.md): реализация/API, source SHA, установленные версии и доказательства отдельно. Проверки конкретного выпуска принадлежат его release package; не копировать весь журнал в несколько документов.
- Для Windows — [актуальная вводная setup](../observatory/v1/OWNER_VIEWER_MANUAL_SETUP.md). Проверить установленный SHA и подходящую базу guarded installer, выполнить Preview, сохранить backup/rollback, затем вручную применить только нужные файлы владельцем alexa. Старые SHA/команды ниже не применять к новому source автоматически.
- Обновление source Notifier не обновляет Tampermonkey в каждом профиле. Сохранить существующий script/Loader и GM-данные, сверить runtime badge и сначала проверить файл без Send. Версия клиента влияет на семантику `mode=send`.
- После изменения обновлять owner документации и указывать отдельно commit/push, Windows install, browser smoke, restart и фактическую попытку/доставку. Отмена/неясный ACK не превращаются в успешную доставку.

Эта актуализация меняет документы и сохраняет ранее подготовленный helper; Windows runtime, Docker, туннели, права и ключи не менялись. Новых подключений или отправок не выполнялось.

## 24.10.2026 — общий workflow и Git-фиксация документации

Постоянная точка входа: [docs/agent-workflow](agent-workflow/README.md). Требования принадлежат REQUIREMENTS, оперативный план — STATE, выполненные действия и проверки — JOURNAL. После значимого этапа обновлять эти владельцы фактов и делать осмысленный локальный коммит только относящихся к работе файлов; порядок проверки diff и публикации указан в точке входа.

Владелец вручную выдал Modify одному Godot-проекту для G2; агент проверил файловый обмен G2/Repo и cleanup. Границы доказательства — в [срезе](agent-workflow/STATE.md), процедура и backup reference — в [журнале](agent-workflow/JOURNAL.md). Эта Git-фиксация добавляет документы/навигацию; новый runtime, Site и Windows GUI ею не запускаются, контейнер/туннели не перезапускаются.

## История проверок 21–22.10.2026

Повторявшиеся здесь 491 строка релизной истории сохранены в [CURRENT_STATE](CURRENT_STATE.md). Текущее состояние Observatory ведётся в [README V1](../observatory/v1/README.md). Ниже остаются остальные датированные инструкции.

## 20.10.2026 — Repo Observatory restarted; next Windows/Edge rollout

Repo-only service на 127.0.0.1:18754 был штатно остановлен с
проверкой identity PID и запущен из новых источников в том же
Docker-контейнере и persistent volume. Зафиксирован реальный
read-back до/после: 2 одинаковых session IDs / 42 события,
ingest=available, без bearer HTTP 401. Docker container НЕ
рестартовали, archive НЕ удаляли, пользовательские сообщения/
ключи и коннекторы Windows не экспортировали.

Следующая операция — только владелец Windows alexa вручную закрывает
старый owner Viewer, применяет ПИН-установку трёх файлов по
observatory/v1/OWNER_VIEWER_MANUAL_SETUP.md, запускает Viewer,
обновляет существующий Tampermonkey до Notifier 5.7.10,
перепривязывает только нужные chats, проверяет Edge UI на безопасных
тестовых данных по observatory/v1/EDGE_SMOKE_2026-10-20.md.
НЕТ автоматической установки через Repo: владелец Windows SID/ACL
и GUI не принадлежат Repo-контейнеру. Реальный native Send не
инициировать без наглядной проверки target chat/вкладки и согласия.
Для результатов Edge требуются позитивный и негативный тесты,
доказанный receipt исходника и подтверждённое вложение (не только
наличие input.files). Не сообщать pairing code в чат.


## 20.10.2026 — post-review source fixes, без установки

По независимому Final Review R-FNO-20261020/v1 исправлены
F-P-03/F-P-04/F-P-05/F-P-06 на уровне исходников.
Notifier 5.7.10: insert-only выполняет посимвольную сверку
исходника и штатного поля; отличающиеся пробелы/пустые строки/
Unicode дают явный отказ без Send, исходник остаётся в Textbox.
File mode распознаёт только dedicated attachment card, а не имя
в любом тексте composer, и не считает busy состояние подтверждением
готовности upload. Настоящая карточка и finished upload в Edge
НЕ проверены. Manual Send после редактирования не автоматически
архивируется с task_id.

Repo Store: staged JSON из .event_bundle не получает receipt
без event_id sidecar из .event_details. При временном отсутствии
sidecar => retryable, архив не пополняется; legacy root events
не требуют detail. Windows owner_dispatch: poll/status/enqueue/ack
сбрасывают истёкший body, late ACK разрешён только для текущего
не заменённого dispatch_id. Две другие развилки Final Review —
отдельное согласие на remote Send и offline queue — НЕ приняты и
не изменялись. Исходники не означают Docker/Windows/Edge rollout.
Нужен controlled deployment и live end-to-end receipt.


## 20.10.2026 — Owner Viewer session composer / Notifier 5.7.9

Для отзыва нажми «Отозвать право адресной отправки» в панели
привязки Viewer; следующая привязка создаст новый ключ.
Это не гарантированная отмена уже выданной вкладке команды.

В sources создан scoped owner-local channel dispatch в
observatory/v1/owner_dispatch.py + owner_viewer.py, и
Notifier 5.7.9 polling / ack через новый отдельный dispatch_key.
Это дополнительное право, которое выдаётся только повторной
явной привязкой конкретного Chat ID к установленному Viewer;
старый observer/writer pairing без ключа не умеет remote Send.
В режиме «Отправить» новый task_id генерирует сам Notifier,
через обычную запись точного исходника. В режиме «Вставить»
Send/task_id не происходит. Вкладка без активного подключения
не получает команды; duplicate dispatch не повторяется и receipt
не выдумывается. Вручную закрыть прежний owner Viewer, проверить
три SHA и исполнить ТОЛЬКО updated Install-FortisObservatoryViewer.ps1
по observatory/v1/OWNER_VIEWER_MANUAL_SETUP.md, а затем обновить
ОДИН existing userscript Notifier 5.7.9. Запущенные Docker/Windows
службы и Tampermonkey при source-изменениях не обновляются сами.
Нужен end-to-end smoke на реальных двух чатах прежде чем считать
remote send готовым. Следующие optional этапы: manual-send capture,
file-aware dispatch, offline queue (после отдельных решений).


## 20.10.2026 — применение подробных событий и Notifier insert-only

Исходники готовятся отдельными source-only релизами: Repo Docker
Observatory event-detail (UTF-8 stdin sidecar и on-demand history),
Windows Owner Viewer (см. PIN SHA в
observatory/v1/OWNER_VIEWER_MANUAL_SETUP.md) и Notifier 5.7.8
с кнопкой «Вставить» над ➤. При event --detail-stdin на старом Repo service новый формат
останется в отдельной staging-очереди, не будет принят до обновления
Store. STAGED_ONLY не является receipt. Сначала обновить/проверить службу в
контролируемом порядке, не сбрасывая archive. AI interim/final
оставить через Repo message STDIN. Сквозная отправка из Observatory,
автоархивация manual Send и очередь закрытых вкладок
остаются отдельными нерешёнными задачами. Не создавать
второй userscript и не перезапускать Windows без владельца.


## 20.10.2026 — крупные вставки Notifier 5.7.5

В новых исходниках Notifier и Observatory оригиналы размером
больше 64 КиБ (до 512 КиБ UTF-8) идут по тому же точному
per-task пути; пересмотрены ограничения Store, HTTP, Windows
Viewer/Relay и Docker relay. Быстрый текстбокс использует короткий
preview для вставок от 12k символов, но ↗ раскрывает полный
редактируемый текст, ⧉ копирует полный текст, ➤ переносит весь
текст порциями и только затем допускает Send. Вторая кнопка
«только вставить» и удалённый текстбокс Observatory из отдельного
плана ещё не реализованы. Для запуска нового пути нужно обновить
существующие Windows/Docker службы штатным способом и заменить
ровно один Tampermonkey Notifier. Ключи не выводить, архив не
удалять. Актуальные installer SHA в
observatory/v1/OWNER_VIEWER_MANUAL_SETUP.md.


## 20.10.2026 — Notifier quick Textbox: 5.7.4 large paste safeguard

При закрытой панели + тяжёлые списки GM истории больше не перечитываются
на каждом UI render. От 12k символов большой текст сохраняется целиком
только в RAM текущей вкладки и показывается краткий preview; ⧉ копирует
полный текст, × очищает его. После клика ➤ сохраняется exact оригинал
через прежнюю pipeline, без нового route и фоновой автопубликации.
Quick send свыше 64 KiB UTF-8 теперь отказывается до записи, т.к.
у Viewer writer оригинала текущий cap 65536 bytes. Обновить
существующий Tampermonkey userscript из Repo вручную; Edge smoke и
прямое профилирование заморозки ещё не проводились.


## 20.10.2026 — закреплённый header и четырёхколоночный Owner Viewer (source)

Изменён исходный UI observatory/v1/owner_viewer.py: sticky topbar,
сессии, задачи, разноцветные записи (оригинал/события/полные AI),
панель подробностей; границы колонок можно перетаскивать или менять
клавиатурой. События отображают шаги, сообщения показывают сохранённый
полный текст. При отсутствии оригинала Viewer сообщает об отсутствии.
API, экспорт архива, scopes и архив не менялись. Новые версии исходника
применяются владельцем только через существующую защищённую установку
с SHA из observatory/v1/OWNER_VIEWER_MANUAL_SETUP.md и ручной
перезапуск Viewer. Без автоматического обновления Windows и Docker.


## 19.10.2026 — компактный главный экран Owner Viewer (source ready)

В observatory/v1/owner_viewer.py форма подключения сессии, инструкция
и привязка Notifier теперь открываются только кнопками верхнего toolbar.
По умолчанию остаются сессии, задачи и история; первый доступный task
открывается автоматически. Данные и серверные маршруты не изменены.
Новый Viewer source не равен установленной защищённой Windows-копии.
Для применения нужен штатный ручной цикл закрыть Viewer → сверить SHA
→ переустановить защищённую копию → запустить; инструкция с новым SHA:
observatory/v1/OWNER_VIEWER_MANUAL_SETUP.md. Repo Docker не
перезапускался; реальный Owner Edge smoke ещё не выполнен.


## 19.10.2026 — Stateless Observatory bootstrap (source ready)

Old generated Repo instructions mixed permanent rules and session,
chat, enrollment, sequence IDs. New repo_service.py bootstrap
prints short ID-free instructions. Live API instructions remain
old until owner-controlled Docker service restart. New
repo_task.py event/message reads enrollment from registered
Docker archive using current-message session/chat/task IDs and
never relies on past prompt memory. Notifier v5.7.2 supplies
fresh fully instantiated sender commands per request and
does not print private writer/observer keys. Planning Helper
ordinary Observatory TextModule updated. Old sender commands
remain supported. No owner environment or live service restarted.


## 19.10.2026 — Observatory TextModule and AI-assisted Notifier references

Generated Observatory instructions were checked and contain Chat ID,
reporting session ID, session enrollment ID, route, Repo event and
full-message senders, and receipt caveats. The new source-library
TextModule fortis.observatory-telemetry adds only a concise reminder
(no secrets or fixed IDs). Until imported into existing Planning Helper
GM through its Import UI or published through Helper Save GitHub and
retrieved by Sync missing, the source file is not active locally.
Notifier v5.7.1 supports explicit user-confirmed bulk paste of existing
module IDs; validates every reference and nested dependency against
the current Helper catalog atomically. AI can propose IDs read-only
from Fortis Repo via notifier_module_refs.py; it cannot silently
modify owner browser GM. No Notifier TextModule editor added.


## 19.10.2026 — Notifier Profiles and shared Helper modules (source)

Notifier 5.7.0: fourth ⚙ button, profiles, attach-only local Helper
TextModules, module ordering, code-registered behavior toggles.
Planning Helper 0.40.9 remains sole editor/GitHub client. Source
GM local snapshot stays inside Helper; read-only same-origin
BroadcastChannel broadcasts on every verified snapshot write.
Notifier holds only profile module IDs; no duplicate persistent
module text library or new module editor in Notifier. Missing
references/cycles/Helper catalog block module-based sends; exact
user original unchanged. Existing queue/upload/Observatory flows
preserved. Manual owner Edge userscript updates and real cross-
Tampermonkey browser acceptance are pending. No owner Windows
configuration, Docker archive, or GitHub live state changed.


## 19.10.2026 — chronological task cards and original uploads (source ready)

The approved owner Viewer source now lists tasks by earliest archive-accepted timestamp with an order number, local browser timestamp, and exact-original excerpt or explicit placeholder. A session-scoped owner-only pairing action lets Tampermonkey v5.6.6 read activity and conditionally upload original text to the one Repo Docker Observatory through a restricted localhost 18755 transport using docker exec stdin. Full AI messages still travel directly via Fortis Repo. No legacy/unpaired task migration. Real owner Windows re-install and Edge smoke are pending. See observatory/v1/OWNER_VIEWER_MANUAL_SETUP.md. PowerShell installer parsed with 0 errors.


## 19.10.2026 — Fortis Textbox v5.6.5: Enter sends after 1s native composer dwell

Right-hand Notifier textbox now treats Enter as submit, with Shift/Alt+Enter
as newline and IME/repeated-key safeguards. The persistent original
and task_id must be verified in Tampermonkey BEFORE native composer
insertion. The old queue controller receives an opt-in
minComposerDwellMs=1000 only for the new textbox. It inserts
into ChatGPT native composer promptly, re-checks ownership and
waits at least 1000ms before clicking the real Send. If the text
was edited during delay, click is aborted; old queue, checkpoint,
upload-after-file and plus-panel paths are unchanged. Version 5.6.5;
129 JS tests expected. Updating owner Edge/Tampermonkey remains
a separate manual action, not a Repo connector operation.


## 19.10.2026 — Notifier v5.6.4: LIST_FAILED fixed with per-chat GM index (source)

Real owner Edge v5.6.3 reported LIST_FAILED. Native GM key
enumeration cannot be relied upon; v5.6.4 writes verified
per-chat index of task storage keys via GM_getValue/GM_setValue.
Existing exact-original record and index are BOTH read back
before sending. Normal enumeration still merges legacy entries;
old unknown unindexed records are retained even if unavailable
for discovery while GM_listValues is broken. Index failure stops
Send; queue/delay/upload original buttons and Repo→Docker
assistant telemetry unchanged. **122 JS tests PASS**;
Tampermonkey v5.6.4 installation under alexa and live send
need manual owner retest. No browser storage reset performed.


## 19.10.2026 — Fortis Textbox v5.6.3 source storage fix

Screenshot from owner Edge v5.6.2: save-before-Send failed with
generic toast; original stayed in textbox and did not send.
No evidence of which GM step failed. Notifier v5.6.3 implements
JSON-string GM record roundtrip (object-format backward compatible),
exact readback plus key-list verification, safe UI rerender, and
stage-specific nonsecret failure codes. No deletion/retry.
116 JS tests PASS. Requires owner Tampermonkey update to verify
real Edge behavior. Existing 3 floating buttons, Repo sender,
Docker Observatory and persistent archive remain unchanged.


## 19.10.2026 — Notifier v5.6.2: текстбокс справа от трёх кнопок (source-only)

Пользователь потребовал НЕ менять три существующих плавающих
кнопки Notifier (◷ checkpoint по таймеру, + очередь/delayed,
⇧ автоотправка после загрузки файла), а добавить текстбокс
справа и оставить общую возможность перетаскивания.

**Выполнено в source** /workspace/repos/tabnotifier-fileautosend-autochat:
в src/upload-button-ui.js справа прикреплены поле и отправка ➤;
двигается вся группа за старые кнопки или ⠿. Сам ввод текста
не запускает перетаскивание. Новая отправка использует уже
проверенный persistentMessageController.saveAndSend:
сначала GM оригинал/task_id, потом штатный native ChatGPT
Send, без изменения очередей и delayed/file handlers.
Сгенерирован userscript v5.6.2, JavaScript tests 112/112 PASS.
Настоящая установка в Edge/Tampermonkey ещё **не выполнялась**;
нужно ручное обновление и browser smoke, не автоматическое
редактирование owner GUI из Fortis Repo/G2. Старые сохранённые
сообщения и единый Docker archive не затрагивались.
Точный исходник пользователя в Docker пока не переносится;
этот UI этап не решает браузерный транспорт.


## 19.10.2026 — Edge Observatory: самостоятельная регистрация сессий

Обновлён Windows-alexa Viewer из одного Docker Observatory:
теперь локальный интерфейс по адресу http://127.0.0.1:18755
позволяет самому зарегистрировать выбранную ChatGPT беседу,
указав URL и название; получить и скопировать инструкцию для этой
же сессии. Регистрация идёт через точный
docker exec fortis-repo-test python3 .../repo_service.py register,
а для инструкции — узкий Repo-local CLI instructions. У существующего
Chat ID при повторном подключении переиспользуется текущая
Repo-сессия вместо обычного дубля.

Это **не** подключение G2 и **не** отдельный Windows archive.
AI продолжает отправлять события и полные ответы через Fortis Repo,
а exact оригинал от браузерного Notifier по-прежнему требует
отдельной проверенной доставки. Windows viewer имеет только одну
дополнительную мутацию: регистрацию по валидному
chatgpt.com/c/<id> и безопасному названию, с обязательным
временным viewer Bearer, exact Origin и ограниченным JSON размером.
Никаких owner-credential, pairing writer keys или сообщений через
этот POST. История остаётся в едином Docker volume.

**Важное применение:** исходник owner_viewer.py обновлён только в
совместно доступном source checkout. Установка под alexa —
**отдельное пользовательское действие**: сначала закрыть текущий
Viewer, затем повторить approved manual installer с новым SHA,
после чего запустить защищённую локальную копию. Установка в
Windows не выполнялась инструментами этого чата; реального
UI Edge обновлённой копии ещё не проверяли.
Инструкция: observatory/v1/OWNER_VIEWER_MANUAL_SETUP.md.

## 19.10.2026 — ручной Observatory в Edge из alexa (готовые исходники; owner install pending)

AI/телеметрия остаются `ChatGPT → Fortis Repo tool → Repo Docker spools →
один persistent Docker volume`, без G2 и Windows owner HOST.
Добавлен ручной **read-only** просмотр из `alexa`:
`observatory/v1/repo_viewer_export.py` (внутри существующего контейнера
через docker exec) и `observatory/v1/owner_viewer.py` (owner Windows
`127.0.0.1:18755`, временный Bearer только из owner-консоли, Edge UI).
`Start-FortisObservatory.cmd` запускает просмотрщик вручную; если
Observatory остановлен, Python-скрипт умеет повторно запустить
**существующий** сервис в том же контейнере, не создавая второго архива.
`Install-FortisObservatoryViewer.ps1` создаёт PIN-версию в
`%LOCALAPPDATA%\FortisObservatoryV1\Viewer` после явной проверки
`alexa` SID, контейнера, Docker volume, NTFS ACL и ожидаемого SHA-256.
Исходные Windows файлы **не установлены**; реальный Edge owner
и guest-negative доступ **не проверены**. Полное описание:
`observatory/v1/OWNER_VIEWER_MANUAL_SETUP.md`. Код просмотра нельзя
отправлять в чат. Реальный original из Notifier пока не приходит автоматически.

Тесты: 56/56 Python ранее + новый Edge-launch test; PowerShell AST
`Install-FortisObservatoryViewer.ps1`: 0 parse errors. Live Repo
Observatory продолжает работать в контейнере. Это SOURCE-READY,
а НЕ installed/production-owner-pass.

## 19.10.2026 — ТЕКУЩЕЕ РЕШЕНИЕ пользователя: AI → Fortis Repo → единый Docker архив

**Fortis Repo — основной инструмент AI.** Для отправки событий и
полного текста **собственных** interim/final ответов ChatGPT вызывает
именно Fortis Repo tool, который в Linux-контейнере исполняет
`observatory/v1/emit.py` и `observatory/v1/repo_message_sender.py`.
Не нужны G2, owner Windows Host, Windows relay, открытие Docker TCP-порта
или отдельный Windows Observatory. Путь в Git-исходниках
`/workspace/repos/tunnel/observatory/v1` — **историческое имя каталога
проекта**, не сетевой туннель и не новый transport.

**Working route:** `ChatGPT (реальный вызов Fortis Repo tool) →
/workspace/repo/fortis-observatory-repo-v1/inbox/repo` (короткие
events) + `.../inbox/messages` (full assistant body из UTF-8 stdin) →
один Python Repo Observatory → единый `archive/sessions` в том же
Docker volume. Если сервер выключен, файловый stage не зависит от
HTTP, а importer обработает запись позже. `STAGED_ONLY` означает
только успешный файловый stage, не accepted archive; при недоступном
tool нельзя заявлять о сохранении. Реальный вызов модели автоматически
из prompt не гарантирован, проверять отдельно на целевой сессии.

**Важный отдельный участок:** точный оригинал пользователя до
дополнения prompt сохраняет Tab Notifier в браузере. Модель не должна
восстанавливать exact original по своему ответу. Его последующая
запись в тот же Docker archive после accepted event — отдельно
решаемая browser/Notifier интеграция; **она не нужна для AI→Repo
доставки** и не является поводом запускать G2/owner relay.
Готовые `owner_browser_relay.py` и Windows helper остаются
**неразвёрнутыми факультативными source-экспериментами**, а не
утверждённой/необходимой архитектурой.

Для явно зарегистрированной `reporting_session_id` и текущего
`task_id` используй инструкции Repo-сервиса:
`python3 /workspace/repos/tunnel/observatory/v1/repo_service.py
instructions --session rs_32hex`. Он показывает enrollment ID и
конкретные команды Repo sender. Не передавай сессию/привязку из
другого чата и не создавай реальную сессию молча. Не раскрывай bearer,
observer/writer keys или полный текст через metadata event summary.
Данные Repo volume доступны обладателям полномочий Fortis Repo.

## 19.10.2026 — Browser↔Docker narrow relay (SOURCE-ONLY; NO WINDOWS LISTENER)

Добавлена source-only пара helper-компонентов в `observatory/v1`:
`owner_browser_relay.py` (Windows owner-local 127.0.0.1:18754,
только 3 browser маршрута, cap keys, no CORS, GET/POST guards,
docker exec fixed argv with stdin-only request) и
`browser_relay_dispatch.py` (Docker-side проверенный forwarding
только к существующему Observatory 127.0.0.1:18754).
`repo_browser_pair.py` выдаёт scoped pairing JSON **только в защищённую
консоль owner** при явном вызове, не через HTTP/ChatGPT logs.
Это НЕ второй Observatory, архив остаётся единым в Docker.

Python source tests `test_browser_relay.py` 6/6 PASS с синтетическим
локальным запросом → мост → event/original writer → read-back.
Windows relay фактически НЕ установлен/НЕ запущен. Из restricted
Windows проверка port 18754 не дала соединения; это не тест owner
или ACL. Реальный мост требует отдельно одобренной protected
owner-install копии, pinned hashes, проверенного Docker container,
guest-negative/owner-positive и настоящего Edge/Tampermonkey smoke.
Инструкция: `observatory/v1/BROWSER_RELAY_OWNER_INSTALL.md`.
Ни Windows network/ACL, ни Docker port binding, ни работающий
Observatory в этой операции не изменялись. В частности, никакой
pairing-code не выводился в чат.

## 19.10.2026 — CURRENT: единый архив в Fortis Repo Docker (Candidate v8)

По решению пользователя Observatory запускается и хранит всю историю **в том
же Docker volume**, который доступен Fortis Repo. Windows Observatory больше
не является обязательным компонентом. Сохраняются **раздельные очереди
внутри одного хранилища**: `inbox/repo` для V2 metadata событий,
`inbox/messages` для **полных AI interim/final messages**, затем
`archive/sessions/.../events`, `user_messages`, `assistant_messages`.
Общий корень: `/workspace/repo/fortis-observatory-repo-v1`.

Доступ Fortis Repo к этому volume означает, что полные тексты доступны
субъектам с правами Repo. Это **не** Windows owner-private storage. Не
класть сообщения в старый общий event inbox, логи, Git, URLs или argv;
не открывать контейнерный loopback на Windows/network без отдельного review.
Repo HTTP: `127.0.0.1:18754` только внутри контейнера; 0700 каталоги,
0600 token и файлы, owner bearer для истории, отдельный writer capability
для точного original пользователя.

**Текущие исходники:** `repo_messages.py` реализует ограниченный
(256 KiB/body, 512 pending files) offline-first spool full AI bodies:
`message_id` + `task_id` + session/enrollment ID + interim/final,
JSON escaped Markdown с SHA256/read-back, idempotent duplicates и
private quarantine для invalid/conflicting payload. Временное отсутствие
сессии приводит к deferred, неверный enrollment — отказ.
`repo_message_sender.py` принимает UTF-8 body только из STDIN, никогда
из CLI аргумента, выводит `STAGED_ONLY`, а не ложный acceptance.
`repo_service.py` в одном процессе опрашивает обе очереди и имеет CLI
`status`, `sessions`, `register`, `instructions`, `history`,
`archive-original` (original via STDIN и только после accepted signal)
и `stop`. Полная история выдаётся по явному запросу
`GET /api/repo-history?session=...&task=...` с bearer либо
`python3 repo_service.py history --session rs_... --task task_...`.
Оригинал пользователя через writer-API сохраняется в **том же Repo archive**.

**Важно:** оригинал от Tab Notifier автоматически в Docker ПОКА НЕ
передаётся: браузерная связка ранее целилась в Windows 127.0.0.1:18753,
а новый сервис слушает Docker loopback 18754; требуются отдельные
bridge + browser security/permissions. Реальная модель должна иметь
Fortis Repo tool, чтобы вызывать sender, а не только текстовую подсказку.
Приватная история Docker доступна Repo, не owner Windows.
Это не доказывает DOM-equivalent запись AI ответа. Отсутствует
автозапуск после перезапуска Docker и backup на случай удаления volume.

**Source tests:** `test_v1.py` 34 + `test_repo_service.py` 4 =
**38/38 PASS**. Test lifecycle: сервер STOP -> V2 metadata и три
полных AI messages STAGED -> сервер START -> exact body read-back;
user original archived после первого accepted event, повтор idempotent,
подменённый message_id карантинируется, неизвестная сессия ждёт.
Windows owner не изменён; новые HTTP credentials не публиковались.

**Примеры (через Fortis Repo, вместо плейсхолдеров настоящие ID):**
`cd /workspace/repos/tunnel/observatory/v1`
`python3 repo_service.py status`
`python3 repo_service.py sessions`
`python3 repo_service.py register --chat-id CHOSEN_CHAT_ID --title "Repo Session"`
`python3 repo_service.py instructions --session rs_32hex`
`python3 repo_service.py history --session rs_32hex --task task_32hex`
`python3 repo_service.py archive-original --session rs_32hex --task task_32hex`
читает **пользовательский exact original** из UTF-8 STDIN только после
accepted event; не вставлять body в командную строку.
`python3 repo_message_sender.py --session rs_32hex --session-task task_ENROLLMENT
--task task_CURRENT --kind interim` читает **AI body** из UTF-8 STDIN;
для последнего сообщения `--kind final`, при retry прежний `--message-id`.
Никакой реальной пользовательской сессии в Repo не регистрировать
молча. Полные тексты выводятся CLI `history` только по явному запросу.

**Status:** исправленная single-Docker цель кодирована и покрыта source
тестами; live Repo process требует restart на новой версии. Никаких
Git source commit/push, owner Windows deploy или браузерного bridge
данное изменение инструкций не выполняет.


## 19.10.2026 — Repo-first Observatory внутри Fortis Repo Docker (SOURCE + RUNNING METADATA MODE)

**Рабочий экземпляр** отдельного `repo_service.py` использует
`127.0.0.1:18754` **внутри Linux Docker**; не занимает owner Windows
`127.0.0.1:18753` и не перезапускает туннели. Состояние находится
в постоянном **внутреннем volume** `/workspace/repo/fortis-observatory-repo-v1`:
`archive/` (только metadata Markdown), `inbox/repo/` (короткие JSON V1/V2),
`.repo-http-token` (только внутренний HTTP-access ключ), `.service.lock`,
`.service.pid`, `service.log`. Каталоги требуют mode 0700, token mode 0600;
никакие реальные owner ключи не передаются.

**Критическое разграничение:** Repo контролирует этот volume, так что он
**не owner-private** по модели Windows. В режиме Repo у `Application`
явно отключены `GET /api/message-writer-pair` и
`POST /api/user-messages` (403 даже с ключом). Нельзя помещать в
Repo inbox или metadata archive полные тексты пользовательских или AI
сообщений, owner credentials и реальные секреты. Source owner Windows
по-прежнему сохраняет штатные функции writer — flag по умолчанию не менялся.
Контур Repo предназначен для **событий, разработческих испытаний и
управления через Fortis Repo**.

**Команды через Fortis Repo:**
- `cd /workspace/repos/tunnel/observatory/v1 && python3 repo_service.py status`
- `python3 repo_service.py sessions` — только session ID/state/count, без body.
- `python3 repo_service.py register --chat-id <id> --title "Repo Session"` —
  явная регистрация metadata-only беседы, не создавать её молча.
- `python3 repo_service.py instructions --session rs_<32hex>` —
  инструкция для разрешённого emitter; sender пишет в
  `/workspace/repo/fortis-observatory-repo-v1/inbox/repo` через `emit.py`
  (только безопасные metadata summary).
- `python3 repo_service.py stop` — остановка **только Repo-сервиса** после
  проверки идентичности PID; никакого owner Windows restart.
- Для ручного запуска, когда сервис остановлен (из **Repo Docker shell**),
  сначала создать приватную папку volume, затем:
  `setsid nohup python3 -u /workspace/repos/tunnel/observatory/v1/repo_service.py run --state-dir /workspace/repo/fortis-observatory-repo-v1 --port 18754 >/workspace/repo/fortis-observatory-repo-v1/service.log 2>&1 </dev/null &`
  Сервис не включён в startup-policy контейнера и **не перезапускается сам**
  после Docker recreation/reboot; данные остаются в именованном volume
  пока volume сохранён. Для автозапуска потребуется отдельное разрешение.

**Проверки в этой разработке:** Python `test_v1.py` (34 теста),
`test_repo_service.py` (1 интеграционный тест процесса) —
**35/35 PASS**. Отдельно живой Repo `status`: `running`,
локальная страница HTTP 200, API без авторизации 401, private user writer 403.
Тест процесса: registration → STOP → stage трёх различных V2 `event_id`
с одинаковым sequence при выключенном сервере → RESTART → три accepted
Markdown с `sender_sequence` и ноль оставшихся JSON; token защищён 0600.
Реальная целевая ChatGPT вкладка и Windows owner browser **не проверены**.
`Tab Notifier` сейчас рассчитан на Windows origin `127.0.0.1:18753`:
Repo `18754` напрямую не является совместимой заменой для browser pairing
и не обеспечивает автоматическое сохранение user originals. Доступ UI
из Edge потребует отдельно одобренный безопасный HTTP bridge/port mapping
и review авторизации; в этой работе его не открывали.

**Repo V1 не является вторым доверенным архивом переписки.**
Новая кандидатная архитектура (Plan v7) ставит metadata Observatory
Repo как основной доступный для tool workspace; Windows-private archive
и Stage2 защищённые AI-тексты остаются отдельной задачей. Никакого
source Git commit/push или owner deployment эта служба не означает.


## 19.10.2026 — Observatory offline file spool corrections (SOURCE TESTED ONLY)

Текущий контракт: разрешённый локальный `emit.py` пишет **только короткие
JSON события** в устойчивый sender inbox даже когда owner Observatory выключен.
`STAGED_ONLY` означает лишь файловую запись. `store.poll()` после запуска
принимает валидные пакеты в защищённый Markdown; первый accepted V2
сигнал по `task_id` разрешает Notifier архивировать оригинал через отдельный
owner writer. Полные ответы AI в этот JSON inbox **не** писать.

**V2 изменение последовательности:** в sender JSON `sequence` остаётся
необязательным с точки зрения доверия **hint** (CLI по-прежнему требует
передать число, совместимость сохранена). При совпавшем `sequence`
двух разных событий V2 приёмник назначает следующую свободную
`sequence` в owner архиве; оригинальное число записывает как
`sender_sequence`. При отсутствии конфликта номер сохраняется. V1
**не изменён** и продолжает отклонять коллизии. Сортировка новых файлов
в очереди приближённо соответствует времени их локальной записи:
`<20 digit time_ns>-<32hex>.json`; старые `<32hex>.json`
поддерживаются. Временная метка отправителя и порядок файлов
**не являются достоверным порядком действий ChatGPT** при параллельности.

**Неизвестная сессия:** если session.md отсутствует временно, V2/V1
входящий валидный JSON не удаляется, `poll` отражает
`deferred_session` и `state=pending_sessions`; при следующем
опросе после восстановления session.md пакет может быть импортирован.
Если session существует, но route или enrollment ID не совпали —
`unknown_session` остаётся *постоянным отказом* с удалением пакета.
Нарушенная схема также отклоняется. Старый файл не становится
accepted только от того, что остался в папке.

**Лимиты / privacy:** входящая очередь ограничена **512 JSON файлов**,
полным накопителем она не является. При переполнении `stage`
возвращает ошибку и эмиттер сообщает `NOT_STAGED`, не обещая доставку.
Неизвестные сессии сохраняют место в этой очереди; требуется контроль
дефекта/ёмкости, стратегия ручной диагностики без чтения приватных
текстов. Папка Repo/G2 **не** owner-private, поэтому принимает
только безопасные события и маркеры, **не полные тексты AI или пользователя**.

**Не подтверждено:** фактическая доступность sender из целевого чата
ChatGPT, совпадение sender inbox c owner Windows receive inbox,
owner/guest ACL и writer API установленной копии, end-to-end browser.
Old source hashes в `OWNER_INSTALL.md` больше не следует считать pin
этого source; runbook intentionally fail-closed. Требуются review,
новый pin и отдельное одобрение owner install. Нет Git commit/push,
не менялись owner Windows/runtime/source permissions в этой работе.

**Следующий этап:** отдельно подтвердить путь отправитель→файлы→owner
импорт offline/reconnect и security; затем Stage 2 — **защищённая**
локальная очередь полных AI-сообщений с отдельным `message_id`,
`task_id` и sender_claim, без расширения Repo/G2 event inbox.
Серверная предрегистрация каждого `task_id` не является обязательным
условием offline файлового импорта; это отдельная необязательная мера
повышения гарантии происхождения сообщения.


## Observatory V1 / Notifier Stage 1C — 19.10.2026 (SOURCE TESTED ONLY)

Добавлена **запись полного оригинального сообщения пользователя в защищённый
owner archive после первого принятого V2 сигнала того же task_id**.
Новый `POST /api/user-messages` принимает только JSON
`reporting_session_id/conversation_id/task_id/original_text` через
дополнительную **сессионную write-capability** `X-Fortis-Message-Writer-Key`.
Ключ просмотра Observatory для записи НЕ подходит; owner bearer панели
сам по себе не подходит. Никакого текста через Repo/G2 inbox и в URL.

Код привязки с правом записи выдаётся только при **явном действии владельца**
«Код с правом записи сообщений» в owner-панели, через owner-authenticated
`GET /api/message-writer-pair`. Обычный «Код для Tab Notifier» остаётся
**только для чтения**. Новый код содержит и observer key, и отдельно
message_writer_key. Вставлять только через меню Notifier «Привязать текущий
чат», НЕ в сообщение ChatGPT. Старые read-only пары продолжают работать
без возможности архивирования исходника; нужна ручная повторная привязка
с новым кодом, а не расширение прав старого ключа.

Owner writer перед записью перечитывает принятый Markdown V2 event/marker
по ID и сессии; STAGED_ONLY не годится. Запись кладётся в
`sessions/rs_.../user_messages/task_....md` (JSON-escaped UTF-8 Markdown
с exact оригиналом при read-back). Метаданные и индекс уникальности содержат
только ID/хэш/времена, не сам текст. Повтор того же payload идемпотентен,
другая версия текста под тем же task_id — конфликт. Архивный ACK не
содержит тело чата. При ручном удалении сохранённого файла индекс предотвращает
его молчаливое воссоздание. Лимит оригинала 64 КиБ UTF-8, превышение —
явный отказ; локальная копия остаётся у пользователя.

В Notifier добавлен write monitor: отправляет original_text после
`activity_status=accepted`, только с дополнительной writer-capability,
повторяет после временной сетевой ошибки, сверяет SHA-256 receipt с локальным
текстом, и лишь затем устанавливает `archive_status=archived`. При ошибке,
отсутствии writer key, чужом ID или рассинхронизации статус остаётся pending.

**Не выполнено:** owner Windows deployment/pin/ACL verification, live browser
smoke, guest-negative на реальном Windows SID, защита/ротация capability в
реальной установленной среде, уведомление через 10–15 секунд, полный AI
message archive и task profiles. Repo tests не являются разрешением запускать
RW-source под владельцем. Git commit/push исходников не выполнялись.


## Observatory V1 / Tab Notifier — Stage 1B, 19.10.2026 (SOURCE ONLY)

Добавлен **read-only**, session-scoped `GET /api/task-activity?session=rs_...&task=task_...`
с `X-Fortis-Observer-Key` (отдельный observer capability, не owner bearer).
Ответ содержит только идентификаторы сессии и задачи, `found`, вид/sequence и
`accepted_unix` первого **принятого** V2 события или метаданного маркера,
`provenance=sender_claim`. Полные тексты, summaries, ключи и owner-токен не возвращаются.
`STAGED_ONLY` не считается принятием. API читает только существующие Markdown
записи в защищённом owner archive. Если файл вручную удалён, он больше не
участвует в ответе. Старый `/api/observer-status` и V1 events не изменены.

Notifier хранит `reporting_session_id` вместе с локальной записью **при отправке**,
если чат уже привязан к Observatory. Он опрашивает accepted activity именно
по ID такой записи (в том числе после reconnect/reload). После подтверждения
сохраняет локально `activity_status=accepted`, `first_activity_at` и тип события;
**`archive_status` остаётся `pending_activity`**. Перенос user original в owner
архив, write API, 15-секундное UI-уведомление и полный AI text — НЕ реализованы.
Сообщение, созданное без привязки, остаётся локально без автоматической
привязки к новой сессии. Сама V2 телеметрия добровольна и может отсутствовать.

В файлах `observatory/v1/{server.py,store.py,test_v1.py}` и в исходниках
Notifier выполнены source changes и тесты. Windows owner V1 и Tampermonkey
**не установлены/не обновлены/не проверены** в этой работе; в прежнем Git
index и live процессах изменений нет. Правила E46, owner-positive/guest-negative,
source pin и ACL перед возможным отдельным deployment сохраняются.


## Исправления V1 после review (18.10.2026) — только исходники

В `observatory/v1` исправлены пять воспроизведённых дефектов обработки
JSON, Markdown, конфликтующих событий, переполнения очереди и времени
последнего сигнала. В Repo прошли 19 тестов V1 и 47 смежных тестов.
Установленный Windows Observatory и G2/Repo не изменялись; перед запуском
сохраняется gate E46, проверка ACL и защищённого расположения исходников.


## Новый Observatory V1 (18.10.2026) — SOURCE ONLY

Добавлена независимая версия [observatory/v1](../observatory/v1/README.md):
ручная регистрация Chat ID, события работы и файловый Markdown-архив.
Существующий owner Observatory, G2/Repo и Docker не менялись; Git
commit/push не выполнялись. Для Windows установки обязателен
review/pin шести файлов в owner-protected директории, ACL/HTTP gate E46
и отдельная actual Windows acceptance. Из Repo RW checkout не запускать
owner-приложение. Подробные пути и ограничения — в runbook V1.

## Актуальный выбор source/deployed и owner действий

G2 entry: [source](../runtime/host-g2/runtime-api-migration/start-g2-guest-session.ps1);
gate: [source](../runtime/host-g2/g2-stdio-gate.py); actual guest login/key отдельно от Git.
Repo deployed E38 AFTER sources:
[run](../runtime/host-g2/runtime-api-migration/repo-run-tunnel.ps1),
[control](../runtime/host-g2/runtime-api-migration/repo-control.ps1).
Старые repo-mode/run/control — BEFORE, НЕ current deployed source.
Linux [Bridge source](../runtime/repo-mode/fortis-mcp-bridge.mjs) не обновляет live volume
автоматически. Old owner HOST retired, не запускать при key rotation ради docs.
Изменения E44 — Markdown/JSON, без reinstall/runtime deploy/restart/commit/push.
[Итог](ISOLATION_GUIDE.md).

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
| Native Repo guidance / legacy UI | fortis-mcp-bridge.mjs, installed /workspace/repo/.fortis/mcp-bridge.mjs | Копия в volume, restart Repo Tunnel, refresh connection |
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


### Observatory V2 message-ID source candidate (19.10.2026; не deployed)

Изменения только в `observatory/v1/` в Repo: приём записей `version=2`,
где `task_id` — один UUID4 на пользовательское сообщение, а `session_task_id`
сохраняет старую проверку принадлежности подключению. Добавлены
`user_message`/`assistant_message` **метаданные**, без текста переписки;
общий `sequence` сохраняется. Старый формат V1 принимается без изменений.
Состояние/архив маркеров видны owner-панели, read-only статус Notifier
пропускает маркеры, чтобы не менять семантику completed. Изменены
`store.py`, `emit.py`, `server.py`, `client.js`, регрессионные тесты и README.
Это source-only подготовка, **не** разрешение обновлять owner Windows copy.
Проверка реального Windows runtime, защищённых путей и публикации отсутствует.
Подробности и границы приватности — `observatory/v1/README.md`.

**Further fail-closed guard:** the owner-private Windows relay install
must include `approved-owner.json` pinning exact Windows owner SID and
approved Repo container. Wrong identity/container or absent config
prevents starting. This file is not present yet, and validation of
real owner ACL/guest-negative remains pending.


## 22.10.2026 — versioned Local Loader target 5.7.28

Prepared byte-identical chatgpt-tab-notifier-5.7.28.user.js alongside the
current generated bundle. SHA-256:
d506f6d7824ac1fcf868290da44f9f2e991acd42514fac31bdb6060fbedc99c5
Use the EXISTING Local Loader, preserve @name/@namespace/GM storage,
change its @version to 5.7.28 and @require to:
file:///C:/Users/alexa/Repos/tabnotifier-fileautosend-autochat/chatgpt-tab-notifier-5.7.28.user.js
Keep GM_listValues grant. A fresh require URL selects the exact reviewed
bundle. No second enabled Notifier, no GM cleanup, no runtime restart by
this preparation. Actual browser installation/version remains unverified.
