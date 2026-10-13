"""
Build script for BananaUI - Windows x64 distribution using PyPy.

Creates a self-contained distribution at bin/Win_x64/ containing:
  - A PyPy virtualenv with copied runtime (portable)
  - All project source files and assets
  - Pillow installed in the virtualenv
  - A launcher batch script (BananaUI.bat) and a PowerShell launcher (BananaUI.ps1)

Usage:
    pypy3 build_win_x64.py
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

# ─── Configuration ────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent
BUILD_DIR = SCRIPT_DIR / "bin" / "Win_x64"
VENV_DIR = BUILD_DIR / "runtime"
APP_DIR = BUILD_DIR / "app"

# Source files to include in the distribution
SOURCE_FILES = [
    "Main.py",
    "ui.py",
    "config.py",
    "api_client.py",
    "exceptions.py",
    "logo.py",
]

# Directories to include
SOURCE_DIRS = [
    "assets",
]

# Packages to install into the virtualenv
REQUIRED_PACKAGES = [
    "Pillow",
]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def log(msg: str):
    print(f"[BUILD] {msg}")


def run(cmd: list, cwd=None, env=None):
    """Run a subprocess command, streaming output, and raise on failure."""
    log(f"  > {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if result.stdout:
        for line in result.stdout.strip().splitlines():
            print(f"       {line}")
    if result.returncode != 0:
        raise RuntimeError(f"Command failed (exit {result.returncode}): {' '.join(str(c) for c in cmd)}")
    return result


# ─── Build Steps ──────────────────────────────────────────────────────────────

def clean_build_dir():
    """Remove previous build directory if it exists."""
    if BUILD_DIR.exists():
        log(f"Cleaning previous build: {BUILD_DIR}")
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)


def create_virtualenv():
    """Create a PyPy virtualenv with copied binaries (not symlinks) for portability."""
    log(f"Creating PyPy virtualenv at: {VENV_DIR}")
    run([
        sys.executable, "-m", "virtualenv",
        "--copies",
        "--clear",
        str(VENV_DIR),
    ])
    log("Virtualenv created successfully.")


def get_venv_python() -> Path:
    """Return the path to the Python/PyPy executable inside the virtualenv."""
    # On Windows, virtualenv puts executables in Scripts/
    candidates = [
        VENV_DIR / "Scripts" / "pypy3.exe",
        VENV_DIR / "Scripts" / "python.exe",
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(f"Could not find Python executable in {VENV_DIR / 'Scripts'}")


def get_venv_pip() -> Path:
    """Return the path to pip inside the virtualenv."""
    pip_path = VENV_DIR / "Scripts" / "pip.exe"
    if pip_path.exists():
        return pip_path
    # Fallback: use python -m pip
    return None


def install_packages():
    """Install required packages into the virtualenv.

    Attempts pip install with retries. If pip fails (e.g. network issues),
    falls back to copying the package directly from the system PyPy's
    user site-packages.
    """
    venv_python = get_venv_python()
    log(f"Using virtualenv Python: {venv_python}")

    # Determine venv site-packages path
    result = subprocess.run(
        [str(venv_python), "-c", "import site; print(site.getsitepackages()[0])"],
        capture_output=True, text=True
    )
    venv_site_packages = Path(result.stdout.strip())
    log(f"Venv site-packages: {venv_site_packages}")

    for pkg in REQUIRED_PACKAGES:
        installed = False

        # Try pip install with retries
        for attempt in range(1, 4):
            log(f"Installing {pkg} via pip (attempt {attempt}/3)...")
            try:
                run([str(venv_python), "-m", "pip", "install", "--retries", "5", pkg])
                installed = True
                break
            except RuntimeError:
                log(f"  pip install attempt {attempt} failed.")

        # Fallback: copy from system PyPy user site-packages
        if not installed:
            log(f"Falling back to copying {pkg} from system PyPy installation...")
            _copy_package_from_system(pkg, venv_site_packages)

    log("All packages installed.")


def _copy_package_from_system(pkg_name: str, venv_site_packages: Path):
    """Copy a package from the system PyPy user site-packages into the venv."""
    # Find system user site-packages
    result = subprocess.run(
        [sys.executable, "-c", f"import {pkg_name.upper() if pkg_name == 'Pillow' else pkg_name}; import os; print(os.path.dirname(os.path.dirname(__import__('{_get_import_name(pkg_name)}').__file__)))"],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        # Try alternative discovery
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", pkg_name, "--files"],
            capture_output=True, text=True
        )
        # Parse location from pip show
        for line in result.stdout.splitlines():
            if line.startswith("Location:"):
                system_site = Path(line.split(":", 1)[1].strip())
                break
        else:
            raise RuntimeError(f"Cannot find system installation of {pkg_name}")
    else:
        system_site = Path(result.stdout.strip())

    log(f"  System site-packages: {system_site}")

    import_name = _get_import_name(pkg_name)

    # Copy the package directory
    src_pkg_dir = system_site / import_name
    if src_pkg_dir.exists():
        dst = venv_site_packages / import_name
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src_pkg_dir, dst)
        log(f"  Copied package: {import_name}/")

    # Copy dist-info if found
    for item in system_site.iterdir():
        if item.name.lower().startswith(pkg_name.lower().replace("-", "_")) and item.name.endswith(".dist-info"):
            dst = venv_site_packages / item.name
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(item, dst)
            log(f"  Copied dist-info: {item.name}/")
            break

    # Verify the import works
    venv_python = get_venv_python()
    run([str(venv_python), "-c", f"import {import_name}; print('{pkg_name} import OK')"])


def _get_import_name(pkg_name: str) -> str:
    """Map package name to its Python import name."""
    mapping = {
        "Pillow": "PIL",
        "pillow": "PIL",
    }
    return mapping.get(pkg_name, pkg_name.lower())


def verify_imports():
    """Verify that all required imports work within the virtualenv."""
    venv_python = get_venv_python()
    log("Verifying imports in virtualenv...")

    test_code = (
        "import tkinter; "
        "from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageFilter; "
        "import json, base64, urllib.request, threading, queue; "
        "print('All imports OK')"
    )
    run([str(venv_python), "-c", test_code])
    log("Import verification passed.")


def copy_source_files():
    """Copy project source files into the app directory."""
    log(f"Copying source files to: {APP_DIR}")
    APP_DIR.mkdir(parents=True, exist_ok=True)

    for f in SOURCE_FILES:
        src = SCRIPT_DIR / f
        dst = APP_DIR / f
        if src.exists():
            shutil.copy2(src, dst)
            log(f"  Copied: {f}")
        else:
            log(f"  WARNING: Source file not found: {f}")

    for d in SOURCE_DIRS:
        src = SCRIPT_DIR / d
        dst = APP_DIR / d
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            log(f"  Copied directory: {d}/")
        else:
            log(f"  WARNING: Source directory not found: {d}/")

    # Create the output directory for generated images
    (APP_DIR / "output").mkdir(parents=True, exist_ok=True)
    log("  Created: output/")


def create_launchers():
    """Create launcher scripts for starting the application."""

    # ── Batch launcher ─────────────────────────────────────────────────────
    bat_content = r"""@echo off
