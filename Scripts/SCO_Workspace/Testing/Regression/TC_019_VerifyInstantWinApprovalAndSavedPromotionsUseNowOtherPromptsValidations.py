"""
TC_019_VerifyInstantWinApprovalAndSavedPromotionsUseNowOtherPromptsValidations.py
---------------------------------------------------------------------------------
TC_019 — IW Approval Use-Now + Saved + Other Prompts

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

TC_ID  = "TC_019_VerifyInstantWinApproval&SavedPromotionsUseNowOtherPromptsValidations"
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
    logger.log("  TC_019 — Instant Win Approval (USE NOW) + Saved + other prompts", status="info")
    logger.log("=" * 70, status="info")

    EAN_IT1    = _get("Item_EAN", 1, "9300677010670;9300677011523;9300677010663")
    EAN_IT2    = _get("Item_EAN", 2, "9300633594176;9300633594176")
    EAN_IT3    = _get("Item_EAN", 3, "9315087192083;9315087192083;9339687023882")
    EAN_IT4    = _get("Item_EAN", 4, "8414775016975;8414775016975")
    CARD_CODE  = _get("Card_number", 1, "9353105915450")
    CHOICE     = _get("Choice_offer", 1, "Market Day Mobile")
    COLLECT    = _get("Collectable_offer", 1, "")
    SAVED_DEN  = _get("Instant_win_offer_redeem", 1, "50")
    IW_APPR    = _get("Instant_win_offer", 1, "")

    if not login_pos():
        raise RuntimeError("login_pos failed")

    # Scan all iterations of articles (eligible + ineligible + restricted)
    for ean in [EAN_IT1, EAN_IT2, EAN_IT3, EAN_IT4]:
        if ean:
            add_item(ean, CARD_CODE)

    if not scan_loyalty_tenderprompt(CARD_CODE):
        raise RuntimeError("scan_loyalty_tenderprompt failed")

    # Step A: IW APPROVAL — click Use Now per scenario.
    if not handle_instant_win_approval(action="use_now", timeout=20):
        logger.log("WARN — IW approval popup not handled or not present.", status="info")

    # Step B: SAVED-promotions popup — use_now on chosen denomination, save remainder.
    handle_instant_win_saved(action="use_now", denomination=SAVED_DEN, timeout=15)

    # Step C: Choice offer (Market Day)
    if CHOICE:
        redeem_choice_offer(CHOICE)

    # Step D: Bunch / collectable offers if any
    if COLLECT:
        redeem_collectable_offer("Collectable", COLLECT)

    if not complete_transaction():
        raise RuntimeError("complete_transaction failed")

    ee = verify_eagleeye_logs(expect_wallet_open=True, expect_wallet_settle=True)
    if ee["all_passed"]:
        logger.log("PASS — TC_019 EE settled.", status="pass")
    else:
        logger.log("FAIL — EE verification failed.", status="fail")

    logger.log("TODO: Verify Tlogs apportionment + receipt image.", status="info")

except Exception as e:
    logger.log(f"FAIL TC_019 unexpected error: {e}", status="fail")
    logger.take_screenshot("TC_019_Unexpected_Error")

finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
