param(
    [Parameter(Mandatory = $true)]
    [int]$Seed,

    [string]$ProjectRoot = "",
    [string]$QuartusBin = "C:\intelFPGA_lite\22.1std\quartus\bin64",
    [string]$BoardIp = "192.168.178.50",
    [int]$BindPort = 1235,
    [int]$PingCount = 50,
    [int]$CsrLoops = 512,
    [string]$RestoreSof = "",
    [switch]$RunCanonicalHpi
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path
}

if ([string]::IsNullOrWhiteSpace($RestoreSof)) {
    $RestoreSof = Join-Path $ProjectRoot "validation_images\de2_115_vga_platform_eth10_switchfix_validated_20260427.sof"
}

$gatewareDir = Join-Path $ProjectRoot "build\terasic_de2_115\gateware"
$qsf = Join-Path $gatewareDir "de2_115_vga_platform.qsf"
$sof = Join-Path $gatewareDir "de2_115_vga_platform.sof"
$quartusSh = Join-Path $QuartusBin "quartus_sh.exe"
$quartusPgm = Join-Path $QuartusBin "quartus_pgm.exe"
$artifactDir = Join-Path $ProjectRoot "artifacts\seed_candidates"
$jsonOut = Join-Path $artifactDir ("cy_hpi_ladder_seed_{0}.json" -f $Seed)

New-Item -ItemType Directory -Force -Path $artifactDir | Out-Null

if (!(Test-Path $qsf)) {
    throw "QSF not found: $qsf. Run scripts/build_soc.sh in the litex_builder container first."
}

$qsfLines = Get-Content -LiteralPath $qsf
$qsfLines = $qsfLines | Where-Object { $_ -notmatch '^\s*set_global_assignment\s+-name\s+SEED\s+' }
$qsfLines = $qsfLines | Where-Object { $_ -notmatch 'FAST_OUTPUT_REGISTER.*rgmii_eth1_tx_(data|ctl)' }
$qsfLines += "set_global_assignment -name SEED $Seed"
Set-Content -LiteralPath $qsf -Value $qsfLines -Encoding ASCII

Push-Location $gatewareDir
try {
    & $quartusSh --flow compile de2_115_vga_platform
    if ($LASTEXITCODE -ne 0) {
        throw "Quartus compile failed for seed $Seed"
    }
}
finally {
    Pop-Location
}

if (!(Test-Path $sof)) {
    throw "SOF not generated: $sof"
}

& $quartusPgm -m jtag -o "p;$sof"
if ($LASTEXITCODE -ne 0) {
    throw "Programming failed for seed $Seed"
}

try {
    & python (Join-Path $ProjectRoot "scripts\ethernet_low_speed_test.py") `
        --board-ip $BoardIp `
        --ping-count $PingCount `
        --csr-loops $CsrLoops `
        --bind-port $BindPort
    if ($LASTEXITCODE -ne 0) {
        throw "Ethernet gate failed for seed $Seed"
    }
}
catch {
    $failedSof = Join-Path $artifactDir ("de2_115_vga_platform_seed_{0}_failed_eth.sof" -f $Seed)
    Copy-Item -LiteralPath $sof -Destination $failedSof -Force
    if (Test-Path $RestoreSof) {
        & $quartusPgm -m jtag -o "p;$RestoreSof"
    }
    throw
}

$passedSof = Join-Path $artifactDir ("de2_115_vga_platform_seed_{0}_ethernet_pass.sof" -f $Seed)
Copy-Item -LiteralPath $sof -Destination $passedSof -Force

if ($RunCanonicalHpi) {
    & python (Join-Path $ProjectRoot "scripts\cy_hpi_ladder_probe.py") `
        --start-server `
        --port $BindPort `
        --timings spec,fast `
        --attempt-mailbox `
        --json-out $jsonOut
    if ($LASTEXITCODE -ne 0) {
        throw "Canonical HPI probe failed for seed $Seed"
    }
}

Write-Host "SEED_CANDIDATE_PASS seed=$Seed sof=$passedSof"
