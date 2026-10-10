param([Parameter(Mandatory=$true)][string]$TunnelId)
$ErrorActionPreference='Stop'
if ($TunnelId -notmatch '^tunnel_[A-Za-z0-9_-]+$') { throw 'Provide the exact newly registered Tunnel ID' }
if ($TunnelId -eq 'tunnel_6ac4a7249a4081918eb0881c870acf07') { throw 'Do not reuse the HOST Tunnel' }
$client='C:\Tools\tunnel-client\tunnel-client.exe'
$node='C:\Tools\desktop-commander-runtime\node.exe'
$container=docker inspect fortis-repo-test | ConvertFrom-Json
if ($LASTEXITCODE -ne 0 -or !$container[0].State.Running) { throw 'Start and inspect the Repo test container first' }
& $node (Join-Path $PSScriptRoot 'probe.mjs')
if ($LASTEXITCODE -ne 0) { throw 'Container verification failed' }
& $client init --sample sample_mcp_stdio_local --profile repo-mode --tunnel-id $TunnelId --control-plane-api-key-ref 'env:FORTIS_REPO_TUNNEL_KEY' --health-listen-addr '127.0.0.1:0' --mcp-command 'docker exec -i fortis-repo-test node /workspace/repo/.fortis/mcp-bridge.mjs'
if ($LASTEXITCODE -ne 0) { throw 'Profile creation failed; do not overwrite an existing profile' }
Write-Output 'Created independent repo-mode profile. Run run-tunnel.ps1 locally; do not send its runtime key to chat.'
