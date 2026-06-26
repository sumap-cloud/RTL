"""
Redeem_instant_win.py
---------------------
Handles the 3 Instant Win popup variants observed in NCR SCO:

  A. APPROVAL prompt   — popup contains an image + "Use now" + "Save for later".
                          Triggered when basket value >= offer threshold (e.g. $25).
  B. NOTIFICATION prompt — popup with image + single "OK" button.
                          Triggered when basket value < offer threshold OR for
                          points-reward style instant wins.
  C. SAVED prompt      — popup with multiple denomination buttons ($10, $25, $50,
                          $100). After each click the prompt refreshes with the
                          remaining denominations. Clicking "Save for later"
                          dismisses the prompt.

Because we don't (yet) have a confirmed live UIA dump for these popups, the
component tries multiple known SCO popup patterns in order:
  1. PopupFrame    (Pane)        + child RedeemButton / SkipCollectableOfferPrompt
                                  — same pattern as collectable offers.
  2. ContainerButtonList (List)  + child ListItems containing 'Usenow' buttons
                                  — same pattern as choice offers.
  3. Title-based fallback over any visible Button matching "Use now"/"Save for later".

If none of the above is found within `timeout`, returns False so the caller can
decide whether the popup was simply not triggered (legitimate for low basket
values) or whether the workflow has drifted.

Validation: per KT transcript, the IMAGE must be present. We do not byte-compare
images; we just take a screenshot of the popup region for the report so the user
can visually verify.
"""
import sys
import time
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components import global_instance
from Components.report import logger


# --------------------------------------------------------------------------- #
# Public entry points
# --------------------------------------------------------------------------- #
def handle_instant_win_approval(action="use_now", timeout=10):
    """Handle the IW APPROVAL popup. action ∈ {'use_now', 'save_for_later'}."""
    win = global_instance.win
    if win is None:
        logger.log("❌ Instant-Win approval: SCO window not initialised.", status="fail")
        return False

    end = time.time() + timeout
    popup = None
    while time.time() < end:
        popup = _find_popup(win)
        if popup is not None:
            break
        time.sleep(0.3)
    if popup is None:
        logger.log("⚠️ Instant-Win approval popup not detected.", status="info")
        return False

    logger.take_screenshot("InstantWin_Approval_Popup")

    if action == "save_for_later":
        return _click_first_match(
            popup, win,
            auto_ids=("SkipCollectableOfferPrompt", "SaveForLaterButton",
                      "SaveForLater", "SkipButton"),
            titles=("Save for later", "Save For Later", "Save"),
            success_log="✅ Instant-Win approval: 'Save for later' clicked.",
            fail_log="❌ Instant-Win approval: 'Save for later' not found.")
    # default: use_now
    return _click_first_match(
        popup, win,
        auto_ids=("RedeemButton", "UseNow", "UseNowButton", "Usenow"),
        titles=("Use now", "Use Now"),
        success_log="✅ Instant-Win approval: 'Use now' clicked.",
        fail_log="❌ Instant-Win approval: 'Use now' not found.")


def handle_instant_win_notification(timeout=10):
    """Acknowledge the IW NOTIFICATION popup (single OK button)."""
    win = global_instance.win
    if win is None:
        logger.log("❌ Instant-Win notification: SCO window not initialised.", status="fail")
        return False

    end = time.time() + timeout
    popup = None
    while time.time() < end:
        popup = _find_popup(win)
        if popup is not None:
            break
        time.sleep(0.3)
    if popup is None:
        logger.log("⚠️ Instant-Win notification popup not detected.", status="info")
        return False

    logger.take_screenshot("InstantWin_Notification_Popup")
    return _click_first_match(
        popup, win,
        auto_ids=("ASAOKButton", "OK_Button", "GenericOKButton", "OKButton",
                  "Continue", "ContinueButton"),
        titles=("OK", "Ok", "Continue"),
        success_log="✅ Instant-Win notification acknowledged.",
        fail_log="❌ Instant-Win notification: OK button not found.")


