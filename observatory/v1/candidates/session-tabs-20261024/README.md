# Fortis Observatory — вкладки сессий под хедером

**Статус: протестированный кандидат; НЕ установлен в Windows Viewer.**

## Что изменено

- Список сессий вынесен из первой боковой колонки в горизонтальную строку под основным toolbar внутри липкого заголовка.
- Активная сессия выделяется. Цветной статус показан по нижней рамке вкладки; полный статус доступен в tooltip/скринридере.
- Длинные названия сокращаются визуально, а список прокручивается горизонтально; список при обновлении сохраняет scrollLeft.
- Вкладки поддерживают мышь и клавиши ArrowLeft, ArrowRight, Home, End.
- Первая колонка «Чаты и привязка» оставляет «Чаты из браузера», «Подробности сессии» и команды Notifier. Существующие четыре колонки и resizers остаются.
- Смена вкладки продолжает обновлять задачи, записи, архив и информацию Notifier для выбранной сессии.
- Нет изменений API, Docker, G2, Repo tunnel, pairings, Bearer auth или архивных файлов.

## Пакет

- `owner_viewer.py` — полный кандидат изменённого Viewer; используется установщиком, НЕ рабочий source.
- `session-tabs.patch` — unified diff относительно текущей исходной копии.
- `Apply-ObservatorySessionTabs.ps1` — guarded Preview/Install/Rollback для защищённой Windows установки.
- `test_owner_viewer_ui.mjs` — UI regression tests.

Базовый SHA-256 owner_viewer.py: `a3eb75f113a6152adbb3381d6a9b6cd845dec4e927c7b20c80885968e635b48d`.
Кандидат SHA-256 owner_viewer.py: `a34cb4ffd3805446c9e81e4051bcbe0018a14b6a507b65b9eecf10b23d5a3035`.

## Применение под Windows пользователем alexa

Открой обычный PowerShell от имени **alexa** (не G2). Сначала выполни:

```powershell
$tabs = 'C:\Users\alexa\Repos\tunnel\observatory\v1\candidates\session-tabs-20261024\Apply-ObservatorySessionTabs.ps1'
& $tabs -Action Preview
```

Ожидается `PREVIEW_ONLY=True` и `READY_TO_INSTALL=True`. При `False` не устанавливать — исходная версия не совпала с проверенной.

Сохрани текущую работу в Viewer, останови **только Viewer** (Ctrl+C в его PowerShell; порт 18755 должен быть свободен). Docker, G2, Fortis Repo Tunnel не трогать.

```powershell
& $tabs -Action Install
```

Должно появиться `INSTALL_OK=True` и путь `BACKUP=...` в защищённом каталоге. Запусти Viewer прежним ярлыком или стандартным owner-launch.

## Проверка

- Вкладки с названиями подключённых сессий находятся под кнопками хедера.
- При выборе вкладки меняются задачи и записи; другая сессия не смешивается с текущей.
- При обновлении выбранная сессия и горизонтальная прокрутка сохраняются.
- «Чаты из браузера», Notifier и Textbox по-прежнему доступны.
- Состояние задач отображается цветной линией вкладки, подробности — при наведении.

## Откат

Закрой только Viewer и выполни (используй настоящий путь `BACKUP=...` из установки):

```powershell
& $tabs -Action Rollback -BackupFile 'C:\Users\alexa\AppData\Local\FortisObservatoryV1\Viewer\owner_viewer.before-session-tabs-...bak'
```

После `ROLLBACK_OK=True` снова запусти Viewer прежним ярлыком.

## Проверки и ограничения

- Python Viewer: **22/22 PASS** в изолированной candidate копии с неизменёнными зависимостями.
- Node UI: все сценарии PASS, в том числе keyboard, horizontal scroll, session selection, Notifier pairing, lifecycle status, XSS-safe rendering.
- Python parse/py_compile PASS; проверенные hashes совпадают с указанными.
- Реальная PowerShell установка, текущий Windows Viewer и визуальный smoke в Edge пока НЕ ПРОВЕРЕНЫ. PS installer имеет хешевые/ACL/SID ограничения и останавливается при несовпадениях.
- Работающий source `C:\Users\alexa\Repos\tunnel\observatory\v1\owner_viewer.py` не переписан.
