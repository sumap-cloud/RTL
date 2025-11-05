import time
import re
from pywinauto import Application, timings

def get_operator_display_item_details(win):
    """
    Finds and parses the currently highlighted item's details from the
    operator display window. It intelligently scans the right side of the screen.
    """
    print("\n🔍 Reading Operator Display Item Details...")
    details = {
        "description": "N/A",
        "price": "N/A",
        "code": "N/A",
        "unit": "N/A",
    }

    try:
        # Strategy: Find all controls on the right half of the window
        window_rect = win.rectangle()
        horizontal_midpoint = window_rect.left + (window_rect.width() / 2)

        right_side_texts_raw = []
        for control in win.descendants():
            try:
                if control.rectangle().left > horizontal_midpoint:
                    text = control.window_text()
                    if text and text.strip():
                        right_side_texts_raw.append(text.strip())
            except Exception:
                continue

        # Clean and de-duplicate the list while preserving order
        right_side_texts = list(dict.fromkeys(right_side_texts_raw))

        if not right_side_texts:
            print("❌ Could not find any text controls on the right side of the operator display.")
            return details
            
        print(f"Found unique text fields to parse: {right_side_texts}")

        # --- Anchor-based parsing for better accuracy ---
        try:
            # 1. Find the 'Code' label as an anchor point.
            code_label_index = right_side_texts.index('Code')
            
            # 2. Get the code value, which is right after the label.
            if code_label_index + 1 < len(right_side_texts):
                details['code'] = right_side_texts[code_label_index + 1]

            # 3. Search for other details in the section *before* the code label.
            search_area = right_side_texts[:code_label_index]

            # 4. Find Price in the search area (take the last one found).
            prices_found = [text for text in search_area if re.fullmatch(r'-?\$?\d+\.\d{2}', text)]
            if prices_found:
                details['price'] = prices_found[-1]

            # 5. Find Unit in the search area.
            # Find the last occurrence of 'Unit' to get the one for the scanned item
            unit_indices = [i for i, x in enumerate(search_area) if x == "Unit"]
            if unit_indices:
                unit_index_in_search = unit_indices[-1]
                if unit_index_in_search > 0:
                    quantity = search_area[unit_index_in_search - 1]
                    details['unit'] = f"{quantity} Unit"

            # --- FIX: More targeted description finding ---
            # 6. Find Description by eliminating all other known details from the search area.
            known_details = list(details.values()) 
            if details['unit'] != 'N/A':
                 known_details.append(details['unit'].split(' ')[0]) # also exclude the quantity number

            blocklist = [
                'Please Scan/Enter Item Code', 'Unit', 'QTY', 
                'Retalix.Client.POS.BusinessObjects.Models.LineItem'
            ]
            
            potential_descriptions = []
            for text in search_area:
                # Check if the text is a candidate for the description
                if (text not in known_details and
                    text not in blocklist and
                    not text.isdigit() and
                    not re.fullmatch(r'-?\$?\d+\.\d{2}', text)): # ensure it's not a price
                    potential_descriptions.append(text)
            
            if potential_descriptions:
                # The last potential description before the price/unit is likely the correct one
                details['description'] = potential_descriptions[-1]

        except ValueError:
            print("❌ Critical Error: Could not find the 'Code' label to anchor the search. Parsing failed.")
            return details
        except Exception as e:
            print(f"An error occurred during parsing: {e}")


        print("\n✅ Successfully Parsed Details:")
        print(f"  - Description: {details['description']}")
        print(f"  - Price:       {details['price']}")
        print(f"  - Code:        {details['code']}")
        print(f"  - Unit:        {details['unit']}")
        return details

    except Exception as e:
        print(f"❌ An error occurred while getting operator display details: {e}")
        return details


def main():
    """
    Main function to connect to the POS operator display and read item details.
    """
    print("Attempting to connect to the POS Operator Display...")
    try:
        # Use the connection details you provided for the operator screen
        app = Application(backend="uia").connect(title_re=".*R10PosClient.*", timeout=10)
        win = app.window(title_re=".*R10PosClient.*")
        win.set_focus()
        print("✅ POS Operator Display found and focused.")
    except (timings.TimeoutError, Exception) as e:
        print(f"❌ Could not connect or focus POS window: {e}")
        print("   Please ensure the POS application is running and the title matches 'R10PosClient'.")
        return

    # Call the function to get the details from the connected window
    get_operator_display_item_details(win)


if __name__ == "__main__":
    main()
