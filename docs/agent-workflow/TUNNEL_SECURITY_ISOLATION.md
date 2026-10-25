# Безопасность и изоляция Fortis Repo / Tunnel — текущий срез и план приёмки

**Срез:** 25 октября 2026 года. **Статус:** проверенное ограниченное состояние; **НЕ** полная аттестация безопасности Windows/Docker. Данные о Windows — результаты owner-run PowerShell, переданные пользователем; Linux MCP — фактические read-only проверки из первого Repo. PID/состояние процессов и ресурсные цифры — исторические снимки, не гарантия непрерывного состояния.

**Главное решение владельца:** **не переносить сейчас Tunnel вручную, не менять ACL вслепую, не останавливать работающие Repo и не удалять Bridge.** Готовится отдельное доверенное локальное приложение для регистрации и контролируемого обновления проверенных Windows-копий приложений на основе исходников в Docker, ревью и хешей. Сначала встроить Tunnel в его pipeline, проверить изоляцию и восстановление; только потом адресно вывести из использования legacy-компоненты. История этого решения: [WF-046](JOURNAL.md), [план будущей очистки](reviews/dual-direct-trusted-runtime-cleanup-plan-20261025.md).

## 1. Где истина и как читать результаты

- **Текущий workflow и следующий шаг:** [STATE.md](STATE.md). Хронология, источники, конкретные ручные отчёты: [JOURNAL.md](JOURNAL.md), WF-020–WF-046.
- **Доказательства:** [аудит Docker/Windows](reviews/repo-protection-20261025.md), [аудит двух Direct после установки](reviews/dual-direct-postinstall-audit-20261025.md), [миграция/rollback Direct](reviews/permanent-direct-mcp-rollout-20261025.md), [сеть и роль Bridge](reviews/repo-network-and-mcp-bridge-20261025.md).
- **Общая G2 Windows-изоляция:** [ISOLATION_GUIDE](../ISOLATION_GUIDE.md). Старые фразы в датированных источниках про «Bridge в serving chain», «второй Repo не переведён» и «ACL ещё не проверены» — исторический статус до WF-036/046, **не актуальный срез**.
- **Источник в Git ≠ работающая установленная версия.** Документированный SHA — контрольный отпечаток конкретных bytes, а не доказательство авторства поставщика или невозможности будущей замены. Не загружать в Git ключи, токены, полные saved profiles, приватные Tunnel URL, дампы конфигураций с секретами и ACL backups.

### Значение статусов

- **PASS(scope):** названная конкретная проверка прошла в указанной среде/дате; не распространять на другие слои и будущее.
- **OPEN:** нет достаточного доказательства, риск не устранён либо необходим безопасный тест.
- **OWNER-REPORTED:** проверка исполнена вручную на Windows; в Linux не было самостоятельного доступа к host ACL/секретам.
- **DESIGN:** требование к ещё не установленному pipeline, а не выполненная защита.

## 2. Модель исполнения и границы

```text
ChatGPT (два браузерных профиля, два Tunnel identity)
       │               │
       ▼               ▼
Windows alexa: два своих launcher/profile/key-runtime
       │  Windows Client + Runtime (C:\Tools; вне обычных RW mounts)
       └───────────────┬──────────────────┘
                       ▼
Docker: общий fortis-repo-test, два Direct MCP DC
       /usr/local/bin/node /opt/dc/.../dist/index.js
           UID1000; общие сеть, DC-config, RW roots
                       │
             ┌─────────┼─────────┐
             ▼         ▼         ▼
         /workspace  /workspace /workspace
          /repos       /files     /repo
          RW bind      RW bind    RW volume
             │          │
             ▼          ▼
         Windows Repos / Windows Workfiles
            доступ к тем же файлам
```

