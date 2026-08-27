"""
run_all_Metro.py
----------------
Runs every TC_*.py test script in this (Metro) suite folder, one after another,
automatically resetting the SCO back to the Welcome screen after each script
(pass, fail, or crash) so the next script always starts from a clean state.

This suite reads the rows in Data\\RegressionSale.csv where Banner = "Metro".
Those rows were seeded as a copy of the "SM" rows, so Metro and SM start out
testing identical data. Change the Metro rows in the CSV as Metro's own test
data diverges — no code change is needed to do that.

Usage (MUST be run with the project root as the working directory):
    cd "C:\\Pywin\\RTL Automation"
    .\\Scripts\\python.exe Scripts\\SCO_Workspace\\Testing\\Metro\\run_all_Metro.py

Results:
    Individual HTML reports : Scripts\\SCO_Workspace\\Results\\Metro\\<TC_ID>.html
    Per-script console logs : Scripts\\SCO_Workspace\\Results\\BatchLogs\\
    Batch summary           : Scripts\\SCO_Workspace\\Results\\BatchSummary_Metro_<timestamp>.txt
"""

import sys
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent  # .../SCO_Workspace

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components.Batch_runner import run_suite

if __name__ == "__main__":
    run_suite(current_file_path.parent, "Metro")
