@echo off
echo Installing Playwright browsers...
py -m playwright install chromium
echo Done. Exit code: %errorlevel%
pause
