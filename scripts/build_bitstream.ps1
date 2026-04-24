# --- Build Bitstream using Quartus on Host (Windows) ---

$QuartusPath = "C:\intelFPGA_lite\22.1std\quartus\bin64"
$ProjectDir = Get-Location
$GatewareDir = "$ProjectDir\build\terasic_de2_115\gateware"
$ProjectName = "de2_115_vga_platform"

$env:PATH += ";$QuartusPath"

Push-Location $GatewareDir

try {
    Write-Host "--- Stage 1: Analysis & Synthesis ---" -ForegroundColor Cyan
    quartus_map.exe $ProjectName
    if ($LASTEXITCODE -ne 0) { throw "quartus_map failed" }

    Write-Host "--- Stage 2: Fitter (Place & Route) ---" -ForegroundColor Cyan
    quartus_fit.exe $ProjectName
    if ($LASTEXITCODE -ne 0) { throw "quartus_fit failed" }

    Write-Host "--- Stage 3: Assembler (Generate Bitstream) ---" -ForegroundColor Cyan
    quartus_asm.exe $ProjectName
    if ($LASTEXITCODE -ne 0) { throw "quartus_asm failed" }

    Write-Host "--- Stage 4: Timing Analysis ---" -ForegroundColor Cyan
    quartus_sta.exe $ProjectName
    if ($LASTEXITCODE -ne 0) { throw "quartus_sta failed" }

    Write-Host "--- Success: Bitstream Generated ---" -ForegroundColor Green
}
catch {
    Write-Error $_
    exit 1
}
finally {
    Pop-Location
}
