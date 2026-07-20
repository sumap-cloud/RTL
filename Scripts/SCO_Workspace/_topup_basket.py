import sys
sys.path.insert(0, '.')
from Components.Login_POS import login_pos
from Components.Add_item import add_item
from Components.Total_amount_details import get_total_amount_salemode

# Basket already has 1x each of these 4 EANs. Add 5 more of each -> 6x each.
EAN_LIST = ";".join(
    ["9300677010670"] * 5 + ["9300677011523"] * 5 + ["9300677010663"] * 5 + ["9357349999405"] * 5
)
CARD_CODE = "9353180804441"

if not login_pos():
    raise SystemExit("login_pos failed")

add_item(EAN_LIST, CARD_CODE)
total = get_total_amount_salemode()
print(f"Basket total after topping up to 6x each: {total}")
