param([ValidateSet('Preview','Stage')][string]$Mode='Preview')
# WF-060 SOURCE ONLY. Owner-operated, side-by-side Repo2 quiet canary builder.
# Preview: verify pinned installed bytes, AST and compatibility; no writes.
# Stage: additionally CREATE a NEW side-by-side launcher in the SAME installed folder.
# Neither mode invokes Repo2 Setup/Start, edits profiles, stops processes, or touches Docker state.
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Windows PowerShell required.' }
$who = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($who)
if ($who.Name -ine 'FORTIS_M\alexa' -or
    $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Use normal, non-admin FORTIS_M\alexa.'
}
$repo2 = Join-Path $env:LOCALAPPDATA 'FortisRepoPlus2\FortisRepo2.ps1'
$repo2Dir = Split-Path -Parent $repo2
$guard = Join-Path $repo2Dir 'Repo2DirectGuard.ps1'
$repo1Quiet = 'C:\Users\alexa\chatgpt-repo-mode\run-tunnel-quiet-logs.ps1'
$target = Join-Path $repo2Dir 'FortisRepo2-quiet-logs.ps1'
$container = 'fortis-repo-test'
$expectedContainerId = 'c6d7be9fe6eb4138a9dc47db3f82c32c377007c2d461c1f03ad37fe9bb3d074a'
$direct = '/opt/dc/node_modules/@wonderwhy-er/desktop-commander/dist/index.js'

function Assert-PinnedFile([string]$Path, [string]$Expected) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw 'Pinned source file missing.' }
    if ((Get-Item -LiteralPath $Path).Attributes -band [IO.FileAttributes]::ReparsePoint) {
        throw 'Unexpected reparse point in pinned file.'
    }
    if ((Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash -ine $Expected) {
        throw 'Pinned source file hash differs; no changes made.'
    }
}
Assert-PinnedFile $repo2 '13C1956DA1E7B7405F50B495A40225D51E42E568965A68AAFFBE404616093CDB'
Assert-PinnedFile $guard '88D5BE54F5E651BBD658BD9F84751511F9D178061EFACF4AA0F2507827CC8533'
Assert-PinnedFile $repo1Quiet 'ADC6B15DE27F845EB0FD451E63E699D711E6A18E3BD4B16D5D32943A4B4C3D4C'
foreach ($folder in @($repo2Dir, (Split-Path -Parent $repo1Quiet))) {
    if ((Get-Item -LiteralPath $folder).Attributes -band [IO.FileAttributes]::ReparsePoint) {
        throw 'Unexpected installed folder reparse point.'
    }
}
$utf8 = [System.Text.UTF8Encoding]::new($false, $true)
function Read-ExactUtf8([string]$Path) {
    $bytes = [IO.File]::ReadAllBytes($Path)
    $body = $utf8.GetString($bytes)
    $roundTrip = $utf8.GetBytes($body)
    if ([Convert]::ToBase64String($bytes) -cne [Convert]::ToBase64String($roundTrip)) {
        throw 'File encoding is not byte-preserving UTF-8.'
    }
    return $body
}
function Parse-PowerShell([string]$Body) {
    $t = $null
    $e = $null
    $ast = [System.Management.Automation.Language.Parser]::ParseInput($Body, [ref]$t, [ref]$e)
    if (@($e).Count -ne 0) { throw 'PowerShell source syntax changed or is invalid.' }
    return $ast
}
function Find-Assignment([object]$Ast, [string]$Name) {
    $a = @($Ast.FindAll({
        param($n)
        if ($n -isnot [System.Management.Automation.Language.AssignmentStatementAst]) { return $false }
        $vars = @($n.Left.FindAll({
            param($v)
            $v -is [System.Management.Automation.Language.VariableExpressionAst]
        }, $true))
        return ($vars.Count -eq 1 -and $vars[0].VariablePath.UserPath -ceq $Name)
    }, $true))
    if ($a.Count -ne 1) { throw 'Required exactly one known assignment in pinned launcher.' }
    return $a[0]
}
function Find-McpCalls([object]$Ast) {
    $c = @($Ast.FindAll({
        param($n)
        if ($n -isnot [System.Management.Automation.Language.CommandAst]) { return $false }
        return @($n.CommandElements | Where-Object {
            $_ -is [System.Management.Automation.Language.StringConstantExpressionAst] -and
            $_.Value -ceq '--mcp.command'
        }).Count -gt 0
    }, $true))
    if ($c.Count -ne 2) { throw 'MCP call count differs; stop.' }
    foreach ($call in $c) {
        $items = @($call.CommandElements)
        if ($items.Count -ne 9 -or
            $items[6] -isnot [System.Management.Automation.Language.StringConstantExpressionAst] -or
            $items[6].Value -cne '--mcp.command' -or
            $items[7] -isnot [System.Management.Automation.Language.ExpandableStringExpressionAst] -or
            $items[7].Value -cne 'command=$Bridge' -or
            @($items[7].NestedExpressions).Count -ne 1 -or
            $items[0] -isnot [System.Management.Automation.Language.VariableExpressionAst] -or
            @('Client','Runtime') -cnotcontains $items[0].VariablePath.UserPath) {
            throw 'Unexpected Client/Runtime MCP argument binding.'
        }
    }
    if (@($c | ForEach-Object {$_.CommandElements[0].VariablePath.UserPath} | Select-Object -Unique).Count -ne 2) {
        throw 'Expected one Client and one Runtime MCP call.'
    }
    return $c
}

