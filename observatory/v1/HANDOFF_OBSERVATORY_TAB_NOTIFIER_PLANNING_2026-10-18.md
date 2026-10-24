# Handoff — Fortis Observatory V1 × ChatGPT Tab Notifier × Planning Helper
**Срез:** 18 октября 2026 г.  
**Назначение:** полный контекст для нового чата: подтверждённые результаты, границы проверки, текущие исходники и следующий план.  
**Правило:** отличай работающую установку Windows, рабочие копии Fortis Repo, GitHub и предварительные планы. Ничего не публикуй, не перезаписывай и не расширяй права автоматически.

## 1. Коротко — состояние

1. **Tab Notifier уже находится в Fortis Repo.** Проверен путь `/workspace/repos/tabnotifier-fileautosend-autochat`, Git-репозиторий с `origin=https://github.com/AlexPastukhh/tabnotifier-fileautosend-autochat.git`, ветка `main`, HEAD `ef3cbc6988c61114fcc18767bd08378fab440905`. **Не создавать новый репозиторий, не клонировать дубликат и не переносить повторно.** В этой рабочей копии есть необходимые изменения Observatory, но они **ещё не закоммичены**.
2. **Observatory V1** реализует добровольную отправку событий работы по файловой очереди, приём, Markdown-архив/панель и read-only статус для Tab Notifier. Исходники и адаптер: `/workspace/repos/tunnel/observatory/v1/`.
3. **Notifier** умеет независимо выбирать источники **начала и конца** работы: DOM / Observatory / оба / ни один. От Observatory: `🔵` работа, `🔷` готово непросмотрено, `🔹` просмотрено; от DOM: `⏳`, `●`, `✓`. Пользователь сообщил «все сделал», «все работает» после установки исправленного патча. Однако прямого доступа к его Edge/Windows runtime из Fortis Repo нет.
4. **Контрольный 10-секундный прогон** был выполнен в чате: staged `started #18`, пауза `sleep 10`, затем staged `completed #19`. Отправитель вернул `STAGED_ONLY` для обоих. Отдельного пользовательского подтверждения поведения значка **именно после этого прогона** не поступало; ранее пользователь сообщил, что интеграция работает. Не выдавать `STAGED_ONLY` за acceptance receipt.
5. **Planning Helper:** подготовлен импорт одной **новой** prompt-записи `work.value-quick-check-observatory`. Существующая `work.value-quick-check` и общий модуль `core.work-value-and-proportionality` остаются без изменений. Импортный файл подготовлен, но фактические `Import local` и `Save GitHub` **не подтверждены**.

## 2. Что конкретно сделано — Observatory

**Репозиторий:** `/workspace/repos/tunnel`, GitHub: https://github.com/AlexPastukhh/tunnel (`origin`), подпроект `observatory/v1/`. Ветка/коммиты этого репозитория не принимались за доказательство установки V1 у Windows owner; сам каталог `observatory/v1/` на момент проверки значился `??` в `git status` Tunnel (некоммитированный/неотслеживаемый путь).

**Файлы:**
- `observatory/v1/server.py` — локальный HTTP viewer/API, инструкции для подключённых чатов, pairing/status.
- `observatory/v1/store.py` — регистрация sessions, приём/валидация, read-back файлового Markdown-архива и статусы.
- `observatory/v1/emit.py` — CLI отправителя в разрешённую очередь.
- `observatory/v1/client.js`, `index.html`, `style.css` — панель с хронологией событий.
- `observatory/v1/test_v1.py` — регрессии V1.
- `observatory/v1/README.md` — описание протокола; `OWNER_INSTALL.md` — **исторические установочные инструкции с устаревшими SHA-пинами**, не запускать вслепую.
- `observatory/v1/notifier-adapter/README.md` — интеграция, патчи и история миграции.

**Протокол:** пользователь явно подключает беседу по Chat ID `/c/...`, получает отдельные `reporting_session_id`, `task_id`, маршрут. Разрешённый отправитель посылает `started`, `progress`, `checkpoint`, `blocked`, `completed`, `failed` с монотонным `sequence` и коротким безопасным `summary`. Stage: `planning`, `editing`, `testing`, `waiting_tool`, `reviewing`, `other`. `STAGED_ONLY` означает лишь файл во входящей очереди; acceptance означает отдельную проверку/архивацию Observatory. `completed` — сообщение о завершении работы, **не доказательство, что полный ответ записан или браузер уже закончил**. Нет автоматического перехвата каждого сообщения чата или фактических вызовов инструментов.

