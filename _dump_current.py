import sys
import time
from pathlib import Path

# Add Scripts/SCO_Workspace to sys.path so we use the exact same imports
current_file_path = Path(__file__).resolve()
sc_workspace = current_file_path.parent / "Scripts" / "SCO_Workspace"

if str(sc_workspace) not in sys.path:
    sys.path.insert(0, str(sc_workspace))

from Components.Login_POS import login_pos
from Components.Screen_identifier import dump_screen
from Components import global_instance

def main():
    if not login_pos():
        print("Login failed")
        return
    win = global_instance.win
    items = dump_screen(win)
    for it in items:
        if it['auto_id'] or it['text']:
            print(f"[{it['control_type']}] id={it['auto_id']!r} txt={it['text']!r} en={it['enabled']}")

if __name__ == "__main__":
    main()
