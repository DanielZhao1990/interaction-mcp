# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import re

block_cipher = None

# 添加所需数据文件
added_datas = [
    ('locales', 'locales'),  # 语言文件
    ('web_templates', 'web_templates')  # Web模板文件
]

# 定义需要包含的隐藏导入
hidden_imports = [
    'fastmcp',
    'ui',
    'ui.ui_cli',
    'ui.ui_pyqt',
    'ui.ui_web',  # Web界面模块
    'flask',  # Flask依赖
    'flask_socketio',  # Flask Socket.IO依赖
    'ui.test_ui',  # 修正：确保这是正确的模块路径
    'typer',
    'dotenv',
    'httpx',
    'difflib',
    'pygments',
]

# 定义需要排除的模块 - 扩展排除列表
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
    # Qt模块排除 - 更全面的排除
    'PyQt5.QtBluetooth', 'PyQt5.QtDBus', 'PyQt5.QtDesigner', 'PyQt5.QtHelp',
    'PyQt5.QtLocation', 'PyQt5.QtMultimedia', 'PyQt5.QtMultimediaWidgets',
    'PyQt5.QtNetwork', 'PyQt5.QtNetworkAuth', 'PyQt5.QtNfc', 'PyQt5.QtOpenGL',
    'PyQt5.QtPositioning', 'PyQt5.QtPrintSupport', 'PyQt5.QtQml', 'PyQt5.QtQuick',
    'PyQt5.QtQuickWidgets', 'PyQt5.QtRemoteObjects', 'PyQt5.QtSensors',
    'PyQt5.QtSerialPort', 'PyQt5.QtSql', 'PyQt5.QtSvg',
    'PyQt5.QtTest', 'PyQt5.QtWebChannel', 'PyQt5.QtWebEngine',
    'PyQt5.QtWebEngineCore', 'PyQt5.QtWebEngineWidgets', 'PyQt5.QtWebSockets',
    'PyQt5.QtXml', 'PyQt5.QtXmlPatterns',
    # 添加更多不需要的Python库
    'PIL', 'wx', 'PyQt6', 'PySide2', 'PySide6',
]

# 添加自定义输出函数，确保日志显示
def debug_print(message):
    print(f"\n{'#' * 80}\nDEBUG: {message}\n{'#' * 80}\n")

