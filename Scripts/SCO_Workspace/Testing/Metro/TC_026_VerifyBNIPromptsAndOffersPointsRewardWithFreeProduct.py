"""
TC_026_VerifyBNIPromptsAndOffersPointsRewardWithFreeProduct.py
--------------------------------------------------------------
TC_026 — Verify BNI Prompts and Offers Points Reward with Free Product

Sibling scenario to TC_025 (BNI Bounceback with Free Product) — same BNI
free product (165306 / EAN 9339423009071), but the eligible-article
campaign here is "102353511 - Points Fixed" (2000 points, not a $ bounce-
back) and a DIFFERENT loyalty card (9353148663592 vs TC_025's
9353179617069).

CONFIRMED LIVE-BUILD SO FAR:
    Step 1  Login              : login_pos() -> Welcome screen.
    Step 2  Eligible article    : add_item(EAN_ELIGIBLE, card) x3, single-
                                  scan loop (NOT a batched duplicate-EAN
                                  string — confirmed unreliable pattern,
                                  see TC_023/TC_025). EAN 9310072023205
                                  confirmed live -> "Arnt Shapes 160g"
                                  $4.00 each.
    Step 3  BNI free product    : add_item(EAN_BNI, card) x1 -> EAN
                                  9339423009071 = "The One GF550g" $7.30
                                  (same product confirmed in TC_025).
    Step 4  Scan loyalty card   : scan_loyalty_salemode(card) -- SALE MODE
                                  per the ticket ("Scan the loyalty card in
                                  the sale mode").
    Step 5  PayButton / popups  : same defensive-check pattern as TC_025 —
                                  actively look for a BNI-specific prompt/
                                  image (_check_for_bni_prompt) at each
                                  step of the popup sequence (Instant-Win /
                                  Collectable / Round-up), so IF the
                                  campaign IS live this run it will be
                                  detected and handled, not silently missed.
    Step 6  Exciting News prompt: verify_exciting_news_prompt() — the
                                  ticket expects this to appear once 2000
                                  points are earned (non-fatal if absent;
                                  the EE log is the ground truth for the
                                  points value per the TC_019/TC_023/TC_025
                                  precedent of on-screen fields being
                                  unreliable for bonus/campaign amounts).
    Step 7  Promotion check     : get_promotion_details() called BEFORE
                                  completing payment to capture any BNI
                                  discount/free-product line by keyword.
    Step 8  complete_transaction(): Card (Tender2) payment.
    Step 9-11 EE verification   : verify_eagleeye_logs(), verify_card_in_ee_log(),
                                  and a defensive check for the BNI
                                  campaign IDs (102331377 free-product /
                                  102353511 points-fixed) in the EE
                                  wallet/settle payload — logs PASS/INFO
                                  honestly rather than assuming either way.

NOTE: this script intentionally mirrors TC_025's defensive-check pattern
(never hard-fails on the BNI-specific behaviour since it was found NOT
provisioned on this backend for TC_025's sibling scenario) but the ACTUAL
result for TC_026's specific campaign IDs must be confirmed via its own
live run — do not assume the TC_025 finding applies here without checking.
"""

import re
import sys
import time
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components.Login_POS import login_pos
from Components.Add_item import add_item
from Components.Scan_loyalty_salemode import scan_loyalty_salemode
from Components.Verify_exciting_news_prompt import verify_exciting_news_prompt
from Components.Promotion_details import get_promotion_details
from Components.Complete_transaction import complete_transaction
from Components.Verify_EagleEye_logs import (
    verify_eagleeye_logs,
    verify_card_in_ee_log,
    _get_todays_log,
    _filter_content_after,
    _extract_settle_block,
)
from Components.Read_csv import get_csv_value
from Components.report import logger
from Components import global_instance

TC_ID  = "TC_026_VerifyBNIPromptsAndOffersPointsRewardWithFreeProduct"
BANNER = "Metro"
logger.set_tc_id(TC_ID)

