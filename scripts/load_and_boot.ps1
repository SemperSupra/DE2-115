$QuartusPath = "C:\intelFPGA_lite\22.1std\quartus\bin64"
$env:PATH += ";$QuartusPath"

Write-Host "Programming FPGA..."
quartus_pgm.exe -m jtag -o "p;build\terasic_de2_115\gateware\de2_115_vga_platform.sof"
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "Starting serial console..."
litex_term COM3
