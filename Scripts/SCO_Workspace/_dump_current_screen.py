import sys
sys.path.insert(0, '.')
from pywinauto import Application
app = Application(backend='uia').connect(title_re='.*NCR NEXTGENUI.*', timeout=10)
win = app.window(title_re='.*NCR NEXTGENUI.*')
from Components.Screen_identifier import dump_screen
items = dump_screen(win)
for i in items:
    print(f"[{i['control_type']}] id={i['auto_id']!r} txt={i['text']!r} en={i['enabled']}")
