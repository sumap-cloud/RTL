import time
import re
import sys
import csv
from pathlib import Path

from pywinauto import Application, timings

# --- Setup for project root and imports ---
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Component.Read_csv import get_csv_value
from Component.Update_csv import update_csv_value
from Component import global_instance
from Component.report import logger



# class AddItem:


    
def collect_basket_items(basket):
    """Collect all basket items from the current page, now with icon detection."""
    items = basket.descendants(control_type="ListItem")
    if not items:
        items = basket.children()

    page_items = []
    total = 0.0
    promo_total = 0.0
    promotion_found = False
    # ind = 0

    print(f"Found {len(items)} item(s) on this page:")

    for idx, item in enumerate(items, 1):
        child_texts = [child.window_text() for child in item.children() if child.window_text()]
        
        name, quantity, price = "N/A", "N/A", None

        # --- NEW: Detect the special deal icon /fast entry article if article having special deal symbol we have to consider as fast entry article ---
        # We assume the green circle is an 'Image' control within the ListItem.
        has_special_deal_icon = False
        try:
            # Check if any child of the list item is an Image control.
            if any(child.element_info.control_type == 'Image' for child in item.children()):
                has_special_deal_icon = True
        except Exception:
            # Silently ignore if children can't be inspected
            pass
        # --- END NEW SECTION ---

        # --- FIX: Smarter name and hash detection ---
        has_hash = any('#' in t for t in child_texts)

        potential_names = [t for t in child_texts if not re.fullmatch(r'-?[\d.]+', t) and t != '#']
        if potential_names:
            name = max(potential_names, key=len)

        quantities = [t for t in child_texts if t.isdigit() and len(t) < 3]
        if quantities:
            quantity = quantities[-1] 

        prices_texts = [t for t in child_texts if re.search(r'-?\d+\.\d{2}', t)]
        if prices_texts:
            try:
                price_text = prices_texts[0]
                price = float(re.sub(r'[^\d.-]', '', price_text))
                global_instance.article_price.append(price)
                global_instance.article_price_list += price_text + ";"
                print(f"   -> Detected price text: '{global_instance.article_price_list}'")
                print(f"   -> Extracted price: {global_instance.article_price} from text '{price_text}'")
                # ind += 1
            except (ValueError, IndexError):
                price = None

        global_instance.article_name_list += name + ";" 
        global_instance.article_qty_list += quantity + ";"  
        print(f"  {idx}. Name: {name}, Qty: {quantity}, Amount: {price if price is not None else 'N/A'}, Has #: {has_hash}, Special Deal: {has_special_deal_icon}")

        logger.log(f"Successfully added article name: '{name}' with quantity: {quantity} and price: {price if price is not None else 'N/A'}", status="pass")

        if price is not None:
            total += price
            if price < 0 or (name and ("promotion" in name.lower() or "bonus" in name.lower() or "ff" in name.lower())):
                promo_total += price
                promotion_found = True

        if not (name and ("promotion" in name.lower() or "bonus" in name.lower() or "ff" in name.lower())):
            # Add the special deal status to the appended data
            page_items.append((name, quantity, price, has_hash, has_special_deal_icon))
        else:
            print(f"   -> Detected as promotion, not counted as an article.")

    return page_items, total, promo_total, promotion_found


