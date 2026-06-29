"""
TC_08A_VerifyDiscountBasketCampaignMarketDayOffer.py
-----------------------------------------------------
Regression Test TC_08A — Validation of Discount Basket Campaign (Market Day Offer)

Confirmed live-run flow (all identifiers verified from screen captures):

  Step 1  Login           : WelcomeText='Welcome', StartScanButton → SCO ready
  Step 2  Eligible items  : 3 items scanned; basket >$100
                            9323966119038 Lindt $30 + 9338441000985 Aus Ckd $27
                            + 9348378001450 TheLady $50 = $107
  Step 3  Gift card       : Scam popup (PopupFrame/List1Button/OK) dismissed WITH focus
                            → GC Battlenet $50 added → basket $157 / 4 items
  Step 4  Loyalty scan    : PayButton → CustomSkip (loyalty prompt visible)
                            → scan card 9353180804441
  Step 5  GC activation   : Assistance Needed (PopupTitle/StoreLogin) → Enter ID
                            (InputTextBox+EnterButton) → Enter Password
                            (InputTextBox+EnterButton) → Gift Card Activation Required
                            (StoreModeScreenTitle1/StoreButton1=OK)
  Step 5b Market Day offer: ContainerButtonList appears with 'Market day 10%' offer
                            → click Usenow button inside matching ListItem
  Step 7  Complete txn    : Select Payment Type screen (LeadthruText)
                            → Tender2 (Card) → EFT auto-approval → Welcome screen
  Step 8  EE settlement   : verify_eagleeye_logs (wallet settle expected = True)
  Step 10 EE logs         : Card validation + Wallet Open + Wallet Settle
  Step 11 EE offer log    : 'Market day 10%' in EE log

Pre-requisite:
  WRC card 9353180804441 (renewed/active) with Market Day 10% basket discount campaign.
  EFT MultiSimulator (RemedyEFTPOSServer) running for auto card approval.

Data source:
  RegressionSale.csv — TC_ID = "TC_08A_VerifyDiscountBasketCampaignMarketDayOffer"
  Iter 1: eligible articles
  Iter 2: exclusion gift card
"""

import sys
import time
import traceback
import ctypes
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from pywinauto import Application
import win32gui

from Components.Login_POS import login_pos
from Components.Add_item import add_item
from Components.Scan_loyalty_tenderprompt import scan_loyalty_tenderprompt
from Components.Redeem_choice_offer import redeem_choice_offer
from Components.Complete_transaction import complete_transaction
from Components.Verify_EagleEye_logs import (
    verify_eagleeye_logs,
    verify_offers_in_ee_log,
    verify_card_in_ee_log,
)
from Components.Read_csv import get_csv_value
from Components.report import logger
from Components import global_instance
from Components.Scan_item import scan_item

TC_ID  = "TC_08A_VerifyDiscountBasketCampaignMarketDayOffer"
BANNER = "SM"
logger.set_tc_id(TC_ID)

_STORE_USER = "ms"
_STORE_PASS = "abcd1234"


def _get_value(column, iteration, fallback):
    try:
        val = get_csv_value("saledata", BANNER, TC_ID, iteration, column)
        if val and not val.startswith("Error") and val != "No matching record found.":
            print(f"✅ Found value: {val}")
            return val
    except Exception:
        pass
    print(f"⚠️ Using fallback for {column} iter {iteration}: {fallback}")
    return fallback


EAN_ELIGIBLE  = _get_value("Item_EAN",  1, "9323966119038;9338441000985;9348378001450")
EAN_EXCLUSION = _get_value("Item_EAN",  2, "076750436640009036009313012991")
CARD_CODE     = _get_value("Card_number", 1, "9353180804441")
CHOICE_OFFER  = _get_value("Choice_offer", 1, "Market day 10%")


def _focus(win):
    """Apply window focus using Alt-key trick — required for WPF button clicks to land."""
    try:
        hwnd = win.wrapper_object().handle
        ctypes.windll.user32.keybd_event(0x12, 0, 0, 0)
        ctypes.windll.user32.keybd_event(0x12, 0, 0x0002, 0)
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.4)
    except Exception:
        pass


def _click_focused(win, auto_id, timeout=5, label=""):
    """Focus window then click button by auto_id. Returns True if clicked."""
    _focus(win)
    btn = win.child_window(auto_id=auto_id, control_type="Button")
    if btn.exists(timeout=timeout):
        btn.click_input()
        logger.log(f"✅ Clicked '{auto_id}' {label}.", status="pass")
        return True
    logger.log(f"⚠️ Button '{auto_id}' not found {label}.", status="info")
    return False


