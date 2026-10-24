# Fortis Observatory — обновление Viewer из alexa

## Актуальная точка входа — 25.10.2026

Текущее состояние компонентов, owner API, результаты пользовательского теста и открытые проблемы ведутся в [главном README V1](README.md). Ниже сохранена история обновлений; старые команды/SHA не являются универсальной инструкцией для текущего main.

Текущие source SHA-256 (установленная Windows-копия отдельно не сверена):

| Файл | SHA-256 |
|---|---|
| `owner_viewer.py` | `eae6879f7559b6b540acbdbaa3ced1c031935883aa6793f8a5901a1d658b3e05` |
| `owner_notifier_bridge.py` | `818089f6796fb2877dcce8535953ec179072b217ae62cb2afb3c189a337ba195` |
| `owner_dispatch.py` | `9da1bc2a223804660c2a9ea9033b86889dca7119d3a1b1dab18c85565360fea5` |
| `owner_enrollment.py` | `873ec864c5996234e930c3ceaf9fb75cbcdea945b7b84c76ea47d1cef164b0d3` |
| `Start-FortisObservatoryAuto.cmd` | `857647ef4b4efdda6334cb7772ce899cfdc5061203b3dfa641efad94f457a9e1` |
| `Enable-FortisObservatoryAutoStart.ps1` | `003a65ec88a10810545d01c8aa69e0af6827d35ba8948e93b6e80dd8428bfd82` |

Main Viewer/enrollment соответствуют [пакету session-groups](candidates/session-groups-20261024/README.md), который включает предшествующие изменения unified workflow и sliding tabs. Этот installer ожидает конкретную предыдущую версию; неизвестную или уже более новую установленную копию не перезаписывать по старой инструкции. Использовать guarded Preview и согласованные source/install SHA; отказ проверки не обходить. Pinned README/manifest пакетов оставлены как датированные release evidence.

Windows checkout пользователя: `C:\Users\alexa\Repos\tunnel\observatory\v1`; защищённая установка: `%LOCALAPPDATA%\FortisObservatoryV1\Viewer`. Ручную установку выполняет владелец alexa обычным PowerShell. Требуются backup, сохранённый идентификатор отката и readback. В рамках актуализации документации Viewer, Docker и туннели не перезапускались; ACL, ключи и Windows-файлы установки не менялись.

Для Notifier текущая source-сборка — 5.7.34 в соседнем репозитории. Обновлять существующий script/Loader с сохранением identity/GM-данных и проверять runtime в каждом целевом профиле. Более старый Notifier может исполнить `mode=send` текстом; наличие owner API само по себе не гарантирует файловый путь. Выполненный пользователем API-тест был отменён им; файловая доставка не подтверждена. Перед новым явно согласованным Send проверить карточку через `Файл` без отправки; старый test helper блокирует повтор предыдущей попытки.

## История обновлений

Даты ниже описывают состояние на тот момент. Например, «не установлено» и PID в старой записи не являются текущим live-статусом.

## 22.10.2026 — «Чаты из браузера» свёрнуты при загрузке (SOURCE READY)

В owner_viewer.py блок discoveryPanel переведён на native details/summary
без open. Нажатие на заголовок или клавиатура раскрывает/сворачивает его;
обычный polling обновляет только внутренний список и сохраняет положение.
Подключённые сессии остаются вне раскрываемого блока. Протокол discovery,
названия/ID, pairing, Send и архив не изменены. Runtime diff: HTML/CSS only.
Существующий Viewer synthetic UI (5 сценариев) PASS; installer source/pins
2/2 PASS. Дополнительно проверены отсутствие open и отсутствие скриптов,
меняющих open при polling. Notifier 5.7.28 и его bundle не менялись.
Viewer SHA-256: aae05194e48001aefcffb850061ba7266e956f821efbf398834c35e6820efbc2
Enrollment остаётся 51ce3eb96fd3da285c591c063cb71642863b825d5fef63bc6c5060a814ca03e3.
Checkpoint /workspace/repo/fortis-collapse-discovery-20261022.
Исходник готов к ручному обновлению одного owner_viewer.py после backup
в текущем owner-protected Windows каталоге. Установленный Viewer и
Docker backend не перезапускались/не изменялись этим шагом.

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
Viewer SHA-256: aae05194e48001aefcffb850061ba7266e956f821efbf398834c35e6820efbc2
Enrollment SHA-256: 51ce3eb96fd3da285c591c063cb71642863b825d5fef63bc6c5060a814ca03e3
Notifier 5.7.28 SHA-256: d506f6d7824ac1fcf868290da44f9f2e991acd42514fac31bdb6060fbedc99c5
Требуется ручное обновление Viewer и одной существующей копии Notifier.
Рекомендуемый порядок: Viewer, затем Notifier и reload вкладок.
Старые команды с SHA предыдущего Viewer/Enrollment к новой source не подходят.
Windows установленную копию, pairing/GM originals и live backend PID 15984
не изменяли/не перезапускали. Новый Edge live QA ещё не выполнен.

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
Viewer SHA-256: aae05194e48001aefcffb850061ba7266e956f821efbf398834c35e6820efbc2
Enrollment SHA-256: 51ce3eb96fd3da285c591c063cb71642863b825d5fef63bc6c5060a814ca03e3
Installer/bridge/dispatch/launchers/Notifier не менялись.
Windows текущую защищённую установку не трогали. Live Docker backend
PID 15984 из offline-outbox candidate не перезапускался.
Новая функция появится после ручного обновления Windows Viewer.
Checkpoint: /workspace/repo/fortis-discovered-chats-20261022.

