import time
import re
from pywinauto import Application, timings

def collect_basket_items(basket):
    """Collect all basket items from the current page, now with icon detection."""
    items = basket.descendants(control_type="ListItem")
    if not items:
        items = basket.children()

    page_items = []
    total = 0.0
    promo_total = 0.0
    promotion_found = False

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
            except (ValueError, IndexError):
                price = None
                
        print(f"  {idx}. Name: {name}, Qty: {quantity}, Amount: {price if price is not None else 'N/A'}, Has #: {has_hash}, Special Deal: {has_special_deal_icon}")

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
    
    print(f"✅ Final Net Total: {grand_total:.2f}")
    print("="*40)
    return True


if __name__ == "__main__":
    get_basket_info()
    
##
