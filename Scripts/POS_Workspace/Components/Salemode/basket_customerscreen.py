import time
from pywinauto import Application

def get_basket_and_balance_due():
    try:
        app_path = r"C:\Retalix\StoreServices\POSClient\Retalix.Client.POS.Shell.exe"

# Connect to the application using its stable path
# This will work every time, regardless of the process ID
        app = Application(backend="uia").connect(path=app_path)

# The rest of your code works perfectly with this change
        win = app.window(auto_id="GraphicCustomerDisplayID")
        win.set_focus()
        print("✅ POS window found and focused.")
    except Exception as e:
        print(f"❌ Could not connect or focus POS window: {e}")
        return

    # Find basket control (left side)
    basket_controls = win.descendants(control_type="List")
    if not basket_controls:
        basket_controls = win.descendants(control_type="ListBox")
    if not basket_controls:
        basket_controls = win.descendants(control_type="ListView")

    if basket_controls:
        basket = basket_controls[0]
        items = basket.descendants(control_type="ListItem")
        if not items:
            items = basket.children()
        print(f"Found {len(items)} item(s) in basket:")
        total = 0.0
        promo_total = 0.0
        for idx, item in enumerate(items, 1):
            name = item.window_text()
            price = None
            quantity = None
            children = item.children()
            for child in children:
                txt = child.window_text()
                # Try to find price (float or currency)
                if any(c in txt for c in ["$", ".", ","]):
                    try:
                        price_val = float(txt.replace("$","").replace(",","").strip())
                        price = price_val
                    except Exception:
                        pass
                # Try to find quantity (integer)
                if txt.isdigit():
                    quantity = int(txt)
            print(f"  {idx}. Name: {name}, Quantity: {quantity if quantity else 'N/A'}, Amount: {price if price else 'N/A'}")
            if price is not None:
                total += price
                # Consider promotion if item name or price is negative
                if price < 0 or (name and "promotion" in name.lower() or "bonus" in name.lower()):
                    promo_total += price
        print(f"\nTotal basket amount: {total:.2f}")
        if promo_total < 0:
            print(f"Promotion/discount applied: {promo_total:.2f}")
            print(f"Final total after promotion: {total:.2f}")
        else:
            print("No promotion/discount applied.")
    else:
        print("❌ Could not find basket/list control on left side.")

    # ...existing code...

if __name__ == "__main__":
    get_basket_and_balance_due()
