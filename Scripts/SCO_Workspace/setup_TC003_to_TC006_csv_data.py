"""
setup_TC003_to_TC006_csv_data.py
--------------------------------
Run this ONCE to add (or update) TC_003 → TC_006 rows in SaleData.csv on the
SMB share.

Usage:
    python setup_TC003_to_TC006_csv_data.py

For each of the 4 TCs:
  1. Opens SaleData.csv from the SMB share.
  2. Checks whether a row already exists for Banner=SM / TC_ID=TC_00X / Iteration=1.
  3. If YES  → updates EAN_Codes / Item_EAN / Card_number columns.
  4. If NO   → appends a new row.
  5. Writes the file back at the end (single round-trip).

To later swap an EDR card number, just edit the corresponding `Card_number`
value in the TC_DATA list below and re-run this script.
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

# --- Test data --------------------------------------------------------------
# 5 × EAN = 5 × $2.40 = $12.00 — basket is generous enough that the loyalty
# point gain (around 1 pt per $1 spent) reliably crosses the 2000-pt threshold
# when the card is preconditioned just below 2000 by the test owner.
EAN_5X = ";".join(["9310072000282"] * 5)

TC_DATA = [
    {
        "Banner":      "SM",
        "TC_ID":       "TC_003",
        "Iteration":   "1",
        "EAN_Codes":   EAN_5X,
        "Item_EAN":    EAN_5X,
        "Card_number": "9353105847300",   # Registered EDR crossing 2000 pts
        "Choice_offer": "",
    },
    {
        "Banner":      "SM",
        "TC_ID":       "TC_004",
        "Iteration":   "1",
        "EAN_Codes":   EAN_5X,
        "Item_EAN":    EAN_5X,
        "Card_number": "9355215896100",   # SFC card (seg 105) crossing 2000 pts
        "Choice_offer": "",
    },
    {
        "Banner":      "SM",
        "TC_ID":       "TC_005",
        "Iteration":   "1",
        "EAN_Codes":   EAN_5X,
        "Item_EAN":    EAN_5X,
        "Card_number": "9355215896056",   # QFF card (seg 104) crossing 2000 pts
        "Choice_offer": "",
    },
    {
        "Banner":      "SM",
        "TC_ID":       "TC_006",
        "Iteration":   "1",
        "EAN_Codes":   EAN_5X,
        "Item_EAN":    EAN_5X,
        "Card_number": "9344450008836",   # Temporary card (unregistered) crossing 2000 pts
        "Choice_offer": "",
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
    # Ensure all columns exist
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
            print(f"   ✏️  Updated existing row → {data['TC_ID']} (card={data['Card_number']})")
            return

    new_row = {col: "" for col in fieldnames}
    new_row.update(data)
    rows.append(new_row)
    print(f"   ➕ Appended new row     → {data['TC_ID']} (card={data['Card_number']})")


def main():
    if not SMB_AVAILABLE:
        print("❌ smbclient is not installed. Install it with: pip install smbprotocol")
        sys.exit(1)

    _register_smb()

    try:
        rows, fieldnames = _read_csv()
    except Exception as e:
        print(f"❌ Could not read CSV: {e}")
        sys.exit(1)

    print("\n🔧 Upserting TC_003 → TC_006 rows...")
    for data in TC_DATA:
        _upsert_row(rows, fieldnames, data)

    try:
        _write_csv(rows, fieldnames)
    except Exception as e:
        print(f"❌ Could not write CSV: {e}")
        sys.exit(1)

    print("\n✅ Done. Summary:")
    for data in TC_DATA:
        print(f"   {data['TC_ID']:8s}  Banner={data['Banner']}  "
              f"Iteration={data['Iteration']}  Card={data['Card_number']}")


if __name__ == "__main__":
    main()
