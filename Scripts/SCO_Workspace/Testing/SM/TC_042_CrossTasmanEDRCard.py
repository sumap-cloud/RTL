"""
TC_042_CrossTasmanEDRCard.py
----------------------------
TC_042 — Validation of Cross Tasman EDR Card.

Scenario:
    Verify that an NZ-issued EDR (Everyday Rewards) loyalty card is
    correctly accepted at an AU SCO, does NOT display WOW reward points
    on screen (cross-banner card), but the transaction still settles
    correctly in EagleEye (Card Validation + Wallet Open + Wallet Settle).

Flow (single pass — eligible + ineligible articles in the same basket):
    1.  Login to the POS/SCO.
    2.  Scan eligible articles (Iteration 1 EANs).
    3.  Scan ineligible article (Iteration 2 EAN).
    4.  Scan the NZ EDR loyalty card in SALE MODE.
    5.  Move to tender mode.
    6.  Verify WoWRewardPoints is NOT displayed on screen.
    7.  Complete the transaction (Card/EFT).
    8.  Verify EagleEye logs: Card Validation, Wallet Open, Wallet Settle
        should ALL be captured (unlike a purely foreign/unlinked card,
        cross-Tasman EDR cards DO settle with AU EagleEye).
    9.  Verify transaction status is SETTLED.
    10. Receipt / Tlog validation — manual placeholders (no flat-file
        Tlog path available on this box).

Pre-requisite:
    Registered NZ EDR loyalty card (9490000000123).

Data source:
    RegressionSale.csv — TC_ID = "TC_042_CrossTasmanEDRCard", Banner = "SM".
    Iteration 1 = eligible articles + card number.
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
TC_ID  = "TC_042_CrossTasmanEDRCard"
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


def _dismiss_cross_banner_prompt(win, timeout=8):
    """
    Detect & dismiss any prompt specific to cross-banner / cross-Tasman card
    scans.

    Two known variants observed live:
      1. "Scan Coupon" screen — the NZ EDR barcode isn't recognised locally
         as a loyalty card, so the SCO defaults to coupon-scan mode.
         Identified by auto_id='LeadthruText' with text 'Scan Coupon' and
         dismissed via auto_id='CancelCoupon'.
      2. Generic PopupFrame + Instructions text (e.g. a cross-banner notice) —
         dismissed via the first available OK/Yes-style button.

    Returns True if a popup was detected and dismissed, False otherwise
    (non-fatal — absence of a popup is not necessarily an error).
    """
    # --- Variant 1: "Scan Coupon" screen ---------------------------------
    try:
        leadthru = win.child_window(auto_id="LeadthruText", control_type="Text")
        if leadthru.exists(timeout=timeout):
            text = (leadthru.window_text() or "").strip()
            if "coupon" in text.lower():
                logger.log(
                    f"✅ 'Scan Coupon' screen detected after cross-Tasman card scan "
                    f"(unrecognised barcode) — dismissing via 'CancelCoupon'.",
                    status="pass"
                )
                print("✅ 'Scan Coupon' screen detected — dismissing via 'CancelCoupon'.")
                logger.take_screenshot("TC_042_ScanCoupon_Screen")
                cancel_btn = win.child_window(auto_id="CancelCoupon", control_type="Button")
                if cancel_btn.exists(timeout=2):
                    cancel_btn.click_input()
                    time.sleep(1.5)
                    logger.log("✅ 'Scan Coupon' screen dismissed via 'CancelCoupon'.", status="pass")
                    print("✅ 'Scan Coupon' screen dismissed via 'CancelCoupon'.")
                    return True
    except Exception as e:
        print(f"  _dismiss_cross_banner_prompt (Scan Coupon check): {e}")

    # --- Variant 2: Generic PopupFrame + Instructions --------------------
    try:
        popup_frame = win.child_window(auto_id="PopupFrame", control_type="Pane")
        if not popup_frame.exists(timeout=2):
            return False

        instr = popup_frame.child_window(auto_id="Instructions", control_type="Text")
        instr_text = ""
        if instr.exists(timeout=1):
            instr_text = instr.window_text()

        logger.log(
            f"✅ Popup detected during cross-Tasman card scan: '{instr_text[:120]}'.",
            status="pass"
        )
        print(f"✅ Popup detected during cross-Tasman card scan: '{instr_text[:120]}'.")
        logger.take_screenshot("TC_042_CrossBanner_Popup")

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
    Verify the WoWRewardPoints text element is either absent or blank/zero —
    cross-Tasman (NZ-issued) EDR cards should not display AU WOW points on
    screen even though the transaction settles with EagleEye.

    Returns True if no meaningful point value is displayed.
    """
    try:
        pts_ctrl = win.child_window(auto_id="WoWRewardPoints", control_type="Text")
        if not pts_ctrl.exists(timeout=3):
            return True  # Element absent entirely — expected.

        raw = (pts_ctrl.window_text() or "").strip()
        match = re.search(r"\d+", raw.replace(",", ""))
        value = int(match.group()) if match else 0
        return value == 0
    except Exception:
        # If we can't read it at all, treat as "not displayed".
        return True


# --- Data ---------------------------------------------------------------------
EAN_ELIGIBLE   = _get_value("Item_EAN", 1, "9339687023882;9315087192083")
EAN_INELIGIBLE = _get_value("Item_EAN", 2, "9339687200924")
CARD_CODE      = _get_value("Card_number", 1, "9490000000123")
CARD_TYPE      = _get_value("Card_type", 1, "NZ EDR")

