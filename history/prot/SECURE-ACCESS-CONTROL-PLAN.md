# План безопасного доступа ChatGPT к Fortis_M

Статус: **проверен и скорректирован**
Дата проверки: 2026-10-06

## 1. Цель

Нужен режим, в котором ChatGPT:
- имеет полный рабочий доступ к Git-репозиториям;
- не имеет штатного доступа к остальной файловой системе Windows;
- может получить временный доступ к явно выбранной пользователем папке;
- может выполнять редкое обслуживание Windows/ПО только после явного действия пользователя;
- не может сам расширить себе постоянный доступ.

## 2. Что проверено на Fortis_M

- Secure MCP Tunnel уже работает и не требует публичного входящего endpoint.
- Текущий Desktop Commander 0.2.52 запущен нативно и имеет `allowedDirectories: []`, что означает полный файловый доступ.
- Docker CLI установлен: 29.8.0, контекст `desktop-linux`.
- Docker Desktop установлен, но daemon сейчас не запущен; сервис `com.docker.service` остановлен и имеет Manual start.
- TCP Docker API на 2375/2376 сейчас не слушает.
- Пользователь `alexa` состоит в группе `docker-users`.
- Основной подготовленный каталог репозиториев существует: `C:\Users\alexa\Documents\Repos`.
- Сейчас в нем найден репозиторий `gdoc`.
- Git-репозитории также есть вне этого корня; они не должны автоматически попадать в постоянный доступ.
## 3. Итог проверки исходного плана

План с одним нативным Desktop Commander + `allowedDirectories` **не подходит как security boundary**.

Причина: сам Desktop Commander прямо указывает, что allowed directories и command blocklist являются guardrails, а не sandbox. Терминальный инструмент может обходить такие ограничения. Для гарантии «чат не видит остальной компьютер» нужен OS-level isolation: Docker/VM.

План с Docker пригоден, но требует следующих обязательных поправок:

1. Основной Repo Mode должен быть отдельным tunnel/plugin от нативного Maintenance Mode.
2. Repo Mode запускает Desktop Commander **в Linux-контейнере Docker Desktop**.
3. В контейнер не передается Docker socket/named pipe и не настраивается Docker TCP API.
4. Контроллер выдачи папок находится только на Windows host и не монтируется в контейнер.
5. Временная папка подключается Docker bind mount'ом только после локального действия пользователя.
6. Mount нельзя добавить в уже работающий контейнер, поэтому выдача/отзыв доступа требует restart Repo Mode; контроллер должен делать это автоматически.
7. Нативный Desktop Commander сохраняется только как редкий Maintenance Mode и никогда не стартует автоматически.
8. Docker image нельзя бесконтрольно запускать по тегу `:latest`; после первой загрузки нужно закрепить image digest и обновлять осознанно.
9. Официальный Docker installer Desktop Commander по умолчанию предлагает весь user profile. Для этой схемы его стандартный default использовать нельзя.

## 4. Целевая архитектура

```text
Обычная работа:
ChatGPT
  -> plugin "Desktop Commander — Repos"
  -> Secure MCP Tunnel A
  -> tunnel-client на Windows host
  -> docker run -i --rm ...
  -> Desktop Commander внутри Linux container
  -> RW: C:\Users\alexa\Documents\Repos
  -> опционально: явно выданные временные bind mounts
```
```text
Редкое обслуживание Windows:
ChatGPT
  -> plugin "Desktop Commander — MAINTENANCE (FULL PC)"
  -> Secure MCP Tunnel B
  -> tunnel-client на Windows host
  -> desktop-commander-trusted.cmd на Windows
  -> права обычного пользователя alexa
  -> подтверждение каждого действия в ChatGPT
  -> UAC остается отдельным локальным барьером для elevation
```

Текущий tunnel можно переиспользовать как Maintenance Mode.
Для Repo Mode нужно создать отдельный tunnel ID и отдельный custom MCP plugin.

## 5. Repo Mode — постоянный безопасный режим

Базовый host mount:

```text
C:\Users\alexa\Documents\Repos  ->  /workspace/repos  (read/write)
```

Требования к `docker run`:
- `--rm -i`; контейнер не живет после закрытия туннеля;
- без `--privileged`;
- без Docker socket / named pipe;
- без `--network=host`;
- без `--pid=host`;
- без host device mounts;
- `--security-opt=no-new-privileges:true`, если не ломает официальный image;
- только необходимые bind mounts;
- runtime API key OpenAI остается на Windows host и **не монтируется** в контейнер;
- access-controller и tunnel profiles host'а **не монтируются**;
- официальный image `mcp/desktop-commander` фиксируется по digest после проверки.
Внутри контейнера `allowedDirectories` можно дополнительно ограничить до `/workspace/repos` и временных mount points, но это только defense-in-depth.

Не нужно монтировать по умолчанию:
- `C:\Users\alexa` целиком;
- `.ssh`, Windows credential stores и OpenAI runtime key;
- `C:\Tools`;
- Docker Desktop data;
- Docker socket/API;
- controller directory.

