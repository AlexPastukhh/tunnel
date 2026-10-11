# Fortis Bridge Broker — утверждённый план V1

**Статус:** COMMITTED — решение и состав реализации; IMPLEMENTATION PARTIAL — основные изменения Bridge/Broker/client установлены и прошли read-only/offline проверки; END-TO-END PENDING — новая реальная передача Artifact в ChatGPT не выполнялась; EXPORT DISABLED — разрешение публиковать snapshot через Broker не выдано.  
**Дата принятия:** 2026-10-11. **Owner рабочего плана:** `Repos/tunnel/docs/BROKER_V1_PLAN.md`.  
Это документ решения, а не утверждение о готовности runtime. Git commit/push и публикация новых snapshot **не входят** в данную транзакцию. План действителен для текущих контуров Windows HOST Bridge, Fortis Repo Linux Docker и приватного GitHub Snapshot Bridge.

## 1. Зачем и какую реальность получаем

- **N-01 (подтверждённая нужда):** обычные небольшие задачи решать внутри Fortis Repo; для большого/многократного анализа получать полный пригодный к проверке snapshot в файловую среду **самого ChatGPT**, без пофайловой передачи через MCP.
- **N-02 (подтверждённая нужда):** Fortis Repo может запрашивать разрешённые операции Windows Bridge **без обязательного HOST-плагина в том же чате и без ручного запуска Bridge**.
- **N-03 (candidate/inferred, вне V1):** позже при необходимости безопасно возвращать большие изменения на Windows или использовать Broker для других задач.
- **FR-01 — Windows security boundary:** посредник исполняет лишь фиксированные именованные операции с валидированными аргументами, без произвольных Windows shell/PowerShell, расширения Docker mounts, доступа Docker к секретам, и без доверия исполняемым Git-настройкам изменяемого Repo-каталога.
- **FR-02 — публикация только по отдельному разрешению:** доступность папки в Repo и `export_enabled` в Windows Bridge **не дают автоматически** разрешения Broker публиковать snapshot. В V1 допускается только приватный transport; пользователь утверждает конкретную область и однократную операцию.
- **FR-03 — доказанный результат:** статус готовности, конкретный Actions Artifact, получение ZIP в файловую среду ChatGPT, проверка пути/состава, manifest и SHA-256 — разные обязательные стадии. Ответ JSON из общей папки не считается самостоятельным доказательством завершённой операции.
- **FR-04 — безопасный повтор:** после тайм-аута выяснить состояние прежней операции по её ID, не создавать вторую публикацию вслепую. Нельзя автоматически коммитить/пушить пользовательский source repository или применять patch без отдельного разрешения.
- **FR-05 — достаточно простая система:** общий транспорт для фиксированных capability adapters, но каждый будущий адаптер требует отдельной политики/проверок и не входит в V1. Не строить general-purpose job service, generic executor или обязательную криптографическую инфраструктуру без установленной нужды.

## 2. Committed Desired Scenario V1

**Условия:** Windows открыт под пользователем и локальный Broker task работает; Docker/Fortis Repo Tunnel подключён; целевой Git worktree зарегистрирован и находится в разрешённой для Broker области `Repos`; GitHub Actions и GitHub connector доступны в данном чате. Эти зависимости не обещают, что Actions исполнится мгновенно.

**Путь:** пользователь в ChatGPT выбирает проект → Fortis Repo вызывает Broker `list`/`preview` → проверяется область экспортируемых файлов и приватность → Windows-сторона получает однократное разрешение на этот конкретный snapshot → Repo посылает фиксированную команду `snapshot` → Windows Bridge создаёт ZIP и отправляет его в приватный Git transport → GitHub Actions создаёт Artifact → через `status` и/или независимый GitHub connector устанавливается подлинная готовность и ID → ChatGPT скачивает конкретный ZIP в собственную файловую среду, валидирует архив и каждый файл по manifest SHA-256 → проводит глубокий анализ. **Observable outcome:** локально доступный, целостный и проверенный snapshot, а не просто `published=true`.

**Вне V1:** автоматический `apply`, `enable`, `register`, универсальный Windows shell, любые новые adapters и обязательный режим постоянного разрешения для всех проектов. HOST Bridge остаётся рабочим резервным путём и путём для отдельно разрешённого `apply`.

### Scenario Realization Composition

