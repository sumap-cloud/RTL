from pywinauto.application import Application
import time
import pywinauto.mouse

# The specific identifier for the search view/pane
search_view_identifier = "Retalix.Woolworths.Client.POS.Presentation.ViewModels.ViewModels.SearchItemByNameExtensionViewModel"

def perform_item_search(search_term, item_to_select):
    """
    Connects to the POS search view, enters a search term, selects an item,
    and then clicks the 'Sell' button.

    Args:
        search_term (str): The item name to search for.
        item_to_select (str): The full name of the item to select from the results.
    """
    try:
        # 1. Connect to the search view dialog directly.
        print(f"Connecting to application with title: {search_view_identifier}...")
        app = Application(backend="uia").connect(title=search_view_identifier, timeout=30)
        print("Successfully connected to the application process.")
        
        # 2. Get a handle to the main window
        search_dialog = app.window(title=search_view_identifier)
        search_dialog.set_focus()
        print("Focused the search dialog window.")

        # 3. Type the search term using the virtual keyboard.
        print(f"Typing '{search_term}' using the virtual keyboard...")
        for char in search_term.lower():
            if char == ' ':
                print("Pressing the space bar by calculating its position...")
                
                # Find two reliable anchor buttons on the same row as the spacebar.
                at_button = search_dialog.child_window(title="@#&", auto_id="@#&", control_type="Button")
                search_key_button = search_dialog.child_window(title="Search", auto_id="Search", control_type="Button")

                # Get the screen coordinates of the anchor buttons.
                at_rect = at_button.rectangle()
                search_rect = search_key_button.rectangle()

                # Calculate the midpoint between the two buttons to find the spacebar.
                click_x = (at_rect.right + search_rect.left) // 2
                click_y = (at_rect.top + at_rect.bottom) // 2

                # Perform a direct mouse click on the calculated coordinates.
                pywinauto.mouse.click(coords=(click_x, click_y))
                time.sleep(0.1)

            else:
                # For all other characters, use the existing logic.
                key_button = search_dialog.child_window(title=char, auto_id=char, control_type="Button")
                key_button.wait('ready', timeout=5)
                key_button.click_input()
                time.sleep(0.1)

        print("Successfully typed search term using virtual keyboard.")

        # 4. Click the main search button.
        print("Finding and clicking the 'Search' button...")
        search_action_button = search_dialog.child_window(title="Search", auto_id="Search", control_type="Button")
        search_action_button.wait('ready', timeout=10)
        search_action_button.click_input()
        print("Search button clicked.")
        
        # Add a short wait for the grid to populate
        time.sleep(2)

        # 5. Wait for results and select the desired item.
        print(f"Searching for and selecting item: '{item_to_select}'...")
        
        item_text_control = search_dialog.child_window(title=item_to_select, control_type="Text")
        item_text_control.wait('visible', timeout=15)
        item_text_control.click_input()
        print("Successfully selected the item.")

        # 6. Click the 'Sell' button to add the item to the transaction.
        print("Finding and clicking the 'Sell' button...")
        sell_button = search_dialog.child_window(title="Sell", auto_id="SellButton", control_type="Button")
        sell_button.wait('ready', timeout=10)
        sell_button.click_input()
        print("'Sell' button clicked.")

        time.sleep(5)
        print("Script finished successfully!")
        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

# --- Main execution ---
if __name__ == "__main__":
    item_to_search_for = "hw cigars"
    # This name must exactly match the text in the search results.
    item_to_select_from_list = "Henri Wintermans Cf Creme Cigars 10pk"
    
    perform_item_search(item_to_search_for, item_to_select_from_list)

