@echo off
REM Set environment variables
for /f "tokens=*" %%a in ('python -c "import sys; print(f'Python{sys.version_info.major}{sys.version_info.minor}')"') do set PYTHON_VER=%%a

set QT_PLUGIN_PATH=%APPDATA%\Python\%PYTHON_VER%\site-packages\PyQt5\Qt5\plugins
set QT_QPA_PLATFORM_PLUGIN_PATH=%APPDATA%\Python\%PYTHON_VER%\site-packages\PyQt5\Qt5\plugins

echo Qt plugin path has been set: %QT_QPA_PLATFORM_PLUGIN_PATH%

REM Run program
python main.py run --ui-type=pyqt
