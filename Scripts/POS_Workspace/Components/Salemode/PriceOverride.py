# -*- coding: utf-8 -*-
"""
This script connects to an R10PosClient "Price Override" screen to automate
the process of changing a price.

It combines two techniques:
1.  Direct UI Automation (pywinauto): To type in new values and click buttons.
2.  Optical Character Recognition (OCR): To read static text labels like
    "Original Price" and "New Total Price" that are not standard UI elements.

Prerequisites:
-   Tesseract-OCR engine must be installed: https://github.com/UB-Mannheim/tesseract/wiki
-   Python libraries: pip install pywinauto Pillow pytesseract
"""
import sys
import time
import re
import pytesseract
from pywinauto import Application, timings
from pywinauto.findwindows import ElementNotFoundError

# --- Configuration ---
# IMPORTANT: Update this path to your Tesseract-OCR installation directory.
# This is a common location, but yours might be different.
try:
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
except Exception:
    print("Warning: Tesseract path might not be configured. OCR will fail.")
    print("Please update the path in the script if needed.")


class PriceOverrideManager:
    """
    Manages connection, reading, and interaction with the POS application
    for performing and verifying price overrides.
    """
    def __init__(self, title_re=".*R10PosClient.*", timeout=15):
        """
        Connects to the application window upon initialization.
        """
        try:
            print("Connecting to the POS window...")
            self.app = Application(backend="uia").connect(title_re=title_re, timeout=timeout)
            self.win = self.app.window(title_re=title_re)
            self.win.set_focus()
            print("✅ Connected to POS window and brought it to the foreground.")
        except (timings.TimeoutError, ElementNotFoundError):
            print(f"❌ Could not connect to a window with title like '{title_re}'. Is it running?")
            raise ConnectionError("POS application window not found.")

    def _extract_values_from_fields(self):
        """
        (Internal) Extracts values from the editable input fields.
        """
        values = {
            "input_new_price": None,
            "input_discount": None,
            "input_percent_discount": None,
        }
        try:
            def get_edit_value(auto_id):
                try:
                    ctrl = self.win.child_window(auto_id=auto_id, control_type="Edit")
                    return (ctrl.window_text() or "").strip()
                except (ElementNotFoundError, timings.TimeoutError):
                    return "" # Return empty string if control not found

            values["input_new_price"] = get_edit_value("FieldItemNewPrice_InnerText")
            values["input_discount"] = get_edit_value("FieldItemDiscount_InnerText")
            values["input_percent_discount"] = get_edit_value("FieldItemDiscountPercent_InnerText")
        except Exception as e:
            print(f"⚠️ Warning: Could not extract from input fields: {e}")
        return values

    def _extract_values_with_ocr(self):
        """
        (Internal) Captures the screen and uses OCR to find static price labels.
        """
        values = {
            "ocr_original_price": None,
            "ocr_total_price_difference": None,
            "ocr_new_total_price": None
        }
        try:
            screenshot = self.win.capture_as_image()
            extracted_text = pytesseract.image_to_string(screenshot)

            # Flexible regex to find price values next to their labels
            original_price_match = re.search(r"Original Price.*?(\d+\.\d{2})", extracted_text, re.IGNORECASE | re.DOTALL)
            values["ocr_original_price"] = original_price_match.group(1) if original_price_match else None

            price_diff_match = re.search(r"Difference.*?(-?\d+\.\d{2})", extracted_text, re.IGNORECASE | re.DOTALL)
            values["ocr_total_price_difference"] = price_diff_match.group(1) if price_diff_match else None

            new_total_price_match = re.search(r"New Total Price.*?(\d+\.\d{2})", extracted_text, re.IGNORECASE | re.DOTALL)
            values["ocr_new_total_price"] = new_total_price_match.group(1) if new_total_price_match else None

        except Exception as e:
            print(f"⚠️ Warning: OCR extraction failed: {e}")

        return values

    def get_all_screen_values(self):
        """
        Gets all possible values from the screen using both direct access and OCR.
        """
        print("\n🔎 Reading all values from the screen...")
        field_values = self._extract_values_from_fields()
        ocr_values = self._extract_values_with_ocr()
        # Merge the two dictionaries
        all_values = {**field_values, **ocr_values}
        return all_values

    def apply_override(self, new_price=None, discount=None, percent_discount=None):
        """
        Handles the price override screen, combining OCR verification and UI interaction.
        """
        print("\n✨ Handling 'Price Override' Screen ✨")
        try:
            # --- 1. Capture and display initial state ---
            initial_values = self.get_all_screen_values()
            print("\n--- Initial Screen State ---")
            for key, value in initial_values.items():
                print(f"  - {key.replace('_', ' ').title()}: {value or 'N/A'}")
            print("----------------------------")

            # --- 2. Determine which field to modify ---
            target_field_id, target_value, field_name = None, None, ""
            if new_price is not None:
                target_field_id, target_value, field_name = "FieldItemNewPrice_InnerText", new_price, "New Price"
            elif discount is not None:
                target_field_id, target_value, field_name = "FieldItemDiscount_InnerText", discount, "Discount"
            elif percent_discount is not None:
                target_field_id, target_value, field_name = "FieldItemDiscountPercent_InnerText", percent_discount, "Percent Discount"

            # --- 3. Interact with the target field ---
            if not target_field_id:
                print("⚠️ No override value was provided. No changes will be made.")
                return False

            print(f"\nAttempting to set {field_name} to '{target_value}'...")
            target_field = self.win.child_window(auto_id=target_field_id, control_type="Edit")
            target_field.wait('visible', timeout=15)
            target_field.set_edit_text("") # Clear the field
            target_field.type_keys(str(target_value), with_spaces=True, set_foreground=True)
            print(f"⌨️ Entered {field_name}: {target_value}")

            # --- 4. Click OK and wait for the app to calculate ---
            ok_button = self.win.child_window(title="OK", auto_id="OK", control_type="Button")
            ok_button.wait('enabled', timeout=10)
            ok_button.click_input()
            print("✅ Clicked 'OK'. Waiting for UI to update...")
            time.sleep(2) # Give UI time to process the change

            # --- 5. Capture and display final state for verification ---
            updated_values = self.get_all_screen_values()
            print("\n--- Updated Screen State (after clicking OK) ---")
            for key, value in updated_values.items():
                print(f"  - {key.replace('_', ' ').title()}: {value or 'N/A'}")
            print("--------------------------------------------------")

            # --- 6. Click Override button to finalize ---
            print("\n🔄 Clicking 'Override' button to finalize...")
            override_button = self.win.child_window(title="Override", auto_id="GenericCommandButtonTemplete_PriceOverride_Override", control_type="Button")
            override_button.wait('enabled', timeout=10)
            override_button.click_input()
            print("✅ Clicked 'Override' button. Price override finalized!")
            time.sleep(1)

            return True

        except (timings.TimeoutError, ElementNotFoundError) as e:
            print(f"❌ A control was not found or timed out: {e}")
            return False
        except Exception as e:
            print(f"❌ An unexpected error occurred while applying the override: {e}")
            return False

