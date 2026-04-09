$ErrorActionPreference = "SilentlyContinue"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$StopScript = Join-Path $ScriptRoot "stop-agent.ps1"

Set-Location $env:TEMP

if (Test-Path $StopScript) {
    & $StopScript
    Start-Sleep -Seconds 1
}

$pathsToRemove = @(
    (Join-Path $ScriptRoot "bin"),
    (Join-Path $ScriptRoot "obj")
)

foreach ($targetPath in $pathsToRemove) {
    if (-not (Test-Path $targetPath)) {
        continue
    }

    $removed = $false
    for ($attempt = 1; $attempt -le 5; $attempt++) {
        try {
            Remove-Item $targetPath -Recurse -Force -ErrorAction Stop
            Write-Host "Rimossa: $targetPath"
            $removed = $true
            break
        }
        catch {
            Start-Sleep -Milliseconds (500 * $attempt)
        }
    }

    if (-not $removed) {
        Write-Host "Impossibile rimuovere subito: $targetPath" -ForegroundColor Yellow
    }
}

Write-Host "Pulizia completata. Se la cartella resta occupata, chiudi anche eventuali shell aperte dentro la directory dell'agent."
