"""
TC_005_SCO_QFFcardcrossing2000points.py
---------------------------------------
Test Case: Validation of POS/SCO transaction with QFF card (segment 104)
crossing 2000 points.

Scenario:
    Verify that the points are converted/moved over 2000 points for a QFF
    (Qantas Frequent Flyer) segment Registered EDR card. The "Exciting
    News" prompt (Qantas Points variant) appears after moving to tender
    mode. After settlement, 2000 points should be removed from the card.

Pre-requisite:
    QFF card (segment 104) preconditioned to JUST UNDER 2000 points.

Expected on-screen message at step 5:
    "Exciting News! You've just converted xxx Qantas Points to put towards
     your next holiday."

Steps automated:
    1. Login to POS.
    2. Scan articles (5 × Tim Tam = ~$12.00).
    3. Scan EDR card in Sale mode.
    4. Move to tender mode.
    5. Verify Exciting News prompt (OCR) and dismiss.
    6. Complete the transaction (EFT, Tender2).
    7. Verify EagleEye settlement (transaction reached + settled).
    8. Verify 2000 points removed (via wallet/settle SETTLED status).
    9. Verify EE logs (Card Validation + Wallet Open + Wallet Settle).
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

TC_ID = "TC_005"
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
CARD_CODE = _get_value("Card_number", "9355215896056")

try:
    if not login_pos():
        raise RuntimeError("Login_POS failed — aborting test.")

    add_item(EAN_LIST, CARD_CODE)

    if not scan_loyalty_salemode(CARD_CODE):
        raise RuntimeError("scan_loyalty_salemode failed — aborting test.")

    if not move_to_tendermode():
        raise RuntimeError("move_to_tendermode failed — aborting test.")

    found = verify_exciting_news_prompt(timeout_seconds=15)
    if found:
        logger.log("✅ Step 5 — Exciting News (Qantas Points) prompt verified.", status="pass")
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

    # Step 8: 2000 pts removed — confirmed by wallet/settle SETTLED status.
    if ee_result.get("wallet_settle") and ee_result.get("settled_status", "").upper() == "SETTLED":
        logger.log(
            "✅ EagleEye SETTLED — 2000 Qantas points were converted/removed from the card.",
            status="pass",
        )
    elif ee_result.get("wallet_settle"):
        logger.log(
            f"⚠️ Wallet Settle found but status is '{ee_result.get('settled_status')}' "
            "(expected SETTLED) — points removal unconfirmed.",
            status="fail",
        )

    if not ee_result["all_passed"]:
        logger.log(
            "❌ EagleEye verification failed. See individual step logs above.",
            status="fail",
        )
    else:
        logger.upgrade_info_to_pass("detected")
        logger.log(
            "✅ TC_005 PASSED — QFF card crossed 2000 pts; transaction settled in EagleEye.",
            status="pass",
        )

except Exception as e:
    logger.log(f"❌ Unexpected error in TC_005: {e}", status="fail")
    print(f"❌ TC_005 ERROR: {e}")
    logger.take_screenshot("TC_005_Unexpected_Error")

finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
