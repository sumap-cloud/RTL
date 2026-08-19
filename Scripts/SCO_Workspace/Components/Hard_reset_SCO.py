"""
Hard_reset_SCO.py
------------------
LAST-RESORT recovery: physically restart the SCO application and log the lane
back in, when the UI-only recovery in Reset_to_welcome.py cannot get back to
the Welcome screen.

WHY THIS EXISTS
    Reset_to_welcome.py clicks its way out of most stuck states, but some
    states cannot be cleared from the customer-facing UI at all — the clearest
    example being the "Assistance Needed / Cancel Purchase" store-approval
    popup, which regenerates itself indefinitely once the lane is in that
    state. When that happens every remaining test in the batch fails for a
    reason that has nothing to do with what it is testing.

    This module escalates:

        1. Soft reset            -> Reset_to_welcome.reset_to_welcome()
        2. Stop the SCO app      -> "Stop (updated).bat"
        3. Start the SCO app     -> "Start (updated).bat"
        4. Dismiss launch popup  -> click OK
        5. Store log in          -> lane is "Lane Closed" after a restart
        6. Verify Welcome screen

CONFIGURATION (environment variables — no code edit needed)
    SCO_LAUNCH_DIR   Folder holding the SCO Start/Stop .bat files.
                     Default: C:\\BAU SCO Automation\\SCO Application Launch
    SCO_START_BAT    Default: "Start (updated).bat"
    SCO_STOP_BAT     Default: "Stop (updated).bat"
    SCO_STORE_USER   Store-login operator id.  Default: taken from
                     Components/Complete_transaction.py (_STORE_USER)
    SCO_STORE_PASS   Store-login password.     Default: as above (_STORE_PASS)

    If the store login is rejected, set SCO_STORE_USER / SCO_STORE_PASS to
    working credentials rather than editing this file — see
    Documentation/KT_Sessions/06_Day6_Failures_Maintenance_and_Handover.md.

Usage
    Standalone (from the project root):
        .\\Scripts\\python.exe Scripts\\SCO_Workspace\\Components\\Hard_reset_SCO.py

    From code:
        from Components.Hard_reset_SCO import ensure_welcome_screen
        ensure_welcome_screen()          # soft reset, escalate only if needed

Exit code
    0 = SCO confirmed at the Welcome screen.
    1 = still not at Welcome (a human needs to look at the lane).
"""

import os
import subprocess
import sys
import time
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent          # .../SCO_Workspace
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from pywinauto import Application

from Components.Screen_identifier import identify_screen, dump_screen
from Components.report import logger
from Components.Reset_to_welcome import reset_to_welcome

try:
    from Components.Complete_transaction import _STORE_USER, _STORE_PASS
except Exception:                                        # pragma: no cover
    # Complete_transaction is the single source of truth for lane credentials.
    # If it cannot be imported, the caller must supply them via env vars.
    _STORE_USER, _STORE_PASS = "", ""

_SCO_TITLE_RE = ".*NCR NEXTGENUI.*"

_LAUNCH_DIR = Path(os.environ.get(
    "SCO_LAUNCH_DIR", r"C:\BAU SCO Automation\SCO Application Launch"))
_START_BAT = os.environ.get("SCO_START_BAT", "Start (updated).bat")
_STOP_BAT = os.environ.get("SCO_STOP_BAT", "Stop (updated).bat")

STORE_USER = os.environ.get("SCO_STORE_USER", _STORE_USER)
STORE_PASS = os.environ.get("SCO_STORE_PASS", _STORE_PASS)

_STOP_SETTLE_SEC = 12        # let taskkill finish and handles release
_WINDOW_WAIT_SEC = 180       # SCO takes a while to paint its first screen
_POST_LOGIN_WAIT_SEC = 60
_LOGIN_ATTEMPTS = 2          # keep low — real store accounts do lock out


