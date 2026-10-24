# Fortis Observatory V1 — ручные сессии и события работы

## 21.10.2026 — latest-task v2 активен в Docker/export; Notifier source 5.7.26

Владелец подтвердил все четыре TRUE installer для Viewer SHA
4df003701e5cc993a9914687c9211eba890d56eea6c71dfa030a6238f3744509.
Переключён только процесс Observatory на immutable candidate:
/workspace/repo/fortis-latest-task-20261021/candidate/repo_service.py.
State dir прежний, loopback 18754, PID 12953. Fallback v1 сохранён рядом.
Manifest SHA 74b1b062da2396ceb306f6a5a7bee895921292901b3e79554c729dd2b1c38f4f.
Проверка после запуска: API task_overview v2/basis latest_task, observer
чтение двух уже привязанных сессий OK, owner intents недоступны анонимно
и по observer key (401). Прежние пары/число событий сохранены, ключи
совпали до/после. Текущее число сессий 3. Откат не потребовался.

Проверенные source файлы модели/export/Notifier перенесены из isolated work
в /workspace/repos. Сессия теперь отражает последний пользовательский таск;
исторические счётчики в UI скрыты, карточки старых задач сохраняют статусы.
DOM использует одноцветные часы/галочку; только свежая scoped Observatory
сводка даёт пять статусных цветов. Local upload — одноцветная стрелка.
Node 261/261, Python 162/162, build:check, synthetic Viewer UI PASS в candidate.
Notifier source 5.7.26 SHA:
a11e40c372e46c3bcc33e278dce36595d79a1eb34788eb5bd5779bc38ae8e6b2.

Docker/container/Tunnel не перезапускались. Новых прав, intents, тестовых
событий/оригиналов и Send не создавалось. Windows Viewer установлен по
подтверждению владельца, но запуск и browser live QA v2 ещё не подтверждены.
Notifier Loader/GM storage в Edge не редактировались; версия в браузере
остаётся непроверенной (последняя подтверждённая 5.7.23). Следующий шаг:
запуск установленного Viewer, проверка текущих статусов, затем обновление
одной существующей копии Loader с сохранением name/namespace/GM originals.

## 21.10.2026 — этап D: favicon Notifier 5.7.25 (source-only)

Существующий GET /api/observer-status дополнен task_overview для той же
сессии и того же observer key. Сводку строит общий session_overview;
только счётчики/статусы, без task_id, текста или ключей. Новых маршрутов,
writer прав и расширения Windows allowlists в D нет.
Notifier использует пять цветов Viewer: жёлтый ожидание, синий работа,
фиолетовый длительная тишина/неизвестность, зелёный reported completed,
красный только reported failed. Черновик/blocked — без цветного favicon,
без серого. Ожидание другой задачи — отдельная жёлтая отметка;
непрочитанный ответ — независимая белая точка. Upload имеет приоритет,
реальная DOM-генерация — синий значок; простой armed Send не означает работу.
DOM unread без сводки имеет зелёный колокольчик, просмотренный — native icon.

Сводка привязана к chat/session/generation, не восстанавливается из storage.
Смена чата/привязки, отключение, ошибка доступа/связи или давность >20 секунд
снимают цвет AI-статуса с явной подписью в title; failed не создаётся.
Устаревший callback не освобождает новый polling request. Старый API
сохраняет прежние уведомления и показывает «старый API» вместо AI-цвета.
Исторический completed не воспроизводит уведомление о новом ответе.

Node 256/256 и build:check PASS; новые HTTP проверки 4/4 PASS.
Полный Python прогон Observatory: 158/158 PASS; synthetic Viewer UI PASS.
Checkpoint: /workspace/repo/fortis-intents-step-d-20261021.
Подготовлены только исходники. Windows/Edge live НЕ проверялись;
установленная рабочая версия 5.7.23 и службы не менялись. Не устанавливать
и не перезапускать по историческим командам без отдельного rollout.
Notifier 5.7.25 source SHA256: 4af2e2021c69a5200bfcaf10b53bae030524bdcfce05506395bd5f086ff037c9
Viewer source SHA256 остаётся 81bfb0980bba0daea94db7aec477da009c863c3ebf59dbfcc28fd75b69299ea3.
См. [контракт A/B/C/D](TASK_INTENTS_V1.md).

## 21.10.2026 — этап C: основной список intents и цветные статусы (source-only)

Read-only Repo export объединяет сохранённые intents и архивные задачи;
owner /api/state получает additive task_overview, owner /api/tasks —
персональное состояние, подпись и разрешённый цвет. Старое session.state
сохранено для диагностики, архив оригиналов/истории не меняется.
Классификатор task_display/session_overview общий в task_intents.py:
жёлтый ожидание, синий работа, фиолетовый silence/unknown, зелёный completed,
красный только failed. Черновик и blocked — текст без цветной маркировки.
Каждый счётчик отдельный; завершение другой задачи не скрывает ожидание.
При ошибке/устаревании данных строки сохраняются и явно помечаются,
актуальная цветная маркировка снимается, failed не создаётся.

Новые unit/export и synthetic Viewer UI проверки PASS; полный Python
прогон: 154/154 PASS. Synthetic UI также проверяет зависшее чтение:
маркировка устаревает без нового запроса/Send и без потери выбора. Текущий этап не меняет Notifier, Windows bridges,
разрешения, service процессы, действующие ключи или оригиналы.
Windows/Edge live проверка НЕ выполнялась; никакой установки/restart.
Favicon следующий этап. См. [контракт A/B/C](TASK_INTENTS_V1.md).

