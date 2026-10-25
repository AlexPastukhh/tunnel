# WF-050 — проверка передачи безопасности Fortis Repo / Tunnel

**Дата:** 26.10.2026, Asia/Bangkok. Свежий Linux snapshot: 25.10.2026 17:26:44 UTC = 26.10.2026 00:26:44 +07:00. Исходный HEAD: `49b2e402f91f9f62e538636b32c0851ab3cef62e`, main ahead 63; индекс пуст. Это документальное исследование и минимальные read-only проверки, не исправление системы и не Windows acceptance.

## 1. Карта архитектуры

Два браузерных профиля ChatGPT используют две Windows Tunnel identity: `repo-mode` и `repo-mode-plus2`. Owner-installed пути и SHA взяты из [security V-07–V-13](../TUNNEL_SECURITY_ISOLATION.md); Windows заново не опрашивалась.

| Слой | Repo1 | Repo2 | Граница |
| --- | --- | --- | --- |
| Windows entry | `C:\Users\alexa\chatgpt-repo-mode\control.ps1` → `run-tunnel.ps1` PR-A-15 | `C:\Users\alexa\AppData\Local\FortisRepoPlus2\FortisRepo2.ps1` + `Repo2DirectGuard.ps1` | Разные launcher/profile/identity; owner Windows context |
| Windows transport | Client/Runtime в `C:\Tools\tunnel-client` | Тот же набор binaries, отдельный профиль | Runtime v0.0.15, narrow API E38; Client и Runtime — разные EXE |
| MCP backend | Direct Linux Desktop Commander | Второй Direct Linux Desktop Commander | Один контейнер `fortis-repo-test`, общий UID1000, сеть, DC config, Git и ресурсы |
| Данные | `/workspace/repos` ↔ Windows Repos; `/workspace/files` ↔ Windows Workfiles | Те же ресурсы | Оба bind RW; `/workspace/repo` — отдельный RW Docker volume |

Исполнение `python/node` через Repo происходит в Linux. Bind mount предоставляет общие файлы, но сам не превращает Linux-команду в Windows-команду. Windows consumer/autostart/IDE или доступный host API остаются потенциальными путями исполнения изменённых файлов. Их универсальное отсутствие не доказано.

G2/`FortisHostG1` — отдельный Windows-контур, не token Linux Repo. Hosted Sites, Snapshot Broker и Observatory имеют независимые маршруты/полномочия; они не образуют обязательный общий security gate. См. [ARCHITECTURE](../../ARCHITECTURE.md), [ACCESS](../../ACCESS.md), [AUDIT](../../AUDIT.md).

## 2. История решений и реальные пределы

| Этап | Что произошло | Что результат не означает |
| --- | --- | --- |
| E38/E43/E44 | Repo переведён на narrow Windows runtime; старый owner HOST остановлен; G2 и Repo разграничены | Не whole-chat isolation, не запрет всех host APIs |
| WF-018–020 | У root-owned Bridge обнаружен writable UID1000 родитель; Windows hashes связали startup source с установкой | Возможность pathname substitution выведена по правам; реальной подмены/компрометации не обнаружено |
| WF-021–024 | Bridge оказался stdio/presentation adapter; isolated Direct/Bridge: 26 одинаковых tool schemas, resources/UI отличаются; actual-client Direct и независимый возврат проверены | Не все 26 tools/UI actions испытаны; возврат тогда использовал Bridge и не годится как нынешняя безопасная стратегия |
| WF-025–029 | Первый Direct установлен владельцем, actual-client smoke и штатный Start; остаточные Bridge процессы адресно убраны | Bridge-файл не удалён; альтернативные старые профили не проинвентаризированы полностью |
| WF-030–032 | Reboot сбросил tmpfs DC/Git; PR-A-14 восстанавливал config, но блокировал сосуществование; PR-A-15 разделил pinned coexistence и gated bootstrap | Новый cold reboot двух профилей не проверен |
| WF-033–038 | Простая замена двух Bridge-путей второго launcher признана недостаточной; добавлен guarded Direct, owner install и совместный census 2/0; затем owner SHA/SDDL/direct-reparse gate | Равенство ACL backup не доказывает безопасный effective access; separate client smoke передан владельцем из другого чата |
| WF-040–046 | Проверены owner metadata Windows EXE/ACL/accounts; принято ждать Project Checker, без ручного переноса | NotSigned не означает компрометацию; исторический SHA не является vendor attestation |
| WF-047–049 | Сведены security gates/документы; зафиксирован cannot fork с неизвестной причиной | Документация не применяет enforcement |

