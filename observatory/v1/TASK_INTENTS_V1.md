# Task intents V1 — этап A, 21.10.2026

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

Пределы доказательств: `task_overview` — вычисленная на момент чтения
сводка принятых событий и metadata. Это не подтверждение доставки ChatGPT.
Observer key получает только агрегированное чтение своей сессии; owner
чтение intents и POST metadata по-прежнему требуют своих отдельных прав.
Ошибка одного snapshot возвращает available:false, сохраняя legacy status.
incomplete сводка остаётся явно помеченной, как в Viewer.

Приоритет сводки общий: working, unknown, silent, waiting_ai,
activity_observed, blocked, prepared, failed, completed. Черновик не получает
зелёный цвет исторически завершённых задач. После просмотра зелёный reported
completed остаётся зелёным; сбрасывается только отдельная unread-точка.

## Этап C — 21.10.2026, owner export и цвета (source-only)

Owner Viewer /api/state получает поле task_overview от repo_viewer_export,
owner /api/tasks объединяет intents с историей по task_id. Экспорт читает
метаданные напрямую в том же Repo archive: Store.__init__, выдача ключей,
новые HTTP grants и мутации не вызываются. Прежний Docker /api/state
остаётся совместимым; source export способен работать с его прежним ответом.
Никакая живая служба для этого этапа не перезапускалась.

Карточка pending task имеет ID, серверное время регистрации, состояние,
status_label/status_color, send_label и время свежести. До принятого
архива original_preview=null и original_received=false; текст из AI или
summary вместо оригинала не подставляется. Серверное время регистрации
используется для first_seen_at, клиентские часы не определяют liveness.

Общий классификатор task_display/session_overview находится в task_intents.py.
activity_observed жёлтый: сигнал был, начала AI work нет. working синий;
silent/unknown фиолетовые; completed зелёный и failed красный с подписью
«сообщено AI». prepared и blocked без цвета, с явными подписями.
Неизвестное входное состояние не получает выдуманный статус/цвет.
Все badge и preview рендерятся через textContent; цвет — только allowlist
из пяти имён, произвольные CSS/HTML не принимаются.

Основное состояние сессии: working, затем unknown/silent, waiting_ai/
activity_observed, blocked, prepared, failed, completed. При этом независимые
счётчики показывают работу, ожидание, тишину, черновики, блокировки,
ошибки и завершения. Historic terminal не скрывает открытые задачи.
Черновик с прежним completed не получает зелёную основную маркировку.
Legacy session.state сохранён в API и доступен в tooltip диагностики.

Предел task list 2256 карточек; при ограничении truncated=true и явная
пометка. Повреждение metadata даёт task_status_available=false и notice;
прежние читаемые архивные карточки сохраняются. Сводка сообщает incomplete
при invalid/truncated events. Отсутствующий archive не создаётся чтением.
Карточки только из assistant archive без рабочих событий остаются без
подтверждённого состояния; ответ AI не превращается в completed.

При сетевой ошибке сохраняются выбор/строки/scroll, появляется пометка
«данные устарели», действующая цветная маркировка снимается. Тот же подход
при возрасте snapshot более 20 секунд или недостоверном времени. Даже
если HTTP-чтение зависло, существующий 5-секундный таймер обновляет
только отображение давности, без параллельного нового запроса. Это не
failed и не подтверждение продолжающейся работы. Следующее успешное чтение
восстанавливает актуальное отображение. Поллинг не отправляет команды.

Проверки: новые unit/export cases и synthetic DOM: подготовленная задача
до AI, отсутствие side effects/утечек, одновременные work+pending+draft+
failed+blocked, marker != started, отсутствие серого, safe DOM, stale read,
сохранение выбора и отсутствие dispatch. Полный Python результат в CURRENT_STATE.
Notifier/favicons и Windows installed copies в этапе C не менялись.

Ниже — датированная история A/B; ограничения UI из прежних этапов
перекрываются описанным здесь source-only этапом C.

## 21.10.2026 — этап B: метаданные Notifier и наблюдения Send (source-only)

Подготовлен Notifier **5.7.24**. В Edge пока остаётся рабочая 5.7.23;
новые исходники не устанавливались, службы не перезапускались.
Полные оригиналы и прежний механизм принятой activity/archive не менялись.

### Новый контракт

- POST /api/task-send-state под тем же отдельным task_intent_key.
- Строгий payload: version=1, reporting_session_id, conversation_id, task_id,
  revision (целое 1..1000000), phase, observed_at_client_ms.
- phase: send_requested (сохранено перед попыткой нажатия), send_unconfirmed
  (попытка/действие пользователя наблюдалось; доставка неизвестна),
  send_observed (признак DOM: генерация или очищенный composer),
  send_not_attempted (прежний отказ до нажатия).
