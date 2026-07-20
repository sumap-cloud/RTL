import sys
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from pywinauto import Application
from Components.Screen_identifier import identify_screen, dump_screen

app = Application(backend="uia").connect(title_re=".*NCR NEXTGENUI.*")
win = app.window(title_re=".*NCR NEXTGENUI.*")
screen = identify_screen(win, verbose=True)
print("IDENTIFIED SCREEN:", screen)
items = dump_screen(win)
for it in items:
    if it["auto_id"] or it["text"]:
        print(f"   [{it['control_type']}] id='{it['auto_id']}' text='{it['text']}' enabled={it['enabled']}")
