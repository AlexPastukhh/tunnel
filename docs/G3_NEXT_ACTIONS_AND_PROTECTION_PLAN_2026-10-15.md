# Fortis G2 — план по подпунктам и реестр доказательств
Создан 2026-10-15; обновлён 2026-10-16 после E44 (docs/Repo metadata; не новый security PASS). Candidate Execution / Verification Plan, уточнён по доказательствам и границам разрешений.
Текущий итог E43: G3 bounded baseline ACCEPTED(scope); G4 initial Workspace policy ACCEPTED(scope); G5 полная personal-security программа не принята; G6 manual daily/normal recovery ACCEPTED(scope). Whole-chat1.4 PENDING; universal PASS не заявляется. Прежний owner HOST остановлен, G2/Repo работают.

## Канонический статус документа

Эта страница — актуальный источник условий G2, разрешений и Candidate Execution / Verification Plan.
[Навигация](README.md) → этот план → [подтверждённое состояние](CURRENT_STATE.md) →
evidence E01–E44 для выбранного подпункта. [Session decision](G3_SESSION_BOUNDARY_OUTCOME_DECISION_2026-10-15.md)
хранит обоснование архитектуры; общие auth/mount/key правила — [ACCESS](ACCESS.md);
операции контуров — [OPERATIONS](OPERATIONS.md).
[Архив прежних указаний](G2_G3_SUPERSEDED_GUIDANCE_2026-10-15.md) не является источником новых команд или разрешений.

Принятые пользователем условия уже действуют в плане. PENDING/CONDITIONAL подпункты — будущая работа;
сохранение Markdown не выполняет native test, deployment, commit или push.

## Как читать план

Каждый подпункт содержит доказанный результат, его конфигурацию и только оставшуюся работу.
PASS сохраняется в указанном scope; новый процесс требует проверки identity, но не обнуляет старое evidence.
Новая Windows-сессия требует адресной приёмки зависимых от session свойств.
Неизменная файловая ACL/версия binary не требует автоматически повторять весь прежний аудит.

Статусы:
- DONE — выполнено решение/подготовка/наблюдение; это не обязательно security PASS.
- PASS(scope) — успешный фактический тест в указанной конфигурации.
- PARTIAL — часть нужного свойства доказана, остаток перечислен.
- FAIL — наблюдалось нарушение нужной границы; ниже указан точный scope.
- PENDING — достаточного evidence нет.
- BLOCKED — конкретная попытка остановлена на указанном условии; это не security DENY.
- CONDITIONAL — работа нужна только при указанной потребности; не обязательная новая функция.
- NOT REQUIRED NOW — не требуется при явно принятых условиях.

Ссылки E01–E44 ниже — локальные ссылки этого плана на evidence, а не новые Need/FR/Finding ID.
Для источников с несколькими историческими статусами применяется последний подтверждённый result,
а не более раннее staged/PENDING описание. Raw JSON и фактический output приоритетнее прежнего общего заголовка.

## Цель и принятые условия

Нужен Windows-инструмент ChatGPT под отдельным non-admin SID1009:
PowerShell, Python, Node, Git, свой Edge/CDP и согласованные файлы.
Защищаются owner private data, credentials, GUI/clipboard, runtime и управляющие интерфейсы.
Fortis Repo остаётся основной средой разработки. Итоговый HOST-инструмент — G2; прежний owner HOST выведен из работы по согласованному шагу E43. Восстановление E42 сохранено; старые чаты не удалялись.

DONE: пользователь явно принял ежедневный ручной вход в FortisHostG1, запуск G2,
возврат в alexa с открытой guest-сессией. Несколько минут допустимы; длительность пока не измерена.
Автозапуск до guest login после cold boot — NOT REQUIRED NOW.
Это заменяет прежний HARD PRODUCT GATE без ежедневного Fast User Switching.

Две приёмки различаются: OS-изоляция самого G2 и отсутствие обхода через другие tools чата.
Одна не доказывает другую. Все будущие consequential изменения остаются Candidate до отдельного решения.

## Целевая замена HOST на G2 — уточнение 2026-10-16 03:35

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
Адресная G2 ACL regression позднее закрыта E26; lifecycle baseline/negative control подготовлены E27.
Normal stop/recovery позднее принят E28; E29 позднее закрывает один failure case; продолжать только применимые boundary gates с переиспользованием E18–E29. Изменения live routes и остановки этим уточнением ещё не выполнены.
G3 BLOCKED; G4–G6 не приняты.

## Целевая политика: что разрешено и что защищаем

| Область | Разрешено G2 | Защищаемая граница |
|---|---|---|
| GUI, экран, clipboard | Свои guest GUI/экран/clipboard, включая нужные тесты на synthetic окне/маркере | GUI/экран/clipboard основной сессии alexa, включая обычные окна без elevation |
| Процессы и handles | Управление своими guest процессами и допустимый обмен handles внутри guest | Handles, дающие запрещённые owner process/token/GUI/file возможности; сам по себе same-SID DUP_HANDLE не FAIL |
| Браузер | Свой профиль, собственные разрешённые web sessions, CDP и нужные окна | Личный browser state/cookies/credentials владельца и owner debug control |
| Файлы и приложения | Согласованные рабочие roots, свои temp/cache/output и необходимые installed programs | Protected owner/private/credential/backup roots; shared runtime без изменения |
| Credentials | Отдельные G2 credentials для согласованных задач | Owner credentials; собственный ключ G2 не обещаем скрывать от кода того же SID |
| Сеть и localhost | Нужный интернет, собственные local servers/debug ports и безопасная диагностика | Опасные owner admin/IPC/service функции и чувствительные owner данные |
| Обмен с владельцем | Явно переданный выбранный фрагмент/файл через согласованный канал | Постоянный свободный доступ к owner clipboard/files/API под видом обмена |
| Ручное переключение Windows | Ожидаемый ежедневный вход и возврат в alexa | Незаметное управление owner input/окнами из гостевой сессии |

Headless и свежий temporary browser profile — безопасные условия synthetic tests.
Они не запрещают рабочие окна, длительно живущий собственный browser profile, cookies и результаты G2.
Cleanup удаляет собственные тестовые объекты и то, что по сценарию должно закончиться;
он не должен уничтожать рабочие результаты, запланированные guest servers и persistent profile.

Инженерные механизмы выбираются по результату: отдельный supervisor/Job/broker не обязательны
сами по себе. Для временных тестовых процессов нужен надёжный bounded cleanup;
можно использовать уже проверенный Job. Вторая private station нужна только при доказанном
недостатке выбранной отдельной Windows-сессии.

## Что исправлено после проверки необходимости

- Явно разделены ALLOW собственных guest GUI/clipboard и DENY owner GUI/clipboard.
- Whole-chat isolation оставлена отдельной гарантией; её отсутствие не обнуляет OS-изоляцию G2
  и не требует глобально отключать используемый для разработки Repo.
