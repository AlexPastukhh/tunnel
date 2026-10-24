@echo off
setlocal
cd /d "%~dp0"
echo Fortis Observatory - manual owner-local viewer
echo Keep this window open while viewing in Edge.
echo A private access code will appear below - paste ONLY into the local Edge viewer.
echo.
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  py -3 "%~dp0owner_viewer.py"
) else (
  python "%~dp0owner_viewer.py"
)
echo.
echo Viewer stopped. Docker archive was not stopped or deleted.
pause
