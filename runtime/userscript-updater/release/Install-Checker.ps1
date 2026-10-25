param(
 [Parameter(Mandatory=$true)][string]$InstallRoot,
 [Parameter(Mandatory=$true)][string]$DataRoot,
 [Parameter(Mandatory=$true)][string[]]$SourceRoot,
 [Parameter(Mandatory=$true)][string[]]$ApprovedRoot,
 [Parameter(Mandatory=$true)][string]$OwnerSid
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$Bundle=$PSScriptRoot
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
 [Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Use elevated owner PowerShell for the reviewed installation.' }
function Assert-Plain([string]$Path) {
 if ($Path -notmatch '^[A-Za-z]:\\' -or $Path.Contains('..')) { throw "Explicit local drive path required: $Path" }
 $next=$Path
 while ($next) {
  if (Test-Path -LiteralPath $next) {
   if ((Get-Item -LiteralPath $next -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Reparse ancestor: $next" }
  }
  $parent=Split-Path -Parent $next
  if ($parent -eq $next) { break }
  $next=$parent
 }
}
foreach ($path in @($InstallRoot,$DataRoot)+$SourceRoot+$ApprovedRoot) { Assert-Plain $path }
if (Test-Path -LiteralPath $InstallRoot) { throw 'Use a new version directory; existing installation is preserved.' }
if (Test-Path -LiteralPath $DataRoot) { throw 'Use a new data directory; migration is a separate reviewed action.' }
foreach ($s in $SourceRoot) {
 if ($Bundle.TrimEnd('\').Equals($s.TrimEnd('\'),[StringComparison]::OrdinalIgnoreCase) -or
     $Bundle.TrimEnd('\').StartsWith($s.TrimEnd('\')+'\',[StringComparison]::OrdinalIgnoreCase)) {
  throw 'Copy/extract the reviewed archive outside source/agent-write workspaces before installation.'
 }
}
$protected=@($InstallRoot,$DataRoot)+$ApprovedRoot
foreach ($p in $protected) {
 foreach ($s in @($Bundle)+$SourceRoot) {
  if ($p.TrimEnd('\').Equals($s.TrimEnd('\'),[StringComparison]::OrdinalIgnoreCase) -or
      $p.TrimEnd('\').StartsWith($s.TrimEnd('\')+'\',[StringComparison]::OrdinalIgnoreCase) -or
      $s.TrimEnd('\').StartsWith($p.TrimEnd('\')+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Protected/source/bundle path overlap.' }
 }
 foreach ($other in $protected) {
  if ($p -ne $other -and ($p.TrimEnd('\').StartsWith($other.TrimEnd('\')+'\',[StringComparison]::OrdinalIgnoreCase) -or
      $other.TrimEnd('\').StartsWith($p.TrimEnd('\')+'\',[StringComparison]::OrdinalIgnoreCase))) { throw 'Protected roots must be separate.' }
 }
}
$manifest=Get-Content -LiteralPath (Join-Path $Bundle 'bundle-manifest.json') -Raw | ConvertFrom-Json
$expected=@{}
foreach ($entry in $manifest.files) {
 if ($entry.path -match '(^|/)\.\.(/|$)|:|\\|^/') { throw 'Unsafe manifest path.' }
 if ($expected.ContainsKey($entry.path)) { throw 'Duplicate/case-colliding manifest path.' }
 $expected[$entry.path]=$true
 $file=Join-Path $Bundle $entry.path.Replace('/','\')
 if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Missing bundle file: $file" }
 if ((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.sha256) { throw "Hash mismatch: $file" }
}
foreach ($file in Get-ChildItem -LiteralPath $Bundle -Recurse -Force) {
 if ($file.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Bundle reparse point: $($file.FullName)" }
 if (-not $file.PSIsContainer) {
  $relative=$file.FullName.Substring($Bundle.Length+1).Replace('\','/')
  if ($relative -ne 'bundle-manifest.json' -and -not $expected.ContainsKey($relative)) { throw "Extra bundle file: $relative" }
 }
}
$installer=Join-Path $Bundle 'python-3.13.17-amd64.exe'
$signature=Get-AuthenticodeSignature -LiteralPath $installer
if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'Python Software Foundation') { throw 'Python Authenticode verification failed.' }
New-Item -ItemType Directory -Path $InstallRoot | Out-Null
New-Item -ItemType Directory -Path $DataRoot | Out-Null
foreach ($p in @((Join-Path $DataRoot 'state'),(Join-Path $DataRoot 'policies'))) { New-Item -ItemType Directory -Path $p | Out-Null }
foreach ($p in $ApprovedRoot) { if (-not (Test-Path -LiteralPath $p)) { New-Item -ItemType Directory -Path $p | Out-Null } }
foreach ($name in @('app','qa','profiles')) { Copy-Item -LiteralPath (Join-Path $Bundle $name) -Destination $InstallRoot -Recurse }
foreach ($name in @('run_installed.py','Start-Checker.cmd','Accept-Checker.ps1','WINDOWS_ACCEPTANCE.md','ROLLBACK_INSTALL.md','release.json','dependency-inventory.json','npm-package-lock.json','requirements-windows.lock')) {
 Copy-Item -LiteralPath (Join-Path $Bundle $name) -Destination $InstallRoot
}
$pythonRoot=Join-Path $InstallRoot 'python'
$arguments='/quiet InstallAllUsers=0 TargetDir="'+$pythonRoot+'" Include_launcher=0 Include_pip=1 Include_tcltk=1 Include_test=0 Include_doc=0 Include_dev=0 PrependPath=0 Shortcuts=0 CompileAll=0'
$setup=Start-Process -FilePath $installer -ArgumentList $arguments -Wait -PassThru
if ($setup.ExitCode -ne 0) { throw "Python setup failed: $($setup.ExitCode). Keep staged files for inspection." }
$python=Join-Path $pythonRoot 'python.exe'
Push-Location $InstallRoot
try {
 & $python -I -B -m pip --isolated --disable-pip-version-check install --no-index --no-compile --no-warn-script-location --require-hashes --find-links (Join-Path $Bundle 'wheelhouse') --target (Join-Path $InstallRoot 'pydeps') -r (Join-Path $Bundle 'requirements-windows.lock')
 if ($LASTEXITCODE -ne 0) { throw 'Offline dependency installation failed.' }
} finally { Pop-Location }
Expand-Archive -LiteralPath (Join-Path $Bundle 'node-v22.23.3-win-x64.zip') -DestinationPath $InstallRoot
Move-Item -LiteralPath (Join-Path $InstallRoot 'node-v22.23.3-win-x64') -Destination (Join-Path $InstallRoot 'node')
# Replay canonical npm tarballs offline; never trust a mutable expanded Docker tree.
$eslintRoot=Join-Path $InstallRoot 'eslint'
$bootstrap=Join-Path $InstallRoot 'bootstrap'
New-Item -ItemType Directory -Path $eslintRoot | Out-Null
New-Item -ItemType Directory -Path $bootstrap | Out-Null
Copy-Item -LiteralPath (Join-Path $Bundle 'npm-cache') -Destination $bootstrap -Recurse
Copy-Item -LiteralPath (Join-Path $Bundle 'npm-package.json') -Destination (Join-Path $eslintRoot 'package.json')
Copy-Item -LiteralPath (Join-Path $Bundle 'npm-package-lock.json') -Destination (Join-Path $eslintRoot 'package-lock.json')
$userNpmConfig=Join-Path $bootstrap 'empty-user.npmrc'
$globalNpmConfig=Join-Path $bootstrap 'empty-global.npmrc'
[IO.File]::WriteAllText($userNpmConfig,'')
[IO.File]::WriteAllText($globalNpmConfig,'')
$checkerPreviousNodeOptions=$env:NODE_OPTIONS
$checkerPreviousNodePath=$env:NODE_PATH
try {
 $env:NODE_OPTIONS=''
 $env:NODE_PATH=''
 & (Join-Path $InstallRoot 'node\node.exe') (Join-Path $InstallRoot 'node\node_modules\npm\bin\npm-cli.js') ci --offline --ignore-scripts --audit=false --fund=false --cache (Join-Path $bootstrap 'npm-cache') --userconfig $userNpmConfig --globalconfig $globalNpmConfig --prefix $eslintRoot
 if ($LASTEXITCODE -ne 0) { throw 'Offline integrity-checked npm dependency replay failed.' }
} finally {
 $env:NODE_OPTIONS=$checkerPreviousNodeOptions
 $env:NODE_PATH=$checkerPreviousNodePath
}
Copy-Item -LiteralPath (Join-Path $InstallRoot 'profiles\starter-pack.json') -Destination (Join-Path $DataRoot 'policies\starter.json')
$tools=@()
foreach ($kind in @('eslint','semgrep')) {
 $exe=if ($kind -eq 'eslint') { Join-Path $InstallRoot 'eslint\node_modules\eslint\bin\eslint.js' } else { $python }
 $cfg=Join-Path $InstallRoot $(if ($kind -eq 'eslint') { 'profiles\base-eslint.cjs' } else { 'profiles\base-semgrep.json' })
 $tools+=@{kind=$kind;executable=$exe;executable_sha256=(Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant();
  config=$cfg;config_sha256=(Get-FileHash -LiteralPath $cfg -Algorithm SHA256).Hash.ToLowerInvariant();
  node=$(if ($kind -eq 'eslint') { Join-Path $InstallRoot 'node\node.exe' } else { $null })}
}
$profile=@{schema_version=1;state_root=(Join-Path $DataRoot 'state');policy_root=(Join-Path $DataRoot 'policies');
 source_roots=$SourceRoot;tools=$tools;required_for_suffix=@{'.js'=@('eslint','semgrep');'.cjs'=@('eslint','semgrep');'.mjs'=@('eslint','semgrep');'.py'=@('semgrep')};timeout_seconds=180}
$utf8=New-Object Text.UTF8Encoding($false)
[IO.File]::WriteAllText((Join-Path $InstallRoot 'installation.json'),($profile | ConvertTo-Json -Depth 8),$utf8)
[IO.File]::WriteAllText((Join-Path $InstallRoot 'installation-owner.json'),(@{owner_sid=$OwnerSid;approved_roots=$ApprovedRoot} | ConvertTo-Json -Depth 5),$utf8)
@'
.
Lib
DLLs
..\app
..\pydeps
..\pydeps\win32
..\pydeps\win32\lib
..\pydeps\Pythonwin
..\pydeps\pywin32_system32
'@ | Set-Content -LiteralPath (Join-Path $pythonRoot 'python313._pth') -Encoding ASCII
function Protect-Tree([string]$Path,[bool]$Immutable) {
 $owner=New-Object Security.Principal.SecurityIdentifier($OwnerSid)
 $admins=New-Object Security.Principal.SecurityIdentifier('S-1-5-32-544')
 $system=New-Object Security.Principal.SecurityIdentifier('S-1-5-18')
 foreach ($item in @(Get-Item -LiteralPath $Path)+@(Get-ChildItem -LiteralPath $Path -Recurse -Force)) {
  if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Reparse installed path: $($item.FullName)" }
  $acl=Get-Acl -LiteralPath $item.FullName
  $acl.SetAccessRuleProtection($true,$false)
  foreach ($rule in @($acl.Access)) { [void]$acl.RemoveAccessRuleSpecific($rule) }
  $inherit=if ($item.PSIsContainer) { [Security.AccessControl.InheritanceFlags]'ContainerInherit,ObjectInherit' } else { [Security.AccessControl.InheritanceFlags]::None }
  foreach ($sid in @($admins,$system)) { $acl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule($sid,'FullControl',$inherit,'None','Allow'))) }
  $rights=if ($Immutable) { 'ReadAndExecute' } else { 'FullControl' }
  $acl.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule($owner,$rights,$inherit,'None','Allow')))
  $acl.SetOwner($(if ($Immutable) { $admins } else { $owner }))
  Set-Acl -LiteralPath $item.FullName -AclObject $acl
 }
}
Protect-Tree $InstallRoot $true
Protect-Tree $DataRoot $false
Write-Output 'Candidate staged; normal runtime Update is blocked until native acceptance.'
Write-Output ('Run as normal owner: & "{0}" -I -S -B -X utf8 "{1}\qa\native_acceptance.py" --profile "{1}\installation.json" --report "{2}\native-qa.json"' -f $python,$InstallRoot,$DataRoot)
Write-Output 'Follow WINDOWS_ACCEPTANCE.md. Existing approved-root ACLs were not modified.'
