@echo off

set script_path=%~dp0
set formated_path=%script_path:~0,-1%

start "BananaUI Builder" /max PowerShell.exe -ExecutionPolicy Bypass -File "%formated_path%\powershell\BUILD_PROJECT_WINDOWS.ps1"
