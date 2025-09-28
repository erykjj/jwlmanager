# -*- mode: python ; coding: utf-8 -*-

import platform
from PyInstaller.utils.hooks import collect_data_files

arch = platform.machine().lower()

block_cipher = None

a = Analysis(
    ['../../JWLManager.py'],
    pathex=['.'],
    binaries=[
        ('../../libs/sqlite3_64.dll', '.'),
        ('../../libs/jwlCore-amd64.dll', '.'),
        ('../../libs/sqlite3_ARM.dll', '.'),
        ('../../libs/jwlCore-arm64.dll', '.')
    ],
    datas=[('../../res', 'res/')],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='JWLManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='../../res/icons/JWLManager.ico',
)
