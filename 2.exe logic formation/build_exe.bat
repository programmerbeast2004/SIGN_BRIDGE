@echo off
echo ============================================
echo       SignBridge Pro - Build Script
echo ============================================

REM Step 1: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Step 2: Install Python packages
echo ✅ Installing Python dependencies...
pip install pyinstaller opencv-python numpy tensorflow mediapipe pillow

REM Step 3: Verify .spec file exists
if not exist "SignBridgePro.spec" (
    echo ❌ ERROR: 'SignBridgePro.spec' not found!
    pause
    exit /b 1
)

REM Step 4: Clean old builds (preserve caption_output.txt if exists)
echo 🔄 Cleaning previous build folders...

REM Temporarily move caption_output.txt if it exists
if exist "dist\caption_output.txt" (
    echo 🛑 Preserving caption_output.txt...
    move "dist\caption_output.txt" ".\caption_output.txt.bak" >nul
)

rmdir /s /q build
rmdir /s /q dist
del /f /q SignBridgePro.exe

REM Restore caption_output.txt after cleaning
if exist "caption_output.txt.bak" (
    echo ♻️ Restoring caption_output.txt...
    move "caption_output.txt.bak" "caption_output.txt" >nul
)


REM Step 5: Build with updated .spec file
echo 🚧 Building executable...
pyinstaller --clean SignBridgePro.spec

REM Step 6: Copy OpenCV DLL manually (camera support)
echo 📦 Copying OpenCV backend DLL...
copy "C:\Users\prvme\AppData\Local\Programs\Python\Python310\Lib\site-packages\cv2\opencv_videoio_ffmpeg4110_64.dll" "dist\" /Y

REM Step 7: Copy additional runtime files (for safety)
echo 🗂️ Copying runtime files...
if not exist "dist\model" mkdir "dist\model"
if not exist "dist\assets" mkdir "dist\assets"

xcopy "model\*" "dist\model\" /Y /E
xcopy "assets\*" "dist\assets\" /Y /E
copy "README.txt" "dist\" /Y
copy "settings.json" "dist\" /Y
copy "caption_output.txt" "dist\" /Y

echo.
echo ✅✅✅========================================
echo     BUILD COMPLETED SUCCESSFULLY!
echo     Executable: dist\SignBridgePro.exe
echo ============================================
pause
