param(
    [int]$Port = 8050,
    [string]$RuleName = "PLConversionTool TIA Windows Agent"
)

$ErrorActionPreference = "Stop"

$existing = Get-NetFirewallRule -DisplayName $RuleName -ErrorAction SilentlyContinue

if ($null -eq $existing) {
    New-NetFirewallRule `
        -DisplayName $RuleName `
        -Direction Inbound `
        -Action Allow `
        -Protocol TCP `
        -LocalPort $Port | Out-Null

    Write-Host "Regola firewall creata per la porta $Port"
}
else {
    Write-Host "Regola firewall gia' presente: $RuleName"
}
