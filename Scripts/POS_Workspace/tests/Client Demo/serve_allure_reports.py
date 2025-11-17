# Allure Report Viewer - Simple HTTP Server
# This script serves allure results and reports via localhost

import http.server
import socketserver
import webbrowser
import os
import sys
import json
from pathlib import Path
import threading
import time

def serve_allure_results(directory=None, port=8000):
    """
    Serve allure results directory via HTTP server
    
    Args:
        directory: Directory containing allure results (default: ./allure-results)
        port: Port number for HTTP server (default: 8000)
    """
    if directory is None:
        directory = Path(__file__).parent / "allure-results"
    
    directory = Path(directory).resolve()
    
    if not directory.exists():
        print(f"❌ Directory does not exist: {directory}")
        return False
    
    # Change to the directory
    os.chdir(directory.parent)
    
    # Create HTTP server
    handler = http.server.SimpleHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            print(f"🌐 Serving allure results at: http://localhost:{port}")
            print(f"📁 Directory: {directory}")
            print(f"🔗 Direct link to results: http://localhost:{port}/{directory.name}")
            print("📊 To view JSON results, navigate to the allure-results folder")
            print("⚠️  Note: This serves JSON results. For HTML reports, use allure command-line tool with Java.")
            print("\n🛑 Press Ctrl+C to stop the server")
            
            # Open browser automatically
            try:
                webbrowser.open(f"http://localhost:{port}/{directory.name}")
            except Exception as e:
                print(f"Could not open browser automatically: {e}")
            
            # Start server
            httpd.serve_forever()
            
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {port} is already in use. Try a different port.")
            return serve_allure_results(directory, port + 1)
        else:
            print(f"❌ Error starting server: {e}")
            return False
    except KeyboardInterrupt:
        print(f"\n🛑 Server stopped.")
        return True

