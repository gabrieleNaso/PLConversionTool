param(
    [string]$Configuration = "Release"
)

$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptRoot

if (-not (Test-Path ".\appsettings.Local.json")) {
    if (Test-Path ".\appsettings.Local.template.json") {
        Copy-Item ".\appsettings.Local.template.json" ".\appsettings.Local.json"
        Write-Host "Creato appsettings.Local.json dal template. Verifica i path prima di usare Openness reale."
    }
}

Write-Host "Avvio TIA Windows Agent dalla cartella $ScriptRoot"
dotnet run --configuration $Configuration
