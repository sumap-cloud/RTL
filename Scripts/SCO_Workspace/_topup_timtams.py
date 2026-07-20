import sys
sys.path.insert(0, '.')
from Components.Login_POS import login_pos
from Components.Add_item import add_item
from Components.Total_amount_details import get_total_amount_salemode

# Basket currently has 1x each of the 4 Instant-Win eligible EANs ($42 total).
# Top up with standard Tim Tam EAN (non-flagged, used across other working TCs)
# to cross the $200 basket threshold required to trigger Instant Win.
EAN_LIST = ";".join(["9310072000282"] * 68)
CARD_CODE = "9353180804441"

if not login_pos():
    raise SystemExit("login_pos failed")

add_item(EAN_LIST, CARD_CODE)
total = get_total_amount_salemode()
print(f"Basket total after adding 68x Tim Tams: {total}")
