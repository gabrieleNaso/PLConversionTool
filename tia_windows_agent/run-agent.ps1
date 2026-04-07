param(
    [string]$Configuration = "Release",
    [switch]$PauseOnExit
)

$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptRoot

try {
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
}
catch {
    Write-Host ""
    Write-Host "ERRORE AVVIO AGENT" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    if ($_.ScriptStackTrace) {
        Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
    }
}
finally {
    if ($PauseOnExit) {
        Write-Host ""
        Read-Host "Premi INVIO per chiudere"
    }
}
