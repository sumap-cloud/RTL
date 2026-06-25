"""
Login_POS.py
------------
Connects to the NCR NEXTGENUI (SCO) application window and verifies the POS
is in the idle/ready state before a test run begins.

For SCO, there is no credential-based login — the POS is already running and
waiting for a customer to start a session. This component:
  1. Resets shared global state.
  2. Connects to the NCR NEXTGENUI window.
  3. Verifies the SCO is in the idle state (StartScanButton or
     Gift Card/Store Credit Balance element is visible).
  4. Stores app/win handles in global_instance for downstream components.
"""

import sys
import ctypes
import win32gui
from datetime import datetime
from pathlib import Path
from pywinauto.timings import Timings
from pywinauto import Application

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components import global_instance
from Components.report import logger

_SCO_TITLE_RE = ".*NCR NEXTGENUI.*"

_user32 = ctypes.windll.user32
_VK_MENU = 0x12
_KEYEVENTF_KEYUP = 0x0002


def _focus_window(hwnd):
    """Best-effort window focus using Alt-key trick to bypass Windows focus stealing."""
    if not hwnd:
        return
    try:
        if win32gui.GetForegroundWindow() == hwnd:
            return
        _user32.keybd_event(_VK_MENU, 0, 0, 0)
        _user32.keybd_event(_VK_MENU, 0, _KEYEVENTF_KEYUP, 0)
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        pass


def login_pos():
    """
    Connect to the SCO application and verify it is in the idle/ready state.

    Returns:
        bool: True if connection and state verification succeeded, False otherwise.
    """
    global_instance.reset_state()

    try:
        app = Application(backend="uia").connect(title_re=_SCO_TITLE_RE, timeout=10)
        win = app.window(title_re=_SCO_TITLE_RE)
        logger.log("✅ Connected to NCR NEXTGENUI window.", status="pass")
    except Exception as e:
        logger.log(f"❌ Could not connect to NCR NEXTGENUI window: {e}", status="fail")
        logger.take_screenshot("Login_POS_Connection_Failed")
        return False

    global_instance.app = app
    global_instance.win = win

    # Attempt to bring window to foreground.
    try:
        hwnd = win.wrapper_object().handle
        _focus_window(hwnd)
    except Exception:
        try:
            win.set_focus()
        except Exception:
            pass

    # Verify the SCO is in idle/ready state.
    # The idle screen exposes either the StartScanButton or the
    # "Gift Card/Store Credit Balance" text element (welcome banner).
    idle_indicators = [
        ("auto_id", "StartScanButton", "Button"),
        ("title_re", ".*Gift Card/Store Credit Balance.*", "Text"),
        ("title_re", ".*Start.*", "Button"),
    ]

    pос_ready = False
    for search_type, value, ctrl_type in idle_indicators:
        try:
            if search_type == "auto_id":
                elem = win.child_window(auto_id=value, control_type=ctrl_type)
            else:
                elem = win.child_window(title_re=value, control_type=ctrl_type)

            if elem.exists(timeout=3):
                pос_ready = True
                logger.log(f"✅ SCO is in idle/ready state.", status="pass")
                break
        except Exception:
            continue

    if not pос_ready:
        logger.log(
            "❌ SCO does not appear to be in idle/ready state. "
            "Verify the application is on the welcome/home screen.",
            status="fail"
        )
        logger.take_screenshot("Login_POS_SCO_Not_Ready")
        return False

    # Record EE log start time as early as possible so subsequent loyalty
    # card scans (which trigger validate / wallet-open calls in EagleEye
    # BEFORE complete_transaction runs) are within the search window.
    # Complete_transaction respects this value and will not overwrite it.
    global_instance.ee_log_start_time = datetime.now()

    return True
