"""
tc022_step1_scan.py — LIVE BUILD STEP 1 for TC_022
Login + scan all 5 iterations (Bond, Coke, BOG, Kitkat, Exclusion GC).
Stops here so we can observe the basket state before proceeding further.
"""
import sys
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components.Login_POS import login_pos
from Components.Add_item import add_item
from Components.Read_csv import get_csv_value
from Components.report import logger
from Components import global_instance

TC_ID = "TC_022_VerifyOpenOffersForUnregisteredCard"
BANNER = "SM"
logger.set_tc_id(TC_ID)


def _get(column, iteration=1, fallback=""):
    try:
        v = get_csv_value("saledata", BANNER, TC_ID, iteration, column)
        if v and not str(v).startswith("Error") and v != "No matching record found.":
            return v
    except Exception:
        pass
    return fallback


CARD_CODE = _get("Card_number", 1, "9344450008836")
print(f"Card code: {CARD_CODE}")

if not login_pos():
    raise RuntimeError("login_pos failed")

for it in [1, 2, 3, 4, 5]:
    ean = _get("Item_EAN", it, "")
    if ean:
        print(f"--- Scanning iteration {it}: {ean} ---")
        add_item(ean, CARD_CODE)

print("✅ Step 1 complete — all 5 iterations scanned.")
logger.save()
