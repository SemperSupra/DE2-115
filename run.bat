@echo off
setlocal enabledelayedexpansion

:: --- Configuration ---
set DOCKER_IMAGE=litex_de2_115
set CONTAINER_NAME=litex_env
set QUARTUS_PATH=C:\intelFPGA_lite\22.1std\quartus\bin64
set LOG_FILE=build.log

:: Redirect all output to a log file while still showing it on screen
powershell -NoProfile -Command ^
  "$lines = @(" ^
  "'============================================================'," ^
  "'--- DE2-115 LiteX Automation Root [%DATE% %TIME%] ---'," ^
  "'============================================================'," ^
  "''" ^
  "); $lines | Out-File -FilePath '%LOG_FILE%' -Encoding utf8"

echo --- DE2-115 LiteX Automation Root ---
echo.

echo [0/4] Verifying host environment...
call :log_and_exec "powershell -ExecutionPolicy Bypass -File .\scripts\setup_host.ps1 -NonInteractive"
if %errorlevel% neq 0 (
    echo [ERROR] Host prerequisites not met. See %LOG_FILE% for details.
    exit /b 1
)

:: Ensure Docker is in PATH for this session
if exist "C:\Program Files\Docker\Docker\resources\bin" (
    set "PATH=%PATH%;C:\Program Files\Docker\Docker\resources\bin"
)

echo [1/4] Building/Updating Docker environment...
:: Use --progress plain for better logging in automation
call :log_and_exec "docker compose --progress plain build"
if %errorlevel% neq 0 (
    echo [ERROR] Docker build failed.
    exit /b 1
)

echo [2/4] Starting container...
call :log_and_exec "docker compose up -d"
if %errorlevel% neq 0 (
    echo [ERROR] Could not start container.
    exit /b 1
)

echo [3.1/4] Generating SoC Software headers (Pass 1)...
call :log_and_exec "docker compose exec -T litex_builder /bin/bash -c 'chmod +x /workspace/scripts/*.sh && /workspace/scripts/build_soc.sh 1'"
if %errorlevel% neq 0 (
    echo [ERROR] LiteX SoC generation failed.
    exit /b 1
)

echo [3.2/4] Compiling firmware demo...
call :log_and_exec "docker compose exec -T litex_builder /bin/bash -c '/workspace/scripts/build_firmware.sh'"
if %errorlevel% neq 0 (
    echo [ERROR] Firmware compilation failed.
    exit /b 1
)

echo [3.3/4] Integrating firmware into ROM (Pass 2)...
call :log_and_exec "docker compose exec -T litex_builder /bin/bash -c '/workspace/scripts/build_soc.sh 1'"
if %errorlevel% neq 0 (
    echo [ERROR] Firmware integration failed.
    exit /b 1
)

echo [3.4/4] Synthesizing FPGA bitstream on Windows host...
if not exist "%QUARTUS_PATH%\quartus_sh.exe" (
    echo [ERROR] Quartus not found at %QUARTUS_PATH%.
    exit /b 1
)

set "GATEWARE_DIR=build\terasic_de2_115\gateware"
:: Auto-detect the project name from the .qsf file
if not exist "%GATEWARE_DIR%" (
    echo [ERROR] Gateware directory not found: %GATEWARE_DIR%
    exit /b 1
)

set "PROJECT_NAME="
for %%F in ("%GATEWARE_DIR%\*.qsf") do (
    if exist "%GATEWARE_DIR%\%%~nF.v" (
        set "PROJECT_NAME=%%~nF"
    )
)

if "!PROJECT_NAME!"=="" (
    for %%F in ("%GATEWARE_DIR%\*.qsf") do (
        set "PROJECT_NAME=%%~nF"
        goto :project_selected
    )
)

:project_selected

if "!PROJECT_NAME!"=="" (
    echo [ERROR] Could not find any .qsf project file in %GATEWARE_DIR%.
    exit /b 1
)

echo Detected Quartus project: !PROJECT_NAME!

pushd %GATEWARE_DIR%
echo Running Quartus synthesis (this may take a while)...
>> %LOG_FILE% echo.
>> %LOG_FILE% echo ------------------------------------------------------------
>> %LOG_FILE% echo [EXEC] "%QUARTUS_PATH%\quartus_sh.exe" --flow compile !PROJECT_NAME!
>> %LOG_FILE% echo [TIME] %TIME%
>> %LOG_FILE% echo ------------------------------------------------------------
"%QUARTUS_PATH%\quartus_sh.exe" --flow compile !PROJECT_NAME! >> %LOG_FILE% 2>&1
set QUARTUS_EXIT=%errorlevel%
popd
if %QUARTUS_EXIT% neq 0 (
    echo [ERROR] Quartus synthesis failed.
    exit /b 1
)

echo [4/4] Loading bitstream onto DE2-115 via USB-Blaster...
call :log_and_exec "powershell -ExecutionPolicy Bypass -File .\scripts\load_bitstream.ps1"
if %errorlevel% neq 0 (
    echo [ERROR] Bitstream loading failed.
    exit /b 1
)

echo.
echo --- Automated Workflow Complete ---
echo 1. Connect serial console at 115200 baud.
echo 2. Press RESET on board or enter 'reboot' in BIOS.
echo.
exit /b 0

:: Helper function to execute a command, log output, and maintain exit code.
:: PowerShell Tee-Object produced mixed encodings with some subprocesses.
:log_and_exec
set "RAW_CMD=%~1"
>> %LOG_FILE% echo.
>> %LOG_FILE% echo ------------------------------------------------------------
>> %LOG_FILE% echo [EXEC] !RAW_CMD!
>> %LOG_FILE% echo [TIME] %TIME%
>> %LOG_FILE% echo ------------------------------------------------------------

call !RAW_CMD! >> %LOG_FILE% 2>&1
exit /b %errorlevel%
