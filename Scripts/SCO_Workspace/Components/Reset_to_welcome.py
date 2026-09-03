"""
Reset_to_welcome.py
--------------------
Best-effort recovery script that forces the SCO back to the Welcome/idle
screen from WHATEVER screen it is currently on (pass, fail, mid-transaction,
hung popup, etc.).

WHY THIS EXISTS:
    run_tests.bat runs each TC_*.py script as its own python.exe process.
    If a script errors out or hangs mid-transaction, the SCO can be left on
    a basket screen, a tender screen, or a stuck popup. The NEXT script in
    the batch then starts login_pos() assuming an idle Welcome screen and
    can fail for reasons unrelated to what it's actually testing.

    This script is meant to be run by run_tests.bat AFTER every TC script,
    regardless of that script's exit code, so every test always starts
    from a known-clean Welcome screen.

GROUND TRUTH ONLY:
    Every auto_id used below has been confirmed either from a live control
    dump captured during this project's TC_050 live-build session, or from
    the existing verified ScreenCache/*.json definitions (welcome_screen.json,
    select_payment.json) / existing Components/*.py files. Nothing here is
    guessed.

Usage:
    python Scripts\\SCO_Workspace\\Components\\Reset_to_welcome.py

Exit code:
    Always 0 (best-effort). Prints a clear "RESET: SUCCESS" or
    "RESET: FAILED" marker plus a full diagnostic dump on failure so the
    batch runner log always shows what actually happened.
"""

import sys
import time
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from pywinauto import Application
from Components.Screen_identifier import identify_screen, dump_screen
from Components.report import logger
# Reuse the already-validated "Assistance Needed / Cancel Purchase" popup
# decliner from Complete_transaction.py instead of duplicating the Store
# Log In (ms/abcd1234) + click-'No' logic here.
from Components.Complete_transaction import (
    _handle_cancel_purchase_assistance,
    store_login_authenticate,
)

_SCO_TITLE_RE = ".*NCR NEXTGENUI.*"
_MAX_ROUNDS = 25
_ROUND_SLEEP = 1.5
_CONNECT_TIMEOUT = 15
# Give up early instead of burning all 25 rounds on a screen we cannot act on
# (previously the loop oscillated redemption_prompt <-> assistance_needed for
# the full budget before escalating to the hard SCO restart).
_MAX_ASSISTANCE_ATTEMPTS = 3
_MAX_STAGNANT_ROUNDS = 8

# --- Ordered recovery actions -------------------------------------------
# Priority 1: abort/void an in-progress sale so the basket is cleared.
_ABORT_SALE_AIDS = [
    "CancelAllBtn",
    "GS1VoidAllButton",
    "OnAccountVoidAllButton",
    "OnDeliveryPartnerVoidAllButton",
    "CancelMain",
    # 'GoBackSale' is the Go Back button on the Select Payment Type /
    # redemption_prompt screen (confirmed in live dumps and in
    # Temp/tc038_click_gobacksale.py). Without it the reset loop had NOTHING
    # clickable on the tender screen and just spun until the round budget
    # ran out. Clicking it returns to the basket/scan screen where
    # CancelAllBtn above is reachable.
    "GoBackSale",
    "GoBackBtn",
    "GoBackButton",
    "CancelButton",
]

# Priority 2: dismiss any blocking popup.
_DISMISS_POPUP_AIDS = [
    "ASAOKButton",
    "OK_Button",
    "GenericOKButton",
    "GenericButton",
    "ItemRemovedButton",
    "No_Button",
    "Yes_Button",
    "CancelCoupon",
    "Continue",
    "DataNeeded_GoBack",
    "CancelAcceptWeight",
    "CustomSkip",
]

# Priority 3: leave any attendant/UNav overlay.
_LEAVE_OVERLAY_AIDS = [
    "ExitUNavButton",
    "CancelUNavButton",
]

_ALL_RECOVERY_AIDS = _ABORT_SALE_AIDS + _DISMISS_POPUP_AIDS + _LEAVE_OVERLAY_AIDS


def _connect():
    """Connect fresh to the live NCR NEXTGENUI window (own process)."""
    try:
        app = Application(backend="uia").connect(title_re=_SCO_TITLE_RE, timeout=_CONNECT_TIMEOUT)
        win = app.window(title_re=_SCO_TITLE_RE)
        print("✅ Reset_to_welcome: connected to NCR NEXTGENUI window.")
        return win
    except Exception as e:
        print(f"❌ Reset_to_welcome: could not connect to NCR NEXTGENUI window: {e}")
        return None


def _print_dump(label, win):
    print(f"\n--- 🔎 Reset_to_welcome SCREEN DUMP: {label} ---")
    try:
        items = dump_screen(win)
        for it in items:
            if it["auto_id"] or it["text"]:
                print(f"   [{it['control_type']}] id='{it['auto_id']}' text='{it['text']}' enabled={it['enabled']}")
        if not items:
            print("   (no visible identified controls)")
    except Exception as e:
        print(f"   (dump failed: {e})")
    print(f"--- end dump: {label} ---\n")


