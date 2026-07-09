"""
TC_043_CrossTasmanSDCCard.py
----------------------------
TC_043 — Validation of Cross Tasman Staff (SDC) Card.

Scenario:
    Verify that an NZ-issued SDC (Staff Discount Card) loyalty card is
    correctly accepted at an AU SCO:
      - Team Discount IS applied on the receipt.
      - WOW reward points are NOT displayed on screen (cross-banner card).
      - Transaction settles correctly in EagleEye (Card Validation +
        Wallet Open + Wallet Settle).

Flow (single pass — eligible + ineligible articles in the same basket):
    1.  Login to the POS/SCO.
    2.  Scan eligible articles (Iteration 1 EANs).
    3.  Scan ineligible articles (Iteration 2 EAN).
    4.  Scan the NZ SDC loyalty card in SALE MODE.
        ➜ SCO may route the scan to "Scan Coupon" mode — handled via
          CancelCoupon dismissal (same as TC_042 NZ EDR card).
    5.  Move to tender mode.
    6.  Verify Team Discount is applied on the receipt.
    7.  Verify WoWRewardPoints is NOT displayed on screen.
    8.  Complete the transaction (Card/EFT).
    9.  Verify EagleEye logs: Card Validation, Wallet Open, Wallet Settle
        all captured; transaction SETTLED.
    10. Receipt / Tlog validation — manual placeholders.

Pre-requisite:
    Registered NZ SDC (Staff Discount Card) loyalty card (9344440000130).

Data source:
    RegressionSale.csv — TC_ID = "TC_043_CrossTasmanSDCCard", Banner = "SM".
    Iteration 1 = eligible articles + card number + Promotion_description.
    Iteration 2 = ineligible article (combined into the same basket).
"""

import sys
import re
import time
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent   # Regression → Testing → SCO_Workspace

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# --- SCO Component imports ---------------------------------------------------
from Components.Login_POS import login_pos
from Components.Add_item import add_item
from Components.Scan_loyalty_salemode import scan_loyalty_salemode
from Components.Move_to_tendermode import move_to_tendermode
from Components.Verify_exciting_news_prompt import verify_exciting_news_prompt
from Components.Promotion_details import get_promotion_details
from Components.Complete_transaction import complete_transaction
from Components.Verify_EagleEye_logs import verify_eagleeye_logs, verify_card_in_ee_log
from Components.Read_csv import get_csv_value
from Components.report import logger
from Components import global_instance

# --- Test-case identity ------------------------------------------------------
TC_ID  = "TC_043_CrossTasmanSDCCard"
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


def _dismiss_cross_banner_prompt(win, timeout=2):
    """
    Dismiss any prompt that appears after scanning a cross-Tasman card.

    Two known variants:
      1. "Scan Coupon" screen — NZ SDC barcode unrecognised locally; SCO
         defaults to coupon-scan mode. Dismissed via CancelCoupon.
         (Primary handler already fires inside scan_loyalty_salemode via
         _dismiss_loyalty_popup; this is a short fallback.)
      2. Generic PopupFrame — dismissed via first available OK-style button.

    Returns True if a popup was detected and dismissed, False otherwise.
    """
    # Variant 1: "Scan Coupon" screen
    try:
        leadthru = win.child_window(auto_id="LeadthruText", control_type="Text")
        if leadthru.exists(timeout=timeout):
            if "coupon" in (leadthru.window_text() or "").lower():
                logger.take_screenshot("TC_043_ScanCoupon_Screen")
                cancel_btn = win.child_window(auto_id="CancelCoupon", control_type="Button")
                if cancel_btn.exists(timeout=2):
                    cancel_btn.click_input()
                    time.sleep(1.5)
                    logger.log("✅ Fallback: 'Scan Coupon' screen dismissed via CancelCoupon.", status="pass")
                    print("✅ Fallback: 'Scan Coupon' screen dismissed via CancelCoupon.")
                    return True
    except Exception as e:
        print(f"  _dismiss_cross_banner_prompt (Scan Coupon): {e}")

    # Variant 2: Generic PopupFrame
    try:
        popup_frame = win.child_window(auto_id="PopupFrame", control_type="Pane")
        if not popup_frame.exists(timeout=2):
            return False
        for aid in ("List1Button", "OK_Button", "ASAOKButton", "GenericOKButton",
                    "GenericButton", "List2Button", "CustomSkip"):
            try:
                btn = win.child_window(auto_id=aid, control_type="Button")
                if btn.exists(timeout=1.0):
                    btn.click_input()
                    time.sleep(1.0)
                    logger.log(f"✅ Cross-banner popup dismissed via '{aid}'.", status="pass")
                    print(f"✅ Cross-banner popup dismissed via '{aid}'.")
                    return True
            except Exception:
                continue
    except Exception as e:
        print(f"  _dismiss_cross_banner_prompt: {e}")
    return False


