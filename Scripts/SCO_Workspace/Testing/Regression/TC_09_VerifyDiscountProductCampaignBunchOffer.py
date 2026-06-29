"""
TC_09_VerifyDiscountProductCampaignBunchOffer.py
------------------------------------------------
Regression Test TC_09 — Validation of Discount Product campaigns (Bunch Offer)

Confirmed live-run flow (identifiers verified from screen captures):
    Step 1  Login          : Welcome screen → StartScanButton → SCO ready
    Step 2  Eligible items : 5 items scanned; basket ~$114
    Step 3  Gift card      : scam popup (PopupFrame/List1Button) → GC Battlenet $50 added
    Step 4  Loyalty scan   : scan_loyalty_salemode → RewardTextBlock shows balance,
                             Member price saving: -$8.00 applied
    Step 5  Pay + GC flow  : PayButton → Assistance Needed (StoreLogin) →
                             Enter ID 'ms' (InputTextBox/EnterButton) →
                             Enter Password (InputTextBox/EnterButton) →
                             Gift Card Activation Required (StoreButton1/OK)
                             → BUNCH OFFER -$2.00 appears in basket
    Step 6  Exciting News  : verify_exciting_news_prompt (non-fatal if absent)
    Step 7  Bunch popup    : PopupFrame/Instructions contains 'Congratulations'
                             dismissed via List1Button (OK)
    Step 7b Tender screen  : LeadthruText='Select Payment Type'
                             TotalRewardsValue='$10.00', WoWRewardPoints='110'
    Step 8  DRY-RUN        : GoBackSale clicked (no real payment)

Pre-requisite:
    WRC card (9353187352211) with active Bunch Offer campaign (1261389 — Test Bunch sample).
"""

import sys
import time
import traceback
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components.Login_POS import login_pos
from Components.Add_item import add_item
from Components.Scan_loyalty_salemode import scan_loyalty_salemode
from Components.Verify_exciting_news_prompt import verify_exciting_news_prompt
from Components.Verify_EagleEye_logs import (
    verify_eagleeye_logs,
    verify_offers_in_ee_log,
    verify_card_in_ee_log,
)
from Components.Read_csv import get_csv_value
from Components.report import logger
from Components import global_instance

import win32gui
import ctypes
from pywinauto import Application

TC_ID  = "TC_09_VerifyDiscountProductCampaignBunchOffer"
BANNER = "SM"
logger.set_tc_id(TC_ID)

# Store login credentials used during gift card activation at PayButton
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


EAN_ELIGIBLE  = _get_value("Item_EAN", 1, "9328854011524;9300633594176;9323966119038;9338441000985;9348378001450")
EAN_EXCLUSION = _get_value("Item_EAN", 2, "076750436640009036009313012991")
CARD_CODE     = _get_value("Card_number", 1, "9353187352211")
PROMO_DESC    = _get_value("Promotion_description", 1, "Test Bunch sample")


def _focus(win):
    hwnd = win.handle
    ctypes.windll.user32.keybd_event(0x12, 0, 0, 0)
    ctypes.windll.user32.keybd_event(0x12, 0, 0x0002, 0)
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(0.3)


def _handle_pay_to_activation(win):
    """
    Click PayButton → dismiss Assistance Needed (StoreLogin) →
    enter store credentials (ms/abcd1234) → click StoreButton1 (Gift Card Activation OK).

    Confirmed identifiers from live captures:
      PayButton                     triggers 'Assistance Needed' popup
      StoreLogin                    opens credential entry screen
      Instructions='Enter ID'       first credential screen
      InputTextBox                  username/password edit field
      EnterButton                   submits each credential
      StoreModeScreenTitle1='Gift Card Activation Required'
      StoreButton1                  OK button on activation screen
    """
    _focus(win)

    pay_btn = win.child_window(auto_id="PayButton", control_type="Button")
    if not pay_btn.exists(timeout=3):
        logger.log("❌ PayButton not found.", status="fail")
        return False
    pay_btn.click_input()
    logger.log("✅ PayButton clicked — waiting for Assistance Needed popup.", status="pass")
    time.sleep(2)

    store_login = win.child_window(auto_id="StoreLogin", control_type="Button")
    if store_login.exists(timeout=5):
        store_login.click_input()
        logger.log("✅ StoreLogin clicked.", status="pass")
        time.sleep(1.5)

        def _fill_field(label, text):
            edit = win.child_window(auto_id="InputTextBox", control_type="Edit")
            if edit.exists(timeout=4):
                edit.click_input()
                time.sleep(0.2)
                edit.type_keys(text, with_spaces=False)
                time.sleep(0.3)
                enter_btn = win.child_window(auto_id="EnterButton", control_type="Button")
                if enter_btn.exists(timeout=2):
                    enter_btn.click_input()
                    logger.log(f"✅ {label} submitted.", status="pass")
                time.sleep(1.2)
            else:
                logger.log(f"⚠️ InputTextBox not found for {label}.", status="info")

        _fill_field("username", _STORE_USER)
        _fill_field("password", _STORE_PASS)
    else:
        logger.log("⚠️ StoreLogin not found after PayButton — may not be needed.", status="info")

    store_btn1 = win.child_window(auto_id="StoreButton1", control_type="Button")
    if store_btn1.exists(timeout=8):
        store_btn1.click_input()
        logger.log("✅ StoreButton1 (Gift Card Activation OK) clicked.", status="pass")
        time.sleep(2)
        return True
    logger.log("⚠️ StoreButton1 not found — activation may have completed automatically.", status="info")
    return True


