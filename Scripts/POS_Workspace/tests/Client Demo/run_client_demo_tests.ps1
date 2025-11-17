# Client Demo Test Suite Runner (PowerShell)
# Run this script to execute both test scenarios with allure reporting

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "   Client Demo Test Suite with Allure" -ForegroundColor Cyan  
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

# Change to the test directory
Set-Location "c:\GITHUB\R10_Pywin_Automation\Scripts\POS_Workspace\tests\Client Demo"

Write-Host "📁 Current Directory: $(Get-Location)" -ForegroundColor Yellow
Write-Host ""

# Run the Python test runner
Write-Host "🚀 Starting test execution..." -ForegroundColor Green
Write-Host ""

try {
    & "C:\GITHUB\R10_Pywin_Automation\Scripts\python.exe" "run_tests.py"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "" 
        Write-Host "✅ Test execution completed successfully!" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "⚠️ Test execution completed with issues (Exit Code: $LASTEXITCODE)" -ForegroundColor Yellow
    }
} catch {
    Write-Host ""
    Write-Host "❌ Error during test execution: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "📊 Check the allure-results folder for detailed test results" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to continue..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