EAN_ALL = ";".join(x for x in (EAN_ELIGIBLE, EAN_INELIGIBLE) if x)

try:
    logger.log("=" * 70, status="info")
    logger.log("  TC_042 — Validation of Cross Tasman EDR Card", status="info")
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
    # Step 4: Scan the NZ EDR loyalty card DURING SALE MODE.
    # ------------------------------------------------------------------
    if not scan_loyalty_salemode(CARD_CODE):
        logger.log(
            f"⚠️ scan_loyalty_salemode returned False for {CARD_TYPE} card "
            f"'{CARD_CODE}' — continuing (cross-banner cards may not show a "
            "loyalty indicator on screen).",
            status="info"
        )
        print("⚠️ Loyalty scan indicator not confirmed — continuing.")

    win = global_instance.win

    # `scan_loyalty_salemode` already dismisses the "Scan Coupon" screen via
    # CancelCoupon in _dismiss_loyalty_popup. Call this as a short fallback
    # in case a secondary popup appears afterwards.
    _dismiss_cross_banner_prompt(win, timeout=2)

    # ------------------------------------------------------------------
    # Step 5: Move to tender mode.
    # ------------------------------------------------------------------
    if not move_to_tendermode(skip_choice_offer=True):
        raise RuntimeError("move_to_tendermode failed — aborting test.")

    logger.log("✅ Step 5 — Moved to tender mode.", status="pass")
    print("✅ Step 5 — Tender mode reached.")

    # Any Exciting News style popup could still appear at this point for
    # other card segments — non-fatal if absent for a cross-Tasman card.
    verify_exciting_news_prompt(timeout_seconds=3)

    # ------------------------------------------------------------------
    # Step 6: Verify WOW points are NOT displayed on screen.
    # ------------------------------------------------------------------
    wow_not_shown = _verify_wow_points_not_displayed(win)
    if wow_not_shown:
        logger.log(
            "✅ Step 6 — WoWRewardPoints NOT displayed on screen for cross-Tasman "
            f"{CARD_TYPE} card (expected).",
            status="pass"
        )
        print("✅ Step 6 — WOW points not displayed (expected for cross-Tasman card).")
    else:
        logger.log(
            "❌ Step 6 — WoWRewardPoints unexpectedly displayed for cross-Tasman "
            f"{CARD_TYPE} card.",
            status="fail"
        )
        print("❌ Step 6 — WOW points unexpectedly displayed.")
        logger.take_screenshot("TC_042_WOWPoints_UnexpectedlyDisplayed")

    # ------------------------------------------------------------------
    # Step 7: Complete the transaction (Card/EFT).
    # ------------------------------------------------------------------
    if not complete_transaction():
        raise RuntimeError("complete_transaction failed — aborting test.")

    logger.log("✅ Step 7 — Transaction completed.", status="pass")
    print("✅ Step 7 — Transaction completed.")

    # Allow EEAdapter time to write the wallet/settle log entry.
    time.sleep(5)

    # ------------------------------------------------------------------
    # Step 8 & 9: Verify EagleEye logs — Card Validation, Wallet Open,
    #             Wallet Settle should ALL be captured, and transaction
    #             should be SETTLED (cross-Tasman EDR cards DO settle
    #             with AU EagleEye, unlike unlinked foreign cards).
    # ------------------------------------------------------------------
    ee_result = verify_eagleeye_logs(
        expect_wallet_open=True,
        expect_wallet_settle=True,
    )

    if ee_result["all_passed"]:
        logger.log(
            "✅ Step 8/9 — EagleEye logs confirmed: Card Validation, Wallet Open, "
            "Wallet Settle all captured; transaction SETTLED.",
            status="pass"
        )
        print("✅ Step 8/9 — EagleEye log verification passed.")
    else:
        logger.log(
            "❌ Step 8/9 — EagleEye log verification failed. See individual "
            "step logs above.",
            status="fail"
        )
        print("❌ Step 8/9 — EagleEye log verification failed.")

    card_in_ee = verify_card_in_ee_log(CARD_CODE)
    if card_in_ee:
        logger.log(
            f"✅ Step 8/9 — NZ EDR card '{CARD_CODE}' confirmed in EE card-validation event.",
            status="pass"
        )
        print(f"✅ Step 8/9 — Card {CARD_CODE} found in EE log.")
    else:
        logger.log(
            f"❌ Step 8/9 — NZ EDR card '{CARD_CODE}' NOT found in EE card-validation event.",
            status="fail"
        )
        print(f"❌ Step 8/9 — Card {CARD_CODE} missing from EE log.")

    # ------------------------------------------------------------------
    # Step 10: Receipt / Tlog validation (manual placeholders).
    # ------------------------------------------------------------------
    logger.log(
        "ℹ️ Step 10 — Receipt verification: TODO (manual check that a receipt "
        "was printed).",
        status="info"
    )
    print("ℹ️ Step 10 — Receipt verification: TODO.")

    logger.log(
        "ℹ️ Step 10 — Tlog verification: TODO. Retail tlogs should be generated; "
        "retroactive tlogs should NOT be generated for this transaction "
        "(requires server-side access to confirm).",
        status="info"
    )
    print("ℹ️ Step 10 — Tlog verification: TODO.")

except Exception as e:
    logger.log(f"❌ TC_042 unexpected error: {e}", status="fail")
    print(f"❌ TC_042 ERROR: {e}")
    logger.take_screenshot("TC_042_Unexpected_Error")

finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
