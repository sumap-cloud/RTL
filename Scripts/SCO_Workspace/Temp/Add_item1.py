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

    _handle_continue_popup(win)
        

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
        print("✅ Extracted item count matches the ReceiptItemCount!")
    else:
        print(f"❌ Warning: Extracted {len(item_descriptions)} items, but expected {expected_count}.")

    print(f"{len(item_descriptions)} items in the basket: and their prices: {item_prices}")

    return item_descriptions, item_prices

def add_item(Code_EANList, card_code):

    try:
        app = Application(backend="uia").connect(title_re=".*NCR NEXTGENUI.*")
        win = app.window(title_re=".*NCR NEXTGENUI.*")
        global_instance.app = app
        global_instance.win = win

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
            
            code_EAN_array =  Code_EANList.split(";") if Code_EANList else []

            for Code_EAN in code_EAN_array:
                scan_item(win, Code_EAN)

                _focus_win()

                # Fast path: check cached PayButton FIRST. If enabled, skip popup
                # tree-walk entirely (single uninterruptible walks are the main
                # remaining cost on heavy WPF apps).
                pay_enabled = _is_button_enabled(win, "PayButton", timeout=0.03)

                if pay_enabled:
                    print("Payment button is enabled after scanning the item.")
                else:
                    _handle_continue_popup(win)
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
                        print("Skip Bagging button is enabled after scanning the item.")
                    elif (not pay_enabled) and _try_click_button(win, "AssistanceButton", timeout=0.08):

                        # Handle Approval prompt with Manager Credentials
                        alpha_num_pad = win.child_window(auto_id="InputTextBox", control_type="Edit")
                        if alpha_num_pad.exists(timeout=0.2):
                            alpha_num_pad.click_input()
                            alpha_num_pad.type_keys("ATMGR5{ENTER}", pause=0.05)
                            alpha_num_pad.click_input()
                            alpha_num_pad.type_keys("abcd1234{ENTER}", pause=0.05)
                    else:
                        print("Skip Bagging and Assistance controls are not available yet.")

                    pay_enabled = _is_button_enabled(win, "PayButton", timeout=0.03)

                if pay_enabled:
                    print(f"Added given {Code_EAN} item successfully.")
                else:
                    print(f"Failed to add given {Code_EAN} item.")

        desc_list, price_list = get_item_details(win)

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

        ensure_EFTSimulator_closed()

        ensure_services_stopped(SERVICES_TO_STOP)


        print("Proceeding to payment...")
        # Dismiss any "Do you wish to continue" popup that may be blocking PayButton.
        _handle_continue_popup(win, timeout=0.2)

        if not _try_click_button(win, "PayButton", timeout=1.0):
            print("PayButton not available; aborting payment step.")
            return

        # Wait briefly for the payment screen's CustomSkip button to appear;
        # keep dismissing the continue-popup if it shows up during the wait,
        # and retry the Pay click once if needed.
        def _payment_ready():
            _handle_continue_popup(win, timeout=0.05)
            return _resolve_wrapper(win, "CustomSkip", timeout=0.05) is not None

        try:
            timings.wait_until(3.0, 0.1, _payment_ready)
        except timings.TimeoutError:
            # Retry Pay once in case the first click was eaten by a popup.
            _try_click_button(win, "PayButton", timeout=0.5)
            try:
                timings.wait_until(3.0, 0.1, _payment_ready)
            except timings.TimeoutError:
                print("CustomSkip button not found; cannot scan card code.")
                return

        scan_item(win, card_code, label="Card number")

    except Exception as e:
        print(f"An error occurred: {e}")




