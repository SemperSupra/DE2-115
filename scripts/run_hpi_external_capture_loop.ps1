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
    [string]$Log = "local_artifacts\hpi_external_capture_loop.log",
    [string]$PinMap = "local_artifacts\hpi_external_analyzer_channels.csv"
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
$pinMapDir = Split-Path -Parent $PinMap
if ($pinMapDir) {
    New-Item -ItemType Directory -Force -Path $pinMapDir | Out-Null
}

$capturePins = @(
    [pscustomobject]@{ Signal = "OTG_DATA[0]";  FpgaPin = "J6"; Direction = "bidir"; Notes = "HPI data bit 0" },
    [pscustomobject]@{ Signal = "OTG_DATA[1]";  FpgaPin = "K4"; Direction = "bidir"; Notes = "HPI data bit 1" },
    [pscustomobject]@{ Signal = "OTG_DATA[2]";  FpgaPin = "J5"; Direction = "bidir"; Notes = "HPI data bit 2" },
    [pscustomobject]@{ Signal = "OTG_DATA[3]";  FpgaPin = "K3"; Direction = "bidir"; Notes = "HPI data bit 3" },
    [pscustomobject]@{ Signal = "OTG_DATA[4]";  FpgaPin = "J4"; Direction = "bidir"; Notes = "HPI data bit 4" },
    [pscustomobject]@{ Signal = "OTG_DATA[5]";  FpgaPin = "J3"; Direction = "bidir"; Notes = "HPI data bit 5" },
    [pscustomobject]@{ Signal = "OTG_DATA[6]";  FpgaPin = "J7"; Direction = "bidir"; Notes = "HPI data bit 6" },
    [pscustomobject]@{ Signal = "OTG_DATA[7]";  FpgaPin = "H6"; Direction = "bidir"; Notes = "HPI data bit 7" },
    [pscustomobject]@{ Signal = "OTG_DATA[8]";  FpgaPin = "H3"; Direction = "bidir"; Notes = "HPI data bit 8" },
    [pscustomobject]@{ Signal = "OTG_DATA[9]";  FpgaPin = "H4"; Direction = "bidir"; Notes = "HPI data bit 9" },
    [pscustomobject]@{ Signal = "OTG_DATA[10]"; FpgaPin = "G1"; Direction = "bidir"; Notes = "HPI data bit 10" },
    [pscustomobject]@{ Signal = "OTG_DATA[11]"; FpgaPin = "G2"; Direction = "bidir"; Notes = "HPI data bit 11" },
    [pscustomobject]@{ Signal = "OTG_DATA[12]"; FpgaPin = "G3"; Direction = "bidir"; Notes = "HPI data bit 12" },
    [pscustomobject]@{ Signal = "OTG_DATA[13]"; FpgaPin = "F1"; Direction = "bidir"; Notes = "HPI data bit 13" },
    [pscustomobject]@{ Signal = "OTG_DATA[14]"; FpgaPin = "F3"; Direction = "bidir"; Notes = "HPI data bit 14" },
    [pscustomobject]@{ Signal = "OTG_DATA[15]"; FpgaPin = "G4"; Direction = "bidir"; Notes = "HPI data bit 15" },
    [pscustomobject]@{ Signal = "OTG_ADDR[0]";  FpgaPin = "H7"; Direction = "out";   Notes = "HPI address bit 0" },
    [pscustomobject]@{ Signal = "OTG_ADDR[1]";  FpgaPin = "C3"; Direction = "out";   Notes = "HPI address bit 1" },
    [pscustomobject]@{ Signal = "OTG_CS_N";     FpgaPin = "A3"; Direction = "out";   Notes = "Trigger qualifier, active low" },
    [pscustomobject]@{ Signal = "OTG_RD_N";     FpgaPin = "B3"; Direction = "out";   Notes = "Read trigger, falling edge" },
    [pscustomobject]@{ Signal = "OTG_WR_N";     FpgaPin = "A4"; Direction = "out";   Notes = "Write trigger, falling edge" },
    [pscustomobject]@{ Signal = "OTG_RST_N";    FpgaPin = "C5"; Direction = "out";   Notes = "CY reset, active low" },
    [pscustomobject]@{ Signal = "OTG_INT0";     FpgaPin = "D5"; Direction = "in";    Notes = "Sideband interrupt input" },
    [pscustomobject]@{ Signal = "OTG_INT1";     FpgaPin = "E5"; Direction = "in";    Notes = "Bridge interrupt input" },
    [pscustomobject]@{ Signal = "OTG_DREQ";     FpgaPin = "J1"; Direction = "in";    Notes = "DREQ input" }
)
$capturePins | Export-Csv -Path $PinMap -NoTypeInformation

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
Write-Host "  Optional sideband: OTG_INT0, OTG_INT1, OTG_DREQ"
Write-Host "Pin map CSV : $PinMap"
Write-Host ""
Write-Host "Analyzer channel labels:"
$capturePins | ForEach-Object {
    Write-Host ("  {0,-13} FPGA {1,-2} {2,-5} {3}" -f $_.Signal, $_.FpgaPin, $_.Direction, $_.Notes)
}
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
