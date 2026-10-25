# Project Checker — актуальный план личной V1

**Обновлено 25.10.2026 по просьбе пользователя.** Это рабочий маршрут разработки в Fortis Repo, а не завершённое приложение, подтверждённый Windows PASS или формальный semantic commit всех technical proposals A4. Обновлён **порядок**, а не набор выбранных потребностей. Полный источник направления: [сохранённая в Repo reading copy CPW-PC-20261025/v4](CANDIDATE_PREWORK_V4_READING_COPY.md) (A4; historical candidate, не committed baseline). **A4 = основной кандидат A2 + PR-13D**, реализующий полный просмотр create/modify/delete относительно actual target без обязательного переключателя режима для каждой регистрации. Следующая точка входа для другого чата — [актуальный самостоятельный хендофф](HANDOFF_CURRENT_V1_20261025.md). Прежний узкий план userscripts сохранён побайтно в [историческом файле](PLAN_LEGACY_USERSCRIPTS_20261025.md).

Актуальные факты: [журнал](IMPLEMENTATION_LOG.md); [исходники](../../runtime/userscript-updater/README.md); [граница Windows](WINDOWS_TRUST_BOUNDARY.md); сохранённые [требования userscripts](REQUIREMENTS.md).

## 1. Цель личной первой версии — законченная программа, не MVP-демо

В одном лёгком Windows GUI владелец регистрирует один файл, несколько файлов, папку или смешанный состав, в том числе несколько source → target mappings. Создаёт/копирует/редактирует общие пакеты правил: прямое сохранение влияет на все проекты-потребители, отдельная копия сохраняет другой набор. Нажимает **«Проверить»**, видит точное покрытие, находки/ошибки и сведения о проверенных байтах. При наличии target позднее отдельно нажимает **«Обновить»**, видит **все create/modify/delete/unchanged и сохранённые внешние файлы**, явно подтверждает точный план, получает backup/readback/journal/recovery. Можно регистрировать проверку без назначения (**check-only**).

ИИ продолжает писать/собирать/тестировать в Docker. После ручной установки пользователь запускает **только независимые внешние копии**, не рабочий Repo. App, анализаторы/зависимости, policies, state/snapshots/backups и approved copies не должны быть доступны ИИ на запись через выданные маршруты, включая alias/Junction/import. Не строим системный запрет всех возможных запусков Repo. Даже удачный статический анализ подтверждает только выполненные правила, не абсолютную безопасность.

## 2. Наблюдаемое состояние на дату обновления

Исходники в Fortis Repo уже содержат модели регистраций и shared packs, SHA-256 snapshots, ESLint/Semgrep JSON adapters и per-file coverage, read-only preview, **отдельную синтетическую** transaction laboratory, view-only Tkinter GUI и строковую проверку Windows layout. В Docker фактически протестированы ESLint 10.13.0 и Semgrep CE 1.182.1 на синтетических JS/Python; последний полный прогон — 123/123 Python tests без skips с обоими CLI. V1-1 исправлен: review binding, бинарные размеры и отдельная реальная effective-config validation. Коммит source-only GUI: 4a832b8; HEAD перед любой новой работой проверять, поскольку есть соседняя работа в том же repo.

**V1-2 начат:** versioned JSON persistence/last selection и source/editor/pickers реализованы в исходниках и тестах; native Windows visual QA ещё NOT_RUN.

**НЕ готово:** shared-pack edit UI, реальный job/progress/cancel/кнопка Check, полноценный Windows GUI test, защищённый установленный toolchain с ACL/handles/route-evidence, production approval/promotion и реальная внешняя приёмка. Scan aggregate в коде остаётся NOT_AUTHORIZED, обе основные GUI-кнопки отключены. Транзакционная лаборатория не является production writer.

## 3. Неизменные требования A4: даже для личного использования

- **Граница доверия.** Никакие результаты/политики от AI-кода не предоставляют право установки. Запуск установленного checker/CLI/плагинов/config из Repo или через импорт Repo исключён. Windows приложение устанавливается вручную за пределы всех agent-write paths, с фактической проверкой parent/link/ACL/write-routes.
- **Правдивый отчёт.** Полный manifest устанавливаемого состава, явно отмеченные поддерживаемые языки/правила/исключения. Missing tool, timeout, unsupported исполняемый файл, skipped rule/file, ignored/parse error → не PASS. Синтетический structural clear без installed authority остаётся NOT_AUTHORIZED.
- **Свежесть.** Source inventory/хеши должны всё ещё соответствовать положительно проверенному snapshot непосредственно перед промоушеном. Изменение registration, общей policy, tool identity, source, target/managed set либо plan делает прежний просмотр/подтверждение недействительным.
- **Отдельное действие владельца.** Проверка не меняет target и не запускает обновление автоматически. Обновление — отдельная кнопка, полный preview всех последствий и явное подтверждение. Другой проект, отмена, двойной клик и устаревший callback не вправе обновлять.
- **Не трогать чужие данные.** Файлы вне управляемого состава сохраняются. Удаления только явно ранее управляемые и видны. Копируются проверенные bytes, с backup и журналом; при partial/locked/crash нет ложного COMPLETED, есть адресное recovery/readback.
- **Владелец выполняет Windows-шаги.** Ни разработки/тесты Docker, ни корректные текстовые пути, ни Git не доказывают отсутствие доступа ИИ через действующие Windows identity/mounts.

