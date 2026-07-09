import sys
sys.path.insert(0, 'Scripts/SCO_Workspace')
from pywinauto import Application
app = Application(backend='uia').connect(title_re='.*NCR NEXTGENUI.*')
win = app.window(title_re='.*NCR NEXTGENUI.*')
win.set_focus()
from Components.Screen_identifier import dump_screen
items = dump_screen(win)
for it in items:
    print(f"[{it['control_type']}] id={it['auto_id']!r} txt={it['text']!r} en={it['enabled']}")