Источники: [JOURNAL WF-018–049](../JOURNAL.md), [первый аудит](repo-protection-20261025.md), [dual audit](dual-direct-postinstall-audit-20261025.md), [rollout PR-A-13–15](permanent-direct-mcp-rollout-20261025.md), [cleanup plan](dual-direct-trusted-runtime-cleanup-plan-20261025.md). Исторические команды не исполнялись.

## 3. Новые доказательства L-01–L-06

**L-01 — live Linux/MCP.** Прямой доступ к `/workspace/repos/tunnel` и AGENTS успешен. `get_config`: DC 0.2.52, Linux Docker, shell /bin/bash, telemetry=false, ровно три ожидаемых allowed roots. Точный argv-entry census /proc: **2 Direct** (PID3400/PID4986), **0 legacy Bridge**; оба UID1000, CapEff=0, NoNewPrivs=1, Seccomp=2. PID — только snapshot. Успех одного текущего MCP не заменяет нового отдельного functional test второго браузерного клиента.

**L-02 — mountinfo.** Корень / — ro; /home/node — tmpfs rw,nosuid,nodev,noexec. /workspace/repos имеет mount root /Users/alexa/Repos, /workspace/files — /Users/alexa/Workfiles; оба rw. /workspace/repo — ext4 volume fortis-repo-workspace rw. Строка C:\134 у обеих bind в get_config — поле source 9p; по ней нельзя считать Repos и Workfiles одним каталогом. Современный Docker inspect с Windows не повторялся; aliases/reparse цели не исследованы.

**L-03 — целостность выбранных Linux путей.** SHA Direct entry:
`a4145198dc75cd34e7c7452c2054b4cc0d29e199ae1459961a17e4da25a13500`.
Модуль, /opt, /opt/dc и /usr/local/bin/node — root-owned 0755, lstat не symlink, W=false для UID1000; полная supply chain не аттестована. DC config UID1000/0644 writable, .gitconfig UID1000/0600 writable. Legacy Bridge файл root/0755, но .fortis UID1000/0755 writable; файл сохранён и не запускался. Два стандартных docker.sock пути отсутствуют; это не отсутствие всех management endpoints.

**L-04 — ресурсные counters.** Одно чтение cgroup: pids.current=54, pids.max=256, pids.events max=316; memory.current=622964736 bytes, memory.max=1073741824, memory.events max=2933, oom=0, oom_kill=0, oom_group_kill=0; cpu.max=200000/100000. **PID-limit events реально наблюдались**, но counters накопительные, без timestamp/actor. Связь с конкретным WF-049, нагрузка/утечка и виновный процесс не установлены. Нельзя утверждать ни измеренный OOM, ни отсутствие прошлых memory-limit событий. Нагрузочные тесты/kill/restart не выполнялись.

**L-05 — Project Checker source и сохранённые test logs.** В рабочем дереве чужие tracked/untracked изменения V1-3. Статически прочитаны promotion.py, promotion_state.py и GUI/jobs/preview: review, confirmation, staged transaction, managed state, backup/readback/recovery/rollback присутствуют как разрабатываемый portable core. GUI создаёт PromotionService без backend; native_update_available=False, _authority без backend отказывает, Update disabled. Исходники не исполнялись этим исследованием.

