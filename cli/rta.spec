# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all

pydantic_datas, pydantic_binaries, pydantic_hiddenimports = collect_all('pydantic')
pydantic_core_datas, pydantic_core_binaries, pydantic_core_hiddenimports = collect_all('pydantic_core')

a = Analysis(
    ['rta_entry.py'],
    pathex=[],
    binaries=pydantic_binaries + pydantic_core_binaries,
    datas=pydantic_datas + pydantic_core_datas + [('src/kon/defaults', 'kon/defaults')],
    hiddenimports=[
        'pydantic',
        'pydantic_core',
        'aiohttp',
        'aiofiles',
        'anthropic',
        'openai',
        'rich',
        'textual',
        'curl_cffi',
    ] + pydantic_hiddenimports + pydantic_core_hiddenimports,
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
