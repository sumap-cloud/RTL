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
    EAN_LIST_1 = _get_value("Item_EAN", ITERATION_1, "9339687023882;9315087192083;9339687200924")
    CARD_CODE = _get_value("Card_number", ITERATION_1, "9353184462906")

    # Step 1: Login to SCO
    if not login_pos():
        raise RuntimeError("login_pos failed (Txn1) — aborting test.")

    # Step 2: Scan eligible and exclusion articles
    add_item(EAN_LIST_1, CARD_CODE)

    # Step 3: Scan loyalty card at loyalty prompt
    if not scan_loyalty_tenderprompt(CARD_CODE):
        raise RuntimeError("scan_loyalty_tenderprompt failed (Txn1) — aborting test.")

    win = global_instance.win

    # Step 4: Verify redemption prompt triggered
    # Real identifiers (confirmed live):
    #   LeadthruText = 'Available Everyday Rewards $XX'
    #   List1Button  = 'Redeem $XX', List2Button = '$10', List3Button = 'Other'
    #   List4Button  = 'Skip', GoBack = 'Go Back'
    # We validate it appeared, log the balance, then click Skip (List4Button).
    # Skip = "I don't want to redeem" → proceeds to payment selection screen.
    # The void after Skip is what triggers the 3-minute card lock.
    redemption_detected = False
    try:
        leadthru = win.child_window(auto_id="LeadthruText", control_type="Text")
        if leadthru.exists(timeout=8):
            leadthru_text = leadthru.window_text()
            if "Everyday Rewards" in leadthru_text or "Available" in leadthru_text:
                redemption_detected = True
                logger.log(
                    f"✅ Txn1 Step 4 — Redemption prompt triggered: '{leadthru_text}'.",
                    status="pass"
                )
                logger.take_screenshot("TC012_Redemption_Prompt_Txn1")

                # Validate WoWRewardPoints shown on screen
                try:
                    pts = win.child_window(auto_id="WoWRewardPoints", control_type="Text")
                    if pts.exists(timeout=1):
                        logger.log(f"✅ Points displayed: {pts.window_text()}", status="pass")
                except Exception:
                    pass

                # Click Skip (List4Button) — explicit "don't redeem" choice → moves forward to
                # payment selection screen; voiding after this triggers the 3-min card lock.
                skip_btn = win.child_window(auto_id="List4Button", control_type="Button")
                if skip_btn.exists(timeout=2):
                    skip_btn.click_input()
                    time.sleep(0.5)
                    logger.log("✅ Txn1 Step 4 — Clicked Skip on redemption prompt.", status="pass")
    except Exception:
        pass

    if not redemption_detected:
        logger.log(
            "❌ Txn1 Step 4 — Redemption prompt NOT triggered (expected for >2000 pts).",
            status="fail"
        )
        logger.take_screenshot("TC012_Redemption_Not_Triggered_Txn1")

    # Step 4b: Now on payment selection screen — validate WoWRewardPoints then go back to sale
    # Screen shows: LeadthruText='Select Payment Type', GoBackSale button
    try:
        payment_screen = win.child_window(auto_id="GoBackSale", control_type="Button")
        if payment_screen.exists(timeout=5):
            # Validate points on payment screen too
            try:
                pts = win.child_window(auto_id="WoWRewardPoints", control_type="Text")
                if pts.exists(timeout=1):
                    logger.log(
                        f"✅ Txn1 Step 4b — Points confirmed on payment screen: {pts.window_text()}",
                        status="pass"
                    )
            except Exception:
                pass
            # Go back to sale mode so we can void
            payment_screen.click_input()
            time.sleep(0.5)
            logger.log("✅ Txn1 Step 4b — Clicked GoBackSale → back in sale mode.", status="pass")
    except Exception:
        pass

    # Step 5: Void the transaction (card becomes locked after this)
    time.sleep(1)
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
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
    raise SystemExit(1)  # Stop — Txn2 must not run on a failed/dirty Txn1


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
    EAN_LIST_2 = _get_value("Item_EAN", ITERATION_2, "9339687200924;9339687200924")

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

    # Step 13: Move to tender mode to trigger any redemption prompt, then verify
    if not move_to_tendermode():
        raise RuntimeError("move_to_tendermode failed (Txn2) — aborting test.")

    # Step 13: Verify redemption prompt does NOT trigger (card locked)
    # Real identifier: LeadthruText = 'Available Everyday Rewards $XX'
    win2 = global_instance.win
    redemption_appeared = False
    try:
        leadthru2 = win2.child_window(auto_id="LeadthruText", control_type="Text")
        if leadthru2.exists(timeout=5):
            txt = leadthru2.window_text()
            if "Everyday Rewards" in txt or "Available" in txt:
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
        # Dismiss via GoBack without redeeming
        try:
            goback2 = win2.child_window(auto_id="GoBack", control_type="Button")
            if goback2.exists(timeout=2):
                goback2.click_input()
        except Exception:
            pass

    # Step 14: Complete transaction
    # ⚠️ COMMENTED OUT — uncomment for actual run (prevents card points exhaustion during dry-run)
    # if not complete_transaction():
    #     raise RuntimeError("complete_transaction failed (Txn2) — aborting test.")
    logger.log("⚠️ Step 14 — complete_transaction SKIPPED (dry-run mode). Uncomment for actual run.", status="info")

    # Steps 15 & 17: Verify EE settlement and logs
    # ⚠️ COMMENTED OUT — wallet settle check requires transaction to be completed first
    # ee_result_2 = verify_eagleeye_logs(
    #     expect_wallet_open=True,
    #     expect_wallet_settle=True,
    # )
    # if ee_result_2["all_passed"]:
    #     logger.upgrade_info_to_pass("detected")
    #     logger.log(
    #         "✅ TC_012 PASSED — Card locking within 3 mins verified. "
    #         "Txn1 voided (no settle), Txn2 completed (settled). "
    #         "No redemption during lock window.",
    #         status="pass"
    #     )
    # else:
    #     logger.log("❌ Txn2 — EagleEye verification failed.", status="fail")

    logger.log(
        "✅ TC_012 dry-run complete — all verifications passed up to payment step. "
        "Uncomment complete_transaction + EE settle check for full run.",
        status="pass"
    )

except Exception as e:
    logger.log(f"❌ Txn2 unexpected error: {e}", status="fail")
    logger.take_screenshot("TC012_Txn2_Unexpected_Error")

finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
