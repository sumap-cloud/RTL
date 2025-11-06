# Pytest-HTML Report Setup for TC_HappyFlow

This folder contains a simple pytest setup with HTML reporting for the Happy Flow test case.

## 📁 Files in this folder:

1. **TC_HappyFlow.py** - The main test file with pytest decorations
2. **run_test_with_html_report.bat** - Batch file to run the test and generate HTML report

## 🚀 How to Run:

### Option 1: Using the Batch File (Recommended - Easiest!)
Simply double-click on `run_test_with_html_report.bat` and it will:
- Automatically navigate to the correct directory
- Run the test using the virtual environment Python
- Generate an HTML report
- Automatically open the report in your browser

### Option 2: Using Command Line
From this directory, run:
```bash
C:\GItHub\R10_Pywin_Automation-3\Scripts\python.exe -m pytest TC_HappyFlow.py -v -s --html=report.html --self-contained-html
```

### Option 3: Run Directly from Python
```bash
C:\GItHub\R10_Pywin_Automation-3\Scripts\python.exe TC_HappyFlow.py
```

## 📊 Report Output:

After running the test, you'll find:
- **report.html** - A beautiful, self-contained HTML report with:
  - Test summary (Pass/Fail)
  - Execution time
  - Detailed test steps with print statements
  - **📸 Screenshots for each step** - Visual proof of test execution
  - Test metadata
- **screenshots/** - Folder containing all captured screenshots with timestamps

## 📝 Test Details:

**Test Name:** `test_BonusBuy()`

**Test Steps:**
1. Login to POS application (User: ATcash5)
2. Add first item (EAN: 9300624016540)
3. Add second item (EAN: 1220000062412)
4. Verify basket contents
5. Validate loyalty card and handle customer popup
6. Process cash tender payment
7. Handle payment completion popups
8. Close cash drawer

**Test Markers:**
- `@pytest.mark.smoke` - Marks this as a smoke test

## 🎨 Features:

- ✅ Clean and simple setup (only 3 files!)
- ✅ Easy to understand test structure
- ✅ Detailed step-by-step print statements
- ✅ **📸 Automatic screenshot capture for all 8 steps**
- ✅ Screenshots embedded directly in the HTML report
- ✅ **Professional Extent Report-style HTML report** with custom styling
- ✅ **Modern gradient theme** with purple/blue color scheme
- ✅ **Click-to-zoom** functionality on screenshots
- ✅ **Step numbering** for easy navigation
- ✅ Self-contained report (no external dependencies)
- ✅ Automatic browser opening after test completion
- ✅ Timestamped screenshots for easy tracking
- ✅ **Responsive design** - works on desktop and mobile
- ✅ **Print-friendly** layout for documentation

## 📦 Requirements:

- Python 3.x
- pytest
- pytest-html
- All POS automation components

All packages are available in: `C:\GItHub\R10_Pywin_Automation-3\Offline_lib\offline_packages`

## 🔧 Troubleshooting:

### If pytest-html is not installed:
```bash
pip install --no-index --find-links=C:\GItHub\R10_Pywin_Automation-3\Offline_lib\offline_packages pytest-html
```

### If screenshots don't appear in the report:
1. Make sure the test completed successfully
2. Check that the `screenshots/` folder has the images
3. The images are embedded as base64 in the HTML - they should appear inline
4. Try refreshing the browser or opening the report in a different browser

### Viewing Screenshots in the Report (Extent Report Style):
- **All 8 screenshots are displayed stacked vertically** - scroll down to see all of them
- **Automatic step numbering** (Step 1, Step 2, etc.) for easy navigation
- Each screenshot is labeled with the step name (e.g., "Step 1: Login Complete")
- **Beautiful gradient headers** for each screenshot with professional styling
- **Click any screenshot to zoom in/out** for detailed viewing
- **Hover effects** on screenshots for better interactivity
- Green bordered images with shadow effects (similar to Extent Reports)
- **Modern card-based layout** with smooth transitions
- No carousel/slider - all screenshots are visible at once!
- **Responsive design** adapts to different screen sizes

### Viewing the Report:
- The report is **self-contained** - all screenshots are embedded in the HTML file
- You can share the `report.html` file and it will work on any computer
- No need for the screenshots folder when sharing - everything is in the HTML!
- Simply open `report.html` in any browser to view the complete test results with all screenshots

## 🎨 Extent Report-Style Customization:

This report has been customized to look similar to **Extent Reports** from Selenium with the following enhancements:

### Visual Features:
- **Modern gradient theme** - Purple and blue gradient headers (similar to Extent Reports)
- **Professional card layout** - Each section is beautifully contained in styled cards
- **Status badges** - Color-coded test results (Green = Passed, Red = Failed, Orange = Skipped)
- **Step numbers** - Automatic numbering for each screenshot step
- **Hover effects** - Interactive elements with smooth transitions
- **Shadow effects** - Depth and dimension to UI elements

### Interactive Features:
- **Click-to-zoom** - Click any screenshot to zoom in for detailed viewing
- **Smooth scrolling** - Navigate between sections smoothly
- **Collapsible sections** - Expandable test details
- **Responsive design** - Adapts to any screen size (desktop, tablet, mobile)

### Report Sections (Extent-style):
1. **Header** - Gradient styled title with test suite name
2. **Summary** - Quick overview of test execution with visual indicators
3. **Environment** - System and test metadata in organized table
4. **Test Results** - Detailed test case information with status
5. **Screenshots** - Visual evidence with step-by-step documentation

### Color Scheme:
- **Primary**: Purple gradient (#667eea to #764ba2)
- **Success**: Green (#4CAF50) for passed tests
- **Error**: Red (#f44336) for failed tests
- **Warning**: Orange (#ff9800) for skipped tests
- **Info**: Blue (#2196F3) for information

### Additional Customizations Available:
The `conftest.py` file contains extensive CSS that can be further customized:
- Change color schemes by modifying CSS variables
- Adjust fonts and sizing
- Add company logos or branding
- Include additional charts or graphs
- Customize print layouts for PDF export

**Tip**: You can easily customize colors by editing the `:root` CSS variables in `conftest.py`!

---

**Happy Testing! 🎉**
