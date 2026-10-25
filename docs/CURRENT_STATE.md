# Текущее состояние — датированный срез

## 25.10.2026 — Project Checker: Tkinter GUI source и Windows layout preflight

Добавлены checker/windows_layout.py, checker/ui_model.py и checker/gui.py. Tkinter source содержит вкладки проектов, правил, отчётов, preview и проверки схемы размещения, но кнопки проверки/обновления отключены до независимой защищённой Windows-установки. Никакого Windows визуального прогона нет: Tkinter недоступен в Docker. Схема путей всегда требует native path/ACL/agent-write проверки, даже при отсутствии явных пересечений. [Описание границы](userscript-updater/WINDOWS_TRUST_BOUNDARY.md), [журнал](userscript-updater/IMPLEMENTATION_LOG.md). Внешние user-consumed copies и Windows profiles не менялись.

## 25.10.2026 — Project Checker: лаборатория транзакции/отката без Windows-допуска

Добавлена отдельная **синтетическая** лаборатория devtools/fixture_transactions.py: сборка заранее проверенных байтов, резервные копии, JSON-журнал, демонстрационная привязка preview/source/policy/target, отказ при дрейфе и тесты восстановления после прерывания. Она жёстко ограничена временными тестовыми каталогами и **не** входит в пакет checker как действующий updater. Уточнён preview: пустые папки и ранее управляемый состав входят в fingerprint. Реальные ESLint+Semgrep тесты включены, 74/74 PASS без skips. НЕ созданы защищённая Windows-установка, реальный пользовательский допуск, Windows GUI и разрешённый external update. [Факты и недостатки](userscript-updater/IMPLEMENTATION_LOG.md). Все более ранние описания ниже — исторические.

## 25.10.2026 — Project Checker: предварительный просмотр без обновления

Добавлен read-only расчёт последствия обновления на синтетических деревьях: create/modify/delete/unchanged, текстовый diff, хеши бинарников, preserved unmanaged files и fingerprint фактического target. Не создаётся интерфейс доверенного подтверждения, файлы назначения не меняются, удаление строго ограничено ранее управляемыми путями. 49/49 тестов PASS с включёнными ESLint и Semgrep внутри Docker. Ничего не перенесено в Windows; будущие Windows ACL/handles, backup/rollback, UI и реальная установка ещё не готовы. [Журнал работы](userscript-updater/IMPLEMENTATION_LOG.md).

## 25.10.2026 — Project Checker: реальные ESLint и Semgrep внутри Docker

Через Fortis Repo проверены ESLint 10.13.0 и Semgrep CE 1.182.1 на безопасных и запрещённых синтетических JS/Python. Пройдено 40/40 Python-тестов без skips при подключённых Docker CLI. Появилась таблица покрытия по файлам; неизвестные типы файлов не пропадают из отчёта. Защищённой Windows-установки, trusted policy, GUI, внешнего обновления, ACL и пользовательской приёмки пока нет. [Подробный журнал и ограничения](userscript-updater/IMPLEMENTATION_LOG.md). Более ранние разделы ниже — датированные срезы, не последний статус.

## 25.10.2026 — Project Checker: начало разработки после pre-work

По отдельному поручению пользователя начата разработка исходников внутри Fortis Repo Docker. Реализованы кандидатные модель регистраций, инвентаризация/снимки, общие пакеты правил, разбор JSON ESLint/Semgrep. Пройдены 30 тестов, в том числе настоящий ESLint 10.13.0 на двух синтетических JS внутри Docker. Semgrep реально не запускался. Нет защищённой Windows-установки/правил, обновления Loader/внешней копии, GUI и пользовательской приёмки. [Журнал и пределы проверки](userscript-updater/IMPLEMENTATION_LOG.md). Ниже сохранён датированный срез предыдущего этапа «только хендофф».

## 25.10.2026 — userscript updater: требования и хендофф

Подготовлен [пакет продолжения](userscript-updater/README.md): требования пользователя, план разработки/проверок и фактическая точка остановки. Текущий статус проекта ведётся там. Код updater, защищённая установка и анализаторы этим этапом не создавались/не устанавливались; изменения ограничены документацией и навигацией.

## 25.10.2026 — Observatory: актуальная сводка и границы проверки

Текущий состав Observatory/Notifier, owner API, различие source/Windows install, результаты пользовательского теста и открытые вопросы теперь ведутся в [README V1](../observatory/v1/README.md). Здесь и ниже сохраняется датированная история; старые PID/версии/статусы «не установлено» не являются live-конфигурацией.

Обновление 25.10 касается документации и сохранения ранее подготовленного owner-local API helper. Runtime/установки/ACL/ключи не изменены; Viewer, Docker и туннели не перезапускались, Send не выполнялся, публикация GitHub не проверялась. Детальные воспроизводимые результаты относятся к указанным пакетам; успешную файловую доставку отменённого пользователем теста не заявляем.

## 24.10.2026 — общий workflow: узкий Godot scope и постоянный план

Пользовательские сценарии, инварианты и Git-порядок ведутся в [agent-workflow](agent-workflow/README.md). Актуальный срез этой инициативы и ближайший шаг — [STATE](agent-workflow/STATE.md); источники и хеши файловой проверки — [JOURNAL](agent-workflow/JOURNAL.md).

После ручного grant владельца G2 подтвердил чтение проекта и создание/чтение/удаление собственного marker, видимого также Docker с тем же SHA-256. Корни Repos/Workfiles по проверке метаданных остаются недоступны G2. Это PASS только файлового scope: запуск Godot/игры, GPU/GUI и общий personal-security PASS не заявляются. Никакой новый runtime в этой фиксации не развёрнут.

## 22.10.2026 — Notifier 5.7.31: selected Prompt card (SOURCE TESTED)

Owner screenshot confirms a Helper Prompt is now listed and attached; it had
only a plain connected-name line, whereas attached Modules had bordered items.
Selected Prompt now uses the same module-row card styling, with its title and
an inline accessible × detach button. Full stable ID is in the title tooltip.
The separate detach button next to the selector is removed. A missing selected
Prompt remains visible with an unavailable label; switching profiles updates
card visibility and text. Empty profiles show the normal no-prompt message.
Explicit module-row[hidden] CSS prevents the flex rule exposing an empty card.