## 21.10.2026 — этап B task metadata, исходники без установки

Notifier source 5.7.24 синхронизирует новые проверенно сохранённые intents,
восстанавливает metadata retry после offline/reload и передаёт отдельно
send_requested / send_unconfirmed / send_observed / send_not_attempted.
DOM observation не считается ChatGPT receipt. Только явный дополнительный
owner grant для одобренного Notifier даёт task_intent_key; старые привязки
автоматически не расширяются. Узкие Windows/Repo transport allowlists
поддерживают два metadata POST; user-original archive gate не менялся.
См. [контракт A/B](TASK_INTENTS_V1.md).
Node 241/241 + build:check PASS; synthetic Viewer UI PASS.
Python: 146 проверок пройдены; 145 в общем прогоне, контроль SHA документа
успешно повторён после актуализации PIN (test_owner_installer_syntax: 2/2 PASS).
Live службы, архив, ключи и Edge 5.7.23 не менялись. Новая сборка source-only,
не применять старые SHA к новым Owner файлам. Цвета/основной task export
и favicon идут следующими шагами. Commit/push/restart/install не выполнялись.

## 21.10.2026 — Task intents: этап A, source-only

Добавлена неизменяемая metadata-only регистрация сохранённого task_id до AI
и отдельное owner-чтение, объединяющее intents с принятыми V2 events.
Новый сессионный task_intent_key выдаётся только явным owner POST;
observer/writer права не расширены. Контракт и пределы доказательств:
[Task intents V1](TASK_INTENTS_V1.md).
25 новых тестов PASS; полный observatory/v1 Python suite 136/136 PASS.
Рабочая служба НЕ перезапускалась, действующий архив/ключи НЕ трогались;
Notifier 5.7.23 и Windows Viewer/Dispatch не менялись. /api/state и текущие
archive/activity endpoints сохранили контракт. Send, Notifier sync, Viewer
export и цвета в этот этап не входят. Не устанавливать/перезапускать ради
этой source-only подготовки; следующих действий на Windows сейчас нет.

## 20.10.2026 — Repo service restarted, Windows/Edge rollout remains manual

Исходники исправлений post-review запущены в действующем Python
Repo Observatory HTTP сервере на loopback 18754 через штатный
stop и setsid/nohup run. Не было Docker container restart.
Контрольное сравнение перед/после: 2 сессии, 42 events,
помесячные ID и счётчики каждой сессии совпали, ingest available.
Отсутствие Repo bearer получает 401. По-прежнему один
persisted archive /workspace/repo/fortis-observatory-repo-v1.
Тестовые пользовательские события в работающую историю ради
smoke не добавлялись. Новая версия Windows Viewer/Notifier
не установлена: см. OWNER_VIEWER_MANUAL_SETUP.md и
EDGE_SMOKE_2026-10-20.md. Для source по-прежнему действуют
86/86 Python и 176/176 Notifier tests; Edge acceptance отсутствует.


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


## 20.10.2026 — Owner Viewer command channel, source-only

Owner Viewer's «Отозвать право адресной отправки» сбрасывает
только in-memory command key, не ключи архива и не AI event path.

Новый owner_dispatch.py содержит in-memory at-most-once команды
для открытых привязанных ChatGPT вкладок, без хранения заданий
для оффлайн-клиентов. Owner Viewer показывает отдельный текстбокс
выбранной сессии, проверяет owner bearer/same-origin для POST
и session/chat по Repo archive; Notifier использует
отдельный per-session dispatch_key, но не observer/writer ключ.
Notifier выполняет команды сам, выдаёт fresh task_id при Send
и возвращает промежуточный статус выполнения через scoped ack.
Никакие события AI или полные ответы не передаются по Windows
command channel: они продолжают идти через Fortis Repo.
Состояние send_initiated не доказывает окончательный Send или
archive receipt. После restart Viewer in-memory token истекает,
нужно повторно привязать Notifier.
Manual Windows installer теперь должен копировать owner_dispatch.py
и сверять три PIN SHA из OWNER_VIEWER_MANUAL_SETUP.md. Реального
Edge smoke/Windows deployment не проводили. Не делайте параллельный
Owner Viewer или второй Tampermonkey userscript.


## 20.10.2026 — расширенные события, legacy-compatible source

Короткий event.summary сохраняется, подробности шага — отдельный
UTF-8 ввод через repo_task.py event --detail-stdin. Сторона
sender записывает sidecar в inbox/repo/.event_details перед JSON метаданных
в inbox/repo/.event_bundle; старый importer игнорирует
.event_bundle, Store новой версии связывает по event_id и сохраняет как отдельный
detail в event Markdown с read-back. Стандартный /api/state
возвращает только has_detail, а /api/repo-history выбранного
task_id отдаёт текст на запрос Viewer. Старые events возвращаются
без detail; AI interim/final не заменяются событиями. Максимальный
ввод detail 8 КиБ, архивная проверка ещё ограничивает формат.
Не писать туда секреты/скрытые рассуждения/тексты пользователей.
При old running server новые event bundles не импортируются:
после ручного обновления Repo service и Viewer проверить
принятую историю. Пока bundle не принят — это очередь, не receipt.
Actual Windows Edge acceptance остаётся непроверенной.