def handle_instant_win_saved(action="save_for_later", denomination=None,
                             timeout=10, max_iterations=4):
    """Handle the IW SAVED-promotions popup with multiple denomination buttons.

    action='use_now'  + denomination=10/25/50/100 — clicks the matching button,
                       then waits for refresh and clicks 'Save for later' on the
                       refreshed prompt to exit.
    action='save_for_later' — clicks Save for later immediately.

    Returns True if the popup was handled (or already absent), False on error.
    """
    win = global_instance.win
    if win is None:
        logger.log("❌ Instant-Win saved: SCO window not initialised.", status="fail")
        return False

    if action == "save_for_later":
        popup = _wait_for_popup(win, timeout)
        if popup is None:
            logger.log("⚠️ Instant-Win saved popup not detected.", status="info")
            return False
        logger.take_screenshot("InstantWin_Saved_Popup")
        return _click_first_match(
            popup, win,
            auto_ids=("SkipCollectableOfferPrompt", "SaveForLater"),
            titles=("Save for later", "Save For Later", "Save"),
            success_log="✅ Instant-Win saved: 'Save for later' clicked.",
            fail_log="❌ Instant-Win saved: 'Save for later' not found.")

    # action == "use_now"
    if denomination is None:
        logger.log("❌ Instant-Win saved use_now: denomination required.", status="fail")
        return False
    denom = str(denomination).strip().lstrip("$").split()[0]

    for it in range(max_iterations):
        popup = _wait_for_popup(win, timeout if it == 0 else 5)
        if popup is None:
            logger.log(
                f"ℹ️ Instant-Win saved: popup gone after {it} click(s) — assuming done.",
                status="info")
            return True
        logger.take_screenshot(f"InstantWin_Saved_Popup_iter{it+1}")

        # Try to find a button matching the chosen denomination.
        clicked = _click_denomination(popup, win, denom)
        if clicked:
            time.sleep(2)  # let the prompt refresh per KT description
            # After the first click, switch to save-for-later to exit per scenarios.
            denom = None  # only one denomination per scenario
            popup2 = _wait_for_popup(win, 5)
            if popup2 is None:
                logger.log("✅ Instant-Win saved: clicked denomination; popup closed.",
                           status="pass")
                return True
            ok = _click_first_match(
                popup2, win,
                auto_ids=("SkipCollectableOfferPrompt", "SaveForLater"),
                titles=("Save for later", "Save For Later", "Save"),
                success_log="✅ Instant-Win saved: refreshed popup dismissed via 'Save for later'.",
                fail_log="⚠️ Instant-Win saved: could not find 'Save for later' on refresh.")
            return ok
        # if no matching denomination, try save-for-later as a fallback exit
        return _click_first_match(
            popup, win,
            auto_ids=("SkipCollectableOfferPrompt", "SaveForLater"),
            titles=("Save for later", "Save For Later"),
            success_log="✅ Instant-Win saved: denom not present; clicked 'Save for later'.",
            fail_log="❌ Instant-Win saved: neither denom nor 'Save for later' found.")

    logger.log("⚠️ Instant-Win saved: exited after max iterations.", status="info")
    return False


# --------------------------------------------------------------------------- #
# Private helpers
# --------------------------------------------------------------------------- #
def _find_popup(win):
    """Return a popup wrapper if any of the known IW popup containers exists."""
    candidates = [
        ("PopupFrame", "Pane"),
        ("ContainerButtonList", "List"),
        ("PopupTitle", "Text"),
    ]
    for aid, ctype in candidates:
        try:
            ctrl = win.child_window(auto_id=aid, control_type=ctype)
            if ctrl.exists(timeout=0.3):
                return ctrl
        except Exception:
            continue
    return None


def _wait_for_popup(win, timeout):
    end = time.time() + timeout
    while time.time() < end:
        p = _find_popup(win)
        if p is not None:
            return p
        time.sleep(0.3)
    return None


def _click_first_match(popup, win, auto_ids, titles, success_log, fail_log):
    # Try the popup scope first, then fall back to the whole window.
    for scope in (popup, win):
        for aid in auto_ids:
            try:
                btn = scope.child_window(auto_id=aid, control_type="Button")
                if btn.exists(timeout=1.0):
                    btn.click_input()
                    logger.log(success_log + f"  (auto_id={aid})", status="pass")
                    return True
            except Exception:
                continue
        for title in titles:
            for ct in ("Button", "Text"):
                try:
                    btn = scope.child_window(title=title, control_type=ct)
                    if btn.exists(timeout=0.5):
                        btn.click_input()
                        logger.log(success_log + f"  (title='{title}')", status="pass")
                        return True
                except Exception:
                    continue
    logger.log(fail_log, status="fail")
    logger.take_screenshot("InstantWin_Click_Not_Found")
    return False


def _click_denomination(popup, win, denom):
    """Click the button matching the denomination text (e.g. '10', '25', '50')."""
    titles = (f"${denom} off", f"${denom}", f"{denom} off", f"{denom}",
              f"Use now ${denom}", f"Use ${denom}")
    for scope in (popup, win):
        for title in titles:
            for ct in ("Button", "Text"):
                try:
                    btn = scope.child_window(title_re=f".*{title}.*",
                                             control_type=ct)
                    if btn.exists(timeout=0.5):
                        btn.click_input()
                        logger.log(
                            f"✅ Instant-Win saved: clicked denomination ${denom}.",
                            status="pass")
                        return True
                except Exception:
                    continue
    return False
