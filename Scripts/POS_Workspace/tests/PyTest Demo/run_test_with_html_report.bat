@echo off
REM ========================================
REM Simple Test Runner with HTML Report
REM ========================================

REM Change to the script directory
cd /d "%~dp0"

echo.
echo ======================================
echo   POS Automation - Happy Flow Test
echo   with pytest-html Report Generation
echo ======================================
echo.
echo Current Directory: %CD%
echo.

REM Set the paths
set TEST_FILE=TC_HappyFlow.py
set REPORT_FILE=report.html
set PYTHON_EXE=C:\GItHub\R10_Pywin_Automation-3\Scripts\python.exe

REM Clean previous report
if exist %REPORT_FILE% (
    echo Cleaning previous report...
    del %REPORT_FILE%
)

echo.
echo ======================================
echo   Running Test with Pytest
echo ======================================
echo.

REM Run pytest with html report using full Python path
"%PYTHON_EXE%" -m pytest "%TEST_FILE%" -v -s --html="%REPORT_FILE%" --self-contained-html

if %ERRORLEVEL% neq 0 (
    echo.
    echo ======================================
    echo   Test execution completed with errors
    echo ======================================
    echo.
) else (
    echo.
    echo ======================================
    echo   Test execution completed successfully!
    echo ======================================
    echo.
)

echo.
echo ======================================
echo   Opening HTML Report in Browser
echo ======================================
echo.

REM Open the report in default browser
if exist %REPORT_FILE% (
    start %REPORT_FILE%
    echo Report opened in browser: %REPORT_FILE%
) else (
    echo ERROR: Report file not found!
)

echo.
echo Press any key to exit...
pause