Сохранённый `/workspace/repo/project-checker-devtools/v1-2-acceptance-tests.log`: 140 tests/OK, mtime 25.10 16:36:04 UTC. Более новый `v1-3-tests.log`: **160 tests/OK**, mtime 25.10 17:26:00 UTC. `tk-qa/gui-smoke.log` при позднем чтении содержит **10/10 PASS**, включая Check→full preview и first-import preview, с SYNTHETIC DOCKER ONLY / WINDOWS NOT TESTED. Эти agent-writable logs прочитаны, но **не независимо повторены**, не являются trusted receipts и не доказывают соответствие каждому будущему изменению dirty tree. Старые 140/8 — исторический checkpoint, не последний весь source status.

**L-06 — статическая проверка потенциально ошибочной диагностики.** Source `runtime/repo-mode/probe.mjs:32–38,57–63` сначала делает write probes, Git setup и spawn legacy Bridge; --check-internet добавляет сеть только позднее. Поэтому команда из конца OPERATIONS.md не является чистой network/read-only проверкой. Сам probe не запускался, Windows установленная копия не перепроверялась.

Source SHA кандидатов PR-A-15 `9f3f3bad533415a21121e1f33f7f844d7d7d7a5640c6711326f4916679907483` и Repo2 guard `88d5be54f5e651bbd658bd9f84751511f9d178061efacf4aa0f2507827cc8533` совпали с историческими owner pins. Это сверка **source**, не новый installed Windows hash.

## 4. Реальная граница изоляции

Агент и его Linux-код могут читать/менять/удалять доступные файлы всех выданных RW roots; перенос результата в Windows через bind — уже изменение Windows-файла. RO rootfs не делает эти roots read-only. Два DC имеют общие данные/config/resources, а не независимую OS isolation.

Выбранные Linux flags/RO module и отсутствие стандартных sockets подтверждены L-01–03. Исторически 2375/2376 refused, выбранные admin GET404 и narrow route graph — ограниченные отрицательные проверки. Но /healthz host runtime был доступен из Docker. Не проверены все сетевые методы, host/LAN APIs, aliases, host consumers, все Windows tokens или container vulnerabilities.

Нет доказанного универсального Windows shell через текущий Repo; нет и доказательства невозможности любого host execution. Отсутствие keys в обычном mount или ограничения file tools не заменяют эти проверки. См. security V-03/04/10/13/14, F-R-06/08/09/10.

## 5. Приоритеты рисков

| Приоритет | Риск | Последствие / нужное evidence |
| --- | --- | --- |
| До trusted release | F-R-06 | Host/API может обойти updater; нужны scoped listeners/routes/firewall/auth и санкционированные negative controls |
| До trusted release | F-R-07 | Подмена Windows EXE/parents, unpinned Client Repo2, origin gap; нужны effective tokens, Delete/DeleteChild, provenance и maintenance/rollback design |
| До trusted release | F-R-08/09 | Alias к installed/approval/keys либо второй credential route; owner no-follow metadata, effective access, без key contents |
| До trusted release | F-R-12 | Незащищённые Checker/tools/policy/approval/deps не создают доверенного допуска; Windows native gates отсутствуют |
| До двухпрофильного recovery/cleanup | F-R-11 и residual F-R-05 | Потеря обоих входов или возврат mutable Bridge; нужен независимый Direct repair и owner boot/rollback tests |
| Операционно сейчас | F-R-13 | Наблюдены PID-limit events; безопасно наблюдать дельты counters и concurrent tasks, не kill/stress/restart |
| Явное решение scope | F-R-10 и прежний F-R-02 | Общий контейнер и широкие RW roots допускают межчатовое воздействие; отдельные контейнеры только отдельным решением |

F-R-07: owner evidence — четыре enabled accounts alexa/FortisHostG1/CodexSandboxOffline/CodexSandboxOnline; Codex не direct admins, состоят в CodexSandboxUsers. G1 имеет targeted Deny. Нельзя вывести effective write любого token только из Authenticated Users Modify; нельзя удалить широкое Allow, не сохранив maintenance alexa. Полные effective token проверки и все ancestors отсутствуют.

## 6. Связь с Project Checker

