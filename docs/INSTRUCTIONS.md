# Где менять исходники и как доставлять изменения

Эта страница владеет маршрутом доставки, а не релизными статусами. Текущие версии и результаты — у [владельцев компонентов](CURRENT_STATE.md); правила сопровождения — в [едином протоколе](agent-workflow/README.md).

## Выбрать источник и контур

| Что меняется | Где источник / маршрут | Где проверять применение |
| --- | --- | --- |
| Два native Repo Tunnel | [Runtime source map](../runtime/README.md), [security-реестр](agent-workflow/TUNNEL_SECURITY_ISOLATION.md) | Installed Windows launcher/control/guard/Client/Runtime и Linux Direct DC — разные звенья; Windows cutover только по отдельному owner plan |
| G2 | [Guest entry source](../runtime/host-g2/runtime-api-migration/start-g2-guest-session.ps1), [gate](../runtime/host-g2/g2-stdio-gate.py) | [G2 plan](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md) и [E42 runbook](G3_G2_INITIAL_SCOPE_AND_RUNBOOK_2026-10-16.md) |
| Project Checker | [Source README](../runtime/userscript-updater/README.md); reviewed offline package и [ручная установка/приёмка/откат](../runtime/userscript-updater/release/WINDOWS_ACCEPTANCE.md) | [PLAN](userscript-updater/PLAN.md), [implementation log](userscript-updater/IMPLEMENTATION_LOG.md), [native Windows gate](userscript-updater/WINDOWS_TRUST_BOUNDARY.md); агент выполняет только Repo/Docker, Windows — владелец |
| Observatory / Notifier / Viewer | [README V1](../observatory/v1/README.md) | Отдельно Docker, Windows Viewer и каждый browser profile; [Windows setup](../observatory/v1/OWNER_VIEWER_MANUAL_SETUP.md) |
| Hosted Site | Собственный source/deployment в Sites Git; [SITES](SITES.md) | Точный source commit и опубликованная Site version; native Tunnel не меняется |
| Plugin-owned skills/metadata | Актуальный update-plugin workflow конкретного plugin | Поддерживаемый package/release; не через произвольную Site страницу |
| Snapshot / Broker | [Сценарий](SNAPSHOT.md), [Broker source/runbook](../runtime/broker/README.md) | Реальный worker/политика экспорта, отдельно от прямого Repo mount доступа |
| Документация | Этот checkout, документ-владелец | Read-back/diff и scoped commit; deploy/restart не требуется |

## Порядок доставки

1. Определить точный изменяемый компонент, текущую установленную базу, полномочия и требуемый scope. Сохранить чужие изменения рабочего дерева/индекса; не расширять audience, mounts или права попутно.
2. Подготовить и проверить source. `runtime/` — копии для разработки/контролируемой доставки, не автоматически применяемая конфигурация. Исходники и installed bytes сверять независимо.
3. Для внешней/native установки подготовить зафиксированный состав и зависимости, проверку путей/ACL, независимые backup/recovery и read-back. Windows-действия выполняет владелец по конкретному согласованному плану. Repo dev-source не запускать как доверенное owner-приложение.
4. Применять только выбранный контур и версию. Restart выполнять только при необходимости и наличии разрешённого окна; общие два Repo/Docker не перезапускать ради документации. Site deploy, Git commit/push, Windows install и browser update не подменяют друг друга.
5. Проверить фактическую доставленную версию и подходящий functional smoke. После неопределённой мутации сначала проверить результат. Source tests не объявлять installed/Windows PASS.
6. Результат, ограничения и следующий шаг записать у владельца компонента и в его журнале. Эту страницу менять, только когда изменился маршрут доставки; текущие release summaries сюда не дописывать.

Для изменения tools/instructions/UI metadata проверять реальный `initialize/tools/list` и нужный ресурс после доставки: cached cards не являются доказательством новой версии. Для Sites/plugins открывать актуальный установленный skill, не копировать сюда его изменяемые команды и schemas.

## Ограничения этой установки

Не возвращать Repo на legacy Bridge/probe и не использовать старый Bridge rollback из исторического документа. Независимое Direct recovery и фактическая приёмка — в security/STATE. Не запускать retired owner HOST ради ротации ключа или проверки документации. Ключи, полные saved profiles и приватные payload не входят в Git/release evidence.

[Прежняя полная лента INSTRUCTIONS](INSTRUCTIONS_HISTORY_20261026.md) сохранена как история. Старые fingerprints, Stop/Install/Apply и NEXT оттуда не являются действующей процедурой.
