"""
Step 2a (probe): scan 1x each of the 5 Instant-Win eligible EANs from the
ticket to learn item prices before deciding final basket quantities.
"""
import sys
from pathlib import Path
sys.path.insert(0, '.')

from Components.Login_POS import login_pos
from Components.Add_item import add_item
from Components.Total_amount_details import get_total_amount_salemode

EAN_LIST = "9300677010670;9300677011523;9300677010663;9357349999405;9350763347364"
CARD_CODE = "9353180804441"

if not login_pos():
    raise SystemExit("login_pos failed")

add_item(EAN_LIST, CARD_CODE)
total = get_total_amount_salemode()
print(f"Probe basket total (1x each of 5 EANs): {total}")
