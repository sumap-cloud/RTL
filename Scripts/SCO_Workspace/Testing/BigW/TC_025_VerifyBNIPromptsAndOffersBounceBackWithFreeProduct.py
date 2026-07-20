"""
TC_025_VerifyBNIPromptsAndOffersBounceBackWithFreeProduct.py
------------------------------------------------------------
TC_025 — Verify BNI Prompts and Offers Bounceback with Free Product

Scenario:
    1. Login to the POS/SCO
    2. Scan 3x eligible articles (EAN 9310015247811)
    3. Scan the BNI free product (EAN 9339423009071)
    4. Scan the loyalty card in sale mode (Card 9353179617069)
    5. Move to tender mode
    6. Verify BNI free product is redeemed (given free)
    7. Verify BNI prompt is displayed with image
    8. Complete the transaction
    9. Verify whether completed transaction is settled in EagleEye
    10. Verify EE logs
    11. Verify Tlogs
"""

import sys
import time
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components.Login_POS import login_pos
from Components.Add_item import add_item
from Components.report import logger

TC_ID = "TC_025"
BANNER = "SM"
ITERATION = 1

logger.set_tc_id(TC_ID)

# --- Test Data ----------------------------------------------------------------
# As explicitly provided by the user:
# Eligible article (x3): 9310015247811
# Free product (x1): 9339423009071
# Card code: 9353179617069
EAN_LIST = "9310015247811;9310015247811;9310015247811;9339423009071"
CARD_CODE = "9353179617069"

try:
    logger.log("=" * 70, status="info")
    logger.log("  [INCREMENTAL RUN] TC_025 — Step 1: Login and Scan Items", status="info")
    logger.log("=" * 70, status="info")

    print("Step 1: Logging in...")
    if not login_pos():
        raise RuntimeError("login_pos failed")
    print("✅ Login successful.")

    print(f"Step 2 & 3: Scanning items ({EAN_LIST})...")
    add_item(EAN_LIST, CARD_CODE)
    print("✅ Items scanned.")

except Exception as e:
    logger.log(f"❌ TC_025 unexpected error: {e}", status="fail")
    print(f"❌ TC_025 ERROR: {e}")
    logger.take_screenshot("TC_025_Unexpected_Error")

finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
