import json
import re
import os
import sys
from pathlib import Path
from datetime import datetime


current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Component.Read_csv import get_csv_value
from Component.Update_csv import update_csv_value
from Component.report import logger



def get_latest_log_for_today(log_directory):
    # 1. Get today's date in the format seen in your files (e.g., 2026-05-21)
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # 2. List all files in the directory
    try:
        files = os.listdir(log_directory)
    except FileNotFoundError:
        return "Directory not found."

    # 3. Filter files that start with EEAdapter and match today's date
    today_logs = [f for f in files if f.startswith(f"EEAdapter_{today_str}")]

    if not today_logs:
        return f"No logs found for today ({today_str})."

    # 4. Sort the filtered files
    # We sort them so the highest version number (e.g., .3 vs .0) is at the end
    today_logs.sort()

    # The last item in the sorted list is the latest version
    return today_logs[-1]



def get_json_block(content, start_pos):
    """Extract balanced JSON using curly brace tracking."""
    brace_count = 0
    json_start = content.find('{', start_pos)

    if json_start == -1:
        return None

    for i in range(json_start, len(content)):
        if content[i] == '{':
            brace_count += 1
        elif content[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                return content[json_start:i + 1]

    return None


def get_last_transaction_status(content):
    """
    Extract status from log lines after:
    MESSAGE: Sending response to R10 - 200:
    """
    marker = "MESSAGE: Sending response to R10 - 200:"

    last_index = content.rfind(marker)
    if last_index == -1:
        return None

    after_text = content[last_index:]
    lines = after_text.splitlines()

    # ✅ Get next non-empty line
    for i in range(1, min(6, len(lines))):
        line = lines[i].strip()
        if line:
            return line

    return None


def extract_last_transaction(log_path, file_path2, banner, TC_ID, Iteration):
    print(f"h1 - Searching in: {log_path}")

    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            print("h2 - File Loaded Successfully")

            req_marker = "via POST to Settle Wallet, Request Body:"
            # req_marker = "Status: OK, Code: 200, Response Content:"
            res_marker = "wallet/settle"
            res_content_marker = "Response Content:"

            # ✅ Extract request JSONs
            request_matches = list(re.finditer(req_marker, content))
            request_jsons = [
                get_json_block(content, m.end())
                for m in request_matches
            ]
            request_jsons = [r for r in request_jsons if r]

            # ✅ Extract response JSONs
            response_jsons = []
            for match in re.finditer(res_marker, content):
                next_res = content.find(res_content_marker, match.end())
                if next_res != -1:
                    block = get_json_block(
                        content,
                        next_res + len(res_content_marker)
                    )
                    if block:
                        response_jsons.append(block)

            response_jsons = [r for r in response_jsons if r]

            print(f"Found {len(request_jsons)} requests and {len(response_jsons)} responses.")

            if not request_jsons or not response_jsons:
                print("⚠️ No transactions found")
                return None, None

            # print("h3 - Processing LAST transaction")

            # ✅ Extract status
            status = get_last_transaction_status(content)

            if status:
                print(f"✅ Transaction Status (from log): {status}")
            else:
                print("⚠️ Status not found")
                return None, None

            # ✅ STRICT CONDITION
            if status.upper() != "SETTLED":
                print(f"❌ Transaction is not SETTLED({status}) → skipping output")
                return None, None

            # ✅ Only if SETTLED → process data
            req_data = json.loads(request_jsons[-1])
            res_data = json.loads(response_jsons[-1])

            tx_list = res_data.get("walletTransactions", [])
            tx = tx_list[0] if tx_list else {}
            tx_meta = tx.get("meta", {})

            data = {
                "Salesorganization": tx_meta.get("salesorganization"),
                # "storeid": req_data.get("storeId"),
                "Workstationid": req_data.get("posId"),
                # "bannerId": req_data.get("location", {}).get("parentIncomingIdentifier"),
                "Sequencenumber": tx_meta.get("sequencenumber"),
                "Saleschannel": tx_meta.get("saleschannel"),
                "Transactionstarttime": tx_meta.get("transactionstarttime"),
                "Laybystatus": tx_meta.get("laybystatus"),
                "RetroActive": req_data.get("any", {}).get("IsRetroActive"),
               
                # "reference": tx_meta.get("reference") or tx.get("reference"),
                # "status": status
            }
            reference = tx_meta.get("reference") or tx.get("reference")

            storeid = req_data.get("storeId")
            posid = req_data.get("posId")

            update_csv_value(file_path2, banner, TC_ID, Iteration, 'Store_No', storeid)
            update_csv_value(file_path2, banner, TC_ID, Iteration, 'Pos_No', posid)

            print(f"✅ Extracted Reference: {reference}")
            return data, reference

    except Exception as e:
        print(f"Error: {e}")

    return None, ""


def update_transaction_details(banner, TC_ID, Iteration, data_file="SaleData.csv", transaction_data_file="TransactionData.csv"):
    # This function can be called to update transaction details in the global instance
    DATA_FILE = data_file
    RESOURCE_DIR = current_file_path.parent.parent / "resources"

    parent_path = Path(__file__).parent.parent
    file_path = parent_path / 'resources' / data_file
    file_path2 = parent_path / 'resources' / transaction_data_file



    path = "C:\\Retalix\\EEAdapter\\Logs"
    latest_file = get_latest_log_for_today(path)
    # print(f"✅ The latest log for today is: {latest_file}")

    log_path = Path(rf"{path}\{latest_file}")
    # result, reference = extract_last_transaction(log_path)
    extracted = extract_last_transaction(log_path, file_path2, banner, TC_ID, Iteration)
    if not extracted:
        print(f"❌ No transaction extracted from {log_path}")
        logger.log(f"❌ No transaction extracted from {log_path}", status="fail")
        return False
    result, reference = extracted

    update_csv_value(file_path2, banner, TC_ID, Iteration, 'Transaction_reference', reference)

    if result:
        print("\n--- LAST TRANSACTION RESULT (SETTLED) ---")
        meta_data = ""
        for key, value in result.items():
            # print(f"{key}: {value}")
            meta_data += f"{key}:{value}" + ";"
        update_csv_value(file_path2, banner, TC_ID, Iteration, 'Meta_Data', meta_data)
        logger.log(f"✅ Updated Meta_Data in TransactionData", status="pass")
    else:
        print("No settled transactions found to update.")
        logger.log(f"❌ No settled transactions found to update.", status="fail")

# ✅ MAIN
if __name__ == "__main__":
    update_transaction_details("SM", "TC_001_RecentTransactionValidation", 1)

#     now = datetime.now()

#         # 2. Format it (YYYY-MM-DD HH:MM:SS)
#     formatted_date = now.strftime("%Y-%m-%d")
#     print(formatted_date)

#         # Example Usage:
#     path = "C:\\Retalix\\EEAdapter\\Logs"
#     latest_file = get_latest_log_for_today(path)
#     print(f"✅ The latest log for today is: {latest_file}")
#     print(f"✅ The latest log for today is: {latest_file}")

#     log_path = Path(rf"C:\Retalix\EEAdapter\Logs\{latest_file}")

#     result = extract_last_transaction(log_path)

#     # ✅ Print ONLY if SETTLED
#     if result:
#         print("\n--- LAST TRANSACTION RESULT (SETTLED) ---")
#         for key, value in result.items():
#             print(f"{key}: {value}")
