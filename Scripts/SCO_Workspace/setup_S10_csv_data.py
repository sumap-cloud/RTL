"""
setup_S10_csv_data.py
---------------------
Run this once to add or update S10 rows in SaleData.csv on the SMB share.

Usage:
    python setup_S10_csv_data.py

Rows written:
  Iteration 1 - Transaction 1 article scan data for the void/lock pass.
  Iteration 2 - Transaction 2 article scan data for the after-3-min unlock pass.

Articles:
  Scan EANs: 9328854011524, 9300633594176, 9339687200924
  Source articles for bunch offer 1261389 - Test Bunch sample include short
  references 100325 and 921694, but SCO scan data must use 13-digit EANs only.

Card:
  9353100734100 - EDR card with bunch/BPM setup and enough points to redeem $10.
"""

import csv
import io
import sys

try:
    import smbclient
    from smbclient import register_session
    from Components.Read_csv import DATA_SOURCES, SMB_PASSWORD, SMB_SERVER, SMB_USERNAME
    SMB_AVAILABLE = True
except ImportError:
    SMB_AVAILABLE = False


FILE_PATH = DATA_SOURCES["saledata"]["path"] if SMB_AVAILABLE else ""
S10_EAN_LIST = "9328854011524;9300633594176;9339687200924"

TC_DATA = [
    {
        "Banner":                "SM",
        "Module":                "LPR",
        "State":                 "Inprogress",
        "TC_ID":                 "S10",
        "Iteration":             "1",
        "EAN_Codes":             S10_EAN_LIST,
        "Item_EAN":              S10_EAN_LIST,
        "Card_number":           "9353100734100",
        "Card_type":             "EDR",
        "Card_status":           "ACTIVE",
        "Promotion_description": "Test Bunch sample",
        "Choice_offer":          "",
        "Redeem_amount":         "10",
        "Scenario":              "Coupon locking after 3 mins - transaction 1 void",
        "Payment_method":        "Card",
    },
    {
        "Banner":                "SM",
        "Module":                "LPR",
        "State":                 "Inprogress",
        "TC_ID":                 "S10",
        "Iteration":             "2",
        "EAN_Codes":             S10_EAN_LIST,
        "Item_EAN":              S10_EAN_LIST,
        "Card_number":           "9353100734100",
        "Card_type":             "EDR",
        "Card_status":           "ACTIVE",
        "Promotion_description": "Test Bunch sample",
        "Choice_offer":          "",
        "Redeem_amount":         "10",
        "Scenario":              "Coupon locking after 3 mins - transaction 2 unlocked",
        "Payment_method":        "Card",
    },
]


def _register_smb():
    try:
        register_session(SMB_SERVER, SMB_USERNAME, SMB_PASSWORD)
        print(f"SMB session registered with {SMB_SERVER}.")
    except Exception as e:
        print(f"SMB session registration failed: {e}. Trying direct access anyway.")


def _read_csv():
    print(f"\nReading: {FILE_PATH}")
    with smbclient.open_file(FILE_PATH, mode="r", encoding="utf-8", newline="") as f:
        content = f.read()
    reader = csv.DictReader(io.StringIO(content))
    fieldnames = list(reader.fieldnames) if reader.fieldnames else []
    rows = list(reader)
    print(f"Loaded {len(rows)} rows. Columns: {fieldnames}")
    return rows, fieldnames


def _write_csv(rows, fieldnames):
    print(f"\nWriting back to: {FILE_PATH}")
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    with smbclient.open_file(FILE_PATH, mode="w", encoding="utf-8", newline="") as f:
        f.write(output.getvalue())
    print("SaleData.csv updated successfully.")


def _validate_13_digit_eans(data):
    eans = [ean.strip() for ean in data["EAN_Codes"].split(";") if ean.strip()]
    invalid = [ean for ean in eans if not (ean.isdigit() and len(ean) == 13)]
    if invalid:
        raise ValueError(
            f"{data['TC_ID']} Iteration {data['Iteration']} contains non-13-digit "
            f"article scan values: {', '.join(invalid)}"
        )


def _upsert_row(rows, fieldnames, data):
    _validate_13_digit_eans(data)

    for col in data:
        if col not in fieldnames:
            fieldnames.append(col)
            print(f"  Added missing column: '{col}'")

    for row in rows:
        if (
            row.get("Banner") == data["Banner"]
            and row.get("TC_ID") == data["TC_ID"]
            and str(row.get("Iteration", "")).strip() == data["Iteration"]
        ):
            for col, val in data.items():
                row[col] = val
            print(
                f"   Updated existing row -> {data['TC_ID']} "
                f"Iter={data['Iteration']} (card={data['Card_number']})"
            )
            return

    new_row = {col: "" for col in fieldnames}
    new_row.update(data)
    rows.append(new_row)
    print(
        f"   Appended new row     -> {data['TC_ID']} "
        f"Iter={data['Iteration']} (card={data['Card_number']})"
    )


def main():
    if not SMB_AVAILABLE:
        print("smbclient is not installed. Install with: pip install smbprotocol")
        sys.exit(1)

    _register_smb()

    try:
        rows, fieldnames = _read_csv()
    except Exception as e:
        print(f"Could not read CSV: {e}")
        sys.exit(1)

    print("\nUpserting S10 rows (Iterations 1 and 2)...")
    for data in TC_DATA:
        _upsert_row(rows, fieldnames, data)

    try:
        _write_csv(rows, fieldnames)
    except Exception as e:
        print(f"Could not write CSV: {e}")
        sys.exit(1)

    print("\nDone. Summary:")
    for data in TC_DATA:
        print(
            f"   {data['TC_ID']:6s}  Iter={data['Iteration']}  "
            f"Banner={data['Banner']}  Card={data['Card_number']}  "
            f"EAN_Codes={data['EAN_Codes']}"
        )


if __name__ == "__main__":
    main()
