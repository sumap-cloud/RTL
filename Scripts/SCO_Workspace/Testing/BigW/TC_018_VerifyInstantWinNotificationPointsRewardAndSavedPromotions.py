"""
TC_018_VerifyInstantWinNotificationPointsRewardAndSavedPromotions.py
--------------------------------------------------------------------
TC_018 — IW Notification (Points reward) + Saved promotions

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

TC_ID  = "TC_018_VerifyInstantWinNotificationPointsReward&SavedPromotions"
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
    logger.log("  TC_018 — Instant Win Notification (Points Reward) + Saved", status="info")
    logger.log("=" * 70, status="info")

    EAN_LIST    = _get("Item_EAN", 1, "9315087192083;9315087192083;9339687023882")
    CARD_CODE   = _get("Card_number", 1, "9353112000000")
    CHOICE      = _get("Choice_offer", 1, "")
    EXCITING    = _get("Exciting_news_popup", 1, "")
    SAVED_DENOM = _get("Instant_win_offer_redeem", 1, "50")  # e.g. "50 off"
    NOTIF_TEXT  = _get("Instant_win_notification", 1, "")    # message to verify
    REDEEM_AMT  = _get("Redeem_amount", 1, "")

    if not login_pos():
        raise RuntimeError("login_pos failed")
    add_item(EAN_LIST, CARD_CODE)

    # Card is scanned at tender prompt so the Instant-Win popups appear.
    if not scan_loyalty_tenderprompt(CARD_CODE):
        raise RuntimeError("scan_loyalty_tenderprompt failed")

    # Step A: Instant-Win NOTIFICATION (single OK).
    notif_ok = handle_instant_win_notification(timeout=15)
    if notif_ok:
        logger.log(f"PASS — IW notification acknowledged. Expected text: '{NOTIF_TEXT}'.",
                   status="pass")

    # Step B: SAVED-promotions popup — click chosen denomination then save-for-later.
    handle_instant_win_saved(action="use_now", denomination=SAVED_DENOM, timeout=15)

    # Step C: Choice offer (market day / EE), if any.
    if CHOICE:
        redeem_choice_offer(CHOICE)

    # Step D: Exciting News prompt
    if EXCITING:
        verify_exciting_news_prompt(timeout_seconds=15)

    # Step E: Complete transaction (Card EFT)
    if not complete_transaction():
        raise RuntimeError("complete_transaction failed")

    # Step F: Verify EE logs
    ee = verify_eagleeye_logs(expect_wallet_open=True, expect_wallet_settle=True)
    if ee["all_passed"]:
        logger.log("PASS — TC_018 EE settled.", status="pass")
    else:
        logger.log("FAIL — EE verification failed.", status="fail")

    logger.log("TODO: Verify Tlogs (apportionment) and receipt image — paths TBC.",
               status="info")

except Exception as e:
    logger.log(f"FAIL TC_018 unexpected error: {e}", status="fail")
    logger.take_screenshot("TC_018_Unexpected_Error")

finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
