param(
    [int]$Port = 1235,
    [string]$Log = "local_artifacts\hpi_reset_timing_sweep.log",
    [string]$ResetLows = "0.01,0.1,0.5,2.0",
    [string]$ResetHighs = "0.1,0.5,2.0,5.0",
    [string]$AccessCycles = "10,32,63",
    [string]$SampleOffsets = "2,8,16",
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

Set-Content -Path $Log -Value "HPI reset timing sweep $(Get-Date -Format s)"

Write-Host "HPI reset timing sweep"
Write-Host "Purpose: test whether CY7C67200 HPI readback appears after longer reset low or post-release boot settle windows."

if (-not $SkipEthernetGate) {
    Invoke-Logged "Ethernet gate" {
        python scripts\ethernet_low_speed_test.py --ping-count 20 --csr-loops 128 --bind-port $Port
    }
}

Invoke-Logged "HPI reset timing sweep" {
    python scripts\hpi_reset_timing_sweep.py --start-server --port $Port --reset-lows $ResetLows --reset-highs $ResetHighs --access-cycles $AccessCycles --sample-offsets $SampleOffsets
}

Write-Host ""
Write-Host "Reset timing sweep log: $Log"
