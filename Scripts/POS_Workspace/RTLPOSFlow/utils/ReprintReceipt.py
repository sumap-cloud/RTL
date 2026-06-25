from pywinauto import Application
from pywinauto.keyboard import send_keys
import re
from Components.Common_components.toggle_menu_navigation import toggle_menu_navigate

class ReprintReceiptFlow:
    """Encapsulate the Reprint Receipt navigation and value extraction."""
    def __init__(self, title_re: str = '.*R10PosClient.*'):
        self.title_re = title_re
        self.app = None
        self.win = None

    def connect(self, timeout: int = 10):
        try:
            self.app = Application(backend="uia").connect(title_re=self.title_re, timeout=timeout)
            self.win = self.app.window(title_re=self.title_re)
            try:
                self.win.set_focus()
            except Exception:
                pass
            return True
        except Exception:
            # try a generic title fallback
            try:
                self.app = Application(backend="uia").connect(title_re='.*R10PosClient.*', timeout=timeout)
                self.win = self.app.window(title_re='.*R10PosClient.*')
                try:
                    self.win.set_focus()
                except Exception:
                    pass
                return True
            except Exception:
                return False

    def _click_button_with_fallback(self, window, exact_titles, contains_terms=None, timeout=5):
        for title in exact_titles:
            try:
                btn = window.child_window(title=title, control_type="Button").wait('enabled', timeout=timeout)
                try:
                    btn.click_input()
                except Exception:
                    btn.click()
                return True
            except Exception:
                continue

        if contains_terms:
            for b in window.descendants(control_type="Button"):
                try:
                    text = (b.window_text() or "").lower()
                    if all(term in text for term in contains_terms):
                        try:
                            b.click_input()
                        except Exception:
                            b.click()
                        return True
                except Exception:
                    continue
        return False

    def open_reprint_and_search(self):
        if not toggle_menu_navigate(["Reprint Receipt"]):
            print("Failed to navigate to Reprint Receipt in toggle menu")
            return False
        if not self.connect():
            print("Failed to connect to POS window after navigating to Reprint Receipt")
            return False
        # Click 'Search transactions'
        if not self._click_button_with_fallback(self.win, exact_titles=["Search transactions", "Search transaction"], contains_terms=["search","trans"]):
            print("'Search transactions' button not found in Reprint Receipt view.")
        return True

    def open_pos_parameters(self):
        # Click 'POS Parameters' (exact + fallback) or fallback to toggle menu
        if not self._click_button_with_fallback(self.win, exact_titles=["POS Parameters"], contains_terms=["pos","param"]):
            print("'POS Parameters' button not found in view, attempting toggle menu navigation...")
            try:
                if toggle_menu_navigate(["POS Parameters"]):
                    print("Opened 'POS Parameters' via toggle menu navigation.")
                    # reconnect window
                    self.connect()
                    return True
                else:
                    print("Failed to open 'POS Parameters' via toggle menu navigation.")
                    return False
            except Exception as em:
                print(f"Exception while falling back to toggle_menu_navigate for POS Parameters: {em}")
                return False
        return True

    def extract_store_pos_trans(self):
        # spatial matching algorithm
        try:
            text_controls = [t for t in self.win.descendants(control_type="Text")]
            edit_controls = [e for e in self.win.descendants(control_type="Edit")]
        except Exception:
            text_controls = []
            edit_controls = []

        def _vertical_overlap(a, b):
            top = max(a.top, b.top)
            bottom = min(a.bottom, b.bottom)
            if bottom <= top:
                return 0
            overlap = bottom - top
            height = min(a.bottom - a.top, b.bottom - b.top)
            if height <= 0:
                return 0
            return overlap / height

        store = None
        pos = None
        trans = None

        for ed in edit_controls:
            try:
                r = ed.rectangle()
            except Exception:
                continue
            best_lbl = None
            best_dist = None
            for lbl in text_controls:
                try:
                    l = lbl.rectangle()
                    if l.right > r.left + 10:
                        continue
                    ov = _vertical_overlap(l, r)
                    if ov < 0.25:
                        continue
                    dist = r.left - l.right
                    if dist < 0:
                        continue
                    if best_dist is None or dist < best_dist:
                        best_dist = dist
                        best_lbl = lbl
                except Exception:
                    continue
            if best_lbl:
                try:
                    lbl_text = (best_lbl.window_text() or "").lower()
                    val = (ed.window_text() or "").strip()
                    digits = re.sub(r"[^0-9]", "", val)
                    if "store" in lbl_text and not store and digits:
                        store = digits
                        continue
                    if ("pos" in lbl_text or "pos no" in lbl_text) and not pos and digits:
                        pos = digits
                        continue
                    if ("trans" in lbl_text or "transaction" in lbl_text) and not trans and digits:
                        trans = digits
                        continue
                except Exception:
                    pass

        # fallback numeric scan
        if not store or not pos or not trans:
            for ed in edit_controls:
                try:
                    v = (ed.window_text() or "").strip()
                    if not v:
                        continue
                    if re.search(r"\d{1,2}/\d{1,2}/\d{2,4}", v) or re.search(r"\d{4}-\d{2}-\d{2}", v) or ('/' in v and '-' in v) or ('to' in v.lower() and '/' in v):
                        continue
                    digits = re.sub(r"[^0-9]", "", v)
                    if not digits or len(digits) > 6:
                        continue
                    if not store and 3 <= len(digits) <= 6:
                        store = digits
                        continue
                    if not pos and 2 <= len(digits) <= 3 and digits != store:
                        pos = digits
                        continue
                    if not trans and 3 <= len(digits) <= 6 and digits != store and digits != pos:
                        trans = digits
                        continue
                except Exception:
                    continue

        # Attempt to close the view by clicking Cancel before returning
        try:
            if self.click_cancel():
                print("Clicked Cancel from extract_store_pos_trans.")
        except Exception:
            pass

        return store, pos, trans
    
    def click_cancel(self):
        # Ensure we have a connected window
        if not self.win:
            if not self.connect():
                return False

        # Enumerate buttons (silent)
        try:
            buttons = [b for b in self.win.descendants(control_type="Button")]
        except Exception:
            buttons = []

        candidates = []
        for b in buttons:
            try:
                txt = (b.window_text() or "").strip()
                # Safely obtain automation_id if available
                aid = ''
                try:
                    aid_val = getattr(b, 'automation_id', None)
                    if callable(aid_val):
                        aid = aid_val()
                    elif aid_val is not None:
                        aid = str(aid_val)
                except Exception:
                    try:
                        # some wrappers expose element_info
                        aid = str(getattr(b.element_info, 'automation_id', '') or '')
                    except Exception:
                        aid = ''

                try:
                    rect = b.rectangle()
                    center = (int((rect.left+rect.right)/2), int((rect.top+rect.bottom)/2))
                except Exception:
                    center = None

                # prioritize likely cancel-like buttons
                low = txt.lower()
                if any(k in low for k in ("cancel", "close", "dismiss")) or (aid and "cancel" in aid.lower()):
                    candidates.insert(0, (b, center))
                else:
                    candidates.append((b, center))
            except Exception:
                continue

        # Try candidates first
        from pywinauto import mouse
        for (b, center) in candidates:
            try:
                try:
                    b.click_input()
                    return True
                except Exception:
                    try:
                        b.click()
                        return True
                    except Exception:
                        try:
                            b.invoke()
                            return True
                        except Exception:
                            pass

                # try clicking by screen coords
                if center:
                    try:
                        mouse.click(button='left', coords=center)
                        return True
                    except Exception:
                        pass
            except Exception:
                continue

        # Strategy: try generic title regex match as last resort
        try:
            btn = self.win.child_window(title_re=r"(?i)cancel|close|dismiss", control_type="Button")
            if btn.exists(timeout=1):
                try:
                    btn.click_input()
                    return True
                except Exception:
                    try:
                        btn.click()
                        return True
                    except Exception:
                        try:
                            btn.invoke()
                            return True
                        except Exception:
                            pass
        except Exception:
            pass

        # Final fallback: keyboard ESC
        try:
            send_keys('{ESC}')
            return True
        except Exception:
            pass

        return False