## 20.10.2026 — увеличен размер точного оригинала (source only)

Связка Notifier 5.7.5 → Windows Viewer / relay → Docker archive
поддерживает точные пользовательские оригиналы до 512 КиБ UTF-8.
Метаданные и полные AI-ответы по-прежнему передаются отдельно.
Изменённые исходники НЕ означают обновления запущенных сервисов:
нужны штатный контролируемый рестарт текущего Docker Observatory,
повторная защищённая установка одного Windows Viewer и обновление
существующего Notifier (не дублировать). См. OWNER_VIEWER_MANUAL_SETUP.md
для актуальных SHA. Реальный Edge smoke ещё не проводился.


## 20.10.2026 — Owner Viewer с лентой записей

Экран после авторизации: sticky toolbar, четыре колонки «Сессии»,
«Задачи», «Записи», «Подробности». Список записей объединяет
оригинал пользователя (если отсутствует — честный placeholder),
этапы работы AI (события из archive/state) и полные сообщения AI
из history; карточки различены цветами и показывают превью.
В четвёртой колонке показываются подробности выбранного элемента,
для AI — полный текст. Ручки между четырьмя колонками регулируют
ширину мышью/стрелками, двойной щелчок сбрасывает пропорции.
Изменены только встроенные HTML/CSS/JS owner_viewer.py,
не API, не Docker archive. Windows Edge обновлять вручную по
OWNER_VIEWER_MANUAL_SETUP.md с новым hash; изменения не установлены
посредством Repo.


## 19.10.2026 — компактный Owner Viewer UI

В owner_viewer.py основной вид после авторизации: три колонки
«Сессии», «Задачи», «История» (история шире). Первая доступная сессия и
задача выбираются автоматически; при обновлении ручной выбор сохраняется.
Форма «Добавить сессию», инструкция и привязка Notifier вынесены в
открываемые по кнопкам верхние панели, по умолчанию закрытые.
При смене сессии код привязки очищается. Исходник изменён в Repo,
Windows installation и Edge acceptance ещё не проверены. Серверные
маршруты, Docker volume, защищённый viewer bearer и pairing scopes
не изменены. Ручное обновление установленной копии: см.
OWNER_VIEWER_MANUAL_SETUP.md (точный новый SHA-256).


## 19.10.2026 — Stateless Repo bootstrap and per-request sender

Previously the large generated Observatory chat prompt contained
per-session Chat ID, reporting session ID, enrollment ID and
sequence hint; Notifier only supplied per-request task ID +
session/chat and required re-reading that large prompt for enrollment.

Now repo_service.py bootstrap emits an ID-free, stable startup prompt
without requiring session or running HTTP. Upon next controlled
restart, the Repo /api/instructions endpoint will return the same
short bootstrap. The existing RUNNING service still returns the OLD
~7.6k instruction until owner restart.

New repo_task.py event / message commands validate the actual current
reporting_session_id, conversation_id and per-user-message task_id,
then recover session_task_id from the registered Docker archive.
They stage metadata through emit.py and full assistant answers
through repo_message_sender.py (UTF-8 STDIN), even if Observatory
HTTP is offline. They do not print enrollment IDs or secret keys.
Old emit.py and repo_message_sender.py interfaces remain supported.

Notifier v5.7.2 TaskIdBehavior now adds all necessary non-secret
per-request IDs and ready-to-run Repo commands to each fresh
Fortis task context. It no longer asks AI to retrieve the long
prompt or remember enrollment/sequence from earlier chat turns.
Existing exact-original provenance and observer/writer pairing
are unchanged. The ordinary Planning Helper Observatory reminder
module is also updated to reflect the new protocol.

No owner Windows / live Docker process has been restarted.
Manual owner Edge Notifier update and approved service restart
are needed for real live acceptance.

## 19.10.2026 — chronological task cards and original uploads (source ready)

The approved owner Viewer source now lists tasks by earliest archive-accepted timestamp with an order number, local browser timestamp, and exact-original excerpt or explicit placeholder. A session-scoped owner-only pairing action lets Tampermonkey v5.6.6 read activity and conditionally upload original text to the one Repo Docker Observatory through a restricted localhost 18755 transport using docker exec stdin. Full AI messages still travel directly via Fortis Repo. No legacy/unpaired task migration. Real owner Windows re-install and Edge smoke are pending. See observatory/v1/OWNER_VIEWER_MANUAL_SETUP.md. PowerShell installer parsed with 0 errors.


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

## 19.10.2026 — Stage 1 offline file spool corrections (SOURCE TESTED ONLY)

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

**Состояние: V1 + V2 message-ID + Stage 1C private user-message writer — SOURCE TESTED ONLY / NOT DEPLOYED.**
Пользователь сообщает, что установленная Windows V1 + Tampermonkey работает; защищённый runtime независимо не проверен.
18–19 октября 2026. Это отдельный компонент и он не заменяет старый Observatory,
не обновляет owner server 8092/8093, G2, Repo, Docker и старый HOST.
Границы: ../../AGENTS.md, ../../docs/INSTRUCTIONS.md и E46 owner HTTP boundary.

## Этап 1C — приватное архивирование пользовательского оригинала (source-only)

