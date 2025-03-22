# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ['../../JWLManager.py'],
    pathex=[],
    binaries=[],
    datas=[('../../res', 'res/'), ('../../CHANGELOG.md', '.'), ('../../LICENSE', '.'), ('../../README.md', '.')],
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
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['../../res/icons/JWLManager.icns'],
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
app = BUNDLE(
    coll,
    name='JWLManager.app',
    icon='../../res/icons/JWLManager.icns',
    bundle_identifier='org.infiniti.jwlmanager',
)
