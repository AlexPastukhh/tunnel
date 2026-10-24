# Fortis Repo: результат исследований защиты, 25 октября 2026

**Выполнено в разрешённом Repo-контуре; меры не применены.** Пользователь разрешил доделать оставшиеся исследования. Это разрешение на анализ и адресные проверки, не на изменение Windows/Docker или принятие всех Proposals C-04. Repo остаётся без отдельного Windows-профиля; аккаунт ручного запуска результата выбирает пользователь.

## Вывод для решения

У Repo есть действующие системные ограничения: UID1000, нулевые capabilities, NoNewPrivs, seccomp, read-only корень и лимиты ресурсов. Они не защищают от чтения/изменения уже выданных Repos/Workfiles и внутреннего RW volume.

**Наиболее конкретный новый риск — целостность действующего MCP Bridge.** Файл root-owned и не writable напрямую, но его каталог и родитель принадлежат рабочему UID1000 и writable; immutable/append-only отсутствуют. По проверенным правам рабочий код может заменить путь к Bridge. Подмену не выполняли. Проверенный исходник Windows launcher запускает этот путь, а hash-проверки Bridge в нём и исходнике probe нет. После ручного сбора пользователя hashes launcher/control/probe совпали с проверенными source bytes; этот конкретный source/live gap закрыт.

Стандартные Docker TCP API на двух выбранных портах отклоняют соединения. Это полезное отрицательное evidence, но изоляция от остальных host/LAN-сервисов не доказана. Полного security PASS и доказательства безопасного исполнения любой неизвестной сборки нет.

Ближайшее решение о MCP entry — прямой установленный DC (PR-A-13) либо защищённый Bridge (PR-A-07). Изолированное сравнение дало одинаковые 26 tools/input schemas, поэтому необходимость дополнительного адаптера нужно оценивать по actual-client/UI совместимости. Достаточная граница данных/сети остаётся отдельным решением. Дополнительный Windows-профиль Repo не требуется этим выбором.

## Дополнение: ручной Windows-сбор и адресная сетевая проверка

Пользователь сообщил об исполнении подготовленного скрипта. Через Repo прочитан единственный созданный `/workspace/files/fortis-repo-boundary-5112ca5ae5994d7eac6a7d4d264ff712.json`: 54 554 bytes, SHA-256 `8c034c269efc83a5cbb69eca49aca72ac220be7dace8f5675f1ccf04d4e3ebbe`. Внутренние metadata: `FORTIS_M\alexa`, `2026-10-24T20:11:53.2152007Z` = 25 октября, 03:11:53 Asia/Bangkok. Это результат ручного сбора пользователя, не выполнение Windows-команд агентом. Полный JSON/ACL payload в Git не копировался.

| Что проверено | Результат | Предел вывода |
| --- | --- | --- |
| Действующие run-tunnel.ps1 / control.ps1 / probe.mjs | Все три hashes совпали с соответствующими source bytes в Git | Закрыт конкретный gap source/live для этих файлов на момент сбора; будущая неизменность не гарантирована |
| Windows runtime EXE | SHA совпал с pinned E38 artifact `A922D372D6BE0649156FBC1C8A040597F1F4BB5B4356890151D7875602593B1A` | Не полный audit бинарника/уязвимостей; fingerprints Node/client также получены, но их отдельная эталонная аттестация не заявляется |
| Windows process | Repo runtime PID19868, parent12488, owner SID1001, ожидаемый executable path; listener 127.0.0.1:61118 | Это динамический срез, не постоянный порт для конфигурации |
| Docker inspect | Тот же полный container ID; User1000:1000, Privileged=false, rootfs RO, CapDrop ALL, NNP; 1ГиБ/2CPU/256pids; ровно прежние три RW mounts, без опубликованных ports | Подтверждены выбранные поля; не полный Docker host audit |
| Namespace/network fields | PidMode="", IpcMode=private, CgroupnsMode=private, UsernsMode=""; network fortis-repo-egress, driver bridge, Internal=false, EnableIPv6=false | Пустые mode поля не выданы за полный audit daemon defaults; null ICC/masquerade options не означают их принудительное отключение |
| runtime.key ACL | InheritanceProtected=true, один ACE: Allow alexa FullControl | Подтверждён DACL этого файла; key contents/hash не собирались. Не обещание защиты от owner/admin privileges или любых иных копий credentials |
| Launcher/probe/config ACL | Owner alexa; SYSTEM/Administrators/alexa FullControl; CodexSandboxUsers ReadAndExecute | Не найден отдельный write Allow для G1 в этих выбранных ACL; effective tokens/все предки/другие профили не проверены |
| C:\Tools и выбранные executable/parent paths | Authenticated Users имеет Modify; для FortisHostG1 есть отдельные Deny на write/delete/permissions/ownership; Users — RX, Administrators/SYSTEM — FC | Общий Modify нельзя считать успешным доступом именно G1; для иной учётки без соответствующего Deny остаётся условный риск |
| Доступ Repo к действующему Windows runtime | 25 октября, 03:15:11: GET /healthz → 200; /ui, /api/log-level, /api/logs → 404 через host.docker.internal:61118 | Без credentials, чтения тел и mutating requests; четыре пути/один endpoint, не проверка всех APIs/методов/host-сервисов |

