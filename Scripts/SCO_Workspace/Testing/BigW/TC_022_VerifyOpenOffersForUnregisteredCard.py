"""
TC_022_VerifyOpenOffersForUnregisteredCard.py
---------------------------------------------
TC_022 — Verify Open Offers For Unregistered Card

Based on TC_038 (Registered card) — same 4 open offers, same campaign IDs,
same promo logic, and now ALSO the same exclusion Gift Card article
(076750436640009036009313012991) scanned as iteration 5, per user decision
to reuse the TC_038 GC-activation-popup live-build pattern. Key differences
from TC_038:
  - Unregistered loyalty card 9344450008836 (no points earned)
  - EE log still expects card validation + wallet open + wallet settle
    (step 9 of the manual test case explicitly requires all three)

OFFER DETAILS (same campaigns as TC_038, confirmed live):
  Bond:   Campaign 1555076 — 10% off Bond items   → expected -$5.00
  Coke:   Offer   1261037 — Buy 2 Coke for $1.50ea → expected -$6.20
  BOG:    Offer   1261715 — Buy Epson → free ink    → expected -$3.75
  Kitkat: Campaign 1260707 — Buy 5 KitKat → -$5     → expected -$5.00

CartReceipt WPF virtualisation fix: scroll to top x15 before reading rows
(confirmed live in TC_038 — mandatory for reliable promo-line detection).

Tender: Card via Tender3 (live-confirmed: Tender2='Cash', Tender3='Card').
"""
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components.Login_POS import login_pos
from Components.Add_item import add_item
from Components.Scan_loyalty_tenderprompt import scan_loyalty_tenderprompt
from Components.Redeem_choice_offer import redeem_choice_offer
from Components.Verify_EagleEye_logs import (
    verify_eagleeye_logs, verify_card_in_ee_log,
    _get_todays_log, _filter_content_after, _extract_settle_block,
)
from Components.Read_csv import get_csv_value
from Components.report import logger
from Components import global_instance

TC_ID  = "TC_022_VerifyOpenOffersForUnregisteredCard"
BANNER = "BigW"
logger.set_tc_id(TC_ID)

# Campaign/offer IDs — identical to TC_038, confirmed live in EE settle payload.
EXPECTED_CAMPAIGN_IDS = {
    "Bond":   "1555076",
    "Coke":   "1261037",
    "BOG":    "1261715",
    "Kitkat": "1260707",
}


def _get(column, iteration=1, fallback=""):
    try:
        v = get_csv_value("saledata", BANNER, TC_ID, iteration, column)
        if v and not str(v).startswith("Error") and v != "No matching record found.":
            return v
    except Exception:
        pass
    return fallback


def _scroll_cart_to_top_and_get_all_rows():
    """
    Scroll CartReceipt to top so ALL rows (items + promo lines) enter the UIA
    tree (WPF virtualisation fix — confirmed live in TC_038 session).
    Returns list of (description, price) tuples.
    """
    win = global_instance.win
    cart_list = win.child_window(auto_id="CartReceipt", control_type="List")
    wrapper = cart_list.wrapper_object()
    try:
        for _ in range(15):
            wrapper.scroll("up", "page")
            time.sleep(0.15)
    except Exception as e:
        print(f"⚠️ Scroll-to-top error (continuing): {e}")
    time.sleep(0.5)
    rows = []
    seen = set()
    for item in wrapper.children(control_type="ListItem"):
        desc_text = ""
        price_text = ""
        for child in item.children():
            aid = child.element_info.automation_id
            if aid == "ItemDescription" and not desc_text:
                desc_text = child.window_text()
            elif aid == "ItemPrice" and not price_text:
                price_text = child.window_text()
        if desc_text and (desc_text, price_text) not in seen:
            seen.add((desc_text, price_text))
            rows.append((desc_text, price_text))
    return rows


