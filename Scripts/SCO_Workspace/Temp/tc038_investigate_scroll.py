"""
tc038_investigate_scroll.py — LIVE investigation.
Dumps the full descendant tree of CartReceipt (and its ancestors) to find
scrollbar / ScrollViewer controls so we can scroll the list and read ALL
basket rows (WPF list virtualization means only ~7 of 11 rows are in the
UIA tree at any given scroll position).
"""
import sys
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from pywinauto import Application
from Components import global_instance

app = Application(backend="uia").connect(title_re=".*NCR NEXTGENUI.*")
win = app.window(title_re=".*NCR NEXTGENUI.*")
global_instance.app = app
global_instance.win = win
try:
    win.set_focus()
except Exception:
    pass
print("Connected.")

cart_list = win.child_window(auto_id="CartReceipt", control_type="List")
print(f"CartReceipt exists: {cart_list.exists(timeout=3)}")

wrapper = cart_list.wrapper_object()
print(f"CartReceipt rectangle: {wrapper.rectangle()}")

# List all ListItem children currently in the tree
items = wrapper.children(control_type="ListItem")
print(f"\nDirect ListItem children count: {len(items)}")
for i, it in enumerate(items):
    try:
        desc = ""
        for c in it.children():
            if c.element_info.automation_id == "ItemDescription":
                desc = c.window_text()
                break
        print(f"  [{i}] {desc!r}  rect={it.rectangle()}")
    except Exception as e:
        print(f"  [{i}] error: {e}")

# Look for scrollbar controls anywhere near/inside CartReceipt's parent
print("\n--- Searching for ScrollBar controls near CartReceipt ---")
try:
    parent = wrapper.parent()
    print(f"Parent control_type: {parent.element_info.control_type}, auto_id: {parent.element_info.automation_id}")
    for desc in parent.descendants():
        try:
            ct = desc.element_info.control_type
            if ct in ("ScrollBar", "Thumb"):
                aid = desc.element_info.automation_id
                print(f"  Found: [{ct}] auto_id={aid!r} rect={desc.rectangle()} visible={desc.is_visible()}")
        except Exception:
            continue
except Exception as e:
    print(f"Parent search error: {e}")

# Try common WPF scroll patterns available on the List itself
print("\n--- Checking scroll support on CartReceipt wrapper ---")
for method_name in ("scroll", "get_scroll_pattern", "iface_scroll"):
    has = hasattr(wrapper, method_name)
    print(f"  hasattr(wrapper, '{method_name}') = {has}")

try:
    print(f"  wrapper.legacy_properties(): {wrapper.legacy_properties()}")
except Exception as e:
    print(f"  legacy_properties() error: {e}")
