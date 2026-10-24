# Owner Windows / Edge — Fortis 5.7.10 controlled acceptance

## 21.10.2026 — file status recognition regression (5.7.20)

NOT RUN in real Windows Edge. Update Windows Owner Viewer/Dispatch
with current six PIN SHA; update the already active Local Loader
to point to built Notifier 5.7.20. Do not make another active userscript.

1. Inspect current ChatGPT native composer, note any already-attached
   file from previous refused attempt; do NOT retry that text.
2. Use a DIFFERENT short unique safe text once in Owner «Файл».
   Do not click either «Отправить» or «Нажать Send».
3. If a file card appears, check native editor for Fortis task_id
   and context. Full «Файл и контекст подготовлены» only after both.
4. If «Файл: одна попытка; карточка не распознана», file may still
   be attached; DON'T RETRY. Collect card HTML/DOM for matching.
5. If «Карточка обнаружена, контекст не подготовлен», refrain from
   Send; the file is an orphan. Confirm latest event reason.
6. In right-hand owner event log, statuses must NOT falsely label
   an unconfirmed attachment as outright refusal. No new task
   or archive receipt is expected without manual Send.


## 21.10.2026 — prepared Send + native task_id + Viewer event stream

REAL EDGE WINDOWS NOT_RUN until owner upgrades both current Viewer
(PIN SHA in OWNER_VIEWER_MANUAL_SETUP.md) and Notifier 5.7.19.

1. Verify live Notifier heartbeat; `Файл` with NEW unique text, no Send.
2. Verify single named attachment and native composer Fortis block with
   matching task_id; Viewer status `file_attached` must show that task ID.
   If `refused` or `unconfirmed`, do NOT retry File: attachment may remain
   although context/task_id failed. Preserve screenshot for diagnosis.
3. Verify event timeline to RIGHT of buttons shows queued, claimed,
   success/refusal as distinct rows with time/task_id, not only one
   overwritten status line. Check 5 sec refresh without any Send.
4. Do not click original «Отправить» when already prepared File exists;
   it creates a NEW message. Only «Нажать Send» may use existing draft.
5. If explicit owner approval for live Send: first test refusal cases
   (missing file card/changed editor/no task ID): must NOT click Send.
   Then test one prepared safe draft using «Нажать Send» ONCE, check
   ChatGPT receipt separately. `send_initiated` alone is NOT receipt.
6. Confirm Fortis archive original/task_id and AI response independently.


## Проверка реальных профилей Notifier в Viewer (5.7.18)

NOT_RUN до Windows owner PIN-установки актуальных 6 SHA
и загрузки версии Notifier 5.7.18 в целевой Edge вкладке.

1. Проверь одну активную копию Notifier, его плавающий Textbox,
   одну открытую привязанную сессию и heartbeat ПОДКЛЮЧЁН.
2. Создай в Notifier два разных профиля: с разным набором
   текстовых модулей и (если нужно) разными поведенческими опциями.
   Не передавай содержимое модулей и ключи в Viewer.
3. В раскрывшемся текстбоксе Viewer через 5–15 сек должен
   появиться список имен ТЕХ ЖЕ профилей. Выбран активный
   в Notifier профиль, пока пользователь не выбирал другой в Viewer.
4. Выбери второй профиль в Viewer: галочки должны точно совпасть с
   модулями выбранного профиля. В Notifier активный GM профиль
   не меняется (это только выбор для адресной команды).
5. Нажми «Вставить» с небольшим уникальным безопасным текстом.
   Проверь в ChatGPT черновик: context/task_id + МОДУЛИ ВТОРОГО
   профиля; никакого Send. При занятости редактора — отказ
   без потери чужого черновика, повтор автоматически НЕ делать.
6. «Файл» проверять другим уникальным исходником; ровно одна
   .txt попытка, task context от того же выбранного профиля.
7. «Отправить» тестировать только после отдельного решения
   владельца и очищенного штатного редактора; queue ACK
   не является доказательством ChatGPT receipt.
