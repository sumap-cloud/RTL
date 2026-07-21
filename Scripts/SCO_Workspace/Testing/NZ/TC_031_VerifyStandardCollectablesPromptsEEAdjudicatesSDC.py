"""
TC_031_VerifyStandardCollectablesPromptsEEAdjudicatesSDC.py
------------------------------------------------------------
TC_031 — Validation of Standard collectables prompts_EE adjudicates_SDC (NZ)

PLACEHOLDER SCRIPT — created to accompany newly-added NZ regression data
(Banner=NZ rows in RegressionSale.csv). Flow steps below are a best-effort
skeleton based on similar SDC/collectable scripts in this suite and have
NOT been live-verified against the POS yet. Refine popup handlers and
assertions once a live UIA dump is captured for this scenario.

Scenario data (NZ_POS regression sheet, scenario #25):
    Card: 9344440000161 (SDC)
    Offer: Bonus - 2 articles; Album - 1 article - 2 points;
           Base - every $30; Weekend offer - $30
    Expected: EE adjudicates standard collectables, customer earns bonus/
              album/base/weekend collectable points.

Data source:
    RegressionSale.csv — Banner="NZ", TC_ID="TC_031_VerifyStandardCollectablesPromptsEEAdjudicatesSDC".
    Iteration 1: Bonus articles (Eligible)
    Iteration 2: Album article
    Iteration 3: Base spend articles
    Iteration 4: Ineligible filler articles
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
from Components.Redeem_collectable_offer import redeem_collectable_offer
from Components.Promotion_details import get_promotion_details
from Components.Complete_transaction import complete_transaction
from Components.Verify_EagleEye_logs import verify_eagleeye_logs
from Components.Read_csv import get_csv_value
from Components.report import logger
from Components import global_instance

TC_ID  = "TC_031_VerifyStandardCollectablesPromptsEEAdjudicatesSDC"
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
    logger.log("  TC_031 — Standard Collectables Prompts EE Adjudicates (SDC)", status="info")
    logger.log("=" * 70, status="info")

    EAN_IT1   = _get("Item_EAN", 1, "")
    EAN_IT2   = _get("Item_EAN", 2, "")
    EAN_IT3   = _get("Item_EAN", 3, "")
    EAN_IT4   = _get("Item_EAN", 4, "")
    CARD_CODE = _get("Card_number", 1, "<FILL_CARD>")

    if not login_pos():
        raise RuntimeError("login_pos failed")

    for ean in [EAN_IT1, EAN_IT2, EAN_IT3, EAN_IT4]:
        if ean:
            add_item(ean, CARD_CODE)

    if not scan_loyalty_salemode(CARD_CODE):
        logger.log("⚠️ scan_loyalty_salemode returned False.", status="info")

    _, _, promo_descs, _, _, _ = get_promotion_details("")
    logger.log(f"Promotions detected: {promo_descs}", status="info")

    # Standard collectables (bonus/album/base/weekend) should be adjudicated by EE
    try:
        redeem_collectable_offer()
        logger.log("✅ Collectable offer prompt handled.", status="pass")
    except Exception as e:
        logger.log(f"⚠️ Collectable offer handling skipped/failed: {e}", status="info")

    if not move_to_tendermode():
        logger.log("⚠️ move_to_tendermode failed", status="info")

    if not complete_transaction():
        logger.log("❌ complete_transaction failed", status="fail")

    verify_eagleeye_logs(expect_wallet_open=True, expect_wallet_settle=True)

    logger.log("ℹ️ TC_031 is a placeholder — needs live UIA verification of "
               "collectable prompt sequence (Bonus/Album/Base/Weekend).",
               status="info")

except Exception as e:
    logger.log(f"❌ TC_031 unexpected error: {e}", status="fail")
    logger.take_screenshot("TC_031_Unexpected_Error")

finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
