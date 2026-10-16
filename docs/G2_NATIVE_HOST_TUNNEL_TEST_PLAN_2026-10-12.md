# G2 — отдельный план тестового native HOST Tunnel под FortisHostG1
Дата исходного плана: 2026-10-12. Актуализация 2026-10-13: G2 запущен; G2-E PASS, G2-F route inventory выполнен / session isolation OPEN, G2-G scoped stop/rollback PASS; после G2-G G2 был остановлен; в G3 повторно запущен; shared runtime blocker исправлен владельцем, post-ACL PASS, общий G3 OPEN. Основной план: Fortis_Windows_Security_Plan_2026-10-12_v5.md (§15.3). Полная расширенная версия этого отдельного плана выдана пользователю в чате как Fortis_G2_Native_HOST_Tunnel_Plan_2026-10-12.md.

## Цель и уже подтверждённые условия
Доказать, что самостоятельный тестовый native tunnel-client → Desktop Commander → shell действительно работает под FORTIS_M\FortisHostG1, со стандартным непривилегированным токеном, независимой авторизацией, не затрагивает действующие HOST и Repo от alexa и соблюдает NTFS ACL через MCP file tools и shell.
G1 подтверждён: FortisHostG1 стандартный Windows пользователь (SID заканчивается на 1009, не Administrators/CodexSandboxUsers), PowerShell, дочерний PowerShell и Python 3.13.16 продемонстрировали RW read/write, RO read-only, DENY access denied. Старые тестовые ACE SID 1008 удалены; осталось проверить rollback/G1 elevation при необходимости.
Синтетические тестовые пути C:\Users\Public\Documents\FortisHostG1Probe\RW, RO и DENY. Python находится в C:\Users\FortisHostG1\AppData\Local\Programs\Python\Python313\python.exe.
Существующий owner launcher: C:\Users\alexa\Documents\prot\Start-Desktop-Commander-Secure-Tunnel.ps1 → C:\Tools\tunnel-client\tunnel-client.exe run --profile desktop-commander. Стандартный тестовый пользователь не должен обращаться к конфигу/ключу owner (%APPDATA%\tunnel-client\runtime.key). Текущий owner HOST нельзя останавливать и перезапускать. Native Repo, Fortis Repo Docker и Observatory остаются в стороне.

## G2-A — read-only исследование (первый следующий шаг; без изменений)
1. Зафиксировать версии, PID, владельца, executable paths, health/ports, существующие имена native профилей/маршрутов, не читая секреты и не останавливая процессы.
2. Проверить, может ли FortisHostG1 читать/запускать tunnel-client.exe и имеющиеся системные бинарники без доступа к C:\Users\alexa. Проверять только метаданные/ACL, не менять их.
3. Через документацию или безопасные CLI help/version узнать: поддерживается ли отдельный test profile, login/registration, independent credential/state directory, изменение endpoint/port без конфликта, secure revocation. НЕ придумывать флаги.
4. Определить путь к Node и Desktop Commander под G1: user-local установка при необходимости, pinned версия и проверенное происхождение; ничего не устанавливать сейчас. ExecutionPolicy .ps1 ранее блокировал запуск под G1: глобальную политику не отключать.
5. Результат: таблица исполняемых файлов, independent auth вариантов, побочных эффектов и блокировок. Если независимый credential официально не поддержан — BLOCKED, не копировать ключ владельца.
Gate: предъявить владельцу конкретную схему, запросить отдельное согласие на provisioning.

## G2-B — отдельные credentials и test namespace (только после согласия)
Создать отдельный поддерживаемый тестовый профиль/регистрацию/учётные данные без переноса runtime.key или секретов alexa. Секреты вводит и хранит только владелец в защищённом профиле FortisHostG1, без публикации в чат, командной строке, stdout и репозитории.
Выбрать уникальные test profile/port/route/state/log path без конфликта с owner desktop-commander и native Repo; проверить, что registration не заменяет рабочий канал.
Выход: схема происхождения, owner SID, мест хранения (метаданные без содержимого) и отзыва test credential.
STOP при потребности в owner secret/общем mutable profile/state или невозможности параллельности.

## G2-C — подготовка runtime под новым SID (только после согласия)
Использовать общий tunnel-client бинарник только при достаточном Read/Execute без разрешения его переписать. Если нужен Node/Desktop Commander — user-scoped verified install под FortisHostG1 (фиксировать версии/signature/hash/путь/rollback).
Использовать абсолютные пути, не открывать личный профиль alexa, не включать админа, не менять системный PATH, ExecutionPolicy, UAC, службы, реестр.
Подготовить только новый test-specific каталог для log/state под G1. Зафиксировать изменения до запуска.
Gate: независимость клиента/ключа/state подтверждена, нет зависимости от privileged посредника.

## G2-D — безопасный параллельный MCP handshake (отдельное согласие)
Запустить один test tunnel-client → Desktop Commander от имени FortisHostG1 и через тестовый профиль. Перед запуском сверить production PID/health, избегать того же профиля/port/listener.
После старта проверить SID и токен test tunnel-client, node.exe и child shell (whoami, whoami /all, parent PIDs), что никто не запущен от alexa, Administrator или SYSTEM.
Проверить MCP initialize, инструменты и read-only Windows диагностическую команду через новый test route, затем health существующих туннелей.
STOP при конфликте маршрута, падении текущего HOST/Repo, elevated/owner token либо неверной аутентификации.

