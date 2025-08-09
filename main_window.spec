# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_data_files

# Все иконки и ресурсы
datas = [
    ('gui/icons/app_icon.ico', 'icons'),
    ('gui/icons/video_light.png', 'icons'),
    ('gui/icons/video_dark.png', 'icons'),
    ('gui/icons/audio_light.png', 'icons'),
    ('gui/icons/audio_dark.png', 'icons'),
    ('gui/icons/image_light.png', 'icons'),
    ('gui/icons/image_dark.png', 'icons'),
    ('gui/icons/document_light.png', 'icons'),
    ('gui/icons/document_dark.png', 'icons'),
    ('gui/icons/pdf_to_image_light.png', 'icons'),
    ('gui/icons/pdf_to_image_dark.png', 'icons'),
    ('gui/icons/pdf_converter_light.png', 'icons'),
    ('gui/icons/pdf_converter_dark.png', 'icons'),
    ('gui/icons/image_to_pdf_light.png', 'icons'),
    ('gui/icons/image_to_pdf_dark.png', 'icons'),
    ('gui/icons/logo_light.png', 'icons'),
    ('gui/icons/logo_dark.png', 'icons'),
    ('settings.json', '.'),
]

a = Analysis(
    ['gui/main_window.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CONMEL Converter',
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
    icon='gui/icons/app_icon.ico'
)
