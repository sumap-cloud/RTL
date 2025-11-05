# Import the necessary library for UI automation
from pywinauto.application import Application
import time
import re

def connect_to_pos():
    """
    Connects to the main application window.
    Returns tuple: (app, win, is_connected)
    """
    try:
        print("Connecting to the POS application...")
        app = Application(backend="uia").connect(title_re=".*R10PosClient.*")
        win = app.window(title_re=".*R10PosClient.*")
        win.set_focus()
        print("Successfully connected to the main window.")
        win.wait('ready', timeout=30)
        return app, win, True
    except Exception as e:
        print(f"An error occurred during connection: {e}")
        print("Please ensure the R10PosClient application is running and tender options are visible.")
        return None, None, False

def capture_tenders():
    """
    Connects to the R10PosClient application and captures the list of tender types.
    """
    try:
        # Connect to the running POS application using its title.
        # We specify the backend as "uia" for modern applications.
        print("Connecting to the POS application...")
        app = Application(backend="uia").connect(title_re=".*R10PosClient.*")
        win = app.window(title_re=".*R10PosClient.*")
        win.set_focus()
        print("Successfully connected to the main window.")
        
        # Wait for the window to be ready
        win.wait('ready', timeout=30)

        # Find the ListBox that contains the tender buttons using its automation ID.
        # This is a more reliable way to find controls than navigating the entire hierarchy.
        print("Searching for the tender list container...")
        tender_list_box = win.child_window(auto_id="TenderButtons", control_type="List")
        
        if not tender_list_box.exists():
            print("Error: Could not find the tender list container (auto_id='TenderButtons').")
            return []

        print("Tender list container found.")

        # Get all the child items within the ListBox. These are the tender buttons.
        tender_items = tender_list_box.children(control_type="ListItem")

        # Extract the text (the tender name) from each item.
        tender_names = [item.window_text() for item in tender_items]
        
        print("Successfully captured tender names.")
        
        return tender_names

    except Exception as e:
        # Handle potential errors, such as the application not running
        # or the window structure being different than expected.
        print(f"An error occurred: {e}")
        print("Please ensure the R10PosClient application is running and the tender page is visible.")
        return None

def select_tender(tender_name):
    """
    Connects to the R10PosClient application and selects a specific tender by name.
    
    Args:
        tender_name (str): The name of the tender to select (e.g., "EFT").
    """
    try:
        print("\nConnecting to the POS application to select a tender...")
        app = Application(backend="uia").connect(title_re=".*R10PosClient.*")
        win = app.window(title_re=".*R10PosClient.*")
        win.set_focus()
        print("Successfully connected to the main window.")
        win.wait('ready', timeout=30)

        print(f"Searching for tender button: '{tender_name}'...")
        
        # We find the ListItem that corresponds to the tender.
        # The title of the ListItem is the name of the tender.
        tender_list_item = win.child_window(title=tender_name, control_type="ListItem")

        if not tender_list_item.exists():
            print(f"Error: Could not find the list item for tender '{tender_name}'.")
            return False

        # Within that ListItem, we find and click the button.
        # This is more specific than searching for any button with the title.
        tender_button = tender_list_item.child_window(control_type="Button")
        
        if tender_button.exists():
            print(f"Tender '{tender_name}' found. Clicking...")
            tender_button.click_input() # Use click_input() for a more robust click
            print(f"Successfully clicked the '{tender_name}' tender button.")
            return True
        else:
            print(f"Error: Could not find the clickable button within the '{tender_name}' list item.")
            return False

    except Exception as e:
        print(f"An error occurred while trying to select the tender: {e}")
        print("Please ensure the R10PosClient application is running and the tender page is visible.")
        return False

