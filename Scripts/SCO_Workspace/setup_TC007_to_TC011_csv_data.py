"""
setup_TC007_to_TC011_csv_data.py
--------------------------------
Run this ONCE (or whenever card numbers change) to upsert TC_007 → TC_011
rows in SaleData.csv on the SMB share.

Usage:
    python setup_TC007_to_TC011_csv_data.py

⚠️  Card numbers below are PLACEHOLDERS (all zeros).
    When you receive the real EDR numbers, update the `Card_number` values
    in TC_DATA and rerun this script — no other file needs changing.
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

SMB_SERVER   = "10.80.19.218"
SMB_USERNAME = r"10.80.19.218\backupuser"
SMB_PASSWORD = "ArC53rv3"
FILE_PATH    = r"\\10.80.19.218\d$\RTL_Pywinauto\SaleData.csv"

EAN_5X = ";".join(["9310072000282"] * 5)

# ---------------------------------------------------------------------------
# ⚠️  PLACEHOLDERS — replace Card_number values when real EDR cards provided
# ---------------------------------------------------------------------------
TC_DATA = [
    {
        "Banner":      "SM",
        "TC_ID":       "TC_007",
        "Iteration":   "1",
        "EAN_Codes":   EAN_5X,
        "Item_EAN":    EAN_5X,
        # Locked fund card (segment 108) with > 2000 pts — WOW redemption
        # prompt must NOT appear.
        "Card_number": "9353109564432",
        "Choice_offer": "",
        "Collectable_offer": "",
    },
    {
        "Banner":      "SM",
        "TC_ID":       "TC_008",
        "Iteration":   "1",
        "EAN_Codes":   ";".join(["9342937005316"] * 5),
        "Item_EAN":    ";".join(["9342937005316"] * 5),
        # SDC card with open offer, choice offer, 3x multiplier, team discount.
        # Campaign 1260707: Buy 5 Kitkat chocolate, Get $5 off.
        "Card_number": "9344779058420",
        "Choice_offer": "Market Day",
        "Collectable_offer": "",
    },
    {
        "Banner":      "SM",
        "TC_ID":       "TC_009",
        "Iteration":   "1",
        "EAN_Codes":   ";".join(["9342937005316"] * 5),
        "Item_EAN":    ";".join(["9342937005316"] * 5),
        # Same SDC card as TC_008 (training mode run).
        # Campaign 1260707: Buy 5 Kitkat chocolate, Get $5 off.
        "Card_number": "9344779058420",
        "Choice_offer": "Market Day",
        "Collectable_offer": "",
    },
    {
        "Banner":      "SM",
        "TC_ID":       "TC_010",
        "Iteration":   "1",
        "EAN_Codes":   EAN_5X,
        "Item_EAN":    EAN_5X,
        # SFL card (segment 109) - NZ only, spend >$20 to cross 2000 pts.
        "Card_number": "9490000001137",
        "Choice_offer": "",
        "Collectable_offer": "",
    },
    {
        "Banner":      "SM",
        "TC_ID":       "TC_011",
        "Iteration":   "1",
        "EAN_Codes":   EAN_5X,
        "Item_EAN":    EAN_5X,
        # AirNZ card (segment 110) - NZ only, spend >$20 to cross 2000 pts.
        "Card_number": "9490000002011",
        "Choice_offer": "",
        "Collectable_offer": "",
    },
]
# ---------------------------------------------------------------------------


def _register_smb():
    if not SMB_AVAILABLE:
        print("⚠️  smbclient not installed.")
        return
    try:
        register_session(SMB_SERVER, SMB_USERNAME, SMB_PASSWORD)
        print(f"✅ SMB session registered with {SMB_SERVER}.")
    except Exception as e:
        print(f"⚠️  SMB session registration failed: {e}.")


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
            print(f"   ✏️  Updated existing row → {data['TC_ID']} (card={data['Card_number']})")
            return
    new_row = {col: "" for col in fieldnames}
    new_row.update(data)
    rows.append(new_row)
    print(f"   ➕ Appended new row     → {data['TC_ID']} (card={data['Card_number']})")


def main():
    if not SMB_AVAILABLE:
        print("❌ smbclient not installed. Run: pip install smbprotocol")
        sys.exit(1)
    _register_smb()
    try:
        rows, fieldnames = _read_csv()
    except Exception as e:
        print(f"❌ Could not read CSV: {e}")
        sys.exit(1)

    print("\n🔧 Upserting TC_007 → TC_011 rows...")
    for data in TC_DATA:
        _upsert_row(rows, fieldnames, data)

    try:
        _write_csv(rows, fieldnames)
    except Exception as e:
        print(f"❌ Could not write CSV: {e}")
        sys.exit(1)

    print("\n✅ Done. Summary:")
    for data in TC_DATA:
        card = data['Card_number']
        note = " ← ⚠️ PLACEHOLDER" if card == "0000000000000" else ""
        print(f"   {data['TC_ID']:8s}  Card={card}{note}")


if __name__ == "__main__":
    main()
