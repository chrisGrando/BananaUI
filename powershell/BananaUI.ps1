# Get PSScriptRoot independently of compiled/not compiled
if (!$PSScriptRoot) { $PSScriptRoot = $ScriptRoot }

# Support for dialog boxes
Add-Type -AssemblyName System.Windows.Forms
$dialog = [System.Windows.Forms.MessageBox]

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
$MY_PYPY_DIR = Join-Path -Path $MY_SCRIPT_DIR -ChildPath "runtime"
$MY_PYPY_PIP_DIR = Join-Path -Path $MY_PYPY_DIR -ChildPath "Scripts"

# Abort if there's no PyPy
$pypyExe = Join-Path -Path $MY_PYPY_DIR -ChildPath "pypy.exe"
if (-not (Test-Path -Path $pypyExe -PathType Leaf)) {
    $null = $dialog::Show("PyPy not found, check if your distribuition is intact!", "ERROR")
    exit 1
}

# Setting up the PATH environment variable for the current process session
$env:PATH = "$MY_PYPY_DIR;$MY_PYPY_PIP_DIR;$env:PATH"

# Running the project
$appFolder = Join-Path -Path $MY_SCRIPT_DIR -ChildPath "app"
$mainScript = Join-Path -Path $appFolder -ChildPath "Main.py"

try {
	& $pypyExe $mainScript
} catch {
	$null = $dialog::Show("Something went wrong when trying to run the app...", "ERROR")
}
