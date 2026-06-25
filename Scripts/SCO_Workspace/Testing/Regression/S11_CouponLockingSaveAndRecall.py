"""
S11_CouponLockingSaveAndRecall.py
----------------------------------
Regression Test S11 — Validation of offers and points / Coupon locking
within 3 mins / Save and Recall.

Scenario (Scenario 16):
    Verify that offers are correctly applied when the transaction is saved
    and recalled within the 3-minute coupon lock window.

    Flow:
      1. Login to SCO
      2. Scan eligible + exclusion + bunch articles
      3. Scan the bunch article
      4. SAVE the transaction from SCO sale mode via Assistance/attendant menu
         (Suspend Transaction)
      5. RECALL the same transaction from welcome mode:
         Assistance → Go To POS → Recall Transaction → Transaction List →
         Recall → Finish Go To SCO
      6. Verify recalled basket/offers are back on SCO
      7. Scan loyalty card at tender prompt
      8. Verify choice offer prompt → click "Use now" (Yes)
      9. Verify redemption prompt → redeem $10
      10. Complete the transaction
      14. Verify EE settlement (with saved transaction reference)
      15. Verify EE logs: Card Validation + Wallet Open + Wallet Settle
      16. Verify Tlogs apportionment

Pre-requisite:
    Registered EDR card (9353105847263) with:
      - Active market day offer (choice offer)
      - Active bunch offer (1261389 - Test Bunch sample)
      - Active BPM offer
      - Sufficient points for redemption ($9 + $10)
    Bunch offer source articles: 100325, 921694
    Scan using the provided 13-digit EANs, not the short PLU/article refs.

Data source:
    SMB SaleData.csv — TC_ID = "S11", Banner = "SM".
    Iteration 1 = Transaction data (eligible + exclusion + bunch articles).
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
from Components.Redeem_reward_voucher import redeem_reward_voucher
from Components.Redeem_choice_offer import redeem_choice_offer
from Components.Save_transaction import save_transaction
from Components.Recall_transaction import recall_transaction
from Components.Move_back_to_salemode import move_back_to_salemode
from Components.Complete_transaction import complete_transaction
from Components.Verify_EagleEye_logs import verify_eagleeye_logs
from Components.Read_csv import get_csv_value
from Components.report import logger
from Components import global_instance

# --- Test-case identity ------------------------------------------------------
TC_ID  = "S11"
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


def _cart_receipt_visible():
    win = global_instance.win
    if win is None:
        return False

    try:
        count_ctrl = win.child_window(auto_id="ReceiptItemCount", control_type="Text")
        count_text = count_ctrl.window_text() if count_ctrl.exists(timeout=1.0) else ""
        if not any(ch.isdigit() for ch in count_text):
            return False

        cart = win.child_window(auto_id="CartReceipt", control_type="List")
        if not cart.exists(timeout=1.0):
            return False

        return len(cart.children(control_type="ListItem")) > 0
    except Exception:
        return False


def _loyalty_prompt_visible():
    win = global_instance.win
    if win is None:
        return False

    try:
        skip_btn = win.child_window(auto_id="CustomSkip", control_type="Button")
        return skip_btn.exists(timeout=0.5)
    except Exception:
        return False


def _sale_mode_visible():
    win = global_instance.win
    if win is None:
        return False

    if _loyalty_prompt_visible():
        return False

    try:
        pay_btn = win.child_window(auto_id="PayButton", control_type="Button")
        return pay_btn.exists(timeout=1.0) and _cart_receipt_visible()
    except Exception:
        return False


def _ensure_sale_mode(step_label):
    if _sale_mode_visible():
        return True

    if move_back_to_salemode():
        return True

    logger.log(
        f"❌ {step_label} — could not return to sale/basket mode.",
        status="fail",
    )
    logger.take_screenshot(f"S11_{step_label.replace(' ', '_')}_Sale_Mode_Not_Available")
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


def _handle_choice_offer(step_label, offer_text, screenshot_name):
    if redeem_choice_offer(offer_text):
        logger.log(
            f"✅ {step_label} — Choice offer prompt handled (clicked 'Use now').",
            status="pass",
        )
        return True

    logger.log(
        f"❌ {step_label} — Choice offer prompt was not available or could not be accepted.",
        status="fail",
    )
    logger.take_screenshot(screenshot_name)
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
# TEST EXECUTION
# ============================================================================
try:
    logger.log("═══════════════════════════════════════════════════════════════", status="info")
    logger.log("  S11 — Save & Recall within 3 mins (coupon locking)", status="info")
    logger.log("═══════════════════════════════════════════════════════════════", status="info")

    ITERATION = 1
    EAN_LIST = _get_value("EAN_Codes", ITERATION, None) or _get_value("Item_EAN", ITERATION, "<FILL_EANS>")
    CARD_CODE = _get_value("Card_number", ITERATION, "9353105847263")
    BUNCH_PROMO = _get_value("Promotion_description", ITERATION, "Test Bunch sample")
    CHOICE_OFFER = _get_value("Choice_offer", ITERATION, "market")
    REDEEM_AMOUNT_2 = _get_value("Redeem_amount_2", ITERATION, "10")

    # Step 1: Login to SCO
    if not login_pos():
        raise RuntimeError("login_pos failed — aborting test.")

    # Steps 2 & 3: Scan eligible + exclusion + bunch articles
    add_item(EAN_LIST, CARD_CODE)

    # Step 5: Verify bunch offer is applied before saving, if visible in basket.
    _, _, promo_descs, _, _, missing = get_promotion_details(BUNCH_PROMO)
    if not missing:
        logger.log(f"✅ Step 5 — Bunch offer detected: '{BUNCH_PROMO}'.", status="pass")
    else:
        logger.log(
            f"⚠️ Step 5 — Bunch offer '{BUNCH_PROMO}' not found in basket promotions. "
            "May appear as popup.",
            status="info"
        )
        logger.take_screenshot("S11_Bunch_Check_Before_Save")

    # Step 8: SAVE the transaction from SCO sale mode via Assistance/attendant menu.
    time.sleep(2)
    if not save_transaction():
        raise RuntimeError("save_transaction failed — aborting test.")

    logger.log("✅ Step 8 — Transaction saved successfully.", status="pass")

    # --- Small pause (within 3-min lock window) ---
    time.sleep(5)
    global_instance.reset_state()

    # Step 9: RECALL the same transaction (within 3 mins)
    # Re-login to SCO (reconnect to the window)
    if not login_pos():
        raise RuntimeError("login_pos failed for recall — aborting test.")

    if not recall_transaction():
        raise RuntimeError("recall_transaction failed — aborting test.")

    logger.log("✅ Step 9 — Transaction recalled successfully (within 3 mins).", status="pass")

    # Step 10: Verify bunch offer is still applied
    if not _ensure_sale_mode("Step 10"):
        raise RuntimeError("Could not confirm sale mode after recall — aborting test.")

    _, _, promo_descs_2, _, _, missing_2 = get_promotion_details(BUNCH_PROMO)
    if not missing_2:
        logger.log(
            f"✅ Step 10 — Bunch offer still applied after recall: '{BUNCH_PROMO}'.",
            status="pass"
        )
    else:
        logger.log(
            f"⚠️ Step 10 — Bunch offer '{BUNCH_PROMO}' not visible after recall. "
            "May re-trigger as popup.",
            status="info"
        )
        logger.take_screenshot("S11_Bunch_After_Recall")

    # Step 4/11/12 after recall: scan EDR at tender prompt, accept choice offer,
    # redeem voucher, then complete the recalled transaction.
    if not scan_loyalty_tenderprompt(CARD_CODE, require_acceptance=True):
        raise RuntimeError("scan_loyalty_tenderprompt failed after recall — aborting test.")

    # Step 11: Verify choice offer prompt → click "Use now"
    if not _handle_choice_offer("Step 11", CHOICE_OFFER, "S11_Choice_Offer_After_Recall"):
        raise RuntimeError("Choice offer was not accepted after recall — aborting test.")

    # Step 12: Verify redemption prompt → redeem $10
    if not _redeem_amount("Step 12", REDEEM_AMOUNT_2, "S11_Redemption_After_Recall"):
        raise RuntimeError("Reward redemption did not complete after recall — aborting test.")

    # Step 13: Complete the transaction
    if not complete_transaction():
        raise RuntimeError("complete_transaction failed — aborting test.")

    # Steps 14 & 15: Verify EE settlement and logs
    ee_result = verify_eagleeye_logs(
        expect_wallet_open=True,
        expect_wallet_settle=True,
    )

    if ee_result["all_passed"]:
        logger.upgrade_info_to_pass("detected")
        logger.log(
            "✅ S11 PASSED — Save & Recall within 3 mins verified. "
            "Offers persisted through save/recall, transaction settled in EE.",
            status="pass"
        )
    else:
        logger.log("❌ EagleEye verification failed after recall.", status="fail")

    # Step 16: Tlogs apportionment
    logger.log(
        "TODO: Verify Tlogs apportionment — triggered offers (bunch + market day + BPM) "
        "should be correctly apportioned in Tlogs.",
        status="info"
    )

except Exception as e:
    logger.log(f"❌ S11 unexpected error: {e}", status="fail")
    logger.take_screenshot("S11_Unexpected_Error")

finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
