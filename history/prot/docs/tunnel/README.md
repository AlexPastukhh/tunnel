# Secure MCP Tunnel — Fortis_M

Статус: рабочий.
Последняя проверка: 2026-10-07.

## Назначение

Текущий tunnel даёт ChatGPT доступ к нативному Desktop Commander на Fortis_M без публичного inbound endpoint.

Рабочий path:

```text
ChatGPT
  -> custom MCP connector
  -> OpenAI Secure MCP Tunnel
  -> tunnel-client on Fortis_M
  -> stdio
  -> desktop-commander-trusted.cmd
  -> Desktop Commander
```

## Текущая конфигурация

- Tunnel ID: `tunnel_6ac4a7249a4081918eb0881c870acf07`
- tunnel-client: `C:\Tools\tunnel-client\tunnel-client.exe`
- version на момент проверки: `0.0.15+a390c168ff1b2d14e73a95991c186c6aba3ff5a0`
- profile: `desktop-commander`
- profile file: `%APPDATA%\tunnel-client\desktop-commander.yaml`
- runtime key file: `%APPDATA%\tunnel-client\runtime.key`
- launcher: `C:\Users\alexa\Documents\prot\Start-Desktop-Commander-Secure-Tunnel.ps1`
- MCP target: `cmd.exe /c C:/Tools/desktop-commander/desktop-commander-trusted.cmd`
- local admin/health listener: `127.0.0.1:8080`
- admin UI: `http://127.0.0.1:8080/ui`
- automatic browser opening: disabled

Runtime key value никогда не хранить в документации, логах или Git.

## Обычный запуск

Сначала при необходимости проверить профиль:

```powershell
& 'C:\Tools\tunnel-client\tunnel-client.exe' doctor --profile desktop-commander --explain
```

Затем запустить launcher:

```powershell
& 'C:\Users\alexa\Documents\prot\Start-Desktop-Commander-Secure-Tunnel.ps1'
```

Launcher намеренно остаётся видимым. Закрытие его окна — штатный способ остановить этот tunnel.

## Проверка состояния

```powershell
Invoke-WebRequest http://127.0.0.1:8080/ui -UseBasicParsing |
    Select-Object StatusCode

Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 8080 -State Listen |
    Select-Object LocalAddress,LocalPort,State,OwningProcess
```

Для полной проверки нужен ещё end-to-end tool call из ChatGPT через connector.

`doctor` проверяет конфигурацию, но сам по себе не заменяет end-to-end проверку рабочего control-plane path.

## Connector

При простой ротации runtime key и неизменном `tunnel_id` connector менять не нужно.

Если создаётся новый tunnel с новым ID, connector/plugin configuration нужно проверить и при необходимости привязать к новому tunnel.

Опциональный Codex plugin, который `doctor` может предлагать установить, не требуется для текущей схемы ChatGPT -> tunnel -> Desktop Commander.

## Security notes

- runtime key остаётся на HOST и не должен попадать в repo, Sandbox или контейнер;
- текущий нативный Desktop Commander — это Maintenance/full-host capability, а не sandbox;
- launcher не запускается автоматически;
- не расширять Kaspersky exclusions без отдельного анализа;
- не публиковать local health/admin listener наружу;
- не считать `allowedDirectories` полноценной security boundary.

## Runbooks

- [Runtime key rotation](RUNBOOK-RUNTIME-KEY-ROTATION.md)

## Связанные документы

- [../../SECURE-ACCESS-CONTROL-PLAN.md](../../SECURE-ACCESS-CONTROL-PLAN.md)
- [../observability/README.md](../observability/README.md)
- [../isolation/README.md](../isolation/README.md)
## Intermittent chat/session timeouts

Наблюдается отдельный класс проблем: один ChatGPT chat/session может получить ~25s timeout или `MCP server is not initialized`, пока локальный tunnel остаётся live/ready и другой chat/session продолжает работать.

Это не следует автоматически трактовать как глобальное падение tunnel-client.
First-line recovery: один лёгкий read-only retry, затем reconnect конкретного app/chat binding при green local health.
Global restart использовать при устойчивом local unhealthy/dead evidence или если несколько paths одновременно не восстанавливаются.

Подробности и controlled experiments: [../observability/TROUBLESHOOTING-TUNNEL-CHAT-TIMEOUTS.md](../observability/TROUBLESHOOTING-TUNNEL-CHAT-TIMEOUTS.md).
