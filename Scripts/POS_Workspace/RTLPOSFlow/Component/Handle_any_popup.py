import time
import sys
from pathlib import Path
from pywinauto import Application, timings

# --- Setup for project root and imports ---
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Component.Read_csv import get_csv_value
from Component import global_instance
try:
    from Component.report import logger
except Exception:
    class _NoopLogger:
        def log(self, *a, **k): pass
        def save(self): pass
    logger = _NoopLogger()


DEFAULT_BUTTONS = ["Skip", "OK", "Ok", "Yes", "No", "Cancel", "Close"]
POS_TITLE_RE = ".*Retalix.Woolworths.Client.POS.Presentation.*"


def _connect_pos(title_re=POS_TITLE_RE, timeout=5):
    """Connect to the POS window and return (app, win) or (None, None)."""
    try:
        app = Application(backend="uia").connect(title_re=title_re, timeout=timeout)
        win = app.window(title_re=title_re)
        win.set_focus()
        return app, win
    except Exception as e:
        print(f"❌ Could not connect to POS window: {e}")
        return None, None


def handle_any_popup(button_names=None, title_re=POS_TITLE_RE, timeout=5, retries=1):
    """
    Try to find and click any of the supplied button names on the POS popup.

    - button_names: list of button labels to try (in order). Defaults to common ones.
    - title_re: regex for the POS window title.
    - timeout: seconds to wait for each button to exist.
    - retries: how many times to retry the whole scan.

    Returns the button name that was clicked, or None if nothing was clicked.
    """
    buttons = list(button_names) if button_names else list(DEFAULT_BUTTONS)

    for attempt in range(1, retries + 1):
        app, win = _connect_pos(title_re=title_re, timeout=timeout)
        if not win:
            time.sleep(1)
            continue

        for name in buttons:
            try:
                # Try common control id first, then fall back to plain title match
                ctrl = win.child_window(title=name, auto_id="MessageBoxCommandButtonTemplate", control_type="Button")
                if not ctrl.exists(timeout=timeout):
                    ctrl = win.child_window(title=name, control_type="Button")
                if ctrl.exists(timeout=timeout):
                    ctrl.click_input()
                    msg = f"✅ Clicked popup button: '{name}'"
                    print(msg)
                    try:
                        logger.log(msg, status="pass")
                    except Exception:
                        pass
                    return name
            except Exception:
                # try next button
                continue

        print(f"⚠️ Attempt {attempt}: No matching popup button found ({buttons}).")
        time.sleep(1)

    print("❌ No popup button matched after retries.")
    try:
        logger.log("No popup button matched.", status="fail")
    except Exception:
        pass
    return None


def handle_round_up_popup():
    """Original behavior: handle the Round-up popup (Skip)."""
    if float(global_instance.total_amount_salemode) % 1 != 0:
        print("⚠️ Total amount has a decimal component. Handling Round up action.")
        time.sleep(4)
        clicked = handle_any_popup(button_names=["Skip", "Cancel", "Close"], timeout=5, retries=2)
        return clicked is not None
    else:
        print("⚠️ Total amount does not have a decimal component. Skipping Round up action.")
        return True