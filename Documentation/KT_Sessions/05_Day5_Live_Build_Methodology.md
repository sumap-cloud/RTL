# Day 5 — The Live-Build Methodology (how to write a new test)

**Session goal:** the team can add a brand-new test case to this suite, using
the same working method that produced the existing ninety-seven.

**After this session they will be able to:**

- Discover the automation id of any control on the SCO.
- Use the dump / cache tooling to work on a single-screen terminal.
- Follow the live-build loop to turn a written scenario into a working script.
- Create a new test case end to end: CSV row, script, verification, report.

> This is the most important session in the pack. Days 1–4 make the team
> *users* of the suite. Day 5 makes them *owners* of it.

---

## Run sheet

| Time | Segment |
|---|---|
| 0–3 min | Recap Day 4, review their Sanity results briefly |
| 3–10 min | The problem: you cannot see what you are automating |
| 10–20 min | The discovery toolkit — `inspect.exe`, `dump_screen`, ScreenCache |
| 20–33 min | **The live-build loop** — the actual working method |
| 33–42 min | **Live:** create a new test case from scratch |
| 42–45 min | Recap + homework |
| 45–60 min | Q&A |

---

## Segment 1 — The core problem (7 min)

Restate the constraint from Day 1, because now it has consequences:

> "On a two-screen POS you put the application on one screen and your editor on
> the other. You can see the button and write the code that clicks it at the
> same time. On the SCO there is **one screen**, and the application owns it.
> While you are looking at the code, you cannot see the lane. While the script
> is running, you cannot see the code.
>
> On top of that, the SCO is not a passive form. It is a live retail terminal
> talking to a real loyalty engine. Prompts appear because of the *state of the
> card*, not because of what you clicked. The same script can see a different
> screen tomorrow because the card's point balance moved."

And then the extra layer:

> "Several scenarios need a **simulator**: the EFT simulator approves the card
> payment, and some flows need a barcode or a number typed into a separate
> simulator window. So the automation is not driving one application — it is
> driving a lane plus its simulators, in the right order."

Set the expectation honestly:

> "You will not write one of these scripts in one pass. Nobody does. The method
> below is designed around that."

---

## Segment 2 — The discovery toolkit (10 min)

### Tool 1 — `inspect.exe` (Windows SDK)

The official Microsoft UI Automation inspector. Point it at any control and it
shows the properties our code uses.

```
C:\Program Files (x86)\Windows Kits\10\bin\<version>\x64\inspect.exe
```

Demo it live: hover over the SCO Pay button and read out:

| Property | Example | We use it as |
|---|---|---|
| **AutomationId** | `PayButton` | `auto_id=` — **this is the one that matters** |
| ControlType | `Button` | `control_type="Button"` |
| Name | `Pay` | `title=` (fallback when there is no AutomationId) |

Which becomes:

```python
win.child_window(auto_id="PayButton", control_type="Button").click_input()
```

**Caveat to state clearly:** `inspect.exe` needs the SCO visible, and it can
steal focus. It is excellent for a single lookup, awkward for exploring a whole
screen. Which is why we have tool 2.

### Tool 2 — `dump_screen()` — the workhorse

```python
from Components.Screen_identifier import dump_screen
for item in dump_screen(win):
    print(item)
```

It walks every visible control and prints `auto_id`, `control_type`, `text` and
`enabled`. **Run it, then read the output in your editor.** That is how you
"see" a screen you cannot look at.

Show a real one-liner they can keep:

```powershell
cd "C:\Pywin\RTL Automation"
.\Scripts\python.exe -c "import sys;sys.path.insert(0,r'Scripts\SCO_Workspace');from pywinauto import Application;from Components.Screen_identifier import dump_screen;w=Application(backend='uia').connect(title_re='.*NCR NEXTGENUI.*',timeout=10).window(title_re='.*NCR NEXTGENUI.*');[print(i) for i in dump_screen(w)]"
```

> "Put the SCO on the screen you care about, run that, and read the list. That
> single command is how most of this project was written."

### Tool 3 — `dump_and_cache()` and the ScreenCache

Once you know a screen, fingerprint it so the code can recognise it later:

```python
from Components.Screen_identifier import dump_and_cache
dump_and_cache(win, "my_new_screen")     # writes Components/ScreenCache/my_new_screen.json
```

Then **trim the JSON by hand**: keep only the two or three `key_identifiers`
that are genuinely unique to that screen, and add `absent_identifiers` for
anything that must *not* be present.

> "A fingerprint with fifteen identifiers is brittle — one UI tweak breaks it.
> Two or three well-chosen ones survive releases. Trimming is not optional."

### Tool 4 — the domain knowledge file

`Scripts\SCO_Workspace\sco-automation.instructions.md`.

> "Every fact in that file cost somebody an hour. For example: on this SCO,
> `Tender1` is Cash and it is **blocked** — card payment is always `Tender2`.
> And popup buttons report `is_enabled() == False` even when they are perfectly
> clickable, so you must use `exists()` and click anyway. You would never guess
> either of those. **When you learn something new about the SCO, add it to that
> file in the same commit.**"

---

