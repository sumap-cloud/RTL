"""
Update a value in the LOCAL test-data CSV (Data/RegressionSale.csv).

History
-------
This module used to write to a remote SMB share (\\\\10.80.19.218) using a
hard-coded service account.  That made every test run depend on another machine
being switched on and reachable, and it stored a password in source control.
The data now lives in the repository (see Components/Read_csv.py), so this
module writes to the local file only — no network, no credentials.

Public API is unchanged:  update_csv_value(source, banner, tc_id, iteration,
column, new_value) -> bool
"""

import csv
import os
import shutil
import tempfile
import time
from pathlib import Path

from Components.Read_csv import get_data_source_path

MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# csv.DictReader puts surplus fields under this key when a row has more columns
# than the header (trailing commas).  It must never be written back out.
_OVERFLOW_KEY = "_overflow"


def _read_rows(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, restkey=_OVERFLOW_KEY)
        fieldnames = reader.fieldnames
        rows = []
        for row in reader:
            row.pop(_OVERFLOW_KEY, None)
            rows.append(row)
    return fieldnames, rows


def _write_rows_atomically(path, fieldnames, rows):
    """Write to a temp file in the same folder, then replace the original.

    A half-written CSV would break every subsequent test, so the swap is atomic.
    """
    folder = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(prefix=".RegressionSale_", suffix=".csv", dir=folder)
    os.close(fd)
    try:
        with open(tmp, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow({k: row.get(k, "") for k in fieldnames})
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def update_csv_value(source_name, banner, tc_id, iteration, target_column, new_value):
    """
    Update a single cell in the local data CSV.

    Args:
        source_name   (str): Accepted for API compatibility — only 'saledata' is used.
        banner        (str): Banner value to match  (e.g. 'SM', 'NZ', 'BigW').
        tc_id         (str): Test case ID to match (must equal the CSV TC_ID exactly).
        iteration     (int): Iteration number to match.
        target_column (str): Column name to update.
        new_value     (str): New value to store.

    Returns:
        bool: True if a row was matched and the file was rewritten, else False.
    """
    try:
        file_path = get_data_source_path(source_name)
    except ValueError as e:
        print(f"❌ Error: {e}")
        return False

    if not Path(file_path).exists():
        print(f"❌ Data file not found: {file_path}")
        return False

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"📝 Updating CSV: {file_path} (attempt {attempt}/{MAX_RETRIES})")
            fieldnames, rows = _read_rows(file_path)

            if target_column not in fieldnames:
                print(f"⚠️ Column '{target_column}' not found in CSV header.")
                return False

            matched = 0
            for row in rows:
                if (row.get("Banner") == banner
                        and row.get("TC_ID") == tc_id
                        and row.get("Iteration") == str(iteration)):
                    row[target_column] = new_value
                    matched += 1

            if not matched:
                print(f"⚠️ No matching record: Banner={banner}, "
                      f"TC_ID={tc_id}, Iteration={iteration}")
                return False

            _write_rows_atomically(file_path, fieldnames, rows)
            print(f"✅ Updated {target_column} to '{new_value}' "
                  f"({matched} row(s)).")
            return True

        except PermissionError:
            # Almost always Excel holding the file open.
            print(f"❌ Permission denied writing {file_path} "
                  f"— is it open in Excel?")
            if attempt < MAX_RETRIES:
                print(f"⏳ Retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
            else:
                return False
        except Exception as e:
            print(f"❌ Error on attempt {attempt}: {e}")
            if attempt < MAX_RETRIES:
                print(f"⏳ Retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
            else:
                return False

    return False
