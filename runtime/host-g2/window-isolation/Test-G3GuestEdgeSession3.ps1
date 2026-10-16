# Manual paste into ordinary PowerShell under SID1009/Session 3; no source ACL/owner profile reads.
# Synthetic Edge --dump-dom against data: URI, standard sandbox, own unique temporary user-data-dir.
# Existing HOST/Repo/Windows ACLs unchanged. Do not run in owner session.
& {
  $ErrorActionPreference='Stop'
  $id=[Security.Principal.WindowsIdentity]::GetCurrent()
  $session=[Diagnostics.Process]::GetCurrentProcess().SessionId
  $admin=(New-Object Security.Principal.WindowsPrincipal($id)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
  $sid='S-1-5-21-303538662-3368424508-2654684973-1009'
  if ($id.User.Value -ne $sid -or $session -ne 3 -or $admin) { throw 'Guest SID1009, session 3, non-admin required; no process started' }
  $edge='C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
  if (!(Test-Path -LiteralPath $edge -PathType Leaf)) { throw 'Installed Edge not found; no process started' }
  $parent=Join-Path $env:LOCALAPPDATA 'FortisHostG2\Workspace\scratch'
  if (!(Test-Path -LiteralPath $parent -PathType Container)) { throw 'Guest scratch root missing; no process started' }
  if ((Get-Item -LiteralPath $parent).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Guest scratch root reparse refused' }
  $folder=Join-Path $parent ('g3-edge-check-'+[guid]::NewGuid().ToString('N'))
  $proc=$null
  $r=[ordered]@{Sid=$id.User.Value;Session=$session;Admin=$admin;EdgeExitCode=$null;DomMarkerFound=$false;TimedOut=$false;ProfileRemoved=$false;Status='FAIL';ErrorType=$null;CleanupError=$null;OwnerObjectsTouched=0;AclWrites=0}
  try {
    [IO.Directory]::CreateDirectory($folder) | Out-Null
    $profile=Join-Path $folder 'profile'
    $stdout=Join-Path $folder 'stdout.txt'
    $stderr=Join-Path $folder 'stderr.txt'
    $url='data:text/html,%3Chtml%3E%3Cbody%3EG3_SESSION3_EDGE_OK%3C%2Fbody%3E%3C%2Fhtml%3E'
    $arguments=@('--headless=new','--no-first-run','--no-default-browser-check',
      '--disable-background-networking','--disable-extensions','--disable-sync',
      ('--user-data-dir="'+$profile+'"'),'--dump-dom',('"'+$url+'"')) -join ' '
    $proc=Start-Process -FilePath $edge -ArgumentList $arguments -PassThru -WindowStyle Hidden -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    if (!$proc.WaitForExit(25000)) {
      $r.TimedOut=$true
    } else {
      $r.EdgeExitCode=$proc.ExitCode
      if (Test-Path -LiteralPath $stdout -PathType Leaf) {
        $r.DomMarkerFound=([IO.File]::ReadAllText($stdout)).Contains('G3_SESSION3_EDGE_OK')
      }
      if ($r.EdgeExitCode -eq 0 -and $r.DomMarkerFound) { $r.Status='PASS' }
    }
  } catch {
    $r.ErrorType=$_.Exception.GetType().Name
  } finally {
    if ($null -ne $proc) {
      try {
        if (!$proc.HasExited) {
          # Kill ONLY our own identified Edge PID and its children on timeout/error.
          & (Join-Path $env:SystemRoot 'System32\taskkill.exe') /PID $proc.Id /T /F 1>$null 2>$null
          $null=$proc.WaitForExit(5000)
        }
      } catch { $r.CleanupError=$_.Exception.GetType().Name }
      $proc.Dispose()
    }
    for ($i=0;$i -lt 5;$i++) {
      try {
        if (Test-Path -LiteralPath $folder) { Remove-Item -LiteralPath $folder -Recurse -Force -ErrorAction Stop }
        if (!(Test-Path -LiteralPath $folder)) { $r.ProfileRemoved=$true; break }
      } catch { $r.CleanupError=$_.Exception.GetType().Name }
      Start-Sleep -Milliseconds 250
    }
    if (!$r.ProfileRemoved) { $r.Status='FAIL' }
  }
  [pscustomobject]$r | ConvertTo-Json -Compress
}