Presentation-only change in textbox-settings-ui.js, plus version metadata.
Manager, profile storage, Prompt/module resolution and the 5.7.30 mixed-catalog
fix remain byte-identical. Helper 0.40.10, Viewer/backend, Send, queue, original
archive, pairing and running processes are unchanged. No new permission, no
automatic insertion or Send. No installed browser script was modified.
Full Node suite 285/285, no skips; build:check PASS. Existing event-driven DOM
fixture covers attach, prompt card/title/ID, profile restore, unavailable card
and detach without Send. No new tests were added for this reversible UI edit.
Real Edge appearance of 5.7.31 remains NOT_RUN; owner's screenshot is pre-fix.
Main and immutable chatgpt-tab-notifier-5.7.31.user.js SHA-256:
482056d051bb5555cb2eeab47d32c8e08f0ce91974b455b79ce8e03d8d23bbf8
Checkpoint: /workspace/repo/fortis-prompt-card-20261022
Manual: update only EXISTING Notifier Loader @version/@require to 5.7.31;
preserve name/namespace/grants/GM data, save draft then reload ChatGPT. Existing
selected Prompt should immediately appear as a card without re-attaching it.
Helper and Observatory do not need an update or restart for this UI change.


## 22.10.2026 — Notifier 5.7.30: mixed Helper catalog replies + truthful version badge (SOURCE TESTED)

Owner screenshots show Helper UI 0.40.10 and Notifier badge 5.7.28. The 5.7.29
bundle incorrectly retained SCRIPT_VERSION=5.7.28 despite its 5.7.29 header;
the badge therefore did not prove that an old bundle was loaded. Corrected in
5.7.30; build and build:check now reject a package/runtime version mismatch.

A real-publisher regression reproduced another failure: a valid Prompt+Module
catalog could be overwritten by a later module-only reply from a still-open
old Helper tab. After the first validated full catalog, Notifier now ignores
legacy replies for the lifetime of that manager, retaining modules and prompts
as one atomic snapshot. Legacy-only startup remains compatible for modules.
Modern updates and empty/deleted catalogs remain authoritative. Invalid modern
catalogs clear cached bodies and block preparation; a legacy reply cannot
restore them. A valid modern packet recovers normally. No GM profile mutation
occurs on receiving or ignoring catalogs.

This is a reproduced code defect and a plausible explanation of the owner's
missing list; the actual set of running Helper publishers in Edge was not read.
The old diagnostic that always said to update Helper was too specific. It now
says the prompt catalog has not been received and suggests refreshing ChatGPT
tabs. Helper source 0.40.10 is unchanged; no repeated Helper update is required.

Regression tests were RED before the fix (four failures); after the fix the
full Notifier suite passes 285/285 with no skips and build:check PASS, including
real Helper projection, both arrival orders, deletion, malformed catalog,
read-only GM behavior, UI events and build-version mismatch rejection.
No live Edge acceptance or automated browser install was performed. Existing
Windows Viewer, pairing/GM originals, backend services and Send were untouched.
Source main and immutable chatgpt-tab-notifier-5.7.30.user.js SHA-256:
e90df0cbd24dcf76db7eeb916f007ca0eb0db33ecc0627156c3298715f7d4eb1
Old immutable 5.7.28 and 5.7.29 files remain exact for code rollback.
Checkpoint: /workspace/repo/fortis-helper-catalog-race-20261022
Manual: update ONLY the existing Notifier Loader @version/@require to 5.7.30,
keep name/namespace/grants, save valued drafts and refresh ChatGPT tabs. Verify
the badge is 5.7.30 and the prompt count/list appears; select/detach without Send.
If still absent, report the current catalog status line; do not infer success.


## 22.10.2026 — Helper Prompts in Notifier Textbox (SOURCE TESTED, MANUAL INSTALL PENDING)

Notifier 5.7.29 adds an optional per-profile Helper prompt selector with search,
attach/detach and preview. Order: exact user original, selected resolved prompt,
then ordered extra modules. Original archive bytes stay unchanged; selecting a
prompt only saves its ID and never inserts, attaches a file or presses Send.
The existing preparation/File/Send safety path is unchanged.

Helper 0.40.10 adds a separate optional prompts[] field to the existing local
read-only BroadcastChannel catalog. Prompt/module texts stay in Helper's local
snapshot and transient consumer RAM; Notifier GM profiles store references only.
Commands, GitHub credentials and repository metadata are not projected. No
implicit GitHub reads or writes. Current source Helper was 0.40.9, newer than
the supplied 0.39.10 snapshot; it was extended in place, never replaced by ZIP.

Legacy profiles/catalogs remain compatible for modules. A selected prompt with
an old Helper, missing body/dependency, cycle or malformed catalog blocks
preparation rather than silently omitting instructions. Prompt module expansion
uses existing literal [[module:id]] references, depth/length limits, no eval.
Module overrides from Observatory retain the saved selected-profile prompt;
there is no new remote prompt-selection payload or Viewer/backend update.

Checks: Notifier full suite 280/280 (including event-driven DOM fixture),
Helper 230 tests, both build:check. Final logs are in checkpoint below.
No installed Chromium here; real Edge visual/GM/BroadcastChannel QA NOT_RUN.
No running service, Windows installed Viewer, browser Loader, GM originals,
pairing approvals, live Docker state, tasks or Send were changed by this work.

