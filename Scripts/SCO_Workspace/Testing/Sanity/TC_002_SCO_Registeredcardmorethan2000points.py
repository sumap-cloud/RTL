"""
TC_002_SCO_Registeredcardmorethan2000points.py
----------------------------------------------
Test Case: Validation of POS/SCO transaction with registered card > 2000 points.

Scenario:
    Verify that the transaction is reached and settled to EagleEye
    (Registered EDR card) WITH $10 redemption.

Pre-requisite:
    An active registered EDR card with more than 2000 points.

Steps automated:
    1. Login to POS (connect to SCO, verify idle state).
    2. Scan the articles (add items to basket).
    3. Move to tender mode and scan EDR card at the loyalty prompt.
    4. Redeem $10 choice offer.
    5. Complete the transaction (EFT card payment).
    6. Verify EagleEye settlement.
    7. Verify points are removed from the card (via wallet settle in EE log).
    8. Verify EE logs (Card Validation + Wallet Open + Wallet Settle).

Data source:
    Primary: CSV via get_csv_value() for EAN codes, card number, and choice offer.
    Fallback: Hardcoded values if CSV is not reachable.
"""

import sys
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent  # → SCO_Workspace/

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# --- Component imports -------------------------------------------------------
from Components.Login_POS import login_pos
from Components.Add_item import add_item
from Components.Scan_loyalty_tenderprompt import scan_loyalty_tenderprompt
from Components.Redeem_reward_voucher import redeem_reward_voucher
from Components.Complete_transaction import complete_transaction
from Components.Verify_EagleEye_logs import verify_eagleeye_logs
from Components.Read_csv import get_csv_value
from Components.report import logger
from Components import global_instance

# --- Test-case identity ------------------------------------------------------
TC_ID = "TC_002"
BANNER = "SM"
ITERATION = 1

logger.set_tc_id(TC_ID)

# --- Data configuration ------------------------------------------------------
def _get_value(column, fallback):
    """Read from CSV; return fallback on any error."""
    try:
        val = get_csv_value("saledata", BANNER, TC_ID, ITERATION, column)
        if val and not val.startswith("Error") and val != "No matching record found.":
            return val
    except Exception:
        pass
    return fallback

EAN_LIST    = _get_value("EAN_Codes", None) or _get_value("Item_EAN", "9310072000282;9310072000282;9310072000282;9310072000282;9310072000282")
CARD_CODE   = _get_value("Card_number", "9353109614656")
CHOICE_OFFER = _get_value("Choice_offer", "$10")

# ---------------------------------------------------------------------------
# Test execution
# ---------------------------------------------------------------------------
try:

    # ------------------------------------------------------------------
    # Step 1: Login / connect to SCO
    # ------------------------------------------------------------------
    if not login_pos():
        raise RuntimeError("Login_POS failed — aborting test.")

    # ------------------------------------------------------------------
    # Step 2: Scan articles (loyalty card NOT scanned in sale mode for TC_002)
    # ------------------------------------------------------------------
    add_item(EAN_LIST, CARD_CODE)

    # ------------------------------------------------------------------
    # Step 3: Move to tender mode and scan EDR card at loyalty prompt
    # PayButton is clicked inside scan_loyalty_tenderprompt — do NOT
    # call move_to_tendermode() separately for this test case.
    # ------------------------------------------------------------------
    if not scan_loyalty_tenderprompt(CARD_CODE):
        raise RuntimeError("scan_loyalty_tenderprompt failed — aborting test.")

    # ------------------------------------------------------------------
    # Step 4: Redeem $10 via Reward Voucher (Tender3 → attendant flow)
    # After loyalty card scan, Tender3 triggers an 'Assistance Needed'
    # popup. The attendant logs in, handles 'Card Tender Declined', selects
    # a voucher amount, and returns to the 'Select Payment Type' screen.
    # ------------------------------------------------------------------
    if not redeem_reward_voucher(
        reward_tender_id="Tender3",
        voucher_options=["Redeem $10", "$10", "Redeem $30", "$30", "Skip"],
    ):
        raise RuntimeError("redeem_reward_voucher failed — aborting test.")

    if global_instance.reward_redeem_status:
        logger.log("✅ Reward voucher redeemed successfully.", status="pass")
    else:
        logger.log(
            "⚠️ reward_redeem_status False after redeem_reward_voucher.",
            status="fail",
        )

    # ------------------------------------------------------------------
    # Step 5: Complete the transaction via EFT card payment (Tender2)
    # SCO is now at 'Select Payment Type' with reduced balance after
    # voucher redemption. complete_transaction() clicks Card (Tender2).
    # ------------------------------------------------------------------
    if not complete_transaction():
        raise RuntimeError("complete_transaction failed — aborting test.")

    # ------------------------------------------------------------------
    # Steps 5, 6 & 7: Verify EagleEye settlement, points removal, EE logs
    # A SETTLED wallet/settle event confirms the transaction settled and
    # the redeemed points were deducted from the customer's account.
    # ------------------------------------------------------------------
    ee_result = verify_eagleeye_logs(
        expect_wallet_open=True,
        expect_wallet_settle=True,
    )

    # Step 7: Points removal confirmation
    if ee_result.get("wallet_settle") and ee_result.get("settled_status", "").upper() == "SETTLED":
        logger.log(
            "✅ EagleEye status is SETTLED — redeemed points have been "
            "deducted from the customer's card.",
            status="pass"
        )
    elif ee_result.get("wallet_settle"):
        logger.log(
            f"⚠️ Wallet Settle found but status is '{ee_result.get('settled_status')}' "
            "(expected SETTLED) — points removal unconfirmed.",
            status="fail"
        )

    if not ee_result["all_passed"]:
        logger.log(
            "❌ EagleEye verification failed. See individual step logs above.",
            status="fail"
        )
    else:
        logger.log(
            "✅ TC_002 PASSED — Transaction settled in EagleEye with $10 redemption.",
            status="pass"
        )

except Exception as e:
    logger.log(f"❌ Unexpected error in TC_002: {e}", status="fail")
    print(f"❌ TC_002 ERROR: {e}")
    logger.take_screenshot("TC_002_Unexpected_Error")

finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
