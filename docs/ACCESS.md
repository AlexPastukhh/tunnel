# Доступ, ключи и интернет

Маршруты и границы доверия — в [ARCHITECTURE](ARCHITECTURE.md); аудит вызовов и будущий Policy Gate — в [AUDIT](AUDIT.md). Настоящий документ отвечает за источники **действующих полномочий**, а не за систему логирования.

## Текущий реестр Repo/Tunnel

Границы и датированные результаты Windows/Docker, installed fingerprints, ACL/key/network gaps принадлежат [security-реестру](agent-workflow/TUNNEL_SECURITY_ISOLATION.md). Ниже — модель полномочий; она не заменяет live-проверку. Не менять ключи, ACL, mounts или установку ради обновления документации.

## Дополнительный проектный scope — 24.10.2026

Отдельное вручную применённое разрешение G2 на один Godot-проект, реальные Repos/Workfiles mounts и пределы последующей проверки поддерживаются в [agent-workflow/STATE](agent-workflow/STATE.md); источник решения, backup reference и откат — в [JOURNAL](agent-workflow/JOURNAL.md). Этот scoped результат не расширяет начальный scope на весь Repos/owner-профиль и не является новым полным security PASS.

## Где задаётся доступ

G2 и Repo — разные native routes. Old owner HOST stopped E43, его key/connector сохранены для intentional recovery. Repo имеет Windows RW mounts, а Site project root не sandbox. [Итог](ISOLATION_GUIDE.md).

Для Repo реальные границы файлового доступа определяют Docker mounts. Рабочая папка файлов и результатов — `/workspace/repo/Workfiles`, внутренний Docker volume. Windows Workfiles не использовать. Старые binds до отдельной миграции остаются writable Windows-папками: изменения и удаления через них сразу видны на HOST. MCP allowedDirectories помогает файловым инструментам, но не является самостоятельной защитой от shell.

Основной Windows GUI/экран/clipboard сессии `alexa` защищается. Собственные guest GUI/экран/clipboard G2 разрешены в согласованном scope; начальный bounded scope принят E43 с явными ограничениями. Docker не даёт Windows GUI автоматически. Полные разрешения и критерии — [в актуальном плане G2](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md).

Site-аудитория, доступ к native Tunnel и GitHub repository permissions — разные настройки. Наши Sites сейчас access_mode=custom; сохранять текущий allowlist, не расширять его при перепубликации. Private GitHub repo также не делает небезопасный endpoint защищённым.

## Сохранённый runtime key

По датированному owner baseline два профиля **owner HOST и Repo** используют один файл:
C:\Users\alexa\AppData\Roaming\tunnel-client\runtime.key

Ссылка в профиле:
```yaml
api_key: "file:C:/Users/alexa/AppData/Roaming/tunnel-client/runtime.key"
```

G2 использует отдельную auth/profile и свой key workflow; owner key к нему не копируется.

Это обычный файл с ACL, не DPAPI. На проверке 2026-10-10 владелец FORTIS_M\alexa, наследование выключено, доступ только этого пользователя. Содержимое ключа не читалось при подготовке этого репозитория. Key file вне Docker mounts и вне Git.

При ротации обновить ключ локально через поддерживаемый интерфейс tunnel-client/выдавшего его сервиса, сохранить в тот же защищённый файл без вывода в чат/логи. Для owner Repo подготовлен [Preview/Install/Rollback script](../runtime/repo-mode/Rotate-RepoRuntimeKey.ps1), проверенный Windows AST (без запуска замены). Скрипт НЕ выпускает новый provider key, не отзывает старый, не останавливает туннель, требует owner SID и проверяет ACL. Install создаёт DPAPI backup под owner LocalAppData и заменяет существующий файл с сохранением DACL; Rollback применим только до отзыва старого ключа. Сначала новый key в OpenAI API Platform → локальный Install → controlled Repo-only restart/MCP check → отозвать старый key. Old owner HOST использовал тот же файл и остаётся выключенным; не запускать его для проверки. G2 отдельный: выпуск нового key → при следующем штатном guest LaunchTest ввод нового ключа, старый key отозвать только после проверки G2. После key rotation проверять действующий Repo doctor/read-only MCP и только затронутые активные профили. Retired owner HOST не запускать ради ротации. Не создавать новую регистрацию и новые Tunnel ID ради обычной ротации.

В Git запрещены runtime.key, реальные профили с credentials, environment dumps, credential backups и приватные upstream адреса. Идентификаторы Tunnel/Site сами по себе не являются ключами.

## Интернет / новые папки

Сеть fortis-repo-egress разрешает исходящие соединения; ports не опубликованы. Это не утверждение, что контейнер не может обратиться к HOST по сети. Git credentials Windows не наследуются.

Изменение JSON/source не меняет actual Docker mounts/network. `probe.mjs` относится к прежнему Bridge startup и не является текущим Direct preflight; не запускать его для изменения среды или read-only проверки. Текущие Direct guards и их ограничения описаны в security-реестре.

Будущая смена mounts/network требует отдельного owner plan: определить точный host resource и RO/RW scope, исключить лишние credentials/control paths, подготовить independent rollback, сверить actual container identity/security/mounts и необходимые исключения. После согласованного применения проверить positive/negative controls и только затронутые подключения. Порядок доставки — [INSTRUCTIONS](INSTRUCTIONS.md), эксплуатация — [OPERATIONS](OPERATIONS.md). Непубликация container ports не запрещает исходящий доступ к host/LAN.

## Предложение о рабочих и закрытых областях, 2026-10-13

[Матрица G2/Repo, удобное управление и ограничения clipboard/browser](G4_ACCESS_POLICY_PROPOSAL_2026-10-13.md) — DRAFT, не применённая политика. Folder ACL, Docker mounts, сеть и window-station/clipboard capabilities требуют разных механизмов. Существующий guest Workspace уже проверен как baseline; дополнительные roots выдаются по задаче, G4/G5 acceptance не завершены. Исторический DRAFT не запрещает собственный guest GUI и не требует универсального ACL manager. Текущие условия — в плане G2.
