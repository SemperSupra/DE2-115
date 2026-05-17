param(
    [string]$Output = "local_artifacts\hpi_source_probe_capture.txt",
    [string]$VcdOutput = "local_artifacts\hpi_read_capture_for_source_probe.vcd",
    [int]$Mode = 1,
    [int]$WaitMs = 8000,
    [int]$Reads = 3,
    [int]$Port = 1235
)

$ErrorActionPreference = "Stop"
$quartusStp = "C:\intelFPGA_lite\22.1std\quartus\bin64\quartus_stp.exe"
$outDir = Split-Path -Parent $Output
if ($outDir) {
    New-Item -ItemType Directory -Force -Path $outDir | Out-Null
}

$probeStdout = "$Output.stp.out"
$probeStderr = "$Output.stp.err"
Remove-Item -Force -ErrorAction SilentlyContinue $Output, $probeStdout, $probeStderr

Write-Host "Arming HPI0 source/probe read-data trigger..."
$probe = Start-Process -FilePath $quartusStp `
    -ArgumentList @("-t", "scripts\read_source_probe.tcl", "HPI0", "$Mode", "$WaitMs", "$Reads") `
    -RedirectStandardOutput $probeStdout `
    -RedirectStandardError $probeStderr `
    -PassThru `
    -WindowStyle Hidden

Start-Sleep -Seconds 2

Write-Host "Triggering CY RAM write/read transaction..."
python scripts\hpi_capture_combined.py --start-server --port $Port --output $VcdOutput

$probe.WaitForExit()
$probe.Refresh()

$stdout = if (Test-Path $probeStdout) { Get-Content $probeStdout } else { @() }
$stderr = if (Test-Path $probeStderr) { Get-Content $probeStderr } else { @() }

$stdout | Tee-Object -FilePath $Output
if ($stderr.Count -gt 0) {
    $stderr | Tee-Object -FilePath $Output -Append
}

$exitCode = $probe.ExitCode
if ($null -eq $exitCode) {
    $exitCode = 0
}
if ($exitCode -ne 0) {
    throw "HPI0 source/probe capture failed with exit code $($probe.ExitCode)"
}

$probeLine = $stdout | Where-Object { $_ -match '^probe_data\[\d+\]=' } | Select-Object -Last 1
if (-not $probeLine) {
    throw "No probe_data line found in $Output"
}

$probeHex = ($probeLine -split '=', 2)[1].Trim()
Write-Host "Decoded final HPI0 probe sample:"
python scripts\decode_hpi_probe.py $probeHex | Tee-Object -FilePath $Output -Append

Write-Host "HPI_SOURCE_PROBE_CAPTURE $Output"
