import sys
import time
import ctypes
import re
from pathlib import Path

import win32gui
from pywinauto.timings import Timings
from pywinauto import Application, timings

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components import global_instance
from Components.Ensure_EFTSimulator_closed import ensure_EFTSimulator_closed
from Components.Ensure_services_stopped import ensure_services_stopped, SERVICES_TO_STOP





def get_promotion_details(promomtion_list):

    app = global_instance.app
    win = global_instance.win

    try:
        count_element = win.child_window(auto_id="ReceiptItemCount", control_type="Text")
        count_text = count_element.window_text()
        match = re.search(r'\d+', count_text)
        expected_count = int(match.group()) if match else 0
        print(f"📦 Expected Item Count: {expected_count}")
    except Exception:
        expected_count = -1

    cart_list = win.child_window(auto_id="CartReceipt", control_type="List")

    item_descriptions = []
    item_prices = []
    promotion_descriptions = []
    promotion_prices = []

    try:
        receipt_items = cart_list.children(control_type="ListItem")
        print(f"Total ListItems found: {len(receipt_items)}")

        for item in receipt_items:
            desc_text = ""
            price_text = ""

            # FIX 1: Use .children() to prevent scanning outside the row
            for child in item.children():
                try:
                    current_id = child.element_info.automation_id

                    # FIX 2: Add 'not desc_text' to lock in the first match
                    if current_id == "ItemDescription" and not desc_text:
                        desc_text = child.window_text()
                    elif current_id == "ItemPrice" and not price_text:
                        price_text = child.window_text()
                except Exception:
                    continue

            if desc_text and price_text:
                if price_text.startswith("-"):
                    print(f"🎁 Promotion found on screen: {desc_text} ({price_text})")
                    promotion_descriptions.append(desc_text)
                    promotion_prices.append(price_text)
                    continue

                item_descriptions.append(desc_text)
                item_prices.append(price_text)

    except Exception as e:
        print(f"⚠️ Error reading basket items: {e}")

    if len(item_descriptions) == expected_count:
        print("✅ Extracted item count matches the ReceiptItemCount!")
    else:
        print(f"❌ Warning: Extracted {len(item_descriptions)} items, but expected {expected_count}.")

    print(f"{len(item_descriptions)} items in the basket: and their prices: {item_prices}")

    # -------------------------------------------------------------------------
    # Verify the promotions passed in `promomtion_list` against on-screen ones
    # and collect their prices in the same order as the input list.
    # `promomtion_list` is expected as a semicolon-separated string,
    # e.g. "Market Day 10% off; Buy 1 Get 1; Loyalty Discount".
    # A list/tuple is also accepted for backwards compatibility.
    # -------------------------------------------------------------------------
    if promomtion_list is None:
        promomtion_list = []
    elif isinstance(promomtion_list, str):
        promomtion_list = [p.strip() for p in promomtion_list.split(";") if p.strip()]
    elif isinstance(promomtion_list, (list, tuple)):
        promomtion_list = [str(p).strip() for p in promomtion_list if str(p).strip()]
    else:
        promomtion_list = [str(promomtion_list).strip()]

    print(f"🔎 Expected promotions ({len(promomtion_list)}): {promomtion_list}")
    print(f"🧾 Promotions on screen ({len(promotion_descriptions)}): {promotion_descriptions}")

    matched_promotion_prices = []
    missing_promotions = []
    # Track which on-screen promotion rows have already been consumed so that
    # duplicate promotion names get matched to distinct rows.
    used_indices = set()

    for expected_promo in promomtion_list:
        expected_norm = str(expected_promo).strip().lower()
        found_index = -1
        for idx, screen_promo in enumerate(promotion_descriptions):
            if idx in used_indices:
                continue
            if expected_norm in screen_promo.strip().lower():
                found_index = idx
                break

        if found_index >= 0:
            used_indices.add(found_index)
            matched_price = promotion_prices[found_index]
            matched_promotion_prices.append(matched_price)
            print(f"✅ Promotion verified: '{expected_promo}' -> "
                  f"'{promotion_descriptions[found_index]}' ({matched_price})")
        else:
            matched_promotion_prices.append(None)
            missing_promotions.append(expected_promo)
            print(f"❌ Promotion NOT found on screen: '{expected_promo}'")

    if promomtion_list and not missing_promotions:
        print("✅ All expected promotions are present on screen.")
    elif missing_promotions:
        print(f"❌ Missing promotions: {missing_promotions}")

    # Persist for downstream steps / reporting
    global_instance.promotion_description_list = promotion_descriptions
    global_instance.promotion_price_list = promotion_prices

    if global_instance.is_loyaltycard_added:
        points_collected = get_points_collected()
        global_instance.loyalty_points = points_collected
        print(f"🎯 Loyalty points collected: {points_collected}")

    return (item_descriptions, item_prices,
            promotion_descriptions, promotion_prices,
            matched_promotion_prices, missing_promotions)

def get_points_collected():

    app = global_instance.app
    win = global_instance.win

    try:
        points_element = win.child_window(auto_id="WoWRewardPoints", control_type="Text")
        points_text = points_element.window_text()
        match = re.search(r'\d+', points_text)
        points_collected = int(match.group()) if match else 0
        print(f"🎯 Points Collected: {points_collected}")
        # return points_collected
    except Exception as e:
        print(f"⚠️ Error reading points collected: {e}")
        points_collected = None

    return points_collected


if __name__ == "__main__":
    # When this file is run directly, global_instance.app / .win are not set
    # because no other component has connected to the SCO window yet.
    # Connect here so the function can read the on-screen cart.
    if global_instance.app is None or global_instance.win is None:
        try:
            app = Application(backend="uia").connect(title_re=".*NCR NEXTGENUI.*")
            win = app.window(title_re=".*NCR NEXTGENUI.*")
            global_instance.app = app
            global_instance.win = win
            try:
                win.set_focus()
            except Exception:
                pass
            print("🔌 Connected to NCR NEXTGENUI window.")
        except Exception as e:
            print(f"❌ Could not connect to NCR NEXTGENUI window: {e}")
            sys.exit(1)

    # Example usage: semicolon-separated promotion names
    promotions_to_check = "WOW 10% OFFER"
    get_promotion_details(promotions_to_check)
    print("Promotion details extraction completed.")
    get_points_collected()
    print("Points collected extraction completed.")


