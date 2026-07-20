import sys, time
sys.path.insert(0, '.')
from pywinauto import Application
from Components import global_instance
from Components.Scan_item import scan_item

app = Application(backend='uia').connect(title_re='.*NCR NEXTGENUI.*', timeout=10)
win = app.window(title_re='.*NCR NEXTGENUI.*')
global_instance.app = app
global_instance.win = win
try:
    win.set_focus()
except Exception:
    pass

scan_item(win, "9300677010670", label="single duplicate test scan")
time.sleep(2)

from Components.Screen_identifier import dump_screen
items = dump_screen(win)
for i in items:
    print(f"[{i['control_type']}] id={i['auto_id']!r} txt={i['text']!r} en={i['enabled']}")
