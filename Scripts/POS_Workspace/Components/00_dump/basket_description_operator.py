import time
import re
from pywinauto import Application

def parse_item_details(details_container):
    """
    A universal function to parse details once a specific container pane is found.
    This is called by both the customer and operator screen logic.
    """
    details = {"description": "N/A", "price": "N/A", "code": "N/A", "unit": "N/A"}
    
    try:
        all_texts = [child.window_text().strip() for child in details_container.children() if child.window_text() and child.window_text().strip()]
        print(f"✅ Found details container with texts: {all_texts}")

        # Find Code
        if 'Code' in all_texts:
            code_index = all_texts.index('Code')
            if code_index + 1 < len(all_texts):
                details['code'] = all_texts[code_index + 1]

        # Find Unit and Quantity
        if 'Unit' in all_texts:
            unit_index = all_texts.index('Unit')
            if unit_index > 0:
                quantity = all_texts[unit_index - 1]
                details['unit'] = f"{quantity} Unit"

        # Find Price
        prices = [t for t in all_texts if re.fullmatch(r'\$?\d+\.\d{2}', t)]
        if prices:
            details['price'] = prices[0]

        # Find Description (the longest text that isn't another detail)
        ignore_list = [details['price'], details['code'], 'Code', 'Unit']
        if details['unit'] != 'N/A':
            ignore_list.append(details['unit'].split()[0])

        potential_descriptions = [t for t in all_texts if t not in ignore_list and not t.isdigit()]
        if potential_descriptions:
            details['description'] = max(potential_descriptions, key=len)

    except Exception as e:
        print(f"⚠️ Error while parsing details container: {e}")

    return details


def get_details_on_operator_screen(win):
    """
    Finds and parses item details specifically for the operator screen.
    It dynamically locates the details panel next to the selected item.
    """
    print("\n🔍 Reading Item Details on Operator Screen...")
    try:
        # The details are in a pane next to the main basket.
        # We find the basket first to get a reference point.
        basket = win.descendants(control_type="List")[0]
        basket_rect = basket.rectangle()

        # The details pane is to the right of the basket.
        possible_panes = win.descendants(control_type="Pane") + win.descendants(control_type="Custom")
        
        for pane in possible_panes:
            pane_rect = pane.rectangle()
            # Condition: Pane is to the right of the basket and contains the "Code" label.
            if pane_rect.left > basket_rect.right and pane.child_window(title="Code", control_type="Text").exists():
                parsed_details = parse_item_details(pane)
                print("\n✅ Successfully Parsed Operator Screen Details:")
                print(f"  - Description: {parsed_details['description']}")
                print(f"  - Price:       {parsed_details['price']}")
                print(f"  - Code:        {parsed_details['code']}")
                print(f"  - Unit:        {parsed_details['unit']}")
                return
        
        print("❌ Could not dynamically locate the operator details panel.")

    except Exception as e:
        print(f"❌ An error occurred on operator screen: {e}")


def get_details_on_customer_screen(win):
    """
    Finds and parses item details specifically for the customer-facing screen.
    """
    print("\n🔍 Reading Item Details on Customer Screen...")
    try:
        # On the customer screen, the details are in the top-right quadrant.
        window_rect = win.rectangle()
        horizontal_midpoint = window_rect.left + (window_rect.width() / 2)
        
        # We find the container that holds the details.
        possible_containers = win.descendants(control_type="Pane") + win.descendants(control_type="Custom")
        for container in possible_containers:
            rect = container.rectangle()
            if rect.left > horizontal_midpoint and container.child_window(title="Code", control_type="Text").exists():
                parsed_details = parse_item_details(container)
                print("\n✅ Successfully Parsed Customer Screen Details:")
                print(f"  - Description: {parsed_details['description']}")
                print(f"  - Price:       {parsed_details['price']}")
                print(f"  - Code:        {parsed_details['code']}")
                print(f"  - Unit:        {parsed_details['unit']}")
                return

        print("❌ Could not locate the customer details panel.")

    except Exception as e:
        print(f"❌ An error occurred on customer screen: {e}")


def read_basket_items(win):
    """Reads all items from the main basket list on the left."""
    print("\n🛒 Reading Basket Items...")
    try:
        basket = win.descendants(control_type="List")[0]
        items = basket.descendants(control_type="ListItem")
        print(f"Found {len(items)} item(s) in basket:")
        
        for idx, item in enumerate(items, 1):
            child_texts = [child.window_text() for child in item.children() if child.window_text()]
            name, quantity, price = "N/A", "N/A", None
            
            potential_names = [t for t in child_texts if not t.isdigit() and not re.fullmatch(r'[\d.]+', t)]
            if potential_names:
                name = max(potential_names, key=len)

            quantities = [t for t in child_texts if t.isdigit() and len(t) < 3] # Quantities are usually short numbers
            if quantities:
                quantity = quantities[-1] # Take the last one, as the first can be '0'

            prices = [t for t in child_texts if re.fullmatch(r'-?\d+\.\d{2}', t)]
            if prices:
                price = float(prices[0])

            print(f"  {idx}. Name: {name}, Quantity: {quantity}, Amount: {price if price is not None else 'N/A'}")
    except Exception as e:
        print(f"❌ Could not read basket items: {e}")


