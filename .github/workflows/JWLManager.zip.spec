# -*- mode: python ; coding: utf-8 -*-

import platform
from PyInstaller.utils.hooks import collect_data_files

arch = platform.machine().lower()

if arch in ('x86_64', 'amd64'):
    sqlite_dll = '../../libs/sqlite3_64.dll'
    core_dll   = '../../libs/jwlCore-amd64.dll'
elif arch in ('aarch64', 'arm64'):
    sqlite_dll = '../../libs/sqlite3_ARM.dll'
    core_dll   = '../../libs/jwlCore-arm64.dll'
else:
    raise RuntimeError(f'Unsupported architecture: {arch}')

block_cipher = None

a = Analysis(
    ['../../JWLManager.py'],
    pathex=[],
    binaries=[
        (core_dll, 'libs'),
        (sqlite_dll, 'libs'),
    ],
    datas=[
        ('../../res', 'res/'),
        ('../../CHANGELOG.md', '.'),
        ('../../LICENSE', '.'),
        ('../../README.md', '.')
    ],
    hiddenimports=['xlsx2csv'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='JWLManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['../../res/icons/JWLManager.ico'],
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='JWLManager',
)