Если Git fetch/push требует credentials, лучше отдельно решить credential flow. Не следует ради удобства монтировать весь Windows user profile.

## 6. Временный доступ к отдельной папке

На Windows host создается локальный **Access Controller**, недоступный из Repo container.

Предлагаемые локальные ярлыки:
- `Desktop Commander — Repos`;
- `Desktop Commander — Grant Temporary Folder`;
- `Desktop Commander — Revoke Extra Access`;
- `Desktop Commander — MAINTENANCE (FULL PC)`;
- `Desktop Commander — STOP ALL`.

Grant flow:
1. Пользователь запускает локальный Grant shortcut.
2. Открывается native folder picker — путь нельзя передать тихо через CLI.
3. Пользователь выбирает режим `Read only` или `Read/Write`.
4. Показывается точный путь и режим; требуется локальное подтверждение.
5. Controller перезапускает Repo tunnel/container с дополнительным bind mount.
6. Grant действует только для текущей Repo session.
7. При обычном следующем запуске Repo Mode extras отсутствуют.
8. Revoke shortcut немедленно перезапускает Repo Mode только с базовым Repos mount.
Для защиты от случайного слишком широкого grant controller должен по умолчанию запрещать выбор:
- корня диска `C:\`;
- всего `C:\Users\alexa`;
- `C:\Windows`;
- `C:\Program Files` и `C:\Program Files (x86)`;
- Docker Desktop data;
- каталога access-controller;
- каталога с runtime key.

Если реально требуется одна из этих областей, использовать Maintenance Mode, а не временный bind mount.

## 7. Почему чат не сможет сам выдать себе папку в Repo Mode

Security boundary строится не на инструкции модели, а на отсутствии возможностей:

- Repo container не видит host filesystem вне bind mounts.
- Controller directory не смонтирован.
- Docker socket/named pipe не смонтирован.
- Docker TCP 2375/2376 должен оставаться выключенным; на момент проверки он выключен.
- OpenAI runtime key остается на host.
- Изменение `allowedDirectories` внутри контейнера не добавляет новые host mounts.
- `start_process` в Repo Mode запускает процессы внутри контейнера, а не на Windows host.

Таким образом штатными инструментами Desktop Commander чат не может добавить новый host mount.

Оговорка: Docker/VM — реальная изоляция, но не математическая гарантия против неизвестного container escape / OS vulnerability. Для обычной модели угроз это значительно сильнее path-based ограничений Desktop Commander.

## 8. Maintenance Mode

Текущая нативная схема становится только Maintenance Mode.

Обязательные правила:
- запуск только отдельным локальным ярлыком;
- никакого автозапуска;
- имя plugin/shortcut должно явно содержать `MAINTENANCE (FULL PC)`;
- ChatGPT permission для этого plugin: **Always ask / Всегда спрашивать**;
- не запускать launcher от имени администратора;
- если установщику нужны admin rights, подтверждение UAC делает пользователь локально;
- закрытие окна tunnel-client отзывает удаленный доступ;
- перед запуском желательно показывать локальное предупреждение и требовать явное подтверждение.

Maintenance Mode нужен для:
- установки/обновления Windows ПО;
- диагностики ПО вне repo sandbox;
- работы с системными каталогами;
- случаев, когда контейнерное окружение не воспроизводит Windows bug.

Важная граница: пока Maintenance Mode активен, Desktop Commander по определению имеет широкие host-возможности. Гарантия «чат не может сам расширить host access» относится к обычному Repo Mode. В Maintenance Mode контроль обеспечивают ручной запуск + Always ask + UAC + короткая сессия.

Если нужна более строгая гарантия даже во время Maintenance Mode, отдельный следующий уровень — запуск maintenance DC под отдельным standard Windows account, не состоящим в `docker-users`, с elevation только через локальный UAC. Это можно сделать позже, если понадобится.

## 9. ChatGPT permissions

Для Repo plugin:
- предпочтительно `Allow all actions`, если этот вариант доступен для custom MCP;
- это допустимо именно потому, что backend физически ограничен контейнером и mount'ами;
- если `Allow all actions` недоступен, использовать наиболее удобный доступный режим и принять дополнительные prompts.

Для Maintenance plugin:
- только `Always ask`;
- не наследовать текущий global default `Allow low-risk actions`.

OpenAI app permissions являются дополнительным уровнем подтверждения, но **не заменяют Docker isolation**.
## 10. Хранение controller и конфигурации

Рекомендуемый host-only каталог:

```text
C:\Program Files\DC Access Controller\
```

Controller scripts/binaries:
- owner SYSTEM/Administrators;
- обычному пользователю — Read & Execute;
- изменение controller требует elevation/UAC;
- controller не принимает silent grant path через аргументы командной строки.

Session data, если понадобится, должно быть временным и удаляться при остановке Repo Mode. Постоянный список дополнительных grants не нужен.

Базовый repo path хранится в controller config как:
`C:\Users\alexa\Documents\Repos`.

## 11. Порядок внедрения без риска

### Phase 1 — не ломаем текущий рабочий доступ
1. Оставить текущий Secure MCP tunnel как есть.
2. Переименовать его логически в Maintenance, но пока не удалять.
3. В ChatGPT выставить Maintenance plugin -> Always ask.

### Phase 2 — Repo sandbox
4. Запустить Docker Desktop вручную и проверить daemon.
5. Pull официального Desktop Commander image.
6. Зафиксировать digest образа.
7. Вручную проверить container с единственным mount `Documents\Repos`.
8. Проверить read/write/terminal внутри repo.
9. Проверить, что контейнер не видит `C:\Users\alexa`, runtime key и controller.
10. Проверить отсутствие Docker socket/API из контейнера.
11. Создать новый Secure MCP Tunnel "Desktop Commander Repos".
12. Настроить tunnel-client stdio command на Docker wrapper.
13. Создать отдельный Repo custom MCP plugin.
14. Протестировать end-to-end из нового ChatGPT chat.

### Phase 3 — grants
15. Сделать host-only Access Controller.
16. Реализовать RO/RW folder picker и session-scoped restart.
17. Реализовать Revoke и STOP ALL.
18. Проверить, что новый обычный запуск всегда сбрасывает extras.

### Phase 4 — финал
19. Repo plugin сделать основным.
20. Maintenance оставить выключенным по умолчанию.
21. Удалить/архивировать старые Floot/localtunnel/Tailscale relay launchers только после acceptance tests.

## 12. Acceptance tests

План считается реализованным только если проходят все тесты:

- Repo plugin читает/пишет `C:\Users\alexa\Documents\Repos`.
- Repo plugin может запускать shell и dev tools внутри контейнера.
- Попытка прочитать произвольный host файл вне mount'ов физически невозможна.
- `set_config_value allowedDirectories=[]` внутри container не открывает host.
- В контейнере нет Docker socket и нет рабочего Docker API endpoint.
- runtime API key отсутствует внутри container.
- Controller path отсутствует внутри container.
- Temporary RO grant читается, но не изменяется.
- Temporary RW grant читается и изменяется.
- После revoke/нового запуска temporary path исчезает.
- Repo chat не может создать новый mount штатными MCP tools.
- Maintenance plugin не работает, пока пользователь не запустил его launcher.
- Maintenance plugin спрашивает подтверждение перед каждым read/action.
- UAC не обходится автоматически.
- STOP ALL завершает оба tunnel-client режима и repo container.

## 13. Rollback

До полного завершения миграции текущий нативный Secure MCP Tunnel остается рабочим fallback.

Если Repo Mode ломает разработку:
1. остановить Repo tunnel;
2. запустить Maintenance только на время диагностики;
3. исправить container image/wrapper;
4. вернуть Repo Mode;
5. не включать обратно публичный Tailscale Funnel.

## 14. Решения, которые нужно подтвердить перед реализацией

1. Постоянный repo root: предлагается `C:\Users\alexa\Documents\Repos`.
2. Репозитории вне этого корня не включать автоматически.
3. Временный grant по умолчанию делать RO или каждый раз спрашивать RO/RW.
4. Нужно ли в Repo container сохранять package caches между сессиями.
5. Нужен ли позже усиленный Maintenance Mode через отдельного Windows user.

## 15. Источники, на которых основана проверка

- Desktop Commander SECURITY.md: allowedDirectories/command blocklist — guardrails; Docker/VM — security boundary.
- Desktop Commander official Docker installer: официальный image `mcp/desktop-commander:latest`, selective mounts поддерживаются; default installer может предложить mount user profile.
- OpenAI Secure MCP Tunnel docs: outbound-only tunnel, stdio targets поддерживаются, MCP server остается private.
- OpenAI app permissions docs: доступны Always ask, Allow read actions, Allow low-risk actions и для некоторых apps Allow all actions.

## 16. Итог

**План одобрен в скорректированном варианте.**

Основная гарантия должна строиться на Docker bind mounts, а не на `allowedDirectories`.
В обычном режиме ChatGPT получает полный доступ только к `Documents\Repos` и явно выданным на текущую сессию папкам.
Выдача mount'ов остается локальным Windows-действием пользователя.
Полный host access существует только в отдельном ручном Maintenance Mode с Always ask.

## 17. Связанные планы

- `ENVIRONMENT-ROADMAP.md` — общий порядок четырёх связанных направлений.
- `REPOSITORY-MIGRATION-PLAN.md` — перенос рабочих репозиториев в единый root.
- `SANDBOX-GUI-PLAN.md` — отдельная GUI-среда для автономной UI-работы без вмешательства в основной desktop.
- `TUNNEL-OBSERVABILITY-PLAN.md` — локальный monitoring tunnel/MCP/sessions, latency, heartbeat и диагностика host interference.

Repo Mode должен учитывать итог миграции репозиториев, Sandbox GUI остаётся отдельной capability boundary, а observability должна охватывать оба контура и HOST MAINTENANCE без расширения их прав.