Notifier main + immutable chatgpt-tab-notifier-5.7.29.user.js SHA-256:
291790febbee4de03d5a2915494686080a0a3b9c01550889f1a02940b358c7b7
Helper main + immutable chat-command-palette-0.40.10.user.js SHA-256:
97f9ba6bf7a1bf249f05016fa5c1db5235ff805478db9591abbbb687b13e44cc
Checkpoint: /workspace/repo/fortis-helper-prompts-20261022
Manual: update the EXISTING Notifier Loader version/require to 5.7.29 without
changing name/namespace/grants; update the EXISTING Helper code/require to
0.40.10 without deleting its GM snapshot or GitHub token. Reload ChatGPT only
after saving a valuable draft. Use gear -> Prompt -> Attach; inspect preview,
then detach as smoke test, without File/Send. No Observatory reinstall/restart.


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
Viewer SHA-256: 34558e098d27139dcec95333bb4f8b51907e03820a902207e47b07d2e87aead6
Enrollment SHA-256: 51ce3eb96fd3da285c591c063cb71642863b825d5fef63bc6c5060a814ca03e3
Notifier 5.7.28 SHA-256: d506f6d7824ac1fcf868290da44f9f2e991acd42514fac31bdb6060fbedc99c5
Требуется ручное обновление Viewer и одной существующей копии Notifier.
Рекомендуемый порядок: Viewer, затем Notifier и reload вкладок.
Старые команды с SHA предыдущего Viewer/Enrollment к новой source не подходят.
Windows установленную копию, pairing/GM originals и live backend PID 15984
не изменяли/не перезапускали. Новый Edge live QA ещё не выполнен.

Финальная проверка: Python 195/195 PASS без skips; Notifier 270/270 PASS,
build:check PASS. Synthetic Viewer UI прошёл прежние сценарии и новые
названия/rename/safe-DOM/stable-task проверки. По скриншоту владельца
предыдущий раздел «Чаты из браузера» уже виден с ID. Наличие нового
title-варианта в установленной Windows копии пока не подтверждено.

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

Проверено до публикации source: Python discovery 187 tests — OK
(186 executed, 1 palette test skipped из-за отсутствовавшего sibling fixture).
Прежний Notifier palette fixture скопирован без изменений, пропущенный
contract test выполнен отдельно: 1/1 PASS. Все проверки покрыты.
Synthetic Viewer UI: прежние layout/lifecycle/stale checks и новый
discovery/one-click/ambiguity/safe-DOM сценарий PASS. Windows installation,
native ACL smoke и реальный Edge для новой функции ещё не выполнены.

## 21.10.2026 — Offline outbox backend активен, браузерное обновление ожидается

Проверенный source перенесён в /workspace/repos (15 файлов с SHA read-back).
Обновлён только процесс backend Observatory: PID 15984,
/workspace/repo/fortis-offline-outbox-20261021/candidate/repo_service.py.
Тот же state dir и loopback 18754; прежние 3 сессии/события сохранены,
ключи совпали до/после, observer API двух привязанных сессий и ограничения
owner API проверены. Live bootstrap содержит offline/current-chat правила
без session ID; реальная pending-context очередь пуста, synthetic событий
в рабочий архив не добавляли. Резервная версия/manifest сохранены рядом.
Manifest SHA 17164ec9b544194fd1bc674c6d0cec5333bec26438f972668fc0795543057f21.

Python 172/172 (включая автоматический collector после регистрации),
Node 264/264 без skips, build:check и synthetic Viewer UI PASS.
Notifier source 5.7.27 SHA:
c3023e49f30fc349d46b99779f7f5f718dd610707875168380db7472a569e17d.
Backend умеет новую очередь, но браузерная установка 5.7.27 НЕ подтверждена.
Следующий ручной шаг — обновление одной существующей копии Notifier/Loader
с сохранением @name, @namespace и GM storage; новую параллельную копию
не создавать. Windows Viewer, Docker/container, сеть и автозапуск не
перезапускались/не переустанавливались. Ручной Send и оригиналы сохранены.

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

## 21.10.2026 — Windows Viewer установлен, подтверждение владельца

Владелец сообщил «все тру» для INSTALL_SOURCE_VERIFIED,
INSTALL_OWNER_ACL_CHECKED, INSTALL_DOCKER_VOLUME_FOUND и MANUAL_START_READY
после команды pinned installer. Команда также проверяла полный SHA
backup owner_viewer.py = 2455109587431bf12705803200a953774c2e7f81e222aef74ecb5665f35daa54.
Windows source/installed Viewer соответствует проверке installer:
81bfb0980bba0daea94db7aec477da009c863c3ebf59dbfcc28fd75b69299ea3.
Это подтверждение пользователя; прямого доступа Repo к AppData нет.
Следующее действие — запуск установленного Start-FortisObservatory.cmd
и приёмка UI. Запуск/браузерная приёмка пока не подтверждены.
Docker backend candidate отвечает, две сессии. Обновление Notifier до
5.7.25, отдельный metadata grant и browser live QA остаются впереди.

## 21.10.2026 — Windows backup подтверждён владельцем

Владелец выполнил inline PowerShell backup установленного Viewer:
BACKUP_OK=True, путь
C:/Users/alexa/AppData/Local/FortisObservatoryV1/Viewer/backup-15a23bcc9d0b452b95a4ac9cb26448e3.
Команда копировала installed code/launchers и available approvals/config,
со сверкой SHA каждой копии. В ответе SHA owner_viewer.py обрезан до
24551095; полная идентичность legacy Viewer ещё должна провериться
локально перед установкой. В Repo не получены JSON/секреты Windows.
Новые 8 source файлов Viewer/installer повторно сверены с candidate manifest.
Следующий шаг — ручная установка Windows Viewer с pinned SHA через
существующий installer; выполнение/успех пока НЕ подтверждены.
Docker backend candidate уже активен. Notifier остаётся последней
подтверждённой версии 5.7.23; metadata grant и browser live QA ещё впереди.

## 21.10.2026 — этап E: Docker backend обновлён и проверен live

По указанию владельца «выполнять» выполнен отдельный доступный этап:
перезапущен только процесс Observatory, с legacy baseline на проверенный
candidate /workspace/repo/fortis-rollout-5.7.25-20261021/candidate/repo_service.py.
PID 3424, loopback 18754, прежний state dir и архив. Docker/container/Tunnel
не перезапускались. Перед активацией SHA всех baseline/candidate файлов
сверены с manifest 885bb8ee... . Скрипт переключения и состояние находятся
в том же private пакете: activate_backend.py, backend-activation-state.json.
Предусмотрен возврат к baseline при отказе проверок; он не потребовался.