REM ──────────────────────────────────────────────────────────────
REM  BananaUI Launcher - Windows x64 (PyPy Runtime)
REM ──────────────────────────────────────────────────────────────
setlocal

set "SCRIPT_DIR=%~dp0"
set "PYPY_EXE=%SCRIPT_DIR%runtime\Scripts\pypy3.exe"
set "APP_MAIN=%SCRIPT_DIR%app\Main.py"

REM Fallback to python.exe in the venv if pypy3.exe is not present
if not exist "%PYPY_EXE%" (
    set "PYPY_EXE=%SCRIPT_DIR%runtime\Scripts\python.exe"
)

if not exist "%PYPY_EXE%" (
    echo ERROR: PyPy runtime not found at: %PYPY_EXE%
    echo Please ensure the distribution is intact.
    pause
    exit /b 1
)

if not exist "%APP_MAIN%" (
    echo ERROR: Application entry point not found at: %APP_MAIN%
    pause
    exit /b 1
)

echo Starting BananaUI with PyPy runtime...
"%PYPY_EXE%" "%APP_MAIN%"

if %ERRORLEVEL% neq 0 (
    echo.
    echo BananaUI exited with an error. Check error.log for details.
    pause
)

endlocal
"""
    bat_path = BUILD_DIR / "BananaUI.bat"
    bat_path.write_text(bat_content, encoding="utf-8")
    log(f"Created launcher: {bat_path.name}")

    # ── PowerShell launcher ────────────────────────────────────────────────
    ps1_content = r"""# ──────────────────────────────────────────────────────────────
