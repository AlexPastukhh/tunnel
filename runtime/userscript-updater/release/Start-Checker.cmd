@echo off
setlocal DisableDelayedExpansion
cd /d "%~dp0"
"%~dp0python\python.exe" -I -S -B -X utf8 "%~dp0run_installed.py"