Live HTTP: /api/state OK, обе существующие пары сохранены, events_count
не уменьшился, инвентарь существующих ключей совпал до/после. Для обеих
сессий owner GET task-intents и observer GET observer-status/task_overview
успешны; available=true. Анонимное и observer-only чтение owner intents
получили 401. Повторная health-проверка после завершения переключения PASS.
Никакие intents, metadata grants, тестовые события/оригиналы или Send
для live-проверки не создавались. Новые API теперь активны в Docker.

Windows Viewer/Notifier не установлены/не обновлены; последняя подтверждённая
версия Notifier 5.7.23. G2 вновь недоступен (429), поэтому Windows installed
backup и последующее обновление остаются незавершёнными. Старое подключение
«Туннель» не использовать. Копия кода в Workfiles ранее проверена (41 файл).

## 21.10.2026 — Observatory запущен по запросу владельца

По явному запросу владельца через Fortis Repo запущена отсутствовавшая
служба Docker Observatory: legacy код до task-status update из
/workspace/repo/fortis-rollout-5.7.25-20261021/baseline/repo_service.py.
Используется прежний state dir /workspace/repo/fortis-observatory-repo-v1,
loopback 18754, PID 1996. HTTP health повторно подтверждён, две сессии.
Ключи/пары/архив не сбрасывались, Docker/Tunnel не перезапускались;
кандидат 5.7.25 не установлен. Windows Viewer и открытие owner Edge
не подтверждены: G2 дважды вернул ошибку подключения 429.
По уточнению пользователя старое подключение «Туннель» больше не использовать.
Адрес установленного Windows Viewer: http://127.0.0.1:18755/.

## 21.10.2026 — этап E: backup через Fortis Repo

Пакет /workspace/repo/fortis-rollout-5.7.25-20261021 проверен по manifest:
baseline 20 файлов (Notifier 5.7.23, прежний Viewer/сервер из checkpoint),
candidate 21 файл (Notifier 5.7.25). Копия в Windows:
C:/Users/alexa/Workfiles/FortisBackups/Observatory-before-5.7.25-20261021
(Repo: /workspace/files/FortisBackups/Observatory-before-5.7.25-20261021).
После копирования SHA всех 41 файлов проверены повторно.

Это backup кода; установленный Viewer в AppData не подключён к Repo
и не скопирован. Архив, оригиналы, ключи, approvals и browser storage
не экспортировались. Установленная Windows-копия остаётся непроверенной.
Старый enrollment не принимает task_intents в grants; при будущем rollback
нельзя слепо заменять approvals старым файлом. Выданный PS скрипт не выполнен
из-за подписи; для созданной копии кода в Workfiles он не нужен.

Read-only live-проверка: .service.pid содержит 194, процесс /proc/194
отсутствует, порт 18754 не отвечает (URLError). Причина не установлена.
Создание backup не запускало/останавливало/перезапускало службы, Docker
или Tunnel, не устанавливало обновление, не меняло pairing и не делало Send.

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
См. [контракт A/B/C/D](../observatory/v1/TASK_INTENTS_V1.md).

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
Favicon следующий этап. См. [контракт A/B/C](../observatory/v1/TASK_INTENTS_V1.md).

## 21.10.2026 — этап B task metadata, исходники без установки

Notifier source 5.7.24 синхронизирует новые проверенно сохранённые intents,
восстанавливает metadata retry после offline/reload и передаёт отдельно
send_requested / send_unconfirmed / send_observed / send_not_attempted.
DOM observation не считается ChatGPT receipt. Только явный дополнительный
owner grant для одобренного Notifier даёт task_intent_key; старые привязки
автоматически не расширяются. Узкие Windows/Repo transport allowlists
поддерживают два metadata POST; user-original archive gate не менялся.
См. [контракт A/B](../observatory/v1/TASK_INTENTS_V1.md).
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
[Task intents V1](../observatory/v1/TASK_INTENTS_V1.md).
25 новых тестов PASS; полный observatory/v1 Python suite 136/136 PASS.
Рабочая служба НЕ перезапускалась, действующий архив/ключи НЕ трогались;
Notifier 5.7.23 и Windows Viewer/Dispatch не менялись. /api/state и текущие
archive/activity endpoints сохранили контракт. Send, Notifier sync, Viewer
export и цвета в этот этап не входят. Не устанавливать/перезапускать ради
этой source-only подготовки; следующих действий на Windows сейчас нет.

## 21.10.2026 — Notifier 5.7.23: file-only paragraph-aware native verification

User agreed to replace overly strict File rich-editor innerText comparison:
file bytes are already SHA-256 guarded before attach and the named
attachment card is verified locally, so native editor verification is
about the FULL Fortis task instruction block and filename, not the
server-side file contents. Previously the real file and full Fortis
context reached ChatGPT but native insertOnly returned
"Вставка не совпала с исходником посимвольно", leaving owner event
attachment_only/context_mismatch.

Notifier File now verifies full prepared text via fileContextTextMatches:
every non-empty line exactly equal in sequence; ONLY empty paragraph
lines, CRLF/LF and NBSP-as-space differ. Non-empty lines preserve
extra spaces, tabs, task_id, file reference, module instructions,
Chat IDs and any other text. Ordinary Insert / non-File queued actions
remain strict byte-for-byte (no option passed). Same file-only
comparison also validates locally stored prepared File draft and the
separate one-shot prepared Send. Existing file card/owner pairing/task
checks remain; nothing is re-attached or auto-Sent.
No claim of server-side attachment contents or delivery.

Notifier full test suite PASS: 229/229 Node and generated build check.
Built v5.7.23 SHA256:
5d6c24978effc46980dd699568c8607a51782ca1d28b5667322cc9e495674c83

