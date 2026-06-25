# --- Setup for project root and imports ---
import sys
from pathlib import Path
from pywinauto import Application

current_file_path = Path(__file__).resolve()
project_root = Path(__file__).resolve().parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Component.Login_to_nosale import initialize_and_login
from Component.Add_Item import add_items_to_basket
from Component.Add_loyalty_card import add_card
from Component.Redeem_collectable_offer import redeem_collectable_offer
from Reusable.Redeem_choice import redeem_choice_offer
from Component.Reedem_point import redeem_point
from Reusable.Promotion_details import promotion_details
from Component.Tender_select import tender_select
from Component.Transaction_details_EE_Logs import update_transaction_details
from Component.Read_csv import get_csv_value
# from Scripts.POS_Workspace.RTLPOSFlow.Component.report import logger

try:
    from Component.report import logger
except Exception:
    class _NoopLogger:
        def log(self, *a, **k):
            pass
        def save(self):
            pass
    logger = _NoopLogger()


# logger = HTMLTestLogger("C:\\GitHub\\R10_Pywin_Automation\\results.html")

DATA_FILE = "SaleData.csv"
RESOURCE_DIR = current_file_path.parent.parent / "resources"

parent_path = Path(__file__).parent.parent
file_path=parent_path /'resources'/ 'SaleData.csv'
file_path2=parent_path /'resources'/ 'TransactionData.csv'


SCRIPT_TC_ID = Path(__file__).stem 
tc_id = "TC_001_RecentTransactionValidation1"

logger.set_tc_id(tc_id)

if __name__ == "__main__":
    try:
        # login_instance = Login()
        app = initialize_and_login("SM", tc_id, 1)
        logger.log("✅ Logged into NOSALE successfully.", status="pass")

        # additem_instance = AddItem()
        app = add_items_to_basket(app, "SM", tc_id, 1)

        if add_card("SM", tc_id, 1):
            print("✅ Loyalty card added successfully.")

        # reedem_collectable_offer("SM", tc_id, 1)

        choice_offer = get_csv_value(file_path, "SM", tc_id, 1, 'Choice_offer')

        redeem_choice_offer(choice_offer)

        # reedem_collectable_offer("SM", tc_id, 1)

        # reedem_choice_offer("SM", tc_id, 1)

        redeem_point("SM", tc_id, 1)

        promotion_details("SM", tc_id, 1)

        tender_select("Cash", "SM", tc_id, 1)

        update_transaction_details("SM", tc_id, 1)

    except Exception as e:
        # logger.log(f"Error: {e}", status="fail")
        print(f"❌ An error occurred during the test execution: {e}")

    finally:
        logger.save()
        print(f"Report saved to {logger.report_path}")