"""
tc038_step3_decline_choice.py — LIVE incremental build, step 3.
Connects to the existing in-progress SCO transaction (Choice Offer popup
currently showing: "You have 2 discounts to select from"). Declines via
SkipChoiceOfferPrompt ("No, save these discounts for later") per user
direction, then dumps the screen.
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
from Components.Screen_identifier import dump_screen

app = Application(backend="uia").connect(title_re=".*NCR NEXTGENUI.*")
win = app.window(title_re=".*NCR NEXTGENUI.*")
global_instance.app = app
global_instance.win = win
try:
    win.set_focus()
except Exception:
    pass
print("Connected to existing NCR NEXTGENUI session.")

skip_btn = win.child_window(auto_id="SkipChoiceOfferPrompt", control_type="Button")
if skip_btn.exists(timeout=5):
    skip_btn.click_input()
    print("Clicked 'No, save these discounts for later' (SkipChoiceOfferPrompt).")
    time.sleep(2)
else:
    print("SkipChoiceOfferPrompt not found!")

print("\n=== SCREEN DUMP AFTER DECLINING CHOICE OFFER ===")
items = dump_screen(win)
for it in items:
    if it['auto_id'] or it['text']:
        print(f"[{it['control_type']}] id={it['auto_id']!r} txt={it['text']!r} en={it['enabled']}")
