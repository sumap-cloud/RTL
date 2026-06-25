# --- Setup for project root and imports ---
import sys
import allure
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = Path(__file__).resolve().parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Component.Login_to_nosale import initialize_and_login
from Component.Add_Item import add_items_to_basket
from Component.Add_loyalty_card import add_card
from Component.Redeem_collectable_offer import reedem_collectable_offer
from Reusable.Redeem_choice import reedem_choice_offer
from Component.Reedem_point import redeem_point
from Component.Promotion_details import promotion_details
from Component.Tender_select import tender_select
from Component.Transaction_details_EE_Logs import update_transaction_details
from Component.Read_csv import get_csv_value
import allure

DATA_FILE = "SaleData.csv"
RESOURCE_DIR = current_file_path.parent.parent / "resources"

parent_path = Path(__file__).parent.parent
file_path=parent_path /'resources'/ 'SaleData.csv'
file_path2=parent_path /'resources'/ 'TransactionData.csv'


SCRIPT_TC_ID = Path(__file__).stem 
tc_id = "TC_001_RecentTransactionValidation1"

# import allure

@allure.title("Full POS Transaction Flow")
def test_pos_transaction_flow():
    app = initialize_and_login("SM", tc_id, 1)
    with allure.step("Add items to basket"):
        app = add_items_to_basket(app, "SM", tc_id, 1)
    with allure.step("Add loyalty card"):
        add_card("SM", tc_id, 1)
    with allure.step("Redeem collectable offer"):
        reedem_collectable_offer("SM", tc_id, 1)
    with allure.step("Redeem choice offer"):
        choice_offer = get_csv_value(file_path, "SM", tc_id, 1, 'Choice_Offer')
        reedem_choice_offer(choice_offer)
    with allure.step("Redeem collectable offer again"):
        reedem_collectable_offer("SM", tc_id, 1)
    with allure.step("Redeem point"):
        redeem_point("SM", tc_id, 1)
    with allure.step("Promotion details"):
        promotion_details("SM", tc_id, 1)
    with allure.step("Tender select"):
        tender_select("Cash", "SM", tc_id, 1)
    with allure.step("Update transaction details"):
        update_transaction_details("SM", tc_id, 1)