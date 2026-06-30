@echo off
setlocal EnableDelayedExpansion

:: ============================================================
::  RTL Automation - Batch Test Runner
::  Double-click this file to run all test cases listed in
::  run_tests.txt.  Results open as a summary HTML at the end.
:: ============================================================

set "ROOT=%~dp0"
set "SCRIPT_DIR=%ROOT%Scripts\SCO_Workspace\Testing\Regression"
set "RESULTS_DIR=%ROOT%Scripts\SCO_Workspace\Results"
set "PYTHON=%ROOT%Scripts\python.exe"
set "TC_LIST=%ROOT%run_tests.txt"
set "SUMMARY_SCRIPT=%ROOT%Scripts\generate_batch_report.py"
set "SUMMARY_FILE=%RESULTS_DIR%\batch_summary.html"

echo.
echo ============================================================
echo   RTL Automation -- Batch Test Runner
echo ============================================================
echo.

:: Verify prerequisites
if not exist "%PYTHON%" (
    echo [ERROR] Python not found at: %PYTHON%
    pause & exit /b 1
)
if not exist "%TC_LIST%" (
    echo [ERROR] Test list not found at: %TC_LIST%
    pause & exit /b 1
)

:: ------------------------------------------------------------------
:: Count and collect test cases from run_tests.txt
:: (skip blank lines and lines starting with #)
:: ------------------------------------------------------------------
set TC_COUNT=0
for /f "usebackq tokens=* eol=#" %%L in ("%TC_LIST%") do (
    set "LINE=%%L"
    if not "!LINE!"=="" (
        set /a TC_COUNT+=1
        set "TC_!TC_COUNT!=!LINE!"
    )
)

if %TC_COUNT%==0 (
    echo [WARN] No test cases found in run_tests.txt
    pause & exit /b 0
)

echo   Found %TC_COUNT% test case(s) to run.
echo.

:: ------------------------------------------------------------------
:: Run each test case sequentially
:: ------------------------------------------------------------------
set PASS_COUNT=0
set FAIL_COUNT=0

for /l %%i in (1,1,%TC_COUNT%) do (
    set "TC=!TC_%%i!"

    :: Normalise: trim trailing spaces and add .py if missing
    for /f "tokens=* delims= " %%T in ("!TC!") do set "TC=%%T"
    if /i "!TC:~-3!" neq ".py" set "TC=!TC!.py"

    set "TC_FILE=%SCRIPT_DIR%\!TC!"

    echo ------------------------------------------------------------
    echo   [%%i/%TC_COUNT%] !TC!
    echo ------------------------------------------------------------

    if exist "!TC_FILE!" (
        "%PYTHON%" "!TC_FILE!"
        if !errorlevel! equ 0 (
            echo   [DONE] Completed successfully.
            set /a PASS_COUNT+=1
        ) else (
            echo   [WARN] Exited with error code !errorlevel!
            set /a FAIL_COUNT+=1
        )
    ) else (
        echo   [ERROR] Script not found: !TC_FILE!
        set /a FAIL_COUNT+=1
    )
    echo.
)

:: ------------------------------------------------------------------
:: Generate batch summary report
:: ------------------------------------------------------------------
echo ============================================================
echo   Generating batch summary report...
echo ============================================================
echo.

"%PYTHON%" "%SUMMARY_SCRIPT%" "%TC_LIST%" "%RESULTS_DIR%"

:: Open summary in default browser
if exist "%SUMMARY_FILE%" (
    echo.
    echo   Opening summary report...
    start "" "%SUMMARY_FILE%"
) else (
    echo   [WARN] Summary report not generated.
)

echo.
echo ============================================================
echo   Batch complete.  Passed: %PASS_COUNT%  Failed: %FAIL_COUNT%
echo ============================================================
echo.
pause