def get_tender_options(win):
    """
    Captures the list of tender sub-options available on the screen.
    It can handle both cash suggestions and other types like cheque.
    
    Args:
        win: The main window object from pywinauto
        
    Returns:
        list: List of available tender options, or None if error occurred
    """
    if not win:
        print("No valid window connection. Cannot get options.")
        return None
    
    try:
        print("Searching for tender sub-option buttons...")
        options = []
        
        # --- Logic for Cash Tender Suggestions ---
        cash_list_box = win.child_window(auto_id="SuggestedCashListBox", control_type="List")
        if cash_list_box.exists():
            print("Cash suggestion panel detected.")
            # Get suggested cash amounts from the list
            list_items = cash_list_box.children(control_type="ListItem")
            for item in list_items:
                # Use .descendants() to find the Custom control nested inside
                amount_controls = item.descendants(control_type="Custom")
                if amount_controls:
                    options.append(amount_controls[0].window_text())
            
            # Check for the "Manual Entry" button separately
            manual_entry_btn = win.child_window(auto_id="btnManualAmountEntryID", control_type="Button")
            if manual_entry_btn.exists():
                options.append("Manual Entry")
        
        # --- Fallback Logic for Cheque/Other Tenders ---
        else:
            print("Checking for other tender types (e.g., Cheque)...")
            all_buttons = win.descendants(control_type="Button")
            option_buttons = [btn for btn in all_buttons if btn.automation_id().startswith("TenderCommandTemplate")]

            for button in option_buttons:
                text_elements = button.children(control_type="Text")
                if text_elements:
                    option_name = text_elements[0].window_text()
                    if option_name:
                        options.append(option_name)

        if not options:
            print("Error: Could not find any tender sub-options.")
            return []

        print("Successfully captured sub-options.")
        return options
    except Exception as e:
        print(f"An error occurred while getting sub-options: {e}")
        return None

def select_tender_option(win, option_name):
    """
    Selects a specific tender sub-option by its name.
    
    Args:
        win: The main window object from pywinauto
        option_name (str): The name of the option to select (e.g., "15.00" or "Temporary Cheque").
        
    Returns:
        bool: True if selection was successful, False otherwise
    """
    if not win:
        print(f"No valid window connection. Cannot select '{option_name}'.")
        return False
    
    try:
        print(f"Attempting to select option: '{option_name}'")
        button_to_click = None
        
        # --- Logic for Cash Options ---
        if option_name == "Manual Entry":
            button_to_click = win.child_window(auto_id="btnManualAmountEntryID", control_type="Button")
        else:
            # Find by text for cash amounts, as their button ID is dynamic
            # Filter descendants manually for UIA backend compatibility
            all_custom_controls = win.descendants(control_type="Custom")
            custom_controls = [c for c in all_custom_controls if c.window_text() == option_name]

            if custom_controls:
                # The parent of the custom text control is the button we need to click
                button_to_click = custom_controls[0].parent()

        # --- Fallback/Logic for Cheque/Other Tenders ---
        if not button_to_click:
            # Do not remove spaces from the option name for the auto_id
            target_auto_id = f"TenderCommandTemplate{option_name}"
            # Filter descendants manually for UIA backend compatibility
            all_buttons = win.descendants(control_type="Button")
            buttons = [btn for btn in all_buttons if btn.automation_id() == target_auto_id]
            
            if buttons:
                button_to_click = buttons[0]

        # --- Click the found button ---
        if button_to_click:
            print(f"Option '{option_name}' found. Clicking...")
            button_to_click.click_input()
            print(f"Successfully clicked the '{option_name}' button.")
            return True
        else:
            print(f"Error: Could not find the button for option '{option_name}'.")
            return False

    except Exception as e:
        print(f"An error occurred while trying to select the option: {e}")
        return False

