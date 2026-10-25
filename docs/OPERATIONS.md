# Эксплуатация подключений

Перед действием открыть [security-реестр Repo/Tunnel](agent-workflow/TUNNEL_SECURITY_ISOLATION.md) и [STATE](agent-workflow/STATE.md). Документ описывает управление, но не даёт нового разрешения на stop/install/reboot. Текущие работающие два Repo и общий Docker сохраняются.

## Native Repo

Оба Windows профиля используют Direct Linux Desktop Commander. Подробные installed paths, owner-reported fingerprints и ограничения находятся в security-реестре; не копировать их как новые pins из истории.

| Подключение | Штатный Windows entry | Особенность |
| --- | --- | --- |
| Repo1 | `C:\Users\alexa\chatgpt-repo-mode\control.ps1` → `run-tunnel.ps1` | `Status`, `Start`, `OpenPanel`, `StopAccess` относятся к этому Tunnel; действия, прерывающие доступ, требуют согласованного scope |
| Repo2 | `C:\Users\alexa\AppData\Local\FortisRepoPlus2\FortisRepo2.ps1` + `Repo2DirectGuard.ps1` | Существующий отдельный shortcut/profile; identity первого не копировать во второй |

Direct startup проверяет закреплённую установку и контейнер; допустимое восстановление DC/Git в tmpfs ограничено guards. При unexpected drift — отказ, без отключения guards или fallback на Bridge. Штатный cold reboot/разный порядок обоих профилей пока требует отдельной приёмки P-10; контейнер должен быть подготовлен независимо.

Repo narrow Runtime использует динамический loopback listener; старый PID/порт не применять к новому процессу. `OpenPanel` относится к узкой диагностике health, не к административной панели прежнего owner HOST.

`StopAccess` может оставить фоновые команды и контейнер работающими. Остановка общего контейнера затрагивает оба Repo и не является обычной реакцией на сбой одного чата.

## Безопасная диагностика и восстановление

1. При 409/timeout выполнить один лёгкий read-only запрос к известному разрешённому файлу/статусу. Различить handshake этого чата, native runtime и независимый Site proxy.
2. После неопределённой записи проверить файл/Git/результат перед повтором. Не считать timeout доказательством отсутствия эффекта.
3. Если backend жив, сначала восстановить подключение конкретной сессии; не начинать с общего restart.
4. Для ресурсного отказа использовать спокойные read-only counters по F-R-13. Для расхождения Git reads — проверку bytes по F-R-14, без сброса ОС/cache/mount.
5. Если нужен stop/reboot/install/repair, подготовить отдельный owner plan с точной identity, актуальными pins и независимым Direct recovery; затем проверить оба затронутых клиента.

**Legacy `probe.mjs` не использовать для read-only диагностики, в том числе с флагом `--check-internet`: он выполняет записи/Git setup и запускает Bridge до сетевой проверки** (WF-050/L-06). Исполняемого примера его запуска в текущем runbook нет.

Сетевые проверки ограничивать конкретным разрешённым endpoint/методом без secret/payload output. Отсутствие доступа к одному endpoint не доказывает запрет всех host/LAN APIs.

## G2 и прежний owner HOST

G2 имеет отдельный Windows контекст; daily start/normal stop/recovery — только по [E42](G3_G2_INITIAL_SCOPE_AND_RUNBOOK_2026-10-16.md) и [текущему G2 plan](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md). Source этой страницы не меняет его scope.

Прежний широкий owner HOST остановлен по [E43](G3_G2_SCOPE_ACCEPTANCE_AND_HOST_RETIREMENT_2026-10-16.md). Credentials/launcher сохранены для намеренного owner recovery; не включать его для диагностики Repo/ротации ключа. Исторический Stop не равен постоянному отзыву connector/key.

## Ключи и изменения среды

Ротация ключа, изменение Windows ACL, mounts/network и установленного runtime — отдельные owner-controlled операции с Preview/review, backup/rollback и scoped verification. Секреты вводятся локально и не выводятся в чат/Git. [ACCESS](ACCESS.md) владеет границами доступа; [INSTRUCTIONS](INSTRUCTIONS.md) — доставкой изменений. Наличие source helper не означает выполненную установку или проверенный rollback.

[Предыдущий runbook](OPERATIONS_HISTORY_20261026.md) сохранён только для истории. Его команды, старые PID/порты и Bridge recovery не выполнять автоматически. Поддерживать здесь только действующую процедуру по [единому протоколу](agent-workflow/README.md).
