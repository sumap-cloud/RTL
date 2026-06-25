"""
Verify_exciting_news_prompt.py
------------------------------
Detect and dismiss the SCO "Exciting News" prompt that appears after the
loyalty card scan (or after moving to tender mode) when the customer's
points cross the 2000-point threshold for various card segments.

Per-segment expected message variations:
  - Registered EDR : "Exciting News! You've just earned $xx ..."
  - SFC (105)      : "Exciting News! You've just banked $xx into your Christmas savings."
  - QFF (104)      : "Exciting News! You've just converted xxx Qantas Points ..."
  - Temporary card : "Great news – you could save $xx off future shop! ..."
  - SFL (109)      : "YOUR SAVINGS ARE GROWING. You now have $xx ..."
  - AirNZ (110)    : "Exciting News! You've just earned $xx Airpoints Dollars ..."

Detection strategy (OCR, like Redeem_choice_offer.py):
  1. Take a screenshot of the SCO window (or full screen) and OCR it.
  2. If any of the trigger phrases appears, log the full message and
     dismiss the prompt by clicking the first available "continue"-style
     button (Continue / OK / ASAOK / GenericOK / GenericButton / CustomSkip).

This component is intentionally NON-FATAL when the prompt does not
appear — the prompt depends on the card's live point balance at run
time, which can drift between runs. Returning False just signals
"no prompt detected"; the caller decides whether to escalate.
"""

import sys
import time
from pathlib import Path

import pytesseract
from PIL import ImageGrab

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components import global_instance
from Components.report import logger

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Substrings that confirm an "Exciting News" prompt is on screen.
# Lower-cased; OCR text is also lower-cased before comparison.
_TRIGGER_PHRASES = (
    "exciting news",
    "great news",
    "your savings are growing",
    "you've just earned",
    "you have just earned",
    "you've just banked",
    "you have just banked",
    "you've just converted",
    "you have just converted",
    "save $",
)

# Buttons (auto_id) that dismiss this prompt — try in order.
# CONFIRMED from live control dump (TC_003): the Exciting News popup is
# rendered inside `PopupFrame` with `List1Button` (text="OK") as the
# primary dismiss action and `List2Button` (text="Yes") as the secondary.
_DISMISS_BUTTON_IDS = (
    "List1Button",         # ← OK (confirmed from PopupFrame dump)
    "List2Button",         # ← Yes (fallback if List1 isn't the dismiss)
    "ContinueButton",
    "Continue_Button",
    "OK_Button",
    "ASAOKButton",
    "GenericOKButton",
    "GenericButton",
    "CustomSkip",
    "SkipChoiceOfferPrompt",
)


def _ocr_window_text():
    """Grab a screenshot of the SCO window (full screen fallback) and return OCR text."""
    win = global_instance.win
    bbox = None
    if win is not None:
        try:
            rect = win.rectangle()
            bbox = (rect.left, rect.top, rect.right, rect.bottom)
        except Exception:
            bbox = None
    try:
        img = ImageGrab.grab(bbox=bbox) if bbox else ImageGrab.grab()
        gray = img.convert("L")
        w, h = gray.size
        gray = gray.resize((w * 2, h * 2))  # zoom for OCR clarity
        return pytesseract.image_to_string(gray, config="--psm 6")
    except Exception as e:
        print(f"⚠️ OCR screenshot failed: {e}")
        return ""


def _find_trigger(ocr_text):
    """Return the matched trigger phrase if any of _TRIGGER_PHRASES appears in OCR text."""
    lowered = ocr_text.lower()
    for phrase in _TRIGGER_PHRASES:
        if phrase in lowered:
            return phrase
    return None


def _extract_message_line(ocr_text, trigger):
    """Pull a short representative line from the OCR output for logging."""
    trigger_l = trigger.lower()
    for line in ocr_text.splitlines():
        if trigger_l in line.lower():
            return line.strip()
    return ocr_text.strip().splitlines()[0] if ocr_text.strip() else "(no text)"


def _dismiss_prompt():
    """Click the first available Continue/OK button. Returns True if any was clicked."""
    win = global_instance.win
    if win is None:
        print("❌ global_instance.win is None — cannot dismiss exciting news prompt.")
        return False

    for aid in _DISMISS_BUTTON_IDS:
        try:
            btn = win.child_window(auto_id=aid, control_type="Button")
            # Per project rule: NEVER use is_enabled() on NCR SCO popup buttons
            if btn.exists(timeout=1.0):
                btn.click_input()
                logger.log(f"✅ Dismissed Exciting News prompt via '{aid}'.", status="pass")
                print(f"✅ Dismissed Exciting News prompt via '{aid}'.")
                time.sleep(1.5)
                return True
        except Exception:
            continue
    return False


