$ErrorActionPreference = "Continue"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$DashboardRoot = Join-Path $RepoRoot "web-dashboard"
$DashboardUrl = "http://127.0.0.1:5173"

function Stop-Repo52PortListeners {
    param(
        [int[]] $Ports
    )

    foreach ($Port in $Ports) {
        $Connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
        foreach ($Connection in $Connections) {
            $ProcessId = $Connection.OwningProcess
            if ($ProcessId -gt 0) {
                try {
                    $Process = Get-Process -Id $ProcessId -ErrorAction Stop
                    Write-Host "Stopping stale Repo 52 listener on port $Port (PID $ProcessId / $($Process.ProcessName))..." -ForegroundColor Yellow
                    Stop-Process -Id $ProcessId -Force -ErrorAction Stop
                } catch {
                    Write-Host "Could not stop listener on port $Port (PID $ProcessId): $($_.Exception.Message)" -ForegroundColor DarkYellow
                }
            }
        }
    }
}

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
Write-Host 'Local demo mode is enabled so PostgreSQL is not required for this shortcut.' -ForegroundColor Yellow
Write-Host 'Leave this window open while using the dashboard.' -ForegroundColor Yellow
Write-Host ''
`$env:REPO52_DEMO_MODE = 'true'
`$env:APP_ENV = 'development'
`$env:REQUIRE_ALEMBIC_MIGRATIONS = 'false'
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
Stop-Repo52PortListeners -Ports @(8787, 5173)

Start-Repo52Window -Title "Repo 52 Backend API" -Command $BackendCommand
Start-Sleep -Seconds 2
Start-Repo52Window -Title "Repo 52 Frontend Dashboard" -Command $FrontendCommand

Write-Host "Waiting for the dashboard to warm up..." -ForegroundColor Yellow
Start-Sleep -Seconds 8
Start-Process $DashboardUrl

Write-Host "Opened $DashboardUrl" -ForegroundColor Green
