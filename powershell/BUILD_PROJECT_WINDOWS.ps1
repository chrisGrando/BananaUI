# Prevents running the script with admin rights
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if ($isAdmin) {
    Write-Host "Running with admin rights may break the project!"
    Write-Host "Aborting..."
    cmd /c pause
    exit 1
}

# Prevents running the script if PS2EXE module isn't installed
try {
	Import-Module -Name ps2exe -Global
} catch {
	Write-Host "PS2EXE module not found!"
	Write-Host "Aborting..."
    cmd /c pause
    exit 1
}

# Project's root directory
$PROJECT_ROOT = Join-Path -Path $PSScriptRoot -ChildPath ".."
# Utilities folder
$UTILS = Join-Path -Path $PROJECT_ROOT -ChildPath "utils"
# Binaries folder
$PROJECT_BIN = Join-Path -Path $PROJECT_ROOT -ChildPath "bin"
# App's source code
$SRC_APP = Join-Path -Path $PROJECT_ROOT -ChildPath "app"
# App's assets
$SRC_ASSETS = Join-Path -Path $SRC_APP -ChildPath "assets"
# App's binary folder
$APP_BIN = Join-Path -Path $PROJECT_BIN -ChildPath "BananaUI_Win_x64"
# App's icon
$APP_ICO = Join-Path -Path $PSScriptRoot -ChildPath "app_icon.ico"
# App's PowerShell script launcher
$APP_PS1 = Join-Path -Path $PSScriptRoot -ChildPath "BananaUI.ps1"

# Erase last build of the app
if (Test-Path $APP_BIN) {
	Write-Host "Deleting last build of BananaUI..."
	Remove-Item -path $APP_BIN -recurse
	Write-Host "BananaUI deleted!"
}

# Creating output folder
Write-Host "Creating folders for exported application..."
$AppContentFolder = Join-Path -Path $APP_BIN -ChildPath "app"
$RuntimeFolder = Join-Path -Path $APP_BIN -ChildPath "runtime"
$RuntimePyPy = Join-Path -Path $RuntimeFolder -ChildPath "pypy.exe"
$RuntimePip = Join-Path -Path $RuntimeFolder -ChildPath "Scripts"

New-Item $APP_BIN -Type Directory
New-Item $AppContentFolder -Type Directory
Write-Host "---------------------------------------"

# Perform clean installation of PyPy
Write-Host "Executing clean installation of PyPy..."

$SevenZ = Join-Path -Path $UTILS -ChildPath "7zr.exe"
$PyPy_7z = Join-Path -Path $UTILS -ChildPath "pypy-3.11.7z"
$Pillow_whl = Join-Path -Path $UTILS -ChildPath "pillow-12.3.0-pp311-pypy311_pp80-win_amd64.whl"

& $SevenZ x -aoa -y -o"$RuntimeFolder" $PyPy_7z
Write-Host "---------------------------------------"
$env:PATH = "$RuntimeFolder;$RuntimePip;$env:PATH"
& $RuntimePyPy -m pip install --force-reinstall --only-binary=pillow "$Pillow_whl" --no-cache-dir

Write-Host "---------------------------------------"

# Copying assets
Write-Host "Copying assets..."
Copy-Item -Path $SRC_ASSETS -Destination $AppContentFolder -Recurse

# Copying folder
Write-Host "Copying code..."
Write-Host "---------------------------------------"
robocopy $SRC_APP $AppContentFolder *.py /s
Write-Host "---------------------------------------"

# Generating executable
Write-Host "Generating app executable file..."
Write-Host "---------------------------------------"
$ExeFile = Join-Path -Path $APP_BIN -ChildPath "BananaUI.exe"
Invoke-ps2exe -inputFile $APP_PS1 -outputFile $ExeFile -iconFile $APP_ICO -x64 -noConsole

# End
Write-Host "---------------------------------------"
Write-Host "DONE!"
cmd /c pause