# --------------------------------------------------------------------------
# low-level helpers
# --------------------------------------------------------------------------
def _say(msg, status="info"):
    print(msg)
    try:
        logger.log(msg, status=status)
    except Exception:
        pass


def _connect(timeout=10):
    try:
        app = Application(backend="uia").connect(
            title_re=_SCO_TITLE_RE, timeout=timeout)
        return app.window(title_re=_SCO_TITLE_RE)
    except Exception:
        return None


def _dump(win, label):
    print(f"\n--- 🔎 Hard_reset SCREEN DUMP: {label} ---")
    try:
        for it in dump_screen(win):
            if it["auto_id"] or it["text"]:
                print(f"   [{it['control_type']}] id='{it['auto_id']}' "
                      f"text='{it['text']}' enabled={it['enabled']}")
    except Exception as e:
        print(f"   (dump failed: {e})")
    print(f"--- end dump: {label} ---\n")


def _run_bat(name):
    """Run one of the SCO launcher .bat files from its own folder."""
    bat = _LAUNCH_DIR / name
    if not bat.exists():
        _say(f"❌ Launcher not found: {bat}", status="fail")
        return False
    try:
        _say(f"▶️  Running: {bat}")
        subprocess.run(["cmd", "/c", str(bat)], cwd=str(_LAUNCH_DIR),
                       capture_output=True, text=True, timeout=120)
        return True
    except Exception as e:
        _say(f"❌ Failed to run {bat}: {e}", status="fail")
        return False


def _wait_for_window(timeout=_WINDOW_WAIT_SEC):
    deadline = time.time() + timeout
    while time.time() < deadline:
        win = _connect(timeout=3)
        if win is not None:
            try:
                if win.exists() and win.is_visible():
                    _say("✅ NCR NEXTGENUI window is up.")
                    return win
            except Exception:
                pass
        time.sleep(3)
    _say(f"❌ NCR NEXTGENUI window did not appear within {timeout}s.",
         status="fail")
    return None


# --------------------------------------------------------------------------
# post-restart screens
# --------------------------------------------------------------------------
_OK_AIDS = ["ASAOKButton", "OK_Button", "GenericOKButton", "GenericButton",
            "Continue"]


def _dismiss_launch_popup(win, rounds=6):
    """The SCO shows a modal notice on start-up that must be OK'd before the
    lane screen is usable. Its auto_id varies by build, so try the known OK
    buttons and then any Button/Text literally labelled OK."""
    for _ in range(rounds):
        clicked = False
        for aid in _OK_AIDS:
            try:
                btn = win.child_window(auto_id=aid, control_type="Button")
                if btn.exists(timeout=0.5) and btn.is_visible():
                    btn.click_input()
                    _say(f"✅ Dismissed launch popup via '{aid}'.")
                    clicked = True
                    break
            except Exception:
                pass
        if not clicked:
            for ctrl_type in ("Button", "Text"):
                try:
                    c = win.child_window(title="OK", control_type=ctrl_type)
                    if c.exists(timeout=0.5) and c.is_visible():
                        c.click_input()
                        _say(f"✅ Dismissed launch popup via {ctrl_type} 'OK'.")
                        clicked = True
                        break
                except Exception:
                    pass
        if not clicked:
            return
        time.sleep(2)


def _type_into_input(win, text):
    """The store-login screen reuses one Edit ('InputTextBox') for the operator
    id and then for the password, each confirmed with 'EnterButton'."""
    try:
        edit = win.child_window(auto_id="InputTextBox", control_type="Edit")
        if not edit.exists(timeout=8):
            return False
        edit.click_input()
        time.sleep(0.3)
        try:
            edit.set_edit_text("")
        except Exception:
            pass
        edit.type_keys(text, with_spaces=False)
        time.sleep(0.3)
        enter_btn = win.child_window(auto_id="EnterButton", control_type="Button")
        if enter_btn.exists(timeout=3):
            enter_btn.click_input()
        time.sleep(2.5)
        return True
    except Exception as e:
        _say(f"⚠️ Could not type into the login field: {e}")
        return False