Current Windows owner_viewer.py/owner_dispatch.py from 5.7.22 remain
UNCHANGED. Update only existing ONE Local Loader to 5.7.23. Docker
Repo/Viewer archive unchanged. Real Edge live check NOT_RUN; verify
a new unique prompt once with File and no Send.

## 21.10.2026 — Notifier 5.7.22: owner Textbox timeline prints FULL diagnostic

Repro: file uploaded, visible Fortis task context and task_id in real
ChatGPT message, but source Notifier reported "Вставка не совпала с
исходником посимвольно", sent owner only short context_mismatch.
Fixed: Notifier v5.7.22 carries the EXACT fixed user-visible Notifier
message in ACK.detail. Owner validates strict allowlisted status
templates; max 512 chars, only file dispatch mode and final events;
stores in existing bounded in-memory event log, never source text,
file content, arbitrary DOM, keys or untrusted exception messages.
Viewer renders full warning via textContent, not HTML. Read-only polling
unchanged. No action retries, no Send, no relaxing native byte equality.
Original historical event cannot be reconstructed; new details only.
Node 225 tests pass, owner full suite being finalized.
Source SHA Notifier: 537f61d23b584959e5c814ade1931e193ec642cece086d595b23daef8548416c
owner_viewer.py SHA: 2455109587431bf12705803200a953774c2e7f81e222aef74ecb5665f35daa54
owner_dispatch.py SHA: a00d22dfdf4cfc8902e85cfd7b101867dc9507fb99f9b4b5352ffe1d5a81a31f
Docker archive not touched; Edge live smoke NOT_RUN.
Install all three updated Windows components; existing one Local Loader
and protected Viewer installer only.


## 21.10.2026 — Notifier 5.7.21: exact real ChatGPT attachment button recognized

Owner provided real DOM for attached file:
<button class="composer-attachment-surface absolute inset-0 cursor-interaction rounded-2xl focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none focus-visible:ring-inset" type="button" aria-label="fortis-prompt-mvh0e4ol.txt"></button>
Root-cause match: previous fileAttachmentVisible selector required
data-testid attachment marker or aria-label starting Attachment, and so
ignored an otherwise valid card with filename-only aria-label.
Added strict selector button.composer-attachment-surface[type="button"][aria-label],
EXACT matching filename (not prefix), after rejecting busy/error state
and excluding contenteditable or unrelated nodes; existing scope limited
to composer plus immediate wrapper, not whole chat. No second upload,
auto-Send or fallback; File/SHA semantics unchanged. Also Notifier
now returns reason='duplicate' to Owner on a blocked consecutive SHA-256
before any upload attempt, rather than generic unknown failure.
New DOM regression test demonstrated RED against previous source,
GREEN after fix, plus negatives for wrong filename, generic button,
different button type, busy state and contenteditable; 223/223 Node
suite PASS, build:check PASS.
Built Notifier 5.7.21 SHA-256:
228c5ff21d99a3ad134376e45dce097fb4e47bd1b61578c6f3d8466b3d8e865f.
Owner Viewer/Dispatch, Windows installer, Docker archive UNCHANGED.
Real installed Edge 5.7.21 smoke NOT_RUN. User should check local Windows
copy SHA and ensure existing ONE Tampermonkey Local Loader loads this
path/version; then use unique safe text, once File, no Send or retry,
verify card and native Fortis task_id in editor / Owner event history.


## 21.10.2026 — Notifier 5.7.20 File upload partial status bug

User saw a real attached .txt but 7 sec after claimed Viewer logged
refused (unknown); next prepared Send rejected missing task_id.
Root cause: narrow attachment-card DOM detection, not proof of
upload failure. 5.7.20 improves title/aria-label descendants of
recognized cards and nearby composer wrappers (no global chat scan);
Notifier ACK now uses attachment_unconfirmed for an attempted upload
not confirmed in DOM, attachment_only for confirmed card but missing
task/context, file_attached only for both confirmed card and context.
Viewer log distinguishes all states and will never present uncertainty
as outright refusal. No retries/auto Send.
Source Node 220/220 PASS, server Python tests being finalized;
live Edge NOT_RUN. Owner guide has PINs.
New Viewer SHA256 f469d0a2fc8b6d1e1ba0b9f65a5788a6a7cd9bc612ec153b8bacad04801165ef, Dispatch SHA256 91bebdf2db8ccda356d42be64ef2cd6553cd4aa7ea8202020a3737ac01f4265a.
Notifier SHA256 fc63fb2a47cd91db6ff792530d6d10839368b0459b25be24590291ed123f2770.


## 21.10.2026 — Notifier 5.7.19 + owner prepared Send and event journal (source only)

Fixed owner File/Insert false success: profile-scoped ACK carries
persisted task_id only when native Fortis context is actually present.
An attached orphan .txt is NOT a prepared request; no retry/Send.
Added separate empty-text send_prepared one-shot owner action, gated by
same-chat saved exact composer draft, current authorized session, visible
attached filename (File) and task_id; rejects mismatches and duplicate
attempts; queued new-message Send remains a different action.
Viewer Textbox status journal is to the RIGHT of File/Insert/Send,
read-only polling every 5 sec; bounded 30 events in owner process memory,
safe stage/enum reason/time/task_id, no original content or secrets.
No Docker archive change, no Windows installation/Edge send yet.
Notifier built SHA256 f82bfaa8821e2c7f9b34eea39c701b962effa10d68fa1914f7a351ee3803937b.
Viewer PIN f1fb1d9ca12e0daf7f7945ce3cbb5b7a39851496793707e1a18c101734644a55; Dispatch PIN b5b70e4907452247accbdb5ff3a398e3fb20ce9d25ce587fb3096ec8e9d4efea.


## 20.10.2026 — Native Notifier profiles mirrored and selected in Observatory (5.7.18)

