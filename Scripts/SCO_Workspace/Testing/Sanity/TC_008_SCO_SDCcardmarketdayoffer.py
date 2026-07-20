"""
TC_008_SCO_SDCcardmarketdayoffer.py
------------------------------------
Test Case: Validation of different offers — open, targeted, points and
POS sync offers (SDC card with Market Day Insurance offer + basket point
multiplier + team discount).

Scenario:
    Verify the full offer sequence for card 9344779058420:
      1. Scan 5 × EAN 9342937005316 (Campaign 1260707 trigger).
      2. Scan SDC card in sale mode.
      3. Move to tender mode — choice offer screen appears.
      4. Accept "Market Day Insurance 10 percent off" via 'Use now' (Choice Offer).
      5. Verify the discount appears as a promotion line in the basket.
      6. Log 3× basket point multiplier value (WoWRewardPoints).
      7. Log team discount savings (TotalRewardsValue).
      8. Complete the transaction (EFT, Tender2).
      9. Verify EagleEye settlement (wallet open + settle).

Pre-requisite:
    SDC card 9344779058420 with Market Day Insurance offer configured.
    Run setup_TC007_to_TC011_csv_data.py once to write EAN and card to CSV.
"""

import sys
import time
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components.Login_POS import login_pos
from Components.Add_item import add_item
from Components.Scan_loyalty_salemode import scan_loyalty_salemode
from Components.Move_to_tendermode import move_to_tendermode
from Components.Redeem_choice_offer import redeem_choice_offer
from Components.Promotion_details import get_promotion_details
from Components.Complete_transaction import complete_transaction
from Components.Verify_EagleEye_logs import verify_eagleeye_logs
from Components.Read_csv import get_csv_value
from Components.report import logger
from Components import global_instance

TC_ID = "TC_008"
BANNER = "SM"
ITERATION = 1

logger.set_tc_id(TC_ID)

# Campaign 1260707: 5 × EAN 9342937005316 triggers the Market Day Insurance offer.
EAN_FALLBACK = ";".join(["9342937005316"] * 5)


def _get_value(column, fallback):
    try:
        val = get_csv_value("saledata", BANNER, TC_ID, ITERATION, column)
        if val and not val.startswith("Error") and val != "No matching record found." and val != "0000000000000":
            return val
    except Exception:
        pass
    return fallback


EAN_LIST     = _get_value("EAN_Codes", None) or _get_value("Item_EAN", EAN_FALLBACK)
CARD_CODE    = _get_value("Card_number", "9344779058420")
# Substring of the offer card text shown in the Choice Offer screen.
CHOICE_OFFER = _get_value("Choice_offer", "Market Day")