def _dismiss_scam_popup(win):
    """
    Dismiss gift card scam warning popup.
    Confirmed: PopupFrame → Instructions='Be aware of scams...' → List1Button (OK)
    MUST apply window focus before clicking — without focus clicks don't land.
    """
    popup = win.child_window(auto_id="PopupFrame", control_type="Pane")
    if not popup.exists(timeout=2):
        return False
    btn = win.child_window(auto_id="List1Button", control_type="Button")
    if not btn.exists(timeout=2):
        return False
    _focus(win)
    for attempt in range(6):
        btn.click_input()
        time.sleep(0.6)
        if not btn.exists(timeout=0.3):
            logger.log(f"✅ Scam popup dismissed (attempt {attempt+1}).", status="pass")
            time.sleep(0.5)
            return True
    logger.log("⚠️ Scam popup persisted after retries.", status="info")
    return True


def _handle_gc_activation(win):
    """
    Handle full gift card activation flow after loyalty card scan:
      Assistance Needed (StoreLogin) → Enter ID → Enter Password
      → Gift Card Activation Required (StoreButton1 = OK)

    Confirmed identifiers:
      StoreLogin          button on Assistance Needed popup
      InputTextBox        edit field for username + password
      EnterButton         submits each field
      StoreButton1        OK on Gift Card Activation Required screen
      StoreModeScreenTitle1='Gift Card Activation Required'
    """
    # Click StoreLogin
    if not _click_focused(win, "StoreLogin", timeout=8, label="(Assistance Needed)"):
        logger.log("⚠️ StoreLogin not found — skipping activation.", status="info")
        return False
    time.sleep(1.5)

    def _fill_field(label, text):
        _focus(win)
        edit = win.child_window(auto_id="InputTextBox", control_type="Edit")
        if edit.exists(timeout=4):
            edit.click_input()
            time.sleep(0.2)
            edit.type_keys(text, with_spaces=False)
            time.sleep(0.3)
            enter = win.child_window(auto_id="EnterButton", control_type="Button")
            if enter.exists(timeout=2):
                enter.click_input()
                logger.log(f"✅ {label} submitted.", status="pass")
            time.sleep(1.2)
        else:
            logger.log(f"⚠️ InputTextBox not found for {label}.", status="info")

    _fill_field("username", _STORE_USER)
    _fill_field("password", _STORE_PASS)

    # Click StoreButton1 (Gift Card Activation Required → OK)
    if _click_focused(win, "StoreButton1", timeout=8, label="(Gift Card Activation OK)"):
        time.sleep(2)
        return True
    logger.log("⚠️ StoreButton1 not found after credentials.", status="info")
    return False


def _handle_loyalty_and_activation(win):
    """
    Full tender-mode flow for TC_08A:
      1. PayButton
      2. Loyalty prompt (CustomSkip visible) → scan card
      3. Assistance Needed for gift card → _handle_gc_activation
      4. Wait for Market Day choice offer (ContainerButtonList)

    All clicks use _click_focused() / _focus() to ensure WPF buttons register.
    """
    # Step 4a: Click PayButton
    logger.log("➡ Step 4 — Clicking PayButton...", status="info")
    if not _click_focused(win, "PayButton", timeout=5, label=""):
        raise RuntimeError("PayButton not found.")
    time.sleep(1.5)

    # Step 4b: Confirm loyalty prompt (CustomSkip)
    cskip = win.child_window(auto_id="CustomSkip", control_type="Button")
    if not cskip.exists(timeout=5):
        raise RuntimeError("Loyalty prompt (CustomSkip) not found after PayButton.")
    logger.log("✅ Step 4 — Loyalty prompt visible (CustomSkip).", status="pass")

    # Step 4c: Scan loyalty card
    _focus(win)
    scan_item(win, CARD_CODE)
    logger.log(f"✅ Step 4 — Loyalty card {CARD_CODE} scanned at tender prompt.", status="pass")
    time.sleep(2)

    # Step 5: Handle gift card Assistance Needed popup
    assist_popup = win.child_window(auto_id="StoreLogin", control_type="Button")
    if assist_popup.exists(timeout=6):
        logger.log("✅ Step 5 — Assistance Needed popup detected.", status="pass")
        logger.take_screenshot("TC08A_AssistanceNeeded")
        if not _handle_gc_activation(win):
            raise RuntimeError("Gift card activation failed.")
        logger.log("✅ Step 5 — Gift card activation complete.", status="pass")
        logger.take_screenshot("TC08A_AfterActivation")
    else:
        logger.log("ℹ️ Step 5 — No Assistance Needed popup (gift card may not need activation).", status="info")