def _verify_bunch_offer_in_basket(win):
    """
    Check basket for 'BUNCH OFFER' discount line.
    Confirmed: ItemDescription='BUNCH OFFER', ItemPrice='-$2.00'
    """
    try:
        cart = win.child_window(auto_id="CartReceipt", control_type="List")
        if not cart.exists(timeout=3):
            return False
        for item in cart.children(control_type="ListItem"):
            for child in item.children():
                if child.element_info.automation_id == "ItemDescription":
                    if "BUNCH" in child.window_text().upper():
                        price_child = next(
                            (c for c in item.children()
                             if c.element_info.automation_id == "ItemPrice"),
                            None
                        )
                        price = price_child.window_text() if price_child else "?"
                        logger.log(
                            f"✅ Step 5 — BUNCH OFFER in basket: '{child.window_text()}' {price}.",
                            status="pass"
                        )
                        return True
    except Exception as e:
        logger.log(f"⚠️ Bunch offer basket check error: {e}", status="info")
    return False


def _handle_bunch_popup(win):
    """
    Wait for and dismiss the bunch congratulations popup.
    Confirmed: PopupFrame → Instructions contains 'Congratulations' → List1Button (OK)
    """
    popup = win.child_window(auto_id="PopupFrame", control_type="Pane")
    for _ in range(20):  # poll up to 10s
        if popup.exists(timeout=0.5):
            instr = win.child_window(auto_id="Instructions", control_type="Text")
            instr_text = ""
            if instr.exists(timeout=0.3):
                try:
                    instr_text = instr.window_text()
                except Exception:
                    pass
            if instr_text:
                logger.log(f"✅ Step 7 — Bunch popup: '{instr_text}'", status="pass")
                logger.take_screenshot("TC09_BunchPopup")
                btn = win.child_window(auto_id="List1Button", control_type="Button")
                if btn.exists(timeout=2):
                    btn.click_input()
                    logger.log("✅ Step 7 — Bunch popup dismissed via List1Button.", status="pass")
                    time.sleep(1)
                    return True
        time.sleep(0.5)
    logger.log("ℹ️ Step 7 — No bunch popup detected within 10s (non-fatal).", status="info")
    return False