## 4. Новая последовательность работы

**Почему переставляем:** завершить удобный V1 check-only и полную пару Check → Review → Update раньше создания универсальных вспомогательных механизмов. E-01…E-05 A4 сохраняются как контрольные блоки. Host-проверки можно готовить параллельно Docker-коду, но **не** пропускать перед доверенным PASS/реальным переносом.

### V1-1 — DONE / DOCKER_TESTED: устранить установленные дефекты модели (E-01 / база E-02)

1. Связать отчёт и preview с конкретной registration, snapshot, policy/tool и target/managed set. **Уже воспроизведён дефект:** GUI-модель принимает preview другого проекта при одинаковом target. Не превращать текущую проверку только target_root в допуск.
2. В полном preview показывать файлы create/modify/delete/unchanged/preserve; для бинарных old/new **размеры** рядом с hashes, а не только пояснение в данных.
3. Развести структуру JSON policy и **валидацию реального effective CLI config**: существование rule IDs, корректность Semgrep YAML, конфликты и доступность обязательных правил; фиктивный валидный JSON-пакет не является валидной политикой.
4. Добавить регрессионные тесты воспроизведённых дефектов и stale bindings. Проверять только synthetic fixtures.

**Gate выполнен в Docker (115/115):** кросс-проектный preview отвергнут; у пользователя в UI виден полный эффект; неправильные effective rules/config блокируют проверку. Docker regressions PASS; permission на реальный перенос всё ещё отсутствует.

### V1-2 — IN_PROGRESS: закончить Check в одном окне (основной E-02, DS-01–03)

- **SOURCE/DOCKER_TESTED (123/123):** локальные versioned JSON-профили для личного применения (никакая БД не нужна): add/edit/remove регистрации, выбор/сохранение последней, Unicode, chooser source/target, one/many/folder/mixed, check-only, atomic save и понятная ошибка при corrupt config/отмене.
- Общие rule packs: create/copy/direct edit/link/unlink/rebind, стабильный captured config при job, effective rules с конфликтами, инвалидировать все зависимые проверки после редактирования.
- Реальная кнопка **«Проверить»** запускает локальные доверенные CLI и даёт file/rule coverage, raw evidence и причины ERROR/INCOMPLETE/FINDINGS. Никакой загрузки проекта как модуля, Repo config/scripts/plugins, autofix, скрытого bypass или auto-update.
- Job не замораживает GUI; есть status, cancel/timeout, повторный запуск и защита от устаревшего callback. Тесты clean/violation/skip/missing engine, source edit, два проекта с одним pack.
- GUI-тесты логики в Docker и отдельный впоследствии native Windows visual smoke. До host verification проверка в Docker — только **development evidence**, а не trusted Windows PASS.

**Gate:** владелец через подготовленный интерфейс может сохранить проект и пакет, запустить полноценную check-only проверку безопасного примера, увидеть причины и повторить после перезапуска. Реальная external mutation ещё отключена.

### V1-3 — завершить preview → confirmation → controlled promotion (E-03, E-04)

- Собрать полноценную цепочку для file/multiple/mixed/folder: scan evidence относится к snapshot, actual target inventory и управляемому previous set; перед применением repeat source/policy/tool/target checks.
- Пользователь видит **полный эффект** относительно фактической внешней копии, включая текстовый diff, бинарные размеры/hashes, удаления ранее управляемого и сохранившиеся unmanaged files/data. Первый импорт existing target не затирает чужие данные без явного включения scope.
- Owner-only confirmation привязывается к этому точному плану. Apply записывает только ранее проверенные staged bytes, ведёт backups/readback/journal/recovery; ошибки/locks/concurrent writes дают точный статус, без второго apply по двойному нажатию.
- Folder/mixed: явные состав/исключения (git/cache/deps/data/пустые каталоги), дубликаты/overlap, удаление/сохранение и multi-root limitation. Если формат неподдержан — **видимый отказ**, не silent skip.
- Имеющаяся devtools/fixture_transactions.py — **исследовательский тестовый код**, не подключать как trusted Windows updater без отдельной реализации и native validation.

