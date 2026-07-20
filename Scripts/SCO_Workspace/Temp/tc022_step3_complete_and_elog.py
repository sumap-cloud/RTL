"""
tc022_step3_complete_and_elog.py — LIVE BUILD STEP 3 for TC_022
Connects to the already-running transaction (12 items, currently on
"Select Payment Type" screen, loyalty card NOT scanned this run),
completes the transaction via card (EFT) payment, then validates the
EagleEye (EE) logs.
"""
import sys
import time
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from pywinauto import Application
from Components import global_instance
from Components.Complete_transaction import complete_transaction
from Components.Verify_EagleEye_logs import verify_eagleeye_logs, verify_card_in_ee_log
from Components.report import logger

TC_ID = "TC_022_VerifyOpenOffersForUnregisteredCard"
logger.set_tc_id(TC_ID)

CARD_CODE = "9344450008836"

app = Application(backend="uia").connect(title_re=".*NCR NEXTGENUI.*")
win = app.window(title_re=".*NCR NEXTGENUI.*")
global_instance.app = app
global_instance.win = win
win.set_focus()
print("✅ Connected to NCR NEXTGENUI window.")

result = complete_transaction()
print(f"complete_transaction result: {result}")

time.sleep(3)  # allow EE logs to populate

ee_result = verify_eagleeye_logs()
print(f"verify_eagleeye_logs result: {ee_result}")

card_result = verify_card_in_ee_log(CARD_CODE)
print(f"verify_card_in_ee_log result: {card_result}")

logger.save()
