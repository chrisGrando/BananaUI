@echo off

:: Prevents running the script with admin rights
net session >nul 2>&1

if %ERRORLEVEL% == 0 (
	echo Running with admin rights may break the project!
	echo Aborting...
	pause
	exit /b 1
)

:: Put variables here!
set ERRORLEVEL=0
set "MY_SCRIPT_DIR=%~dp0"
set "MY_BIN_DIR=%MY_SCRIPT_DIR%bin"
set "MY_PYPY_DIR=%MY_BIN_DIR%\pypy"
set "MY_PYPY_PIP_DIR=%MY_PYPY_DIR%\Scripts"
set "SevenZ=%MY_SCRIPT_DIR%assets\7zr.exe"
set "Pillow=%MY_SCRIPT_DIR%assets\pillow-12.3.0-pp311-pypy311_pp80-win_amd64.whl"

:: Creates necessary folders (if they do not exist)
if not exist "%MY_BIN_DIR%" mkdir "%MY_BIN_DIR%"
if not exist "%MY_PYPY_DIR%" mkdir "%MY_PYPY_DIR%"

:: Extracts PyPy with bundled 7-Zip tool
if not exist "%SevenZ%" (
	echo ERROR: Bundled 7-Zip not found!
	echo Aborting...
	pause
	exit /b 1
)

if not exist "%MY_SCRIPT_DIR%assets\pypy-3.11.7z" (
	echo ERROR: PyPy package not found!
	echo Aborting...
	pause
	exit /b 1
)

cd "%MY_PYPY_DIR%"
echo Extracting PyPy...
echo -----------------------------------------------------

"%SevenZ%" x -aoa -y "%MY_SCRIPT_DIR%assets\pypy-3.11.7z"

echo.
echo -----------------------------------------------------
echo.
cd "%MY_SCRIPT_DIR%"

:: Setting up and testing PyPy and pip
echo PyPy is at: %MY_PYPY_DIR%\pypy.exe
echo Pip from PyPy is at: %MY_PYPY_PIP_DIR%\pip.exe
echo.
echo -----------------------------------------------------
echo.

set "PATH=%MY_PYPY_DIR%;%MY_PYPY_PIP_DIR%;%PATH%"

"%MY_PYPY_DIR%\pypy.exe" --version

if %ERRORLEVEL% NEQ 0 (
	echo WARNING: There might be something wrong with the PyPy installation!
	set ERRORLEVEL=0
)

echo.
echo -----------------------------------------------------
echo.

"%MY_PYPY_DIR%\pypy.exe" -m pip --version

if %ERRORLEVEL% NEQ 0 (
	echo WARNING: There might be something wrong with the pip from PyPy installation!
	set ERRORLEVEL=0
)

echo.
echo -----------------------------------------------------
echo.

:: Attempts to install "pillow" package
if not exist "%Pillow%" (
	echo ERROR: Bundled pillow wheel package not found!
	echo Aborting...
	pause
	exit /b 1
)

"%MY_PYPY_DIR%\pypy.exe" -m pip install --force-reinstall --only-binary=pillow "%Pillow%" --no-cache-dir

if %ERRORLEVEL% NEQ 0 echo WARNING: There might be something wrong with the pillow installation!

pause