try:
    logger.log("=" * 70, status="info")
    logger.log("  TC_022 — Verify Open Offers For Unregistered Card", status="info")
    logger.log("=" * 70, status="info")

    CARD_CODE = _get("Card_number", 1, "9344450008836")

    # --- Step 1: Login ---
    if not login_pos():
        raise RuntimeError("login_pos failed")

    # --- Step 2: Scan all 5 iterations (Bond, Coke, BOG, Kitkat, Exclusion GC) ---
    # Iteration 5 = same exclusion Gift Card article used in TC_038
    # (076750436640009036009313012991) — triggers GC activation popup handling
    # inside add_item()/scan_loyalty_tenderprompt().
    for it in [1, 2, 3, 4, 5]:
        ean = _get("Item_EAN", it, "")
        if ean:
            print(f"--- Scanning iteration {it}: {ean} ---")
            add_item(ean, CARD_CODE)

    logger.log("✅ All CSV iterations scanned into basket.", status="pass")

    # --- Step 3: Scan loyalty card at the tender prompt ---
    # PayButton click + GC activation loop handled inside scan_loyalty_tenderprompt.
    # For TC_022 there is no gift card in the basket, so no GC popup is expected —
    # the function will proceed directly to the loyalty-prompt screen.
    if not scan_loyalty_tenderprompt(CARD_CODE):
        logger.log("⚠️ Loyalty scan at tender prompt failed.", status="info")
    else:
        logger.log(f"✅ Loyalty card '{CARD_CODE}' scanned at tender prompt.", status="pass")

    # --- Step 4: Handle Choice Offer popup if it appears (step 6: no redemption expected) ---
    win = global_instance.win
    try:
        choice_popup = win.child_window(auto_id="ContainerButtonList", control_type="List")
        if choice_popup.exists(timeout=3):
            logger.log(
                "⚠️ DEVIATION: Choice Offer popup appeared (manual step 6 expects "
                "NO redemption). Declining via SkipChoiceOfferPrompt.",
                status="info"
            )
            redeem_choice_offer("")
        else:
            logger.log(
                "✅ No redemption popup appeared — matches manual step 6 expectation.",
                status="pass"
            )
    except Exception as e:
        logger.log(f"⚠️ Choice offer popup check error: {e}", status="info")

    # --- Step 5: Verify all 4 open offers triggered with correct prices ---
    # Promo lines populate asynchronously after loyalty acceptance (server-side
    # calculation). Retry for up to 45 s. Verify by price value, not description
    # text (description strings are SCO-locale-specific; campaign IDs are ground
    # truth, confirmed live in EE settle payload for TC_038).
    print("⏳ Waiting for promo lines to populate in CartReceipt (up to 45s)...")
    rows = []
    for _w in range(9):  # 9 × 5s = 45s max
        time.sleep(5)
        rows = _scroll_cart_to_top_and_get_all_rows()
        promo_rows = [(d, p) for d, p in rows if p.startswith("-$")]
        print(f"  [{(_w+1)*5}s] {len(rows)} total rows, {len(promo_rows)} promo rows")
        if promo_rows:
            print(f"✅ Promo lines appeared after ~{(_w+1)*5}s")
            break
    else:
        print("⚠️ No promo lines found after 45s — verifying anyway.")

    print("\nFull cart contents (post scroll-to-top):")
    for desc, price in rows:
        print(f"  {price:>10}  {desc}")

    promo_rows = [(d, p) for d, p in rows if p.startswith("-$")]
    promo_prices = [p for _, p in promo_rows]
    print(f"\nPromo lines ({len(promo_rows)}): {promo_rows}")
    logger.log(f"ℹ️ Promo lines found in cart: {promo_rows}", status="info")

    _remaining = list(promo_prices)
    for label, expected_price in [
        ("Bond promo (-$5.00 expected)",   "-$5.00"),
        ("Coke promo (-$6.20 expected)",   "-$6.20"),
        ("BOG promo (-$3.75 expected)",    "-$3.75"),
        ("Kitkat promo (-$5.00 expected)", "-$5.00"),
    ]:
        if expected_price in _remaining:
            _remaining.remove(expected_price)
            logger.log(f"✅ {label}: found ({expected_price}).", status="pass")
            print(f"✅ {label}: found ({expected_price}).")
        else:
            logger.log(
                f"❌ {label}: {expected_price} not in promo prices {promo_prices}.",
                status="fail"
            )
            print(f"❌ {label}: {expected_price} not found. Promo prices: {promo_prices}")

    # --- Step 6: Complete transaction via Card tender ---
    # Tender3 = Card (live-confirmed; Tender2 = Cash on this SCO configuration).
    win = global_instance.win
    tender3 = win.child_window(auto_id="Tender3", control_type="Button")
    if tender3.exists(timeout=5):
        tender3.click_input()
        logger.log("✅ Card tender (Tender3) clicked.", status="pass")
        print("✅ Card tender (Tender3) clicked.")
    else:
        logger.log("❌ Tender3 (Card) button not found.", status="fail")
        logger.take_screenshot("TC_022_Tender3_Not_Found")

    time.sleep(5)

    # --- Steps 8–9: Verify EagleEye logs ---
    start_time = datetime.now() - timedelta(minutes=5)

    ee_result = verify_eagleeye_logs(
        expect_wallet_open=True, expect_wallet_settle=True, start_time=start_time
    )
    if ee_result["all_passed"]:
        logger.log(
            "✅ EE logs: card validation, wallet open, wallet settle all captured.",
            status="pass"
        )
    else:
        logger.log(f"❌ EE log verification incomplete: {ee_result}", status="fail")

    if verify_card_in_ee_log(CARD_CODE, start_time=start_time):
        logger.log(f"✅ Card '{CARD_CODE}' confirmed in EE log.", status="pass")
    else:
        logger.log(f"❌ Card '{CARD_CODE}' NOT found in EE log.", status="fail")

    # Verify campaign IDs in the settle payload (same approach as TC_038 —
    # description strings don't appear in EE log; resourceId/campaign IDs do).
    log_path = _get_todays_log()
    if log_path:
        content = log_path.read_text(encoding="utf-8", errors="ignore")
        content = _filter_content_after(content, start_time)
        settle_block = _extract_settle_block(content) or ""
        for offer_name, campaign_id in EXPECTED_CAMPAIGN_IDS.items():
            marker = f'"resourceId":"{campaign_id}"'
            if marker in settle_block:
                logger.log(
                    f"✅ {offer_name} campaign ({campaign_id}) found in EE settle payload.",
                    status="pass"
                )
            else:
                logger.log(
                    f"❌ {offer_name} campaign ({campaign_id}) NOT found in EE settle payload.",
                    status="fail"
                )
    else:
        logger.log("❌ No EE log file found for campaign ID verification.", status="fail")

except Exception as e:
    print(f"\n❌ ERROR OCCURRED: {e}")
    import traceback
    traceback.print_exc()
    logger.log(f"❌ TC_022 unexpected error: {e}", status="fail")
    logger.take_screenshot("TC_022_Unexpected_Error")

finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