def create_simple_html_viewer():
    """
    Create a simple HTML viewer for allure JSON results
    """
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Allure Test Results Viewer</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 30px; }
        .test-item { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; background: #fafafa; }
        .test-passed { border-left: 5px solid #28a745; }
        .test-failed { border-left: 5px solid #dc3545; }
        .test-skipped { border-left: 5px solid #ffc107; }
        .test-title { font-weight: bold; color: #333; margin-bottom: 10px; }
        .test-description { color: #666; margin-bottom: 10px; }
        .test-steps { margin-top: 10px; }
        .step { margin-left: 20px; padding: 5px 0; border-left: 2px solid #eee; padding-left: 10px; margin-bottom: 5px; }
        .step-passed { border-left-color: #28a745; }
        .step-failed { border-left-color: #dc3545; }
        .attachments { margin-top: 10px; }
        .attachment { display: inline-block; margin: 2px 5px; padding: 3px 8px; background: #007bff; color: white; text-decoration: none; border-radius: 3px; font-size: 12px; }
        .attachment:hover { background: #0056b3; }
        .metadata { margin-top: 10px; font-size: 12px; color: #999; }
        .no-results { text-align: center; color: #666; padding: 40px; }
        .file-list { margin-bottom: 20px; }
        .file-item { padding: 8px; margin: 2px 0; background: #e9ecef; border-radius: 3px; cursor: pointer; }
        .file-item:hover { background: #dee2e6; }
        .file-item.selected { background: #007bff; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 Allure Test Results Viewer</h1>
            <p>Simple viewer for Allure JSON test results</p>
        </div>
        
        <div class="file-list" id="fileList">
            <h3>Available Test Result Files:</h3>
        </div>
        
        <div id="testResults">
            <div class="no-results">
                📂 Select a test result file from the list above to view details
            </div>
        </div>
    </div>

    <script>
        // Load and display allure result files
        async function loadFiles() {
            try {
                const response = await fetch('.');
                const text = await response.text();
                const parser = new DOMParser();
                const doc = parser.parseFromString(text, 'text/html');
                const links = Array.from(doc.querySelectorAll('a')).filter(a => a.href.includes('-result.json'));
                
                const fileList = document.getElementById('fileList');
                if (links.length === 0) {
                    fileList.innerHTML = '<div class="no-results">❌ No allure result files found</div>';
                    return;
                }
                
                fileList.innerHTML = '<h3>Available Test Result Files:</h3>';
                links.forEach(link => {
                    const fileName = link.textContent;
                    const fileItem = document.createElement('div');
                    fileItem.className = 'file-item';
                    fileItem.textContent = fileName;
                    fileItem.onclick = () => loadTestResult(fileName);
                    fileList.appendChild(fileItem);
                });
                
                // Auto-load first file
                if (links.length > 0) {
                    loadTestResult(links[0].textContent);
                }
            } catch (error) {
                console.error('Error loading files:', error);
                document.getElementById('fileList').innerHTML = '<div class="no-results">❌ Error loading files</div>';
            }
        }
        
        async function loadTestResult(fileName) {
            // Update selected file
            document.querySelectorAll('.file-item').forEach(item => {
                item.classList.remove('selected');
                if (item.textContent === fileName) {
                    item.classList.add('selected');
                }
            });
            
            try {
                const response = await fetch(fileName);
                const result = await response.json();
                displayTestResult(result);
            } catch (error) {
                console.error('Error loading test result:', error);
                document.getElementById('testResults').innerHTML = '<div class="no-results">❌ Error loading test result</div>';
            }
        }
        
        function displayTestResult(result) {
            const container = document.getElementById('testResults');
            const statusClass = `test-${result.status}`;
            
            let stepsHtml = '';
            if (result.steps) {
                stepsHtml = '<div class="test-steps"><strong>Test Steps:</strong>';
                result.steps.forEach(step => {
                    const stepClass = `step-${step.status}`;
                    let attachmentsHtml = '';
                    if (step.attachments) {
                        attachmentsHtml = '<div class="attachments">' + 
                            step.attachments.map(att => `<a href="${att.source}" class="attachment" target="_blank">${att.name}</a>`).join('') + 
                            '</div>';
                    }
                    stepsHtml += `<div class="step ${stepClass}">
                        📋 ${step.name}${attachmentsHtml}
                    </div>`;
                });
                stepsHtml += '</div>';
            }
            
            let attachmentsHtml = '';
            if (result.attachments) {
                attachmentsHtml = '<div class="attachments"><strong>Attachments:</strong><br>' + 
                    result.attachments.map(att => `<a href="${att.source}" class="attachment" target="_blank">${att.name}</a>`).join('') + 
                    '</div>';
            }
            
            const duration = result.stop && result.start ? 
                `⏱️ Duration: ${((result.stop - result.start) / 1000).toFixed(2)}s` : '';
            
            container.innerHTML = `
                <div class="test-item ${statusClass}">
                    <div class="test-title">
                        ${result.status === 'passed' ? '✅' : result.status === 'failed' ? '❌' : '⚠️'} 
                        ${result.name || 'Test Result'}
                    </div>
                    ${result.description ? `<div class="test-description">${result.description}</div>` : ''}
                    ${stepsHtml}
                    ${attachmentsHtml}
                    <div class="metadata">
                        📁 Test: ${result.fullName || 'Unknown'} | 
                        🏷️ Status: ${result.status} | 
                        ${duration}
                    </div>
                </div>
            `;
        }
        
        // Load files on page load
        loadFiles();
    </script>
</body>
</html>'''
    
    return html_content

def main():
    """Main function to serve allure results"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Serve allure test results via HTTP")
    parser.add_argument("--directory", "-d", help="Directory containing allure results (default: ./allure-results)")
    parser.add_argument("--port", "-p", type=int, default=8000, help="Port number (default: 8000)")
    parser.add_argument("--create-viewer", action="store_true", help="Create simple HTML viewer")
    
    args = parser.parse_args()
    
    if args.create_viewer:
        viewer_path = Path(__file__).parent / "allure-results" / "index.html"
        viewer_path.parent.mkdir(exist_ok=True)
        with open(viewer_path, 'w', encoding='utf-8') as f:
            f.write(create_simple_html_viewer())
        print(f"✅ Created HTML viewer at: {viewer_path}")
        return
    
    serve_allure_results(args.directory, args.port)

if __name__ == "__main__":
    main()
