param(
    [int]$Port = 1235,
    [int]$WaitMs = 1000,
    [int]$Reads = 2,
    [int]$SweepCount = 4,
    [string]$Log = "local_artifacts\hpi_no_analyzer_contrast.log",
    [switch]$SkipEthernetGate,
    [switch]$SkipActiveCapture
)

$ErrorActionPreference = "Stop"
if ($PSVersionTable.PSVersion.Major -ge 7) {
    $PSNativeCommandUseErrorActionPreference = $false
}
$PSDefaultParameterValues["Out-File:Encoding"] = "ascii"
$PSDefaultParameterValues["Set-Content:Encoding"] = "ascii"

$quartusStp = "C:\intelFPGA_lite\22.1std\quartus\bin64\quartus_stp.exe"
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

function Capture-HpiProbe {
    param(
        [string]$Label,
        [int]$Mode,
        [int]$CaptureWaitMs = $WaitMs,
        [int]$CaptureReads = $Reads
    )

    Invoke-Logged $Label {
        & $quartusStp -t scripts\read_source_probe.tcl HPI0 $Mode $CaptureWaitMs $CaptureReads
    }

    $lines = Get-Content $Log
    $probeLine = $lines | Where-Object { $_ -match '^probe_data\[\d+\]=' } | Select-Object -Last 1
    if ($probeLine) {
        $probeHex = ($probeLine -split "=", 2)[1].Trim()
        Invoke-Logged "$Label decoded" {
            python scripts\decode_hpi_probe.py $probeHex
        }
    } else {
        throw "No probe_data line found for $Label"
    }
}

Set-Content -Path $Log -Value "HPI no-analyzer contrast $(Get-Date -Format s)"

Write-Host "HPI no-analyzer contrast"
Write-Host "Assumption: the currently programmed image has OTG_DATA weak pull-ups enabled."
Write-Host "Expected split: idle/reset-low DATA should read high if the FPGA input path is sane; active HPI reads are the suspect condition."

if (-not $SkipEthernetGate) {
    Invoke-Logged "Ethernet gate" {
        python scripts\ethernet_low_speed_test.py --ping-count 20 --csr-loops 128 --bind-port $Port
    }
}

Capture-HpiProbe "Idle/released source-probe" 0

Invoke-Logged "Force CY reset low" {
    python scripts\hpi_set_reset.py --start-server --port $Port --rst-n 0
}

Capture-HpiProbe "Reset-low source-probe" 0

Invoke-Logged "Release CY reset" {
    python scripts\hpi_set_reset.py --start-server --port $Port --rst-n 1
}

foreach ($name in @("data", "mailbox", "status", "address")) {
    Invoke-Logged "Sequential HPI read sweep: $name" {
        python scripts\hpi_cycle_loop.py --start-server --port $Port --mode read --port-name $name --count $SweepCount --period-ms 50 --reset
    }
}

if (-not $SkipActiveCapture) {
    Invoke-Logged "Active DATA-read source-probe capture" {
        powershell -ExecutionPolicy Bypass -File .\scripts\capture_hpi_source_probe.ps1 -Output local_artifacts\hpi_no_analyzer_active_read_source_probe.txt -VcdOutput local_artifacts\hpi_no_analyzer_active_read_capture.vcd -Mode 1 -WaitMs 8000 -Reads 3 -Port $Port
    }
}

Write-Host ""
Write-Host "Contrast log: $Log"
