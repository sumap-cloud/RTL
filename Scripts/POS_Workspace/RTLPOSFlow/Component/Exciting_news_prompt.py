import time
import sys
from pathlib import Path
from pywinauto import Application

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Component.Read_csv import get_csv_value
from Component import global_instance
from Component.report import logger

POS_TITLE_RE = ".*Retalix.Woolworths.Client.POS.Presentation.*"


def handle_exciting_news_prompt(banner=None, TC_ID=None, Iteration=None,
                                data_file="SaleData.csv",
                                action="Use now",
                                timeout=5):
    """
    Acknowledge the "exciting news" / Instant-Win prompt that may appear after
    a loyalty card scan.

    - If banner/TC_ID/Iteration provided, reads expected prompt text from CSV
      column 'Instant_win_offer' (format: "<message>_<button>" optional).
    - `action` is used as fallback button title when CSV is not provided or
      doesn't contain a button override. Common values: "Use now",
      "Save for later", "OK".

    Returns True if a button was clicked, False otherwise.
    """
    expected_msg = None
    button_title = action

    if banner and TC_ID and Iteration is not None:
        parent_path = Path(__file__).parent.parent
        file_path = parent_path / 'resources' / data_file
        raw = get_csv_value(file_path, banner, TC_ID, Iteration, 'Instant_win_offer')
        if raw and raw not in ("No matching record found.", "Error: File not found."):
            if '_' in raw:
                expected_msg, button_title = raw.split('_', 1)
            else:
                expected_msg = raw

    try:
        time.sleep(2)
        app = Application(backend="uia").connect(title_re=POS_TITLE_RE, timeout=timeout)
        win = app.window(title_re=POS_TITLE_RE)
        win.set_focus()
    except Exception as e:
        msg = f"⚠️ Exciting-news prompt window not present: {e}"
        print(msg)
        logger.log(msg, status="info")
        return False

    msg_ctrl = win.child_window(auto_id="GiftCardInstructions", control_type="Text")
    if not msg_ctrl.exists(timeout=timeout):
        msg_ctrl = win.child_window(auto_id="MessageTextBox", control_type="Edit")

    if not msg_ctrl.exists(timeout=timeout):
        print("⚠️ Exciting-news / Instant-Win prompt not detected. Skipping.")
        logger.log("⚠️ Exciting-news / Instant-Win prompt not detected.", status="info")
        return False

    try:
        actual = msg_ctrl.window_text().strip()
    except Exception:
        actual = ""

    print(f"🔔 Exciting-news prompt detected: '{actual}'")
    logger.log(f"🔔 Exciting-news prompt detected: '{actual}'", status="pass")

    if expected_msg:
        clean_actual = " ".join(actual.replace('\n', ' ').split())
        clean_expected = " ".join(expected_msg.replace('\n', ' ').split())
        if clean_actual != clean_expected:
            warn = (f"⚠️ Exciting-news prompt text mismatch.\n"
                    f"   expected: '{clean_expected}'\n"
                    f"   actual:   '{clean_actual}'")
            print(warn)
            logger.log(warn, status="fail")

    for candidate in (button_title, "OK", "Use now", "Save for later", "Close"):
        if not candidate:
            continue
        btn = win.child_window(title=candidate, control_type="Button")
        if not btn.exists(timeout=2):
            btn = win.child_window(title=candidate, control_type="Text")
        if btn.exists(timeout=2):
            try:
                btn.click_input()
                print(f"✅ Acknowledged exciting-news prompt by clicking '{candidate}'.")
                logger.log(f"✅ Acknowledged exciting-news prompt by clicking '{candidate}'.", status="pass")
                global_instance.instant_win_acknowledged = True
                return True
            except Exception as e:
                print(f"⚠️ Click on '{candidate}' failed: {e}")
                continue

    print("❌ Could not find any acknowledgement button on the exciting-news prompt.")
    logger.log("❌ Could not acknowledge the exciting-news prompt.", status="fail")
    logger.take_screenshot("Exciting_News_Prompt_Acknowledge_Failed")
    return False
