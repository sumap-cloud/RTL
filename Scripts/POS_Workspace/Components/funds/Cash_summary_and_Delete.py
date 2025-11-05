from pywintypes import Time
from pywinauto.application import Application
import time
import re
import json

# --- Configuration ---
app_title = ".*R10PosClient.*"  # Regex for the application title
# Using a dictionary to map numpad digits to their control identifiers.

def capture_cash_summary(window):
    """
    Finds the cash summary list, captures all entries by handling pagination,
    and adds a calculation check to verify the total amount for each row.

    Args:
        window: The pywinauto window object.
    
    Returns:
        A list of dictionaries, where each dictionary represents a row in the summary.
    """
    print("\n--- Capturing Cash Summary ---")
    summary_data = []
    processed_items = set() # To keep track of items we've already processed to avoid duplicates
    try:
        summary_list = window.child_window(auto_id="SummaryList", control_type="List")
        down_arrow = window.child_window(auto_id="ListPagerButtonDown", control_type="Button")

        if not summary_list.exists():
            print("Error: Cash summary list (auto_id='SummaryList') not found.")
            return summary_data

        while True:
            summary_items = summary_list.children(control_type="ListItem")
            
            new_items_found = False
            for item in summary_items:
                # Create a unique identifier for the item to check if we've seen it before
                item_text = "".join([child.window_text() for child in item.children()])
                if item_text not in processed_items:
                    new_items_found = True
                    processed_items.add(item_text)
                    
                    item_details = item.children()
                    row_data = {}
                    if len(item_details) >= 3:
                        denomination_str = item_details[0].texts()[0]
                        quantity_str = item_details[1].texts()[0]
                        reported_total_str = item_details[2].texts()[0]
                        
                        row_data['Denomination'] = denomination_str
                        row_data['Qty'] = quantity_str
                        row_data['Reported_Total'] = reported_total_str

                        try:
                            denom_val = float(re.sub(r'[^\d.]', '', denomination_str))
                            qty_val = int(re.sub(r'[^\d]', '', quantity_str))
                            calculated_total = f"${denom_val * qty_val:,.2f}"
                            row_data['Calculated_Total'] = calculated_total
                        except (ValueError, IndexError):
                            row_data['Calculated_Total'] = "Error"
                        
                        summary_data.append(row_data)

            if not down_arrow.is_enabled() or not new_items_found:
                break # Exit loop if down arrow is disabled or no new items are found

            print("Down arrow is enabled, clicking to see more entries...")
            down_arrow.click_input()
            time.sleep(0.5) # Wait for UI to update

        print(f"Found a total of {len(summary_data)} item(s) in the summary.")
        return summary_data

    except Exception as e:
        print(f"An error occurred while capturing the cash summary: {e}")
        return summary_data

def delete_all_summary_items(window):
    """
    Selects and deletes each item from the cash summary list one by one.

    Args:
        window: The pywinauto window object.
    """
    print("\n--- Deleting All Cash Summary Items ---")
    try:
        summary_list = window.child_window(auto_id="SummaryList", control_type="List")
        delete_button = window.child_window(title="Delete", auto_id="DeleteButton", control_type="Button")

        if not summary_list.exists() or not delete_button.exists():
            print("Error: Could not find the summary list or the delete button.")
            return

        # Loop as long as there are items in the list
        while summary_list.children(control_type="ListItem"):
            # Always select the first item in the list
            first_item = summary_list.children(control_type="ListItem")[0]
            item_text = first_item.children()[0].window_text()
            print(f"Selecting item: {item_text}")
            
            # Click to select the item
            first_item.click_input()
            time.sleep(0.2) # Brief pause to ensure selection registers

            # Click the delete button
            if delete_button.is_enabled():
                print("Clicking Delete button...")
                delete_button.click_input()
                time.sleep(0.5) # Wait for the UI to update after deletion
            else:
                print("Delete button is not enabled. Stopping deletion.")
                break
        
        print("All items have been deleted from the summary.")

    except Exception as e:
        print(f"An error occurred during the deletion process: {e}")


def delete_summary_funds():
    """
    Connects to the application, enters a quantity, verifies the cash summary,
    and then deletes all items from the summary.

    Args:
        quantity (str): The quantity to enter as a string.
    """
    try:
        print(f"Connecting to application with title regex: {app_title}")
        # Connect to an already running application
        app = Application(backend="uia").connect(title_re=app_title)

        # Get the main window
        main_window = app.window(title_re=app_title)
        main_window.set_focus() # Bring the window to the foreground

        print("Application connected successfully.")

        # Define the sequence of keys to press
        #keys_to_press = list(quantity) + ['OK']

        # Call the function to press the numpad keys
        #press_numpad_keys(main_window, keys_to_press)
        #print("Quantity entry complete.")

        # Wait a moment for the summary to update
        time.sleep(1)

        # Capture and verify the cash summary
        summary_details = capture_cash_summary(main_window)
        
        print("\n--- Verifying Cash Summary Details ---")
        if not summary_details:
            print("No data captured from the summary to verify.")
        else:
            for i, row in enumerate(summary_details):
                print(f"\n--- Row {i+1} ---")
                print(f"  Denomination: {row.get('Denomination', 'N/A')}")
                print(f"  Quantity: {row.get('Qty', 'N/A')}")
                print(f"  Reported Total: {row.get('Reported_Total', 'N/A')}")
                
                # Verification Step
                reported = row.get('Reported_Total', '')
                calculated = row.get('Calculated_Total', '')
                # Normalize by removing currency symbols and commas for comparison
                is_match = re.sub(r'[^\d.]', '', reported) == re.sub(r'[^\d.]', '', calculated)

                if is_match:
                    print(f"  Verification: PASSED (Reported total matches calculated total: {calculated})")
                else:
                    print(f"  Verification: FAILED (Reported: {reported}, Calculated: {calculated})")
        
        # Finally, delete all the items from the summary
        delete_all_summary_items(main_window)
        return True


    except Exception as e:
        print(f"An error occurred: {e}")
        print("Please ensure the application is running and the title matches the regex.")

# --- Main Execution ---
#if __name__ == "__main__":
    # This is where you specify the quantity you want to enter.
    #quantity_to_enter = "5"
    #delete_summary_funds()
