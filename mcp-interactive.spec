# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import re

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

# Define modules to exclude - extended exclude list
excludes = [
    'tkinter',
    'ui.ui_psg',
    'ui.ui_tkinter',
    'unittest',
    'pydoc',
    'doctest',
    'pdb',
    'lib2to3',
    'matplotlib',
    'pandas',
    'numpy',
    'scipy',
    'pytest',
    # Qt modules exclusion - more comprehensive exclusion
    'PyQt5.QtBluetooth', 'PyQt5.QtDBus', 'PyQt5.QtDesigner', 'PyQt5.QtHelp',
    'PyQt5.QtLocation', 'PyQt5.QtMultimedia', 'PyQt5.QtMultimediaWidgets',
    'PyQt5.QtNetwork', 'PyQt5.QtNetworkAuth', 'PyQt5.QtNfc', 'PyQt5.QtOpenGL',
    'PyQt5.QtPositioning', 'PyQt5.QtPrintSupport', 'PyQt5.QtQml', 'PyQt5.QtQuick',
    'PyQt5.QtQuickWidgets', 'PyQt5.QtRemoteObjects', 'PyQt5.QtSensors',
    'PyQt5.QtSerialPort', 'PyQt5.QtSql', 'PyQt5.QtSvg',
    'PyQt5.QtTest', 'PyQt5.QtWebChannel', 'PyQt5.QtWebEngine',
    'PyQt5.QtWebEngineCore', 'PyQt5.QtWebEngineWidgets', 'PyQt5.QtWebSockets',
    'PyQt5.QtXml', 'PyQt5.QtXmlPatterns',
    # Add more unnecessary Python libraries
    'PIL', 'wx', 'PyQt6', 'PySide2', 'PySide6',
]

# Add custom output function to ensure logs are displayed
def debug_print(message):
    try:
        print(f"\n{'#' * 80}\nDEBUG: {message}\n{'#' * 80}\n")
    except UnicodeEncodeError:
        # Fallback to ASCII if terminal encoding doesn't support Unicode
        print(f"\n{'#' * 80}\nDEBUG: [Unicode message - encoding error]\n{'#' * 80}\n")

debug_print("Starting PyInstaller configuration")

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=added_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={
        'PyQt5': {
            'plugins': [ # Minimize necessary plugins
                'platforms/qwindows.dll',      # Windows platform support
                'styles/qwindowsvistastyle.dll', # Windows visual style
            ],
            'excluded_plugins': [
                # Exclude all other plugins
                'imageformats', 'iconengines', 'platformthemes',
                'generic', 'mediaservice', 'printsupport', 'sensors', 'sqldrivers',
                'texttospeech', 'virtualkeyboard', 'webengine',
            ]
        }
    },
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)

debug_print("Analysis object created, preparing to filter Qt components")

# Check how many Qt-related files are in the binary list
def count_qt_files(binaries_toc):
    count = 0
    for dest_path, _, _ in binaries_toc:
        norm_path = dest_path.replace('\\', '/')
        if 'Qt5' in norm_path or 'PyQt5' in norm_path:
            count += 1
    return count

qt_files_before = count_qt_files(a.binaries)
debug_print(f"Analysis object contains {qt_files_before} Qt-related files")

# Large graphics DLL files to exclude (but keep SSL-related files)
large_graphics_dlls = [
    'opengl32sw.dll',
    'd3dcompiler_47.dll',
    'libGLESv2.dll',
    'libEGL.dll',
]

# List of DLL files to keep
keep_dlls = [
    'libcrypto-1_1.dll', 
    'libcrypto-1_1-x64.dll',
    'libssl-1_1.dll', 
    'libssl-1_1-x64.dll',
    '_ssl.pyd',
    'python3.dll',
    'python310.dll',
    'python312.dll',
]

# Calculate space occupied by large DLLs
def calc_large_dll_size(binaries_toc):
    total_size = 0
    found_dlls = []
    
    for dest_path, source_path, _ in binaries_toc:
        file_name = os.path.basename(dest_path).lower()
        for dll in large_graphics_dlls:
            if dll.lower() == file_name:
                file_size = os.path.getsize(source_path) if os.path.exists(source_path) else 0
                found_dlls.append((file_name, file_size))
                total_size += file_size
                break
                
    if found_dlls:
        debug_print(f"Found the following large graphics DLL files:")
        for dll, size in found_dlls:
            size_mb = size / (1024 * 1024)
            print(f"- {dll}: {size:,} bytes ({size_mb:.2f} MB)")
        
        total_mb = total_size / (1024 * 1024)
        debug_print(f"These DLLs occupy a total of {total_size:,} bytes ({total_mb:.2f} MB)")
    else:
        debug_print("No large graphics DLLs found to exclude")
        
    return total_size

graphics_dll_size = calc_large_dll_size(a.binaries)

