@echo off
set "DESKTOP_COMMANDER_DISABLE_MCP_UI=1"
"C:\Tools\desktop-commander-runtime\node.exe" "C:\Tools\desktop-commander\node_modules\@wonderwhy-er\desktop-commander\dist\index.js" %*
exit /b %errorlevel%