- Own-process handles, полезная сеть, safe health и рабочие guest credentials не запрещаются избыточно.
- Blanket admin-GET-DENY заменён целью защитить dangerous owner functions и sensitive data;
  safe GET может быть ALLOW, если его безопасность обоснована и версия соответствует reviewed source.
- Полное перебирание HTTP routes × methods не является обязательным новым тестом неизменного runtime:
  используются pinned artifact/source graph и уже пройденные fixtures; дополнительные cases условны.
- Из очереди убрана обязанность добиться успеха именно Get-SmbConnection и вводить универсальный ACL manager.
  Требуется достоверный вывод о фактическом доступе, а не успех конкретной диагностической команды.
- Проверочный запуск конечной chain допустим как отдельное контролируемое испытание после source review
  и согласования конкретного запуска, если оно требуется. Нельзя требовать evidence этой chain до её первого запуска.
  Production acceptance остаётся после закрытия применимых обязательных Evidence Gaps.
- Ручной start/stop является достаточным Candidate. Новый supervisor/restart engine не создаётся автоматически.
- Сроки и количество минут остаются фактической оценкой после цикла; stopwatch не самостоятельный security gate.

## Сводка по прежним восьми пунктам

| Пункт | Уже закрытая часть | Что остаётся |
|---|---|---|
| 1. ChatGPT routes | Маршруты исследованы; широкий обход в прежнем контексте подтверждён; ручной вход принят | При необходимости гарантии всего чата — ограниченный контекст; OS-приёмка G2 принимается отдельно |
| 2. GUI/clipboard | Own window/browser E20, own clipboard E22; owner fresh-open station DENY E21, selected owner DUP_HANDLE DENY E22, handles/inheritance E23/E24 | 2.5/2.6 PARTIAL: concrete bridges/owner API и явные gaps; без повторения own positives или exhaustive Native audit |
| 3. CLI/browser | Actual guest PowerShell/Node/Python/source iteration E18/E19, synthetic Git E19 и browser/CDP/storage E20 PASS(scope) | Новые Windows project scopes — по реальной задаче; не повторять Git/browser без нового gap |
| 4. Owner API | Repo реально переведён на narrow runtime E38; native MCP/selected boundary PASS, automatic source monitor E39 | E43: old HOST закрыт, G2/Repo after-check PASS(scope); его migration не нужна |
| 5. Services/IPC/SMB | E03 rights/tasks/pipes; E30 service source; E31/E32 namespace controls; E33 selected TCP; E41 known Snapshot Broker78 DENY5 и service-account correction | Concrete changes/routes — адресно; source/binary/unknown IPC limits перечислены. Не generic scan/fuzzing |
| 6. Native G2 | Guest Session2/non-admin native MCP/CLI и pinned chain подтверждены E18–E28; normal entry/stop/recovery PASS(scope) E28 | E43: bounded baseline/initial scope приняты; universal completeness — Limitations, без повторного provisioning |
| 7. Files/policy | Workspace/runtime/root controls сохранены; E40 selected owner files/backups130 DENY5, E41 broker control path mutation DENY | E43: baseline принят; новые assets/grants по задаче, independent Repo/whole-chat отдельно |
| 8. Daily/recovery | Actual reboot/manual start reused E20/E28; normal stop/restart E28 и один synthetic MCP-peer failure E29 PASS(scope) | E43: manual workflow принят(scope); произвольный crash/logoff не принят, нового reboot/fault test нет |

## 1. ChatGPT routes и условия — закрыть обход через другой инструмент
Необходимость: actual route restriction обязательно для фразы «весь чат изолирован».
Для отдельной OS-гарантии G2 это независимое условие, не запрет пользоваться owner Repo для разрешённой разработки.
Цена остатка: проверка доступного продуктового режима при выборе этой гарантии, возможно действие пользователя; Windows restart не нужен.

| ID | Подпункт | Статус и доказательство | Оставшаяся работа / критерий |
|---|---|---|---|
| 1.1 | Ежедневный login/start/switch-back допустим | DONE — решение пользователя; ручной сценарий принят(scope) E43 |8.3 подтверждён E18/E20/E28; числового time gate нет, stopwatch test не нужен |
| 1.2 | Выяснить, доступны ли owner routes в старом контексте | DONE; результат для изоляции FAIL — owner HOST и Repo реально вызывались, E01 | Не делать заново общий route inventory ради того же вывода |
| 1.3 | Проверить, ограничивает ли @G2 или обычный permissions mode весь чат | DONE в исследованном scope — выбора @ и confirmations недостаточно, E01 | Не считать инструкцию модели обязательным deny |
| 1.4 | Получить и проверить отдельный контекст без исполняемых owner routes | PENDING для whole-chat guarantee | Использовать доступное продуктовое ограничение, если требуется изолировать весь чат; один tools/list не доказывает постоянный запрет. Недоступный режим — ограничение этой гарантии, не причина отменять OS-исследование G2 |
| 1.5 | Сохранить старые чаты и подключения | PASS(scope) в предыдущих проверках, E01/E02/E06/E08 | При будущих изменениях не отключать plugins глобально; проверять затронутый route адресно |

Угроза: чат обходит SID1009 через независимый owner инструмент.
При невозможности 1.4 можно продолжать безопасные synthetic исследования OS-границы G2,
но нельзя объявлять весь контекст изолированным.

## 2. GUI/clipboard — доказать owner boundary в выбранной session
Необходимость: обязательно проверить нужные guest capabilities и owner boundary.
Цена остатка: один подготовленный pinned user-local сценарий с положительными и отрицательными контролями.

| ID | Подпункт | Статус и доказательство | Оставшаяся работа / критерий |
|---|---|---|---|
| 2.1 | Отдельная guest Windows session, точный SID и non-admin | PASS(scope) — guest Session3, owner Session2, E10/E11/E12 | При каждом запуске выяснять actual SessionId; номер 3 не зашивать |
| 2.2 | Собственная WinSta0 и station metadata гостя | PASS(scope) — name/visibility/enumeration, E11 | Не повторять names-only inventory как доказательство owner DENY |
| 2.3 | Synthetic private station/desktop deny | PASS(scope) — девять fresh-open DENY на тестовых объектах, E07 | Переиспользовать методику; это не owner-object DENY в новой session |
| 2.4 | Моделируемая защита owner WinSta0/Default | PASS(scope) только AccessCheck предложенной DACL в памяти, E07 | Live owner ACL не применялась; текущая session-based схема не требует автоматически её менять |
| 2.5 | Запрет owner screen/clipboard/window capabilities из новой guest session | PARTIAL, E21 — 10 own positives PASS; owner station четыре rights DENY5; шесть desktop paths blocked at station root5; target corroborated через HOST до/после | Не выдавать root denial за individual desktop DACL DENY. Fresh-open scope доказан; existing/inherited/duplicated handles и clipboard bridges — 2.6. Owner contents не читать |
| 2.6 | Нет handles/bridges с запрещёнными owner capabilities | PARTIAL universal, E22–E24/E41/E43; selected owner DUP_HANDLE DENY, launch/inheritance reviewed, known Broker denied; bounded baseline принят | Legacy HOST закрыт E43.184 PSS entries/relative desktop names и clipboard completeness остаются Limitations. Новый аудит по конкретной существенной поверхности; NOT_CONFIGURED не disabled |
| 2.7 | Новая вторая приватная station в guest logon | BLOCKED в старой попытке: Win32 183, E17; CONDITIONAL для дальнейшей работы | Не чинить ради самого имени station. Возвращаться только если отдельная session не обеспечивает нужную границу |
| 2.8 | Собственные guest GUI/clipboard доступны | PASS(scope), E20/E22 — own Session2 window create/visible/destroy и authorized clipboard exact-marker roundtrip/cleanup подтверждены | Закрыто в этом scope. Prior guest contents заменены с явного разрешения, не читались; owner contents не затронуты. Не повторять без нового вопроса |

