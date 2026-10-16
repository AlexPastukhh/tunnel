# G3 — проверка необходимости GUI-тестов и ручных переходов

## Статус

Источник запроса: пользователь попросил проверить, можно ли избежать повторных logon/password,
ручного переноса скриптов и повторного доказательства свойств, уже описанных Microsoft.
Это review метода и Candidate Proposal; Need/FR, защищаемая owner граница и фактические
security acceptance статусы не изменены. **G3 BLOCKED; G4–G6 не приняты.**
План-владелец: [G2 next actions](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md).
Windows evidence/ошибки: [диагностический журнал](G3_SESSION_GUI_BOUNDARY_DIAGNOSTIC_2026-10-15.md).

Следующий recovery block пока не требуется выполнять: пользователь поставил вопрос о ценности
такого тестового цикла. Исторические команды/пины сохранены; эта пауза не делает их PASS.

## Последующее решение пользователя

Пользователь принял [guest MCP рабочий порядок](G3_GUEST_MCP_WORKFLOW_2026-10-15.md) и поручил подготовить шаг 1.
Источник launcher подготовлен, Repo и Windows HOST component checks выполнены; Public copy доставлена.
Guest Preview / LaunchTest / switch-back acceptance ещё не выполнены. Review Findings сохранены;
изменение security acceptance из P01 остаётся Candidate, существующие G3 gaps не закрыты.

## Что проверял исходный сценарий

- Разные actual SID/session и действительные owner/guest WinSta0/desktop objects.
- Работу своих guest window/clipboard, не ценой запрета собственных GUI функций.
- Отрицательные owner capabilities через открытие handles, без owner content reads.
- Возможность получить запрещённые capabilities через owner processes/retained handles/bridges.

Это разные вопросы. Свойство ОС, фактический запуск нашей chain, её полезная работа и наличие
обходных маршрутов требуют разных доказательств. Generic open-handle matrix не заменяет ни
функциональный smoke конечной G2 chain, ни проверку owner HTTP API.

## Первичные источники: что уже подтверждено

Проверены 2026-10-15; английские термины сохранены для точности.

