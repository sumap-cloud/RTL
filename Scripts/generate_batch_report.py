"""
generate_batch_report.py
------------------------
Reads the test case list (run_tests.txt) and the individual HTML reports
in the Results folder, then generates a batch summary HTML report.

The summary report:
  - Shows overall batch pass/fail status
  - Lists every TC with its result, step counts, and start time
  - Each TC name links to its individual detailed report

Usage (called automatically by run_tests.bat):
    python generate_batch_report.py <run_tests.txt> <results_dir>
"""

import sys
import os
import re
from datetime import datetime
from pathlib import Path


def _parse_tc_name(line):
    """Strip .py extension and whitespace to get a bare TC name."""
    name = line.strip()
    if name.lower().endswith('.py'):
        name = name[:-3]
    return name


def _find_report(results_dir, tc_name):
    """
    Find the latest HTML report for a given TC name.
    Tries exact match first, then prefix wildcard.
    """
    results = Path(results_dir)
    exact = results / f"{tc_name}.html"
    if exact.exists():
        return exact
    matches = sorted(
        results.glob(f"{tc_name}*.html"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    if matches:
        return matches[0]
    return None


def _parse_report(html_path):
    """Parse an individual TC HTML report and return summary dict."""
    with open(html_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()

    result = {
        'path': str(html_path),
        'tc_id': html_path.stem,
        'status': 'UNKNOWN',
        'started': '',
        'total': 0,
        'passed': 0,
        'failed': 0,
    }

    if 'badge-pass' in content:
        result['status'] = 'PASS'
    elif 'badge-fail' in content:
        result['status'] = 'FAIL'

    m = re.search(r'Started:\s*([\d\-:. ]+)', content)
    if m:
        result['started'] = m.group(1).strip()

    m = re.search(r'Total Steps:\s*(\d+)', content)
    if m:
        result['total'] = int(m.group(1))
    m = re.search(r'Passed Steps:\s*(\d+)', content)
    if m:
        result['passed'] = int(m.group(1))
    m = re.search(r'Failed Steps:\s*(\d+)', content)
    if m:
        result['failed'] = int(m.group(1))

    return result


def generate_summary(tc_list_path, results_dir):
    """Generate the batch_summary.html in results_dir."""
    results_path = Path(results_dir)

    # Read TC list
    tc_names = []
    with open(tc_list_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            tc_names.append(_parse_tc_name(line))

    if not tc_names:
        print("⚠️  No test cases found in the list file.")
        return

    # Find and parse each report
    reports = []
    for name in tc_names:
        report_file = _find_report(results_dir, name)
        if report_file:
            reports.append(_parse_report(report_file))
        else:
            reports.append({
                'path': None,
                'tc_id': name,
                'status': 'NOT RUN',
                'started': '',
                'total': 0,
                'passed': 0,
                'failed': 0,
            })

    # Overall batch result
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    all_pass = all(r['status'] == 'PASS' for r in reports)
    overall = 'PASSED' if all_pass else 'FAILED'
    overall_class = 'badge-pass' if all_pass else 'badge-fail'
    overall_icon = '✅' if all_pass else '❌'
    total_tc = len(reports)
    pass_count = sum(1 for r in reports if r['status'] == 'PASS')
    fail_count = sum(1 for r in reports if r['status'] == 'FAIL')
    not_run = sum(1 for r in reports if r['status'] == 'NOT RUN')

    # Build table rows
    rows = []
    for r in reports:
        st = r['status']
        row_class = 'pass' if st == 'PASS' else ('fail' if st == 'FAIL' else 'info')
        icon = '✅' if st == 'PASS' else ('❌' if st == 'FAIL' else '⚪')

        if r['path']:
            rel = os.path.relpath(r['path'], str(results_path)).replace('\\', '/')
            tc_link = (
                f'<a href="{rel}" '
                f'style="color:inherit;text-decoration:underline;">'
                f'{r["tc_id"]}</a>'
            )
        else:
            tc_link = r['tc_id']

        rows.append(f'''        <tr class="{row_class}">
            <td>{tc_link}</td>
            <td>{r["started"]}</td>
            <td style="text-align:center">{r["total"]}</td>
            <td style="text-align:center;color:#388e3c;font-weight:bold">{r["passed"]}</td>
            <td style="text-align:center;color:#c62828;font-weight:bold">{r["failed"]}</td>
            <td class="status-cell">{icon} {st}</td>
        </tr>''')

    rows_html = '\n'.join(rows)
    not_run_row = (
        f'<span class="total" style="color:#888">Not Run: {not_run}</span>'
        if not_run else ''
    )

    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Batch Summary — {now}</title>
    <style>
        body {{ background: #f7f9fa; font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; }}
        .header {{ background: #283593; color: #fff; padding: 24px 0 12px 0; text-align: center; box-shadow: 0 2px 8px #0001; }}
        .badge-container {{ text-align: center; margin: 18px auto 4px auto; }}
        .overall-badge {{ display: inline-block; font-size: 1.45em; font-weight: bold; padding: 12px 48px; border-radius: 10px; letter-spacing: 0.02em; }}
        .badge-pass {{ background: #e8f5e9; color: #388e3c; border: 2.5px solid #388e3c; }}
        .badge-fail {{ background: #ffebee; color: #c62828; border: 2.5px solid #c62828; }}
        .summary-bar {{ background: #fff; margin: 10px auto 18px auto; max-width: 960px; border-radius: 8px; box-shadow: 0 2px 8px #0001; display: flex; justify-content: center; align-items: center; gap: 32px; padding: 14px 0; font-size: 1.1em; }}
        .summary-bar .total {{ color: #283593; font-weight: bold; }}
        .summary-bar .failed {{ color: #c62828; font-weight: bold; }}
        .summary-bar .passed {{ color: #388e3c; font-weight: bold; }}
        table {{ border-collapse: separate; border-spacing: 0; width: 90%; margin: 0 auto 32px auto; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 12px #0002; }}
        th, td {{ border: none; padding: 10px 14px; text-align: left; }}
        th {{ background: #3949ab; color: #fff; font-size: 1.05em; }}
        tr:nth-child(even) {{ background: #f4f6fb; }}
        tr:nth-child(odd) {{ background: #e8eaf6; }}
        tr:hover {{ background: #d1c4e9; }}
        .pass {{ background: #e8f5e9 !important; color: #388e3c; font-weight: bold; }}
        .fail {{ background: #ffebee !important; color: #c62828; font-weight: bold; }}
        .info {{ background: #e3f2fd !important; color: #1565c0; font-weight: bold; }}
        td.status-cell {{ text-align: center; font-size: 1.05em; }}
        .footer {{ text-align: center; color: #888; font-size: 0.95em; margin-bottom: 24px; padding-top: 4px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1 style="margin-bottom: 0.2em;">RTL Automation — Batch Run Summary</h1>
        <div>Generated: {now}</div>
    </div>
    <div class="badge-container">
        <span class="overall-badge {overall_class}">{overall_icon} Batch {overall}</span>
    </div>
    <div class="summary-bar">
        <span class="total">Test Cases: {total_tc}</span>
        <span class="passed">Passed: {pass_count}</span>
        <span class="failed">Failed: {fail_count}</span>
        {not_run_row}
    </div>
    <table>
        <tr>
            <th>Test Case</th>
            <th>Started</th>
            <th style="text-align:center">Total Steps</th>
            <th style="text-align:center">Passed</th>
            <th style="text-align:center">Failed</th>
            <th style="text-align:center">Result</th>
        </tr>
{rows_html}
    </table>
    <div class="footer">Click a test case name to open its individual detailed report.</div>
</body>
</html>'''

    out = results_path / 'batch_summary.html'
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'✅ Batch summary report saved to: {out}')
    return str(out)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: generate_batch_report.py <run_tests.txt> <results_dir>")
        sys.exit(1)
    generate_summary(sys.argv[1], sys.argv[2])
