# E40 — защита выбранных файлов и backup владельца, 16 октября 2026

**PASS(scope) для выбранных объектов. Подпункт7.6 в целом PARTIAL.**
[JSON](G3_SELECTED_OWNER_ASSETS_2026-10-16.json) · [План](G3_NEXT_ACTIONS_AND_PROTECTION_PLAN_2026-10-15.md).

## Польза и переиспользованное evidence

E05 уже подтвердил отказ открытия owner home/Repos/Workfiles/AppData/Documents/Desktop/Downloads,
.ssh/.aws и tunnel-client key directory. Эти корни повторно не проверялись.
E26/E32 закрыли selected shared runtime ACL/alternate paths; их матрицы не повторялись.

Остаток — прямые обращения к конкретным вложенным файлам и backup parents.
Корневой directory DENY сам по себе не доказывает отказ открытия каждого известного вложенного пути.
Для backup одного отказа DELETE на файле недостаточно: отдельно проверено право DELETE_CHILD
непосредственного родительского каталога. Никаких настоящих удалений для этого не требуется.

## Выбранные объекты

| Метка | Объект / основание |
|---|---|
| RepoNamedProfile | Текущий owner repo-mode.yaml |
| RepoRuntimeKeyFile | Реальный runtime.key, на который ссылается этот профиль |
| RepoRun / RepoControl | Два применённых owner launcher/control файла E38 |
| RepoRecoveryBackup | Конкретный backup.json, созданный E38 |
| RuntimeDaclBackup | Конкретный runtime-dacl backup, созданный при применении E03 |
| OwnerEdgeLocalState | Local State основного Edge в owner AppData |
| RepoRecoveryParent / RuntimeDaclBackupParent | Два непосредственных каталога backup |

Точные пути перечислены в pinned source; значения секретов в нём отсутствуют.
Owner read-only Get-Item подтвердил шесть существующих обычных файлов, без reparse flag.
Ссылка на runtime.key получена локальным разбором уже известного профиля после проверки его
SHA EEB6000A…; ключ не открывался/не читался/не хешировался. Файл ключа существует, symlink flag=false.
Owner key/browser/backup содержимое в отчёт не экспортировалось.

Стандартный .aws\credentials отсутствует. Это ABSENT, не DENY; его probe не выполнялся.
Поиск других credential names или чтение private directory listing не проводились.

## Actual Windows G2 результат

16 октября07:45:23 Asia/Bangkok, SID1009/Session2/non-admin.
Source доставлен в собственный Workspace G2, pinned bytes/readback и Windows PowerShell AST проверены.
C# P/Invoke скомпилирован штатным Add-Type. OPEN_EXISTING + share read/write/delete,
без чтения или записи через полученный дескриптор; каждый успешный handle сразу закрывается.

Проверены normal paths и localhost C$:

- Семь файлов: READ, WRITE, APPEND, WRITE_ATTRIBUTES, DELETE, WRITE_DAC, WRITE_OWNER.
- Два backup parents: те же права плюс DELETE_CHILD.
- Все130 protected requests: Win32=5, эффективный отказ доступа.
- Все15 own synthetic file/directory positive requests: разрешены.
- Own temporary file/directory удалены; cleanup=true.

Профили, ключи, browser state, backup и их ACL не менялись.
Owner data bytes не читались самим capability probe. Owner metadata step отдельно разобрал
known-reference профиль, поэтому не утверждать, что вообще ни один owner файл не читался
локальными средствами при подготовке. Сам секрет, browser и backup bytes не читались.
Не было directory enumeration владельца, privilege enable, delete/write attempts с фактическим
изменением данных, runtime/container restart или новых grants.

## Код и доставка

runtime/host-g2/runtime-api-migration/Test-G2SelectedOwnerAssets.ps1:
6144 bytes, SHA256 805EF36816DA4824E729F6BADC0D5BF75C38A5A0029E9FD56D1AD797D6B5B970.
Guest copy:
C:\Users\FortisHostG1\AppData\Local\FortisHostG2\Workspace\e40-owner-assets\Test-G2SelectedOwnerAssets.ps1.
Копия исходника оставлена для воспроизведения; synthetic positive fixture удалён.
Это один малый logical transfer6144 bytes; protected data не передавались.

В нынешнем Repo container команда pwsh не найдена; Linux AST PASS не заявляется.
Windows AST, C# compile и фактические positive/negative controls успешно выполнены.
Контейнерные инструменты не переустанавливались ради дублирующей проверки.
Commit/push не выполнялись.

## Что принято и что осталось

Для выбранных семи файлов и двух backup parents свежий эффективный доступ G2 закрыт.
Изменение ACL этих объектов не требуется по полученным результатам.
Это scoped file-access evidence, не доказательство конкретного NTFS/SMB механизма каждого отказа:
SMB authenticated identity отдельно не устанавливалась.

7.6 остаётся PARTIAL: прочие личные документы/фото/финансовые данные/recovery assets и backup locations
не выбраны поимённо; нет полного backup restoration/media/versioning/offline resilience теста.
Не выполнять произвольный поиск приватных файлов ради увеличения покрытия.
Дополнительные assets проверять после определения конкретной ценности/пути и ещё не закрытого риска.

Отдельно остаются applicable owner IPC/bridges и final G2 takeover по плану.
G2 DENY не ограничивает независимые owner Repo RW mounts/широкие tools этого чата (1.4).
baseline-policy.json в Repo — документированный source/design, не обязательный enforcement engine;
его сохранение в доступном Repo не означает защищённую active policy.
G3 BLOCKED; G4–G6 не приняты.
