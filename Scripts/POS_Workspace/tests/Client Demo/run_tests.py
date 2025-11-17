# Client Demo Test Suite Runner
# This script runs both test scenarios and generates allure reports

import subprocess
import sys
import os
from pathlib import Path

def run_client_demo_tests():
    """
    Run Client Demo test suite with allure reporting
    """
    # Get the current directory (Client Demo folder)
    current_dir = Path(__file__).parent
    
    # Set up paths
    python_exe = r"C:/GITHUB/R10_Pywin_Automation/Scripts/python.exe"
    allure_results_dir = current_dir / "allure-results"
    allure_report_dir = current_dir / "allure-report"
    
    # Create directories if they don't exist
    allure_results_dir.mkdir(exist_ok=True)
    allure_report_dir.mkdir(exist_ok=True)
    
    print("🚀 Starting Client Demo Test Suite with Allure Reporting")
    print("=" * 60)
    
    # Run pytest with allure
    cmd = [
        python_exe, "-m", "pytest",
        "TC001_paidout.py", "TC002_agerestiction_Scenario.py",
        "--alluredir", str(allure_results_dir),
        "--verbose",
        "--tb=short"
    ]
    
    print(f"Executing: {' '.join(cmd)}")
    print("-" * 60)
    
    try:
        # Run the tests
        result = subprocess.run(cmd, cwd=current_dir, check=False, capture_output=False)
        
        if result.returncode == 0:
            print("\n✅ All tests passed successfully!")
        else:
            print(f"\n⚠️  Tests completed with return code: {result.returncode}")
            print("   (This may indicate test failures or errors)")
        
        print("\n📊 Test execution completed!")
        print(f"📁 Allure results saved to: {allure_results_dir}")
        
        # Check if allure command-line tool is available for HTML report generation
        allure_exe = r"C:\GITHUB\R10_Pywin_Automation\Offline_lib\offline_packages\allure\allure-2.35.1\bin\allure.bat"
        
        if os.path.exists(allure_exe):
            print("\n🔧 Attempting to generate HTML report...")
            try:
                # Check if Java is available
                java_check = subprocess.run(["java", "-version"], 
                                          capture_output=True, 
                                          text=True)
                if java_check.returncode == 0:
                    # Generate HTML report
                    report_cmd = [
                        allure_exe, "generate", 
                        str(allure_results_dir), 
                        "-o", str(allure_report_dir),
                        "--clean"
                    ]
                    
                    report_result = subprocess.run(report_cmd, 
                                                 cwd=current_dir, 
                                                 check=False,
                                                 capture_output=True,
                                                 text=True)
                    
                    if report_result.returncode == 0:
                        print(f"✅ HTML report generated successfully!")
                        print(f"📄 Open: {allure_report_dir / 'index.html'}")
                    else:
                        print(f"❌ Failed to generate HTML report: {report_result.stderr}")
                else:
                    print("⚠️  Java not found. HTML report generation skipped.")
                    print("   Install Java and set JAVA_HOME to generate HTML reports.")
            except Exception as e:
                print(f"❌ Error during HTML report generation: {e}")
        else:
            print("⚠️  Allure command-line tool not found. Only JSON results available.")
        
        print("\n" + "=" * 60)
        print("📋 Test Summary:")
        print(f"   • Results format: JSON (allure-results)")
        print(f"   • Results location: {allure_results_dir}")
        if os.path.exists(allure_report_dir / "index.html"):
            print(f"   • HTML Report: {allure_report_dir / 'index.html'}")
        print("=" * 60)
        
        # Ask user if they want to view results in browser
        try:
            print("\n🌐 Would you like to view the test results in your browser?")
            print("   This will start a local web server to display the results.")
            user_input = input("   Press 'y' for Yes, any other key to skip: ").lower().strip()
            
            if user_input == 'y':
                print("🚀 Starting web server for test results...")
                
                # Create simple HTML viewer
                from serve_allure_reports import create_simple_html_viewer
                viewer_path = allure_results_dir / "index.html"
                with open(viewer_path, 'w', encoding='utf-8') as f:
                    f.write(create_simple_html_viewer())
                print(f"✅ Created HTML viewer at: {viewer_path}")
                
                # Start web server in a separate process
                import subprocess
                server_cmd = [
                    python_exe, "serve_allure_reports.py",
                    "--directory", str(allure_results_dir),
                    "--port", "8000"
                ]
                print("   Server will start in a separate window...")
                subprocess.Popen(server_cmd, cwd=current_dir)
                
        except KeyboardInterrupt:
            print("\n   Skipped web server startup.")
        except Exception as e:
            print(f"   Error starting web server: {e}")
        
        return result.returncode
        
    except Exception as e:
        print(f"❌ Error executing tests: {e}")
        return 1

if __name__ == "__main__":
    exit_code = run_client_demo_tests()
    sys.exit(exit_code)