8. Измени активный профиль в Notifier. Пока в Viewer не было
   собственного явного выбора, он должен отразить изменение
   при следующем polling; после ручного выбора он сохраняет
   этот выбор для своей сессии.


## Viewer Textbox + Notifier 5.7.16 — File, Insert, Send, module choice

REAL EDGE/WINDOWS NOT_RUN. Reinstall owner-protected Viewer with
new Viewer + Dispatch SHA (other four unchanged); update precisely
one Tampermonkey userscript to 5.7.16 and refresh target ChatGPT tab.

1. After owner login confirm URL matches selected session and status
   Notifier connected. No test action before verified heartbeat.
2. In Viewer click «✎ Текстбокс выбранной сессии ▾»:
   panel opens above four columns, but not inside sticky header.
   Close/open preserves unsent text; switch sessions gives independent
   unsent drafts, and settings are in-memory only.
3. Click «⚙ Модули». Within ~12 sec actual titles/IDs from
   Notifier catalog should appear. Search and select checkboxes;
   never show module contents/keys in Viewer. Verify that
   Tampermonkey active profile was NOT overwritten.
4. Enter a short unique text. Click «Вставить». Inspect ChatGPT:
   native draft contains original + selected modules + Fortis context
   with current task_id; no Send was clicked.
5. Enter a DIFFERENT unique text. Click «Файл». Exactly one
   .txt card should be attached, native draft retains any existing
   text plus Fortis context, no Send. On same-text repeated File
   action SHA-256 prevents duplicate, including after page reload.
6. Check new owner status: file_attached means prepared,
   not a sent message. On ambiguous upload outcome don't
   retry automatically. Ensure no unknown duplicate.
7. Only with user permission click «Отправить» on safe content,
   verify send_initiated then independently check ChatGPT Send and
   accepted Repo task/event/receipt. Never assert receipt from ACK.
8. Verify a long «Вставить» (>=12000 chars) routes to File
   preparation and never pastes huge editor text.
9. Disable target tab: no dispatch action to closed tab; old
   paired scope, one in-flight command, and guest denial unchanged.


## Viewer: ручной smoke latest-record, polling 5s, auto-follow checkbox

NOT_RUN до обновления единственной Windows Viewer копии по новым
PIN SHA из OWNER_VIEWER_MANUAL_SETUP.md.

1. Открой http://127.0.0.1:18755/ и введи временный owner code
   только в Viewer. «Подробности сессии» по умолчанию закрыты;
   раскрой и проверь URL/Notifier, затем сверни. Никаких Send.
2. При первом открытии каждой сессии должна быть выбрана
   ПОСЛЕДНЯЯ по first_seen_at задача, выбрана её последняя
   хронологическая запись, третья колонка прокручена к низу.
3. Чекбокс «Автоследование» изначально выключен.
   Выбери старый таск и событие, прокрути детали; подожди
   10+ секунд и нажми «Обновить». Выбор и scroll сохраняются.
   Новый task/record может появиться в списке, но фокус не
   перескакивает.
4. Включи «Автоследование». Следующий опрос в течение ~5 сек
   покажет новую задачу/новейшую запись и прокрутит список
   записей в самый низ; при включении тоже обновляет сразу.
5. Во время уже идущей задачи прими ещё событие, дождись
   следующего 5-сек polling: запись должна стать видна внизу,
   справа — её деталь; старые данные не исчезают.
6. Снова сними галочку. Переключи сессию: вручную открытая
   сессия всё равно раскрывает последний таск и последнюю
   запись по умолчанию.
7. При краткой потере доступа к Repo Viewer не должен стирать
   выбранную задачу. Архив не меняется от браузерного polling.


## Новая автоматическая привязка 5.7.15 / reboot owner smoke

