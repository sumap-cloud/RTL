"""
tc022_step2_loyalty.py — LIVE BUILD STEP 2 for TC_022
Connects to the already-running transaction (12 items in basket from step 1)
and scans the unregistered loyalty card at the tender prompt.
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
from Components.Scan_loyalty_tenderprompt import scan_loyalty_tenderprompt
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

result = scan_loyalty_tenderprompt(CARD_CODE)
print(f"scan_loyalty_tenderprompt result: {result}")

logger.save()
