# -*- mode: python ; coding: utf-8 -*-
import os

opencv_ffmpeg_dll = r'C:\Users\prvme\AppData\Local\Programs\Python\Python310\Lib\site-packages\cv2\opencv_videoio_ffmpeg4110_64.dll'

a = Analysis(
    ['main.py'],  # ✅ Your main script file
    pathex=[],
    binaries=[(opencv_ffmpeg_dll, '.')],  # ✅ OpenCV DLL
    datas=[
        ('model', 'model'),
        ('assets', 'assets'),
        ('settings.json', '.'),
        ('caption_output.txt', '.'),
        ('README.txt', '.'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SignBridgePro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=r'assets\signbridge_icon.ico'  # ✅ Only if this icon exists
)
