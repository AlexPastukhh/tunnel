$ErrorActionPreference='Stop'
$client='C:\Tools\tunnel-client\tunnel-client.exe'
$node='C:\Tools\desktop-commander-runtime\node.exe'
& $node (Join-Path $PSScriptRoot 'probe.mjs') --start-if-stopped
if ($LASTEXITCODE -ne 0) { throw 'Repo isolation/configuration verification failed; Tunnel will not start' }
$mcpCommand='command=docker exec -i fortis-repo-test node /workspace/repo/.fortis/mcp-bridge.mjs'
docker exec fortis-repo-test test -r /workspace/repo/.fortis/mcp-bridge.mjs
if ($LASTEXITCODE -ne 0) { throw 'Install the Fortis Repo MCP bridge before starting this Tunnel' }
# The repo-mode profile references the already saved Windows runtime-key file.
& $client doctor --profile repo-mode --mcp.command $mcpCommand --explain
if ($LASTEXITCODE -ne 0) { throw 'Tunnel profile check failed' }
& $client run --profile repo-mode --mcp.command $mcpCommand
if ($LASTEXITCODE -ne 0) { throw 'Repo Tunnel exited with an error' }