**Шаги:** обновлена инструкция, выдаваемая через `/api/instructions?session=...`: для существенной работы показывать пользователю логические этапы **по ходу выполнения** и отправлять соответствующие `progress/checkpoint` тогда же, а не в конце пачкой; обычно 2–6 полезных промежуточных событий, только по реальным изменениям, без искусственной телеметрии для простого ответа. Напоминание: установленная защищённая Windows-копия `server.py` может отличаться от Repo — отдельно проверить версию инструкции перед заявлением об её работе.

**Интеграционный API:** owner-only `/api/observer-pair?session=...` выдаёт read-only pairing; `/api/observer-status?session=...` с отдельным `X-Fortis-Observer-Key` возвращает **последнее** принятое событие (тип, sequence, accepted_unix, идентификаторы). Не публиковать pairing, owner token, приватные URL или полные чаты.

**Свежая проверка в Fortis Repo:** `cd /workspace/repos/tunnel/observatory/v1 && python3 -m unittest -q test_v1.py` — **21/21 PASS** (18.10.2026). В предыдущих прогонах смежные тесты Observatory проходили **47/47**; это исторический результат, не новая повторная проверка в этом handoff.

## 3. Что конкретно сделано — ChatGPT Tab Notifier

**GitHub:** https://github.com/AlexPastukhh/tabnotifier-fileautosend-autochat  
**Fortis Repo:** `/workspace/repos/tabnotifier-fileautosend-autochat` — существует.  
**Отдельный пользовательский Windows checkout:** `C:\Users\alexa\tabnotifier-fileautosend-autochat` — использовался для PowerShell build и Tampermonkey. **Не предполагать** на основании совпадения путей, что две рабочие копии всегда синхронизируются автоматически.

Подтверждено в рабочей копии Fortis Repo:
- `src/response-monitor.js` — нативный DOM-start/end, `startFromExternal()`, `finishFromExternal()`, отделение auto-send/onFinished от внешнего completed.
- `src/observatory-completion.js` — привязка по Chat ID, опрос Observatory, проверка возраста/sequence, переключатели источников.
- `src/runtime.js` — подключение моста, команды меню.
- `src/config.js`, `src/title-utils.js`, `src/tab-state.js`, `src/notifications.js` — индикаторы, favicon, desktop notification.
- `build-userscript.mjs`, `chatgpt-tab-notifier.user.js` — сборка Tampermonkey userscript.
- `tests/*.test.mjs` — собственные регрессии.

**Четыре режима для текущего Chat ID и текущей вкладки Edge:**
| Выбор | Начало | Завершение |
|---|---|---|
| Только DOM | Нативные ⏳ | Нативные ● / ✓ |
| Только Observatory | Принятый свежий started/progress/checkpoint → 🔵 | Принятый completed → 🔷 / 🔹 |
| Оба | Оба источника разрешены | Оба источника разрешены; выигрывает первый применимый |
| Ни один | Ни один из этих источников не начинает индикатор | Ни один из этих источников его не завершает |

Меню Tampermonkey: `Fortis: переключить DOM (начало и конец)`, `Fortis: переключить Observatory (начало и конец)`, `Fortis: показать источники состояния`, а также привязка/отключение текущего чата. Режим по умолчанию `both`; сохраняется в `sessionStorage` для вкладки/Chat ID. Pairing ключ хранится отдельно, не в переписке. В режиме «только Observatory» DOM и нажатие Send не должны сами включать рабочий значок; внешнее completed не запускает очередь сообщений и автоматическую отправку.

**Текущее состояние Git:** HEAD `ef3cbc6`, ветка `main`, remote `origin` указан выше. Незаписанные в коммит изменения: `build-userscript.mjs`, `chatgpt-tab-notifier.user.js`, `src/config.js`, `src/notifications.js`, `src/response-monitor.js`, `src/runtime.js`, `src/tab-state.js`, `src/title-utils.js`; новый неотслеживаемый `src/observatory-completion.js`. **Не делать git reset/clean/checkout, commit или push без явного согласия пользователя и проверки diff/секретов.**

