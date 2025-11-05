# -*- coding: utf-8 -*-
"""
This script connects to an already open R10PosClient sales screen and
captures the "PRODUCT VOIDED" text using OCR.

This version has debugging (print statements and image saves) re-enabled.

Prerequisites:
- Tesseract-OCR engine must be installed: https://github.com/UB-Mannheim/tesseract/wiki
- Python libraries: pip install pywinauto Pillow pytesseract
"""
import pytesseract
from pywinauto.application import Application
import time
import re
from PIL import Image, ImageOps # Import ImageOps for inverting
import traceback # Import traceback for detailed error logging

# --- Configuration ---
# IMPORTANT: Update this path to your Tesseract-OCR installation directory.
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def get_voided_product_text():
    """
    Captures the main sales screen, crops to the top-right area, and uses OCR
    to find "PRODUCT VOIDED" or similar text.

    Returns:
        str: The extracted voided product text (e.g., "PRODUCT VOIDED") or None if not found.
    """
    # print("\n--- Searching for 'PRODUCT VOIDED' on the sales screen ---")
    window_title = ".*R10PosClient.*"
    try:
        app = Application(backend="uia").connect(title_re=window_title, timeout=10)
        main_window = app.window(title_re=window_title)
        main_window.set_focus()
        
        # Give screen time to be fully rendered
        time.sleep(1)
        screenshot = main_window.capture_as_image()
        
        # --- Crop Strategy for "PRODUCT VOIDED" ---
        width, height = screenshot.size
        
        # Target the top-right quadrant where the stamp appears
        # (left, top, right, bottom)
        crop_left = int(width * 0.5)    # Start from the middle horizontally
        crop_top = int(height * 0.15)   # Was 0.1, moved down
        crop_right = int(width * 0.8)   # Go to 80% of width, not 100%
        crop_bottom = int(height * 0.35) # Was 0.4, moved up
        
        crop_box = (crop_left, crop_top, crop_right, crop_bottom)
        cropped_image = screenshot.crop(crop_box)
        
        # --- ADDED BACK DEBUG SAVE ---
        print("Saving original cropped image to 'debug_voided_product_cropped_image.png'...")
        cropped_image.save("debug_voided_product_cropped_image.png")
        # --- END DEBUG SAVE ---
        
        # --- NEW STEP: Rotate the image to make the text linear ---
        # The stamp is angled counter-clockwise, so we rotate clockwise (-20 degrees).
        print("Rotating cropped image by -20 degrees...")
        rotated_image = cropped_image.rotate(-20, expand=True, fillcolor='black')
        
        # --- ADDED BACK DEBUG SAVE ---
        print("Saving rotated image to 'debug_voided_rotated_image.png'...")
        rotated_image.save("debug_voided_rotated_image.png")
        # --- END DEBUG SAVE ---
        
        # --- PREPROCESSING STEPS ---
        # Convert the NEW rotated_image to grayscale
        print("Converting *rotated* image to inverted grayscale...")
        grayscale_image = rotated_image.convert('L')
        
        # Invert the grayscale image directly
        inverted_image = ImageOps.invert(grayscale_image)
        
        # --- NEW STEP: Apply binary threshold for clear B&W ---
        # A threshold of 150 will keep the bright text and kill the gray text.
        print("Applying binary threshold for clear B&W...")
        threshold = 150
        # p > threshold becomes 255 (white), else 0 (black)
        processed_image = inverted_image.point(lambda p: 255 if p > threshold else 0)
        # Convert to 'L' mode for Tesseract
        processed_image = processed_image.convert('L') 
        
        # --- ADDED BACK DEBUG SAVE ---
        print("Saving processed B&W image to 'debug_voided_processed_image.png'...")
        processed_image.save("debug_voided_processed_image.png")
        # --- END DEBUG SAVE ---
        
        # --- UPDATED TESSERACT CONFIG ---
        # Use Page Segmentation Mode 6 (Assume a single uniform block of text.)
        custom_config = r'--oem 3 --psm 6'
        
        # --- STRATEGY: Back to image_to_string ---
        print("Running Tesseract with image_to_string...")
        extracted_text = pytesseract.image_to_string(processed_image, config=custom_config)
        
        # Combine all found words into a single string for searching
        clean_text = " ".join(extracted_text.split()).upper()
        # --- END STRATEGY ---
        
        # --- UPDATED REGEX ---
        # Look for "PROD..." and then "VOID..." or "ED"
        print("Searching for 'PROD... ... (VOID|ED|OID)...' in extracted text...")
        match = re.search(r"PRO\w*.*(VOID\w*|\w*OID|\w*VED|\w*ED)", clean_text)
        
        if match:
            # Return a clean string.
            print(f"'PRODUCT VOIDED' text found. Match: {clean_text}")
            return "PRODUCT VOIDED"
        else:
            # Failed to find, return None
            print("Could not find 'PRODUCT VOIDED' or 'VOIDED' in the cropped area.")
            print(f"\n--- VOIDED PRODUCT OCR DEBUG TEXT (from 'image_to_string') ---\n{clean_text}\n----------------------")
            return None

    except Exception as e:
        # Keep a minimal error log for failures
        print(f"An error occurred in get_voided_product_text: {e}")
        return None

def main():
    """
    Main function to capture the voided product text.
    """
    print("\n--- Searching for 'PRODUCT VOIDED' on the sales screen ---")
    # Capture Voided Product Text
    voided_text = get_voided_product_text()
    
    if voided_text:
        print(f"Successfully Captured Voided Product Text: {voided_text}")
    else:
        print("Failed to capture the Voided Product Text.")


if __name__ == "__main__":
    main()