NOT_RUN. После ручной установки шести PIN SHA и обновления ОДНОГО
Notifier до 5.7.15 открой зарегистрированный ChatGPT URL в Edge.
Без доступа к настройкам Tampermonkey в Viewer дождись заявки,
убедись в совпадении Chat ID и нажми «Одобрить найденный Notifier».
Без отправки сообщения дождись статуса «ПОДКЛЮЧЁН».
Закрой вкладку -> через 15+ секунд статус пропадает.
Открой заново -> pairing восстанавливается автоматически.
Затем (сохранить пользовательскую работу!) перезагрузить Windows,
войти владельцем, проверить готовность Docker Desktop и
existing fortis-repo-test контейнера. Viewer с opt-in HKCU autorun
должен стартовать; Notifier после открытия URL должен восстановить
pairing без Tampermonkey menu. Дополнительные Send и новые задачи
тестировать ОТДЕЛЬНО. Отзыв owner auto-grant не заменяет
ротацию observer/writer keys Repo.


## Owner Viewer: URL сессии и живой Notifier heartbeat (новый)

NOT_RUN в настоящем Windows Edge, пока Viewer не переустановлен.

1. Войдите в Owner Viewer после защищённой установки актуальных
   трёх SHA из OWNER_VIEWER_MANUAL_SETUP.md. Выберите «прод обс»,
   затем «обс»: URL каждой сессии, Chat ID и reporting_session_id
   должны соответствовать выбранной карточке, ссылку можно открыть.
2. Нажмите «Проверить связь Notifier». «Код ещё не создавался»
   означает только память текущего процесса Viewer.
3. Откройте РОВНО ту зарегистрированную беседу ChatGPT в Edge,
   с активным userscript 5.7.14. В Viewer для этой сессии вручную
   создайте и скопируйте код; вставьте ТОЛЬКО в меню Tampermonkey
   «Fortis: привязать текущий чат». Код НЕ вставлять в сообщение.
4. Не нажимайте Send. Через 3–10 сек нажмите «Проверить связь».
   Должно появиться «ПОДКЛЮЧЁН» со временем последнего
   авторизованного запроса меньше 15 секунд.
5. Закройте вкладку либо временно отключите Notifier и подождите
   более 15 сек; ожидается «ранее отвечал, но сейчас НЕТ СВЯЗИ».
   Не путать это с отказом работы Repo.
6. Выберите другую сессию. Её URL и статус должны быть
   независимыми; никакого автоматического переноса pairing нет.
7. Признак «ПОДКЛЮЧЁН» подтверждает только живой канал
   Notifier↔Viewer. Новые задачи/архив проверять позднее
   отдельным безопасным ручным Send и event acceptance.


## Notifier 5.7.14 — регрессия: одно нажатие «Файл»

В установленном Edge обновить один существующий userscript
до 5.7.14. Переключатель ⇧ автоотправки выключен.
Использовать НОВЫЙ короткий тестовый текст в том же чате
(при сохранённом last SHA прежний точно идентичный блокируется).
Одно нажатие «Файл» — один новый .txt или явное UNKNOWN.
Если первая карточка не была вовремя обнаружена, альтернативных
попыток быть не должно. Если появился второй файл/сообщение,
FAIL: не отправлять повторно и уточнить, дублируются ли
карточки вложений либо непосредственно сообщения чата.
Native composer и модули не очищать автоматически, Send
только по отдельному решению владельца. NOT_RUN до owner smoke.


## Дополнение Notifier 5.7.13 — file SHA-256 и занятый native composer

Проводится только владельцем в Edge после ручного обновления
РОВНО одного существующего Tampermonkey скрипта до 5.7.13.
Все тесты ниже **без Send**; переключатель ⇧ upload-auto-send ВЫКЛЮЧЕН.

1. В Fortis Textbox ввести «Тест A  B 🌍». Native composer
   предварительно заполнить другим безопасным текстом.
   Нажать «Файл». Ожидается НОВАЯ карточка .txt; native текст
   сохранён и дополнен новой короткой инструкцией про этот файл,
   активными модулями Planning Helper и Fortis task context.
2. Не очищать ChatGPT composer и не убирать карточку. Нажать
   «Файл» снова с тем же точным оригиналом. Ожидается явный
   отказ о совпадении SHA-256; второго файла/другого task_id нет.