Обновлять вручную только Windows Viewer. Перед установкой сохранить
приватную проверенную копию кода и текущих approvals в каталоге Viewer,
затем закрыть его старую консоль, выполнить прежний pinned installer
с суммами ниже и запустить Start-FortisObservatory.cmd. Docker backend
останавливать не требуется. После ввода owner code раздел «Чаты из браузера»
наполняется по объявлениям Notifier; кнопка подключает выбранный чат.
Если требуется откат, восстановить прежний код owner_viewer.py и
owner_enrollment.py, сохранив действующий approved-notifiers.json:
откат approvals удалил бы разрешения, созданные после обновления.

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

## 21.10.2026 — latest-task + отдельные символы DOM, подготовка rollout

Исправление проверено в /workspace/repo/fortis-latest-task-20261021/work.
Python 162/162 PASS, Node 261/261 PASS, build:check и synthetic Viewer UI PASS.
Состояние сессии = состояние последнего пользовательского таска, по времени
подготовки оригинала; legacy fallback = первое событие. Поздний progress
старой задачи не поднимает её в текущие. Исторические счётчики сессии убраны,
карточки старых задач и их статусы сохранены без автоматического failed.
Применение к реальному архиву read-only: для сессии с 7 задачами новая
сводка completed вместо unknown; вторая сессия остаётся completed.

Контракт task_overview v2, basis latest_task; v1 aggregate не выдаётся за
текущее состояние. Цвета favicon только из свежей scoped сводки Observatory.
DOM отдельно: одноцветные часы/галочка, local upload — одноцветная стрелка.
При двух источниках DOM-символ виден рядом с Observatory-цветом в title.
DOM completion не превращает текущую задачу Observatory в completed.

Подготовлен только новый owner_viewer.py в Windows Repo source, для ручной
установки владельцем. SHA256: 4df003701e5cc993a9914687c9211eba890d56eea6c71dfa030a6238f3744509
Остальные Python/Notifier изменения остаются в изолированной копии,
чтобы установленный пока Viewer v1 не потерял совместимость с export.
Активный Docker backend 5.7.25/candidate и live repo export не переключались.
Для следующего шага владелец устанавливает Viewer v2 и сообщает результат;
затем AI согласованно переключает export/backend на v2 и готовит Notifier.
Notifier candidate 5.7.26 SHA256: a11e40c372e46c3bcc33e278dce36595d79a1eb34788eb5bd5779bc38ae8e6b2
Windows installation/fresh browser checks нового исправления НЕ подтверждены.

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

## 21.10.2026 — этап C: статусы и ожидающие задачи (исходники)

Подготовлены объединённый список archive/intents, цветные задачи/сессии
и отдельные счётчики ожидания/работы/тишины/черновиков/блокировок/терминальных
событий. Серый статус отсутствует. Черновик и blocked имеют текст без
цветной маркировки. Старый session.state доступен как диагностика в tooltip.
Чтение использует существующий Docker export; пустой оригинал не заменяется
текстом AI. Ошибка чтения сохраняет старые строки с явной пометкой давности.

Изменены только исходники; Windows Viewer не установлен/перезапущен.
Notifier остаётся source 5.7.24, установленная рабочая 5.7.23 не менялась;
favicon — следующий этап. Старые команды установки не запускать сейчас.
Следующий rollout требует отдельного согласования и проверки Windows SHA.
Новая source SHA owner_viewer.py: 81bfb0980bba0daea94db7aec477da009c863c3ebf59dbfcc28fd75b69299ea3

## 21.10.2026 — 5.7.24 metadata source preparation; НЕ устанавливать сейчас

Рабочая система остаётся 5.7.23 + прежний Windows Viewer. Этап B
подготовлен только в исходниках: отдельное право metadata для уже одобренного
Notifier, узкие metadata POST, offline/reload retry и наблюдения Send.
Цвета и task export ещё впереди. Службы не перезапускались; installer НЕ запускался.
Следующий rollout требует отдельного согласования, без сброса pairing/GM/archive.
Ниже operative SHA обновлены для текущих исходников; старые датированные
блоки не применять к новой сборке. Обычная прежняя привязка не получает
metadata право сама: после будущего rollout владелец разрешает его отдельной
кнопкой «Разрешить метаданные сохранённых задач» в диагностике сессии.
Текущая новая сборка Notifier SHA256: f70b51228bd8b9492837c031b96dc0c651b3c723827dea8314dba279ed4f67ad

## 21.10.2026 — Notifier 5.7.23: file-only tolerant blank paragraph representation

Changes only in Notifier (NOT owner Viewer/Dispatch installer files):
the full saved Fortis context must match the native rich editor
ignoring ONLY empty paragraphs, CRLF vs LF and NBSP vs ordinary
space. Every nonempty line and order, task_id, filename and
instructions must match; normal Insert stays exact. The same matching
rule checks file preparation and the separately requested Send, which
is never pressed automatically. This does NOT verify server-side TXT.
Tests 229/229 PASS; real Edge NOT_RUN.
Built 5.7.23 SHA:
5d6c24978effc46980dd699568c8607a51782ca1d28b5667322cc9e495674c83