def perform_price_override(new_price=None, discount=None, percent_discount=None):
    """
    High-level function to connect and run the full price override workflow.
    """
    provided_args_count = sum(1 for arg in [new_price, discount, percent_discount] if arg is not None)
    if provided_args_count > 1:
        print("❌ Error: Please provide only one override type (price, discount, or percent).")
        return False
    if provided_args_count == 0:
        print("❌ Error: No override value provided.")
        return False

    try:
        manager = PriceOverrideManager()
        if manager.apply_override(new_price=new_price, discount=discount, percent_discount=percent_discount):
            print("\n🎉 Price Override workflow completed successfully.")
            return True
        else:
            print("\n🛑 Price Override workflow failed.")
            return False
    except ConnectionError:
        # Error is already printed in the __init__ method.
        return False

if __name__ == "__main__":
    # --- Example Usage from Command Line ---
    # python merged_price_override.py --price 9.50
    # python merged_price_override.py --discount 2.00
    # python merged_price_override.py --percent 15

    # args = sys.argv[1:]
    # new_price_arg, discount_arg, percent_discount_arg = None, None, None

    # try:
    #     if "--price" in args:
    #         new_price_arg = args[args.index("--price") + 1]
    #     elif "--discount" in args:
    #         discount_arg = args[args.index("--discount") + 1]
    #     elif "--percent" in args:
    #         percent_discount_arg = args[args.index("--percent") + 1]
    # except IndexError:
    #     print("❌ Error: A value must follow a flag (e.g., --price 1.99).")
    #     sys.exit(1)

    # # If no arguments are provided, use a default for demonstration
    # if all(arg is None for arg in [new_price_arg, discount_arg, percent_discount_arg]):
    #     print("ℹ️ No command-line override value provided. Using default price: 8.00")
    #     new_price_arg = "8.00"

    # perform_price_override(
    #     new_price=new_price_arg,
    #     discount=discount_arg,
    #     percent_discount=percent_discount_arg
    # )

    #Example usage in a script
    success1 = perform_price_override(new_price="9.99")

    if success1:
        print("✅ Task 1 completed successfully.")
    else:
        print("❌ Task 1 failed. Aborting script.")
        