@echo off
echo ==========================================
echo    Allure Reports Viewer (Localhost)
echo ==========================================
echo.

cd /d "c:\GITHUB\R10_Pywin_Automation\Scripts\POS_Workspace\tests\Client Demo"

echo Starting web server to view test results...
echo.
echo The server will open in your default browser automatically.
echo Use Ctrl+C to stop the server when you're done viewing.
echo.

C:\GITHUB\R10_Pywin_Automation\Scripts\python.exe serve_allure_reports.py --create-viewer
C:\GITHUB\R10_Pywin_Automation\Scripts\python.exe serve_allure_reports.py

echo.
echo Server stopped.
pause