def get_basket_info():
    """Connects to the POS application and extracts all basket information."""
    try:
        app = Application(backend="uia").connect(title_re=".*R10PosClient.*", timeout=10)
        win = app.window(title_re=".*R10PosClient.*")
        win.set_focus()
        print("✅ POS window found and focused.")
    except (timings.TimeoutError, Exception) as e:
        print(f"❌ Could not connect or focus POS window: {e}")
        return

    basket_controls = win.descendants(control_type="List")
    if not basket_controls:
        basket_controls = win.descendants(control_type="ListBox")
    if not basket_controls:
        basket_controls = win.descendants(control_type="ListView")

    if not basket_controls:
        print("❌ Could not find basket/list control on left side.")
        return

    basket = basket_controls[0]

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

    if up_btn and up_btn.is_enabled():
        print("Scrolling to the top of the basket...")
        while up_btn.is_enabled():
            up_btn.click_input()
            time.sleep(0.3)
        print("Reached the top.")

    page_num = 1
    while True:
        print(f"\n--- Reading Page {page_num} ---")
        items_data, total, promo_total, promo_found = collect_basket_items(basket)
        print(f"Found {len(items_data)} article(s) on this page.")

        all_items.extend(items_data)
        grand_total += total
        grand_promo_total += promo_total
        promo_found_any = promo_found_any or promo_found

        if down_btn and down_btn.is_enabled():
            print("Navigating to next page...")
            down_btn.click_input()
            time.sleep(0.3)
            page_num += 1
        else:
            print("No more pages down.")
            break

    item_count_text = "N/A"
    bulk_count_text = "N/A"
    try:
        print("\n🔍 Searching for Item and Bulk counts...")
        all_text_controls = win.descendants(control_type='Text')
        for control in all_text_controls:
            text = control.window_text()
            if "Items" in text:
                item_count_text = text
            if "Bulk" in text:
                bulk_count_text = text
    except Exception as e:
        print(f"Could not find item/bulk counts. Error: {e}")

    print("\n" + "="*40)
    print("                BASKET SUMMARY")
    print("="*40)
    print(f"🛒 TOTAL Articles in basket (all pages): {len(all_items)}")
    print(f"🔢 Item Count Display: {item_count_text}")
    print(f"📦 Bulk Count Display: {bulk_count_text}")
    print(f"💰 Gross Total: {grand_total - grand_promo_total:.2f}")
    if grand_promo_total != 0:
        print(f"🎯 Total Promotions/Discounts: {grand_promo_total:.2f}")
    else:
        print("ℹ️ No promotions or discounts applied.")
    global_instance.total_amount_salemode = f"{grand_total:.2f}"
    print(f"💵 Net Total: {global_instance.total_amount_salemode}")
    print(f"✅ Final Net Total: {grand_total:.2f}")

    logger.log(f"✅ Final Net Total in salemode: {grand_total:.2f}", status="pass")
    print("="*40)
    return app

# def add_items_to_basket(self, win, article_ean_list) -> bool:
def add_items_to_basket(win, banner, TC_ID, Iteration, data_file="SaleData.csv", transaction_data_file="TransactionData.csv") -> bool:
# if not validate_step(
#     Kayin_EAN_POS(eans_to_add=TEST_CONFIG["items"]["ean_codes"]),
#     "Adding items by EAN"
# ):
#     return False

    # title_regex = ".*R10PosClient.*"
    DATA_FILE = data_file
    RESOURCE_DIR = current_file_path.parent.parent / "resources"

    parent_path = Path(__file__).parent.parent
    file_path = parent_path / 'resources' / data_file
    # print(f"Reading credentials from: {file_path}")

    time.sleep(4)  # Ensure the POS is ready for input

    win.set_focus()
    item_input = win.child_window(auto_id="InputProductNumber", control_type="Edit")
    
    article_ean_list = get_csv_value(file_path, banner, TC_ID, Iteration, 'Item_EAN')
    article_eans = article_ean_list.split(';') if isinstance(article_ean_list, str) else article_ean_list

    for ean in article_eans:
        # Adding a pause between keystrokes helps the POS "see" every digit
        item_input.type_keys(ean + "{ENTER}", pause=0.05, with_spaces=True)
        # Give the POS a moment to register the item before the next loop
        time.sleep(1.0)
        logger.log(f"Added item with EAN: {ean}", status="info")
    # item_input.type_keys(f"9300624016571{ENTER}")
    
    time.sleep(2) 
    
    # if not validate_step(
    get_basket_info()
        # "Validating basket contents"
    # ):
        # return False
    # parent_path = Path(__file__).parent.parent
    file_path2 = parent_path / 'resources' / transaction_data_file
    print(f"Updating article names and prices to CSV at: {file_path2}")
    update_csv_value(file_path2, banner, TC_ID, Iteration, 'Item_Description', global_instance.article_name_list)
    print(f"   -> Updated Item_Price with: '{global_instance.article_price_list}'")
    update_csv_value(file_path2, banner, TC_ID, Iteration, 'Item_Price', global_instance.article_price_list)
    
    click_OK_button = win.child_window(title="OK", control_type="Button")
    # return validate_step(
    click_OK_button.exists(timeout=5) and click_OK_button.click_input() is None,
        # "Navigating to loyalty mode"
    # )