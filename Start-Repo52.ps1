$ErrorActionPreference = "Continue"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$DashboardRoot = Join-Path $RepoRoot "web-dashboard"
$DashboardUrl = "http://127.0.0.1:5173"

function Start-Repo52Window {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Title,
        [Parameter(Mandatory = $true)]
        [string] $Command
    )

    Start-Process powershell.exe -ArgumentList @(
        "-NoExit",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        $Command
    )
}

$BackendCommand = @"
`$Host.UI.RawUI.WindowTitle = 'Repo 52 Backend API'
Set-Location -LiteralPath '$DashboardRoot'
Write-Host ''
Write-Host 'Repo 52 backend starting on http://127.0.0.1:8787' -ForegroundColor Cyan
Write-Host 'Leave this window open while using the dashboard.' -ForegroundColor Yellow
Write-Host ''
py -3.11 server.py
"@

$FrontendCommand = @"
`$Host.UI.RawUI.WindowTitle = 'Repo 52 Frontend Dashboard'
Set-Location -LiteralPath '$DashboardRoot'
Write-Host ''
Write-Host 'Repo 52 frontend starting on $DashboardUrl' -ForegroundColor Cyan
Write-Host 'Leave this window open while using the dashboard.' -ForegroundColor Yellow
Write-Host ''
if (-not (Test-Path -LiteralPath 'node_modules')) {
    Write-Host 'Installing dashboard npm packages...' -ForegroundColor Yellow
    npm install
}
npm run dev
"@

Write-Host "Launching Repo 52 Command Center..." -ForegroundColor Cyan
Write-Host "Repo: $RepoRoot"

Start-Repo52Window -Title "Repo 52 Backend API" -Command $BackendCommand
Start-Sleep -Seconds 2
Start-Repo52Window -Title "Repo 52 Frontend Dashboard" -Command $FrontendCommand

Write-Host "Waiting for the dashboard to warm up..." -ForegroundColor Yellow
Start-Sleep -Seconds 8
Start-Process $DashboardUrl

Write-Host "Opened $DashboardUrl" -ForegroundColor Green
