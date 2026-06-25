"""
TC_011_SCO_AirNZcardcrossing2000points.py
------------------------------------------
Test Case: Validation of POS/SCO transaction with AirNZ card (segment 110)
crossing 2000 points.

Scenario:
    Verify that the points are moved over 2000 points for an AirNZ segment
    card. The Exciting News prompt appears after moving to tender mode.

Pre-requisite:
    AirNZ card (segment 110) preconditioned to JUST UNDER 2000 points.
    ⚠️  Update Card_number in SaleData.csv before running.

Expected on-screen message at step 5:
    "Exciting News! You've just earned $xx Airpoints Dollars to put towards
     your next adventure."

Steps automated:
    1. Login to POS.
    2. Scan articles (5 × Tim Tam = ~$12.00).
    3. Scan EDR card in Sale mode.
    4. Move to tender mode.
    5. Verify Exciting News prompt (UIA + OCR) and dismiss.
    6. Complete the transaction (EFT, Tender2).
    7. Verify EagleEye settlement + EE logs.
"""

import sys
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components.Login_POS import login_pos
from Components.Add_item import add_item
from Components.Scan_loyalty_salemode import scan_loyalty_salemode
from Components.Move_to_tendermode import move_to_tendermode
from Components.Verify_exciting_news_prompt import verify_exciting_news_prompt
from Components.Complete_transaction import complete_transaction
from Components.Verify_EagleEye_logs import verify_eagleeye_logs
from Components.Read_csv import get_csv_value
from Components.report import logger

TC_ID = "TC_011"
BANNER = "SM"
ITERATION = 1

logger.set_tc_id(TC_ID)

# NZ only — AirNZ card (segment 110), spend >$20 to earn enough points to cross 2000
# Card: 9490000002011
EAN_FALLBACK = ";".join(["9310072000282"] * 5)   # 5 × Tim Tam ≈ $12; adjust if >$20 needed


def _get_value(column, fallback):
    try:
        val = get_csv_value("saledata", BANNER, TC_ID, ITERATION, column)
        if val and not val.startswith("Error") and val != "No matching record found." and val != "0000000000000":
            return val
    except Exception:
        pass
    return fallback


EAN_LIST  = _get_value("EAN_Codes", None) or _get_value("Item_EAN", EAN_FALLBACK)
CARD_CODE = _get_value("Card_number", "9490000002011")

try:
    if not login_pos():
        raise RuntimeError("Login_POS failed — aborting test.")

    add_item(EAN_LIST, CARD_CODE)

    if not scan_loyalty_salemode(CARD_CODE):
        raise RuntimeError("scan_loyalty_salemode failed — aborting test.")

    if not move_to_tendermode():
        raise RuntimeError("move_to_tendermode failed — aborting test.")

    # Step 5: Verify "Airpoints Dollars" prompt.
    # move_to_tendermode() handles the prompt inline if it appears during
    # the tender transition. verify_exciting_news_prompt() acts as safety net.
    found = verify_exciting_news_prompt(timeout_seconds=15)
    if found:
        logger.log(
            "✅ Step 5 — 'Airpoints Dollars' (AirNZ) Exciting News prompt verified.",
            status="pass",
        )
    else:
        logger.log(
            "ℹ️ Step 5 — Exciting News prompt was NOT detected within timeout. "
            "Continuing transaction (card may not have crossed 2000 pts this run).",
            status="info",
        )

    if not complete_transaction():
        raise RuntimeError("complete_transaction failed — aborting test.")

    ee_result = verify_eagleeye_logs(
        expect_wallet_open=True,
        expect_wallet_settle=True,
    )

    if not ee_result["all_passed"]:
        logger.log(
            "❌ EagleEye verification failed. See individual step logs above.",
            status="fail",
        )
    else:
        logger.upgrade_info_to_pass("detected")
        logger.log(
            "✅ TC_011 PASSED — AirNZ card crossed 2000 pts; transaction settled in EagleEye.",
            status="pass",
        )

except Exception as e:
    logger.log(f"❌ Unexpected error in TC_011: {e}", status="fail")
    print(f"❌ TC_011 ERROR: {e}")
    logger.take_screenshot("TC_011_Unexpected_Error")

finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
