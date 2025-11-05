from pywinauto.application import Application
import time

# --- Helper Functions (remain mostly unchanged) ---

def connect_to_app(app_title_re=".*R10PosClient.*"):
    """
    Connects to the running POS application.
    :param app_title_re: Regular expression for the application title.
    :return: The main application window object if successful, otherwise None.
    """
    try:
        app = Application(backend="uia").connect(title_re=app_title_re, found_index=0, timeout=10)
        win = app.window(title_re=app_title_re)
        win.set_focus()
        print("Successfully connected to the R10PosClient application.")
        return win
    except Exception as e:
        print(f"Failed to connect to the application. Please ensure it is running. Error: {e}")
        return None

def get_all_promotion_names(promotion_screen):
    """
    Finds all available promotion names by correctly traversing the UI tree.
    :param promotion_screen: The window object for the promotion screen.
    :return: A list of promotion name strings.
    """
    try:
        promotions_list = promotion_screen.child_window(auto_id="PromotionsList", control_type="List")
        promotions_list.wait('visible', timeout=10)

        list_items = promotions_list.children(control_type="ListItem")

        names = []
        if not list_items:
            print("Warning: Found the promotion list, but it appears to be empty (no ListItems).")
            return []

        for item in list_items:
            try:
                # Use descendants() on each item to find the text control,
                # as it may be nested deeper than a direct child.
                name_controls = item.descendants(control_type="Text")
                if name_controls:
                    # The actual promotion name is the first text block found.
                    names.append(name_controls[0].window_text())
            except Exception as e:
                print(f"Warning: A ListItem was found, but an error occurred while reading its text. Error: {e}")
                continue

        if names:
            print(f"Found {len(names)} promotions: {names}")
        else:
            print("Warning: Found ListItems, but could not find any promotion name controls within them.")
        return names
    except Exception as e:
        print(f"An error occurred while getting promotion names. Error: {e}")
        return []

def get_promotion_details(main_win):
    """
    Extracts the text from the promotion details screen by searching within the nested list.
    :param main_win: The main application window object.
    :return: The string containing promotion details, or None if not found.
    """
    try:
        # 1. Find the main container for the details screen
        details_screen = main_win.child_window(auto_id="WhyDidntGetPromotionDetailsViewID", control_type="Custom")
        details_screen.wait('visible', timeout=10)

        # 2. The details are inside another List control on this screen.
        details_list = details_screen.child_window(auto_id="PromotionsList", control_type="List")
        details_list.wait('visible', timeout=10)

        # 3. Find the text block within that list. There should only be one.
        #    Using descendants finds the text control regardless of nesting depth.
        details_text_control = details_list.descendants(control_type="Text")[0]

        return details_text_control.window_text()
    except IndexError:
         print("Error: Found the details list, but it was empty or had no text controls inside.")
         return None
    except Exception as e:
        print(f"Error extracting promotion details: {e}")
        return None

def process_all_promotions(main_win):
    """
    Main workflow to iterate through promotions, get details, and navigate.
    :param main_win: The main application window object.
    :return: Dictionary containing all collected promotion details.
    """
    all_details = {}
    try:
        main_win.set_focus()
        promotion_screen = main_win.child_window(auto_id="WhyDidntGetPromotionsViewID", control_type="Custom")
        promotion_screen.wait('visible', timeout=10)
        print("Promotion list screen found.")

        promotion_names = get_all_promotion_names(promotion_screen)
        if not promotion_names:
            print("No promotions found or could not read the list. Exiting.")
            return None # Return None if no promotions are found

        for name in promotion_names:
            print(f"\n--- Processing promotion: '{name}' ---")

            # Re-find the promotion screen each loop to prevent stale elements
            current_promo_screen = main_win.child_window(auto_id="WhyDidntGetPromotionsViewID", control_type="Custom")

            # CORRECTED: The .descendants() method returns an already-found wrapper object.
            # You cannot call .wait() on it. Click it directly.
            promotion_item = current_promo_screen.descendants(title=name, control_type="Text")[0]
            promotion_item.click_input()
            print(f"Selected '{name}'.")
            time.sleep(1)

            details_button = current_promo_screen.child_window(title="Promotion Details", control_type="Button")
            details_button.wait('ready', timeout=5).click_input()
            print("Clicked 'Promotion Details'.")

            details = get_promotion_details(main_win)
            if details:
                all_details[name] = details
                print("Successfully extracted details.")
            else:
                print(f"Warning: Could not extract details for '{name}'.")

            details_view_screen = main_win.child_window(auto_id="WhyDidntGetPromotionDetailsViewID", control_type="Custom")
            back_button = details_view_screen.child_window(title="Back", control_type="Button")
            back_button.wait('ready', timeout=10).click_input()
            print("Clicked 'Back' to return to the list.")

            # Wait for the main promotion list screen to reappear before the next loop
            main_win.child_window(auto_id="WhyDidntGetPromotionsViewID", control_type="Custom").wait('visible', timeout=10)
            time.sleep(2)

        return all_details

    except Exception as e:
        print(f"\nA critical error occurred during the main workflow. Error: {e}")
        return all_details # Return any details collected before the error

def print_summary(all_details):
    """
    Prints a formatted summary of all collected promotion details.
    :param all_details: A dictionary containing all the promotion data.
    """
    if not all_details:
        print("\n--- No promotion details were collected. ---")
        return

    print("\n\n" + "="*50)
    print("           PROMOTION DETAILS SUMMARY")
    print("="*50)

    for name, details in all_details.items():
        print(f"\nPROMOTION: {name}")
        print("-"*30)
        for line in details.split('\n'):
            print(f"  - {line.strip()}")

    print("\n" + "="*50)

# --- New Reusable Main Function ---
def scrape_promotion_details(app_title_re=".*R10PosClient.*"):
    """
    Connects to the POS application and scrapes details for all promotions.
    :param app_title_re: Regular expression for the application title.
    :return: A dictionary containing all collected promotion details, or None on connection failure.
    """
    print("--- Starting Promotion Screen Automation Script ---")
    main_window = connect_to_app(app_title_re)

    if main_window:
        collected_details = process_all_promotions(main_window)
        return collected_details
    else:
        return None # Indicate connection failure


# --- Main execution block (for running this script directly) ---
if __name__ == "__main__":
    # Example of how to use the reusable function within this file
    scraped_data = scrape_promotion_details()
    if scraped_data is not None: # Check if scraping was attempted (connection successful)
         print_summary(scraped_data)
    else:
         print("Could not connect to the application.")

    print("\nScript finished.")

