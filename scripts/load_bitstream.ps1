# --- Load Bitstream to Terasic DE2-115 via USB-Blaster ---

$LogFile = "load_bitstream.log"
Start-Transcript -Path $LogFile -Append

$QuartusPath = "C:\intelFPGA_lite\22.1std\quartus\bin64" # Adjust if necessary
$ProjectDir = Get-Location
$GatewareDir = "$ProjectDir\build\terasic_de2_115\gateware"

try {
    if (-not (Test-Path $GatewareDir)) {
        Write-Error "Gateware directory not found: $GatewareDir"
        exit 1
    }

    # Auto-detect SOF file
    $SofFile = Get-ChildItem -Path $GatewareDir -Filter "*.sof" | Select-Object -First 1
    if ($null -eq $SofFile) {
        Write-Error "Bitstream file (.sof) not found in $GatewareDir. Did the synthesis finish?"
        exit 1
    }

    Write-Host "--- Programming DE2-115 via USB-Blaster (!($SofFile.Name)) ---" -ForegroundColor Cyan

    # Set path for quartus_pgm
    $env:PATH += ";$QuartusPath"

    # Run the programmer
    # -m jtag: Use JTAG mode
    # -o "p;file.sof": Program action
    quartus_pgm.exe -m jtag -o "p;$($SofFile.FullName)"

    if ($LASTEXITCODE -eq 0) {
        Write-Host "--- Success: DE2-115 Programmed ---" -ForegroundColor Green
    } else {
        Write-Error "Programming failed. Check board connection and power."
        exit 1
    }
} finally {
    Stop-Transcript
}