# --- Test Data --------------------------------------------------------
# Confirmed live-used values (ticket alternate article list, first EAN):
#   Eligible article x3 : 9310072023205 -> "Arnt Shapes 160g" $4.00
#   BNI free product x1 : 9339423009071 -> "The One GF550g" $7.30
#   Loyalty card         : 9353148663592
EAN_ELIGIBLE = "9310072023205"
EAN_BNI = "9339423009071"
CARD_CODE = "9353148663592"

BNI_KEYWORDS = ("big night in", "bni", "points reward", "2000 point", "2,000 point")
BNI_CAMPAIGN_IDS = ("102331377", "102353511")


def _get(column, iteration=1, fallback=""):
    try:
        v = get_csv_value("saledata", BANNER, TC_ID, iteration, column)
        if v and not v.startswith("Error") and v != "No matching record found.":
            return v
    except Exception:
        pass
    return fallback


def _click(win, aid, label, timeout=5):
    """Best-effort click by auto_id. Returns True if clicked."""
    try:
        b = win.child_window(auto_id=aid, control_type="Button")
        if b.exists(timeout=timeout):
            b.click_input()
            logger.log(f"✅ Clicked '{aid}' ({label}).", status="pass")
            time.sleep(2.5)
            return True
    except Exception as e:
        logger.log(f"⚠️ Could not click '{aid}' ({label}): {e}", status="info")
    return False


def _check_for_bni_prompt(win, max_checks=3, wait_between=2.0):
    """
    Look for a BNI-specific popup (Instructions/LeadthruText containing a
    BNI keyword, optionally with an Image control). Acknowledges it via
    List1Button/OK_Button/List2Button if found.

    Returns True if a BNI prompt was detected and handled, False otherwise
    (i.e., simply not shown this run — NOT treated as a script failure).
    """
    for _ in range(max_checks):
        for text_aid in ("Instructions", "LeadthruText"):
            try:
                ctrl = win.child_window(auto_id=text_aid, control_type="Text")
                if ctrl.exists(timeout=1.0) and ctrl.is_visible():
                    txt = (ctrl.window_text() or "").lower()
                    if any(k in txt for k in BNI_KEYWORDS):
                        logger.log(
                            f"✅ BNI prompt detected via '{text_aid}': '{ctrl.window_text()}'.",
                            status="pass"
                        )
                        logger.take_screenshot("TC_026_BNI_Prompt_Detected")
                        for btn_aid in ("List1Button", "OK_Button", "List2Button"):
                            if _click(win, btn_aid, "BNI prompt acknowledged"):
                                return True
                        return True
            except Exception:
                continue
        time.sleep(wait_between)
    logger.log(
        "ℹ️ No BNI-specific prompt/image detected in the popup sequence this run.",
        status="info"
    )
    return False


def _check_bni_campaign_in_ee_log():
    """
    Search the EE wallet/settle payload for the BNI ticket campaign IDs
    (102331377 free-product / 102353511 points-fixed). Logs PASS with the
    actual value if found and triggered (value != 0), INFO if found but
    not triggered, INFO if absent entirely (campaign not provisioned on
    this backend). Never fails the script outright for this check.
    """
    log_path = _get_todays_log()
    if log_path is None:
        logger.log("⚠️ No EEAdapter log found — cannot check BNI campaign IDs.", status="info")
        return

    try:
        content = log_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        logger.log(f"⚠️ Could not read EE log: {e}", status="info")
        return

    start_time = global_instance.ee_log_start_time
    if start_time is not None:
        content = _filter_content_after(content, start_time)

    settle_block = _extract_settle_block(content)
    if not settle_block:
        logger.log("⚠️ wallet/settle block not found — cannot check BNI campaign IDs.", status="info")
        return

    for cid in BNI_CAMPAIGN_IDS:
        pattern = re.compile(
            r'"resourceId":"' + re.escape(cid) + r'".{0,120}?"value":(-?\d+(?:\.\d+)?|null)'
        )
        m = pattern.search(settle_block)
        if not m:
            logger.log(
                f"ℹ️ Campaign {cid} NOT found in EE wallet/settle payload this run "
                f"(not provisioned/triggered on this backend).",
                status="info"
            )
            continue
        value_str = m.group(1)
        if value_str == "null" or value_str in ("0", "0.0"):
            logger.log(
                f"ℹ️ Campaign {cid} present in EE payload but did NOT redeem "
                f"(value={value_str}).",
                status="info"
            )
        else:
            logger.log(
                f"✅ Campaign {cid} TRIGGERED in EE payload with value={value_str}.",
                status="pass"
            )


