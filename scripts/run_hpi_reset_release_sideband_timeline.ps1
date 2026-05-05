param(
    [int]$Port = 1235,
    [string]$Log = "local_artifacts\hpi_reset_release_sideband_timeline.log",
    [string]$DelaysMs = "0,10,50,100,250,500,1000,2000,5000",
    [int]$WaitMs = 100,
    [int]$Reads = 1,
    [switch]$SkipEthernetGate
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

function Capture-HpiIdle {
    param(
        [string]$Label
    )

    Invoke-Logged $Label {
        & $quartusStp -t scripts\read_source_probe.tcl HPI0 0 $WaitMs $Reads
    }

    $probeLine = Get-Content $Log | Where-Object { $_ -match '^probe_data\[\d+\]=' } | Select-Object -Last 1
    if (-not $probeLine) {
        throw "No probe_data line found for $Label"
    }

    $probeHex = ($probeLine -split "=", 2)[1].Trim()
    Invoke-Logged "$Label decoded" {
        python scripts\decode_hpi_probe.py $probeHex
    }
}

$delayValues = $DelaysMs.Split(",") | ForEach-Object {
    $text = $_.Trim()
    if ($text.Length -gt 0) {
        [int]$text
    }
}

Set-Content -Path $Log -Value "HPI reset-release sideband timeline $(Get-Date -Format s)"

Write-Host "HPI reset-release sideband timeline"
Write-Host "Purpose: sample HPI0 idle/sideband state before and after CY reset release without an external analyzer."

if (-not $SkipEthernetGate) {
    Invoke-Logged "Ethernet gate" {
        python scripts\ethernet_low_speed_test.py --ping-count 20 --csr-loops 128 --bind-port $Port
    }
}

Invoke-Logged "Force CY reset low" {
    python scripts\hpi_set_reset.py --start-server --port $Port --rst-n 0
}
Capture-HpiIdle "Reset-low HPI0 idle"

Invoke-Logged "Release CY reset" {
    python scripts\hpi_set_reset.py --start-server --port $Port --rst-n 1
}

foreach ($delayMs in $delayValues) {
    if ($delayMs -gt 0) {
        Start-Sleep -Milliseconds $delayMs
    }
    Capture-HpiIdle "Reset-release +${delayMs}ms HPI0 idle"
}

Write-Host ""
Write-Host "Reset-release sideband timeline log: $Log"
