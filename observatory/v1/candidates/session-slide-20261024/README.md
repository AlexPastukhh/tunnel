# Observatory — живое перетаскивание вкладок

**Патч готов, Windows Viewer ещё не установлен.** 24.10.2026.

Теперь вкладка следует за указателем во время перетаскивания, а соседние вкладки плавно сдвигаются ещё до отпускания кнопки мыши. Это не стандартный HTML Drag & Drop с полупрозрачным «призраком», а реальное перемещение текущей вкладки. На завершении жеста порядок сохраняется в localStorage. До отпускания мыши ничего не записывается. Отмена жеста (включая Escape) восстанавливает прежний порядок.

Также сохранены: обычный клик по вкладке, Alt+стрелки для перестановки, стрелки для переключения, текущая выбранная сессия, статусы, действия Notifier/Send. При переполнении строки работает автоматическая горизонтальная прокрутка к краю.

## Проверки исходников

- `node test_owner_viewer_ui.mjs`: PASS — синтетический pointerdown/move/up, плавный сдвиг соседей, запрет сохранения во время перемещения, отмена, вертикальный жест, нормальный клик, автопрокрутка.
- `python3 -m unittest -q test_owner_viewer.py test_owner_dispatch.py`: 44/44 PASS.
- `python3 -m py_compile owner_viewer.py`: PASS.
- `git apply --reverse --check`: PASS на текущем исходнике, патч из коммитированной базы применим.
- **Реальный Edge не проверен.**

## Точные версии

- Предыдущий установленный Viewer должен иметь SHA-256 `f3230cb531d89d9cc4f60bea52fd5722b1b1e82a724759dede6636aabf806c8a` (если отличается, скрипт остановится).
- Новый `owner_viewer.py` SHA-256 `d5a752267ed78bcadf4da4e27b71452f3fb2d2c69fb4d138bda3af13bbf49878`.
- Защищённый PowerShell installer SHA-256 `4a77ebdc9eceb73bd5d927960ac32a15e129b2c0842a56d92733e003ad4cced0`.

## Установка под обычным владельцем Windows, не Administrator и не G2

В **обычном PowerShell пользователя alexa** выполни:

```powershell
$ErrorActionPreference = 'Stop'
$src = 'C:\Users\alexa\Repos\tunnel\observatory\v1\candidates\session-slide-20261024\Apply-ObservatorySlidingTabs.ps1'
$sha = '4a77ebdc9eceb73bd5d927960ac32a15e129b2c0842a56d92733e003ad4cced0'
if ((Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash.ToLowerInvariant() -cne $sha) {
    throw 'SHA установщика не совпадает'
}
$dst = Join-Path $env:LOCALAPPDATA 'FortisObservatoryV1\Viewer\Apply-ObservatorySlidingTabs.ps1'
Copy-Item -LiteralPath $src -Destination $dst -Force
if ((Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash.ToLowerInvariant() -cne $sha) {
    throw 'SHA копии не совпадает'
}
& $dst -Action Preview
```

Продолжай **только если** напечатано `READY_TO_INSTALL=True`. Если False — остановись и пришли `InstalledSHA`: это не ошибка мыши, а расхождение версии установленного Viewer. **Не отключай проверку.**

После успешного Preview останови **только** Viewer (его окно, `Ctrl+C`), затем в том же PowerShell:

```powershell
& $dst -Action Install
```

Дождись `INSTALL_OK=True` и сохрани строку `BACKUP=...`. Запусти Viewer прежним ярлыком; обнови Edge `Ctrl+R`.

При необходимости отката снова останови только Viewer:

```powershell
& $dst -Action Rollback -BackupFile '<точный путь из BACKUP=...>'
```

Потом запусти прежний Viewer. Docker, оба Repo-туннеля, G2 и данные задач не меняются.

## Smoke-проверка в Edge

Зажми левую кнопку мыши на вкладке «графы» и проведи вправо через соседнюю вкладку. Пока держишь кнопку, первая вкладка должна **двигаться вместе с указателем**, а соседняя — **сдвигаться с анимацией**. Отпусти: порядок сохраняется после обновления страницы. Простой клик продолжает открывать выбранную сессию. Для проверки отказа от сохранения прерви жест, например событием `pointercancel`; после отмены прежний порядок должен остаться.

Код затрагивает только Viewer frontend (`owner_viewer.py`) и его синтетический UI-тест; Notifier/Dispatch/Windows installation не менялись автоматически.