# Enhanced binary file filtering function
def filter_qt_binaries(binaries_toc):
    filtered_binaries = []
    excluded_binaries = []
    qt_dll_pattern = re.compile(r'qt5[a-z]+\.dll', re.IGNORECASE)  # Match Qt5 DLLs
    
    debug_print(f"Starting binary file filtering, total {len(binaries_toc)} files")
    
    for dest_path, source_path, typecode in binaries_toc:
        # Normalize path for reliable matching (handle Windows backslashes)
        norm_dest_path = dest_path.replace('\\', '/')
        file_name = os.path.basename(norm_dest_path).lower()
        
        # Filter conditions:
        is_excluded = False
        exclusion_reason = ""
        
        # 0. Keep specific DLL files (such as OpenSSL-related files)
        if file_name in [dll.lower() for dll in keep_dlls]:
            filtered_binaries.append((dest_path, source_path, typecode))
            continue
            
        # 0. Exclude large graphics DLLs (priority check for readability)
        if file_name in [dll.lower() for dll in large_graphics_dlls]:
            is_excluded = True
            exclusion_reason = f"Large graphics DLL ({os.path.getsize(source_path) / (1024*1024):.2f} MB)"
        
        # 1. Exclude all Qt translation files
        elif 'translations/' in norm_dest_path or 'translations\\' in norm_dest_path:
            is_excluded = True
            exclusion_reason = "Qt translation file"
        
        # 2. Exclude unnecessary Qt DLLs (keep only core components)
        elif qt_dll_pattern.search(norm_dest_path.lower()):
            # Keep core Qt components
            if not any(core_mod in norm_dest_path.lower() for core_mod in ['qt5core', 'qt5gui', 'qt5widgets']):
                is_excluded = True
                exclusion_reason = "Non-core Qt DLL"
        
        # 3. Exclude unnecessary plugin directories
        qt_plugin_dirs = [
            'imageformats', 'iconengines', 'bearer', 'audio', 'geoservices',
            'mediaservice', 'playlistformats', 'position', 'printsupport',
            'qmltooling', 'scenegraph', 'sensorgestures', 'sensors',
            'sqldrivers', 'texttospeech', 'virtualkeyboard', 'webview',
        ]
        
        for plugin_dir in qt_plugin_dirs:
            if f'plugins/{plugin_dir}' in norm_dest_path or f'plugins\\{plugin_dir}' in norm_dest_path:
                # But keep necessary Windows platform plugins
                if 'platforms/qwindows' in norm_dest_path or 'styles/qwindowsvistastyle' in norm_dest_path:
                    break  # Keep these files
                
                is_excluded = True
                exclusion_reason = f"Qt plugin: {plugin_dir}"
                break
                
        if is_excluded:
            excluded_binaries.append((norm_dest_path, exclusion_reason))
        else:
            filtered_binaries.append((dest_path, source_path, typecode))
    
    # Output excluded file list
    debug_print(f"Filtering completed: Kept {len(filtered_binaries)} files, excluded {len(excluded_binaries)} files")
    if excluded_binaries:
        debug_print("Excluded files list (first 20):")
        for i, (path, reason) in enumerate(excluded_binaries[:20], 1):
            print(f"{i}. {path} - Reason: {reason}")
        
        if len(excluded_binaries) > 20:
            print(f"... {len(excluded_binaries) - 20} more files excluded ...")
    
    return filtered_binaries

debug_print("Applying enhanced Qt resource filter...")
a.binaries = filter_qt_binaries(a.binaries)

# Check how many Qt-related files remain after filtering
qt_files_after = count_qt_files(a.binaries)
debug_print(f"After filtering, {qt_files_after} Qt-related files remain")

# Also filter Qt-related data files
def filter_qt_datas(datas_toc):
    filtered_datas = []
    excluded_datas = []
    
    debug_print(f"Starting data file filtering, total {len(datas_toc)} files")
    
    for dest_path, source_path, typecode in datas_toc:
        norm_dest_path = dest_path.replace('\\', '/')
        
        # Exclude Qt resources, translations, etc.
        is_excluded = False
        if 'PyQt5/Qt5/resources' in norm_dest_path or 'PyQt5/Qt5/translations' in norm_dest_path:
            is_excluded = True
            excluded_datas.append(norm_dest_path)
            
        if not is_excluded:
            filtered_datas.append((dest_path, source_path, typecode))
    
    debug_print(f"Data file filtering completed: Kept {len(filtered_datas)} files, excluded {len(excluded_datas)} files")
    if excluded_datas:
        debug_print("Excluded data files list (first 10):")
        for i, path in enumerate(excluded_datas[:10], 1):
            print(f"{i}. {path}")
        
        if len(excluded_datas) > 10:
            print(f"... {len(excluded_datas) - 10} more files excluded ...")
    
    return filtered_datas

debug_print("Applying Qt data file filter...")
a.datas = filter_qt_datas(a.datas)

pyz = PYZ(a.pure)

debug_print("Creating executable...")
exe = EXE(
    pyz,
    a.scripts,
    a.binaries, # Use filtered binary list
    a.datas,
    [],
    name='mcp-interactive',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,  # Enable strip to reduce file size
    upx=True,    # Enable UPX compression
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icons/app.ico' if os.path.exists('icons/app.ico') else None,
)
debug_print("Spec file execution completed")

