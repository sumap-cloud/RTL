from pywinauto import Application
from pywinauto.findwindows import ElementNotFoundError
from pywinauto.timings import TimeoutError
import time

app = None
win = None
# try:
#     app = Application(backend="uia").connect(title_re=".*R10PosClient.*")
#     win = app.window(title_re=".*R10PosClient.*")
    
#     print("✅ Successfully connected to the application.")
# except ElementNotFoundError:
#     print("❌ Application 'R10PosClient' not found. Please make sure it is running.")


# win.set_focus()
# win.print_control_identifiers()
# win.child_window(title="No Sale", control_type="Button", found_index=0).click_input()
# item_input = win.child_window(auto_id="InputProductNumber", control_type="Edit")
# item_input.type_keys("9300624016571{ENTER}")

try:
    app = Application(backend="uia").connect(title_re=".*Retalix.Woolworths.Client.POS.Presentation.*")
    win = app.window(title_re=".*Retalix.Woolworths.Client.POS.Presentation.*")
    # win.set_focus()
        
except Exception as e:
    print(f"❌ Could not connect to loyalty popup: {e}")


redeem_amount_popup = win.child_window(title_re=".*Current Rewards Balance:.*", auto_id="MessageTextBox", control_type="Edit")
redeem_amount = '10'


win.set_focus()
roundup_popup = win.child_window(title_re=".*Round up to.*", auto_id="SuggestedAmountButton", control_type="Button")
balance_msg = win.child_window(title="Balance Due: $37.50", auto_id="BalanceDueText", control_type="Edit")
if roundup_popup.exists(timeout=5) and balance_msg.exists(timeout=5):
    print(f"✅ Round up popup detected with balance message: '{balance_msg.window_text()}'.")
    win.child_window(title="Skip", auto_id="MessageBoxCommandButtonTemplate", control_type="Button").click_input()
    print("✅ Clicked on Round up button.")
else:
    print("❌ Round up popup or balance message not detected.")

# if redeem_amount_popup.exists(timeout=5):
#     if redeem_amount == None:
#         print("⚠️ No redeem amount specified. Skipping redeem points action.")
#         # return False
#     else:
#         enter_amount = win.child_window(auto_id="InputProductNumber", control_type="Edit")
#         enter_amount.click_input()
#         enter_amount.type_keys(redeem_amount)
#         enter_amount.click_input()
#         # win.child_window(title="Redeem", auto_id="MessageBoxCommandButtonTemplate", control_type="Button").click_input()
#         print(f"✅ Clicked on Current Rewards Balance popup.")
# else:
    # print(f"❌ Current Rewards Balance popup not detected.")

# popup_title = win.child_window(title="Do you want me to apply it now?", auto_id="MessageTextBox", control_type="Edit")
# if popup_title.exists(timeout=5):
#     print(f"✅ Choice offer popup detected: '{popup_title.window_text()}' offered.")

#     offer_btn = win.child_window(title_re=".*Market Day Mobile 10 percent off.*", auto_id="button", control_type="Button")
#     if offer_btn.exists(timeout=5):
#         # offer_btn.click_input()
#         print(f"✅ Redeemed choice offer 'Market Day Mobile 10 percent off'.")
#     else:
#         print(f"❌ Choice offer button 'Market Day Mobile 10 percent off' not found.")

# else:
#     print("❌ Choice offer popup not detected.")
# win.print_control_identifiers()
