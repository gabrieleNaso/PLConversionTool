param(
    [string]$Configuration = "Release",
    [string]$Output = ".\publish"
)

$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptRoot

dotnet publish .\PLConversionTool.TiaAgent.csproj `
    --configuration $Configuration `
    --output $Output

Write-Host "Publish completata in $Output"
