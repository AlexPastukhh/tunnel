# WF-037 — Audit двух Direct Fortis Repo после установки (25.10.2026)

## Вопрос и граница
Проверка на текущий момент без остановки процессов, изменений Windows/Docker/профилей и чтения ключей. Точность относится к доступным живым Linux-данным, исходникам в Repo и owner-reported Windows проверкам. Это **не полный security attestation** Windows/host и не cold-reboot test.

## Первоначальная уязвимость и результат миграции
- Исходно MCP Bridge `/workspace/repo/.fortis/mcp-bridge.mjs` был root-owned, но `.fortis` и `/workspace/repo` UID1000 writable, поэтому обычный код с UID1000 способен заменить *путь* к выполняемому скрипту, несмотря на запрет прямой записи в файл. Старый Windows launcher запускал именно эту ссылку без Bridge hash. См. [WF-029](repo-protection-20261025.md).
- Теперь первый Windows launcher (PR-A-15, owner installed), второй `FortisRepo2.ps1` (owner SHA `13C1956DA1E7B7405F50B495A40225D51E42E568965A68AAFFBE404616093CDB`) и guard (owner SHA `88D5BE54F5E651BBD658BD9F84751511F9D178061EFACF4AA0F2507827CC8533`) настроены на Direct entry `/opt/dc/node_modules/@wonderwhy-er/desktop-commander/dist/index.js`. Owner reported independent Bridge-backup intact.
- Live read-only `/proc` snapshot: **2 Direct DC** (PID3400 и PID4986, оба UID1000), **0 active Bridge** (exact argv token). Первый actual client `get_config` и `read_file` PASS; другой чат owner подтвердил чтение Git metadata проекта `rd-graphs` через второе подключение. Это не проверка всех 26 MCP tools.
- **Файл Bridge не удалён**: по прежнему существует root:root 0755, не symlink; `.fortis` и `/workspace/repo` UID1000 writable. Старый путь остаётся небезопасным, но **не используется двумя live entry**. Переход на старый backup/старый профиль либо иной неаудированный клиент может вернуть проблему. Не утверждать 'Bridge физически исчез'.

## Живые runtime/security проверки
- Pinned Linux direct entry SHA-256 `a4145198dc75cd34e7c7452c2054b4cc0d29e199ae1459961a17e4da25a13500` PASS; модуль и все проверенные предки под `/opt/dc` root:root, mode755, не symlinks и недоступны на запись UID1000.
- Два Direct MCP: UID1000; CapEff=0, NoNewPrivs=1, Seccomp=2. Read-only root mount true. Стандартный `/var/run/docker.sock` не обнаружен; это не аудит всех Docker management surfaces.
- Shared DC config присутствует; `allowedDirectories` ровно `[/workspace/repos,/workspace/files,/workspace/repo]`, defaultShell `/bin/bash`, telemetry=false. `get_config` включает `blockedCommands` (33), но guards сравнивают лишь allowedDirectories/defaultShell/telemetry. Файл config UID1000 mode644, writable UID1000 — не изоляция процессов и не realtime attestation.
- `/home/node/.gitconfig` uid1000 0600, без symlink; `safe.directory=/workspace/repos/tunnel` и `core.autocrlf=true` PASS. Эти настройки в `/home/node` tmpfs и могут исчезнуть при Docker reset.
- Cgroup live: 546 MiB/1024 MiB (53%), 56/256 pids, memory.events oom=0 и oom_kill=0 на момент snapshot. Сосуществование сейчас не привело к наблюдаемому OOM, но лимиты общие.

## Замечания, которые остаются
1. **Windows ACL / junction алиасы: НЕ ПРОВЕРЕНО после второй установки.** Установку выполняли двухшаговым same-folder File.Move вместо провалившегося File.Replace. SHA подтверждён owner, но SDDL нового Windows `FortisRepo2.ps1` и `Repo2DirectGuard.ps1` после замены не сравнены с оригинальным backup/ожидаемым trust boundary. Также неизвестны effective ACL Windows launcher ancestors, aliases через Repos/Workfiles. Это важный next read-only gate, без остановки Repo.
2. **Windows tools client/runtime**: F-R-07 из [WF-029](repo-protection-20261025.md) условно не закрыт: на выбранных C:\Tools paths ранее находили Authenticated Users Modify при отдельных Deny другой учётке; effective access данного threat principal не установлен. Второй `Start` содержит отдельный запуск `$Client` и `$Runtime`; проверка Get-FileHash исходного launcher найдена только для `$Runtime`. Полный доверенный путь/пин `$Client` без inspection установленного Windows source не подтверждён.
3. **Пара профилей в одном контейнере не означает OS isolation.** Оба UID1000, один writable workspace, Git, DC tmpfs config и общая сеть. Повреждение разрешённых файлов одним чатом возможно и для другого; `allowedDirectories` и blockedCommands не независимая OS security boundary для shell/кода.
4. **Проверка DC настроек неполная и однократная на старте.** Изменение `blockedCommands` или иных свойств вне трёх pinned полей может не быть замечено; файл редактируем рабочим UID. Исправление — отдельный согласованный hardening, не hot-change двух live процессов.
5. **Reboot не проверяли.** PR-A-15/PR-A-16 умеют guarded восстановление DC/Git при stock/missing tmpfs, но в race двух стартов после сброса один может fail-closed. Контейнер должен уже работать; Windows автозапуск обоих ярлыков не установлен. Live simultaneous startup пока PASS только при уже pinned config.
6. **Сеть/host LAN**: выбранные ограничения Docker PASS(scope), но полный egress/host firewall policy F-R-06 остаётся open; доступ к выданным RW roots и другим host-сервисам не становится закрытым благодаря отказу от Bridge.
7. **Windows saved profile contents** не читались целиком и не публиковались. Текущий effective runtime Direct доказан по /proc; возможный legacy `mcp.command` в иных saved profiles/старых launcher не исключён. Bridge backup хранить как rollback artifact, не выполнять автоматически.

## Вывод
**PASS для функциональной миграции и конкретной первоначальной Bridge startup path substitution у обоих live подключений.** **НЕ PASS** для полной Windows ACL/trusted-executable integrity, независимости профилей, полной конфигурационной целостности, network enforcement или cold reboot. Никаких процессов/репозиториев/контейнеров для этого аудита не останавливали, ничего не удаляли.

### Рекомендуемый следующий gate
Owner-run только read-only: текущие SHA и ACL установленного второго launcher/guard против backup; reparse metadata parents (без follow в новые targets); при необходимости inspect `$Client` fingerprint и saved profile MCP command без печати секретов. Потом согласовать безопасный reboot test отдельно.
