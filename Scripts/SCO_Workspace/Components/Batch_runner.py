"""
Batch_runner.py
----------------
Shared engine used by the per-suite "run all" entry scripts:
    Testing/Sanity/run_all_Sanity.py
    Testing/Regression/run_all_Regression.py
    Testing/BigW/run_all_BigW.py
    Testing/NZ/run_all_NZ.py

WHAT IT DOES:
    Runs every TC_*.py test script found directly inside a suite folder, one
    at a time, and ALWAYS returns the SCO to the Welcome screen after each
    one (pass, fail, or crash) before starting the next — so every test in
    the batch starts from a clean idle Welcome screen regardless of how the
    previous test ended. Also resets once at the very start of the batch.

    The reset escalates: Reset_to_welcome.py (UI-only) first, and if that
    cannot reach Welcome, Hard_reset_SCO.py stops and restarts the SCO
    application and logs the lane back in. Set SCO_DISABLE_HARD_RESET=1 to
    turn the escalation off.

    After each script runs, the newest matching HTML report in Results/ is
    inspected for the PASS/FAIL badge written by Components/report.py, and a
    consolidated summary (console table + text file in Results/) is produced
    at the end of the batch.

WORKING DIRECTORY:
    Every subprocess launched by this module (test scripts AND the reset
    utilities) is run with the working directory forced to the project root
    (the folder containing this venv's Scripts\\python.exe, e.g.
    "C:\\Pywin\\RTL Automation"). Components/report.py now resolves the
    Results folder from its own file location, so reports land in the right
    place either way — but keeping the working directory consistent means
    any relative path used inside a test script behaves the same whether it
    is run on its own or as part of a batch.
"""

import os
import re
import subprocess
import sys
import time
from pathlib import Path

_COMPONENTS_DIR = Path(__file__).resolve().parent          # .../SCO_Workspace/Components
_SCO_WORKSPACE = _COMPONENTS_DIR.parent                     # .../SCO_Workspace
_PROJECT_ROOT = _SCO_WORKSPACE.parent.parent                # .../RTL Automation  (venv root)
_RESULTS_DIR = _SCO_WORKSPACE / "Results"
_BATCH_LOG_DIR = _RESULTS_DIR / "BatchLogs"
_RESET_SCRIPT = _COMPONENTS_DIR / "Reset_to_welcome.py"
_HARD_RESET_SCRIPT = _COMPONENTS_DIR / "Hard_reset_SCO.py"

# Set SCO_DISABLE_HARD_RESET=1 to keep the old behaviour (soft reset only) —
# useful when debugging on a lane you do not want restarted underneath you.
_HARD_RESET_ENABLED = os.environ.get("SCO_DISABLE_HARD_RESET", "") not in ("1", "true", "True")

_TC_NUM_RE = re.compile(r"TC_0*(\d+)([A-Za-z]*)", re.IGNORECASE)

_SCRIPT_TIMEOUT_SEC = 900          # 15 min max per test script
_RESET_TIMEOUT_SEC = 180           # 3 min max for the soft reset-to-welcome
_HARD_RESET_TIMEOUT_SEC = 480      # 8 min max for a full SCO stop/start/login


def _natural_key(path: Path):
    """Sort TC_02, TC_003, TC_08A, TC_0011 etc. in sensible numeric order."""
    m = _TC_NUM_RE.search(path.stem)
    if m:
        return (int(m.group(1)), m.group(2).upper(), path.stem)
    return (999999, "", path.stem)


def discover_tests(suite_dir: Path):
    """Return sorted list of top-level TC_*.py scripts directly inside suite_dir
    (does NOT recurse into nested helper folders like Scripts/ or Steps/)."""
    tests = [p for p in Path(suite_dir).glob("TC_*.py") if p.is_file()]
    return sorted(tests, key=_natural_key)


