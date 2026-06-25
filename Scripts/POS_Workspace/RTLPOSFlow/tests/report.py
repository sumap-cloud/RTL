import datetime
from pathlib import Path
from pywinauto import Application
 
class HTMLTestLogger:
    def __init__(self, report_path="C:\\GitHub\\R10_Pywin_Automation\\report.html"):
        self.report_path = Path(report_path)
        self.entries = []
        self.start_time = datetime.datetime.now()
    
    def log(self, action, element=None, status="info", screenshot=None):
        entry = {
            "time": datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "action": action,
            "element": str(element) if element else "",
            "status": status,
            "screenshot": screenshot
        }
        self.entries.append(entry)
    
    def save(self):
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Test Report - {self.start_time.strftime("%Y-%m-%d %H:%M")}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background: #4CAF50; color: white; }}
        .pass {{ background: #dff0d8; }}
        .fail {{ background: #f2dede; }}
        .info {{ background: #d9edf7; }}
        img {{ max-width: 400px; cursor: pointer; }}
    </style>
</head>
<body>
    <h1>Pywinauto Test Report</h1>
    <p>Started: {self.start_time}</p>
    <table>
        <tr><th>Time</th><th>Action</th><th>Element</th><th>Status</th><th>Screenshot</th></tr>
        {"".join(self._row(e) for e in self.entries)}
    </table>
</body>
</html>"""
        self.report_path.write_text(html, encoding="utf-8")
    
    def _row(self, entry):
        img = f'<img src="{entry["screenshot"]}">' if entry["screenshot"] else ""
        return f"""<tr class="{entry['status']}">
            <td>{entry['time']}</td>
            <td>{entry['action']}</td>
            <td>{entry['element']}</td>
            <td>{entry['status'].upper()}</td>
            <td>{img}</td>
        </tr>"""
# Shared singleton logger to use across the project
logger = HTMLTestLogger("C:\\GitHub\\R10_Pywin_Automation\\results.html")
