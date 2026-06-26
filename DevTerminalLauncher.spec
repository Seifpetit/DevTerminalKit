# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path


block_cipher = None

python_tcl_dir = Path(sys.base_prefix) / 'tcl'
tcl_tk_datas = []
for source_name, target_name in (
    ('tcl8.6', 'tcl'),
    ('tk8.6', 'tk'),
    ('tcl8', 'tcl8'),
):
    source_path = python_tcl_dir / source_name
    if source_path.is_dir():
        tcl_tk_datas.append((str(source_path), target_name))

app_datas = tcl_tk_datas + [('app-icon.ico', '.')]


a = Analysis(
    ['program.py'],
    pathex=[],
    binaries=[],
    datas=app_datas,
    hiddenimports=[],
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
    name='DevTerminalLauncher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app-icon.ico',
)
