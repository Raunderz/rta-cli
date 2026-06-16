# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all, collect_data_files

pydantic_datas, pydantic_binaries, pydantic_hiddenimports = collect_all('pydantic')
pydantic_core_datas, pydantic_core_binaries, pydantic_core_hiddenimports = collect_all('pydantic_core')

kon_datas = collect_data_files('kon')

a = Analysis(
    ['run.py'],
    pathex=['src'],
    binaries=pydantic_binaries + pydantic_core_binaries,
    datas=pydantic_datas + pydantic_core_datas + kon_datas,
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
        'ddgs',
        'html_to_markdown',
        'readability',
        'libcst',
        'PIL',
        'kon.defaults',
        'kon.defaults.config',
        'kon.builtin_skills',
        'kon.builtin_skills.init',
        'kon.builtin_skills.review',
    ] + pydantic_hiddenimports + pydantic_core_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'unittest',
        'test',
        'pytest',
        'numpy',
        'pandas',
        'scipy',
        'matplotlib',
        'torch',
        'tensorflow',
        'notebook',
        'IPython',
        'sphinx',
        'docutils',
        'pydoc',
        'doctest',
        'lib2to3',
        'ensurepip',
        'idlelib',
        'turtledemo',
        'distutils',
        'setuptools',
        'pip',
        'wheel',
    ],
    noarchive=False,
    optimize=1,
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