debug_print("开始设置PyInstaller配置")

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=added_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={
        'PyQt5': {
            'plugins': [ # 最小化必需的插件
                'platforms/qwindows.dll',      # Windows平台支持
                'styles/qwindowsvistastyle.dll', # Windows视觉样式
            ],
            'excluded_plugins': [
                # 排除所有其他插件
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

debug_print("Analysis对象创建完成，准备过滤Qt组件")

# 检查二进制文件列表中有多少Qt相关文件
def count_qt_files(binaries_toc):
    count = 0
    for dest_path, _, _ in binaries_toc:
        norm_path = dest_path.replace('\\', '/')
        if 'Qt5' in norm_path or 'PyQt5' in norm_path:
            count += 1
    return count

qt_files_before = count_qt_files(a.binaries)
debug_print(f"Analysis对象中共有 {qt_files_before} 个Qt相关文件")

# 需要排除的大型图形DLL文件
large_graphics_dlls = [
    'opengl32sw.dll',
    'd3dcompiler_47.dll',
    'libGLESv2.dll',
    'libEGL.dll',
]

# 计算大型DLL占用的空间
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
        debug_print(f"发现以下大型图形DLL文件:")
        for dll, size in found_dlls:
            size_mb = size / (1024 * 1024)
            print(f"- {dll}: {size:,} 字节 ({size_mb:.2f} MB)")
        
        total_mb = total_size / (1024 * 1024)
        debug_print(f"这些DLL总共占用 {total_size:,} 字节 ({total_mb:.2f} MB)")
    else:
        debug_print("未找到待排除的大型图形DLL文件")
        
    return total_size

graphics_dll_size = calc_large_dll_size(a.binaries)

# 增强的二进制文件过滤函数
def filter_qt_binaries(binaries_toc):
    filtered_binaries = []
    excluded_binaries = []
    qt_dll_pattern = re.compile(r'qt5[a-z]+\.dll', re.IGNORECASE)  # 匹配Qt5的DLL
    
    debug_print(f"开始过滤二进制文件，共 {len(binaries_toc)} 个文件")
    
    for dest_path, source_path, typecode in binaries_toc:
        # 规范化路径以便可靠匹配 (处理Windows的反斜杠)
        norm_dest_path = dest_path.replace('\\', '/')
        file_name = os.path.basename(norm_dest_path).lower()
        
        # 过滤条件:
        is_excluded = False
        exclusion_reason = ""
        
        # 0. 排除大型图形DLL (优先检查以提升可读性)
        if file_name in [dll.lower() for dll in large_graphics_dlls]:
            is_excluded = True
            exclusion_reason = f"大型图形DLL ({os.path.getsize(source_path) / (1024*1024):.2f} MB)"
        
        # 1. 排除所有Qt翻译文件
        elif 'translations/' in norm_dest_path or 'translations\\' in norm_dest_path:
            is_excluded = True
            exclusion_reason = "Qt翻译文件"
        
        # 2. 排除不需要的Qt DLL (只保留核心组件)
        elif qt_dll_pattern.search(norm_dest_path.lower()):
            # 保留核心Qt组件
            if not any(core_mod in norm_dest_path.lower() for core_mod in ['qt5core', 'qt5gui', 'qt5widgets']):
                is_excluded = True
                exclusion_reason = "非核心Qt DLL"
        
        # 3. 排除不需要的插件目录
        qt_plugin_dirs = [
            'imageformats', 'iconengines', 'bearer', 'audio', 'geoservices',
            'mediaservice', 'playlistformats', 'position', 'printsupport',
            'qmltooling', 'scenegraph', 'sensorgestures', 'sensors',
            'sqldrivers', 'texttospeech', 'virtualkeyboard', 'webview',
        ]
        
        for plugin_dir in qt_plugin_dirs:
            if f'plugins/{plugin_dir}' in norm_dest_path or f'plugins\\{plugin_dir}' in norm_dest_path:
                # 但保留必需的Windows平台插件
                if 'platforms/qwindows' in norm_dest_path or 'styles/qwindowsvistastyle' in norm_dest_path:
                    break  # 保留这些文件
                
                is_excluded = True
                exclusion_reason = f"Qt插件: {plugin_dir}"
                break
                
        if is_excluded:
            excluded_binaries.append((norm_dest_path, exclusion_reason))
        else:
            filtered_binaries.append((dest_path, source_path, typecode))
    
    # 输出排除的文件列表
    debug_print(f"过滤完成: 保留 {len(filtered_binaries)} 个文件，排除 {len(excluded_binaries)} 个文件")
    if excluded_binaries:
        debug_print("排除的文件列表(前20个):")
        for i, (path, reason) in enumerate(excluded_binaries[:20], 1):
            print(f"{i}. {path} - 原因: {reason}")
        
        if len(excluded_binaries) > 20:
            print(f"... 还有 {len(excluded_binaries) - 20} 个文件被排除 ...")
    
    return filtered_binaries

debug_print("应用增强的Qt资源过滤器...")
a.binaries = filter_qt_binaries(a.binaries)

# 检查过滤后还有多少Qt相关文件
qt_files_after = count_qt_files(a.binaries)
debug_print(f"过滤后还剩 {qt_files_after} 个Qt相关文件")

# 也过滤掉Qt相关的数据文件
def filter_qt_datas(datas_toc):
    filtered_datas = []
    excluded_datas = []
    
    debug_print(f"开始过滤数据文件，共 {len(datas_toc)} 个文件")
    
    for dest_path, source_path, typecode in datas_toc:
        norm_dest_path = dest_path.replace('\\', '/')
        
        # 排除Qt资源、翻译等
        is_excluded = False
        if 'PyQt5/Qt5/resources' in norm_dest_path or 'PyQt5/Qt5/translations' in norm_dest_path:
            is_excluded = True
            excluded_datas.append(norm_dest_path)
            
        if not is_excluded:
            filtered_datas.append((dest_path, source_path, typecode))
    
    debug_print(f"数据文件过滤完成: 保留 {len(filtered_datas)} 个文件，排除 {len(excluded_datas)} 个文件")
    if excluded_datas:
        debug_print("排除的数据文件列表(前10个):")
        for i, path in enumerate(excluded_datas[:10], 1):
            print(f"{i}. {path}")
        
        if len(excluded_datas) > 10:
            print(f"... 还有 {len(excluded_datas) - 10} 个文件被排除 ...")
    
    return filtered_datas

debug_print("应用Qt数据文件过滤器...")
a.datas = filter_qt_datas(a.datas)

pyz = PYZ(a.pure)

debug_print("创建可执行文件...")
exe = EXE(
    pyz,
    a.scripts,
    a.binaries, # 使用过滤后的二进制列表
    a.datas,
    [],
    name='mcp-interactive',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,  # 启用strip以减小文件大小
    upx=True,    # 启用UPX压缩
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
debug_print("spec文件执行完毕")

