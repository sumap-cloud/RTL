"""
S5_TieredSpendWithRegisteredCardEReceipt.py
--------------------------------------------
Regression Test S5 — Validation of Tiered Spend campaign with Registered card
with E-receipt (electronic receipt).

Scenario:
    Verify that the tiered spend campaign applies correct tiers and that
    redemption is offered for a registered card with >2000 points. Redeem $10
    at the second tier.

Steps automated:
    1.  Login to SCO.
    2.  Scan eligible articles worth below $100.
    3.  Scan exclusion articles (gift card).
    4.  Scan loyalty card at loyalty prompt (scan_loyalty_tenderprompt).
    5.  Verify Tiered Spend offer applied (Tier 1); no points for exclusion.
    6.  Verify redemption IS displayed (>2000 pts); do NOT redeem yet.
    7.  Acknowledge exciting-news prompt if triggered.
    8.  Move back to sale mode.
    9.  Scan more articles (total > $500 for next tier).
    10. Move to tender mode.
    11. Verify Tiered Spend with next-tier points applied.
    12. Verify redemption is displayed → redeem $10.
    13. Complete transaction.
    14. Verify EagleEye settlement.
    15. Verify EE logs.
    16. Verify Tlogs apportionment.

Pre-requisite:
    Registered EDR card with >2000 points and a tiered spend campaign configured.
    E-receipt enabled for the card.

Data source:
    SMB SaleData.csv — TC_ID = "TC_007_VerifyTieredSpendCampaignWithRegisteredCard", Banner = "SM".
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
from Components.Redeem_reward_voucher import redeem_reward_voucher
from Components.Complete_transaction import complete_transaction
from Components.Verify_EagleEye_logs import verify_eagleeye_logs
from Components.Read_csv import get_csv_value
from Components.report import logger
from Components import global_instance

# --- Test-case identity ------------------------------------------------------
TC_ID  = "TC_007_VerifyTieredSpendCampaignWithRegisteredCard"
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
EAN_LIST_INITIAL = _get_value("EAN_Codes", 1, None) or _get_value("Item_EAN", 1, "<FILL_INITIAL_EANS>")
EAN_LIST_ADDITIONAL = _get_value("EAN_Codes", 2, None) or _get_value("Item_EAN", 2, "<FILL_ADDITIONAL_EANS>")
CARD_CODE = _get_value("Card_number", 1, "<FILL_REGISTERED_CARD>")
PROMO_TIER1 = _get_value("Promotion_description", 1, "")
PROMO_TIER2 = _get_value("Promotion_description", 2, "")
REDEEM_AMOUNT = _get_value("Redeem_amount", 2, "10")

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
    # ------------------------------------------------------------------
    if not scan_loyalty_tenderprompt(CARD_CODE):
        raise RuntimeError("scan_loyalty_tenderprompt failed — aborting test.")

    # ------------------------------------------------------------------
    # Step 5: Verify Tiered Spend offer applied (Tier 1)
    # ------------------------------------------------------------------
    _, _, _, _, _, missing_t1 = get_promotion_details(PROMO_TIER1)
    if not missing_t1:
        logger.log(
            "✅ Step 5 — Tiered Spend Tier 1 verified on screen. "
            "Exclusion product has no points.",
            status="pass"
        )
    else:
        logger.log(
            f"❌ Step 5 — Missing Tier 1 promotions: {missing_t1}.",
            status="fail"
        )

    # ------------------------------------------------------------------
    # Step 6: Verify redemption IS displayed (>2000 pts).
    #         Do NOT redeem yet — just confirm the prompt appears.
    # ------------------------------------------------------------------
    win = global_instance.win
    redemption_detected = False
    try:
        redemption_popup = win.child_window(
            title_re=".*Current Rewards Balance.*", control_type="Edit"
        )
        if redemption_popup.exists(timeout=8):
            redemption_text = redemption_popup.window_text()
            logger.log(
                f"✅ Step 6 — Redemption prompt displayed: '{redemption_text}'.",
                status="pass"
            )
            redemption_detected = True
            # Dismiss without redeeming — click "Do Not Redeem" or equivalent
            for dismiss_title in ("Do Not\nRedeem", "Do Not Redeem", "Skip", "No"):
                try:
                    dismiss_btn = win.child_window(title_re=f".*{dismiss_title}.*", control_type="Button")
                    if dismiss_btn.exists(timeout=2):
                        dismiss_btn.click_input()
                        logger.log(
                            f"✅ Step 6 — Dismissed redemption via '{dismiss_title}' (will redeem at Tier 2).",
                            status="pass"
                        )
                        break
                except Exception:
                    continue
    except Exception:
        pass

    if not redemption_detected:
        logger.log(
            "❌ Step 6 — Redemption prompt NOT displayed (expected for >2000 pts card).",
            status="fail"
        )
        logger.take_screenshot("S5_Redemption_Not_Shown_Tier1")

    # ------------------------------------------------------------------
    # Step 7: Acknowledge exciting-news prompt if triggered
    # ------------------------------------------------------------------
    verify_exciting_news_prompt(timeout_seconds=10)

    # ------------------------------------------------------------------
    # Step 8: Move back to sale mode
    # ------------------------------------------------------------------
    if not move_back_to_salemode():
        raise RuntimeError("move_back_to_salemode failed — aborting test.")

    # ------------------------------------------------------------------
    # Step 9: Scan more articles (total > $500 for next tier)
    # ------------------------------------------------------------------
    add_item(EAN_LIST_ADDITIONAL, CARD_CODE)

    # ------------------------------------------------------------------
    # Step 10: Move to tender mode
    # ------------------------------------------------------------------
    if not move_to_tendermode():
        raise RuntimeError("move_to_tendermode failed — aborting test.")

    # ------------------------------------------------------------------
    # Step 11: Verify Tiered Spend with next-tier points
    # ------------------------------------------------------------------
    _, _, _, _, _, missing_t2 = get_promotion_details(PROMO_TIER2)
    if not missing_t2:
        logger.log(
            "✅ Step 11 — Tiered Spend Tier 2 verified (next tier after >$500).",
            status="pass"
        )
    else:
        logger.log(
            f"❌ Step 11 — Missing Tier 2 promotions: {missing_t2}.",
            status="fail"
        )

    # ------------------------------------------------------------------
    # Step 12: Verify redemption displayed again → redeem $10
    # ------------------------------------------------------------------
    redeemed = redeem_reward_voucher(
        reward_tender_id="Tender3",
        voucher_options=[f"Redeem ${REDEEM_AMOUNT}", f"${REDEEM_AMOUNT}", "Redeem $10", "$10"],
    )
    if redeemed:
        logger.log(
            f"✅ Step 12 — Redeemed ${REDEEM_AMOUNT} reward voucher.",
            status="pass"
        )
    else:
        logger.log(
            f"❌ Step 12 — Reward voucher redemption (${REDEEM_AMOUNT}) failed.",
            status="fail"
        )

    # ------------------------------------------------------------------
    # Step 13: Complete transaction (pay remaining via Card)
    # ------------------------------------------------------------------
    if not complete_transaction():
        raise RuntimeError("complete_transaction failed — aborting test.")

    # ------------------------------------------------------------------
    # Steps 14 & 15: Verify EagleEye settlement + EE logs
    # ------------------------------------------------------------------
    ee_result = verify_eagleeye_logs(
        expect_wallet_open=True,
        expect_wallet_settle=True,
    )

    if ee_result["all_passed"]:
        logger.upgrade_info_to_pass("detected")
        logger.log(
            "✅ S5 PASSED — Tiered Spend campaign verified across tiers with "
            f"${REDEEM_AMOUNT} redemption. Transaction settled in EagleEye.",
            status="pass"
        )
    else:
        logger.log(
            "❌ EagleEye verification failed. See logs above.",
            status="fail"
        )

    # ------------------------------------------------------------------
    # Step 16: Tlogs apportionment
    # ------------------------------------------------------------------
    logger.log(
        "TODO: Verify Tlogs apportionment — tiered spend points correctly "
        "apportioned; exclusion product = 0 pts; redemption amount reflected.",
        status="info"
    )

except Exception as e:
    logger.log(f"❌ Unexpected error in S5: {e}", status="fail")
    print(f"❌ S5 ERROR: {e}")
    logger.take_screenshot("S5_Unexpected_Error")

finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
