# Project Checker — ручная Windows-приёмка личной V1

Это кандидат для проверки владельцем. Windows в Docker не запускалась.
Linux tests, хеш ZIP и отредактированный JSON не являются Windows PASS.
Установка, ACL, реальные chooser/GUI и проверка маршрутов — ручные действия
владельца. Агент подготовил код, пакет и проверочные команды.

## Состав и ограничения

Пакет offline: Python с Tcl/Tk, Node, ESLint, Semgrep CE, полный закреплённый
Windows wheel closure, npm tarballs/lock, приложение и проверочные скрипты.
Точные версии/хеши — release.json, dependency-inventory.json,
downloads.lock.json, requirements-windows.lock и npm-package-lock.json.
Ни pip, ни npm не скачивают зависимости при установке. Npm выполняет
offline ci --ignore-scripts с проверкой integrities; готовому изменяемому
Docker node_modules доверять не требуется.

Первый профиль поддерживает JS/CJS/MJS и Python. Dependency анализируется как
code; resource имеет явный suffix-профиль и не выдаётся за проверенный код;
data и явные исключения сохраняются, не копируются/удаляются. Неизвестный код
блокирует обновление. Нет скрытых исключений .git/cache/deps и автоматической
сборки/миграции/установки зависимостей проекта под owner.

Стартовый пакет запрещает dynamic eval; это не исчерпывающая политика
безопасности каждого проекта. Владелец выбирает/расширяет общие правила для
реального применения. Успешный static scan не доказывает абсолютную безопасность.

Явные лимиты inventory: 10 000 entries, 50 MiB/file, 250 MiB total; превышение
даёт отказ, не skip. Списки файлов CLI разбиваются ниже Windows UTF-16 argv limit,
с полным объединением coverage/findings. Пропавшие выбранные файлы/папки видны
как кандидаты удаления только прежних managed paths. Недоступный source root
и ошибки доступа остаются ошибками.

## 1. Скопировать и проверить пакет

Сначала скопировать ZIP **за пределы всех agent write routes**, затем сверить
SHA-256 с отдельным receipt и распаковать в новую owner review folder там же.
Просмотреть diff/состав и bundle-manifest.json. Не запускать доверенную
установку из рабочей Repo-копии. Каталог review также должен быть недоступен ИИ
на запись во время проверки/установки.

Выбрать новые отдельные InstallRoot и DataRoot вне agent routes.
Для первой приёмки — новый пустой ApprovedRoot с безопасными fixtures.
Действующие пользовательские копии/Loader здесь не нужны.
Installer откажется перезаписывать существующий install/data directory и
не станет менять ACL уже существующих approved roots.

В обычном owner PowerShell сохранить SID и значения, заменив SourceRoot на
**фактический Windows-путь** источников. Не переводить Linux path догадкой:

```powershell
$OwnerSid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$InstallRoot = Join-Path $env:ProgramFiles 'ProjectChecker\V1-20261025'
$DataRoot = Join-Path $env:LOCALAPPDATA 'ProjectChecker\V1-20261025'
$ApprovedRoot = Join-Path $env:LOCALAPPDATA 'ProjectChecker\Approved-Fixture-V1'
$SourceRoot = 'D:\SET-THE-ACTUAL-WINDOWS-SOURCE-ROOT'
```

Передать эти значения в **elevated owner PowerShell**, открытый в проверенном
review folder. При UAC под другой учётной записью сохранить SID обычного
владельца, а не подставлять SID администратора:

```powershell
.\Install-Checker.ps1 -InstallRoot $InstallRoot -DataRoot $DataRoot -SourceRoot @($SourceRoot) -ApprovedRoot @($ApprovedRoot) -OwnerSid $OwnerSid
```

Скрипт проверяет bundle hashes и Authenticode Python installer, устанавливает
offline, фиксирует Python ._pth без site/.pth/usercustomize, защищает app для
SYSTEM/Administrators с owner read/execute; data получает owner write.
Receipt ещё отсутствует, обычная кнопка обновления остаётся заблокирована.

Эти команды не следует выполнять из ChatGPT или ради них расширять host-доступ
агента. Если unsigned script заблокирован политикой PowerShell, сначала
проверить его и правила этой машины; скрытого ExecutionPolicy bypass здесь нет.

## 2. Запустить безопасные native и GUI probes

В **обычном owner PowerShell**, не elevated:

```powershell
& "$InstallRoot\python\python.exe" -I -S -B -X utf8 "$InstallRoot\qa\native_acceptance.py" --profile "$InstallRoot\installation.json" --report "$DataRoot\native-qa.json"
& "$InstallRoot\python\python.exe" -I -S -B -X utf8 "$InstallRoot\qa\gui_acceptance.py" --profile "$InstallRoot\installation.json" --report "$DataRoot\gui-qa.json"
```