**Свежая проверка Fortis Repo (18.10.2026):** `cd /workspace/repos/tabnotifier-fileautosend-autochat && npm run verify` — **57/57 тестов PASS**, `build:check` — `Generated userscript matches modular sources.` Это подтверждает Repo checkout, не независимо установленный Tampermonkey runtime.

**Патчи и история:** в `tunnel/observatory/v1/notifier-adapter/` есть первоначальный, цветовой, старый toggle, несколько миграций. Проблема установки заключалась в том, что Windows checkout уже содержал часть старого toggle и два комментария `response-monitor.js`, поэтому несколько общих патчей не проходили `git apply --check`. Финально адресно изготовлен `notifier-observatory-upgrade-exact-v1.patch`, SHA-256 `00391ad29b4ea901b1cf8ed9c7535ec2eac380be466e10b05999d9825d6f29e3`; пользователь сообщил, что всё сделал и работает. **Не применять эти патчи повторно к нынешнему дереву Fortis Repo: нужные изменения уже присутствуют.**

Tampermonkey Local Loader должен иметь `GM_getValue`, `GM_setValue`, `GM_deleteValue`, `GM_xmlhttpRequest`, `@connect 127.0.0.1` и локальный `@require` на собранный userscript; если в установленном Edge нужны дополнительные действия, сначала сверить фактические метаданные, не копировать ключи в чат.

## 4. Planning Helper: две соразмерные версии промпта

**Канон:** https://github.com/AlexPastukhh/obs-planning-docs (`main`), в Fortis Repo есть `/workspace/repos/obs-planning-docs`.
- Существующий Prompt (оставить неизменным): `planning/helper-library/prompts/work.value-quick-check.prompt.md`, ID `work.value-quick-check`, title «выполняй соразмерно — без лишних действий».
- Его общий Module (оставить неизменным): `planning/helper-library/modules/core.work-value-and-proportionality.module.md`, ID `core.work-value-and-proportionality`. Ссылка в Prompt: `[[module:core.work-value-and-proportionality]]`.
- **Новый ADD Prompt:** ID `work.value-quick-check-observatory`, title «выполняй соразмерно — с Fortis Observatory и шагами». Его `text` начинается с **полного исходного `text` существующего Prompt**, включая ссылку на тот же модуль; далее добавлен раздел про разрешённую телеметрию `started/progress/checkpoint/blocked/completed/failed`, своевременные логические шаги, последовательность, приватность и ограничения `STAGED_ONLY`.
- Импортный файл из этой беседы: `planning-helper-proportional-work-observatory-import.txt` (передать новому чату как вложение при необходимости), один `[PLANNING_HELPER_PATCH]`, `upsert.helperItems` — только **1 ADD**, `delete.helperItems` — пусто; Commands, Modules, каталог/группы, UI не затрагиваются.
- Проверка ZIP/GitHub источников для существующего Prompt и Module выполнена по Git blob SHA. Повторная проверка валидным `chat-recovery.js` + `helper-library-codec.js` + `helper-module-resolver.js` из ZIP: **PASS**, длина нового текста 5800 знаков, после раскрытия Module — 9387. В ZIP присутствуют 62 prompts, 34 modules и 3 legacy helper-command (99 файлов библиотеки); ранее прозвучавшее «96→97» не считать проверенным фактом, фактическое локальное число может отличаться.
- **Не подтверждено:** пользователь импортировал `.txt` в Planning Helper или сохранил новый Prompt в GitHub. Следующие действия пользователя: `Import` → вставка файла → preview `ADD 1 / UPDATE 0 / DELETE 0` → `Import local`; при готовности — per-row `Save GitHub` с учётом возможной публикации текущего порядка Prompts. Не делать прямой Git commit/push вместо этого workflow.

