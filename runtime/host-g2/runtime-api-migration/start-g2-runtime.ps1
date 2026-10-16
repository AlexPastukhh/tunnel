$ErrorActionPreference='Stop'
$RequiredSid='S-1-5-21-303538662-3368424508-2654684973-1009'
$identity=[Security.Principal.WindowsIdentity]::GetCurrent()
$principal=New-Object Security.Principal.WindowsPrincipal($identity)
if($identity.User.Value -ne $RequiredSid -or $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Run only in the existing standard FortisHostG1 console'}
$Runtime='C:\Tools\tunnel-client\runtime\v0.0.15\tunnel-client-runtime.exe'
if((Get-FileHash -LiteralPath $Runtime -Algorithm SHA256).Hash -ne 'A922D372D6BE0649156FBC1C8A040597F1F4BB5B4356890151D7875602593B1A'){throw 'Runtime changed'}
$Profile='fortis-host-g2-test'
$ProfileDir=Join-Path $env:LOCALAPPDATA 'FortisHostG2\profiles'
if(!(Test-Path -LiteralPath (Join-Path $ProfileDir ($Profile+'.yaml')))){throw 'Existing G2 profile missing'}
# This account is dedicated to G2. Check the actual owner SID, independently of argv order.
$existing=@(foreach($running in (Get-CimInstance Win32_Process -Filter "Name='tunnel-client.exe' OR Name='tunnel-client-runtime.exe'")){
 $runningOwner=Invoke-CimMethod -InputObject $running -MethodName GetOwnerSid -ErrorAction Stop
 if($runningOwner.ReturnValue -ne 0){throw 'Cannot verify a running tunnel owner; inspect before switching'}
 if($runningOwner.Sid -eq $RequiredSid){$running}
})
if($existing.Count){throw 'G2 is already running; close its existing console before switching'}
$key=Read-Host 'Enter the separate G2 test runtime key locally' -AsSecureString
$ptr=[IntPtr]::Zero
try{
 $ptr=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($key)
 $env:CONTROL_PLANE_API_KEY=[Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
 $env:DESKTOP_COMMANDER_DISABLE_MCP_UI='1'
 & $Runtime run --profile $Profile --profile-dir $ProfileDir --control-plane.api-key env:CONTROL_PLANE_API_KEY '--harpoon.additional-transport='
 if($LASTEXITCODE -ne 0){throw 'G2 runtime exited with an error'}
}finally{
 Remove-Item Env:CONTROL_PLANE_API_KEY -ErrorAction SilentlyContinue
 if($ptr -ne [IntPtr]::Zero){[Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)}
 $key.Dispose()
}