Use exactly one existing Local Loader, pointing to the new built file
in C:\Users\alexa\Repos\tabnotifier-fileautosend-autochat.
Do NOT re-run installer if the 5.7.22 Viewer/Dispatch are already
installed. Existing profiles/pairing and Docker archive unchanged.
New unique text/one File action only; no Send until user approval.


## 21.10.2026 — Notifier 5.7.22: полная диагностика в правом журнале Textbox

Owner reproducer: a single file was attached and the Fortis task
context was visible in ChatGPT, but the Notifier strict native
exact-character verification returned context_mismatch. Owner timeline
only showed attachment_only/context_mismatch and omitted the full
Notifier message "Файл прикреплён, но контекст не добавлен:
Вставка не совпала с исходником посимвольно. Исходник сохранён;
Send не нажимался. Не отправляй до ручной проверки."

Fix: full fixed Notifier status now accompanies the terminal File
dispatch ACK as an optional detail, stored in the same bounded,
owner-only, in-memory event history and displayed as textContent.
Both Notifier and owner_dispatch.py independently enforce fixed
allowlisted error/success templates, max length 512, no arbitrary
prompt, filename, DOM, native editor, keys or full exception objects.
Reason enum, at-most-once claims, no-retry, no automatic Send,
strict native verification and no fake ChatGPT receipt unchanged.
Viewer still polls READ ONLY every 5 sec; old events will not gain
detail retroactively. No Repo Docker archive changes.
Integration tests cover Node/Notifier, Owner dispatch, real localhost
API ACK/status, and Viewer DOM text rendering, including adversarial
payload rejection.

Built Notifier SHA256 (5.7.22):
537f61d23b584959e5c814ade1931e193ec642cece086d595b23daef8548416c

Windows INSTALL REQUIRED for updated owner_viewer.py, owner_dispatch.py;
the PIN-protected existing installer SHA is unchanged. Existing
Tampermonkey Local Loader must use the ONE current built Notifier file.
No re-pairing/profile resets. Verify in live Edge after manual install,
using a NEW unique text and exactly ONE File action, without Send.
Even if ChatGPT has a visible task context, Notifier still does NOT
claim file_attached unless strict local validation passes.


## 21.10.2026 — fix: File attached in ChatGPT but Observatory incorrectly said refused (5.7.20)

User evidence: event history File queued → claimed → refused after ~7 sec,
while a .txt file was visibly attached to ChatGPT. Prepared Send was
correctly refused: there was no verified task_id / Fortis context.

Cause: narrow DOM file-card recognition (file name nested in title or
aria-label, or preview mounted as sibling under composer wrapper).
After 5 sec waitForFileCard returned false, even if ChatGPT had accepted
the file; old handler returned no result and the broker displayed
generic refused. No receipt was ever proved.

Fix: Notifier checks recognized card's nested title/aria-label and one
local composer ancestor, never whole conversation or input.files.
Adds TWO statuses to existing owner dispatch:
  attachment_unconfirmed: one upload attempt, no verified file card;
    file MAY be attached; NO automatic retry; do not click Send;
  attachment_only: verified file card, but preparing Fortis task_id /
    context failed; NO automatic Send or retry;
  file_attached: card AND task_id/context preparation succeeded.
No fake task_id in ambiguous states, no claim of ChatGPT receipt.
Owner event log lists the corresponding evidence level, plus a bounded
allowlisted reason code. Old pending commands are never replayed.

Notifier 5.7.20 checksum:
fc63fb2a47cd91db6ff792530d6d10839368b0459b25be24590291ed123f2770

Updated owner Viewer/Dispatch SHA are in the pinned installer invocation
below. Four other source SHA unchanged. Changes do not alter Docker
archive, Windows ACL or existing target sessions.
Source tests PASS; REAL EDGE ATTACHMENT CARD DOM NOT VERIFIED.
To verify, update both Viewer and the SINGLE Local Loader to 5.7.20,
use a new unique safe prompt, observe one file card and task context,
without pressing Send. If still ambiguous despite visible card,
capture the card HTML/DOM for precise non-repeating debugging.


## 21.10.2026 — separate prepared Send, task_id in File/Insert ACK, status journal (5.7.19)

Notifier 5.7.19 / Owner Viewer source update; Windows installed copies
and Edge live Send NOT_RUN. Docker Repo archive untouched.

- File and Insert complete only when the native composer contains the
  saved task_id and Fortis context (for File, after a confirmed single
  attachment attempt). ACK `file_attached` or `inserted` carries the
  saved task_id under the profile-scoped v5.7.19 protocol. Failure may
  leave an already-attached orphan .txt; Notifier MUST refuse to call it
  prepared and NEVER auto-retry the upload or auto-Send.
- Original «Отправить» remains the Notifier new-message queue.
  Separate «Нажать Send» is ONLY a one-shot click for already prepared
  native ChatGPT draft. It does NOT re-insert text, create another task,
  re-attach files or switch profile. Before click, Notifier validates
  exact saved draft content, current paired session, task_id and Fortis
  context, and the named file card if draft_mode=file. Any ambiguity,
  edited draft, duplicate, disabled button or missing evidence refuses
  WITHOUT clicking. First attempt marks only send_unconfirmed, never
  confirmed ChatGPT receipt. No auto-retry after any failure.
- To right of File/Insert/Send/Modules/Prepared Send buttons, an owner
  Textbox timeline shows up to 30 latest events: queued, claimed,
  file_attached/inserted, send_initiated, refused and expiry. Every row
  shows approximate time, action, enumerated-safe reason code and task_id
  if available. No original prompt content, module bodies, secrets or
  keys in log. Timeline lives only in Windows Viewer server memory for
  the current process; 5s read polling updates it without Send.