**Контракт/код проверки:** `planning/helper-library/README.md`; UI import: `planning/documentation/tools/tampermonkey/chat-command-palette/scenarios/SCN-PH-IMPORT.md`, `src/chat-recovery.js`, `src/helper-library-codec.js`, `src/helper-module-resolver.js`. ZIP — снимок, при новых правках сверять GitHub отдельно.

## 5. Запланировано / открытые вопросы — порядок приоритета

### Ближайшие практические действия
1. **Перенос Tab Notifier в Fortis Repo — уже удовлетворён.** Папка и Git remote существуют, необходимые source changes обнаружены; не создавать новый репозиторий. Если требуется публичное постоянное сохранение текущей интеграции, отдельно получить разрешение на **осмысленный commit/push** после проверки diff и конфиденциальности. Не путать наличие GitHub repo и публикацию незакоммиченных изменений.
2. Подтвердить актуальную Windows-защищённую установку Observatory V1: правильный `server.py` и новые инструкции про логические шаги, owner-only API, парный статус; `OWNER_INSTALL.md` содержит старые SHA и не является готовой повторной инструкцией. Без отдельного разрешения не менять ACL, порты, mount и доверенные owner-каталоги.
3. Подтвердить локальный импорт нового Planning Helper Prompt и, если нужно, явно инициировать его `Save GitHub` через пользовательский интерфейс.
4. Провести при необходимости **узкий** повторный live-тест после новых изменений: `started` → `progress` → `checkpoint` → `completed` при режиме «только Observatory», проверить переключение 🔵 → 🔷/🔹 и отсутствие auto-send. Никаких искусственных долгих ожиданий, если цель — просто проверить парсинг.
5. **Ограничение коротких работ:** read-only `/api/observer-status` сейчас отдаёт лишь *последнее* событие. Если `started` и `completed` пришли между опросами, Notifier может пропустить запуск/завершение. Потенциальное отдельное улучшение: возвращать **несколько последних кратких маркеров** без `summary`/секретов, применять по sequence с защитой от старых событий и двойных уведомлений; оценить необходимость перед реализацией, написать синтетический тест быстрого цикла.
6. Проверить граничные случаи: несколько вкладок одного Chat ID, смена URL, новая задача в том же подключении, опрос после перезагрузки и отключения Observatory, HTTP error/offline, зависший Edge. Применять только по реальной потребности; основные synthetic tests уже проходят.

### Более поздние планы (не принятые решения)
Есть отдельный **candidate / not committed** pre-work `fortis_observatory_candidate_prework_v3_2026-10-18.md` и Browser Companion candidate. Это **не** описание того, что уже полностью реализовано. В нём в качестве будущих направлений описаны:
- Сохранение **полного текста пользовательских сообщений и ответов** в отдельном согласованном приватном контуре; текущая V1 этого не делает.
- Browser Companion/extension или иной способ получения дополнительных browser-событий; отдельно исследовать приватность и права доступа.
- Фактический аудит **всех наблюдаемых `tools/call`** по G2/Repo (файловые операции, поиск, CLI, процессы и др.), а не просто самодекларации ассистента. Будущая `SRU-07`, отдельное решение и безопасность. `session_ref` на уровне MCP — лишь предложенная гипотеза `PR-14`, **deferred/pending**, не V1. Различать verified attribution / sender-claimed / unassociated; не приписывать вызов чату по близости времени.
- Публикация личного архива или расширение прав доступа — только по отдельному решению. Никакого автоматического Git push приватных записей.

## 6. Карта мест: что открывать новому чату

