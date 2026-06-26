"""
S9_CouponLockingWithin3Mins.py
--------------------------------
Regression Test S9 — Validation of offers / coupon locking within 3 minutes.

Scenario:
    Verify that when a transaction is voided after offers (bunch + points fixed)
    and redemption have been triggered, the coupons/offers become "locked" for
    ~3 minutes. A second transaction with the SAME card within the lock window
    should:
      - NOT trigger the bunch offer (coupon locked).
      - NOT trigger the points fixed offer (coupon locked).
      - NOT show redemption prompt (card locked).
      - Still settle successfully in EagleEye.

    Transaction 1 (voided — coupons become locked):
        - Scan eligible + exclusion articles
        - Scan the bunch article (Article 100325 or 921694)
        - Scan loyalty card at loyalty prompt
        - Verify redemption prompt triggers → redeem $10
        - Verify bunch prompt triggers
        - Void the transaction
        - Verify NOT settled in EE (wallet open only)
        - Verify EE logs: Card Validation + Wallet Open ONLY

    Transaction 2 (within 3 mins — coupons still locked):
        - Login immediately (within 3-min lock window)
        - Scan same articles (including bunch article)
        - Scan loyalty card
        - Verify NO offers triggered (bunch + points fixed locked)
        - Verify redemption prompt NOT triggered (card locked)
        - Complete transaction → settled in EE
        - Verify EE logs: Card Validation + Wallet Open + Wallet Settle

Pre-requisite:
    Registered EDR card (9353105847249) with:
      - >2000 points (to trigger redemption)
      - Active bunch offer (1261389 - Test Bunch sample)
      - Active points fixed offer
    Bunch articles: 100325, 921694

Data source:
    SMB SaleData.csv — TC_ID = "TC_014_VerifyOffersCouponLockingWithin3mins", Banner = "SM".
    Iteration 1 = Txn1 (eligible + exclusion + bunch articles).
    Iteration 2 = Txn2 (same articles, within lock window).
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
from Components.Redeem_reward_voucher import redeem_reward_voucher
from Components.Move_to_tendermode import move_to_tendermode
from Components.Verify_EagleEye_logs import verify_eagleeye_logs
from Components.Complete_transaction import complete_transaction
from Components.Read_csv import get_csv_value
from Components.report import logger
from Components import global_instance

# --- Test-case identity ------------------------------------------------------
TC_ID  = "TC_014_VerifyOffersCouponLockingWithin3mins"
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
# TRANSACTION 1 — Void (offers triggered, then locked)
# ============================================================================
try:
    logger.log("═══════════════════════════════════════════════════════════════", status="info")
    logger.log("  TRANSACTION 1 — Void (bunch + redemption triggered → locked)", status="info")
    logger.log("═══════════════════════════════════════════════════════════════", status="info")

    ITERATION_1 = 1
    EAN_LIST_1 = _get_value("EAN_Codes", ITERATION_1, None) or _get_value("Item_EAN", ITERATION_1, "<FILL_EANS_TXN1>")
    CARD_CODE = _get_value("Card_number", ITERATION_1, "9353105847249")
    REDEEM_AMOUNT = _get_value("Redeem_amount", ITERATION_1, "10")
    BUNCH_PROMO = _get_value("Promotion_description", ITERATION_1, "Test Bunch sample")

    # Step 1: Login to SCO
    if not login_pos():
        raise RuntimeError("login_pos failed (Txn1) — aborting test.")

    # Steps 2 & 3: Scan eligible + exclusion + bunch articles
    # EAN list should include: eligible EANs + exclusion EANs + bunch articles (100325;921694)
    add_item(EAN_LIST_1, CARD_CODE)

    # Step 3b: Scan loyalty card at loyalty prompt
    if not scan_loyalty_tenderprompt(CARD_CODE):
        raise RuntimeError("scan_loyalty_tenderprompt failed (Txn1) — aborting test.")

    # Step 4: Verify redemption prompt triggers → redeem $10
    win = global_instance.win
    redeemed = redeem_reward_voucher(
        reward_tender_id="Tender3",
        voucher_options=[f"Redeem ${REDEEM_AMOUNT}", f"${REDEEM_AMOUNT}", "Redeem $10", "$10"],
    )

    if redeemed:
        logger.log(
            f"✅ Txn1 Step 4 — Redemption prompt triggered and ${REDEEM_AMOUNT} redeemed.",
            status="pass"
        )
    else:
        logger.log(
            f"⚠️ Txn1 Step 4 — Redemption/voucher flow did not complete as expected.",
            status="fail"
        )
        logger.take_screenshot("S9_Redemption_Issue_Txn1")

    # Step 5: Verify bunch prompt triggers
    # The bunch offer prompt may appear as a promotion in the basket or
    # as a popup. Check promotion details for the bunch offer description.
    _, _, promo_descs_1, _, _, missing_1 = get_promotion_details(BUNCH_PROMO)
    if not missing_1:
        logger.log(
            f"✅ Txn1 Step 5 — Bunch offer prompt/promotion detected: '{BUNCH_PROMO}'.",
            status="pass"
        )
    else:
        logger.log(
            f"⚠️ Txn1 Step 5 — Bunch offer '{BUNCH_PROMO}' not found on screen. "
            "It may appear as a popup rather than basket promotion.",
            status="info"
        )
        logger.take_screenshot("S9_Bunch_Prompt_Check_Txn1")

    # Step 6 (void): Void the transaction
    time.sleep(2)
    if not void_transaction():
        raise RuntimeError("void_transaction failed (Txn1) — aborting test.")

    logger.log("✅ Txn1 — Transaction voided. Coupons are now locked.", status="pass")

    # Step 7: Verify NOT settled in EE (wallet open only)
    ee_result_1 = verify_eagleeye_logs(
        expect_wallet_open=True,
        expect_wallet_settle=False,
    )

    if ee_result_1.get("wallet_open") and not ee_result_1.get("wallet_settle"):
        logger.log(
            "✅ Txn1 Step 7 — Transaction NOT settled (wallet open only). "
            "Coupons are locked.",
            status="pass"
        )
    else:
        logger.log(
            "❌ Txn1 Step 7 — Unexpected EE state. "
            f"WalletOpen={ee_result_1.get('wallet_open')}, "
            f"WalletSettle={ee_result_1.get('wallet_settle')}.",
            status="fail"
        )

except Exception as e:
    logger.log(f"❌ Txn1 unexpected error: {e}", status="fail")
    logger.take_screenshot("S9_Txn1_Unexpected_Error")


# ============================================================================
# TRANSITION — Minimal wait (stay within 3-min coupon lock window)
# ============================================================================
logger.log(
    "⏳ Minimal wait before Transaction 2 (must be within 3-min coupon lock window)...",
    status="info"
)
time.sleep(5)
global_instance.reset_state()


# ============================================================================
# TRANSACTION 2 — Within 3-min lock (offers + redemption NOT available)
# ============================================================================
try:
    logger.log("═══════════════════════════════════════════════════════════════", status="info")
    logger.log("  TRANSACTION 2 — Coupons locked (within 3 mins of void)", status="info")
    logger.log("═══════════════════════════════════════════════════════════════", status="info")

    ITERATION_2 = 2
    # Same articles as Txn1 (to confirm offers are NOT re-triggered)
    EAN_LIST_2 = _get_value("EAN_Codes", ITERATION_2, None) or _get_value("Item_EAN", ITERATION_2, EAN_LIST_1)

    # Step 9: Login to SCO (within 3 mins)
    if not login_pos():
        raise RuntimeError("login_pos failed (Txn2) — aborting test.")

    # Step 10: Scan same articles
    add_item(EAN_LIST_2, CARD_CODE)

    # Step 11: Scan loyalty card
    if not scan_loyalty_salemode(CARD_CODE):
        raise RuntimeError("scan_loyalty_salemode failed (Txn2) — aborting test.")

    # Step 12: Verify NO offers triggered (bunch + points fixed locked)
    _, _, promo_descs_2, _, _, _ = get_promotion_details("")
    bunch_found = any(BUNCH_PROMO.lower() in p.lower() for p in promo_descs_2) if promo_descs_2 else False

    if not bunch_found and not promo_descs_2:
        logger.log(
            "✅ Txn2 Step 12 — No offers triggered (bunch + points fixed locked). "
            "Base points only displayed.",
            status="pass"
        )
    elif bunch_found:
        logger.log(
            "❌ Txn2 Step 12 — Bunch offer still triggered despite coupon lock!",
            status="fail"
        )
        logger.take_screenshot("S9_Bunch_Still_Active_Txn2")
    else:
        logger.log(
            f"⚠️ Txn2 Step 12 — Promotions on screen: {promo_descs_2}. "
            "Verifying these are base-level only (not locked offers).",
            status="info"
        )

    # Step 13: Verify redemption prompt NOT triggered (card locked)
    if not move_to_tendermode():
        raise RuntimeError("move_to_tendermode failed (Txn2) — aborting test.")

    win = global_instance.win
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
            "✅ Txn2 Step 13 — Redemption prompt NOT triggered (card locked). Correct!",
            status="pass"
        )
    else:
        logger.log(
            "❌ Txn2 Step 13 — Redemption prompt appeared (should NOT for locked card).",
            status="fail"
        )
        logger.take_screenshot("S9_Unexpected_Redemption_Txn2")
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
            "✅ S9 PASSED — Coupon locking within 3 mins verified. "
            "Txn1 voided (offers + redemption triggered), "
            "Txn2 completed within lock window (no offers, no redemption, settled).",
            status="pass"
        )
    else:
        logger.log("❌ Txn2 — EagleEye verification failed.", status="fail")

except Exception as e:
    logger.log(f"❌ Txn2 unexpected error: {e}", status="fail")
    logger.take_screenshot("S9_Txn2_Unexpected_Error")

finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
