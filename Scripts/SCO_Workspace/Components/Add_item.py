import sys
import time
import ctypes
import re
from pathlib import Path

import win32gui
from pywinauto.timings import Timings
from pywinauto import Application, timings

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components import global_instance
from Components.Ensure_EFTSimulator_closed import ensure_EFTSimulator_closed
from Components.Ensure_services_stopped import ensure_services_stopped, SERVICES_TO_STOP
from Components.report import logger

# class _FallbackLogger:
#     def log(self, message, status=None):
#         print(message)

#     def take_screenshot(self, name):
#         print(f"[screenshot] {name}")


# logger = globals().get("logger", _FallbackLogger())


def _screenshot_safe_name(value):
    return re.sub(r"[^A-Za-z0-9_\-]", "_", str(value))

_user32 = ctypes.windll.user32
_VK_MENU = 0x12
_KEYEVENTF_KEYUP = 0x0002

# Global pywinauto timing tuning for UIA backend speed
Timings.after_click_wait = 0.02
Timings.after_clickinput_wait = 0.02
Timings.after_setfocus_wait = 0.02
Timings.after_setcursorpos_wait = 0.0
Timings.exists_timeout = 0.5
Timings.exists_retry = 0.05

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components.Scan_item import scan_item


# Cache of resolved UIA wrapper objects so we avoid re-walking the whole
# window tree on every is_enabled / click. WindowSpecification.exists() and
# is_enabled() each re-search the entire descendant tree; a resolved wrapper
# does NOT. This is the single biggest speed win on heavy WPF apps.
_wrapper_cache = {}


def _resolve_wrapper(win, auto_id, control_type="Button", timeout=0.1):
    cached = _wrapper_cache.get(auto_id)
    if cached is not None:
        try:
            # Cheap liveness probe; raises if element is gone.
            cached.element_info.runtime_id
            return cached
        except Exception:
            _wrapper_cache.pop(auto_id, None)

    spec = win.child_window(auto_id=auto_id, control_type=control_type)
    if not spec.exists(timeout=timeout):
        return None
    try:
        w = spec.wrapper_object()
        _wrapper_cache[auto_id] = w
        return w
    except Exception:
        return None


def _fast_click(control):
    """Prefer UIA invoke/click first; fall back to mouse click_input when needed."""
    try:
        control.click()
    except Exception:
        control.click_input()


def _is_button_enabled(win, auto_id, timeout=0.05):
    w = _resolve_wrapper(win, auto_id, timeout=timeout)
    if w is None:
        return False
    try:
        return w.is_enabled()
    except Exception:
        _wrapper_cache.pop(auto_id, None)
        return False


def _try_click_button(win, auto_id, timeout=0.05):
    w = _resolve_wrapper(win, auto_id, timeout=timeout)
    if w is None:
        return False
    _fast_click(w)
    return True


def _handle_continue_popup(win, timeout=0.05):
    """Fast popup handler: look directly for Yes_Button (single tree walk)."""
    yes_spec = win.child_window(auto_id="Yes_Button", control_type="Button")
    if yes_spec.exists(timeout=timeout):
        try:
            _fast_click(yes_spec.wrapper_object())
            return True
        except Exception:
            return False
    return False

