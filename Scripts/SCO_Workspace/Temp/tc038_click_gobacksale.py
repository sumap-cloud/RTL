"""
tc038_click_gobacksale.py — click GoBackSale to leave the Select Payment
Type screen and return to the basket/scan screen, then dump the resulting
screen so we can find a real cancel-all/void control.
"""
import sys
import time
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from pywinauto import Application
from Components.Screen_identifier import dump_screen

app = Application(backend="uia").connect(title_re=".*NCR NEXTGENUI.*")
win = app.window(title_re=".*NCR NEXTGENUI.*")
try:
    win.set_focus()
except Exception:
    pass

btn = win.child_window(auto_id="GoBackSale", control_type="Button")
if btn.exists(timeout=5):
    btn.click_input()
    print("Clicked GoBackSale.")
else:
    print("GoBackSale not found.")

time.sleep(2)
print("\n--- Screen dump after GoBackSale ---")
items = dump_screen(win)
for it in items:
    if it["auto_id"] or it["text"]:
        print(f"   [{it['control_type']}] id='{it['auto_id']}' text='{it['text']}' enabled={it['enabled']}")
