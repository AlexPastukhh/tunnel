@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo Fortis Observatory - protected owner autostart after Windows sign-in.
echo Waiting up to 15 minutes for Docker and the approved existing Repo container.
set /a TRIES=0
:waitBackend
set /a TRIES+=1
docker.exe info >nul 2>nul
if errorlevel 1 goto notReady
docker.exe exec fortis-repo-test test -d /workspace/repo/fortis-observatory-repo-v1 >nul 2>nul
if errorlevel 1 goto notReady
goto launch
:notReady
if %TRIES% GEQ 60 goto timedOut
timeout /t 15 /nobreak >nul
goto waitBackend
:launch
echo Docker is available. Start exactly one owner-local viewer.
where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
  py -3 "%~dp0owner_viewer.py"
) else (
  python "%~dp0owner_viewer.py"
)
echo Owner Viewer stopped; no automatic Send or duplicate viewer launched.
exit /b 0
:timedOut
echo Docker container was not available in 15 minutes.
echo No Docker container was started or network port exposed.
exit /b 1
