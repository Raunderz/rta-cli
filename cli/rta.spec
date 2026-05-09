# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['rta_cli/__init__.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['rta_cli.functions.get_file_content', 'rta_cli.functions.get_files_info', 'rta_cli.functions.write_file', 'rta_cli.functions.run_command', 'rta_cli.functions.grep_search', 'rta_cli.functions.glob_search', 'rta_cli.functions.edit_file', 'rta_cli.functions.edit_file_ast', 'rta_cli.functions.apply_diff', 'rta_cli.functions.delete_file', 'rta_cli.functions.create_dir', 'rta_cli.functions.list_directory'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='rta',
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
)
