# How to View Allure Test Reports in Localhost

This guide explains multiple ways to view your allure test reports in a browser using localhost.

## 🚀 Quick Start (Recommended)

### Method 1: Using the Built-in Viewer (Easiest)
```bash
# Double-click this file or run in command prompt
view_allure_reports.bat
```

**What this does:**
- Creates a simple HTML viewer for your test results
- Starts a local web server on http://localhost:8000  
- Automatically opens your default browser
- Displays test results, steps, and screenshots in a user-friendly format

### Method 2: Manual Web Server
```bash
# Navigate to the test directory
cd "c:\GITHUB\R10_Pywin_Automation\Scripts\POS_Workspace\tests\Client Demo"

# Start the web server
python serve_allure_reports.py
```

## 🌐 Accessing Your Reports

Once the web server starts:

1. **Automatic Browser Opening**: The server tries to open your default browser automatically
2. **Manual Access**: Navigate to `http://localhost:8000` in any browser
3. **Direct Results**: Go to `http://localhost:8000/allure-results` to see JSON files

## 📊 What You'll See

### Simple HTML Viewer Features:
- **Test List**: All executed test cases with pass/fail status
- **Detailed Steps**: Each test step with execution status
- **Screenshots**: Captured screenshots at key moments (automatically attached)
- **Attachments**: Error logs, test data, configuration details
- **Timing**: Test execution duration and timestamps
- **Metadata**: Test information, labels, and categories

### File Structure in Browser:
```
http://localhost:8000/
├── allure-results/           # JSON test results
│   ├── index.html           # Simple viewer (auto-created)
│   ├── *-result.json        # Individual test results
│   └── *-attachment.txt     # Test attachments
└── screenshots/             # Test screenshots
    └── *.png               # Timestamped screenshots
```

## 🎯 Different Viewing Options

### Option 1: JSON Results (Always Available)
- **Access**: `http://localhost:8000/allure-results/`
- **Format**: Raw JSON files with complete test data
- **Best for**: Detailed analysis, integration with other tools

### Option 2: Simple HTML Viewer (Recommended)
- **Access**: `http://localhost:8000/allure-results/index.html`
- **Format**: User-friendly web interface
- **Best for**: Quick review, screenshots, team sharing

### Option 3: Full Allure HTML (Requires Java)
- **Setup**: Install Java JDK/JRE + Set JAVA_HOME
- **Command**: `allure serve ./allure-results`
- **Format**: Complete allure dashboard with charts and trends
- **Best for**: Comprehensive reporting, CI/CD integration

## 🔧 Troubleshooting

### Port Already in Use
If port 8000 is busy, the server will automatically try 8001, 8002, etc.

### Cannot Access Server
1. Check if firewall is blocking the connection
2. Try different port: `python serve_allure_reports.py --port 8080`
3. Access via `http://127.0.0.1:8000` instead of localhost

### Screenshots Not Showing
1. Verify `screenshots` folder exists and contains `.png` files
2. Check browser console for loading errors
3. Ensure screenshots were captured during test execution

### Browser Not Opening Automatically
1. Manually navigate to `http://localhost:8000`
2. Check default browser settings
3. Try different browser

## 📱 Advanced Usage

### Custom Port
```bash
python serve_allure_reports.py --port 9000
```

### Specific Directory
```bash
python serve_allure_reports.py --directory "path/to/other/results"
```

### Create Viewer Only
```bash
python serve_allure_reports.py --create-viewer
```

## 🎨 Screenshot Features

Your tests automatically capture screenshots at:
- ✅ **Login success**
- 🧭 **Navigation steps**
- 📝 **Data entry completion**  
- ❌ **Error conditions**
- 🏁 **Test completion**

Screenshots are:
- 🕒 **Timestamped** for easy identification
- 📎 **Automatically attached** to allure reports
- 🗂️ **Organized** in dedicated screenshots folder
- 🔗 **Linked** in the web viewer for easy access

## 🚪 Stopping the Server

- **Windows**: Press `Ctrl + C` in the command window
- **Browser**: Simply close the browser (server continues running)
- **Complete Stop**: Close the command window

## 💡 Pro Tips

1. **Keep Server Running**: Leave the server running while reviewing multiple test runs
2. **Bookmark Results**: Add `http://localhost:8000/allure-results/` to browser bookmarks  
3. **Share Results**: Others on your network can access via your IP address
4. **Multiple Tests**: Each test run creates new timestamped files
5. **Screenshot Review**: Use screenshots to debug failed tests quickly

---

**Need Help?**
- Check the main README.md for comprehensive documentation
- Review console output for detailed error messages
- Ensure all prerequisites are installed and configured
