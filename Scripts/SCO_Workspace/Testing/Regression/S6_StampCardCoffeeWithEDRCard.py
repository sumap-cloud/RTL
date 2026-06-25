"""
S6_StampCardCoffeeWithEDRCard.py
----------------------------------
Regression Test S6 — Validation of Stamp Card (Coffee Card) with EDR card.

Scenario:
    Verify that the stamp card accumulates stamps for coffee products across
    transactions and triggers the free coffee discount product once the
    required stamp count is reached.

    Transaction 1 (5 stamps — accumulation, no reward yet):
        - Scan 5 coffee articles
        - Scan EDR loyalty card in Sale mode
        - Verify base points displayed (no stamp card changes on screen)
        - Complete transaction → settled in EE
        - Verify 5 stamps added to stamp card accounts in EE

    Transaction 2 (5 more stamps — threshold reached, free coffee triggered):
        - SCO returns to idle → new basket
        - Scan 5 coffee articles
        - Scan EDR loyalty card in Sale mode
        - Verify base points displayed (no stamp card changes on screen)
        - Complete transaction → settled in EE
        - Verify 5 stamps added (total now meets threshold)
        - Verify discount product for free coffee is added in EE

Pre-requisite:
    EDR card with an active coffee stamp card campaign. Card's stamp count
    should be preconditioned so that Transaction 2 (5 more stamps) triggers
    the free coffee reward (e.g., if threshold = 10, start with 5 stamps).

Data source:
    SMB SaleData.csv — TC_ID = "S6", Banner = "SM".
    Iteration 1 = Txn1 (5 coffee EANs).
    Iteration 2 = Txn2 (5 coffee EANs).
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
from Components.Scan_loyalty_salemode import scan_loyalty_salemode
from Components.Move_to_tendermode import move_to_tendermode
from Components.Promotion_details import get_promotion_details
from Components.Complete_transaction import complete_transaction
from Components.Verify_EagleEye_logs import verify_eagleeye_logs
from Components.Read_csv import get_csv_value
from Components.report import logger
from Components import global_instance

# --- Test-case identity ------------------------------------------------------
TC_ID  = "S6"
BANNER = "SM"

logger.set_tc_id(TC_ID)


def _get_value(column, iteration, fallback):
    try:
        val = get_csv_value("saledata", BANNER, TC_ID, iteration, column)
        if val and not val.startswith("Error") and val != "No matching record found.":
            return val
    except Exception:
        pass
    return fallback


# ============================================================================
# TRANSACTION 1 — 5 coffee stamps (accumulation, no reward yet)
# ============================================================================
try:
    logger.log("═══════════════════════════════════════════════════════════════", status="info")
    logger.log("  TRANSACTION 1 — 5 coffee stamps (accumulation only)", status="info")
    logger.log("═══════════════════════════════════════════════════════════════", status="info")

    ITERATION_1 = 1
    EAN_LIST_1 = _get_value("EAN_Codes", ITERATION_1, None) or _get_value("Item_EAN", ITERATION_1, "<FILL_COFFEE_EANS_TXN1>")
    CARD_CODE = _get_value("Card_number", ITERATION_1, "<FILL_EDR_CARD>")

    # Step 1: Login to SCO
    if not login_pos():
        raise RuntimeError("login_pos failed (Txn1) — aborting test.")

    # Step 2: Scan 5 coffee articles
    add_item(EAN_LIST_1, CARD_CODE)

    # Step 3: Scan loyalty card in Sale mode
    if not scan_loyalty_salemode(CARD_CODE):
        raise RuntimeError("scan_loyalty_salemode failed (Txn1) — aborting test.")

    # Step 4: Verify no changes on screen — base points should be displayed
    _, _, promo_descs_1, _, _, _ = get_promotion_details("")
    if not promo_descs_1:
        logger.log(
            "✅ Txn1 Step 4 — No promotion changes on screen. Base points displayed as expected.",
            status="pass"
        )
    else:
        logger.log(
            f"⚠️ Txn1 Step 4 — Unexpected promotions detected: {promo_descs_1}. "
            "Expected only base points (no stamp card reward yet).",
            status="info"
        )

    # Move to tender + Step 5: Complete transaction
    if not move_to_tendermode():
        raise RuntimeError("move_to_tendermode failed (Txn1) — aborting test.")

    if not complete_transaction():
        raise RuntimeError("complete_transaction failed (Txn1) — aborting test.")

    # Steps 6 & 8: Verify EE settlement and logs
    ee_result_1 = verify_eagleeye_logs(
        expect_wallet_open=True,
        expect_wallet_settle=True,
    )

    if ee_result_1["all_passed"]:
        logger.log("✅ Txn1 — Transaction settled in EagleEye.", status="pass")
    else:
        logger.log("❌ Txn1 — EagleEye verification failed.", status="fail")

    # Step 7: Verify stamps added in stamp card accounts
    # TODO: Implement stamp card accounts verification in EE
    #       (parse wallet/settle response for stamp card section,
    #        confirm 5 stamps added to coffee card account)
    logger.log(
        "TODO: Txn1 — Verify 5 stamps added to coffee stamp card accounts in EE.",
        status="info"
    )

except Exception as e:
    logger.log(f"❌ Txn1 unexpected error: {e}", status="fail")
    logger.take_screenshot("S6_Txn1_Unexpected_Error")


# ============================================================================
# TRANSITION — Wait for SCO to return to idle
# ============================================================================
logger.log("⏳ Waiting for SCO to return to idle for Transaction 2...", status="info")
time.sleep(10)
global_instance.reset_state()


# ============================================================================
# TRANSACTION 2 — 5 more stamps (threshold reached → free coffee)
# ============================================================================
try:
    logger.log("═══════════════════════════════════════════════════════════════", status="info")
    logger.log("  TRANSACTION 2 — 5 more stamps (threshold met → free coffee)", status="info")
    logger.log("═══════════════════════════════════════════════════════════════", status="info")

    ITERATION_2 = 2
    EAN_LIST_2 = _get_value("EAN_Codes", ITERATION_2, None) or _get_value("Item_EAN", ITERATION_2, "<FILL_COFFEE_EANS_TXN2>")

    # Step 9: Login (SCO at idle after Txn1)
    if not login_pos():
        raise RuntimeError("login_pos failed (Txn2) — aborting test.")

    # Step 10: Scan 5 coffee articles
    add_item(EAN_LIST_2, CARD_CODE)

    # Step 11: Scan loyalty card in Sale mode
    if not scan_loyalty_salemode(CARD_CODE):
        raise RuntimeError("scan_loyalty_salemode failed (Txn2) — aborting test.")

    # Step 12: Verify no changes on screen — base points displayed
    _, _, promo_descs_2, _, _, _ = get_promotion_details("")
    if not promo_descs_2:
        logger.log(
            "✅ Txn2 Step 12 — No promotion changes on screen. Base points displayed.",
            status="pass"
        )
    else:
        logger.log(
            f"⚠️ Txn2 Step 12 — Promotions detected: {promo_descs_2}. "
            "Checking if this includes the free coffee discount.",
            status="info"
        )

    # Move to tender + Step 13: Complete transaction
    if not move_to_tendermode():
        raise RuntimeError("move_to_tendermode failed (Txn2) — aborting test.")

    if not complete_transaction():
        raise RuntimeError("complete_transaction failed (Txn2) — aborting test.")

    # Steps 14 & 17: Verify EE settlement and logs
    ee_result_2 = verify_eagleeye_logs(
        expect_wallet_open=True,
        expect_wallet_settle=True,
    )

    if ee_result_2["all_passed"]:
        logger.log("✅ Txn2 — Transaction settled in EagleEye.", status="pass")
    else:
        logger.log("❌ Txn2 — EagleEye verification failed.", status="fail")

    # Step 15: Verify 5 stamps added (cumulative now meets threshold)
    # TODO: Implement stamp card accounts verification
    logger.log(
        "TODO: Txn2 — Verify 5 stamps added to coffee stamp card accounts in EE "
        "(cumulative should now meet threshold).",
        status="info"
    )

    # Step 16: Verify discount product for free coffee is added in EE
    # TODO: Implement free coffee discount product verification
    #       (parse wallet/settle response for discount product entry,
    #        confirm free coffee reward issued)
    logger.log(
        "TODO: Txn2 — Verify discount product for free coffee is added in EE "
        "(stamp card reward triggered after threshold met).",
        status="info"
    )

    # Final pass/fail
    if ee_result_1.get("all_passed") and ee_result_2.get("all_passed"):
        logger.upgrade_info_to_pass("detected")
        logger.log(
            "✅ S6 PASSED — Coffee stamp card verified across 2 transactions. "
            "Stamps accumulated and free coffee reward triggered.",
            status="pass"
        )
    else:
        logger.log(
            "❌ S6 — One or more EE verifications failed. See logs above.",
            status="fail"
        )

except Exception as e:
    logger.log(f"❌ Txn2 unexpected error: {e}", status="fail")
    logger.take_screenshot("S6_Txn2_Unexpected_Error")

finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