def get_item_details(win):

    # _handle_continue_popup(win)
        

    try:
        count_element = win.child_window(auto_id="ReceiptItemCount", control_type="Text")
        count_text = count_element.window_text() 
        match = re.search(r'\d+', count_text)
        expected_count = int(match.group()) if match else 0
        print(f"📦 Expected Item Count: {expected_count}")
    except Exception:
        expected_count = -1

    cart_list = win.child_window(auto_id="CartReceipt", control_type="List")

    item_descriptions = []
    item_prices = []

    try:
        receipt_items = cart_list.children(control_type="ListItem")
        print(f"Total ListItems found: {len(receipt_items)}")
        
        for item in receipt_items:
            desc_text = ""
            price_text = ""
            
            # FIX 1: Use .children() to prevent scanning outside the row
            for child in item.children():
                try:
                    current_id = child.element_info.automation_id
                    
                    # FIX 2: Add 'not desc_text' to lock in the first match
                    if current_id == "ItemDescription" and not desc_text:
                        desc_text = child.window_text()
                    elif current_id == "ItemPrice" and not price_text:
                        price_text = child.window_text()
                except Exception:
                    continue
                    
            if desc_text and price_text:
                if price_text.startswith("-"):
                    print(f"⏭️ Skipping Promotion: {desc_text} ({price_text})")
                    continue 
                    
                item_descriptions.append(desc_text)
                item_prices.append(price_text)
                
    except Exception as e:
        print(f"⚠️ Error reading basket items: {e}")
        
    if len(item_descriptions) == expected_count:
        logger.log("✅ Extracted item count matches the Cart Item Count!", status="pass")
    else:
        logger.log(
            f"❌ Warning: Extracted item count{len(item_descriptions)} items, but expected {expected_count}.",
            status="fail"
        )
        logger.take_screenshot("Receipt_Item_Count_Mismatch")

    print(f"{len(item_descriptions)} items in the basket: and their prices: {item_prices}")

    return item_descriptions, item_prices

def _dismiss_item_not_found(win, timeout=0.1):
    """
    Acknowledge any error popup (item not found / not available) after scanning.
    Short timeout — popups appear immediately or not at all.
    """
    for aid in ("ASAOKButton", "OKButton", "OK_Button", "CommandButton1",
                "AlertOKButton", "ErrorOKButton"):
        try:
            btn = win.child_window(auto_id=aid, control_type="Button")
            if btn.exists(timeout=timeout):
                btn.click_input()
                logger.log(f"⚠️ Item-not-found popup dismissed via auto_id='{aid}'.", status="info")
                time.sleep(0.3)
                return True
        except Exception:
            continue

    for title in ("OK", "Ok", "Continue", "Acknowledge"):
        try:
            btn = win.child_window(title=title, control_type="Button")
            if btn.exists(timeout=0.1):
                btn.click_input()
                logger.log(f"⚠️ Item-not-found popup dismissed via title='{title}'.", status="info")
                time.sleep(0.3)
                return True
        except Exception:
            continue

    return False


def _store_login_credentials(win, username="ms", password="abcd1234"):
    """
    Enter store manager credentials into the SCO login screen.

    Confirmed screen identifiers (from live capture):
      - Instructions text: 'Enter ID' then 'Enter Password'
      - Edit field: auto_id='InputTextBox'
      - Submit button: auto_id='EnterButton'

    Flow: type username → EnterButton → type password → EnterButton.
    Uses click_input + type_keys for the on-screen keyboard field.
    """
    def _fill_and_confirm(label, text):
        logger.log(f"🔑 Entering {label}.", status="info")
        edit = win.child_window(auto_id="InputTextBox", control_type="Edit")
        if edit.exists(timeout=3):
            edit.click_input()
            time.sleep(0.2)
            edit.type_keys(text, with_spaces=False)
            time.sleep(0.3)
        else:
            logger.log(f"⚠️ InputTextBox not found for {label}.", status="info")
        enter_btn = win.child_window(auto_id="EnterButton", control_type="Button")
        if enter_btn.exists(timeout=2):
            enter_btn.click_input()
            logger.log(f"✅ {label} submitted via EnterButton.", status="info")
        else:
            logger.log(f"⚠️ EnterButton not found after {label}.", status="info")
        time.sleep(1.0)  # allow screen transition between ID and password

    _fill_and_confirm("username (ID)", username)
    _fill_and_confirm("password", password)


