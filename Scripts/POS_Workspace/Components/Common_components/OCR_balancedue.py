# -*- coding: utf-8 -*-
"""
This script connects to an already open R10PosClient sales screen and
captures the "Balance Due" amount using OCR.

This version includes a more precise crop and a smarter regex for
better accuracy.

Prerequisites:
- Tesseract-OCR engine must be installed: https://github.com/UB-Mannheim/tesseract/wiki
- Python libraries: pip install pywinauto Pillow pytesseract
"""
import pytesseract
from pywinauto.application import Application
import time
import re
from PIL import Image
import traceback # Import traceback for detailed error logging

# --- Configuration ---
# IMPORTANT: Update this path to your Tesseract-OCR installation directory.
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def get_balance_due_from_screen():
    """
    Captures the main sales screen, crops to the relevant area, and uses OCR
    and regex to find the balance due.

    Returns:
        str: The balance due amount (e.g., "23.00", "0.00") or None if not found.
    """
    print("\n--- Searching for Balance Due on the sales screen ---")
    window_title = ".*R10PosClient.*"
    try:
        app = Application(backend="uia").connect(title_re=window_title, timeout=10)
        main_window = app.window(title_re=window_title)
        main_window.set_focus()
        
        # Give screen time to be fully rendered
        time.sleep(1) # 1 second is often enough
        screenshot = main_window.capture_as_image()
        
        # --- Tighter Crop Strategy ---
        width, height = screenshot.size
        
        # Define the crop box (left, top, right, bottom)
        crop_left = 0
        crop_top = int(height * 0.8) # Start 80% of the way down
        crop_right = width // 2       # End at the middle divider
        crop_bottom = height          # End at the bottom
        
        crop_box = (crop_left, crop_top, crop_right, crop_bottom)
        cropped_image = screenshot.crop(crop_box)
        
        # For debugging, save the cropped image to see what OCR is looking at
        print("Saving debug image to 'debug_cropped_image.png'...")
        cropped_image.save("debug_cropped_image.png")

        # Use Page Segmentation Mode 6 (Assume a single uniform block of text)
        custom_config = r'--oem 3 --psm 6'
        extracted_text = pytesseract.image_to_string(cropped_image, config=custom_config)
        
        # --- Smarter Regex ---
        # Normalize text for easier searching (lowercase, one space)
        clean_text = " ".join(extracted_text.split()).lower()
        
        # Regex to find "due", "oue", or "ove" (to account for OCR errors)
        # followed by any characters (non-greedy) and then capture the dollar amount.
        print("Searching for '...(due|oue|ove)... XX.XX' in extracted text...")
        match = re.search(r"(?:due|oue|ove).*?(?:\$|s)?(\d+\.\d{2})", clean_text)
        
        if match:
            balance_due = match.group(1)
            print(f"Match found: {balance_due}")
            return balance_due
        else:
            print("Could not find text '...(due|oue|ove)' followed by an amount XX.XX.")
            # For debugging, print all the text that OCR found to see why it failed
            print(f"\n--- OCR DEBUG TEXT (from cropped image) ---\n{extracted_text}\n----------------------")
            return None

    except Exception as e:
        print(f"An error occurred while trying to capture the balance due: {e}")
        print("\n--- FULL ERROR TRACEBACK ---")
        traceback.print_exc()
        print("------------------------------")
        return None

def main():
    """
    Main function to capture the balance due from the R10PosClient screen.
    """
    balance = get_balance_due_from_screen()
    
    if balance:
        print(f"\nSuccessfully Captured Balance Due: ${balance}")
    else:
        print("\nFailed to capture the Balance Due.")


if __name__ == "__main__":
    main()

