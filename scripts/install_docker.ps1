# --- Automated Docker Desktop Installer for Windows ---
# This script downloads and installs Docker Desktop with WSL2 backend support.

$LogFile = "install_docker.log"
Start-Transcript -Path $LogFile -Append

$DockerUrl = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
$TempDir = "$env:TEMP\DockerInstall"
$InstallerPath = "$TempDir\DockerDesktopInstaller.exe"

function Check-Admin {
    $currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
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
        Write-Error "This script must be run as an Administrator to install Docker Desktop."
        exit 1
    }

    Write-Host "--- Automated Docker Desktop Installation ---" -ForegroundColor Cyan

    # 1. Create Temp Directory
    if (-not (Test-Path $TempDir)) { New-Item -ItemType Directory -Path $TempDir | Out-Null }

    # 2. Download Docker Installer
    if (-not (Test-Path $InstallerPath)) {
        Write-Host "[1/2] Downloading Docker Desktop Installer (~600MB)..." -ForegroundColor Yellow
        Start-ObservableDownload -Source $DockerUrl -Destination $InstallerPath -DisplayName "Docker Desktop"
    }

    # 3. Enable WSL2 and VirtualMachinePlatform if not already enabled
    Write-Host "Ensuring WSL2 and Virtual Machine Platform are enabled..." -ForegroundColor Gray
    dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
    dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

    # 4. Silent Installation
    Write-Host "[2/2] Installing Docker Desktop (Silent Mode)..." -ForegroundColor Yellow
    Write-Host "Note: This may prompt for a reboot after completion." -ForegroundColor Gray

    # Flags:
    # --quiet: No UI
    # --accept-license: Accept the agreement
    # --always-run-service: Start service automatically
    # --backend=wsl-2: Use WSL2 backend
    $installArgs = "install --quiet --accept-license --always-run-service --backend=wsl-2"

    $process = Start-Process -FilePath $InstallerPath -ArgumentList $installArgs -Wait -PassThru

    if ($process.ExitCode -eq 0) {
        Write-Host "[SUCCESS] Docker Desktop installed successfully." -ForegroundColor Green
        Write-Host "IMPORTANT: You MUST reboot your computer to complete the WSL2 and Docker setup." -ForegroundColor Red
    } elseif ($process.ExitCode -eq 3010) {
        Write-Host "[SUCCESS] Docker Desktop installed, but a REBOOT is required." -ForegroundColor Yellow
    } else {
        Write-Error "Docker installation failed with exit code $($process.ExitCode)."
        exit 1
    }

    Write-Host "`n--- Installation Complete ---" -ForegroundColor Cyan
} finally {
    Stop-Transcript
}
