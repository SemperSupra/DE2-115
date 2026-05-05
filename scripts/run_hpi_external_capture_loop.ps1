param(
    [int]$Port = 1235,
    [string]$Mode = "rw",
    [string]$HpiPort = "data",
    [string]$TestAddr = "0x1000",
    [string]$TestData = "0x1234",
    [int]$Count = 0,
    [double]$PeriodMs = 100,
    [int]$PingCount = 10,
    [int]$CsrLoops = 32,
    [switch]$SkipEthernetGate,
    [switch]$NoReset,
    [string]$Log = "local_artifacts\hpi_external_capture_loop.log"
)

$ErrorActionPreference = "Stop"

$validModes = @("read", "write", "rw")
$validPorts = @("address", "data", "mailbox", "status")
if ($validModes -notcontains $Mode) {
    throw "Invalid Mode '$Mode'. Use one of: $($validModes -join ', ')"
}
if ($validPorts -notcontains $HpiPort) {
    throw "Invalid HpiPort '$HpiPort'. Use one of: $($validPorts -join ', ')"
}

$logDir = Split-Path -Parent $Log
if ($logDir) {
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
}

Write-Host "HPI external capture automation"
Write-Host "Board target : 192.168.178.50"
Write-Host "LiteX port   : $Port"
Write-Host "Mode/port    : $Mode / $HpiPort"
Write-Host "HPI address  : $TestAddr"
Write-Host "HPI data     : $TestData"
Write-Host "Period       : $PeriodMs ms"
Write-Host "Count        : $Count (0 means until Ctrl+C)"
Write-Host ""
Write-Host "External analyzer trigger:"
Write-Host "  read/rw : trigger on OTG_RD_N falling or OTG_CS_N low"
Write-Host "  write   : trigger on OTG_WR_N falling or OTG_CS_N low"
Write-Host "Capture pins:"
Write-Host "  OTG_DATA[15:0], OTG_ADDR[1:0], OTG_CS_N, OTG_RD_N, OTG_WR_N, OTG_RST_N"
Write-Host ""

if (-not $SkipEthernetGate) {
    Write-Host "Running quick Ethernet gate before capture loop..."
    python scripts\ethernet_low_speed_test.py --ping-count $PingCount --csr-loops $CsrLoops --bind-port $Port
    if ($LASTEXITCODE -ne 0) {
        throw "Ethernet gate failed; not starting HPI capture loop"
    }
    Write-Host ""
}

$argsList = @(
    "scripts\hpi_cycle_loop.py",
    "--start-server",
    "--port", "$Port",
    "--mode", $Mode,
    "--port-name", $HpiPort,
    "--test-addr", $TestAddr,
    "--test-data", $TestData,
    "--count", "$Count",
    "--period-ms", "$PeriodMs"
)

if (-not $NoReset) {
    $argsList += "--reset"
}

Write-Host "Starting HPI cycle loop. Press Ctrl+C after the external analyzer has captured enough samples."
Write-Host "Logging to $Log"
Write-Host ""

python @argsList 2>&1 | Tee-Object -FilePath $Log
if ($LASTEXITCODE -ne 0) {
    throw "HPI capture loop exited with code $LASTEXITCODE"
}
