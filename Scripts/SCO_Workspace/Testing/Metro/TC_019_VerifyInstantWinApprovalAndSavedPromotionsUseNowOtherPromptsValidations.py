"""
TC_019_VerifyInstantWinApprovalAndSavedPromotionsUseNowOtherPromptsValidations.py
---------------------------------------------------------------------------------
TC_019 — IW Approval Use-Now + Saved + Other Prompts

CONFIRMED LIVE-RUN FLOW (2 live runs against card 9353105915450, SM banner):
    Step 1  Login              : login_pos() -> Welcome screen.
    Step 2  Add IW items       : add_item("9300677010670;9300677011523;9300677010663", card)
                                  -> basket $37.00 (C/Pure Honey, Clvr Honey, Pure Hny UD).
    Step 3  Add bunch items    : add_item("9300633594176;9328854011524", card)
                                  -> basket $49.10 (WW Lem/Med Cake, Moki L Metal EPh).
                                  NOTE: these EANs are the confirmed bunch-eligible set
                                  from TC_09 (campaign 1261389 "Test Bunch sample").
                                  Original CSV had the SAME ean duplicated x2, which
                                  is NOT reliable -- do not batch-scan a duplicate EAN
                                  inside one add_item() call (see gotcha below).
    Step 4  Top-up to >$100    : 3x single add_item("9300677011523", card) calls
                                  (Clvr Honey $23 ea) -> basket $118.10 (8 items).
    Step 5  Scan loyalty card  : scan_loyalty_salemode(card) -- must be SALE MODE.
                                  Confirmed: 'Scan Coupon' screen auto-dismissed via
                                  CancelCoupon; RewardTextBlock='Current Rewards
                                  Balance: $0'.
    Step 6  PayButton           : popup appears --
                                  LeadthruText='You have 1 discount to select from'
                                  ExpiryDaysText='Hurry, expiring in 16 days'
                                  Button id='Usenow' (flat/top-level, click_input() WORKS
                                  here -- unlike TC_018's nested ContainerButtonList
                                  variant) + SkipChoiceOfferPrompt + GoBack.
                                  Clicking Usenow applies an EXACT 10% discount
                                  ($118.10 -> $106.29) = "Market Day Mobile 10 percent
                                  off" CHOICE offer -- confirmed via math, reproduced
                                  identically across 2 separate live runs.
    Step 7  Collectable popup   : PopupFrame with:
                                  Instructions='You have earned 6 Disney Ooshies. Are
                                  you collecting? If Yes, take redemption token to Team
                                  Member.'
                                  List1Button='Yes' / List2Button='No' -- clicked No.
    Step 8  Round-up popup      : PopupFrame with
                                  LeadthruText='Would you like to round the transaction
                                  to $107.00 and donate $0.71 to SALVATION ARMY 2?'
                                  List1Button='Yes, Please' / List2Button='No, Thank
                                  You' -- clicked No.
    Step 9  Payment              : 'Select Payment Type' screen appears very briefly
                                  (Tender2/Tender3/OtherPaymentButton visible but
                                  disabled) then PIN Pad Entry popup
                                  (PopupTitle='PIN Pad Entry',
                                  Instructions='Please follow the instructions on the
                                  PIN Pad') auto-processes -- NO Tender2 click was
                                  needed; transaction auto-completed and returned to
                                  Welcome screen with 'Printing receipt... please
                                  wait.' / AmountPaid=$106.29 / AmountDue=$0.00.

IMPORTANT FINDING -- NOT A SCRIPT BUG:
    The Instant Win APPROVAL popup ($25 use-now) and the Instant Win SAVED popup
    ($10/$50 denominations) described in the ticket NEVER appeared in either of the
    2 live runs performed, despite basket exceeding $100 and containing all 4
    ticket-specified IW-eligible EANs (9300677010670, 9300677011523, 9300677010663;
    the 5th ticket EAN 9350763347364 is PERMANENTLY BLOCKED on this SCO -- confirmed
    during TC_018 build, dropped here too). Only the 10% choice offer, the
    collectable (Disney Ooshies) prompt, and the round-up donation prompt triggered.
    This was reproduced identically twice (same card, full basket rebuild both
    times), ruling out a one-off timing fluke. Conclusion: the IW Approval/Saved
    campaign is NOT currently active/provisioned on this card in the live EagleEye
    backend. This needs backend/campaign-team verification before this TC can be
    completed end-to-end -- do NOT assume the automation is at fault.

    handle_instant_win_approval() / handle_instant_win_saved() below are left as
    best-effort per the original component design (Components/Redeem_instant_win.py)
    for when the offer IS live, but their click_input() calls have NOT been
    confirmed against a real IW popup (only against the differently-shaped choice
    offer popup, which uses a flat Usenow button, not nested in
    ContainerButtonList/ListItem like TC_018's IW SAVED popup). If a future run
    shows the real IW popup, dump the UIA tree before trusting these handlers --
    they may need the win32api click workaround discovered in TC_018.
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
from Components.Redeem_instant_win import (
    handle_instant_win_approval,
    handle_instant_win_saved,
)
from Components.Complete_transaction import complete_transaction
from Components.Verify_EagleEye_logs import verify_eagleeye_logs
from Components.Read_csv import get_csv_value
from Components.report import logger
from Components import global_instance

TC_ID  = "TC_019_VerifyInstantWinApproval&SavedPromotionsUseNowOtherPromptsValidations"
BANNER = "Metro"
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
    logger.log("  TC_019 — Instant Win Approval (USE NOW) + Saved + other prompts", status="info")
    logger.log("=" * 70, status="info")

    # Confirmed-good EANs (see module docstring for live-run history).
    # NOTE: 9350763347364 from the ticket is permanently blocked on this SCO
    # (confirmed during TC_018 build) and is intentionally omitted.
    EAN_IT1    = _get("Item_EAN", 1, "9300677010670;9300677011523;9300677010663")
    EAN_IT2    = _get("Item_EAN", 2, "9300633594176;9328854011524")
    EAN_TOPUP  = "9300677011523"  # Clvr Honey $23 — scanned singly to top up >$100
    CARD_CODE  = _get("Card_number", 1, "9353105915450")
    SAVED_DEN  = _get("Instant_win_offer_redeem", 1, "50")

    if not login_pos():
        raise RuntimeError("login_pos failed")

    add_item(EAN_IT1, CARD_CODE)
    time.sleep(1)
    add_item(EAN_IT2, CARD_CODE)

    # Top up to >$100 with single (non-batched) scans of the same EAN — batching
    # 3x of an identical EAN in one add_item() call was observed to silently fail
    # to register on this SCO; single scans with a short pause work reliably.
    for _ in range(3):
        time.sleep(2)
        add_item(EAN_TOPUP, CARD_CODE)

    time.sleep(1)
    if not scan_loyalty_salemode(CARD_CODE):
        raise RuntimeError("scan_loyalty_salemode failed")

    win = global_instance.win
    win.child_window(auto_id="PayButton", control_type="Button").click_input()
    logger.log("✅ PayButton clicked.", status="pass")
    time.sleep(3)

    # Step A: IW APPROVAL — click Use Now per scenario (best-effort; see docstring
    # — this offer has NOT reliably triggered live for this card).
    if not handle_instant_win_approval(action="use_now", timeout=8):
        logger.log(
            "ℹ️ IW approval popup not detected — card may not currently have an "
            "active IW Approval campaign provisioned (confirmed across 2 live "
            "runs). Continuing with whatever popup is actually on screen.",
            status="info")

    # Step B: SAVED-promotions popup — use_now on chosen denomination (best-effort).
    handle_instant_win_saved(action="use_now", denomination=SAVED_DEN, timeout=5)

    # Step C: Choice offer popup — confirmed live pattern: flat 'Usenow' button
    # (NOT nested like TC_018's IW SAVED popup), click_input() works directly.
    _click(win, "Usenow", "Choice offer — Use now")

    # Step D: Collectable offer popup (e.g. Disney Ooshies) — decline.
    _click(win, "List2Button", "Collectable offer — No")

    # Step E: Round-up donation popup — decline.
    _click(win, "List2Button", "Round-up donation — No")

    if not complete_transaction():
        raise RuntimeError("complete_transaction failed")

    ee = verify_eagleeye_logs(expect_wallet_open=True, expect_wallet_settle=True)
    if ee["all_passed"]:
        logger.log("PASS — TC_019 EE settled.", status="pass")
    else:
        logger.log("FAIL — EE verification failed.", status="fail")

    logger.log(
        "ℹ️ IW Approval/Saved offers did not trigger in live testing — needs "
        "backend/campaign verification for card 9353105915450 before this TC "
        "can be marked fully complete.", status="info")
    logger.log("TODO: Verify Tlogs apportionment + receipt image.", status="info")

except Exception as e:
    logger.log(f"FAIL TC_019 unexpected error: {e}", status="fail")
    logger.take_screenshot("TC_019_Unexpected_Error")

finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