- New `send_prepared` dispatch requires empty text and null profile/module
  overrides. Owner capability + live notifier heartbeat + at-most-once
  claim/ACK and no stale replay remain mandatory. Legacy insert/file
  ACK without task_id retains previous behavior only for legacy routes;
  profile-scoped new route rejects it.

Source test suite PASS: Notifier 5.7.19 216/216 Node tests; Windows
Viewer unit/UI source tests are verified separately. Real Edge smoke
must confirm file card, Fortis context, task_id and manual action.
Run the existing pinned Windows installer below AFTER copying latest
source to Windows checkout and update single existing Tampermonkey
Local Loader @require to point at the new v5.7.19 file. No second
Notifier script. Do NOT press «Нажать Send» during installation smoke.


## 20.10.2026 — один набор профилей Notifier и Observatory (Notifier 5.7.18)

Ранее Observatory получал только каталог module IDs, поэтому
отдельные галочки не соответствовали сохранённым профилям Notifier.
Теперь в профиле выбранной сессии Viewer есть SELECT с теми же
ID и названиями профилей, что в Tampermonkey текущей вкладки.
Отмеченные текстовые модули отображаются именно для выбранного
профиля. При смене профиля применяются текстовые модули И поведение
этого исходного профиля, включая паузу перед Send и focus option.

Notifier 5.7.18 раз в ~12 сек посылает по scoped owner Dispatch
metadata только names, IDs, списки IDs; module bodies, scripts,
secrets, GM contents не передаются. Viewer обновляет через свой
5-секундный read-only polling. По умолчанию Viewer следует
активному профилю Notifier; собственный выбор в Viewer остаётся
в памяти открытого Owner окна отдельно на сессию. ВАЖНО:
это ВЫБОР профиля для команды, а не операция создания/удаления
или изменения активного GM профиля Notifier. Профили и их
постоянные настройки создаются в самом Notifier.
Чекбоксы внутри Viewer дают только одноразовый override
text module IDs, не изменяют профиль GM.

HTTP протокол: profile_id — проверенный идентификатор из scoped
Notifier snapshot; module_ids:null означает использовать ТОЧНЫЕ
настройки выбранного профиля внутри Notifier. Любой неизвестный
profile_id отклоняется. Старые команды без profile_id остаются
обратно совместимы. Viewer не получает module body и не выполняет
JS-код Helper. File/Insert не вызывают Send; Send проверяется
отдельным live Edge тестом, НЕ подтверждён исходниками.

Чтобы включить новое поведение, Windows Owner Viewer требуется
переустановить по PIN SHA НИЖЕ, предварительно завершив старый
процесс на 18755; одновременно нужна ровно одна копия
Notifier 5.7.18. Отдельный Docker archive не менялся.
Требуется также убедиться, что Tampermonkey Local Loader @require
указывает на ОБНОВЛЁННЫЙ файл checkout: ранее пользователь показал
другой путь без папки Repos. Не переустанавливать Loader
параллельной второй копией. Real Windows/Edge smoke NOT_RUN.


## 20.10.2026 — полный адресный Fortis Textbox над колонками (Viewer + Notifier 5.7.16)

ТЕКУЩАЯ версия исходников. Owner Viewer и Notifier в Windows/Edge
нужно отдельно обновить; пока live smoke не выполнен.

Под липкой шапкой (НЕ sticky) размещается сворачиваемый
полноширинный Textbox выбранной сессии — над workspace-grid.
Его «Файл», «Вставить», «Отправить» — строго owner-local
адресные команды живой привязанной вкладке ChatGPT. Есть
«⚙ Модули» с поиском/галочками по реальному каталогу
Planning Helper Notifier. Модули передаются только по ID,
их текст готовит Notifier внутри исходной вкладки.
Активный профиль Tampermonkey GM не перезаписывается.

File: та же внутренняя функция handleQuickFile Notifier, что и у
собственной кнопки; оригинал в .txt, SHA-256 guard на
последовательные идентичные оригиналы, только одна попытка
прикрепления без «упал ACK -> повтор». При подтверждённом
прикреплении Notifier добавляет модули и task_id/Fortis context
в штатный ChatGPT редактор без замены прежнего текста. Send не
нажимается. Insert: та же prepareDraft/task_id + модули, Send
не нажимается, большой текст направляется по File-маршруту.
Send: та же безопасная persisted-очередь Notifier и только
send_initiated ACK после проверенного task_id + queue state.
После ACK нет гарантии фактического приёма ChatGPT/Repo receipt.

В Viewer у каждой сессии свой in-memory текст и свой
in-memory набор выбранных module IDs. Наличие/содержимое
Helper module не записывается в Docker archive и НЕ
передаётся Viewer. Каталог metadata ограничен 200 item, его
заголовки и ID проходят валидацию. Если каталог ещё не
синхронизирован — используется активный профиль Notifier;
пустой выбранный список — без текстовых модулей.
Источник названия модулей: сама вкладка Notifier, не
какой-либо внешний сервер.

Проверки: Python + Node synthetic PASS, Windows installed copies
и реальная File/Insert/Send проверка на конкретной Edge вкладке
ещё NOT_RUN. Не запускать двойной Notifier. Обновить оба компонента
сначала и проверить READ-only связь, затем File/Insert без Send;
Send тестировать отдельно после явного решения пользователя.


