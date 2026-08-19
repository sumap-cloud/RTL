"""
TC_028 — Verify Discount Basket Campaign (Market Day Offer)

STATUS: NOT IMPLEMENTED (placeholder).

This scenario is already covered by the implemented script
    TC_08A_VerifyDiscountBasketCampaignMarketDayOffer.py
in the same folder. This file was left as an empty 0-byte placeholder, which
made the batch runner report it as a silent PASS (an empty Python file exits
with code 0). It now exits with a non-zero code so it can never be mistaken
for a passing test.

To implement it, copy the structure of TC_08A_*.py, give it its own TC_ID,
and add matching rows to Scripts/SCO_Workspace/Data/RegressionSale.csv.
"""

import sys

TC_ID = "TC_028_VerifyDiscountBasketCampaignMarketDayOffer"
BANNER = "BigW"

if __name__ == "__main__":
    print("=" * 70)
    print(f"  {TC_ID}")
    print("  SKIPPED — placeholder, not implemented.")
    print("  Covered by TC_08A_VerifyDiscountBasketCampaignMarketDayOffer.py")
    print("=" * 70)
    sys.exit(2)
