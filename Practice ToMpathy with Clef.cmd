@echo off
setlocal
cd /d "%~dp0"
set TOMPATHY_CLEF=1
call npm run practice
if errorlevel 1 pause