## 20.10.2026 — Viewer: сворачиваемые сведения, latest-record и 5-секундный polling

Обновлён только owner_viewer.py в Repo source. ПЕРЕУСТАНОВКА Windows
Viewer владельцем ещё не выполнялась; ранее установленный Viewer
не получает изменений автоматически. Шесть источников установки
PIN SHA ниже; единственная изменившаяся сумма — owner_viewer.py.

- Блок «Подробности сессии» — HTML details/summary, ЗАКРЫТ по
  умолчанию. В открытом состоянии URL, Chat ID, статус Notifier,
  approve/revoke и диагностические кнопки остаются работоспособными.
- При первом открытии Viewer и при каждом выборе другой сессии
  автоматически выбирается последняя задача по first_seen_at
  (дата принятия, не позиция в произвольном списке); в ней выбирается
  последняя хронологическая запись (событие или AI сообщение),
  список записей прокручивается до низа.
- Автоматический read-only polling каждые ~5 сек через прежние
  owner bearer API state/tasks/history/status/pending. НЕТ нового
  listener, нет webhook, нет запуска Notifier Send или другой команды.
  Когда предыдущий опрос ещё не завершён, следующий пропускается.
  Любой network/Repo outage отображает ошибку, не сбрасывая
  ручной выбор задачи/записи.
- Чекбокс «Автоследование» по умолчанию ВЫКЛЮЧЕН и держится только
  в памяти вкладки Viewer. Пока выключен, polling обновляет список
  задач/событий, но сохраняет выбранную задачу, запись, позиции
  прокрутки записей и деталей. Когда включён, сразу и после каждого
  опроса выбирает самую свежую задачу + последнюю запись и
  прокручивает записи вниз. Выбор другой сессии всегда открывает
  последнее независимо от чекбокса.
- Кнопка «Обновить» использует ту же read-only логику.
  Старые session permissions, archive bytes, SMTP/Repo service,
  отдельный Notifier userscript здесь не изменялись.

Только synthetic Node/Python source checks, настоящий Edge
пользователь должен проверить после ручной установки. Открывать
вторую копию Viewer или выключать Docker Observatory не требуется.
Не путать локальный 5-секундный browser-poll с приёмом AI события.


## 20.10.2026 — исправление PowerShell ParserError установщика

Установка Windows Viewer с шестью PIN_SHA остановилась до начала выполнения
из-за шести случаев разрыва Get-FileHash -LiteralPath переводом строки
между параметром и значением. Они исправлены в
Install-FortisObservatoryViewer.ps1; SHA шести УСТАНАВЛИВАЕМЫХ исходников
не менялись. Контрольная SHA256 САМОГО установщика после исправления:
47f194b647d7118328636128b9ed05b6c9c56286467d2ce7b9db8abfc661b61f

Перед повторным запуском в PowerShell 5.1 в Windows проверить совпадение
суммы установщика и синтаксис через Parser::ParseFile БЕЗ выполнения:
$src = "C:\Users\alexa\Repos\tunnel\observatory\v1"
(Get-FileHash -Algorithm SHA256 "$src\Install-FortisObservatoryViewer.ps1").Hash
$tokens=$null; $parseErrors=$null
[System.Management.Automation.Language.Parser]::ParseFile(
  "$src\Install-FortisObservatoryViewer.ps1", [ref]$tokens, [ref]$parseErrors) | Out-Null
if ($parseErrors) { $parseErrors | Select-Object -ExpandProperty Message }
else { 'SYNTAX_PASS' }

Если checksum другой, Windows checkout ещё не получил исправленный исходник
и повторная установка запускать НЕЛЬЗЯ. Linux static regression
test_owner_installer_syntax.py PASS; реальный PowerShell Parser у владельца
на Windows ещё требуется (pwsh отсутствует в Repo Docker).


## 20.10.2026 — автоматическое обнаружение Notifier и повторное подключение после reboot

НОВОЕ: Viewer + Enrollment + Autostart installer (6 SHA) и Notifier 5.7.15.
Пока только исходники. Установленные Windows/Edge процессы не обновлены.

1. Владелец добавляет URL ChatGPT в Owner Viewer. Вкладка с установленным
   Notifier 5.7.15 должна быть открыта (но переключаться на неё не нужно).
2. Notifier сам каждые ~7 секунд объявляет текущий Chat ID и случайный
   256-bit proof на Windows loopback 127.0.0.1:18755. Только URL НЕ
   позволяет получить ключи. Неизвестные Chat ID и чужие Origin
   не получают доступа.
3. В Owner Viewer рядом с выбранной сессией появится «Notifier обнаружен».
   Владелец нажимает «Одобрить найденный Notifier» ОДИН раз.
   Никакой ручной код в Tampermonkey не требуется.
4. Proof Notifier остаётся в GM-хранилище этого чата. Владелец сохраняет
   только SHA-256 proof в approved-notifiers.json внутри owner-ACL
   защищённого каталога Viewer. После перезагрузки Windows, Viewer,
   Edge или Tampermonkey живой pairing восстановится автоматически,
   когда вкладка снова откроется. Не восстанавливаются просроченные
   команды, нет автоматического Send/retry.
5. В Viewer доступна кнопка «Отозвать постоянную привязку».
   Она запрещает автоматическое восстановление прав dispatch, но
   НЕ выполняет ротацию старых отдельно выданных Repo observer/writer
   ключей. Полная ротация требует отдельного средства управления
   авторизацией Repo.