- **SRU-01 — выбор и допуск.** Вход: alias + область файлов. Проверить регистрацию, private transport, `preview`/selection и однократное Windows-разрешение. Выход: узкое одобренное действие (alias, scope, request ID, ограниченная действительность). Никакого включения экспорта по умолчанию.
- **SRU-02 — безопасный Broker IPC.** Вход: валидированный JSON с ID и именем операции. Worker на Windows вне RW-монтажей; без произвольных команд. Результат JSON из общедоступного `out` сам по себе advisory; provenance итогового ZIP проверяется отдельно.
- **SRU-03 — проверяемый snapshot и восстановление.** Windows Bridge читает недоверенный Git worktree в безопасном Git execution context; создаёт snapshot ровно один раз, сохраняет связь `request_id → snapshot_id` и умеет сообщить последующее состояние. `status` должен обновлять сведения об Actions до `ready`/ошибки с ограниченным ожиданием.
- **SRU-04 — GitHub Artifact в ChatGPT.** Независимо получить актуальный Artifact, сопоставить с request/snapshot/transport, распаковать без небезопасных путей и сверить SHA-256 каждого файла с manifest. Только тогда `done`.
- **SRU-05 (future candidate, не требуется для V1) — возврат изменений.** Варианты HOST `apply -CheckOnly`/`apply`, малые изменения через Repo или новый отдельно проверенный adapter. Отдельный Proposal по выбору, без текущих прав на запись в Windows через Broker.

## 3. Atomic decision / принятые Proposals

**Граница коммита:** одной транзакцией утверждены **целевой V1, его ограничения и следующие технические решения**; НЕ утверждены работающие изменения кода, экспорт какого-либо живого проекта или новая публикация GitHub. `COMMITTED` здесь означает «решение принято», не «feature внедрён».

**Включено в принятую композицию:**

| Источник / Proposal ID | Принятое решение | Статус решения / статус исполнения |
|---|---|---|
| Source `PR-01` (`F-R-01`) | Защитить **все** вызываемые Windows Bridge Git subprocess от запуска недоверенных helpers/config, включая пути preview/snapshot; отрицательные тесты на отдельном worktree. | COMMITTED / pending implementation |
| Source `PR-04` и `MMR-PR-04` (`F-R-02`) | **Минимальный** durable recovery по исходному request ID, без повторного snapshot; исправить обработку claim collision. Полную job platform не строить. | COMMITTED / pending |
| Previous `MR-PR-01` (`MR-F-P-01`) | Исправить `status`/bounded Actions polling и корректную выдачу snapshot_id, status, artifact_id; проверить waiting→ready/failed. | COMMITTED / pending |
| `MMR-PR-01` (`MMR-F-P-01`) | **Всегда** независимо проверять Artifact/manifest/хеши, независимо от любой защиты IPC. Промежуточные ответы Broker не являются final proof. | COMMITTED / pending |
| `MMR-PR-02B` (`MMR-F-U-01`) | Для первого Broker-export — **однократное Windows-разрешение** на выбранный alias/scope с ограничением времени и отзывом; после использования автоматически закрыть. | COMMITTED / pending. Вариант standing approval `MMR-PR-02A` НЕ включён в V1 |
| `MMR-PR-03` (`MMR-F-R-01`) | Перед разрешением проверить определяемый состав файлов; связывать согласованный scope с фактическим snapshot, обнаруживать существенное изменение selection. Для небольшого теста использовать явный список; для больших проектов утвердить соразмерную политику отдельно. | COMMITTED / pending |
| `MMR-PR-05` (`MMR-F-R-02`) | Первый сквозной тест через **`test-private`**, только после read-only preview, проверки private transport и отдельного разрешения именно безопасных файлов; публичный `test` из V1 Broker-export исключить. | COMMITTED / pending test/approval |
| Previous `MR-PR-03` (`MR-F-P-02`) и source `PR-03` | Один полноценный end-to-end **после** защитных правок и разрешения, не считать старый Actions Artifact доказательством нового теста. | COMMITTED / blocked by prerequisites |
| Source `PR-07` | Расширяемый **fixed-capability Broker**. Новые modules добавляются отдельными handlers + allowlists/tests; не открывать generic shell. | COMMITTED design constraint / действует частично |
| Source `PR-05` (`F-R-03`) | Зафиксировать: любой процесс с доступом к Workfiles может инициировать запрос. Ограничить полномочия каждой операции, проверить replay/authorization, не использовать ответы очереди как proof. | COMMITTED security acceptance criteria / pending verification |

