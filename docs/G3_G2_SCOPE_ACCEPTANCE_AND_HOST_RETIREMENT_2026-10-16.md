# E43 — принят начальный G2 scope, прежний owner HOST остановлен

16 октября 2026. **Переход завершён в согласованных пределах.**
[JSON](G3_G2_SCOPE_ACCEPTANCE_AND_HOST_RETIREMENT_2026-10-16.json) ·
[Рабочая инструкция E42](G3_G2_INITIAL_SCOPE_AND_RUNBOOK_2026-10-16.md) ·
[План](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md).

В08:33:06 Asia/Bangkok пользователь ответил «давай» на конкретное предложение принять scope
E42/P01 и остановить только прежний общий owner HOST с последующим after-check.
Это решение о выбранном переходе, не разрешение менять другие контуры/права или удалять чаты.

## Принятое решение и предел

G2 — действующий Windows-инструмент FortisHostG1/SID1009/non-admin в собственной Session2.
Начальный рабочий каталог — C:\Users\FortisHostG1\AppData\Local\FortisHostG2\Workspace.
Собственные GUI/clipboard/browser/persistent state/scoped credentials/CLI и нужная сеть разрешены
по задаче. Новые owner project grants не выдавались. Fortis Repo остаётся основной средой разработки.

Принят ограниченный baseline E41/P01 → E42/P01 на имеющихся доказательствах.
Цель защиты owner сохраняется; остаточные Evidence Limitations приняты как предел доказанности.
Утверждение «нет никаких неизвестных handles/IPC/services/clipboard bridges» не принимается.
Ни один PARTIAL подпункт универсального свойства этим решением не превращается в общий PASS.

| Слой | Итог |
|---|---|
| G3 | Bounded G2 baseline ACCEPTED(scope), прежний широкий HOST route закрыт в проверенном live scope. Универсальная полнота/whole-chat гарантия не заявляется |
| G4 | Начальный Workspace policy/scope ACCEPTED(scope); universal ACL manager и новые grants не внедрены |
| G5 | Selected owner assets E40 PASS(scope); полная personal-security/backup программа не принята |
| G6 | Ручной daily entry/normal stop/recovery и инструкция E42 ACCEPTED(scope) на E20/E28/E29; произвольные crash/logoff/descendants не приняты |
| Whole-chat1.4 | PENDING для отдельной полной гарантии: Repo Windows RW и другие маршруты сохраняют свои полномочия |

Действующим начальным G2 пользоваться можно. Это не заявление «вся Windows и весь чат изолированы».

## Фактическая остановка и after-check

В01:34:01Z actual G2 before-call подтвердил old HOST13520 → cmd16092 → Node24724,
G2 runtime25920 и Repo runtime31420 с прежними CIM fingerprints/listeners.
Repo MCP также выполнил read-only CLI перед изменением.

Source Stop-LegacyOwnerHost.ps1,3127bytes, SHA256
557C3AEC158C82CD0C1FFA63797F4A5A8FC1487A5920FEB422B012CF85264742
подготовлен в Repo. Default Preview; fixed owner SID, exact three process IDs/names/session/parent/
native creation timestamps, HOST profile/path и EXE/recovery-launcher hashes.
Каждый original process handle открыт до Stop; Kill использует выбранные Process objects.
Это узкий одноразовый stop helper, не migration старого HOST на другой runtime.

Первый Preview отказал до мутаций: CIM timestamps округлены до microseconds, native
Process.StartTime сохраняет100ns ticks. Read-only owner сверка установила точные native значения;
pins исправлены без добавления tolerance и без снятия проверок:

| PID | Native CreatedUtc |
|---|---|
| 13520 | 2026-10-15T18:57:19.7775467Z |
| 16092 | 2026-10-15T18:57:20.0262353Z |
| 24724 | 2026-10-15T18:57:20.0652942Z |

Windows AST и corrected Preview прошли; KillAttempted пуст. Содержимое profiles/key/owner files
и raw argv/env не выводились. Profile mapping проверен локально, только boolean predicate.
Одинаковое имя процесса без fingerprint недостаточно.

В01:37:33Z через existing owner HOST запущен отдельный краткоживущий Windows PowerShell worker25304,
чтобы завершить выбранную chain при отключении самого owner MCP. ExecutionPolicy, privileges,
tasks/services/autostart не менялись. В01:37:38Z журнал записал Completed=true и ровно три
KillAttempted:13520,16092,24724. **Это адресный Process.Kill, не graceful Ctrl+C**;
normal G2 lifecycle/recovery остаётся отдельным ранее проверенным E28.

В01:38:02Z независимый G2 MCP/CLI подтвердил:

| Объект | Результат |
|---|---|
| HOST13520,cmd16092,Node24724 | Все три PID отсутствуют в успешном bounded CIM query |
| Port8080 | Listener отсутствует |
| Stop worker25304 | Уже завершился, не resident process |
| G2 runtime25920/Python18956/Node32272 | Те же Session2/parent/creation fingerprints; G2 MCP/CLI отвечает, SID1009/non-admin |
| G2 listener |127.0.0.1:54647, тот же runtime |
| Repo runtime31420 | Те же Session1/parent/creation fingerprint и listener127.0.0.1:50385 |

Независимый Repo MCP/CLI после Stop завершился: UID1000, /workspace/repos/tunnel; журнал прочитан
и Completed=true подтверждён. Это after-check выбранной цепочки/TCP и реальной доступности MCP,
не полный inventory машины и не continuous uptime.

Журнал: [фактический Stop](G3_LEGACY_HOST_STOP_ATTEMPT_2026-10-16.json).
Повторно Stop не вызывался; helper при existing journal отказывает до нового Stop.
После uncertain mutation сначала сверяют реальный эффект, не удаляют journal ради повтора.

## Что осталось и что больше не требуется

Обязательный шаг текущего согласованного перехода выполнен: scope принят, old HOST закрыт,
G2/Repo сохранены, инструкция/доказательства согласованы.

Остаются пределы доказательств:184 неразрешённых PSS types/relative desktop names,
неполная clipboard-bridge и service source/binary полнота, selected-assets scope,
недоказанная общая изоляция всех маршрутов чата и произвольный crash/logoff cleanup.
Они перечислены в E42 и main plan. Без новой конкретной угрозы/изменения/задачи это не новый
автоматический полный scan, fuzzing, reboot, ACL rewrite или повтор GUI/clipboard/lifecycle.

Для нового Windows-пути/программы/privileged посредника нужна адресная оценка и проверка
затронутой границы. Для whole-chat guarantee нужно отдельное технически обеспеченное ограничение
маршрутов; просто @G2/инструкция модели его не создают.
Установка старой панели, постоянные журналы и universal ACL manager — отдельные необязательные
Proposals при реальной потребности, не долг этого перехода.

Прежний connector/key не отозван; launcher/EXE/profile сохранены для осознанного локального
восстановления E42. Восстановление owner HOST сейчас не репетировалось. Его последующий ручной
запуск снова откроет широкий route; permanent revoke/невозможность relaunch не заявляются.
Автозапуск не настраивался и его полное отсутствие этим тестом не доказывается.
Старые чаты/плагины не удалялись; offline старого HOST после выбранного Stop ожидаем.

Изменены только новый stop source, metadata journal и документация. G2/Repo не перезапускались,
StopContainer/общий StopAccess не выполнялись. Runtime launcher/config, ACL/mounts/network/AV/
tasks/services/credentials не менялись. Source/native Windows проверены в указанном scope;
другой runtime/панель не устанавливались. Commit/push/публикация не выполнялись.
