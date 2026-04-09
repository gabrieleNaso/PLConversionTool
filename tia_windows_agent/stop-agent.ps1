$ErrorActionPreference = "SilentlyContinue"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ExePath = [System.IO.Path]::GetFullPath((Join-Path $ScriptRoot "bin\Release\net48\PLConversionTool.TiaAgent.exe"))

function Get-AgentProcesses {
    $processes = @()

    $processes += Get-Process | Where-Object {
        $_.ProcessName -eq "PLConversionTool.TiaAgent" -or
        $_.MainWindowTitle -like "*TIA Windows Agent*"
    }

    $cimProcesses = Get-CimInstance Win32_Process | Where-Object {
        $_.ExecutablePath -and (
            $_.ExecutablePath -ieq $ExePath -or
            $_.ExecutablePath -like "*PLConversionTool.TiaAgent.exe"
        )
    }

    foreach ($cimProcess in $cimProcesses) {
        $matched = Get-Process -Id $cimProcess.ProcessId -ErrorAction SilentlyContinue
        if ($matched) {
            $processes += $matched
        }
    }

    $processes |
        Where-Object { $_ } |
        Sort-Object Id -Unique
}

$processes = Get-AgentProcesses

if (-not $processes) {
    Write-Host "Nessun processo agent trovato."
    return
}

foreach ($process in $processes) {
    try {
        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
    }
    catch {
    }

    try {
        taskkill /PID $process.Id /T /F | Out-Null
    }
    catch {
    }
}

$deadline = (Get-Date).AddSeconds(8)
do {
    Start-Sleep -Milliseconds 400
    $remaining = Get-AgentProcesses
} while ($remaining -and (Get-Date) -lt $deadline)

if ($remaining) {
    Write-Host "Alcuni processi agent risultano ancora attivi: $($remaining.Id -join ', ')" -ForegroundColor Yellow
}
else {
    Write-Host "Processo agent terminato."
}
