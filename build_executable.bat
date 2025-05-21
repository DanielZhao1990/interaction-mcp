@echo off
REM ========================================
REM MCP Interactive Build Script
REM Using optimized spec file to build executable
REM ========================================

echo [INFO] Starting MCP Interactive build process...

REM Check Python environment
python --version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found. Please make sure Python is installed and added to PATH
    exit /b 1
)

REM Check PyInstaller
python -c "import PyInstaller" > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] PyInstaller not found. Installing now...
    pip install pyinstaller
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to install PyInstaller. Please install it manually
        exit /b 1
    )
)

REM Check required dependencies
echo [INFO] Ensuring all necessary dependencies are installed...
pip install -r requirements/requirements-all.txt
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install dependencies
    exit /b 1
)

REM Clean previous builds
echo [INFO] Cleaning old build files...
if exist "dist/mcp-interactive.exe" del /f /q "dist/mcp-interactive.exe"
if exist "build/mcp-interactive" rmdir /s /q "build/mcp-interactive"

REM Use PyInstaller with optimized spec file
echo [INFO] Using optimized spec file for packaging...
pyinstaller mcp-interactive.spec

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Build failed. Please check error messages
    exit /b 1
)

echo [INFO] Build completed!

REM Show output location
echo [SUCCESS] Package file located at:
echo   - Single file version: dist/mcp-interactive.exe

echo [INFO] You can run the following command to test the packaged application:
echo   - dist\mcp-interactive.exe run

pause 