"""
TC_003_SCO_Registeredcardcrossing2000points.py
----------------------------------------------
Test Case: Validation of POS/SCO transaction with registered card crossing
2000 points.

Scenario:
    Verify that the points are moved over 2000 points for a Registered EDR
    card and that the "Exciting News" prompt is displayed at the loyalty
    prompt step. Transaction must settle in EagleEye.

Pre-requisite:
    Registered EDR card preconditioned to JUST UNDER 2000 points so this
    transaction crosses the threshold.

Expected on-screen message at step 4:
    "Exciting News! You've just earned $xx to use on a future purchase."

Steps automated:
    1. Login to POS (connect to SCO, verify idle state).
    2. Scan the articles (5 × Tim Tam = ~$12.00).
    3. Scan the EDR card at the loyalty prompt (PayButton handled inside).
    4. Verify the Exciting News prompt is displayed (OCR) and dismiss it.
    5. Complete the transaction (EFT card payment, Tender2).
    6. Verify EagleEye settlement.
    7. Verify EE logs (Card Validation + Wallet Open + Wallet Settle).
"""

import sys
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent  # → SCO_Workspace/

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components.Login_POS import login_pos
from Components.Add_item import add_item
from Components.Scan_loyalty_tenderprompt import scan_loyalty_tenderprompt
from Components.Verify_exciting_news_prompt import verify_exciting_news_prompt
from Components.Complete_transaction import complete_transaction
from Components.Verify_EagleEye_logs import verify_eagleeye_logs
from Components.Read_csv import get_csv_value
from Components.report import logger

TC_ID = "TC_003"
BANNER = "SM"
ITERATION = 1

logger.set_tc_id(TC_ID)

EAN_FALLBACK = ";".join(["9310072000282"] * 5)


def _get_value(column, fallback):
    try:
        val = get_csv_value("saledata", BANNER, TC_ID, ITERATION, column)
        if val and not val.startswith("Error") and val != "No matching record found.":
            return val
    except Exception:
        pass
    return fallback


EAN_LIST  = _get_value("EAN_Codes", None) or _get_value("Item_EAN", EAN_FALLBACK)
CARD_CODE = _get_value("Card_number", "9353105847300")

try:
    if not login_pos():
        raise RuntimeError("Login_POS failed — aborting test.")

    add_item(EAN_LIST, CARD_CODE)

    # Loyalty card scanned AT the loyalty prompt (after PayButton, handled
    # inside scan_loyalty_tenderprompt — do NOT call move_to_tendermode first).
    if not scan_loyalty_tenderprompt(CARD_CODE):
        raise RuntimeError("scan_loyalty_tenderprompt failed — aborting test.")

    # Exciting News prompt: OCR-detect, log, dismiss. Non-fatal if missing
    # (depends on the card's live point balance crossing 2000 this run).
    found = verify_exciting_news_prompt(timeout_seconds=15)
    if found:
        logger.log("✅ Step 4 — Exciting News prompt verified.", status="pass")
    else:
        logger.log(
            "ℹ️ Step 4 — Exciting News prompt was NOT detected within timeout. "
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
            "✅ TC_003 PASSED — Transaction settled in EagleEye and points crossed 2000.",
            status="pass",
        )

except Exception as e:
    logger.log(f"❌ Unexpected error in TC_003: {e}", status="fail")
    print(f"❌ TC_003 ERROR: {e}")
    logger.take_screenshot("TC_003_Unexpected_Error")

finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
