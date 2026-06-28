"""
capture_popup.py
-----------------
Run this script WHILE the "Item not found" (or any unknown) popup is visible
on the SCO screen. It will dump all visible buttons and their auto_ids to
'popup_dump.txt' so we can add the correct auto_id to _dismiss_item_not_found().

Usage:
    cd "C:\Pywin\RTL Automation"
    .\Scripts\python.exe capture_popup.py

Then read popup_dump.txt and send it back so the handler can be updated.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pywinauto import Application

OUTPUT = Path(__file__).resolve().parent / "popup_dump.txt"

try:
    app = Application(backend="uia").connect(title_re=".*NCR NEXTGENUI.*")
    win = app.window(title_re=".*NCR NEXTGENUI.*")
    print("Connected to NCR NEXTGENUI window.")
except Exception as e:
    print(f"Could not connect to NCR NEXTGENUI: {e}")
    sys.exit(1)

lines = []
lines.append("=== POPUP / DIALOG DUMP ===\n")

# Walk all visible controls
try:
    all_controls = win.descendants()
    for ctrl in all_controls:
        try:
            ct = ctrl.element_info.control_type
            aid = ctrl.element_info.automation_id or ""
            title = ctrl.element_info.name or ""
            visible = ctrl.is_visible()
            if not visible:
                continue
            if ct in ("Button", "Text", "Edit", "Pane", "Window", "Dialog"):
                line = f"  [{ct}]  auto_id='{aid}'  title='{title}'"
                lines.append(line)
                print(line)
        except Exception:
            continue
except Exception as e:
    lines.append(f"Error walking controls: {e}")

OUTPUT.write_text("\n".join(lines), encoding="utf-8")
print(f"\nDump saved to: {OUTPUT}")