- Bind mount делает **файлы общими**: запись агентом в `/workspace/repos` меняет файл в Windows `C:\Users\alexa\Repos`. Вызов `python`/`node` внутри контейнера **исполняется в Linux**, а не автоматически в Windows.
- **Но mount не является полным запретом host execution.** Windows task/service/IDE/launcher может позже прочитать и выполнить изменённый файл; также агент может обратиться к доступному Windows API/сетевому сервису, если такой путь существует и разрешает действие. Универсальный Windows shell из Linux Repo **не подтверждён**, но универсальная невозможность обойти host updater **ещё не доказана**.
- Второй браузерный профиль не создаёт OS-изоляцию: в проверенном срезе оба DC были UID1000 в **одном Docker**, с общими файловыми разрешениями, Git, DC config, ресурсами и сетью. Для изоляции профилей по данным потребуются отдельные контейнеры/UID/volumes/mounts.
- Windows G2 — отдельная Windows identity `FortisHostG1`; это **не** Windows user, под которым исполняется обычная Linux-команда Fortis Repo.
- Нельзя полагаться на `allowedDirectories` Desktop Commander как на sandbox для произвольного shell или обещать, что Linux rootfs read-only запрещает писать в выданные RW roots.

## 3. Что мы фактически проверили

| ID | Проверка / источник | Результат | Что НЕ доказано |
| --- | --- | --- | --- |
| V-01 | Миграция двух Windows Tunnel на Direct MCP; WF-035–037 | **PASS(scope)**: после owner install первое `get_config`/`read_file` успешно, второй чат подтвердил отдельное read-only чтение Git; Linux `/proc` видел **2 Direct DC, 0 Bridge** | Непрерывная работа, все MCP-команды, повторное подключение после закрытия профилей и холодная перезагрузка |
| V-02 | Direct DC module, предки пути; WF-037 | **PASS(scope)**: module SHA-256 `a4145198dc75cd34e7c7452c2054b4cc0d29e199ae1459961a17e4da25a13500`, protected root-owned `/opt/dc` path, не writable UID1000 | Не гарантирует целостность других файлов, всей supply chain или Windows start chain |
| V-03 | Docker confinement; WF-020/037 | **PASS(scope)**: UID/GID1000, RO rootfs, no Linux capabilities, `NoNewPrivs=1`, `Seccomp=2`, не найден стандартный docker.sock; ресурсы ограничены 1 GiB/2 CPU/256 pids | Нельзя исключить все Docker API/Windows network routes, контейнерные уязвимости или данные в RW mounts |
| V-04 | Реальные mounts; WF-020/029/037 | **PASS(scope)**: `/workspace/repos` ↔ Windows Repos RW; `/workspace/files` ↔ Windows Workfiles RW; `/workspace/repo` — writable Docker volume | Не установлены все Windows junction/reparse aliases, цели и обходные пути |
| V-05 | Direct DC config; WF-036/037 | **PASS(scope)**: три allowed roots, `/bin/bash`, telemetry=false. При старте guard pin именно эти поля | `blockedCommands` и иные поля не закреплены guard; сам config writable UID1000 и общий двум DC |
| V-06 | Legacy Bridge; WF-029/037 | **Устранён из обеих текущих startup chains**; Linux файл `/workspace/repo/.fortis/mcp-bridge.mjs` по-прежнему существует в UID1000-writable родителе | Безопасность старого Bridge fallback/других launcher; файл **не удалён** |
| V-07 | Первый Windows installed launcher/control; WF-030–035 | **OWNER-REPORTED PASS**: штатный запуск Direct после pin/Preview и отдельного восстановления tmpfs/DC/Git; первый профиль `repo-mode` | Полный холодный старт обоих профилей в произвольном порядке, постоянная защита всех предков Windows paths |
| V-08 | Второй Windows launcher/guard; WF-035/038 | **OWNER-REPORTED PASS**: SHA installed launcher/guard и backup; ACL SDDL launcher=старому backup, guard=launcher; 0 reparse на проверенной прямой цепочке путей | Равенство ACL ≠ безопасные эффективные права; не доказана недоступность через иные junction aliases |
| V-09 | Windows Client/Runtime identity; WF-040/041 | **OWNER-REPORTED PASS по внутренним эталонам**: Client SHA `1946DE55A038313A9B9B2458D05FE1719FA9CF1F20A94DD5F38FC26A98BFDD42`; Runtime SHA `A922D372D6BE0649156FBC1C8A040597F1F4BB5B4356890151D7875602593B1A`. Оба вне обычных Repos/Workfiles, не reparse на проверенных путях | Оба EXE Windows Authenticode=`NotSigned`: исторические SHA не подтверждают происхождение от вендора; второй launcher pin-at-start Runtime есть, Client в Start **не закреплён** |
| V-10 | Windows `C:\Tools` ACL; WF-041/042 | **OPEN, реальное evidence**: `Authenticated Users` имеет наследуемый `Modify` на Client/Runtime и родителях. Для `FortisHostG1` применим Deny Write/Delete/DeleteChild/ACL/Owner. SYSTEM/Admin Allow, у `alexa` нет отдельного Allow Write, вероятно использует широкую группу | Не установлен effective write другого конкретного token; нельзя удалять broad Allow вслепую (сломается обновление `alexa`) |
| V-11 | Состав локальных Windows пользователей; WF-043/044 | **OWNER-REPORTED PASS(scope)**: включены `alexa`, `FortisHostG1`, `CodexSandboxOffline`, `CodexSandboxOnline`. Оба Codex включены в `CodexSandboxUsers`, не прямые Administrators | Restricted token/эффективный доступ песочницы не проверялся; наличие Codex не является доказанным успешным доступом к EXE |
| V-12 | Windows roots владельца; WF-045 | **OWNER-REPORTED PASS(scope)**: профиль `C:\Users\alexa` имеет защищённое наследование и Allow Write alexa без broad Allow; обе директории установленных launcher имеют OwnerIsAlexa=true, AlexaWriteAllow=true, BroadWriteAllow=false | Вся цепочка `AppData/Local`, effective ACL, `docker.exe` и возможные aliases остаются без полной проверки |
| V-13 | Credentials первого Tunnel; WF-020/репо-защита | **OWNER-REPORTED PASS(scope)**: Windows `runtime.key` ACL protected, только `alexa FullControl`; содержимое ключа не читалось | Все копии credentials, ключ/профиль второго Tunnel, передача ключей в процесс/сеть, отсутствие secrets внутри Docker |
| V-14 | Network/host diagnostics; WF-020/021/029 | **OPEN F-R-06**: из Docker был доступен узкий host loopback `/healthz` (200); выбранные admin GET давали 404 | Нельзя утверждать запрет других методов, host/LAN endpoints, unauthenticated launch/promotion APIs либо всего сетевого egress |
| V-15 | Reboot и memory/tmpfs; WF-030/031/037 | **Частичный recovery PASS** одного Repo после сброса `/home/node` tmpfs и pinned восстановления DC/Git; два Direct совместно работали при pinned config. Snapshot memory 546/1024 MiB, 56/256 pids, OOM=0 | **OPEN:** холодный reboot с двумя профилями и racing first start, emergency rollback независимо от Bridge |