Сверенные source/live hashes: launcher `52848cda49fecb4d78589e9979781a28d114a92f694cf75bc66ea6d4412eb93b`; control `605f9d54a0a35ff3011dc44356a733f975a8993f1225ff53378a6b7880a193c5`; probe `f300ef82966ac0b12a981143d3f8ae4062f129699ab6c6e3234a790c2b747105`.

Теперь вывод о startup Bridge основан на source bytes, совпавших с действующими Windows-файлами. В этих launcher/probe нет hash-проверки Linux Bridge перед его исполнением. F-R-05 остаётся unresolved: evidence gap уменьшился, защита пути не внедрена.

Положительный /healthz показывает конкретную доступность host loopback-сервиса из Repo через Docker host alias. Это предусмотренная узкая диагностика, не установленный обход прав. Выбранные admin GET404 и совпавший narrow artifact подтверждают лишь соответствующую поверхность. F-R-06 сохраняется: изоляцию от всей host/LAN сети заявлять нельзя.

**F-R-07 — Risk, conditional/unresolved:** широкое Modify для Authenticated Users на выбранных доверенных Windows tool paths может позволить подмену runtime коду иной Windows-учётки, на которую не распространяется соответствующий Deny. Это наблюдаемые ACE и условный механизм, не выполненный access/подмена-тест. Нет доказательства записи G1, доступа Linux UID1000 к C:\Tools или существования конкретного другого атакующего token. Review HIGH; Intervention NEXT перед заявлением защиты runtime от произвольной другой локальной учётки; не blocker подготовки Linux Bridge protection. Gate — определить защищаемые principals и нужные updater/maintenance права, затем проверить относящийся effective access без реальной подмены.

**PR-A-11 — assistant/pending, условный:** при необходимости защиты от иных локальных Windows principals сузить write/modify на выбранных trusted tool/install paths до известных maintainers с сохранением нужного RX и обновлений. Это независимый ACL Proposal, не обязательный перенос Repo в другой профиль и не автоматическое удаление нынешних Deny. Цена — настройка update/maintenance permissions и проверка/recovery; применять только отдельной конкретной единицей.