Исторический FAIL: в прежней общей owner/guest session подтверждались clipboard/screen/WRITE_DAC ALLOW, E05.
Это причина смены схемы, а не доказательство такого же доступа из новой Session3.

**Историческая подготовка Native-сценария:** дальнейшие PENDING/ошибки этого абзаца относятся к прежней диагностике. Поздние E21/E22/E24/E41 и статусы таблицы выше имеют приоритет; не запускать этот цикл заново по старому тексту.
Подготовлен [pinned диагностический сценарий](G3_SESSION_GUI_BOUNDARY_DIAGNOSTIC_2026-10-15.md) для 2.5, 2.8 и части 2.6.
PowerShell AST, C# language version 5, captured-bytes Validate и шесть name-guard checks проверены в Repo.
Первый Windows OwnerWitness предыдущего pin скомпилировался, но остановился на предположении о полном desktop path;
наблюдены owner Session1 / WinSta0 / сырое `\Default`. Исправленный station-bound lookup / schema 2:
Windows OwnerWitness текущего pin получен 21:51:41 Asia/Bangkok — SID1001, Session1, PID/creation time и имена подтверждены.
GuestProbe BLOCKED на HoldProcess / QUERY_LIMITED_INFORMATION; точный Win32 и caller stage неизвестны.
Inline recovery ошибочно зависел от прежних переменных; автономный recovery block подготовлен в диагностической инструкции.
Owner native capability controls PENDING; own guest window PASS, clipboard SKIPPED_NONEMPTY (E20).
Owner metadata без необходимости не повторять.
Это metadata evidence и ошибка теста, не owner DENY; статусы подпунктов не меняются.
Сначала owner metadata witness, затем guest self/missing controls и owner open/close probes.
Native cross-session метод экспериментальный; INCONCLUSIVE не закрывает gate.
Существующие handles конечной MCP chain и clipboard bridges этим исходником не инвентаризируются.
Один API с именем WinSta0 не обещает полной приёмки; статусы таблицы выше не изменились.

## 3. CLI/browser — проверить только отсутствующую совместимость
Необходимость: обязательно для функциональности; часть проверок ниже уже завершена.
Цена остатка: один компактный synthetic Session3 сценарий; без настоящего tunnel key.
Чистый временный профиль нужен для воспроизводимого теста, а рабочий guest profile может быть persistent.

| ID | Подпункт | Статус и доказательство | Оставшаяся работа / критерий |
|---|---|---|---|
| 3.1 | PowerShell/Node/Python под SID1009, descendants и workspace | PASS(scope) прежних MCP/private fixtures, E01/E05/E06/E07 | В новой Session3 связать identity и минимальные нужные команды в одном gate; не повторять прежнюю полную программу отдельно |
| 3.2 | Полный Edge CDP/DOM/localStorage со своим профилем и sandbox | PASS(scope) старых baseline/private fixtures, E05/E07 | Это не полностью PENDING; переносится методика, нужна приёмка в новой session |
| 3.3 | Session3 Local mutex и Edge startup/CDP port-file | PASS(scope), E10/E12 | Не повторять отдельные smoke: они не добавят protocol evidence |
| 3.4 | Session3 Job stop и profile cleanup | PASS(scope) для временного Edge, E10 | Не выдавать за cleanup всего постоянного G2; повторить лишь как часть нового расширенного сценария |
| 3.5 | CDP commands, synthetic DOM/storage, CLI chain в новой guest session | PASS(scope), E20 — approved corrected Session2 repeat exit0; CDP DOM query, exact DOM/localStorage, new document/storage after reload, default sandbox и temporary Job/profile cleanup подтверждены | Не повторять неизменный smoke без нового вопроса. Это не owner boundary и не long-lived G2 stop/cleanup |
| 3.6 | Git выполняет необходимую задачу под guest | PASS(scope), E19 — own synthetic init/add/commit/status, clean worktree и cleanup; network/auth не проверялись | Одна локальная synthetic git операция в своей workspace. Сетевой push/auth нужен только для реальной Git network задачи; отдельный большой аудит не требуется |

Защита 3.2–3.5: собственный browser state, отсутствие случайных owner credentials и оставленного debug endpoint.
Остальная польза: доказать, что выбранная изоляция не требует позднего ослабления прав.

## 4. Owner API — защитить опасные функции и чувствительные данные
Необходимость: защитить применимые сохраняющиеся owner API и исключить обход при итоговом переходе.
Для заменяемого HOST достаточно согласованного вывода прежнего owner процесса и проверки результата;
его отдельная runtime-only миграция сейчас не требуется. Repo остаётся отдельным контуром.