def _detect_via_uia():
    """
    Fast UIA-first detector. Looks for the `Instructions` Text element inside
    `PopupFrame` (confirmed from live control dump). Returns the on-screen
    message text if found, else None.

    Typical timing: <0.2s per check vs. ~7s for OCR — much safer for
    one-shot EDR cards where the popup may auto-dismiss quickly.
    """
    win = global_instance.win
    if win is None:
        return None
    # Primary: Instructions text inside PopupFrame
    for aid in ("Instructions", "GiftCardInstructions"):
        try:
            txt_ctrl = win.child_window(auto_id=aid, control_type="Text")
            if txt_ctrl.exists(timeout=0.3):
                text = ""
                try:
                    text = txt_ctrl.window_text() or ""
                except Exception:
                    text = ""
                if text.strip():
                    return text.strip()
        except Exception:
            continue
    return None


def verify_exciting_news_prompt(timeout_seconds=15, poll_interval=0.5):
    """
    Poll for the Exciting News prompt.

    Strategy (per-iteration):
      1. UIA fast-path — look for PopupFrame.Instructions Text element
         (sub-second; reliable).
      2. OCR fallback — full window screenshot + Tesseract (slow; only
         runs every ~3rd iteration to keep CPU low).

    Args:
        timeout_seconds: total time to keep looking for the prompt.
        poll_interval:   seconds between checks (default 0.5s for fast UIA path).

    Returns:
        bool: True if the prompt was detected AND dismissed.
              False otherwise (caller decides whether that is fatal).
    """
    win = global_instance.win
    if win is None:
        logger.log(
            "❌ verify_exciting_news_prompt: global_instance.win is None.",
            status="fail",
        )
        print("❌ verify_exciting_news_prompt: global_instance.win is None.")
        return False

    try:
        win.set_focus()
    except Exception:
        pass

    deadline = time.time() + timeout_seconds
    attempt = 0
    while time.time() < deadline:
        attempt += 1

        # --- 1. Fast UIA detector --------------------------------------
        uia_text = _detect_via_uia()
        if uia_text:
            # Confirm it's actually the Exciting News popup by matching a
            # known trigger phrase — protects against unrelated popups
            # that happen to use the same `Instructions` auto_id.
            trigger = _find_trigger(uia_text)
            if trigger or "exciting" in uia_text.lower() or "great news" in uia_text.lower() or "savings" in uia_text.lower():
                logger.log(
                    f"✅ Exciting News prompt detected via UIA (trigger='{trigger or 'savings/exciting'}').",
                    status="pass",
                )
                logger.log(f"   Captured message: {uia_text}", status="pass")
                print(f"✅ Exciting News prompt detected via UIA: {uia_text}")
                try:
                    logger.take_screenshot("Exciting_News_Prompt")
                except Exception:
                    pass
                if _dismiss_prompt():
                    return True
                logger.log(
                    "⚠️ Exciting News prompt detected (UIA) but no known "
                    f"dismiss button ({', '.join(_DISMISS_BUTTON_IDS)}) was clickable.",
                    status="info",
                )
                print("⚠️ Exciting News prompt detected (UIA) but no dismiss button found.")
                return False

        # --- 2. OCR fallback (run sparingly — every ~3rd iteration) ----
        if attempt % 3 == 0:
            ocr_text = _ocr_window_text()
            trigger = _find_trigger(ocr_text)
            if trigger:
                message = _extract_message_line(ocr_text, trigger)
                logger.log(
                    f"✅ Exciting News prompt detected via OCR (trigger='{trigger}').",
                    status="pass",
                )
                logger.log(f"   Captured message: {message}", status="pass")
                print(f"✅ Exciting News prompt detected via OCR (trigger='{trigger}').")
                print(f"   Captured message: {message}")
                try:
                    logger.take_screenshot("Exciting_News_Prompt")
                except Exception:
                    pass
                if _dismiss_prompt():
                    return True
                logger.log(
                    "⚠️ Exciting News prompt detected (OCR) but no known "
                    f"dismiss button ({', '.join(_DISMISS_BUTTON_IDS)}) was clickable.",
                    status="info",
                )
                print("⚠️ Exciting News prompt detected (OCR) but no dismiss button found.")
                return False

        time.sleep(poll_interval)

    # Non-fatal: the prompt may not have appeared because the card's actual
    # live point balance didn't cross 2000 this run. Log as info for now;
    # the TC script will upgrade this to pass if EE log validates successfully.
    logger.log(
        f"ℹ️ No Exciting News prompt detected after {timeout_seconds}s "
        f"({attempt} detection attempts) — EE log will be the ground truth.",
        status="info",
    )
    print(
        f"⚠️ No Exciting News prompt detected after {timeout_seconds}s "
        f"({attempt} OCR attempts) — continuing."
    )
    return False