Microsoft [AccessCheck](https://learn.microsoft.com/en-us/windows/win32/secauthz/how-dacls-control-access-to-an-object) и [well-known SIDs](https://learn.microsoft.com/en-us/windows/win32/secauthz/well-known-sids) использованы для интерпретации token/group/Allow/Deny semantics. Полный effective access не выведен из одного группового Allow.

Повторный ручной запуск текущего collector сейчас не нужен. Для подготовки PR-A-07 достаточно новых hashes/config/process metadata; effective firewall policy, иные host endpoints и полный audit Windows permissions остаются отдельными пределами исследования.

## Уточнение пользователя: возможные junction в Repos

Пользователь сообщил предположение: репозитории прежде находились в разных местах, а объединение в один каталог могло быть сделано junction, без физического переноса. **Это сообщение пользователя с неопределённостью, не проверенная карта ссылок/целей.** Наличие, тип, расположение и работа таких ссылок из нынешнего Docker не исследовались.

Подтверждённые mount Source/Destination/RW остаются фактами конфигурации. Однако по строке `C:\Users\alexa\Repos` нельзя считать доказанным, что все фактические данные физически лежат только там. Windows junction может указывать на иной локальный каталог/том; конкретное поведение такого пути в данном Docker Desktop/file-sharing слое нужно устанавливать отдельно. Возможны доступность цели, иное представление ссылки или ошибка разрешения; ни один вариант здесь не объявляется проверенным.

Это расширяет прежний F-R-02 и его evidence gap: неизвестна фактическая карта выданных ресурсов при переадресации. Не установлены container escape, доступ ко всему C:, обход ACL или успешное чтение конкретной внешней цели. Новое уточнение не делает прежние ограниченные mount/file observations ошибочными.

**PR-A-12 — assistant/pending:** перед сужением mounts, миграцией/«исправлением» Repos и обещанием минимальной границы данных подготовить адресную карту `путь в Repos → тип ссылки → записанная Windows-цель → представление в Repo → фактически разрешённый ресурс`.

Достаточная подготовка следующей единицы:

1. Согласовать конкретные roots/уровни каталога; сначала сами roots/предки и места размещения репозиториев. Получать Windows reparse/link metadata без рекурсивного перехода через ссылки и без чтения содержимого их целей. Не использовать слепой рекурсивный обход всего профиля.
2. Сопоставить с нынешними mounts и адресным представлением известных путей из Repo. Обнаруженный адрес посторонней цели не расширяет поручение; для уже выданного проекта сохраняется прежняя авторизация без повторного запроса. Если проверка поведения выходит за неё и требует иной цели или синтетического control, определить отдельный узкий scope; прежний Godot marker не повторяется автоматически.
3. Отдельно учесть циклы/вложенные ссылки, возможность изменения ссылок и границу будущих доступов. Карта текущих ссылок сама по себе не является enforcement.
4. После карты выбрать: сохранить намеренные junction и явно учесть ресурс; монтировать нужные физические каталоги явно; либо подготовить реальный перенос с обновлением потребителей. Не объявлять перенос обязательным до оценки пользы/цены.
5. Перед возможной миграцией учесть Git worktree metadata/исходные и незакоммиченные файлы, backup вне записи агента, пути IDE/скриптов/launcher/Docker и проверку восстановления. Не удалять junction/оригиналы и не копировать/перемещать репозитории до отдельного конкретного плана и разрешения.

PR-A-12 — prerequisite проверки фактических данных для соответствующего PR-A-08/миграции. Он совместим с PR-A-07: защиту Linux Bridge в отдельном ext4 volume можно готовить без переноса Windows-репозиториев. Перед итоговой гарантией, что Windows launcher/pin недоступны рабочему коду, учесть возможные aliases к ним через выданные roots. Возможность исправления остаётся будущим вариантом; сейчас выполняется только фиксация контекста, без обхода targets/нового файлового аудита/изменения настроек.

Первичные источники: Microsoft [junctions](https://learn.microsoft.com/en-us/windows/win32/fileio/hard-links-and-junctions) и [reparse points](https://learn.microsoft.com/en-us/windows/win32/fileio/reparse-points). Они подтверждают Windows-механизм, а не конкретную доступность целей из этого контейнера.

## Текущий фокус: сеть и необходимость Bridge — WF-021

Пользователь отложил junction и выбрал сетевую политику/функцию Bridge. [Фокусное исследование](repo-network-and-mcp-bridge-20261025.md) показывает, что Bridge — presentation/stdio adapter, не обязательный MCP security слой. Direct/backend isolated comparison PASS(scope): одинаковые26 tools/schemas; различаются UI/resources/serverInfo. PR-A-13 assistant/pending — ALTERNATIVE_TO PR-A-07, actual Windows/client compatibility ещё не проверена. F-R-05 не устранён реальным переключением; риск не означает новых Windows/root прав.

Для сети подготовлен [read-only ActiveStore/Hyper-V/backend collector](../tools/Read-RepoNetworkPolicy.ps1). Текущих inspect/probes недостаточно для вывода о конкретных firewall rules. Никакие правила/runtime entry/профили/mounts не менялись; PR-A-09 и прочие меры pending. Подробные функции, ограничения, методы, вариант прямого запуска и команда ручного сбора — в одном фокусном результате.

## Источники, target и метод

- Начальный Git HEAD документации: `0f091aa43d72c9b54e42ffc695fdede9679e956b`; дерево/index чистые. AGENTS и протокол agent-workflow после `b16ebad` не менялись.
- Действующий контейнер: `c6d7be9fe6eb`, тот же короткий ID, что в прежнем срезе. Контрольная временная отметка: `2026-10-24T19:47:48.310633+00:00` = 25 октября, 02:47:48 Asia/Bangkok.
- Переиспользованы [отчёт registry/Repo](software-registry-and-paths-20261024.md), WF-013–WF-014 в [JOURNAL](../JOURNAL.md), `fd2193a` и `80f500e`; источник приоритета направления — `c21d48f` и прямые уточнения пользователя.
- Новые данные: текущие process/module/permission metadata, inode flags, выбранные конфигурационные определения установленного DC, cgroup limits, маршруты/DNS/listening metadata; два адресных подключения к стандартным Docker API и два HEAD-запроса к публичным dependency destinations.
- Не проводились сканирование портов/сети/содержимого Repos, чтение секретов/credentials/логов, запись/подмена runtime, marker-тест, повторный software inventory, установка зависимостей, Windows/G2-вызовы, restart, CI или публикация.

## Карта доступа и ограничений

Под «кодом» здесь понимается обычный процесс с теми же UID/правами внутри нынешнего Repo. Отдельные дополнительные credentials или полномочия, выданные конкретному процессу позднее, требуют отдельной оценки.

| Ресурс / действие | Доступ агента и кода | Чем ограничено | Подтверждено | Неизвестно / мера и удобство |
| --- | --- | --- | --- | --- |
| Repos и Workfiles | Чтение/запись по выданным RW roots; изменения отражаются на Windows | Реальные mounts/FS permissions; не обещание выбранного проекта в тексте | Оба roots RW; mode 0777, текущий UID имеет W; полный nested-content scan не выполнялся | Какие материалы действительно должны быть общими. Сохранение roots удобно; сужение — отдельная настройка. В обоих случаях нужен независимый backup |
| Внутренний `/workspace/repo` | RW volume, рабочий UID1000 владеет корнем | Отдельный volume и права | mode 0755, UID/GID1000, RW ext4 | Восстановление/квоты не проверялись. Не использовать агент-доступный volume как единственную защищённую резервную копию |
| ОС и установленные Node/DC | Нет обычной записи в read-only корень и проверенные бинарники | Root ro, UID1000, capabilities=0, NNP=1, seccomp mode2 | `node` и main DC module root-owned, не writable, parents не writable | Не установлены точный seccomp profile, Docker Desktop/Engine patch level и отсутствие уязвимостей |
| Действующий MCP Bridge | Нет прямой записи в файл; путь находится в изменяемом каталоге | Только права файла, недостаточные для целостности пути | Файл root:root 0755; `.fortis` и родитель UID1000/writable; flags не immutable/append-only | Изоляция/attestation пути — PR-A-07. Нет доказательства фактической подмены или host takeover |
| Настройки DC и разрешения tools | Настройки доступны рабочему UID; shell имеет OS-доступ вне file-tool allowlist | MCP checks применяются к конкретным tools; системные ограничения отдельно | Config UID1000 0644, parent UID1000 0755; поля blockedCommands/allowedDirectories конфигурируемые; live Bridge пересылает tools/call | Это защита от части ошибок, не независимый барьер от произвольного кода. Не строить гарантию на одном blocklist |
| Docker control | В прежнем scope нет стандартного socket; выбранные TCP endpoints недоступны | Отсутствие выданного стандартного socket; отказ выбранных соединений | DOCKER_HOST/CONTEXT/CERT_PATH не заданы; 2375/2376 host alias → ConnectionRefused | Другие sockets/TCP/SSH/proxies и точная host policy не исключены. Не выдавать Docker socket/credentials ради удобства |
| Host/LAN и интернет | Есть сетевой маршрут; публичный HTTPS работает; host aliases разрешаются | Наблюдаемые правила сети/host, полностью не установлены | Default route; DNS aliases; GitHub/npm HEAD200 | Запрет иных host/LAN endpoints не доказан. Нужна адресная egress-политика с сохранением нужных downloads/API, без общего отключения сети |
| Соседние процессы/локальные сервисы | Общие UID и network namespace не создают независимой границы задач | Имеющиеся OS controls; отдельной task-изоляции не установлено | MCP и наблюдённые Python listeners UID1000; среди них контейнерный Observatory 127.0.0.1 | API/данные сервисов не трогались. Loopback контейнера сам по себе не защищает от кода того же контейнера; это не приёмка Observatory |
| Ресурсы | Работа ограничена общей ёмкостью контейнера | Cgroups | memory.max=1073741824; cpu.max=200000/100000; pids.max=256 | Disk/traffic/API-cost quotas и независимость задач не подтверждены; рост файлов и платные API требуют отдельных лимитов по задаче |
| Windows launcher/runtime/key | Selected metadata получены ручным сбором пользователя; Windows token автоматически в Linux не передаётся | Windows permissions и narrow runtime | Live hashes run/control/probe совпали с source; runtime artifact совпал с E38; key DACL protected; host health200/admin GET404 | Полные effective ACL, patch level и host/firewall policy не проверены. Отдельная Windows-учётка Repo не предлагается |
| Windows-запуск результата | Опционально основной или тестовый аккаунт по выбору пользователя | Права выбранного Windows token/ACL | Пользовательское решение | Не устраняет уже совершённую запись из Repo в RW mounts; функциональный PASS не доказывает безвредность всего кода |

## Новое evidence с точными пределами

### Действующая цепочка и доверенные файлы

В `/proc` установлена текущая цепочка: Node PID137 с модулем `/workspace/repo/.fortis/mcp-bridge.mjs` → Node PID149 с `/opt/dc/node_modules/@wonderwhy-er/desktop-commander/dist/index.js`. Оба UID/GID1000; CapInh/Prm/Eff/Bnd=0, NoNewPrivs=1, Seccomp=2. Это наблюдение реально работающей Linux-цепочки, а не только копии исходников.

| Объект | Владелец / mode | W для UID1000 | Parent W | Hash / дополнительное evidence |
| --- | --- | --- | --- | --- |
| `/workspace/repo` | 1000:1000 / 0755 | да | нет | inode flags 0x81000; не immutable/append-only |
| `/workspace/repo/.fortis` | 1000:1000 / 0755 | да | да | flags 0x80000; не immutable/append-only |
| `mcp-bridge.mjs` в этом каталоге | 0:0 / 0755 | нет | да | flags 0x80000; SHA256 `8389436658e22f213d9865a78872159e027ca33094999db64ca96b5a7c79fc21` |
| Установленный DC main module | 0:0 / 0755 | нет | нет | SHA256 `a4145198dc75cd34e7c7452c2054b4cc0d29e199ae1459961a17e4da25a13500` |
| `/usr/local/bin/node` | 0:0 / 0755 | нет | нет | На read-only корне |
| `/home/node/.claude-server-commander/config.json` | 1000:1000 / 0644 | да | да | Значения файла не выгружались; определения configurability прочитаны в установленном коде |

Hash live Bridge совпадает с записанным в E38. Его 62 строки читаемого live-кода изменяют presentation/initialize и пересылают запросы upstream; обязательного per-call policy gate там нет.

**Вывод по правам:** в Linux удаление имени файла определяется в том числе правами каталога, а не только owner/mode файла. С учётом W+X на `.fortis`, RW mount и отсутствия sticky/immutable/append-only барьеров замена имени Bridge доступна по проверенным метаданным. Это вывод из прав и семантики ОС, не выполненный destructive test. Уже загруженный процесс не объявляется автоматически переписанным; риск существенен для следующего запуска/переподключения.

Прочитаны E38 AFTER [source launcher](../../../runtime/host-g2/runtime-api-migration/repo-run-tunnel.ps1) и [source probe](../../../runtime/repo-mode/probe.mjs). Launcher pin-проверяет Windows runtime EXE, запускает probe, затем выполняет Bridge из RW volume. В этих source bytes нет проверки hash Bridge; probe сам исполняет Bridge для проверки MCP. Код probe также выполняет временные записи и настройки — **он не запускался** при этом обзоре. После ручного fingerprint run/control/probe совпали с этими source bytes; этот gap для трёх файлов закрыт на момент сбора.

Readonly Bridge уменьшит риск персистентной подмены, но не изолирует произвольный код от MCP-процессов/данных с тем же UID. Более сильная task-изоляция — отдельный Linux UID/worker-container с ограниченными входами — возможная отдельная мера для действительно враждебных входов; она не требует отдельного Windows-профиля и сейчас не внедряется.

### Сеть и управление

- `host.docker.internal` → `192.168.65.254`; `gateway.docker.internal` → `192.168.65.1`. Default route наблюдался через `172.18.0.1`. DNS/route не доказывают успешный доступ к каждому сервису.
- Попытки GET `/_ping` через `host.docker.internal:2375` (HTTP) и `:2376` (TLS с проверкой сертификата) завершились ConnectionRefusedError/errno111 ещё на установлении соединения. Успешного HTTP/TLS/API-сеанса не было; мутации Docker не отправлялись.
- HEAD `https://github.com/` и `https://registry.npmjs.org/` с проверкой TLS вернули 200, без credentials/body downloads/установки.
- В окружении MCP-процессов по именам не найдены выбранные TOKEN/SECRET/PASSWORD/API_KEY/CREDENTIAL шаблоны; значений env не выводили. Это не полный поиск всех секретов.
- Наблюдались loopback listeners контейнера и DNS stub. Их порт-список не является Windows port inventory. К API Observatory и соседнего проекта не обращались; исходники/данные соседних задач не читались.
- Наличие действенной политики запрета private/host адресов не подтверждено. Непубликация container ports относится к входящему маршруту и сама по себе не запрещает исходящие соединения.

## Findings и меры для следующего решения

| ID / тип / disposition | Что решает | Review / Intervention / следующий gate |
| --- | --- | --- |
| F-R-02 / Risk / unresolved, прежний | Широкие RW roots дают доступ ко всему доступному внутри них, не только текущему заданию; актуальное содержимое не инвентаризировалось | HIGH / NEXT перед обещанием «только выбранные данные». Выбрать намеренно общие области и независимый backup; без сканирования личного содержимого |
| F-R-05 / Risk / unresolved | Путь live Bridge может быть заменён рабочим UID; matched live launcher/probe не проверяют hash Bridge | HIGH / NEXT перед опорой на неизменяемость MCP runtime. Source/live gap закрыт; подготовить PR-A-07 |
| F-R-06 / Risk / unresolved | Actual host runtime health доступен из Repo; выбранные admin GET404 не покрывают другие сервисы/API | HIGH / NEXT перед заявлением изоляции host-интерфейсов. Определить нужные маршруты/политику, не сканируя все сервисы |
| F-R-07 / Risk / conditional, unresolved | Authenticated Users Modify на selected trusted Windows paths; G1-specific Deny ограничивает вывод для G1 | HIGH / NEXT перед общей гарантией против иных локальных Windows principals; effective access не проверялся, PR-A-11 условен |

Компрометация, фактическая подмена Bridge, захват Docker или чтение всего личного профиля не установлены. Неподтверждённые Windows ACL/patch level — evidence gaps, не самостоятельный пятый Finding Type.

| Proposal / статус | Достаточная мера и проверка | Влияние на удобство |
| --- | --- | --- |
| PR-A-07 / assistant, pending | Хранить Bridge и доверенные части runtime в read-only image либо отдельном RO mount с защищённым путём; pin/проверку держать вне агент-writable области и выполнять до исполнения. Проверять защиту всей цепочки parent directories; одной смены mode файла недостаточно | Рабочие проекты остаются RW; обычные команды/зависимости сохраняются. Потребуются отдельные update image/mount/launcher/probe и проверка/recovery; сейчас не применено |
| PR-A-08 / assistant, pending | Явно признать общими текущие roots либо предложить более узкие рабочие roots под задачи; резервная копия/восстановление вне области записи агента | Первый вариант проще, но допускает ущерб всему выданному дереву. Второй требует настройки при смене области; не требует отдельного Windows-профиля |
| PR-A-09 / assistant, pending | Нужные внешний HTTPS/DNS/API сохранить; ненужные host/LAN/control маршруты ограничить вне управления рабочего кода. Перед правилами определить необходимые исключения и проверить обе стороны | Не вводить blind block всех private/loopback адресов: можно нарушить DNS, локальные интеграции и Observatory. Windows Docker backend может обслуживать другие контейнеры — глобальные правила требуют оценки |
| PR-A-10 / assistant, pending, условный | При требовании исполнять потенциально враждебные зависимости/локальные ИИ с более сильной границей отделить рабочий код от MCP/control по Linux UID/worker-container и входам | Дополнительная оркестрация/обмен/лимиты. Не обязательный перенос Windows-аккаунта и не prerequisite обычной работы с доверенными проектами |

PR-A-07 совместим с PR-A-08/09 и не требует их атомарного применения. Он требует конкретного дизайна защищённого live target и обновления startup checks, если меняется путь/mount/image. PR-A-08/09 остаются отдельными решениями о границе данных/сети. PR-A-10 условен модели доверия и не принимается авансом. Git-коммит отчёта не внедряет эти Proposals.

Сохраняются все S-01–S-07: write/build/test, игры, media/3D/audio/local AI, CI и обмен с Observatory. Усиление не должно превращать каждую обратимую команду в ручное разрешение. Нужные зависимости устанавливаются в выданной рабочей области; системный read-only образ меняется отдельной доставкой.

## Ручной Windows-сбор и оставшиеся ограничения

Первоначальные gaps выбранных Windows hashes/ACL/listener/Docker metadata теперь закрыты ручным результатом пользователя (дополнение выше). Полная host/firewall policy, effective access всех principals и все endpoints остаются за пределами результата. Обход через G2 или новые mounts не выполнялся.

Пользователь уже выполнил [Read-RepoHostBoundary.ps1](../tools/Read-RepoHostBoundary.ps1) из обычного `FORTIS_M\alexa` PowerShell. Команда сохранена для воспроизводимости; повтор сейчас не нужен:

```powershell
& 'C:\Users\alexa\Repos\tunnel\docs\agent-workflow\tools\Read-RepoHostBoundary.ps1'
```

Скрипт печатает только выбранные file hashes/ACL, Repo runtime process/listener metadata, выбранные Docker inspect/network fields. Он не выводит process command lines, полный profile/env, key contents или key hash; не запускает launcher/probe и не меняет настройки. Нет доступа к Docker/ACL — в результате будет отдельная ошибка без повышения прав. Для нулевого числа processes есть limitation о доступности profile matching.

Это адресный набор недостающих metadata, не software inventory и не полный host-аудит. Первоначально код проверялся чтением; затем пользователь выполнил ручной запуск, сформировавший прочитанный корректный JSON без ErrorType в выбранных полях. Отдельная AST-проверка агентом не выполнялась; сверка source/live hashes и анализ selected ACL/listeners завершены. Effective firewall policy и неизвестные endpoints этим скриптом полностью не доказываются.

## Достаточность и дальнейшая работа

Исследования доступной Repo-части завершены в этом scope: получено новое необходимое evidence, ограничения сформулированы, меры и их цена выделены. Ручной сбор завершён; оставшиеся policy/effective-access/endpoint ограничения перечислены. Не требуется повторять registry/marker, собирать весь Windows inventory или переносить Repo в другую Windows-учётку для продолжения.

Ближайшая техническая единица после выбора меры — подготовить конкретную реализацию PR-A-07 с проверкой неизменяемости trusted path и сохранением рабочего сценария. Основные live metadata для подготовки получены; перед применением актуализировать только действительно изменившиеся prerequisites. Применение, restart, изменение mounts/ACL/network, новая сильная изоляция, Windows-запуск результатов и публикация остаются отдельными действиями.

## Первичные внешние источники интерпретации

- [Docker: bind mounts](https://docs.docker.com/engine/storage/bind-mounts/) — RW/RO host data и отдельность mounts от rootfs.
- [Docker: Engine security](https://docs.docker.com/engine/security/) — namespace/control/daemon границы.
- [Docker Desktop: networking](https://docs.docker.com/desktop/features/networking/) и [host aliases](https://docs.docker.com/desktop/features/networking/networking-how-tos/) — направления сети и host connectivity.
- [Docker: remote access](https://docs.docker.com/engine/daemon/remote-access/) — выбранные стандартные 2375/2376.
- [Linux man-pages: unlink(2)](https://man7.org/linux/man-pages/man2/unlink.2.html) и [chmod(2)](https://man7.org/linux/man-pages/man2/chmod.2.html) — права каталога/файла и изменение owner-controlled mode.
- [Docker: seccomp](https://docs.docker.com/engine/security/seccomp/) — mode/profile различаются; наличие фильтра не доказывает выбранную политику.

Официальные документы объясняют модель, но не заменяют перечисленные наблюдения этой установки.
