#Requires -Version 5.1
# Read selected uninstall metadata only. No applications or uninstallers are run.
# Output is JSON on stdout. No registry values or files are changed.
& {
    Set-StrictMode -Version 2.0
    $ErrorActionPreference = 'Stop'

    if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
        throw 'This collector requires Windows.'
    }
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    if ($identity.Name -ine 'FORTIS_M\FortisHostG1') {
        throw 'Run manually in the FortisHostG1 Windows account, without elevation.'
    }
    $principal = New-Object -TypeName System.Security.Principal.WindowsPrincipal -ArgumentList $identity
    if ($principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'Use an ordinary, non-elevated PowerShell window.'
    }

    $scopes = @(
        @{ Scope = 'Machine64'; Hive = [Microsoft.Win32.RegistryHive]::LocalMachine;
            View = [Microsoft.Win32.RegistryView]::Registry64 },
        @{ Scope = 'Machine32'; Hive = [Microsoft.Win32.RegistryHive]::LocalMachine;
            View = [Microsoft.Win32.RegistryView]::Registry32 },
        @{ Scope = 'CurrentG1'; Hive = [Microsoft.Win32.RegistryHive]::CurrentUser;
            View = [Microsoft.Win32.RegistryView]::Registry64 }
    )
    $uninstallPath = 'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall'
    $raw = [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames
    $rows = New-Object 'System.Collections.Generic.List[object]'
    $failures = New-Object 'System.Collections.Generic.List[object]'

    foreach ($scope in $scopes) {
        $baseKey = $null
        $uninstall = $null
        try {
            $baseKey = [Microsoft.Win32.RegistryKey]::OpenBaseKey($scope.Hive, $scope.View)
            $uninstall = $baseKey.OpenSubKey($uninstallPath, $false)
            if ($null -eq $uninstall) {
                $failures.Add([pscustomobject]@{
                    Scope = $scope.Scope; Key = $uninstallPath; Status = 'RootMissing'
                })
                continue
            }
            foreach ($subkeyName in $uninstall.GetSubKeyNames()) {
                $app = $null
                try {
                    $app = $uninstall.OpenSubKey($subkeyName, $false)
                    if ($null -eq $app) {
                        $failures.Add([pscustomobject]@{
                            Scope = $scope.Scope; Key = $subkeyName; Status = 'KeyMissing'
                        })
                        continue
                    }
                    $name = [string]$app.GetValue('DisplayName', $null, $raw)
                    if ([string]::IsNullOrWhiteSpace($name)) { continue }
                    $rows.Add([pscustomobject]@{
                        Scope = $scope.Scope
                        RegistryKey = $app.Name
                        Name = $name
                        Version = [string]$app.GetValue('DisplayVersion', $null, $raw)
                        Publisher = [string]$app.GetValue('Publisher', $null, $raw)
                        RecordedInstallLocation = [string]$app.GetValue('InstallLocation', $null, $raw)
                        RecordedDisplayIcon = [string]$app.GetValue('DisplayIcon', $null, $raw)
                    })
                }
                catch {
                    $failures.Add([pscustomobject]@{
                        Scope = $scope.Scope; Key = $subkeyName
                        Status = 'ReadError'; ErrorType = $_.Exception.GetType().FullName
                    })
                }
                finally {
                    if ($null -ne $app) { $app.Close() }
                }
            }
        }
        catch {
            $failures.Add([pscustomobject]@{
                Scope = $scope.Scope; Key = $uninstallPath
                Status = 'ReadError'; ErrorType = $_.Exception.GetType().FullName
            })
        }
        finally {
            if ($null -ne $uninstall) { $uninstall.Close() }
            if ($null -ne $baseKey) { $baseKey.Close() }
        }
    }

    [pscustomobject]@{
        CollectedUnder = $identity.Name
        UserSid = $identity.User.Value
        CollectedAtUtc = [DateTime]::UtcNow.ToString('o')
        Evidence = 'Registry declarations only; paths, file permissions and launchability are not verified.'
        RecordCount = $rows.Count
        Rows = @($rows.ToArray() | Sort-Object Scope, Name, Version, RegistryKey)
        Failures = @($failures.ToArray())
    } | ConvertTo-Json -Depth 5
}
