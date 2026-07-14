"""
tc038_dump_popup.py — dump PopupControl contents to see what's active on
screen right now, before attempting to void the transaction.
"""
import sys
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from pywinauto import Application

app = Application(backend="uia").connect(title_re=".*NCR NEXTGENUI.*")
win = app.window(title_re=".*NCR NEXTGENUI.*")
try:
    win.set_focus()
except Exception:
    pass

popup = win.child_window(auto_id="PopupControl")
print(f"PopupControl exists: {popup.exists(timeout=3)}")
w = popup.wrapper_object()
print(f"PopupControl rectangle: {w.rectangle()}")

print("\n=== PopupControl descendants ===")
for d in w.descendants():
    try:
        ct = d.element_info.control_type
        aid = d.element_info.automation_id
        name = d.element_info.name
        vis = d.is_visible()
        if vis and (name or aid):
            print(f"  [{ct}] auto_id={aid!r} name={name!r}")
    except Exception:
        continue
