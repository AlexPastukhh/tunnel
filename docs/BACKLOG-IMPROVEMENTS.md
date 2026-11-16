# Backlog улучшений — Tunnel / Repo1 / Repo2

**Единый backlog этого репозитория.** Пункты ниже — будущая работа, не разрешение менять Windows, Docker или действующие соединения. Выполненные изменения подтверждаются отдельно в `docs/CURRENT_STATE.md` и dated evidence. Подробные технические планы остаются в существующих документах и не копируются сюда.

## Приоритет: проверяемые Windows Guards

- Разработать повторяемый **read-only Preview обоих Repo1/Repo2 Guards** перед изменением Docker image, mounts, network, user, capabilities, source workers или launcher chain. Проверка исходников в Docker **не доказывает** приём Windows guard; итог подтверждает только owner-run Windows PowerShell 5.1 и live reconnect.
- Свести owner-команды в один защищённый launcher/runner c фиксированными допустимыми действиями `Preview` / `Check` / `Apply` и точными exit codes. Для каждой операции показывать идентичность container/image/source SHA, последствия, остановку при ошибке и результат; **не выдавать AI произвольный PowerShell или Docker Engine**.
- При отдельном обновлении worker source — использовать уже существующий `runtime/windows-repo/Invoke-FortisRepo.ps1` и парный `script-control-center/tools/Update-Windows-ControlCenter.ps1`. Не повторять разработанный механизм зеркалирования и девятифайловый manifest.
- Проверить неоднозначность Repo1-process detection перед будущим запуском/перезапуском; owner-preflight должен отличать работающий чужой процесс от отсутствующего соединения (см. `runtime/windows-repo/README.md`).

## Ожидающая owner acceptance

- Подтвердить cold boot/reboot, альтернативный порядок старта и длительную
  стабильность Repo1/Repo2 на выбранном runtime; после каждого нового cutover
  отделять Guard Preview от реального MCP reconnect.
- Отработать rollback в изолированном согласованном сценарии. Наличие сохранённого
  image/container/state не доказывает выполненное восстановление.
- Старое `REPO_RECONNECT_PENDING` и process observation от pre-cutover GO3
  2026-11-04 не являются текущим блокером: subsequent deployment/reconnect evidence
  хранится у Fortis Container. Новую неоднозначность разбирать только по свежей
  identity/Guard inventory, без повторения закрытой диагностики по умолчанию.

## Повторяемый производственный цикл

- Добавить regression tests для Docker-effective settings → shared `FortisContainerPolicy.ps1` verdict, включая Repo1/Repo2 profile differences, отсутствие неожиданных mounts и сохранение Qwen connections. Полные host/Windows проверки всё равно остаются у владельца.
- Для любого host-only шага применять **общий** Fortis host-only UC-CONT-025 (UC-CONT-015 — только передача артефакта): source in project repo → owner-reviewed PowerShell 5.1 → проверяемый вывод/STOP; не превращать этот backlog в ещё один runbook передачи файлов.
- После GitHub-only source update проверять separate Windows Preview и controlled reconnect: опубликованный коммит не перезапускает workers.

## Навигация

Актуальная Windows source/Guard карта: [`runtime/windows-repo/README.md`](../runtime/windows-repo/README.md), [`docs/FORTIS_GIT_WINDOWS_LAUNCHER_WORKFLOW.md`](FORTIS_GIT_WINDOWS_LAUNCHER_WORKFLOW.md), [`docs/OPERATIONS.md`](OPERATIONS.md). Общие Docker build/host-only/backup случаи принадлежат `fortis-container`, не этому репозиторию.
