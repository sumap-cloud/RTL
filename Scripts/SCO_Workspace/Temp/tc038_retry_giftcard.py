"""
tc038_retry_giftcard.py — standalone retry of the gift-card 'Assistance
Needed' popup handling, called directly (not nested inside
scan_loyalty_tenderprompt) so we can observe its full 20-round loop
behavior without interference from an outer script being stopped early.
"""
import sys
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from pywinauto import Application
from Components import global_instance
from Components.Add_item import _handle_giftcard_activation
from Components.Screen_identifier import dump_screen

app = Application(backend="uia").connect(title_re=".*NCR NEXTGENUI.*")
win = app.window(title_re=".*NCR NEXTGENUI.*")
global_instance.app = app
global_instance.win = win
try:
    win.set_focus()
except Exception:
    pass
print("Connected.")

result = _handle_giftcard_activation(win)
print(f"_handle_giftcard_activation returned: {result}")

print("\n=== SCREEN DUMP AFTER RETRY ===")
items = dump_screen(win)
for it in items:
    if it['auto_id'] or it['text']:
        print(f"[{it['control_type']}] id={it['auto_id']!r} txt={it['text']!r} en={it['enabled']}")
