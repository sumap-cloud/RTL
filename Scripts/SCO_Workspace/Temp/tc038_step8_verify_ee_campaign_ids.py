"""
tc038_step8_verify_ee_campaign_ids.py — verify EE apportionment using the
REAL campaign/offer IDs (confirmed live from the wallet/settle payload),
not description strings (which don't appear in the EE log at all — only
SKUs/campaign IDs do). This matches the manual test case's own campaign
ID references exactly:
  Bond      = 1555076
  Coke      = 1261037
  BOG       = 1261715
  Kitkat    = 1260707
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components.Verify_EagleEye_logs import _get_todays_log, _filter_content_after, _extract_settle_block

start_time = datetime.now() - timedelta(minutes=30)
log_path = _get_todays_log()
content = log_path.read_text(encoding="utf-8", errors="ignore")
content = _filter_content_after(content, start_time)
block = _extract_settle_block(content)

EXPECTED_CAMPAIGNS = {
    "Bond (1555076)": '"resourceId":"1555076"',
    "Coke (1261037)": '"resourceId":"1261037"',
    "BOG (1261715)": '"resourceId":"1261715"',
    "Kitkat (1260707)": '"resourceId":"1260707"',
}

print("=== Campaign ID verification in EE wallet/settle payload ===")
all_found = True
for label, marker in EXPECTED_CAMPAIGNS.items():
    found = marker in block
    print(f"  {'PASS' if found else 'FAIL'}: {label} -> {found}")
    if not found:
        all_found = False

print(f"\nALL CAMPAIGNS FOUND: {all_found}")

# Also confirm the exclusion items (GC Battlenet sku 242647, 1 OzHarvst Hmper
# sku 182226) do NOT have adjustmentResults (i.e. no discount applied to them).
import re
for sku, name in [("242647", "GC Battlenet"), ("182226", "1 OzHarvst Hmper")]:
    pattern = re.compile(r'"sku":"' + sku + r'".{0,300}')
    m = pattern.search(block)
    if m:
        snippet = m.group(0)
        has_adjustment = "adjustmentResults" in snippet
        print(f"  {name} (sku {sku}): adjustmentResults present = {has_adjustment} (expect False)")
    else:
        print(f"  {name} (sku {sku}): NOT FOUND in settle block")
