import os
import time
from datetime import datetime
from PIL import ImageGrab

# Try to import pywinauto for window focusing
from pywinauto import Application

# Define the base directory for saving files
BASE_SAVE_DIR = r"C:\python\python\Scripts\SCANPOS"

def cleanup_existing_files():
    """
    Delete any existing PNG and TXT files in the base directory
    """
    try:
        if not os.path.exists(BASE_SAVE_DIR):
            os.makedirs(BASE_SAVE_DIR)
            print(f"Created directory: {BASE_SAVE_DIR}")
            return
            
        files_deleted = 0
        for filename in os.listdir(BASE_SAVE_DIR):
            if filename.lower().endswith(('.png', '.txt')):
                file_path = os.path.join(BASE_SAVE_DIR, filename)
                try:
                    os.remove(file_path)
                    files_deleted += 1
                    print(f"Deleted existing file: {filename}")
                except Exception as e:
                    print(f"Could not delete {filename}: {e}")
        
        if files_deleted == 0:
            print("No existing PNG or TXT files found to delete.")
        else:
            print(f"Deleted {files_deleted} existing file(s).")
            
    except Exception as e:
        print(f"Error during cleanup: {e}")

def focus_r10pos_window():
    """
    Focus the R10PosClient window before taking screenshot
    
    Returns:
        tuple: (bool, Application object, Window object) - Success status and objects for debugging
    """
    try:
        application_window_title = ".*R10PosClient.*"
        app = Application(backend="uia").connect(title_re=application_window_title, timeout=20)
        win = app.window(title_re=application_window_title)
        win.set_focus()
        print("R10PosClient window focused successfully.")
        return True, app, win
    except Exception as e:
        print(f"Could not focus R10PosClient window: {e}")
        print("Continuing with screenshot anyway...")
        return False, None, None

def print_control_identifiers(win, debug_file_path=None):
    """
    Save control identifiers to a file for debugging the focused window
    
    Args:
        win: pywinauto Window object
        debug_file_path: Path to save debug information (optional)
    """
    try:
        # Generate debug filename if not provided
        if debug_file_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            debug_file_path = os.path.join(BASE_SAVE_DIR, f"debug_controls_{timestamp}.txt")
        
        debug_content = []
        debug_content.append("=" * 50)
        debug_content.append("CONTROL IDENTIFIERS DEBUG")
        debug_content.append("=" * 50)
        
        # Add window information
        debug_content.append(f"Window Title: {win.window_text()}")
        debug_content.append(f"Window Class: {win.class_name()}")
        debug_content.append("")
        debug_content.append("Control Identifiers:")
        
        # Capture control identifiers output
        import io
        from contextlib import redirect_stdout
        
        # Capture the print_control_identifiers output
        output_buffer = io.StringIO()
        with redirect_stdout(output_buffer):
            win.print_control_identifiers()
        
        control_identifiers = output_buffer.getvalue()
        debug_content.append(control_identifiers)
        debug_content.append("=" * 50)
        
        # Write to file
        with open(debug_file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(debug_content))
        
        print(f"Debug information saved to: {debug_file_path}")
        
    except Exception as e:
        print(f"Error saving control identifiers: {e}")

def take_screenshot(save_path=None, focus_r10pos=True, debug_controls=False):
    """
    Take a screenshot using PIL ImageGrab (built-in with Pillow)
    
    Args:
        save_path (str): Path to save the screenshot (optional)
        focus_r10pos (bool): Whether to focus R10PosClient window first (default: True)
        debug_controls (bool): Whether to print control identifiers for debugging (default: False)
    
    Returns:
        str: Path to the saved screenshot
    """
    app, win = None, None
    
    try:
        # Focus R10PosClient window if requested
        if focus_r10pos:
            success, app, win = focus_r10pos_window()
            if success:
                # Small delay to ensure window is properly focused
                time.sleep(0.5)
        
        # Take screenshot of entire screen
        screenshot = ImageGrab.grab()
        
        # Generate filename if not provided
        if save_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(BASE_SAVE_DIR, f"screenshot_{timestamp}.png")
        
        # Save the screenshot
        screenshot.save(save_path)
        print(f"Screenshot saved to: {save_path}")
        
        # Print control identifiers if debugging is enabled and window was focused
        if debug_controls and win is not None:
            # Generate debug file path with same timestamp as screenshot
            debug_file_path = save_path.replace('.png', '_debug.txt')
            print_control_identifiers(win, debug_file_path)
        
        return save_path
        
    except Exception as e:
        print(f"Error taking screenshot: {e}")
        return None

def take_bbox_screenshot(bbox, save_path=None, focus_r10pos=False, debug_controls=False):
    """
    Take a screenshot of a specific area
    
    Args:
        bbox (tuple): Bounding box as (left, top, right, bottom)
        save_path (str): Path to save the screenshot (optional)
        focus_r10pos (bool): Whether to focus R10PosClient window first (default: False)
        debug_controls (bool): Whether to print control identifiers for debugging (default: False)
    
    Returns:
        str: Path to the saved screenshot
    """
    app, win = None, None
    
    try:
        # Focus R10PosClient window if requested
        if focus_r10pos:
            success, app, win = focus_r10pos_window()
            if success:
                # Small delay to ensure window is properly focused
                time.sleep(0.5)
            
        # Take screenshot of specific area
        screenshot = ImageGrab.grab(bbox=bbox)
        
        # Generate filename if not provided
        if save_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(BASE_SAVE_DIR, f"screenshot_region_{timestamp}.png")
        
        # Save the screenshot
        screenshot.save(save_path)
        print(f"Region screenshot saved to: {save_path}")
        
        # Print control identifiers if debugging is enabled and window was focused
        if debug_controls and win is not None:
            # Generate debug file path with same timestamp as screenshot
            debug_file_path = save_path.replace('.png', '_debug.txt')
            print_control_identifiers(win, debug_file_path)
        
        return save_path
        
    except Exception as e:
        print(f"Error taking region screenshot: {e}")
        return None

if __name__ == "__main__":
    # Clean up existing files first
    print("Cleaning up existing files...")
    cleanup_existing_files()
    
    # Automatically take screenshot with R10PosClient focus and debug controls
    print("\nTaking screenshot with R10PosClient focus...")
    screenshot_path = take_screenshot(focus_r10pos=True, debug_controls=True)
    
    if screenshot_path:
        print(f"✅ Screenshot completed successfully!")
        print(f"📁 File saved at: {os.path.abspath(screenshot_path)}")
    else:
        print("❌ Screenshot failed!")
