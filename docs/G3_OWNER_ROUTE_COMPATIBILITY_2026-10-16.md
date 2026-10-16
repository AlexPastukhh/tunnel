# G3 — совместимость owner routes: подготовка, 2026-10-16 03:23

> **Статус после E43 (16.10.2026):** old owner HOST остановлен. Сведения ниже о работающем HOST и будущем переключении — исторические наблюдения до приёмки. Действующий результат: [E43](G3_G2_SCOPE_ACCEPTANCE_AND_HOST_RETIREMENT_2026-10-16.md) и [план](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md).

> Уточнение цели 2026-10-16 03:35: G2 заменяет прежний owner HOST. Его runtime-only migration и helper больше не являются следующей работой (NOT REQUIRED NOW). Датированные факты и JSON ниже сохранены; действующий порядок — [актуальный план](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md). Live HOST пока не остановлен.

**4.8 PARTIAL; 4.9/4.10 PENDING; переключение не выполнялось. G3 BLOCKED.**
[Structured evidence E25](G3_OWNER_ROUTE_COMPATIBILITY_2026-10-16.json).

## Что установлено на HOST

Read-only запрос от owner SID1001/Session1 прочитал metadata двух известных процессов,
выделил только разрешённое имя профиля через CommandLineToArgvW и записал SHA256 выбранных файлов.
Raw argv, environment values и содержимое профилей не выводились. HTTP-запросов не было.

| Route | Profile | PID / Session | Loopback listener |
|---|---|---|---|
| HOST | desktop-commander | 13520 / 1 | 127.0.0.1:8080 |
| Repo | repo-mode | 22488 / 1 | 127.0.0.1:59183 |

Оба full EXE: SHA1946DE55…; creation fingerprints совпали с E22. Три действующих launcher/control файла
совпали с BEFORE pins migration-plan; narrow runtime совпал с A922D372….
Это датированный срез, не разрешение остановить указанные PID позже без повторной identity guard.

## Зависимости и последствия Candidate

| Компонент | Что прочитано в исходнике | Последствие runtime-only / необходимая подготовка |
|---|---|---|
| HOST launcher | Candidate сохраняет profile desktop-commander, меняет executable на pinned runtime и отключает additional Harpoon | Один файл; actual native HOST compatibility пока не проверена |
| HOST Observatory | server.py: /health?details=true, /health/mcp, /metrics и /api/logs | Health/metrics есть в reviewed runtime graph. /api/logs отсутствует: collector вернёт пустой events list; WARN/ERROR input теряется. Monitor degradation отличать от tunnel failure |
| Repo run launcher | Candidate сохраняет profile repo-mode и Docker stdio command; full client doctor остаётся preflight | Native owner profile + Docker/MCP compatibility не проверена; credential/profile export не нужен |
| Live Repo control | Get-RepoTunnel фильтрует только tunnel-client.exe | После замены одного run launcher не найдёт runtime-only. Для Repo нужен комплект run-tunnel + control |
| Candidate Repo control | Ищет оба EXE, сверяет creation time; OpenPanel меняется /ui → /health | Учесть изменение пользовательской функции; GUI в этой проверке не запускался |
| Repo monitor source | Ищет process по tunnel-client/repo-mode и identity в /metrics; читает /health?details=true | Предварительно совместим по source/graph; actual owner acceptance ещё нет |

Repository observatory sources не доказывают установленную или запущенную Windows-версию.
Потребность пользователя в full UI/Codex/Harpoon и конкретных функциях мониторинга не установлена.

## Прежний Candidate на 03:23 — HOST migration снят уточнением 03:35

Подготовить независимый one-route helper, default Preview: фиксированный route, expected live/candidate
hashes и file identity, drift guards, независимый backup, scoped apply/rollback и read-back.
Для HOST выбирать только его один launcher; для Repo — только его run-tunnel/control.
Существующий all-three switch helper не применять. Рестарт не включать автоматически в apply.

До live cutover определить full-only потребности и допустимое изменение мониторинга/панели,
подготовить ручное восстановление при недоступности выбранного route, затем согласовать конкретный
route и прерывание. Второй owner route и G2 сохраняются.
Ключи и реальные profiles не копировать в Docker или GitHub. Полный routes × methods fixture,
clipboard/browser smoke и новый reboot сейчас не нужны.

Выполнены source review и owner metadata read-only. Не выполнены deployment, profile migration,
restart, native runtime-only compatibility, guest acceptance после cutover или commit/push.
