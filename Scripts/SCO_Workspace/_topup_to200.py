"""
Top-up basket from $102 → ~$206
  4× Clvr Honey 2.5kg (9300677011523 @ $23.00) = $92
  2× Arn Tim Tam 200g (9310072000282 @  $6.00) = $12
  ─────────────────────────────────────────────
  Total added: $104  →  new basket: $206
"""
import sys
sys.path.insert(0, '.')

from Components.Add_item import add_item
from Components.Total_amount_details import get_total_amount_salemode

CARD_CODE = "9353180804441"

# 4× Clvr Honey then 2× Tim Tams
EAN_LIST = ";".join([
    "9300677011523",
    "9300677011523",
    "9300677011523",
    "9300677011523",
    "9310072000282",
    "9310072000282",
])

print("▶ Adding 4× Clvr Honey + 2× Tim Tams to basket…")
add_item(EAN_LIST, CARD_CODE)

total = get_total_amount_salemode()
print(f"\n🛒 Basket total after top-up: {total}")
