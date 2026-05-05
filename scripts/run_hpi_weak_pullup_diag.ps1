param(
    [int]$EthPort = 1,
    [int]$Port = 1235,
    [int]$PingCount = 50,
    [int]$CsrLoops = 512,
    [string]$Log = "local_artifacts\hpi_weak_pullup_diag.log",
    [switch]$SkipBuild,
    [switch]$SkipCompile,
    [switch]$SkipProgram,
    [switch]$SkipEthernetGate
)

$ErrorActionPreference = "Stop"
if ($PSVersionTable.PSVersion.Major -ge 7) {
    $PSNativeCommandUseErrorActionPreference = $false
}
$PSDefaultParameterValues["Out-File:Encoding"] = "ascii"
$PSDefaultParameterValues["Set-Content:Encoding"] = "ascii"

$logDir = Split-Path -Parent $Log
if ($logDir) {
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
}

function Invoke-Logged {
    param(
        [string]$Label,
        [scriptblock]$Command
    )

    Write-Host ""
    Write-Host "=== $Label ==="
    "=== $Label ===" | Tee-Object -FilePath $Log -Append | Out-Null
    $oldErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & $Command 2>&1 | Tee-Object -FilePath $Log -Append
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $oldErrorActionPreference
    }
    if ($exitCode -ne 0) {
        throw "$Label failed with exit code $exitCode"
    }
}

Set-Content -Path $Log -Value "HPI weak-pullup diagnostic $(Get-Date -Format s)"

Write-Host "HPI weak-pullup diagnostic"
Write-Host "Purpose: distinguish released DATA bus from CY7C67200 actively driving zero."
Write-Host "Interpretation:"
Write-Host "  read/sample/cy == 0xffff or mostly high : CY is not driving DATA during reads."
Write-Host "  read/sample/cy == 0x0000                 : CY or board path is actively holding DATA low."
Write-Host ""

if (-not $SkipBuild) {
    Invoke-Logged "Build SoC with OTG_DATA weak pull-ups" {
        docker compose exec -T litex_builder /bin/bash -c "DE2_USB_HPI_WEAK_PULLUPS=1 /workspace/scripts/build_soc.sh $EthPort"
    }
}

if (-not $SkipCompile) {
    Invoke-Logged "Quartus compile" {
        C:\intelFPGA_lite\22.1std\quartus\bin64\quartus_sh.exe --flow compile de2_115_vga_platform
    }
}

if (-not $SkipProgram) {
    Invoke-Logged "Program weak-pullup image" {
        powershell -ExecutionPolicy Bypass -File .\scripts\load_bitstream.ps1
    }
}

if (-not $SkipEthernetGate) {
    Invoke-Logged "Ethernet gate" {
        python scripts\ethernet_low_speed_test.py --ping-count $PingCount --csr-loops $CsrLoops --bind-port $Port
    }
}

Invoke-Logged "HPI read/write diagnostic" {
    python scripts\hpi_cycle_loop.py --start-server --port $Port --mode rw --count 8 --period-ms 50 --reset
}

Write-Host ""
Write-Host "Diagnostic log: $Log"