## G2-E — тест synthetic ACL через настоящий MCP
Сначала MCP file read на RW и RO = ALLOW, DENY = DENIED; затем write/create только в RW = ALLOW, в RO и DENY = DENIED. Любой тестовый файл в RW должен иметь уникальное имя probe-* и удаляться после readback.
Отдельно проверить вызов shell/PowerShell/.NET и Python из MCP: RW read/write True/True; RO True/False; DENY False/False. Убедиться в точном SID child процесса и отсутствии записи в RO/DENY. Политика MCP allowedDirectories может давать собственный запрет; отдельно документировать, где ограничение ОС, а где MCP.
Проверить одну пользовательски полезную неадминистративную read-only диагностическую операцию, без реальных секретов.
Никаких обращений к настоящим личным папкам, токенам, cookies или критическим службам.

## G2-F — граница маршрутов
Подтверждение ограничения одного test tunnel НЕ означает ограничения чата, где одновременно доступны owner HOST, Sites/коннекторы или Fortis Repo с RW Windows bind mounts.
Зафиксировать список ChatGPT/MCP маршрутов, реально доступных тестовой сессии, и возможность изоляции/раздельного подключения. Полная проверка обходов через privileged tasks/services/IPC/localhost/SMB/other routes — G3.
Не объявлять режим защищённым, пока существует другой broad route в том же доверенном контуре.

## G2-G — остановка и rollback
Остановить только проверенный тестовый PID/его дочернюю цепочку; сохранить текущие PID и health owner HOST/Repo. Отозвать только test credential при необходимости по согласованной процедуре. Не удалять чужие конфиги и ключи.
Сохранить sanitized evidence: caller SID, PID/parent, версии, MCP handshake, результаты tests RW/RO/DENY, список созданных тестовых объектов, выявленные ограничения, rollback и open risks.
Отдельно проверить после остановки: старые HOST/Repo живы, owner ACL, launcher и runtime credentials не менялись.

## PASS / FAIL / BLOCKED
G2 PASS: независимые profile/auth/state; SID 1009 на tunnel-client/Node/child; MCP initialized; положительные диагностические задачи работают; все synthetic ACL соблюдаются через MCP file tools и shell/Python; нет production impact; есть безопасный rollback; secrets не раскрыты.
FAIL: wrong/elevated token; запрет DENY обойдён; изменён реальный профиль/туннель; появился непредвиденный доступ или побочный эффект.
BLOCKED: отдельная официальная auth недоступна или требует owner runtime.key/admin/system changes. Рассмотреть на G4 Windows Sandbox/VM/narrow broker, не обходить блокировку.
Следующий G3 — проверка обходных путей. Переход к реальному production limited HOST только отдельным решением G4; G5 personal security самостоятельный слой; G6 эксплуатация и восстановление.

## STOP условия
Запрос owner пароля/credential, runtime.key/токена, cookies; повышение через UAC/admin; расширение ACL C:\Users\alexa; конфликт profile/port; изменение действующего HOST/Repo; разрешение запрещённой операции. Немедленно прекратить тесты и задокументировать blocker/rollback.

## Evidence чеклист
[ ] A: read-only inventory и supported independent auth доказаны.
[ ] B: отдельное разрешение, отдельная auth/namespace и revocation plan.
[ ] C: версии, provenance, SID/permissions и test-local runtime.
[ ] D: Test PID tree/token + MCP initialization + unchanged production health.
[x] E: MCP file tools (переданная история), новые PowerShell/Python child; RW/RO/DENY matrix PASS.
[x] F: route inventory выполнен; broad owner HOST/Repo доступны, session isolation OPEN.
[x] G: test stopped, production PID/CreationDate и HTTP 200 сохранены; backup tested on temporary copy, sanitized results saved.

Шаблон: дата | route | PID/token | tool | synthetic path | операция | expected | actual | evidence без секретов | PASS/FAIL/BLOCKED.

### Следующее действие
Только G2-A read-only: выяснить официально поддерживаемую независимую native auth/registration и доступность executable/Node/Desktop Commander под FortisHostG1. После этого предоставить конкретное предложение G2-B и запросить явное разрешение.
## Актуальная точка продолжения — 2026-10-13

Разделы A–D выше сохраняют исходную последовательность; указание начинать с A устарело. G2-G выполнен, см. [evidence](G2_G_EVIDENCE_2026-10-13.md). Далее: поддерживаемая защита localhost administrative API и фактическая route isolation. Согласованные runtime ACL уже применены владельцем, post-ACL verification PASS; G3 overall OPEN. G3 начат: исходный writable runtime blocker исправлен, runtime gate PASS; общий G3 OPEN. См. [post-ACL evidence](G3_POST_ACL_VERIFICATION_2026-10-13.md). G2 повторно запущен; owner HOST/Repo сохранены. Production migration не начата; согласованные четыре ACL применены вручную владельцем. [Доказательства G2-E/F](G2_E_F_EVIDENCE_2026-10-13.md).

## Точка продолжения — local API, 2026-10-13 16:06 Asia/Bangkok

[Evidence и переход](G3_LOCAL_API_RUNTIME_2026-10-13.md): narrow runtime installed side-by-side, isolated и G2 HTTP/ACL tests PASS; live G2/owner tunnels не переключены. Подготовлены pinned candidates, Preview/backup/rollback. Production switch PENDING, whole-chat isolation OPEN. Существующую FortisHostG1-консоль закрывать только на согласованном шаге G2 restart; test key вводится локально.
