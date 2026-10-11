# Fortis Snapshot Bridge / Broker V2 — общий план и Desired Scenarios

**Решение/состав:** **DESIGN SELECTED (2026-10-11)** — пользователь выбрал ранее рекомендованные варианты и поручил включить Desired Scenario и документацию в общий план перед реализацией.  
**Текущий статус реализации на 2026-10-11:** **V2 CORE INSTALLED / TWO STANDING SNAPSHOT E2E VERIFIED ON test-private**. Дважды использовано одно временное standing-разрешение для `test-private`, оба приватных GitHub Actions Artifact получены и независимо проверены в файловой среде ChatGPT (восемь файлов / 13 510 байт / manifest и SHA-256). Второй push первоначально прервался из-за временного отсутствия соединения с GitHub: отправлен **тот же ранее созданный коммит**, после чего `recover` вернул тот же Artifact. После того теста Broker был остановлен и approvals возвращены к 0. **Позднее, по явному новому пользовательскому решению «без пользовательских ограничений состава и включить все подходящие проекты», постоянное разрешение включено для 17 приватно-транспортируемых alias.** Два других private alias пока не проходят технические проверки, публичный синтетический `test` не допущен. Broker по-прежнему остановлен. E2E доказан на `test-private`, не на всех остальных проектах. Исторические строки прежних этапов ниже отражают состояние на момент их составления.  
**Рабочий owner новой версии:** этот файл в `Repos/tunnel/docs/`. **Старый V1:** [BROKER_V1_PLAN.md](BROKER_V1_PLAN.md) — самостоятельный исторический COMMITTED baseline, не переписывать его прошлое.  
**Источники выбора:** последующая переписка пользователя; [Candidate Pre-work V3](https://github.com/AlexPastukhh/forfiles/blob/main/artifacts/2026-10-11/candidate-prework-controlled-snapshots-revised-v3.md); [Candidate Scenario](https://github.com/AlexPastukhh/forfiles/blob/main/artifacts/2026-10-11/candidate-scenario-snapshot-bridge-broker-documentation-v1.md). Копии в forfiles — reading artifacts, не рабочий owner.  
**Версия:** 2026-10-11; перед фактическими правками проверить актуальное runtime, поскольку содержимое Windows task/config/permissions может измениться.

## 1. Цель и принятая архитектура

Пользователь хочет дать ChatGPT возможность делать глубокий анализ **актуальных локальных Git working trees** в файловой системе ChatGPT, по возможности **без широкого Windows HOST-доступа и без ручного разрешения каждого snapshot**. Пользователь сам выбирает, **какие проекты можно передавать**, настраивает разрешённое содержимое на Windows и **вручную включает/выключает Broker**. Пока Broker запущен, ChatGPT через Fortis Repo может многократно запросить snapshot **ранее разрешённого** alias; доставка идёт по уже работающему каналу **Windows Bridge → приватный GitHub transport → GitHub Actions Artifact → скачивание и проверка в ChatGPT**. Обычные изменения файлов, попадающих в разрешённый scope, не требуют нового ручного разрешения.

Это **не** обещает, что ChatGPT в том же чате видит только ZIP: Fortis Repo имеет прямые bind mounts Repos/Workfiles, широкие HOST/GitHub инструменты могут иметь другие права. Ограничение состава ZIP и ограничение прав подключений — разные вещи. Для строго «только переданный snapshot» потребуется **отдельный** согласованный режим анализа без расширенных подключений; это не обязательная часть V2.

**Схема:** владелец (Windows approves alias/policy, manually starts Broker) → ChatGPT/Fortis Repo (fixed request) → JSON in shared Workfiles → Windows Broker (alias authorization, private transport, verified preview/fingerprint) → Windows Bridge (snapshot, byte/digest binding, limits) → private Git transport → GitHub Actions Artifact → ChatGPT (download, origin/manifest/path/size/SHA256 verification) → анализ/рекомендации. Применение patch на Windows — отдельное разрешение и другой путь.

**Технический baseline:** 2026-10-11 V1 действительно завершил E2E на `test-private` (8 файлов, 13 510 байт, run 38119248033, Artifact 11694374265, SHA256 verified, recover без дубля). Это подтверждает **путь передачи V1 с одноразовым разрешением**, но не будущие автоматические разрешения V2. Исторические строки «E2E pending» в старых документах могут быть датированными и должны быть исправлены в актуальных эксплуатационных инструкциях.

## 2. User Needs и Fundamental Requirements

| ID | Смысл | Источник / статус |
|---|---|---|
| **N-2-01** | Текущий локальный snapshot пригоден для работы в собственном файловом окружении ChatGPT | пользователь, продолжаем V1 |
| **N-2-02** | Разрешение источников задаётся владельцем один раз, запросы при ручном Broker-on не требуют его присутствия для каждого snapshot | пользователь, выбрано для V2 |
| **N-2-03** | Не расширять ради snapshot Windows HOST-доступ, не создавать новый общий исполнитель | пользователь, сохраняем |
| **N-2-04** | Простой отбор: .gitignore для обычного Git-мусора, Windows .snapshotignore для экспорта, без двойных правил папок | пользователь, выбрано |
| **N-2-05** | После реализации останется компактное, правдивое, полноценное руководство с Desired Scenarios, security boundaries, принятыми рисками и восстановлением | пользователь, новая обязательная цель |
| **N-2-06** | Минимум поддержки и лишних компонентов | пользователь, выбранный принцип |

**Инварианты результата:**

- **FR-2-01 — права Windows:** Broker только с фиксированными именованными операциями, без произвольного Windows shell, записи в приватные policies/permits из Docker, регистрации новых alias/изменения export-режима и вызова `apply` через общую очередь.
- **FR-2-02 — проекты:** повторный snapshot возможен только для **явно одобренного зарегистрированного alias**. Прежний `export_enabled=true` в Bridge сам по себе не даёт standing право Broker. Новые и неизвестные aliases **default deny**.
- **FR-2-03 — файлы:** `.gitignore` — не security policy и не требует закрытия от ChatGPT; при `respect_gitignore=true` влияет лишь на игнорируемые **неотслеживаемые** Git-файлы. Действующий `.snapshotignore` хранится **на Windows вне Docker RW mounts**, применяется при `selection_mode=exclude` и определяет исключения из snapshot независимо от tracked статуса. Обязательные Bridge exclusions, проверка типов, лимитов и известных сигнатур сохраняются. Если требуется политика, но она отсутствует/некорректна или режим `all` ссылается на ignore, нельзя тихо публиковать всё.
- **FR-2-04 — ручной жизненный цикл:** Broker не стартует автоматически при Windows logon, но доступен для ручного старта/остановки в Windows. Вручную включённый Broker — **окно** операций; он не выдаёт разрешение всем проектам.
- **FR-2-05 — права на повтор:** новый проектный Windows opt-in допускает будущие меняющиеся байты внутри утверждённых правил; **каждый конкретный snapshot** независимо вычисляет актуальный fingerprint и Bridge проверяет совпадение отобранных байтов до публикации, без повторного Windows grant для одобренного alias.
- **FR-2-06 — резерв V1:** оставить нынешний Windows one-shot режим для не одобренных standing alias; не превращать одобрение Bridge `export_enabled` в общий доступ Broker.
- **FR-2-07 — доказанный результат:** приватный transport, проверка workflow run/Artifact происхождения, materialization ZIP именно в файловое окружение ChatGPT, безопасная распаковка, manifest/все SHA256/размеры/пути; промежуточный JSON или `ready` — недостаточны.
- **FR-2-08 — ошибки:** replay/timeout/recover по исходному ID не создают повторный snapshot вслепую; остановка/отзыв не означает исчезновения ZIP из Git transport history. Source commit/push и patch/apply не выполняются по одному праву на snapshot.
- **FR-2-09 — документация:** после внедрения понятный текущий сценарий, настройки, безопасность, принятые ограничения и runbook должны быть **доказательно согласованы с установленной версией**; V1 history и V2 готовность разделены.

**Согласованное принятие риска:** запросы JSON в `Workfiles/.fortis-bridge-broker-v1/in` могут писать не только ChatGPT/Fortis Repo, но и другие процессы с соответствующим доступом к папке. Пока Broker работает, такой отправитель может запросить snapshot одобренного alias. **Пользователь явно решил: этот риск зафиксировать, но НЕ добавлять sender authentication, подписи IPC, новые очереди или иную специальную защиту.** Отсутствие аутентификации не скрывать. При расширении операций или круга локальных писателей риск пересмотреть отдельно; сегодня **это не блокер**.

## 3. Committed архитектурный выбор / Proposal Composition

Пользователь выбрал предложенный основной набор в разговоре 2026-10-11. **Решения как дизайн выбраны; код/эксплуатационные эффекты ещё не реализованы.** Внутри V2 они рассматриваются как согласованная композиция, не как набор независимых галочек.

| Предложение | Выбранное решение и причина | Статус |
|---|---|---|
| **PR-C01** (user) | Manual start/stop Broker, убрать автоматический логон-триггер, **не** отключать саму Windows Task | **SELECTED/DESIGN APPROVED** |
| **PR-C02A** (assistant recommendation accepted) | В **существующем приватном** Bridge `repos.json` добавить независимый per-alias `broker_snapshot_enabled`, отсутствие/false = нет standing допуска. **Не** второй список путей, **не** новый скрипт. | **SELECTED/DESIGN APPROVED**, меняет V1 one-shot для explicit approved aliases |
| **PR-C03** (user + code review) | Обычный Git .gitignore; private Windows .snapshotignore; `exclude` там, где политика нужна; fail closed при противоречиях | **SELECTED/DESIGN APPROVED** |
| **PR-C04** (assistant recommendation) | Полный локальный preview при первоначальном разрешении alias; для каждой повторной отправки fresh digest и byte binding | **SELECTED/DESIGN APPROVED** |
| **PR-C05** (user clarification) | **Только существующий private GitHub/Actions** для автоматической доставки; без нового local ZIP/ручного attachment | **SELECTED/DESIGN APPROVED** |
| **PR-C06** (assistant recommendation) | Сохранить old one-shot permits для остальных aliases, fixed ops/recovery, private transport | **SELECTED/DESIGN APPROVED** |
| **PR-C08/C09** (user intent/assistant) | Документировать tool-access scope отдельно от ZIP; исключить лишний manager, duplicate allowed_scope, generic executor, защиту .gitignore | **SELECTED/DESIGN APPROVED** |
| **PR-SC01/02** (user request + assistant recommendation accepted) | **Документация и Scenario — обязательный acceptance V2**. Два уровня: основное краткое руководство + технический Broker runbook и синхронные ссылки в transport docs | **SELECTED/DESIGN APPROVED** |

**PG-BROKER-V2-CORE (единый выбранный набор):** PR-C01+C02A+C03+C04+C05+C06+C08/C09+PR-SC01/02; исторические защитные решения V1 остаются. Выбор **PR-C02B** (повторно использовать `export_enabled` как Broker standing gate) **отклонён как альтернатива** из-за неожиданного расширения прав старых проектов. Новый standalone local ZIP, отдельный manager, защита .gitignore и монолитный SECURITY_MANUAL.md — исключены из V2.

**Независимые невыбранные возможности:** `PR-C07 / PR-SC04` — отдельный приватный Git source repo Bridge (user proposal, optional, **не prerequisite V2**); `PR-SC05` — отдельный строгий analysis-only chat без широких tools (optional при реальной потребности). Ни одну из них не внедрять по умолчанию и не выдавать за уже одобренный scope. При желании вернуться отдельным решением.

**Граница полномочий:** выбор архитектуры **не** даёт разрешения на включение конкретного живого alias, изменение приватного Windows permit/config прямо сейчас, публикацию ZIP/нового проекта или push исходников. Эти действия требуют отдельного явного действия/согласия владельца в соответствующем месте.

## 4. Desired Scenarios — реальная ситуация и наблюдаемый outcome

В источнике [Candidate Scenario](https://github.com/AlexPastukhh/forfiles/blob/main/artifacts/2026-10-11/candidate-scenario-snapshot-bridge-broker-documentation-v1.md) есть более подробная читаемая версия. Здесь **полный по смыслу и самостоятельный baseline**, а не просто ссылка. Это сценарии **целевой V2**, а не заявление об уже установленной функции.

### SC-2-01 — обычный рабочий сеанс

**Участники:** пользователь, ChatGPT, Fortis Repo (Linux Docker), Windows Broker/Bridge, private GitHub Actions. **Prerequisites:** Windows работает; владелец ранее одобрил конкретный alias и Windows .snapshotignore; GitHub private/Actions и GitHub подключение в этом чате доступны; task разрешено вручную запускать.

**Путь:** пользователь вручную запускает Broker → просит ChatGPT анализировать актуальный проект → ChatGPT делает через Fortis Repo `snapshot alias` → Broker проверяет явный допуск alias, private transport и правила, Bridge берёт актуальные Git-файлы, сверяет fingerprint и создаёт ZIP/manifest → private GitHub Actions публикует Artifact → ChatGPT скачивает конкретный Artifact в свою файловую среду и проверяет origin/пути/хеши → анализирует копию и при необходимости повторяет snapshot **без новых Windows grants** → по окончании пользователь останавливает Broker.

**Outcome:** рабочие проверенные данные в ChatGPT при manual-on-demand Broker, без неожиданного Windows HOST shell и source commits; вызовы snapshot не предоставляют права применить patch. **Стоимость прохождения:** два ручных действия start/stop на сеанс, ожидание Actions/download/verification на каждый snapshot; числовые SLA неизвестны.

### SC-2-02 — первичная настройка, новая политика, отзыв

**Prerequisites:** владелец знает нужный зарегистрированный Git-проект, его локальный путь и приватное назначение. **Путь:** при необходимости ChatGPT по предоставленной структуре предлагает `.snapshotignore`; владелец **сам** устанавливает его в Windows Bridge (не через Fortis Repo), получает **полный локальный** список файлов и размеры, проверяет private destination и будущие границы передачи → включает standing Broker opt-in только выбранного alias. Новый alias и неутверждённые проекты остаются выключенными. При смене требований владелец меняет политику/opt-in на Windows или отзывает допуск.

**Outcome:** состав экспорта понятен, новые изменения в разрешённой области передаются автоматически, неразрешённые aliases — нет. **Ограничение:** обычный .gitignore может редактироваться как любой Git-файл; он не должен выдавать себя за защиту от публикации. Опубликованные раньше ZIP остаются в Git transport history и не исчезают после revoke.

### SC-2-03 — сбой, неготовый Artifact, остановка, возврат patch

**Путь:** если ответ потерян или status неизвестен, ChatGPT пользуется **исходным request UUID**, recover и status, не посылает слепой второй snapshot. Если GitHub Actions не дал пригодный Artifact, сообщает промежуточное/ошибочное состояние, не утверждает «получено». Пользователь останавливает Broker только с учётом возможной активной операции, при необходимости разбирает status/recover после рестарта. После анализа ChatGPT может **предложить** patch; изменение на Windows выполняется отдельно согласованным путём, но не командами Broker.

**Outcome:** повтор не приводит к скрытой второй публикации; нет самовольного apply; можно прекратить новые запросы; последствия уже совершённого ZIP push не скрыты.

### SC-2-04 — работа нового чата и владельца по компактным документам

Через время пользователь или новый чат открывает **одну входную страницу**. Из неё понятно зачем нужен Bridge, какие среды/права участвуют, основной повторяемый путь, как настроить alias, начать и закрыть сеанс, что может и чего не может каждый механизм защиты, как восстановиться при ошибке. Для точных команд открывает короткий runbook; GitHub protocol объясняет доставку/manifest. Старый V1 и legacy HOST route обозначены как история/отдельная возможность, **не** как неизбежный default новой версии.

**Outcome:** использование возможно без чтения переписки, без ошибочного auto-host доступа, без слепых повторов и без ложных утверждений о готовности функции. Документация соответствует **фактическому** deployed state после приёмки, а не идеальному проекту.

**Инвариант между SC:** не считать «snapshot-only» автоматической изоляцией прямых подключений Fortis Repo/Windows HOST/GitHub; политики Bridge фильтруют ZIP, а не возможности другого плагина. Строгая изоляция — отдельное решение, не скрытый dependency V2.

## 5. Top-level Scenario Realization Composition

Единицы ниже — **top-level**, с операционными зависимостями и наблюдаемой проверкой. Их внутренний код/дочерние SRU не определены этой таблицей.

| SRU | Purpose / prerequisites / inputs | Capability, output и downstream use | Success criteria |
|---|---|---|---|
| **SRU-2-01 — отбор файлов** | зарегистрированный alias + Git tree + private Windows .snapshotignore; правила и размеры | Явный согласованный selection, full local preview, fail-closed; передаёт область SRU-2-02/04 | `all` не маскирует ignore; tracked/untracked semantics известны; full report и сигнатурные/лимитные проверки |
| **SRU-2-02 — допуск alias** | owner посмотрел полный выбор/назначение | Windows-only `broker_snapshot_enabled`, default false, отдельно от `export_enabled`; употребляется Broker | только одобренный alias делает повторный snapshot, не одобренный требует V1 permit/отклоняется |
| **SRU-2-03 — Broker manual lifecycle** | сохранён Task XML, ограниченный private worker | ручной start/stop; отсутствие logon auto, узкая IPC-очередь; открывает SC-2-01 | работа task manual, после logon не стартует, не требует HOST shell из ChatGPT |
| **SRU-2-04 — проверяемая автоматическая передача** | SRU-2-01–03, private GitHub, доступ в ChatGPT | fingerprint, ZIP, GitHub Actions Artifact, независимая materialization/verification; основа анализа | каждый реальный approved snapshot реально загружен и полностью проверен в ChatGPT; no mismatch |
| **SRU-2-05 — сбои/закрытие/отзыв** | request UUID, статус/owner permissions | безопасный recover, отсутствие дубля, запрет apply, остановка и отзыв; завершение SC-2-03 | timeout/replay не создают второй push; отказ для неразрешённого после revoke/stop |
| **SRU-2-06 — каноническая компактная документация** | согласованные SC/границы и доказанное deployed behavior SRU-2-01–05 | одна краткая точка входа с real-life scenarios/осей безопасности и отдельный runbook с точными командами | можно пользоваться без чата/истории и без ложных полномочий |
| **SRU-2-07 — синхронизация документации и истории** | итог SRU-2-06 и исторический V1/GitHub transport | один owner определений, ссылки/entrypoints, текущая дата и truthful runtime state | актуальные README, SNAPSHOT, CURRENT_STATE и transport docs не противоречат; V1 сохранён |

**Последовательность результата:** SRU-2-01/02/03 формируют доверенный сеанс; SRU-2-04 получает проверенный архив; SRU-2-05 закрывает сбои/отзыв; SRU-2-06/07 документируют **проверенное** поведение. Черновики docs готовятся параллельно, но финализация следует за E2E; source Git repo Bridge опционален, не gate.

## 6. Оси безопасности и осознанные компромиссы (зафиксировать в финальных docs)

| Ось | Выбранная мера | Что НЕ гарантируется / принятый риск |
|---|---|---|
| **Ограничение полномочий Windows** | Broker fixed operations, Windows worker/policy вне Docker writable mounts, без общего Windows shell/apply | прямые права Fortis Repo к смонтированным каталогам остаются |
| **Окно активности** | Broker manual-on-demand | пока включён, shared queue принимает доступные запросы |
| **Допуск проекта** | отдельный opt-in alias, по умолчанию выключен; private-only, старый `export_enabled` не standing permission | разрешённый alias может менять свой набор файлов по установленной policy |
| **Состав snapshot** | Git candidates, mandatory denies, private Windows .snapshotignore и лимиты | .gitignore не security filter для tracked; content scan эвристичен |
| **Неподменность при публикации** | current fingerprint и expected selection digest | digest прошлой версии не блокирует законно изменившийся следующий snapshot |
| **Готовность и достоверность** | independent Artifact origin + manifest SHA256 + safe extraction в ChatGPT | JSON из общей очереди, `status=ready` сами по себе недостаточны |
| **Хранение и отмена** | отдельный private Git transport без source project commit | ZIP остаётся в Git history после local revoke/Artifact expiry |
| **IPC sender** | **принят риск** Workfiles writers, без новой защиты | Broker не удостоверяет именно чат ChatGPT, инициировавший запрос |
| **Повтор/ошибка** | идентичность request UUID, status/recover, no blind retry | при прерывании возможна неопределённость до recovery |
| **Обратные изменения** | snapshot не даёт apply rights | патч на Windows требует отдельного разрешения |
| **Недоверенные Git settings** | сохранить V1 защитные Git subprocess и targeted regression | универсальный аудит всех расширений Git не заявлять без evidence |

Критерий документации: читатель отличает «доступ к ZIP» от «доступ к исходникам через tool», знает дату реального E2E и цену приватной Git history, понимает accepted-risk без ложной обещанной аутентификации.

## 7. План реализации (сначала verification, не реальные приватные экспорты)

**Этап 0 — инвентаризация без изменений.** Read-only проверить Windows Task XML/триггеры, live source vs `runtime/broker`, реальный Bridge registry/modes/путь .snapshotignore, GitHub transport private, старые V1 permits/state. Отметить недоступные поля как Evidence Gap, не обходить блокировки. Зафиксировать целевой затрагиваемый alias и резервные копии. Пользовательские несвязанные Git изменения не сбрасывать.

**Этап 1 — корректный scope/file preview (SRU-2-01).** Для нужных aliases обеспечить рабочий `selection_mode=exclude` и защищённые policies. В режиме `all` если указан обязательный snapshot_ignore_file — fail closed/явная ошибка (не тихо игнорировать); не мигрировать все проекты пакетом. Windows preview — полный локальный отчёт путей/объёма/private destination при начальном одобрении, с digest. Не возвращать потенциально чувствительный полный список всем писателям shared queue без необходимости. Прогнать temp Git worktree tests, проверку size/secret/symlinks/TOCTOU.

**Этап 2 — допуск и текущие байты (SRU-2-02/04).** В действующем **Windows-private Bridge repos.json** добавить per-alias `broker_snapshot_enabled`, отсутствие означает false. Не унаследовать права от старого `export_enabled`; **никакого массового true**. Broker при запросе разрешённого alias повторно проверяет scope/private/limits, считает current selection digest, Bridge сверяет его до GitHub side effect; **Windows grant для каждого snapshot разрешённого alias больше не нужен**. Для остальных сохранить one-shot V1 и отказы. Нет new `enable/register/apply` through queue.

**Этап 3 — Broker task manual (SRU-2-03).** Экспортировать и сохранить старый task XML. Убрать auto triggers/самовозобновление, **не disable task**; оставить минимально нужного Windows пользователя и private worker path. После изменения проверить start, stop, новый logon, активные запросы/recover и отсутствие изменений Docker/Repo/HOST tunnel.

**Этап 4 — негативные offline tests + интеграция (SRU-2-04/05).** Неизвестные/публичные alias, false approval и старые enabled aliases, missing policy, all/exclude mismatch, tracked/untracked, size/secret/symlink/traversal, разные файлы в момент fingerprint, неподдерживаемые verb, expired/reused old permit, recover/replay, тайм-аут/отключение, corrupted/forged shared reply (response advisory), отсутствие неожиданного git helper execution. **Не** добавлять проверку аутентичности отправителя IPC: отдельная новая защита отклонена пользователем.

**Этап 5 — контролируемый live E2E по отдельному пользовательскому разрешению.** До внешней передачи владелец явно согласует безопасный набор тестовых файлов/алиас и приватный GitHub history consequence. Запустить Broker руками; сделать один approved automatic snapshot в GitHub Actions; скачать ZIP **в среду ChatGPT** и проверить manifest; убедиться, что следующий запрос того же approved alias технически может пройти без нового Windows grant. Для **второго фактического push** также получить разрешение на тестовую публикацию, учитывая неизбирательное сохранение ZIP в истории. Проверить recover, отсутствие source commit и apply; затем stop. Не называть прод готовым только по mock тестам.

**Этап 6 — эксплуатационные docs и acceptance (SRU-2-06/07).** Черновики допускается делать раньше, но финальные статусы/команды писать по реально установленному коду после Stage 5. Обновить owners ниже и провести отдельный «новый чат → документ → корректные действия/границы» тест без лишних реальных snapshot. **Реализация V2 не считается закрытой без этого шага.**

**Rollback:** вернуть проверенные backups Bridge/registry/private policy/worker и экспортированный Windows Task XML; default-disable новый Broker standing opt-in, сохранить V1 one-shot и request journal, не стирать permits/state без понимания; не трогать чужие worktrees. Уже запушенные ZIP **не откатываются** локальными правками и остаются в Git history. Нет hard deadline/budget; время прохождения Actions и трудоёмкость ещё не измерены, не обещать числовые SLA.

## 8. План компактной документации после реализации — обязательная часть V2

**Предпочтительное разделение: одна основная страница + один короткий runbook + обновление существующих entrypoints, не новое семейство security/Scenario файлов.**

| Owner (существующий файл) | Какой результат после implementation | Критерий |
|---|---|---|
| **docs/SNAPSHOT.md** — главный вход | что и зачем; схема; SC-2-01/02/03/04 коротко; start/stop/high-level setup; `.gitignore` vs `.snapshotignore`; понятная таблица security boundaries/accepted Workfiles risk; limits и ссылки | новичок читает один файл и знает рабочий путь/запреты |
| **runtime/broker/README.md** — технический runbook | проверенные реальные команды manual Task, alias opt-in/revoke, preview/snapshot/status/recover, private paths/rights, safe stop/restart/rollback, V1 fallback | команды и deny/allow совпадают с live worker; не утверждать «E2E pending» после известного V1 E2E |
| **docs/CURRENT_STATE.md** — датированное состояние | фактически проверенные Task/worker/Bridge/GitHub capabilities V2 и evidence/limitations, без предсказаний | проверка по live на дату |
| **docs/BROKER_V1_PLAN.md** — исторический baseline | сохранить историю V1; при необходимости только cross-link на этот V2 owner с отдельным статусом | нет переписывания старого FR/решений |
| **transport/CHATGPT_START_HERE.md** (в `AlexPastukhh/chatgpt-snapshot-transfer`) | для нового чата основной Broker V2 маршрут, нужные подключения и ссылка на каноническое руководство, без принудительного HOST-first | не отправляет чат в legacy HOST по умолчанию |
| **transport/docs/CHATGPT_BRIDGE_WORKFLOW.md** | private Github/Actions/download/verifier, retention, recover и отдельность HOST apply; краткие ссылки на Windows selection/alias owner | одни определения transport, без дубля Windows policy |
| **Windows Bridge README** | оставить ссылкой к `docs/SNAPSHOT.md`, если достаточно; при будущей Git source repository — только public-safe source/readme | не возникает второго конкурирующего runbook |

**Содержание основного docs/SNAPSHOT.md минимум:** цель и компоненты; четыре Desired Scenarios; как включить, получить snapshot, проверить, выключить; `.gitignore` для Git мусора vs protected `.snapshotignore`; per-alias approval vs manual Broker lifecycle; таблица безопасности с явно принятым Workfiles risk и отдельным Repo/HOST доступом; приватная Git history; восстановление, revoke и patch policy; ссылки на точные команды; дата/status deployed.

**Документационные инварианты:** не раскрывать реальные токены/permits/private policies/ZIP; не дублировать строки команд с противоположными значениями по разным файлам; различать installed/reviewed/verified от selected design; не превращать старые IDs и прежние E2E snapshots в актуальные session IDs; обновлять связанные ссылки/entrypoints после изменения CLI. Отдельный GLOSSARY или Security Registry не создавать без необходимости.

**Проверка docs:** новый читатель из `docs/SNAPSHOT.md` находит единственные актуальные команды, определяет какой alias approved, понимает невозможность без GitHub connection скачать Artifact, не запускает HOST Shell как обязательный шаг, видит принятую очередь Workfiles и не считает .gitignore защитой секретов; при ошибке использует recover, а не второй snapshot. Датированный `CURRENT_STATE.md` подтверждён live. Финальная правка документации — часть release gate, не необязательная «потом».

**Существующие подтверждённые несовпадения docs:** `runtime/broker/README.md` упоминает «первой полной публикации не было», хотя V1 E2E test-private подтверждён 2026-10-11; `docs/SNAPSHOT.md` содержит старое «до защитных исправлений/разрешения экспорт закрыт» наряду с более поздним V1 E2E; `CHATGPT_START_HERE.md` текущего приватного transport default oriented on HOST. После развёртывания V2 эти entrypoints нужно пересверить; прежний V1 факт не стирать.

## 9. Verification gates / readiness и полномочия

1. **Before code changes:** подтверждён текущий Windows state/task XML/bridge registry, backup, нет случайных затрагиваний чужих worktrees. Если чтение защищённых private permits заблокировано — остановить только зависимую операцию, не пытаться обойти.
2. **Before standing opt-in project:** full actual Windows preview, private transport and retention explanation, действующая policy корректна, владелец явно выбирает alias. **Этот план не включает никакие конкретные real aliases в разрешённый список**.
3. **Before GitHub export:** отдельное разрешение на конкретный safe live test scope/transport; пользовательское согласие на архитектуру V2 не разрешает произвольную приватную публикацию при испытаниях.
4. **Before declare V2 E2E:** хотя бы один real test approved alias с actual Artifact в ChatGPT filesystem и полным SHA256 verification, negative denied alias, recovery и manual Task checks. Не полагаться только на historic V1.
5. **Before release complete:** документация по Stage 6 написана, проверена readback, согласована с live; старые entrypoints не ведут к опасным/ложным командам.
6. **Before any Git commit/push:** посмотреть git status/diff/staged paths и связанные несохранённые чужие изменения. Не делать commit/push по самому факту выбора плана; для отдельного source Bridge repo отдельное разрешение и staging review.

**Статус на 2026-10-11:** выбранные архитектурные/документационные решения зафиксированы в этом плане как design; **implementation pending**, новые standing opt-in **не выставлены**, Windows Task **не менялась**, V2 acceptance **не выполнен**. Исторический `PG-BROKER-V1` был committed и E2E test-private verified. Новый план можно использовать для подготовки реализации и offline проверок; конкретное включение/экспорт данных требует явной операции владельца.

## 10. Альтернативы и оценка экономичности

- **PR-C02B: использовать старое export_enabled вместо нового broker_snapshot_enabled** — отвергнуто как выбор V2: снижает малую цену одного поля, но неожиданно делает доступными старые enabled aliases. Новый флаг — право на действие, не дублирование списков файлов.
- **Local ZIP → ручное вложение в чат** — исключено: пользователь предпочёл действующий GitHub Actions и отсутствие ручного участия для разрешённых snapshot.
- **Отдельная защита .gitignore** — исключена: Git рабочий файл, не security gate, хотя может менять Git candidate listing.
- **Sender authentication общей очереди** — пользователь осознанно принял risk; не входит в текущую версию.
- **Отдельный монолитный Security/Scenario документ** — исключён: краткая таблица в SNAPSHOT и практический runbook дают тот же результат с меньшим дублированием.
- **Bridge source Git repo** — user-origin вариант, **не выбран в обязательный набор**; рассмотреть отдельно после проверки состава (private Windows `repos.json`, state, policies, transport ZIP, backup исключены).
- **Строго ZIP-only ChatGPT session** — возможный отдельный будущий вариант с иными plugin/mount permissions; в V2 честно описать текущие прямые права, не обещать недостижимую изоляцию.

**Три поверхности затрат:** повторяющиеся действия пользователя уменьшаются до start/stop сеанса и начального approval alias; работа реализации — выборка/допуск/task/проверки плюс актуализация уже существующих docs; поддержка ограничена одним policy, одним Broker auth flag, двумя основными doc owner и ссылками. Время GitHub Actions и общее время реализации неизвестны. При обнаружении более простой равнонадёжной реализации отдельной SRU не изменять молча выбранные Needs/FR/сценарии.

---

**Предел записи:** этот документ — канонический план новой выбранной V2 композиции в `Repos/tunnel/docs`, **не** deployed runtime, не GitHub release и не создание рабочего Scenario State отдельно от общего плана. Scenario полностью включён в сам план. Никакие действия с Windows Broker/Bridge, permits, экспортом или приватным GitHub транспортом из этой записи не выполнены.


**Ниже — исторические этапы внедрения, не текущие инструкции.** В одном документе намеренно сохранены прежние промежуточные статусы (например, «V2 ещё не установлен», «standing approvals = 0») с их датами. **Действующий пользовательский путь:** [SNAPSHOT.md](SNAPSHOT.md); **датированное текущее состояние:** [CURRENT_STATE.md](CURRENT_STATE.md); **операционные команды:** [Broker README](../runtime/broker/README.md). Не применять старый `runtime/broker/bridge-v2-windows.patch` к исправленному live Bridge.

## 11. Implementation Log — 2026-10-11 (частичная подготовка, не выпуск)

**Фактический статус:** SOURCE PREPARED / OFFLINE TESTED; **Windows live V2 NOT DEPLOYED**, V2 E2E NOT VERIFIED. Это запись о проделанной работе по просьбе пользователя «реализуй по плану», а не новое право публиковать данные.

- В исходниках /workspace/repos/tunnel/runtime/broker/worker.py подготовлен Windows-only per-alias opt-in broker_snapshot_enabled (отсутствие = false, строковые/небулевы значения отклоняются), V1 one-shot fallback, отказ при snapshot_ignore_file с неправильным selection_mode, без новых verbs/общего shell.
- В runtime/broker/test_worker.py добавлены тесты standing repeated snapshot, неявных старых разрешений, небулевого флага, public transport и policy conflict. **10 offline тестов прошли**. Это не реальный Broker→GitHub test.
- В runtime/broker/bridge-v2-windows.patch подготовлен патч Windows Bridge для explicit snapshotignore guard, полного локального preview и передачи fingerprint через Bridge.ps1. **Он не применён, не проверен против живого Windows кода.**
- Созданы резервные копии текущего Bridge: config-backups/bridge.pre-v2-20261011.py, bridge_selection.pre-v2-20261011.py, Bridge.pre-v2-20261011.ps1. Резервную копию worker live выполнить не удалось из-за блокировки Windows-подключения.
- Из Windows Task XML read-only установлено наличие LogonTrigger и RestartOnFailure (3 раза через PT1M). Task не изменялась; ручной режим и отсутствие автозапуска не подтверждены.
- Операции чтения/записи живого Windows worker/Bridge и большая правка runtime/broker/README.md блокировались системой безопасности подключения. **Не обходить блок**; ограничить утверждения фактически сделанным.
- **Не менялись:** реальные Windows permits/registry/selection policies, Windows Task, GitHub transport, Docker mounts и пользовательские рабочие проекты. Git commit/push и snapshot-публикации не выполнялись.
- **Перед выпуском:** восстановить разрешённый доступ к live Windows runtime, проверить и сохранить worker/Task backups, установить и протестировать Bridge patch/worker, безопасно изменить Task, согласовать конкретный тестовый alias и разрешение на private GitHub E2E, завершить компактную документацию и синхронизацию transport entrypoints. До этого основной пользовательский workflow остаётся V1 one-shot.


## 12. Implementation Log — подтверждённое состояние после установки (2026-10-11)

**Статус:** **V2 CORE INSTALLED / OFFLINE & READ-ONLY INTEGRATION VERIFIED; STANDING-AUTHORIZATION E2E PENDING; DOCS UPDATED**. Эта запись **заменяет по актуальности** предыдущую промежуточную запись (раздел 11) об отказах Windows-подключения; предыдущая запись сохраняется как история процесса, а не текущий статус.

**Подтверждено по живому Windows readback:**
- Live `worker.py` обновлён из репозитория `tunnel/runtime/broker/worker.py`, source/live SHA256 совпали, Python compiled.
- `FortisRepoBridgeBrokerV1`: исходный Task XML сохранён; убраны logon triggers и RestartOnFailure; повторный readback: **Triggers=0, RestartOnFailure=0, TaskEnabled=true, Task State=Ready** (вручную остановлена). Manual start/stop реально проверены.
- Через Fortis Repo при ручном Broker-on работают `list` и `preview test-private`; `snapshot test-private` при отсутствии approval вернул `snapshot_requires_single_use_windows_approval` без публикации. В общем JSON `broker_snapshot_enabled=false` у старых alias.
- Live Bridge `bridge_selection.py` запрещает конфигурацию `snapshot_ignore_file` с режимом `all/include` (fail closed); `bridge.py` и `Bridge.ps1` поддерживают read-only full preview/fingerprint. В реальном `gendocen` preview `selected_manifest=738` полностью соответствует `selected_files=738`, `selected_sample=12`, `published=false`. Windows selection tests passed; Broker synthetic/offline tests: **10/10 passed** на Windows.
- Бэкапы live Bridge source/selection/PowerShell, live Broker worker и исходный Windows Task XML сохранены в приватных Windows каталогах; `repos.json` дополнительно скопирован в `config-backups/repos.pre-v2-live.json`.
- Приватный GitHub transport не использовался для новых snapshot и работа исходных project worktrees не коммитилась. В transport repo опубликованы **только Markdown** обновления start/workflow инструкций; workflow настроен на push ZIP-path, поэтому документационный commit не инициирует Artifact.
- `docs/SNAPSHOT.md`, `runtime/broker/README.md`, `docs/CURRENT_STATE.md` локально актуализированы; старый `BROKER_V1_PLAN.md` оставлен историческим.

**Не завершено и почему:**
- В защищённом Windows `repos.json` **все standing alias approvals остаются false/отсутствуют**. Попытки записать и атомарно заменить JSON получили отказ ОС (file in use / WinError 5). **Не обходить защиту.** Владелец должен на Windows самостоятельно установить `broker_snapshot_enabled=true` только для конкретно разрешённого alias после просмотра полного scope.
- `obs-planning-docs`: `selection_mode=all` + `snapshot_ignore_file`. Новый Bridge отклоняет запрос до экспорта; владелец должен самостоятельно проверить policy и изменить режим на `exclude`, если желает этот alias использовать.
- **V2 live standing snapshot → GitHub Actions Artifact → ChatGPT** не проходил E2E, так как не было нового явного разрешения конкретного проекта и его передаваемых файлов. **Не объявлять полный выпуск/production verification выполненным.** Выполнение после owner opt-in: manual start → 2 approved snapshots без новых one-shot grants → verified artifact/download/manifest/SHA256 → stop/revoke; тестовые private публикации отдельно согласовать.
- Локальный `Repos/tunnel` содержит более ранние несвязанные unstaged/untracked изменения; **git commit/push не делались**, чтобы не включить чужие правки. GitHub-документы приватного transport зафиксированы независимо.

**Вывод:** основная техническая инфраструктура V2 установлена и проверена без новых разрешений и публикаций. Последний пользовательский gate — установить approval/private policy через защищённый Windows-контур и разрешить один безопасный end-to-end. До этого Broker работает вручную, но реальные повторные snapshot **default denied**.


## 13. Remediation по независимому review — технические исправления, документы, проверка 18 aliases (2026-10-11)

**Источник review:** [Final Review R-BV2-1011/v1](https://github.com/AlexPastukhh/forfiles/blob/main/artifacts/2026-10-11/final-review-broker-v2-installed-implementation-r-bv2-1011-v1.md). **Текущий вывод:** исправления части `PR-04` (transport branch), `PR-06` (single byte-capture preview), `PR-03` (transport docs) установлены/проверены; `PR-07` и revoke протестированы synthetic. **Ни одно automatic standing разрешение не включалось, V2 E2E всё ещё pending.** Исторические разделы выше сохраняют предыдущие состояния.

- **Bridge transport branch:** Windows `bridge.py` больше не использует branch исходного проекта как branch частного GitHub transport. Для `private_bridge` target `main`; для synthetic public сохраняется исходный branch. Read-only Python assertion на нестандартной source branch PASS. Реальный private ZIP push на нестандартном alias **не делался**.
- **Preview:** для `-FullFiles -Fingerprint` один Git candidate selection и один byte capture одновременно дают manifest, sizes, SHA256. `test-private` read-only 8 файлов, 13 510 байт, прежний fingerprint и `published=false`; py_compile и selection regression PASS. Копии live Bridge/test/registry до правки сохранены.
- **Broker:** `runtime/broker/test_worker.py` +2 случая: interruption/recover по исходному request UUID без нового snapshot и standing revoke; **12/12 PASS** в Windows и Fortis Repo. Отдельный новый тест в Windows `test_selection.py` не записан из-за security block на инструменте, branch Python assertion выполнен read-only.
- **Все приватные registered aliases, read-only metadata:** 18 проверенных aliases; 13 дали непустой file preview без нарушения записанных file/total limit; `obs-planning-docs` блокирован policy/mode; `research-and-bank` блокирован non-regular выбранным объектом; `obs`, `theory-conspects-and-banks`, `testrepo` экспорт отключён/пустая область `include`. Это **не полный owner audit содержимого**, поскольку проверялись metadata и область, но не каждый файл на конфиденциальность.
- **obs-planning-docs:** read-only trial `selection_mode=exclude` с настоящей private `.snapshotignore` даёт 1183/1183 selected и ноль исключённых, 13 143 358 байт. Простой перевод `all→exclude` без полного review **не обеспечивает фильтрацию текущих файлов**. `repos.json` не менялся; policy конфликт остаётся fail closed.
- **Документация:** два GitHub transport Markdown документа исправлены, независимо перечитаны; главный вход уже не предлагает выполнить snapshot на заблокированном `obs-planning-docs`; исторический HOST путь помечен как legacy; private ZIP history и separate GitHub Artifact обязательны к проверке. Локальные `docs/SNAPSHOT.md`, `runtime/broker/README.md`, `docs/CURRENT_STATE.md` приведены к новой стадии и 12 тестам.
- **Оставшиеся gates:** (1) восстановить штатное Windows HOST соединение (последний ответ `MCP server is not initialized`), (2) Windows owner review/опт-ин хотя бы одного конкретного безопасного private alias и исправление конфигурации только после проверки файлов, (3) разбор non-regular `research-and-bank`, (4) отдельно согласованный настоящий V2 `Broker→Bridge→private GitHub→Actions Artifact→ChatGPT verifier` и безопасный recover, (5) финальная синхронизация deployed docs, (6) отдельный scoped Git commit при необходимости после review staged diff. **Решение пользователя «в целом все проекты могут быть включены» — допустимость рассмотрения, не глобальное default true.**

**Никаких новых GitHub snapshot ZIP, permission grants или source commit/push в этом этапе не было.** Для текущих деталей и evidence см. [датированный CURRENT_STATE](CURRENT_STATE.md) и исходный review.

## V2 E2E — 2026-10-11: две повторные передачи `test-private`

**Outcome:** **PASS для согласованного synthetic/private `test-private`**, при временном `broker_snapshot_enabled=true`, без выдачи нового одноразового permit между snapshot. Пользователь разрешил **две** публикации конкретного восьмифайлового `test-private` в PRIVATE `AlexPastukhh/chatgpt-snapshot-transfer` со знанием о сохранении ZIP в Git-истории. Третьих snapshot и других alias **не публиковали**.

**Перед запуском:** полный read-only `Bridge.ps1 preview -Repo test-private -FullFiles -Fingerprint` подтвердил 8 файлов, 13 510 байт, selection SHA256 `fe8c59282aa7f97d59db5e591e54ace30bf5c453baefd428375f18461621d00f` (тот же ранее согласованный digest), `published=false`. Transport Git clone был чистым, `origin` указан на приватный репозиторий, `main`; в очереди Broker не было ожидающих запросов. Только для `test-private` временно установлен `broker_snapshot_enabled=true`, другие aliases остались false. Windows Task вручную запущена.

| Snapshot | Original Broker request UUID | Git transport commit | GitHub Actions run | Artifact ID | Outcome |
|---|---|---|---|---|---|
| `test-private-20261011T100500Z-acd18897` | `85940bad-e405-48f6-8f36-a1d91f4c9df5` | `10cb156789a741a4909cce87dd72666d0cc35cd5` | `38130685868` | `11697988578` | ready, download and SHA256 verified |
| `test-private-20261011T100632Z-ec1edf9a` | `f80db177-85a5-4637-83e5-ec50ac2bd782` | `6f2255424583a3077098bb21eb510e720e18294c` | `38130962007` | `11698538347` | ready **after precise recovery**; download and SHA256 verified |

**Независимая проверка ChatGPT:** GitHub plugin `download_workflow_artifact` поместил оба архива в файловую систему этой сессии. Проверен каждый ZIP на повреждения, лишние/повторные пути, path traversal, symlink и ожидаемый `_bridge/manifest.json`; сверены snapshot ID, source base commit `b99e8c0de3ec6e8b050fd5f89f6f5b11aaaf442b`, `repo/` paths, все восемь individual file SHA256 и размеры, и независимо пересчитан `selection_sha256` по manifest: оба архива — **8 файлов, 13 510 байт, PASS**. У двух ZIP разные snapshot IDs, но одинаковое одобренное содержимое; проверена принадлежность Artifact каждому конкретному workflow run, GitHub history содержит два последовательных transport commits. SHA256 **самиx скачанных Actions ZIP**: №1 `8fc637eefbec07930daf31992c3ab36510705a52fe3b4a21f7395cc38f1983bd`, №2 `3b9e62ca1b118490292c46faff0b09e962e8f2db2ae7f6373fc59b4627fdd4fc`. Actions упаковка отличается байтами от внутреннего Windows ZIP (`snapshot_sha256`), поэтому эти два digest не следует механически сравнивать между собой.

**Сбой и доказанный способ восстановления:** второй Broker `snapshot` создал ZIP и локальный Git commit, но первоначальный push получил сетевую ошибку `Failed to connect to github.com port 443`. Broker ответил `operation_failed_inspect_recovery`; первый `recover` исходного UUID временно дал `unknown_or_not_started`. Прямой read-only `Bridge.ps1 status` показал `status=error`, точный созданный `transport_commit` и сетевую причину. GitHub compare подтвердил, что удалённая `main` ещё у первого коммита. **Не создавая новый snapshot**, после проверки origin, local HEAD=именно созданный second commit и clean status был повторён **только `git push` ранее созданного commit** на `main`. После этого GitHub подтвердил один дополнительный commit и второй Artifact; `recover` **с тем же исходным UUID** вернул `ready` и `artifact_id=11698538347`. Это восстановление с **ручным оперативным вмешательством**, не обещание полностью автоматической сетевой retry логики. Нельзя при подобных сетевых сбоях слепо создавать новый snapshot.

**Закрытие теста:** временное `broker_snapshot_enabled` для `test-private` изменено обратно на **false**, вручную остановлена Task. Обратное Windows readback: `taskState=Ready` (не запущена), `taskEnabled=true`, `testPrivateStanding=false`, **allStandingEnabled=0**. Имеющиеся два ZIP остаются в PRIVATE Git history и Actions Artifact независимо от local revoke. Изменений source worktree, `apply`, новых grants для остальных aliases, дополнительных ZIP и push исходного проекта не было.

**Статус проекта после E2E:** SC-2-01/SRU-2-04 **E2E подтверждён для synthetic/private `test-private`**, включая повторную передачу без one-shot grant. Не подтверждён широкий production rollout на все реальные private aliases. Открыты ограничения политики `obs-planning-docs`, nonregular file у `research-and-bank`, пустые include/выключенный export у части alias и непроверенный файловый scope настоящих проектов. Базовый Workfiles writer risk остаётся принятым без новой защиты. Для нового пользовательского сеанса нужно отдельно включить выбранные aliases после review файлов и вручную запустить Broker.

## 2026-10-11 — широкое включение проектов после явного решения пользователя

**Новое решение:** пользователь разрешил отсутствие пользовательских исключений файлов и постоянные snapshot-разрешения для всех технически пригодных проектов. Это отменяет прежнее требование отдельного пользовательского выбора каждого alias, но **не** отменяет mandatory Bridge exclusions, приватность GitHub, scan на потенциальные credentials, лимиты, контроль SHA256, ручной запуск Broker и ранее принятый Workfiles writer risk.

**Фактически записано и проверено обратным чтением:** приватный Windows registry (C:\Users\alexa\chatgpt-bridge\repos.json) содержит 20 алиасов, у **17** private-transport aliases стоят broker_snapshot_enabled=true, export_enabled=true, selection_mode=all и respect_gitignore=true, а привязки snapshot_ignore_file отсутствуют. Старый файл политики на Windows оставлен неизменённым, ни один alias теперь его не использует. Публичный synthetic test не получает права приватного Broker. Task FortisRepoBridgeBrokerV1 осталась остановленной (Ready, Enabled=true). **Ни один архив не публиковался** при этой настройке. Backup: config-backups/repos.before-all-alias-20261011.json.

**research-and-bank:** причиной старого nonregular/missing была длина обычного Windows-пути **261 символ**; extended Windows path подтвердил, что Git-tracked файл существует и является обычным. Live Bridge confine использует расширенные локальные Windows paths с сохранением realpath confinement и запрета symlink. Backup: config-backups/bridge.before-all-alias-20261011.py. Точный full preview: **1 307 файлов, 31 059 466 байт**; отдельный total limit увеличен с 30 до **35 МБ**, лимиты размера одного файла и content scan сохранены.

**obs-planning-docs:** удалена только ссылка alias на старый snapshot_ignore_file; в выбранном режиме all 1 183/1 183 файлов, 13 143 358 байт, полный fingerprint read-only PASS. Старый policy файл оставлен без удаления. В остальных включённых alias отбор работает без специальных пользовательских правил, но с mandatory Bridge excludes.

**Два private alias не включены из-за технических блокировок:**
- obs: mode=all дал **59 022 candidates**, уже более **719 821 395 байт** до обнаружения недоступного пути; превышены старые per-file 5 МБ и total 30 МБ. Не расширять лимиты до огромных ZIP без отдельного решения о стоимости private Git history и корректности путей.
- theory-conspects-and-banks: в **15 файлах** найден regex-вариант потенциального OpenAI-ключа. Это ещё не доказательство реальных действующих ключей, но отключать scanner или давать standing право до проверки нельзя.
Публичный synthetic test — третий исключённый alias, не private export target.

**Реализация/проверки:** стандартная atomic save Windows registry завершилась WinError 5 (без изменения файла); штатное Windows file-edit подключение успешно сохранило JSON, exact readback совпал. Live worker registry/private_entry read-only перечисляет **17 стоящих разрешений** и **3 отключённых**. Реальные read-only full preview после записи: research-and-bank 1307, obs-planning-docs 1183, testrepo 2, test-private 8 — manifest count, bytes, digest и published=false подтверждены. Bridge Python compile, selection suite PASS, Broker unit suite **12/12 PASS**. Worktree и GitHub snapshot transport не изменялись.

**Осторожность при дальнейшем использовании:** как только владелец вручную запустит Broker, запрос к любому из этих 17 alias может создать ZIP и записать его в постоянную историю приватного Git transport. E2E на отдельных реальных alias ещё не исполнялся; прежние два Artifact test-private доказывают только основной механизм, не индивидуальное качество/конфиденциальность всех других проектов.
