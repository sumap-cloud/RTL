"""
TC_012_VerifyPointsCardLockingWithin3mins.py
---------------------------------------------
Regression Test TC_012 — Validation of points / card locking within 3 minutes.

Scenario:
    Verify that when a transaction is voided (wallet opened but NOT settled),
    the card enters a "locked" state for ~3 minutes. During this window, a
    second transaction with the same card should:
      - NOT show a redemption prompt (card is locked).
      - Still settle successfully in EagleEye.

    Transaction 1 (voided — card becomes locked):
        - Scan eligible + exclusion articles
        - Scan loyalty card at loyalty prompt
        - Verify redemption prompt triggers → click "Skip"
        - Void the transaction
        - Verify transaction NOT settled in EE (active/open state)
        - Verify EE logs: Card Validation + Wallet Open ONLY (no Settle)

    Transaction 2 (within 3 mins — card still locked):
        - Login again immediately (within 3-min lock window)
        - Scan some articles
        - Scan loyalty card
        - Verify base points displayed (no promo changes)
        - Verify redemption prompt does NOT trigger (card locked)
        - Complete transaction → settled in EE
        - Verify EE logs: Card Validation + Wallet Open + Wallet Settle

Pre-requisite:
    Registered EDR card with >2000 points (to trigger redemption prompt).
    Both transactions must complete within the 3-minute lock window.

Data source:
    SMB SaleData.csv — TC_ID = "TC_012_VerifyPointsCardLockingWithin3mins", Banner = "SM".
    Iteration 1 = Txn1 (eligible + exclusion articles).
    Iteration 2 = Txn2 (some articles for the locked retry).
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
from Components.Scan_loyalty_salemode import scan_loyalty_salemode
from Components.Promotion_details import get_promotion_details
from Components.Void_transaction import void_transaction
from Components.Verify_EagleEye_logs import verify_eagleeye_logs
from Components.Complete_transaction import complete_transaction
from Components.Move_to_tendermode import move_to_tendermode
from Components.Read_csv import get_csv_value
from Components.report import logger
from Components import global_instance

# --- Test-case identity ------------------------------------------------------
TC_ID  = "TC_012_VerifyPointsCardLockingWithin3mins"
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
# TRANSACTION 1 — Void (wallet open, NO settle → card locked)
# ============================================================================
try:
    logger.log("═══════════════════════════════════════════════════════════════", status="info")
    logger.log("  TRANSACTION 1 — Void transaction (card becomes locked)", status="info")
    logger.log("═══════════════════════════════════════════════════════════════", status="info")

    ITERATION_1 = 1
    EAN_LIST_1 = _get_value("EAN_Codes", ITERATION_1, None) or _get_value("Item_EAN", ITERATION_1, "9339687023882;9315087192083;8720077181786")
    CARD_CODE = _get_value("Card_number", ITERATION_1, "9353184462906")

    # Step 1: Login to SCO
    if not login_pos():
        raise RuntimeError("login_pos failed (Txn1) — aborting test.")

    # Step 2: Scan eligible and exclusion articles
    add_item(EAN_LIST_1, CARD_CODE)

    # Step 3: Scan loyalty card at loyalty prompt
    if not scan_loyalty_tenderprompt(CARD_CODE):
        raise RuntimeError("scan_loyalty_tenderprompt failed (Txn1) — aborting test.")

    # Step 4: Handle bunch offer prompt if triggered (dismiss it, then check redemption)
    win = global_instance.win
    try:
        bunch_btn = win.child_window(auto_id="SkipCollectableOfferPrompt", control_type="Button")
        if bunch_btn.exists(timeout=5):
            logger.log("✅ Txn1 Step 4 — Bunch offer prompt detected → dismissing.", status="pass")
            bunch_btn.click_input()
            time.sleep(1)
    except Exception:
        pass

    # Step 4: Verify redemption prompt triggers → skip it (click "Do Not Redeem" / "Skip")
    redemption_detected = False
    try:
        redemption_popup = win.child_window(
            title_re=".*Current Rewards Balance.*", control_type="Edit"
        )
        if redemption_popup.exists(timeout=8):
            redemption_text = redemption_popup.window_text()
            logger.log(
                f"✅ Txn1 Step 4 — Redemption prompt triggered: '{redemption_text}'.",
                status="pass"
            )
            redemption_detected = True
            for dismiss in ("Do Not\nRedeem", "Do Not Redeem", "Skip", "No"):
                try:
                    btn = win.child_window(title_re=f".*{dismiss}.*", control_type="Button")
                    if btn.exists(timeout=2):
                        btn.click_input()
                        logger.log(f"✅ Redemption skipped via '{dismiss}'.", status="pass")
                        break
                except Exception:
                    continue
    except Exception:
        pass

    if not redemption_detected:
        logger.log(
            "❌ Txn1 Step 4 — Redemption prompt NOT triggered (expected for >2000 pts).",
            status="fail"
        )
        logger.take_screenshot("TC012_Redemption_Not_Triggered_Txn1")

    # Step 5 (numbered 4 in spec): Void the transaction
    time.sleep(2)
    if not void_transaction():
        raise RuntimeError("void_transaction failed (Txn1) — aborting test.")

    logger.log("✅ Txn1 — Transaction voided successfully.", status="pass")

    # Step 6: Verify transaction NOT settled in EE (wallet still active)
    ee_result_1 = verify_eagleeye_logs(
        expect_wallet_open=True,
        expect_wallet_settle=False,  # Must NOT be settled (voided)
    )

    if ee_result_1.get("wallet_open") and not ee_result_1.get("wallet_settle"):
        logger.log(
            "✅ Txn1 Step 6 — Transaction NOT settled in EE (wallet open only). "
            "Card is now locked.",
            status="pass"
        )
    else:
        logger.log(
            "❌ Txn1 Step 6 — Unexpected EE state. "
            f"WalletOpen={ee_result_1.get('wallet_open')}, "
            f"WalletSettle={ee_result_1.get('wallet_settle')}.",
            status="fail"
        )

except Exception as e:
    logger.log(f"❌ Txn1 unexpected error: {e}", status="fail")
    logger.take_screenshot("TC012_Txn1_Unexpected_Error")


# ============================================================================
# TRANSITION — Minimal wait (stay within 3-min lock window)
# ============================================================================
logger.log(
    "⏳ Minimal wait before Transaction 2 (must be within 3-min card lock window)...",
    status="info"
)
time.sleep(5)  # Brief pause for SCO to settle to idle — do NOT exceed 3 mins total
global_instance.reset_state()


# ============================================================================
# TRANSACTION 2 — Within 3-min lock window (no redemption expected)
# ============================================================================
try:
    logger.log("═══════════════════════════════════════════════════════════════", status="info")
    logger.log("  TRANSACTION 2 — Card locked (within 3 mins of void)", status="info")
    logger.log("═══════════════════════════════════════════════════════════════", status="info")

    ITERATION_2 = 2
    EAN_LIST_2 = _get_value("EAN_Codes", ITERATION_2, None) or _get_value("Item_EAN", ITERATION_2, "9339687200924;9339687200924")

    # Step 9: Login to SCO (within 3 mins)
    if not login_pos():
        raise RuntimeError("login_pos failed (Txn2) — aborting test.")

    # Step 10: Scan some articles
    add_item(EAN_LIST_2, CARD_CODE)

    # Step 11: Scan loyalty card (sale mode for locked card scenario)
    if not scan_loyalty_salemode(CARD_CODE):
        raise RuntimeError("scan_loyalty_salemode failed (Txn2) — aborting test.")

    # Step 12: Verify no promo changes — base points displayed
    _, _, promo_descs_2, _, _, _ = get_promotion_details("")
    if not promo_descs_2:
        logger.log(
            "✅ Txn2 Step 12 — No promotion changes. Base points displayed.",
            status="pass"
        )
    else:
        logger.log(
            f"⚠️ Txn2 Step 12 — Unexpected promotions: {promo_descs_2}.",
            status="info"
        )

    # Step 13: Verify redemption prompt does NOT trigger (card locked)
    if not move_to_tendermode():
        raise RuntimeError("move_to_tendermode failed (Txn2) — aborting test.")

    redemption_appeared = False
    try:
        redemption_popup_2 = win.child_window(
            title_re=".*Current Rewards Balance.*", control_type="Edit"
        )
        if redemption_popup_2.exists(timeout=5):
            redemption_appeared = True
    except Exception:
        pass

    if not redemption_appeared:
        logger.log(
            "✅ Txn2 Step 13 — Redemption prompt NOT triggered (card is locked). Correct!",
            status="pass"
        )
    else:
        logger.log(
            "❌ Txn2 Step 13 — Redemption prompt appeared (should NOT for locked card).",
            status="fail"
        )
        logger.take_screenshot("TC012_Unexpected_Redemption_Txn2")
        # Dismiss it
        for dismiss in ("Do Not\nRedeem", "Do Not Redeem", "Skip", "No"):
            try:
                btn = win.child_window(title_re=f".*{dismiss}.*", control_type="Button")
                if btn.exists(timeout=2):
                    btn.click_input()
                    break
            except Exception:
                continue

    # Step 14: Complete transaction
    if not complete_transaction():
        raise RuntimeError("complete_transaction failed (Txn2) — aborting test.")

    # Steps 15 & 17: Verify EE settlement and logs
    ee_result_2 = verify_eagleeye_logs(
        expect_wallet_open=True,
        expect_wallet_settle=True,
    )

    if ee_result_2["all_passed"]:
        logger.upgrade_info_to_pass("detected")
        logger.log(
            "✅ S7 PASSED — Card locking within 3 mins verified. "
            "Txn1 voided (no settle), Txn2 completed (settled). "
            "No redemption during lock window.",
            status="pass"
        )
    else:
        logger.log("❌ Txn2 — EagleEye verification failed.", status="fail")

except Exception as e:
    logger.log(f"❌ Txn2 unexpected error: {e}", status="fail")
    logger.take_screenshot("TC012_Txn2_Unexpected_Error")

finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
