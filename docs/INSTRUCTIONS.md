# Обновление инструкций после изменений

Не существует одной универсальной «инструкции плагина»: несколько слоёв принадлежат разным источникам. Менять источник нужного слоя и проверять доставленную версию.

| Изменение | Где править | Как доставить |
|---|---|---|
| Docker folders/network/identity | Фактический контейнер, workspace-config.json, probe.mjs | Проверенный recreate/config update, затем native Repo restart |
| Native Repo guidance / legacy UI | fortis-mcp-bridge.mjs, installed /workspace/repo/.fortis/mcp-bridge.mjs | Копия в volume, restart Repo Tunnel, refresh connection |
| Native HOST launcher/env | trusted.cmd, profile, HOST launcher | Локальная проверка и restart HOST при необходимости |
| Site MCP инструкции/tools/UI | Worker initialize.instructions, schemas/descriptions/_meta/resources, page/status | Existing Site source workflow → version → deploy |
| Site snapshot README/deployment/ | В том же Sites Git | Согласовать с runtime и опубликовать нужную Site version |
| App skills/onboarding/keywords | Plugin-owned files / metadata, точный canonical plugin | По update-plugin skill, не через случайный Site HTML |
| Текущая эксплуатационная документация | Этот GitHub repo; старые пути — pointers | Commit/push, проверить remote HEAD |
| Snapshot workflow/policy | `docs/SNAPSHOT.md` — сценарий; `runtime/broker/README.md` — операции; Bridge runtime — исполнение | При смене поведения обновить эти источники и только затронутые подсказки в private snapshot-transfer. Не дублировать текущие разрешения/статусы между файлами; затем проверить опубликованные ссылки и readback |

## Порядок на нашей установке

1. Определить точные затронутые контуры и текущие версии. Не менять HOST при исправлении Repo. Не менять audience/export permissions попутно.
2. Обновить источник поведения и все зависимые утверждения: пути, доступ к internet, key reference, cwd, «что готово / что выключено». Удалить необоснованные default website/project предположения из onboarding, skills и runtime guidance.
3. Для native сравнить runtime/ копию с live path, сохранить backup вне Git, применить выбранные файлы и проверить gate. Внутренний volume не обновляется просто от изменения Windows исходника.
4. Для Site следовать Sites skill на существующем project_id; сохранить/развернуть точный source commit. Для App skills применять update-plugin только к реально поддерживаемому типу plugin.
5. При account-backed skill package update использовать текущий release, semantic version и expected_release_id (CAS); сохранять существующие App configs. После конфликта перечитать release, не перезаписывать чужие изменения. Это не замена процесса обновления native managed server.
6. Перезапустить нужный native child/Tunnel или дождаться Site deployment. Обновление Site не меняет native MCP; GitHub docs push не меняет ни один runtime.
7. Обновить подключение/инвентарь tools в ChatGPT при необходимости. Старые UI cards в истории чата могут сохраниться. Если новый tools/list всё ещё содержит старый outputTemplate/resourceUri — исправлять фактический источник presentation, а не только текст страницы.
8. Проверить доставленную версию: instructions, tools/list, schemas, отсутствие legacy UI attachments, status/один безопасный read-only вызов. Проверить startup использует saved key без нового prompt. После неопределённой мутации сначала inspect state.
9. Записать проверенный HEAD/version, чего не применяли, оставшиеся ограничения; обновить CURRENT_STATE/SITES/OPERATIONS и соответствующие source readme. Commit/push только намеренных файлов.

## Важный текущий долг

Repo Site версия 7 содержит прежние claims о /workspace/repo и deployment snapshot. При будущей публикации исправить их по CURRENT_STATE.md, не выдавая обновление native за активированный Site upstream.

Скрипт configure-tunnel.ps1 в действующей установке ранее создавал env-key reference. Его текущую копию нельзя слепо запускать поверх существующего профиля. У нас profile repo-mode уже настроен на saved file; новый initializer должен задавать тот же file reference и не перезаписывать существующий профиль. Нужна отдельная проверка initializer при следующей новой регистрации, не запуск init ради обновления docs.

## Как найти стандартную инструкцию

Использовать **sites:sites → site-mcp-server.md**, **plugin-creator:update-plugin → account-updates.md** и **plugin-creator:create-plugin → extensions.md**. Открыть текущую установленную версию перед операцией; команды и schemas из этих skills здесь намеренно не скопированы.
