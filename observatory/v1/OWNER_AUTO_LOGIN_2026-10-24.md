# Fortis Observatory V1 — временный вход без ручного кода (24.10.2026)

## Назначение и фактический статус

SOURCE PREPARED / SYNTHETIC CHECKS PASS. Установленный Windows owner Viewer НЕ изменён.
В локальной рабочей копии этот V1-каталог untracked. Ничего не публиковать/не коммитить без разрешения.

Пользователь хочет временно убрать необходимость вводить Viewer code и сохранить
полную возможность возврата авторизации. Реализация НЕ отключает Bearer-проверки
API и не вводит unauthenticated localhost доступ для G2/других Windows-пользователей.

Файлы:
- owner_viewer.py — источник Viewer, по умолчанию --auth-mode owner-launch;
  старый режим --auth-mode manual сохранён.
- test_owner_autologin.py — синтетические проверки ACL/формата launcher,
  источника bearer и сохранения API-проверок.
- Apply-FortisObservatoryOwnerAutoLogin.ps1 — отдельный guarded Preview/Install/Rollback
  только для owner_viewer.py в защищённой папке владельца.

## Как работает owner-launch

1. Уже существующий Windows-пользователь alexa запускает прежний Viewer.
2. В начале процесса генерируется прежний случайный Viewer Bearer.
3. Перед созданием временной HTML-страницы PowerShell проверяет owner-only ACL
   папки установки, отсутствие reparse и allow-ACE только текущего owner SID
   и SYSTEM. Файл внутри папки наследует только эти разрешения;
   ACL созданного файла проверяется повторно.
4. В owner-private файле `viewer-private-launch-*.html` находится временный
   Bearer текущего Viewer (plaintext на диске только на время работы).
   Edge открывается по file:/// пути БЕЗ секрета в URL/аргументах/HTTP.
5. Эта локальная страница открывает реальную `http://127.0.0.1:18755/`
   и передаёт токен через строго origin-bound window.postMessage.
   Viewer проверяет источник открывшего окна и выполняет прежний
   запрос `/api/state` с `Authorization: Bearer ...`.
6. Все существующие owner API сохраняют обязательную Bearer-проверку;
   Notifier и Repo ключи, Docker сервис, HTTP порт, границы G2 не меняются.
7. При остановке Viewer временный файл удаляется штатно; при аварийном
   прекращении процесса возможен остаточный plaintext в защищённом
   owner-only каталоге. Его следует удалять при корректном восстановлении,
   не копируя секреты в Repo/Git/чат.

Ограничения: Edge может заблокировать автоматическое новое окно: тогда
на owner-private странице нужно нажать `Открыть Observatory`, всё равно без ввода
кода. Прямой переход на HTTP Viewer в новом Edge профиле по-прежнему
показывает старую форму входа; открыть для него приватную страницу
запуска из owner-консоли (`OWNER_PRIVATE_LAUNCHER=...`).
Файловый bootstrap требует отдельно доверенного владельца Windows;
не защищает от вредоносного кода с доступом *под тем же SID*.

## Статус тестов

Repo Python: 69 HTTP unit tests PASS; отдельные 4 теста
test_owner_autologin.py PASS. Node UI synthetic PASS (5 сценариев).
Python AST/py_compile и JS syntax PASS. Реальные Windows PowerShell ACL,
Edge file:// postMessage, G2-negative и инсталляция пока НЕ ПРОВЕДЕНЫ.

## Установка без затрагивания Docker, Repo/G2 Tunnel, archive

Под Windows alexa, а НЕ G2:

1. В установленном Windows Viewer закрой ТОЛЬКО Viewer (Ctrl+C в
   его owner-консоли); НЕ останавливай Docker, Repo Tunnel, G2.
   Restart Viewer сбрасывает краткоживущие dispatch-пары, поэтому
   Notifier может потребовать заново связать сессию.
2. Сначала просмотри
   `C:\Users\alexa\Repos\tunnel\observatory\v1\Apply-FortisObservatoryOwnerAutoLogin.ps1`
   и запусти `-Action Preview`. Он сверяет SHA candidate, SID и ACL,
   ничего не меняет.
3. Только при Preview PASS `-Action Install` создаёт резервную копию
   старого установленного `owner_viewer.py` внутри защищённой папки
   и заменяет только этот файл, сверяя SHA.
4. Запусти прежний ярлык/Start-FortisObservatory.cmd. В нём может
   остаться историческая строка «код появится», но при auto режиме
   реальный Python выводит `OWNER_PRIVATE_AUTO_LOGIN=prepared`,
   не выводит API/Bearer секрет. После первого старта нужно вручную
   подтвердить owner-positive в Edge и guest-negative в G2.
5. Если автоматическая авторизация заблокирована или неудобна,
   используй кнопку на локальной приватной странице; при
   проблемах верни `--auth-mode manual` (ниже).

### Штатный возврат к ручному вводу без отката файлов

Останови ТОЛЬКО Viewer, затем в PowerShell alexa:
```powershell
& py -3 "$env:LOCALAPPDATA\FortisObservatoryV1\Viewer\owner_viewer.py" --auth-mode manual
```
При этом owner API и ключи не меняются; код снова выводится в owner-консоли.
Для постоянного возврата используй `-Action Rollback -BackupFile '<путь из BACKUP>'`
на скрипте применения; только после остановки Viewer.

Не менять старый owner HOST, G2, Docker mounts, ACL, Windows services,
Repo credentials и Git в ходе этой задачи. Не публиковать launcher file или
его содержимое. Legacy `OWNER_INSTALL.md` содержит устаревшие hashes
и не является инструкцией для этой локальной правки.

## 24.10.2026 — Edge file:// → HTTP 403 denied, адресный hotfix

После owner-install первого auto-login source SHA
`c3c71e8e04f863f8addc7fa424378d3103ecaa72128e456acaff50669450e7ab`
пользователь подтвердил, что Edge блокирует автоматическое окно; при
нажатии кнопки «Открыть Observatory» новый HTTP Viewer показывал
`{"ok":false,"error":"denied"}`.

Причина в прежней проверке `owner_viewer.py`: `GET /` запрещал
`Sec-Fetch-Site: cross-site`, в том числе законный **top-level navigation**
из owner-private `file://` bootstrap. Исправление допускает только
`GET /` без query для навигации с `Sec-Fetch-Mode: navigate`,
`Sec-Fetch-Dest: document`, правильным Host, `Origin` без значения или `null`.
В теле HTML **нет токена**. Запросы `/api/*` продолжают отклонять
cross-site и требуют прежний Bearer; POST owner endpoints не менялись.

Актуальный кандидат SHA-256 `owner_viewer.py`:
`a3eb75f113a6152adbb3381d6a9b6cd845dec4e927c7b20c80885968e635b48d`
Проверенный SHA в `Apply-FortisObservatoryOwnerAutoLogin.ps1` синхронизирован.

Для owner установки: остановить только Windows Viewer (порт 18755);
запустить `-Action Preview`, затем `-Action Install`; сохранить путь
`BACKUP=...` из результата, запустить только Viewer в owner-launch.
Остальные Repo, G2, Docker, архив, ACL и Notifier не менять.
Реальное принятие hotfix в Edge ещё не подтверждено пользователем;
проверки синтетические и не заменяют реальную проверку.