Значения SHA и пройденные проверки выше — **срез, а не инструкция автоматически доверять любому следующему файлу с похожим именем**. Фактическая установка/проверка актуального runtime всегда требует нового read-back.

## 4. Открытые вопросы и приоритет

| ID | Риск / недостаток доказательств | Почему важно | Следующая безопасная проверка |
| --- | --- | --- | --- |
| F-R-05 residual | Старый Bridge остаётся по подменяемому пути внутри Docker RW | Не должно быть возвращения к небезопасному startup при recovery | Inventory всех профилей/fallback references; убрать только после независимого Direct rollback |
| F-R-06 **OPEN** | Docker → host/LAN и управляющие API изучены не полностью | Обход внешнего updater даже без Windows shell через host service/API | Read-only inventory/listeners/firewall/auth, затем отдельно санкционированный отрицательный API-test |
| F-R-07 **OPEN** | Broad Windows ACL `C:\Tools`, неаттестованное происхождение EXE, в Repo2 Client без startup pin | Путь к рабочему EXE может быть заменён при недостаточной защите; это отдельный риск от Docker | Windows DACL/effective target principals/parent delete, build provenance, разработка узкой trusted install policy через promotion app |
| F-R-08 **OPEN** | Не проверены все reparse/junction и фактическое покрытие RW mounts | «Вне Repos» не исключает альтернативный путь | Адресная карта Windows alias **без** рекурсивного обхода незнакомых targets |
| F-R-09 **OPEN** | Второй runtime key/profile, возможные copies/secret exposure | Dev-код без ключа не должен получить production identity | Owner-only read-only location/ACL/mount-reference inventory; **без** вывода secret |
| F-R-10 **OPEN** | Shared DC config/UID/Git/two profiles | Изоляции одного Repo от второго **нет** | Явно принять общий контейнер либо отдельно проектировать два контейнера |
| F-R-11 **OPEN** | Холодный reboot обоих Repo, restore, order/race, Bridge-free rollback | Fail-closed может прервать работу, а старый fallback небезопасен | Owner-controlled test window после защиты восстановления и бэкапов |
| F-R-12 **DESIGN** | Пока не реализована и не проверена trust boundary нового локального promotion-приложения | Непроверенный Docker source не должен получить Windows production execution | Приёмка по разделу 6 и фиксация реальных receipt/логов тестов |

