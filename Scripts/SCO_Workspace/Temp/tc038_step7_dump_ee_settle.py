"""
tc038_step7_dump_ee_settle.py — print the raw wallet/settle block from
today's EE log (scoped to last 20 min) so we can see the REAL payload
format instead of guessing why our offer-name keyword search failed.
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components.Verify_EagleEye_logs import _get_todays_log, _filter_content_after, _extract_settle_block

start_time = datetime.now() - timedelta(minutes=20)
log_path = _get_todays_log()
print(f"Log path: {log_path}")

content = log_path.read_text(encoding="utf-8", errors="ignore")
content = _filter_content_after(content, start_time)
block = _extract_settle_block(content)
print(f"\n=== SETTLE BLOCK (len={len(block) if block else 0}) ===")
print(block)
