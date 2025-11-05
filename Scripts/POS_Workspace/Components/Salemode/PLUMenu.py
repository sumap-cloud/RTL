from pywinauto.application import Application
from pywinauto import mouse
import time

def click_plu_path(path_list, app_title=".*R10PosClient.*"):
    """
    Click through PLU hierarchy with flexible depth and paging for PLUMainListBox.
    """
    print(f"Connecting to '{app_title}'...")
    app = Application(backend="uia").connect(title_re=app_title, timeout=15)
    win = app.window(title_re=app_title)
    win.restore()
    win.set_focus()
    print("Connected.")

    for level, target_text in enumerate(path_list, start=1):
        # Determine which list to search
        if level == 1:
            list_auto_id = "PLUMainListBox"
        elif level == 2:
            list_auto_id = "PLUSubListBox"
        else:
            list_auto_id = "PLULeafListBox"

        print(f"Level {level}: Searching '{target_text}' in {list_auto_id}...")

        # Paging only for PLUMainListBox
        if list_auto_id == "PLUMainListBox":
            if not _find_and_click(win, list_auto_id, target_text):
                pager_down = win.child_window(auto_id="ConsumableDataPagerButtonDownID", control_type="Button")
                seen_pages = 0
                max_pages = 10  # safety stop
                while seen_pages < max_pages:
                    pager_down.click_input()
                    time.sleep(0.5)
                    if _find_and_click(win, list_auto_id, target_text):
                        break
                    seen_pages += 1
                else:
                    raise RuntimeError(f"'{target_text}' not found in {list_auto_id} after paging.")
            else:
                print(f"Clicked '{target_text}'")
        else:
            if not _find_and_click(win, list_auto_id, target_text):
                raise RuntimeError(f"'{target_text}' not found in {list_auto_id}")
            print(f"Clicked '{target_text}'")

        time.sleep(0.8)  # allow UI refresh

    print("PLU path click completed.")
    finish_btn = win.child_window(title="Finish", control_type="Button")
    finish_btn.click_input()
    time.sleep(0.5)  # allow UI to update  
    return True


def _find_and_click(win, list_auto_id, target_text):
    """Search for item in given list and click if found. Returns True/False."""
    plu_list = win.child_window(auto_id=list_auto_id, control_type="List")
    items = plu_list.descendants(control_type="ListItem")
    for item in items:
        texts = [c.window_text() for c in item.descendants(control_type="Text")]
        if any(target_text.lower() in (t or "").lower() for t in texts):
            rect = item.rectangle()
            mouse.click(button="left",
                        coords=(rect.left + rect.width() // 2,
                                rect.top + rect.height() // 2))
            print(f"Found and clicked item: {target_text}")
 
            return True
    return False


# Example usage
if __name__ == "__main__":
    click_plu_path(["Heavy & Misc", "Soft Drinks (10 Pack)", "coke z/s 10pk"])