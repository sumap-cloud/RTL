"""
tc038_step2b_scan_loyalty_direct.py — we are ALREADY at the "Select Payment
Type" screen (PayButton + gift-card popups already handled by earlier
scripts). This picks up exactly where scan_loyalty_tenderprompt() would be
at its Step 3: scan the loyalty card directly using the same shared
scan_item() component, then observe what happens.
"""
import sys
import time
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from pywinauto import Application
from Components import global_instance
from Components.Scan_item import scan_item
from Components.Screen_identifier import dump_screen, identify_screen

app = Application(backend="uia").connect(title_re=".*NCR NEXTGENUI.*")
win = app.window(title_re=".*NCR NEXTGENUI.*")
global_instance.app = app
global_instance.win = win
try:
    win.set_focus()
except Exception:
    pass
print("Connected.")

screen = identify_screen(win, verbose=True)
print(f"Current screen before loyalty scan: {screen}")

CARD_CODE = "9353186777909"
print(f"Scanning loyalty card: {CARD_CODE}")
scan_item(win, CARD_CODE, label="Loyalty card (tender prompt)")

time.sleep(3)
print("\n=== SCREEN DUMP AFTER LOYALTY SCAN ===")
items = dump_screen(win)
for it in items:
    if it['auto_id'] or it['text']:
        print(f"[{it['control_type']}] id={it['auto_id']!r} txt={it['text']!r} en={it['enabled']}")
