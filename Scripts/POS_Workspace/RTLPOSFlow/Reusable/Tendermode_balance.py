from operator import index
import time
import re
import sys
import csv
from pathlib import Path

from pywinauto import Application, timings, Desktop

# --- Setup for project root and imports ---
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Component.Read_csv import get_csv_value
from Component import global_instance

def get_balance_due():

    app_window = None

    try:
        app_window = Desktop(backend="uia").window(auto_id="GraphicCustomerDisplayID")

        # Verify connection
        app_window.draw_outline()

        parent_container = app_window.child_window(auto_id="ReceiptViewIDCustomerDispaly", control_type="Custom")

        # 2. Get all children of that specific container
        all_children = parent_container.children()
        amount = 0.0
        # Based on your dump, the '16' is near the end. 
        # You can find it by looking for the label and taking the next one.
        for i, child in enumerate(all_children):
            if "Balance Due:" in child.window_text():
                # The value '16' is the very next child in the list
                amount_value_element = all_children[i + 1]
                amount = amount_value_element.window_text()
                break
        # global_instance.total_amount_tendermode = amount
        

        return amount
    
    except Exception as e:
        print(f"❌ Could not connect to Customer Display: {e}")
        return "Total amount not found."

if __name__ == "__main__":
    # get_balance_due(...)
    balance = get_balance_due()
    print(f"✅ Extracted Active Amount: {balance}")
    global_instance.total_amount_tendermode = balance

