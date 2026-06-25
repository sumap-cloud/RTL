"""
Verify_EagleEye_logs.py
-----------------------
Parses the EEAdapter daily log file at:
    C:\\Retalix\\EEAdapter\\Logs\\EEAdapter_{YYYY-MM-DD}.{n}.log

After a transaction completes, this component verifies that the three
mandatory EagleEye events were captured in the log:

  1. Card Validation  — "Received request from R10 via POST to validate card number"
  2. Wallet Open      — POST to wallet/open endpoint
  3. Wallet Settle    — POST to wallet/settle endpoint
                        (use expect_wallet_settle=False for training-mode TCs
                         where the settle must NOT occur)

The search is scoped to log lines written AFTER a recorded start timestamp
(global_instance.ee_log_start_time) to avoid matching entries from previous
test runs in the same daily log file.

Adapted from:
  Scripts/POS_Workspace/RTLPOSFlow/Component/Transaction_details_EE_Logs.py
"""

import os
import re
import sys
import json
from datetime import datetime
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components import global_instance
from Components.report import logger

# ----- Configuration -------------------------------------------------------
EE_LOG_DIR = r"C:\Retalix\EEAdapter\Logs"

# Log-line markers for each EE event (case-sensitive, substring match).
_CARD_VALIDATION_MARKER = "via POST to validate card number"
_WALLET_OPEN_MARKER = "wallet/open"
_WALLET_SETTLE_MARKER_1 = "wallet/settle"          # URL marker
_WALLET_SETTLE_MARKER_2 = "via POST to Settle Wallet"  # request-body marker
_WALLET_SETTLED_STATUS = "SETTLED"                 # status string in response
_WALLET_OPEN_RESPONSE_OK = "200"                   # HTTP 200 in open response