#  BananaUI Launcher - Windows x64 (PyPy Runtime)
# ──────────────────────────────────────────────────────────────

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$PyPyExe = Join-Path $ScriptDir "runtime\Scripts\pypy3.exe"
$AppMain = Join-Path $ScriptDir "app\Main.py"

# Fallback to python.exe if pypy3.exe is not present
if (-not (Test-Path $PyPyExe)) {
    $PyPyExe = Join-Path $ScriptDir "runtime\Scripts\python.exe"
}

if (-not (Test-Path $PyPyExe)) {
    Write-Error "PyPy runtime not found. Ensure the distribution is intact."
    exit 1
}

if (-not (Test-Path $AppMain)) {
    Write-Error "Application entry point not found at: $AppMain"
    exit 1
}

Write-Host "Starting BananaUI with PyPy runtime..." -ForegroundColor Yellow
& $PyPyExe $AppMain
"""
    ps1_path = BUILD_DIR / "BananaUI.ps1"
    ps1_path.write_text(ps1_content, encoding="utf-8")
    log(f"Created launcher: {ps1_path.name}")


def print_summary():
    """Print build summary with sizes."""
    log("=" * 60)
    log("BUILD COMPLETE!")
    log("=" * 60)

    total_size = 0
    file_count = 0
    for root, dirs, files in os.walk(BUILD_DIR):
        for f in files:
            fp = Path(root) / f
            total_size += fp.stat().st_size
            file_count += 1

    size_mb = total_size / (1024 * 1024)
    log(f"  Output directory : {BUILD_DIR}")
    log(f"  Total files      : {file_count}")
    log(f"  Total size       : {size_mb:.1f} MB")
    log("")
    log("  Launchers:")
    log(f"    - BananaUI.bat  (double-click to run)")
    log(f"    - BananaUI.ps1  (PowerShell alternative)")
    log("")
    log("  Distribution structure:")
    log("    bin/Win_x64/")
    log("    ├── BananaUI.bat        # Main launcher")
    log("    ├── BananaUI.ps1        # PowerShell launcher")
    log("    ├── app/                # Application source code")
    log("    │   ├── Main.py")
    log("    │   ├── ui.py")
    log("    │   ├── config.py")
    log("    │   ├── api_client.py")
    log("    │   ├── exceptions.py")
    log("    │   ├── logo.py")
    log("    │   ├── assets/")
    log("    │   └── output/")
    log("    └── runtime/            # PyPy virtualenv (self-contained)")
    log("        ├── Scripts/")
    log("        ├── Lib/")
    log("        └── ...")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    log(f"BananaUI Build Script - Windows x64 (PyPy)")
    log(f"PyPy: {sys.executable} ({sys.version})")
    log(f"Project: {SCRIPT_DIR}")
    log("")

    try:
        clean_build_dir()
        create_virtualenv()
        install_packages()
        verify_imports()
        copy_source_files()
        create_launchers()
        print_summary()
    except Exception as e:
        log(f"BUILD FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
