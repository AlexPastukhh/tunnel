# G3 — проверка после применения ACL, 2026-10-13

**Runtime ACL: PASS в проверенном scope. G3 в целом: OPEN.**
Пользователь явно согласовал изменение четырёх DACL и выполнил protect-shared-runtime.ps1 -Mode Apply в PowerShell владельца с правами администратора. Применение: 2026-10-13T07:12:59.5574260Z (14:12 Asia/Bangkok).
Backup: C:\Users\alexa\AppData\Local\FortisHostG2AclBackup\runtime-dacl-20261013T071259525Z-d7c956e72739475a93ff507bf7048ee7.json.
Повторный Apply и live Rollback не выполнялись.

## Применённый scope и фактические права

Только SID FortisHostG1 / 1009, mutation mask 0xD0156:
- C:\Tools — сам каталог, без наследования в прочие подкаталоги.
- C:\Tools\tunnel-client, C:\Tools\desktop-commander-runtime, C:\Tools\desktop-commander — с наследованием на содержимое.

Четыре live root DACL совпадают с After сохранённого backup. На реальном G2 токене handles для write/create, append/mkdir, DeleteChild, Delete, WriteDac, WriteOwner дали Win32 5. Read/list и execute/traverse дали 0. Проверены четыре каталога, оба EXE и общий dist\index.js.
Ранее WriteData на запущенные EXE давал sharing violation (32), после ACL — именно Access denied (5).

| Дерево | Объектов AccessCheck | Writable | Без read/execute | Ошибок |
|---|---:|---:|---:|---:|
| tunnel-client | 9 | 0 | 0 | 0 |
| desktop-commander-runtime | 2 | 0 | 0 | 0 |
| desktop-commander | 22 747 | 0 | 0 | 0 |
| Всего | 22 758 | 0 | 0 | 0 |

AccessCheck MAXIMUM_ALLOWED выполнен под настоящим токеном G2, не только по вручную выбранным ACE. Protected DACL и reparse points в этих деревьях отсутствуют. Проверка завершилась exit 0.
Это уже полученные live результаты до сбоя потока сообщений; после восстановления повторно проверены четыре root DACL, полный скан не повторялся.
Тестовая synthetic область сохранила RW write/create ALLOW, RO write DENY, DENY read/write DENY. G2 остаётся SID 1009, non-admin, UI disabled.

## Junction и альтернативные пути

Первый junction-тест INVALID: выражение массива PowerShell без скобок создало три элемента, и RO link указывал на родительский synthetic каталог. Ошибка FileNotFound не была ACL-результатом. Раннее предположение о другом имени marker.txt ошибочно: файл существует.
Перед повтором независимо подтверждены отсутствие первого probe-каталога и неизменность marker size/mtime. Исправленный тест использует именованные объекты и сверяет Target каждой ссылки.

Nonce исправленного теста: probe-g3-junction-1791876964475-nj60am.
- Junction RW: create/write ALLOW, readback совпал.
- Junction RO: read ALLOW, write DENY (0x80070005).
- Junction DENY: read/write DENY (0x80070005).
Все link targets сверены с ожидаемыми synthetic путями. Cleanup без ошибок; link/data/base и собственный probe-файл удалены. Junction удалялся через RemoveDirectory без рекурсивного удаления target. Независимый observer подтвердил отсутствие probe в RW/RO/DENY.

Python own process token: SID 1009, elevated=false.
Через extended path namespace и \\localhost\C$ synthetic RW/RO marker reads ALLOW; DENY marker read PermissionError errno 13. Содержимое маркеров не выводилось.
Первичный JSON classifier пометил errno 13 без winerror как BLOCKED. Evidence содержит raw output и корректную нормализацию этого PermissionError в DENY; повторная файловая операция для переименования результата не нужна.
[Namespace probe source](../runtime/host-g2/g3-namespace-probe.py) сохраняет исправленную классификацию errno 13.

## Открытые границы G3

Localhost: G2 без credentials получил GET /api/log-level HTTP 200 на owner HOST 8080, Repo tunnel 58122 и own G2 65069; OPTIONS вернул 405 и Allow: GET, PUT.
Исходник установленного tunnel-client v0.0.15 ранее показал loopback gate и runtime PUT handler; проверка Windows identity между локальными пользователями отсутствует в изученном guard. SameOriginUnsafe допускает non-browser запросы без Origin/Referer.
Это подтверждённая доступность read endpoint и вывод из исходника о потенциальном write channel; PUT/POST старым туннелям не отправлялись, запуск действий от owner не демонстрировался. MCP UI cards отключены отдельно от localhost admin API.

C$ share ACL содержит Allow Full для Administrators, Backup Operators и INTERACTIVE. Фактические local UNC reads RW/RO доступны G2; запрещённый synthetic файл остаётся недоступным. Административное имя share само по себе не является дополнительным отказом на этом ПК.
Get-SmbConnection под G2 завершился CIM exception; отдельная идентификация network session не подтверждена. Проверялись только localhost и synthetic paths; не LAN/прочие shares и не личные файлы. SMB ACL/сессии не изменялись.

Ранее адресные tasks ACL четырёх заданий и два Docker pipe дали DENY. SERVICE_USER_DEFINED_CONTROL у GoodbyeDPI/MySQL80 ALLOW; коды не отправлялись, handlers остаются OPEN. Запуск/изменение services/tasks не выполнялись.
Owner HOST и native Repo доступны той же ChatGPT сессии: session isolation остаётся OPEN. G4 production migration не принята.

## Финальный срез

На 2026-10-13T07:43:39.0790099Z (14:43 Asia/Bangkok):
HOST PID 5580 / created 02:59:43.4833490Z, Repo PID 23904 / 03:00:34.2137140Z, G2 PID 8452 / 06:43:30.0963580Z — без перезапуска.
Healthz/readyz 8080, 58122 и 65069 — HTTP 200/200.
Original markers: RW 23 bytes, RO 23, DENY 25; все lastWriteUtc совпадают с исходными значениями 2026-10-12.
Результаты сохранены в [structured evidence](G3_POST_ACL_VERIFICATION_2026-10-13.json). Исходный FAIL shared runtime сохранён как история в [pre-ACL evidence](G3_READONLY_EVIDENCE_2026-10-13.md).

Следующее действие: определить и подготовить поддерживаемую защиту localhost administrative API и фактическое разделение маршрутов. Изменение owner профилей/служб/shares и перезапуск старых туннелей не входили в согласованный scope четырёх ACL.