$body = Read-ExactUtf8 $repo2
$ast = Parse-PowerShell $body
$null = Find-McpCalls $ast
$bridgeAssignment = Find-Assignment $ast 'Bridge'
$bridgeLiterals = @($bridgeAssignment.Right.FindAll({
    param($n)
    $n -is [System.Management.Automation.Language.StringConstantExpressionAst]
}, $true))
if ($bridgeAssignment.Extent.StartLineNumber -ne 24 -or $bridgeLiterals.Count -ne 1) {
    throw 'Unexpected Bridge definition shape.'
}
$bridge = $bridgeLiterals[0]
# NO matching of unknown args or dynamic expressions: only explicitly known Direct exec forms.
$old = $bridge.Value
$suffix = [regex]::Escape($direct)
$known = '^docker exec -i(?: --user 1000:1000| -u 1000:1000)? fortis-repo-test /usr/local/bin/node ' + $suffix + '$'
if ($old -cnotmatch $known) {
    throw 'Repo2 Direct command has a different option shape; stop for read-only review.'
}
$rawLiteral = $bridge.Extent.Text
if ($rawLiteral.Length -lt 2 -or
    ($rawLiteral[0] -ne [char]39 -and $rawLiteral[0] -ne [char]34) -or
    $rawLiteral[$rawLiteral.Length - 1] -ne $rawLiteral[0]) {
    throw 'Bridge quoting is not a single recognized string literal.'
}

$quietBody = Read-ExactUtf8 $repo1Quiet
$quietAst = Parse-PowerShell $quietBody
$quietAssignment = Find-Assignment $quietAst 'fortisQuietNodeOption'
$quietLiterals = @($quietAssignment.Right.FindAll({
    param($n)
    $n -is [System.Management.Automation.Language.StringConstantExpressionAst]
}, $true))
if ($quietLiterals.Count -ne 1) { throw 'Repo1 quiet option definition changed.' }
$option = $quietLiterals[0].Value
$prefix = '--import=data:text/javascript;base64,'
if (-not $option.StartsWith($prefix, [StringComparison]::Ordinal)) {
    throw 'Unexpected Node preload option format.'
}
$preload = [Convert]::FromBase64String($option.Substring($prefix.Length))
$hasher = [Security.Cryptography.SHA256]::Create()
try { $preloadHash = ([BitConverter]::ToString($hasher.ComputeHash($preload))).Replace('-','').ToLowerInvariant() }
finally { $hasher.Dispose() }
if ($preloadHash -cne 'a18a0d409cd1e40bcb6bbb82935a041297aec43de34c65ac26015fa1f7422eb3') {
    throw 'Quiet preload does not match reviewed source.'
}

# Read-only Docker guard for Preview/Stage. The generated Start will repeat this check.
$docker = (Get-Command docker.exe -CommandType Application -ErrorAction Stop).Source
$inspectOutput = & $docker inspect --type container -- $container 2>$null
if ($LASTEXITCODE -ne 0) { throw 'Existing container inspect failed.' }
$inspect = @($inspectOutput | ConvertFrom-Json)
if ($inspect.Count -ne 1 -or $inspect[0].Id -ne $expectedContainerId -or
    -not $inspect[0].State.Running) {
    throw 'Pinned running container not found.'
}
$nodeEnv = @($inspect[0].Config.Env | Where-Object {
    ([string]$_).StartsWith('NODE_OPTIONS=', [StringComparison]::Ordinal)
})
if ($nodeEnv.Count -gt 1 -or ($nodeEnv.Count -eq 1 -and $nodeEnv[0] -cne 'NODE_OPTIONS=')) {
    throw 'Inherited container NODE_OPTIONS is nonempty/ambiguous; stop.'
}

