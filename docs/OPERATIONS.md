# Запуск, панели, остановка

## Важно: нынешние два Fortis Repo — Direct, legacy Bridge не запускать (WF-036–048, 25.10.2026)

После миграции **первый `repo-mode` и второй `repo-mode-plus2` работают через Direct MCP** (`docker exec` → закреплённый `/opt/dc/.../dist/index.js`), а не через `/workspace/repo/.fortis/mcp-bridge.mjs`. Read-only повтор 25 октября показал **2 Direct, 0 legacy Bridge**; это point-in-time, не cold-reboot acceptance. Для проверки/восстановления **сначала** читать [единую security карту](agent-workflow/TUNNEL_SECURITY_ISOLATION.md) и [актуальный STATE](agent-workflow/STATE.md). Ниже сохранены старые команды, меню и исторические этапы; **не выполнять legacy Bridge command, StopContainer, fallback/восстановление, новый Windows install или перезапуск двух Repo только по этой странице**. Изменения/остановка Windows runtime требуют отдельного owner-controlled плана. Второй launcher установлен в профиле alexa (`AppData\Local\FortisRepoPlus2\FortisRepo2.ps1`); его отдельный Tunnel identity не заменять первым.

## Scope принят, прежний owner HOST остановлен — E43, 2026-10-16

[E43](G3_G2_SCOPE_ACCEPTANCE_AND_HOST_RETIREMENT_2026-10-16.md): пользователь принял E42/P01
и разрешил выбранный old HOST Stop.13520/16092/24724 завершились,8080 не слушает.
After-check actual G2 SID1009/non-admin/Session2 и Repo MCP/CLI PASS; их process/listener
fingerprints сохранены, G2/Repo не перезапускались.
G3 bounded baseline ACCEPTED(scope); G4 initial Workspace policy ACCEPTED(scope); G5 полная personal-security программа не принята; G6 manual daily/normal recovery ACCEPTED(scope). Whole-chat1.4 PENDING; universal PASS не заявляется.
Credentials/connector не отозваны; local owner recovery сохранён, ручной relaunch снова откроет
широкий route. Новых ACL/mount/network/AV/task/service/автозапуск изменений нет.
Далее обычная работа G2/Repo; новые scopes/существенные изменения проверять адресно.
[Действующая инструкция E42](G3_G2_INITIAL_SCOPE_AND_RUNBOOK_2026-10-16.md).
Candidate/BLOCKED/NEXT ниже — датированная история стадий до E43.

> G2 guest-session entry/stop/recovery: [итоговая инструкция E42](G3_G2_INITIAL_SCOPE_AND_RUNBOOK_2026-10-16.md). Scope — Candidate, old HOST пока работает. Retirement и его recovery — отдельные решения; Repo/G2 не останавливать вместе с ним. Ниже сохранены команды других контуров и датированные этапы; их наличие не разрешает заново запускать retiring owner HOST.

> Продолжение 2026-10-16: после user reboot G2 вручную запущен в guest Session2; MCP/CLI SID1009/non-admin подтверждены. В 02:36 approved corrected browser repeat PASS(scope): CDP/DOM/storage/reload, default sandbox и temporary cleanup. Own window и authorized guest clipboard marker/cleanup PASS(scope), E22; E21 fresh-open owner GUI scope и E22 selected owner DUP_HANDLE DENY подтверждены; E23/E24: selected G2 handle walk и launch/inheritance review завершены; 2.6 PARTIAL, concrete brokers/owner API и G2 stop остаются. Уточнение 03:35: G2 заменяет owner HOST; отдельная HOST runtime-only migration/helper NOT REQUIRED NOW. E26 current ACL regression PASS(scope); E28 normal stop/restart и E29 controlled peer failure PASS(scope), real G2 unchanged. Exit0 runtime не доказывает MCP task success. E30 selected service metadata/source review: 5.4 PARTIAL, live controls не отправлялись. Next — relevant boundary/protected paths/final G2 takeover; без повторения пройденных tests. Прежний HOST пока не остановлен, Repo остаётся отдельным. Для актуального NEXT и границ см. [рабочий порядок](G3_GUEST_MCP_WORKFLOW_2026-10-15.md). Старые PID и тогдашние NEXT ниже — датированная история.


