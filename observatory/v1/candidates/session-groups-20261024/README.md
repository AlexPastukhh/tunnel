# Observatory V1 — группы, доступность и архив сессий

**2026-10-24. Source-only release candidate. Windows Viewer и Edge ещё НЕ установлены/не проверены.** Основные исходники Fortis Repo обновлены; архитектура Docker-архива, Notifier и две Repo-связи не изменялись.

## Изменения

- **Сильное выделение выбранной сессии**: светлая рамка, контрастный синий фон, яркий маркер.
- **На связи**: зарегистрированные сессии, для которых Notifier с одобренным proof прислал heartbeat не старше 25 секунд. В строке сохраняется слайд-перетаскивание мышью и текущая клавиатурная навигация.
- **Доступны · не подключены**: вторая строка с отдельным бирюзовым стилем и явным действием «Подключить». Данные взяты из существующего защищённого discovery; подозрительные/дублирующиеся claimant не получают кнопку подключения, остаются с диагностикой в исходном списке «Чаты из браузера».
- **Нет связи**: отдельно сворачиваемый блок с числом зарегистрированных сессий: оранжевые — с одобренной привязкой, но без heartbeat; серо-синие — зарегистрированные без одобренной привязки. Ручное сворачивание сохраняется в localStorage, опрос не разворачивает блок принудительно.
- **Архив**: отдельная свёрнутая секция восстановления. Сессии из архива не показываются среди обычных доступных, неподключённых и недоступных; штатный автовыбор после опроса пропускает архивированные сессии.
- **Отключить Notifier**: отозвать owner-approved enrollment и dispatch, сохранив сессию и историю. Она остаётся зарегистрированной, но без live-привязки.
- **Архивировать сессию**: явное подтверждение, запись ID/Chat ID в owner-only \`archived-sessions.json\`, отзыв привязки/dispatch и исключение из оперативных списков. История и оригиналы в Docker не удаляются. При восстановлении Notifier может потребовать нового подключения/одобрения.

Это **статус рабочей панели, а не запрет независимого создания событий в Docker**: архивные данные сохранены; сервер блокирует новые owner-dispatch к архивированной сессии, но уже заявленную ChatGPT попытку Send задним числом отменить нельзя. При чтении файла архива с ошибкой Viewer не показывает непроверенные сессии как доступные (fail-closed).

## Проверки

- 67 Python тестов \`test_owner_viewer.py\`, \`test_owner_enrollment.py\`, \`test_owner_dispatch.py\` — результат см. release log/текущий отчёт.
- Синтетический Node UI-тест: online/unconnected/offline/archive, owner POST, readback, изоляция задач, drag, явный Send, статус, старый UI без изменений.
- Владельцу необходимо провести **ручную проверку Edge** после Windows install. Никакого утверждения о live установке без неё.

## Источники и точные SHA

Предыдущие установленные версии (должны совпасть, иначе Preview/Install откажет):
- \`owner_viewer.py\` SHA-256 **d5a752267ed78bcadf4da4e27b71452f3fb2d2c69fb4d138bda3af13bbf49878** (sliding tabs).
- \`owner_enrollment.py\` SHA-256 **51ce3eb96fd3da285c591c063cb71642863b825d5fef63bc6c5060a814ca03e3**.
- \`owner_dispatch.py\` SHA-256 **9da1bc2a223804660c2a9ea9033b86889dca7119d3a1b1dab18c85565360fea5**; **не заменяется**.

Новая версия:
- \`owner_viewer.py\` **eae6879f7559b6b540acbdbaa3ced1c031935883aa6793f8a5901a1d658b3e05**
- \`owner_enrollment.py\` **873ec864c5996234e930c3ceaf9fb75cbcdea945b7b84c76ea47d1cef164b0d3**
- \`Apply-ObservatorySessionGroups.ps1\` **caff60d59013082f60f4cea5b16605493b9b4ab70b8ad1ac0cf07401f7c7f810**

Точный JSON manifest содержит SHA всех файлов и unified diff \`session-groups.patch\`. Если локальный установленный Viewer отличается от ожидаемой предыдущей версии, **не отключай проверку SHA**: версия должна быть исследована отдельно.

## Windows: установка владельцем без эскалации

Исполняй в **обычном PowerShell пользователя alexa** (не Administrator/G2). Скопируй сначала проверенный скрипт в уже существующий защищённый каталог:

\`\`\`powershell
$ErrorActionPreference = 'Stop'
$src = 'C:\Users\alexa\Repos\tunnel\observatory\v1\candidates\session-groups-20261024\Apply-ObservatorySessionGroups.ps1'
$expected = 'caff60d59013082f60f4cea5b16605493b9b4ab70b8ad1ac0cf07401f7c7f810'
if (((Get-Item -LiteralPath $src).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Ссылка вместо файла запрещена' }
if ((Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash.ToLowerInvariant() -cne $expected) { throw 'SHA не совпадает' }
$dst = Join-Path $env:LOCALAPPDATA 'FortisObservatoryV1\Viewer\Apply-ObservatorySessionGroups.ps1'
if (Test-Path -LiteralPath $dst) {
  if (((Get-Item -LiteralPath $dst).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'Ссылка в Viewer запрещена' }
}
Copy-Item -LiteralPath $src -Destination $dst -Force
if ((Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash.ToLowerInvariant() -cne $expected) { throw 'SHA копии не совпадает' }
& $dst -Action Preview
\`\`\`

**Только при \`PREVIEW_OK=True\`:** останови ТОЛЬКО прежний Viewer, оставив Docker и Notifier работающими. Затем:

\`\`\`powershell
& $dst -Action Install
\`\`\`

Сохрани \`BACKUP_ID\`; скрипт защитит и проверит резервные копии обоих файлов. Затем запусти Viewer существующим ярлыком и обнови вкладку Edge.

**Откат:** останови только Viewer, затем:

\`\`\`powershell
& $dst -Action Rollback -BackupId '<точный BACKUP_ID из Install>'
\`\`\`

После \`ROLLBACK_OK=True\` запусти прежний Viewer. Резервные копии и \`archived-sessions.json\` остаются в owner-only каталоге.

## Edge smoke (ручной)

1. Открой две зарегистрированные сессии с работающим Notifier и одну закрытую. На связи — только те, по которым пришёл свежий одобренный heartbeat. Пока не пришёл — показывай честный offline.
2. Открой новый ChatGPT-чат с Notifier, но не подключай его. Он появляется в бирюзовой группе, кнопка \`Подключить\` делает один адресный connect, не нажимая ChatGPT Send.
3. Проверь выделение выбранной сессии, перетаскивание вкладок мышью, refresh и сворачивание offline блока.
4. Для **тестовой**, не критичной сессии нажми \`Архивировать\`, подтверди. Проверь отсутствие в оперативных списках после обновления и наличие в \`Архив\`.
5. Восстанови тестовую сессию. История не потеряна; если grant был отозван, повторно одобри обнаруженный Notifier.
6. Проверь \`Отключить Notifier\` для тестовой сессии. Это не удаляет её из истории. Проверь, что owner-отправка недоступна без повторного одобрения.
7. Если есть ошибки или новый Reader не открывается, прекрати проверку и воспользуйся \`Rollback\`.

Не используйте тест реальной отправки важных пользовательских сообщений: в этой версии меняется только UI/состояние сессий; функциональность Send не переписывалась.