**Не путать:** «агент не запускает Windows EXE автоматически через bind mount» — свойство самого mount. «агенту недоступен *любой* способ инициировать Windows execution» — пока **не проверенное** обобщение.

## 5. Целевой pipeline доверенного приложения (DESIGN)

Требование владельца: регистрировать приложение как соответствие **Docker dev path ↔ Windows trusted installed copy**, автоматически собирать и проверять код, а выпускать/обновлять только явно одобренную версию по точному совпадению хешей.

```text
Docker RW sources (untrusted agent)
        │ tests / lint / review candidate
        ▼
Frozen candidate + file manifest/digests (untrusted until host verifies)
        │ authenticated approval / policy — not writable by agent
        ▼
Trusted host promotion controller (outside mounts, protected Windows ACL)
        │ re-check candidate digest, materialize secure staging
        │ re-check every artifact+dependency/hash in staging
        ▼
Approved release manifest+receipt (outside Docker, agent cannot edit)
        │ atomic install/version swap + independent rollback
        ▼
Windows installed application (trusted path) + keys/profiles outside Docker
        │ normal запуск зарегистрированного приложения
        └─ **никакой** прямой запуск dev-копии Windows
```

**Обязательные свойства:**

1. Адрес и Windows-путь installed/runtime/launcher, approval store, ключи, backups и updater **нельзя изменить** через выданные Docker RW roots, junction/aliases, другие неавторизованные Windows token и сетевой интерфейс. У updater отдельный минимально привилегированный контекст; агент не получает host admin/shell.
2. Lint/tests/AI review — средства поиска ошибок, **не доказательство безвредности**. Основание допуска: зафиксированная ревизия, trusted approver/политика, независимые digest и проверка состава поставки/зависимостей.
3. Одобрение относится к **конкретным bytes**, а не к названию ветки/папки. Файлы могут измениться после review; Windows installer принимает только staging, чьи SHA-256 совпали с одобренным manifest. Manifest/approval нельзя хранить единственно в Docker RW.
4. Установленные скрипты/библиотеки/плагины/конфиг с исполняемой семантикой тоже входят в проверяемую поставку. Защитить путь и все критичные предки от rename/delete/path substitution; безопасно обработать junction/symlink/hardlink, TOCTOU и подписи/доверенный origin where applicable.
5. Runtime secrets остаются только на Windows у разрешённого процесса. **Отсутствия ключа в Docker недостаточно**, если Docker может вызвать host API с действием на чужих credentials: контролировать authentication/authorization и network ingress.
6. Запуск одобренной Windows-копии владельцем или доверенной автоматизацией допускается. Не требуется запрещать обычный запуск Windows; необходимо предотвратить подмену рабочих файлов и альтернативный запуск *неодобренного* кода с правами owner.
7. Не выдавать агенту возможность самостоятельно включить release/update без одобрения, изменить registered source/target/launch command, approved hash или отключить проверки. Все отказы должны быть fail-closed, без автоматического fallback на Bridge/dev source.
8. Заранее подготовить backup предыдущей рабочей версии, атомарный rollback и независимую возможность восстановить updater/manifest из места вне записи агента. Изменения installed file/ACL не проводить в момент работы двух Repo без контролируемого плана.

