# Prevents running the script with admin rights
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if ($isAdmin) {
    Write-Host "Running with admin rights may break the project!"
    Write-Host "Aborting..."
    cmd /c pause
    exit 1
}

# Put variables here!
$MY_SCRIPT_DIR = $PSScriptRoot
$MY_BIN_DIR = Join-Path -Path $MY_SCRIPT_DIR -ChildPath "bin"
$MY_PYPY_DIR = Join-Path -Path $MY_BIN_DIR -ChildPath "pypy"
$MY_PYPY_PIP_DIR = Join-Path -Path $MY_PYPY_DIR -ChildPath "Scripts"

# Abort if there's no PyPy
$pypyExe = Join-Path -Path $MY_PYPY_DIR -ChildPath "pypy.exe"
if (-not (Test-Path -Path $pypyExe -PathType Leaf)) {
    Write-Host "ERROR: PyPy not found, check if your distribuition is intact!"
    cmd /c pause
    exit 1
}

# Setting up the PATH environment variable for the current process session
$env:PATH = "$MY_PYPY_DIR;$MY_PYPY_PIP_DIR;$env:PATH"

# Running the project
$appFolder = Join-Path -Path $MY_SCRIPT_DIR -ChildPath "app"
$mainScript = Join-Path -Path $appFolder -ChildPath "Main.py"
& $pypyExe $mainScript
