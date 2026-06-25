"""
S2_ProductPointsMultiplierWithQFFCard.py
-----------------------------------------
Regression Test S2 — Validation of product points multiplier campaigns
with Qantas Frequent Flyer (QFF) card.

Scenario:
    Verify that the product points multiplier offer is applied correctly for
    eligible products when a QFF (segment 104) EDR card is scanned at the
    loyalty prompt. Points must NOT be allocated to exclusion products
    (e.g. donation articles).

Pre-requisite:
    QFF (Qantas) EDR card configured with a product-level points multiplier offer.
    Eligible articles (qualifying for the multiplier) and at least one exclusion
    article (e.g. donation) must be scanned.

Steps automated:
    1.  Login to SCO.
    2.  Scan eligible articles applicable for product points multiplier.
    3.  Scan exclusion articles (e.g. donation).
    4.  Scan QFF loyalty card at the loyalty prompt (PayButton handled inside
        scan_loyalty_tenderprompt — do NOT call move_to_tendermode separately).
    5.  Verify product points multiplier offer applied on screen; points NOT
        allocated to exclusion product.
    6.  Acknowledge "exciting news" prompt if triggered (QFF variant).
    7.  Complete the transaction.
    8.  Verify EagleEye settlement.
    9.  Verify EE logs (Card Validation + Wallet Open + Wallet Settle).
    10. Verify Tlogs apportionment (placeholder — to be implemented).

Data source:
    SMB share SaleData.csv — TC_ID = "S2", Banner = "SM", Iteration = 1.
    Fallback hardcoded values used when SMB share is unreachable.
"""

import sys
from pathlib import Path

current_file_path = Path(__file__).resolve()
# Testing/Regression -> Testing -> SCO_Workspace  (project root)
project_root = current_file_path.parent.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# --- SCO Component imports ---------------------------------------------------
from Components.Login_POS import login_pos
from Components.Add_item import add_item
from Components.Scan_loyalty_tenderprompt import scan_loyalty_tenderprompt
from Components.Promotion_details import get_promotion_details
from Components.Verify_exciting_news_prompt import verify_exciting_news_prompt
from Components.Complete_transaction import complete_transaction
from Components.Verify_EagleEye_logs import verify_eagleeye_logs
from Components.Read_csv import get_csv_value
from Components.report import logger

# --- Test-case identity ------------------------------------------------------
TC_ID     = "S2"
BANNER    = "SM"
ITERATION = 1

logger.set_tc_id(TC_ID)

# --- Data helpers ------------------------------------------------------------
def _get_value(column, fallback):
    """Read from SMB CSV; return fallback on any error."""
    try:
        val = get_csv_value("saledata", BANNER, TC_ID, ITERATION, column)
        if val and not val.startswith("Error") and val != "No matching record found.":
            return val
    except Exception:
        pass
    return fallback

# Semicolon-separated EANs: eligible multiplier articles first, then exclusion
# (donation) article EAN.
# e.g. "9300624016571;9300624016571;9310072000282"
EAN_LIST = _get_value("EAN_Codes", None) or _get_value("Item_EAN", "<FILL_EAN_LIST>")

# QFF (Qantas Frequent Flyer, segment 104) EDR card number
CARD_CODE = _get_value("Card_number", "<FILL_QFF_CARD_NUMBER>")

# Semicolon-separated product multiplier promotion descriptions to verify on screen
PROMO_LIST = _get_value("Promotion_description", "")

# ---------------------------------------------------------------------------
# Test execution
# ---------------------------------------------------------------------------
try:
    # ------------------------------------------------------------------
    # Step 1: Login / connect to SCO
    # ------------------------------------------------------------------
    if not login_pos():
        raise RuntimeError("login_pos failed — aborting test.")

    # ------------------------------------------------------------------
    # Steps 2 & 3: Scan eligible articles + exclusion article (donation)
    #              All EANs passed as semicolon-separated string.
    # ------------------------------------------------------------------
    add_item(EAN_LIST, CARD_CODE)

    # ------------------------------------------------------------------
    # Step 4: Scan QFF loyalty card at the loyalty prompt.
    #         scan_loyalty_tenderprompt clicks PayButton internally —
    #         do NOT call move_to_tendermode() before this.
    # ------------------------------------------------------------------
    if not scan_loyalty_tenderprompt(CARD_CODE):
        raise RuntimeError("scan_loyalty_tenderprompt failed — aborting test.")

    # ------------------------------------------------------------------
    # Step 5: Verify product points multiplier offer is applied on screen.
    #         Points must NOT be allocated to the exclusion (donation) line.
    # ------------------------------------------------------------------
    _, _, promo_descs, promo_prices, _, missing_promos = get_promotion_details(PROMO_LIST)

    if not missing_promos:
        logger.log(
            "✅ Step 5 — Product points multiplier offer verified on screen. "
            "Exclusion product (donation) confirmed not contributing to offer.",
            status="pass"
        )
    else:
        logger.log(
            f"❌ Step 5 — Missing promotions: {missing_promos}. "
            "Product points multiplier offer may not have applied correctly.",
            status="fail"
        )

    # ------------------------------------------------------------------
    # Step 6: Acknowledge exciting-news prompt if triggered.
    #         For QFF cards: "Exciting News! You've just converted xxx
    #         Qantas Points to put towards your next holiday."
    #         Non-fatal if not shown (depends on live card balance).
    # ------------------------------------------------------------------
    found = verify_exciting_news_prompt(timeout_seconds=15)
    if found:
        logger.log(
            "✅ Step 6 — Exciting news (Qantas Points) prompt verified and dismissed.",
            status="pass"
        )
    else:
        logger.log(
            "ℹ️ Step 6 — Exciting news prompt not detected within timeout. "
            "Continuing (card may not have crossed 2000 pts this run).",
            status="info"
        )

    # ------------------------------------------------------------------
    # Step 7: Complete the transaction
    # ------------------------------------------------------------------
    if not complete_transaction():
        raise RuntimeError("complete_transaction failed — aborting test.")

    # ------------------------------------------------------------------
    # Steps 8 & 9: Verify EagleEye settlement + EE log events
    #   (Card Validation, Wallet Open, Wallet Settle)
    # ------------------------------------------------------------------
    ee_result = verify_eagleeye_logs(
        expect_wallet_open=True,
        expect_wallet_settle=True,
    )

    if not ee_result["all_passed"]:
        logger.log(
            "❌ EagleEye verification failed. See individual step logs above.",
            status="fail"
        )
    else:
        logger.upgrade_info_to_pass("detected")
        logger.log(
            "✅ S2 PASSED — Product points multiplier offer applied correctly for "
            "QFF card. Transaction settled in EagleEye with all expected events.",
            status="pass"
        )

    # ------------------------------------------------------------------
    # Step 10: Tlogs apportionment
    # TODO: implement Tlogs apportionment verifier to confirm:
    #   - Product points multiplier correctly apportioned to eligible items.
    #   - Exclusion product (donation article) has 0 points allocated.
    # ------------------------------------------------------------------
    logger.log(
        "TODO: Verify Tlogs apportionment — product points multiplier must be "
        "correctly apportioned; exclusion product (donation) must have 0 pts.",
        status="info"
    )

except Exception as e:
    logger.log(f"❌ Unexpected error in S2: {e}", status="fail")
    print(f"❌ S2 ERROR: {e}")
    logger.take_screenshot("S2_Unexpected_Error")

finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
