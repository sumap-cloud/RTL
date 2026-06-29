import csv
from pathlib import Path

# --- Local Data Path ---
_DATA_DIR       = Path(__file__).resolve().parent.parent / "Data"
LOCAL_SALE_DATA = _DATA_DIR / "RegressionSale.csv"


def get_csv_value(source_name, banner, tc_id, iteration, target_column):
    """
    Read a value from the local RegressionSale.csv by matching Banner, TC_ID,
    and Iteration.

    Args:
        source_name   (str): Accepted for API compatibility — only 'saledata' used.
        banner        (str): Banner to match (e.g. 'SM').
        tc_id         (str): Full TC_ID string to match.
        iteration     (int): Iteration number to match.
        target_column (str): Column name whose value to return.

    Returns:
        str: Matched value, or an error/info string.
    """
    csv_path = LOCAL_SALE_DATA

    if not csv_path.exists():
        msg = f"Error: Data file not found at {csv_path}"
        print(f"❌ {msg}")
        return msg

    try:
        with open(csv_path, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if (row.get("Banner") == banner
                        and row.get("TC_ID") == tc_id
                        and row.get("Iteration") == str(iteration)):
                    value = row.get(target_column, f"Column '{target_column}' not found")
                    print(f"✅ Found value: {value}")
                    return value

        print(f"⚠️ No matching record: Banner={banner}, TC_ID={tc_id}, Iteration={iteration}")
        return "No matching record found."

    except Exception as e:
        msg = f"Error reading {csv_path}: {e}"
        print(f"❌ {msg}")
        return msg


def get_data_source_info(source_name=None):
    """Return info about the active data source."""
    return {
        "filename": LOCAL_SALE_DATA.name,
        "description": "Sales transaction data (local)",
        "local_path": str(LOCAL_SALE_DATA),
    }


def get_data_source_path(source_name=None):
    """Return path to the local data file."""
    return str(LOCAL_SALE_DATA)

