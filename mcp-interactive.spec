# -*- mode: python ; coding: utf-8 -*-
import os

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
    "test_ui",
    'typer',
    'dotenv',
    'httpx',
    "difflib",
    'pygments',
]

# 定义需要排除的模块
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
    'pytest'
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=added_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

# 单文件版本
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='mcp-interactive',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
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
