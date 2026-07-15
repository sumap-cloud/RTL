import sys, time
sys.path.insert(0, '.')
from pywinauto import Application
app = Application(backend='uia').connect(title_re='.*NCR NEXTGENUI.*', timeout=10)
win = app.window(title_re='.*NCR NEXTGENUI.*')
try:
    win.set_focus()
except Exception:
    pass
btn = win.child_window(auto_id="OK_Button", control_type="Button")
if btn.exists(timeout=3):
    btn.click_input()
    print("Dismissed 'RTI Event was not found' popup.")
time.sleep(1.5)
from Components.Screen_identifier import dump_screen
for i in dump_screen(win):
    print(f"[{i['control_type']}] id={i['auto_id']!r} txt={i['text']!r} en={i['enabled']}")
