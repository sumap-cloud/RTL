import json
import re
from pathlib import Path

class TransactionDetailsFromLog:
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


    def extract_last_transaction(file_path):
        print(f"h1 - Searching in: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                print("h2 - File Loaded Successfully")

                req_marker = "via POST to Settle Wallet, Request Body:"
                res_marker = "wallet/settle"
                res_content_marker = "Response Content:"

                # ✅ Extract request JSONs
                request_matches = list(re.finditer(req_marker, content))
                request_jsons = [
                    TransactionDetailsFromLog.get_json_block(content, m.end())
                    for m in request_matches
                ]
                request_jsons = [r for r in request_jsons if r]

                # ✅ Extract response JSONs
                response_jsons = []
                for match in re.finditer(res_marker, content):
                    next_res = content.find(res_content_marker, match.end())
                    if next_res != -1:
                        block = TransactionDetailsFromLog.get_json_block(
                            content,
                            next_res + len(res_content_marker)
                        )
                        if block:
                            response_jsons.append(block)

                response_jsons = [r for r in response_jsons if r]

                print(f"Found {len(request_jsons)} requests and {len(response_jsons)} responses.")

                if not request_jsons or not response_jsons:
                    print("⚠️ No transactions found")
                    return None

                print("h3 - Processing LAST transaction")

                # ✅ Extract status
                status = TransactionDetailsFromLog.get_last_transaction_status(content)

                if status:
                    print(f"✅ Transaction Status (from log): {status}")
                else:
                    print("⚠️ Status not found")
                    return None

                # ✅ STRICT CONDITION
                if status.upper() != "SETTLED":
                    print(f"❌ Transaction is not SETTLED({status}) → skipping output")
                    return None

                # ✅ Only if SETTLED → process data
                req_data = json.loads(request_jsons[-1])
                res_data = json.loads(response_jsons[-1])

                tx_list = res_data.get("walletTransactions", [])
                tx = tx_list[0] if tx_list else {}
                tx_meta = tx.get("meta", {})

                data = {
                    "salesorganization": tx_meta.get("salesorganization"),
                    "storeid": req_data.get("storeId"),
                    "posid": req_data.get("posId"),
                    "bannerId": req_data.get("location", {}).get("parentIncomingIdentifier"),
                    "sequenceNumber": tx_meta.get("sequencenumber"),
                    "Laybystatus": tx_meta.get("laybystatus"),
                    "IsRetroActive": req_data.get("any", {}).get("IsRetroActive"),
                    "transactionstarttime": tx_meta.get("transactionstarttime"),
                    "reference": tx_meta.get("reference") or tx.get("reference"),
                    "status": status
                }

                return data

        except Exception as e:
            print(f"Error: {e}")

        return None


# ✅ MAIN
if __name__ == "__main__":
    log_path = Path(r"C:\Users\2318941\Testing\.venv\ee.log")

    logParser = TransactionDetailsFromLog()

    result = logParser.extract_last_transaction(log_path)

    # ✅ Print ONLY if SETTLED
    if result:
        print("\n--- LAST TRANSACTION RESULT (SETTLED) ---")
        for key, value in result.items():
            print(f"{key}: {value}")
