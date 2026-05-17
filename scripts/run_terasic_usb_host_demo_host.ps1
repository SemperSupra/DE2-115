param(
    [string]$QuartusRoot = "C:\intelFPGA_lite\22.1std\quartus",
    [string]$NiosRoot = "C:\intelFPGA_lite\22.1std\nios2eds",
    [string]$DemoDir = "DE2_115_demonstrations\DE2_115_NIOS_HOST_MOUSE_VGA",
    [string]$Cable = "USB-Blaster [USB-0]",
    [int]$Device = 1,
    [int]$Instance = 0,
    [int]$TerminalSeconds = 0,
    [switch]$SkipProgram,
    [switch]$RestoreCandidate,
    [string]$RestoreSof = "artifacts\de2_115_vga_platform_hpi_pad_capture_033626D0_20260517.sof",
    [string]$OutDir = "artifacts\terasic_host_demo"
)

$ErrorActionPreference = "Stop"

function Resolve-RepoPath {
    param([string]$Path)
    if ([System.IO.Path]::IsPathRooted($Path)) {
        return $Path
    }
    return (Join-Path (Get-Location) $Path)
}

function Require-File {
    param([string]$Path, [string]$Label)
    if (!(Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "$Label not found: $Path"
    }
}

$quartusPgm = Join-Path $QuartusRoot "bin64\quartus_pgm.exe"
$gdbServer = Join-Path $QuartusRoot "bin64\nios2-gdb-server.exe"
$terminal = Join-Path $QuartusRoot "bin64\nios2-terminal.exe"
$objcopy = Join-Path $NiosRoot "bin\gnu\H-x86_64-mingw32\bin\nios2-elf-objcopy.exe"

$demoRoot = Resolve-RepoPath $DemoDir
$sof = Join-Path $demoRoot "DE2_115_NIOS_HOST_MOUSE_VGA.sof"
$elf = Join-Path $demoRoot "software\DE2_115_NIOS_HOST_MOUSE_VGA\DE2_115_NIOS_HOST_MOUSE_VGA.elf"
$outRoot = Resolve-RepoPath $OutDir
$srec = Join-Path $outRoot "DE2_115_NIOS_HOST_MOUSE_VGA.srec"
$restoreSofPath = Resolve-RepoPath $RestoreSof

Require-File $quartusPgm "Quartus programmer"
Require-File $gdbServer "Nios GDB server"
Require-File $terminal "Nios terminal"
Require-File $objcopy "Nios objcopy"
Require-File $sof "Terasic SOF"
Require-File $elf "Terasic ELF"

New-Item -ItemType Directory -Force -Path $outRoot | Out-Null

Write-Host "Converting ELF to SREC..."
& $objcopy -O srec $elf $srec
Require-File $srec "Generated SREC"

if (!$SkipProgram) {
    Write-Host "Programming Terasic SOF..."
    & $quartusPgm -m jtag -o "p;$sof"
}

Write-Host "Downloading and starting Terasic Nios application..."
& $gdbServer -c $Cable -d $Device -i $Instance --accept-bad-sysid -r -g $srec

if ($TerminalSeconds -gt 0) {
    Write-Host "Capturing JTAG UART for $TerminalSeconds seconds..."
    & $terminal -c $Cable -d $Device -i $Instance --flush "--quit-after=$TerminalSeconds"
}

if ($RestoreCandidate) {
    Require-File $restoreSofPath "Restore SOF"
    Write-Host "Restoring candidate LiteX image..."
    & $quartusPgm -m jtag -o "p;$restoreSofPath"
}
