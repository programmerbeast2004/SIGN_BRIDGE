@echo off
echo ============================================
echo    Creating SignBridge Pro Installer
echo ============================================

REM Check if NSIS is installed
where makensis >nul 2>&1
if errorlevel 1 (
    echo ERROR: NSIS is not installed or not in PATH
    echo Please download and install NSIS from:
    echo https://nsis.sourceforge.io/Download
    pause
    exit /b 1
)

REM Check if executable exists
if not exist "dist\SignBridgePro.exe" (
    echo ERROR: SignBridgePro.exe not found in dist folder
    echo Please run build_exe.bat first
    pause
    exit /b 1
)

echo Building installer...
makensis simple_installer.nsi

if exist "SignBridgePro_Setup.exe" (
    echo.
    echo ============================================
    echo    INSTALLER CREATED SUCCESSFULLY!
    echo ============================================
    echo Installer: SignBridgePro_Setup.exe
    echo.
) else (
    echo ERROR: Installer creation failed
)

pause