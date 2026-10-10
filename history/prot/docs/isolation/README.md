# Isolation and access boundaries

Статус: архитектура спроектирована, основная container/VM boundary ещё не внедрена.

Главный подробный документ: [../../SECURE-ACCESS-CONTROL-PLAN.md](../../SECURE-ACCESS-CONTROL-PLAN.md)

## Основной принцип

Security boundary должна обеспечиваться отсутствием capability, а не только prompt-инструкцией или Desktop Commander `allowedDirectories`.

## Планируемые режимы

### REPO
Обычная работа с кодом в изолированном container/VM контуре.
Постоянно доступен только выбранный repo root и явно выданные временные mounts.

### SANDBOX GUI
Отдельная GUI-среда для autonomous screenshots, mouse/keyboard и UI testing.
Не должна автоматически давать управление основным HOST desktop.

### HOST MAINTENANCE
Нативный Desktop Commander с широким доступом.
Запуск вручную, без autostart, только для задач, которым реально нужен HOST.

### HOST GUI
Отдельный повышенный уровень разрешения поверх HOST CLI/filesystem.
Не подразумевается автоматически.

## Важные границы

- writable bind mount даёт реальный доступ к host-файлам в этой папке;
- monitoring не является security boundary;
- наличие Sandbox plugin не должно давать произвольный host shell;
- runtime key и controller files остаются вне Sandbox/Repo container;
- Docker socket/API нельзя передавать Repo Mode;
- временный grant должен требовать локального пользовательского действия.

## Связанные документы

- [../tunnel/README.md](../tunnel/README.md)
- [../sandbox-plugin/README.md](../sandbox-plugin/README.md)
- [../observability/README.md](../observability/README.md)
- [../../SANDBOX-GUI-PLAN.md](../../SANDBOX-GUI-PLAN.md)

Этот файл — короткая карта boundaries. Детальные threat model, mounts, controller flow и acceptance criteria остаются в `SECURE-ACCESS-CONTROL-PLAN.md`.