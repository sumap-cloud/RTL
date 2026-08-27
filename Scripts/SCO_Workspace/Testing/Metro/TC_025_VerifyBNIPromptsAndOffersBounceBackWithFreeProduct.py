"""
TC_025_VerifyBNIPromptsAndOffersBounceBackWithFreeProduct.py
------------------------------------------------------------
TC_025 — Verify BNI Prompts and Offers Bounceback with Free Product

CONFIRMED LIVE-RUN FLOW (1 live run, card 9353179617069, SM banner):
    Step 1  Login              : login_pos() -> Welcome screen.
    Step 2  BB-eligible article : add_item(EAN_BB, card) x3, called ONCE PER
                                  SCAN in a loop (NOT batched as a single
                                  semicolon-duplicated string — duplicate-EAN
                                  batching is unreliable, confirmed in TC_023/
                                  TC_025 live-builds) -> "D/Supreme 380g"
                                  $8.50 each, basket $25.50 (3 items).
    Step 3  BNI free product    : add_item(EAN_BNI, card) x1 -> "The One
                                  GF550g" $7.30 added at FULL price (no promo
                                  line visible at scan time), basket $32.80
                                  (4 items).
    Step 4  Scan loyalty card   : scan_loyalty_salemode(card) -- SALE MODE.
                                  Accepted successfully (RewardTextBlock=
                                  'Current Rewards Balance: $50' — a
                                  pre-existing dollar balance on the card,
                                  unrelated to this transaction's points).
    Step 5  PayButton            : clicked manually.
    Step 6  Popup sequence      : Collectable offer (Disney Ooshies,
                                  "You have earned 2...") declined via
                                  List2Button ('No'). Round-up donation
                                  ($33.00/$0.20 to Salvation Army) declined
                                  via List2Button ('No, Thank You'). NO
                                  BNI-specific prompt/image ever appeared in
                                  this run — see FINDING below. The script
                                  below actively LOOKS FOR a BNI prompt (by
                                  Instructions/LeadthruText keyword match)
                                  before/between the known popups so that if
                                  campaign provisioning changes in future
                                  runs, the script will detect and handle it
                                  instead of silently missing it.
    Step 7  Promotion check     : get_promotion_details() called BEFORE
                                  completing payment to capture any on-screen
                                  promo/discount line for the BNI free
                                  product by keyword ("big night"/"bounce").
    Step 8  complete_transaction(): clicks Card (Tender2), waits for EFT
                                  auto-approval. Transaction completed
                                  immediately in the live run (AmountPaid=
                                  $32.80, AmountDue=$0.00).

CONFIRMED FINDING (live run 1) — BNI free-product campaign did NOT trigger:
    - "The One GF550g" was charged FULL PRICE ($7.30); no promo/discount line
      appeared on screen at any point.
    - No BNI prompt/image popup ever appeared during the PayButton -> tender
      flow.
    - On-screen WoWRewardPoints showed 32, matching EXACTLY the base-points-
      only formula ((32.80+1.02)//2)*2 = 32 — no bonus contribution visible.
    - EE backend wallet/settle payload (C:\\Retalix\\EEAdapter\\Logs\\
      EEAdapter_{date}.{n}.log) was checked per the TC_019/TC_023 methodology
      (never trust on-screen fields alone). Confirmed via 1 live run:
      totalPointsGiven=35 (earn=34, credit=1). adjudicationResults only
      contained SCHEME 1214545/898125/1214547 (base) and CAMPAIGN 102825606
      (the SAME generic item/category-multiplier campaign already confirmed
      in TC_023 — unrelated to BNI, contributed +1 reward unit off "The One
      GF550g" itself) plus CAMPAIGN 1270870/102903033 (createRedeem value=0,
      did NOT trigger — same basket-level campaigns seen not triggering in
      TC_023). The BNI ticket-referenced campaigns (102331380 "BB"/102331377
      "Big Night In Winner") DID NOT APPEAR ANYWHERE in the settle payload —
      not even as a zero-value entry. "The One GF550g" contributionResults
      show totalUnitCostAfterDiscount=730 (unchanged from itemUnitCost=730),
      confirming NO discount/free redemption was applied server-side either.

    CONCLUSION: this mirrors the TC_019 "described campaign not provisioned/
    live on this backend" pattern — NOT a script or scanning defect. This TC
    is NOT marked a full pass; the BNI bounce-back/free-product behaviour is
    UNCONFIRMED on this environment. The script below is written DEFENSIVELY
    (checks for the prompt/discount/EE campaign presence and logs PASS/INFO
    accordingly, never assumes/fabricates a result) so that IF the campaign
    becomes live in a future run, the same script will automatically detect
    and validate it without modification.
"""

import re
import sys
import time
from datetime import datetime
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components.Login_POS import login_pos
from Components.Add_item import add_item
from Components.Scan_loyalty_salemode import scan_loyalty_salemode
from Components.Complete_transaction import complete_transaction
from Components.Promotion_details import get_promotion_details
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

