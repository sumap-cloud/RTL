"""
tc038_step4_promo_details.py — LIVE incremental build, step 4.
Connects to the existing in-progress SCO transaction (loyalty scanned,
choice offer declined). Calls get_promotion_details() — the authoritative
component that walks CartReceipt.children() (immune to on-screen list
virtualization, unlike raw dump_screen) — to see the REAL item/promo
descriptions and prices before writing any price-math assertions.
"""
import sys
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from pywinauto import Application
from Components import global_instance
from Components.Promotion_details import get_promotion_details

app = Application(backend="uia").connect(title_re=".*NCR NEXTGENUI.*")
win = app.window(title_re=".*NCR NEXTGENUI.*")
global_instance.app = app
global_instance.win = win
try:
    win.set_focus()
except Exception:
    pass
print("Connected to existing NCR NEXTGENUI session.")

expected_promos = ("Buy any Bonds product and get 10% off;"
                    "New Price_Buy 2 Coke For $1;"
                    "Buy Epson NX230 Printer to get Epson 91N Magenta Catridge Ink for free;"
                    "Buy 5 KitKat get $5 off")

result = get_promotion_details(expected_promos)
(item_descriptions, item_prices, promotion_descriptions, promotion_prices,
 matched_promotion_prices, missing_promotions) = result

print("\n=== RESULT ===")
print("item_descriptions:", item_descriptions)
print("item_prices:", item_prices)
print("promotion_descriptions:", promotion_descriptions)
print("promotion_prices:", promotion_prices)
print("matched_promotion_prices:", matched_promotion_prices)
print("missing_promotions:", missing_promotions)
print("global_instance.loyalty_points:", global_instance.loyalty_points)
