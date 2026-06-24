@echo off
cd /d "C:\Users\hapee\Documents\Job Hunt AI"
py job_scanner.py > scanner_log.txt 2>&1
echo Exit code: %errorlevel% >> scanner_log.txt