Добавлен отдельный канал `POST /api/user-messages` с JSON полями
`reporting_session_id`, `conversation_id`, `task_id`, `original_text`.
Сервер принимает его только с `X-Fortis-Message-Writer-Key` (owner-issued
случайный **сессионный** секрет, НЕ owner bearer и НЕ observer key).
Owner-панель выдаёт его **только по отдельной кнопке** «Код с правом записи
сообщений» через `GET /api/message-writer-pair` при owner authorization.
Старый код чтения события не расширяется молча: для записи нужна повторная
ручная привязка Notifier новым кодом. Код никогда не вставлять в чат.

После проверки capability сервер требует найденный **принятый** V2
`task_id` в соответствующей reporting session, затем один раз пишет
`owner_archive/sessions/rs_.../user_messages/task_....md`. Содержимое —
полный оригинал UTF-8 (не текст с appended ID) в JSON-escaped Markdown;
проверяется точный read-back, максимальный исходник 512 КиБ UTF-8 (исходники 20.10.2026; запущенные службы нужно обновить).
Повтор с тем же текстом возвращает старый receipt, попытка заменить текст
отклоняется; небольшая `.user-message-ids.jsonl` сохраняет только ID
в качестве защиты от повторного восстановления удалённого владельцем файла.
API возвращает только ID, status, UTC archive time и SHA-256, не текст.

Важно: `sender_claim`/`first_activity_at` подтверждают **приём сигнала**,
а `archived_at` — запись оригинала. Ни один из них не доказывает реальные
действия модели либо совпадение с браузерным ответом. Данные живут только
в owner-private archive, **не** в Repo inbox и не в GitHub.

`POST /api/user-messages` и `GET /api/message-writer-pair` **пока только
изменения исходников**; до owner Win deployment обязательны source pin,
owner/guest HTTP gate, проверка ACL/reparse, границы расширения возможностей,
ручной повторный pairing, browser smoke. Реальный owner archive не тронут.

## Этап 1B: первый принятый сигнал по task_id — только исходники (19.10.2026)

В V2 событие или метаданный маркер сообщения из разрешённого inbox
содержит `task_id` конкретного сообщения и legacy `session_task_id`. После
**реального принятия** в Markdown этот сигнал доступен в read-only endpoint:

`GET /api/task-activity?session=rs_...&task=task_<32hex>`

Заголовок `X-Fortis-Observer-Key` нужен от pairing **именно этой сессии**.
Owner bearer нельзя заменять на observer key: он не даёт право регистрировать
сессии или писать в архив. HTTP ответ не содержит текста переписки, summary,
содержимого Markdown и секретов, только `found`, `task_id`, `conversation_id`,
`reporting_session_id`, `event`, `sequence`, `accepted_unix`, `provenance`.
Первым событием может быть `progress`, `started`, `completed` либо метаданный
маркер `user_message`/`assistant_message`; `started` не обязателен и служит
семантической меткой содержательного первого шага. Это **sender claim**, а не
криптографическое доказательство реальной работы ChatGPT.

Читается именно хранящаяся Markdown-история, включая после рестарта;
обычный `/api/observer-status` остаётся неизменным и показывает последний
рабочий event. `STAGED_ONLY` недостаточно. Если первые файлы удалены вручную,
первым доступным становится следующее принятое событие. Если V2 событий
нет — `found:false`; из этого нельзя сделать вывод, что пользовательский
запрос не был доставлен ChatGPT.

Для Notifier локальное `first_activity_at` **не равно `archived_at`**.
Stage 1C (передача оригинала в owner-private архив через отдельный
разрешённый writer), полные тексты AI и таймер предупреждения ещё не выполнены.
Исходники НЕ являются подтверждением установленной owner Windows V1.

## Сценарий V1

1. Владелец открывает панель Observatory в Edge и вводит токен из своей консоли.
2. Вручную указывает URL обычной беседы ChatGPT /c/ID, маршрут и название задачи.
3. Панель создаёт отдельные reporting_session_id и task_id, выдаёт инструкцию,
   которую можно вручную вставить в конкретный чат.
4. Чат через разрешённый Repo или отдельно разрешённый G2 пишет краткое JSON
   событие в согласованный inbox. Событие — сообщение о ходе работы, НЕ
   доказательство реального вызова инструмента и НЕ полный текст переписки.
5. Сборщик опрашивает inbox каждые 3 секунды; после проверки создаёт
   Markdown, сохраняет receipt ID и удаляет принятое входящее событие.
   Некорректные, неизвестные и конфликтующие с уже принятым sequence
   записи отвергаются без автоматического повтора; ошибки доступа к
   архиву оставляют файл во входящем каталоге для следующей попытки.
6. Панель показывает события прямо из Markdown, с обновлением раз в 5 сек.
   Отредактированный в VS Code/Obsidian текст события перечитывается.
7. Удаление файла события скрывает его, удаление session.md скрывает сессию.
   Старые обработанные файлы не восстанавливаются из SQLite/очереди.

## Архив — независимые файлы Markdown

~~~text
OWNER_PRIVATE_ARCHIVE/
  sessions/
    rs_<id>/
      session.md
      events/
        000000-<event_id>.md
        000001-<event_id>.md
  .imported-ids.jsonl
~~~

