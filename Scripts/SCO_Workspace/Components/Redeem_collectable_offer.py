import re
import sys
import time
from pathlib import Path

from pywinauto import Application, timings

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components import global_instance
from Components.report import logger



def _resolve_button(popup, btn_title):
    """Return the popup button matching `btn_title` (defaults to 'No' if empty)."""
    title = (btn_title or "").strip() or "No"
    return (popup.child_window(title_re=f".*{title}.*", control_type="Text"), title)


def _read_popup_message(popup):
    """Read the popup message from the 'Instructions' Text control."""
    try:
        txt = popup.child_window(auto_id="Instructions",
                                 control_type="Text").window_text()
        return (txt or "").strip()
    except Exception as ex:
        logger.log(f"⚠️ Could not read popup 'Instructions' text: {ex}", status="warn")
        print(f"⚠️ Could not read popup 'Instructions' text: {ex}")
        return ""


def redeem_collectable_offer(offer_type="Collectable", collectable_offer_list=None):
    """
    Redeem one or more collectable offers in the SCO UI.

    - Validates input offer list (semicolon-separated supported).
    - For each offer, waits for the SCO `PopupFrame` popup, matches the message,
      and clicks the correct button (RedeemButton / SkipCollectableOfferPrompt).
    - Logs all failures.
    - offer_type: 'Collectable' or 'Instant Win' (used only in logs).
    """

    app = global_instance.app
    win = global_instance.win

    try:
        # --- No offer supplied: dismiss popup with 'Save for later' if present ---
        if not collectable_offer_list:
            try:
                win.set_focus()
                popup = win.child_window(auto_id="PopupFrame", control_type="Pane")
                if popup.exists(timeout=3):
                    popup.child_window(auto_id="SkipCollectableOfferPrompt",
                                       control_type="Button").click_input()
                    print(f"⚠️ No {offer_type} offer specified. Clicked "
                          f"'Save this discount for later'.")
                    global_instance.reward_redeem_status = True
                else:
                    print(f"⚠️ No {offer_type} offer specified and no popup present. "
                          f"Skipping offer redemption.")
            except Exception as e:
                print(f"❌ Error while dismissing empty {offer_type} offer popup: {e}")
            return True

        # --- Parse offer list (semicolon-separated or single string) ---
        raw = str(collectable_offer_list)
        offers = [o for o in (raw.split(';') if ';' in raw else [raw]) if o.strip()]
        if not offers:
            logger.log(f"❌ {offer_type} offer is empty after split.", status="fail")
            print(f"❌ {offer_type} offer is empty after split.")
            logger.take_screenshot(f"{offer_type}_Offer_Empty_After_Split")
            return False

        # logger.log(f"✅ {offer_type} offer(s) to redeem: {offers}", status="pass")

        # Focus once; subsequent popups inherit the same window focus.
        try:
            win.set_focus()
        except Exception:
            pass

        # --- Main offer redemption loop ---
        for offer in offers:
            # Parse offer into message and button title -> "msg_btn"
            if '_' in offer:
                offer_msg, offer_btn_title = offer.split('_', 1)
            else:
                offer_msg = offer
                offer_btn_title = "No"
            offer_msg = offer_msg.strip()
            offer_btn_title = offer_btn_title.strip() or "No"

            if not offer_msg:
                logger.log(f"❌ {offer_type} offer message is empty.", status="fail")
                print(f"❌ {offer_type} offer message is empty.")
                logger.take_screenshot(
                    f"{offer_type}_Offer_Message_Empty"
                )
                continue

            # --- Connect to SCO popup ---
            try:
                popup = win.child_window(auto_id="PopupFrame", control_type="Pane")
                if not popup.exists(timeout=3):
                    logger.log(f"❌ {offer_type} offer redeem popup not found.", status="fail")
                    print(f"❌ {offer_type} offer redeem popup not found.")
                    logger.take_screenshot(
                        f"{offer_type}_Redeem_Popup_Not_Found"
                    )
                    return False
                logger.log(f"✅ {offer_type} offer redeem popup detected.", status="pass")
                print(f"✅ {offer_type} offer redeem popup detected.")
            except Exception as e:
                logger.log(f"❌ {offer_type} offer redeem popup not available: {e}", status="fail")
                print(f"❌ {offer_type} offer redeem popup not available: {e}")
                logger.take_screenshot(
                    f"{offer_type}_Redeem_Popup_Not_Available"
                )
                return False

            # --- Read popup message ---
            msg = _read_popup_message(popup)
            if not msg:
                logger.log(
                    f"❌ Could not read any Text content from {offer_type} popup.",
                    status="fail"
                )
                print(f"❌ Could not read any Text content from {offer_type} popup.")
                logger.take_screenshot(
                    f"{offer_type}_Popup_Text_Not_Readable"
                )
                print(f"Listing descendants for debug:")
                try:
                    for ctrl in popup.descendants():
                        print(f"  type: {ctrl.element_info.control_type}, "
                              f"auto_id: '{getattr(ctrl.element_info, 'automation_id', '')}', "
                              f"text: '{ctrl.window_text()}'")
                except Exception as ex:
                    print(f"  (failed to enumerate descendants: {ex})")
                continue

            # --- Resolve the button to click ---
            collectable_btn, btn_label = _resolve_button(popup, offer_btn_title)
            if not collectable_btn.exists(timeout=1):
                logger.log(
                    f"❌ {offer_type} offer button '{offer_btn_title}' not found on popup.",
                    status="fail"
                )
                print(f"❌ {offer_type} offer button '{offer_btn_title}' not found on popup.")
                logger.take_screenshot(
                    f"{offer_type}_Button_{offer_btn_title}_Not_Found"
                )
                continue

            # --- Compare popup message to expected offer ---
            clean_msg = " ".join(msg.replace('\n', ' ').split())
            clean_offer = " ".join(offer_msg.replace('\n', ' ').split())
            print(f"{offer_type} offer popup message: '{clean_msg}' "
                  f"and expected: '{clean_offer}'")
            try:
                # Treat the expected offer as literal text with `.*` wildcards.
                # Everything else (including '?', '.', '(', ')', '+') is escaped
                # so it is matched literally against the popup text.
                pattern = ".*".join(
                    re.escape(part) for part in clean_offer.split(".*")
                )
                matched = re.search(pattern, clean_msg, flags=re.IGNORECASE)
            except re.error:
                matched = clean_offer.lower() in clean_msg.lower()

            if matched:
                collectable_btn.click_input()
                logger.log(
                    f"✅ Handled {offer_type} offer '{clean_msg}' with action '{btn_label}'.",
                    status="pass"
                )
                print(f"✅ Handled {offer_type} offer '{clean_msg}' with action '{btn_label}'.")
                global_instance.reward_redeem_status = True
            else:
                logger.log(
                    f"❌ {offer_type} offer message did not match expected '{offer_msg}'.",
                    status="fail"
                )
                print(f"❌ {offer_type} offer message did not match expected '{offer_msg}'.")
                logger.take_screenshot(
                    f"{offer_type}_Offer_Message_Mismatch"
                )
                continue

        return True

    except Exception as e:
        logger.log(f"❌ Error occurred while handling {offer_type.lower()} offer: {e}", status="fail")
        print(f"❌ Error occurred while handling {offer_type.lower()} offer: {e}")
        logger.take_screenshot(f"{offer_type}_Offer_Handler_Exception")
        return True



