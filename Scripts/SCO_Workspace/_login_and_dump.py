import sys, time
sys.path.insert(0, '.')
from pywinauto import Application
app = Application(backend='uia').connect(title_re='.*NCR NEXTGENUI.*', timeout=10)
win = app.window(title_re='.*NCR NEXTGENUI.*')
try:
    win.set_focus()
except Exception:
    pass

store_login_btn = win.child_window(auto_id="StoreLogin", control_type="Button")
if store_login_btn.exists(timeout=3):
    store_login_btn.click_input()
    time.sleep(1.5)

    input_box = win.child_window(auto_id="InputTextBox", control_type="Edit")
    enter_btn = win.child_window(auto_id="EnterButton", control_type="Button")
    if input_box.exists(timeout=5):
        input_box.click_input()
        input_box.type_keys("ATMGR5", pause=0.05)
        time.sleep(0.3)
        enter_btn.click_input()
        time.sleep(1.5)

    input_box = win.child_window(auto_id="InputTextBox", control_type="Edit")
    enter_btn = win.child_window(auto_id="EnterButton", control_type="Button")
    if input_box.exists(timeout=5):
        input_box.click_input()
        input_box.type_keys("abcd1234", pause=0.05)
        time.sleep(0.3)
        enter_btn.click_input()
        time.sleep(2)

from Components.Screen_identifier import dump_screen
for i in dump_screen(win):
    print(f"[{i['control_type']}] id={i['auto_id']!r} txt={i['text']!r} en={i['enabled']}")