**Не входят в committed V1 (не объявлять автоматически реализованными):**

- `MMR-PR-02A` — постоянный доступ для алиаса: **rejected for V1**, можно рассмотреть заново по просьбе пользователя; `ALTERNATIVE_TO MMR-PR-02B`.
- Previous `MR-PR-02B` — отдельная подпись/аутентификация **каждого** IPC reply: **deferred option**, дополнительный уровень только после новой threat-model проверки. Не является альтернативой проверке Artifact. Source `PR-02` принят как требование достоверного итога, но его способ реализуется через `MMR-PR-01` и независимую GitHub-проверку; обещание подписывать все ответы не принято.
- Previous `MR-PR-05` — развитые квоты/очереди: **deferred**, revisit при задержках/spam либо новых привилегированных adapters; разумные базовые лимиты запросов проверить в SRU-02.
- Source `PR-06` — Broker `apply`/Repo-only двусторонний режим: **deferred**, revisit по явному запросу на запись в HOST.
- Расширение за пределы зарегистрированных Git worktrees и private transport — **out of scope V1**. Срок, бюджет и SLA не заданы.

**Proposal Group `PG-BROKER-V1` — HARD_BUNDLE (решение COMMITTED, реализация PENDING):** `PR-01 + PR-04 + MR-PR-01 + MMR-PR-01 + MMR-PR-02B + MMR-PR-03 + MMR-PR-04 + MMR-PR-05 + MR-PR-03/PR-03`. Hard dependency перед первой реальной публикацией: защитные Git-вызовы + разрешение точного scope + безопасный запрос/recovery + проверяемая готовность + доверенный download. Нельзя включать `snapshot_allowed_aliases` просто по факту принятия этого документа.

## 4. Принятый порядок реализации и проверки

**Этап 0. Сохранить рабочее состояние.** Проверить live исходники/policy и состояние Windows task. Не менять Docker mounts, туннели, HOST и существующие Bridge export permissions. Установить отличия Git source snapshot от активного Windows worker. Пока `snapshot_allowed_aliases=[]`.

**Этап 1. Малые изолированные тесты.** Без публикации: проверить (1) Git helper/config execution boundary на временном worktree, (2) Broker response trust/forgery, (3) state `waiting_artifact → ready`, (4) timeout/collision/recover same request ID, (5) проверку scope и private transport. Критерии сценария записать до изменения кода. Не трогать реальные приватные проекты.

**Этап 2. Минимальные защитные изменения в нужных владельцах.** Windows Bridge owning source: безопасная среда Git-команд. Broker source и private live worker: one-shot approval, проверки scope/private route, корректный status, минимальный recovery; Linux client: `receive/recover` и запрет слепого retry. Защищать промежуточные ответы дополнительно только если end-to-end provenance этого требует. Сохранить backup, применить точечно и выполнить негативные тесты; не запускать/перезапускать пользовательские туннели без необходимости.

**Этап 3. Один приватный end-to-end.** Отдельно проверить текущее содержимое `test-private`, приватность и scope; после конкретного разрешения пользователя открыть **одну** операцию, пройти Repo → Broker → Windows Bridge → private GitHub Actions Artifact → локальная файловая среда ChatGPT → manifest/SHA-256. Проверить отказ для `test` и иных неразрешённых alias, отсутствие повторной публикации после uncertain response и отсутствие неожиданного Git commit в source repo. Закрыть permit сразу после использования. Если источник не materialize в ChatGPT — тест не пройден.

**Этап 4. Документировать delivered version, эксплуатацию и возможность расширения.** После реального успеха синхронизировать `docs/SNAPSHOT.md`, `docs/CURRENT_STATE.md`, `runtime/broker/README.md`, живые инструкции и owning Bridge docs без ложных claims о версиях. Любой новый adapter — отдельная изолированная authorization policy, отдельный review, acceptance и lifecycle; `apply` отдельно.

### Gate: когда V1 можно объявить работающей

