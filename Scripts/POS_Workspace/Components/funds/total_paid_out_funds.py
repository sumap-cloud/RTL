import pytesseract
from PIL import ImageGrab, Image, ImageEnhance, ImageFilter
from pywinauto.application import Application
import re
import time

# --- IMPORTANT ---
# You must have Google's Tesseract-OCR engine installed and in your system's PATH.
# Download it from: https://github.com/UB-Mannheim/tesseract/wiki
# After installation, you might need to specify the path to the executable, like this:
# On Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# On Linux (if not in PATH)
# pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'


def preprocess_image(image):
    """
    Preprocesses the image to improve OCR accuracy.
    - Converts to grayscale
    - Increases contrast
    """
    # Convert the image to grayscale
    processed_image = image.convert('L')
    # Increase the contrast of the image
    enhancer = ImageEnhance.Contrast(processed_image)
    processed_image = enhancer.enhance(2)
    return processed_image


def total_paid_out():

    """
    Captures a screenshot of the R10PosClient application, uses OCR to read
    the text, and extracts the 'Total Cash' and 'Total Paid Out Amount' values.
    """

    try:
        # Regex for the application window title
        app_title_regex = ".*R10PosClient.*"
        print(f"Attempting to connect to application with title regex: {app_title_regex}")

        # Connect to the running application to get its coordinates
        # Using the "win32" backend can sometimes be more reliable for older apps
        app = Application(backend="win32").connect(title_re=app_title_regex, timeout=20)
        win = app.window(title_re=app_title_regex)

        print("Successfully connected. Bringing window to front...")
        win.set_focus()
        time.sleep(1)  # Give a moment for the window to come to the front

        # Get the window's screen coordinates
        rect = win.rectangle()
        print(f"Window coordinates: {rect}")

        # Capture a screenshot of the application window
        screenshot = ImageGrab.grab(bbox=(rect.left, rect.top, rect.right, rect.bottom))

        # Save the original screenshot for debugging
        screenshot.save("pos_screenshot_original.png")
        print("Original screenshot saved as 'pos_screenshot_original.png'")

        # Preprocess the image for better OCR results
        processed_screenshot = preprocess_image(screenshot)
        processed_screenshot.save("pos_screenshot_processed.png")
        print("Processed screenshot saved as 'pos_screenshot_processed.png'")

        # Use pytesseract to extract text from the processed image
        # Using a specific page segmentation mode (psm) can help with layout
        custom_config = r'--oem 3 --psm 6'
        extracted_text = pytesseract.image_to_string(processed_screenshot, config=custom_config)

        #print("\n--- OCR Extracted Text (Full Window) ---")
        #print(extracted_text)
        #print("----------------------------------------\n")

        # --- Use Regular Expressions to find the amounts ---

        total_cash = None
        paid_out_amount = None
        top_right_cash = None

        # Regex to find "Total Cash" followed by a dollar amount
        cash_match = re.search(r"Total Cash[:\.]*\s*\$?([\d,]+\.\d{2})", extracted_text, re.IGNORECASE)
        if cash_match:
            total_cash = cash_match.group(1)
            print(f">>> SUCCESS: Found Total Cash: ${total_cash}")
        else:
            print(">>> INFO: Could not find 'Total Cash' amount.")

        # Regex to find "Total Paid Out Amount" followed by a dollar amount
        paid_out_match = re.search(r"Total Paid Out Amount[:\s\n]*\$?([\d,]+\.\d{2})", extracted_text, re.IGNORECASE)
        if paid_out_match:
            paid_out_amount = paid_out_match.group(1)
            print(f">>> SUCCESS: Found Total Paid Out Amount: ${paid_out_amount}")
        else:
            print(">>> INFO: Main regex failed for 'Total Paid Out Amount'. Trying line-by-line fallback...")
            lines = extracted_text.split('\n')
            for i, line in enumerate(lines):
                if "total paid out amount" in line.lower():
                    if i + 1 < len(lines):
                        next_line = lines[i+1]
                        amount_match = re.search(r"\$?([\d,]+\.\d{2})", next_line)
                        if amount_match:
                            paid_out_amount = amount_match.group(1)
                            print(f">>> SUCCESS (Fallback): Found Total Paid Out Amount: ${paid_out_amount}")
                            break
            
            if not paid_out_amount:
                 print(">>> INFO: Could not find 'Total Paid Out Amount' with fallback either.")

        # --- NEW: Find the cash amount in the top-right corner ---
        print("\n--- Finding Top-Right Cash Amount ---")
        try:
            # Define the region of interest (ROI) for the top-right corner.
            # These are percentages of the window's width and height.
            # I've adjusted the left boundary to capture the full number.
            roi_left = int(rect.width() * 0.78) # Changed from 0.80 to 0.78
            roi_top = int(rect.height() * 0.05)
            roi_right = int(rect.width() * 0.98)
            roi_bottom = int(rect.height() * 0.15)
            
            # Crop the screenshot to the ROI
            top_right_crop = screenshot.crop((roi_left, roi_top, roi_right, roi_bottom))
            top_right_crop.save("pos_screenshot_top_right.png")
            print("Saved top-right crop to 'pos_screenshot_top_right.png'")

            # Preprocess and OCR the cropped image
            processed_crop = preprocess_image(top_right_crop)
            top_right_text = pytesseract.image_to_string(processed_crop, config='--psm 7')
            
            print(f"Extracted text from top-right: '{top_right_text.strip()}'")

            # Use regex to find the dollar amount in the cropped text
            cash_match_top = re.search(r"([\d,]+\.\d{2})", top_right_text)
            if cash_match_top:
                top_right_cash = cash_match_top.group(1)
                print(f">>> SUCCESS: Cash Amount: ${top_right_cash}")
            else:
                print(">>> INFO: Could not find cash amount in the top-right corner.")
            return True
        except Exception as e:
            print(f"An error occurred while processing the top-right corner: {e}")


    except Exception as e:
        print(f"An error occurred: {e}")

# Run the function

#if __name__ == "__main__":
    #total_paid_out()