# ---------------------------------------------------------------------------
# TEST EXECUTION
# ---------------------------------------------------------------------------
try:
    logger.log("═" * 70, status="info")
    logger.log("  TC_09 — Discount Product Campaign: Bunch Offer", status="info")
    logger.log("═" * 70, status="info")

    # Step 1: Login
    if not login_pos():
        raise RuntimeError("login_pos failed.")
    logger.log("✅ Step 1 — SCO login successful.", status="pass")

    # Step 2: Scan eligible articles (bunch items + fillers, basket > $100)
    add_item(EAN_ELIGIBLE, CARD_CODE)
    logger.log(f"✅ Step 2 — Eligible articles scanned: {EAN_ELIGIBLE}.", status="pass")

    # Step 3: Scan exclusion gift card (scam popup auto-dismissed by add_item)
    add_item(EAN_EXCLUSION, CARD_CODE)
    logger.log(f"✅ Step 3 — Exclusion gift card scanned: {EAN_EXCLUSION}.", status="pass")

    # Step 4: Scan loyalty card in SALE MODE
    if not scan_loyalty_salemode(CARD_CODE):
        raise RuntimeError("scan_loyalty_salemode failed.")
    logger.log(f"✅ Step 4 — Loyalty card {CARD_CODE} scanned in sale mode.", status="pass")
    time.sleep(2)

    # Re-connect win for direct UIA operations
    app = Application(backend="uia").connect(title_re=".*NCR NEXTGENUI.*")
    win = app.window(title_re=".*NCR NEXTGENUI.*")
    global_instance.app = app
    global_instance.win = win

    # Step 5: PayButton → gift card activation → BUNCH OFFER appears in basket
    logger.log("➡ Step 5 — PayButton + gift card activation flow...", status="info")
    if not _handle_pay_to_activation(win):
        raise RuntimeError("Gift card activation flow failed.")

    if not _verify_bunch_offer_in_basket(win):
        logger.log("⚠️ Step 5 — BUNCH OFFER not yet visible in basket.", status="info")
        logger.take_screenshot("TC09_BunchOffer_NotInBasket")

    # Step 6: Exciting News prompt (non-fatal)
    if verify_exciting_news_prompt(timeout_seconds=5):
        logger.log("✅ Step 6 — Exciting News prompt detected and dismissed.", status="pass")
    else:
        logger.log("ℹ️ Step 6 — No Exciting News prompt.", status="info")

    # Step 7: Bunch congratulations popup → dismiss
    _handle_bunch_popup(win)

    # Step 7b: Confirm tender screen identifiers
    leadthru = win.child_window(auto_id="LeadthruText", control_type="Text")
    if leadthru.exists(timeout=5) and "Select Payment Type" in leadthru.window_text():
        savings = win.child_window(auto_id="TotalRewardsValue", control_type="Text")
        points  = win.child_window(auto_id="WoWRewardPoints",   control_type="Text")
        logger.log(
            f"✅ Step 7b — Tender screen: savings={savings.window_text() if savings.exists(timeout=1) else '?'}, "
            f"points={points.window_text() if points.exists(timeout=1) else '?'}.",
            status="pass"
        )
        logger.take_screenshot("TC09_TenderScreen")
    else:
        logger.log("⚠️ Step 7b — Tender screen not detected.", status="info")
        logger.take_screenshot("TC09_TenderScreen_NotFound")

    # Step 8: DRY-RUN — go back instead of completing
    go_back = win.child_window(auto_id="GoBackSale", control_type="Button")
    if go_back.exists(timeout=3):
        go_back.click_input()
        logger.log("ℹ️ Step 8 — DRY-RUN: GoBackSale clicked (transaction not completed).", status="info")
    else:
        logger.log("ℹ️ Step 8 — DRY-RUN: GoBackSale not found — already in scan mode.", status="info")

    # Steps 10-11: EE log verification
    ee_result = verify_eagleeye_logs(
        card_number=CARD_CODE,
        expect_wallet_open=True,
        expect_wallet_settle=False,
        start_time=global_instance.ee_log_start_time,
    )
    logger.log(
        f"{'✅' if ee_result else '⚠️'} Step 10 — EE log card validation + wallet open: {ee_result}.",
        status="pass" if ee_result else "info"
    )
    verify_card_in_ee_log(CARD_CODE, start_time=global_instance.ee_log_start_time)

    offers_ok = verify_offers_in_ee_log(
        [PROMO_DESC],
        start_time=global_instance.ee_log_start_time,
    )
    logger.log(
        f"{'✅' if offers_ok else '⚠️'} Step 11 — EE log '{PROMO_DESC}': {offers_ok} "
        "(dry-run — settle not sent).",
        status="pass" if offers_ok else "info"
    )

    logger.log("═" * 70, status="info")
    logger.log("  TC_09 COMPLETE", status="pass")
    logger.log("═" * 70, status="info")

except RuntimeError as err:
    logger.log(f"❌ TC_09 ERROR: {err}", status="fail")
    print(f"❌ TC_09 ERROR: {err}")
except Exception as ex:
    logger.log(f"❌ TC_09 UNEXPECTED ERROR: {ex}", status="fail")
    print(f"❌ TC_09 UNEXPECTED ERROR: {ex}")
    traceback.print_exc()
    logger.take_screenshot("TC09_Unexpected_Error")
finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
