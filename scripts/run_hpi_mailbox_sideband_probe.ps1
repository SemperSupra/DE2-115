param(
    [int]$Port = 1235,
    [string]$Log = "local_artifacts\hpi_mailbox_sideband_probe.log",
    [string]$Values = "0xfa50,0xce00,0x0000,0xffff",
    [int]$WaitMs = 1000,
    [int]$Reads = 2,
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

function Capture-HpiProbe {
    param(
        [string]$Label,
        [int]$Mode
    )

    Invoke-Logged $Label {
        & $quartusStp -t scripts\read_source_probe.tcl HPI0 $Mode $WaitMs $Reads
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

function Capture-HpiProbeDuring {
    param(
        [string]$Label,
        [int]$Mode,
        [scriptblock]$Command
    )

    Write-Host ""
    Write-Host "=== $Label ==="
    "=== $Label ===" | Tee-Object -FilePath $Log -Append | Out-Null

    $safeLabel = ($Label -replace '[^A-Za-z0-9_.-]', '_')
    $probeStdout = Join-Path $logDir "$safeLabel.stp.out"
    $probeStderr = Join-Path $logDir "$safeLabel.stp.err"
    Remove-Item -Force -ErrorAction SilentlyContinue $probeStdout, $probeStderr

    $captureWaitMs = [Math]::Max($WaitMs, 5000)
    $probe = Start-Process -FilePath $quartusStp `
        -ArgumentList @("-t", "scripts\read_source_probe.tcl", "HPI0", "$Mode", "$captureWaitMs", "$Reads") `
        -RedirectStandardOutput $probeStdout `
        -RedirectStandardError $probeStderr `
        -PassThru `
        -WindowStyle Hidden

    Start-Sleep -Milliseconds 200

    $oldErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & $Command 2>&1 | Tee-Object -FilePath $Log -Append
        $cmdExitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $oldErrorActionPreference
    }
    if ($cmdExitCode -ne 0) {
        throw "$Label trigger command failed with exit code $cmdExitCode"
    }

    $probe.WaitForExit()
    $probe.Refresh()

    $stdout = if (Test-Path $probeStdout) { Get-Content $probeStdout } else { @() }
    $stderr = if (Test-Path $probeStderr) { Get-Content $probeStderr } else { @() }
    $stdout | Tee-Object -FilePath $Log -Append
    if ($stderr.Count -gt 0) {
        $stderr | Tee-Object -FilePath $Log -Append
    }

    $probeExitCode = $probe.ExitCode
    if ($null -eq $probeExitCode) {
        $probeExitCode = 0
    }
    if ($probeExitCode -ne 0) {
        throw "$Label HPI0 source/probe failed with exit code $probeExitCode"
    }

    $probeLine = $stdout | Where-Object { $_ -match '^probe_data\[\d+\]=' } | Select-Object -Last 1
    if (-not $probeLine) {
        throw "No probe_data line found for $Label"
    }
    $probeHex = ($probeLine -split "=", 2)[1].Trim()
    Invoke-Logged "$Label decoded" {
        python scripts\decode_hpi_probe.py $probeHex
    }
}

Set-Content -Path $Log -Value "HPI mailbox sideband probe $(Get-Date -Format s)"

Write-Host "HPI mailbox sideband probe"
Write-Host "Purpose: check whether mailbox writes produce any observable INT/DREQ/idle-sideband reaction while HPI reads stay zero."

if (-not $SkipEthernetGate) {
    Invoke-Logged "Ethernet gate" {
        python scripts\ethernet_low_speed_test.py --ping-count 20 --csr-loops 128 --bind-port $Port
    }
}

Capture-HpiProbe "Baseline idle HPI0" 0

Invoke-Logged "Mailbox writes and readback" {
    python scripts\hpi_mailbox_sideband_probe.py --start-server --port $Port --reset --values $Values
}

Capture-HpiProbe "Post-mailbox idle HPI0" 0
Capture-HpiProbeDuring "Mailbox write-window HPI0" 6 {
    python scripts\hpi_mailbox_sideband_probe.py --start-server --port $Port --values $Values --pre-write-delay 2.0
}

Write-Host ""
Write-Host "Mailbox sideband log: $Log"