| Источник | Подтверждает | Не подтверждает для нашей установки |
|---|---|---|
| [Microsoft Window Stations](https://learn.microsoft.com/en-us/windows/win32/winstation/window-stations) | Window station содержит clipboard и desktops; station принадлежит session; interactive sessions имеют собственные WinSta0 | Какую session/station реально получил наш G2 и его descendants |
| [Microsoft Desktops](https://learn.microsoft.com/en-us/windows/win32/winstation/desktops) | Window messages и hooks ограничены одним desktop | Отсутствие дополнительного privileged helper/bridge в нашей chain |
| [OpenWindowStationW](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-openwindowstationw) | Документированный вызов открывает station текущей session | Корректность нашего экспериментального Native cross-session probe |
| [SetProcessWindowStation](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setprocesswindowstation) | Назначаемая station должна принадлежать текущей session | Защиту произвольного TCP API, файлов или привилегированного посредника |
| [Microsoft Windows boundaries в AVD guidance](https://learn.microsoft.com/en-us/azure/virtual-desktop/security-recommendations#security-boundaries) | User/session boundaries защищают от неавторизованного доступа; local admin может пересекать границы | Абсолютную защиту от всех ошибок конфигурации/уязвимостей или пригодность конкретной chain |
| [CreateProcessWithLogonW](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-createprocesswithlogonw) | Alternate credentials могут использовать desktop/station родителя | Что обычный Run as different user из alexa создаёт отдельный GUI SessionId |
| [Process access rights](https://learn.microsoft.com/en-us/windows/win32/procthread/process-security-and-access-rights) | Открытие process проверяет требуемое право; QUERY_LIMITED_INFORMATION — отдельное право | Что отказ этого права означает запрет owner screen/clipboard |

Вывод: общий механизм session/window-station separation уже документирован. Повторное исследование
Windows через undocumented API не является автоматически необходимым приёмочным gate.
Нужна проверка применения этой модели к нашей chain и адресная проверка реальных обходных путей.
Это не основание объявить локальную конфигурацию принятой только по документации Microsoft.

## Findings

**F01 — Problem: вспомогательная metadata стала блокером независимого теста.**
Полный GuestProbe останавливается на HoldProcess / QUERY_LIMITED_INFORMATION. Native Win32 code
и точный caller stage не получены. Скрипт не выдал GUI/clipboard outcome. Сам отказ не доказал
owner GUI DENY. Для самостоятельного guest positive он не нужен; менять права owner ради него нельзя.

**F02 — Problem: тестовый процесс требует повторной ручной доставки и состояния консоли.**
Была ошибка ожидания полного desktop path, затем inline recovery зависел от прежних `$h`/`$Error[0]`.
Отладка harness стала отдельной работой без достаточной новой evidence по целевой границе.
Email не является техническим prerequisite: предыдущие PS1 уже доставлялись через Public Documents.

**F03 — Opportunity: использовать существующий narrow G2 MCP для итераций.**
В установленном connector представлены guest file/shell tools. Схема после одноразового guest login/start:
разработка в Repo → выбранные исходники в guest Workspace через существующий G2 → guest CLI/test → JSON обратно.
Чат может получать ответы guest-процесса независимо от того, чей desktop сейчас отображается.
Последнее — инженерный вывод из независимого MCP транспорта; наш конкретный цикл после switch-back
ещё требует проверки. Наличие tools в registry не доказывает работающий runtime в правильной session.

Live проверка get_config существующего G2 выполнена дважды: оба ответа — gateway/SSE probe HTTP429.
Реальные SID/session/доступность guest MCP сейчас не проверены. Это не доказательство остановки
Windows guest или отказа самого G2 runtime. Ни один tunnel не перезапускался.

**F04 — Problem/Risk: старый entry недостаточен для новой session acceptance.**
Прочитан `runtime/host-g2/runtime-api-migration/start-g2-runtime.ps1`.
Он проверяет SID1009 и non-elevated role, runtime hash и отдельный profile, но не actual SessionId.
Duplicate guard перечисляет все tunnel-client processes и требует GetOwnerSid для каждого,
включая чужие owner процессы. Любая ошибка metadata прерывает старт.
Это наблюдение по source, не доказанный новый Windows запуск/сбой launcher.
Минимальный guest entry должен адресно учитывать свой контекст без требования читать чужие процессы.
Не следует обходить это повышением прав или запуском в owner session.

## Proposal P01 — сократить ручную работу, сохранить цель защиты

**Статус: Candidate, не применён к runtime и не закрывает пункты 2.5/2.6/6.5/8.**

| Действие | Что даёт / последствие отказа | Условия и стоимость |
|---|---|---|
| Подготовить минимальный session-compatible entry существующего G2 | Позволяет один раз запустить G2 внутри guest, затем проводить итерации через него | Source работа в Repo; точная identity/session/свои duplicate guards; сохранение separate auth/runtime pins. Existing live profile/entry нужно сверить без чтения ключа |
| Один user-local guest login/start, затем switch back в alexa | Убирает необходимость вводить Windows password и переносить код на каждой итерации | Уже принятый daily login остаётся. Проверить, что guest logon сохраняется и G2 отвечает после switch-back; длительность не измерена |
| Доставка выбранных файлов через G2 в собственный Workspace | Убирает email и ручные copy-paste для разработки | Только согласованный scope и действующий G2. Размер текущего PS1 около 26 КБ; соблюдать лимит 1 000 000 байт на логический набор, если маршрут является прямой передачей HOST↔ChatGPT |
| Один компактный smoke конечной chain | Подтверждает actual SID/non-admin/session/objects, свои GUI/clipboard, нужную CLI/Edge работу, cleanup и доступ после switch-back | Положительные GUI тесты не должны зависеть от QUERY к owner process; owner contents не читаются |
| Адресно проверить реальные обходные пути | Защищает owner control/data вне обычного desktop API | Owner HTTP API/auth, применимые privileged IPC/helpers, clipboard bridges и выбранные protected files. Уже достаточные scoped PASS не повторять без drift |
| Native cross-session matrix — только при конкретной новой гипотезе | Сохраняет возможность углублённой диагностики при неизвестной опасной capability | Не делать отладку undocumented ABI условием работоспособности G2. Если контракт 2.5 требует именно fresh-open experiment, отдельно согласовать заменяющую достаточную методику; не объявлять строку PASS по источникам |

Цель та же: guest сохраняет свои GUI/clipboard и не получает неавторизованный owner доступ.
Предлагается изменить метод и порядок проверки, а не ослабить owner boundary.
Применение launcher/запуск и изменение verification acceptance — отдельные конкретные действия.
Новый SYSTEM broker, service, task, autologon, сохранение Windows password, mount/ACL expansion,
новая инфраструктура или отключение существующих plugins для этого Proposal не требуются.

Если существующий G2 transport пока недоступен, допустим один заранее подготовленный пакет/один
локальный запуск вместо интерактивной переписки по каждой строке. Адресную Windows CLI/file доставку
можно рассмотреть после проверки доступного разрешённого маршрута; не подменять её широким mount
и не читать owner secrets. Такой fallback не является уже выполненным действием.

## Достаточность evidence и оставшаяся работа

- Документированная модель ОС: подтверждена первичными источниками выше.
- Owner metadata/schema2 текущего pin: подтверждены user-local JSON, Session1, 21:51:41 Bangkok.
- Guest interactive test: имел остановки harness; полный GUI/clipboard outcome не получен.
- Конечная narrow G2 MCP chain в отдельной guest session: не принята; live probe сейчас HTTP429.
- Owner API, relevant service/IPC/SMB и final-chain handles/bridges: остаются применимые gaps плана.
- Старые file/runtime/task/Docker/Edge scoped PASS сохраняют свой scope; повтор всего аудита не нужен.

Не принимать generic OS documentation за полный аудит Windows. Не требовать повторного исследования
самой Windows без конкретного риска. Практическая цель ближайшего теста — проверить нашу сборку,
права, запуск и интеграцию, а не заново доказать существование session boundary.
