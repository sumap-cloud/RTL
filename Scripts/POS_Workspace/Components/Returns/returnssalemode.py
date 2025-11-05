"""
================================================================================
 Automated POS Interaction and Return Flow
================================================================================

PURPOSE:
--------
This script automates the user interaction flow for a Point of Sale (POS) 
application. Its primary role is to detect which screen is currently active 
and execute a series of context-specific actions. The main flow demonstrated
is for handling a product return, which may or may not require a forced 
quantity adjustment.

The script is designed to be both executable for standalone testing and 
importable as a reusable module in a larger automation framework.

--------------------------------------------------------------------------------
STEP-BY-STEP FLOW:
--------------------------------------------------------------------------------

The core logic follows these sequential steps:

1.  **Connect and Identify the Screen:**
    The script first connects to the main POS application window. It then checks for
    unique UI elements to determine which screen is currently displayed. This could
    be the main Operator/Customer screen, or a specific return-related screen.

2.  **Handle the 'Return Transaction' Screen:**
    If the "Return Transaction" screen is detected, the script will:
    a. Read all the articles listed in the return basket.
    b. If a specific article name is provided, it will search for and select that item.
    c. If no name is provided (or the item isn't found), it will select the first 
       article in the list by default.
        
3.  **Check for 'Force Quantity' Pop-up:**
    After selecting an article, the script intelligently checks if a special 
    "Force Quantity" window has appeared. This window prompts the user to 
    manually enter the number of items being returned.
    a. **If the window appears:** The script calls a specialized function 
       (`adjust_return_quantity`) to automatically adjust the number to a predefined
       target (e.g., from 9 to 1) and clicks "OK".
    b. **If the window does not appear:** The script assumes it's a standard return
       and simply moves to the next step.
    
4.  **Handle the 'Return Item' Reason Code Screen:**
    Finally, after the quantity has been confirmed (or if it was never asked), 
    the script expects the "Return Item" screen to appear. On this screen, it:
    a. Verifies that all expected reason codes ("Damaged / Faulty", "Double Scan", etc.)
       are visible.
    b. Clicks on a predefined reason, such as "Double Scan", to complete the
       return process for the selected item.
    
5.  **Handle Other Screens:**
    The script also includes logic to handle the main Operator and Customer screens
    by reading basket contents, item details, and the balance due, although these
    are not part of the primary return flow logic.

"""
import time
import re
from pywinauto import Application
from pywinauto.findbestmatch import MatchError
from pywinauto.timings import TimeoutError

# Note: The 'adjust_return_quantity' function is imported from another file.
# Ensure 'forcequantity.py' is in the same directory.
from .forcequantity import adjust_return_quantity

# ==============================================================================
# SECTION 1: HELPER FUNCTIONS FOR DATA PARSING
# ==============================================================================

def parse_item_details(details_container):
    """
    A universal function to parse details once a specific container pane is found.
    """
    details = {"description": "N/A", "price": "N/A", "code": "N/A", "unit": "N/A"}
    try:
        all_texts = [child.window_text().strip() for child in details_container.children() if child.window_text() and child.window_text().strip()]
        if 'Code' in all_texts:
            code_index = all_texts.index('Code')
            if code_index + 1 < len(all_texts):
                details['code'] = all_texts[code_index + 1]
        if 'Unit' in all_texts:
            unit_index = all_texts.index('Unit')
            if unit_index > 0:
                quantity = all_texts[unit_index - 1]
                details['unit'] = f"{quantity} Unit"
        prices = [t for t in all_texts if re.fullmatch(r'\$?\d+\.\d{2}', t)]
        if prices:
            details['price'] = prices[0]
        ignore_list = [details['price'], details['code'], 'Code', 'Unit']
        if details['unit'] != 'N/A':
            ignore_list.append(details['unit'].split()[0])
        potential_descriptions = [t for t in all_texts if t not in ignore_list and not t.isdigit()]
        if potential_descriptions:
            details['description'] = max(potential_descriptions, key=len)
    except Exception as e:
        print(f"⚠️ Error while parsing details container: {e}")
    return details

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
            if potential_names: name = max(potential_names, key=len)
            quantities = [t for t in child_texts if t.isdigit() and len(t) < 3]
            if quantities: quantity = quantities[-1]
            prices = [t for t in child_texts if re.fullmatch(r'-?\d+\.\d{2}', t)]
            if prices: price = float(prices[0])
            print(f"  {idx}. Name: {name}, Quantity: {quantity}, Amount: {price if price is not None else 'N/A'}")
    except Exception as e:
        print(f"❌ Could not read basket items: {e}")

