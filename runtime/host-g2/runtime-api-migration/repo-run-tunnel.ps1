$ErrorActionPreference='Stop'
$client='C:\Tools\tunnel-client\tunnel-client.exe'
$runtime='C:\Tools\tunnel-client\runtime\v0.0.15\tunnel-client-runtime.exe'
if((Get-FileHash -LiteralPath $runtime -Algorithm SHA256).Hash -ne 'A922D372D6BE0649156FBC1C8A040597F1F4BB5B4356890151D7875602593B1A'){throw 'Runtime SHA256 changed'}
$node='C:\Tools\desktop-commander-runtime\node.exe'
& $node (Join-Path $PSScriptRoot 'probe.mjs') --start-if-stopped
if ($LASTEXITCODE -ne 0) { throw 'Repo isolation/configuration verification failed; Tunnel will not start' }
$mcpCommand='command=docker exec -i fortis-repo-test node /workspace/repo/.fortis/mcp-bridge.mjs'
docker exec fortis-repo-test test -r /workspace/repo/.fortis/mcp-bridge.mjs
if ($LASTEXITCODE -ne 0) { throw 'Install the Fortis Repo MCP bridge before starting this Tunnel' }
# The repo-mode profile references the already saved Windows runtime-key file.
& $client doctor --profile repo-mode --mcp.command $mcpCommand --explain
if ($LASTEXITCODE -ne 0) { throw 'Tunnel profile check failed' }
& $runtime run --profile repo-mode --mcp.command $mcpCommand '--harpoon.additional-transport='
if ($LASTEXITCODE -ne 0) { throw 'Repo Tunnel exited with an error' }
