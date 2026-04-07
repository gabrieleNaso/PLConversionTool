param(
    [string]$Configuration = "Release",
    [int]$Port = 8050
)

$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptRoot

Write-Host "Bootstrap VM Windows per TIA Windows Agent"

if (-not (Get-Command dotnet -ErrorAction SilentlyContinue)) {
    Write-Warning "dotnet non trovato. Va bene se compili con Visual Studio/MSBuild, ma gli script dotnet non funzioneranno."
}

if (-not (Test-Path ".\appsettings.Local.json")) {
    if (Test-Path ".\appsettings.Local.template.json") {
        Copy-Item ".\appsettings.Local.template.json" ".\appsettings.Local.json"
        Write-Host "Creato appsettings.Local.json dal template."
    }
    else {
        throw "Template appsettings.Local.template.json non trovato."
    }
}

$assemblyPath = "C:\Program Files\Siemens\Automation\Portal V20\PublicAPI\V20\Siemens.Engineering.dll"
if (Test-Path $assemblyPath) {
    Write-Host "OK: Siemens.Engineering.dll trovata in $assemblyPath"
}
else {
    Write-Warning "Siemens.Engineering.dll non trovata nel path standard. Aggiorna appsettings.Local.json."
}

& ".\install-firewall-rule.ps1" -Port $Port

Write-Host ""
Write-Host "Bootstrap completato."
Write-Host "Passi successivi:"
Write-Host "1. Verifica appsettings.Local.json"
Write-Host "2. Avvia con .\run-agent.ps1"
Write-Host "3. Testa GET http://localhost:$Port/health"