Подтверждённый committed V1-2: регистрации file/files/folder/mixed/check-only, shared mutable packs, captured policy, snapshots/SHA, actual ESLint/Semgrep, coverage/reports, async/cancel, read-only full target preview. В незавершённом V1-3 появились portable review/confirmation/transaction/recovery и GUI preview. Ни один из этих слоёв не является installed Windows authority.

**Отдельный blocker Tunnel:** `checker/settings.py:37–40` разрешает только .js/.cjs/.mjs/.py в development coverage. `coverage.py:68–78` помечает отсутствие trusted applicability как UNSUPPORTED. Tunnel включает PowerShell и Windows EXE, а также docker.exe/Node/DC/deps и profiles/config с исполняемой семантикой. Поэтому текущий Check нельзя объявить полным review Tunnel: нужны явный PS1 review/test route, binary provenance/manifest и весь dependency closure. Регистрация metadata и одобрение полноценного executable release — разные gates.

До использования для Tunnel: закончить V1-3, подготовить отдельную проверенную V1-4 Windows установку приложения/tools/transitive deps/policies/state/approval/backups, доказать native handles/final paths/reparse/ACL/route independence, исключить Repo imports/config discovery/scripts, испытать recovery. Две кнопки и owner confirmation привязывать ко всем конкретным bytes/source/target/policies/tools/managed set; drift отменяет approval. Даже чистые анализаторы не доказывают безвредность.

Источники: [Checker PLAN](../../userscript-updater/PLAN.md), [HANDOFF](../../userscript-updater/HANDOFF_CURRENT_V1_20261025.md), [Windows boundary](../../userscript-updater/WINDOWS_TRUST_BOUNDARY.md), [implementation log](../../userscript-updater/IMPLEMENTATION_LOG.md), [source README](../../../runtime/userscript-updater/README.md), текущие исходники L-05. Историческая REQUIREMENTS.md userscript-specific, A4 reading copy остаётся Candidate, не новая автоматически принятая policy.

## 7. Качество документации и пробелы

- **D-01:** repo-protection audit содержит старые настоящие формулировки про active Bridge и выбор PR-A-07/13. Dual postinstall audit говорит, что Repo2 ACL после установки ещё не проверен, хотя WF-038 позже подтвердил scoped SDDL/reparse. Читать как датированные этапы; действующий указатель — security/JOURNAL.
- **D-02:** rollout headings PR-A-14 Windows not installed / PR-A-15 source-only сохранены рядом с более поздними owner installation фактами WF-031/032. Workflow README final link PR-A-13 также говорит, что штатный restart ещё не проверен. Это устаревшие summaries, не требования повторить миграцию.
- **D-03:** Checker README/handoff/log/PLAN отражают 140/8 и отсутствие transaction core; текущий dirty V1-3 и logs160/10 опережают их. Это активная работа другого чата; документы Checker этим исследованием не перезаписываются. Их синхронизация остаётся за владельцем workstream.
- **D-04:** OPERATIONS diagnostics печатает старый probe --check-internet без локального предупреждения о его side effects; ACCESS network section всё ещё говорит «не отключать probe». Верхнее legacy предупреждение не делает эту команду безопасной. Исторические команды не выполнялись; будущую редактуру runbook нужно отделить от исполнения.
- **D-05:** get_config tool descriptions/hostPath C:\134 противоречат наивной интерпретации реальных mounts; L-02 разрешает конкретное расхождение. Metadata инструмента не источник Windows ACL/physical alias map.
- **D-06:** исторические SHA/owner сообщения и неподписанные mutable Docker test logs не являются vendor provenance, continuous attestation или Windows acceptance. Не хватает native receipts, tool closure, key2/effective ACL/alias/network/reboot evidence.

В этом шаге актуализированы центральные security/STATE/JOURNAL и этот отчёт. Исторические записи сохранены; Checker source/docs и остальные runbooks не изменены. Старые ошибки/FAIL и ограничения не удалялись.

## 8. Последовательность следующих шагов — предложение, не исполнение