1. Независимая проверка Windows Git subprocess не допускает внешних программ из недоверенного `.git/config`/helpers (negative test).
2. Repo может выполнить `list`, `preview`, получить `status=ready` с корректным artifact_id; неподтверждённый JSON не считается выполнением.
3. Без Windows one-shot permit `snapshot` отклоняется; с ним принимается только разрешённый приватный alias и согласованный scope; повторный запрос/неизвестное состояние не создаёт второй архив.
4. ZIP скачан в ChatGPT именно из разрешённого приватного transport, безопасно распакован, все файлы проверены по manifest SHA-256; числа/ID/исключения согласованы.
5. Source working tree остался без незапрошенных commit/push/изменений; ключи/токены не попали в Docker; чужие alias и команды отклоняются.
6. Условия автозапуска Broker и зависимости от Windows logon/Docker/GitHub/ChatGPT connectors явно описаны; не заявлять автономность при отсутствии этих dependencies.

## 5. Полномочия, последствия выбора и незакрытые внешние условия

- **Decision autonomy:** выбор минимальных технических реализаций и тестов после принятия плана — HIGH, но изменения security boundary должны проходить review/read-back. **USER_REQUIRED** для реального открытия экспорта, утверждения содержимого test-private и любого расширения до standing approval, публичного транспорта или нового полномочного адаптера.
- **Стоимость рабочего сценария:** one-shot approval добавляет отдельное подтверждение при каждом snapshot. Это **принятый** компромисс ради безопасности V1. Если позже ежедневная частота делает его слишком дорогим, standing narrow access — новый Proposal, не автоматическое смягчение.
- **Стоимость реализации:** короткие offline fixtures + локальное hardening предпочтительнее full-now универсального сервера; оценка effort/calendar/deadline неизвестна, нет установленного hard deadline.
- **Lifecycle:** держать политики private/не записываемыми из Docker, оригинал рабочего скрипта вне общих RW folders; Git исходники в Repo не обновляют live Windows код автоматически. Контроль версий и deployment — отдельная проверка.

## 6. Source references, Review Log и persistence

