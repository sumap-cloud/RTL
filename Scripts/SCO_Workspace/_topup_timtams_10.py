import sys
sys.path.insert(0, '.')
from Components.Login_POS import login_pos
from Components.Add_item import add_item
from Components.Total_amount_details import get_total_amount_salemode

CARD_CODE = "9353180804441"
EAN_LIST = ";".join(["9310072000282"] * 10)

if not login_pos():
    raise SystemExit("login_pos failed")

add_item(EAN_LIST, CARD_CODE)
total = get_total_amount_salemode()
print(f"Basket total after adding 10x Tim Tams: {total}")