def _handle_giftcard_activation(win):
    """
    Handle the store login + approval flow triggered when a gift card is scanned.

    Two observed flows (handled automatically):
      A. Auto-login: StoreLogin → 'Gift Card Activation Required' (StoreButton1) directly.
      B. Credential login: StoreLogin → username/password screen → StoreButton1.

    Always checks for StoreButton1 first before attempting credential entry,
    avoiding accidental keyboard input that could dismiss the approval screen.
    """
    try:
        store_btn = win.child_window(auto_id="StoreLogin", control_type="Button")
        if not store_btn.exists(timeout=1.5):
            return False

        logger.log("✅ Gift card activation: 'Assistance Needed' popup — clicking StoreLogin.", status="pass")
        print("✅ Gift card activation popup detected — clicking StoreLogin.")
        store_btn.click_input()
        time.sleep(0.8)  # let the resulting screen settle

        # --- Path A: auto-login (StoreButton1 appears immediately, no credentials) ---
        activation_btn = win.child_window(auto_id="StoreButton1", control_type="Button")
        if activation_btn.exists(timeout=2.0):
            activation_btn.click_input()
            time.sleep(0.5)
            logger.log("✅ Gift card activation: auto-login — StoreButton1 clicked.", status="pass")
            print("✅ Gift card activation: auto-login, StoreButton1 (OK) clicked.")
            return True

        # --- Path B: credentials required (StoreButton1 not yet visible) ---
        logger.log("🔑 Gift card activation: credential screen detected — entering credentials.", status="info")
        _store_login_credentials(win, "ATMGR5", "abcd1234")
        logger.log("✅ Gift card activation: credentials submitted.", status="pass")
        print("✅ Gift card activation: credentials submitted.")

        # After credentials, wait for 'Gift Card Activation Required' (StoreButton1)
        for aid in ("StoreButton1", "OK_Button", "ASAOKButton", "OKButton",
                    "GenericOKButton", "List1Button"):
            try:
                btn = win.child_window(auto_id=aid, control_type="Button")
                if btn.exists(timeout=6):
                    btn.click_input()
                    time.sleep(0.5)
                    logger.log(f"✅ Gift card activation: approved via auto_id='{aid}'.", status="pass")
                    print(f"✅ Gift card activation: approved via '{aid}'.")
                    return True
            except Exception:
                pass

        for title in ("OK", "Ok", "Approve", "Continue"):
            try:
                btn = win.child_window(title=title, control_type="Button")
                if btn.exists(timeout=1):
                    btn.click_input()
                    time.sleep(0.5)
                    logger.log(f"✅ Gift card activation: approved via title='{title}'.", status="pass")
                    return True
            except Exception:
                pass

        logger.log("⚠️ Gift card activation: approval button not found.", status="info")

    except Exception as e:
        logger.log(f"⚠️ Gift card activation handler error: {e}", status="info")

    return False


def _handle_scan_popups(win, timeout=0.15):
    """
    Handle any popup that appears during item scanning.
    IMPORTANT: Always applies window focus before clicking — without focus
    click_input() calls don't land on NCR NEXTGENUI WPF buttons.

    Handles:
      1. Gift card scam-warning (PopupFrame/List1Button=OK) — retries with focus.
      2. Collectable/bunch offer prompt (PopupFrame/List2Button=No).
      3. Item-not-found / error popup.
    """
    try:
        popup = win.child_window(auto_id="PopupFrame", control_type="Pane")
        if popup.exists(timeout=0.5):
            yes_btn = win.child_window(auto_id="List1Button", control_type="Button")
            if yes_btn.exists(timeout=0.2):
                # Apply focus before every click attempt
                try:
                    hwnd = win.wrapper_object().handle
                    _user32.keybd_event(_VK_MENU, 0, 0, 0)
                    _user32.keybd_event(_VK_MENU, 0, _KEYEVENTF_KEYUP, 0)
                    win32gui.SetForegroundWindow(hwnd)
                    time.sleep(0.4)
                except Exception:
                    pass
                # Retry dismiss until confirmed gone (max 6 attempts × 0.6s = 3.6s)
                for attempt in range(6):
                    yes_btn.click_input()
                    time.sleep(0.6)
                    if not yes_btn.exists(timeout=0.3):
                        logger.log(
                            f"✅ Scam popup dismissed via List1Button (attempt {attempt+1}).",
                            status="pass"
                        )
                        time.sleep(0.5)  # allow gift card to register in basket
                        return True
                logger.log("⚠️ Scam popup persisted after retries — continuing.", status="info")
                return True

            no_btn = win.child_window(auto_id="List2Button", control_type="Button")
            if no_btn.exists(timeout=0.1):
                no_btn.click_input()
                logger.log("⚠️ Collectable/bunch offer popup: clicked No (List2Button).", status="info")
                time.sleep(0.3)
                return True
    except Exception:
        pass

    return _dismiss_item_not_found(win, timeout=0.1)


