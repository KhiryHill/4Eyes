# 4Eyes.spec
# PyInstaller spec file for macOS, Windows, and Linux

import sys
import os

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('vision-extension', 'vision-extension'),  # Include Chrome extension
    ],
    hiddenimports=[
        'screeninfo',
        'pystray',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'rumps',
        'screen_brightness_control',
    ],
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

# -------------------------
# macOS - creates a .app bundle
# -------------------------
if sys.platform == 'darwin':
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='4Eyes',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        icon='assets/icon.icns',
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='4Eyes',
    )
    app = BUNDLE(
        coll,
        name='4Eyes.app',
        icon='assets/icon.icns',
        bundle_identifier='com.4eyes.app',
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSAppleScriptEnabled': False,
            'CFBundleDisplayName': '4Eyes',
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': True,
            'LSUIElement': True,  # Hides from dock, runs as menu bar app
        },
    )

# -------------------------
# Windows - creates a .exe
# -------------------------
elif sys.platform == 'win32':
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='4Eyes',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon='assets/icon.ico',
        version='version_info.txt',
    )

# -------------------------
# Linux - creates a binary
# -------------------------
elif sys.platform.startswith('linux'):
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='4Eyes',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        icon='assets/icon.png',
    )