## Segment 3 — The live-build loop (13 min)

This is the method. Present it as a named process, because it is one.

```
   ┌──────────────────────────────────────────────────────────┐
   │ 0. WRITE THE SCENARIO IN ENGLISH FIRST                    │
   │    numbered steps, and the expected result of each        │
   └───────────────┬──────────────────────────────────────────┘
                   ▼
   ┌──────────────────────────────────────────────────────────┐
   │ 1. GET THE LANE TO A KNOWN STATE (Welcome)                │
   └───────────────┬──────────────────────────────────────────┘
                   ▼
   ┌──────────────────────────────────────────────────────────┐
   │ 2. EXECUTE ONE STEP — and only one                        │
   │    reuse an existing component if there is one            │
   └───────────────┬──────────────────────────────────────────┘
                   ▼
   ┌──────────────────────────────────────────────────────────┐
   │ 3. DUMP THE SCREEN. What actually happened?               │
   │    Expected screen?  -> record the auto_ids, go to 2      │
   │    Unexpected popup? -> that is a real finding. Handle it │
   │    Needs data (card / article number)? -> supply it AND   │
   │       write it into RegressionSale.csv immediately        │
   └───────────────┬──────────────────────────────────────────┘
                   ▼
   ┌──────────────────────────────────────────────────────────┐
   │ 4. STEP WORKS -> append it to the script file             │
   │    Repeat 2-4 until the scenario is complete              │
   └───────────────┬──────────────────────────────────────────┘
                   ▼
   ┌──────────────────────────────────────────────────────────┐
   │ 5. RUN THE WHOLE SCRIPT FROM WELCOME, TWICE               │
   │    Once proves it works. Twice proves it is repeatable.   │
   └──────────────────────────────────────────────────────────┘
```

### Why step by step, and never all at once

Say this from experience:

> "If you write the whole script and then run it, and it fails at step 6, you
> do not know whether step 6 is wrong or whether step 4 left the lane in a
> state step 6 didn't expect. You have to unwind the whole transaction and
> start again — which on a live lane means voiding a basket and waiting.
>
> Building one step at a time means when something surprises you, you know
> exactly which action caused it, and the lane is already sitting on the screen
> you need to inspect."

### Rule: data goes into the CSV *the moment* you use it

> "The instant you type a card number or an article number to make a step work,
> put it in `RegressionSale.csv` — before you carry on. If you leave it until
> the end you will have twelve numbers, no memory of which belonged to which
> step, and you will be back on the lane re-deriving them. This is the single
> discipline that made the ten-day build possible."

### Using an AI assistant for this loop

Be straightforward about it — it is a genuine engineering technique, not a
confession:

> "I built most of this with an AI coding assistant in what I call **live-build
> mode**. The pattern is:
>
> 1. Give the assistant the written scenario and the existing component list.
> 2. Ask it to perform **one step at a time** against the live lane, and to
>    dump the screen after each one.
> 3. When it needs data it does not have — a card number, an article — supply
>    it, and have it record that value in the CSV straight away.
> 4. Only once a step is proven live does it get written into the script file.
>
> Two things make this work and both are non-negotiable. First, **the assistant
> must never guess an automation id** — every id must come from a live dump or
> from the existing verified components. Second, **nothing goes into the script
> until it has been observed working on the lane.** With those two rules you
> get scripts made only of verified facts. Without them you get plausible code
> that has never worked."

If the team will use the same approach, point them at
`sco-automation.instructions.md` — it is written to be loaded automatically as
context for anything under `Scripts/SCO_Workspace/**`, which is what keeps an
assistant honest about this SCO's quirks.

### Handling the simulators

- **EFT simulator** (`RemedyEFTPOSServer` + `MultiSimulator.exe`) must be
  **running** — it auto-approves the card payment. ⚠️ Never call
  `ensure_EFTSimulator_closed()` or `ensure_services_stopped()` before a
  payment; there are commented-out calls in `Add_item.py` left over from an
  earlier design — leave them commented.
- The EFT approval wait is **90 seconds** on purpose (`_EFT_APPROVAL_TIMEOUT`).
  Do not reduce it below 60 — the simulator may be driven manually.
- Where a scenario needs a number typed into a simulator window, the flow is:
  focus the simulator window → type → return focus to the SCO → continue. Treat
  the simulator as just another window pywinauto can connect to.

---

## Segment 4 — Live: build a new test case (9 min)

Do this on screen. Keep it deliberately simple — the *process* is the lesson.

### Step 1 — Write the scenario in the docstring first

Create `Testing\Regression\TC_099_VerifyPointsForSingleItem.py`:

```python
"""
TC_099 — Points earned for a single eligible item

Scenario:
    Scan one eligible article, scan a registered EDR card at the tender
    prompt, and confirm points are collected and the transaction settles in
    EagleEye.

Pre-requisite:
    Registered EDR card, active. EFT MultiSimulator running.

Steps automated:
    1. Login to SCO.
    2. Scan the article.
    3. Scan the loyalty card at the tender prompt.
    4. Read the points collected.
    5. Complete the transaction by card.
    6. Verify EagleEye wallet open + settle.

Data source:
    Local CSV: Data/RegressionSale.csv — Banner="SM", TC_ID="TC_099", Iteration=1.
"""
```

