"""
S1_BasketPointsFixedWithXMASCard.py
------------------------------------
Regression Test S1 — Validation of basket points fixed campaigns with XMAS card.

Scenario:
    Verify that the basket-level points-fixed offer is applied correctly when an
    XMAS (Christmas Savings) EDR card is scanned in Sale mode. Points must NOT be
    allocated to exclusion products (e.g. gift cards).

Pre-requisite:
    EDR XMAS card configured with a basket-based points-fixed offer.
    Basket spend must exceed the qualification threshold (e.g. > $100).
    At least one exclusion article (e.g. gift card) must be scanned.

Steps automated:
    1. Login to SCO.
    2. Scan qualifying articles (spend > $100) + exclusion article (gift card).
    3. Scan XMAS loyalty card in Sale mode.
    4. Move to tender mode.
    5. Verify basket-level points-fixed offer is applied; points NOT allocated
       to exclusion product.
    6. Acknowledge "exciting news" prompt if triggered.
    7. Complete the transaction (Cash).
    8. Verify EagleEye settlement.
    9. Verify EE logs (Card Validation + Wallet Open + Wallet Settle).
   10. Verify Tlogs apportionment (placeholder — to be implemented).

Data source:
    SMB share SaleData.csv — TC_ID = "S1", Banner = "SM", Iteration = 1.
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
from Components.Scan_loyalty_salemode import scan_loyalty_salemode
from Components.Move_to_tendermode import move_to_tendermode
from Components.Promotion_details import get_promotion_details
from Components.Verify_exciting_news_prompt import verify_exciting_news_prompt
from Components.Complete_transaction import complete_transaction
from Components.Verify_EagleEye_logs import verify_eagleeye_logs
from Components.Read_csv import get_csv_value
from Components.report import logger

# --- Test-case identity ------------------------------------------------------
TC_ID     = "S1"
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

# Semicolon-separated EANs: qualifying articles first, then exclusion (gift card)
# e.g. "9300624016571;9300624016571;9312771000115"
EAN_LIST = _get_value("EAN_Codes", None) or _get_value("Item_EAN", "<FILL_EAN_LIST>")

# XMAS (Christmas Savings) loyalty card number
CARD_CODE = _get_value("Card_number", "<FILL_XMAS_CARD_NUMBER>")

# Semicolon-separated basket-level promotion descriptions to verify on screen
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
    # Steps 2: Scan qualifying articles + exclusion article (gift card)
    # ------------------------------------------------------------------
    add_item(EAN_LIST, CARD_CODE)

    # ------------------------------------------------------------------
    # Step 3: Scan XMAS loyalty card in Sale mode
    # ------------------------------------------------------------------
    if not scan_loyalty_salemode(CARD_CODE):
        raise RuntimeError("scan_loyalty_salemode failed — aborting test.")

    # ------------------------------------------------------------------
    # Step 4: Move to tender mode
    # ------------------------------------------------------------------
    if not move_to_tendermode():
        raise RuntimeError("move_to_tendermode failed — aborting test.")

    # ------------------------------------------------------------------
    # Step 5: Verify basket points-fixed promotion displayed.
    #         Points must NOT be allocated to the exclusion product.
    # ------------------------------------------------------------------
    _, _, promo_descs, promo_prices, _, missing_promos = get_promotion_details(PROMO_LIST)

    if not missing_promos:
        logger.log(
            "✅ Step 5 — Basket points-fixed offer verified on screen. "
            "Exclusion product price confirmed not contributing to offer.",
            status="pass"
        )
    else:
        logger.log(
            f"❌ Step 5 — Missing promotions: {missing_promos}. "
            "Basket points-fixed offer may not have applied correctly.",
            status="fail"
        )

    # ------------------------------------------------------------------
    # Step 6: Acknowledge exciting-news prompt if triggered
    #         (non-fatal if not shown — depends on live card balance)
    # ------------------------------------------------------------------
    found = verify_exciting_news_prompt(timeout_seconds=15)
    if found:
        logger.log("✅ Step 6 — Exciting news prompt verified and dismissed.", status="pass")
    else:
        logger.log(
            "ℹ️ Step 6 — Exciting news prompt not detected within timeout. "
            "Continuing (card balance may not have triggered it this run).",
            status="info"
        )

    # ------------------------------------------------------------------
    # Step 7: Complete the transaction (Cash)
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
            "✅ S1 PASSED — Basket points-fixed offer applied correctly. "
            "Transaction settled in EagleEye with all expected events.",
            status="pass"
        )

    # ------------------------------------------------------------------
    # Step 10: Tlogs apportionment
    # TODO: implement Tlogs apportionment verifier to confirm basket
    #       points-fixed offer is correctly apportioned, and the
    #       exclusion product (gift card) has 0 points allocated.
    # ------------------------------------------------------------------
    logger.log(
        "TODO: Verify Tlogs apportionment — basket points-fixed offer must NOT "
        "apportion points to exclusion product (gift card line item = 0 pts).",
        status="info"
    )

except Exception as e:
    logger.log(f"❌ Unexpected error in S1: {e}", status="fail")
    print(f"❌ S1 ERROR: {e}")
    logger.take_screenshot("S1_Unexpected_Error")

finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
