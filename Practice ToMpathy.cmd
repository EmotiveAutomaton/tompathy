@echo off
setlocal
cd /d "%~dp0"
call npm run practice
if errorlevel 1 (
  echo.
  echo Practice setup did not finish. See the error above.
  pause
)
