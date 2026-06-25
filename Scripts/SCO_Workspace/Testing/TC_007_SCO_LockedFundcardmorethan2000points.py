"""
TC_007_SCO_LockedFundcardmorethan2000points.py
----------------------------------------------
Test Case: Validation of WOW redemption with registered card that has a
locked fund (segment 108) with more than 2000 points.

Scenario:
    Verify that the WOW ($10) redemption prompt is NOT displayed at the
    tender screen for a Locked Fund card — even though the card has > 2000
    points, the locked fund flag prevents redemption from being offered.
    Transaction must still settle in EagleEye.

Pre-requisite:
    Locked fund card (segment 108) with more than 2000 points.
    ⚠️  Update Card_number in SaleData.csv (setup_TC007_to_TC011_csv_data.py)
        before running.

Steps automated:
    1. Login to POS.
    2. Scan articles (5 × Tim Tam = ~$12.00).
    3. Scan EDR card in Sale mode.
    4. Move to tender mode.
    5. Verify WOW redemption prompt (Tender3) is NOT displayed.
    6. Complete the transaction (EFT, Tender2).
    7. Verify EagleEye settlement + EE logs.
"""

import sys
import time
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components.Login_POS import login_pos
from Components.Add_item import add_item
from Components.Scan_loyalty_salemode import scan_loyalty_salemode
from Components.Move_to_tendermode import move_to_tendermode
from Components.Complete_transaction import complete_transaction
from Components.Verify_EagleEye_logs import verify_eagleeye_logs
from Components.Read_csv import get_csv_value
from Components.report import logger
from Components import global_instance

TC_ID = "TC_007"
BANNER = "SM"
ITERATION = 1

logger.set_tc_id(TC_ID)

EAN_FALLBACK = ";".join(["9310072000282"] * 5)


def _get_value(column, fallback):
    try:
        val = get_csv_value("saledata", BANNER, TC_ID, ITERATION, column)
        if val and not val.startswith("Error") and val != "No matching record found." and val != "0000000000000":
            return val
    except Exception:
        pass
    return fallback


EAN_LIST  = _get_value("EAN_Codes", None) or _get_value("Item_EAN", EAN_FALLBACK)
CARD_CODE = _get_value("Card_number", "9353109564432")  # Locked fund card > 2000 pts

try:
    if not login_pos():
        raise RuntimeError("Login_POS failed — aborting test.")

    add_item(EAN_LIST, CARD_CODE)

    if not scan_loyalty_salemode(CARD_CODE):
        raise RuntimeError("scan_loyalty_salemode failed — aborting test.")

    if not move_to_tendermode():
        raise RuntimeError("move_to_tendermode failed — aborting test.")

    # Step 5: Verify WOW redemption prompt (Tender3) is NOT displayed.
    # For a locked-fund card, Tender3 (Reward Voucher) should be absent from
    # the tender screen. If it IS present, that is a test failure.
    win = global_instance.win
    time.sleep(1)  # Allow tender screen to fully render
    try:
        tender3 = win.child_window(auto_id="Tender3", control_type="Button")
        if tender3.exists(timeout=3.0):
            logger.log(
                "❌ Step 5 — WOW redemption prompt (Tender3) IS displayed for a "
                "Locked Fund card. Expected: NOT displayed.",
                status="fail",
            )
            print("❌ Step 5 — Tender3 (WOW redemption) unexpectedly present for Locked Fund card.")
            logger.take_screenshot("TC_007_Tender3_Unexpectedly_Present")
        else:
            logger.log(
                "✅ Step 5 — WOW redemption prompt (Tender3) is NOT displayed. "
                "Locked Fund card correctly suppresses redemption offer.",
                status="pass",
            )
            print("✅ Step 5 — Tender3 absent as expected for Locked Fund card.")
    except Exception as e:
        logger.log(f"⚠️ Step 5 — Could not check Tender3 presence: {e}", status="fail")
        print(f"⚠️ Step 5 — Tender3 check failed: {e}")

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
        logger.log(
            "✅ TC_007 PASSED — Locked Fund card: no redemption offered; "
            "transaction settled in EagleEye.",
            status="pass",
        )

except Exception as e:
    logger.log(f"❌ Unexpected error in TC_007: {e}", status="fail")
    print(f"❌ TC_007 ERROR: {e}")
    logger.take_screenshot("TC_007_Unexpected_Error")

finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
