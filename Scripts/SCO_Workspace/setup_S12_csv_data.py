"""
setup_S12_csv_data.py
---------------------
Run this ONCE to add (or update) S12 rows in SaleData.csv on the SMB share.

Usage:
    python setup_S12_csv_data.py

Rows written:
  Iteration 1 — eligible + Food Co / Our Brand articles (Pass 1, no subscription).
  Iteration 2 — ineligible articles (gift card) for Pass 2 + subscription offer.

To update a card number or EAN later, edit TC_DATA below and re-run this script.

⚠️  Fill in <FILL_GIFTCARD_EAN> before running for the first time.
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
# Article: 9300677010752 (EAN provided for S12)
# Food Co / Our Brand PLU articles: 100123, 100988, 100066, 100067
# Card: 9344770036069 (Registered SDC / Everyday Extra card with team benefits)

TC_DATA = [
    # --- Pass 1: eligible general article + Food Co / Our Brand PLUs ----------
    {
        "Banner":                "SM",
        "TC_ID":                 "S12",
        "Iteration":             "1",
        "EAN_Codes":             "9339687182374;9339687182381",
        "Item_EAN":              "9339687182374;9339687182381",
        "Card_number":           "9344770036069",
        # Semicolon-separated promo descriptions expected on screen at Pass 1
        # (Food Co 5.27% + 5% Team Discount + 3x multiplier — NO subscription)
        # Update these strings to match the exact text shown on the SCO screen.
        "Promotion_description": "Our WW Brand Disc;Team Discount",
        "Food_co_offer":         "Our WW Brand Disc",
        "Team_discount":         "Team Discount",
        "Multiplier":            "3x",
        "Subscription_offer":    "",
        "Choice_offer":          "",
    },
    # --- Pass 2: same articles cumulative + subscription accepted ------------
    {
        "Banner":                "SM",
        "TC_ID":                 "S12",
        "Iteration":             "2",
        "EAN_Codes":             "9339687182374;9339687182381",
        "Item_EAN":              "9339687182374;9339687182381",
        "Card_number":           "9344770036069",
        "Promotion_description": "Our WW Brand Disc;Team Discount",
        "Food_co_offer":         "Our WW Brand Disc",
        "Team_discount":         "Team Discount",
        "Multiplier":            "3x",
        "Subscription_offer":    "Everyday Extra",
        "Choice_offer":          "",
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
    # Ensure all columns from data exist in the fieldnames list
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

    # Row not found — append a new one
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

    print("\n🔧 Upserting S12 rows (Iteration 1 and 2)...")
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
