# Fortis Windows Security — checkpoint G1→G2 (2026-10-12)

> **Датированный checkpoint 12–13 октября, сохранён для истории.** Более поздние E43/E44 меняют принятый scope и статус старого HOST; для актуального состояния сначала читать [руководство](docs/ISOLATION_GUIDE.md) и [CURRENT_STATE](docs/CURRENT_STATE.md). Указанные ниже NEXT/NOT STARTED не считать действующими после E43.


Это краткая локальная контрольная точка. Полный исходный план с историей v4 и новой главой G1 доступен в файле Fortis_Windows_Security_Plan_2026-10-12_v5.md, выданном в чате.

## Архитектура
1. Fortis Repo — изолированный Docker MCP для основной разработки; RW-монтирования Repos и Workfiles, ограничения Docker отдельны от HOST.
2. Native Windows HOST — целевая отдельная локальная стандартная identity FortisHostG1, а не обычный процесс в сеансе alexa; файлы/команды только в пределах реальных OS ACL. Инструментальные allowedDirectories/blockedCommands не security boundary против shell.
3. Персональная защита — приватные файлы, учётные данные, браузерные сессии, внешние операции, backups, сеть; отдельные principals, MFA, vault, резервные копии и запреты. Observatory — только read-only диагностика туннелей.

## Gates
G0-A: исходный token/UAC/ACL baseline, DONE scoped.
G0-B: выборочные задачи/службы/localhost inventory, DONE scoped; отсутствие обходов НЕ доказано.
G0-C: согласовано: разрешённые PowerShell/Python/Git, файлы, диагностика, тесты без admin. Продакшен-пути позже.
G1: синтетические ACL тесты PASS. Нужен финальный rollback и, по необходимости, отдельная проверка elevation.
G2: NEXT, NOT STARTED — безопасная независимая native-auth, тестовый tunnel-client + Desktop Commander под FortisHostG1, не трогая текущий HOST и runtime.key alexa.
G3: future — пути обхода: tasks, services, IPC, localhost, SMB, connectors, shell.
G4: future user decision — production limited HOST или VM/Sandbox/broker.
G5: future parallel — реальная персональная защита.
G6: future — operation, recovery, rollback, Observatory telemetry only.

## G1 факты
FORTIS_M\FortisHostG1 — standard Windows local user, SID S-1-5-21-303538662-3368424508-2654684973-1009; нет Administrators/CodexSandboxUsers.
Синтетические каталоги: C:\Users\Public\Documents\FortisHostG1Probe\{RW,RO,DENY}.
Под G1 подтверждено: PowerShell/.NET RW read/write, RO read-only, DENY no access; дочерний PowerShell whoami FortisHostG1, RO читает, DENY UnauthorizedAccessException; отдельный Python 3.13.16 под G1, аналогично три PASS.
Python: C:\Users\FortisHostG1\AppData\Local\Programs\Python\Python313\python.exe; PATH не обязательно автоматически обновлён во всех run-as сессиях.
Изначально ACL ошибочно дали неактуальному SID 1008; исправлены для SID 1009, наследование на RW исправлено, старые ACL 1008 удалены (подтверждён скан 12 объектов).
Другие первоначальные фикстуры: C:\Users\alexa\AppData\Local\FortisHostG1Probe\ — подготовленные synthetic data; не трогать личные файлы.
Существующий HOST/Repo не переведены под SID 1009. Ни конфигурации tunnel-client, ни ключи не копировались.
PowerShell Script ExecutionPolicy блокировал .ps1 -File, поэтому тесты выполнены интерактивными командами. runas command отказал при чтении пароля; user запустил отдельный PowerShell через GUI Run as different user.

## G2 next: безопасная read-only предпроверка
Выяснить независимое provisioning native test profile/auth, доступность node.exe/DC под отдельной identity; проверить процессы и ACL без чтения/копирования runtime.key. После явного согласия тестировать отдельный параллельный профиль, проверяя SID и MCP allow/deny. Не менять существующий HOST, Docker, реальные ACL, личные папки.

