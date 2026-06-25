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

from Components.Salemode.Keyin_item import Kayin_EAN_POS


class Login:
    @staticmethod
    # def initialize_and_login(title_regex, username, password):
    def initialize_and_login(title_regex, username, password):
        """Initializes connection, handles Login/Unlock, and validates dashboard or void flow."""
        print(f"Initializing connection to: {title_regex}")
        try:
            win = Application(backend="uia").connect(title_re=title_regex, timeout=15)
            app = win.window(title_re=title_regex)
            app.set_focus()

            # Handle Screensaver
            sav = app.child_window(class_name="MediaElement", found_index=0)
            if sav.exists(timeout=5):
                print("Screensaver detected. Dismissing...")
                sav.click_input()
                time.sleep(1)

            # UI Elements
            login_btn = app.child_window(title="Login", control_type="Button")
            unlock_btn = app.child_window(title="Unlock", control_type="Button")
            locked_label = app.child_window(title_re="Locked by", control_type="Text")

            # ===== LOGIN / UNLOCK FLOW =====
            if login_btn.exists(timeout=3):
                print("Path: Standard Login")
                login_btn.click_input()
                app.child_window(auto_id="UserName", control_type="Edit").set_text(username)
                app.child_window(auto_id="Password", control_type="Edit").set_text(password)
                app.child_window(title="Login", control_type="Button").click_input()

            elif unlock_btn.exists(timeout=3) and locked_label.exists():
                print("Path: Session Unlock")
                app.child_window(auto_id="Password", control_type="Edit").set_text(password)
                unlock_btn.click_input()

            else:
                print("Application already at dashboard or in unknown state.")

            print("Waiting for dashboard to stabilize...")

            # ===== DASHBOARD / VOID VALIDATION =====
            nosale_btn = app.child_window(title="No Sale", control_type="Button")
            void_btn = app.child_window(title="Void Transaction", control_type="Button")

            if nosale_btn.exists(timeout=12):
                print("✅ Success: At Dashboard.")

            elif void_btn.exists(timeout=3):
                print("Detected Void state. Processing approval...")
                void_btn.click_input()

                # if mgr_username and mgr_password:
                Login.approval_popup_handler("ATMgr5", "abcd1234")
                # else:
                #     print("❌ Manager credentials missing for approval.")

                print("Verifying final state...")
                if nosale_btn.exists(timeout=10):
                    if nosale_btn.is_enabled():
                        print("⭐⭐ FINAL SUCCESS: Void complete. No Sale is ENABLED.")
                    else:
                        print("⚠️ Warning: At Dashboard, but No Sale is DISABLED.")
                else:
                    print("❌ Error: Dashboard not found after Void sequence.")

            else:
                print("❌ Error: UI state unrecognized.")
                app.print_control_identifiers()

            return app

        except Exception as e:
            print(f"❌ Initialization Error: {e}")
            return None


    def reasoncode_popup_handler(reason_code):
        try:
            popup_res_con = Application(backend="uia").connect(title_re=".*Retalix.*Presentation.*", timeout=5)
            popup_res_win = popup_res_con.window(title_re=".*Retalix.*Presentation.*")
            popup_res_win.set_focus()

            reason_btn = popup_res_win.child_window(title=reason_code, control_type="Button")
            if reason_btn.exists(timeout=3):
                reason_btn.click_input()
                print(f"✅ Reason '{reason_code}' selected.")

        except Exception as e:
            print(f"❌ Reason Selection Failed: {e}")


    def approval_popup_handler(username, password):
        print("Requesting Manager Approval...")
        try:
            popup_conn = Application(backend="uia").connect(title_re=".*Retalix.*Presentation.*", timeout=5)
            popup_win = popup_conn.window(title_re=".*Retalix.*Presentation.*")
            popup_win.set_focus()

            user_field = popup_win.child_window(auto_id="ValueTextBox", control_type="Edit")
            pass_field = popup_win.child_window(auto_id="Password", control_type="Edit")

            if user_field.exists(timeout=5):
                user_field.click_input()
                user_field.type_keys(username)

                pass_field.click_input()
                pass_field.type_keys(password)

                user_field.click_input()
                time.sleep(1)

                ok_btn = popup_win.child_window(title="OK", control_type="Button")
                if ok_btn.exists(timeout=3):
                    ok_btn.click_input()

                time.sleep(1)
                Login.reasoncode_popup_handler("Unwanted Goods")
            else:
                print("❌ Manager Login fields not found.")

        except Exception as e:
            print(f"❌ Approval Failed: {e}")