| ID | Подпункт | Статус и доказательство | Оставшаяся работа / критерий |
|---|---|---|---|
| 4.1 | Установить достижимость owner API | DONE — guest Session3 GET200 на двух owner listeners без credentials, E13; прежний тест admin-GET DENY дал FAIL | Не повторять тот же GET без новой причины. Достижимость не доказывает owner write/RCE; любой GET200 сам по себе не является нарушением уточнённой политики безопасной диагностики |
| 4.2 | Найти/получить официальный narrow runtime и проверить artifact | DONE/PASS(scope) — v0.0.15 установлен side-by-side, SHA/manifest/version и guest ACL проверены, E08 | Не скачивать/устанавливать заново. Перед apply проверить сохранность pinned bytes |
| 4.3 | Доказать MCP и выбранные admin/Harpoon 404 в isolated runtime fixtures | PASS(scope) — два isolated Windows fixtures, guest negative tests, E08 | Не повторять неизменный fixture целиком без нового вопроса; source review E15 уточнил реальные routes, см. 4.7 |
| 4.4 | Убрать ненужный additional Harpoon HTTP transport при inherited env | PASS(scope) — пустой flag override проверен, E08 | Сохранить проверенное отключение ненужного privileged transport; /harpoon/mcp учитывать отдельно. Нужный собственный local API/CDP не запрещается автоматически |
| 4.5 | Подготовить candidates и выполнить owner Preview | DONE/PASS(scope) — syntax/hash gates и actual Preview: все три live файла BEFORE, E08/E14 | Это не production switch. Общий Apply меняет три launchers — не использовать для one-route scope |
| 4.6 | Исследовать реальные full-client routes и узкий config вариант | DONE source-only — E15, закреплённый commit | Не начинать аудит заново. Live full EXE ↔ source/version соответствие не установлено заново |
| 4.7 | Достаточность negative coverage выбранного решения | PASS(scope) выбранных реальных routes/fixtures и source graph, E08/E15; дополнительные cases CONDITIONAL | Для того же pinned narrow artifact с исключённым admin-модулем не требуется перебрать все paths × methods заново. Добавлять тест, только если не закрыт вопрос registration/transport/version либо выбран новый auth gate. 404 несуществующего пути отдельно доказательством не является |
| 4.8 | Совместимость сохраняющихся owner routes и итоговый HOST-переход | PASS(scope), E38/E39/E43 — Repo narrow/native/monitor source, G2 initial scope и old HOST retirement/after-check подтверждены | Старый dashboard не доставлен, без потребности не gate. HOST migration не нужна; новые routes — адресно |
| 4.9 | Scoped переход и восстановление без смены остальных routes | PASS(scope) Repo, E36/E38 — guarded two-file Apply, backup identity до stop, selected StopAccess старого PID и actual narrow start/MCP выполнены; HOST/G2/container fingerprints сохранены. Live rollback не выполнялся, recovery проверен fixtures E36 | Не повторять Apply/restart/rollback ради перечня. BackupPath/SHA256 сохранены в E38 и recovery. Two-file операция не атомарна; unknown DRIFT не затирать. HOST retirement отдельно, all-three Apply не использовать |
| 4.10 | Закрыть применимые owner API пути и принять итоговую границу | PASS(scope) выбранных routes, E38/E43 — Repo narrow/selected admin GET404; old HOST three PIDs gone/8080 absent; bounded baseline принят | Не universal/whole-chat PASS. Credentials/connector не отозваны; ручной relaunch вновь откроет route. Repo RW mounts/1.4 отдельно |

Narrow runtime уже раньше применялся к G2 и прошёл реальный MCP acceptance, E06.
Это не owner HOST/Repo switchover и не доказательство текущей Session3 acceptance.
OPENAI_ADMIN_KEY относится к удалённому control plane, а не local adminui.
Proxy с оставленным прямым full TCP listener не исправляет проблему.
Live unsafe methods, export/stream probes, blanket firewall и одновременный restart обоих контуров не входят в приёмку.
Connection failure, 405 либо 500 не равны authorization DENY. Safe health/необходимая диагностика допустимы;
details/metrics требуют отдельной оценки состава, а не автоматического запрета всего listener.
В reviewed source GET /api/log-level возвращает current/supported logging levels без изменения состояния:
это Candidate для safe diagnostic ALLOW при подтверждённом соответствии live binary и reviewed source.
PUT этого пути меняет owner настройку и оценивается отдельно. Чувствительные status/logs/export/Codex
и управляющие handlers защищаются по данным и эффекту, а не только по названию /api.
Исторический FAIL E13 сохранён как результат более строгого admin-GET-DENY теста;
он не становится доказательством RCE и не обязывает запрещать безопасную диагностику.
В этом пересмотре live response bodies и mutating owner calls не читались/не отправлялись.

## 5. Services/IPC/SMB — оставить в работе только известный остаток
Необходимость: обязательны применимые открытые пути; full scan всей Windows не требуется.
Цена остатка: metadata/source и synthetic targets; изменения прав/сети отдельно согласуются.

| ID | Подпункт | Статус и доказательство | Оставшаяся работа / критерий |
|---|---|---|---|
| 5.1 | Четыре выбранных scheduler tasks | PASS(scope) — ACL read/write/execute/delete/WriteDac/WriteOwner DENY, E03 | Закрыто для этих четырёх объектов; Run/Update не вызывались. Не повторять без drift |
| 5.2 | Docker pipes docker_engine и dockerDesktopLinuxEngine | PASS(scope) — read/write handles DENY5, E03 | Закрыто для этих pipes; не расширять вывод на весь IPC |
| 5.3 | Управление GoodbyeDPI/MySQL80 стандартными service rights | PASS(scope) — start/stop/change-config/pause/delete/ACL mutation DENY, E03 | Не повторять эти denied rights; query права были разрешены и сами по себе не FAIL |
| 5.4 | SERVICE_USER_DEFINED_CONTROL этих двух служб | PARTIAL, E03/E30/E41 — ALLOW; MySQL matching8.0.44 source custom codes status-only. Actual MySQL NetworkService, GoodbyeDPI Stopped/LocalSystem. E30 LocalSystem inference для MySQL исправлен | Source/binary binding неполон, особенно GoodbyeDPI. Нет доказанного dangerous custom effect; дополнительная проверка при конкретном relevant version/path/handler изменении. Не live fuzzing и не ACL denial только из-за ALLOW |
| 5.5 | Защита service executable | PASS(scope) для MySQL binary/bin; для GoodbyeDPI PATH_NOT_FOUND, E03 | Missing path не равен DENY. GoodbyeDPI уточнять лишь если этот service path применим к угрозе |
| 5.6 | Junction/extended/UNC bypass на synthetic paths | PASS(scope), E04/E31 — junction read/write и 135 normal/extended/localhost C$ capability opens RW/RO/DENY; одинаковые ожидаемые права | Synthetic scope закрыт; protected contents/ACL не менялись. Не повторять матрицу; реальные targets и SMB identity относятся к 5.7 |
| 5.7 | C$ и SMB effective access выбранных protected roots | PASS(scope), E31/E32 — synthetic matrix и восемь выбранных runtime объектов: 24 read/list ALLOW, 104 mutation DENY5 через extended/localhost C$ | Scope ограничен перечисленными объектами; не весь C:/shares/личные данные. Owner assets/backups остаются 7.6, IPC/API — 5.8. SMB identity отдельно не установлена и не нужна для этих effective rights; не повторять матрицу без drift |
| 5.8 | Прочие owner IPC/API/debug endpoints | PARTIAL universal, E33/E38/E41/E43 — selected TCP absent, Repo narrow, Broker78 DENY5; old HOST chain/listener закрыты | Не все неизвестные IPC/handles исключены. Bounded baseline принят с Limitations; новые конкретные routes — адресно, без автоматического полного scan |

## 6. Native G2 — принять существующий инструмент в новой session
Необходимость: обязательно; это перенос приёмки, а не создание G2 с нуля.
Цена остатка: минимальный session-compatible запуск и один user-local старт с отдельным key.
Сначала рассмотреть обычный guest-local ручной запуск. Отдельный постоянный supervisor/IPC broker
потребуется только при доказанном недостатке запуска, остановки либо cleanup.