Первая строка Markdown — JSON metadata в HTML-комментарии, далее заголовок
и доступный редактированию текст. Малый .imported-ids.jsonl содержит
исключительно идентификаторы принятых событий для анти-повтора, без текста.
Он не является альтернативной историей. При ручном удалении файлов
редактор, панель и простой файловый просмотр видят одно и то же.
SQLite в V1 не используется. GitHub не подключается автоматически.

Идентификатор вкладки tab_session_id равен null: панель отдельно от
ChatGPT, не устанавливает дополнение Edge и не наблюдает вкладки напрямую.
Несколько ручных регистраций одной беседы имеют один conversation_id,
но разные reporting_session_id и task_id.

## Безопасность и границы

- Owner archive должен находиться в проверенной защищённой области
  основного Windows-пользователя, НЕ в доступных Repo RW mounts.
- Repo может писать только небольшие данные в ранее разрешённый inbox.
  G2 не получает доступ к owner-home, GUI или clipboard.
- HTTP сервер привязан к 127.0.0.1, но Windows localhost разделяется
  разными пользователями. Любой API требует 256-битный owner bearer
  token, который вводится в браузере и не сохраняется.
- Статические маршруты обслуживают только index.html, client.js,
  style.css. Нет загрузки произвольных файлов и нет API, выполняющего
  команды. HTML/CSS/JS читаются без токена; приватные данные — нет.
- Исходники из Repo RW нельзя запускать под Windows владельцем.
  Перед установкой требуется отдельный review/pin и копия в
  owner-protected каталог. В server.py предусмотрен guard против
  запуска непосредственно из owner Repos или Workfiles.
- Отдельный тест owner-positive и guest-negative по E46, проверка ACL,
  Windows reparse/hardlink и pinned-source требуются до native запуска.
  Отсутствие прав администратора НЕ гарантирует безопасность API.
- Токен никогда не помещать в инструкции чату, GitHub, скриншоты,
  редиректы вывода, копии G2 или Repo.

## Установка в основном Windows-пользователе — НЕ ПРОИЗВЕДЕНА

Действия ниже — подготовительный runbook, а не выполненная установка.

1. Установить реальное состояние старого небезопасного preview 8093 и,
   если он работает, остановить только его через Ctrl+C в owner PowerShell.
   Не перезапускать другие контуры.
2. Проверить и закрепить точные исходники 6 файлов: store.py, emit.py,
   server.py, index.html, client.js, style.css. Скопировать их в
   защищённую owner-папку, пример:
   C:\Users\alexa\AppData\Local\FortisObservatoryV1\App
3. Проверить owner-only архив, пример:
   C:\Users\alexa\Documents\FortisObservatoryHistory
   (пока не создан и ACL не проверен).
4. При необходимости выделить Repo inbox внутри уже разрешённого
   Windows Workfiles mount, без расширения ACL/mount, например:
   C:\Users\alexa\Workfiles\FortisObservatory-v1\inbox\repo
   Repo-side path: /workspace/files/FortisObservatory-v1/inbox/repo
   (пока не создан).
5. После E46 acceptance, owner-контекст и путь защищённого deployment
   запустить из своей интерактивной owner PowerShell:

~~~powershell
py -3 .\server.py --archive "C:\Users\alexa\Documents\FortisObservatoryHistory" --repo-inbox "C:\Users\alexa\Workfiles\FortisObservatory-v1\inbox\repo" --repo-sender-inbox "/workspace/files/FortisObservatory-v1/inbox/repo" --port 18753
~~~

Открыть в Edge: http://127.0.0.1:18753/
Скопировать токен из owner-консоли в форму панели, не в чат.
Пути выше — примеры, не проверенные текущие пути deployment.
G2-route включается отдельно, только после разрешённого inbox.

## Пример события

После ручного подключения инструкция содержит корректные session/task IDs.
Событие от Repo:

~~~bash
python3 /workspace/repos/tunnel/observatory/v1/emit.py --inbox /workspace/files/FortisObservatory-v1/inbox/repo --session rs_ID --task task_ID --route repo --sequence 0 --event started --stage planning --summary "Начата работа"
~~~

Далее sequence увеличивается на 1. Допустимые event:
started, progress, checkpoint, blocked, completed, failed.
stage: planning, editing, testing, waiting_tool, reviewing, other.

**Новая инструкция для подключённого чата требует пошаговые сообщения
во время выполнения**, согласованные по смыслу с содержательными
обновлениями пользователя в интерфейсе ChatGPT. Обычно для многоэтапной
работы: started planning → progress reviewing → progress editing →
checkpoint testing → progress reviewing → completed other.
Переходы отправляются **сразу**, не пачкой в конце работы.
Точное копирование сообщений ChatGPT и реальные вызовы инструментов
автоматически не перехватываются: это добровольные события отправителя.
Не выдумывать проверки ради событий и не отправлять событие на каждый
вызов инструмента. Для коротких ответов промежуточные шаги не нужны.

Описание короткое и не содержит секретов, путей, полного чата,
команд и аргументов инструментов. Ограничение по каждому JSON: 2 KiB.
Термин STAGED_ONLY означает запись в очередь, НЕ факт приёма;
reported_completed не доказывает, что полный ответ сохранён.
При недоступности инструментов чат всё равно отвечает пользователю.

## Observatory → Tab Notifier (исходники подготовлены, ещё не установлены)

