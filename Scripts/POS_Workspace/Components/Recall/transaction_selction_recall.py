from pywinauto import Application, findwindows, timings
from pathlib import Path
import sys
import time

def find_transaction():
    """
    This function automates interactions on the 'Find Transaction' screen of the POS system.
    It identifies the POS number input, the list of saved transactions, and key buttons.
    It then prints all transactions, selects the first one, and clicks 'Recall'.
    """
    # Using the exact window title from the control identifiers
    application_window_title = "R10PosClient"

    try:
        print("Connecting to the POS application...")
        app = Application(backend="uia").connect(title=application_window_title, timeout=20)
        
        win = app.window(title=application_window_title)
        win.set_focus()
        print(f"Successfully connected to application: '{win.window_text()}'")

        win.wait('ready', timeout=30)
        time.sleep(2) # Wait for UI to settle after the screen transition
        print("Application window is ready.")

        # --- Interact with the 'Find Transaction' screen ---
        print("\nAnalyzing 'Find Transaction' screen...")

        try:
            # Find the main container for this view using its specific auto_id
            find_transaction_view = win.child_window(auto_id="ResumeTransactionViewID", control_type="Custom")
            find_transaction_view.wait('visible', timeout=15)
            print("- Found the main 'Find Transaction' view.")

            # 1. POS Number Input Field
            pos_number_input = find_transaction_view.child_window(auto_id="tbPOSNumber_InnerText", control_type="Edit")
            if pos_number_input.exists() and pos_number_input.is_visible():
                print("- Found 'POS number' input field.")
            else:
                print("- Could not find 'POS number' input field.")

            # 2. Saved Transactions List
            transactions_list = find_transaction_view.child_window(auto_id="SearchResultsDataGrid", control_type="DataGrid")
            if transactions_list.exists() and transactions_list.is_visible():
                print("- Found the saved transactions list.")
                item_count = transactions_list.item_count()
                print(f"- The list contains {item_count} saved transactions.")
                
                # Print all items from the list to the console
                print("\n--- Saved Transactions ---")
                for i in range(item_count):
                    # Get each row (DataItem)
                    row = transactions_list.get_item(i)
                    # Get all text elements (cells) within that row
                    cells = [cell.window_text() for cell in row.children(control_type='Custom')]
                    print(f"  - {' | '.join(cells)}")
                print("--------------------------\n")

                # Select the first item in the list
                if item_count > 0:
                    first_item = transactions_list.get_item(0)
                    first_item.select()
                    print("- Selected the first transaction in the list.")
                else:
                    print("- No transactions to select.")

            else:
                print("- Could not find the saved transactions list.")

            # 3. Buttons (Recall and Cancel)
            recall_button = find_transaction_view.child_window(title="Recall", control_type="Button")
            if recall_button.exists() and recall_button.is_visible():
                print(f"- Found 'Recall' button. Enabled: {recall_button.is_enabled()}")
                if recall_button.is_enabled():

                    cancel_button = find_transaction_view.child_window(title="Cancel", control_type="Button")
                    if cancel_button.exists() and cancel_button.is_visible():
                        print(f"- Found 'Cancel' button. Enabled: {cancel_button.is_enabled()}")
                    else:
                        print("- Could not find 'Cancel' button.")
                    print("- Clicking the 'Recall' button...")
                    recall_button.click_input()
                    print("- Successfully clicked 'Recall'.")

                    return True
            else:
                print("- Could not find 'Recall' button.")

            


        except timings.TimeoutError:
            print("Error: Timed out waiting for the 'Find Transaction' screen elements to appear.")
            return False
        except Exception as e:
            print(f"An error occurred while analyzing the screen: {e}")
            return False
            
    except timings.TimeoutError:
        print(f"Failed to connect to the POS application. Timed out waiting for window with title matching '{application_window_title}'.")
        return False
    except findwindows.ElementNotFoundError:
        print(f"Failed to find the application window. Make sure the application is running and the title is correct.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

    return True

if __name__ == "__main__":
    find_transaction()
