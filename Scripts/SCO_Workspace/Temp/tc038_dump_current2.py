"""
tc038_dump_current2.py — quick live check of current screen state after
Choice Offer decline, to see what mode we're in (can we still add items,
or are we locked into tender flow?).
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

print("=== Top-level controls ===")
for c in win.children():
    try:
        print(f"  auto_id={c.element_info.automation_id!r} type={c.element_info.control_type} name={c.element_info.name!r} visible={c.is_visible()}")
    except Exception as e:
        print(f"  error: {e}")
