"""
tc038_step6_verify_ee_logs.py — verify EagleEye logs for the TC_038
transaction just completed (card '9353186777909', card tender $113.05).
Uses an explicit start_time (a few minutes before the loyalty scan) since
global_instance.ee_log_start_time was never set across our separate
incremental script invocations.
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components.Verify_EagleEye_logs import (
    verify_eagleeye_logs,
    verify_offers_in_ee_log,
    verify_card_in_ee_log,
)

# Scope the search to the last 20 minutes to safely cover the whole TC_038
# live-build transaction (login -> scan -> loyalty -> tender -> settle).
start_time = datetime.now() - timedelta(minutes=20)
print(f"Searching EE logs from: {start_time}")

CARD = "9353186777909"
EXPECTED_OFFERS = [
    "Buy any Bonds product and get 10% off",
    "New Price_Buy 2 Coke For",
    "Buy Epson NX230 Printer",
    "Buy 5 KitKat get",
]

print("\n=== verify_eagleeye_logs() ===")
r1 = verify_eagleeye_logs(expect_wallet_open=True, expect_wallet_settle=True, start_time=start_time)
print(r1)

print("\n=== verify_card_in_ee_log() ===")
r2 = verify_card_in_ee_log(CARD, start_time=start_time)
print(r2)

print("\n=== verify_offers_in_ee_log() ===")
r3 = verify_offers_in_ee_log(EXPECTED_OFFERS, start_time=start_time)
print(r3)