Notifier сохраняет профили (имена, ID, module IDs и behavior flags)
в своём GM store — без копирования в Observatory. Теперь scoped
Notifier /api/dispatch/modules включает минимальную метаинформацию
всех сохранённых профилей и active_profile_id. В Windows Viewer
есть профиль-селектор и module checkbox список исходного профиля.
По умолчанию следует active Notifier, вручную выбранное
сохраняется только локально Viewer для сессии.
Адресные команды File/Insert/Send содержат profile_id и
module_ids=null для полного локального native поведения,
либо список module IDs как one-shot override.
Notifier локально применяет и модули, и native behavioral options
ТОГО профиля, не меняя active GM profile. Идёт строгая
валидация профилей на 40 profiles, 100 IDs per profile, 512 KiB.
Нет нового listener, нет повторной отправки, не меняется Docker.

Source tests PASS, live Windows Edge manual smoke NOT_RUN.
Нужны и owner_viewer.py PIN f1fb1d9ca12e0daf7f7945ce3cbb5b7a39851496793707e1a18c101734644a55,
owner_dispatch.py PIN b5b70e4907452247accbdb5ff3a398e3fb20ce9d25ce587fb3096ec8e9d4efea, Notifier 5.7.18 и
корректный Tampermonkey Loader @require. Реальная установка
в Windows пока не выполнена этими инструментами.


## 20.10.2026 — Notifier completely disappeared: 5.7.16 startup ReferenceError repaired (5.7.17)

User local loader remains enabled, but all Notifier UI/menu features absent.
Diagnosed exact source crash: src/upload-button-ui.js createUploadButtonUi()
returned `dispatchQuickAction` from outer scope, while function was
only declared inside ensureUi(), causing ReferenceError before
startTabNotifier() could register any Tampermonkey menu commands.
Wrote regression test, verified FAIL with exact exception, corrected
outer stable wrapper + inner handler delegation; new Notifier 5.7.17
211/211 Node tests PASS, build:check PASS.
Built repository checksum SHA256:
ac9225a8d103f9f57090d0168b4d5842b26fd38ffa643c00e2c9dc8c78fdefbd.

Separate local loader config supplied by user has an outdated @require path
`C:/Users/alexa/tabnotifier-fileautosend-autochat/...` while expected
Windows repo checkout used in previous installation is
`C:/Users/alexa/Repos/tabnotifier-fileautosend-autochat/...`.
Loader lacks `@grant GM_listValues`, needed by newer Notifier archive.
Windows HOST access returned 429, so actual on-disk Windows path, updated
version 5.7.17 and real Edge smoke have NOT been confirmed. Advise owner
to verify Windows file exists/version/checksum, then update ONLY existing
Tampermonkey Local Loader (@require proper file, @grant GM_listValues,
@version 1.0.1 for cache refresh), without removing GM storage, and
refresh target ChatGPT tab. No Viewer/Docker archive changes and no Send.

## 20.10.2026 — Owner Viewer full-width Textbox + Notifier 5.7.16 (source only)

Viewer composer moved above four-column workspace, under but outside
sticky header, collapsible, with File/Insert/Send and searchable
ID/title-based Planning Helper module choices (separate per-session
in-memory; no GM profile mutation). Notifier dispatch uses the exact
local File/Insert/Send handlers and SHA-256 one-attempt guard,
task_id/Fortis context; owner dispatch backend accepts validated
file_attached ACK, module_ids and scoped metadata heartbeat.
Owner bearer, dispatch_key, Chat ID + live heartbeat and no
retries intact. Origin-only is not permission. No Docker service
or archive changes. Windows Viewer and one Notifier 5.7.16 require
manual install; source tests PASS, actual Edge live smoke NOT_RUN.

New owner_viewer.py pin: 056c7616642618129cd031f8cc14df0f487c165f68b1d991070c3cc31f98a716
New owner_dispatch.py pin: fffae760e975601d252aa72547ea659cc2cf0edcdc51519df39669acd24c4ebd


## 20.10.2026 — Windows Viewer collapsible session diagnostics + 5s archive polling (source only)

owner_viewer.py в Repo source обновлён без изменения API Docker:
«Подробности сессии» стали details/summary (закрыты при первом входе).
При входе/переключении сессии выбираются newest task по first_seen_at
и последняя по времени архивная запись; список записей скролл вниз.
Через 5 сек обновляются archive state, tasks, history и статус Notifier
(read-only), перекрывающиеся refresh пропускаются. Опциональный
чекбокс «Автоследование» по умолчанию OFF: при ON переключает
на новейший task/record и scroll bottom, OFF сохраняет ручной выбор.
Никакого Send, создания задач, потери archive state или новой
экспозиции Docker/Windows порта. Только source tests; Windows owner
Viewer ещё не переустановлен, live Edge smoke NOT_RUN.
PIN owner_viewer.py: dae7e32429e956f507b3fb038094266266e74f03873b605b88db8b6870614af1.


## 20.10.2026 — six PowerShell 5.1 parse errors in Owner Installer corrected

На Windows владелец получил ParserError ещё до исполнения установки:
шесть Get-FileHash -LiteralPath с недопустимым переносом строки.
В исходном Install-FortisObservatoryViewer.ps1 все исправлены на
однострочные expressions, регрессия 2/2 PASS.
SHA самого исправленного установщика:
47f194b647d7118328636128b9ed05b6c9c56286467d2ce7b9db8abfc661b61f.
Шесть ранее указанных SHA для копируемых Python/CMD/PS1 файлов НЕ изменены.
Установщик повторно в Windows НЕ запускался; требуются checksum и
Parser::ParseFile в Windows перед следующей попыткой.


## 20.10.2026 — Notifier 5.7.15 / URL-based owner-approved auto enrollment

В исходниках добавлен Windows Enrollment с однократным явным owner
approval per exact chat/claimant, хранением SHA-256 proof в owner ACL
файле, auto reconnect после перезапуска Viewer/Windows через новый
dispatch_key. Notifier хранит proof в Tampermonkey и проверяет
сервер каждые ~7 сек; URL сам не даёт прав.
Owner Viewer показывает обнаруженные заявки, approve/revoke
и текущий live heartbeat. Auto Windows logon через опциональный
HKCU Run, Docker wait до 15 мин, без контейнерного автозапуска.
Installer проверяет 6 SHA. Исходники/source tests only.
Никакой Windows install, реальный Edge/reboot или auto Send
инструментом не выполнялись, Docker archive остается прежним.


