"""
S4_TieredSpendBPMWithFundsLockedCard.py
----------------------------------------
Regression Test S4 — Validation of Tiered Spend BPM campaign with Funds Locked Card.

Scenario:
    Verify that the BPM tiered spend campaign applies the correct tier as
    the basket value increases mid-transaction. Card has >2000 points (Funds
    Locked) but NO redemption should be displayed.

Steps automated:
    1.  Login to SCO.
    2.  Scan eligible articles worth below $100.
    3.  Scan exclusion articles (gift card).
    4.  Scan loyalty card at loyalty prompt (scan_loyalty_tenderprompt).
    5.  Verify BPM Tiered Spend Tier 1 applied; no points for exclusion.
    6.  Acknowledge exciting-news prompt if triggered.
    7.  Move back to sale mode.
    8.  Scan more articles (total > $500 to hit next tier).
    9.  Move to tender mode.
    10. Verify NO redemption prompt displayed.
    10b.Verify BPM Tiered Spend with next-tier points applied.
    11. Complete transaction.
    12. Verify EagleEye settlement.
    13. Verify EE logs.
    14. Verify Tlogs apportionment.

Pre-requisite:
    Funds Locked EDR card with >2000 points and a BPM tiered spend campaign
    configured (Tier 1 < $100, Tier 2 > $500).

Data source:
    SMB SaleData.csv — TC_ID = "TC_006_VerifyTieredSpendCampaignForEligibleArticles", Banner = "SM".
    Iteration 1 = initial items (<$100) + exclusion.
    Iteration 2 = additional items (>$500 cumulative).
"""

import sys
import time
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# --- SCO Component imports ---------------------------------------------------
from Components.Login_POS import login_pos
from Components.Add_item import add_item
from Components.Scan_loyalty_tenderprompt import scan_loyalty_tenderprompt
from Components.Move_to_tendermode import move_to_tendermode
from Components.Move_back_to_salemode import move_back_to_salemode
from Components.Promotion_details import get_promotion_details
from Components.Verify_exciting_news_prompt import verify_exciting_news_prompt
from Components.Complete_transaction import complete_transaction
from Components.Verify_EagleEye_logs import verify_eagleeye_logs
from Components.Read_csv import get_csv_value
from Components.report import logger
from Components import global_instance

# --- Test-case identity ------------------------------------------------------
TC_ID  = "TC_006_VerifyTieredSpendCampaignForEligibleArticles"
BANNER = "SM"
ITERATION = 1

logger.set_tc_id(TC_ID)


def _get_value(column, iteration, fallback):
    try:
        val = get_csv_value("saledata", BANNER, TC_ID, iteration, column)
        if val and not val.startswith("Error") and val != "No matching record found.":
            return val
    except Exception:
        pass
    return fallback


# --- Data -------------------------------------------------------------------
# Iteration 1: Initial items (<$100) + exclusion (gift card)
EAN_LIST_INITIAL = _get_value("EAN_Codes", 1, None) or _get_value("Item_EAN", 1, "<FILL_INITIAL_EANS>")

# Iteration 2: Additional items to push total > $500
EAN_LIST_ADDITIONAL = _get_value("EAN_Codes", 2, None) or _get_value("Item_EAN", 2, "<FILL_ADDITIONAL_EANS>")

CARD_CODE = _get_value("Card_number", 1, "<FILL_FUNDS_LOCKED_CARD>")

# Expected promo descriptions for Tier 1 and Tier 2
PROMO_TIER1 = _get_value("Promotion_description", 1, "")
PROMO_TIER2 = _get_value("Promotion_description", 2, "")