| ID | Подпункт | Статус и доказательство | Оставшаяся работа / критерий |
|---|---|---|---|
| 6.1 | Отдельный G2 profile/auth/non-admin tunnel → gate → Node chain | PASS(scope), E01/E06 | Не provision заново и не копировать owner auth |
| 6.2 | Native MCP initialize/tools/list/tools/call и file/shell матрица | PASS(scope) прежнего G2, E06 | В новой session нужен compact real-chain regression, не полное повторение G1/G2 |
| 6.3 | UI metadata/resources и env forwarding | PASS(scope) прежних tests: 26 tools, UI metadata 0/resources 0, выбранные env names absent; live ответы без UI metadata, E06 | Сохранить принятые UI settings. Это не запрет guest OS GUI. Проверять отсутствие неожиданной передачи owner credentials; нужные собственные guest credentials допустимы. Wrapper не hard boundary против same-SID кода |
| 6.4 | Достаточный session-compatible entry/stop | PASS(scope), E18/E20/E28 — ordinary guest entry, normal manual stop и restart; old baseline runtime/Python/Node gone, new pinned chain/MCP работают | Не повторять normal cycle без drift. Arbitrary future descendants и forced crash не покрыты; при доказанном недостатке выбирать механизм cleanup, а не требовать Job/supervisor заранее |
| 6.5 | Полный G2 runtime в отдельной guest session | PASS(scope) начального сценария, E18–E29/E40–E43 — native identity/pins/MCP/files/CLI/browser/Git, scoped protection/lifecycle, accepted baseline и after-check | Universal отсутствие owner capabilities не доказано.2.5/2.6/5.4/5.8/7.6 limits сохранены. Новые проекты/программы/посредники — адресно |
| 6.6 | Отсутствие лишних listeners/fallback | PASS(scope), E18–E19 — Session2 narrow runtime pin/empty transport, три chain PIDs: один diagnostic TCP listener, selected GET 200/404; не exhaustive audit | Проверить конечный запуск, сохранить narrow runtime и transport settings; не fallback на full binary автоматически |

Production acceptance требует закрытых применимых G3 gates и конкретного решения владельца.
Контролируемый user-local проверочный запуск 6.5 может быть нужен для доказательств 2.6/6.5/8:
не требовать их заранее и не запускать обычные непроверенные workloads до приёмки.
Безопасные isolated/no-real-key сценарии из 2–3 можно выполнять раньше после source review.
Одна такая испытательная серия должна закрывать несколько подпунктов без лишних повторных стартов.

## 7. Files/policy — сохранить доказанные ACL и принять нужный baseline
Необходимость: baseline acceptance обязательно; новые project grants — CONDITIONAL.
Цена остатка: выбранные synthetic проверки, а не массовая правка owner home.
Workspace — начальная рабочая область, а не запрет guest own AppData/cache и installed apps.
Нужные рабочие roots/зависимости разрешаются по задаче без открытия всего owner profile.

| ID | Подпункт | Статус и доказательство | Оставшаяся работа / критерий |
|---|---|---|---|
| 7.1 | Immutable shared runtime | PASS(scope), E04/E08/E26 — четыре DACL и прежний 22758 scan; текущая G2 regression восьми объектов: 48 mutation DENY5, 16 read/execute ALLOW | Не повторять Apply/полный scan без drift; E26 не расширять до нового полного аудита |
| 7.2 | Synthetic RW/RO/DENY через file/PowerShell/Python | PASS(scope), E01/E04/E06 | Использовать baseline; в новой final chain достаточно адресной regression |
| 7.3 | Owner private root/key-directory handles | PASS(scope) — read/write opens DENY к home/Repos/Workfiles/AppData/Documents/Desktop/Downloads/.ssh/.aws/tunnel key dir, E05 | Не читать contents. Это не рекурсивный аудит children/links. Missing .azure/.kube/.git-credentials не считать DENY |
| 7.4 | Guest Workspace, scratch/browser-profiles/results и file allowlist | DONE/PASS(scope): созданы, write/readback/cleanup и вне-guard отказ проверены, E05 | Не создавать заново. Allowlist изменяем самим SID и не ограничивает arbitrary shell как OS boundary |
| 7.5 | Принять минимальный рабочий scope | DONE/ACCEPTED(scope), E42/P01 принято в E43: Workspace, own GUI/clipboard/browser/state/credentials/network/CLI | Новые owner grants только по задаче; Repo RW/whole-chat1.4 отдельно. Дополнительные roots для принятого старта не нужны |
| 7.6 | Конкретные protected assets/backups/policy через relevant routes | PARTIAL overall; PASS(scope) E40 — семь реальных файлов (profile/key/launchers/two backups/Edge Local State) и два backup parents:130 normal/C$ opens DENY5, включая DELETE_CHILD;15 own controls ALLOW и cleanup PASS. E05 root evidence сохранено | Для выбранного набора ACL менять не требуется. Прочие assets/backup locations не выбраны; не требовать произвольный private scan или restore/media audit без конкретной цели. Independent Repo RW/whole-chat1.4 остаются отдельными; source policy не является mandatory enforcement |
| 7.7 | Универсальный ACL manager/GUI для grants | NOT IMPLEMENTED; CONDITIONAL, E16 | Не делать prerequisite baseline G2. Если понадобится recurring изменение scopes — отдельный минимальный Proposal |
| 7.8 | Новые ACL/mount grants | CONDITIONAL | Только при доказанной потребности: exact Preview/backup/rollback и отдельное решение. Существующие достаточные права сохранять |

Windows SID1009 DENY не ограничивает независимый owner Repo RW bind.
Для защиты всего чата сначала нужен пункт 1.4 либо явное ограничение заявляемого scope.

## 8. Daily/recovery — дополнить проверенный stop/cleanup, не начинать заново
Необходимость: конечный ежедневный цикл обязателен; unattended startup не нужен.
Цена остатка: совмещённый сценарий с пунктом 6, а не отдельная серия одинаковых запусков.

| ID | Подпункт | Статус и доказательство | Оставшаяся работа / критерий |
|---|---|---|---|
| 8.1 | Scoped stop G2 без остановки owner HOST/Repo | PASS(scope), E02/E28 — actual new-session baseline three processes и old listener gone; owner PID/creation fingerprints сохранены, Repo MCP ответил | Закрыто для этого normal cycle. After-check point-in-time, не continuous uptime/новая owner HTTP health acceptance; не повторять без drift |
| 8.2 | Wrapper backup restore | PASS(scope) — восстановление на отдельной RW копии, hash/self-test/cleanup, E02 | Не production rollback ACL/profile/key. Не запускать live ACL rollback ради повторения этого PASS |
| 8.3 | Guest login → start → switch-back → полезная MCP задача | PASS(scope), E18/E20/E28 — user-reported manual cycle, новый guest MCP/CLI/baseline read работает; owner active console1 наблюдалась в after-check | Длительность не измерялась; числовой time gate не задавался. Ручной вход принят, дополнительный stopwatch/relogin test не нужен ради прежнего вывода; full G6 отдельно |
| 8.4 | Failure/cleanup новой цепочки | PASS(scope), E28/E29 — normal stop/manual recovery и controlled synthetic MCP-peer exit37 на actual runtime, самостоятельный runtime exit/cleanup; real G2 unchanged | Не actual Python/DC crash/runtime kill/logoff. Exit0 runtime не доказывает успех задачи. Дополнительный fault test только при конкретной оставшейся угрозе; новый supervisor/restart engine не требуется |
| 8.5 | Reboot/relogon и повторный ручной старт | PASS(scope), E20/E28 — actual user reboot/manual startup и последующий normal guest stop/restart с рабочим MCP подтверждены | Не повторять reboot ради прежнего startup evidence. Полная G6 acceptance и crash/logoff cleanup из этого scoped PASS не следуют |
| 8.6 | Сохранность owner инфраструктуры | PASS(scope), E02/E04/E06/E07/E28 — owner HOST/Repo creation fingerprints сохранены после G2 cycle; Repo MCP ответил | После consequential changes проверять только затронутые процессы/routes и ожидаемые неизменные соседи; не объявлять непрерывный мониторинг по отдельному sample |
| 8.7 | Понятные operation/recovery инструкции конечной версии | DONE/ACCEPTED(scope), E42/E43 — pinned entry/normal stop/recovery, actual old HOST retirement/after-check и local recovery описаны | Old HOST live recovery не репетировался. Arbitrary crash/logoff не принят; не повторять reboot/normal cycle без drift. Commit/push не требуется |