## 20.10.2026 — Notifier 5.7.14 single attachment-attempt hotfix

В owner Edge smoke пользователь сообщил два результата от
одного нажатия «Файл». Найдена source-level причина:
если native file input принял событие change, но карточка ChatGPT
задержалась, предыдущая версия пыталась второй route (плюс меню/
drag drop). Теперь только один upload event на клик; если
первая попытка дала неизвестный результат, нет повторной попытки.
Даже если обработчик file input бросил после event, следующий
input или drop не вызывается. SHA-256 dedup сохранён.
Модули/Context и no-auto-Send не менялись.
В установленном Edge/Tampermonkey версия не обновлена;
реальный smoke требуется. Docker Repo / Windows Viewer без изменений.


## 20.10.2026 — Notifier 5.7.13: file dedup by per-chat SHA-256 (source only)

Owner сообщил, что «Файл» блокирует прикрепление при занятом
native composer или уже выбранном файле. Из исходников удалены
эти два блокиратора. По Chat ID через приватное GM-хранилище
записывается последний SHA-256 оригинала; второй подряд тот же
hash не пытается прикрепляться, даже после reload; другой hash
разрешён. Неопределённая upload попытка оставляет защитный hash,
повторного действия автоматически нет.

Для каждого отличающегося файла оригинал в UTF-8 .txt,
модули Helper и Fortis task context добавляются без Send к
уже существующему native тексту (append-only + exact read-back,
никакого стирания). Несколько task_id сопоставляются с их
префиксами при последующем доверенном native ручном Send;
send_unconfirmed — НЕ подтверждение успешного сообщения и
НЕ архивный receipt. Режим ⇧ upload auto-send должен быть
отключён; источник и исторические изменения только source,
реальный Edge smoke ещё требуется. Windows Viewer/Docker без
перезапуска и Windows установка не изменялись.


## 20.10.2026 — Notifier 5.7.12 draft-with-modules, source only

Кнопки «Вставить» и «Файл» теперь готовят выбранные модули
Planning Helper и Fortis task context с локальным task_id через
отдельную prepareDraft API, не используя saveAndSend/sendNow/native Send.
«Файл» прикрепляет полный оригинал .txt, native ChatGPT получает
только краткую инструкцию о файле, модули и task context.
При 12000+ символах «Вставить» переходит к файловому маршруту
после подтверждённого Edge freeze. При ручном native Send только
по точному совпадению черновика и (для файла) карточке вложения
с no-busy ставится send_unconfirmed; это НЕ подтверждение приёма
ChatGPT и НЕ archive receipt. После редактирования native
черновика автопривязка task_id может не сработать — нужен Edge smoke.
Не развёрнуто в Windows/Edge; только исходники и тесты.


## 20.10.2026 — Edge insert-only failure / Notifier 5.7.11, source only

При пошаговом Edge smoke пользователь подтвердил Viewer и версию
Notifier 5.7.10, но «Вставить» отклонила короткий промпт
без переноса в native ChatGPT. Причина в source: initial
insertOnly сравнивал пустую строку с rich-editor structural
placeholder newline. Notifier 5.7.11 меняет ТОЛЬКО предварительную
проверку пустого поля; после первого символа — strict exact
read-back, no Send и исходник сохранён. Нужно вручную обновить
установленный Tampermonkey и повторить шаг 3. Реальный Edge
положительный результат не получен. Repo Observatory running
с прежним архивом, Windows Viewer не перезапускался.


## 20.10.2026 — controlled Repo Observatory restart COMPLETED; Edge/Windows pending

После source-fix F-P-03/04/05/06 выполнен контролируемый restart
ТОЛЬКО Python Repo HTTP Observatory на loopback 127.0.0.1:18754.
Команда repo_service.py stop проверила identity старого PID, новый
сервер запущен из /workspace/repos/tunnel/observatory/v1/repo_service.py
через setsid/nohup в прежнем контейнере, с ТЕМ ЖЕ приватным
state-dir /workspace/repo/fortis-observatory-repo-v1. Docker-контейнер,
архив, pairing Windows и существующие ключи не сбрасывались.
После restart read-back подтвердил те же 2 session IDs и
events_count каждой: 42 события суммарно, ingest available.
GET /api/state без bearer — HTTP 401, с owner Repo bearer работает.
Один первоначальный локальный compare аварийно завершился
из-за различия типов json list vs Python tuple, не из-за утраты
данных; скорректированный поэлементный compare PASS.

Обновление Windows Viewer / owner_dispatch и Tampermonkey 5.7.10
в Edge НЕ выполнялось: Installer/ACL/практическая загрузка файла,
native Send и cross-chat task_id read-back ещё требуют владельца
Windows и реального Edge smoke. Проверка одних исходников, синтетических
тестов и живого Repo HTTP не подтверждает end-to-end взаимодействие.
Нельзя выдавать staging / send_initiated за принятый archive receipt.


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


## 20.10.2026 — адресная отправка из Owner Viewer и Notifier 5.7.9, SOURCE ONLY

Можно отдельно отозвать dispatch permission через owner-authenticated
/api/dispatch/revoke; новые команды старый ключ не примет.
Ранее выданное действие может продолжить работу, поэтому это
не принудительная отмена уже инициированного Send.

Добавлены: owner_dispatch.py (памятный одноразовый канал, отдельный
per-session dispatch_key, TTL, at-most-once claim), owner_viewer.py
(скрытый по умолчанию session composer, локальный owner bearer + same-origin
для POST, отдельная scoped polling/ack API для Notifier), новый
Notifier observatory-dispatch.js (проверка Chat ID/pair, очереди,
native composer и профильных модулей). Отправку выполняет только
Notifier с новым task_id через существующий persistentMessageController.
«Вставить» не создаёт task_id/не вызывает Send. Ключи observer/writer
не дают права на dispatch. Преднамеренно не реализована offline
очередь и не производится автоматическая повторная отправка.
По ack send_initiated известна лишь локальная постановка в штатную
очередь, не доказаны приём ChatGPT и archive receipt.

