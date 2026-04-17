param(
    [string]$BoardIp = "192.168.178.50",
    [int]$BoardUdpPort = 1234,
    [string]$BindIp = "0.0.0.0",
    [int]$BindPort = 1234,
    [switch]$Scan
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Push-Location $repoRoot
try {
    Write-Host "Starting/ensuring Docker service container..." -ForegroundColor Cyan
    docker compose up -d litex_builder
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose up failed with exit code $LASTEXITCODE"
    }

    Write-Host "Clearing stale litex_server processes in container..." -ForegroundColor Cyan
    docker compose exec -T litex_builder /bin/bash -lc "pkill -f litex_server || true"

    if ($Scan) {
        $serverCmd = "litex_server --udp --udp-scan --bind-ip $BindIp --bind-port $BindPort"
    } else {
        $serverCmd = "litex_server --udp --udp-ip $BoardIp --udp-port $BoardUdpPort --bind-ip $BindIp --bind-port $BindPort"
    }

    Write-Host ""
    Write-Host "Launching LiteX server in foreground:" -ForegroundColor Green
    Write-Host "  $serverCmd"
    Write-Host ""
    Write-Host "Use Ctrl+C in this terminal to stop it." -ForegroundColor Yellow
    Write-Host "Run captures from another terminal with litescope_cli against 127.0.0.1:$BindPort." -ForegroundColor Yellow
    Write-Host ""

    docker compose exec -T litex_builder /bin/bash -lc "$serverCmd"
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