## Candidate Proposal P01 — достаточность тестов и меньше ручных переходов

[Source review, Findings и Proposal P01](G3_GUI_BOUNDARY_METHOD_REVIEW_2026-10-15.md) подготовлены по запросу пользователя.
Предложено опереться на документированную модель Windows и проверить её применение к конечной G2 chain,
сначала обеспечив существующий G2 guest-local route для file/CLI итераций после одного ручного старта.
Отладка undocumented Native matrix и owner QUERY metadata не должна автоматически быть prerequisite
для независимых own guest positive tests. Возможная замена критерия 2.5 — Candidate, не закрытие gate.
Сейчас прежний recovery/Native цикл на паузе; 58 decision rows и их security acceptance статусы сохранены.

## Scope принят, прежний owner HOST остановлен — E43, 2026-10-16

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

Текущий согласованный переход завершён. PARTIAL2.5/2.6/5.4/5.8/7.6 сохраняют Evidence
Limitations, не назначают автоматически exhaustive audit. Новая существенная поверхность/изменение
или отдельная потребность whole-chat/personal-security требуют конкретного нового scope.

## Точка продолжения 2026-10-16

Ниже — история browser/recovery; текущий итог E43 выше имеет приоритет.

Переиспользовать E18–E20. Не повторять уже пройденные Git, initial Edge startup, temporary Job cleanup
и own window checks без нового вопроса. После фактической user reboot обычный G2 MCP/CLI старт
в Session2 подтверждён; E28 позже закрывает normal entry/stop/recovery 6.4/8.3 и scoped reboot/start 8.5; E29 позднее закрывает один scoped failure case 8.4; общий G6 не принят.
Старое PDM не является отдельным G3 gate; экспорт AV отчёта — дополнительная диагностика.
После уточнения пользователя сделана попытка доставки двух pinned sources для продолжения 3.5.
Tool auto-review сначала отклонил её до Windows исполнения. Пользователь явно разрешил повтор
в 02:34:58; та же G2 операция прошла новую проверку: оба pinned source файла записаны с read-back,
browser smoke 02:36:41 завершился exit0/PASS(scope). Прежний отказ не обходили другой кодировкой/tool.
3.5 закрыт в указанном scope; clipboard затем принят E22, stop/recovery E28, controlled failure E29; продолжать только применимые owner-boundary gaps.
Точный PDM trigger и true/false positive не установлены; Windows Event Log дополнительных данных не дал.
Owner capabilities (2.5/2.6) и relevant owner API protection остаются PARTIAL/PENDING. ACL regression принята E26, normal stop/cleanup E28 и один failure case E29; не считать их снова pending.

## Реальный дальнейший порядок работ

1. **DONE E43:** E42/P01 scope/bounded baseline приняты; собственные guest возможности сохранены.
2. **DONE E43:** old HOST retirement и after-check выполнены, G2/Repo сохранены.
3. **DONE(scope):** инструкция и итог согласованы. Далее обычная работа G2/Repo.
   Новая project access/программа/посредник — конкретная задача и адресная проверка.
   Whole-chat1.4 и полная G5 отдельно; universal PASS не заявляется.

Не повторять Stop helper/all-three Apply/reboot/tests ради перечня. После uncertain mutation сначала
проверять effect. Новые ACL/mount/network/task/service/автозапуск требуют отдельного решения.
Old HOST credentials/connector не отозваны; локальный relaunch по E42 вновь открывает широкий route.

## Что не возвращаем в обязательный план

Запрет собственных guest GUI/clipboard, всех guest handles/credentials/network, обязательный headless
и обязательное удаление рабочего browser profile не входят в целевую политику.
Новый supervisor/Job/broker, автоматическое восстановление и exhaustive route/method матрица
не являются самостоятельными целями; нужны только для конкретного нерешённого требования.
Task Scheduler S4U/PASSWORD, autologon, SYSTEM broker и запуск до guest login — NOT REQUIRED NOW.
Вторая private station — CONDITIONAL, не незакрытая функция ради самой реализации.
Полный повтор 22 758 scan, G1/G2, mutex smoke, Edge port-file smoke и старых неизменных fixtures
не является следующим шагом без drift либо конкретного нового Evidence Gap.
Полный аудит всей Windows/всех личных файлов не был выполнен и этим планом не заявляется.
Его нельзя подменять ограниченным PASS, но он также не должен бесконтрольно расширять текущий scope.

## E44 — bounded Repo metadata и документы

[Итог](ISOLATION_GUIDE.md) разделяет verified/accepted/limitations, сохраняет историю,
содержит 10 шагов повторения. [E44](G3_DOCS_CONSOLIDATION_AND_REPO_BOUNDARY_2026-10-16.md)
проверяет Repo UID/caps/mount/Bridge source-live pins, не universal Docker/Windows security.
Решение E43 и 58 критериев не изменены; runtime/права/туннели не менялись.

## Реестр evidence

Файлы находятся в /workspace/repos/tunnel/docs. ID внутри этого документа фиксируют источник,
а не подтверждают live-состояние на момент каждого будущего запуска.

