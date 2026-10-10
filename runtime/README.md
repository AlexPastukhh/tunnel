# Датированные копии исходников

Копии действующих source files на 2026-10-10, не новый автоматический installer.

Live Repo: C:\Users\alexa\chatgpt-repo-mode; установленный MCP bridge: /workspace/repo/.fortis/mcp-bridge.mjs.
Live HOST: C:\Users\alexa\Documents\prot\Start-Desktop-Commander-Secure-Tunnel.ps1 и C:\Tools\desktop-commander\desktop-commander-trusted.cmd.

workspace-config.example.json фиксирует существующую machine identity; для другой машины/нового контейнера нельзя переиспользовать ID без inspect и проверки. Dockerfile задаёт базовый image; mounts/network/limits задаются при container create, не самим Dockerfile. Проверенный набор ограничений см. CURRENT_STATE.md и probe.mjs.

configure-tunnel.ps1 — исторически действующий initializer с env reference; текущий repo-mode profile уже использует saved file. Не запускать init поверх существующего профиля. См. INSTRUCTIONS.md.

После изменения runtime source обязательно синхронизировать нужный live path / volume, проверить, перезапустить только затронутый контур и обновить docs. Credential files не входят в эту папку.