def read_balance_due(win):
    """Finds and prints the Balance Due and Savings amounts."""
    print("\n💰 Reading Balance Due...")
    try:
        candidates = []
        for ctrl in win.descendants(control_type="Custom"):
            if "AmountControl" in ctrl.class_name():
                txt = ctrl.child_window().window_text()
                if txt and re.fullmatch(r'-?\d+\.\d+', txt.strip()):
                    candidates.append((float(txt.strip()), ctrl.rectangle().top))
        if not candidates:
            print("⚠️ AmountControl not found, trying label-based fallback...")
            # Fallback logic here...
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
    """Parses all items on the current page of the return basket."""
    items = basket.descendants(control_type="ListItem") or basket.children()
    page_articles, tender_keywords = [], ['cash', 'card', 'eftpos', 'credit']
    for item in items:
        all_item_texts = []
        for child in item.children():
            all_item_texts.append(child.window_text().strip().lower())
            if 'button' in child.class_name().lower():
                try:
                    for grandchild in child.children():
                        all_item_texts.append(grandchild.window_text().strip().lower())
                except Exception: pass
        all_item_texts = [t for t in all_item_texts if t]
        if any(keyword in text for keyword in tender_keywords for text in all_item_texts):
            print(f"  - Skipping tender line: {' | '.join(all_item_texts)}")
            continue
        name, quantity, price = "N/A", "N/A", None
        potential_names = [t for t in all_item_texts if not t.isdigit() and not re.fullmatch(r'[-]?\$?\d+\.\d{2}', t) and t != '#']
        if potential_names: name = max(potential_names, key=len)
        quantities = [t for t in all_item_texts if t.isdigit() and len(t) < 4]
        if quantities: quantity = quantities[-1]
        prices = [t for t in all_item_texts if re.fullmatch(r'[-]?\$?\d+\.\d{2}', t)]
        if prices:
            try: price = float(prices[0].replace('$', ''))
            except ValueError: price = None
        article = {"name": name, "quantity": quantity, "price": price, "control": item}
        page_articles.append(article)
        print(f"  -> Found Article: {article['name']} (Qty: {article['quantity']}, Price: {article['price']})")
    return page_articles

# ==============================================================================
# SECTION 2: DEDICATED SCREEN HANDLER FUNCTIONS
# ==============================================================================

def process_return_transaction_screen(win, app, article_to_return=None, quantity=None, reason_code=None):
    """
    Handles the entire logic for the 'Return Transaction' screen, including
    article selection and subsequent screen checks.
    """
    print("\n✨ Return Transaction Screen Detected ✨")
    articles = handle_return_screen(win)
    if not articles:
        print("No articles found to select.")
        return

    # --- Article Selection Logic ---
    article_to_select = None
    if article_to_return:
        print(f"\n--- Searching for Article: '{article_to_return}' ---")
        for article in articles:
            if article_to_return.lower() == article['name'].lower().strip():
                article_to_select = article
                print(f"✅ Found exact matching article: {article['name']}")
                break
        if not article_to_select:
            for article in articles:
                if article_to_return.lower() in article['name'].lower():
                    article_to_select = article
                    print(f"✅ Found partial matching article: {article['name']}")
                    break
        if not article_to_select:
            print(f"⚠️ Could not find article. Defaulting to first item.")
    
    if not article_to_select:
        article_to_select = articles[0]
        print("\n--- Selecting First Article by Default ---")

    print(f"Selecting: {article_to_select['name']}")
    try:
        article_to_select['control'].click_input()
        print("✅ Article selected successfully.")
        time.sleep(3)

        print("🤔 Checking for 'Force Quantity' screen...")
        try:
            app.window(title_re=".*TransactionBasedReturnQuantityPickerViewModel.*", timeout=3)
            print("✨ Force Quantity screen detected. Handling it now...")
            adjust_return_quantity(target_quantity=(quantity if quantity is not None else 1))
            time.sleep(3)
        except (TimeoutError, MatchError):
            print("➡️ Force Quantity screen not found. This is normal.")

        print("🔍 Now checking for 'Reason Code' screen...")
        if win.child_window(title="Return Item", control_type="Text").exists() and win.child_window(title="Double Scan", control_type="Button").exists():
            handle_reason_code_screen(win, reason_code=reason_code)
        else:
            print("❓ Did not navigate to the reason code screen.")

    except Exception as e:
        print(f"❌ Failed to click the selected article: {e}")

