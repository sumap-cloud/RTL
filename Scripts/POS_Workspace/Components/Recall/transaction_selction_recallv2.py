import time
from pywinauto import Application, timings, findwindows

def get_all_transactions():
    """
    Connects to the R10PosClient application, captures key UI element text,
    scrapes all transaction data, returns to the top, selects the first
    item, and clicks 'Recall'.
    """
    all_transactions = []
    seen_transactions = set() # To avoid duplicates when paginating
    captured_elements = {}

    try:
        # Set a longer default timeout for controls to appear
        timings.Timings.window_find_timeout = 10

        print("Connecting to the application...")
        # Connect to the running application
        app = Application(backend="uia").connect(title_re=".*R10PosClient.*", timeout=20)
        
        # Get the main window
        win = app.window(title_re=".*R10PosClient.*")
        win.set_focus()
        print("Successfully connected to the main window.")

        # Access the specific view containing the transaction list
        resume_view = win.child_window(auto_id="ResumeTransactionViewID", control_type="Custom")
        resume_view.wait('visible', timeout=10)
        print("Found the 'Resume Transaction' view.")

        # --- Capture additional UI elements ---
        print("\n--- Capturing UI Elements ---")
        
        # Capture the main title "Recall Transaction"
        try:
            recall_title = win.child_window(title="Recall Transaction", control_type="Text").wait('visible', timeout=5)
            captured_elements['recall_transaction_title'] = recall_title.window_text()
            print(f"Captured Title: '{captured_elements['recall_transaction_title']}'")
        except Exception:
            print("Could not find 'Recall Transaction' title text, using window title instead.")
            captured_elements['recall_transaction_title'] = win.window_text()

        # Capture "Find Transaction" text
        find_transaction_label = resume_view.child_window(title="Find Transaction", auto_id="Title", control_type="Text")
        captured_elements['find_transaction_text'] = find_transaction_label.window_text()
        print(f"Captured Label: '{captured_elements['find_transaction_text']}'")

        # Locate the POS number input box (we'll just confirm its presence)
        pos_number_input = resume_view.child_window(auto_id="tbPOSNumber_InnerText", control_type="Edit")
        captured_elements['pos_number_input_exists'] = pos_number_input.exists()
        print(f"POS Number Input Box Found: {captured_elements['pos_number_input_exists']}")

        # Capture "Recall" button text
        recall_button = resume_view.child_window(title="Recall", control_type="Button")
        captured_elements['recall_button_text'] = recall_button.window_text()
        print(f"Captured Button Text: '{captured_elements['recall_button_text']}'")
        
        # Capture "Cancel" button text
        cancel_button = resume_view.child_window(title="Cancel", control_type="Button")
        captured_elements['cancel_button_text'] = cancel_button.window_text()
        print(f"Captured Button Text: '{captured_elements['cancel_button_text']}'")

        # Locate the pagination buttons
        down_button = resume_view.child_window(auto_id="LeftRegionDataPagerButtonDownID", control_type="Button")
        up_button = resume_view.child_window(auto_id="LeftRegionDataPagerButtonUpID", control_type="Button")
        print("Located the pagination controls.")
        
        print("\n--- Scraping All Pages (Scrolling Down) ---")
        while True:
            # Locate the grid containing the transaction data
            grid = resume_view.child_window(auto_id="SearchResultsDataGrid", control_type="DataGrid")
            items = grid.children(control_type="DataItem")
            
            if not items:
                print("No items found on this page.")
                break

            print(f"Found {len(items)} items on the current page.")
            
            # Extract data from each row
            for item in items:
                cells = item.children()
                if len(cells) >= 4:
                    date_time = cells[0].window_text()
                    pos = cells[1].window_text()
                    trans_id = cells[2].window_text()
                    amount = cells[3].window_text()

                    transaction_key = f"{date_time}-{pos}-{trans_id}"

                    if transaction_key not in seen_transactions:
                        transaction_data = {
                            "Date": date_time,
                            "Pos": pos,
                            "Trans.": trans_id,
                            "Amount": amount
                        }
                        all_transactions.append(transaction_data)
                        seen_transactions.add(transaction_key)

            if down_button.is_enabled():
                down_button.click()
                time.sleep(1)
            else:
                print("Reached the end of the list.")
                break
        
        print("\n--- Returning to Top (Scrolling Up) ---")
        while up_button.is_enabled():
            print("Navigating to previous page...")
            up_button.click()
            time.sleep(1)
        
        print("Reached the top of the list.")

        # --- Select the first transaction and click Recall ---
        print("\n--- Selecting First Transaction and Recalling ---")
        grid = resume_view.child_window(auto_id="SearchResultsDataGrid", control_type="DataGrid")
        items = grid.children(control_type="DataItem")
        
        if items:
            first_item = items[0]
            print(f"Selecting first transaction: '{first_item.window_text()}'")
            first_item.click_input() # Use click_input() for reliable selection
            time.sleep(1)

            recall_button = resume_view.child_window(title="Recall", control_type="Button")
            if recall_button.is_enabled():
                print("Clicking the 'Recall' button...")
                recall_button.click()
            else:
                print("The 'Recall' button is not enabled.")
        else:
            print("No transactions available to select.")
            
        return {"ui_elements": captured_elements, "transactions": all_transactions}

    except findwindows.ElementNotFoundError:
        print("\nError: Could not find the application window or a required control.")
        print("Please ensure the 'R10PosClient' application is running and on the correct screen.")
        return None
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        return None

def select_recall_transaction():
    """
    Main controller function. Calls the scraper, prints results, and returns a
    boolean status indicating success or failure.
    """
    results = get_all_transactions()
    
    if results:
        print("\n--- All Scraped Transactions ---")
        transactions = results.get("transactions", [])
        if transactions:
            for trans in transactions:
                # Format the output as requested: Date | Pos | Trans. | Amount |
                print(f"  - {trans['Date']} | {trans['Pos']} | {trans['Trans.']} | {trans['Amount']} |")
            print(f"\nTotal transactions found: {len(transactions)}")
            print("✅ Automation completed successfully.")
            return True # Success: Found and processed transactions
        else:
            print("❌ No transactions were found, but the script ran without errors.")
            return False # Failure: Could not complete the full task
    else:
        print("❌ Automation failed to retrieve results.")
        return False # Failure: An error occurred in the scraping function

# --- Main Execution Block ---
# This part of the script only runs when you execute it directly.
if __name__ == "__main__":
    print("Running Recall Transaction automation script directly for testing...")
    
    # Call the main function and check its boolean return value
    if select_recall_transaction():
        # If the function returned True, it prints a success message.
        print("\n--- Standalone Test PASSED ---")
    else:
        # If the function returned False, it prints a failure message.
        print("\n--- Standalone Test FAILED ---")
