param(
    [string]$Session = "signaltap\usb_hpi_capture.stp",
    [string]$Output = "local_artifacts\hpi_pin_capture.csv",
    [int]$WaitMs = 5000
)

$ErrorActionPreference = "Stop"

$quartusStp = "C:\intelFPGA_lite\22.1std\quartus\bin64\quartus_stp.exe"
$env:SIGNALTAP_WAIT_MS = [string]$WaitMs

$captureArgs = @(
    "-t", "scripts\run_capture.tcl",
    $Session,
    $Output,
    "log_1"
)

$capture = Start-Process -FilePath $quartusStp `
    -ArgumentList $captureArgs `
    -NoNewWindow `
    -PassThru `
    -RedirectStandardOutput "local_artifacts\hpi_pin_capture.stp.out" `
    -RedirectStandardError "local_artifacts\hpi_pin_capture.stp.err"

Start-Sleep -Seconds 3

python scripts\test_a0_stuck.py

$capture.WaitForExit()

Get-Content "local_artifacts\hpi_pin_capture.stp.out"
if (Test-Path "local_artifacts\hpi_pin_capture.stp.err") {
    Get-Content "local_artifacts\hpi_pin_capture.stp.err"
}

if ($capture.ExitCode -ne 0) {
    throw "SignalTap capture failed with exit code $($capture.ExitCode)"
}

Write-Host "HPI_PIN_CAPTURE $Output"
