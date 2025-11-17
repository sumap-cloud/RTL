@echo off
echo ==========================================
echo    Client Demo Test Suite with Allure
echo ==========================================
echo.

cd /d "c:\GITHUB\R10_Pywin_Automation\Scripts\POS_Workspace\tests\Client Demo"

echo Starting test execution...
echo.

C:\GITHUB\R10_Pywin_Automation\Scripts\python.exe run_tests.py

echo.
echo Press any key to exit...
pause > nul
