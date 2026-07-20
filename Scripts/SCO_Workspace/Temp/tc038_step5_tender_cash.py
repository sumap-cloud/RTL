"""
tc038_step5_tender_cash.py — click Tender2 (confirmed live as 'Cash' on
THIS screen state) to complete TC_038's transaction, then dump whatever
screen appears next. Does NOT reuse Complete_transaction.py's card-EFT
logic since that component hardcodes Tender2=Card, which contradicts our
own live dump (Tender2=Cash here) — avoiding blind reuse per no-hallucination
rule.
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
print("Connected.")

btn = win.child_window(auto_id="Tender2", control_type="Button")
if btn.exists(timeout=5):
    print(f"Tender2 label text nearby confirmed as 'Cash' from prior dump. Clicking...")
    btn.click_input()
    print("Clicked Tender2.")
else:
    print("Tender2 not found!")

time.sleep(3)
print("\n=== SCREEN DUMP AFTER TENDER2 (CASH) CLICK ===")
items = dump_screen(win)
for it in items:
    if it['auto_id'] or it['text']:
        print(f"[{it['control_type']}] id={it['auto_id']!r} txt={it['text']!r} en={it['enabled']}")
