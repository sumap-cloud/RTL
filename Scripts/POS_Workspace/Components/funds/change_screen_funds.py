# ==== COMPONENT DOCUMENTATION CHECKLIST ====
# @Component: chnagescreen_funds
# @Purpose: Captures payment confirmation details from the POS final screen
# @Dependencies: pywinauto.application.Application, re
# @Input_Params: None
# @Return_Values: Dictionary with amount, thank_you_message, and goodbye_message
# @Used_By_Tests: TC001_paidout, Other funds management tests
# @Known_Limitations: Relies on specific UI elements and text patterns
# ============================================

from pywinauto.application import Application
import time
import re

def chnagescreen_funds():
    """
    Connects to the POS client, finds the transparent popup window,
    and captures the total amount, "Thank You" message, and "Goodbye"
    message using specific properties found during debugging.
    """
    app_title_regex = ".*R10PosClient.*"
    
    try:
        print(f"Attempting to connect to application with title regex: '{app_title_regex}'...")
        app = Application(backend="uia").connect(title_re=app_title_regex, timeout=20)
        print("Successfully connected to the main application.")

        print("\nSearching for the popup window with AutomationId: 'TransparentWindowID'...")
        popup_window = app.window(auto_id="TransparentWindowID")
        popup_window.wait('visible', timeout=30)
        print(">>> SUCCESS: Found the popup window.")

        print("Searching for the amount control inside the popup...")
        amount_control = popup_window.child_window(
            control_type="Custom",
            title_re=r"[\d,]+\.\d{2}"
        ).wait('visible', timeout=10)
        final_amount = amount_control.window_text()
        print(f">>> SUCCESS: Found Final Amount: ${final_amount}")

        print("Searching for the 'Thank You' message control...")
        message_control = popup_window.child_window(
            title="Thank You for Shopping with Us",
            control_type="Text"
        ).wait('visible', timeout=10)
        thank_you_message = message_control.window_text()
        print(f">>> SUCCESS: Found Message: '{thank_you_message}'")

        print("Searching for the 'Goodbye' message control...")
        goodbye_control = popup_window.child_window(
            title="Goodbye",
            control_type="Text"
        ).wait('visible', timeout=10)
        goodbye_message = goodbye_control.window_text()
        print(f">>> SUCCESS: Found Message: '{goodbye_message}'")

        print("Searching for the 'Total Amount:' title control...")
        title_control = popup_window.child_window(
            title="Total Amount:",
            control_type="Text"
        ).wait('visible', timeout=10)
        total_amount_title = title_control.window_text()
        print(f">>> SUCCESS: Found Title: '{total_amount_title}'")

        # --- Final Output Summary ---
        print("\n================= Change Screen  Summary =================")
        print(f"{total_amount_title} {final_amount}")
        print(f"Message: {thank_you_message}")
        print(f"message: {goodbye_message}")
        print("=======================================================")

        return True

    except Exception as e:
        print(f"An error occurred while trying to find the final amount or message: {e}")
        return False


if __name__ == "__main__":
    chnagescreen_funds()
 