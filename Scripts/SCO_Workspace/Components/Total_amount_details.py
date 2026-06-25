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


def get_total_amount_salemode():

    app = global_instance.app
    win = global_instance.win

    try:
        total_amount_element = win.child_window(auto_id="PayAmountValue", control_type="Text")
        total_amount = total_amount_element.window_text()
        formatted_total_amount = re.sub(r'[^\d\.\-]', '', total_amount)
        print(f"💰 Total Amount: ${formatted_total_amount}")
    except Exception as e:
        print(f"❌ Could not read Total Amount: {e}")
        formatted_total_amount = None

    global_instance.total_amount_salemode = formatted_total_amount
    return formatted_total_amount

def get_total_amount_tendermode():

    app = global_instance.app
    win = global_instance.win

    try:
        total_amount_element = win.child_window(auto_id="TotalAmountValue", control_type="Text")
        total_amount = total_amount_element.window_text()
        formatted_total_amount = re.sub(r'[^\d\.\-]', '', total_amount)
        print(f"💰 Total Amount: ${formatted_total_amount}")
    except Exception as e:
        print(f"❌ Could not read Total Amount: {e}")
        formatted_total_amount = None

    global_instance.total_amount_tendermode = formatted_total_amount
    return formatted_total_amount

def get_total_balancedue_tendermode():

    app = global_instance.app
    win = global_instance.win

    try:
        total_balancedue_element = win.child_window(auto_id="DueAmountValue", control_type="Text")
        total_balancedue = total_balancedue_element.window_text()
        formatted_balancedue = re.sub(r'[^\d\.\-]', '', total_balancedue)
        # print(f"💰 Total Balance Due (raw): {total_balancedue}, (formatted): {formatted_balancedue}")

        print(f"💰 Total Balance Due: ${formatted_balancedue}")
    except Exception as e:
        print(f"❌ Could not read Total Balance Due: {e}")
        formatted_balancedue = None

    global_instance.total_balancedue_tendermode = formatted_balancedue
    return total_balancedue

if __name__ == "__main__":

    try:
        app = Application(backend="uia").connect(title_re=".*NCR NEXTGENUI.*")
        win = app.window(title_re=".*NCR NEXTGENUI.*")
        global_instance.app = app
        global_instance.win = win
        print("✅ Connected to NCR NEXTGENUI window.")
        total_amount = get_total_amount_tendermode()
        print(f"Total Amount at Tender Mode: {total_amount}")
        total_balancedue = get_total_balancedue_tendermode()
        print(f"Total Balance Due at Tender Mode: {total_balancedue}")
    except Exception as e:
        print(f"❌ Could not connect to NCR NEXTGENUI window: {e}")
