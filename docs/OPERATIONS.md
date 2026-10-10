# Запуск, панели, остановка

## Native HOST

Ярлык **Desktop Commander Secure Tunnel** запускает:
C:\Users\alexa\Documents\prot\Start-Desktop-Commander-Secure-Tunnel.ps1

Профиль desktop-commander лежит в %APPDATA%\tunnel-client\desktop-commander.yaml. MCP command:
```text
cmd.exe /c C:/Tools/desktop-commander/desktop-commander-trusted.cmd
```
Обёртка выставляет DESKTOP_COMMANDER_DISABLE_MCP_UI=1. Клиент: C:\Tools\tunnel-client\tunnel-client.exe, Desktop Commander 0.2.52.

Локальная техническая панель: http://127.0.0.1:8080/ui. Закрытие окна запуска останавливает этот туннель. Повторный запуск не должен создавать второй процесс с тем же listener.

Ошибка bind 127.0.0.1:8080 означает занятый порт. Сначала определить OwningProcess и профиль; не завершать любой процесс только по номеру порта.

## Native Repo

Ярлыки **Fortis Repo Start** и **Fortis Repo Web** используют:
C:\Users\alexa\chatgpt-repo-mode\control.ps1

Меню: C:\Users\alexa\chatgpt-repo-mode\Fortis-Repo-Control.cmd

```powershell
$control = 'C:\Users\alexa\chatgpt-repo-mode\control.ps1'
& $control -Action Status
& $control -Action Start
& $control -Action OpenPanel
# Для отключения ChatGPT:
& $control -Action StopAccess
# Для остановки также вычислений контейнера:
& $control -Action StopContainer
```

Start запускает run-tunnel.ps1: проверка контейнера, восстановление временной MCP/Git конфигурации, проверка bridge, doctor профиля, затем tunnel-client run. Ключ берётся из уже сохранённого файла. Повторно вводить его при обычном запуске не нужно.

Repo listener выбирает свободный loopback port (127.0.0.1:0). OpenPanel находит процесс по точному Repo Tunnel ID в metrics и открывает его /ui. Постоянный адрес для Repo панели не задан.

Native MCP command:
```text
docker exec -i fortis-repo-test node /workspace/repo/.fortis/mcp-bridge.mjs
```

StopAccess отключает Repo Tunnel; фоновые команды/контейнер могут продолжить работу. StopContainer также останавливает проверенный контейнер. Ни одна команда не удаляет host-файлы или volume и не останавливает HOST Tunnel.

Панель /ui показывает техническое состояние tunnel-client. Это не UI для выдачи доступа к папкам, управления всеми репозиториями или изменения Docker mounts. Права задаются в конфигурации и проверяются probe; «тумблер интернета» в нашей панели не реализован.

## Диагностика и безопасное восстановление

```powershell
& 'C:\Tools\desktop-commander-runtime\node.exe' 'C:\Users\alexa\chatgpt-repo-mode\probe.mjs' --check-internet
```

Доступность внешнего сайта не обязательна для обычного запуска. Интернет-проверка запускается отдельно.

При 409 «MCP server is not initialized» или timeout:
1. Выполнить один лёгкий read-only запрос/проверку статуса.
2. Различить локальный процесс, MCP handshake конкретного чата и Site proxy.
3. После неопределённой записи/команды проверить файл, Git или процесс перед повторением.
4. При живом daemon сначала обновить подключение/сессию. Общий restart не должен быть первой реакцией на один сбой.
5. Перезапускать только установленный нужный контур, затем проверить состояние.

Docker mkfs «disk apparently in use» после очистки виртуальных дисков не исправлять принудительным форматированием неизвестного /dev/sd*. Остановить Docker, выполнить контролируемый restart WSL/Docker, проверить используемые диски. Reset/Delete volume — отдельное разрушительное действие, не обычная диагностика.

Полные прежние расследования сохранены в [history](../history/README.md).
