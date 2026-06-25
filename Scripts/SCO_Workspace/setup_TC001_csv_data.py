"""
setup_TC001_csv_data.py
-----------------------
Run this ONCE to add the TC_001 test data row to SaleData.csv on the SMB share.

Usage (from project root or any directory):
    python setup_TC001_csv_data.py

What it does:
  1. Opens SaleData.csv from the SMB share.
  2. Checks whether a row already exists for Banner=SM / TC_ID=TC_001 / Iteration=1.
  3. If YES  → updates the EAN_Codes and Card_number columns.
  4. If NO   → appends a new row with all required columns.
  5. Writes the file back.
"""

import csv
import sys
from pathlib import Path

try:
    from smbclient import register_session
    SMB_AVAILABLE = True
except ImportError:
    SMB_AVAILABLE = False

# --- SMB / file configuration -----------------------------------------------
SMB_SERVER   = "10.80.19.218"
SMB_USERNAME = r"10.80.19.218\backupuser"
SMB_PASSWORD = "ArC53rv3"
FILE_PATH    = r"\\10.80.19.218\d$\RTL_Pywinauto\SaleData.csv"

# --- TC_001 data row ---------------------------------------------------------
TARGET_BANNER    = "SM"
TARGET_TC_ID     = "TC_001"
TARGET_ITERATION = "1"

TC001_DATA = {
    "Banner":       TARGET_BANNER,
    "TC_ID":        TARGET_TC_ID,
    "Iteration":    TARGET_ITERATION,
    # Item EAN codes — SCO workspace uses both column names (handled below)
    "EAN_Codes":    "9310072000282",
    "Item_EAN":     "9310072000282",
    # Loyalty card
    "Card_number":  "9353109614779",
    # Choice offer — empty means no redemption (< 1000 pts)
    "Choice_offer": "",
}
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


def main():
    _register_smb()

    # --- Read existing CSV ---------------------------------------------------
    print(f"\n📂 Reading: {FILE_PATH}")
    try:
        import io
        import smbclient
        with smbclient.open_file(FILE_PATH, mode="r", encoding="utf-8", newline="") as f:
            content = f.read()
        reader = csv.DictReader(io.StringIO(content))
        fieldnames = list(reader.fieldnames) if reader.fieldnames else []
        rows = list(reader)
        print(f"✅ Loaded {len(rows)} rows. Columns: {fieldnames}")
    except Exception as e:
        print(f"❌ Could not read CSV: {e}")
        sys.exit(1)

    # Ensure all TC001_DATA keys are present as columns (add if missing).
    for col in TC001_DATA:
        if col not in fieldnames:
            fieldnames.append(col)
            print(f"  ➕ Added missing column: '{col}'")

    # --- Find or create matching row -----------------------------------------
    matched = False
    for row in rows:
        if (row.get("Banner") == TARGET_BANNER and
                row.get("TC_ID") == TARGET_TC_ID and
                str(row.get("Iteration", "")).strip() == TARGET_ITERATION):
            # Update all TC001 fields in the existing row.
            for col, val in TC001_DATA.items():
                row[col] = val
            matched = True
            print(f"✅ Existing row found → updated TC_ID={TARGET_TC_ID}, Iteration={TARGET_ITERATION}.")
            break

    if not matched:
        # Build a new row: start with empty values for all columns, then fill TC001_DATA.
        new_row = {col: "" for col in fieldnames}
        new_row.update(TC001_DATA)
        rows.append(new_row)
        print(f"✅ No matching row found → appended new row for TC_ID={TARGET_TC_ID}.")

    # --- Write back ----------------------------------------------------------
    print(f"\n📝 Writing back to: {FILE_PATH}")
    try:
        import io
        import smbclient
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
        with smbclient.open_file(FILE_PATH, mode="w", encoding="utf-8", newline="") as f:
            f.write(output.getvalue())
        print(f"✅ SaleData.csv updated successfully.")
        print(f"\n   Banner      : {TARGET_BANNER}")
        print(f"   TC_ID       : {TARGET_TC_ID}")
        print(f"   Iteration   : {TARGET_ITERATION}")
        print(f"   EAN_Codes   : {TC001_DATA['EAN_Codes']}")
        print(f"   Card_number : {TC001_DATA['Card_number']}")
    except Exception as e:
        print(f"❌ Could not write CSV: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