- send_observed НЕ является ChatGPT/server receipt. send_confirmed запрещён.
- Сначала должна существовать принятая intent registration. Send metadata
  не создаёт work event, не устанавливает activity.found и не разрешает original archive.
- Последнее состояние хранится отдельно: task_send_state/task_<id>.md;
  atomic write/readback, один файл на intent. Большая revision обновляет,
  точный retry идемпотентен, меньшая revision получает stale без отката.
  Конфликт одинаковой revision отвергается. Это снимок состояния, не полный
  журнал всех попыток; offline-клиент может передать сразу последнюю фазу.
- Поздний Send metadata не открывает completed/failed заново. Ожидание
  отображается как waiting_ai с явным send_phase; после 15 минут серверного
  ожидания waiting_overdue=true, но не failed. Work silence использует
  прежние серверные timestamps. send_not_attempted остаётся prepared.

### Notifier: локальная очередь метаданных

Новые записи помечаются intent_version=1; после успешного readback оригинала
и индекса устанавливается intent_ready. Частичный остаток неудачного save
не регистрируется. Старые записи 5.7.23 не мигрируют и не переотправляются.
Метаданные уходят неблокирующе после сохранения, затем по существующему
ритму polling; минимум 3.5 сек между запросами, timeout 4 сек, backoff
до 60 сек при ошибке. GM запись и локальные ACK обеспечивают retry после
reload/offline. Потерянный HTTP-ответ не вызывает нового task_id или Send.

Синхронизация сверяет chat/session/origin и отдельный ключ; ответ для
предыдущего чата/ключа игнорируется. Поздний ACK более старой revision
не стирает новую локальную фазу. Не меняются поля send_status и archive_status
вследствие одного сетевого ACK метаданных. Нет новых DOM-кликов, attach,
автоповторов или второго userscript. Старые File-only проверки сохранены.

### Отдельное разрешение владельца

Старые approvals читаются без task_intents и НЕ получают новое право.
В Owner Viewer для уже одобренного Notifier добавлена отдельная кнопка
«Разрешить метаданные сохранённых задач». Owner bearer + same-origin
POST /api/notifier/task-intents, body строго session/chat, записывает
дополнительный scope для того же approved claimant proof. Следующий
announce выдаёт дополненную пару без сброса старой привязки.
Иной proof не получает ключ. Grant переживает перезапуск Viewer.

repo_browser_pair.py --task-intents и owner_pair(..., task_intents=True)
запрашивают ключ только явно. Без этого флага прежний pairing не меняется.
Windows → Repo допускает ровно два новых metadata POST, каждый проверяется
по allowlist. Нет generic proxy или доступа к owner API через этот ключ;
оригиналы по-прежнему используют отдельный message_writer_key.
Отзыв постоянной auto enrollment не означает отзыв ранее выданных
observer/writer/intent bearer keys; прежняя семантика отзыва не расширялась.

### Проверки и пределы этапа

Node: 241/241 PASS и build:check PASS; synthetic Viewer UI PASS.
Python полный набор: результат последнего прогона указан в CURRENT_STATE.
Изолированная цепочка owner HTTP → narrow bridge → relay → ephemeral
Repo HTTP проверяется без Windows/Docker restart и без live 18754/18755.
Цвета, favicon и включение intents в основной Viewer task export — этап C/D.
В действующем интерфейсе новые записи пока не обещаются. Установку сейчас
не выполнять: требуется отдельный согласованный rollout и live проверка.

Ниже сохранён контракт этапа A как история; его ограничения «Send не входит»
и отсутствие Notifier/Viewer правок относятся только к предыдущему этапу.

Статус: реализовано в исходниках; в работающую систему НЕ установлено.
Notifier 5.7.23, Windows Viewer/Dispatch, действующая служба и её архив
не менялись. Здесь нет маршрута Send и нет автоматической отправки.

## Назначение и границы

Зарегистрировать per-message task_id до первого AI event после сообщения
Notifier об успешной локальной записи оригинала. Сервер сохраняет только
утверждение клиента о локальном сохранении: provenance=notifier_local_save_claim.
Это не независимая проверка GM storage, доставка в ChatGPT или архив оригинала.
Подготовленный локальный контекст также не доказывает его вставку в composer.

Файлы task_intents/task_<32 lowercase hex>.md хранятся внутри каталога
соответствующей Repo-сессии. Один неизменяемый metadata record на (session,task).
Повтор точного payload возвращает прежний registered_at_unix; конфликт — отказ.
После потери HTTP-ответа клиент может безопасно повторить ТОТ ЖЕ payload.

## HTTP-контракт

| Метод и путь | Полномочие | Результат |
|---|---|---|
| POST /api/task-intent-pair | Owner bearer, Host/Origin guard | Отдельный task_intent_key для этой session/chat |
| POST /api/task-intents | X-Fortis-Task-Intent-Key | 201 created или 200 existing |
| GET /api/task-intents?session=... | Owner bearer | Метаданные и проекция принятых V2 событий по task_id |

