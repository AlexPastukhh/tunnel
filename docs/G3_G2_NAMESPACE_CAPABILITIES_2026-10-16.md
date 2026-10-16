# G3 — права через normal, extended и localhost C$ пути, 16 октября 2026

**5.6 PASS(scope): проверенная матрица тестовых объектов не показала обхода прав.**
[Полные результаты E31](G3_G2_NAMESPACE_CAPABILITIES_2026-10-16.json).
G3 BLOCKED; G4–G6 не приняты. Этот этап не закрывал 5.7. Позднее [E32](G3_G2_PROTECTED_NAMESPACE_CAPABILITIES_2026-10-16.md) принял 5.7 для восьми runtime объектов; private assets/backups7.6 остаются.

Из действующего G2 выполнено 135 open/close проверок: SID1009, Session2, без группы Administrators.
Использован прежний synthetic root `C:\Users\Public\Documents\FortisHostG1Probe`,
каталоги RW/RO/DENY и их `marker.txt`. Три маршрута: normal, `\\?\` и `\\localhost\C$`.
Файлы открывались только с OPEN_EXISTING. Чтения содержимого, записи, создания файлов,
изменения ACL, запуска/остановки runtime и операций с owner GUI не было.

| Объект | Один маршрут: ALLOW / DENY5 | Результат |
|---|---|---|
| RW, каталог и файл | 10 / 5 | Разрешён Modify; изменение ACL/владельца и directory DELETE_CHILD запрещены |
| RO, каталог и файл | 2 / 13 | Разрешены READ/LIST; все проверенные mutation rights запрещены |
| DENY, каталог и файл | 0 / 15 | Все проверенные права запрещены |

Каждый маршрут дал одну и ту же матрицу. В финальном запуске: 135/135 ожидаемых результатов,
каждый полученный дескриптор закрыт. Win32 errors, отличные от ожидаемого ACCESS_DENIED=5,
не считались успешным запретом.

Для файла проверены READ_DATA, WRITE_DATA, APPEND_DATA, WRITE_ATTRIBUTES, DELETE, WRITE_DAC,
WRITE_OWNER; для каталога — соответствующие LIST/CREATE права и дополнительно DELETE_CHILD.
Это проверка выдачи прав дескриптору, без попыток изменить защищённые данные.
Ранее выполненные actual synthetic write/roundtrip и junction проверки E04/E26 переиспользуются.

## Исправление критерия теста

Первый запуск вернул Passed=false: автор теста ошибочно предположил RW FullControl.
Пять прав на каждом маршруте получили DENY5 вместо ожидаемого ALLOW. Других расхождений не было.
Адресное чтение ACL подтвердило guest Allow Modify,Synchronize, mask1245631, для RW directory/file.
Критерий исправлен под этот контракт; финальный pinned script повторно выполнен на Windows.
Raw первого запуска сохранён в JSON. Права Windows не менялись.

Исходник: [Test-G2NamespaceCapabilities.ps1](../runtime/host-g2/runtime-api-migration/Test-G2NamespaceCapabilities.ps1).
SHA256: `8861428FC7D47FAA2E0DD9979F0B6510564A37FF75BBBE56AE57039F6CD4CB1C`, 3581 байт.
Guest копия: `%LOCALAPPDATA%\FortisHostG2\Workspace\g2-namespace-8861428F.ps1`;
CreateNew или проверка существующего файла, SHA read-back перед запуском.
Финальный результат: 2026-10-15T21:49:08.9075307Z. Первоначальный source прошёл Repo AST/C# compile;
финальный source успешно скомпилирован и выполнен Windows PowerShell5.1.

## Что этот результат защищает и чего не доказывает

В проверенных тестовых объектах другой синтаксис пути и localhost C$ не дали прав,
запрещённых через normal path. Это закрывает оставшуюся synthetic capability matrix пункта 5.6.
Изменение содержимого и ACL защищённых объектов не требовалось для такой проверки.

5.7 остаётся PARTIAL: это не проверка всех реальных protected roots, shares, owner private files,
backup locations и не доказательство личности, которой SMB-сервер авторизовал соединение.
Положительные RW controls подтверждают рабочий маршрут, но отдельного SMB identity witness нет.
Не требуется повторять эту матрицу или добиваться успеха Get-SmbConnection ради перечня.
Следующая адресная проверка — только конкретный недоказанный protected target или owner IPC/API.