6. Необязательный owner-only автозапуск ПОСЛЕ Windows sign-in:
   один раз выполнить из PowerShell владельца:
   & "$env:LOCALAPPDATA\FortisObservatoryV1\Viewer\Enable-FortisObservatoryAutoStart.ps1"
   Чтобы отменить, выполнить эту же команду с параметром -Disable.
   Используется только HKCU Run. После входа в Windows wrapper ждёт
   до 15 минут существующий Docker Desktop и контейнер fortis-repo-test.
   Он НЕ запускает контейнер, не открывает сеть и не создаёт второй
   экземпляр при занятом порте. Docker Desktop должен быть настроен
   отдельно на запуск при входе. Временный Viewer owner code нужно
   вводить в UI после каждого restart, но связь Notifier не требует
   открытой авторизованной страницы Viewer.

Важное ограничение: синтетические тесты Windows endpoint/JS и
перезагрузки не заменяют настоящий Edge, PowerShell ACL/install и
Windows reboot smoke. Пока владелец их не выполнил, реальный
автозапуск и автоматическое переподключение НЕ ПОДТВЕРЖДЕНЫ.


## 20.10.2026 — диагностика URL и Notifier (только исходники до owner установки)

Owner Windows Viewer доработан: под выбранной сессией показывается
проверенный URL беседы https://chatgpt.com/c/<conversation_id> из
зарегистрированной Repo сессии, Chat ID и reporting_session_id.
Новая строка «Notifier» и кнопка «Проверить связь Notifier»
используют существующий защищённый owner API /api/dispatch/status.
Никакие ключи Notifier или секреты owner bearer не публикуются.

ОТДЕЛЬНЫЕ состояния:
- paired=false: для этой сессии в памяти ЭТОГО ЗАПУСКА Viewer
  ещё не получали код привязки; это не показатель прошлых запусков;
- paired=true, ever_seen=false: код получен, но НЕ было
  подтверждённого опроса от подходящего Notifier;
- available=true: ключ/Chat ID подтвердились в /api/dispatch/poll
  за последние 15 сек (реальная живая привязка, без отправки сообщений);
- ever_seen=true, available=false: ранее был опрос, но сейчас
  вкладка не подтверждает связь, последняя давность в секундах.

Проверка автоматическая каждые ~5 сек или вручную, без отправки
ChatGPT сообщения. Не следует трактовать ни одно состояние
как доказательство фактического Send, входа AI в Repo или receipt.
Владельцу требуется снова вручную установить только ОДНУ копию
Windows Viewer через ниже приведённый PIN SHA, предварительно закрыв
старый процесс 18755. НОВЫЙ Viewer при запуске теряет старый
in-memory dispatch_key, поэтому после обновления потребуется
заново сгенерировать код и вставить в Tampermonkey ТОЙ ЖЕ
открытой беседы, без копирования приватного кода в чат.
Docker Repo archive и Tampermonkey source этим изменением не менялись.


## Актуальное состояние применения 20.10.2026

Repo Observatory HTTP server **перезапущен** контролируемо на том
же 127.0.0.1:18754, старый PID завершён, новый работает на
исправленном исходнике. Repo archive read-back подтверждён:
2 прежние сессии, 42 события, без изменения количества каждой.
Общее состояние ingest available, без bearer API вернул HTTP 401.
Docker-контейнер НЕ рестартовали.

Windows Viewer 3 SHA + Notifier **5.7.10** всё ещё требуют ручной
установки владельцем alexa по командам ниже. Ожидать, что
обновление исходников автоматически изменило установленную Windows
копию/Edge, нельзя. Перед настоящей отправкой выполнять
EDGE_SMOKE_2026-10-20.md. Тесты Windows ACL/PowerShell и
Edge загрузки файлов/Send ещё не проводились. Pairing codes,
dispatch keys и viewer code не передавать в чат.


## Post-review: новый exact SHA для owner_dispatch.py

Исправлена очистка просроченных in-memory команд на каждом poll;
для ещё актуального dispatch_id разрешён поздний подтверждённый ACK,
автоматического повторного Send нет. Installer требует тот же набор
из трёх исходников и SHA. Новая dispatch SHA уже актуализирована
ниже (у Viewer и bridge SHA без изменений). Windows installation
и live Edge/Owner smoke не выполнялись.


## 20.10.2026 — адресный текстбокс, новый независимый ключ

Owner Viewer содержит закрытую по умолчанию форму «Написать в выбранную
сессию» в четвёртой колонке. Она поддерживает действия «Вставить без Send»
и «Отправить в выбранный чат» и хранит по одному черновику на сессию
только в памяти открытой страницы.

Код привязки Notifier теперь имеет ТРЕТИЙ dispatch_key, отдельный
от observer_key / message_writer_key. После установки НУЖНО повторно
привязать конкретную открытую беседу через меню Tampermonkey, иначе
адресная отправка не включится. Разрешение позволяет владельцу
из локального Viewer инициировать Send через Notifier; его нельзя
передавать в чат, логи или сторонние приложения. При перезапуске
Windows Viewer ключ очереди и команды теряются, привязку для
удалённой отправки следует обновить. Старые read/writer-ключи
сохраняют свои права, НЕ превращаются в права Send автоматически.

