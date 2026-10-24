# Fortis Observatory V1: установка основным Windows-пользователем

**ВНИМАНИЕ к новой версии 19.10.2026:** после изменений offline
очереди `store.py` и `server.py` приведённые ниже шесть
`$expected` SHA256 относятся **к старому проверенному snapshot**.
Они НЕ являются pin текущего source. Не заменять хэши автоматически,
не обходить ошибку сверки и не запускать RW Repo source владельцем.
До owner install нужны отдельные review, snapshot pin, ACL/guest
negative и явное разрешение владельца.


**Подготовлено: 2026-10-18. Не установлено; текущий репозиторий НЕ является доверенным местом исполнения под владельцем.**
Разрешение пользователя на установку получено. Доступные инструменты работают в Linux Repo и ограниченном G2; они **не исполняют команды основного Windows-пользователя**. Это ручная передача точных действий основному пользователю, не задание G2 на обход прав.

## Owner PowerShell: проверить, закрепить шесть файлов, запустить

Открой обычный **PowerShell основного Windows-пользователя** (не «Администратор», не FortisHostG1). Просмотри блок, затем вставь целиком. Он НЕ изменяет ACL, mounts или действующие процессы. Если что-то не совпадает, выполнение остановится. Нельзя запускать Python или установочный скрипт прямо из доступной Repo RW директории.

