$ErrorActionPreference = "SilentlyContinue"

$processes = Get-Process | Where-Object {
    $_.ProcessName -eq "PLConversionTool.TiaAgent" -or
    $_.MainWindowTitle -like "*TIA Windows Agent*"
}

if ($processes) {
    $processes | Stop-Process -Force
    Write-Host "Processo agent terminato."
}
else {
    Write-Host "Nessun processo agent trovato."
}
