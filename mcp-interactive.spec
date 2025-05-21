# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import platform

block_cipher = None

# Added data files
added_datas = [
    ('locales', 'locales'),  # Language files
    ('web_templates', 'web_templates')  # Web template files
]

# Define hidden imports
hidden_imports = [
    'fastmcp',
    'ui',
    'ui.ui_cli',
    'ui.ui_pyqt',
    'ui.ui_web',  # Web interface module
    'flask',  # Flask dependency
    'flask_socketio',  # Flask Socket.IO dependency
    'ui.test_ui',  # Fixed: ensure this is the correct module path
    'typer',
    'dotenv',
    'httpx',
    'difflib',
    'pygments',
    # Add SSL-related modules
    'ssl',
    '_ssl',
]

# Define modules to exclude
excludes = [
    'tkinter',
    'ui.ui_psg',
    'ui.ui_tkinter',
    'unittest',
    'pydoc',
    'doctest',
    'pdb',
    'lib2to3',
]

# Add custom output function to ensure logs are displayed
def debug_print(message):
    try:
        print(f"\n{'#' * 80}\nDEBUG: {message}\n{'#' * 80}\n")
    except UnicodeEncodeError:
        print(f"\n{'#' * 80}\nDEBUG: [Unicode message - encoding error]\n{'#' * 80}\n")

debug_print("Starting PyInstaller configuration")

# Check if we're running in GitHub Actions
is_github_actions = os.environ.get('GITHUB_ACTIONS') == 'true'
debug_print(f"Building in GitHub Actions environment: {is_github_actions}")

# Get system info
debug_print(f"Platform: {platform.platform()}")
debug_print(f"Python version: {platform.python_version()}")

# Add critical DLLs explicitly for CI environment
extra_binaries = []
if platform.system() == 'Windows' and is_github_actions:
    python_dir = os.path.dirname(sys.executable)
    debug_print(f"Python directory: {python_dir}")
    
    # Add Python DLL explicitly
    python_dll = 'python312.dll'
    python_dll_path = os.path.join(python_dir, python_dll)
    if os.path.exists(python_dll_path):
        extra_binaries.append((python_dll, python_dll_path))
        debug_print(f"Added Python DLL: {python_dll}")
    else:
        debug_print(f"Could not find Python DLL: {python_dll}")

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=extra_binaries,
    datas=added_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)

pyz = PYZ(a.pure, cipher=block_cipher)

# Set basic options for all environments
exe_options = {
    'debug': False,
    'strip': False,
    'upx': False,
    'console': True,
}

# Override for GitHub Actions Windows
if platform.system() == 'Windows' and is_github_actions:
    debug_print("Using CI-specific options for Windows in GitHub Actions")
    exe_options['debug'] = True

debug_print("Creating executable...")
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='mcp-interactive',
    runtime_tmpdir=None,
    **exe_options,
    icon='icons/app.ico' if os.path.exists('icons/app.ico') else None,
)
debug_print("Spec file execution completed")

