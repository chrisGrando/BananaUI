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

:: Abort if there's no PyPy
if not exist "%MY_PYPY_DIR%\pypy.exe" (
	echo "ERROR: PyPy not found, have you already run the script 'SETUP_PROJECT_WINDOWS.bat'?"
	pause
	exit /b 1
)

:: Setting up the %PATH% environment variable
set "PATH=%MY_PYPY_DIR%;%MY_PYPY_PIP_DIR%;%PATH%"

:: Running the project
"%MY_PYPY_DIR%\pypy.exe" "%MY_SCRIPT_DIR%app\Main.py"

if %ERRORLEVEL% NEQ 0 pause
