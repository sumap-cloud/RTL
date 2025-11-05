import time
import re
from pywinauto import Application, timings, findbestmatch

# -------------------------------------------------------------------
# --- ORIGINAL FUNCTION (Unchanged) ---
# --- This function is still used for the first summary pass. ---
# -------------------------------------------------------------------
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
        has_special_deal_icon = False
        try:
            if any(child.element_info.control_type == 'Image' for child in item.children()):
                has_special_deal_icon = True
        except Exception:
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
            page_items.append((name, quantity, price, has_hash, has_special_deal_icon))
        else:
            print(f"  -> Detected as promotion, not counted as an article.")

    return page_items, total, promo_total, promotion_found


# -------------------------------------------------------------------
# --- NEW FUNCTION (REWRITTEN) ---
# --- This function finds the detail pane and parses its text. ---
# -------------------------------------------------------------------
def get_item_details(win):
    """
    Finds the item detail panel (LineDetailsViewID) and scrapes its content.
    This version is more robust and parses fields based on keywords.
    """
    details = {
        "Name": "N/A",
        "MainPrice": "N/A",     # Price at the top (e.g., 11.99 or 4.00)
        "UnitQuantity": "N/A",  # e.g., 1
        "UnitPrice": "N/A",     # e.g., 4.00
        "PriceOverride": "N/A", # e.g., "Price Override, Old Price is"
        "OldPrice": "N/A",      # e.g., 11.99
        "Code": "N/A",          # e.g., 9300675014779
        "TotalInBasket": "N/A", # e.g., 1
        "IsVoided": False,      # --- NEW: Added void check ---
        "AllText": []
    }
    try:
        # Find the detail pane using the properties you provided
        detail_pane = win.child_window(auto_id="LineDetailsViewID", control_type="Custom")
        detail_pane.wait('exists', timeout=3)
        
        # --- REMOVED: Sleep was moved to scrape_page_details ---
        # time.sleep(0.5) 
        
        # Scrape all text from ALL descendants, not just 'Text' controls
        all_texts = [child.window_text() for child in detail_pane.descendants() if child.window_text()]
        details["AllText"] = all_texts

        # --- NEW: Check for voided status in the entire text list *first* ---
        if any("VOIDED" in t.upper() for t in all_texts):
            details["IsVoided"] = True
        
        if not all_texts:
            print("      -> Detail pane found, but no text content.")
            return details

        # --- Parse the text using a loop (much more robust) ---
        details["Name"] = all_texts[0]
        if len(all_texts) > 1:
            details["MainPrice"] = all_texts[1] # This is the main total, e.g., "$26.00"

        for i, text in enumerate(all_texts):
            # Case 1: "1", "Unit", "11.99"
            if text == "Unit" and i > 0 and i < len(all_texts) - 1:
                details["UnitQuantity"] = all_texts[i-1]
                details["UnitPrice"] = all_texts[i+1]
            
            # Case 2: "2", "Qty X", "$13.00", "=", "$26.00"
            # We find "Qty X"
            elif "Qty X" in text and i > 0 and i < len(all_texts) - 1:
                details["UnitQuantity"] = all_texts[i-1] # This is "2"
                details["UnitPrice"] = all_texts[i+1] # This is "$13.00"
            
            # Look for "Price Override"
            if "Price Override" in text and i < len(all_texts) - 1:
                details["PriceOverride"] = text
                # The next text seems to be the old price, based on output
                details["OldPrice"] = all_texts[i+1] 
            
            # Look for "Code"
            if text == "Code" and i < len(all_texts) - 1:
                details["Code"] = all_texts[i+1]
                
            # Look for "total in basket"
            if "total in basket" in text:
                match = re.search(r'(\d+) total in basket', text)
                if match:
                    details["TotalInBasket"] = match.group(1)

            # --- REMOVED: Void check moved above the loop ---
            # if "VOIDED" in text.upper():
            #     details["IsVoided"] = True

    except (timings.TimeoutError, Exception) as e:
        print(f"      -> Could not find or parse item detail pane: {e}")
        
    return details