**Особенность Tunnel:** внутри Docker **должен работать** проверенный Linux Direct Desktop Commander — это сама MCP execution среда. «Сделать Docker-копию Tunnel нерабочей» значит **не выдавать ей настоящую Windows Tunnel identity/keys и право продвигать релизы**, а не ломать Linux DC.

## 6. План приёмочных испытаний, когда локальное приложение будет готово

Каждая строка — будущий тест, пока **PENDING**, если отдельно не указано иначе. Сначала mock/canary, без разрушения рабочего Windows Tunnel и без чтения реальных ключей агентом. Любой host/Docker ACL, networking, stop/reboot/install — только отдельная owner-approved операция с сохранением rollback.

| Gate | Положительная проверка | Отрицательная / adversarial проверка | Приёмочный результат |
| --- | --- | --- | --- |
| P-01 Регистрация Tunnel | Сохранены source root в Docker, trusted installed root в Windows, состав двух launchers/guard/control, Client+Runtime, Linux DC pin, deps и profiles по **метаданным** | Регистрация пути в RW-root/alias в качестве trusted target отвергается | Manifest регистрации хранится вне доступа Docker; все runtime dependencies перечислены |
| P-02 Boundary/credentials | Из Docker видно только dev-source, тестовые конфиги; ключи остаются Windows-only | Read-only проверка mounts/aliases/references; Docker не читает рабочие ключи и не меняет installed bytes | Pass/Fail по фактическим правам и путям; без вывода key contents |
| P-03 Review freeze | Candidate фиксируется с независимым SHA manifest и связывается с результатами lint/tests/review | Агент меняет dev файл **после** approve, повторный install отклонён | Host-side re-hash reject и audit receipt |
| P-04 Approval integrity | Только доверенный approver/политика выпускает release | Агент меняет локальный Docker manifest, approvals, registry/config, команду запуска | Утверждённый host approval не изменился, попытка отклонена |
| P-05 Secure staging | Защищённое host staging, повторная проверка каждого файла/зависимости до замены | Подмена staging bytes, symlink/junction/path traversal, non-approved dependency | Отказ до установки; production hash прежний |
| P-06 Atomic deploy / rollback | Одобренная версия устанавливается с read-back SHA и независимым backup | Прерывание/сбой во время install, несовпадение хеша после копирования | Нет partial live install; рабочая версия восстановлена |
| P-07 Windows execution gate | Одобренная установленная версия штатно запускается | Проверенный и безопасный тест альтернативного host runner/API/автозапуска и ситуации, когда Windows пытается исполнять dev-script из mount | Нет подтверждённого обхода, либо он явно устранён/принят до PASS |
| P-08 Windows ACL/copy | Рабочие launchers, bins, manifests доступны нужным владельцам/SYSTEM; trusted path защищён | У контролируемого тестового principal/контролируемого synthetic path нет Modify/Delete/DeleteChild/ChangePermissions, нельзя переименовать parent | Effective rights + backup/restore проверены, `alexa` не потерял обслуживание |
| P-09 API/network | Из Docker доступны только согласованные функции | Проверить доступность управляющего/update/start API без credentials/role, включая host.docker.internal и LAN | Negative controls без изменения prod; egress/auth policy документирована |
| P-10 Two-profile boot | После контролируемого reboot оба сохранённых MCP профиля запускаются Direct, конфиг восстанавливается без Bridge | Старт в разном порядке, отсутствие/порча tmpfs config, параллельный старт, неверный pin | 2 Direct, 0 Bridge, оба real-client smoke, fail-closed+repair без RW legacy |
| P-11 Legacy cleanup | Точные consumers Bridge/старых copies отсутствуют и rollback не нуждается в них | Отдельная проверка, что каждый другой saved profile не использует legacy entry | **Только после** независимого recovery и owner approval — архив/удаление известных путей, repeat smoke |
| P-12 Evidence/observability | Для каждой установки сохраняются source fingerprint, approved digest, установленный digest, actor/time и outcome | Intentional reject не записывает секреты, но даёт аудируемую причину | Redacted receipts, version history, безопасная диагностика и возврат старой версии |

