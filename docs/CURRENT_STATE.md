# Текущее состояние — датированный срез

**Последняя предметная проверка Broker/Bridge: 2026-10-11.** Это запись наблюдений, **не динамический список допусков**; перед новым snapshot сверять live `list/preview` и состояние Windows Task. Для действий: [SNAPSHOT.md](SNAPSHOT.md) → [Broker runbook](../runtime/broker/README.md). Для объяснения архитектуры, всех этапов и E2E evidence: [BROKER_V2_PLAN.md](BROKER_V2_PLAN.md).

## Windows Bridge/Broker V2 — подтверждённые факты

| Что | Проверенный срез |
|---|---|
| Broker Task `FortisRepoBridgeBrokerV1` | **Enabled, Ready (остановлена)**; ручной start/stop, без logon trigger и RestartOnFailure |
| Windows `repos.json` | **20 alias**; **17** standing `broker_snapshot_enabled=true` для приватного транспорта, `selection_mode=all`, `respect_gitignore=true`, без пользовательских `.snapshotignore` |
| Не включены | `obs`: ~59 тыс. Git-кандидатов, более 719 МБ до ошибки пути, превышены лимиты; `theory-conspects-and-banks`: 15 файлов с сигнатурами возможных OpenAI-ключей; публичный synthetic `test` |
| Исправления | Windows long path в Bridge (`research-and-bank`: 1 307 файлов / 31 059 466 байт, total limit 35 МБ); `obs-planning-docs`: 1 183 файла / 13 143 358 байт; оба full preview проходят |
| Тесты | Python compile, Bridge selection tests, Broker offline **12/12**; для 17 разрешённых alias — read-only preflight, **не 17 реальных GitHub E2E** |
| Реальные V2 E2E | **2 на `test-private`**: Actions run `38130685868` / Artifact `11697988578` и run `38130962007` / Artifact `11698538347`; оба 8 файлов, 13 510 байт, независимо сверены SHA-256/manifest в ChatGPT |
| Известное восстановление | Второй Git push прервался из-за сети: повторно отправлен **ранее созданный commit**, не новый snapshot; `recover` вернул прежний запрос/Artifact |
| Текущий экспорт | Транспорт `AlexPastukhh/chatgpt-snapshot-transfer` **private**. Право на будущие snapshot **не означает**, что данные 17 проектов уже опубликованы. Новых ZIP при широком включении не создавалось |
| Хранение исходников | Windows worker/Bridge — live вне Docker RW; `runtime/broker/` в локальном `tunnel` — исходник, **не автодеплой**. Git рабочий каталог ранее содержал чужие несвязанные правки/untracked V2; push исходников не подтверждён |

**Границы безопасности:** любые будущие Git-видимые подходящие файлы 17 alias могут оказаться в ZIP во время manual Broker-on. Mandatory excludes, size/secret/path/SHA256 checks сохранены; проверка сигнатур не исключает неизвестные секреты. Очередь Workfiles не аутентифицирует sender (ранее явно принятый риск). Ограничение ZIP **не** скрывает директории `Repos` от Fortis Repo, которому они смонтированы. ZIP в приватной Git history не удаляется вместе со сроком Artifact.

**Нерешённое:** снять реальные блокировки `obs` и `theory-conspects-and-banks` только после отдельной технической проверки; integration fault-injection на остановке в середине публикации не завершён; не утверждать, что live E2E выполнен на всех 17. Старый `bridge-v2-windows.patch` не устанавливать поверх живого исправленного Bridge.

## Другие контуры — срез 2026-10-10 (исторический)

Ниже сохранён **исторический срез от 2026-10-10**. Его статусы процессов, прав и подключений **не заменяют** живую проверку; актуальные документы по snapshot приведены выше.

| Контур | Идентичность | Назначение и граница |
|---|---|---|
| Native HOST | profile desktop-commander; tunnel_6ac4a7249a4081918eb0881c870acf07 | Windows Desktop Commander, широкий доступ HOST; не sandbox |
| Native Repo | profile repo-mode; tunnel_6ac9e4dc9e688191ae1838e858424e8d | Desktop Commander внутри fortis-repo-test |
| HOST Site | Desktop Commander · prot, версия 4 | Отдельный HTTP MCP proxy к upstream; Site-аудитория — отдельная граница |
| Repo Site | Fortis · Repo Mode, версия 7 | Отдельный диагностический Site; его file/terminal gate ещё не активирован |

Native Repo работает независимо от настройки Site. Нельзя заключать «Docker-туннель не работает» по ответу не настроенного Site.

### Docker на срезе 2026-10-10

| Windows | Linux | Доступ |
|---|---|---|
| C:\Users\alexa\Repos | /workspace/repos | bind, чтение и запись |
| C:\Users\alexa\Workfiles | /workspace/files | bind, чтение и запись |
| Docker volume fortis-repo-workspace | /workspace/repo | внутреннее хранилище |

Контейнер **fortis-repo-test**, ID **c6d7be9fe6eb4138a9dc47db3f82c32c377007c2d461c1f03ad37fe9bb3d074a**. Рабочий каталог /workspace/repos. Сеть **fortis-repo-egress**, исходящий интернет включён; опубликованных портов нет. uid/gid 1000:1000, root filesystem read-only, cap-drop ALL, no-new-privileges, без Docker socket, 2 CPU, 1 GiB RAM, pids limit 256, restart policy no.

HOME и /tmp — временные tmpfs. Git safe.directory добавляется для конкретных Git-корней, не глобальным wildcard; core.autocrlf=true соответствует HOST. Настройки и ограничения проверяет probe.mjs перед запуском.

На проверке в ходе переноса документации контейнер **running=true**, но Repo Tunnel не был найден локальным control.ps1. Это не постоянная настройка; актуальный ответ даёт Status.

Старый контейнер **fortis-repo-test-before-access-20261010t112331268z** оставлен остановленным для отката. Данные volume сохранены.

### Проверено 2026-10-10

Двусторонние тестовые записи в обоих bind-каталогах; чтение Git-корней; HTTPS GitHub/NPM; схемы и MCP presentation; запрет файлового чтения вне разрешённых каталогов. Контрольные файлы удалены. Это не доказательство невозможности доступа shell к сетевым службам HOST.

Windows Git credentials в контейнер не перенесены. Для private push нужна отдельная настройка авторизации.

### Было не реализовано на срезе 2026-10-10

- Repo Site ещё не подключён к подходящему upstream endpoint и не разблокирован.
- Sandbox GUI / Windows VM — планы, не установленная возможность.
- Нет отдельной изоляции каждого чата и универсальной веб-панели управления разрешениями.
- Site Repo README/deployment snapshot и некоторые его тексты отстают от текущих Windows mounts / интернета / saved key. Их нельзя использовать для восстановления текущего контейнера. В этом изменении Site не перепубликовывался.

[Управление](OPERATIONS.md) · [Site и версии](SITES.md) · [Обновление слоёв](INSTRUCTIONS.md)

**Где история V2:** в [плане V2](BROKER_V2_PLAN.md), разделы Implementation Log и E2E; там сохранены промежуточные состояния с прежними цифрами и ограничениями. Они **не актуальные инструкции**.