**Gate:** синтетические сценарии create/modify/delete, cancel, stale, partial crash и восстановление; затем native Windows controlled fixtures до любых реальных external targets.

### V1-4 — подготовка и ручная проверка Windows-цепочки (E-01 host gate + E-05)

**Подготовку пакета можно вести одновременно с V1-1…3; owner-run проверка обязательна до активации настоящих Check/Update/Approved.**
- Подготовить отдельную установку app/Node/Python/Tkinter/ESLint/Semgrep со **всеми транзитивными зависимостями и локальными packs**; inventory, hashes, версионированный config/state, команды ручной установки/отката.
- Пользователь отдельно проверяет реальный Windows final path/identity, ancestors, reparse/Junction/hardlink, ACL/effective principals и маршруты записи из Docker. Если agent и owner фактически пишут от одной identity, просто другой каталог или ACL той же identity могут быть недостаточны. Отрицательные write-probes — только специально подготовленные безопасные markers.
- Native тесты reparse/race/rename/locked files, import/cwd/config canaries, versions/rule coverage, GUI pickers/progress/cancel, staged bytes/backups/recovery. Никакой Windows-операции от агента без отдельного разрешения.
- Owner walkthrough: сперва безопасный один файл, затем папка/mixed; только потом реальный consumer. Для userscripts — Loader/cache/identity/grants без доступа к GM данным и без send. Никакой тихой перепривязки существующих Loader.

**Gate V1 release:** Windows trust boundary подтверждена в оговорённых agent routes, работающие обе кнопки и GUI, positive/negative scan coverage, точный approved bytes output, сохранённые чужие данные и проверяемое восстановление. Только тогда статус OWNER_ACCEPTED, а не SOURCE_READY.

## 5. Допустимые упрощения для личной V1

| Допустимо | Не упрощать |
| --- | --- |
| Один владелец, локальный JSON вместо БД, без облака, ролей и сервера | Внешние копии и trusted chain вне AI-write routes |
| Только явно перечисленные в первой конфигурации языки и правила | Unknown/unsupported обязательные проверки не PASS |
| Tkinter, если Windows UI smoke проходит; простой дизайн | Реальные picker/persistence/Check/Update, полный preview и отмена |
| Явный отказ от редкого неподдержанного формата/locked состояния | Запись наугад, обход политик, потеря unmanaged data |
| Не строить глобальный OS execution gate или универсальный installer | Checked snapshot, consent, backup/journal/recovery и native route checks |

Это **не сокращение полного V1**: сохранены register file/files/folder/mixed, shared editable packs, check-only, полный create/modify/delete preview, controlled update и owner-use acceptance.

## 6. Как вести работу и подтверждать результаты

- V1-1 завершён; следующий coding шаг — **V1-2**. Не тратить следующий цикл на новый большой synthetic transaction framework, пока Check как пользовательский путь не завершён.
- Перед записью — AGENTS, git status/index; изменять только свои файлы, не захватывать чужой staged work. Локальные коммиты отдельны от push/Windows install.
- Различать SOURCE_READY, DOCKER_TESTED, WINDOWS_PREREQS_CHECKED, WINDOWS_GUI_TESTED, HOST_BOUNDARY_VERIFIED, OWNER_ACCEPTED. Не выводить из Docker tests статус Windows-установки.
- Все Windows-модификации, Loader, браузер/GM/secrets и использование реальных пользовательских target **вне текущего поручения обновить план**.
- [IMPLEMENTATION_LOG.md](IMPLEMENTATION_LOG.md) — проверенные факты; [WINDOWS_TRUST_BOUNDARY.md](WINDOWS_TRUST_BOUNDARY.md) — условия доверенной установки; [HANDOFF.md](HANDOFF.md) — исходный исторический контекст, не текущий маршрут; [REQUIREMENTS.md](REQUIREMENTS.md) — ранее сформулированные userscript constraints.

## Сохранение направления A4

| A4 / основание | Сохранено в V1 |
| --- | --- |
| FR-01, FR-08; PR-06/07/12/13D | Separate Check/Update, полный exact preview, byte-bound approval, backup/recovery |
| FR-02/05; PR-03/08 | Независимый Windows install вне AI-write, owner-run native gate |
| FR-03/07; PR-01/02/04B/11 | Лёгкий GUI, registry/mixed, mutable shared packs, готовые анализаторы |
| FR-04/06; PR-05/09 | Docker dev; правдивые scan results и использование только внешних копий |
| WR-01–27, DS-01–04, EA-01–10 | Сохраняются как карта критериев при V1-1…4, **не объявляются выполненными** по названию этапа |

**Смысл обновления плана:** закончить личную рабочую программу раньше расширения второстепенной инфраструктуры, **не ослабляя исходную главную границу доверия**.