def _store_login(win):
    """Log the lane in from the 'Lane Closed' screen. Returns True if the lane
    left the closed/login screens."""
    for attempt in range(1, _LOGIN_ATTEMPTS + 1):
        _say(f"🔐 Store login attempt {attempt}/{_LOGIN_ATTEMPTS} "
             f"(user='{STORE_USER}')")
        try:
            store_login = win.child_window(auto_id="StoreLogin",
                                           control_type="Button")
            if store_login.exists(timeout=5) and store_login.is_visible():
                store_login.click_input()
                time.sleep(2)
        except Exception:
            pass

        if not _type_into_input(win, STORE_USER):
            _dump(win, "store login — operator id field not found")
            return False
        _type_into_input(win, STORE_PASS)

        time.sleep(4)
        screen = identify_screen(win)
        _say(f"   screen after login attempt: '{screen}'")
        if screen == "welcome_screen":
            return True
        try:
            still_closed = win.child_window(
                auto_id="StoreLogin", control_type="Button").exists(timeout=2)
        except Exception:
            still_closed = False
        if not still_closed:
            return True

        _say("⚠️ Store login appears to have been rejected "
             "(back on the Lane Closed screen).")

    _say("❌ Store login failed. Set SCO_STORE_USER / SCO_STORE_PASS to "
         "working credentials and retry. NOT retrying further — repeated "
         "attempts can lock the store account.", status="fail")
    _dump(win, "store login rejected")
    return False


def _wait_for_welcome(win, timeout=_POST_LOGIN_WAIT_SEC):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if identify_screen(win) == "welcome_screen":
                return True
        except Exception:
            pass
        time.sleep(3)
    return False


# --------------------------------------------------------------------------
# public API
# --------------------------------------------------------------------------
def hard_reset_sco():
    """Restart the SCO application and log the lane back in.
    Returns True only when the Welcome screen is confirmed."""
    logger.set_tc_id("Hard_reset_SCO")
    _say("=" * 70)
    _say("  HARD RESET — restarting the SCO application")
    _say("=" * 70)

    _run_bat(_STOP_BAT)
    _say(f"⏳ Waiting {_STOP_SETTLE_SEC}s for the SCO processes to exit...")
    time.sleep(_STOP_SETTLE_SEC)

    if not _run_bat(_START_BAT):
        logger.save()
        return False

    win = _wait_for_window()
    if win is None:
        logger.save()
        return False

    time.sleep(5)
    _dismiss_launch_popup(win)

    screen = identify_screen(win, verbose=True)
    _say(f"   screen after restart: '{screen}'")

    if screen != "welcome_screen":
        if not _store_login(win):
            logger.take_screenshot("Hard_reset_StoreLoginFailed")
            logger.save()
            return False

    if _wait_for_welcome(win):
        _say("✅ HARD RESET: SUCCESS — SCO at Welcome screen.", status="pass")
        logger.save()
        return True

    _say("❌ HARD RESET: FAILED — SCO did not reach the Welcome screen.",
         status="fail")
    _dump(win, "FINAL (hard reset failed)")
    logger.take_screenshot("Hard_reset_Failed")
    logger.save()
    return False


def ensure_welcome_screen():
    """Soft reset first; escalate to a full application restart only if the
    soft reset could not reach the Welcome screen. This is what the batch
    runner calls between test scripts."""
    try:
        if reset_to_welcome():
            return True
    except Exception as e:
        _say(f"⚠️ Soft reset raised: {e}")

    _say("⚠️ Soft reset could not reach the Welcome screen — escalating to a "
         "full SCO restart.")
    return hard_reset_sco()


if __name__ == "__main__":
    ok = ensure_welcome_screen()
    sys.exit(0 if ok else 1)