# Regex to extract the timestamp from a log line:
#   "2026-06-15 15:22:19,929  INFO ..."
_LOG_TIMESTAMP_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d+"
)
# --------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def verify_eagleeye_logs(
    expect_wallet_open=True,
    expect_wallet_settle=True,
    start_time=None,
):
    """
    Verify EagleEye events in the current day's EEAdapter log.

    Args:
        expect_wallet_open (bool):   True if WalletOpen must be present.
        expect_wallet_settle (bool): True if WalletSettle must be present
                                     (False for training-mode TCs).
        start_time (datetime):       Search only log lines after this time.
                                     Defaults to global_instance.ee_log_start_time.

    Returns:
        dict: {
            "card_validation": bool,
            "wallet_open":     bool,
            "wallet_settle":   bool,
            "settled_status":  str or None,
            "all_passed":      bool,
        }
    """
    result = {
        "card_validation": False,
        "wallet_open": False,
        "wallet_settle": False,
        "settled_status": None,
        "all_passed": False,
    }

    # Visual section header in the HTML report.
    logger.log_section("🔍 EagleEye Log Verification")

    # Determine search start time.
    if start_time is None:
        start_time = global_instance.ee_log_start_time
    if start_time is None:
        logger.log(
            "⚠️ No EE log start time recorded. "
            "Searching entire today's log (may match previous transactions).",
            status="pass"
        )

    # Locate today's log file.
    log_path = _get_todays_log()
    if log_path is None:
        logger.log(
            f"❌ No EEAdapter log found for today in {EE_LOG_DIR}.",
            status="fail"
        )
        logger.take_screenshot("Verify_EE_Log_File_Not_Found")
        return result

    logger.log(f"✅ Reading EE log: {log_path.name}", status="pass")

    # Read log content.
    try:
        content = log_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        logger.log(f"❌ Could not read EE log file: {e}", status="fail")
        logger.take_screenshot("Verify_EE_Log_Read_Error")
        return result

    # Scope content to lines written AFTER start_time.
    if start_time is not None:
        content = _filter_content_after(content, start_time)
        logger.log(
            f"✅ Filtering EE log from {start_time.strftime('%H:%M:%S')} onwards.",
            status="pass"
        )

    # ------------------------------------------------------------------
    # Check 1: Card Validation
    # ------------------------------------------------------------------
    if _CARD_VALIDATION_MARKER in content:
        result["card_validation"] = True
        logger.log("✅ Card Validation event found in EE logs.", status="pass")
    else:
        logger.log(
            "❌ Card Validation event NOT found in EE logs. "
            "Expected marker: 'via POST to validate card number'.",
            status="fail"
        )
        logger.take_screenshot("Verify_EE_CardValidation_Missing")

    # ------------------------------------------------------------------
    # Check 2: Wallet Open
    # ------------------------------------------------------------------
    if _WALLET_OPEN_MARKER in content:
        result["wallet_open"] = True
        if expect_wallet_open:
            logger.log("✅ Wallet Open event found in EE logs.", status="pass")
        else:
            # Unexpected (not an error for current scenarios, just note it).
            logger.log("✅ Wallet Open event found in EE logs.", status="pass")
    else:
        if expect_wallet_open:
            logger.log(
                "❌ Wallet Open event NOT found in EE logs.",
                status="fail"
            )
            logger.take_screenshot("Verify_EE_WalletOpen_Missing")
        else:
            logger.log("✅ Wallet Open not found (not expected).", status="pass")

    # ------------------------------------------------------------------
    # Check 3: Wallet Settle
    # ------------------------------------------------------------------
    wallet_settle_found = (
        _WALLET_SETTLE_MARKER_1 in content
        or _WALLET_SETTLE_MARKER_2 in content
    )
    result["wallet_settle"] = wallet_settle_found

    if expect_wallet_settle:
        if wallet_settle_found:
            logger.log("✅ Wallet Settle event found in EE logs.", status="pass")
            # Extract the settlement status from the response.
            status_val = _extract_settle_status(content)
            result["settled_status"] = status_val
            if status_val and status_val.upper() == _WALLET_SETTLED_STATUS:
                logger.log(
                    f"✅ EagleEye transaction status: {status_val}.",
                    status="pass"
                )
            elif status_val:
                logger.log(
                    f"❌ EagleEye transaction status is '{status_val}', expected 'SETTLED'.",
                    status="fail"
                )
                logger.take_screenshot("Verify_EE_Settlement_Status_Mismatch")
            else:
                logger.log(
                    "⚠️ Could not extract settlement status from EE log response.",
                    status="pass"
                )
        else:
            logger.log(
                "❌ Wallet Settle event NOT found in EE logs. "
                "The transaction may not have been settled with EagleEye.",
                status="fail"
            )
            logger.take_screenshot("Verify_EE_WalletSettle_Missing")
    else:
        # Training mode: Wallet Settle must NOT be present.
        if wallet_settle_found:
            logger.log(
                "❌ Wallet Settle event FOUND in EE logs but was NOT expected "
                "(training mode transaction should not settle).",
                status="fail"
            )
            logger.take_screenshot("Verify_EE_WalletSettle_Unexpected")
        else:
            logger.log(
                "✅ Wallet Settle NOT present in EE logs as expected (training mode).",
                status="pass"
            )

    # ------------------------------------------------------------------
    # Overall pass/fail decision.
    # ------------------------------------------------------------------
    cv_ok = result["card_validation"]
    wo_ok = result["wallet_open"] == expect_wallet_open or result["wallet_open"]
    ws_ok = (result["wallet_settle"] == expect_wallet_settle)

    result["all_passed"] = cv_ok and wo_ok and ws_ok

    if result["all_passed"]:
        logger.log(
            "✅ All expected EagleEye log events verified successfully.",
            status="pass"
        )
    else:
        logger.log(
            "❌ One or more EagleEye log checks failed. Review individual steps above.",
            status="fail"
        )

    return result


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _get_todays_log():
    """
    Return a Path to the latest EEAdapter log file for today, or None.

    Files follow the pattern: EEAdapter_{YYYY-MM-DD}.{n}.log
    When multiple numbered versions exist (e.g., .0.log, .1.log), the
    highest-numbered one is returned.
    """
    today_str = datetime.now().strftime("%Y-%m-%d")
    log_dir = Path(EE_LOG_DIR)
    if not log_dir.exists():
        return None

    prefix = f"EEAdapter_{today_str}"
    matching = sorted(
        [f for f in log_dir.iterdir() if f.name.startswith(prefix)],
        key=lambda f: f.name,
    )
    return matching[-1] if matching else None


def _filter_content_after(content, start_time):
    """
    Return the substring of `content` that begins at (or after) `start_time`.

    Works by scanning log-line timestamps; returns everything from the first
    line whose timestamp is >= start_time.  Falls back to returning the full
    content if no matching timestamp is found.
    """
    lines = content.splitlines(keepends=True)
    for i, line in enumerate(lines):
        m = _LOG_TIMESTAMP_RE.match(line)
        if m:
            try:
                line_dt = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
                if line_dt >= start_time:
                    return "".join(lines[i:])
            except ValueError:
                continue
    return content


def _extract_settle_status(content):
    """
    Extract the EagleEye transaction status from the log.

    Looks for the pattern:
        MESSAGE: Sending response to R10 - 200:
        <next non-empty line>  →  e.g. "SETTLED" or "NOT_SETTLED"
    """
    marker = "MESSAGE: Sending response to R10 - 200:"
    last_idx = content.rfind(marker)
    if last_idx == -1:
        return None

    after = content[last_idx:]
    for line in after.splitlines()[1:6]:
        stripped = line.strip()
        if stripped:
            return stripped
    return None