def read_balance_due(win):
    """Finds and prints the Balance Due and Savings amounts."""
    print("\n💰 Reading Balance Due...")
    try:
        # Primary method: Look for AmountControl class
        candidates = []
        for ctrl in win.descendants(control_type="Custom"):
            if "AmountControl" in ctrl.class_name():
                txt = ctrl.child_window().window_text()
                if txt and re.fullmatch(r'-?\d+\.\d+', txt.strip()):
                    candidates.append((float(txt.strip()), ctrl.rectangle().top))
        
        # Fallback method: Look for labels
        if not candidates:
            print("⚠️ AmountControl not found, trying label-based fallback...")
            for label in win.descendants(control_type="Text"):
                if "Balance Due" in label.window_text():
                    balance_ctrl = label.right()
                    balance_val = float(balance_ctrl.window_text().strip())
                    candidates.append((balance_val, balance_ctrl.rectangle().top))
                elif "Savings" in label.window_text():
                    savings_ctrl = label.right()
                    savings_val = float(savings_ctrl.window_text().strip())
                    candidates.append((savings_val, savings_ctrl.rectangle().top))

        if not candidates:
            print("❌ Could not find Balance Due with any method.")
            return

        candidates.sort(key=lambda x: x[1], reverse=True)
        print(f"  - Balance Due Found: {candidates[0][0]:.2f}")
        if len(candidates) > 1:
            print(f"  - Savings Found: {candidates[1][0]:.2f}")

    except Exception as e:
        print(f"❌ An error occurred while reading balance due: {e}")

def collect_return_basket_items(basket):
    """Collect all basket items from the current page on the return screen."""
    items = basket.descendants(control_type="ListItem")
    if not items:
        items = basket.children()

    page_items = []
    total = 0.0
    promo_total = 0.0
    promotion_found = False

    for idx, item in enumerate(items, 1):
        name = item.window_text()
        price = None
        quantity = None
        children = item.children()

        for child in children:
            txt = child.window_text()
            # Try to find price
            if any(c in txt for c in ["$", ".", ","]):
                try:
                    price_val = float(txt.replace("$", "").replace(",", "").strip())
                    price = price_val
                except Exception:
                    pass
            # Try to find quantity
            if txt.isdigit():
                quantity = int(txt)

        print(f"  {idx}. Name: {name}, Quantity: {quantity if quantity else 'N/A'}, Amount: {price if price else 'N/A'}")

        if price is not None:
            total += price
            if price < 0 or (name and ("promotion" in name.lower() or "bonus" in name.lower() or "ff" in name.lower())):
                promo_total += price
                promotion_found = True

        # Promotion detection
        if "promotion" in name.lower() or "bonus" in name.lower() or "ff" in name.lower():
            promotion_found = True
            print(f"🎉 Promotion found in basket item: {name}")
        else:
            # Only count actual articles (exclude promotions)
            page_items.append((name, quantity, price))

    return page_items, total, promo_total, promotion_found


def handle_return_screen(win):
    """Handles the entire process for the Return Transaction screen."""
    print("\n✨ Return Transaction Screen Detected ✨")
    
    # Locate basket control
    basket_controls = win.descendants(control_type="List")
    if not basket_controls:
        basket_controls = win.descendants(control_type="ListView")

    if not basket_controls:
        print("❌ Could not find basket/list control on the return screen.")
        return

    basket = basket_controls[0]

    # Locate navigation buttons
    try:
        up_btn = win.child_window(auto_id="rptBtnPgUp", control_type="Button")
        down_btn = win.child_window(auto_id="rptBtnPgDown", control_type="Button")
    except Exception:
        up_btn = None
        down_btn = None

    all_items = []
    grand_total = 0.0
    grand_promo_total = 0.0
    promo_found_any = False

    # Step 1: Scroll up to the top if possible
    if up_btn and up_btn.is_enabled():
        while up_btn.is_enabled():
            up_btn.click_input()
            time.sleep(0.3)

    # Step 2: Iterate through all pages
    while True:
        items_data, total, promo_total, promo_found = collect_return_basket_items(basket)
        print(f"Found {len(items_data)} article(s) in basket (this page).")

        all_items.extend(items_data)
        grand_total += total
        grand_promo_total += promo_total
        promo_found_any = promo_found_any or promo_found

        if down_btn and down_btn.is_enabled():
            down_btn.click_input()
            time.sleep(0.3)
        else:
            break

    # Final summary
    print(f"\n🛒 TOTAL Articles in basket (all pages): {len(all_items)}")
    print(f"💰 TOTAL Basket amount across all pages: {grand_total:.2f}")
    if grand_promo_total < 0:
        print(f"🎯 Promotion/discount applied: {grand_promo_total:.2f}")
    else:
        print("ℹ️ No promotion/discount applied.")
    print(f"✅ Final total after promotion: {grand_total:.2f}")

    if promo_found_any:
        print("✅ Basket contains promotion items.")
    else:
        print("ℹ️ Basket contains items without promotions.")


def main():
    """
    Main function to connect, detect the screen type, and extract all data.
    """
    try:
        app = Application(backend="uia").connect(title_re=".*R10PosClient.*", timeout=10)
        win = app.window(title_re=".*R10PosClient.*")
        win.set_focus()
        print("✅ POS window found and focused.")
    except Exception as e:
        print(f"❌ Could not connect or focus POS window: {e}")
        return

    # --- Screen Detection and Specific Logic ---
    # Check for unique elements on each screen to decide which logic to run.
    if win.child_window(title="Return Transaction", control_type="Text").exists():
        handle_return_screen(win)
    elif win.child_window(title="OK", control_type="Button").exists():
        print("\n✨ Operator Screen Detected ✨")
        read_basket_items(win)
        get_details_on_operator_screen(win)
        read_balance_due(win)
    else:
        print("\n✨ Customer Screen Detected ✨")
        read_basket_items(win)
        get_details_on_customer_screen(win)
        read_balance_due(win)


if __name__ == "__main__":
    main()
