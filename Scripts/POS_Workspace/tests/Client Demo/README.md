# Client Demo Test Suite with Allure Reporting

This folder contains automated test scenarios for the POS system with comprehensive allure reporting.

## Test Scenarios

### TC001_paidout.py
- **Purpose**: Validate POS Paid Out Functionality and Cash Management
- **Features**: Cash management, denomination handling, financial controls
- **User Role**: ATcash1
- **Key Tests**: Denomination entry, amount validation, category selection, GST handling

### TC002_agerestiction_Scenario.py  
- **Purpose**: Validate Age Restriction functionality with Save/Recall Transaction
- **Features**: Age verification, transaction save/recall, multiple item addition methods
- **User Role**: ATcash5
- **Key Tests**: 18+ age restrictions, item search/EAN/PLU, transaction persistence

## How to Run Tests

### Option 1: Using the Python Runner (Recommended)
```bash
python run_tests.py
```

### Option 2: Using Batch File (Windows)
```bash
run_client_demo_tests.bat
```

### Option 3: Using PowerShell Script
```powershell
.\run_client_demo_tests.ps1
```

### Option 4: Direct Pytest Command
```bash
C:/GITHUB/R10_Pywin_Automation/Scripts/python.exe -m pytest --alluredir=allure-results --verbose
```

## Test Results

### Screenshots
- **Location**: `./screenshots/` 
- **Content**: Timestamped screenshots captured at key test steps
- **Naming**: `{step_name}_{timestamp}.png`
- **Integration**: Automatically attached to allure reports

### Allure Results
- **Location**: `./allure-results/` (JSON format)
- **Content**: Detailed test execution data, steps, attachments, errors

### HTML Report (if Java is available)
- **Location**: `./allure-report/index.html`
- **Content**: Interactive HTML dashboard with charts, trends, test details

## Viewing Test Results

### Option 1: Simple Web Viewer (Recommended)
```bash
# View results in browser via localhost
view_allure_reports.bat
```
or
```bash
python serve_allure_reports.py
```
This will:
- Start a local web server on http://localhost:8000
- Automatically open your browser
- Display test results in a user-friendly format
- Show screenshots and attachments

### Option 2: Direct File Access
- Open `./allure-results/` folder
- View individual `*-result.json` files
- Access screenshots in `./screenshots/` folder

### Option 3: Full Allure HTML (Requires Java)
```bash
# Generate and serve full allure HTML report
allure serve ./allure-results
```

## Allure Features Included

### Test Organization
- **Epic**: POS System Testing
- **Features**: Cash Management, Age Restriction & Transaction Management  
- **Stories**: Specific functionality areas
- **Severity**: Critical level tests

### Enhanced Reporting
- **Steps**: Detailed test execution steps with descriptions
- **Attachments**: Error messages, test data, configuration details, **screenshots**
- **Test Case IDs**: Linked to test documentation
- **Descriptions**: Comprehensive test purpose and scope
- **Screenshots**: Automatic capture at key test points with timestamps

### Test Data Capture
- **Cash Summary Details**: Amount calculations and validations
- **Final Transaction Details**: Complete transaction information
- **Error Information**: Detailed error messages and contexts
- **Application State**: Connection and navigation confirmations

## Prerequisites

### Required Software
- Python 3.12+ (configured in virtual environment)
- POS Application (R10PosClient)
- Test credentials (ATcash1/ATcash5)

### Optional for HTML Reports
- Java JDK/JRE (for allure HTML report generation)
- JAVA_HOME environment variable set

### Python Packages (Already Installed)
- allure-pytest (2.15.0)
- allure-python-commons (2.15.0)
- pytest (8.4.1)
- pywinauto (0.6.9)

## File Structure

```
Client Demo/
├── TC001_paidout.py              # Paid Out test scenario
├── TC002_agerestiction_Scenario.py # Age restriction test scenario
├── run_tests.py                   # Python test runner
├── run_client_demo_tests.bat      # Windows batch runner
├── run_client_demo_tests.ps1      # PowerShell runner
├── view_allure_reports.bat        # Web viewer for reports
├── serve_allure_reports.py        # HTTP server for results viewing
├── pytest.ini                     # Pytest configuration
├── README.md                      # This file
├── screenshots/                   # Test screenshots
├── allure-results/                # Test results (JSON)
└── allure-report/                 # HTML report (if generated)
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure virtual environment is activated
   - Check Python path configuration

2. **POS Connection Issues**
   - Verify R10PosClient is running
   - Check login credentials
   - Ensure application window titles match

3. **Java Not Found (for HTML reports)**
   - Install Java JDK/JRE
   - Set JAVA_HOME environment variable
   - JSON results will still be available

4. **Test Failures**
   - Check POS application state
   - Verify test data configuration
   - Review allure results for detailed error information

### Getting Help

- Check the allure-results folder for detailed error information
- Review test logs and console output
- Ensure all prerequisites are met
- Verify POS application accessibility

## Example Usage

```bash
# Navigate to test directory
cd "c:\GITHUB\R10_Pywin_Automation\Scripts\POS_Workspace\tests\Client Demo"

# Run tests with detailed output
python run_tests.py

# View results in browser (after tests complete)
view_allure_reports.bat

# Or start web server manually
python serve_allure_reports.py

# Check results
# - Screenshots: ./screenshots/
# - JSON: ./allure-results/
# - Web viewer: http://localhost:8000
# - HTML: ./allure-report/index.html (if Java available)
```

## Test Execution Flow

1. **Setup Phase**
   - Clean previous results
   - Initialize allure reporting
   - Validate prerequisites

2. **Test Execution**
   - Run TC001_paidout.py (Cash Management)
   - Run TC002_agerestiction_Scenario.py (Age Restrictions)
   - Capture detailed steps and results

3. **Report Generation**
   - Generate JSON results (always available)
   - Generate HTML report (if Java available)
   - Display summary and file locations

---

**Note**: This test suite is designed for automated POS testing with comprehensive reporting. Ensure the POS application is accessible and test credentials are valid before execution.
