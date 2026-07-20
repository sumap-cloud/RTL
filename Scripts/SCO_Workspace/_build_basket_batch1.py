import sys, time
sys.path.insert(0, '.')
from Components.Login_POS import login_pos
from Components.Add_item import add_item
from Components.Total_amount_details import get_total_amount_salemode

CARD_CODE = "9353180804441"

# Scan 1x of each of the 4 working Instant-Win eligible EANs first.
EAN_BATCH_1 = "9300677010670;9300677011523;9300677010663;9357349999405"

if not login_pos():
    raise SystemExit("login_pos failed")

add_item(EAN_BATCH_1, CARD_CODE)
total = get_total_amount_salemode()
print(f"Basket total after batch 1 (1x each of 4 eligible EANs): {total}")
