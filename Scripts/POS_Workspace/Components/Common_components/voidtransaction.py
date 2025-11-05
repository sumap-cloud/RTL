from pywinauto import Application
import time
from Approvalrequired import handle_approval_popup
from ResonCode_popup import handle_select_reason_code_popup

def handle_void_transaction(win=None):
    """
    Handle void transaction including approval and reason code flows.
    If multiple "Void Transaction" buttons exist, it clicks the last one.
    Returns:
        bool: True if void transaction was successful, False otherwise
    """
    try:
        # Connect to POS if window not provided
        if not win:
            app = Application(backend="uia").connect(title_re=".*R10PosClient.*")
            win = app.window(title_re=".*R10PosClient.*")
            win.set_focus()
        else:
            app = win.top_level_parent().parent()  # Get the application instance

        # Find all "Void Transaction" buttons and click the last one, as multiple may exist
        void_transaction_buttons = win.descendants(title="Void Transaction", control_type="Button")
        if void_transaction_buttons:
            # Select and click the last button found
            void_transaction_buttons[-1].click_input()
            print("✓ Clicked the last 'Void Transaction' button")
            
            # Wait for potential approval dialog
            time.sleep(4)
            
            # Handle potential approval (always continue the flow)
            handle_approval_popup(approval_required=True)
            
            # Wait briefly for any UI updates
            time.sleep(2)
            
            # Handle reason code selection
            try:
                handle_select_reason_code_popup(app)
                print("✓ Reason code selected successfully")
            except Exception as e:
                print(f"! Note: {e}, continuing...")
            
            print("✓ Void transaction completed")
            return True
        else:
            print("✗ Void Transaction button not found")
            return False
            
    except Exception as e:
        print(f"✗ Error in void transaction: {e}")
        return False

if __name__ == "__main__":
    # Test the function
    if handle_void_transaction():
        print("\nVoid transaction process completed successfully")
    else:
        print("\nVoid transaction process failed")

