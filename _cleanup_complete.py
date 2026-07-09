import sys, time
sys.path.insert(0, 'Scripts/SCO_Workspace')
from pywinauto import Application
from Components import global_instance

app = Application(backend='uia').connect(title_re='.*NCR NEXTGENUI.*')
win = app.window(title_re='.*NCR NEXTGENUI.*')
win.set_focus()
global_instance.app = app
global_instance.win = win

from Components.Complete_transaction import complete_transaction
result = complete_transaction()
print('complete_transaction result:', result)