class AddItem:


    
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
            items_data, total, promo_total, promo_found = AddItem.collect_basket_items(basket)
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
        return app



def validate_step(condition: bool, message: str, screenshot: bool = False) -> bool:
    if not condition:
        print(f"Failed: {message}")
        return False
    print(f"Passed: {message}")
    return True

def add_items_to_basket(win, article_ean_list) -> bool:
    # if not validate_step(
    #     Kayin_EAN_POS(eans_to_add=TEST_CONFIG["items"]["ean_codes"]),
    #     "Adding items by EAN"
    # ):
    #     return False

    win.set_focus()
    item_input = win.child_window(auto_id="InputProductNumber", control_type="Edit")
    
    article_eans = article_ean_list.split(';') if isinstance(article_ean_list, str) else article_ean_list

    for ean in article_eans:
        # Adding a pause between keystrokes helps the POS "see" every digit
        item_input.type_keys(ean + "{ENTER}", pause=0.05, with_spaces=True)
        # Give the POS a moment to register the item before the next loop
        time.sleep(1.0)
    
    # item_input.type_keys(f"9300624016571{ENTER}")
    
    time.sleep(2) 
    
    # if not validate_step(
    AddItem.get_basket_info(),
        # "Validating basket contents"
    # ):
        # return False
    
    click_OK_button = win.child_window(title="OK", control_type="Button")
    # return validate_step(
    click_OK_button.exists(timeout=5) and click_OK_button.click_input() is None,
        # "Navigating to loyalty mode"
    # )

def add_card():
    app1 = None
    win1 = None

    try:
        time.sleep(2)  # Wait for the loyalty popup to appear
        app1 = Application(backend="uia").connect(title_re=".*Retalix.Woolworths.Client.POS.Presentation.*")
        win1 = app1.window(title_re=".*Retalix.Woolworths.Client.POS.Presentation.*")
        # win1.set_focus()
        # win1.print_control_identifiers()
    except Exception as e:
        print(f"❌ Could not connect to loyalty popup: {e}")
        return None
    # win.child_window(title="Loyalty Card Number", control_type="Edit").type_keys("1234567890")
    # win1.top_window()
    win1.set_focus()
    win1.child_window(auto_id="ValueTextBox", control_type="Edit").click_input()
    win1.child_window(auto_id="ValueTextBox", control_type="Edit").type_keys("1234567890")
    win1.child_window(title="Next", control_type="Button").click_input()
    win1.child_window(title="OK", control_type="Button").click_input()


def reedem_choice_offer():
    app1 = None
    win1 = None

    try:
        time.sleep(2)  # Wait for the loyalty popup to appear
        app1 = Application(backend="uia").connect(title_re=".*Retalix.Woolworths.Client.POS.Presentation.*")
        win1 = app1.window(title_re=".*Retalix.Woolworths.Client.POS.Presentation.*")
        # win1.set_focus()
        # win1.print_control_identifiers()
    except Exception as e:
        print(f"❌ Could not connect to loyalty popup: {e}")
        return None
    
    win1.set_focus()
    popup_title = win1.child_window(title="Do you want me to apply it now?", auto_id="MessageTextBox", control_type="Edit")
    if popup_title.exists(timeout=5):
        print(f"✅ Choice offer popup detected: '{popup_title.window_text()}' offered.")

        offer_btn = win1.child_window(title_re=".*Market Day Mobile 10 percent off.*", auto_id="button", control_type="Button")
        if offer_btn.exists(timeout=5):
            # offer_btn.click_input()
            print(f"✅ Redeemed choice offer 'Market Day Mobile 10 percent off'.")
        else:
            print(f"❌ Choice offer button 'Market Day Mobile 10 percent off' not found.")

    else:
        print("❌ Choice offer popup not detected.")

    # ==============================================================================
    # MAIN EXECUTION BLOCK
    # ==============================================================================

app = Login.initialize_and_login(
    ".*R10PosClient.*",
    "Atcash1",
    "abcd1234"
)



app = add_items_to_basket(app, "9313820016146;9313820016146")

app = add_card()