def _run_reset():
    """Return the SCO to the Welcome screen between test scripts.

    Two stages, because some stuck states (notably the "Assistance Needed /
    Cancel Purchase" store-approval popup) regenerate themselves and simply
    cannot be cleared by clicking:

        1. Reset_to_welcome.py  — UI-only recovery, fast, always tried first.
        2. Hard_reset_SCO.py    — stops and restarts the SCO application and
                                  logs the lane back in. Only used when
                                  stage 1 did not report "RESET: SUCCESS".

    Without stage 2 one stuck test poisons every remaining test in the batch.
    """
    print("\n↩️  Resetting SCO to Welcome screen before next script...")
    soft_ok = False
    try:
        proc = subprocess.run(
            [sys.executable, str(_RESET_SCRIPT)],
            cwd=str(_PROJECT_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=_RESET_TIMEOUT_SEC,
        )
        out = proc.stdout or ""
        soft_ok = "RESET: SUCCESS" in out
        tail = "\n".join(out.strip().splitlines()[-3:])
        print(f"    {tail}")
    except Exception as e:
        print(f"⚠️ Reset_to_welcome invocation failed: {e}")

    if soft_ok:
        return True

    if not _HARD_RESET_ENABLED:
        print("⚠️ Soft reset failed and hard reset is disabled "
              "(SCO_DISABLE_HARD_RESET=1). Continuing anyway.")
        return False

    if not _HARD_RESET_SCRIPT.exists():
        print(f"⚠️ Hard reset script not found: {_HARD_RESET_SCRIPT}")
        return False

    print("⚠️ Soft reset did not reach Welcome — escalating to a full "
          "SCO restart (Hard_reset_SCO.py)...")
    try:
        proc = subprocess.run(
            [sys.executable, str(_HARD_RESET_SCRIPT)],
            cwd=str(_PROJECT_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=_HARD_RESET_TIMEOUT_SEC,
        )
        out = proc.stdout or ""
        tail = "\n".join(out.strip().splitlines()[-5:])
        print(f"    {tail}")
        if proc.returncode == 0:
            return True
        print("❌ Hard reset also failed — the lane needs a human. "
              "Remaining scripts in this batch are likely to fail.")
    except Exception as e:
        print(f"⚠️ Hard_reset_SCO invocation failed: {e}")
    return False


def _find_report_html(tc_stem: str, since: float):
    """Best-effort match of the HTML report produced by this run.
    Prefers a Results/*.html whose filename starts with the same prefix as
    the script name and was modified at/after `since`; otherwise falls back
    to the most recently modified html changed since `since`.
    """
    if not _RESULTS_DIR.exists():
        return None
    candidates = [p for p in _RESULTS_DIR.glob("*.html") if p.stat().st_mtime >= since]
    if not candidates:
        return None
    prefix = tc_stem.split("_Verify")[0].split("_SCO")[0]
    matches = [p for p in candidates if p.stem.startswith(prefix)]
    pool = matches if matches else candidates
    return max(pool, key=lambda p: p.stat().st_mtime)


def _parse_result(html_path: Path):
    """Inspect the <span class="overall-badge ..."> element written by
    Components/report.py. NOTE: the <style> block in every report always
    defines BOTH ".badge-pass" and ".badge-fail" CSS rules, so a plain
    substring search for "badge-fail" would always match — we must match
    the specific "overall-badge badge-fail"/"overall-badge badge-pass"
    span class combination instead.
    """
    try:
        text = html_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return "UNKNOWN"
    if "overall-badge badge-fail" in text:
        return "FAIL"
    if "overall-badge badge-pass" in text:
        return "PASS"
    return "UNKNOWN"


def run_suite(suite_dir, suite_name):
    """Run every TC_*.py script directly inside suite_dir, resetting to the
    Welcome screen after every single one (pass, fail, or crash).
    Returns the list of per-script result dicts.
    """
    suite_dir = Path(suite_dir).resolve()
    tests = discover_tests(suite_dir)
    if not tests:
        print(f"⚠️ No TC_*.py scripts found directly inside {suite_dir}")
        return []

    _BATCH_LOG_DIR.mkdir(parents=True, exist_ok=True)
    run_stamp = time.strftime("%Y%m%d_%H%M%S")

    print(f"\n{'=' * 70}\n  BATCH RUN — {suite_name} suite — {len(tests)} script(s)\n{'=' * 70}")
    for i, t in enumerate(tests, start=1):
        print(f"   {i:>2}. {t.stem}")

    # Always start the batch from a known-clean state.
    _run_reset()

    results = []
    for idx, script in enumerate(tests, start=1):
        tc_stem = script.stem
        print(f"\n--- [{idx}/{len(tests)}] Running {tc_stem} ---")
        start_time = time.time()

        log_file = _BATCH_LOG_DIR / f"{suite_name}_{tc_stem}_{run_stamp}.log"
        try:
            proc = subprocess.run(
                [sys.executable, "-u", str(script)],
                cwd=str(_PROJECT_ROOT),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=_SCRIPT_TIMEOUT_SEC,
            )
            output = (proc.stdout or "") + "\n" + (proc.stderr or "")
            returncode = proc.returncode
        except subprocess.TimeoutExpired as e:
            output = (e.stdout or "") + "\n" + (e.stderr or "") + f"\n[TIMED OUT after {_SCRIPT_TIMEOUT_SEC}s]"
            returncode = "TIMEOUT"
        except Exception as e:
            output = f"[Batch runner failed to launch script: {e}]"
            returncode = "LAUNCH_ERROR"

        log_file.write_text(output, encoding="utf-8")

        report_html = _find_report_html(tc_stem, start_time)
        status = _parse_result(report_html) if report_html else "NO_REPORT"
        duration = time.time() - start_time

        print(f"    Result: {status}   (exit={returncode}, {duration:.0f}s)")
        if report_html:
            print(f"    Report: {report_html}")
        print(f"    Log:    {log_file}")

        results.append({
            "tc": tc_stem,
            "status": status,
            "returncode": returncode,
            "duration": duration,
            "report": str(report_html) if report_html else "",
            "log": str(log_file),
        })

        # ALWAYS reset — pass, fail, or crash — before the next script runs.
        _run_reset()

    _write_summary(suite_name, results, run_stamp)
    return results


def _write_summary(suite_name, results, run_stamp):
    summary_path = _RESULTS_DIR / f"BatchSummary_{suite_name}_{run_stamp}.txt"
    passed = sum(1 for r in results if r["status"] == "PASS")
    other = len(results) - passed

    lines = [
        f"Batch Summary - {suite_name} suite - {run_stamp}",
        "=" * 70,
        f"Total: {len(results)}   Passed: {passed}   Failed/Other: {other}",
        "-" * 70,
    ]
    for r in results:
        lines.append(f"[{r['status']:<9}] {r['tc']}  ({r['duration']:.0f}s, exit={r['returncode']})")
        if r["report"]:
            lines.append(f"             report: {r['report']}")
        lines.append(f"             log:    {r['log']}")
    lines.append("=" * 70)

    text = "\n".join(lines)
    _RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(text, encoding="utf-8")
    print("\n" + text)
    print(f"\nSummary saved to: {summary_path}")