def handle_return_screen(win):
    """Gathers all articles from the paginated return basket."""
    basket_controls = win.descendants(control_type="List") or win.descendants(control_type="ListView")
    if not basket_controls:
        print("❌ Could not find basket control on return screen.")
        return []
    basket = basket_controls[0]
    try:
        up_btn = win.child_window(auto_id="rptBtnPgUp", control_type="Button")
        down_btn = win.child_window(auto_id="rptBtnPgDown", control_type="Button")
    except Exception:
        up_btn, down_btn = None, None
    all_articles = []
    if up_btn and up_btn.is_enabled():
        while up_btn.is_enabled():
            up_btn.click_input()
            time.sleep(0.4)
    while True:
        all_articles.extend(collect_return_basket_items(basket))
        if down_btn and down_btn.is_enabled():
            down_btn.click_input()
            time.sleep(0.4)
        else:
            break
    print(f"\n✅ Found a total of {len(all_articles)} article(s).")
    return all_articles

def handle_reason_code_screen(win, reason_code=None):
    """Verifies and clicks a reason code on the 'Return Item' screen."""
    print("\n✨ Return Item Reason Code Screen Detected ✨")
    reason_to_click = reason_code if reason_code else "Double Scan"
    
    expected_reasons = {"Damaged / Faulty", "Change of Mind", "Tickets Not Printed", "Poor Quality / Fit", "Price Discrepancy", "Double Scan", "Store Lead Discretion", "Product Recall", "Out of Date", "Price Scan Policy", "GC Activation Error"}
    try:
        win.child_window(title=reason_to_click, control_type="Button").wait('visible', timeout=10)
        all_buttons = {b.window_text() for b in win.descendants(control_type="Button") if b.window_text()}
        print("\n--- Available Reason Codes ---")
        for reason in sorted(list(all_buttons)):
            if reason in expected_reasons:
                print(f"  - {reason}")
        print("----------------------------\n")
        if expected_reasons.issubset(all_buttons):
            print("✅ All expected reason codes are visible.")
            print(f"🖱️ Clicking '{reason_to_click}'...")
            win.child_window(title=reason_to_click, control_type="Button").click_input()
            print(f"✅ '{reason_to_click}' button clicked successfully.")
        else:
            print(f"❌ ERROR: Missing reason codes: {expected_reasons - all_buttons}")
    except (TimeoutError, MatchError) as e:
        print(f"❌ An error on the reason code screen: {e}")

def process_operator_screen(win):
    """Handles the main operator screen."""
    print("\n✨ Operator Screen Detected ✨")
    read_basket_items(win)
    # get_details_on_operator_screen(win) # Example of other functions
    read_balance_due(win)

def process_customer_screen(win):
    """Handles the customer-facing screen."""
    print("\n✨ Customer Screen Detected ✨")
    read_basket_items(win)
    # get_details_on_customer_screen(win) # Example of other functions
    read_balance_due(win)

# ==============================================================================
# SECTION 3: MAIN EXECUTABLE FLOW
# ==============================================================================

def returns_item_selection(article_to_return=None, quantity=None, reason_code=None):
    """
    Connects to the POS app, detects the screen, and dispatches to the correct handler.
    """
    try:
        app = Application(backend="uia").connect(title_re=".*R10PosClient.*", timeout=10)
        win = app.window(title_re=".*R10PosClient.*")
        win.set_focus()
        print("✅ POS window found and focused.")
    except Exception as e:
        print(f"❌ CRITICAL: Could not connect or focus POS window: {e}")
        return False

    try:
        # --- Screen Detection and Dispatch Logic ---
        if win.child_window(title="Return Item", control_type="Text").exists() and win.child_window(title="Double Scan", control_type="Button").exists():
            handle_reason_code_screen(win, reason_code=reason_code)
        elif win.child_window(title="Return Transaction", control_type="Text").exists():
            process_return_transaction_screen(win, app, article_to_return, quantity, reason_code)
        elif win.child_window(title="OK", control_type="Button").exists():
            process_operator_screen(win)
        else:
            process_customer_screen(win)
        return True
    except Exception as e:
        print(f"❌ An unexpected error occurred during the automation flow: {e}")
        return False

# This block allows the script to be run directly for testing purposes.
if __name__ == "__main__":
    print("--- Running POS Automation in standalone mode for testing ---")
    
    # --- Example: Run by specifying an article, quantity, and reason code ---
    print("\n--- TEST CASE: Selecting a specific article with quantity and reason ---")
    article_name_to_find = None
    target_quantity = 4
    reason = "Double Scan"

    if not returns_item_selection(
        article_to_return=article_name_to_find,
        quantity=target_quantity,
        reason_code=reason
    ):
        print("\n--- The automation script encountered an error. ---")
    else:
        print("\n--- The automation script completed successfully. ---")