def add_item(Code_EANList, card_code):

    try:
        if not Code_EANList or not str(Code_EANList).strip():
            logger.log("❌ Code_EANList is empty; cannot start item scan.", status="fail")
            logger.take_screenshot("Empty_Code_EANList")
            return

        if not card_code or not str(card_code).strip():
            logger.log("❌ Card code is empty; cannot proceed to payment scan.", status="fail")
            logger.take_screenshot("Empty_Card_Code")
            return

        app = Application(backend="uia").connect(title_re=".*NCR NEXTGENUI.*")
        win = app.window(title_re=".*NCR NEXTGENUI.*")
        global_instance.app = app
        global_instance.win = win
        logger.log("✅ Connected to NCR NEXTGENUI window.", status="pass")

        try:
            win_hwnd = win.wrapper_object().handle
        except Exception:
            win_hwnd = None

        def _focus_win():
            if win_hwnd:
                try:
                    if win32gui.GetForegroundWindow() == win_hwnd:
                        return
                    _user32.keybd_event(_VK_MENU, 0, 0, 0)
                    _user32.keybd_event(_VK_MENU, 0, _KEYEVENTF_KEYUP, 0)
                    win32gui.SetForegroundWindow(win_hwnd)
                    if win32gui.GetForegroundWindow() == win_hwnd:
                        return
                except Exception:
                    pass
            try:
                win.set_focus()
            except Exception:
                pass

        _focus_win()

        balance_check_btn = win.child_window(title_re=".*Gift Card/Store Credit Balance.*", control_type="Text")

        if balance_check_btn.exists(timeout=1.5):

            Timings.after_click_wait = 0.05
            _try_click_button(win, "StartScanButton", timeout=0.5)
            
            code_EAN_array = [ean.strip() for ean in Code_EANList.split(";") if ean.strip()] if Code_EANList else []

            if not code_EAN_array:
                logger.log("❌ No valid EAN values found after parsing Code_EANList.", status="fail")
                logger.take_screenshot("No_Valid_EAN_Found")
                return

            for Code_EAN in code_EAN_array:
                scan_item(win, Code_EAN)

                # Handle any popup that appears during scanning:
                # collectable/bunch offer (PopupFrame + List1Button) OR item-not-found error
                _handle_scan_popups(win)

                _focus_win()

                # Always check SkipBaggingButton FIRST, regardless of PayButton state.
                # Some items (e.g. Lindt) need bagging confirmation even when other items
                # have already enabled PayButton. Skipping this leaves the item "pending"
                # and the SCO may drop it when the next item is scanned.
                if _is_button_enabled(win, "SkipBaggingButton", timeout=0.1):
                    _try_click_button(win, "SkipBaggingButton", timeout=0.1)
                    time.sleep(0.15)

                # Fast path: check cached PayButton FIRST. If enabled, skip popup
                # tree-walk entirely (single uninterruptible walks are the main
                # remaining cost on heavy WPF apps).
                pay_enabled = _is_button_enabled(win, "PayButton", timeout=0.03)

                if pay_enabled:
                    print(" PayButton is enabled immediately after scanning the item.")
                    # logger.log("✅ Payment button is enabled after scanning the item.", status="pass")
                else:
                    # _handle_continue_popup(win)
                    try:
                        timings.wait_until(
                            0.5,
                            0.05,
                            lambda: _is_button_enabled(win, "PayButton", timeout=0.02) or _is_button_enabled(win, "SkipBaggingButton", timeout=0.02)
                        )
                    except timings.TimeoutError:
                        pass

                    pay_enabled = _is_button_enabled(win, "PayButton", timeout=0.03)

                    if (not pay_enabled) and _is_button_enabled(win, "SkipBaggingButton", timeout=0.05):
                        _try_click_button(win, "SkipBaggingButton", timeout=0.05)
                        # logger.log("✅ Skip Bagging button is enabled after scanning the item.", status="pass")
                    elif (not pay_enabled) and _try_click_button(win, "AssistanceButton", timeout=0.08):

                        # Handle Approval prompt with Manager Credentials
                        alpha_num_pad = win.child_window(auto_id="InputTextBox", control_type="Edit")
                        if alpha_num_pad.exists(timeout=0.2):
                            alpha_num_pad.click_input()
                            alpha_num_pad.type_keys("ATMGR5{ENTER}", pause=0.05)
                            alpha_num_pad.click_input()
                            alpha_num_pad.type_keys("abcd1234{ENTER}", pause=0.05)
                    else:
                        logger.log("ℹ️ Skip Bagging and Assistance controls not available yet — item proceeding.", status="info")

                    pay_enabled = _is_button_enabled(win, "PayButton", timeout=0.03)

                if pay_enabled:
                    logger.log(f"✅ Added given '{Code_EAN}' item successfully.", status="pass")
                # else:
                #     logger.log(f"❌ Failed to add given '{Code_EAN}' item.", status="fail")
                #     logger.take_screenshot(f"Add_Item_Failed_{_screenshot_safe_name(Code_EAN)}")
        else:
            logger.log("❌ Balance check control is not visible; POS may not be in expected state.", status="fail")
            logger.take_screenshot("Balance_Check_Control_Not_Found")
            return

        desc_list, price_list = get_item_details(win)

        if not desc_list or not price_list:
            logger.log("❌ Basket extraction returned empty details or prices.", status="fail")
            logger.take_screenshot("Basket_Extraction_Empty")
            return

        if len(desc_list) != len(price_list):
            logger.log(
                f"❌ Basket data mismatch: {len(desc_list)} descriptions vs {len(price_list)} prices.",
                status="fail"
            )
            logger.take_screenshot("Basket_Data_Mismatch")
            return

        # logger.log("✅ Basket details extracted and validated.", status="pass")

        for article_desc, article_price in zip(desc_list, price_list):
            logger.log(
                f"✅ Article '{article_desc}' is captured with price: {article_price}.",
                status="pass"
            )

        global_instance.article_price = price_list if price_list else []

        item_name_list = ""
        item_price_list = ""

        for desc, price in zip(desc_list, price_list):
            item_name_list += desc + ";"
            item_price_list += price + ";"

        global_instance.article_name_list = item_name_list
        global_instance.article_price_list = item_price_list

        print("Item Descriptions:", desc_list)
        print("Item Prices:", price_list)

        global_instance.win = win

        # ensure_EFTSimulator_closed()

        # ensure_services_stopped(SERVICES_TO_STOP)


        # logger.log("✅ Proceeding to payment...", status="pass")
        # # Dismiss any "Do you wish to continue" popup that may be blocking PayButton.
        # _handle_continue_popup(win, timeout=0.2)

        # if not _try_click_button(win, "PayButton", timeout=1.0):
        #     logger.log("❌ PayButton not available; aborting payment step.", status="fail")
        #     logger.take_screenshot("PayButton_Not_Available")
        #     return

        # # Wait briefly for the payment screen's CustomSkip button to appear;
        # # keep dismissing the continue-popup if it shows up during the wait,
        # # and retry the Pay click once if needed.
        # def _payment_ready():
        #     _handle_continue_popup(win, timeout=0.05)
        #     return _resolve_wrapper(win, "CustomSkip", timeout=0.05) is not None

        # try:
        #     timings.wait_until(3.0, 0.1, _payment_ready)
        # except timings.TimeoutError:
        #     # Retry Pay once in case the first click was eaten by a popup.
        #     _try_click_button(win, "PayButton", timeout=0.5)
        #     try:
        #         timings.wait_until(3.0, 0.1, _payment_ready)
        #     except timings.TimeoutError:
        #         logger.log("❌ CustomSkip button not found; cannot scan card code.", status="fail")
        #         logger.take_screenshot("CustomSkip_Button_Not_Found")
        #         return

        # scan_item(win, card_code, label="Card number")
        # global_instance.is_loyaltycard_added = True
        # logger.log("✅ Card code scanned successfully.", status="pass")

    except Exception as e:
        logger.log(f"❌ An error occurred: {e}", status="fail")
        logger.take_screenshot("Add_Item_Exception")