try:
    # ------------------------------------------------------------------
    # Step 1: Login / connect to SCO
    # ------------------------------------------------------------------
    if not login_pos():
        raise RuntimeError("Login_POS failed — aborting test.")

    # ------------------------------------------------------------------
    # Step 2: Scan 5 articles (triggers Campaign 1260707)
    # ------------------------------------------------------------------
    add_item(EAN_LIST, CARD_CODE)

    # ------------------------------------------------------------------
    # Step 3: Scan SDC card in sale mode
    # ------------------------------------------------------------------
    if not scan_loyalty_salemode(CARD_CODE):
        raise RuntimeError("scan_loyalty_salemode failed — aborting test.")

    # ------------------------------------------------------------------
    # Step 4: Move to tender mode.
    # Pass skip_choice_offer=False so the choice offer screen is NOT
    # auto-dismissed — redeem_choice_offer() handles it below.
    # ------------------------------------------------------------------
    if not move_to_tendermode(skip_choice_offer=False):
        raise RuntimeError("move_to_tendermode failed — aborting test.")

    # ------------------------------------------------------------------
    # Step 5: Accept "Market Day Insurance" choice offer via 'Use now'.
    # redeem_choice_offer() locates the ContainerButtonList, OCR-matches
    # the offer card containing CHOICE_OFFER text, and clicks Usenow.
    # ------------------------------------------------------------------
    logger.log("➡️ Step 5 — Accepting Market Day Insurance choice offer...", status="info")
    print("➡️ Step 5 — Accepting Market Day Insurance choice offer...")
    redeem_choice_offer(CHOICE_OFFER)

    # ------------------------------------------------------------------
    # Step 6: Verify discount promotion line appears in basket.
    # get_promotion_details() reads CartReceipt list items — items with a
    # negative price are treated as promotion lines. Pass the expected
    # promotion description substring to validate it is present on screen.
    # ------------------------------------------------------------------
    win = global_instance.win
    time.sleep(1)  # allow WPF to refresh basket display

    logger.log("➡️ Step 6 — Verifying promotion lines in basket...", status="info")
    print("➡️ Step 6 — Verifying promotion lines in basket...")
    item_descs, item_prices, promo_descs, promo_prices, matched_prices, missing = get_promotion_details(
        "Market Day"  # substring match against on-screen promotion description
    )

    # ------------------------------------------------------------------
    # Points validation:
    #   Formula  : base_pts = ((net_spend + 1) // 2) * 2
    #              expected_pts = base_pts * 3   (3× multiplier)
    #   net_spend = sum(item prices) − sum(abs(promo prices))
    # ------------------------------------------------------------------
    def _parse_price(text):
        try:
            return abs(float(str(text).replace("$", "").replace(",", "").strip()))
        except Exception:
            return 0.0

    normal_total = sum(_parse_price(p) for p in item_prices)
    promo_total  = sum(_parse_price(p) for p in promo_prices)
    net_spend    = round(normal_total - promo_total, 2)

    base_pts      = int(((net_spend + 1) // 2) * 2)
    expected_pts  = base_pts * 3          # 3× multiplier for SDC card

    actual_pts = global_instance.loyalty_points
    logger.log(
        f"ℹ️ Points calc — normal: ${normal_total:.2f}, promo: -${promo_total:.2f}, "
        f"net: ${net_spend:.2f}, base: {base_pts}, expected (3×): {expected_pts}, "
        f"actual: {actual_pts}",
        status="info",
    )
    print(
        f"ℹ️ Points calc — net spend: ${net_spend:.2f} | "
        f"base: {base_pts} | expected (3×): {expected_pts} | actual: {actual_pts}"
    )

    if actual_pts is not None:
        if int(actual_pts) == expected_pts:
            logger.log(
                f"✅ Loyalty points correct — expected {expected_pts}, actual {actual_pts} (3× multiplier).",
                status="pass",
            )
            print(f"✅ Points match: {actual_pts} == {expected_pts}")
        else:
            logger.log(
                f"❌ Loyalty points mismatch — expected {expected_pts}, actual {actual_pts}.",
                status="fail",
            )
            print(f"❌ Points mismatch: actual {actual_pts} ≠ expected {expected_pts}")
    else:
        logger.log("⚠️ Could not read WoWRewardPoints for validation.", status="info")
        print("⚠️ WoWRewardPoints not readable — skipping points assertion.")

    # Report total savings (TotalRewardsValue reflects team discount + promotions)
    try:
        savings_ctrl = win.child_window(auto_id="TotalRewardsValue", control_type="Text")
        savings = savings_ctrl.window_text() if savings_ctrl.exists(timeout=3) else "N/A"
        logger.log(f"ℹ️ Step 7 — TotalRewardsValue (team discount + savings): '{savings}'", status="info")
        print(f"ℹ️ Step 7 — TotalRewardsValue: '{savings}'")
    except Exception as e:
        logger.log(f"⚠️ Step 7 — Could not read TotalRewardsValue: {e}", status="info")

    # ------------------------------------------------------------------
    # Step 8: Complete transaction via EFT (Tender2)
    # ------------------------------------------------------------------
    if not complete_transaction():
        raise RuntimeError("complete_transaction failed — aborting test.")

    # ------------------------------------------------------------------
    # Step 9: Verify EagleEye logs (wallet open + wallet settle)
    # ------------------------------------------------------------------
    ee_result = verify_eagleeye_logs(
        expect_wallet_open=True,
        expect_wallet_settle=True,
    )

    if not ee_result["all_passed"]:
        logger.log(
            "❌ EagleEye verification failed. See individual step logs above.",
            status="fail",
        )
    else:
        logger.log(
            "✅ TC_008 PASSED — Market Day Insurance offer accepted; "
            "transaction settled in EagleEye.",
            status="pass",
        )

except Exception as e:
    logger.log(f"❌ Unexpected error in TC_008: {e}", status="fail")
    print(f"❌ TC_008 ERROR: {e}")
    logger.take_screenshot("TC_008_Unexpected_Error")

finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
