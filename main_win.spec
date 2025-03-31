# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src-py\\main.py'],
    pathex=[],
    binaries=[],
        datas=[
        ('D:\\Users\\18593\\miniconda3\\envs\\lazyeat_py39\\Lib\\site-packages\\vosk\\*', 'vosk'),
        ('D:\\Users\\18593\\miniconda3\\envs\\lazyeat_py39\\Lib\\site-packages\\mediapipe\\*', 'mediapipe'),
        ('D:\\Users\\18593\\miniconda3\\envs\\lazyeat_py39\\Lib\\site-packages\\mediapipe\\modules\\*', 'mediapipe/modules'),
        ('D:\\Users\\18593\\miniconda3\\envs\\lazyeat_py39\\Lib\\site-packages\\mediapipe\\modules\\palm_detection\\*', 'mediapipe/modules/palm_detection'),
        ('D:\\Users\\18593\\miniconda3\\envs\\lazyeat_py39\\Lib\\site-packages\\mediapipe\\modules\\hand_landmark\\*', 'mediapipe/modules/hand_landmark'),
        ('D:\\Users\\18593\\miniconda3\\envs\\lazyeat_py39\\Lib\\site-packages\\mediapipe\\python\\*', 'mediapipe/python'),
        ('D:\\Users\\18593\\miniconda3\\envs\\lazyeat_py39\\Lib\\site-packages\\uvicorn\\*', 'uvicorn'),
        ('D:\\Users\\18593\\miniconda3\\envs\\lazyeat_py39\\Lib\\site-packages\\win10toast\\*', 'win10toast'),
    ],
    hiddenimports=[
        'vosk',
        'mediapipe',
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.protocols',
        'win10toast',
    ],
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
    [],
    exclude_binaries=True,
    name='Lazyeat Backend-x86_64-pc-windows-msvc',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='backend-py',
)
