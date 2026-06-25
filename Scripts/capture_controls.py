"""
capture_controls.py
-------------------
Utility to capture ALL control identifiers from the currently active
SCO (NCR NEXTGENUI) or POS (R10PosClient) window and save to a file.

HOW TO USE:
  1. Open the screen whose controls you want to capture.
  2. Run this script:
       python capture_controls.py
  The script auto-detects SCO or POS window.

  To force a specific window, pass an argument:
       python capture_controls.py sco    <- captures NCR NEXTGENUI (SCO)
       python capture_controls.py pos    <- captures R10PosClient (POS)

OUTPUT:
  Saved to: Scripts\SCANPOS\captured_controls_<SCREEN_NAME>_<TIMESTAMP>.txt
"""

import sys
import io
import os
from datetime import datetime
from pathlib import Path
from contextlib import redirect_stdout

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
current_file_path = Path(__file__).resolve()
script_dir = current_file_path.parent
output_dir = script_dir / "SCANPOS"
output_dir.mkdir(parents=True, exist_ok=True)

try:
    from pywinauto import Application
except ImportError:
    print("❌ pywinauto not found. Make sure you're running from the project venv.")
    sys.exit(1)

WINDOW_CONFIGS = {
    "sco": {
        "title_re": ".*NCR NEXTGENUI.*",
        "label": "SCO_NCR_NEXTGENUI",
    },
    "pos": {
        "title_re": ".*R10PosClient.*",
        "label": "POS_R10PosClient",
    },
}


def capture(target="auto"):
    """
    Connect to the target window and dump all control identifiers.

    Args:
        target (str): 'sco', 'pos', or 'auto' (tries SCO first, then POS).
    """
    win = None
    label = None

    if target == "auto":
        candidates = ["sco", "pos"]
    else:
        candidates = [target]

    for key in candidates:
        cfg = WINDOW_CONFIGS[key]
        print(f"🔍 Trying to connect to '{cfg['label']}' (title_re: {cfg['title_re']})...")
        try:
            app = Application(backend="uia").connect(
                title_re=cfg["title_re"], timeout=10
            )
            win = app.window(title_re=cfg["title_re"])
            win.set_focus()
            label = cfg["label"]
            print(f"✅ Connected to: {label}")
            break
        except Exception as e:
            print(f"  ⚠️ Not found: {e}")
            continue

    if win is None:
        print("\n❌ Could not connect to any known window.")
        print("   Make sure the SCO (NCR NEXTGENUI) or POS (R10PosClient) is running and visible.")
        sys.exit(1)

    # Build output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_filename = f"captured_controls_{label}_{timestamp}.txt"
    out_path = output_dir / out_filename

    lines = []
    lines.append("=" * 60)
    lines.append("CONTROL IDENTIFIERS CAPTURE")
    lines.append("=" * 60)
    lines.append(f"Window  : {label}")
    lines.append(f"Title   : {win.window_text()}")
    lines.append(f"Class   : {win.class_name()}")
    lines.append(f"Captured: {datetime.now().isoformat()}")
    lines.append("=" * 60)
    lines.append("")

    print("📋 Capturing control identifiers (this may take a few seconds)...")
    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            win.print_control_identifiers(depth=None)
        lines.append(buf.getvalue())
    except Exception as e:
        lines.append(f"[ERROR during capture: {e}]")
        print(f"⚠️ Partial capture: {e}")

    lines.append("=" * 60)
    lines.append("END OF CAPTURE")
    lines.append("=" * 60)

    content = "\n".join(lines)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"\n✅ Done! Control identifiers saved to:")
    print(f"   {out_path}")
    print(f"\n📌 Quick reference — child_window syntax examples:")
    # Print first 30 child_window lines as quick reference
    quick = [l for l in content.splitlines() if "child_window(" in l][:30]
    for q in quick:
        print(f"   {q.strip()}")
    if len([l for l in content.splitlines() if "child_window(" in l]) > 30:
        print(f"   ... (see full file for all {len([l for l in content.splitlines() if 'child_window(' in l])} entries)")

    return str(out_path)


if __name__ == "__main__":
    target = "auto"
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in WINDOW_CONFIGS:
            target = arg
        else:
            print(f"⚠️ Unknown target '{arg}'. Use 'sco' or 'pos'. Falling back to auto-detect.")

    print("=" * 60)
    print("  NCR SCO / POS Control Identifier Capture Utility")
    print("=" * 60)
    print(f"  Mode   : {target}")
    print(f"  Output : {output_dir}")
    print("=" * 60)
    capture(target)