def process_tender(tender_name=None, tender_option=None, list_only=False, list_tenders=False):
    """
    Unified method for all tender operations:
    - List available tenders
    - List available tender sub-options
    - Select a specific tender
    - Select a specific tender sub-option
    - Complete workflow (tender + sub-option)
    
    Args:
        tender_name (str, optional): The name of the tender to select (e.g., "Cash", "Cheque").
        tender_option (str, optional): The sub-option to select after tender selection.
        list_only (bool): If True, only lists available sub-options without selecting anything.
        list_tenders (bool): If True, only lists available tenders without selecting anything.
        
    Returns:
        dict: Contains success status, captured data, and operation results
              Format: {
                  'success': bool,
                  'tenders': list or None,
                  'options': list or None,
                  'tender_selected': bool,
                  'option_selected': bool,
                  'message': str
              }
    """
    result = {
        'success': False,
        'tenders': None,
        'options': None,
        'tender_selected': False,
        'option_selected': False,
        'message': ''
    }
    
    print(f"\n=== Starting Tender Processing ===")
    
    # Operation 1: List all available tenders
    if list_tenders or (not tender_name and not list_only):
        print("Capturing available tenders...")
        captured_tenders = capture_tenders()
        result['tenders'] = captured_tenders
        
        if captured_tenders is not None:
            print("\n--- Available Tenders ---")
            if captured_tenders:
                for tender in captured_tenders:
                    print(f"- {tender}")
                result['message'] += f"Found {len(captured_tenders)} tenders. "
            else:
                print("No tenders were found.")
                result['message'] += "No tenders found. "
            print("------------------------")
        
        # If only listing tenders, return here
        if list_tenders:
            result['success'] = captured_tenders is not None
            return result
    
    # Operation 2: Connect to POS for further operations
    if tender_name or list_only:
        app, win, is_connected = connect_to_pos()
        if not is_connected:
            result['message'] += "Failed to connect to POS application."
            return result
    
    # Operation 3: Select tender if specified
    if tender_name:
        print(f"Selecting tender: '{tender_name}'")
        tender_success = select_tender(tender_name)
        result['tender_selected'] = tender_success
        
        if not tender_success:
            result['message'] += f"Failed to select tender '{tender_name}'."
            return result
        
        result['message'] += f"Successfully selected tender '{tender_name}'. "
        
        # Wait for UI to update after tender selection
        if tender_option or list_only:
            print("Waiting for sub-options to appear...")
            time.sleep(2)
            
            # Reconnect to get updated window state
            app, win, is_connected = connect_to_pos()
            if not is_connected:
                result['message'] += "Failed to reconnect for sub-option operations."
                return result
    time.sleep(3)  # Ensure UI is ready before proceeding
    # Operation 4: Get and display available sub-options
    if (tender_name and tender_option) or list_only:
        print("Capturing available sub-options...")
        available_options = get_tender_options(win)
        result['options'] = available_options
        
        if available_options is not None:
            print("\n--- Available Tender Sub-Options ---")
            if available_options:
                for option in available_options:
                    print(f"- {option}")
                result['message'] += f"Found {len(available_options)} sub-options. "
            else:
                print("No tender sub-options were found.")
                result['message'] += "No sub-options found. "
            print("------------------------------------")
        
        # If only listing options, return here
        if list_only:
            result['success'] = available_options is not None
            return result
    
    # Operation 5: Select sub-option if specified
    if tender_option and win:
        print(f"Selecting sub-option: '{tender_option}'")
        option_success = select_tender_option(win, tender_option)
        result['option_selected'] = option_success
        
        if not option_success:
            result['message'] += f"Failed to select sub-option '{tender_option}'."
            return result
        
        result['message'] += f"Successfully selected sub-option '{tender_option}'. "
    
    # Determine overall success
    if list_tenders:
        result['success'] = result['tenders'] is not None
    elif list_only:
        result['success'] = result['options'] is not None
    elif tender_name and tender_option:
        result['success'] = result['tender_selected'] and result['option_selected']
    elif tender_name:
        result['success'] = result['tender_selected']
    else:
        result['success'] = result['tenders'] is not None
    
    if result['success']:
        print(f"\n=== Tender Processing Completed Successfully ===")
    else:
        print(f"\n=== Tender Processing Failed ===")
    
    print(f"Result: {result['message']}")
    return result

def validate_tender_options(option_to_select):
    """
    Main function to validate tender options without using a class.
    This function demonstrates the complete workflow for sub-options only.
    """
    # Connect to the POS application
    app, win, is_connected = connect_to_pos()
    
    # Proceed only if the connection was successful
    if is_connected and win:
        # Get the available sub-options
        options = get_tender_options(win)

        if options is not None:
            print("\n--- Available Tender Sub-Options ---")
            if options:
                for option in options:
                    print(f"- {option}")
            else:
                print("No tender sub-options were found.")
            print("------------------------------------")
        
        # --- Example of selecting an option ---
        success = select_tender_option(win, option_to_select)
        if success:
            print(f"Option '{option_to_select}' selection successful.")
        else:
            print(f"Option '{option_to_select}' selection failed.")
            
        return options, success
    else:
        print("Failed to connect to POS application.")
        return None, False

if __name__ == "__main__":
    # --- Example Usage of the Unified process_tender Method ---
    
    # # Example 1: List all available tenders only
    # print("=== Example 1: List All Tenders ===")
    # result = process_tender(list_tenders=True)
    
    # # Example 2: Select a tender only (no sub-option)
    # print("\n=== Example 2: Select Tender Only ===")
    # result = process_tender(tender_name="Cheque")
    
    # # Example 3: Complete workflow - select tender and sub-option
    # print("\n=== Example 3: Complete Workflow ===")
    # result = process_tender(tender_name="Cash", tender_option="15.00")
    
    # # Example 4: List sub-options only (after manually selecting a tender)
    # print("\n=== Example 4: List Sub-Options Only ===")
    # result = process_tender(list_only=True)
    
    # Example 5: Select different tender and sub-option
    print("\n=== Example 5: Another Complete Workflow ===")
    result = process_tender(tender_name="EFT")
    