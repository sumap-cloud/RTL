from pywinauto.application import Application
import time

def capture_and_interact(button_title_to_click=None):
    """
    Connects to the R10PosClient application, captures UI elements
    from the 'Enhanced Reprint' screen, and optionally clicks a button.

    Args:
        button_title_to_click (str, optional): The exact title of the button to click
                                             (e.g., 'Search transaction').
                                             Defaults to None.
    """
    try:
        # Connect to the application
        app = Application(backend="uia").connect(title_re=".*R10PosClient.*")
        win = app.window(title_re=".*R10PosClient.*")
        win.set_focus()
        print("Successfully connected to the application.")

        # --- Dictionaries to store captured elements by section ---
        all_elements = {}
        header_elements = {}
        left_panel_elements = {}

        # --- Capture Header Elements ---
        enhanced_reprint_view = win.child_window(auto_id="RePrintRightViewID", control_type="Custom")
        if enhanced_reprint_view.exists():
            header_elements['header_text'] = enhanced_reprint_view.child_window(
                title="Enhanced Reprint", auto_id="MainHeader", control_type="Text"
            )
        else:
             print("Enhanced Reprint view not found.")
             return

        # --- Capture Left Panel Elements ---
        reprint_transaction_view = win.child_window(auto_id="ReprintTransactionByBarcodeViewID", control_type="Custom")
        if reprint_transaction_view.exists():
            # This static text does not have a unique ID, so we find it by its name within the parent.
            try:
                left_panel_elements['load_transaction_label'] = reprint_transaction_view.child_window(
                    title_re="Load Transaction Using.*", control_type="Text"
                )
            except Exception:
                 left_panel_elements['load_transaction_label'] = None # Element not found

            left_panel_elements['search_transaction_button'] = reprint_transaction_view.child_window(
                title="Search transaction", auto_id="ActionCommandButtonTempletButtonSearch transaction", control_type="Button"
            )
            left_panel_elements['reprint_pickup_button'] = reprint_transaction_view.child_window(
                title="Reprint PickUp", auto_id="ActionCommandButtonTempletButtonReprint PickUp", control_type="Button"
            )
            left_panel_elements['cancel_button'] = reprint_transaction_view.child_window(
                title="Cancel", auto_id="GenericCommandButtonTemplete_Cancel", control_type="Button"
            )
            left_panel_elements['reprint_button'] = reprint_transaction_view.child_window(
                title="Reprint", auto_id="GenericCommandButtonTemplete_Reprint", control_type="Button"
            )
        else:
            print("Could not find the left panel (ReprintTransactionByBarcodeViewID).")

        # Combine all captured elements for easier access
        all_elements.update(header_elements)
        all_elements.update(left_panel_elements)

        # --- Print details of captured elements in a simplified format ---
        print("\n\n==========================================")
        print("      ENHANCED REPRINT SCREEN CAPTURE")
        print("==========================================")

        sections_for_printing = {
            "Header": header_elements,
            "Left Panel": left_panel_elements,
        }

        for section_name, elements in sections_for_printing.items():
            print(f"\n--- {section_name} Elements ---")
            if not elements:
                print("  No elements captured in this section.")
                continue
            
            for name, element in elements.items():
                if element and element.exists():
                    print(f"  -> Found '{name}': '{element.element_info.name}'")
                else:
                    print(f"  -> '{name}' was not found.")
        
        print("\n==========================================")


        # --- Perform Actions Based on Parameter ---
        if button_title_to_click:
            print(f"\n--- ACTION: Clicking button with title '{button_title_to_click}' ---")
            element_to_click = None
            
            # Find the element in our dictionary that has the matching title
            for element in all_elements.values():
                if element and element.exists() and element.element_info.name == button_title_to_click:
                    element_to_click = element
                    break

            if element_to_click:
                element_to_click.click()
                print(f"Successfully clicked the '{button_title_to_click}' button.")
                time.sleep(2) # Wait a moment for the UI to respond
            else:
                print(f"Could not perform click. Button with title '{button_title_to_click}' was not found.")
        else:
            print("\n--- ACTION: No button click requested. ---")

    except Exception as e:
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    # Example: Run the script and click the "Search transaction" button.
    # The button title must be an exact match.
    capture_and_interact(button_title_to_click="Search transaction")
    
    
    
    # To run the script without clicking any button, call it without arguments:
    # capture_and_interact()

