"""
TC_038_VerifyOpenOffersForRegisteredCard.py
-------------------------------------------
TC_038 — Verify Open Offers For Registered Card

LIVE-BUILD HISTORY (this script was built and verified incrementally
against a real physical NCR SCO terminal — see session Temp/tc038_step*.py
scripts for the step-by-step live verification of every piece below):

  1. Scan 5 iterations of CSV data (Bond, Coke, BOG, Kitkat, Exclusion GC).
  2. Scan loyalty card at the tender prompt (after PayButton).
  3. An UNEXPECTED Choice Offer popup ("You have 2 discounts to select
     from") appears after the loyalty scan on this data set — this is a
     deviation from the manual test case's step 6 ("no redemption should
     be displayed"). Per user decision, this is declined
     (redeem_choice_offer("") -> SkipChoiceOfferPrompt) and logged as a
     non-fatal deviation, not a hard failure.
  4. Promotion assertions are built from real live-verified data:
       - Bond:   10% off eligible Bond items (Campaign 1555076)
       - Coke:   Buy 2 Coke items for $1 each, limit 5 (Offer 1261037)
       - BOG:    Buy Epson NX230 -> free Epson ink; the Wahu Dive Pk BOG
                 item confirmed to itself receive a $-item-price discount
                 (Offer 1261715)
       - Kitkat: Buy 5 KitKat get $5 off (Campaign 1260707)
     NOTE: CartReceipt is a WPF VIRTUALIZING list — only currently
     on-screen rows exist in the UIA tree at any moment. Scrolling the
     list to the very top (wrapper.scroll("up","page") x15) was confirmed
     live to bring ALL rows (items + promo lines) into the tree at once,
     so reads AFTER a scroll-to-top are reliable. This script performs
     that scroll before reading the cart.
  5. Complete via CARD tender. NOTE: Complete_transaction.py's shared
     _CARD_BUTTON_AIDS incorrectly assumes 'Tender2'=Card; live dumps
     this session consistently showed Tender2='Cash' and Tender3='Card'.
     Per user decision (leave shared component alone), this script clicks
     Tender3 directly instead of using complete_transaction().
  6. Verify EagleEye logs: card validation / wallet open / wallet settle,
     plus real per-offer verification using CAMPAIGN IDs (confirmed live
     in the wallet/settle JSON payload — description strings do NOT
     appear in the EE log, only SKU + resourceId/campaign ID), which
     match exactly the campaign IDs given in the manual test case.

KNOWN LIVE DATA GAP (documented, not hidden):
  EAN 9314020603921 (2nd BOG-eligible article) failed to register in the
  basket on 2 separate live attempts even with 3 scan retries + increasing
  backoff — this appears to be a genuine EAN/item-master issue rather than
  a timing glitch. Per user decision, the BOG offer is validated with only
  1 of its 2 eligible articles (Wahu Dive Pk) since the offer already
  triggers correctly with 1 unit live.
"""
import sys
import time
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components.Login_POS import login_pos
from Components.Add_item import add_item
from Components.Scan_loyalty_tenderprompt import scan_loyalty_tenderprompt
from Components.Redeem_choice_offer import redeem_choice_offer
from Components.Verify_EagleEye_logs import verify_eagleeye_logs, verify_card_in_ee_log
from Components.Read_csv import get_csv_value
from Components.report import logger
from Components import global_instance

TC_ID  = "TC_038_VerifyOpenOffersForRegisteredCard"
BANNER = "BigW"
logger.set_tc_id(TC_ID)