Pairing body строго: version=1, reporting_session_id, conversation_id.
Это новый ЯВНЫЙ owner-authorized POST; текущие observer/writer/enroll
маршруты не выдают это право автоматически. Повтор выдачи возвращает
тот же сохранённый ключ. Pairing keys не попадают в обычные status ответы.

Registration body строго:

```json
{
  "version": 1,
  "reporting_session_id": "rs_<32 lowercase hex>",
  "conversation_id": "<current registered chat>",
  "task_id": "task_<32 lowercase hex>",
  "prepared_at_client_ms": 1792530000000
}
```

Угловые скобки — документационные placeholders, не корректные ID.
Тексты, summary, filename, ключи, произвольные дополнительные поля и
send_state не разрешены. Общий JSON предел 1024 байта, application/json;
дубли полей, Content-Length и неоднозначное framing отвергаются.
POST query не допускается. Host только loopback, cross-site/чужой Origin
отклоняются; ключ нужен независимо от loopback. Ключи не идут в URL/argv/log.

Только Repo-сессии. Session/chat проверяются по существующему session.md;
bootstrap session_task_id запрещён в качестве нового task_id.
Ключ другой сессии, observer_key, message_writer_key и owner bearer
не заменяют task_intent_key при регистрации. Клиентский task_id остаётся
утверждением держателя этой capability, не платформенным доказательством.

prepared_at_client_ms: целое >0 и <4102444800000; для новой записи
не дальше 30 секунд в будущем. Старые offline drafts разрешены.
registered_at_unix назначает сервер. Точный retry не зависит от
последующего перевода часов. Клиентское время не определяет AI liveness.

Ошибки: 401 owner auth; 403 capability/origin; 409 schema/conflict/limit;
503 файловое хранилище. Ответ не содержит exception или исходный payload.
Успех записи требует atomic write + fsync + readback. Предел 256 intent
records на сессию; автоматического удаления/сброса нет. Достигнутый лимит
не блокирует точный retry. Symlink/reparse и повреждённые записи дают отказ.

## Проекция состояния

GET объединяет intents и принятые V2 events, не меняет ни один из источников.
Не читает original_text, assistant body или staging inbox; summary/detail
событий не входят в ответ.
Возвращает отдельные timestamps first_activity_at, first_work_at,
last_work_at, terminal_event и происхождение обеих групп данных.
Фильтрация сверяет session, chat через регистрацию, route, enrollment и
archive sequence/filename; legacy V1 session task сюда не превращается.

- prepared: есть только metadata local-save claim; Send не утверждается.
- activity_observed: принят user_message/assistant_message без work event;
  это не started и не платформенная квитанция ChatGPT.
- working: started/progress/checkpoint; допускается пропущенный started.
- silent: 15 минут без work event; unknown: 60 минут.
- waiting_tool удваивает оба порога; timestamps берутся из принятого архива.
- blocked: явное последнее управление blocked; progress может возобновить работу.
- completed/failed: явное terminal событие, в том числе без started.
  Первый terminal в логическом archive sequence фиксирует проекцию этой задачи;
  поздний progress и поздняя регистрация её не открывают заново. Сами события
  сохраняются в прежней истории. Новый пользовательский запрос — новый task_id.

Нет серого статуса/цветов в этом этапе и нет автоматического failed.
Данные о Send в протокол пока не входят: API не выдаёт prepared за доставку.
Счётчики всех состояний возвращаются отдельно; completed одной задачи
не скрывает prepared/working другой. Чтение ограничено MAX_EVENTS_PER_SESSION
и 256 intents; invalid_event_files/truncated_events сообщают пределы проекции.
Intent corruption — явная ошибка, а не тихое исчезновение черновика.

## Совместимость и проверки

Store, /api/state, /api/task-activity, /api/user-messages, оригинальный
writer receipt/digest и Windows bridge allowlists не изменены. Intent
никогда не разрешает запись оригинала: нужен прежний принятый activity signal.
Нет нового кода в Notifier, Viewer, installer или favicon.

Изолированные проверки: 25 новых unit/HTTP tests PASS; полный набор
observatory/v1 Python: 136/136 PASS. Архивы синтетические, HTTP-порты
эфемерные; live 18754/18755 и текущая история не использовались.

Следующий шаг: отдельные сведения о попытке Send и неблокирующая
Notifier-синхронизация после проверенной локальной записи с offline/reload
retry. Для Windows транспорта позже потребуются согласованные изменения
узких allowlists и pairing. Не расширять их generic proxy. Viewer export,
цвета и favicon — последующие этапы. Никакие команды установки или restart
для текущего этапа выполнять не требуется.
