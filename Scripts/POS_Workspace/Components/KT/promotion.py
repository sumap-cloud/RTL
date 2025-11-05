from pywinauto.application import Application
import time

def connect_to_app(app_title_re=".*R10PosClient.*"):
    """
    Connects to the running POS application and finds the promotion screen.
    :param app_title_re: Regular expression for the application title.
    :return: The promotion screen window object if successful, otherwise None.
    """
    try:
        app = Application(backend="uia").connect(title_re=app_title_re, found_index=0, timeout=10)
        win = app.window(title_re=app_title_re)
        win.set_focus()
        print("Successfully connected to the R10PosClient application.")
        
        # Find and return the main container for the promotion screen
        promotion_screen = win.child_window(auto_id="WhyDidntGetPromotionsViewID", control_type="Custom")
        promotion_screen.wait('exists', timeout=10)
        print("Promotion screen container found.")
        return promotion_screen
    except Exception as e:
        print(f"Failed to connect or find the promotion screen. Please ensure it is visible. Error: {e}")
        return None

def select_promotion_by_name(promotion_screen, promotion_name):
    """
    Finds a promotion in the list by its name and clicks on it.
    :param promotion_screen: The window object for the promotion screen.
    :param promotion_name: The exact text of the promotion to click.
    :return: True if the promotion was clicked successfully, False otherwise.
    """
    if not promotion_screen:
        print("Error: Invalid promotion screen object provided.")
        return False
    
    try:
        print(f"\n--- Attempting to select promotion: '{promotion_name}' ---")
        promotions_list = promotion_screen.child_window(auto_id="PromotionsList", control_type="List")
        
        # The clickable element is the Text block within the list item
        promotion_item = promotions_list.child_window(title=promotion_name, control_type="Text")
        promotion_item.wait('exists', timeout=5)
        
        print(f"Found promotion: '{promotion_item.window_text()}'")
        promotion_item.click_input()
        print(f"Successfully clicked on '{promotion_name}'.")
        
        # Adding a small delay to observe the result of the action
        time.sleep(2)
        return True
    except Exception as e:
        print(f"\nAn error occurred while trying to select the promotion '{promotion_name}'. Error: {e}")
        return False

# --- Main execution block ---
# This block will only run when the script is executed directly.
if __name__ == "__main__":
    print("--- Running Promotion Screen script ---")
    
    # 1. Connect to the application and get the promotion screen object
    promo_screen_win = connect_to_app()
    
    # 2. Proceed only if the connection was successful
    if promo_screen_win:
        
        # 3. Perform an action, e.g., select a promotion
        success = select_promotion_by_name(promo_screen_win, "REWARDS OFFER")
        
        if success:
            print("\nScript finished successfully.")
        else:
            print("\nScript finished with errors.")

