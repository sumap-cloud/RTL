"""
setup_TC002_csv_data.py
-----------------------
Run this ONCE to add the TC_002 test data row to SaleData.csv on the SMB share.

Usage (from project root or any directory):
    python setup_TC002_csv_data.py

What it does:
  1. Opens SaleData.csv from the SMB share.
  2. Checks whether a row already exists for Banner=SM / TC_ID=TC_002 / Iteration=1.
  3. If YES  → updates the EAN_Codes, Card_number, and Choice_offer columns.
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

# --- TC_002 data row ---------------------------------------------------------
TARGET_BANNER    = "SM"
TARGET_TC_ID     = "TC_002"
TARGET_ITERATION = "1"

TC002_DATA = {
    "Banner":       TARGET_BANNER,
    "TC_ID":        TARGET_TC_ID,
    "Iteration":    TARGET_ITERATION,
    # 5× EAN = 5 × $2.40 = $12.00 — basket must exceed $10 for redemption offer to appear.
    "EAN_Codes":    "9310072000282;9310072000282;9310072000282;9310072000282;9310072000282",
    "Item_EAN":     "9310072000282;9310072000282;9310072000282;9310072000282;9310072000282",
    "Card_number":  "9353109614656",
    # Choice offer OCR search string — must appear in the on-screen offer card text.
    "Choice_offer": "$10",
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

    # Ensure all TC002_DATA keys are present as columns (add if missing).
    for col in TC002_DATA:
        if col not in fieldnames:
            fieldnames.append(col)
            print(f"  ➕ Added missing column: '{col}'")

    # --- Find or create matching row -----------------------------------------
    matched = False
    for row in rows:
        if (row.get("Banner") == TARGET_BANNER and
                row.get("TC_ID") == TARGET_TC_ID and
                str(row.get("Iteration", "")).strip() == TARGET_ITERATION):
            for col, val in TC002_DATA.items():
                row[col] = val
            matched = True
            print(f"✅ Existing row found → updated TC_ID={TARGET_TC_ID}, Iteration={TARGET_ITERATION}.")
            break

    if not matched:
        new_row = {col: "" for col in fieldnames}
        new_row.update(TC002_DATA)
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
        print(f"   EAN_Codes   : {TC002_DATA['EAN_Codes']}")
        print(f"   Card_number : {TC002_DATA['Card_number']}")
        print(f"   Choice_offer: {TC002_DATA['Choice_offer']}")
    except Exception as e:
        print(f"❌ Could not write CSV: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
