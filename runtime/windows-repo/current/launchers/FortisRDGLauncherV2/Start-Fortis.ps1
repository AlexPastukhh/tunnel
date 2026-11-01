. (Join-Path $PSScriptRoot 'Common.ps1')
try {
    $id = Ensure-Fortis
    Write-Host "Fortis готов. ID: $id" -ForegroundColor Green
    Write-Host 'Подключение Fortis Repo 2 -> Fortis Repo 1 выполняется вручную в прежнем порядке.'
} catch { Write-Host $_.Exception.Message -ForegroundColor Red; exit 1 }