### Step 2 — Add the CSV row *first*

Open `Data\RegressionSale.csv` in VS Code, copy an existing SM row, and change:

```
SM,LPR,New,TC_099,1,9310072000282,,,9353109614779,WRC,ACTIVE,,,,,,,,,
```

> "Data before code. Now the script has something to read from the moment it
> exists."

### Step 3 — The boilerplate

```python
import sys
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from Components.Login_POS import login_pos
from Components.Add_item import add_item
from Components.Scan_loyalty_tenderprompt import scan_loyalty_tenderprompt
from Components.Promotion_details import get_points_collected
from Components.Complete_transaction import complete_transaction
from Components.Verify_EagleEye_logs import verify_eagleeye_logs
from Components.Read_csv import get_csv_value
from Components.report import logger

TC_ID     = "TC_099"
BANNER    = "SM"
ITERATION = 1

logger.set_tc_id(TC_ID)


def _get_value(column, fallback):
    try:
        val = get_csv_value("saledata", BANNER, TC_ID, ITERATION, column)
        if val and not val.startswith("Error") and val != "No matching record found.":
            return val
    except Exception:
        pass
    return fallback


EAN_LIST  = _get_value("Item_EAN", "9310072000282")
CARD_CODE = _get_value("Card_number", "9353109614779")
```

### Step 4 — Add one step, run it, dump, repeat

Add only this, and run the file:

```python
try:
    if not login_pos():
        raise RuntimeError("login_pos failed — aborting test.")
    logger.log("✅ Step 1 — connected to the SCO.", status="pass")
```

It runs, it connects, it stops. Dump the screen. Confirm you are on Welcome.
**Then** add step 2 and run again. And so on.

### Step 5 — Close it out properly

```python
except Exception as e:
    logger.log(f"❌ Unexpected error in TC_099: {e}", status="fail")
    logger.take_screenshot("TC_099_Unexpected_Error")

finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
```

### Step 6 — Register it

- Add the filename to `run_tests.txt` if it should be in the list-driven run.
  (`run_all_*.py` and `Run_Suite.bat` pick up any `TC_*.py` automatically.)
- Run the three-key health check from Day 3 and confirm it resolves.
- Run the script twice, cleanly, from Welcome.
- Commit the script **and** the CSV row **and** any new ScreenCache JSON
  together, in one commit.

---

## Segment 5 — Recap & homework (3 min)

1. You cannot see the SCO while you code — so **dump, then read**.
2. `inspect.exe` for one control, `dump_screen()` for a whole screen,
   `dump_and_cache()` to teach the code a new screen.
3. **One step at a time. Never write the whole script blind.**
4. **Data into the CSV the moment you use it.**
5. Never invent an automation id. Live dump or existing verified component only.
6. Prove it twice from Welcome before you commit.

**Homework:**

- Run the `dump_screen` one-liner on three different SCO screens (Welcome,
  basket with an item, payment) and save the output.
- Write the docstring — scenario, pre-requisites, numbered steps — for one test
  case you would like to add. No code. We will review these on Day 6.

---

## Q&A bank

**Q: How long does it take to build one new test?**
A: A simple one that reuses existing components: an hour or two, most of it
waiting on the lane. One that hits an unhandled popup or needs a new component:
most of a day. Be honest about that in planning — the lane time, not the
typing, is the cost.

**Q: What if the component I need doesn't exist?**
A: Write it in `Components\`, not in your test script. Give it one job, a clear
name, and make it return `True`/`False` rather than raising. Then use it from
the script. If you put UI code in the test script it will be copy-pasted into
the next twenty scripts and you will have to fix it twenty times.

**Q: The same script passes sometimes and fails other times. Why?**
A: Almost always live state. Point balances move, offers get consumed, campaign
windows expire. That is why prompts that depend on balance — like Exciting News
— are logged as `info` and not `fail`. If a genuinely deterministic step is
flaky, it is usually a missing wait or an unhandled popup, and the auto-captured
screenshot will show you which.

**Q: Do we have to use an AI assistant to build these?**
A: No. The live-build loop is a manual method that happens to work very well
with one. What matters is the discipline: one step, dump, verify, record the
data, commit only what you have seen work.

**Q: Can we record and replay instead, like a macro recorder?**
A: Not usefully. Record-and-replay produces coordinate clicks that break the
moment the layout shifts, and it cannot make assertions. Everything here
targets controls by automation id, which survives layout changes and lets us
actually verify values.

**Q: How do I know if a popup is a bug or expected behaviour?**
A: Check `sco-automation.instructions.md` first — the common ones are
documented, including the counter-intuitive one where scanning a loyalty card
in sale mode is *also* read as an unknown product and raises "Assistance
Needed". If it is not documented, it is a finding: raise it with the business
before you code around it.

**Q: What is the `Steps\` folder in `Testing\`?**
A: Leftover scaffolding from an early attempt to split one scenario into
separate step files. The files are empty. Ignore it — and see Day 6, where it
is on the cleanup list.
