import sys, time
sys.path.insert(0, '.')
from pywinauto import Application
from Components import global_instance
from Components.Add_item import _store_login_credentials

app = Application(backend='uia').connect(title_re='.*NCR NEXTGENUI.*', timeout=10)
win = app.window(title_re='.*NCR NEXTGENUI.*')
global_instance.app = app
global_instance.win = win
try:
    win.set_focus()
except Exception:
    pass

store_login_btn = win.child_window(auto_id="StoreLogin", control_type="Button")
if store_login_btn.exists(timeout=3):
    store_login_btn.click_input()
    time.sleep(1)
    _store_login_credentials(win, username="ATMGR5", password="abcd1234")
    time.sleep(1.5)
    print("Manager override submitted.")
else:
    print("StoreLogin not found.")

from Components.Screen_identifier import dump_screen
for i in dump_screen(win):
    print(f"[{i['control_type']}] id={i['auto_id']!r} txt={i['text']!r} en={i['enabled']}")
