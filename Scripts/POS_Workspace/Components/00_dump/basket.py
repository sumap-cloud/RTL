import time
from pywinauto import Application

def collect_basket_items(basket):
    """Collect all basket items from the current page."""
    items = basket.descendants(control_type="ListItem")
    if not items:
        items = basket.children()

    page_items = []
    total = 0.0
    promo_total = 0.0
    promotion_found = False

    for idx, item in enumerate(items, 1):
        name = item.window_text()
        #child_texts = [child.window_text() for child in item.children() if child.window_text()]
        price = None
        quantity = None
        children = item.children()

        for child in children:
            txt = child.window_text()
            # Try to find price
            if any(c in txt for c in ["$", ".", ","]):
                try:
                    price_val = float(txt.replace("$", "").replace(",", "").strip())
                    price = price_val
                except Exception:
                    pass
            # Try to find quantity
            if txt.isdigit():
                quantity = int(txt)

        print(f"  {idx}. Name: {name}, Quantity: {quantity if quantity else 'N/A'}, Amount: {price if price else 'N/A'}")

        if price is not None:
            total += price
            if price < 0 or (name and ("promotion" in name.lower() or "bonus" in name.lower() or "ff" in name.lower())):
                promo_total += price
                promotion_found = True

        # Promotion detection
        if "promotion" in name.lower() or "bonus" in name.lower() or "ff" in name.lower():
            promotion_found = True
            print(f"🎉 Promotion found in basket item: {name}")
        else:
            # Only count actual articles (exclude promotions)
            page_items.append((name, quantity, price))

    return page_items, total, promo_total, promotion_found


def get_basket_info():
    try:
        app = Application(backend="uia").connect(title_re=".*R10PosClient.*")
        win = app.window(title_re=".*R10PosClient.*")
        win.set_focus()
        print("✅ POS window found and focused.")
    except Exception as e:
        print(f"❌ Could not connect or focus POS window: {e}")
        return

    # Locate basket control
    basket_controls = win.descendants(control_type="List")
    if not basket_controls:
        basket_controls = win.descendants(control_type="ListBox")
    if not basket_controls:
        basket_controls = win.descendants(control_type="ListView")

    if not basket_controls:
        print("❌ Could not find basket/list control on left side.")
        return

    basket = basket_controls[0]

    # Locate navigation buttons
    try:
        up_btn = win.child_window(auto_id="rptBtnPgUp", control_type="Button")
        down_btn = win.child_window(auto_id="rptBtnPgDown", control_type="Button")
    except Exception:
        up_btn = None
        down_btn = None

    all_items = []
    grand_total = 0.0
    grand_promo_total = 0.0
    promo_found_any = False

    # Step 1: Scroll up to the top if possible
    if up_btn and up_btn.is_enabled():
        while up_btn.is_enabled():
            up_btn.click_input()
            time.sleep(0.3)

    # Step 2: Iterate through all pages
    while True:
        items_data, total, promo_total, promo_found = collect_basket_items(basket)
        print(f"Found {len(items_data)} article(s) in basket (this page).")

        all_items.extend(items_data)
        grand_total += total
        grand_promo_total += promo_total
        promo_found_any = promo_found_any or promo_found

        if down_btn and down_btn.is_enabled():
            down_btn.click_input()
            time.sleep(0.3)
        else:
            break

    # Final summary
    print(f"\n🛒 TOTAL Articles in basket (all pages): {len(all_items)}")
    print(f"💰 TOTAL Basket amount across all pages: {grand_total:.2f}")
    if grand_promo_total < 0:
        print(f"🎯 Promotion/discount applied: {grand_promo_total:.2f}")
    else:
        print("ℹ️ No promotion/discount applied.")
    print(f"✅ Final total after promotion: {grand_total:.2f}")

    if promo_found_any:
        print("✅ Basket contains promotion items.")
    else:
        print("ℹ️ Basket contains items without promotions.")


if __name__ == "__main__":
    get_basket_info()