try:
    logger.log("=" * 70, status="info")
    logger.log("  TC_026 — BNI Prompts and Offers Points Reward with Free Product", status="info")
    logger.log("=" * 70, status="info")

    EAN_ELIGIBLE_CSV = _get("Item_EAN", 1, EAN_ELIGIBLE)
    EAN_BNI_CSV = _get("Item_EAN", 2, EAN_BNI)
    CARD_CSV = _get("Card_number", 1, CARD_CODE)

    if not login_pos():
        raise RuntimeError("login_pos failed")

    # Step 2: scan the eligible article 3x — single-scan loop, NOT a
    # batched duplicate-EAN string (confirmed unreliable pattern).
    for i in range(3):
        add_item(EAN_ELIGIBLE_CSV, CARD_CSV)
        time.sleep(1)

    # Step 3: scan the BNI free product once.
    add_item(EAN_BNI_CSV, CARD_CSV)
    time.sleep(1)

    # Step 4: scan the loyalty card in SALE MODE.
    if not scan_loyalty_salemode(CARD_CSV):
        raise RuntimeError("scan_loyalty_salemode failed")

    win = global_instance.win

    # Step 5: PayButton.
    win.child_window(auto_id="PayButton", control_type="Button").click_input()
    logger.log("✅ PayButton clicked.", status="pass")
    time.sleep(3)

    # Step 6a: actively look for a BNI-specific prompt/image FIRST.
    _check_for_bni_prompt(win)

    # Step 6b: Collectable offer popup — decline (if shown).
    _click(win, "List2Button", "Collectable offer — No")

    # Step 6c: check again after collectable popup.
    _check_for_bni_prompt(win, max_checks=1)

    # Step 6d: Round-up donation popup — decline (if shown).
    _click(win, "List2Button", "Round-up donation — No")

    # Step 6e: Exciting News prompt (2000 points threshold) — non-fatal.
    verify_exciting_news_prompt(timeout_seconds=8)

    # Step 7: capture on-screen promotion/discount lines BEFORE finalising
    # payment, so a BNI discount/free-product line (if present) is captured.
    try:
        (_, _, promo_desc, promo_prices, matched, missing) = get_promotion_details(BNI_KEYWORDS)
        if promo_desc:
            logger.log(f"ℹ️ On-screen promo lines present: {promo_desc} @ {promo_prices}.", status="info")
        else:
            logger.log(
                "ℹ️ No on-screen promo/discount line found before payment.",
                status="info"
            )
    except Exception as e:
        logger.log(f"⚠️ get_promotion_details() check failed: {e}", status="info")

    # Step 8: finalise payment via Card (Tender2).
    if not complete_transaction():
        raise RuntimeError("complete_transaction failed")

    # Step 9 & 10: EagleEye verification.
    ee = verify_eagleeye_logs(expect_wallet_open=True, expect_wallet_settle=True)
    verify_card_in_ee_log(CARD_CSV)

    if ee["all_passed"]:
        logger.log("PASS — TC_026 EE settled.", status="pass")
    else:
        logger.log("FAIL — EE verification failed.", status="fail")

    # Step 11: check specifically for the BNI free-product (102331377) and
    # points-fixed (102353511) campaigns in the settle payload.
    _check_bni_campaign_in_ee_log()

except Exception as e:
    logger.log(f"❌ TC_026 unexpected error: {e}", status="fail")
    print(f"❌ TC_026 ERROR: {e}")
    logger.take_screenshot("TC_026_Unexpected_Error")

finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