owner_dispatch.py — новый обязательный модуль Windows Viewer, поэтому
обновлённый ручной установщик требует ТРИ SHA-256 ниже и проверяет
все три файла до и после копирования. Старой командой с двумя SHA
новый Viewer не устанавливать. Режим адресной доставки НЕ требует
нового Docker listener или отдельного браузерного релея; команды
живут в памяти Windows Viewer и доступны только текущей
авторизованной / привязанной сессии. Закрытые вкладки не получают
команду, отложенной очереди нет. Команда выдается единожды
по dispatch_id — без автоматических повторов после неопределённого
результата. Статус send_initiated = локальная очередь Notifier,
НЕ доказанный ChatGPT Send и НЕ receipt точного оригинала.

Важно: исходники проверяются синтетически, настоящий Edge smoke,
проверка ручного Windows Installer в owner PowerShell,
обновление Docker службы и установленного Tampermonkey НЕ выполнены.


## 20.10.2026 — подробные пояснения событий (исходники, установка не выполнена)

Изменены источники Store/Repo sender и Owner Viewer. Для значимых
progress/checkpoint AI может передать содержательное пояснение шага
как UTF-8 STDIN флагом --detail-stdin в repo_task.py event.
Краткий summary до 140 символов остаётся метаданными; событие
получает связанный подробный текст (до 8192 байт, контроль
архивного размера). Старые события остаются короткими.
В Viewer раскрываются detail записи выбранной задачи; все
подробности разом в /api/state не загружаются.
Сведения sender-claimed, не доказательство скрытых мыслей AI.
Запущенный старый Repo Observatory не умеет читать новый event
bundle; новые события останутся в staging без приёма до
штатного обновления и контролируемой проверки active-сервера.
Полный interim/final по-прежнему через repo_task.py message,
оригинал пользователя — только от Notifier. Не добавлять секреты.

Для обновлённого Viewer использовать ниже новый exact SHA-256.
Сначала owner вручную закрывает текущий Viewer, обновляет
Repo Observatory и проверяет archive, потом устанавливает
Viewer, затем сверяет работу на Edge. Ничего автоматически
не перезапущено и не установлено.


AI продолжает отправлять события и свои полные ответы через Fortis Repo.
Общий архив по-прежнему только в Docker; Windows Viewer — только ручной
интерфейс и узкий путь оригиналов из Notifier.

## 20.10.2026 — длинные оригиналы после сборки Notifier 5.7.5

В Repo исходники нового owner Viewer/bridge разрешают точные оригиналы
до 512 КиБ UTF-8 (вместо 64 КиБ); тот же предел применяется к API,
relay и архиву существующего Docker Observatory. Старые версии,
уже запущенные в Windows/Docker, продолжают применять СТАРЫЕ ограничения.
Порядок применения: сначала контролируемо обновить/перезапустить
существующий Observatory в Repo Docker без сброса архива; затем
повторно установить существующий защищённый Windows Viewer с
обновлёнными проверенными SHA ниже, запустить его; и только после
этого заменить текущий Tampermonkey Notifier на 5.7.5 и обновить Edge.
Не запускать параллельно второй экземпляр Viewer или Docker сервера.
После установки проверить длинный синтетический промпт в настоящем Edge.
Сами скрипты остаются source-only; текущие службы этим изменением
не перезапускались.

## Четыре регулируемые колонки (источник 20.10.2026)

После ввода кода просмотра верхняя панель с заголовком и кнопками
остаётся видимой при прокрутке страницы. Основная область состоит
из четырёх колонок: «Сессии» → «Задачи» → «Записи» → «Подробности».
В третьей колонке разные цвета отличают точный оригинал пользователя
(зелёный), событие работы (янтарный) и полное сообщение AI (синий).
Нажатие на карточку показывает подробности только этой записи справа.

«Событие» — метка шага: тип, стадия, краткое описание, номер и время,
если они представлены в архиве. «Сообщение AI» — полный сохранённый
текст interim/final без сокращения; карточка слева показывает превью.
Если оригинал пользователя не поступил, его карточка явно сообщает
об отсутствии текста — содержимое AI не используется как замена.

Для изменения ширины перетаскивайте три тонких разделителя между
колонками. Можно использовать стрелки ←/→, при Shift шаг больше;
двойной щелчок по разделителю восстанавливает пропорции по умолчанию.
Выбранные ширины сохраняются до обновления страницы; на узком окне
четырёхколоночная область прокручивается горизонтально.

Кнопки «Добавить сессию», «Инструкция», «Привязка Notifier» открывают
служебные панели только по запросу. Код привязки очищается при смене
сессии. Никакие API, ключи, права и Docker архив не менялись.

Изменения произведены только в Repo checkout. Чтобы увидеть их в Edge,
закройте предыдущий Windows Viewer, повторите существующую защищённую
установку с новым SHA-256 ниже и откройте Viewer. Установка на Windows
не выполняется автоматически инструментами Fortis Repo.

## Новая панель

Карточки задач показываются по времени первого принятого сигнала
в порядке работы: номер, локальное время Edge и до 105 символов
настоящего оригинала. Если точный оригинал отсутствует,
показано «— Оригинал ещё не получен» и фактическое время события.
Нельзя заполнять оригинал восстановленным текстом AI.

Выбрав сессию и открыв верхнюю кнопку «Привязка Notifier», можно получить «Код привязки Notifier» —
обособленные observer, writer и dispatch keys только этой сессии. НИКОГДА не
отправляй эти ключи в чат. Код вставляется через меню Tampermonkey
«Fortis: привязать текущий чат» в соответствующей беседе.

