function Get-G2BytesHash([byte[]]$Bytes){
 $sha=[Security.Cryptography.SHA256]::Create()
 try{return ([BitConverter]::ToString($sha.ComputeHash($Bytes))).Replace('-','')}finally{$sha.Dispose()}
}
function Convert-G2SddlBytes([string]$Sddl){
 $sd=New-Object Security.AccessControl.RawSecurityDescriptor($Sddl)
 $bytes=New-Object byte[]($sd.BinaryLength);$sd.GetBinaryForm($bytes,0);return ,$bytes
}
function Get-G2Canonical([byte[]]$Bytes){
 return (New-Object Security.AccessControl.RawSecurityDescriptor($Bytes,0)).GetSddlForm('All')
}
function Get-G2DaclHash([byte[]]$Bytes){
 $sd=New-Object Security.AccessControl.RawSecurityDescriptor($Bytes,0)
 if(!$sd.DiscretionaryAcl){throw 'NULL DACL unsupported'}
 $acl=New-Object byte[]($sd.DiscretionaryAcl.BinaryLength)
 $sd.DiscretionaryAcl.GetBinaryForm($acl,0);return Get-G2BytesHash $acl
}
function New-G2Change([IntPtr]$Handle,[string]$Kind,[string]$Sid,[int]$Mask,[bool]$Synthetic=$false){
 $before=[G2WindowBoundary]::Read($Handle)
 $descriptor=New-Object Security.AccessControl.RawSecurityDescriptor($before,0)
 if($descriptor.Owner.Value -eq $Sid -and !$Synthetic){throw 'Target SID owns the live object; separate recovery required'}
 if($Synthetic -and [G2WindowBoundary]::Name($Handle) -eq 'WinSta0'){throw 'Synthetic operation cannot target WinSta0'}
 $desired=[G2WindowBoundary]::Deny($before,$Sid,$Mask,$Synthetic)
 return [pscustomobject]@{Kind=$Kind;Name=[G2WindowBoundary]::Name($Handle);BeforeSddl=(Get-G2Canonical $before);BeforeHash=(Get-G2BytesHash $before);DesiredSddl=(Get-G2Canonical $desired);DesiredDaclHash=(Get-G2DaclHash $desired);AfterSddl=$null;Applied=$false}
}
function Set-G2Change([IntPtr]$Handle,$Record){
 if([G2WindowBoundary]::Name($Handle) -ne $Record.Name){throw 'Object name changed'}
 $current=[G2WindowBoundary]::Read($Handle)
 if((Get-G2Canonical $current) -ne $Record.BeforeSddl){throw 'Apply CAS mismatch; nothing overwritten'}
 $desired=Convert-G2SddlBytes $Record.DesiredSddl
 [G2WindowBoundary]::Set($Handle,$desired)
 $actual=[G2WindowBoundary]::Read($Handle);$sd=New-Object Security.AccessControl.RawSecurityDescriptor($actual,0)
 $old=New-Object Security.AccessControl.RawSecurityDescriptor($Record.BeforeSddl)
 if($sd.Owner.Value -ne $old.Owner.Value -or $sd.Group.Value -ne $old.Group.Value -or (Get-G2DaclHash $actual) -ne $Record.DesiredDaclHash){throw 'Applied DACL did not match proposal'}
 $Record.AfterSddl=Get-G2Canonical $actual;$Record.Applied=$true
}
function Undo-G2Change([IntPtr]$Handle,$Record){
 if([G2WindowBoundary]::Name($Handle) -ne $Record.Name){throw 'Rollback object name mismatch'}
 $current=[G2WindowBoundary]::Read($Handle);$canonical=Get-G2Canonical $current
 if($canonical -eq $Record.BeforeSddl){return 'AlreadyOriginal'}
 $old=New-Object Security.AccessControl.RawSecurityDescriptor($Record.BeforeSddl)
 $sd=New-Object Security.AccessControl.RawSecurityDescriptor($current,0)
 $matches=if($Record.AfterSddl){$canonical -eq $Record.AfterSddl}else{($sd.Owner.Value -eq $old.Owner.Value -and $sd.Group.Value -eq $old.Group.Value -and (Get-G2DaclHash $current) -eq $Record.DesiredDaclHash)}
 if(!$matches){throw 'Rollback CAS mismatch; later ACL changes preserved'}
 [G2WindowBoundary]::Set($Handle,(Convert-G2SddlBytes $Record.BeforeSddl))
 if([G2WindowBoundary]::Sddl($Handle) -ne $Record.BeforeSddl){throw 'Rollback verification failed'}
 return 'Restored'
}
function Save-G2Backup($Record,[string]$Path){
 $temp=$Path+'.'+[Guid]::NewGuid().ToString('N')+'.tmp'
 try{
  $bytes=[Text.UTF8Encoding]::new($false).GetBytes(($Record|ConvertTo-Json -Depth 10))
  $stream=[IO.File]::Open($temp,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
  try{$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)}finally{$stream.Dispose()}
  if([IO.File]::Exists($Path)){[IO.File]::Replace($temp,$Path,$null)}else{[IO.File]::Move($temp,$Path)}
 }finally{if([IO.File]::Exists($temp)){[IO.File]::Delete($temp)}}
}
function Get-G2Inventory([string]$Sid,[int]$Session){
 $debug=$false
 try{
  if((New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){[Diagnostics.Process]::EnterDebugMode();$debug=$true}
  return @([G2ProcessInventory]::ForSid($Sid,$Session))
 }finally{if($debug){[Diagnostics.Process]::LeaveDebugMode()}}
}
function Assert-G2Absent([string]$Sid,[int]$Session){
 $rows=@(Get-G2Inventory $Sid $Session)
 if($rows.Count){throw ('G2/unknown processes remain; no transition: '+($rows -join ', '))}
}
function New-G2Environment([string]$Profile,[string]$User,[string]$Domain){
 $e=@{SystemRoot='C:\Windows';windir='C:\Windows';ComSpec='C:\Windows\System32\cmd.exe';USERPROFILE=$Profile;LOCALAPPDATA=($Profile+'\AppData\Local');APPDATA=($Profile+'\AppData\Roaming');HOMEDRIVE='C:';HOMEPATH=$Profile.Substring(2);USERNAME=$User;USERDOMAIN=$Domain;TEMP=($Profile+'\AppData\Local\Temp');TMP=($Profile+'\AppData\Local\Temp');DESKTOP_COMMANDER_DISABLE_MCP_UI='1';PATHEXT='.COM;.EXE;.BAT;.CMD';PATH=('C:\Windows\System32;C:\Windows;C:\Windows\System32\WindowsPowerShell\v1.0;C:\Tools\desktop-commander-runtime;'+$Profile+'\AppData\Local\Programs\Python\Python313;'+$Profile+'\AppData\Local\Programs\Python\Python313\Scripts;C:\Program Files\Git\cmd;'+$Profile+'\AppData\Roaming\npm')}
 foreach($name in @('ProgramData','ProgramFiles','ProgramFiles(x86)','NUMBER_OF_PROCESSORS','PROCESSOR_ARCHITECTURE')){
  $value=[Environment]::GetEnvironmentVariable($name,'Machine');if(!$value){$value=[Environment]::GetEnvironmentVariable($name,'Process')};if($value){$e[$name]=$value}
 }
 return $e
}