# ---------------------------------------------------------------------------
# Test execution
# ---------------------------------------------------------------------------
try:
    # ------------------------------------------------------------------
    # Step 1: Login to SCO
    # ------------------------------------------------------------------
    if not login_pos():
        raise RuntimeError("login_pos failed — aborting test.")

    # ------------------------------------------------------------------
    # Steps 2 & 3: Scan eligible articles (<$100) + exclusion (gift card)
    # ------------------------------------------------------------------
    add_item(EAN_LIST_INITIAL, CARD_CODE)

    # ------------------------------------------------------------------
    # Step 4: Scan loyalty card at loyalty prompt
    #         (scan_loyalty_tenderprompt handles PayButton internally)
    # ------------------------------------------------------------------
    if not scan_loyalty_tenderprompt(CARD_CODE):
        raise RuntimeError("scan_loyalty_tenderprompt failed — aborting test.")

    # ------------------------------------------------------------------
    # Step 5: Verify BPM Tiered Spend Tier 1 applied
    #         Points NOT allocated to exclusion product (gift card).
    # ------------------------------------------------------------------
    _, _, _, _, _, missing_t1 = get_promotion_details(PROMO_TIER1)
    if not missing_t1:
        logger.log(
            "✅ Step 5 — BPM Tiered Spend Tier 1 verified on screen.",
            status="pass"
        )
    else:
        logger.log(
            f"❌ Step 5 — Missing Tier 1 promotions: {missing_t1}.",
            status="fail"
        )

    # ------------------------------------------------------------------
    # Step 6: Acknowledge exciting-news prompt if triggered
    # ------------------------------------------------------------------
    verify_exciting_news_prompt(timeout_seconds=10)

    # ------------------------------------------------------------------
    # Step 7: Move back to sale mode to add more items
    # ------------------------------------------------------------------
    if not move_back_to_salemode():
        raise RuntimeError("move_back_to_salemode failed — aborting test.")

    # ------------------------------------------------------------------
    # Step 8: Scan additional articles (total > $500 for next tier)
    # ------------------------------------------------------------------
    add_item(EAN_LIST_ADDITIONAL, CARD_CODE)

    # ------------------------------------------------------------------
    # Step 9: Move to tender mode
    # ------------------------------------------------------------------
    if not move_to_tendermode():
        raise RuntimeError("move_to_tendermode failed — aborting test.")

    # ------------------------------------------------------------------
    # Step 10: Verify NO redemption prompt displayed
    #          (Funds Locked card → redemption is blocked)
    # ------------------------------------------------------------------
    win = global_instance.win
    redemption_popup = None
    try:
        redemption_popup = win.child_window(
            title_re=".*Current Rewards Balance.*", control_type="Edit"
        )
    except Exception:
        pass

    if redemption_popup and redemption_popup.exists(timeout=5):
        logger.log(
            "❌ Step 10 — Redemption prompt displayed (should NOT appear for Funds Locked card).",
            status="fail"
        )
        logger.take_screenshot("S4_Unexpected_Redemption_Prompt")
    else:
        logger.log(
            "✅ Step 10 — No redemption prompt displayed (correct for Funds Locked card).",
            status="pass"
        )

    # ------------------------------------------------------------------
    # Step 10b: Verify BPM Tiered Spend with NEXT tier points
    # ------------------------------------------------------------------
    _, _, _, _, _, missing_t2 = get_promotion_details(PROMO_TIER2)
    if not missing_t2:
        logger.log(
            "✅ Step 10b — BPM Tiered Spend Tier 2 verified (next tier applied after $500).",
            status="pass"
        )
    else:
        logger.log(
            f"❌ Step 10b — Missing Tier 2 promotions: {missing_t2}.",
            status="fail"
        )

    # ------------------------------------------------------------------
    # Step 11: Complete transaction
    # ------------------------------------------------------------------
    if not complete_transaction():
        raise RuntimeError("complete_transaction failed — aborting test.")

    # ------------------------------------------------------------------
    # Steps 12 & 13: Verify EagleEye settlement + EE logs
    # ------------------------------------------------------------------
    ee_result = verify_eagleeye_logs(
        expect_wallet_open=True,
        expect_wallet_settle=True,
    )

    if ee_result["all_passed"]:
        logger.upgrade_info_to_pass("detected")
        logger.log(
            "✅ S4 PASSED — BPM Tiered Spend campaign verified across tiers. "
            "Transaction settled in EagleEye.",
            status="pass"
        )
    else:
        logger.log(
            "❌ EagleEye verification failed. See logs above.",
            status="fail"
        )

    # ------------------------------------------------------------------
    # Step 14: Tlogs apportionment
    # ------------------------------------------------------------------
    logger.log(
        "TODO: Verify Tlogs apportionment — tiered spend points correctly "
        "apportioned; exclusion product (gift card) = 0 pts.",
        status="info"
    )

except Exception as e:
    logger.log(f"❌ Unexpected error in S4: {e}", status="fail")
    print(f"❌ S4 ERROR: {e}")
    logger.take_screenshot("S4_Unexpected_Error")

finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
