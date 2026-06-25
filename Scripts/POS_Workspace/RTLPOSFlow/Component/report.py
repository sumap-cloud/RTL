import datetime
from pathlib import Path
from pywinauto import Application
from PIL import ImageGrab

class HTMLTestLogger:
    def __init__(self, report_path="C:\\GitHub\\R10_Pywin_Automation\\Scripts\\POS_Workspace\\RTLPOSFlow\\Results"):
        self.report_path = Path(report_path)
        self.entries = []
        self.start_time = datetime.datetime.now()
        self.tc_id = ""
        self.updated_path = self.report_path

    def set_tc_id(self, tc_id):
        """Set the Test Case ID that will appear as the HTML report title."""
        self.tc_id = str(tc_id) if tc_id else ""

    def log(self, action, element=None, status="info", screenshot=None):
        # If failed and no screenshot, take one automatically
        if status and status.lower() == "fail" and screenshot is None:
            screenshot = self.take_screenshot(f"failstep_{len(self.entries)+1}")
        entry = {
            "time": datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "action": action,
            "element": str(element) if element else "",
            "status": status,
            "screenshot": screenshot
        }
        self.entries.append(entry)
    
    def save(self):
        title_text = self.tc_id if self.tc_id else "Pywinauto Test Report"
        # Count total and failed steps
        total_steps = len(self.entries)
        failed_steps = sum(1 for e in self.entries if e.get("status", "").lower() == "fail")
        # Determine output file path: use <tc_id>.html inside the Results folder if tc_id set
        base_dir = self.report_path if self.report_path.is_dir() or self.report_path.suffix == "" else self.report_path.parent
        base_dir.mkdir(parents=True, exist_ok=True)
        if self.tc_id:
            safe_name = "".join(c for c in self.tc_id if c.isalnum() or c in ("_", "-", ".")) or "report"
            target_path = Path(base_dir) / f"{safe_name}.html"
        else:
            target_path = Path(base_dir) / "report.html"
        self.updated_path = target_path
        # Professional HTML/CSS
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title_text} - {self.start_time.strftime('%Y-%m-%d %H:%M')}</title>
    <style>
        body {{ background: #f7f9fa; font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; }}
        .header {{ background: #283593; color: #fff; padding: 24px 0 12px 0; text-align: center; box-shadow: 0 2px 8px #0001; }}
        .summary-bar {{ background: #fff; margin: 0 auto 18px auto; max-width: 900px; border-radius: 8px; box-shadow: 0 2px 8px #0001; display: flex; justify-content: center; align-items: center; gap: 32px; padding: 16px 0; font-size: 1.1em; }}
        .summary-bar .total {{ color: #283593; font-weight: bold; }}
        .summary-bar .failed {{ color: #c62828; font-weight: bold; }}
        .summary-bar .passed {{ color: #388e3c; font-weight: bold; }}
        table {{ border-collapse: separate; border-spacing: 0; width: 90%; margin: 0 auto 32px auto; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 12px #0002; }}
        th, td {{ border: none; padding: 10px 12px; text-align: left; }}
        th {{ background: #3949ab; color: #fff; font-size: 1.05em; }}
        tr:nth-child(even) {{ background: #f4f6fb; }}
        tr:nth-child(odd) {{ background: #e8eaf6; }}
        tr:hover {{ background: #d1c4e9; }}
        .pass {{ background: #e8f5e9 !important; color: #388e3c; font-weight: bold; }}
        .fail {{ background: #ffebee !important; color: #c62828; font-weight: bold; }}
        .info {{ background: #e3f2fd !important; color: #1565c0; font-weight: bold; }}
        td.status-cell {{ text-align: center; font-size: 1.05em; }}
        img {{ max-width: 320px; max-height: 180px; border-radius: 4px; border: 1px solid #bbb; box-shadow: 0 1px 4px #0002; }}
        .footer {{ text-align: center; color: #888; font-size: 0.98em; margin-bottom: 18px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1 style="margin-bottom: 0.2em;">{title_text}</h1>
        <div>Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}</div>
    </div>
    <div class="summary-bar">
        <span class="total">Total Steps: {total_steps}</span>
        <span class="failed">Failed Steps: {failed_steps}</span>
        <span class="passed">Passed Steps: {total_steps - failed_steps}</span>
    </div>
    <table>
        <tr><th>Time</th><th>Action</th><th>Element</th><th>Status</th><th>Screenshot</th></tr>
        {"".join(self._row(e) for e in self.entries)}
    </table>
    <div class="footer">
        Report generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
</body>
</html>"""
        self.updated_path.write_text(html, encoding="utf-8")

    def _row(self, entry):
        img_link = ""
        if entry["screenshot"]:
            # Make screenshot path relative to the HTML report file
            try:
                rel_path = Path(entry["screenshot"]).relative_to(self.updated_path.parent)
            except Exception:
                rel_path = entry["screenshot"]
            img_link = f'<a href="{rel_path}" target="_blank">View Screenshot</a>'
        return f"""<tr class=\"{entry['status']}\">\n            <td>{entry['time']}</td>\n            <td>{entry['action']}</td>\n            <td>{entry['element']}</td>\n            <td class='status-cell'>{entry['status'].upper()}</td>\n            <td>{img_link}</td>\n        </tr>"""
    
    def take_screenshot(self, img_name):
        """Utility method to take a screenshot and return the file path."""
        base_dir = self.report_path if self.report_path.is_dir() or self.report_path.suffix == "" else self.report_path.parent
        if self.tc_id:
            screenshot_path = Path(base_dir) / self.tc_id / f"{img_name}.png"
        else:
            screenshot_path = Path(base_dir) / f"{img_name}.png"
        screenshot_path.parent.mkdir(parents=True, exist_ok=True)
        ImageGrab.grab().save(screenshot_path)
        return str(screenshot_path)

# Shared singleton logger to use across the project
# logger = HTMLTestLogger("C:\\GitHub\\R10_Pywin_Automation\\results.html")
logger = HTMLTestLogger("./Scripts\\POS_Workspace\\RTLPOSFlow\\Results")