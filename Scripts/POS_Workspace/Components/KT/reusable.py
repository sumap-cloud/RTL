from promotion import select_promotion_by_name
from pywinauto import Application

def promotion():
    app = Application(backend="uia").connect(title_re=".*R10PosClient.*", found_index=0)
    win = app.window(title_re=".*R10PosClient.*")
    win.set_focus()
    
    select_promotion_by_name(win, "REWARDS OFFER")
    
promotion()