~~~powershell
$ErrorActionPreference = 'Stop'
$identity = [Security.Principal.WindowsIdentity]::GetCurrent().Name
if ($identity.Split('\')[-1] -ne 'alexa') { throw 'Нужен основной Windows-пользователь' }
$source = Join-Path $env:USERPROFILE 'Repos\tunnel\observatory\v1'
$target = Join-Path $env:LOCALAPPDATA 'FortisObservatoryV1\App'
$history = Join-Path $env:USERPROFILE 'Documents\FortisObservatoryHistory'
$inbox = Join-Path $env:USERPROFILE 'Workfiles\FortisObservatory-v1\inbox\repo'
$expected = [ordered]@{
  'server.py' = 'd263569416af3e8f6902b6106efb1232cc50b13281e955a96d3a7807b72cbc3e'
  'store.py' = '9b18bec12a7912e3d9355009f0401d6728d776d8ef97e3403d80358a5dca3659'
  'emit.py' = '26d8a393a79984d23ae8b3444bf21753a6f90162b88a50c446d8514aa03cded3'
  'index.html' = '81fe084c74ff07e66bc75c187d4667ac0adffaa4d6c674309bb04359d6b75f75'
  'client.js' = 'f756aa76590cd4ac4d4eccedec1de6e698fafd94e18903cd9761a8f0499f1ea0'
  'style.css' = 'a681d2992a28e1f4878a553f3cc431aeb72a57398d052cd816aba97263af33e0'
}
if (!(Test-Path -LiteralPath $source -PathType Container)) { throw 'Не найден каталог исходников V1' }
foreach ($name in $expected.Keys) {
  $file = Join-Path $source $name
  if (!(Test-Path -LiteralPath $file -PathType Leaf)) { throw "Нет файла: $name" }
  if ((Get-Item -LiteralPath $file -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Ссылка запрещена: $name" }
  if ((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected[$name]) { throw "Неизвестный хеш: $name" }
}
$pythonInfo = (& py -3 -c "import sys; print(sys.version_info.major, sys.version_info.minor)" 2>&1 | Out-String).Trim().Split(' ')
if ($LASTEXITCODE -ne 0 -or [int]$pythonInfo[0] -ne 3 -or [int]$pythonInfo[1] -lt 9) { throw 'Требуется Python 3.9+ основного пользователя' }
foreach ($port in @(8093,18753)) {
  $client = New-Object System.Net.Sockets.TcpClient
  try {
    $ar = $client.BeginConnect('127.0.0.1',$port,$null,$null)
    if ($ar.AsyncWaitHandle.WaitOne(500)) {
      try { $client.EndConnect($ar); throw "Порт $port занят; не останавливать службу автоматически" }
      catch [System.Net.Sockets.SocketException] { }
    }
  } finally { $client.Dispose() }
}
function SafeFolder([string]$path) {
  if (!(Test-Path -LiteralPath $path)) { [void](New-Item -ItemType Directory -Path $path -Force) }
  $item = Get-Item -LiteralPath $path -Force
  if (-not $item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw "Недопустимая папка $path" }
}
function CheckPrivateAcl([string]$path) {
  $access = (Get-Acl -LiteralPath $path).Access
  foreach ($rule in $access) {
    if ($rule.AccessControlType -ne 'Allow') { continue }
    try { $sid = $rule.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value }
    catch { throw "Невозможно проверить ACL: $path" }
    if ($sid -in @('S-1-1-0','S-1-5-11','S-1-5-32-545','S-1-5-32-546','S-1-5-4','S-1-5-2') -or $sid -match '^S-1-5-21-.*-1009$') {
      throw "Широкий или гостевой доступ к $path ($sid): ОСТАНОВИТЬ, ACL автоматически не менять"
    }
  }
}
SafeFolder $target
SafeFolder $history
CheckPrivateAcl $target
CheckPrivateAcl $history
SafeFolder $inbox
foreach ($name in $expected.Keys) {
  $from = Join-Path $source $name
  $to = Join-Path $target $name
  if (Test-Path -LiteralPath $to) {
    if ((Get-Item -LiteralPath $to -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Ссылка в установке: $name" }
    if ((Get-FileHash -LiteralPath $to -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected[$name]) { throw "Уже установлен другой файл: $name" }
  } else {
    if ((Get-FileHash -LiteralPath $from -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected[$name]) { throw "Источник изменился: $name" }
    Copy-Item -LiteralPath $from -Destination $to -ErrorAction Stop
  }
  if ((Get-FileHash -LiteralPath $to -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected[$name]) { throw "Ошибка проверки копии: $name" }
}
CheckPrivateAcl $target
Write-Host 'Файлы закреплены, начинается запуск V1.' -ForegroundColor Green
Set-Location -LiteralPath $target
& py -3 .\server.py --archive $history --repo-inbox $inbox --repo-sender-inbox '/workspace/files/FortisObservatory-v1/inbox/repo' --port 18753
~~~

**НЕ отправляй токен приложения из консоли в ChatGPT.** При успешном запуске открой в своём Edge адрес http://127.0.0.1:18753/ и введи токен только в форме страницы. Не запускай второй экземпляр. Для остановки использовать Ctrl+C именно в консоли нового приложения.

## После owner запуска — отдельный этап приёмки

1. Owner: проверь регистрацию тестовой беседы и пустую историю.
2. G2: тесты GET и HEAD /api/state без токена должны получить 401; неизвестный статический маршрут — 404. Гостевому процессу нельзя давать owner токен.
3. Repo: отправить через утверждённый inbox одно синтетическое событие для конкретного reporting_session_id/task_id; owner проверяет Markdown в Documents и его отображение в Edge.
4. Если проверка прав, адресов или защиты не проходит — остановить только новый сервер, не старый HOST/туннели/Docker, и сохранить ошибку без секретов.

**Ограничение:** эти команды не являются автоматической установкой. Без инструментального исполнения основного Windows-пользователя статус остаётся NOT INSTALLED до подтверждения реального запуска и гостевых проверок. Программа хранит короткие события работы, а не полную переписку или реальные вызовы MCP.

## Stage 1C writer — отдельные проверки перед owner install

- Не копировать код из RW Repo прямо в owner execution; выполнить pin/review
  source файлов `store.py`, `server.py`, `client.js`, `index.html`, `style.css`
  и связанного Notifier userscript. Точное множество применяемых файлов
  определяется owner snapshot/diff.
- Проверить owner-private архив, ACL/reparse и HTTP owner-positive/guest-negative
  с отдельными ключами чтения/записи; обычный observer key НЕ должен писать.
- В owner UI **явно** выбрать «Код с правом записи сообщений» для выбранной
  сессии и вручную заменить старую read-only pairing в Notifier. Никогда не
  отправлять этот JSON в ChatGPT и не размещать в GitHub.
- Проверить `started`-free first progress/assistant marker, retry после
  отключения и совпадение SHA-256/read-back; никакие live изменения этим
  исходным описанием не выполняются.
- Writer key до отдельной реализации ротации/отзыва является долгоживущей
  bearer capability для выбранной сессии: учитывать это в acceptance и
  защищать Tampermonkey профиль. Не обещать доказанный owner SID boundary
  на основании лишь loopback, Host или наличия ключа.