# -------------------------------------------------------------------
# --- NEW FUNCTION (LOGIC UPDATED) ---
# --- This function clicks all items on the *current* page. ---
# -------------------------------------------------------------------
def scrape_page_details(basket, win):
    """
    Clicks each item on the current basket page and scrapes its details.
    
    IMPORTANT: We must re-find the items in the loop because clicking
    can make the old item references "stale" or invalid.
    """
    all_page_details = []
    
    # Get the initial count of items on the page
    try:
        item_controls = basket.descendants(control_type="ListItem")
        if not item_controls:
            item_controls = basket.children()
        num_items_on_page = len(item_controls)
    except Exception:
        num_items_on_page = 0
        
    if num_items_on_page == 0:
        print("   -> No items found on this page to click.")
        return []

    print(f"   -> Found {num_items_on_page} items to click on this page.")
    
    # Iterate by index, NOT by the control list itself
    for i in range(num_items_on_page):
        item_to_click = None
        item_name = f"Item {i+1}"
        try:
            # Re-find the list of items *every single time*
            # This is critical to avoid "element not found" errors
            current_items_list = basket.descendants(control_type="ListItem")
            if not current_items_list:
                current_items_list = basket.children()

            # Safety check
            if i >= len(current_items_list):
                print(f"   -> Item index {i} out of bounds. Stopping page scan.")
                break
                
            item_to_click = current_items_list[i]
            
            # --- UPDATED NAME LOGIC ---
            # Try to get a name for logging (using same logic as collect_basket_items)
            try:
                child_texts = [child.window_text() for child in item_to_click.children() if child.window_text()]
                potential_names = [t for t in child_texts if not re.fullmatch(r'-?[\d.]+', t) and t != '#']
                if potential_names:
                    item_name = max(potential_names, key=len)
                else:
                    item_name = item_to_click.window_text() # Fallback
            except Exception:
                item_name = item_to_click.window_text() # Fallback
            # --- END UPDATED NAME LOGIC ---

            print(f"\n   -> Clicking Item {i+1}: '{item_name}'")
            item_to_click.click_input()
            
            # --- NEW: Wait for pane to update *after* click ---
            # This is critical to prevent reading stale data
            time.sleep(1.0) 
            
            # Now, call the new function to get details
            details = get_item_details(win)
            print(f"      - Name: {details['Name']} (Code: {details['Code']})")
            print(f"      - Qty: {details['UnitQuantity']} @ {details['UnitPrice']} (Main Price: {details['MainPrice']})")
            if details['PriceOverride'] != "N/A":
                print(f"      - Override: {details['PriceOverride']} (Old Price: {details['OldPrice']})")
            
            # --- NEW: Print if voided ---
            if details['IsVoided']:
                print("      - !!! ITEM IS VOIDED !!!")
            
            all_page_details.append(details)

        except Exception as e:
            print(f"   -> ERROR clicking or getting details for '{item_name}': {e}")
            # Try to continue to the next item
            pass
            
    return all_page_details


# -------------------------------------------------------------------
# --- UPDATED MAIN FUNCTION ---
# --- Added the new detail collection loop at the end. ---
# -------------------------------------------------------------------
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

    # --- Find Basket Control ---
    basket_controls = win.descendants(control_type="List")
    if not basket_controls:
        basket_controls = win.descendants(control_type="ListBox")
    if not basket_controls:
        basket_controls = win.descendants(control_type="ListView")

    if not basket_controls:
        print("❌ Could not find basket/list control on left side.")
        return

    basket = basket_controls[0]

    # --- Find Page Buttons ---
    try:
        up_btn = win.child_window(auto_id="rptBtnPgUp", control_type="Button")
        down_btn = win.child_window(auto_id="rptBtnPgDown", control_type="Button")
    except Exception:
        up_btn = None
        down_btn = None
        print("   -> Warning: Could not find page up/down buttons.")

    # ==================================================================
    # === PART 1: ORIGINAL SUMMARY (Unchanged) ===
    # ==================================================================
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
        print(f"\n--- Reading Page {page_num} (Summary Pass) ---")
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

    # --- Get Footer Counts ---
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

    # --- Print Summary ---
    print("\n" + "="*40)
    print("           BASKET SUMMARY (PASS 1)")
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

    # ==================================================================
    # === PART 2: NEW ITEM DETAIL COLLECTION ===
    # ==================================================================
    print("\n\n" + "="*40)
    print("        STARTING ITEM DETAIL SCRAPE (PASS 2)")
    print("="*40)
    all_item_details = []

    # --- Scroll back to top ---
    if up_btn and up_btn.is_enabled():
        print("Scrolling to the top of the basket for detail pass...")
        while up_btn.is_enabled():
            up_btn.click_input()
            time.sleep(0.3)
        print("Reached the top.")
    
    page_num = 1
    while True:
        print(f"\n--- Clicking Items on Page {page_num} (Detail Pass) ---")
        
        # Call the NEW function to click items and get details
        details_from_page = scrape_page_details(basket, win)
        all_item_details.extend(details_from_page)

        if down_btn and down_btn.is_enabled():
            print("\nNavigating to next page for detail pass...")
            down_btn.click_input()
            time.sleep(0.3)
            page_num += 1
        else:
            print("\nNo more pages down. Detail scrape complete.")
            break

    # --- Print Final Detail Summary (UPDATED) ---
    print("\n" + "="*40)
    print("         ITEM DETAIL SUMMARY (PASS 2)")
    print("="*40)
    print(f"📰 Total items clicked and details parsed: {len(all_item_details)}")
    
    if not all_item_details:
        print("   -> No item details were collected.")
    else:
        for idx, details in enumerate(all_item_details, 1):
            print(f"\n--- Item {idx} ---")
            print(f"   Name:     {details.get('Name')}")
            print(f"   Code:     {details.get('Code')}")
            print(f"   MainPrice:{details.get('MainPrice')}")
            print(f"   Unit Qty: {details.get('UnitQuantity')}")
            print(f"   Unit Prc: {details.get('UnitPrice')}")
            if details.get('PriceOverride') != "N/A":
                print(f"   Override: {details.get('PriceOverride')}")
                print(f"   OldPrice: {details.get('OldPrice')}")
            print(f"   InBasket: {details.get('TotalInBasket')}")
            # --- NEW: Print if voided ---
            if details.get('IsVoided'):
                print(f"   Status:   *** VOIDED ***")
            
            # print(f"   All Text: {details.get('AllText')}") # Uncomment for debugging
    print("="*40)
    
    return True


if __name__ == "__main__":
    get_basket_info()