Исходные Findings/Proposals остаются историческими: `F-R-01/F-P-01/F-P-02/F-R-02/F-R-03/F-U-01/F-O-01`, затем `MR-F-P-01/MR-F-P-02/MR-F-U-01` и `MMR-F-P-01/MMR-F-U-01/MMR-F-R-01/MMR-F-O-01/MMR-F-R-02`; исходные IDs не переименованы. Читаемая копия последнего meta-review: [2026-10-11 meta-review](https://github.com/AlexPastukhh/forfiles/blob/main/artifacts/2026-10-11/meta-review-broker-security-simplicity-61e3.md). Настоящий документ — **канонический owner принятого состава**, а не новая ситуационная копия в forfiles.

**Review Log после начала реализации:** `PG-BROKER-V1` COMMITTED decision; SRU-02 и часть SRU-03 развернуты, но полная безопасность/готовность до live export не подтверждены; SRU-04 проверен только на синтетическом ZIP. `F-R-01`: защитный Git subprocess введён и отдельно проверен на `core.fsmonitor`, полный аудит всех Git extensions остаётся Evidence Gap. `F-P-01`: ответы общей очереди по-прежнему advisory, а итог требует независимого GitHub/manifest proof — принятый компромисс V1. `MR-F-P-01`: статусный polling реализован, реальный GitHub `ready` через новый Broker пока не проверялся. `MMR-F-U-01`: однократное разрешение реализовано, список permit пуст. `MMR-F-R-02`: публичный test блокируется кодом Broker. `F-U-01`: apply deferred. **EXPORT DISABLED / E2E EVIDENCE GAP**.

## 7. Фактическая реализация и evidence (2026-10-11)

Это запись о доставке технической реализации, не изменение committed Need/FR/Scope. Установленная часть не равна прохождению полного Desired Scenario.

- **Windows Bridge:** в live `chatgpt-bridge/bridge.py` добавлены защитные параметры Git для source worktree (отключение `core.fsmonitor`, hooks, external diff); отпечаток выбранных путей и байтов; проверка `--expected-selection-sha256` перед публикацией; сохранение fingerprint в статусе/manifest. Необязательный `git status` для недоверенного source worktree больше не запускается.
- **Broker/client:** обновлён live Windows task `FortisRepoBridgeBrokerV1`, сохранён private worker вне RW Docker mounts, клиент в Docker volume обновлён. Работают `list`, `preview` с content fingerprint, private-only `snapshot` с однократным разрешением Windows по ранее просмотренному fingerprint, `status` с ограниченным Actions polling, `recover` по request UUID и запрет слепого повторного snapshot с тем же UUID.
- **Artifact verifier:** `runtime/broker/verify_artifact.py` проверяет ZIP, небезопасные пути и symlinks, лишние файлы, snapshot ID, SHA256/размеры всех файлов и соответствие всему отпечатку одобренного preview. Это исходник для проверки в файловой среде ChatGPT; нахождение исходника в Docker не означает загрузку ZIP в ChatGPT.
- **Реальный read-only smoke-test:** Windows task Running, `list` и `preview test-private` из Fortis Repo успешны; на момент теста восемь файлов. Snapshot без permit отклонён. Private `permits.json` пуст, `issued-snapshots.json` пуст. GitHub-публикации не создавались.
- **Offline проверки:** шесть тестов `python3 runtime/broker/test_worker.py` прошли с mock Bridge (права, однократность, отпечаток, восстановление, запреты, ZIP). На Windows временный Git-репозиторий подтвердил, что опасный `core.fsmonitor` запускает helper при обычном вызове и не запускает его при защищённом. Временный тестовый репозиторий удалён.
- **Доставка/резерв:** Windows worker имеет резервные копии `worker.pre-v1-20261011.py` и `worker.pre-approval-binding-20261011.py`; прежний Linux client — `bridge-broker-client.pre-v1-20261011.py`. Текущий Bridge скопирован в `config-backups/bridge-deployed-v1-20261011.py` и сверён по SHA-256; это backup **после** исходных правок, а не восстановленный первоначальный `bridge.py`. Worker сверён с Git-исходником по SHA-256. Перезапускали только Broker task, не HOST/Repo Tunnel или Docker.
- **Открытый gate:** перед Stage 3 требуется отдельное разрешение владельца на точный scope `test-private`; затем реальный приватный GitHub Actions Artifact, скачивание в файловую среду ChatGPT, независимый manifest/SHA256 check. Переход `waiting_artifact → ready` с реальными GitHub Actions через этот Broker ещё не проверен. **EXPORT DISABLED / END-TO-END PENDING**.
- **Git:** новые файлы и изменения в `Repos/tunnel` пока только локальные; исходные пользовательские изменения сохранены. Commit/push не выполнялись.

## 8. Сквозная проверка принятого V1 — 2026-10-11

**Результат: E2E VERIFIED для одного одобренного test-private snapshot; универсальная security certification не проводилась.** Исторические записи выше отражают состояние *до* этого теста.

- Одноразовый Windows grant создан для восьми согласованных файлов, 13 510 исходных байт, selection SHA-256 `fe8c59282aa7f97d59db5e591e54ace30bf5c453baefd428375f18461621d00f` и приватного transport `AlexPastukhh/chatgpt-snapshot-transfer`.
- Из Fortis Repo `snapshot --submit-only` создал request UUID `35ca8271-af0b-4343-9d69-eb344dcd0dd3`; `receive` вернул snapshot ID `test-private-20261011T064804Z-553bc983` и transport commit `8dccb5b7946bbfe65b5d883015967a0f44c097b7`.
- `status` через тот же Repo Broker достиг `ready`: workflow run `38119248033`, Artifact ID `11694374265`. GitHub connector независимо подтвердил соответствие Artifact transport commit, приватному repo и название `chatgpt-snapshot`.
- Artifact скачан **в файловую среду ChatGPT**, ZIP SHA-256 `266b13002c70353ebc1f4251e459247fafb1c9e83279015c6ec860a6089e3ed1` совпал с данными GitHub. При распаковке в `/mnt/data/verified-test-private-20261011T064804Z-553bc983` проверены восемь файлов, размеры, per-file SHA-256, manifest snapshot ID, точный список одобренных файлов, content selection digest, отсутствие traversal/symlinks/лишних ZIP-файлов.
- `recover` по первоначальному request UUID вернул **тот же** snapshot и Artifact без новой публикации. Источник изменений — приватный Git transport; не было запроса на `apply`, изменяющего проект.
- **Evidence Gap:** дополнительная Windows-диагностика private permit состояния и исходного Git HEAD после запуска была заблокирована системой безопасности подключения. Следовательно, эти два значения не заявляются независимо проверенными. Ранее проверенная логика однократного permit и отсутствие source commit в Bridge не заменяют живой readback.
- **Следующие snapshot:** отдельное разрешение на каждый новый content fingerprint по-прежнему обязательно. Нельзя считать проведённый тест постоянным правом на публикации.

**Статус:** Committed plan — сохраняется; Installed technical V1 — **E2E VERIFIED на test-private**; broader production/security review — не пройден; расширения, public transport и автоматический apply — вне текущего V1.