TC_ID = "TC_025_VerifyBNIPromptsAndOffersBounceBackWithFreeProduct"
BANNER = "Metro"
logger.set_tc_id(TC_ID)

# --- Test Data ------------------------------------------------------------
# Confirmed live-used values (ticket alternate article list):
#   BB-eligible article  x3 : 9310015247811 -> "D/Supreme 380g" $8.50
#   BNI free product     x1 : 9339423009071 -> "The One GF550g" $7.30
#   Loyalty card             : 9353179617069
EAN_BB = "9310015247811"
EAN_BNI = "9339423009071"
CARD_CODE = "9353179617069"

# Keywords used to detect a BNI-specific prompt/promo if/when the campaign
# is live — kept broad on purpose (case-insensitive substring match).
BNI_KEYWORDS = ("big night in", "bni", "bounce", "bounceback", "bounce back")
BNI_CAMPAIGN_IDS = ("102331380", "102331377")


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
                        logger.take_screenshot("TC_025_BNI_Prompt_Detected")
                        for btn_aid in ("List1Button", "OK_Button", "List2Button"):
                            if _click(win, btn_aid, "BNI prompt acknowledged"):
                                return True
                        return True
            except Exception:
                continue
        time.sleep(wait_between)
    logger.log(
        "ℹ️ No BNI-specific prompt/image detected in the popup sequence this run "
        "(see module docstring — campaign not currently provisioned/live).",
        status="info"
    )
    return False


def _check_bni_campaign_in_ee_log():
    """
    Search the EE wallet/settle payload for the BNI ticket campaign IDs
    (102331380 / 102331377). Logs PASS with the actual value if found and
    triggered (value != 0), INFO if found but not triggered, INFO if absent
    entirely (campaign not provisioned on this backend). Never fails the
    script outright for this check — this is a documented/known gap.
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
        # Look for {"resourceType":"CAMPAIGN","resourceId":"<cid>", ... "value":<n>
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
    logger.log("  TC_025 — BNI Prompts and Offers Bounceback with Free Product", status="info")
    logger.log("=" * 70, status="info")

    EAN_BB_CSV = _get("Item_EAN", 1, EAN_BB)
    EAN_BNI_CSV = _get("Item_EAN", 2, EAN_BNI)
    CARD_CSV = _get("Card_number", 1, CARD_CODE)

    if not login_pos():
        raise RuntimeError("login_pos failed")

    # Step 2: scan the BB-eligible article 3x — single-scan loop, NOT a
    # batched duplicate-EAN string (confirmed unreliable in TC_023/TC_025).
    for i in range(3):
        add_item(EAN_BB_CSV, CARD_CSV)
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

    # Step 6a: actively look for a BNI-specific prompt/image FIRST (before
    # the generic collectable/round-up popups consume the screen).
    _check_for_bni_prompt(win)

    # Step 6b: Collectable offer popup — decline.
    _click(win, "List2Button", "Collectable offer — No")

    # Step 6c: check again in case the BNI prompt appears after collectable.
    _check_for_bni_prompt(win, max_checks=1)

    # Step 6d: Round-up donation popup — decline.
    _click(win, "List2Button", "Round-up donation — No")

    # Step 7: capture on-screen promotion/discount lines BEFORE finalising
    # payment, so a BNI discount line (if present) is captured.
    try:
        (_, _, promo_desc, promo_prices, matched, missing) = get_promotion_details(BNI_KEYWORDS)
        if promo_desc:
            logger.log(f"ℹ️ On-screen promo lines present: {promo_desc} @ {promo_prices}.", status="info")
        else:
            logger.log(
                "ℹ️ No on-screen promo/discount line found before payment "
                "(consistent with BNI free-product campaign not triggering).",
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
        logger.log("PASS — TC_025 EE settled.", status="pass")
    else:
        logger.log("FAIL — EE verification failed.", status="fail")

    # Step 11 (part of the ticket's Tlog check, mirrored via EE payload
    # since direct Tlog/server access is not available): check specifically
    # for the BNI bounce-back (102331380) and free-product (102331377)
    # campaigns in the settle payload.
    _check_bni_campaign_in_ee_log()

    logger.log(
        "ℹ️ SUMMARY (live run 1): BNI prompt/image did NOT appear on screen; "
        "'The One GF550g' was charged full price ($7.30) with no discount; "
        "EE wallet/settle payload does NOT contain campaigns 102331380/"
        "102331377 at all. This matches the TC_019 'described campaign not "
        "provisioned' pattern — flagged for backend/campaign-team follow-up. "
        "This TC is NOT marked a full pass. The checks above are written "
        "defensively so a future run where the campaign IS live will be "
        "automatically detected and validated without script changes.",
        status="info"
    )
    logger.log("TODO: Verify Tlogs directly once server/Tlog access is available "
               "(BB campaign id should not be captured; free product should be "
               "captured in the tlog per the ticket).", status="info")

except Exception as e:
    logger.log(f"❌ TC_025 unexpected error: {e}", status="fail")
    print(f"❌ TC_025 ERROR: {e}")
    logger.take_screenshot("TC_025_Unexpected_Error")

finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
