"""
TC_022_VerifyOpenOffersForUnregisteredCard.py
---------------------------------------------
TC_022 — Open Offers for Unregistered Card

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

TC_ID  = "TC_022_VerifyOpenOffersForUnregisteredCard"
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
    logger.log("  TC_022 — Open Offers for Unregistered Card", status="info")
    logger.log("=" * 70, status="info")

    EAN_IT1   = _get("Item_EAN", 1, "9356044248337;9356044248337")
    EAN_IT2   = _get("Item_EAN", 2, "9300602355692;9300602355692;9300602355692")
    EAN_IT3   = _get("Item_EAN", 3, "8720077181786;9314020603921")
    EAN_IT4   = _get("Item_EAN", 4, "9342937005316;9342937005316;9342937005316;9342937005316;9342937005316")
    CARD_CODE = _get("Card_number", 1, "9344450000000")  # Unregistered card prefix
    CARD_STAT = (_get("Card_status", 1, "Unregistered") or "").strip().lower()

    if not login_pos():
        raise RuntimeError("login_pos failed")

    for ean in [EAN_IT1, EAN_IT2, EAN_IT3, EAN_IT4]:
        if ean:
            add_item(ean, CARD_CODE)

    # Per KT: open offers apply irrespective of card.  Still scan the unregistered
    # card per scenario to confirm SCO accepts it without crashing.  EE wallet
    # open/settle is NOT expected for an Unregistered card — flag accordingly.
    if CARD_STAT.startswith("unreg"):
        logger.log("ℹ️ Unregistered card — EE wallet_open/settle NOT expected.",
                   status="info")
        if not scan_loyalty_salemode(CARD_CODE):
            logger.log("WARN — Unregistered loyalty scan rejected (expected on some cards).",
                       status="info")
        if not move_to_tendermode():
            raise RuntimeError("move_to_tendermode failed")
        if not complete_transaction():
            raise RuntimeError("complete_transaction failed")
        ee = verify_eagleeye_logs(expect_wallet_open=False, expect_wallet_settle=False)
    else:
        if not scan_loyalty_salemode(CARD_CODE):
            raise RuntimeError("scan_loyalty_salemode failed")
        if not move_to_tendermode():
            raise RuntimeError("move_to_tendermode failed")
        if not complete_transaction():
            raise RuntimeError("complete_transaction failed")
        ee = verify_eagleeye_logs(expect_wallet_open=True, expect_wallet_settle=True)

    if ee["all_passed"]:
        logger.log("PASS — TC_022 open-offer scenario completed.", status="pass")
    else:
        logger.log("FAIL — TC_022 EE verification failed.", status="fail")

    logger.log("TODO: Verify open-offer promotions on basket + Tlogs.", status="info")

except Exception as e:
    logger.log(f"FAIL TC_022 unexpected error: {e}", status="fail")
    logger.take_screenshot("TC_022_Unexpected_Error")

finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
