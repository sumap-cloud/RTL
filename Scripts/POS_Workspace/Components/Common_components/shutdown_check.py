from pywinauto import Application
import sys
from pathlib import Path
import time

# --- Setup for project root and imports ---
current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
from Components.Common_components.handle_any_popup_POS import handle_Any_popup

app = Application(backend="uia").connect(title_re=".*R10PosClient.*", found_index=0)
win = app.window(title_re=".*R10PosClient.*")
win.set_focus()
def shutdown_check():
    shutdownbtn = win.child_window(auto_id="btnPower", control_type="Button")
    if shutdownbtn.exists(timeout=5):
        shutdownbtn.click_input()
        print("Clicked shutdown button.")
        
        handle_Any_popup(specific_button="Cancel")
    else:
        print("Shutdown button not found.")

shutdown_check()