# Real campaign/offer IDs confirmed live in the EE wallet/settle payload —
# these match exactly what the manual test case specifies.
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
    Scroll CartReceipt to the top so ALL rows (items + promo lines) are
    present in the UIA tree (confirmed live: CartReceipt virtualizes rows
    outside the visible viewport). Returns a list of (description, price)
    tuples for every unique row found.
    """
    win = global_instance.win
    cart_list = win.child_window(auto_id="CartReceipt", control_type="List")
    wrapper = cart_list.wrapper_object()

    try:
        for _ in range(15):
            wrapper.scroll("up", "page")
            time.sleep(0.15)
    except Exception as e:
        print(f"⚠️ Scroll-to-top error (continuing anyway): {e}")

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
    logger.log("  TC_038 — Verify Open Offers For Registered Card", status="info")
    logger.log("=" * 70, status="info")

    CARD_CODE = _get("Card_number", 1, "9353186777909")

    # --- Step 1: Login ---
    if not login_pos():
        raise RuntimeError("login_pos failed")

    # --- Step 2: Scan all 5 iterations (Bond, Coke, BOG, Kitkat, Exclusion) ---
    for it in [1, 2, 3, 4, 5]:
        ean = _get("Item_EAN", it, "")
        if ean:
            print(f"--- Scanning iteration {it}: {ean} ---")
            add_item(ean, CARD_CODE)

    logger.log("✅ All CSV iterations scanned into basket.", status="pass")

    # --- Step 3: Scan loyalty card at the tender prompt ---
    if not scan_loyalty_tenderprompt(CARD_CODE):
        logger.log("⚠️ loyalty scan at tender prompt failed", status="info")
    else:
        logger.log(f"✅ Loyalty card '{CARD_CODE}' scanned at tender prompt.", status="pass")

    # --- Step 4: Handle unexpected Choice Offer popup (deviation) ---
    # Manual step 6 says "no redemption should be triggered" — but this
    # data set consistently triggers a Choice Offer popup after the
    # loyalty scan. Decline it (do not redeem) and log as a deviation,
    # not a hard failure, per user decision.
    win = global_instance.win
    try:
        choice_popup = win.child_window(auto_id="ContainerButtonList", control_type="List")
        if choice_popup.exists(timeout=3):
            logger.log(
                "⚠️ DEVIATION: Choice Offer popup appeared after loyalty scan "
                "(manual step 6 expects NO redemption to be displayed). "
                "Declining via 'No, save these discounts for later'.",
                status="info"
            )
            redeem_choice_offer("")
        else:
            logger.log(
                "✅ No Choice/Collectable/Instant-Win redemption popup appeared — "
                "matches manual step 6 expectation.",
                status="pass"
            )
    except Exception as e:
        logger.log(f"⚠️ Choice offer popup check error: {e}", status="info")

    # --- Step 5: Verify all 4 open offers triggered with correct prices ---
    # After loyalty card acceptance, the SCO performs a server-side promo
    # calculation that can take 10–30 s before promo lines appear in the
    # CartReceipt. Retry for up to 45 s before giving up.
    print("⏳ Waiting for promo lines to populate in CartReceipt (up to 45s)...")
    rows = []
    for _w in range(9):  # 9 × 5 s = 45 s max
        time.sleep(5)
        rows = _scroll_cart_to_top_and_get_all_rows()
        promo_rows_found = [(d, p) for d, p in rows if p.startswith("-$")]
        print(f"  [{(_w+1)*5}s] {len(rows)} total rows, {len(promo_rows_found)} promo rows")
        if promo_rows_found:
            print(f"✅ Promo lines appeared after ~{(_w+1)*5}s")
            break
    else:
        print("⚠️ No promo lines found after 45s — verifying anyway.")

    # Log the full cart for diagnostics
    print("\nFull cart contents (post scroll-to-top):")
    for desc, price in rows:
        print(f"  {price:>10}  {desc}")

    promo_rows_found = [(d, p) for d, p in rows if p.startswith("-$")]
    promo_prices_found = [p for _, p in promo_rows_found]
    print(f"\nPromo lines ({len(promo_rows_found)}): {promo_rows_found}")
    logger.log(f"ℹ️ Promo lines found in cart: {promo_rows_found}", status="info")

    # Verify by PRICE (description text is SCO-locale-specific — verified live
    # via campaign IDs in EE logs instead). Two promos share -$5.00 (Bond, Kitkat).
    _remaining_prices = list(promo_prices_found)
    checks = [
        ("Bond promo (-$5.00 expected)",   "-$5.00"),
        ("Coke promo (-$6.20 expected)",   "-$6.20"),
        ("BOG promo (-$3.75 expected)",    "-$3.75"),
        ("Kitkat promo (-$5.00 expected)", "-$5.00"),
    ]
    for label, expected_price in checks:
        if expected_price in _remaining_prices:
            _remaining_prices.remove(expected_price)
            logger.log(f"✅ {label}: found ({expected_price}).", status="pass")
            print(f"✅ {label}: found ({expected_price}).")
        else:
            logger.log(
                f"❌ {label}: {expected_price} not in promo prices {promo_prices_found}.",
                status="fail"
            )
            print(f"❌ {label}: {expected_price} not found. Promo prices: {promo_prices_found}")

    # --- Step 6: Complete transaction via Card tender ---
    # NOTE: Complete_transaction.py's shared Card-button auto_id list
    # ('Tender2') was confirmed live this session to be INCORRECT for this
    # screen configuration (Tender2='Cash', Tender3='Card' observed
    # consistently). Per user decision, click Tender3 directly here rather
    # than modify the shared component.
    win = global_instance.win  # refresh in case reference was updated during loyalty flow
    tender3 = win.child_window(auto_id="Tender3", control_type="Button")
    if tender3.exists(timeout=5):
        tender3.click_input()
        logger.log("✅ Card tender (Tender3) clicked.", status="pass")
        print("✅ Card tender (Tender3) clicked.")
    else:
        logger.log("❌ Tender3 (Card) button not found.", status="fail")
        logger.take_screenshot("TC_038_Tender3_Not_Found")

    time.sleep(5)

    # --- Step 7: Verify EagleEye logs ---
    from datetime import datetime, timedelta
    start_time = datetime.now() - timedelta(minutes=5)

    ee_result = verify_eagleeye_logs(
        expect_wallet_open=True, expect_wallet_settle=True, start_time=start_time
    )
    if ee_result["all_passed"]:
        logger.log(
            "✅ EE logs verified: card validation, wallet open, wallet settle all captured.",
            status="pass"
        )
    else:
        logger.log(f"❌ EE log verification incomplete: {ee_result}", status="fail")

    if verify_card_in_ee_log(CARD_CODE, start_time=start_time):
        logger.log(f"✅ Card '{CARD_CODE}' confirmed in EE log.", status="pass")
    else:
        logger.log(f"❌ Card '{CARD_CODE}' NOT found in EE log.", status="fail")

    # Verify campaign IDs directly in the settle payload (description
    # strings do not appear in the EE log — only SKU + resourceId/campaign
    # ID do, confirmed live).
    from Components.Verify_EagleEye_logs import _get_todays_log, _filter_content_after, _extract_settle_block
    log_path = _get_todays_log()
    if log_path:
        content = log_path.read_text(encoding="utf-8", errors="ignore")
        content = _filter_content_after(content, start_time)
        settle_block = _extract_settle_block(content) or ""
        for offer_name, campaign_id in EXPECTED_CAMPAIGN_IDS.items():
            marker = f'"resourceId":"{campaign_id}"'
            if marker in settle_block:
                logger.log(f"✅ {offer_name} campaign ({campaign_id}) found in EE settle payload.", status="pass")
            else:
                logger.log(f"❌ {offer_name} campaign ({campaign_id}) NOT found in EE settle payload.", status="fail")
    else:
        logger.log("❌ No EE log file found for campaign ID verification.", status="fail")

except Exception as e:
    print(f"\n❌ ERROR OCCURRED: {e}")
    import traceback
    traceback.print_exc()
    logger.log(f"❌ TC_038 unexpected error: {e}", status="fail")
    logger.take_screenshot("TC_038_Unexpected_Error")

finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
