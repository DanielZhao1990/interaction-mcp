@echo off
setlocal

REM Get Python version
for /f "tokens=*" %%a in ('python -c "import sys; print(f'Python{sys.version_info.major}{sys.version_info.minor}')"') do set PYTHON_VER=%%a

REM Set Qt plugin path
set QT_PLUGIN_PATH=%APPDATA%\Python\%PYTHON_VER%\site-packages\PyQt5\Qt5\plugins
set QT_QPA_PLATFORM_PLUGIN_PATH=%APPDATA%\Python\%PYTHON_VER%\site-packages\PyQt5\Qt5\plugins

REM Permanently add to system environment variables
setx QT_PLUGIN_PATH "%QT_PLUGIN_PATH%" /M
setx QT_QPA_PLATFORM_PLUGIN_PATH "%QT_QPA_PLATFORM_PLUGIN_PATH%" /M

echo Qt plugin paths have been permanently added to system environment variables:
echo QT_PLUGIN_PATH = %QT_PLUGIN_PATH%
echo QT_QPA_PLATFORM_PLUGIN_PATH = %QT_QPA_PLATFORM_PLUGIN_PATH%
echo.
echo Note: Environment variables have been set, but may require a computer restart or re-login to take effect.
echo If you need to use these environment variables immediately in the current session, please run the original run_pyqt.bat script.

pause
