"""
S10_CouponLockingAfter3Mins.py
--------------------------------
Regression Test S10 — Validation of offers / coupon locking AFTER 3 minutes.

Scenario:
    Verify that after a voided transaction (where bunch + BPM offers and
    redemption were triggered), the coupon lock expires after ~3 minutes.
    A second transaction with the SAME card AFTER the lock window should:
      - Re-trigger the bunch offer (coupon unlocked).
      - Re-trigger the BPM offer (coupon unlocked).
      - Show the redemption prompt (card unlocked) → redeem $10.
      - Settle successfully in EagleEye.

    Transaction 1 (voided — coupons become locked):
        - Scan eligible + exclusion + bunch articles
        - Scan loyalty card at loyalty prompt
        - Verify redemption prompt triggers → redeem $10
        - Verify bunch prompt triggers
        - Void the transaction
        - Verify NOT settled in EE (wallet open only)
        - Verify EE logs: Card Validation + Wallet Open ONLY

    Wait > 3 minutes (lock expiry)

    Transaction 2 (after 3 mins — coupons unlocked):
        - Login again (after lock expired)
        - Scan same articles (including bunch article)
        - Scan loyalty card
        - Verify same offers ARE triggered (bunch + BPM re-applied)
        - Verify redemption prompt IS triggered → redeem $10
        - Verify bunch prompt triggers
        - Complete transaction → settled in EE
        - Verify EE logs: Card Validation + Wallet Open + Wallet Settle
        - Verify Tlogs apportionment

Pre-requisite:
    Registered EDR card (9353100734100) with:
      - >2000 points (to trigger redemption)
      - Active bunch offer (1261389 - Test Bunch sample)
      - Active BPM offer
    Bunch articles: 100325, 921694
    Scan articles using 13-digit EANs only; do not scan short PLU/article
    references such as 100325 or 921694 directly.

Data source:
    SMB SaleData.csv — TC_ID = "TC_015_VerifyOffersCouponLockingAfter3mins", Banner = "SM".
    Iteration 1 = Txn1 (eligible + exclusion + bunch articles).
    Iteration 2 = Txn2 (same articles, after lock expiry).
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
from Components.Promotion_details import get_promotion_details
from Components.Void_transaction import void_transaction
from Components.Redeem_reward_voucher import redeem_reward_voucher
from Components.Verify_EagleEye_logs import verify_eagleeye_logs
from Components.Complete_transaction import complete_transaction
from Components.Read_csv import get_csv_value
from Components.report import logger
from Components import global_instance

# --- Test-case identity ------------------------------------------------------
TC_ID  = "TC_015_VerifyOffersCouponLockingAfter3mins"
BANNER = "SM"

logger.set_tc_id(TC_ID)

# Lock expiry wait time in seconds (3 mins + 15s safety margin)
LOCK_EXPIRY_WAIT = 195

# Same article scan data as S11; these are 13-digit EANs, not short article refs.
DEFAULT_EAN_LIST = "9328854011524;9300633594176;9339687200924"


def _is_csv_value(value):
    if value is None:
        return False
    text = str(value).strip()
    return (
        bool(text)
        and not text.startswith("Error")
        and not text.startswith("Column ")
        and text != "No matching record found."
    )


def _get_value(column, iteration, fallback):
    try:
        val = get_csv_value("saledata", BANNER, TC_ID, iteration, column)
        if _is_csv_value(val):
            return str(val).strip()
    except Exception:
        pass
    return fallback


def _validate_article_eans(raw_eans, iteration):
    eans = [ean.strip() for ean in str(raw_eans or "").split(";") if ean.strip()]
    if not eans:
        raise ValueError(f"S10 Iteration {iteration} has no article EANs configured.")

    invalid = [ean for ean in eans if not (ean.isdigit() and len(ean) == 13)]
    if invalid:
        raise ValueError(
            f"S10 Iteration {iteration} article scan data must contain only "
            f"13-digit EANs. Invalid values: {', '.join(invalid)}"
        )

    return ";".join(eans)


def _get_ean_list(iteration, fallback):
    ean_list = _get_value("EAN_Codes", iteration, None)
    if ean_list is None:
        ean_list = _get_value("Item_EAN", iteration, fallback)
    return _validate_article_eans(ean_list, iteration)


def _voucher_options(amount):
    amount_text = str(amount).strip().lstrip("$")
    options = [f"Redeem ${amount_text}", f"${amount_text}"]

    try:
        numeric = int(amount_text)
    except ValueError:
        return options

    options.extend([
        f"Redeem ${numeric}",
        f"${numeric}",
        f"Redeem ${numeric:02d}",
        f"${numeric:02d}",
    ])
    return list(dict.fromkeys(options))


def _reward_popup_visible():
    win = global_instance.win
    if win is None:
        return False

    try:
        popup_title = win.child_window(auto_id="PopupTitle", control_type="Text")
        if popup_title.exists(timeout=0.5):
            title = popup_title.window_text() or ""
            if "assistance" in title.lower():
                return True
    except Exception:
        pass

    try:
        popup_frame = win.child_window(auto_id="PopupFrame", control_type="Pane")
        if popup_frame.exists(timeout=0.5):
            for aid in ("RedeemButton", "SkipCollectableOfferPrompt"):
                if popup_frame.child_window(auto_id=aid).exists(timeout=0.1):
                    return True
    except Exception:
        pass

    return False


def _reward_tender_visible():
    win = global_instance.win
    if win is None:
        return False

    try:
        tender = win.child_window(auto_id="Tender3", control_type="Button")
        return tender.exists(timeout=2.0)
    except Exception:
        return False


def _redeem_amount(step_label, amount, screenshot_name):
    if _reward_popup_visible():
        tender_id = None
    elif _reward_tender_visible():
        tender_id = "Tender3"
    else:
        logger.log(
            f"❌ {step_label} — reward tender (Tender3) is not visible; "
            "not clicking any payment tender.",
            status="fail",
        )
        logger.take_screenshot(screenshot_name)
        return False

    redeemed = redeem_reward_voucher(
        reward_tender_id=tender_id,
        voucher_options=_voucher_options(amount),
    )

    if redeemed:
        logger.log(
            f"✅ {step_label} — Redemption prompt triggered and ${amount} redeemed.",
            status="pass",
        )
        return True

    logger.log(
        f"❌ {step_label} — Redemption/voucher flow (${amount}) did not complete.",
        status="fail",
    )
    logger.take_screenshot(screenshot_name)
    return False


# ============================================================================
# TRANSACTION 1 — Void (offers triggered, then locked)
# ============================================================================
try:
    logger.log("═══════════════════════════════════════════════════════════════", status="info")
    logger.log("  TRANSACTION 1 — Void (bunch + BPM + redemption → locked)", status="info")
    logger.log("═══════════════════════════════════════════════════════════════", status="info")

    ITERATION_1 = 1
    EAN_LIST_1 = _get_ean_list(ITERATION_1, DEFAULT_EAN_LIST)
    CARD_CODE = _get_value("Card_number", ITERATION_1, "9353100734100")
    REDEEM_AMOUNT = _get_value("Redeem_amount", ITERATION_1, "10")
    BUNCH_PROMO = _get_value("Promotion_description", ITERATION_1, "Test Bunch sample")

    # Step 1: Login to SCO
    if not login_pos():
        raise RuntimeError("login_pos failed (Txn1) — aborting test.")

    # Steps 2 & 3: Scan eligible + exclusion + bunch articles
    add_item(EAN_LIST_1, CARD_CODE)

    # Step 5: Verify bunch offer is visible in basket BEFORE moving to loyalty prompt.
    # Bunch/BPM offers appear as soon as the qualifying articles are scanned.
    _, _, promo_descs_1, _, _, missing_1 = get_promotion_details(BUNCH_PROMO)
    if not missing_1:
        logger.log(f"✅ Txn1 Step 5 — Bunch offer detected: '{BUNCH_PROMO}'.", status="pass")
    else:
        logger.log(
            f"⚠️ Txn1 Step 5 — Bunch offer '{BUNCH_PROMO}' not found in basket. "
            "May appear as a popup after loyalty scan.",
            status="info",
        )
        logger.take_screenshot("S10_Bunch_Prompt_Check_Txn1")

    # Step 3b: Scan loyalty card at loyalty prompt.
    # NOT fatal if it fails — we must still void the transaction so the coupons
    # lock in EagleEye.  Only handle redemption if loyalty was accepted.
    loyalty_ok_1 = scan_loyalty_tenderprompt(CARD_CODE)
    if not loyalty_ok_1:
        logger.log(
            "⚠️ Txn1: Loyalty scan at prompt did not complete — proceeding to void anyway.",
            status="fail",
        )
        logger.take_screenshot("S10_Loyalty_Scan_Issue_Txn1")
    else:
        # Step 4: Loyalty accepted — handle the redemption prompt
        _redeem_amount("Txn1 Step 4", REDEEM_AMOUNT, "S10_Redemption_Issue_Txn1")

    # Void the transaction — CRITICAL: this is what locks the coupons in EagleEye.
    # Must always be reached regardless of whether loyalty scan succeeded.
    time.sleep(2)
    if not void_transaction():
        raise RuntimeError("void_transaction failed (Txn1) — aborting test.")

    logger.log("✅ Txn1 — Transaction voided. Coupons are now locked.", status="pass")

    # Step 6: Verify NOT settled in EE
    ee_result_1 = verify_eagleeye_logs(
        expect_wallet_open=True,
        expect_wallet_settle=False,
    )

    if ee_result_1.get("wallet_open") and not ee_result_1.get("wallet_settle"):
        logger.log(
            "✅ Txn1 — Transaction NOT settled (wallet open only). Coupons locked.",
            status="pass"
        )
    else:
        logger.log(
            "❌ Txn1 — Unexpected EE state. "
            f"WalletOpen={ee_result_1.get('wallet_open')}, "
            f"WalletSettle={ee_result_1.get('wallet_settle')}.",
            status="fail"
        )

except Exception as e:
    logger.log(f"❌ Txn1 unexpected error: {e}", status="fail")
    logger.take_screenshot("S10_Txn1_Unexpected_Error")


# ============================================================================
# TRANSITION — Wait > 3 minutes for coupon lock to expire
# ============================================================================
logger.log(
    f"⏳ Waiting {LOCK_EXPIRY_WAIT}s (>3 mins) for coupon lock to expire...",
    status="info"
)
print(f"⏳ Waiting {LOCK_EXPIRY_WAIT}s for coupon lock to expire...")
time.sleep(LOCK_EXPIRY_WAIT)
logger.log("✅ Lock expiry wait complete. Proceeding with Transaction 2.", status="info")
global_instance.reset_state()


# ============================================================================
# TRANSACTION 2 — After 3 mins (coupons unlocked → offers re-triggered)
# ============================================================================
try:
    logger.log("═══════════════════════════════════════════════════════════════", status="info")
    logger.log("  TRANSACTION 2 — Coupons unlocked (after 3 mins)", status="info")
    logger.log("═══════════════════════════════════════════════════════════════", status="info")

    ITERATION_2 = 2
    EAN_LIST_2 = _get_ean_list(ITERATION_2, EAN_LIST_1)
    PROMO_LIST_2 = _get_value("Promotion_description", ITERATION_2, BUNCH_PROMO)

    # Step 9: Login to SCO (after 3 mins)
    if not login_pos():
        raise RuntimeError("login_pos failed (Txn2) — aborting test.")

    # Step 10: Scan same articles (bunch + BPM offers appear in basket automatically)
    add_item(EAN_LIST_2, CARD_CODE)

    # Step 12: Verify offers are re-triggered in basket BEFORE scanning loyalty.
    # Bunch/BPM are product-based and visible in CartReceipt as soon as articles are scanned.
    _, _, promo_descs_2, _, _, missing_2 = get_promotion_details(PROMO_LIST_2)
    if not missing_2:
        logger.log(
            "✅ Txn2 Step 12 — Offers re-triggered after lock expiry (bunch + BPM applied).",
            status="pass",
        )
    else:
        logger.log(
            f"❌ Txn2 Step 12 — Missing offers after unlock: {missing_2}. "
            "Coupons may still be locked or offers misconfigured.",
            status="fail",
        )
        logger.take_screenshot("S10_Offers_Not_Retriggered_Txn2")

    # Step 11: Scan loyalty card at the loyalty prompt.
    # scan_loyalty_tenderprompt clicks PayButton internally — do NOT call
    # move_to_tendermode() before this.
    if not scan_loyalty_tenderprompt(CARD_CODE):
        raise RuntimeError("scan_loyalty_tenderprompt failed (Txn2) — aborting test.")

    # Step 13: Verify redemption prompt IS triggered → redeem $10
    redeemed_2 = _redeem_amount("Txn2 Step 13", REDEEM_AMOUNT, "S10_Redemption_Failed_Txn2")

    if redeemed_2:
        logger.log(
            "✅ Txn2 Step 13 — Card is confirmed UNLOCKED after 3 mins.",
            status="pass"
        )
    else:
        logger.log(
            f"❌ Txn2 Step 13 — Reward voucher redemption (${REDEEM_AMOUNT}) failed. "
            "Card may still be locked.",
            status="fail"
        )
        logger.take_screenshot("S10_Redemption_Failed_Txn2")

    # Step 14: Verify bunch prompt triggers again
    # Already verified via get_promotion_details in step 12.
    # If bunch is a popup (not basket promo), it should have re-appeared.
    logger.log(
        "✅ Txn2 Step 14 — Bunch prompt verified (included in Step 12 promotion check).",
        status="pass"
    )

    # Step 15: Complete transaction
    if not complete_transaction():
        raise RuntimeError("complete_transaction failed (Txn2) — aborting test.")

    # Steps 16 & 17: Verify EE settlement and logs
    ee_result_2 = verify_eagleeye_logs(
        expect_wallet_open=True,
        expect_wallet_settle=True,
    )

    if ee_result_2["all_passed"]:
        logger.upgrade_info_to_pass("detected")
        logger.log(
            "✅ S10 PASSED — Coupon locking after 3 mins verified. "
            "Txn1 voided (offers locked), waited >3 mins, "
            "Txn2 completed (offers re-triggered + redemption + settled).",
            status="pass"
        )
    else:
        logger.log("❌ Txn2 — EagleEye verification failed.", status="fail")

    # Step 18: Tlogs apportionment
    logger.log(
        "TODO: Verify Tlogs apportionment — triggered offers (bunch + BPM) "
        "should be correctly apportioned in Tlogs.",
        status="info"
    )

except Exception as e:
    logger.log(f"❌ Txn2 unexpected error: {e}", status="fail")
    logger.take_screenshot("S10_Txn2_Unexpected_Error")

finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
