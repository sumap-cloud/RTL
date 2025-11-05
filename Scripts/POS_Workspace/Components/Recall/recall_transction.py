from pywinauto import Application, findwindows, timings
from pathlib import Path
import sys
import time
# --- OCR Imports ---
# Make sure to install pytesseract and Pillow: pip install pytesseract Pillow
# Also, ensure you have Google's Tesseract OCR engine installed on your system.
try:
    import pytesseract
    from PIL import Image, ImageEnhance
    import numpy as np
except ImportError:
    print("Error: Pytesseract or Pillow is not installed. Please install them using 'pip install pytesseract Pillow'")
    sys.exit(1)

# --- Tesseract Configuration ---
# IMPORTANT: You may need to update this path to where Tesseract is installed on your system.
# On Windows, the default is often: r'C:\Program Files\Tesseract-OCR\tesseract.exe'
try:
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    # You can test if tesseract is found with the line below
    # print(pytesseract.get_tesseract_version())
except pytesseract.TesseractNotFoundError:
    print("Tesseract Error: 'tesseract.exe' not found. Please ensure Tesseract is installed and the path in the script is correct.")
    # You can download Tesseract for Windows here: https://github.com/UB-Mannheim/tesseract/wiki
    sys.exit(1)


def preprocess_image(image):
    """
    Preprocesses the image to improve OCR accuracy.
    - Converts to grayscale
    - Increases contrast
    """
    processed_image = image.convert('L') # Convert to grayscale
    enhancer = ImageEnhance.Contrast(processed_image)
    processed_image = enhancer.enhance(2) # Increase contrast
    return processed_image

def recall_transaction():
    """
    This function automates the process of recalling a transaction in a POS system.
    It connects to the application, captures on-screen text, identifies key buttons,
    and clicks on the 'Transaction List' button.
    """
    application_window_title = ".*R10PosClient.*"

    try:
        print("Connecting to the POS application...")
        app = Application(backend="uia").connect(title_re=application_window_title, timeout=20)
        
        win = app.window(title_re=application_window_title)
        win.set_focus()
        print(f"Successfully connected to application: '{win.window_text()}'")

        win.wait('ready', timeout=30)
        time.sleep(2)
        print("Application window is ready.")

        # --- Capture the 'Recall Transaction' Title ---
        try:
            recall_title_element = win.child_window(auto_id="MainHeader", control_type="Text")
            recall_title_element.wait('visible', timeout=10)
            title_text = recall_title_element.window_text()
            print(f"\nSuccessfully captured title: '{title_text}'")
        except timings.TimeoutError:
            print("Error: Timed out waiting for the 'Recall Transaction' title to appear.")
        except Exception as e:
            print(f"An error occurred while trying to capture the title: {e}")

        # --- Capture the main instruction message using OCR ---
        try:
            print("\nAttempting to capture instruction message with OCR...")
            left_panel = win.child_window(auto_id="ResumeTransactionByBarcodeViewID", control_type="Custom")
            left_panel.wait('visible', timeout=10)
            
            panel_screenshot = left_panel.capture_as_image()
            processed_screenshot = preprocess_image(panel_screenshot)
            extracted_text = pytesseract.image_to_string(processed_screenshot)
            lines = [line.strip() for line in extracted_text.split('\n') if line.strip()]
            
            found_message = False
            for line in lines:
                if "Scan/Type Transaction Code" in line:
                    print(f"Successfully captured instruction message via OCR: '{line}'")
                    found_message = True
                    break
            
            if not found_message:
                 print("Error: Could not find the instruction message using OCR.")
                 print("--- Text extracted by OCR for debugging ---\n" + "\n".join(lines))

        except timings.TimeoutError:
            print("Error: Timed out waiting for the left panel to appear for OCR.")
        except Exception as e:
            print(f"An error occurred during OCR process: {e}")

        # --- Capture the 'Scan/Enter Trans. Barcode' message ---
        try:
            scan_message_element = win.child_window(auto_id="keypadHelper", control_type="Text")
            scan_message_element.wait('visible', timeout=10)
            message_text = scan_message_element.window_text()
            print(f"Successfully captured keypad message: '{message_text}'")
        except timings.TimeoutError:
            print("Error: Timed out waiting for the 'Scan/Enter Trans. Barcode' message to appear.")
            return False
        except Exception as e:
            print(f"An error occurred while trying to capture the scan message: {e}")
            return False

        # --- Identify and interact with visible buttons ---
        print("\nIdentifying and clicking buttons...")

        try:
            # Transaction List Button
            transaction_list_button = win.child_window(title="Transaction List", auto_id="GenericCommandButtonTemplete_TransactionList", control_type="Button")
            transaction_list_button.wait('visible', timeout=10)
            if transaction_list_button.is_enabled():
                print("- 'Transaction List' button is visible and enabled. Clicking it now...")
                transaction_list_button.click_input() # Using click_input() for reliability
                print("- Successfully clicked 'Transaction List'.")
            else:
                print("- 'Transaction List' button is visible but not enabled.")

            # You can add a small delay here to wait for the next screen to load
            time.sleep(3)

        except timings.TimeoutError:
            print("Error: Timed out waiting for the 'Transaction List' button to appear.")
            return False
        except Exception as e:
            print(f"An error occurred while clicking the button: {e}")
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
    recall_transaction()
