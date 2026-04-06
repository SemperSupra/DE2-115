# --- Automated Software Installer for LiteX/DE2-115 ---
# This script downloads and installs Git, GitHub CLI, Intel Quartus Prime Lite 22.1std.2 and Cyclone IV support.

$LogFile = "install_software.log"
Start-Transcript -Path $LogFile -Append

$QuartusVersion = "22.1std.2"
$InstallDir = "C:\intelFPGA_lite\22.1std"
$TempDir = "$env:TEMP\QuartusInstall"

# Download URLs (Direct Links from Intel/Altera)
$CoreUrl = "https://downloads.intel.com/akdlm/software/acdsinst/22.1std.2/922/ib_installers/QuartusLiteSetup-22.1std.2.922-windows.exe"
$DeviceUrl = "https://downloads.intel.com/akdlm/software/acdsinst/22.1std.2/922/ib_installers/cyclone-22.1std.2.922.qdz"

$CoreFile = "$TempDir\QuartusLiteSetup.exe"
$DeviceFile = "$TempDir\cyclone-22.1std.2.922.qdz"

function Check-Admin {
    $currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Refresh-Env {
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
}

function Start-ObservableDownload {
    param ($Source, $Destination, $DisplayName)
    Write-Host "Starting download: $DisplayName" -ForegroundColor Cyan
    $job = Start-BitsTransfer -Source $Source -Destination $Destination -DisplayName $DisplayName -Asynchronous
    $lastPercent = -1
    while ($job.State -eq "Transferring" -or $job.State -eq "Connecting") {
        if ($job.BytesTotal -gt 0) {
            $percent = [Math]::Round(($job.BytesTransferred / $job.BytesTotal) * 100)
            if ($percent -ne $lastPercent -and $percent % 5 -eq 0) {
                Write-Output "[PROGRESS] ${DisplayName}: $percent% ($([Math]::Round($job.BytesTransferred/1MB, 2))MB / $([Math]::Round($job.BytesTotal/1MB, 2))MB)"
                $lastPercent = $percent
            }
        }
        Start-Sleep -Seconds 2
    }
    if ($job.State -eq "Transferred") {
        Complete-BitsTransfer -BitsJob $job
        Write-Host "[SUCCESS] Downloaded $DisplayName" -ForegroundColor Green
    } else {
        Write-Error "Download failed: $($job.ErrorContext) - $($job.Description)"
        exit 1
    }
}

try {
    if (-not (Check-Admin)) {
        Write-Error "This script must be run as an Administrator to install software and drivers."
        exit 1
    }

    Write-Host "--- Automated Software Installation for DE2-115 ---" -ForegroundColor Cyan

    # 0. Install Git and GitHub CLI
    Write-Host "[0/3] Checking for Git and GitHub CLI..." -ForegroundColor Yellow

    # Function to install and configure tools via winget
    function Install-Tool {
        param ($CommandName, $WingetId, $ConfigScript)
        if (Get-Command $CommandName -ErrorAction SilentlyContinue) {
            Write-Host "[OK] $CommandName is already installed." -ForegroundColor Green
        } else {
            Write-Host "$CommandName not found. Attempting installation via winget..." -ForegroundColor Yellow
            if (Get-Command "winget" -ErrorAction SilentlyContinue) {
                winget install --id $WingetId -e --source winget --accept-package-agreements --accept-source-agreements
                Refresh-Env
                if (Get-Command $CommandName -ErrorAction SilentlyContinue) {
                    Write-Host "[SUCCESS] $CommandName installed." -ForegroundColor Green
                    if ($null -ne $ConfigScript) {
                        Write-Host "Configuring $CommandName..." -ForegroundColor Yellow
                        Invoke-Expression $ConfigScript
                    }
                } else {
                    Write-Warning "Failed to verify $CommandName installation. You may need to restart your terminal."
                }
            } else {
                Write-Error "winget is not available. Please install $CommandName manually."
            }
        }
    }

    Install-Tool "git" "Git.Git" "git config --global core.autocrlf true"
    Install-Tool "gh" "GitHub.cli" "gh config set editor notepad"

    # 1. Check if already installed
    if (Test-Path "$InstallDir\quartus\bin64\quartus_pgm.exe") {
        Write-Host "[OK] Quartus $QuartusVersion is already installed at $InstallDir." -ForegroundColor Green
    } else {
        # 2. Disk Space Check (~10GB)
        $drive = Get-PSDrive C
        $freeSpaceGB = $drive.Free / 1GB
        if ($freeSpaceGB -lt 10) {
            Write-Error "Not enough disk space on C: (Found $($freeSpaceGB)GB, need at least 10GB)."
            exit 1
        }

        # 3. Create Temp Directory
        if (-not (Test-Path $TempDir)) { New-Item -ItemType Directory -Path $TempDir | Out-Null }

        # 4. Download Files (using BITS with observability)
        Write-Host "[1/3] Downloading Quartus Core (~1.6GB) and Cyclone IV Support (~460MB)..." -ForegroundColor Yellow
        
        if (-not (Test-Path $CoreFile)) {
            Start-ObservableDownload -Source $CoreUrl -Destination $CoreFile -DisplayName "Quartus Core"
        }
        
        if (-not (Test-Path $DeviceFile)) {
            Start-ObservableDownload -Source $DeviceUrl -Destination $DeviceFile -DisplayName "Cyclone IV Support"
        }

        # 5. Unattended Installation
        Write-Host "[2/3] Installing Quartus Prime Lite (this will take 5-10 minutes)..." -ForegroundColor Yellow
        $installArgs = "--mode unattended --installdir $InstallDir --accept_eula 1"
        Start-Process -FilePath $CoreFile -ArgumentList $installArgs -Wait -NoNewWindow
        
        if (Test-Path "$InstallDir\quartus\bin64\quartus_pgm.exe") {
            Write-Host "[SUCCESS] Quartus installed successfully." -ForegroundColor Green
        } else {
            Write-Error "Quartus installation failed. Check logs in the temp directory."
            exit 1
        }
    }

    # 6. Install USB-Blaster Drivers
    Write-Host "[3/3] Installing USB-Blaster Drivers..." -ForegroundColor Yellow
    $driverPath = "$InstallDir\quartus\drivers\usb-blaster\usbblstr.inf"

    if (Test-Path $driverPath) {
        # Use pnputil to add and install the driver
        pnputil.exe /add-driver $driverPath /install
        Write-Host "[OK] USB-Blaster drivers installed." -ForegroundColor Green
    } else {
        Write-Warning "Driver file not found at $driverPath. You may need to install them manually from the Windows Device Manager."
    }

    Write-Host "`n--- Installation Complete ---" -ForegroundColor Cyan
    Write-Host "You can now run 'run.bat' to build your SoC."
} finally {
    Stop-Transcript
}
