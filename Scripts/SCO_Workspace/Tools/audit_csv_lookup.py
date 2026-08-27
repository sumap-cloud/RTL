"""
Health check: does every test script actually find its data row?

WHY THIS EXISTS
---------------
Every test script declares two constants:

    BANNER = "SM"          # or BigW / NZ
    TC_ID  = "TC_004"

and looks its data up with Read_csv.get_csv_value(BANNER, TC_ID, ...).

If no CSV row matches that Banner+TC_ID pair, the lookup does NOT raise.
Every script falls back to a hardcoded value instead - so the test still
runs, still goes green, but runs on the *wrong data*. That is the most
dangerous failure mode in this project: a passing report that proves
nothing.

This script finds those silent mismatches before they cost you a test cycle.

WHEN TO RUN IT
--------------
  * After editing Data/RegressionSale.csv
  * After adding a new test script
  * After changing any BANNER or TC_ID constant
  * Before handing a regression run to anyone

HOW TO RUN IT
-------------
    cd "C:\\Pywin\\RTL Automation"
    .\\Scripts\\python.exe Scripts\\SCO_Workspace\\Tools\\audit_csv_lookup.py

READING THE OUTPUT
------------------
    Sanity: 11/11 resolve            <- good
    BigW: 31/32 resolve
        MISS  TC_028_....py
              no CSV row for  BigW / TC_028_...

For every MISS line, either add a row to the CSV with exactly that
Banner + TC_ID, or correct the constant in the script.

Exit code 0 = every script resolves. Exit code 1 = at least one MISS.
Safe to wire into CI.
"""

import csv
import re
import sys
from pathlib import Path

# Tools/ lives inside SCO_Workspace, so the workspace is our parent.
WORKSPACE = Path(__file__).resolve().parent.parent
CSV_PATH = WORKSPACE / "Data" / "RegressionSale.csv"
TESTING = WORKSPACE / "Testing"

SUITES = ("Sanity", "Regression", "SM", "Metro", "BigW", "NZ")


def load_keys():
    if not CSV_PATH.exists():
        print(f"ERROR: test data file not found: {CSV_PATH}")
        sys.exit(2)
    # restkey is essential - the CSV has trailing columns that would otherwise
    # be silently dropped and corrupt the file if it were ever rewritten.
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh, restkey="_overflow"))
    return {
        (r.get("Banner", "").strip(), r.get("TC_ID", "").strip())
        for r in rows
        if r.get("Banner") and r.get("TC_ID")
    }


def audit_suite(name, keys):
    folder = TESTING / name
    if not folder.exists():
        print(f"{name}: FOLDER NOT FOUND ({folder})")
        return 0, 0, []

    files = sorted(p for p in folder.rglob("TC_*.py"))
    ok, misses = 0, []
    for f in files:
        txt = f.read_text(encoding="utf-8", errors="replace")
        m_banner = re.search(r'^BANNER\s*=\s*["\']([^"\']+)["\']', txt, re.M)
        m_tcid = re.search(r'^TC_ID\s*=\s*["\']([^"\']+)["\']', txt, re.M)
        if not m_banner or not m_tcid:
            misses.append((f.name, "script declares no BANNER / TC_ID"))
            continue
        key = (m_banner.group(1).strip(), m_tcid.group(1).strip())
        if key in keys:
            ok += 1
        else:
            misses.append((f.name, f"no CSV row for  {key[0]} / {key[1]}"))
    return ok, len(files), misses


def main():
    keys = load_keys()
    print(f"Test data: {CSV_PATH}")
    print(f"Distinct Banner+TC_ID keys in CSV: {len(keys)}")
    print("-" * 60)

    total_miss = 0
    for name in SUITES:
        ok, total, misses = audit_suite(name, keys)
        print(f"{name}: {ok}/{total} resolve")
        for filename, reason in misses:
            print(f"    MISS  {filename}")
            print(f"          {reason}")
        total_miss += len(misses)

    print("-" * 60)
    if total_miss:
        print(f"{total_miss} script(s) will silently fall back to hardcoded data.")
        return 1
    print("All scripts resolve to a real CSV row.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