3. Изменить один символ оригинала в Fortis Textbox. Нажать
   «Файл» снова. Ожидается вторая НОВАЯ карточка и второй
   добавленный Fortis task context, старый native текст без
   изменений. Send не происходит.
4. Обновить страницу Edge (сначала сохрани отдельно нужный
   черновик, поскольку reload может сбросить DOM вложения).
   Повторная попытка с последним идентичным содержимым должна
   блокироваться по сохранённому per-chat SHA.
5. В другой отдельной ChatGPT беседе тот же SHA не блокируется
   глобально; ограничение применяется отдельно по Chat ID.
6. При ошибке rich-editor exact read-back файл может
   оказаться прикреплённым, но context не принят. Это FAIL:
   не нажимать Send, сохранить отзыв без секретов.

Источник не содержит доказательства, что actual Edge проработал
все эти шаги; до результатов владелец отмечает их NOT_RUN.


## Новый smoke Notifier 5.7.12 — активные модули, БЕЗ Send

В этой версии режимы «Вставить» и «Файл» формируют черновик
с Fortis task context и текстами выбранных Planning Helper модулей,
сохраняют точный оригинал и новый task_id локально, но
НЕ выполняют Send. Ниже приведены действия без внешней отправки.
Это лишь критерии будущей реальной проверки, НЕ уже выполненные тесты.

1. Обновить ровно существующий Tampermonkey скрипт до 5.7.12.
   Не создавать второго Notifier. Сверить активный профиль модулей.
2. В пустом native ChatGPT composer через Fortis Textbox ввести
   короткий тест с пробелами, пустыми строками и 🌍.
   «Вставить» должен дать native draft: ТОЧНЫЙ оригинал,
   Fortis task context с ОДНИМ новым task_id и выбранные модули.
   Никакой отправки, AI-ответа или archive receipt не должно быть.
3. Очистить native composer; подготовить безопасный тест >=12000
   символов, затем нажать «Вставить». Он должен идти в файловый
   маршрут, не вставляя огромный оригинал в React composer.
4. При успешной загрузке: отдельная карточка .txt (точный текст
   внутри) и короткая инструкция в native composer с task context
   того же нового task_id и активными модулями, без native Send.
   Сравнить нет ли загрузки/error. Если модулей слишком много для
   безопасной вставки — явный отказ; исходник в Fortis Textbox.
5. Проверить отказ при уже занятом native поле: файл НЕ добавлен
   и чужой текст не заменён. При переключении беседы — операция
   прерывается. Проверить отсутствие программного Send.
6. Ручной native Send тестировать ОТДЕЛЬНО, только после согласия
   владельца и на безопасном коротком запросе; без изменения
   подготовленного native текста. Не считать send_unconfirmed
   доказательством успешной отправки или приёма в архив.

После этого актуальный исходный smoke ниже остаётся историческим
планом; если встретится шаг о Notifier 5.7.10, использовать 5.7.12.


**Срез:** 20.10.2026. **Назначение:** проверка после реальной ручной установки. Не является подтверждением Edge-теста.

## Что подтверждено без Windows GUI

- Repo Observatory loopback HTTP перезапущен на новых исходниках.
- Два прежних session ID и количество событий каждой совпали: 2 сессии, 42 события.
- /api/state без bearer вернул HTTP 401; состояние ingest available.
- Последние задачи двух сессий открываются через Repo history, но точный оригинал последней задачи подтверждён только в одной сессии; нельзя реконструировать отсутствующий оригинал из AI.
- Source тесты Observatory 86/86, Notifier 5.7.10 176/176, synthetic Viewer PASS. Не заменяют real Edge smoke.

## A — Windows Viewer (только владелец Windows)