1. Сохранить два live Direct и чужую разработку. Для F-R-13 без нагрузки снять последующие дельты pids/memory events в спокойный момент; root cause и actor пока OPEN.
2. После ближайшего milestone Project Checker получить точный committed source/test checkpoint, завершить V1-3/V1-4 и определить поддержанный маршрут анализа PS1/EXE/deps для Tunnel. До этого разрешён только design/metadata registration.
3. Параллельно подготовить owner-only read-only boundary inventory: exact installed dependency paths, docker.exe identity, ancestors/reparse/effective ACL, key2 location/ACL, saved MCP command classification без profiles/secret output; actual host/LAN listeners/auth/policy. Никаких изменений по старым командам.
4. До реального promotion защитить Checker, tools/deps/policy/registry/snapshots/approvals/backups и installed target от всех agent-write routes. Проверить synthetic negative controls; source-root/target не могут быть alias одного дерева.
5. P-01: зарегистрировать оба Tunnel и весь runtime contract без обновления. P-02–P-05: credentials/boundary, frozen manifest, independent review+owner approval, source drift и approval tamper reject, secure staging и повторный host SHA.
6. P-06/P-08: canary install, full read-back, backup и failure/locked/partial/crash recovery; no global multi-volume atomicity promise. Windows changes только отдельным ручным owner plan.
7. P-07/P-09: закрыть или явно принять конкретные альтернативные Windows runner/API/autostart/network пути. Этот gate планировать до production cutover, не после объявления release безопасным.
8. Только с независимым Bridge-free recovery и согласованным окном: реальный Tunnel cutover/rollback, P-10 обоих real clients после cold reboot, разные порядки/параллельный старт/stock-missing-drift tmpfs.
9. P-11 отдельно: exact consumers inventory и owner-approved архив/cleanup legacy, без рекурсивного удаления общих директорий; затем повторный 2 Direct/0 Bridge, оба client smoke, P-12 redacted receipts.

Все P-01–P-12 остаются PENDING до соответствующего evidence. **Ближайший шаг после обсуждения отчёта:** выбрать узкую owner read-only boundary проверку и дождаться/сверить готовый Checker milestone; не переносить Tunnel и не запускать обновление.

## Границы выполненной работы

Не устанавливались зависимости, не переносились/удалялись runtime файлы, не менялись Windows ACL/firewall/mounts/profiles/keys, не запускался Windows код или старый Bridge, не останавливались/перезапускались Tunnel/Docker. Не читались keys/credentials/full profiles/raw payload logs; не выполнялись registry/port scans, CI, stress или полный повтор Checker suite. Чужие исходники только прочитаны, не stage/commit. Только scoped документация и локальная Git-фиксация; push отсутствует.


## Дополнение QA: L-07 / D-07 — Git bytes, не только status

Перед коммитом обнаружено: HEAD/index JOURNAL.md на 49b2e40 содержит 137637 bytes, из них последние 1257 — NUL-only suffix; WF-049 в blob отсутствует, хотя в рабочем тексте до нашего шага WF-049 был виден. Текущий рабочий текст после WF-050 содержит обе записи по одному разу, NUL=0; весь исторический текст HEAD до первого NUL сохранён как точный prefix.

В одном read-only сравнении stat/read_bytes рабочего JOURNAL=142868, Python SHA1 Git-blob frame и git hash-object --stdin дали 1f734e47c31654b0249da8109dc05c9a5cb91568, но git hash-object --no-filters <path> дал dac9d612deb64bc59b46203794bd6ed17a18476e. Для других трёх наших docs все три метода совпали. Разница подтверждена, причина не установлена; нельзя автоматически приписывать её 9p/mmap, чужому агенту или атаке. Предыдущий status «docs clean» и название коммита не доказывают сохранность каждой записи. Новый **F-R-14 OPEN, evidence integrity**.

Безопасный способ этой фиксации: staging только собственных docs из явно прочитанных bytes через git hash-object -w --stdin, затем сравнить staged и committed blobs с этими bytes. Это адресная операция Git, не настройка ОС/перезапуск/чистка кеша. Сохранить WF-049; нормализация NUL не удаляет исторический текст. Причину рассогласования исследовать отдельно, не объявлять общим повреждением всех Repo.