def _try_click(win, auto_id):
    """Click auto_id only if it exists AND is visible. Returns True if clicked."""
    try:
        btn = win.child_window(auto_id=auto_id, control_type="Button")
        if btn.exists(timeout=0.5) and btn.is_visible():
            btn.click_input()
            print(f"✅ Reset_to_welcome: clicked '{auto_id}'.")
            return True
    except Exception:
        pass
    return False


def reset_to_welcome():
    """
    Force the SCO back to the Welcome screen. Returns True on success.
    Never raises — this is a best-effort recovery utility for the batch runner.
    """
    logger.set_tc_id("Reset_to_welcome")
    win = _connect()
    if win is None:
        logger.log("❌ Reset_to_welcome: SCO window not found.", status="fail")
        return False

    assistance_attempts = 0
    stagnant_rounds = 0
    last_screen = None

    for round_num in range(1, _MAX_ROUNDS + 1):
        try:
            screen = identify_screen(win, verbose=True)
        except Exception as e:
            screen = "unknown"
            print(f"⚠️ identify_screen error: {e}")

        print(f"🔁 Reset_to_welcome round {round_num}/{_MAX_ROUNDS}: identified screen = '{screen}'")
        _print_dump(f"round {round_num} ({screen})", win)

        if screen == "welcome_screen":
            logger.log("✅ Reset_to_welcome: SCO confirmed at Welcome screen.", status="pass")
            print("✅ RESET: SUCCESS — SCO at Welcome screen.")
            logger.save()
            return True

        # Priority 0: the "Assistance Needed / Cancel Purchase" store-approval
        # popup is NOT in _ALL_RECOVERY_AIDS (its Yes/No control is a Text
        # element behind a Store Log In gate, not a simple button click) and
        # the generic recovery loop below will spin forever on it otherwise.
        # IMPORTANT: we answer 'Yes' (approve=True) here. Declining it — which
        # is correct mid-payment — simply resumes the transaction and drops
        # the SCO back on the tender screen, which is the exact opposite of
        # what a reset wants and caused an endless
        # redemption_prompt <-> assistance_needed oscillation.
        if screen == "assistance_needed":
            if assistance_attempts >= _MAX_ASSISTANCE_ATTEMPTS:
                print(
                    f"⚠️ Reset_to_welcome: 'assistance_needed' still present after "
                    f"{assistance_attempts} attempts — giving up on soft reset."
                )
                break
            assistance_attempts += 1
            if _handle_cancel_purchase_assistance(win, approve=True):
                stagnant_rounds = 0
                last_screen = screen
                time.sleep(_ROUND_SLEEP)
                continue

            # Other "Assistance Needed" variants (confirmed live: 'Delayed
            # Interventions') carry no Yes/No — every control on the screen is
            # disabled EXCEPT 'StoreLogin'. The only way past the hold is to
            # authenticate through it, so the generic click loop below can
            # never make progress on its own.
            if store_login_authenticate(win):
                print("✅ Reset_to_welcome: cleared assistance hold via Store Log In.")
                stagnant_rounds = 0
                last_screen = screen
                time.sleep(_ROUND_SLEEP)
                continue

        clicked_any = False
        for aid in _ALL_RECOVERY_AIDS:
            if _try_click(win, aid):
                clicked_any = True
                time.sleep(_ROUND_SLEEP)
                break  # re-dump/re-identify after every single click

        if clicked_any:
            stagnant_rounds = 0
        else:
            # Nothing recognisable to click this round — just wait a beat,
            # the screen may still be transitioning (e.g. EFT finalising).
            # But if the SAME screen keeps coming back with nothing we can
            # act on, stop early and let the caller escalate to a hard reset
            # rather than idling for the whole round budget.
            stagnant_rounds = stagnant_rounds + 1 if screen == last_screen else 1
            if stagnant_rounds >= _MAX_STAGNANT_ROUNDS:
                print(
                    f"⚠️ Reset_to_welcome: no actionable control on '{screen}' for "
                    f"{stagnant_rounds} consecutive rounds — giving up on soft reset."
                )
                last_screen = screen
                break
            time.sleep(_ROUND_SLEEP)

        last_screen = screen

    # Exhausted all rounds without reaching Welcome — final diagnostic dump.
    print("❌ RESET: FAILED — could not confirm Welcome screen within budget.")
    _print_dump("FINAL (reset failed)", win)
    logger.log("❌ Reset_to_welcome: failed to reach Welcome screen within budget.", status="fail")
    logger.take_screenshot("Reset_to_welcome_Failed")
    logger.save()
    return False


if __name__ == "__main__":
    reset_to_welcome()
    # Always exit 0: this is a recovery utility, not a test case — the batch
    # runner must proceed to the next TC regardless of reset outcome. The
    # PASS/FAIL is visible in the printed "RESET:" marker and the HTML log.
    sys.exit(0)
