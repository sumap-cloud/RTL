"""
Step 3 — Scan loyalty card 9353180804441 in SALE MODE.
Basket is already at $206. This script re-attaches to the live SCO,
sets global_instance.win, scans the card, then dumps the screen.
"""
import sys
import time
sys.path.insert(0, '.')

from pywinauto import Application
from Components import global_instance
from Components.Scan_loyalty_salemode import scan_loyalty_salemode
from Components.report import logger

TC_ID = "TC_018_VerifyInstantWinNotificationPointsReward&SavedPromotions"
logger.set_tc_id(TC_ID)
CARD_CODE = "9353180804441"

# Re-attach to live SCO window
app = Application(backend="uia").connect(title_re=".*NCR NEXTGENUI.*")
win = app.window(title_re=".*NCR NEXTGENUI.*")
global_instance.app = app
global_instance.win = win
print("✅ Re-attached to NCR NEXTGENUI window.")

# Step 3: scan loyalty card in sale mode
print(f"\n▶ Scanning loyalty card {CARD_CODE} in sale mode…")
result = scan_loyalty_salemode(CARD_CODE)
print(f"scan_loyalty_salemode returned: {result}")

# Wait for popups to appear
time.sleep(2)

# Dump live screen
print("\n=== LIVE SCREEN DUMP after loyalty scan ===")
for c in win.descendants():
    try:
        aid = c.element_info.automation_id
        txt = c.window_text()[:80]
        en  = c.is_enabled()
        ct  = c.element_info.control_type
        if aid or txt:
            print(f"  [{ct}] id={repr(aid)} txt={repr(txt)} en={en}")
    except Exception:
        pass

logger.save()
print(f"\nReport saved to: {logger.updated_path}")
