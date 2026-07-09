import sys, time
sys.path.insert(0, 'Scripts/SCO_Workspace')
from pywinauto import Application
app = Application(backend='uia').connect(title_re='.*NCR NEXTGENUI.*')
win = app.window(title_re='.*NCR NEXTGENUI.*')
win.set_focus()

btn = win.child_window(auto_id="StoreButton1", control_type="Button")
print("StoreButton1 exists:", btn.exists(timeout=2))
btn.click_input()
time.sleep(2.0)

from Components.Screen_identifier import dump_screen
items = dump_screen(win)
print("--- After StoreButton1 ---")
for it in items:
    print(f"[{it['control_type']}] id={it['auto_id']!r} txt={it['text']!r} en={it['enabled']}")
