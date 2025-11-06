"""
Pytest configuration for HTML report with screenshots
"""
import pytest
from datetime import datetime
import sys

def pytest_html_report_title(report):
    """Set the title of the HTML report"""
    report.title = "POS Automation - Happy Flow Test Report"

def pytest_configure(config):
    """Configure pytest with metadata"""
    config._metadata = {
        'Project': 'POS Automation',
        'Test Suite': 'Happy Flow - Bonus Buy Transaction',
        'Environment': 'Test',
        'Python Version': sys.version,
        'Test Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'Tester': 'Automation Framework'
    }

def pytest_html_results_table_header(cells):
    """Customize table headers"""
    cells.insert(2, '<th>Description</th>')

def pytest_html_results_table_row(report, cells):
    """Customize table rows"""
    cells.insert(2, f'<td>{getattr(report, "description", "")}</td>')

def pytest_html_report_summary(summary):
    """Add custom summary section similar to Extent Reports"""
    summary.extend([
        '<div style="margin: 20px 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">',
        '<h2 style="margin: 0 0 10px 0; font-size: 24px;">📊 Test Execution Summary</h2>',
        '<p style="margin: 5px 0; font-size: 16px;">Complete automation test report with visual evidence</p>',
        '</div>'
    ])

@pytest.hookimpl(hookwrapper=True)
def pytest_html_results_table_html(report, data):
    """Add custom CSS and JS - Extent Report style"""
    outcome = yield
    if report.passed:
        custom_code = """
        <style>
            /* === EXTENT REPORT STYLE CUSTOMIZATION === */
            
            /* Modern color scheme */
            :root {
                --primary-color: #667eea;
                --secondary-color: #764ba2;
                --success-color: #4CAF50;
                --danger-color: #f44336;
                --warning-color: #ff9800;
                --info-color: #2196F3;
            }
            
            /* Body and main container styling */
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: #f5f7fa;
            }
            
            /* Header styling */
            h1 {
                background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
                color: white !important;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                margin-bottom: 30px;
            }
            
            /* Summary section */
            #summary {
                background: white;
                padding: 25px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.08);
                margin-bottom: 30px;
            }
            
            /* Test result table */
            #results-table {
                background: white;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 2px 15px rgba(0,0,0,0.1);
            }
            
            #results-table-head {
                background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
            }
            
            #results-table-head th {
                color: white !important;
                font-weight: 600;
                padding: 15px;
                text-transform: uppercase;
                font-size: 12px;
                letter-spacing: 1px;
            }
            
            /* Result rows */
            .results-table-row {
                border-bottom: 1px solid #e0e0e0;
                transition: all 0.3s ease;
            }
            
            .results-table-row:hover {
                background: #f8f9fa;
                transform: translateX(5px);
            }
            
            /* Status badges */
            .col-result {
                font-weight: bold;
                text-transform: uppercase;
                font-size: 11px;
                letter-spacing: 0.5px;
            }
            
            .passed {
                color: var(--success-color) !important;
            }
            
            .failed {
                color: var(--danger-color) !important;
            }
            
            .skipped {
                color: var(--warning-color) !important;
            }
            
            /* Hide carousel controls */
            .media-controls { 
                display: none !important; 
                visibility: hidden !important;
            }
            
            /* Screenshot container - Extent Report style */
            .media {
                display: block !important;
                width: 100% !important;
                overflow: visible !important;
                background: white;
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
            }
            
            /* Individual screenshot containers */
            .media-container {
                display: block !important;
                position: relative !important;
                width: 100% !important;
                height: auto !important;
                margin: 25px 0 !important;
                overflow: visible !important;
                left: 0 !important;
                top: 0 !important;
                transform: none !important;
                background: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            
            /* Screenshot images - full width display */
            .media-container img {
                display: block !important;
                width: 100% !important;
                height: auto !important;
                max-width: 100% !important;
                margin: 15px 0 !important;
                border: 3px solid var(--success-color) !important;
                box-shadow: 0 4px 15px rgba(0,0,0,0.15) !important;
                border-radius: 8px !important;
                opacity: 1 !important;
                visibility: visible !important;
                position: relative !important;
                transition: transform 0.3s ease;
            }
            
            .media-container img:hover {
                transform: scale(1.02);
                box-shadow: 0 6px 20px rgba(0,0,0,0.2) !important;
            }
            
            /* Show all media items */
            .media-item {
                display: block !important;
                opacity: 1 !important;
                visibility: visible !important;
                position: relative !important;
                height: auto !important;
            }
            
            /* Screenshot labels - Extent style */
            .media-container::before {
                content: "📸 " attr(data-label);
                display: block;
                font-weight: bold;
                font-size: 16px;
                margin: 0 0 15px 0;
                color: white;
                background: linear-gradient(135deg, var(--info-color) 0%, var(--primary-color) 100%);
                padding: 12px 20px;
                border-radius: 6px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.15);
                position: relative;
            }
            
            .media-container::after {
                content: "";
                position: absolute;
                left: 15px;
                top: 50px;
                width: 4px;
                height: calc(100% - 50px);
                background: linear-gradient(180deg, var(--info-color) 0%, transparent 100%);
                border-radius: 2px;
            }
            
            /* Extra row styling */
            .extras-row {
                display: table-row !important;
                background: #fafbfc;
            }
            
            .extra {
                display: table-cell !important;
                padding: 30px !important;
            }
            
            /* Metadata section styling */
            #environment {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.08);
                margin-bottom: 20px;
            }
            
            #environment h2 {
                color: var(--primary-color);
                border-bottom: 2px solid var(--primary-color);
                padding-bottom: 10px;
                margin-bottom: 15px;
            }
            
            #environment table {
                width: 100%;
                border-collapse: separate;
                border-spacing: 0 8px;
            }
            
            #environment tr {
                background: #f8f9fa;
                transition: background 0.2s;
            }
            
            #environment tr:hover {
                background: #e9ecef;
            }
            
            #environment td {
                padding: 12px;
                border-radius: 4px;
            }
            
            /* Collapsible sections */
            .collapsible {
                cursor: pointer;
                transition: all 0.3s ease;
            }
            
            .collapsible:hover {
                background: #e3f2fd !important;
            }
            
            /* Add step numbers */
            .media-container {
                counter-increment: screenshot-counter;
            }
            
            .media-container::before {
                content: "Step " counter(screenshot-counter) ": " attr(data-label);
            }
            
            .media {
                counter-reset: screenshot-counter;
            }
            
            /* Responsive design */
            @media (max-width: 768px) {
                .media-container img {
                    max-width: 100% !important;
                }
                
                h1 {
                    font-size: 24px;
                    padding: 20px;
                }
            }
            
            /* Print styles */
            @media print {
                .media-container {
                    page-break-inside: avoid;
                }
                
                .media-container img {
                    max-width: 100%;
                    border: 1px solid #000;
                }
            }
        </style>
        <script>
            // Enhanced JavaScript for Extent-like functionality
            document.addEventListener('DOMContentLoaded', function() {
                // Force all media containers to be visible
                const mediaContainers = document.querySelectorAll('.media-container');
                mediaContainers.forEach((container, index) => {
                    container.style.display = 'block';
                    container.style.position = 'relative';
                    container.style.opacity = '1';
                    container.style.visibility = 'visible';
                    container.style.height = 'auto';
                    container.style.width = '100%';
                    container.style.left = '0';
                    container.style.top = '0';
                    container.style.transform = 'none';
                    
                    // Ensure images are fully visible
                    const img = container.querySelector('img');
                    if (img) {
                        img.style.display = 'block';
                        img.style.width = '100%';
                        img.style.height = 'auto';
                        img.style.opacity = '1';
                        img.style.visibility = 'visible';
                        
                        // Add labels from image alt text
                        if (img.alt) {
                            container.setAttribute('data-label', img.alt);
                        } else {
                            container.setAttribute('data-label', 'Screenshot ' + (index + 1));
                        }
                        
                        // Add click to zoom functionality
                        img.addEventListener('click', function() {
                            if (this.style.maxWidth === '100%' || this.style.maxWidth === '') {
                                this.style.maxWidth = 'none';
                                this.style.cursor = 'zoom-out';
                            } else {
                                this.style.maxWidth = '100%';
                                this.style.cursor = 'zoom-in';
                            }
                        });
                        img.style.cursor = 'zoom-in';
                    }
                });
                
                // Hide navigation controls
                const controls = document.querySelectorAll('.media-controls');
                controls.forEach(control => {
                    control.style.display = 'none';
                    control.style.visibility = 'hidden';
                });
                
                // Add smooth scroll to screenshots
                const links = document.querySelectorAll('a[href^="#"]');
                links.forEach(link => {
                    link.addEventListener('click', function(e) {
                        e.preventDefault();
                        const target = document.querySelector(this.getAttribute('href'));
                        if (target) {
                            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        }
                    });
                });
            });
        </script>
        """
        data.append(custom_code)

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Attach extras to the test report for pytest-html
    """
    outcome = yield
    report = outcome.get_result()
    
    # Add extras from the test item to the report
    if report.when == "call":
        # Get extras that were collected during test execution
        extras = getattr(item, "_extras", [])
        if extras:
            # pytest-html expects report.extra to be a list
            report.extra = extras
        
        # Add test description from docstring
        if hasattr(item, "function") and item.function.__doc__:
            report.description = item.function.__doc__

@pytest.fixture
def extra(request):
    """
    Fixture that provides a list to append pytest-html extras (like screenshots)
    Usage in test: extra.append(pytest_html.extras.png(image_bytes))
    """
    # Initialize extras list on the test item
    _extras = []
    request.node._extras = _extras
    yield _extras
    # Extras will be picked up by pytest_runtest_makereport hook
