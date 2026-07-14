"""
tc038_investigate_scroll2.py — LIVE investigation, part 2.
CartReceipt supports the UIA scroll pattern (iface_scroll). Scroll to the
top, dump visible rows, then scroll down step by step collecting all rows
(by their ItemDescription+ItemPrice signature) until no new rows appear.
This confirms whether all 11 physical items + 1 promo row can be recovered
via programmatic scrolling.
"""
import sys
import time
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
wrapper = cart_list.wrapper_object()


def read_rows():
    rows = []
    for item in wrapper.children(control_type="ListItem"):
        desc_text = ""
        price_text = ""
        for child in item.children():
            aid = child.element_info.automation_id
            if aid == "ItemDescription" and not desc_text:
                desc_text = child.window_text()
            elif aid == "ItemPrice" and not price_text:
                price_text = child.window_text()
        if desc_text:
            rows.append((desc_text, price_text))
    return rows


# --- Try scrolling to top first ---
print("\n--- Attempting scroll to top ---")
try:
    for _ in range(15):
        wrapper.scroll("up", "page")
        time.sleep(0.15)
    print("Scrolled up 15x (page).")
except Exception as e:
    print(f"scroll up error: {e}")

time.sleep(0.5)
top_rows = read_rows()
print(f"Rows at top: {len(top_rows)}")
for r in top_rows:
    print(f"  {r}")

# --- Now scroll down incrementally, collecting all unique rows ---
print("\n--- Scrolling down collecting all rows ---")
all_rows = []
seen = set()
for r in top_rows:
    key = r
    if key not in seen:
        seen.add(key)
        all_rows.append(r)

for step in range(20):
    try:
        wrapper.scroll("down", "line", count=2)
    except Exception as e:
        print(f"scroll down error at step {step}: {e}")
        break
    time.sleep(0.2)
    rows = read_rows()
    new_found = False
    for r in rows:
        if r not in seen:
            seen.add(r)
            all_rows.append(r)
            new_found = True
    print(f"step {step}: visible={len(rows)} total_unique_so_far={len(all_rows)} new_found={new_found}")

print(f"\n=== FINAL UNIQUE ROWS ({len(all_rows)}) ===")
for r in all_rows:
    print(f"  {r}")