| Что | Fortis Repo / GitHub | Локально Windows (проверять, не предполагать тождественность) |
|---|---|---|
| Tab Notifier — рабочие исходники | `/workspace/repos/tabnotifier-fileautosend-autochat` ; [GitHub](https://github.com/AlexPastukhh/tabnotifier-fileautosend-autochat) | `C:\Users\alexa\tabnotifier-fileautosend-autochat` |
| Observatory V1 — source и инструкции | `/workspace/repos/tunnel/observatory/v1` ; [GitHub tunnel](https://github.com/AlexPastukhh/tunnel) — V1 untracked в рабочей копии | исходники `C:\Users\alexa\Repos\tunnel\observatory\v1` |
| Установленное Observatory — owner | **Не Fortis Repo checkout** | исторический целевой путь `%LOCALAPPDATA%\FortisObservatoryV1\App`; проверить фактическую установку, `OWNER_INSTALL.md` устарел |
| Owner archive | изолированно от RW-репозитория | исторический план `Documents\FortisObservatoryHistory`; фактический каталог подтвердить у owner |
| Repo inbox событий | `/workspace/files/FortisObservatory-v1/inbox/repo` — **очередь**, не архив | `Workfiles\FortisObservatory-v1\inbox\repo` по установочному шаблону |
| Адаптер и миграции | `/workspace/repos/tunnel/observatory/v1/notifier-adapter/` | `C:\Users\alexa\Repos\tunnel\observatory\v1\notifier-adapter` |
| Planning Helper library | `/workspace/repos/obs-planning-docs/planning/helper-library/` ; [GitHub](https://github.com/AlexPastukhh/obs-planning-docs) | локальные записи Planning Helper в браузере могут отличаться от GitHub |
| Импорт второго промпта | `.txt` из этого чата, не опубликовано автоматически | `Planning Helper → Import → Import local` |
| Будущая архитектура | `fortis_observatory_candidate_prework_v3_2026-10-18.md` — отдельный candidate file | не объявлять committed или реализованным |

**Синтетические проверки:**
```bash
cd /workspace/repos/tabnotifier-fileautosend-autochat && npm run verify
cd /workspace/repos/tunnel/observatory/v1 && python3 -m unittest -q test_v1.py
```
Старая связанная документация отмечает дополнительные 47 synthetic смежных тестов Observatory; не требуется повторять без причины.

## 7. Безопасность, полномочия, достоверность

- Не менять owner-local `AppData`, ACL, mounts, Windows services, G2/Repo trust boundary без отдельной авторизации и фактической проверки owner-процесса.
- Не вставлять в чат токены Observatory, pairing key (`X-Fortis-Observer-Key`), содержимое приватного архива или полные конфиденциальные беседы.
- Не запускать publisher/owner server из изменяемого RW checkout Fortis Repo.
- Не путать `STAGED_ONLY`, accepted event, завершение ответа, сохранение полного текста, синтетическую проверку и ручное подтверждение UI.
- Не применять старые patch-файлы повторно; нужный код уже найден в текущем Fortis Repo дереве.
- Не менять связанные Commands, UI, общие Modules или GitHub без отдельного запроса.
- Не считать старый prework `candidate / not committed` принятым целевым дизайном; сравнивать с реально внедрённой V1 перед дальнейшими планами.

## 8. Готовый ввод для нового чата

> Продолжи проект Fortis Observatory V1 + ChatGPT Tab Notifier + Planning Helper по этому handoff. Сначала проверь наличие и status трёх репозиториев в Fortis Repo и свежесть нужных файлов; не дублируй Tab Notifier — он уже есть в `/workspace/repos/tabnotifier-fileautosend-autochat`. Учитывай, что его интеграция Observatory незакоммичена, а пользователь сообщает о работающем Windows-установленном Notifier. Не делай commit/push, не меняй Windows owner security, не запускай повторные миграционные патчи. Действующий базовый режим: DOM/Observatory независимо определяют начало и конец; Observatory сообщает логические шаги добровольными событиями. Новый Planning Helper Prompt подготовлен как ADD, но импорт/сохранение ещё нужно подтвердить. В первую очередь спроси, **какую из оставшихся задач выполнять сейчас**: подтвердить импорт второго prompt, исправить пропуск быстрых событий Observatory, подготовить осмысленный Git commit/push с разрешением или продолжать другую явно выбранную работу. Не переисполняй всё без причины.

---
**Источники проверки handoff:** фактические чтения рабочих копий Fortis Repo и `npm run verify` (57 PASS + build:check), Observatory `test_v1.py` (21 PASS), GitHub поиск существующего Tab Notifier repo, fetch действующих Planning Helper Prompt/Module/codec, предоставленный ZIP библиотеки, разбор импортного payload действующим `chat-recovery.js` и раскрытие через `helper-module-resolver.js`. Нет прямой независимой проверки содержимого защищённой Windows `AppData`, установленного Edge и факта локального импорта Planning Helper.
