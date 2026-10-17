# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for CDR Forensic Investigator System."""

from PyInstaller.utils.hooks import collect_all, collect_submodules

# --- Collect data files, binaries, and hidden imports for tricky packages ---
datas = []
binaries = []
hiddenimports = []

PACKAGES_TO_COLLECT = [
    "keyring",
    "matplotlib",
    "folium",
    "scipy",
    "networkx",
]

for pkg in PACKAGES_TO_COLLECT:
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception as e:
        print(f"[spec] Warning: could not collect {pkg}: {e}")

# --- Explicit hidden imports PyInstaller sometimes misses ---
hiddenimports += [
    # PyQt5
    "PyQt5.sip",
    "PyQt5.QtPrintSupport",

    # Matplotlib backends (Qt5 and newer alias)
    "matplotlib.backends.backend_qtagg",
    "matplotlib.backends.backend_qt5agg",
    "matplotlib.backends.backend_agg",

    # Keyring backends (all platforms — harmless extras)
    "keyring.backends.Windows",
    "keyring.backends.SecretService",
    "keyring.backends.macOS",
    "keyring.backends.chainer",
    "keyring.backends.fail",

    # SciPy bits used by our KDTree co-location
    "scipy.spatial",
    "scipy.spatial._ckdtree",
    "scipy._lib.messagestream",
    "scipy._lib._ccallback_c",

    # pandas
    "pandas._libs.tslibs.base",
    "pandas._libs.tslibs.np_datetime",

    # folium uses jinja2 templates
    "jinja2.ext",
]

# --- Files to bundle alongside the .exe ---
datas += [
    ("sample_cdr.csv", "."),          # demo data (optional)
]

# --- Entry point ---
a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Trim known-big unused modules to reduce size
        "tkinter",
        "PyQt5.QtWebEngineWidgets",
        "PyQt5.QtQml",
        "PyQt5.QtQuick",
        "PyQt5.Qt3DCore",
        "PyQt5.QtBluetooth",
        "PyQt5.QtMultimedia",
        "PyQt5.QtNetworkAuth",
        "PyQt5.QtNfc",
        "PyQt5.QtWebSockets",
    ],
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
    name="CDR-Forensic",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,           # ← no console window; set True to see errors
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon="assets/app.ico",   # ← uncomment when you have an icon
)