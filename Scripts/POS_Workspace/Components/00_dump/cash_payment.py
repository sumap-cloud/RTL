import time
from pywinauto import Application
from ..Tenders.receipt_handler import handle_receipt_popup

def cash_payment(app, amount=None):
    """
    Handle cash payment in POS client
    
    Args:
        app: pywinauto Application instance
        amount: Optional specific amount to select from the suggestion list
    """
    win = app.window(title_re=".*R10PosClient.*")
    win.set_focus()
    try:
        # Click the cash tender button
        tender_btn = win.child_window(auto_id="TenderButtonsCash", control_type="ListItem")
        if not tender_btn.exists():
            print("❌ Cash tender button not found")
            return False
            
        tender_btn.click_input()
        print("Clicked on Cash tender button.")
        time.sleep(1)  # Wait for suggestion list to appear

        # Find and interact with the suggestion list
        cash_list = win.child_window(auto_id="SuggestedCashListBox", control_type="List")
        list_items = cash_list.children(control_type="ListItem")
        
        print("💵 Available cash amounts:")
        for item in list_items:
            print(f"- {item.window_text()}")
            
        if list_items:
            # If specific amount is provided, try to find it
            if amount:
                for item in list_items:
                    if amount in item.window_text():
                        item.click_input()
                        print(f"Selected amount: {item.window_text()}")
                        break
            else:
                # Default to first suggestion
                list_items[0].click_input()
                print(f"Selected default amount: {list_items[0].window_text()}")
            
            # Handle receipt popup
            return handle_receipt_popup(app)
        else:
            print("❌ No cash amount suggestions found")
            return False
            
    except Exception as e:
        print(f"Error during cash payment: {e}")
        return False
        
    return True

def main():
    try:
        app = Application(backend="uia").connect(title_re=".*R10PosClient.*")
        success = cash_payment(app)
        if success:
            print("✅ Cash payment completed successfully")
        else:
            print("❌ Cash payment failed")
    except Exception as e:
        print(f"Error connecting to POS client: {e}")

if __name__ == "__main__":
    main()
