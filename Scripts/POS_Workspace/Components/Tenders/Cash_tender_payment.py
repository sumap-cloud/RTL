import time
from pywinauto import Application
from pywinauto.findwindows import ElementNotFoundError
from pywinauto.timings import TimeoutError

def connect_to_app():
    """Connects to the running R10PosClient application and returns the app object."""
    try:
        app = Application(backend="uia").connect(title_re=".*R10PosClient.*")
        print("✅ Successfully connected to the application.")
        return app
    except ElementNotFoundError:
        print("❌ Application 'R10PosClient' not found. Please make sure it is running.")
        return None

def process_tenders(app, tender_to_select="Cash"):
    """
    Finds available tender types on the screen, selects one, and handles the
    suggestion list that appears.
    
    Args:
        app: The pywinauto Application object connected to the POS client.
        tender_to_select (str): The name of the tender to select (e.g., "Cash").
    """
    try:
        # Connect to the main application window
        win = app.window(title_re=".*R10PosClient.*")
        win.set_focus()
        print("✅ Successfully focused on the R10PosClient window.")

        # --- 1. Find and list all available tender buttons ---
        print("\n🔎 Finding all available tender types...")
        
        buttons = win.descendants(control_type="Button")
        list_items = win.descendants(control_type="ListItem")
        all_potential_controls = buttons + list_items

        all_tender_buttons = [
            child for child in all_potential_controls
            if child.automation_id().startswith("TenderButtons")
        ]
        
        if not all_tender_buttons:
            print("❌ No tender buttons found. Please check the window identifiers.")
            return False

        print("📋 Available tender types found:")
        tender_names = [btn.window_text() for btn in all_tender_buttons]
        for name in tender_names:
            print(f"- {name}")

        # --- 2. Select the specified tender button ---
        if tender_to_select not in tender_names:
            print(f"❌ The tender '{tender_to_select}' is not in the available list.")
            return False
            
        print(f"\n▶️ Selecting '{tender_to_select}' tender...")
        tender_btn_found = None
        for btn in all_tender_buttons:
            if btn.window_text() == tender_to_select:
                tender_btn_found = btn
                break
        
        if tender_btn_found:
            tender_btn_found.click_input()
            print(f"✅ Clicked on '{tender_to_select}' tender button.")
        else:
            # This case should ideally not be reached due to the check above
            print(f"❌ Could not re-locate the '{tender_to_select}' button to click it.")
            return False

        time.sleep(1)  # Wait for the suggestion list to appear

        # --- 3. Find and select from the suggestion list ---
        print(f"\n🔎 Looking for '{tender_to_select}' suggestion list...")
        suggestion_list_id = f"Suggested{tender_to_select}ListBox"
        
        try:
            suggestion_list = win.child_window(auto_id=suggestion_list_id, control_type="List")
            suggestion_list.wait('visible', timeout=5) # Wait for the list to be visible
            list_items = suggestion_list.children(control_type="ListItem")
        except (ElementNotFoundError, TimeoutError):
             print(f"⚠️ Suggestion list for '{tender_to_select}' did not appear or was not found.")
             # Depending on the workflow, you might want to return True here if this is not a critical error
             return True


        if not list_items:
            print(f"✅ No suggestion items found for '{tender_to_select}', which may be expected. Continuing.")
            return True

        print("💵 Suggested cash list items:")
        for item in list_items:
            print(f"- {item.window_text()}")
        
        # Click the first suggested item
        first_item = list_items[0]
        first_item_text = first_item.window_text()
        first_item.click_input()
        print(f"✅ Clicked on the first list item: {first_item_text}")

        print("\n✅ Tender processing complete.")
        return True

    except ElementNotFoundError as e:
        print(f"\n❌ Error: A UI element was not found. Please ensure the application is in the correct state.")
        print(f"Details: {e}")
        return False
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")
        return False

def main():
    """Main function to connect to the app and run the tender processing."""
    print("--- Starting Tender Processing Script ---")
    app = connect_to_app()
    if app:
        # You can change "Cash" to any other tender type to test
        process_tenders(app, tender_to_select="Cash")
    print("\n--- Script Finished ---")


# This block ensures that main() is called only when the script is executed directly
if __name__ == "__main__":
    main()