Навигация: [docs/README](README.md). Здесь находятся **операционные команды**; модель маршрутов и ролей — в [ARCHITECTURE](ARCHITECTURE.md), действующие разрешения — в [ACCESS](ACCESS.md). Перед изменением проверять live-состояние.

## Legacy owner HOST — только recovery, исторические команды

Ярлык **Desktop Commander Secure Tunnel** запускает:
C:\Users\alexa\Documents\prot\Start-Desktop-Commander-Secure-Tunnel.ps1

Профиль desktop-commander лежит в %APPDATA%\tunnel-client\desktop-commander.yaml. MCP command:
```text
cmd.exe /c C:/Tools/desktop-commander/desktop-commander-trusted.cmd
```
Обёртка выставляет DESKTOP_COMMANDER_DISABLE_MCP_UI=1. Клиент: C:\Tools\tunnel-client\tunnel-client.exe, Desktop Commander 0.2.52.

Историческая owner HOST панель: http://127.0.0.1:8080/ui (после E43 offline). Закрытие окна запуска останавливает этот туннель. Повторный запуск не должен создавать второй процесс с тем же listener.

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
# ОПАСНО: следующий пример сохранён для истории; общий Docker двух Repo НЕ останавливать без отдельного owner-approved плана:
# & $control -Action StopContainer
```

В действующей установке первого Repo `Start` вызывает закреплённый `run-tunnel.ps1` PR-A-15: проверка Docker/container и pinned Direct DC, guarded восстановление tmpfs-конфигураций DC/Git при допустимых условиях, запуск отдельного сохранённого профиля. Это **не** проверка/запуск legacy Bridge. Второй Repo использует отдельный `FortisRepo2.ps1` и Direct guard; штатный автозапуск обоих после reboot не был проверен. Рабочий ключ остаётся на Windows; не переносить в Docker/Git.

Repo listener выбирает свободный loopback port (127.0.0.1:0). После [E38](G3_REPO_RUNTIME_CUTOVER_2026-10-16.md) установленный control находит full/runtime EXE по точному Repo Tunnel ID в metrics; OpenPanel выбирает /health. Полной /ui у Repo runtime нет. Постоянный адрес не задан; PID24720/port65202 — датированный срез, не команда для будущего stop.

**Актуальный MCP target** (описание установленного Direct entry; не команда для ручного интерактивного запуска):
```text
docker exec -i fortis-repo-test /usr/local/bin/node /opt/dc/node_modules/@wonderwhy-er/desktop-commander/dist/index.js
```
**Исторический Bridge** `/workspace/repo/.fortis/mcp-bridge.mjs` в UID1000-writable родителе; **не запускать его и не использовать в recovery**. Оба Windows launcher находятся вне обычных Docker mounts, но полная проверка Windows ACL/aliases и host network ещё OPEN — см. [аудит](agent-workflow/TUNNEL_SECURITY_ISOLATION.md).

StopAccess отключает Repo Tunnel; фоновые команды/контейнер могут продолжить работу. StopContainer также останавливает проверенный контейнер. Ни одна команда не удаляет host-файлы или volume и не останавливает HOST Tunnel.

После E38 Repo OpenPanel открывает /health, а полной /ui у narrow Repo runtime нет. Раннее описание /ui относится только к исторической панели старого owner HOST: она не задавала права и не имела тумблера интернета.

## Ротация runtime key Repo / G2 (script source, не выполнено)

В Windows owner PowerShell, **не из Docker и не G2**:

```powershell
& 'C:\Users\alexa\Repos\tunnel\runtime\repo-mode\Rotate-RepoRuntimeKey.ps1' -Action Preview
# Только после выпуска нового provider runtime key, согласования перерыва Repo и Preview PASS:
& 'C:\Users\alexa\Repos\tunnel\runtime\repo-mode\Rotate-RepoRuntimeKey.ps1' -Action Install
```

`Install` запросит новый ключ скрыто, зашифрует старый DPAPI в owner LocalAppData и заменит существующий saved-file key; сам tunnel не перезапускает. Затем штатно перезапустить **только Repo** через существующий control (после явного разрешения на короткое прерывание), проверить native MCP/doctor и только после успешной проверки отозвать прежний ключ у OpenAI. Backup path выводится без секретов; для `-Action Rollback -BackupFile <exact-path>` старый provider key должен быть ещё действителен. G2 при каждом штатном запуске вводит отдельный key, но обновление API key у провайдера всё равно обязательно для настоящей ротации. Старый owner HOST не включать.

## Действующий G2 manual daily сценарий

Пользоваться pinned guest-local Preview/LaunchTest/normal Ctrl+C/recovery
в [E42](G3_G2_INITIAL_SCOPE_AND_RUNBOOK_2026-10-16.md).
E43 принял scope; owner HOST и private-station prototypes не ordinary start.
Repo narrow имеет health/metrics, а не full legacy owner /ui.
Новые credentials, runtime и права ради документации не менять.

## Исторические результаты G2 и действия

> Статусы PENDING и «не принято» ниже относятся к прежнему этапу. Текущий запуск — только по E42/E43.

[Актуальный план](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md) и [CURRENT_STATE](CURRENT_STATE.md) различают прежний G2 MCP PASS
и ещё не принятую конечную chain в отдельной guest Windows-сессии.

Принят ручной цикл: войти в FortisHostG1 → запустить проверенный G2 entry →
переключиться в alexa, оставив guest logged-on → выполнить нужную задачу →
остановить только G2 при необходимости. Длительность и final-session recovery ещё не приняты.
Собственный guest GUI/clipboard разрешён; основной owner GUI этим контуром не управляется.

[Новый рабочий порядок, подготовленный source и точная Preview команда](G3_GUEST_MCP_WORKFLOW_2026-10-15.md) используют существующий G2.
Guest-visible копия создана: `C:\Users\Public\Documents\Fortis-G2-GuestEntry-0638D14A.ps1`; pin — в рабочем порядке.
Windows HOST component checks и user-local guest Preview (SID1009/Session2) пройдены;
user-local старт выполнен; restricted G2 MCP/file/CLI отвечает под SID1009/Session2 при active console Session1.
Повторный LaunchTest не нужен. Gate full path/hash совпал с Repo; source/test iteration, synthetic Git и scoped TCP/GET smoke пройдены.
История до approved browser repeat 02:36 (актуальный итог выше):
Own window PASS, clipboard SKIPPED_NONEMPTY; browser smoke частичный, test Job/profile cleanup PASS (E20).
Corrected browser source в Repo; доставка получила spawn EPERM, новые файлы ENOENT.
Сначала диагноз причины отказа; HOST event query timeout. Owner boundary и G2 stop/cleanup остаются;
точный следующий шаг и evidence — в рабочем порядке.
Старый 30-minute OwnerWitness для нового launcher не нужен.

Новый готовый Session3 production launcher здесь не объявляется. Не использовать старый owner-session
private Launch либо runtime-api helper с Apply трёх launchers как обычный G2 start.
Обычная guest-консоль/ручное восстановление допустимы, если проходят критерии плана.
Отдельный ключ вводится локально по проверенному G2 workflow; owner saved key не переносится.

Изменение только документации не требует запускать/останавливать HOST, Repo, G2 или Docker.
Датированные scripts/pins из runtime README перед выполнением сверяются с актуальным планом и конкретным scope.

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
