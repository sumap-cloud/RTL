import ctypes
import time

import win32gui
from pywinauto import Application

_user32 = ctypes.windll.user32
_VK_MENU = 0x12
_KEYEVENTF_KEYUP = 0x0002

_scanner_win = None
_scanner_hwnd = None
_scan_type_control = None
_tag_data_control = None
_code128_ready = False


def _get_scanner_window():
    global _scanner_win, _scanner_hwnd
    if _scanner_win is None:
        app = Application(backend="uia").connect(title_re=".*Scanner.*Emulator_Scanner.*")
        _scanner_win = app.window(title_re=".*Scanner.*Emulator_Scanner.*")
        try:
            _scanner_hwnd = _scanner_win.wrapper_object().handle
        except Exception:
            _scanner_hwnd = None
    return _scanner_win


def _fast_focus(hwnd, fallback_spec=None):
    """Reliable fast focus using Alt-key trick to bypass Windows focus
    stealing prevention. Falls back to wrapper.set_focus() on failure."""
    if hwnd:
        try:
            if win32gui.GetForegroundWindow() == hwnd:
                return
            # Alt press+release tricks Windows into allowing the focus change
            _user32.keybd_event(_VK_MENU, 0, 0, 0)
            _user32.keybd_event(_VK_MENU, 0, _KEYEVENTF_KEYUP, 0)
            win32gui.SetForegroundWindow(hwnd)
            if win32gui.GetForegroundWindow() == hwnd:
                return
        except Exception:
            pass
    if fallback_spec is not None:
        try:
            fallback_spec.set_focus()
        except Exception:
            pass


def _get_scanner_controls(win):
    global _scan_type_control, _tag_data_control
    if _scan_type_control is None or _tag_data_control is None:
        # Resolve to actual wrappers so subsequent calls don't re-walk the tree.
        st_spec = win.child_window(auto_id="DropDown", control_type="Button", found_index=0)
        td_spec = win.child_window(auto_id="DropDown", control_type="Button", found_index=1)
        _scan_type_control = st_spec.wrapper_object()
        _tag_data_control = td_spec.wrapper_object()
    return _scan_type_control, _tag_data_control


def _scan_type_value(scan_type):
    """Return the currently SELECTED symbology label.

    `scan_type` is the dropdown-arrow Button (auto_id='DropDown') inside a
    WPF ComboBox; its own window_text() is the literal word 'Open' (the
    action label), NOT the selected value. To read the selected value we
    walk up to the parent ComboBox and inspect it / its text children.
    """
    try:
        parent = scan_type.parent()
    except Exception:
        return ""

    # 1. If parent exposes ComboBox semantics, selected_text() works.
    for attr in ("selected_text", "selected_item_text"):
        fn = getattr(parent, attr, None)
        if callable(fn):
            try:
                val = fn()
                if val:
                    return val
            except Exception:
                pass

    # 2. Many WPF combos show the selection as the parent's own name.
    try:
        txt = parent.window_text()
        # Avoid returning generic container names.
        if txt and txt not in ("Open", "DropDown"):
            return txt
    except Exception:
        pass

    # 3. Last resort: find a Text/Edit child of the parent that holds it.
    for ctype in ("Text", "Edit"):
        try:
            for child in parent.children(control_type=ctype):
                t = child.window_text()
                if t:
                    return t
        except Exception:
            continue

    return ""


def _fast_click(control):
    try:
        control.click()
    except Exception:
        control.click_input()


def _handle_scanner_popup(app_window, timeout=0.03):
    """Single-walk popup handler: look directly for the Yes_Button."""
    yes_spec = app_window.child_window(auto_id="Yes_Button", control_type="Button")
    if yes_spec.exists(timeout=timeout):
        try:
            _fast_click(yes_spec.wrapper_object())
            return True
        except Exception:
            return False
    return False


def _handle_scanner_popup_retry(app_window, attempts=3, interval=0.03):
    """Handle delayed popup appearance before sending scanner EAN input.

    Fast-fail: if first check finds no popup, exit immediately on next miss.
    """
    for i in range(attempts):
        if _handle_scanner_popup(app_window, timeout=0.02):
            return True
        if i < attempts - 1:
            time.sleep(interval)
    return False


def _select_code128(win, scan_type):
    """Reliably select the 'Code 128' symbology even when another symbology
    is currently selected.

    The scanner emulator's symbology dropdown is a WPF ComboBox exposed as
    a Button. Selection by typing only works if:
      * the dropdown has keyboard focus, AND
      * the full string is sent fast enough (no per-key pause) so WPF's
        incremental search treats it as one token instead of jumping on
        each first letter.
    """
    if _scan_type_value(scan_type) == "Code 128":
        return True

    # 1. Give the dropdown keyboard focus and open it.
    try:
        scan_type.set_focus()
    except Exception:
        pass
    try:
        scan_type.click_input()
    except Exception:
        try:
            scan_type.click()
        except Exception:
            pass

    # 2. Type the full symbology name with no per-key delay, then ENTER.
    #    pause=0.0 is critical -- any delay and WPF resets the search
    #    buffer between keystrokes and you end up on 'Codabar' / 'Code 11'.
    for _ in range(2):
        try:
            scan_type.type_keys("Code 128", pause=0.0,
                                set_foreground=False)
        except Exception:
            pass
        if _scan_type_value(scan_type) == "Code 128":
            return True

    # 3. Last resort: close any open dropdown and report failure.
    try:
        scan_type.type_keys("{ESC}", pause=0.0, set_foreground=False)
    except Exception:
        pass
    return False


def scan_item(app1, Code_EAN, label="EAN code"):
    global _code128_ready

    win = _get_scanner_window()
    scan_type, tag_data = _get_scanner_controls(win)

    _fast_focus(_scanner_hwnd, fallback_spec=win)

    # Re-validate the cached "ready" flag against the live UI: if the user
    # (or a previous test) changed symbology after the first scan, the
    # cache lies. Read the SELECTED value, not the dropdown-arrow button's
    # accessible name (which is the literal word 'Open').
    if _code128_ready and _scan_type_value(scan_type) != "Code 128":
        _code128_ready = False

    if not _code128_ready:
        if _select_code128(win, scan_type):
            print("Selected 'Code 128' Symbology.")
            _code128_ready = True
        else:
            print(f"⚠️ Failed to select 'Code 128' Symbology "
                  f"(current: '{_scan_type_value(scan_type)}').")

    # Move keyboard focus to the EAN text field so type_keys lands there,
    # not in the symbology dropdown we may have just typed into.
    try:
        tag_data.set_focus()
    except Exception:
        try:
            tag_data.click_input()
        except Exception:
            pass

    # Skip app1 focus + popup retry here -- add_item handles popup after scan.
    # Those two calls cost ~12s per item on heavy WPF apps.

    if tag_data.window_text() != Code_EAN:
        tag_data.type_keys(Code_EAN + "{ENTER}", pause=0.01, set_foreground=False)
    else:
        tag_data.type_keys("{ENTER}", pause=0.01, set_foreground=False)
    print(f"Entered {label}: {Code_EAN}")

