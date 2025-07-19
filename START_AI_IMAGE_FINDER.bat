@echo off
echo.
echo  ===================================================
echo     🎯 AI Image Finder - One-Click Launcher  
echo  ===================================================
echo.
echo  🚀 Starting AI Image Search System...
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  ❌ Python not found! Please install Python 3.8+ first.
    echo  📥 Download from: https://python.org/downloads
    echo.
    pause
    exit /b 1
)

echo  ✅ Python detected
echo  🎯 Launching AI Image Finder...
echo.

REM Run the main application
python ai_image_finder.py

echo.
echo  👋 Thanks for using AI Image Finder!
pause
