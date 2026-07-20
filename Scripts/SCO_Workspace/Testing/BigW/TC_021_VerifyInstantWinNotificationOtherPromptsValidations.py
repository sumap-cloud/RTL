"""
TC_021_VerifyInstantWinNotificationOtherPromptsValidations.py
-------------------------------------------------------------
TC_021 — IW Notification + Other Prompts Validations

Auto-generated skeleton (see RegressionSale.csv for data).
Refine UI handlers (Instant Win, BNI, etc.) once live UIA dumps are confirmed.
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
from Components.Complete_transaction import complete_transaction
from Components.Verify_EagleEye_logs import verify_eagleeye_logs
from Components.Read_csv import get_csv_value
from Components.report import logger
from Components import global_instance

TC_ID  = "TC_021_VerifyInstantWinNotificationOtherPromptsValidations"
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
    logger.log("  TC_021 — IW Notification + Other Prompts validations", status="info")
    logger.log("=" * 70, status="info")

    # NOTE: TC_021 is not present in RegressionSale.csv. Fallback values are
    # used until the row is added to SaleData.csv on the SMB share.
    EAN_LIST    = _get("Item_EAN", 1, "9315087192083;9315087192083;9339687023882")
    CARD_CODE   = _get("Card_number", 1, "9353112000000")
    CHOICE      = _get("Choice_offer", 1, "Market Day")
    COLLECT     = _get("Collectable_offer", 1, "")
    EXCITING    = _get("Exciting_news_popup", 1, "")
    NOTIF_TEXT  = _get("Instant_win_notification", 1, "")

    if not login_pos():
        raise RuntimeError("login_pos failed")
    add_item(EAN_LIST, CARD_CODE)

    if not scan_loyalty_tenderprompt(CARD_CODE):
        raise RuntimeError("scan_loyalty_tenderprompt failed")

    # Single-OK notification — basket should be below approval threshold so
    # only the notification variant appears.
    if not handle_instant_win_notification(timeout=15):
        logger.log("WARN — IW notification popup not present.", status="info")

    if CHOICE:
        redeem_choice_offer(CHOICE)
    if COLLECT:
        redeem_collectable_offer("Collectable", COLLECT)
    if EXCITING:
        verify_exciting_news_prompt(timeout_seconds=15)

    if not complete_transaction():
        raise RuntimeError("complete_transaction failed")

    ee = verify_eagleeye_logs(expect_wallet_open=True, expect_wallet_settle=True)
    if ee["all_passed"]:
        logger.log("PASS — TC_021 EE settled.", status="pass")
    else:
        logger.log("FAIL — EE verification failed.", status="fail")

    logger.log("TODO: Add TC_021 row in SMB SaleData.csv with real card+EANs.",
               status="info")

except Exception as e:
    logger.log(f"FAIL TC_021 unexpected error: {e}", status="fail")
    logger.take_screenshot("TC_021_Unexpected_Error")

finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
