"""
TC_001_SCO_Registeredcardlessthan1000points.py
-----------------------------------------------
Test Case: Validation of POS/SCO transaction with registered card < 1000 points.

Scenario:
    Verify that the transaction is reached and settled to EagleEye
    (Registered EDR card) WITHOUT redemption.

Pre-requisite:
    An active registered EDR card with fewer than 1000 points.

Steps automated:
    1. Login to POS (connect to SCO, verify idle state).
    2. Scan the articles (add items to basket).
    3. Scan the EDR card in Sale mode.
    4. Move to tender mode.
    5. Complete the transaction (Cash).
    6. Verify EagleEye settlement.
    7. Verify EE logs (Card Validation + Wallet Open + Wallet Settle).

Data source:
    Primary: CSV via get_csv_value() for EAN codes and card number.
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
from Components.Scan_loyalty_salemode import scan_loyalty_salemode
from Components.Move_to_tendermode import move_to_tendermode
from Components.Complete_transaction import complete_transaction
from Components.Verify_EagleEye_logs import verify_eagleeye_logs
from Components.Read_csv import get_csv_value
from Components.report import logger

# --- Test-case identity ------------------------------------------------------
TC_ID = "TC_001"
BANNER = "SM"
ITERATION = 1

logger.set_tc_id(TC_ID)

# --- Data configuration ------------------------------------------------------
# EAN codes and card number are read from the SCO SaleData CSV.
# If the SMB share is unavailable the hardcoded fallbacks are used so the
# test can still be run in a disconnected environment.

def _get_value(column, fallback):
    """Read from CSV; return fallback on any error."""
    try:
        val = get_csv_value("saledata", BANNER, TC_ID, ITERATION, column)
        if val and not val.startswith("Error") and val != "No matching record found.":
            return val
    except Exception:
        pass
    return fallback

# Semicolon-separated list of item EAN codes to scan.
# Try both column names (EAN_Codes = SCO convention, Item_EAN = POS convention).
EAN_LIST = _get_value("EAN_Codes", None) or _get_value("Item_EAN", "9310072000282")

# EDR loyalty card number (registered, < 1000 points).
CARD_CODE = _get_value("Card_number", "9353109614779")

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
    # Step 2: Scan articles
    # ------------------------------------------------------------------
    add_item(EAN_LIST, CARD_CODE)

    # ------------------------------------------------------------------
    # Step 3: Scan EDR card in Sale mode
    # ------------------------------------------------------------------
    if not scan_loyalty_salemode(CARD_CODE):
        raise RuntimeError("scan_loyalty_salemode failed — aborting test.")

    # ------------------------------------------------------------------
    # Step 4: Move to tender mode
    # ------------------------------------------------------------------
    if not move_to_tendermode():
        raise RuntimeError("move_to_tendermode failed — aborting test.")

    # ------------------------------------------------------------------
    # Step 5: Complete the transaction
    # ------------------------------------------------------------------
    if not complete_transaction():
        raise RuntimeError("complete_transaction failed — aborting test.")

    # ------------------------------------------------------------------
    # Steps 6 & 7: Verify EagleEye settlement and EE logs
    # ------------------------------------------------------------------
    ee_result = verify_eagleeye_logs(
        expect_wallet_open=True,
        expect_wallet_settle=True,  # Transaction MUST settle (not training mode)
    )

    if not ee_result["all_passed"]:
        logger.log(
            "❌ EagleEye verification failed. See individual step logs above.",
            status="fail"
        )
    else:
        logger.log(
            "✅ TC_001 PASSED — Transaction settled in EagleEye with all expected events.",
            status="pass"
        )

except Exception as e:
    logger.log(f"❌ Unexpected error in TC_001: {e}", status="fail")
    print(f"❌ TC_001 ERROR: {e}")
    logger.take_screenshot("TC_001_Unexpected_Error")

finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