Связь направлена **из Observatory в Tab Notifier**: новое принятое событие
started/progress/checkpoint может включить индикатор работы по Observatory,
а completed — показать завершение. Когда DOM отключён, оба перехода зависят
от событий Observatory; пользовательские действия не эмулируются. Это не запись состояний
вкладки в Observatory, не аудит реальных вызовов Repo/G2 и не подтверждение
сохранённого ответа. Детали, отдельный read-only ключ, проверенный патч для
внешнего репозитория и инструкция установки — в
[notifier-adapter/README.md](notifier-adapter/README.md). Изменённый owner
сервер нужно отдельно проверить и обновить; он НЕ перезапускался.

## Исправления после независимого Final Review R-FOBS-1018/v1

**18.10.2026 — source fixes, не Windows deployment.** Отчёт review остаётся
историческим снимком проверенной ранее версии; этот код изменён после него.

- **F-P-V1-01:** входящий JSON с нестроковым route/event/stage теперь
  отвергается без исключения и не останавливает обработку других событий.
- **F-P-V1-02:** метаданные Markdown проверяются до сортировки и расчёта
  времени. Ошибочный файл помечается через invalid_files; остальные
  сессии и файлы сохраняют доступность. Текст заметки можно редактировать.
- **F-P-V1-03:** постоянные отказы (неверный JSON, неизвестная сессия,
  конфликт sequence) теперь удаляются из входящей очереди. Поэтому
  старый отклонённый конфликт не восстановит удалённый Markdown.
  Это выбранное простое поведение V1: отклонённый пакет **не архивируется**
  и не восстанавливается автоматически. Для новой попытки отправитель
  должен явно создать новое корректное событие.
- **F-P-V1-04:** при переполнении обрабатываются до 512 файлов за проход,
  остальные остаются до следующих проходов; capacity_exceeded означает
  наличие backlog, а не полную остановку. Очередь обходится по
  круговому указателю, чтобы временно недоступные первые файлы не
  блокировали более поздние. Ошибки диска/повреждённый session.md
  дают retryable; события не удаляются по такому временному сбою.
- **F-P-V1-05:** состояние задачи выбирается по наибольшему sequence,
  а `last_signal_at` и тишина — по последнему времени принятия.
  Запоздавшее более раннее событие не делает время последнего
  сигнала старым.
- Непредвиденный сбой фонового опроса больше не должен без уведомления
  завершать поток: его состояние отмечается `failed`, затем
  следующий проход пробует снова.

**Предел гарантий:** если пользователь удаляет Markdown во время
незавершённой записи/сбоя fsync или одновременно изменяет файлы,
атомарность между архивом, receipts и очередью ещё не проверена на NTFS.
Гарантированно проверено поведение без одновременных конфликтующих
операций; к настоящей Windows-установке по-прежнему нужен E46/ACL
gate. Сканирование других контуров и изменение полномочий не проводились.

## Тесты (в Repo, не на Windows)

~~~bash
cd /workspace/repos/tunnel/observatory/v1
python3 -m unittest -v test_v1.py
python3 -m py_compile server.py store.py emit.py
node --check client.js
~~~

Синтетические тесты: ручная регистрация, несколько sessions,
ID и route mismatch, HTTP owner positive/guest-like negative,
файловые операции, read-back, внешние изменения, повторные события,
удаление, обработка неверных типов JSON/Markdown, конфликтов, 513
входящих событий, круговой обход при retryable и раздельная
хронология sequence/accepted_at, отсутствие раскрытия server source.
**21/21 V1 тестов PASS (Repo); смежные тесты Observatory проверяются отдельно.**

Не проверено: Windows installed UI, native owner-G2 negative access,
реальное подключение чата и его tool capability, owner ACL, Edge GUI.
Ограничение V1: ни автоматический захват переписки, ни реальные вызовы
любых инструментов G2/Repo, ни OS-уведомления в V1 не реализованы.
Максимум 200 sessions, 2000 events per session и 512 queued JSON за обход.


## V2 source candidate — `task_id` = ID сообщения пользователя (19.10.2026)

**Не установлен в Windows.** Это новая версия записей в исходниках `store.py`,
`emit.py`, `server.py`, `client.js`; старая V1 и её работающая пользовательская
установка не заменены. Сначала нужен отдельный owner-source review/deployment,
без запуска исходников из RW монтирования и без изменения ACL/портов.

- `conversation_id` — ChatGPT `/c/...` и может иметь несколько подключений.
- `reporting_session_id` — конкретное ручное подключение Observatory.
- `task_id` в событии `version=2` — случайный UUID4 `task_<32 lowercase hex>`,
  **новый для каждого пользовательского сообщения**, общий для всех его
  событий работы и маркера ответа, включая краткие ответы без реальных этапов.
- `session_task_id` — **legacy enrollment ID**, который раньше назывался
  `task_id` в `session.md`. Он продолжает проверку принадлежности событий
  подключению, но НЕ является ID сообщения. Не переименовывать исторические
  записи и не генерировать новый `session_task_id` на каждое сообщение.
- `sequence` по-прежнему глобален **внутри reporting session**, а не задачи.
  Это число не сбрасывается при следующем сообщении. `event_id` — отдельный
  UUID для защиты от повторного приёма файла события.
- Маркеры `user_message` и `assistant_message` принимаются только в `version=2`,
  только со `stage=other` и строго заданными `summary`. Они содержат
  **только роль/факт/идентификатор**, не отправляют и не сохраняют
  полный текст сообщения. Это `sender_claim`, не verified browser capture.
