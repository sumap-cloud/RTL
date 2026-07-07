"""
Screen_identifier.py
---------------------
Identifies the current SCO screen by matching live UI identifiers against
cached JSON screen definitions stored in ScreenCache/.

Usage:
    from Components.Screen_identifier import identify_screen, dump_and_cache

    screen = identify_screen(win)
    # Returns e.g. "sale_mode", "welcome_screen", "loyalty_prompt", "unknown"

    # During live-build: dump unknown screen and save as new cache
    dump_and_cache(win, "my_new_screen")

Screen Cache files live at:
    Components/ScreenCache/<screen_name>.json

Each JSON has:
    key_identifiers   — auto_ids that MUST be present (all must match)
    absent_identifiers — auto_ids that MUST be absent (none must be present)

Priority: more specific screens (more key_identifiers) are checked first.
"""

import json
import time
from pathlib import Path

CACHE_DIR = Path(__file__).parent / "ScreenCache"

_screen_cache = {}  # name -> dict (lazy-loaded)


def _load_all():
    """Load all JSON screen definitions from ScreenCache/ into memory."""
    global _screen_cache
    if _screen_cache:
        return
    for f in sorted(CACHE_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            name = data.get("screen_name", f.stem)
            _screen_cache[name] = data
        except Exception:
            pass


def _get_visible_ids(win):
    """Return a set of auto_ids currently visible on the SCO window."""
    ids = set()
    try:
        for c in win.descendants():
            try:
                if c.is_visible():
                    aid = c.element_info.automation_id
                    if aid:
                        ids.add(aid)
            except Exception:
                pass
    except Exception:
        pass
    return ids


def identify_screen(win, verbose=False):
    """
    Identify the current SCO screen.

    Args:
        win:     pywinauto WindowSpecification for NCR NEXTGENUI.
        verbose: If True, prints match details to stdout.

    Returns:
        str: screen_name from the best-matching cache entry, or "unknown".
    """
    _load_all()
    visible_ids = _get_visible_ids(win)

    # Sort candidates: prefer those with more key_identifiers (more specific first)
    candidates = sorted(
        _screen_cache.values(),
        key=lambda d: len(d.get("key_identifiers", [])),
        reverse=True,
    )

    for definition in candidates:
        name = definition.get("screen_name", "?")
        key_ids = [i["auto_id"] for i in definition.get("key_identifiers", [])]
        absent_ids = [i["auto_id"] for i in definition.get("absent_identifiers", [])]

        # All key identifiers must be present
        keys_present = all(k in visible_ids for k in key_ids)
        # No absent identifier must be present
        none_absent = all(a not in visible_ids for a in absent_ids)

        if keys_present and none_absent:
            if verbose:
                print(f"[Screen_identifier] Matched: {name!r}  (keys={key_ids})")
            return name

    if verbose:
        print(f"[Screen_identifier] Unknown screen. Visible IDs: {sorted(visible_ids)}")
    return "unknown"


def dump_screen(win):
    """
    Dump all visible identifiers from the current screen.

    Returns:
        list[dict]: Each dict has keys: auto_id, control_type, text, enabled.
    """
    items = []
    try:
        for c in win.descendants():
            try:
                if c.is_visible():
                    r = c.rectangle()
                    if r.left == 0 and r.right == 0:
                        continue
                    aid = c.element_info.automation_id
                    txt = c.window_text().strip()
                    ct = c.element_info.control_type
                    if (aid or txt) and len(txt) < 100 and ct in (
                        "Text", "Button", "Pane", "Edit"
                    ):
                        items.append({
                            "auto_id": aid,
                            "control_type": ct,
                            "text": txt,
                            "enabled": c.is_enabled(),
                        })
            except Exception:
                pass
    except Exception:
        pass
    return items


def dump_and_cache(win, screen_name):
    """
    Dump the current screen's identifiers and save as a new ScreenCache JSON.
    Use during live-build when an unrecognised screen is encountered.

    Args:
        win:         pywinauto WindowSpecification.
        screen_name: Name to save the cache file as (e.g. "my_new_screen").

    Returns:
        Path to the saved JSON file.
    """
    items = dump_screen(win)

    # Print for developer reference
    print(f"\n=== SCREEN DUMP: {screen_name} ===")
    for item in items:
        print(
            f"  [{item['control_type']}] id={item['auto_id']!r} "
            f"txt={item['text']!r} en={item['enabled']}"
        )

    # Build a skeleton cache JSON — developer should review and trim
    skeleton = {
        "screen_name": screen_name,
        "description": f"Auto-captured screen: {screen_name}",
        "key_identifiers": [
            {"auto_id": i["auto_id"], "control_type": i["control_type"]}
            for i in items
            if i["auto_id"] and i["control_type"] in ("Button", "Text")
        ][:6],  # take first 6 as candidates — trim manually
        "absent_identifiers": [],
        "sample_texts": {
            i["auto_id"]: i["text"]
            for i in items
            if i["auto_id"] and i["text"]
        },
        "_raw_dump": items,
    }

    out_path = CACHE_DIR / f"{screen_name}.json"
    out_path.write_text(
        json.dumps(skeleton, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[Screen_identifier] Saved cache: {out_path}")

    # Reload cache
    global _screen_cache
    _screen_cache = {}
    _load_all()

    return out_path


def wait_for_screen(win, expected_screen, timeout=15, poll=0.5):
    """
    Wait until the current screen matches expected_screen.

    Args:
        win:             pywinauto WindowSpecification.
        expected_screen: Screen name to wait for (e.g. "sale_mode").
        timeout:         Max seconds to wait.
        poll:            Polling interval in seconds.

    Returns:
        bool: True if screen matched within timeout, False otherwise.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        current = identify_screen(win)
        if current == expected_screen:
            return True
        time.sleep(poll)
    return False
