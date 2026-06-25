from pywinauto import Desktop

# Use Desktop to find the window by its AutomationId
app_window = Desktop(backend="uia").window(auto_id="GraphicCustomerDisplayID")

# Verify connection
app_window.draw_outline()

app_window.print_control_identifiers()

parent_container = app_window.child_window(auto_id="ReceiptViewIDCustomerDispaly", control_type="Custom")

# 2. Get all children of that specific container
all_children = parent_container.children()

# Based on your dump, the '16' is near the end. 
# You can find it by looking for the label and taking the next one.
for i, child in enumerate(all_children):
    if "Points Collected:" in child.window_text():
        # The value '16' is the very next child in the list
        points_value_element = all_children[i + 1]
        points = points_value_element.window_text()
        print(f"Found Points via Child Navigation: {points}")
        break