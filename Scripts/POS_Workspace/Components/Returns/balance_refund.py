import time
import re
from pywinauto import Application
from pywinauto.findbestmatch import MatchError
from pywinauto.timings import TimeoutError

def read_balance_due(win):
    """Finds and prints the Balance Due amount from the screen."""
    print("\n💰 Reading Balance Due...")
    try:
        # This method looks for a specific control class 'AmountControl' which is
        # often used for displaying amounts in this application.
        candidates = []
        for ctrl in win.descendants(control_type="Custom"):
            if "AmountControl" in ctrl.class_name():
                txt = None
                # First, try to find a TextBlock descendant within the control,
                # as this is a common pattern for holding the visible text.
                try:
                    text_block = ctrl.descendants(control_type="Text")[0]
                    txt = text_block.window_text()
                except (IndexError, TimeoutError):
                    # If no TextBlock is found, fall back to reading the text
                    # from the AmountControl itself.
                    print("  - No TextBlock found, checking the control's main text...")
                    txt = ctrl.window_text()

                # Check if the text is a valid number (e.g., "-13.00")
                if txt and re.fullmatch(r'-?\$?\d+\.\d+', txt.strip()):
                    # Store the amount and its vertical position on the screen
                    candidates.append((float(txt.strip().replace('$', '')), ctrl.rectangle().top))
        
        if not candidates:
            print("❌ Could not find the Balance Due amount using any method.")
            return None

        # The Balance Due is usually the lowest amount control on the screen.
        # We sort by the vertical position (top coordinate) in reverse.
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        balance_due = candidates[0][0]
        print(f"  ✅ Balance Due Found: {balance_due:.2f}")
        return balance_due

    except Exception as e:
        print(f"❌ An error occurred while reading balance due: {e}")
        return None

def main():
    """
    Main function to connect to the POS and read the balance due.
    """
    try:
        # Connect to the running application
        app = Application(backend="uia").connect(title_re=".*R10PosClient.*", timeout=10)
        win = app.window(title_re=".*R10PosClient.*")
        win.set_focus()
        print("✅ POS window found and focused.")
    except Exception as e:
        print(f"❌ Could not connect or focus POS window: {e}")
        return

    # Call the function to read the balance due
    read_balance_due(win)


if __name__ == "__main__":
    main()
