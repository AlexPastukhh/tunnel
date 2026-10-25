# Доступ, ключи и интернет

Маршруты и границы доверия — в [ARCHITECTURE](ARCHITECTURE.md); аудит вызовов и будущий Policy Gate — в [AUDIT](AUDIT.md). Настоящий документ отвечает за источники **действующих полномочий**, а не за систему логирования.

## Актуальное уточнение Fortis Repo / Tunnel — 25.10.2026 (WF-048)

Два Repo из разных браузерных профилей теперь используют **Direct Linux Desktop Commander** в одном контейнере, 0 активных Bridge в последнем read-only срезе. Не использовать сохранённые ниже исторические описания `probe.mjs`/старого Bridge как команду для текущего запуска или как доказательство полной защиты. [Текущая security/изоляционная карта](agent-workflow/TUNNEL_SECURITY_ISOLATION.md) — V-01–V-15, F-R и P-01–P-12. В частности, `C:\Tools` Windows binaries имеют **Authenticated Users: Modify** (FortisHostG1-specific Deny наблюдён, полный effective access не установлен), второй Tunnel key/profile ACL ещё OPEN, Docker host/LAN API policy OPEN. **Не менять** ни ключи, ACL, Docker mounts, ни установку только ради этой документальной корректировки.

## Дополнительный проектный scope — 24.10.2026

Отдельное вручную применённое разрешение G2 на один Godot-проект, реальные Repos/Workfiles mounts и пределы последующей проверки поддерживаются в [agent-workflow/STATE](agent-workflow/STATE.md); источник решения, backup reference и откат — в [JOURNAL](agent-workflow/JOURNAL.md). Этот scoped результат не расширяет начальный scope на весь Repos/owner-профиль и не является новым полным security PASS.

## Где задаётся доступ

G2 и Repo — разные native routes. Old owner HOST stopped E43, его key/connector сохранены для intentional recovery. Repo имеет Windows RW mounts, а Site project root не sandbox. [Итог](ISOLATION_GUIDE.md).

Для Repo реальные границы файлового доступа определяют Docker mounts. /workspace/repos и /workspace/files — writable Windows-папки: изменения и удаления сразу видны на HOST. MCP allowedDirectories помогает файловым инструментам, но не является самостоятельной защитой от shell.

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

workspace-config.json + probe.mjs описывают и проверяют **фактический** контейнер. Изменение JSON само не меняет mounts/network Docker. При добавлении папки или изменении сети:
1. Определить нужный host каталог и доступ read-only/read-write.
2. Проверить, что в mounts не попадут весь home, ключи, Docker socket или лишние credentials.
3. Подготовить контейнер с ожидаемой конфигурацией, сохранить прежний контейнер/volume для отката.
4. Сверить новый immutable container ID, mounts, network и ограничения; лишь затем обновить gate config.
5. Проверить доступ, отказ вне разрешённых папок, интернет при необходимости и оба направления записи собственным marker.
6. Удалить marker, перезапустить Repo Tunnel и обновить текущие документы.

Не отключать probe ради обхода несоответствия. StopAccess — отзыв доступа ChatGPT; StopContainer — также прекращение вычислений. Не публиковать native health UI наружу.

## Предложение о рабочих и закрытых областях, 2026-10-13

[Матрица G2/Repo, удобное управление и ограничения clipboard/browser](G4_ACCESS_POLICY_PROPOSAL_2026-10-13.md) — DRAFT, не применённая политика. Folder ACL, Docker mounts, сеть и window-station/clipboard capabilities требуют разных механизмов. Существующий guest Workspace уже проверен как baseline; дополнительные roots выдаются по задаче, G4/G5 acceptance не завершены. Исторический DRAFT не запрещает собственный guest GUI и не требует универсального ACL manager. Текущие условия — в плане G2.
