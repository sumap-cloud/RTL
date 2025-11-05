import pytest
import sys
from datetime import datetime
from pathlib import Path

def pytest_html_report_title(report):
    report.title = "POS Automation Test Report"

def pytest_configure(config):
    """
    Configure pytest with metadata
    """
    # Add custom metadata directly to the config object
    metadata = {
        'Project': 'POS Automation',
        'Environment': 'Test',
        'Python Version': sys.version,
        'Test Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    setattr(config, '_metadata', metadata)

def pytest_html_report_title(report):
    """
    Set the title for the html report
    """
    report.title = "POS Automation Test Report"

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Extend the report with timing and screenshot info
    """
    outcome = yield
    report = outcome.get_result()
    
    report.description = str(item.function.__doc__)
    
    # Add timestamp to the report
    report.start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if report.when == "call":
        if report.failed:
            try:
                # If test failed, add screenshot path to the report
                test_screenshots = list(Path(item.funcargs['pytestconfig'].rootdir) \
                    .glob(f'test_screenshots/**/*failure*.png'))
                if test_screenshots:
                    report.extra = [{'name': 'Screenshot on Failure',
                                   'format': 'image',
                                   'content': test_screenshots[-1].read_bytes(),
                                   'mime_type': 'image/png'}]
            except Exception as e:
                print(f"Failed to attach screenshot to report: {e}")
