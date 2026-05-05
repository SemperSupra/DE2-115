param(
    [int]$Port = 1235,
    [string]$Log = "local_artifacts\hpi_reset_release_live_sideband_watch.log",
    [int]$WaitMs = 50,
    [int]$Reads = 80,
    [int]$PreReleaseMs = 300,
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

Set-Content -Path $Log -Value "HPI reset-release live sideband watch $(Get-Date -Format s)"

Write-Host "HPI reset-release live sideband watch"
Write-Host "Purpose: keep HPI0 source/probe running across reset release and sample live sidebands every ~100ms."

if (-not $SkipEthernetGate) {
    Invoke-Logged "Ethernet gate" {
        python scripts\ethernet_low_speed_test.py --ping-count 20 --csr-loops 128 --bind-port $Port
    }
}

Invoke-Logged "Force CY reset low" {
    python scripts\hpi_set_reset.py --start-server --port $Port --rst-n 0
}

$safeLabel = "Reset_release_live_HPI0"
$probeStdout = Join-Path $logDir "$safeLabel.stp.out"
$probeStderr = Join-Path $logDir "$safeLabel.stp.err"
Remove-Item -Force -ErrorAction SilentlyContinue $probeStdout, $probeStderr

Write-Host ""
Write-Host "=== Arm live HPI0 source/probe ==="
"=== Arm live HPI0 source/probe ===" | Tee-Object -FilePath $Log -Append | Out-Null
$probe = Start-Process -FilePath $quartusStp `
    -ArgumentList @("-t", "scripts\read_source_probe.tcl", "HPI0", "0", "$WaitMs", "$Reads") `
    -RedirectStandardOutput $probeStdout `
    -RedirectStandardError $probeStderr `
    -PassThru `
    -WindowStyle Hidden

Start-Sleep -Milliseconds $PreReleaseMs

Invoke-Logged "Release CY reset while probe is live" {
    python scripts\hpi_set_reset.py --start-server --port $Port --rst-n 1
}

$probe.WaitForExit()
$probe.Refresh()
$probeExitCode = $probe.ExitCode
if ($null -eq $probeExitCode) {
    $probeExitCode = 0
}

$stdout = if (Test-Path $probeStdout) { Get-Content $probeStdout } else { @() }
$stderr = if (Test-Path $probeStderr) { Get-Content $probeStderr } else { @() }
$stdout | Tee-Object -FilePath $Log -Append
if ($stderr.Count -gt 0) {
    $stderr | Tee-Object -FilePath $Log -Append
}

if ($probeExitCode -ne 0) {
    throw "Live HPI0 source/probe failed with exit code $probeExitCode"
}

$probeLines = $stdout | Where-Object { $_ -match '^probe_data\[\d+\]=' }
if (-not $probeLines) {
    throw "No probe_data lines found in live watch"
}

foreach ($probeLine in $probeLines) {
    $label = ($probeLine -split "=", 2)[0]
    $probeHex = ($probeLine -split "=", 2)[1].Trim()
    Invoke-Logged "$label decoded" {
        python scripts\decode_hpi_probe.py $probeHex
    }
}

Write-Host ""
Write-Host "Live reset-release sideband watch log: $Log"
