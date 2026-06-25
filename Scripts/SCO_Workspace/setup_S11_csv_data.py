"""
setup_S11_csv_data.py
---------------------
Run this ONCE to add (or update) S11 rows in SaleData.csv on the SMB share.

Usage:
    python setup_S11_csv_data.py

Rows written:
  Iteration 1 — all scan articles for the Save & Recall coupon locking test.

Articles:
  Scan EANs:      9328854011524, 9300633594176, 9339687200924
  Bunch offer ID: 1261389 — Test Bunch sample

Card:  9353105847263  (EDR card with active market day / bunch / BPM offer)
Redeem Pass 1: $9   |  Redeem Pass 2 (after recall): $10
"""

import csv
import io
import sys

try:
    import smbclient
    from smbclient import register_session
    SMB_AVAILABLE = True
except ImportError:
    SMB_AVAILABLE = False

# --- SMB / file configuration -----------------------------------------------
SMB_SERVER   = "10.80.19.218"
SMB_USERNAME = r"10.80.19.218\backupuser"
SMB_PASSWORD = "ArC53rv3"
FILE_PATH    = r"\\10.80.19.218\d$\RTL_Pywinauto\SaleData.csv"

# --- Test data ---------------------------------------------------------------
# EAN order follows the 13-digit values provided for the eligible/exclusion
# and bunch-triggering articles. Do not scan PLU/article refs like 100325/921694
# directly on SCO.
TC_DATA = [
    {
        "Banner":                "SM",
        "TC_ID":                 "S11",
        "Iteration":             "1",
        "EAN_Codes":             "9328854011524;9300633594176;9339687200924",
        "Item_EAN":              "9328854011524;9300633594176;9339687200924",
        "Card_number":           "9353105847263",
        # Bunch offer name as it appears on the SCO screen
        "Promotion_description": "Test Bunch sample",
        # Choice offer label used for OCR matching in Redeem_choice_offer.py
        "Choice_offer":          "market",
        # Redeem amounts: Pass 1 (before save) and Pass 2 (after recall)
        "Redeem_amount":         "9",
        "Redeem_amount_2":       "10",
    },
]
# ---------------------------------------------------------------------------


def _register_smb():
    if not SMB_AVAILABLE:
        print("⚠️  smbclient not installed — trying direct UNC path access.")
        return
    try:
        register_session(SMB_SERVER, SMB_USERNAME, SMB_PASSWORD)
        print(f"✅ SMB session registered with {SMB_SERVER}.")
    except Exception as e:
        print(f"⚠️  SMB session registration failed: {e}. Trying direct access anyway.")


def _read_csv():
    print(f"\n📂 Reading: {FILE_PATH}")
    with smbclient.open_file(FILE_PATH, mode="r", encoding="utf-8", newline="") as f:
        content = f.read()
    reader = csv.DictReader(io.StringIO(content))
    fieldnames = list(reader.fieldnames) if reader.fieldnames else []
    rows = list(reader)
    print(f"✅ Loaded {len(rows)} rows. Columns: {fieldnames}")
    return rows, fieldnames


def _write_csv(rows, fieldnames):
    print(f"\n📝 Writing back to: {FILE_PATH}")
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    with smbclient.open_file(FILE_PATH, mode="w", encoding="utf-8", newline="") as f:
        f.write(output.getvalue())
    print("✅ SaleData.csv updated successfully.")


def _upsert_row(rows, fieldnames, data):
    for col in data:
        if col not in fieldnames:
            fieldnames.append(col)
            print(f"  ➕ Added missing column: '{col}'")

    for row in rows:
        if (row.get("Banner") == data["Banner"]
                and row.get("TC_ID") == data["TC_ID"]
                and str(row.get("Iteration", "")).strip() == data["Iteration"]):
            for col, val in data.items():
                row[col] = val
            print(f"   ✏️  Updated existing row → {data['TC_ID']} "
                  f"Iter={data['Iteration']} (card={data['Card_number']})")
            return

    new_row = {col: "" for col in fieldnames}
    new_row.update(data)
    rows.append(new_row)
    print(f"   ➕ Appended new row     → {data['TC_ID']} "
          f"Iter={data['Iteration']} (card={data['Card_number']})")


def main():
    if not SMB_AVAILABLE:
        print("❌ smbclient is not installed. Install with: pip install smbprotocol")
        sys.exit(1)

    _register_smb()

    try:
        rows, fieldnames = _read_csv()
    except Exception as e:
        print(f"❌ Could not read CSV: {e}")
        sys.exit(1)

    print("\n🔧 Upserting S11 row (Iteration 1)...")
    for data in TC_DATA:
        _upsert_row(rows, fieldnames, data)

    try:
        _write_csv(rows, fieldnames)
    except Exception as e:
        print(f"❌ Could not write CSV: {e}")
        sys.exit(1)

    print("\n✅ Done. Summary:")
    for data in TC_DATA:
        print(f"   {data['TC_ID']:6s}  Iter={data['Iteration']}  "
              f"Banner={data['Banner']}  Card={data['Card_number']}  "
              f"EAN_Codes={data['EAN_Codes']}")


if __name__ == "__main__":
    main()
