
$ErrorActionPreference='Stop'
$id=[Security.Principal.WindowsIdentity]::GetCurrent()
if($id.User.Value -ne 'S-1-5-21-303538662-3368424508-2654684973-1009'){throw 'Wrong SID'}
Add-Type -TypeDefinition 'using System;using System.Runtime.InteropServices;public static class G3RemoveLink{[DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)]static extern bool RemoveDirectory(string p);public static int Remove(string p){return RemoveDirectory(p)?0:Marshal.GetLastWin32Error();}}'
$root='C:\Users\Public\Documents\FortisHostG1Probe'
$nonce='probe-g3-junction-1791876964475-nj60am'
$base=Join-Path ($root+'\RW') $nonce
$data=Join-Path $base 'data'
$probe=$nonce+'.txt'
if(Test-Path -LiteralPath $base){throw 'Existing probe: STOP'}
$rows=@(
 [pscustomobject]@{Kind='rw';Target=$data},
 [pscustomobject]@{Kind='ro';Target=(Join-Path $root 'RO')},
 [pscustomobject]@{Kind='deny';Target=(Join-Path $root 'DENY')}
)
$links=@();$createdFiles=@();$results=@();$cleanup=@();$fatal=$null
try{
 [IO.Directory]::CreateDirectory($data)|Out-Null
 foreach($row in $rows){
  $link=Join-Path $base ('link-'+$row.Kind)
  $info=New-Object Diagnostics.ProcessStartInfo
  $info.FileName=$env:COMSPEC
  $info.Arguments='/d /c mklink /J "'+$link+'" "'+$row.Target+'"'
  $info.UseShellExecute=$false
  $info.RedirectStandardOutput=$true
  $info.RedirectStandardError=$true
  $p=[Diagnostics.Process]::Start($info)
  $stdout=$p.StandardOutput.ReadToEnd();$stderr=$p.StandardError.ReadToEnd();$p.WaitForExit()
  if($p.ExitCode -ne 0){throw ('Junction create failed: '+$row.Kind)}
  $links+=$link
  $item=Get-Item -LiteralPath $link -Force
  $actualTarget=[string]@($item.Target)[0]
  if(!$actualTarget.Equals($row.Target,[StringComparison]::OrdinalIgnoreCase)){throw ('Junction target mismatch: '+$row.Kind)}
  $results+=[pscustomobject]@{kind=$row.Kind;operation='target_verification';result='PASS';target=$actualTarget}

  $path=Join-Path $link $probe
  $writeResult='ERROR';$writeError=$null
  try{
   $stream=[IO.File]::Open($path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
   $createdFiles+=$path
   try{$bytes=[Text.Encoding]::UTF8.GetBytes('G3 synthetic junction fixture');$stream.Write($bytes,0,$bytes.Length)}finally{$stream.Dispose()}
   $writeResult='ALLOW'
  }catch{
   $ex=$_.Exception;while($ex.InnerException){$ex=$ex.InnerException}
   $writeError=('0x{0:X8}' -f $ex.HResult)
   if($ex -is [UnauthorizedAccessException]){$writeResult='DENY'}
  }
  $results+=[pscustomobject]@{kind=$row.Kind;operation='write';result=$writeResult;hresult=$writeError}
  if(($row.Kind -eq 'rw' -and $writeResult -ne 'ALLOW') -or ($row.Kind -ne 'rw' -and $writeResult -ne 'DENY')){throw ('Unexpected write result: '+$row.Kind)}

  $readPath=if($row.Kind -eq 'rw'){$path}else{Join-Path $link 'marker.txt'}
  $readResult='ERROR';$readError=$null;$readback=$null
  try{$value=[IO.File]::ReadAllText($readPath);$readResult='ALLOW';if($row.Kind -eq 'rw'){$readback=($value -ceq 'G3 synthetic junction fixture')}}catch{
   $ex=$_.Exception;while($ex.InnerException){$ex=$ex.InnerException}
   $readError=('0x{0:X8}' -f $ex.HResult)
   if($ex -is [UnauthorizedAccessException]){$readResult='DENY'}
  }
  $results+=[pscustomobject]@{kind=$row.Kind;operation='read';result=$readResult;hresult=$readError;rwReadback=$readback}
  if(($row.Kind -eq 'deny' -and $readResult -ne 'DENY') -or ($row.Kind -ne 'deny' -and $readResult -ne 'ALLOW') -or ($row.Kind -eq 'rw' -and !$readback)){throw ('Unexpected read result: '+$row.Kind)}
 }
}catch{$fatal=$_.Exception.Message}
finally{
 foreach($file in $createdFiles){try{[IO.File]::Delete($file)}catch{$cleanup+=[pscustomobject]@{path=$file;error=$_.Exception.GetType().FullName}}}
 foreach($link in $links){
  try{
   if(([IO.File]::GetAttributes($link) -band [IO.FileAttributes]::ReparsePoint) -eq 0){throw 'Cleanup refused ordinary directory'}
   $code=[G3RemoveLink]::Remove($link)
   if($code -ne 0){$cleanup+=[pscustomobject]@{path=$link;win32=$code}}
  }catch{$cleanup+=[pscustomobject]@{path=$link;error=$_.Exception.GetType().FullName}}
 }
 try{if([IO.Directory]::Exists($data)){[IO.Directory]::Delete($data,$false)};if([IO.Directory]::Exists($base)){[IO.Directory]::Delete($base,$false)}}catch{$cleanup+=[pscustomobject]@{path=$base;error=$_.Exception.GetType().FullName}}
}
[pscustomobject]@{sid=$id.User.Value;nonce=$nonce;targetProbeName=$probe;results=$results;fatal=$fatal;cleanupErrors=$cleanup;baseAbsent=![IO.Directory]::Exists($base)}|ConvertTo-Json -Depth 8
