# ==== COMPONENT DOCUMENTATION CHECKLIST ====
# @Component: handle_chnagescreen_refunds
# @Purpose: Captures and validates data from the final refund summary screen
# @Dependencies: pywinauto.application.Application
# @Input_Params: None
# @Return_Values: Dictionary with refund details or None if failed
# @Used_By_Tests: TC008_nrr_scenario, Other refund-related tests
# @Known_Limitations: Read-only, does not handle further interactions
# ============================================

from pywinauto.application import Application
import time

def handle_chnagescreen_refunds():
    """
    Connects to the POS application, finds the final "Please Close Drawer"
    refund summary pop-up, and captures all visible text elements.

    This function is designed for data validation and does not perform
    any click actions.

    Returns:
        dict: A dictionary containing the captured screen details
              (header, title, tender_details, message, sub_message)
              if successful, otherwise None.
    """
    application_window_title = ".*R10PosClient.*"
    
    try:
        print(f"Connecting to application with title matching: '{application_window_title}'...")
        app = Application(backend="uia").connect(title_re=application_window_title, timeout=30)
        
        print("Application connected. Looking for the main window...")
        win = app.window(title_re=application_window_title)
        win.set_focus()
        print("Main window focused.")

        print("Looking for the refund popup window...")
        popup_window = app.window(auto_id="TransparentWindowID")
        popup_window.wait('ready visible', timeout=20) 
        print("Refund popup window found.")

        # --- Text Extraction Logic ---
        # Target specific controls based on debug information to get text content.

        print("Capturing screen elements...")
        header_text = popup_window.child_window(title="Please Close Drawer", control_type="Text").window_text()
        title_text = popup_window.child_window(title="Refund", control_type="Text").window_text()
        cash_label_text = popup_window.child_window(title="Cash: ", control_type="Text").window_text()
        amount_text = popup_window.child_window(title="60.00", control_type="Custom").window_text()
        message_text = popup_window.child_window(title="Thank You for Shopping with Us", control_type="Text").window_text()
        sub_message_text = popup_window.child_window(title="Goodbye", control_type="Text").window_text()
        
        full_tender_text = f"{cash_label_text.strip()} ${amount_text}"
        
        screen_data = {
            "header": header_text,
            "title": title_text,
            "tender_details": full_tender_text,
            "message": message_text,
            "sub_message": sub_message_text,
        }
        
        print(">>> SUCCESS: All elements captured.")
        return screen_data

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Please ensure the application and the correct popup window are open and visible.")
        return None

if __name__ == "__main__":
    """
    This block allows the script to be run directly for testing purposes.
    """
    print("--- Running Final Refund Screen Handler in Standalone Mode ---")
    
    # Add a small delay to ensure the UI is ready before the script runs
    time.sleep(2)
    
    captured_data = handle_chnagescreen_refunds()

    if captured_data:
        print("\n================= Final Screen Summary =================")
        print(f"Header: {captured_data.get('header', 'N/A')}")
        print(f"Title: {captured_data.get('title', 'N/A')}")
        print(f"Tender Details: {captured_data.get('tender_details', 'N/A')}")
        print(f"Message: {captured_data.get('message', 'N/A')}")
        print(f"Sub-Message: {captured_data.get('sub_message', 'N/A')}")
        print("=======================================================")
        print("\n✅ Standalone test completed successfully.")
    else:
        print("\n❌ Standalone test failed.")

