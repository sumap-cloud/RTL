"""
tc038_step2_loyalty.py — LIVE incremental build, step 2.
Connects to the EXISTING in-progress SCO transaction (basket already has
11 items from step 1 — user chose NOT to void). Scans the loyalty card at
the tender prompt (Scan_loyalty_tenderprompt), then dumps the screen so we
can see promotion lines / prices for real before writing assertions.

Does NOT call login_pos() because the SCO is mid-transaction (sale mode),
not idle — login_pos()'s idle-state check would fail. Connects directly
instead, matching the same pattern used in Add_item.py / Promotion_details.py.
"""
import sys
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from pywinauto import Application
from Components import global_instance
from Components.Scan_loyalty_tenderprompt import scan_loyalty_tenderprompt
from Components.Screen_identifier import dump_screen
from Components.Read_csv import get_csv_value

TC_ID = "TC_038_VerifyOpenOffersForRegisteredCard"
BANNER = "SM"


def _get(column, iteration, fallback=""):
    v = get_csv_value("saledata", BANNER, TC_ID, iteration, column)
    if v and not str(v).startswith("Error") and v != "No matching record found.":
        return v
    return fallback


app = Application(backend="uia").connect(title_re=".*NCR NEXTGENUI.*")
win = app.window(title_re=".*NCR NEXTGENUI.*")
global_instance.app = app
global_instance.win = win
try:
    win.set_focus()
except Exception:
    pass
print("Connected to existing NCR NEXTGENUI session.")

CARD_CODE = _get("Card_number", 1, "9353186777909")
print(f"Card code: {CARD_CODE}")

result = scan_loyalty_tenderprompt(CARD_CODE)
print(f"scan_loyalty_tenderprompt returned: {result}")

print("\n=== SCREEN DUMP AFTER LOYALTY SCAN ===")
items = dump_screen(win)
for it in items:
    if it['auto_id'] or it['text']:
        print(f"[{it['control_type']}] id={it['auto_id']!r} txt={it['text']!r} en={it['enabled']}")
