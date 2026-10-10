# Runbook — rotation of tunnel runtime key

Назначение: заменить runtime key текущего Secure MCP Tunnel без создания нового tunnel и без передачи секрета в ChatGPT.

Проверено на Fortis_M: 2026-10-07.

## 1. Остановить tunnel

Закрыть окно текущего launcher и убедиться, что старый tunnel-client больше не обслуживает этот profile.

## 2. Ручная работа в OpenAI Platform

Выполняет пользователь:
1. revoke/delete старого runtime key;
2. создать новый runtime key с доступом, необходимым текущему tunnel;
3. скопировать новый secret локально.

Новый key **не отправлять в чат**.

Если меняется только key, а `tunnel_id` остаётся прежним, ChatGPT connector обычно не требует перенастройки.

## 3. Безопасно записать новый key локально

Открыть Windows PowerShell вручную и выполнить:

```powershell
$path = "$env:APPDATA\tunnel-client\runtime.key"

$secret = Read-Host "Paste NEW tunnel runtime key" -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)

try {
    $key = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    [System.IO.File]::WriteAllText(
        $path,
        $key,
        [System.Text.UTF8Encoding]::new($false)
    )
}
finally {
    if ($bstr -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
    Remove-Variable key, secret -ErrorAction SilentlyContinue
}

Write-Host "New runtime key saved."
Get-Item $path | Select-Object FullName, Length, LastWriteTime
```

Secret не отображается при вводе и не встраивается прямо в командную строку.

## 4. Проверить ACL и metadata без чтения секрета

```powershell
Get-Item "$env:APPDATA\tunnel-client\runtime.key" |
    Select-Object FullName,Length,LastWriteTime

(Get-Acl "$env:APPDATA\tunnel-client\runtime.key").Access |
    Select-Object IdentityReference,FileSystemRights,AccessControlType,IsInherited
```

Текущая ожидаемая схема на Fortis_M: только `FORTIS_M\alexa`, `FullControl`, не inherited.

## 5. Doctor

```powershell
& 'C:\Tools\tunnel-client\tunnel-client.exe' doctor --profile desktop-commander --explain
```

Ожидание: `RESULT ok`. Для stdio target проверки `mcp_server_reachable` и `oauth_metadata` могут быть `SKIP`.

Не устанавливать optional Codex plugin только из-за рекомендации doctor: он не нужен текущему ChatGPT connector path.

## 6. Запустить tunnel

```powershell
& 'C:\Users\alexa\Documents\prot\Start-Desktop-Commander-Secure-Tunnel.ps1'
```

## 7. Локальная проверка

```powershell
Invoke-WebRequest http://127.0.0.1:8080/ui -UseBasicParsing |
    Select-Object StatusCode

Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 8080 -State Listen |
    Select-Object LocalAddress,LocalPort,State,OwningProcess
```

Ожидание: HTTP `200` и listener на `127.0.0.1:8080`.

## 8. End-to-end проверка

Сделать один безопасный read-only Desktop Commander tool call из ChatGPT.

Если он проходит, rotation подтверждена end-to-end.

## Критерий завершения

`old key revoked -> new key written -> doctor ok -> launcher running -> localhost healthy -> ChatGPT tool call succeeds`.

Никакой secret не должен появиться в документации, Git history или сообщениях чата.