- Старые события `version=1` остаются допустимыми только с их прежним
  `session.task_id` и прежним набором `event`. V2 требует
  `--version 2 --session-task <legacy-id> --task <message-id>`.
- `observer-status` выбирает последнее событие **работы**, пропуская маркеры
  сообщений, чтобы не ломать текущий Notifier. Маркеры видны в owner-панели,
  а в read-only status не отдаются. Текст по observer key не раскрывается.

### Пример одного сообщения (все данные вымышленные)

Сначала ChatGPT (при разрешённом инструменте) создаёт один ID сообщения:

~~~bash
python3 -c 'import uuid; print("task_" + uuid.uuid4().hex)'
~~~

Затем использует полученное значение `task_id` во **всех** событиях данного
пользовательского сообщения: `user_message`, `started`, `progress`,
`checkpoint`, `assistant_message`, `completed`, когда соответствующие события
действительно есть. При следующем сообщении — новый ID; `sequence` продолжает
прошлый ряд. Для маркеров роль и текст summary заданы в `store.MESSAGE_SUMMARIES`.
`STAGED_ONLY` — только факт записи в очередь, а не приём архивом.

**Не реализовано:** сохранение полного текста сообщений пользователя/ответов,
автоматический захват каждого сообщения и достоверная привязка к нативному
ChatGPT message-id. Repo inbox не является разрешённым каналом передачи
переписки. Будущее собственное поле Notifier / Browser Companion потребуют
отдельного приватного транспорта и owner-side решения. Отсутствие вызова
разрешённого инструмента означает, что сообщения/события могут не попасть в
архив; модельная инструкция не даёт гарантии 100%-го покрытия.

**Further fail-closed guard:** the owner-private Windows relay install
must include `approved-owner.json` pinning exact Windows owner SID and
approved Repo container. Wrong identity/container or absent config
prevents starting. This file is not present yet, and validation of
real owner ACL/guest-negative remains pending.


## 21.10.2026 — Offline current-chat outbox, source 5.7.27

Prepared in /workspace/repo/fortis-offline-outbox-20261021/work.
Notifier always supplies current conversation_id + new task_id on prepared
insert/file/Send routes, even without browser pairing. With pairing the exact
registered session check remains mandatory; an explicitly wrong session does
not downgrade to the unbound queue. No IDs from earlier requests are reused.

repo_task.py without --session durably stages events and full assistant
interim/final separately under the private Repo volume inbox/pending-context.
HTTP Observatory, Windows Viewer, observer/writer keys and browser pairing
are not prerequisites for staging. Normal bound offline sender is retained.
STAGED_ONLY proves queue staging, never acceptance, DOM display or delivery.

The new collector forwards after exactly one locally registered Repo session
matches the supplied current conversation_id; no registration is created.
Ambiguous/absent registrations wait with payload preserved, no automatic
failed. Binding is pinned before forwarding and never changes on retries.
Stable event/message IDs use the existing archive duplicate checks.
Corrupt/oversized/linked entries are retained/refused without body logs.
Bounds: 512 records per action, 350 KiB serialized envelope; original body
limit 256 KiB, event detail 8 KiB; safe metadata checks remain in force.

No user originals are reconstructed or migrated. Browser originals, archive
activity gate, approval scopes, owner/observer access and manual Send are
unchanged. Existing unpaired browser records stay unpaired. Without a valid
current chat/task or accessible Repo, instructions require continuing the
user task without inventing IDs or claiming data was saved.

Deployment and browser installation are recorded separately in CURRENT_STATE.


## 22.10.2026 — Чаты из браузера и подключение одной кнопкой (SOURCE TESTED, INSTALL PENDING)

Notifier уже отправляет chat + proof из конкретных /c/<id> вкладок каждые
несколько секунд. Новая Windows Viewer source показывает их в колонке
«Сессии» → «Чаты из браузера», включая ещё не зарегистрированные беседы.
Идентификация в первом варианте — Chat ID и ссылка «открыть чат».
«Подключить» под owner bearer + same-origin регистрирует точный URL,
подтверждает выбранный свежий Notifier и сохраняет обычное разрешение
на переподключение. Отдельный task_intents grant сам не включается;
Send остаётся отдельным ручным действием. Ручной ввод URL сохранён как запасной.

Обнаружение не создаёт сессии и не выдаёт ключи. Его сообщения не содержат
текстов чата или оригиналов; в памяти только ID, digest proof и last_seen.
Список доступен только владельцу, limit 200 claimant entries, TTL 180 сек,
heartbeat продлевает TTL. Исчезновение кандидата не меняет статус
зарегистрированной сессии и не создаёт failed. Закрытая/приостановленная
вкладка может оставаться в найденных до истечения TTL. Это не чтение всей
истории ChatGPT. Нужен работающий Notifier в открытой вкладке.

Подключение не выбирает случайно между разными claimant, не перезаписывает
чужую существующую привязку, повтор успешно завершённого запроса идемпотентен.
Отказ регистрации/сохранения разрешения сохраняет кандидат для повтора;
частично созданная сессия используется повторно через прежний repo_register.
При недоступном Repo обнаружение всё равно сохраняется локально.
Права, исходные originals, schema approved-notifiers.json и адресный
ручной Send сохранены. Клик не вызывает dispatch и не меняет выбор задачи.

