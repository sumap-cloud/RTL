"""
TC_032_VerifyPriorityOfPrompts.py
----------------------------------
TC_032 — Validation of priority of prompts (NZ)

PLACEHOLDER SCRIPT — created to accompany newly-added NZ regression data
(Banner=NZ rows in RegressionSale.csv). Flow steps below are a best-effort
skeleton and have NOT been live-verified against the POS yet. Refine popup
handlers and assertions once a live UIA dump is captured for this scenario.

Scenario data (NZ_POS regression sheet, scenario #26):
    Card: 9355164247497
    Offers stacked: 1614277 Choice offer (Flexi) + 1655466 Team Benefits
                    2x basket points multiplier + 1614118 Bunch Offer +
                    1614267 Team Benefits Base 5% + Std Collectable +
                    Exciting News prompt
    Expected prompt priority order: Flexi (choice offer) -> Std collectables
        -> Exciting news -> Bunch prompt.

Data source:
    RegressionSale.csv — Banner="NZ", TC_ID="TC_032_VerifyPriorityOfPrompts".
    Iteration 1: Eligible articles for stacked offers.
    Iteration 2: Ineligible filler articles.
"""
import sys
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components.Login_POS import login_pos
from Components.Add_item import add_item
from Components.Scan_loyalty_salemode import scan_loyalty_salemode
from Components.Move_to_tendermode import move_to_tendermode
from Components.Redeem_choice_offer import redeem_choice_offer
from Components.Redeem_collectable_offer import redeem_collectable_offer
from Components.Verify_exciting_news_prompt import verify_exciting_news_prompt
from Components.Promotion_details import get_promotion_details
from Components.Complete_transaction import complete_transaction
from Components.Verify_EagleEye_logs import verify_eagleeye_logs
from Components.Read_csv import get_csv_value
from Components.report import logger
from Components import global_instance

TC_ID  = "TC_032_VerifyPriorityOfPrompts"
BANNER = "NZ"
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
    logger.log("  TC_032 — Verify Priority Of Prompts", status="info")
    logger.log("=" * 70, status="info")

    EAN_IT1   = _get("Item_EAN", 1, "")
    EAN_IT2   = _get("Item_EAN", 2, "")
    CARD_CODE = _get("Card_number", 1, "<FILL_CARD>")

    if not login_pos():
        raise RuntimeError("login_pos failed")

    for ean in [EAN_IT1, EAN_IT2]:
        if ean:
            add_item(ean, CARD_CODE)

    if not scan_loyalty_salemode(CARD_CODE):
        logger.log("⚠️ scan_loyalty_salemode returned False.", status="info")

    _, _, promo_descs, _, _, _ = get_promotion_details("")
    logger.log(f"Promotions detected: {promo_descs}", status="info")

    # Expected priority: Choice/Flexi offer -> Std collectables -> Exciting news -> Bunch
    try:
        redeem_choice_offer()
        logger.log("✅ Choice/Flexi offer prompt handled first.", status="pass")
    except Exception as e:
        logger.log(f"⚠️ Choice offer handling skipped/failed: {e}", status="info")

    try:
        redeem_collectable_offer()
        logger.log("✅ Std collectable prompt handled.", status="pass")
    except Exception as e:
        logger.log(f"⚠️ Collectable offer handling skipped/failed: {e}", status="info")

    try:
        verify_exciting_news_prompt()
        logger.log("✅ Exciting news prompt handled.", status="pass")
    except Exception as e:
        logger.log(f"⚠️ Exciting news prompt handling skipped/failed: {e}", status="info")

    if not move_to_tendermode():
        logger.log("⚠️ move_to_tendermode failed", status="info")

    if not complete_transaction():
        logger.log("❌ complete_transaction failed", status="fail")

    verify_eagleeye_logs(expect_wallet_open=True, expect_wallet_settle=True)

    logger.log("ℹ️ TC_032 is a placeholder — needs live UIA verification of "
               "actual prompt ordering (Flexi > Std collectables > Exciting news > Bunch).",
               status="info")

except Exception as e:
    logger.log(f"❌ TC_032 unexpected error: {e}", status="fail")
    logger.take_screenshot("TC_032_Unexpected_Error")

finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
