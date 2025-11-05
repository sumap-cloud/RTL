from pywinauto import Application
from pywinauto.findwindows import ElementNotFoundError
import ctypes
import time

def close_cash_drawer(win, status="close"):
    """
    Finds and interacts with the cash drawer button.

    Args:
        win (pywinauto.WindowSpecification): The application window object.
        status (str): "close" to click the button if enabled, otherwise does nothing.

    Returns:
        bool: True on success or if the button is not enabled, False if the button isn't found.
    """
    try:
        cash_btn = win.child_window(control_type="Button", title="Close Drawer")
        if not cash_btn.exists():
            print("❌ 'Close Drawer' button not found.")
            return False

        print("✅ 'Close Drawer' button found.")
        if status == "close":
            if cash_btn.is_enabled():
                print("▶️ Clicking 'Close Drawer' button to close the cash drawer.")
                cash_btn.click_input()
            else:
                # Assuming if it's not enabled, it's already closed, which is a success state.
                print("ℹ️ 'Close Drawer' button is not enabled (already closed).")
        else:
            print("ℹ️ Status is not 'close', so no action was taken on the cash drawer.")

        return True
    except Exception as e:
        print(f"❌ An error occurred in close_cash_drawer: {e}")
        return False

def move_with_ctypes(title, x, y, width, height):
    """
    Moves a window using ctypes, providing a fallback mechanism.

    Returns:
        bool: True if the window was moved, False if it was not found.
    """
    user32 = ctypes.WinDLL('user32')
    hwnd = user32.FindWindowW(None, title)

    if hwnd:
        flags = 0x0004 | 0x0010  # SWP_NOZORDER | SWP_NOACTIVATE
        user32.SetWindowPos(hwnd, 0, x, y, width, height, flags)
        print(f"✅ Moved '{title}' to ({x}, {y}) with size ({width}, {height})")
        return True
    else:
        print(f"❌ Window '{title}' not found by ctypes.")
        return False

def move_window(app, window_title, target_x, target_y, target_width=None, target_height=None):
    """
    Moves the application window to a specified position.

    Returns:
        bool: True if the window was moved successfully, False otherwise.
    """
    try:
        win = app.window(title=window_title, control_type="Window")
        win.set_focus()

        rect = win.rectangle()
        width = target_width or rect.width()
        height = target_height or rect.height()

        if win.is_maximized() or win.is_minimized():
            win.restore()
            time.sleep(0.5)

        return move_with_ctypes(window_title, target_x, target_y, width, height)

    except ElementNotFoundError:
        print(f"❌ Window '{window_title}' not found by pywinauto. Trying ctypes fallback...")
        # Fallback with a default size if the window object couldn't be found initially
        return move_with_ctypes(window_title, target_x, target_y, 800, 600)
    except Exception as e:
        print(f"❌ An unexpected error occurred in move_window: {e}")
        return False

def cashdrawer_move_and_close(status_to_set="close"):
    """
    Main function to connect to the app, move the window, and close the drawer.

    Returns:
        bool: True if all operations succeed, False otherwise.
    """
    try:
        # --- Configuration ---
        TARGET_X, TARGET_Y = 1500, 62
        WINDOW_TITLE = "Cognizant OPOS Cashdrawer"

        print("Connecting to application...")
        app = Application(backend="uia").connect(title_re=f".*{WINDOW_TITLE}.*")
        win = app.window(title_re=f".*{WINDOW_TITLE}.*")
        win.set_focus()
        print("✅ Successfully connected to application.")

        if not move_window(app, WINDOW_TITLE, TARGET_X, TARGET_Y):
            print("❌ Failed to move the window.")
            return False

        if not close_cash_drawer(win, status=status_to_set):
            print("❌ Failed to process the cash drawer closure.")
            return False

        print("\n✅ All cash drawer operations completed successfully.")
        return True

    except ElementNotFoundError:
        print(f"❌ Application window '{WINDOW_TITLE}' not found. Is the application running?")
        return False
    except Exception as e:
        print(f"❌ A critical error occurred: {e}")
        return False

if __name__ == "__main__":
    # Set to "close" to close the drawer, or any other string to just move the window.
    is_successful = cashdrawer_move_and_close(status_to_set="close")

    if is_successful:
        print("\n--- SCRIPT SUCCEEDED ---")
    else:
        print("\n--- SCRIPT FAILED ---")