Изменились только runtime source owner_viewer.py и owner_enrollment.py:
Viewer SHA-256: 6b1574ea1ccb09056fbbe1a703c6ad6820dbec3fe8fa52d8c3d1118fe02d0130
Enrollment SHA-256: 2bc00765a657493eb4dffee900408e29b7f24ab9a639348f61e1d389727f9d55
Installer/bridge/dispatch/launchers/Notifier не менялись.
Windows текущую защищённую установку не трогали. Live Docker backend
PID 15984 из offline-outbox candidate не перезапускался.
Новая функция появится после ручного обновления Windows Viewer.
Checkpoint: /workspace/repo/fortis-discovered-chats-20261022.



## 22.10.2026 — Названия вкладок в найденных и подключённых сессиях (SOURCE READY)

Notifier source 5.7.28 передаёт ограниченное очищенное natural title
только после supports_tab_titles=true от Windows Viewer. Старый Viewer
получает прежний chat/proof запрос; при downgrade и отказе optional поля
Notifier возвращается к прежнему payload на очередном heartbeat.
Служебные favicon/title значки и Observatory connection prefixes удаляются
существующим cleanTitle. Контрольные/bidi символы и unpaired surrogates
исключаются, предел 128 Unicode codepoints / 512 UTF-8 bytes.
Ни body сообщений, ни DOM беседы, ни task/original тексты не читаются.

Windows enrollment принимает необязательный title в том же localhost
endpoint (body <=1024), legacy payload поддержан. Названия живут только
в owner RAM с TTL 180 сек, не записываются в approved-notifiers.json,
Docker archive, event summaries или shared файлы. В discovered список
название передаётся owner bearer API; connected session_titles доступны
только для точно одобренного chat+proof. Чужой proof не переименовывает
подключённую сессию. При неоднозначных claimant с разными названиями
название не выбирается случайно. Права и identity всегда определяются ID.

В карточках найденных чатов название — основная ссылка, Chat ID — мелкая
подпись. В списке подключённых сессий и адресате текстбокса используется
свежее название из этой же одобренной вкладки; fallback — архивное
название/ID. Rename приходит с очередным heartbeat/poll. Старые архивные
названия не переписываются. Выбранные task/session и ручной Send сохранены.

Изолированная копия: /workspace/repo/fortis-tab-titles-20261022/work.
Viewer SHA-256: 34558e098d27139dcec95333bb4f8b51907e03820a902207e47b07d2e87aead6
Enrollment SHA-256: 51ce3eb96fd3da285c591c063cb71642863b825d5fef63bc6c5060a814ca03e3
Notifier 5.7.28 SHA-256: d506f6d7824ac1fcf868290da44f9f2e991acd42514fac31bdb6060fbedc99c5
Требуется ручное обновление Viewer и одной существующей копии Notifier.
Рекомендуемый порядок: Viewer, затем Notifier и reload вкладок.
Старые команды с SHA предыдущего Viewer/Enrollment к новой source не подходят.
Windows установленную копию, pairing/GM originals и live backend PID 15984
не изменяли/не перезапускали. Новый Edge live QA ещё не выполнен.


## 24.10.2026 — автоматическое закрытие задачи при сохранении AI final

Исправление для `repo_task.py message --kind final`: до него полный финальный
ответ мог быть сохранён в `assistant_messages`, но карточка задачи оставалась
`silent` или `unknown`, поскольку TaskIntents читает терминальный статус
из `event completed`/`failed`, а не из текста `final`.

**Теперь** после *успешной локальной постановки полного `final`* в очереди
ставится **связанное событие `completed`**: строго тот же task_id,
reporting_session_id и Docker enrollment session_task_id. Event ID
детерминирован от message_id: повтор с тем же --message-id не создаёт
второго терминального события в архиве. Никакой проверки HTTP, новых
ключей/сессий, отправки через G2/Windows owner или browser relay нет.

То же правило действует для `repo_task.py message` без --session: сообщения
и статусные события отдельно сохраняются в pending-context с одним chat/task
и попадают только в его точно зарегистрированную сессию. Промежуточные
сообщения (kind interim) не меняют терминальный статус. При ошибке
постановки полного сообщения `completed` не создаётся. Если сам финал
уже сохранён в очереди, а staging события не удался, выдаётся
`COMPLETED_NOT_STAGED`; повтор полного ответа **не** выполняется.

`STAGED_ONLY` / `COMPLETION_STAGED_ONLY` — локальная очередь, **не** receipt
Docker. Зелёный статус появляется только после принятого коллектором
`completed` и по-прежнему означает «Завершено (сообщено AI)», а не
подтверждение фактической доставки сообщения в ChatGPT.

**Восстановление исторической задачи:** проверен сохранённый final для
`task_aceb281618bc4cc0b9d10c6f830bbadf` в сессии
`rs_ec0efd2d34544441b6f5c058aac266ed`; недостающее `completed` поставлено
через Repo, и read-only TaskIntents.snapshot подтвердил `state=completed`,
`terminal_event=completed`. Другие исторические задачи, файлы originals,
данные отправителя, Notifier, Viewer и G2 не изменены.

Тесты: 56/56 PASS (`test_repo_task.py`, `test_repo_pending.py`, `test_task_intents.py`,
`test_task_status_export.py`, `test_observer_task_overview.py`). До правок
создан backup в `/workspace/repo/fortis-final-completion-20261024`.
