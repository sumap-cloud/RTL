from pywinauto import Application
from pywinauto.findwindows import ElementNotFoundError # Corrected import
import sys
import time
# Re-adding imports for OCR
import pytesseract
from PIL import ImageGrab
import os 

# --- OCR SETUP ---
# NOTE: For OCR to work, you MUST install:
# 1. The pytesseract library:
#    pip install pytesseract
# 2. Google's Tesseract-OCR Engine:
#    Download and install it from here: https://github.com/UB-Mannheim/tesseract/wiki
#
# 3. After installation, you *may* need to tell pytesseract where to find it.
#    Uncomment the line below and set the correct path if you get an error.
#    This path is the default for the installer.
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# ---------------

def check_activation_status(win):
    """
    Checks for both the 'Online Item' title (via OCR) and the
    'Please wait...' content text (via pywinauto).
    
    Args:
        win: The pywinauto window object for 'R10PosClient'.
        
    Returns:
        tuple (str, str): A tuple containing (title_text, content_text).
                         Defaults to "Not found" if an item isn't present.
    """
    title_text = "Not found"
    content_text = "Not found"

    # --- 1. Check for content text ---
    try:
        # Find the parent view first
        parent_view = win.child_window(auto_id="OnlineItemActivationProcessViewID", control_type="Custom")
        parent_view.wait('exists', timeout=10)
        
        # Then find the text control inside it.
        background_text_control_robust = parent_view.child_window(
            title="Please wait, online item activation in progress", 
            control_type="Text"
        )
        background_text_control_robust.wait('exists', timeout=5)
        
        # Store the captured text
        content_text = background_text_control_robust.window_text()

    except Exception:
        pass # If not found, content_text remains "Not found"

    # --- 2. Check for title bar text using OCR ---
    try:
        # Get the bounding box of the main window
        rect = win.rectangle()
        
        # Define a specific, small region for the title bar
        # Bounding box: (left, top, right, bottom)
        title_bar_bbox = (
            rect.left + 25,  # Approx Left from debug
            rect.top + 65,   # Approx Top from debug
            rect.left + 500, # Approx Right from debug
            rect.top + 150   # Approx Bottom (giving it 85px height)
        )
        
        screenshot = ImageGrab.grab(bbox=title_bar_bbox)
        
        # Save the screenshot to a file for debugging (optional, can be commented out)
        save_path = os.path.join(os.getcwd(), "ocr_title_screenshot.png")
        screenshot.save(save_path)
        
        # Use Tesseract to extract text from the screenshot
        extracted_text = pytesseract.image_to_string(screenshot)
        
        # Check *only* for the "Online Item" text
        if "Online Item" in extracted_text:
            title_text = "Online Item"
        
    except Exception:
        pass # If not found, title_text remains "Not found"

    return title_text, content_text

def main():
    """
    Main execution function to connect to the app and get texts.
    """
    try:
        # Connect to the already running application
        app = Application(backend="uia").connect(title="R10PosClient", timeout=20)
        
        # Get the main window
        win = app.window(title="R10PosClient")
        win.set_focus()
        time.sleep(1) # Give a moment for focus

        # --- Call the reusable combined function ---
        title_text, content_text = check_activation_status(win)

        # --- Print Final Simple Output ---
        print(f"title: {title_text}")
        print(f"content: {content_text}")

    except Exception as e:
        print(f"Error: Failed to connect to application.")
        print(f"Details: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