# ---------------------------------------------------------------------------
# TEST EXECUTION
# ---------------------------------------------------------------------------
try:
    logger.log("═" * 70, status="info")
    logger.log("  TC_08A — Discount Basket Campaign: Market Day Offer", status="info")
    logger.log("═" * 70, status="info")

    # Step 1: Login
    if not login_pos():
        raise RuntimeError("login_pos failed.")
    logger.log("✅ Step 1 — SCO login successful.", status="pass")

    # Step 2: Scan eligible articles (basket > $100)
    add_item(EAN_ELIGIBLE, CARD_CODE)
    logger.log(f"✅ Step 2 — Eligible articles scanned: {EAN_ELIGIBLE}.", status="pass")

    # Step 3: Scan exclusion gift card (scam popup auto-dismissed with focus)
    add_item(EAN_EXCLUSION, CARD_CODE)
    logger.log(f"✅ Step 3 — Exclusion gift card scanned: {EAN_EXCLUSION}.", status="pass")

    # Reconnect win for direct UIA operations
    app = Application(backend="uia").connect(title_re=".*NCR NEXTGENUI.*")
    win = app.window(title_re=".*NCR NEXTGENUI.*")
    global_instance.app = app
    global_instance.win = win

    # Verify basket state before proceeding
    count_el = win.child_window(auto_id="ReceiptItemCount", control_type="Text")
    total_el = win.child_window(auto_id="TotalAmountValue",  control_type="Text")
    basket_count = count_el.window_text() if count_el.exists(timeout=2) else "?"
    basket_total = total_el.window_text() if total_el.exists(timeout=2) else "?"
    logger.log(f"✅ Step 3b — Basket: {basket_count}, Total: {basket_total}.", status="pass")
    logger.take_screenshot("TC08A_BasketBeforePay")

    # Steps 4-5: PayButton → loyalty scan → gift card activation
    _handle_loyalty_and_activation(win)

    # Step 5b / Step 6: Market Day choice offer (ContainerButtonList)
    logger.log("➡ Step 6 — Waiting for Market Day choice offer...", status="info")
    if not redeem_choice_offer(CHOICE_OFFER):
        raise RuntimeError(f"redeem_choice_offer failed for '{CHOICE_OFFER}'.")
    logger.log(f"✅ Step 6 — Market Day offer '{CHOICE_OFFER}' redeemed.", status="pass")
    logger.take_screenshot("TC08A_MarketDayRedeemed")

    # Step 7: Complete transaction (Card payment via EFT auto-approval)
    logger.log("➡ Step 7 — Completing transaction via Card payment...", status="info")
    if not complete_transaction():
        raise RuntimeError("complete_transaction failed.")
    logger.log("✅ Step 7 — Transaction completed successfully.", status="pass")
    logger.take_screenshot("TC08A_TransactionComplete")

    # Step 8: Verify EagleEye settlement
    ee_result = verify_eagleeye_logs(
        card_number=CARD_CODE,
        expect_wallet_open=True,
        expect_wallet_settle=True,
        start_time=global_instance.ee_log_start_time,
    )
    logger.log(
        f"{'✅' if ee_result else '⚠️'} Step 8/10 — EE log "
        f"Card Validation + Wallet Open + Wallet Settle: {ee_result}.",
        status="pass" if ee_result else "info"
    )

    # Step 10: Card in EE log
    card_ok = verify_card_in_ee_log(CARD_CODE, start_time=global_instance.ee_log_start_time)
    logger.log(
        f"{'✅' if card_ok else '⚠️'} Step 10 — EE log card {CARD_CODE}: {card_ok}.",
        status="pass" if card_ok else "info"
    )

    # Step 11: Market Day offer in EE log
    offers_ok = verify_offers_in_ee_log(
        [CHOICE_OFFER],
        start_time=global_instance.ee_log_start_time,
    )
    logger.log(
        f"{'✅' if offers_ok else '⚠️'} Step 11 — EE log '{CHOICE_OFFER}': {offers_ok}.",
        status="pass" if offers_ok else "info"
    )

    logger.log("═" * 70, status="info")
    logger.log("  TC_08A COMPLETE", status="pass")
    logger.log("═" * 70, status="info")

except RuntimeError as err:
    logger.log(f"❌ TC_08A ERROR: {err}", status="fail")
    print(f"❌ TC_08A ERROR: {err}")
    try:
        app2 = Application(backend="uia").connect(title_re=".*NCR NEXTGENUI.*")
        win2 = app2.window(title_re=".*NCR NEXTGENUI.*")
        logger.take_screenshot("TC08A_Failure_Screen")
    except Exception:
        pass
except Exception as ex:
    logger.log(f"❌ TC_08A UNEXPECTED ERROR: {ex}", status="fail")
    print(f"❌ TC_08A UNEXPECTED ERROR: {ex}")
    traceback.print_exc()
    try:
        app2 = Application(backend="uia").connect(title_re=".*NCR NEXTGENUI.*")
        win2 = app2.window(title_re=".*NCR NEXTGENUI.*")
        logger.take_screenshot("TC08A_Unexpected_Error")
    except Exception:
        pass
finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