Пробы создают только новую private temporary folder. Проверяют native handles,
junction/hardlink/ADS refusal, sharing, security/timestamps/attributes, настоящие
clean/violation CLI scans, startup/config canaries, пустые dirs, checked-byte
transaction, прерывание/recovery и Job Object cleanup.

GUI fixture ограничивает запись этой временной папкой, фиксирует реальные
Check/cancel/policy-save/review/apply/rollback события и просит владельца
проверить нативные chooser, Unicode, размеры/diff и понятность результатов.
Он не разрешает обновление настоящих пользовательских roots.

FAIL/INCOMPLETE не редактировать в PASS и не обходить пропущенные возможности.
Сохранить отчёт и вернуть ошибку разработчику. Нужна исправленная программа,
а не ручное дописывание backend владельцем.

## 3. Проверить фактические agent write routes

Перечислить **все** действующие Docker bind mounts/aliases, native bridge
allowlists/identities и внешние import/copy/update API. Проверять текущую
конфигурацию, не старое описание. routes.example.json — схема, не доказательство.

Для каждой route и каждого защищённого app/data/state/policy/approved root
создать owner marker с случайным не секретным ASCII challenge. Записать без
BOM/перевода строки, например:

```powershell
$Challenge = [Guid]::NewGuid().ToString('N') + [Guid]::NewGuid().ToString('N')
$Marker = Join-Path $InstallRoot '.checker-boundary-marker'
[IO.File]::WriteAllText($Marker,$Challenge,[Text.Encoding]::ASCII)
```

Повторить для остальных roots с новыми challenges; app marker требует elevated
owner. Через **ту же самую проверяемую agent route** попробовать заменить только
этот marker. Сохранить точный DENIED outcome и SHA-256 локального transcript,
убедиться, что challenge не изменился. Секреты, действующие scripts, Loader,
credentials и пользовательские документы не использовать для проб.

Сформировать $DataRoot\routes.json по наблюдённым фактам. Должна быть
negative-probe matrix для всех routes и roots. Сохранять accepted markers
неизменными на срок действия приёмки: удаление/изменение инвалидирует context.

Программа проверяет declared overlap, ACL и markers. Полнота внешних routes —
attestation владельца: скрытый сервис программа обнаружить не может.
Owner SID == agent SID с широким native write API не изолируется ACL той же
identity. Сначала реально ограничить маршрут/identity; не выдумывать DENIED.
Declared writable Windows system-dependency paths также отклоняются.
Изменение реальных routes после приёмки требует новой проверки.

## 4. Зафиксировать проверенную установку

Просмотреть native/GUI отчёты, фактические routes и marker outcomes. Только после
этого в **elevated owner PowerShell**:

```powershell
& "$InstallRoot\Accept-Checker.ps1" -NativeReport "$DataRoot\native-qa.json" -RouteInventory "$DataRoot\routes.json" -GuiReport "$DataRoot\gui-qa.json"
```

Issuer связывает полный установленный manifest, profile, native/GUI/route
receipts, approved roots и owner SID. Development profile этого не создаёт.
Обычный запуск — без elevation:

```powershell
& "$InstallRoot\Start-Checker.cmd"
```

Сначала повторить на безопасном независимом файле и folder/mixed:
Check → полный preview → cancel → новый preview → confirm/apply →
history → inverse preview → rollback. Проверить hashes, binary sizes,
managed deletes, сохранение чужих данных, empty dirs, restart/pending recovery.
До этого installed walkthrough статус WINDOWS_ACCEPTANCE_PENDING,
не OWNER_ACCEPTED. Настоящие consumers/Loader — позднее, отдельно.

## Восстановление и границы

Native профиль: fixed local NTFS, plain single-link files без reparse/ADS,
поддерживаемые metadata и восстанавливаемый owner. Lock, stale inputs,
неподдержанный состав и неожиданный tree drift дают явный отказ.

Один target root на регистрацию, много mappings и source roots. Независимые
destinations используют отдельные registrations/consents/journals.
Global atomicity через files/roots/volumes не обещается.

Existing file пишется через held handle с сохранением DACL/identity и проверкой
metadata/readback. Это journaled write, не atomic replace. Crash посреди write
может оставить partial bytes: default recovery их не затирает. Отдельный
conflict preview показывает current→backup hashes/sizes/diff; после явного
consent текущие конфликтные bytes сначала сохраняются отдельным backup.

Rollback удаляет только созданный той же операцией пустой каталог с совпадающей
identity. Старые/существующие dirs, включая устаревшие пустые, явно сохраняются.
Не удалять state/journals/backups до завершения необходимого восстановления.
Откат установки — ROLLBACK_INSTALL.md; автоматического изменения Loader,
старой версии или настоящих external copies в этой процедуре нет.
