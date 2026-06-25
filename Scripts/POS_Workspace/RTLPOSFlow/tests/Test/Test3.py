import time
import re
import sys
import csv
from pathlib import Path

from pywinauto import Application, timings

# --- Setup for project root and imports ---
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Component.Read_csv import get_csv_value


# def extract_tendermode_balance_due():

title_regex = ".*R10PosClient.*"

win = None
app = None

print(f"Initializing connection to: {title_regex}")
try:
    app = Application(backend="uia").connect(title_re=title_regex, timeout=15)
    win = app.window(title_re=title_regex)
    win.set_focus()
    win.print_control_identifiers()
except Exception as e:
    print(f"❌ Initialization Error: {e}")

# reward_ctrl = win.child_window(title_re=f".*REWARDS SAVINGS.*", auto_id="tbTenderType", control_type="Text")
# reward_ctrl2 = win.child_window(title_re=f".*REWARDS SAVINGS.*", control_type="ListItem")
# # if reward_ctrl.exists(timeout=5):
# reward_ctrl_wrapper = reward_ctrl2.wrapper_object()
# # reward_amount = reward_ctrl.window_text().strip()
# # reward_amount_formatted = f"{abs(float(reward_amount)):.2f}"
# # print(f"✅ Reward is displayed on the POS with amount: {reward_amount}.")
# child = reward_ctrl_wrapper.children()
# print(f"Children count: {len(child)}")
# if child and len(child) > 1:
#     reward_amount = child[1].window_text().strip()
#     reward_amount_formatted = f"{abs(float(reward_amount)):.2f}"
# #     # global_instance.total_promotions_price += float(promo_price_formatted)
# #     # global_instance.promotion_price_list.append(promo_price_formatted)
# #     # global_instance.promotion_description_list.append(promo)
#     print(f"✅ Reward is displayed on the POS with amount: {reward_amount_formatted}.")
#     # else:
#     #     print(f"✅ Reward is displayed on the POS.")
# else:
#     print(f"❌ Reward not found on the POS.")



    # def get_balance_due():
    #     try:
    #         # 1. Find ALL "Balance Due:" labels in the tree
    #         labels = win.descendants(title="Balance Due:", control_type="Text")
    #         if not labels:
    #             return "Label Not Found"
            
    #         # 2. Use the LAST label in the tree (bypasses the hidden 0.00 ghost layer)
    #         active_label = labels[-1]
    #         label_rect = active_label.rectangle()

    #         # 3. Get all Custom controls
    #         all_customs = win.descendants(control_type="Custom")
            
    #         valid_amounts = []
            
    #         # 4. Filter by location
    #         for element in all_customs:
    #             rect = element.rectangle()
                
    #             is_to_the_right = rect.left > label_rect.right
    #             is_vertically_aligned = abs(rect.top - label_rect.top) < 30
                
    #             if is_to_the_right and is_vertically_aligned:
    #                 text = element.window_text()
    #                 if text and text.strip() != "":
    #                     # Clean the text to just numbers and decimals
    #                     clean_text = "".join(c for c in text if c.isdigit() or c == '.')
    #                     valid_amounts.append(clean_text)
                        
    #         # 5. Return the LAST valid amount found (the active layer)
    #         if valid_amounts:
    #             return valid_amounts[-1]
                
    #         return "Not Found"
    #     except Exception as e:
    #         return f"Error: {e}"

    # balance = get_balance_due()
    # print(f"✅ Extracted Active Amount: {balance}")




# # 1. Find the anchor (this returns a WindowSpecification)
# balance_spec = win.child_window(title="Balance Due:", control_type="Text")

# # 2. Get the actual wrapper object by calling .wrapper_object()
# balance_label = balance_spec.wrapper_object()

# # 3. Get its parent, then look through the parent's children
# parent_container = balance_label.parent()

# amount_val = None
# for sibling in parent_container.children():
#     # Look for the Custom control in the same container
#     if sibling.element_info.control_type == "Custom":
#         # Ensure it actually has text (to avoid blank custom containers)
#         text = sibling.window_text()
#         if text and text.strip():
#             amount_val = text
#             break

# print(f"✅ Extracted Amount: {amount_val}")


# def get_balance_due():
#     try:
#         # We find the label first
#         anchor = win.child_window(title="Balance Due:", control_type="Text")
        
#         # We look for the 'Custom' control that is a sibling of the anchor.
#         # Since the auto_id/title changes with the price, we use found_index=0 
#         # to get the first Custom control associated with that specific pane.
#         amount_element = win.child_window(control_type="Custom",  top_level_only=False, found_index=11)
        
#         # Better yet, search for the Custom control that has a numeric title
#         # which is located near the Balance Due text.
#         price = amount_element.window_text()
        
#         return price
#     except Exception as e:
#         return f"Error extracting price: {e}"

# balance = get_balance_due()
# print(f"✅ Extracted Balance Due: {balance}")

# balance_label = app.child_window(title="Balance Due:", control_type="Text")

# # 2. Use 'parent()' to move up and then find the Custom child
# # This is robust because even if the amount changes, the structure stays the same
# amount_val = balance_label.parent().child_window(control_type="Custom").window_text()

# print(f"The detected amount is: {amount_val}")

# text = app.child_window(auto_id="ReceiptViewID", control_type="Custom")
# print(f"Button Text: {text}")

# all_children = text.children()
# dynamic_balance = None

# # 2. Iterate through the children to find the static label
# for index, element in enumerate(all_children):
    
#     # Use .window_text() or .element_info.name to check the label
#     if element.window_text().strip() == "Balance Due:":
        
#         # 3. The dynamic value is the very next element in the list
#         value_element = all_children[index + 1]
        
#         # Extract the text from this custom element
#         dynamic_balance = value_element.window_text()
#         break

# print(f"Extracted Balance: {dynamic_balance}")


# promo = "Bonus Buy Amount Off"
# promo_ctrl = app.child_window(title_re=f".*{re.escape(promo)}.*", control_type="ListItem")
# if promo_ctrl.exists(timeout=5):
#     promo_ctrl_wrapper = promo_ctrl.wrapper_object()
#     child = promo_ctrl_wrapper.children()
#     if child and len(child) > 2:
#         promo_price = child[2].window_text().strip()
#         print(f"✅ Promotion '{promo}' is displayed on the POS with price: {abs(float(promo_price))}.")
#     else:
#         print(f"✅ Promotion '{promo}' is displayed on the POS.")
# else:
#     print(f"❌ Promotion '{promo}' not found on the POS.")