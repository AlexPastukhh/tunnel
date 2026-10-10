# Перенос репозиториев

Текущий общий каталог — **C:\Users\alexa\Repos**, не прежний план C:\Users\alexa\Documents\Repos.

2026-10-10 перенесены 19 зарегистрированных основных Git working trees. Сохранены HEAD, repo identity и статус; на момент окончания их main worktrees были clean. Registry Bridge обновлён по путям, экспортные разрешения не расширены. Совместимость старых путей поддерживают Windows junctions.

До добавления tunnel здесь уже находилось 20 Git-корней: 19 зарегистрированных и feature-projection. Новый tunnel — дополнительный Git repo; число каталогов не равно числу registry aliases. __pycache__ не является репозиторием.

## Сохранённые исключения

У obs-planning-docs есть два отдельные dirty linked worktree в Windows Temp:
- obs-prompt-groups-patch-stage-20261009
- obs-state-sharing-stage-20261010

Их изменения не удалены и не объявлены закоммиченными. Windows metadata repaired после переноса main root. Эти Temp-папки не смонтированы в Docker; не prune/repair их из Linux по причине недоступных Windows путей.

Старая C:\Users\alexa\Documents\Repos\gdoc оставлена: чистая, но отстаёт от авторитетной копии на 74 commits на момент проверки. Не удалять без отдельного решения.

## Блокировки / фоновые процессы

Закрытие вкладки браузера не останавливает Vite/Node server. При прошлой попытке работали prototype Vite на 4195/4196; после их остановки блокировка осталась у Desktop Commander. Перенос завершился после его restart. Не завершать все Node процессы без установления владельца/назначения.

Два prototype server после переноса не запускались автоматически. Сами observability prototypes остаются в Documents\prot; перенос документации не перемещает приложения и не меняет ярлыки.

Предыдущий план сохранён в history/prot/REPOSITORY-MIGRATION-PLAN.md. Его старые destination/status не использовать как текущую правду.
