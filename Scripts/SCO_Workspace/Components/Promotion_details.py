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
from Components.report import logger


def get_promotion_details(promomtion_list):

    app = global_instance.app
    win = global_instance.win

    try:
        count_element = win.child_window(auto_id="ReceiptItemCount", control_type="Text")
        count_text = count_element.window_text()
        match = re.search(r'\d+', count_text)
        expected_count = int(match.group()) if match else 0
        logger.log(f"✅ Receipt reports expected item count: {expected_count}.", status="pass")
        print(f"✅ Receipt reports expected item count: {expected_count}.")
    except Exception:
        expected_count = -1
        logger.log("❌ Could not read ReceiptItemCount from POS.", status="fail")
        print("❌ Could not read ReceiptItemCount from POS.")
        logger.take_screenshot("ReceiptItemCount_Not_Readable")

    cart_list = win.child_window(auto_id="CartReceipt", control_type="List")

    item_descriptions = []
    item_prices = []
    promotion_descriptions = []
    promotion_prices = []

    try:
        receipt_items = cart_list.children(control_type="ListItem")
        # logger.log(f"✅ Total ListItems found: {len(receipt_items)}.", status="pass")

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
                    # logger.log(f"✅ Promotion found on screen: '{desc_text}' ({price_text}).", status="pass")
                    promotion_descriptions.append(desc_text)
                    promotion_prices.append(price_text)
                    continue

                item_descriptions.append(desc_text)
                item_prices.append(price_text)

    except Exception as e:
        logger.log(f"❌ Error reading basket items: {e}", status="fail")
        print(f"❌ Error reading basket items: {e}")
        logger.take_screenshot("Basket_Read_Error")

    if len(item_descriptions) == expected_count:
        logger.log("✅ Extracted item count matches the Cart Item Count!", status="pass")
        print("✅ Extracted item count matches the Cart Item Count!")
    else:
        logger.log(
            f"❌ Warning: Extracted {len(item_descriptions)} items, but expected {expected_count}.",
            status="fail"
        )
        print(f"❌ Warning: Extracted {len(item_descriptions)} items, but expected {expected_count}.")
        logger.take_screenshot("Receipt_Item_Count_Mismatch")

    # logger.log(f"✅ {len(item_descriptions)} items extracted from basket.", status="pass")
    # for article_desc, article_price in zip(item_descriptions, item_prices):
    #     logger.log(
    #         f"✅ Article '{article_desc}' is captured with price: {article_price}.",
    #         status="pass"
    #     )

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

    # logger.log(f"✅ Expected promotions ({len(promomtion_list)}): {promomtion_list}", status="pass")
    # logger.log(f"✅ Promotions on screen ({len(promotion_descriptions)}): {promotion_descriptions}", status="pass")

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
            logger.log(
                f"✅ Promotion '{expected_promo}' is displayed on the POS with price: {matched_price}.",
                status="pass"
            )
            print(f"✅ Promotion '{expected_promo}' is displayed on the POS with price: {matched_price}.")
        else:
            matched_promotion_prices.append(None)
            missing_promotions.append(expected_promo)
            logger.log("❌ Promotion price is not displayed on the POS.", status="fail")
            print("❌ Promotion price is not displayed on the POS.")
            logger.take_screenshot(
                f"Promotion_{expected_promo}_Price_Not_Found"
            )

    if promomtion_list and not missing_promotions:
        logger.log("✅ All expected promotions are present on screen.", status="pass")
        print("✅ All expected promotions are present on screen.")
    elif missing_promotions:
        logger.log(f"❌ Missing promotions: {missing_promotions}", status="fail")
        print(f"❌ Missing promotions: {missing_promotions}")
        logger.take_screenshot("Missing_Promotions")

    # Persist for downstream steps / reporting
    global_instance.promotion_description_list = promotion_descriptions
    global_instance.promotion_price_list = promotion_prices

    if global_instance.is_loyaltycard_added:
        points_collected = get_points_collected()
        global_instance.loyalty_points = points_collected
        if points_collected is not None:
            logger.log(f"✅ Loyalty points collected: {points_collected}.", status="pass")
            print(f"✅ Loyalty points collected: {points_collected}.")
        else:
            logger.log("❌ Loyalty points were not collected/read.", status="fail")
            print("❌ Loyalty points were not collected/read.")
            logger.take_screenshot("Loyalty_Points_Not_Collected")

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
        # logger.log(f"✅ Points Collected: {points_collected}", status="pass")
        # return points_collected
    except Exception as e:
        # logger.log(f"❌ Error reading points collected: {e}", status="fail")
        # logger.take_screenshot("Points_Collected_Read_Error")
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
            logger.log("✅ Connected to NCR NEXTGENUI window.", status="pass")
            print("✅ Connected to NCR NEXTGENUI window.")
        except Exception as e:
            logger.log(f"❌ Could not connect to NCR NEXTGENUI window: {e}", status="fail")
            print(f"❌ Could not connect to NCR NEXTGENUI window: {e}")
            logger.take_screenshot("NCR_Window_Connection_Failed")
            sys.exit(1)

    # Example usage: semicolon-separated promotion names
    promotions_to_check = "WOW 10% OFFER"
    get_promotion_details(promotions_to_check)
    logger.log("✅ Promotion details extraction completed.", status="pass")
    print("✅ Promotion details extraction completed.")
    get_points_collected()
    logger.log("✅ Points collected extraction completed.", status="pass")
    print("✅ Points collected extraction completed.")