Статус: рабочий план / кандидат, НЕ утверждённая production-миграция.

## Актуализация 2026-10-13 — заменяет прежний статус G2 NEXT/NOT STARTED

G2 работает на независимом тестовом профиле под SID 1009, non-admin, UI disabled. G2-E PowerShell/.NET и Python matrix PASS через настоящий MCP; readback/cleanup и отсутствие запрещённых изменений подтверждены.
G2-F: owner HOST под alexa и native Repo доступны этой сессии; процесс G2 ограничен, вся сессия не изолирована. G2-G stop/rollback wrapper на копии PASS; тестовый G2 остановлен, конфигурация headless сохранена. Старые HOST/Repo сохраняют прежние PID и HTTP 200; production migration не выполнена.
Дальше: запуск restricted G2 для G3 и фактическая route isolation. [G2-G evidence](docs/G2_G_EVIDENCE_2026-10-13.md). [Evidence](docs/G2_E_F_EVIDENCE_2026-10-13.md).

## G3 — обнаружение writable runtime до ACL, 2026-10-13

После повторного запуска G2 PID 8452 под SID 1009, UI disabled, начат G3. Shared runtime в C:\Tools writable для G2: подтверждены handles и AccessCheck, старый owner HOST использует тот же DC index.js. G3 FAIL/STOP; код не подменяли, ACL не меняли. Tasks ACL и Docker pipes проверены адресно, остальные пути G3 открыты.
G2 остаётся запущенным. HOST/Repo сохранили исходные PID/CreationDate и HTTP 200. Подготовлены проверенные syntax/Preview и точечный ACL proposal только для SID 1009; Apply/Rollback не выполнялись, require separate owner decision.
[Evidence](docs/G3_READONLY_EVIDENCE_2026-10-13.md), [предложение](docs/G3_RUNTIME_ACL_PROPOSAL_2026-10-13.md). G4 production и session isolation не приняты.

## G3 — актуальная точка после ACL, 2026-10-13

Owner вручную применил согласованные четыре DACL в 14:12; backup сохранён. Реальные G2 mutation handles DENY, read/execute ALLOW; AccessCheck 22 758 runtime objects PASS, без writable exceptions и ошибок.
Junction и extended/localhost UNC synthetic paths сохраняют запреты. Все probe objects очищены, original markers metadata совпадают. HOST/Repo/G2 сохраняют исходные PID/CreationDate и HTTP 200; UI disabled.
G3 overall OPEN: localhost administrative API owner туннелей достижим G2; C$ разрешён INTERACTIVE; service user-defined handlers и actual chat route isolation не закрыты. Owner API mutations не выполнялись.
[Post-ACL evidence](docs/G3_POST_ACL_VERIFICATION_2026-10-13.md). Следующий шаг — поддерживаемая защита localhost admin API и разделение маршрутов перед G4. Повторный Apply или live Rollback не нужен на этой точке.

## Следующая точка — G3 local API, 2026-10-13 16:06 Asia/Bangkok

[Runtime evidence](docs/G3_LOCAL_API_RUNTIME_2026-10-13.md): official runtime side-by-side installed, два isolated Windows stdio теста PASS, G2 admin/Harpoon HTTP 404 при health/metrics 200; новые объекты защищены inherited SID 1009 deny. Candidate launchers и Preview/rollback helper готовы, production-переход PENDING. HOST/Repo/G2 сохранены; общий G3 и chat route isolation OPEN. Следующее — согласованный поочерёдный переход Repo → G2 → HOST, с локальным вводом G2 key и проверкой после каждого restart.

## Актуальная точка G2-only, 2026-10-13 18:06 Asia/Bangkok

[G2-only evidence](docs/G3_G2_ONLY_SWITCH_2026-10-13.md): пользователь выбрал сохранить HOST/Repo и переключить только G2. Launcher staged, duplicate SID guard PASS, local key/start PENDING. Не применять широкий helper трёх owner launchers. G2 — основа будущего limited HOST; G3 и G4 не приняты.