| ID | Источник | Что принимаем из него |
|---|---|---|
| E01 | G2_E_F_EVIDENCE_2026-10-13.md | Actual identity/file matrix и наблюдавшиеся owner routes |
| E02 | G2_G_EVIDENCE_2026-10-13.md | Scoped stop, wrapper restore на копии, owner preservation |
| E03 | G3_READONLY_EVIDENCE_2026-10-13.md + .json | Service/task/Docker rights; pre-ACL FAIL хранится как история |
| E04 | G3_POST_ACL_VERIFICATION_2026-10-13.md + .json | Applied runtime ACL, 22 758 scan, junction и namespace results |
| E05 | G3_BASELINE_HISTORY_AUDIT_2026-10-13.md + .json | Workspace/allowlist, owner-directory handles, старый Edge и общий WinSta0 ALLOW |
| E06 | G3_G2_RUNTIME_ACCEPTANCE_2026-10-13.md + .json | Actual G2-only runtime/MCP acceptance в прежней конфигурации |
| E07 | G3_WINDOW_ISOLATION_PROTOTYPE_2026-10-13.md + .json | Synthetic private station/CDP, synthetic DENY; in-memory proposed owner ACL |
| E08 | G3_LOCAL_API_RUNTIME_2026-10-13.md + .json | Installed official runtime, два fixtures, env override, ACL, syntax/Preview; ранние rollout предложения исторические |
| E09 | G3_PRIVATE_LAUNCHER_STAGING_2026-10-13.json; G3_PRIVATE_LAUNCHER_QUERY_ONLY_2026-10-13.json | Старые synthetic Job/env/pipe/CAS/validator tests; не acceptance новой guest-session launch |
| E10 | G3_GUEST_EDGE_SESSION3_SMOKE_2026-10-15.md | Actual Session3 startup/port-file/Job/profile cleanup, не полный CDP |
| E11 | G3_SESSION3_STATIONS_READONLY_2026-10-15.md | Actual guest station metadata, не owner GUI DENY |
| E12 | G3_SESSION_BOUNDARY_OUTCOME_DECISION_2026-10-15.md; G3_GUEST_SESSION_MUTEX_TEST_2026-10-15.md | Separate session/mutex facts; старый unattended UX gate заменён текущим решением пользователя |
| E13 | G3_LIVE_OWNER_LISTENERS_2026-10-15.md | Guest Session3 GET200 на двух owner listeners, no body/no writes |
| E14 | G3_OWNER_RUNTIME_ONLY_PREVIEW_2026-10-15.md | Actual all-three BEFORE Preview; не Apply и не compatibility |
| E15 | G3_OWNER_HTTP_API_SOURCE_REVIEW_2026-10-15.md | Pinned source route/guard/config review; не live native evidence |
| E16 | G4_ACCESS_POLICY_PROPOSAL_2026-10-13.md | Design/не реализованный general policy manager, не PASS |
| E17 | G3_GUEST_STATION_EXISTING_OBJECT_2026-10-15.md | Actual CreateWindowStation create-only Win32 183, не DENY и не новая station |
| E18 | [G3_GUEST_MCP_SESSION2_SMOKE_2026-10-15.json](G3_GUEST_MCP_SESSION2_SMOKE_2026-10-15.json) | Actual SID1009/Session2 ancestry/MCP/file/CLI при active console1, lock; первоначальный gate-path gap |
| E19 | [G3_GUEST_MCP_ITERATION_2026-10-15.json](G3_GUEST_MCP_ITERATION_2026-10-15.json) | Repo→G2 source iteration, gate argv/path/hash, local synthetic Git/cleanup и scoped TCP/GET; не owner protection PASS |
| E20 | [G3_GUEST_GUI_BROWSER_POSITIVE_2026-10-16.json](G3_GUEST_GUI_BROWSER_POSITIVE_2026-10-16.json) | Own window PASS, clipboard SKIPPED_NONEMPTY; failed initial DOM/storage smoke, successful test Job/profile cleanup; corrected source in Repo, initial delivery EPERM/PDM и tool refusal сохранены как история; после явного разрешения corrected browser repeat PASS(scope), default sandbox/Job/profile cleanup, G2 после reboot отвечает |
| E21 | [G3_G2_OWNER_GUI_CAPABILITIES_2026-10-16.json](G3_G2_OWNER_GUI_CAPABILITIES_2026-10-16.json) | Final G2 Session2: 10 own positives, owner station four DENY5, desktop paths blocked at station root; owner metadata before/after; clipboard still nonempty; no content reads/capture/input/ACL writes |
| E22 | [G3_G2_CLIPBOARD_AND_HANDLE_GATES_2026-10-16.json](G3_G2_CLIPBOARD_AND_HANDLE_GATES_2026-10-16.json) | Authorized guest clipboard marker roundtrip/cleanup PASS; current selected owner DUP_HANDLE DENY with PID fingerprints; limited bridge metadata; not full handle/bridge exclusion |
| E23 | [G3_G2_HANDLE_INVENTORY_2026-10-16.json](G3_G2_HANDLE_INVENTORY_2026-10-16.json) | Calibrated documented PSS walk selected G2 runtime/Python/Node; resolved stations Session2; empty types/relative desktops remain Evidence Gaps, 2.6 PARTIAL |
| E24 | [G3_G2_LAUNCH_INHERITANCE_2026-10-16.md](G3_G2_LAUNCH_INHERITANCE_2026-10-16.md), [JSON](G3_G2_LAUNCH_INHERITANCE_2026-10-16.json) | Current guest parent/chain/pins and Python defaults; documented cross-session inheritance restriction; source standard-handle path review; no complete broker/owner-API exclusion |
| E25 | [G3_OWNER_ROUTE_COMPATIBILITY_2026-10-16.md](G3_OWNER_ROUTE_COMPATIBILITY_2026-10-16.md), [JSON](G3_OWNER_ROUTE_COMPATIBILITY_2026-10-16.json) | Current owner profile/PID/listener/hash mapping; source monitor/control dependencies; 4.8 PARTIAL, no live cutover |
| E26 | [G3_G2_CURRENT_ACL_REGRESSION_2026-10-16.json](G3_G2_CURRENT_ACL_REGRESSION_2026-10-16.json) | Actual current G2: 48 mutation DENY5, 16 read/execute ALLOW, 12 own controls and Workspace roundtrip/cleanup PASS; no ACL/shared writes |
| E27 | [G3_G2_LIFECYCLE_PREPARATION_2026-10-16.json](G3_G2_LIFECYCLE_PREPARATION_2026-10-16.json), [Runbook](G3_G2_STOP_RECOVERY_2026-10-16.md) | Pinned guest baseline and before-stop negative Verify; actual stop/restart not yet executed |
| E28 | [G3_G2_NORMAL_STOP_RECOVERY_2026-10-16.md](G3_G2_NORMAL_STOP_RECOVERY_2026-10-16.md), [JSON](G3_G2_NORMAL_STOP_RECOVERY_2026-10-16.json) | Actual old three processes/listener gone; new pinned guest chain/MCP; owner fingerprints preserved; normal cycle PASS(scope), forced-failure not tested |
| E29 | [G3_G2_SYNTHETIC_PEER_FAILURE_2026-10-16.md](G3_G2_SYNTHETIC_PEER_FAILURE_2026-10-16.md), [JSON](G3_G2_SYNTHETIC_PEER_FAILURE_2026-10-16.json) | Controlled synthetic MCP peer exit37, actual runtime exits0; Job fallback not used, cleanup PASS, real G2 fingerprints unchanged; 8.4 scoped PASS |
| E30 | [G3_SELECTED_SERVICE_HANDLERS_2026-10-16.md](G3_SELECTED_SERVICE_HANDLERS_2026-10-16.md), [JSON](G3_SELECTED_SERVICE_HANDLERS_2026-10-16.json) | Selected service state/version metadata and primary handler source; no live controls; MySQL custom branch status-only in source, GoodbyeDPI stopped; binary binding remains scoped limitation |
| E31 | [G3_G2_NAMESPACE_CAPABILITIES_2026-10-16.md](G3_G2_NAMESPACE_CAPABILITIES_2026-10-16.md), [JSON](G3_G2_NAMESPACE_CAPABILITIES_2026-10-16.json) | 135 expected capability opens; synthetic normal/extended/localhost C$ права совпали; RW Modify; initial criterion correction retained; 5.6 PASS(scope), 5.7 PARTIAL |
| E32 | [G3_G2_PROTECTED_NAMESPACE_CAPABILITIES_2026-10-16.md](G3_G2_PROTECTED_NAMESPACE_CAPABILITIES_2026-10-16.md), [JSON](G3_G2_PROTECTED_NAMESPACE_CAPABILITIES_2026-10-16.json) | 8 selected runtime objects: 24 read/list ALLOW, 104 mutation DENY5; extended/localhost C$; no content/ACL writes or restart; 5.7 PASS(scope), private assets7.6 separate |
| E33 | [G3_SELECTED_OWNER_IPC_SURFACE_2026-10-16.md](G3_SELECTED_OWNER_IPC_SURFACE_2026-10-16.md), [JSON](G3_SELECTED_OWNER_IPC_SURFACE_2026-10-16.json) | Known owner HOST/Repo TCP listeners unchanged; selected cmd/Node no listeners; no HTTP or changes; 5.8 PARTIAL, owner API gate unremediated |
| E34 | [G3_REPO_API_PROTECTION_PREVIEW_2026-10-16.md](G3_REPO_API_PROTECTION_PREVIEW_2026-10-16.md), [JSON](G3_REPO_API_PROTECTION_PREVIEW_2026-10-16.json) | Repo-only Windows Preview: two BEFORE files/pins/parser PASS; ReadyForApply=false; bounded health source/readyz/metrics assessment; monitor source compatibility; no backup/apply/restart |
| E35 | [G3_REPO_STDIO_READ_SURFACE_2026-10-16.md](G3_REPO_STDIO_READ_SURFACE_2026-10-16.md), [JSON](G3_REPO_STDIO_READ_SURFACE_2026-10-16.json) | Main stdio skips MCP/OAuth probes; presumed readyz error path excluded; metric producers no stdio params/results projection; bridge hashes match; source-scope only, Candidate not deployed |
| E36 | [G3_REPO_GUARDED_MIGRATION_2026-10-16.md](G3_REPO_GUARDED_MIGRATION_2026-10-16.md), [JSON](G3_REPO_GUARDED_MIGRATION_2026-10-16.json), [recovery](G3_REPO_RUNTIME_ONLY_RECOVERY_2026-10-16.md) | Repo-only guarded wrapper/core/test; Windows32/32 fixtures, default owner Preview BEFORE; live Apply/Rollback/restart absent; native compatibility remains |
| E37 | [G3_REPO_PROFILE_PREFLIGHT_2026-10-16.md](G3_REPO_PROFILE_PREFLIGHT_2026-10-16.md), [JSON](G3_REPO_PROFILE_PREFLIGHT_2026-10-16.json) | Actual Windows named-profile shape preflight, selected observer env и BEFORE continuity; no shape conflicts, CLI command precedence source-reviewed; native compatibility/Apply/restart absent |
| E38 | [G3_REPO_RUNTIME_CUTOVER_2026-10-16.md](G3_REPO_RUNTIME_CUTOVER_2026-10-16.md), [JSON](G3_REPO_RUNTIME_CUTOVER_2026-10-16.json) | Approved Repo-only live Apply/backup/selected restart; narrow native MCP/health/metrics/control and guest selected GET404; source monitor explicit listener UP, auto-discovery UNKNOWN; old HOST remains full |
| E39 | [G3_REPO_MONITOR_DISCOVERY_2026-10-16.md](G3_REPO_MONITOR_DISCOVERY_2026-10-16.md), [JSON](G3_REPO_MONITOR_DISCOVERY_2026-10-16.json) | Discovery timeout3s reproduced; bounded15s/name filter/error reasons fix, Repo11 tests PASS and Windows automatic UP/initialized without override; old dashboard not installed/started |
| E40 | [G3_SELECTED_OWNER_ASSETS_2026-10-16.md](G3_SELECTED_OWNER_ASSETS_2026-10-16.md), [JSON](G3_SELECTED_OWNER_ASSETS_2026-10-16.json) | Seven existing owner files/two backup parents,130 normal/C$ opens DENY5;15 own controls/cleanup PASS; no protected content/ACL writes. 7.6 PARTIAL overall, independent Repo/other assets not accepted |
| E41 | [G3_OWNER_BRIDGES_RESIDUAL_REVIEW_2026-10-16.md](G3_OWNER_BRIDGES_RESIDUAL_REVIEW_2026-10-16.md), [JSON](G3_OWNER_BRIDGES_RESIDUAL_REVIEW_2026-10-16.json) | Concrete Snapshot Broker task/source/queue/control review;78 guest DENY5/6 positives. MySQL NetworkService correction. Residual disposition/P01 Candidate, old HOST remains; no controls/snapshot/restart |
| E42 | [G3_G2_INITIAL_SCOPE_AND_RUNBOOK_2026-10-16.md](G3_G2_INITIAL_SCOPE_AND_RUNBOOK_2026-10-16.md), [JSON](G3_G2_INITIAL_SCOPE_AND_RUNBOOK_2026-10-16.json) | Concrete Candidate scope/final guest entry/stop/recovery; fresh G2 chain/pins and owner recovery metadata; G2 after-check observability. Old HOST still running; no acceptance/restart/ACL/config changes |
| E43 | [G3_G2_SCOPE_ACCEPTANCE_AND_HOST_RETIREMENT_2026-10-16.md](G3_G2_SCOPE_ACCEPTANCE_AND_HOST_RETIREMENT_2026-10-16.md), [JSON](G3_G2_SCOPE_ACCEPTANCE_AND_HOST_RETIREMENT_2026-10-16.json) | E42/P01 принят; exact-handle Preview/Stop once; three old PIDs/8080 gone, G2/Repo fingerprints unchanged and actual MCP/CLI PASS. Scoped acceptance, not universal/whole-chat guarantee |

| E44 | [G3_DOCS_CONSOLIDATION_AND_REPO_BOUNDARY_2026-10-16.md](G3_DOCS_CONSOLIDATION_AND_REPO_BOUNDARY_2026-10-16.md), [JSON](G3_DOCS_CONSOLIDATION_AND_REPO_BOUNDARY_2026-10-16.json) | Metadata/docs only; не новый security PASS |
Первоначальная сверка E01–E17 читала имеющееся evidence. Последующие Windows проверки E18–E19
выполнены через существующий G2 и отражены отдельно. Runtime/ACL/mount/network/task/service настройки,
project commit/push не менялись. Synthetic Git commit выполнен только во временном тестовом репозитории.
