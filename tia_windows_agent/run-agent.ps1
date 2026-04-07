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

if (-not (Get-Command dotnet -ErrorAction SilentlyContinue)) {
    throw "dotnet non trovato. Installa un SDK compatibile o compila il progetto con Visual Studio/MSBuild."
}

dotnet build .\PLConversionTool.TiaAgent.csproj --configuration $Configuration

$exePath = ".\bin\$Configuration\net48\PLConversionTool.TiaAgent.exe"
if (-not (Test-Path $exePath)) {
    throw "Eseguibile non trovato: $exePath"
}

& $exePath