Для новых сообщений с origin http://127.0.0.1:18755 Notifier
сначала локально сохраняет точный текст. После принятого события
соответствующего task_id он через узкий владелец-local viewer
отправляет оригинал в Docker; digest SHA-256 receipt проверяется.
Старые сообщения без привязки/другого origin не мигрируют.

## Шаги владельца Windows alexa

1. Закрой старое окно Start-FortisObservatory.cmd, чтобы освободить порт 18755.
   Docker Observatory и архив НЕ выключай и не удаляй.
2. Независимо проверь исходники и installer в Repo checkout, а также
   шесть контрольных сумм. В обычном PowerShell под alexa:

~~~powershell
$src = "C:\Users\alexa\Repos\tunnel\observatory\v1"
Get-FileHash -Algorithm SHA256 "$src\owner_viewer.py"
Get-FileHash -Algorithm SHA256 "$src\owner_notifier_bridge.py"
Get-FileHash -Algorithm SHA256 "$src\owner_dispatch.py"
Get-FileHash -Algorithm SHA256 "$src\owner_enrollment.py"
Get-FileHash -Algorithm SHA256 "$src\Start-FortisObservatoryAuto.cmd"
Get-FileHash -Algorithm SHA256 "$src\Enable-FortisObservatoryAutoStart.ps1"
~~~

Viewer SHA-256: aae05194e48001aefcffb850061ba7266e956f821efbf398834c35e6820efbc2
Bridge SHA-256: 818089f6796fb2877dcce8535953ec179072b217ae62cb2afb3c189a337ba195
Dispatch SHA-256: a00d22dfdf4cfc8902e85cfd7b101867dc9507fb99f9b4b5352ffe1d5a81a31f
Enrollment SHA-256: 51ce3eb96fd3da285c591c063cb71642863b825d5fef63bc6c5060a814ca03e3
Auto CMD SHA-256: 857647ef4b4efdda6334cb7772ce899cfdc5061203b3dfa641efad94f457a9e1
Auto enable PS SHA-256: 003a65ec88a10810545d01c8aa69e0af6827d35ba8948e93b6e80dd8428bfd82

3. Если все шесть сумм совпали, установи обновление ОДНОЙ командой:

~~~powershell
& "$src\Install-FortisObservatoryViewer.ps1" -Container "fortis-repo-test" -ExpectedViewerSha256 "aae05194e48001aefcffb850061ba7266e956f821efbf398834c35e6820efbc2" -ExpectedBridgeSha256 "818089f6796fb2877dcce8535953ec179072b217ae62cb2afb3c189a337ba195" -ExpectedDispatchSha256 "a00d22dfdf4cfc8902e85cfd7b101867dc9507fb99f9b4b5352ffe1d5a81a31f" -ExpectedEnrollmentSha256 "51ce3eb96fd3da285c591c063cb71642863b825d5fef63bc6c5060a814ca03e3" -ExpectedAutoCmdSha256 "857647ef4b4efdda6334cb7772ce899cfdc5061203b3dfa641efad94f457a9e1" -ExpectedAutoEnableSha256 "003a65ec88a10810545d01c8aa69e0af6827d35ba8948e93b6e80dd8428bfd82"
~~~

4. Запусти локальную защищённую копию и открой Edge:

~~~powershell
& "$env:LOCALAPPDATA\FortisObservatoryV1\Viewer\Start-FortisObservatory.cmd"
~~~

Адрес: http://127.0.0.1:18755/
Введи временный viewer code из owner-консоли ТОЛЬКО в Edge, не в чат.

5. Обнови только СУЩЕСТВУЮЩИЙ Tampermonkey userscript из
C:\Users\alexa\Repos\tabnotifier-fileautosend-autochat\chatgpt-tab-notifier.user.js
до версии 5.7.28. Сохрани, убедись, что нет второго включённого
экземпляра Notifier, и перезагрузи нужную беседу ChatGPT.
6. В Viewer в «Чаты из браузера» нажми «Подключить» у нужного Chat ID.
URL вручную вводить и pairing code копировать не требуется. Для уже
подключённых сессий прежнее одобрение сохраняется. Отдельное разрешение
«Метаданные сохранённых задач» по-прежнему выдаётся в подробностях сессии.
7. Раскрой новый Textbox над колонками. Выбери модули через «⚙ Модули»,
проверь «Вставить» и «Файл» БЕЗ Send. Проверь одну .txt карточку,
текущий task_id, отсутствие повторов и сохранение текста Viewer.
Только после отдельного согласования допускается тест «Отправить»
с последующим подтверждением события и полного ответа в архиве.

## Границы

Viewer запускается только вручную под alexa и требует owner-private
Windows SID/ACL, approved existing контейнер Docker и проверенные SHA.
Не открывает Docker порт в сеть и не создаёт второй архив.
Для Notifier открыты узкие observer-status/task-activity и user-message POST,
а с отдельным разрешением — task-intents/task-send-state POST. Каждый
путь проверяет своё сессионное право; metadata не разрешает архивирование. Общее API истории/регистрации
не доступно этим ключам. Авторизованный writer не может заменить
другой уже принятый оригинал или записать до accepted activity.
Подлинность DOM ChatGPT отдельно не подтверждается.
Исходники готовы; Windows owner-positive/guest-negative и Edge smoke
должны пройти после ручной установки.


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
