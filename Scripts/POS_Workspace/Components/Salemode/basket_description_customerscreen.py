import time
import re
from pywinauto import Application

def get_top_right_item_details(win):
    """
    Finds and parses the item details from the top-right panel of the window.
    This version uses a more targeted approach based on the UI structure.
    """
    print("\n🔍 Reading Top-Right Item Details...")
    details = {
        "description": "N/A",
        "price": "N/A",
        "code": "N/A",
        "unit": "N/A"
    }

    try:
        # --- New Strategy: Locate specific text patterns and parse around them ---
        window_rect = win.rectangle()
        horizontal_midpoint = window_rect.left + (window_rect.width() / 2)

        # Get all static text controls on the right side of the window
        right_side_texts = []
        all_right_controls = []
        for control in win.descendants(): # Get all controls
            try:
                if control.rectangle().left > horizontal_midpoint:
                    all_right_controls.append(control)
                    text = control.window_text()
                    if text and text.strip():
                        right_side_texts.append(text.strip())
            except Exception:
                continue

        if not right_side_texts:
            print("❌ Could not find any text controls in the top-right area.")
            return details
            
        print(f"Found text fields to parse on the right: {right_side_texts}")

        # --- More precise parsing logic based on the output provided ---
        try:
            # Find the item code
            if 'Code' in right_side_texts:
                code_index = right_side_texts.index('Code')
                if code_index + 1 < len(right_side_texts):
                    details['code'] = right_side_texts[code_index + 1]

            # Find the unit
            if 'Unit' in right_side_texts:
                unit_index = right_side_texts.index('Unit')
                if unit_index > 0:
                    details['unit'] = f"{right_side_texts[unit_index - 1]} {right_side_texts[unit_index]}"

            # --- FIX: Robust Price Detection ---
            # Search all controls on the right for a value that looks like a price.
            for control in all_right_controls:
                try:
                    text = control.window_text()
                    # Find the first text that looks like a price.
                    if text and re.fullmatch(r'\$?\d+\.\d+', text.strip()):
                         # From the screenshot, there are two prices. We want the first one.
                        if details['price'] == 'N/A':
                            details['price'] = text.strip()
                except Exception:
                    continue
            
            # --- FIX: Smarter Description Detection ---
            # The description is the longest text that is not a price, code, or other keyword.
            potential_descriptions = []
            for text in right_side_texts:
                # Check if the text is NOT any of the other details we've found
                is_other_detail = (text == details['price'] or
                                   text == details['code'] or
                                   text in details['unit'] or
                                   'retalix.client.pos' in text.lower() or # Ignore internal class names
                                   text.lower() in ['code', 'unit', '1 total in basket', 'promotions', 'coupons', 'member card'] or
                                   re.fullmatch(r'[\d.]+', text)) # ignore simple numbers
                
                if not is_other_detail:
                    potential_descriptions.append(text)
            
            if potential_descriptions:
                # The longest remaining text is the description
                details['description'] = max(potential_descriptions, key=len)


        except Exception as e:
            print(f"Could not fully parse details, but extracted what was possible. Error: {e}")


        print("\n✅ Successfully Parsed Details:")
        print(f"  - Description: {details['description']}")
        print(f"  - Price:       {details['price']}")
        print(f"  - Code:        {details['code']}")
        print(f"  - Unit:        {details['unit']}")
        return details

    except Exception as e:
        print(f"❌ An error occurred while getting top-right details: {e}")
        return details


def get_basket_and_balance_due():
    """
    Connects to the POS application, reads the basket items from the left,
    and reads the highlighted item's details from the top-right.
    """
    try:
        app_path = r"C:\Retalix\StoreServices\POSClient\Retalix.Client.POS.Shell.exe"
        app = Application(backend="uia").connect(path=app_path)
        win = app.window(auto_id="GraphicCustomerDisplayID")
        win.set_focus()
        print("✅ POS window found and focused.")
    except Exception as e:
        print(f"❌ Could not connect or focus POS window: {e}")
        return

    # --- Get Basket Items (Left Side) ---
    print("\n🛒 Reading Basket Items...")
    basket_controls = win.descendants(control_type="List")
    if not basket_controls:
        basket_controls = win.descendants(control_type="ListView")

    if basket_controls:
        basket = basket_controls[0]
        items = basket.descendants(control_type="ListItem")
        print(f"Found {len(items)} item(s) in basket:")
        
        for idx, item in enumerate(items, 1):
            # Get all child controls to find all pieces of text
            all_children = item.children()
            child_texts = [child.window_text() for child in all_children if child.window_text()]

            name = "N/A"
            quantity = "N/A"
            price_str = "N/A"
            price = None

            # FIX: More robust parsing for basket items
            # The name is usually the longest text that isn't a number
            potential_names = [t for t in child_texts if not t.isdigit() and not re.fullmatch(r'\$?\d+\.\d+', t)]
            if potential_names:
                name = max(potential_names, key=len)

            # The quantity is usually a single digit
            quantities = [t for t in child_texts if t.isdigit()]
            if len(quantities) > 1 and quantities[0] == '0':
                # If the first digit is '0', it's likely a status, so take the next one
                quantity = quantities[1]
            elif quantities:
                quantity = quantities[0]
            
            # The price is the text that matches a currency format
            prices = [t for t in child_texts if re.fullmatch(r'\$?\d+\.\d+', t)]
            if prices:
                price_str = prices[0]

            try:
                price_val = float(re.sub(r'[^\d.-]', '', price_str))
                price = price_val
            except (ValueError, AttributeError, TypeError):
                pass
            
            print(f"  {idx}. Name: {name}, Quantity: {quantity}, Amount: {price if price is not None else 'N/A'}")

        # Get final totals from UI
        try:
            # Using more specific automation_id if available
            balance_due = win.child_window(automation_id="BalanceDueAmount").window_text()
            savings = win.child_window(automation_id="TotalSavingsAmount").window_text()
            print(f"\nBalance Due: {balance_due}")
            print(f"Your Savings: {savings}")
        except Exception:
            print("\nCould not find Balance Due or Savings fields automatically.")

    else:
        print("❌ Could not find basket/list control on left side.")

    # --- Call the function to get top-right details ---
    get_top_right_item_details(win)


if __name__ == "__main__":
    get_basket_and_balance_due()
