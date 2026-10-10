# Доступ, ключи и интернет

## Где задаётся доступ

Native HOST и Repo имеют разные Tunnel ID и профили. Сначала выбирать нужный контур. HOST предоставляет Windows file/terminal доступ; значение «project root» в Site не превращает HOST в sandbox.

Для Repo реальные границы файлового доступа определяют Docker mounts. /workspace/repos и /workspace/files — writable Windows-папки: изменения и удаления сразу видны на HOST. MCP allowedDirectories помогает файловым инструментам, но не является самостоятельной защитой от shell.

Основной Windows GUI не разрешён. Docker не даёт Windows GUI автоматически.

Site-аудитория, доступ к native Tunnel и GitHub repository permissions — разные настройки. Наши Sites сейчас access_mode=custom; сохранять текущий allowlist, не расширять его при перепубликации. Private GitHub repo также не делает небезопасный endpoint защищённым.

## Сохранённый runtime key

Оба native профиля используют один файл:
C:\Users\alexa\AppData\Roaming\tunnel-client\runtime.key

Ссылка в профиле:
```yaml
api_key: "file:C:/Users/alexa/AppData/Roaming/tunnel-client/runtime.key"
```

Это обычный файл с ACL, не DPAPI. На проверке 2026-10-10 владелец FORTIS_M\alexa, наследование выключено, доступ только этого пользователя. Содержимое ключа не читалось при подготовке этого репозитория. Key file вне Docker mounts и вне Git.

При ротации обновить ключ локально через поддерживаемый интерфейс tunnel-client/выдавшего его сервиса, сохранить в тот же защищённый файл без вывода в чат/логи. Затем перезапустить **оба** профиля и проверить doctor + read-only MCP отдельно для HOST и Repo. Замена общего файла затрагивает оба. Не создавать новую регистрацию и новые Tunnel ID ради обычной ротации.

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