Новый модуль нужно установить на Windows вместе с Viewer и bridge
через обновлённый manual installer с тремя SHA; повторно привязать
каждый чат после установки Viewer (ephemeral dispatch ключ меняется
после рестарта viewer). Результаты unit+HTTP mock доказательств
НЕ равны Edge/Windows smoke. Установка, Git commit/push и
перезапуск Docker/Windows не выполнялись. Подробные события остаются
source-only до штатного обновления Repo archive службы.
Актуальные PIN в observatory/v1/OWNER_VIEWER_MANUAL_SETUP.md.


## 20.10.2026 — подробные events и insert-only Notifier, source-only

В observatory/v1 Store новый optional event-detail направляется
через repo_task.py event --detail-stdin, staging event JSON внутри невидимого старому importer
inbox/repo/.event_bundle и отдельного sidecar по event_id
в .event_details; archive Markdown JSON detail, read-back и on-demand history
selected task. В /api/state остаётся только has_detail. Краткий
summary ≤140 и разные AI interim/final сохранены. Старый live
server не применял эту схему; новые bundle-события останутся
в очереди до запуска нового Store, чтобы не потерять detail.
Это не acceptance receipt. В Notifier 5.7.8 добавлена кнопка «Вставить»
без Send/task/queue, с порционной передачей и сохранением исходника,
а ручная отправка после такой вставки пока не гарантирует
автоархивацию task_id. Тесты в исходниках; Edge smoke отсутствует.
Удалённая отправка из Observatory и её права не реализованы.


## 20.10.2026 — сквозная поддержка длинных промптов (source only)

После уточнения пользователя снято искусственное блокирование >64 КиБ.
Notifier 5.7.5 (Repo source) удерживает большую вставку полностью
в памяти, по кнопке ↗ раскрывает весь текст в редактируемом поле,
по ➤ порционно (4096 UTF-16 единиц с yield) переносит в штатный
редактор ChatGPT, сохраняет task_id/оригинал до Send; при изменении
редактора отменяет автоотправку. Лимит оригинала Notifier, узкого
Windows Viewer/Relay и Repo Docker archive согласован до 512 КиБ
UTF-8 с байтовыми guards и точным read-back. Тестирование в
синтетических браузерных/HTTP сценариях, реальные Edge/Windows
инсталляции и Docker рестарт НЕ выполнялись. До controlled
deployment live archive остаётся на старых лимитах.


## 20.10.2026 — Notifier 5.7.4 защита от больших вставок (source only)

В совместном Repo source tabnotifier-fileautosend-autochat устранены
лишние синхронные чтения GM истории при закрытой панели +.
В правом Textbox большие вставки от 12k символов перехватываются в
память с коротким preview без гигантского DOM textarea; добавлены
явные Copy Full и Clear, отправка проверяет 64-КиБ лимит текущего
передатчика exact-original. Сами оригиналы при ручной отправке идут
через прежний persistentMessageController/task_id. Состояние в Edge
пока не проверено, настоящая причина зависания без профилирования
не доказана. Никакие Windows установки, перезапуски, архивы
или Git-коммиты не менялись.


## 20.10.2026 — Owner Viewer: четыре регулируемые колонки (source only)

По предоставленному владельцем скриншоту подтверждён показ предыдущего
компактного Viewer. В Repo source обновлён observatory/v1/owner_viewer.py:
закреплённая верхняя панель, четыре колонки «Сессии», «Задачи»,
«Записи», «Подробности». Три разделителя регулируют ширину мышью и
клавиатурой, двойной щелчок сбрасывает пропорции. Записи различают
точный оригинал, краткое событие и полный AI interim/final по цвету;
подробности раскрываются по клику. Для события краткая метаинформация
сопоставляется с уже доступным авторизованным состоянием сессии,
без изменения сервера. Отсутствующий оригинал помечается явно.
Новые браузерные взаимодействия синтетически протестированы, Windows
установку и реальное отображение обновлённого UI не подтверждали.
Инструкция и новые SHA в observatory/v1/OWNER_VIEWER_MANUAL_SETUP.md;
Docker/Windows службы и Git публикация без изменений.


## 19.10.2026 — Owner Viewer: главный экран сессий и задач (source only)

Изменён только HTML/CSS/JS в observatory/v1/owner_viewer.py: верхняя
компактная панель «Обновить», «Добавить сессию», «Инструкция»,
«Привязка Notifier»; регистрация, инструкция и pairing скрыты до
нажатия соответствующих кнопок. Основной экран теперь имеет три
колонки: сессии, задачи, история; первую доступную сессию и задачу
Viewer открывает автоматически, ручной выбор сохраняется при refresh.
Pairing-код очищается при смене сессии. Эндпоинты, транспорт,
Docker архив и owner security boundary не менялись. Источник требует
ручной повторной установки защищённого Windows Viewer с новым SHA
по observatory/v1/OWNER_VIEWER_MANUAL_SETUP.md. Owner Edge UI и
установленная Windows-копия пока не проверены. Без рестартов.


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



**19.10.2026 — актуальное уточнение:** Fortis Repo — основной AI
tool/send-channel. Event metadata и полные ответы AI проходят прямо
через sender CLI в Repo Docker volume, без G2/Windows/owner relay.
Прежний Windows narrow relay source-only и не блокирует этот путь.
Оригинал пользователя от browser Notifier — отдельная ещё не
интегрированная задача. См. `docs/INSTRUCTIONS.md`.

**19.10.2026 / Observatory source-only:** Repo Docker unified archive работает внутри контейнера 127.0.0.1:18754. Узкий Windows↔Docker браузерный relay подготовлен и протестирован только в синтетических source-тестах, **не установлен** в Windows, owner/guest security и Edge/Tampermonkey end-to-end не проверены. См. `observatory/v1/BROWSER_RELAY_OWNER_INSTALL.md` и `docs/INSTRUCTIONS.md`. Не считать новой production установкой.

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
