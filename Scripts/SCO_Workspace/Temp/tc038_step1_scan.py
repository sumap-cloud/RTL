"""
tc038_step1_scan.py — LIVE incremental build, step 1.
Login + scan all 5 iterations (Bond, Coke, BOG, Kitkat, Exclusion gift card)
for TC_038. Does NOT scan loyalty card or pay yet. Dumps the basket screen
at the end so real item descriptions/prices can be inspected before writing
promotion-price assertions.
"""
import sys
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components.Login_POS import login_pos
from Components.Add_item import add_item
from Components.Screen_identifier import dump_screen
from Components.Read_csv import get_csv_value
from Components import global_instance

TC_ID = "TC_038_VerifyOpenOffersForRegisteredCard"
BANNER = "SM"


def _get(column, iteration, fallback=""):
    v = get_csv_value("saledata", BANNER, TC_ID, iteration, column)
    if v and not str(v).startswith("Error") and v != "No matching record found.":
        return v
    return fallback


if not login_pos():
    print("LOGIN FAILED")
    sys.exit(1)

CARD_CODE = _get("Card_number", 1, "9353186777909")
print(f"Card code from CSV: {CARD_CODE}")

for it in [1, 2, 3, 4, 5]:
    ean = _get("Item_EAN", it, "")
    print(f"--- Iteration {it}: EAN(s)='{ean}' ---")
    if ean:
        add_item(ean, CARD_CODE)

print("\n=== BASKET SCREEN DUMP AFTER ALL 5 ITERATIONS ===")
win = global_instance.win
items = dump_screen(win)
for it in items:
    if it['auto_id'] or it['text']:
        print(f"[{it['control_type']}] id={it['auto_id']!r} txt={it['text']!r} en={it['enabled']}")
