# 4Eyes.spec
import sys
import os

block_cipher = None

# Platform specific hidden imports
if sys.platform == 'darwin':
    platform_imports = ['rumps', 'pystray', 'PIL', 'PIL.Image', 'PIL.ImageDraw']
elif sys.platform == 'win32':
    platform_imports = ['pystray', 'PIL', 'PIL.Image', 'PIL.ImageDraw', 'screen_brightness_control']
else:
    platform_imports = ['pystray', 'PIL', 'PIL.Image', 'PIL.ImageDraw']

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('vision-extension', 'vision-extension'),
    ],
    hiddenimports=['screeninfo'] + platform_imports,
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
# macOS
# -------------------------
if sys.platform == 'darwin':
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='4Eyes',
        debug=False,
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
            'LSUIElement': True,
        },
    )

# -------------------------
# Windows
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
        strip=False,
        upx=True,
        console=False,
        icon='assets/icon.ico',
    )

# -------------------------
# Linux
# -------------------------
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='4Eyes',
        debug=False,
        strip=False,
        upx=True,
        console=False,
        icon='assets/icon.png',
    )
