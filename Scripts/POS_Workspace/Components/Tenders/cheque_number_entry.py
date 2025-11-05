from pywinauto import Application
import time
from typing import Optional, Dict

DEFAULT_WINDOW_TITLE = "Retalix.Client.POS.Presentation.ViewModels.BRM.StringInputDataViewModel"


def _connect(window_title: str = DEFAULT_WINDOW_TITLE, timeout: int = 30):
    """Connect to the target POS string input dialog and return (app_window, container)."""
    app = Application(backend="uia").connect(title_re=window_title, timeout=timeout)
    dlg = app.window(title_re=window_title)
    dlg.set_focus()
    container = dlg.child_window(auto_id="StringInputDataViewID", control_type="Custom")
    return dlg, container


def _get_prompt_text(container) -> str:
    try:
        title_ctrl = container.child_window(auto_id="Title", control_type="Text")
        return title_ctrl.window_text()
    except Exception as e:  # noqa: BLE001
        return f"<Could not retrieve title text: {e}>"


def _build_key_finder(on_screen_keyboard):
    def find_key(ch: str):
        low = ch.lower()
        candidates = (
            lambda: on_screen_keyboard.child_window(auto_id=low, control_type="Button"),
            lambda: on_screen_keyboard.child_window(title=low, control_type="Button"),
            lambda: on_screen_keyboard.child_window(title=ch, control_type="Button"),
        )
        for attempt in candidates:
            try:
                btn = attempt()
                btn.wait("enabled", timeout=1)
                return btn
            except Exception:  # noqa: BLE001
                pass
        for btn in on_screen_keyboard.descendants(control_type="Button"):
            try:
                if btn.window_text().lower() == low:
                    return btn
            except Exception:  # noqa: BLE001
                continue
        return None

    return find_key


def ChequeNumberEntry(
    text: str,
    window_title: str = DEFAULT_WINDOW_TITLE,
    restore_lowercase: bool = True,
    timeout: int = 30,
    inter_key_delay: float = 0.12,
) -> Dict[str, Optional[str]]:
    """Reusable API to type a string into the BRM StringInputData dialog via on‑screen keyboard.

    Returns dict with keys: success (bool), message_text, typed_value, error (optional).
    """
    result: Dict[str, Optional[str]] = {
        "success": False,
        "message_text": None,
        "typed_value": None,
        "error": None,
    }
    try:
        dlg, container = _connect(window_title, timeout=timeout)
        message_text = _get_prompt_text(container)
        result["message_text"] = message_text

        on_screen_keyboard = container.child_window(title="OnScreenKeyboard", auto_id="PosContainerAutomationID", control_type="Custom")
        toggle_button = on_screen_keyboard.child_window(title="A ↔ a", control_type="Button")
        find_key = _build_key_finder(on_screen_keyboard)

        uppercase_mode = False  # assume starts lowercase

        for ch in text:
            if ch.isalpha():
                need_upper = ch.isupper()
                if need_upper != uppercase_mode:
                    toggle_button.wait("enabled", timeout=5)
                    toggle_button.click_input()
                    time.sleep(0.15)
                    uppercase_mode = need_upper
            key_btn = find_key(ch)
            if key_btn is None:
                print(f"<Could not find key for '{ch}'>")
                continue
            key_btn.click_input()
            time.sleep(inter_key_delay)

        if restore_lowercase and uppercase_mode:
            try:
                toggle_button.click_input()
            except Exception:  # noqa: BLE001
                pass

        # Read back the typed value
        edit = container.child_window(auto_id="ValueTextBox", control_type="Edit")
        typed_value = edit.window_text()
        result["typed_value"] = typed_value

        # Click OK
        ok_btn = container.child_window(title="OK", control_type="Button")
        ok_btn.wait("enabled", timeout=5)
        ok_btn.click_input()

        result["success"] = True
        return result
    except Exception as e:  # noqa: BLE001
        result["error"] = str(e)
        return result


# Backwards compatible simple demo when run directly
if __name__ == "__main__":
    demo_text = "COGnizant"
    info = ChequeNumberEntry(demo_text)
    print(f"Prompt: {info['message_text']}")
    print(f"Typed: {info['typed_value']}")
    print(f"Success: {info['success']} Error: {info['error']}")