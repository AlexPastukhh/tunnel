# G3 — выбранный runtime через extended и localhost C$ пути, 16 октября 2026

**5.7 PASS(scope): для восьми выбранных runtime объектов обход прав не обнаружен.**
[Полные результаты E32](G3_G2_PROTECTED_NAMESPACE_CAPABILITIES_2026-10-16.json).
G3 BLOCKED; G4–G6 не приняты. Личные активы и backups 7.6 этой проверкой не приняты.

Из actual G2 SID1009/Session2 без группы Administrators выполнено 128 open/close проверок.
Использован OPEN_EXISTING; содержимое не читалось и не записывалось, каталоги не перечислялись,
ACL и установленные файлы не менялись. Туннели и процессы не перезапускались.

## Выбранные объекты

- Каталоги: `C:\Tools`, `C:\Tools\tunnel-client`, `C:\Tools\desktop-commander-runtime`, `C:\Tools\desktop-commander`.
- Файлы: `C:\Tools\tunnel-client\tunnel-client.exe`,
  `C:\Tools\tunnel-client\runtime\v0.0.15\tunnel-client-runtime.exe`,
  `C:\Tools\desktop-commander-runtime\node.exe`,
  `C:\Tools\desktop-commander\node_modules\@wonderwhy-er\desktop-commander\dist\index.js`.

Это те же восемь объектов, что в E26. Normal mutation matrix E26 не повторялась;
E31 предоставляет synthetic RW/RO/DENY controls для трёх namespace.

| Маршрут | READ/LIST ALLOW | Mutation rights DENY5 |
|---|---:|---:|
| Обычный путь: контроль существования/доступности | 8 | Переиспользуются E26 |
| Extended `\\?\` | 8 | 52 |
| Localhost `\\localhost\C$` | 8 | 52 |

У каждого файла проверены WRITE_DATA, APPEND_DATA, WRITE_ATTRIBUTES, DELETE, WRITE_DAC и WRITE_OWNER;
у каталога дополнительно DELETE_CHILD, а первые два права означают CREATE_FILE/CREATE_DIRECTORY.
Все 24 полученных read/list дескриптора закрыты. Все 104 mutation opens получили Win32=5.
Missing path, сетевой сбой или другой код ошибки не считались успешным запретом.

## Что это доказывает

В проверенных объектах alternate namespace не дали изменить файлы, создать объекты в каталогах,
удалить выбранные объекты/children или получить права изменения ACL/владельца.
Право проверялось запросом дескриптора, без реальных защищённых writes/deletes/ACL changes.
Проверка снижает риск подмены установленного runtime через другой синтаксис пути или C$.

Каталог `C:\Tools` проверен сам по себе. Вывод не относится рекурсивно ко всем его descendants.
Все личные файлы, прочие shares, backups, child ACL и owner IPC/API этой проверкой не покрыты.
Это не blanket запрет SMB и не доказательство SMB authenticated identity.
Положительные read controls и E31 RW controls подтверждают рабочие маршруты;
отдельный Get-SmbConnection не нужен для вывода об этих effective rights.

## Исходник, доставка и приёмка

[Test-G2ProtectedNamespaceCapabilities.ps1](../runtime/host-g2/runtime-api-migration/Test-G2ProtectedNamespaceCapabilities.ps1),
4139 байт, SHA256 `40876E94EFC9B0CB256D11FFFF19C61A734BE38AEF3004618F64849D0FEBB8E9`.
Repo: AST и native C# helper compilation PASS. Windows: pinned guest source создан через CreateNew
либо сверку существующего файла, SHA read-back перед исполнением; actual test 128/128 PASS.
Копия: `%LOCALAPPDATA%\FortisHostG2\Workspace\g2-protected-namespace-40876E94.ps1`.
Результат UTC: 2026-10-15T21:54:35.2586477Z (16 октября 04:54 Asia/Bangkok).

5.7 принят только для явно перечисленного scope E31/E32. Не требуется полный Windows/SMB scan
или повтор этих tests без drift. Оставшиеся owner data routes/backups относятся к 7.6;
relevant owner IPC/API — к 5.8 и 4.8. Это следующие конкретные gaps, а не новые проверки ради перечня.