### Минимальный шаблон evidence для каждого Gate

- Идентификатор проверки, дата/среда/версия приложения, проверявший (`owner Windows` / `Linux MCP` / `app receipt`).
- Начальные условия и **точная граница scope**, команда/метод (без секретов), expected/observed и PASS/FAIL/OPEN.
- Хеши **одобренных и фактически установленных** файлов, список обязательных зависимостей, идентификатор записи release (не ключ/URL).
- Негативный контроль на synthetic/test артефактах; независимый read-back целевого installed места, откат с подтверждением.
- Различать: авторский отчёт, журнал инструмента, файлы текущего runtime, реальные функциональные smoke и фактическое восстановление после reboot.

## 7. Что делать до готовности приложения и что делать после

**Сейчас (без изменения runtime):**

1. Сохранить оба рабочих Direct Repo, текущие Windows installed файлы и ключи, не удалять legacy Bridge.
2. Не выполнять вручную предлагаемый ранее перенос в профиль `alexa` и не править наследование `C:\Tools`; выбор production-root делает будущий promotion app после анализа ACL/alias и rollback.
3. При необходимости только read-only уточнить второй key/profile location/ACL и host API/network/aliases, не извлекать secret bytes.
4. Эта страница — центральная запись по *Repo/Tunnel*; исторические G2/G3 документы остаются отдельной доказательной базой, а не заменяются.

**Когда приложение готово:**

1. Зарегистрировать Tunnel как первый controlled promotion target **без немедленного обновления**.
2. Выполнить P-01–P-09 на synthetic/staging и реальной metadata boundary, исправить все пути обхода; затем пройти owner-approved cutover/rollback P-10.
3. После реальной приёмки и независимого rollback провести P-11 cleanup Bridge, затем повторить audit P-12.
4. Обновить этот документ, [STATE](STATE.md) и [JOURNAL](JOURNAL.md) реальными receipts; **не** проставлять PASS заранее.

## 8. Ограничения и запрещённые преждевременные действия

- Текущие два Tunnel Direct — **функционально PASS(scope)**; это не доказательство непроницаемости Docker или всего host.
- Не сканировать чужие пути за пределами согласованных roots и не следовать автоматически по reparse targets; не запускать разрушительные ACL/marker-тесты на рабочих EXE, не kill текущие PID, не чистить `/workspace/repo/.fortis` рекурсивно.
- Не переносить Windows key/profile в Git/Docker, не публиковать raw Tunnel profile, credentials или лог с приватным URL. Не путать `NotSigned` с доказанной компрометацией.
- Git-коммит этого документа **не меняет** host ACL, Tunnel installs, Docker, сеть, автозапуск и не выполняет release. Отдельный owner-approved deployment обязателен.

**Краткий итог:** защищённость от прежнего **исполняемого** Bridge-path substitution обеспечена для двух проверенных Direct chains; полноценная Docker ↔ Windows trust boundary и гарантированный promotion-only release пока **OPEN**. Следующий крупный рубеж — **реальная приёмка будущего локального updater/promotion app по P-01–P-12**, а не перенос файлов до готовности этого механизма.
