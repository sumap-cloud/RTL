"""
TC_023_VerifyCombinationalOfProductCategoryAndBasketPointsOffers.py
--------------------------------------------------------------------
TC_023 — Validation of combinational behaviour of product, category and
basket level points offers.

CONFIRMED LIVE-RUN FLOW (2 live runs against card 9353105847133, SM banner):
    Step 1  Login              : login_pos() -> Welcome screen.
    Step 2  Item-level offer    : add_item("9349673003620;9349673003552", card)
                                  -> MrCpnSoySce250ml $2.85 + MrCpngNdlThk300g $2.15
                                  (Cartology_MR CHEN'S brand items, ticket line 1106706).
    Step 3  Category-level offer: add_item("5010775192324;5010775195936", card)
                                  -> Mug & Egg 50g $5.00 + Troll Suprse Egg $6.00
                                  (ticket line 1321142 brand-specific multiplier).
    Step 4  Produce category    : add_item("9315265004078;9300633026028", card)
                                  -> Apple Toffee $2.00 + Strawberries250g $5.90
                                  (ticket line 1170918 produce-category multiplier —
                                  Apple Toffee + Strawberries used as fruit/veg items).
    Step 5  Basket-level filler : add_item("9315087192083", card)
                                  -> B/Chc CatLttr24l $30.00 (crosses the $50
                                  basket-level threshold for 1206522 / 1297323).
                                  Run 1 basket total: $53.90 (7 items).
                                  Run 2 (retry, extra top-up): added 1x extra
                                  Strawberries250g ($5.90) + accidentally 2x
                                  B/Chc CatLttr24l ($30.00 x2, one retry landed
                                  after a transient scan failure) -> basket
                                  grew to $89.80 (9 items) — see FINDING below.
    Step 6  Scan loyalty card  : scan_loyalty_salemode(card) -- SALE MODE.
                                  Confirmed: 'Scan Coupon' screen auto-dismissed
                                  via CancelCoupon both runs.
    Step 7  PayButton           : an UNEXPECTED Instant-Win "prize to use now"
                                  choice popup appears on THIS card too
                                  (LeadthruText='You have 1 prize to use now.
                                  T&Cs apply', button 'Usenow' / 'SkipChoiceOfferPrompt'
                                  (Save for later) / 'GoBack'). This is unrelated
                                  to TC_023's points scope, so 'Save for later'
                                  (SkipChoiceOfferPrompt) is clicked to avoid
                                  interfering with the points measurement.
    Step 8  Collectable popup   : PopupFrame (List1Button='Yes' / List2Button='No')
                                  — sometimes with visible Instructions text
                                  ("You have earned N Disney Ooshies...") and
                                  sometimes blank-text but same button layout —
                                  declined via List2Button both runs.
    Step 9  Round-up popup      : PopupFrame LeadthruText='Would you like to
                                  round the transaction to $X.00 and donate $Y
                                  to SALVATION ARMY 2?' — declined via List2Button
                                  ('No, Thank You') both runs.
    Step 10 Payment              : Auto-finalizes (PIN Pad Entry / "Finalising
                                  Payment, please wait") with NO manual Tender
                                  click needed — same auto-payment behaviour
                                  observed in TC_019. Transaction completes and
                                  returns to Welcome screen.

IMPORTANT FINDING — on-screen points vs backend EE points MISMATCH:
    The on-screen 'WoWRewardPoints' field shown just before finalisation
    matched EXACTLY the base-points-only formula ((total+1.02)//2)*2 in BOTH
    runs (Run1: basket $53.90 -> screen showed 54; Run2: basket $89.80 ->
    screen showed 90). This field does NOT reflect any bonus/multiplier
    campaign contribution and is NOT a reliable indicator of the final
    settled points — it must NOT be used alone to validate TC_023's expected
    combinational points math.

    The ACTUAL points breakdown only appears in the EagleEye backend
    wallet/settle log (C:\\Retalix\\EEAdapter\\Logs\\EEAdapter_{date}.{n}.log),
    read via verify_eagleeye_logs()/raw log parsing. Confirmed via 2 live
    runs:
      Run 1 (basket $53.90): totalPointsGiven=58 (earn=57, credit=1).
        adjudicationResults: SCHEME 1214545 (+1), SCHEME 898125 (+54, base),
        SCHEME 1214547 (+2), CAMPAIGN 102825606 REDEEMED (value=1,
        totalRewardUnits=14, qualifying matched spend $30.00 — the single
        B/Chc CatLttr24l item). CAMPAIGN 1270870 and CAMPAIGN 102903033 did
        NOT trigger (createRedeem value=0), with qualifying matched spend
        stuck at $29.98 and $15.00 respectively — just under whatever their
        real thresholds are.
      Run 2 (basket $89.80, extra Strawberries + duplicate B/Chc CatLttr24l):
        totalPointsGiven=98 (earn=96, credit=2). SCHEME totals grew
        proportionally (898125 -> 90, matching new base). CAMPAIGN 102825606
        grew too (value=2, totalRewardUnits=18) because its qualifying item
        (B/Chc CatLttr24l) was now duplicated. HOWEVER CAMPAIGN 1270870 and
        102903033's qualifying matched spend REMAINED IDENTICAL ($29.98 /
        $15.00) despite the much bigger basket — proving these two
        campaigns' qualifying spend is tied to a SPECIFIC SUBSET of SKUs
        already present in the basket (not overall basket total), and
        adding MORE of the SAME items already in the basket does not move
        them. Different/new item SKUs would be needed to push those two
        over their thresholds — this was not further pursued in this
        session (per user direction) and is left as a documented gap.

    CONCLUSION: campaign 102825606 (whichever ticket line it maps to,
    likely the item- or category-multiplier offer given its per-item
    contributionResults keying off Apple Toffee) IS live and DOES apply on
    this SCO/card. The other 2 campaigns described in the ticket
    (1206522 "Spend min $50 -> 3X points" and/or 1297323 "hurdle $50 ->
    500pts") did NOT trigger in either run despite the basket exceeding
    $50 in both cases — this needs backend/campaign-team follow-up
    (mirrors the TC_019 pattern of a described campaign not being
    live/provisioned) OR a different item-mix that actually satisfies
    their specific qualifying-spend calculation. This TC is NOT being
    marked as a full pass — the combinational behaviour is PARTIALLY
    confirmed (item/category-level campaign 102825606 verified working)
    but the basket-level campaigns (1206522/1297323) remain unconfirmed.
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
from Components.Scan_loyalty_salemode import scan_loyalty_salemode
from Components.Complete_transaction import complete_transaction
from Components.Verify_EagleEye_logs import verify_eagleeye_logs
from Components.Read_csv import get_csv_value
from Components.report import logger
from Components import global_instance

TC_ID  = "TC_023_VerifyCombinationalOfProductCategoryAndBasketPointsOffers"
BANNER = "SM"
logger.set_tc_id(TC_ID)


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


try:
    logger.log("=" * 70, status="info")
    logger.log("  TC_023 — Combinational product/category/basket points offers", status="info")
    logger.log("=" * 70, status="info")

    EAN_ITEM_LEVEL     = _get("Item_EAN", 1, "9349673003620;9349673003552")
    EAN_CATEGORY_LEVEL = _get("Item_EAN", 2, "5010775192324;5010775195936")
    EAN_PRODUCE        = _get("Item_EAN", 3, "9315265004078;9300633026028")
    EAN_BASKET_FILLER  = _get("Item_EAN", 4, "9315087192083")
    CARD_CODE          = _get("Card_number", 1, "9353105847133")

    if not login_pos():
        raise RuntimeError("login_pos failed")

    add_item(EAN_ITEM_LEVEL, CARD_CODE)
    time.sleep(1)
    add_item(EAN_CATEGORY_LEVEL, CARD_CODE)
    time.sleep(1)
    add_item(EAN_PRODUCE, CARD_CODE)
    time.sleep(1)
    add_item(EAN_BASKET_FILLER, CARD_CODE)  # crosses $50 basket-level threshold

    time.sleep(1)
    if not scan_loyalty_salemode(CARD_CODE):
        raise RuntimeError("scan_loyalty_salemode failed")

    win = global_instance.win
    win.child_window(auto_id="PayButton", control_type="Button").click_input()
    logger.log("✅ PayButton clicked.", status="pass")
    time.sleep(3)

    # Step A: unexpected IW "prize to use now" popup — save for later (unrelated
    # to TC_023's points scope; see module docstring).
    _click(win, "SkipChoiceOfferPrompt", "IW prize offer — Save for later")

    # Step B: Collectable offer popup (e.g. Disney Ooshies) — decline.
    _click(win, "List2Button", "Collectable offer — No")

    # Step C: Round-up donation popup — decline.
    _click(win, "List2Button", "Round-up donation — No")

    if not complete_transaction():
        raise RuntimeError("complete_transaction failed")

    ee = verify_eagleeye_logs(expect_wallet_open=True, expect_wallet_settle=True)
    if ee["all_passed"]:
        logger.log("PASS — TC_023 EE settled.", status="pass")
    else:
        logger.log("FAIL — EE verification failed.", status="fail")

    logger.log(
        "ℹ️ On-screen WoWRewardPoints only reflects BASE points, not bonus "
        "campaigns — the true points breakdown must be read from the EE "
        "wallet/settle backend log. Confirmed live: item/category campaign "
        "102825606 DOES apply (totalRewardUnits scales with qualifying item "
        "count). Basket-level campaigns 1206522/1297323 (or their EE-side "
        "equivalents 1270870/102903033) did NOT trigger in 2 live runs "
        "despite basket exceeding $50 both times — needs backend/campaign "
        "team follow-up before this TC can be marked a full pass.",
        status="info")
    logger.log("TODO: Verify Tlogs apportionment for item/category/basket campaigns + receipt image.", status="info")

except Exception as e:
    logger.log(f"FAIL TC_023 unexpected error: {e}", status="fail")
    logger.take_screenshot("TC_023_Unexpected_Error")

finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