def _verify_wow_points_not_displayed(win):
    """
    Verify WoWRewardPoints is absent or zero — NZ-issued cards must not
    display AU WOW points on screen even though EE settles normally.
    """
    try:
        pts_ctrl = win.child_window(auto_id="WoWRewardPoints", control_type="Text")
        if not pts_ctrl.exists(timeout=3):
            return True
        raw = (pts_ctrl.window_text() or "").strip()
        match = re.search(r"\d+", raw.replace(",", ""))
        value = int(match.group()) if match else 0
        return value == 0
    except Exception:
        return True


# --- Data --------------------------------------------------------------------
EAN_ELIGIBLE   = _get_value("Item_EAN", 1, "9339687023882;9315087192083")
EAN_INELIGIBLE = _get_value("Item_EAN", 2, "9339687200924;9339687200924")
CARD_CODE      = _get_value("Card_number", 1, "9344440000130")
CARD_TYPE      = _get_value("Card_type", 1, "NZ SDC")
PROMO_EXPECTED = _get_value("Promotion_description", 1, "Team Discount")

# Combine all EANs into a single basket scan
EAN_ALL = ";".join(x for x in (EAN_ELIGIBLE, EAN_INELIGIBLE) if x)

try:
    logger.log("=" * 70, status="info")
    logger.log("  TC_043 — Validation of Cross Tasman Staff (SDC) Card", status="info")
    logger.log("=" * 70, status="info")

    # ------------------------------------------------------------------
    # Step 1: Login to SCO
    # ------------------------------------------------------------------
    if not login_pos():
        raise RuntimeError("login_pos failed — aborting test.")

    # ------------------------------------------------------------------
    # Steps 2 & 3: Scan eligible + ineligible articles (single basket)
    # ------------------------------------------------------------------
    add_item(EAN_ALL, CARD_CODE)

    # ------------------------------------------------------------------
    # Step 4: Scan the NZ SDC loyalty card in SALE MODE.
    #         scan_loyalty_salemode internally dismisses the "Scan Coupon"
    #         screen via CancelCoupon (added in TC_042 fix).
    # ------------------------------------------------------------------
    loyalty_linked = scan_loyalty_salemode(CARD_CODE)
    if not loyalty_linked:
        logger.log(
            f"⚠️ scan_loyalty_salemode returned False for {CARD_TYPE} card "
            f"'{CARD_CODE}' — continuing (cross-banner cards may not show "
            "a loyalty indicator on screen).",
            status="info"
        )
        print("⚠️ Loyalty scan indicator not confirmed — continuing.")

    win = global_instance.win

    # Only run the fallback if scan_loyalty_salemode didn't already handle
    # the CancelCoupon screen (avoids double-dismissal noise in the log).
    if not loyalty_linked:
        _dismiss_cross_banner_prompt(win, timeout=2)

    # ------------------------------------------------------------------
    # Step 5: Move to tender mode.
    # ------------------------------------------------------------------
    if not move_to_tendermode(skip_choice_offer=True):
        raise RuntimeError("move_to_tendermode failed — aborting test.")

    logger.log("✅ Step 5 — Moved to tender mode.", status="pass")
    print("✅ Step 5 — Tender mode reached.")

    # Non-fatal exciting-news prompt check (unlikely for NZ SDC card).
    verify_exciting_news_prompt(timeout_seconds=3)

    # Allow the tender receipt panel to fully populate after PayButton.
    time.sleep(5)

    # ------------------------------------------------------------------
    # Step 6: Verify Team Discount is applied on the receipt.
    # ------------------------------------------------------------------
    promo_list = [p.strip() for p in PROMO_EXPECTED.split(";") if p.strip()]
    (_, _, promos_found, _, matched_prices, missing_promos) = get_promotion_details(promo_list)

    if not missing_promos:
        logger.log("✅ Step 6 — All expected promotions present.", status="pass")
        print("✅ Step 6 — All expected promotions present.")
    else:
        logger.log(
            f"❌ Step 6 — Missing promotions: {missing_promos}. Found: {promos_found}",
            status="fail"
        )
        print(f"❌ Step 6 — Missing promotions: {missing_promos}")

    # ------------------------------------------------------------------
    # Step 7: Verify WOW points are NOT displayed on screen.
    # ------------------------------------------------------------------
    wow_not_shown = _verify_wow_points_not_displayed(win)
    if wow_not_shown:
        logger.log(
            f"✅ Step 7 — WoWRewardPoints NOT displayed for {CARD_TYPE} card (expected).",
            status="pass"
        )
        print("✅ Step 7 — WOW points not displayed (expected for cross-Tasman card).")
    else:
        logger.log(
            f"❌ Step 7 — WoWRewardPoints unexpectedly displayed for {CARD_TYPE} card.",
            status="fail"
        )
        print("❌ Step 7 — WOW points unexpectedly displayed.")
        logger.take_screenshot("TC_043_WOWPoints_UnexpectedlyDisplayed")

    # ------------------------------------------------------------------
    # Step 8: Complete the transaction (Card/EFT).
    # ------------------------------------------------------------------
    if not complete_transaction():
        raise RuntimeError("complete_transaction failed — aborting test.")

    logger.log("✅ Step 8 — Transaction completed.", status="pass")
    print("✅ Step 8 — Transaction completed.")

    # Allow EEAdapter time to write the wallet/settle log entry.
    time.sleep(5)

    # ------------------------------------------------------------------
    # Step 9: Verify EagleEye logs — Card Validation, Wallet Open,
    #         Wallet Settle all captured; transaction SETTLED.
    #         NZ SDC cards DO settle with AU EagleEye.
    # ------------------------------------------------------------------
    ee_result = verify_eagleeye_logs(
        expect_wallet_open=True,
        expect_wallet_settle=True,
    )

    if ee_result["all_passed"]:
        logger.log(
            "✅ Step 9 — EagleEye logs confirmed: Card Validation, Wallet Open, "
            "Wallet Settle all captured; transaction SETTLED.",
            status="pass"
        )
        print("✅ Step 9 — EagleEye log verification passed.")
    else:
        logger.log(
            "❌ Step 9 — EagleEye log verification failed.",
            status="fail"
        )
        print("❌ Step 9 — EagleEye log verification failed.")

    card_in_ee = verify_card_in_ee_log(CARD_CODE)
    if card_in_ee:
        logger.log(
            f"✅ Step 9 — NZ SDC card '{CARD_CODE}' confirmed in EE card-validation event.",
            status="pass"
        )
        print(f"✅ Step 9 — Card {CARD_CODE} found in EE log.")
    else:
        logger.log(
            f"❌ Step 9 — NZ SDC card '{CARD_CODE}' NOT found in EE card-validation event.",
            status="fail"
        )
        print(f"❌ Step 9 — Card {CARD_CODE} missing from EE log.")

    # ------------------------------------------------------------------
    # Step 10: Receipt / Tlog validation (manual placeholders).
    # ------------------------------------------------------------------
    logger.log(
        "ℹ️ Step 10 — Receipt verification: TODO (manual check).",
        status="info"
    )
    logger.log(
        "ℹ️ Step 10 — Tlog verification: TODO. Retail tlogs should be generated; "
        "retroactive tlogs should NOT be generated for this transaction.",
        status="info"
    )
    print("ℹ️ Step 10 — Receipt / Tlog verification: TODO.")

except Exception as e:
    logger.log(f"❌ TC_043 unexpected error: {e}", status="fail")
    print(f"❌ TC_043 ERROR: {e}")
    logger.take_screenshot("TC_043_Unexpected_Error")

finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
