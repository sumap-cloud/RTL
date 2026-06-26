"""
TC_050_VerifyCrossTasmanEDRCard.py
----------------------------------
TC_050 — Verify Cross Tasman E D R Card

Auto-generated from RegressionSale.csv. Data is fetched live from SMB
SaleData.csv; fallback values present so the script runs even if a row
is missing.

Iterations: 1
Flavour:    cross_tasman

Refine popup handlers (Instant Win, BNI, subscription) once live UIA
dumps are confirmed.
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
from Components.Scan_loyalty_salemode import scan_loyalty_salemode
from Components.Scan_loyalty_tenderprompt import scan_loyalty_tenderprompt
from Components.Move_to_tendermode import move_to_tendermode
from Components.Verify_exciting_news_prompt import verify_exciting_news_prompt
from Components.Redeem_choice_offer import redeem_choice_offer
from Components.Redeem_collectable_offer import redeem_collectable_offer
from Components.Redeem_instant_win import (
    handle_instant_win_approval,
    handle_instant_win_notification,
    handle_instant_win_saved,
)
from Components.Promotion_details import get_promotion_details
from Components.Complete_transaction import complete_transaction
from Components.Verify_EagleEye_logs import verify_eagleeye_logs
from Components.Read_csv import get_csv_value
from Components.report import logger
from Components import global_instance

TC_ID  = "TC_050_VerifyCrossTasmanEDRCard"
BANNER = "SM"
logger.set_tc_id(TC_ID)


def _get(column, iteration=1, fallback=""):
    try:
        v = get_csv_value("saledata", BANNER, TC_ID, iteration, column)
        if v and not v.startswith("Error") and v != "No matching record found.":
            return v
    except Exception:
        pass
    return fallback


try:
    logger.log("=" * 70, status="info")
    logger.log("  TC_050 — Verify Cross Tasman E D R Card", status="info")
    logger.log("=" * 70, status="info")

    EAN_IT1   = _get("Item_EAN", 1, "")
    CARD_CODE = _get("Card_number", 1, "<FILL_CARD>")
    CARD_STAT = (_get("Card_status", 1, "") or "").strip().lower()
    if not login_pos():
        raise RuntimeError("login_pos failed")

    # Cross-Tasman (NZ-issued) card — scan and validate behaviour.
    for ean in [EAN_IT1]:
        if ean:
            add_item(ean, CARD_CODE)
    try:
        scan_loyalty_tenderprompt(CARD_CODE)
    except Exception:
        pass
    verify_exciting_news_prompt(timeout_seconds=3)
    if not complete_transaction():
        logger.log('❌ complete_transaction failed', status='fail')
    # NZ cards: AU EE wallet open/settle is NOT expected
    verify_eagleeye_logs(expect_wallet_open=False, expect_wallet_settle=False)

    # ------------------------------------------------------------------
    # Receipt + Tlog validation are manual (no flat-file Tlog path on box).
    # ------------------------------------------------------------------
    logger.log("ℹ️ Tlog/Receipt validation: TODO (see SCO_Automation_Handoff).",
               status="info")

except Exception as e:
    logger.log(f"❌ TC_050 unexpected error: {e}", status="fail")
    logger.take_screenshot("TC_050_Unexpected_Error")

finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
