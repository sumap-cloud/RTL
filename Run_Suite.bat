@echo off
setlocal EnableDelayedExpansion

:: ============================================================
::  RTL SCO Automation - Suite Launcher
::  Double-click this file, pick a banner, and the whole suite
::  runs unattended.  The SCO is returned to the Welcome screen
::  after every single test (pass, fail, or crash).
::
::  Reports  : Scripts\SCO_Workspace\Results\<TC_ID>.html
::  Logs     : Scripts\SCO_Workspace\Results\BatchLogs\
::  Summary  : Scripts\SCO_Workspace\Results\BatchSummary_<Suite>_<stamp>.txt
:: ============================================================

set "ROOT=%~dp0"
set "PYTHON=%ROOT%Scripts\python.exe"
set "TESTING=%ROOT%Scripts\SCO_Workspace\Testing"

if not exist "%PYTHON%" (
    echo [ERROR] Python not found at: %PYTHON%
    echo         Did you clone the repo to a different folder, or is the
    echo         virtual environment missing?  See Documentation\KT_Sessions.
    pause & exit /b 1
)

:menu
cls
echo ============================================================
echo   RTL SCO Automation - which suite do you want to run?
echo ============================================================
echo.
echo    1. Sanity      (11 quick smoke tests - run this first)
echo    2. Regression  (Supermarket / Metro - full suite)
echo    3. BigW        (BigW banner)
echo    4. NZ          (Countdown / New Zealand)
echo    5. Exit
echo.
set "CHOICE="
set /p CHOICE=Enter 1-5 and press Enter:

if "%CHOICE%"=="1" set "SUITE=Sanity"     & goto run
if "%CHOICE%"=="2" set "SUITE=Regression" & goto run
if "%CHOICE%"=="3" set "SUITE=BigW"       & goto run
if "%CHOICE%"=="4" set "SUITE=NZ"         & goto run
if "%CHOICE%"=="5" exit /b 0
echo Invalid choice. & timeout /t 2 >nul & goto menu

:run
set "RUNNER=%TESTING%\%SUITE%\run_all_%SUITE%.py"
if not exist "%RUNNER%" (
    echo [ERROR] Runner not found: %RUNNER%
    pause & exit /b 1
)

echo.
echo ============================================================
echo   Running the %SUITE% suite...
echo   Do NOT touch the SCO screen while this is running.
echo ============================================================
echo.

:: The working directory MUST be the project root - Components\report.py
:: writes its HTML/screenshots to a path relative to the current directory.
pushd "%ROOT%"
"%PYTHON%" -u "%RUNNER%"
set "RC=!errorlevel!"
popd

echo.
echo ============================================================
echo   %SUITE% suite finished (exit code !RC!).
echo   Open the newest BatchSummary_%SUITE%_*.txt in
echo   Scripts\SCO_Workspace\Results\ to see what passed.
echo ============================================================
echo.
start "" "%ROOT%Scripts\SCO_Workspace\Results"
pause
