@echo off
setlocal
cd /d "%~dp0"
where node >nul 2>nul
if errorlevel 1 (
  echo Node.js is needed. Install Node 22.14 or later, then open this file again.
  pause
  exit /b 1
)
if not exist "node_modules\@playwright\test\package.json" (
  echo Preparing this checkout for its first review...
  call npm ci
  if errorlevel 1 goto failed
)
call npm run review
if errorlevel 1 goto failed
exit /b 0
:failed
echo.
echo Setup did not finish. The error above explains which step failed.
pause
exit /b 1
