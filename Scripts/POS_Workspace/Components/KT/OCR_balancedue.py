"""
Prerequisites:
- Tesseract-OCR engine must be installed: https://github.com/UB-Mannheim/tesseract/wiki
- Python libraries: pip install pywinauto Pillow pytesseract
"""
import re
import pytesseract
from pywinauto.application import Application
from PIL import Image
import time

# --- Configuration ---
# IMPORTANT: Update this path to your Tesseract-OCR installation directory.
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def capture_balance_due_with_ocr():
    """
    Connects to the R10PosClient application, takes a screenshot of the receipt area,
    and uses OCR to find and capture the Balance Due amount.
    """
    try:
        # Connect to the application
        application_window_title = ".*R10PosClient.*"
        print(f"Connecting to application with title: {application_window_title}")
        app = Application(backend="uia").connect(title_re=application_window_title, timeout=20)
        win = app.window(title_re=application_window_title)
        win.set_focus()
        print("Successfully connected to the application window.")
        time.sleep(1)  # Wait a moment for the window to be fully rendered

        # --- Logic to find the Balance Due amount using OCR ---

        # 1. Capture a screenshot of the application window
        screenshot = win.capture_as_image()
        print("Screenshot captured.")

        # 2. Define the cropping area for the "Balance Due" section.
        # Based on the control identifiers (ReceiptViewID is L25, T65, R501, B671),
        # we can define a region at the bottom of the receipt to scan.
        # Coordinates are (left, top, right, bottom).
        crop_box = (190, 600, 500, 670)
        receipt_bottom_area = screenshot.crop(crop_box)
        print(f"Cropped image to area: {crop_box}")

        # 3. Use Tesseract to perform OCR on the cropped image
        # Pre-processing the image (converting to grayscale) can improve accuracy.
        gray_image = receipt_bottom_area.convert('L')
        ocr_text = pytesseract.image_to_string(gray_image)
        print("\n--- Extracted OCR Text ---")
        print(ocr_text)
        print("--------------------------\n")

        # 4. Use regex to find the balance due amount in the extracted text
        # This pattern looks for "Balance Due" followed by any characters,
        # and then captures the first number in "xx.xx" format.
        match = re.search(r"Balance\s*Due:.*?(\d+\.\d{2})", ocr_text, re.IGNORECASE | re.DOTALL)

        if match:
            balance_due_amount = match.group(1)
            print("-----------------------------------------")
            print(f"Successfully Captured Balance Due (OCR): ${balance_due_amount}")
            print("-----------------------------------------")
            return balance_due_amount
        else:
            print("Error: Could not find 'Balance Due' amount in the OCR text.")
            return None

    except FileNotFoundError:
        print("OCR Error: 'tesseract.exe' not found.")
        print(f"Please ensure Tesseract is installed and the path is correct in the script:")
        print(f"pytesseract.pytesseract.tesseract_cmd = r'{pytesseract.pytesseract.tesseract_cmd}'")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

if __name__ == "__main__":
    capture_balance_due_with_ocr()