$newBridge = $old.Replace('docker exec -i ', ('docker exec -i --env NODE_OPTIONS=' + $option + ' '))
if ($newBridge -ceq $old) { throw 'No Bridge transformation made.' }
$quote = [string]$rawLiteral[0]
$newLiteral = $quote + $newBridge + $quote
$start = $bridge.Extent.StartOffset
$end = $bridge.Extent.EndOffset
if ($body.Substring($start, $end-$start) -cne $rawLiteral) {
    throw 'Bridge literal span verification failed.'
}
$lineEnd = $body.IndexOf("`n", $end)
if ($lineEnd -lt 0) { $lineEnd = $body.Length }
if ($body.Substring($end, $lineEnd-$end).Trim().Length -ne 0) {
    throw 'Bridge assignment has trailing source on its line; stop.'
}
$newBody = $body.Substring(0,$start) + $newLiteral + $body.Substring($end)

# Start-time fail-closed check; no additional Docker writes, no effect on Status/Setup.
# Insert AFTER the static Bridge definition; leave all original profile, guard and CLI intact.
$crlf = if ($body.Contains("`r`n")) { "`r`n" } else { "`n" }
$check = @'
if ($Action -eq 'Setup') { throw 'Side-by-side quiet candidate refuses Setup/profile or shortcut changes.' }
if ($Action -eq 'Start') {
    $quietDocker = (Get-Command docker.exe -CommandType Application -ErrorAction Stop).Source
    $quietRaw = & $quietDocker inspect --type container -- fortis-repo-test 2>$null
    if ($LASTEXITCODE -ne 0) { throw 'Quiet launcher container inspect failed.' }
    $quietInfo = @($quietRaw | ConvertFrom-Json)
    if ($quietInfo.Count -ne 1 -or
        $quietInfo[0].Id -ne 'c6d7be9fe6eb4138a9dc47db3f82c32c377007c2d461c1f03ad37fe9bb3d074a' -or
        -not $quietInfo[0].State.Running) { throw 'Quiet launcher pinned container missing.' }
    $quietEnv = @($quietInfo[0].Config.Env | Where-Object {
        ([string]$_).StartsWith('NODE_OPTIONS=', [StringComparison]::Ordinal)
    })
    if ($quietEnv.Count -gt 1 -or
        ($quietEnv.Count -eq 1 -and $quietEnv[0] -cne 'NODE_OPTIONS=')) {
        throw 'Quiet launcher refuses existing NODE_OPTIONS.'
    }
}
'@
$check = $check.Replace("`r`n", "`n").Replace("`n", $crlf)
$injectAfter = $start + $newLiteral.Length
$newBody = $newBody.Substring(0, $injectAfter) + $crlf + $check + $newBody.Substring($injectAfter)
$newAst = Parse-PowerShell $newBody
$null = Find-McpCalls $newAst
$newAssignment = Find-Assignment $newAst 'Bridge'
$newLiteralMatches = @($newAssignment.Right.FindAll({
    param($n)
    $n -is [System.Management.Automation.Language.StringConstantExpressionAst] -and
    $n.Value -ceq $newBridge
}, $true))
if ($newLiteralMatches.Count -ne 1) { throw 'Generated Bridge verification failed.' }

# These are two insertions only: exact Bridge expression + the Start-specific read-only policy.
$prepared = $utf8.GetBytes($newBody)
$sha = [Security.Cryptography.SHA256]::Create()
try { $digest = ([BitConverter]::ToString($sha.ComputeHash($prepared))).Replace('-','').ToLowerInvariant() }
finally { $sha.Dispose() }
$result = [ordered]@{
    Mode = $Mode
    SourceShaMatched = $true
    GuardShaMatched = $true
    Repo1QuietShaMatched = $true
    QuietPreloadSha256 = $preloadHash
    BridgeVariant = $(if ($old.Contains('--user 1000:1000')) {'PinnedUserLong'}
        elseif ($old.Contains('-u 1000:1000')) {'PinnedUserShort'} else {'Basic'})
    BothMcpBindingsVerified = $true
    NewPowerShellAst = 'PASS'
    ContainerPinAndNodeOptions = 'PASS'
    CandidateSha256 = $digest
    OriginalUntouched = $true
}
if ($Mode -eq 'Preview') {
    $result['Staged'] = $false
    [pscustomobject]$result | ConvertTo-Json -Depth 4
    return
}
if (Test-Path -LiteralPath $target) { throw 'Side-by-side target already exists; will not overwrite.' }
$stream = [IO.File]::Open($target, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
try { $stream.Write($prepared,0,$prepared.Length) } finally { $stream.Dispose() }
if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -ine $digest) {
    throw 'Staged candidate read-back differs; original remains unchanged.'
}
Assert-PinnedFile $repo2 '13C1956DA1E7B7405F50B495A40225D51E42E568965A68AAFFBE404616093CDB'
$result['Staged'] = $true
$result['CandidateFileName'] = 'FortisRepo2-quiet-logs.ps1'
[pscustomobject]$result | ConvertTo-Json -Depth 4
