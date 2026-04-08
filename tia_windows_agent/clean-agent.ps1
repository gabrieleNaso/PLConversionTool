$ErrorActionPreference = "SilentlyContinue"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Set-Location $env:TEMP

$processes = Get-Process | Where-Object {
    $_.ProcessName -eq "PLConversionTool.TiaAgent" -or
    $_.MainWindowTitle -like "*TIA Windows Agent*"
}

if ($processes) {
    $processes | Stop-Process -Force
    Start-Sleep -Milliseconds 800
    Write-Host "Processo agent terminato."
}
else {
    Write-Host "Nessun processo agent trovato."
}

$binPath = Join-Path $ScriptRoot "bin"
$objPath = Join-Path $ScriptRoot "obj"

if (Test-Path $binPath) {
    Remove-Item $binPath -Recurse -Force
    Write-Host "Cartella bin rimossa."
}

if (Test-Path $objPath) {
    Remove-Item $objPath -Recurse -Force
    Write-Host "Cartella obj rimossa."
}

Write-Host "Pulizia completata. Ora la cartella dell'agent non dovrebbe piu' essere occupata dalla shell corrente."
