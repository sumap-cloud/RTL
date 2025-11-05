from pywinauto.application import Application
import time


#Paidout_relevent_category_name = "Team Recognition"
# --- Configuration ---
app_title = ".*R10PosClient.*"  # Regex for the application title

def select_petty_cash_category(window, category_name):
    """
    Finds and clicks a specific petty cash category button.

    Args:
        window: The pywinauto window object.
        category_name (str): The name of the category to select (e.g., "Team Recognition").
    """
    print(f"\n--- Selecting Petty Cash Category: {category_name} ---")
    try:
        # Based on the screenshot, the categories appear to be standard buttons.
        # We will try to find the button by its title (the text on it).
        category_button = window.child_window(title=category_name, control_type="Button")
        
        if category_button.exists() and category_button.is_enabled():
            print(f"Found '{category_name}' button. Clicking...")
            category_button.click_input()
            print(f"'{category_name}' button clicked successfully.")
        else:
            print(f"Error: '{category_name}' button not found or not enabled.")
            # If this fails, you may need to run with print_control_identifiers()
            # to find a more reliable identifier like an auto_id.
            
    except Exception as e:
        print(f"An error occurred while selecting the category: {e}")


def Paidout_relevent_category_selection(Paidout_relevent_category_name):
    """
    Main function to connect to the app and select the petty cash category.
    """
    try:
        # --- Step 1: Connect to the Application ---
        print(f"Attempting to connect to '{app_title}'...")
        app = Application(backend="uia").connect(title_re=app_title, timeout=20)
        win = app.window(title_re=app_title)
        win.wait('ready', timeout=20)
        win.set_focus()
        print("Successfully connected to the application.")

        # --- Step 2: Select the Category ---
        # This function will find and click the "Team Recognition" button.
        select_petty_cash_category(win, Paidout_relevent_category_name)
        
        time.sleep(1) # Wait for any potential screen transition

        print("\nAutomation script finished.")
        return True  # Indicate success
    
    except Exception as e:
        print(f"A critical error occurred: {e}")

# --- Run the main function ---
if __name__ == "__main__":
    Paidout_relevent_category_selection()

