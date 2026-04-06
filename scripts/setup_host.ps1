# --- Setup Host Dependencies for LiteX/DE2-115 ---

param (
    [switch]$NonInteractive
)

$LogFile = "setup_host.log"
Start-Transcript -Path $LogFile -Append

$QuartusVersion = "22.1std"
$DefaultQuartusPath = "C:\intelFPGA_lite\$QuartusVersion"
$QuartusUrl = "https://downloads.intel.com/akdlm/software/acdsinst/22.1std.2/922/ib_tar/Quartus-Lite-22.1std.2.922-windows.tar"

function Refresh-Env {
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
}

function Start-Docker {
    $dockerApp = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if (Test-Path $dockerApp) {
        if (-not (Get-Process "Docker Desktop" -ErrorAction SilentlyContinue)) {
            Write-Host "Starting Docker Desktop app..." -ForegroundColor Yellow
            Start-Process $dockerApp
            # Give it some time to start the engine
            Write-Host "Waiting for Docker daemon to initialize (this may take 30-60 seconds)..." -ForegroundColor Gray
            for ($i=0; $i -lt 30; $i++) {
                if (& "docker" info 2>$null) {
                    Write-Host "[OK] Docker daemon is running." -ForegroundColor Green
                    return $true
                }
                Start-Sleep -Seconds 2
            }
            Write-Warning "Docker Desktop started, but the engine is still initializing or needs a REBOOT."
        } else {
            if (& "docker" info 2>$null) {
                Write-Host "[OK] Docker is running." -ForegroundColor Green
                return $true
            } else {
                Write-Warning "Docker Desktop app is running, but the engine is not responding. A REBOOT is likely required."
            }
        }
    }
    return $false
}

function Check-Admin {
    $currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Check-Command {
    param ($CommandName)
    $where = Get-Command $CommandName -ErrorAction SilentlyContinue
    return $null -ne $where
}

function Get-UserConsent {
    param ($Message)
    if ($NonInteractive) {
        Write-Host "$Message (NonInteractive: Auto-approving 'Y')" -ForegroundColor Gray
        return $true
    }
    Write-Host "$Message" -ForegroundColor Yellow
    $response = Read-Host "Enter 'Y' to proceed or 'N' to skip"
    return $response -eq 'Y'
}

try {
    if (-not (Check-Admin)) {
        Write-Warning "Running as non-Administrator. Some automated installations (drivers, software) will fail."
    }

    # Refresh path in case Docker was just installed
    Refresh-Env

    Write-Host "--- Checking Host Prerequisites ---" -ForegroundColor Cyan

    # 1. Docker
    if (Check-Command "docker") {
        Start-Docker | Out-Null
    } else {
        Write-Host "[FAIL] Docker Desktop not found." -ForegroundColor Red
        if (Get-UserConsent "Would you like to automatically download and install Docker Desktop with WSL2 backend? (~600MB download)") {
            powershell -ExecutionPolicy Bypass -File .\scripts\install_docker.ps1 -ErrorAction SilentlyContinue
            # Refresh path after install
            Refresh-Env
            Start-Docker | Out-Null
        } else {
            Write-Host "Skipping installation. Please install manually: https://www.docker.com/products/docker-desktop" -ForegroundColor Gray
        }
    }

    # 2. Git and GitHub CLI
    $missingTools = @()
    if (-not (Check-Command "git")) { $missingTools += "Git" }
    if (-not (Check-Command "gh")) { $missingTools += "GitHub CLI" }

    if ($missingTools.Count -gt 0) {
        Write-Host "[FAIL] Missing tools: $($missingTools -join ", ")." -ForegroundColor Red
        if (Get-UserConsent "Would you like to automatically install them via winget?") {
            # In NonInteractive mode, we don't want to exit if this fails (likely due to non-admin)
            & powershell -ExecutionPolicy Bypass -File .\scripts\install_software.ps1 2>$null
            Refresh-Env
        }
    } else {
        Write-Host "[OK] Git and GitHub CLI are installed." -ForegroundColor Green
    }

    # 3. Quartus Prime Lite
    if (Test-Path "$DefaultQuartusPath\quartus\bin64\quartus_pgm.exe") {
        Write-Host "[OK] Quartus Prime Lite $QuartusVersion found at $DefaultQuartusPath." -ForegroundColor Green
    } else {
        Write-Host "[FAIL] Quartus Prime Lite not found at $DefaultQuartusPath." -ForegroundColor Red
        if (Get-UserConsent "Would you like to automatically download and install Quartus Lite and Cyclone IV support? (~2GB download, ~10GB space)") {
            & powershell -ExecutionPolicy Bypass -File .\scripts\install_software.ps1 2>$null
        } else {
            Write-Host "Skipping installation. Please install manually: $QuartusUrl" -ForegroundColor Gray
        }
    }

    # 4. USB-Blaster Drivers
    $drivers = pnputil /enum-devices /class "USB" | Select-String "Altera USB-Blaster"
    if ($null -ne $drivers) {
        Write-Host "[OK] USB-Blaster drivers are active." -ForegroundColor Green
    } else {
        Write-Host "[WARN] USB-Blaster not detected or driver not installed." -ForegroundColor Yellow
        if (Get-UserConsent "Would you like to attempt to install USB-Blaster drivers from the Quartus directory?") {
            if (Test-Path "$DefaultQuartusPath\quartus\drivers\usb-blaster\usbblstr.inf") {
                & pnputil.exe /add-driver "$DefaultQuartusPath\quartus\drivers\usb-blaster\usbblstr.inf" /install 2>$null
            } else {
                Write-Warning "Driver file not found. Install Quartus first."
            }
        }
    }

    Write-Host "`n--- Host Check Complete ---" -ForegroundColor Cyan
    exit 0
} finally {
    Stop-Transcript
}