1. Под предусмотренной Windows-учётной записью alexa закрыть старый Start-FortisObservatory.cmd. Не выключать Docker.
2. Выполнить в обычном PowerShell ручной установщик с тремя exact SHA по OWNER_VIEWER_MANUAL_SETUP.md.
3. Должны быть видны все признаки: INSTALL_SOURCE_VERIFIED=True, INSTALL_OWNER_ACL_CHECKED=True, INSTALL_DOCKER_VOLUME_FOUND=True, MANUAL_START_READY=True. Если отсутствует любой признак — FAIL.
4. Запустить owner-protected Start-FortisObservatory.cmd, открыть http://127.0.0.1:18755/ в Edge.
5. Ввести viewer code только в Edge, не публиковать его в чате.
6. Проверить четыре колонки, историю и кнопку «Написать в выбранную сессию».

## B — ровно один Tampermonkey Notifier

1. Обновить существующий userscript из C:\Users\alexa\Repos\tabnotifier-fileautosend-autochat\chatgpt-tab-notifier.user.js. Версия 5.7.10.
2. Убедиться, что не включена дублирующая копия Notifier; обновить вкладку ChatGPT.
3. Для каждого разрешённого чата в Viewer: выбрать нужную сессию, открыть «Привязка Notifier», создать код. Вставить код ТОЛЬКО через команду меню Tampermonkey «Fortis: привязать текущий чат». Никогда не вставлять pairing/dispatch key в ChatGPT.
4. Проверить различие «вкладка подключена» и «недоступна»; отсутствующая вкладка не должна получать remote-команду.

## C — безопасные локальные действия без Send

1. В чистом Fortis Textbox вставить короткий пробный текст с ДВУМЯ пробелами, ДВУМЯ пустыми строками и Unicode 🌍. Нажать «Вставить», НЕ стрелку ➤.
2. Сверить точность пробелов/пустых строк и отсутствие Send. Если ChatGPT преобразовал содержимое, Notifier должен выдать отказ — это правильный fail-closed.
3. Очистить штатный composer вручную. Не затрагивать существующий чужой черновик.
4. В локальном PowerShell сгенерировать тест 68k+ символов без реальных данных:
    $nl = [Environment]::NewLine
    $sample = ("Проверка  🌍  A  B" + $nl + $nl + "Следующая строка 📝" + $nl) * 3000
    Set-Clipboard -Value $sample
   Вставить в Fortis Textbox и нажать «Вставить». Критерий: без зависания/обрыва, либо явный отказ с полным исходником в Fortis Textbox.
5. Нажать «Файл» с тем же безопасным образцом. Успех — отдельная карточка TXT с совпадающим именем, без busy/error. Голое input.files или имя TXT в тексте сообщения не считается успехом.
6. Не нажимать Send на этом этапе.

## D — адресность из Viewer, только вставка

1. Привязать две открытые беседы к двум разным зарегистрированным сессиям (если доступны).
2. В Viewer выбрать сессию A, набрать «Тест адресности A 🌐» и нажать «Вставить без Send».
3. Текст должен попасть ТОЛЬКО в native composer A, без Send и без воздействия на B. Очистить composer A вручную.
4. Повторить для B с другим безопасным текстом. Проверить отказ, когда вкладка закрыта или native composer заполнен.
5. Проверить «Отозвать право адресной отправки» и недействительность прежнего права после revoke. Отзыв не может отменить действие, уже выданное вкладке.

## E — реальный Send, только с явным подтверждением владельца

После успешных A–D, только с безопасным коротким сообщением:
1. Проверить точного адресата и осознанно нажать «Отправить в выбранный чат» либо ➤.
2. Убедиться в одном фактическом Send и новом task_id, отсутствии повторов.
3. Дождаться accepted activity и точного per-task read-back оригинала в Repo archive: правильный Chat ID, исходный текст, архивный receipt. STAGED_ONLY и send_initiated не равны receipt.
4. При unconfirmed **не делать автоматического повтора**: сначала проверить реальный чат и архив.

## Итог

Для каждого шага записывать PASS / FAIL / NOT_RUN. При ошибках передавать только обезличенное сообщение или скриншот без viewer code, pairing keys, dispatch keys, внутренних оригиналов и токенов. Пока A–E не завершены, end-to-end нельзя объявлять подтверждённым.
