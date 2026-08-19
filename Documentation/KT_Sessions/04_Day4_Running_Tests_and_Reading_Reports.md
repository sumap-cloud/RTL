# Day 4 — Running Tests & Reading Reports

**Session goal:** everyone can run a single test, run a whole suite, and read
the output well enough to say *what went wrong and where*.

**After this session they will be able to:**

- Run one test case and a full suite, unattended.
- Open and interpret the HTML report and the batch summary.
- Find the console log for a specific test in a batch.
- Do first-line triage on a failure without asking for help.

---

## Run sheet

| Time | Segment |
|---|---|
| 0–3 min | Recap Day 3 |
| 3–8 min | Before you run anything: the pre-flight checklist |
| 8–17 min | **Live:** running a single test |
| 17–27 min | **Live:** running a whole suite |
| 27–40 min | Reading the reports, logs and summaries |
| 40–45 min | Recap + homework |
| 45–60 min | Q&A |

---

## Segment 1 — Pre-flight checklist (5 min)

> "Most 'the automation is broken' reports are actually 'the lane wasn't
> ready'. Go through this list every single time. It takes thirty seconds and
> it saves an hour."

| # | Check | How |
|---|---|---|
| 1 | SCO is on the **Welcome** screen | Look at the lane |
| 2 | EFT simulator is running | `Get-Process MultiSimulator, RemedyEFTPOSServer -ErrorAction SilentlyContinue` — **if these are not running, no card payment will ever complete** |
| 3 | Nobody else is using the lane | Ask / check the booking |
| 4 | You are in the project root | `cd "C:\Pywin\RTL Automation"` |
| 5 | You are using the venv Python | `.\Scripts\python.exe` — not plain `python` |
| 6 | The CSV is not open in Excel | Close it |
| 7 | The data is intact | `Select-String Scripts\SCO_Workspace\Data\RegressionSale.csv -Pattern "E\+\d"` returns nothing |

Say the rule out loud twice:

> **"Always run from `C:\Pywin\RTL Automation`, always with `.\Scripts\python.exe`."**

---

## Segment 2 — Running a single test (9 min)

This is what you will do 90% of the time while developing or debugging.

```powershell
cd "C:\Pywin\RTL Automation"
.\Scripts\python.exe Scripts\SCO_Workspace\Testing\Sanity\TC_001_SCO_Registeredcardlessthan1000points.py
```

**Do this live and narrate the console as it scrolls.** Point out:

```
✅ Found value: 9310072000282        <- the CSV lookup worked
✅ Connected to NCR NEXTGENUI
🛒 Scanning item 9310072000282 ...
✅ Loyalty card accepted — Registered
💳 Clicking Tender2 (Card) ...
⏳ Waiting for EFT approval (up to 90s) ...
✅ Transaction complete
Report saved to: C:\Pywin\RTL Automation\Scripts\SCO_Workspace\Results\TC_001.html
```

Things to point out while it runs:

- **Do not touch the lane.** The script is moving the mouse and clicking. Any
  human interaction will derail it.
- The EFT wait is **90 seconds** by design, because the simulator can be
  operated manually. A long pause there is normal, not a hang.
- The last line tells you exactly where the report went.

### If you want breakpoints

VS Code already has a debug configuration. `Run and Debug` → pick the
configured test → set breakpoints → step through. `.vscode\launch.json` sets
`cwd` to the project root for you.

There are also VS Code tasks (`Terminal → Run Task`) for the common scripts and
a "Compile-check all regression scripts" task worth knowing about — it catches
syntax errors in seconds without touching the lane.

---

## Segment 3 — Running a whole suite (10 min)

### The easy way — `Run_Suite.bat`

Double-click `Run_Suite.bat` in the project root. You get a menu:

```
   1. Sanity      (11 quick smoke tests - run this first)
   2. Regression  (Supermarket / Metro - full suite)
   3. BigW        (BigW banner)
   4. NZ          (Countdown / New Zealand)
   5. Exit
```

Pick one and walk away. Show the Sanity suite starting, then stop it — you do
not want to spend 40 minutes of the session watching it.

### What the runner actually does

```
  reset the SCO to Welcome
       │
  ┌────▼─────────────────────────────────┐
  │  for each TC_*.py in the suite:      │
  │      run it as its own python.exe    │  (15-minute cap)
  │      capture all console output      │  -> Results\BatchLogs\*.log
  │      find its HTML report            │
  │      read the PASS/FAIL badge        │
  │      RESET THE SCO TO WELCOME  ◄──── always, pass or fail or crash
  └────┬─────────────────────────────────┘
       │
  write BatchSummary_<Suite>_<timestamp>.txt
```

Three points worth dwelling on:

1. **Each test is a separate process.** If one crashes hard, it cannot take the
   others down with it.
2. **The reset between tests is the thing that makes unattended runs
   possible.** Without it, one stuck popup fails every remaining scenario.
   Day 6 covers how the reset escalates to a full SCO restart when clicking is
   not enough.
3. **There is a 15-minute cap per script.** A hung test is killed and recorded
   as `TIMEOUT`, and the batch continues.

### The other runners (know they exist)

| Entry point | Scope |
|---|---|
| `Run_Suite.bat` | **Preferred.** Menu → any of the four suites |
| `Scripts\SCO_Workspace\Testing\<Suite>\run_all_<Suite>.py` | Same thing, from the command line |
| `run_tests.bat` + `run_tests.txt` | Older, Regression only, driven by an editable list of script names. Useful when you want to run a specific subset — edit the list, `#` to comment a line out |

---

## Segment 4 — Reading the output (13 min)

Everything lands in `Scripts\SCO_Workspace\Results\`.

```
Results\
├── TC_001.html                              ← per-test report
├── TC_007_Verify....html
├── TC_001\                                  ← screenshots for that test
│   └── failstep_14.png
├── BatchLogs\
│   └── Sanity_TC_001_20260819_1730.log      ← full console output per test
├── BatchSummary_Sanity_20260819_1730.txt    ← the text summary
└── batch_summary.html                       ← the run_tests.bat summary
```

### 1. The per-test HTML report — open one live

Structure, top to bottom:

- **Header** — the TC_ID and the start time.
- **Badge** — one big green `✅ ... PASSED` or red `❌ ... FAILED`.
- **Summary bar** — Total Steps / Failed Steps / Passed Steps.
- **Step table** — one row per logged step:

| Time | Action | Element | Status | Screenshot |
|---|---|---|---|---|
| 17:31:04.221 | ✅ Scanned item 9310072000282 | | PASS | |
| 17:31:19.882 | ❌ Step 5 — Missing promotions: ['2x points'] | | FAIL | View Screenshot |

Colour code:

| Colour | Status | Meaning |
|---|---|---|
| 🟩 Green | PASS | that check succeeded |
| 🟥 Red | FAIL | that check failed — **and the whole test is FAILED** |
| 🟦 Blue | INFO | noted, no verdict |
| 🟦 Dark navy | SECTION | a heading grouping the steps below it |

Teach the reading technique:

> **"Scroll to the first red row. Not the last — the first. Everything after
> the first failure is usually a consequence of it. Read that row's Action
> text, then click View Screenshot to see what the lane actually looked like at
> that moment."**

Point out that **a failure screenshot is taken automatically** — you do not have
to ask for it. That screenshot is often the whole answer.

### 2. The batch summary text file

```
Batch Summary - Sanity suite - 20260819_1730
======================================================================
Total: 11   Passed: 8   Failed/Other: 3
----------------------------------------------------------------------
[PASS     ] TC_001_SCO_Registeredcardlessthan1000points  (94s, exit=0)
             report: ...\Results\TC_001.html
             log:    ...\Results\BatchLogs\Sanity_TC_001_....log
[FAIL     ] TC_004_SCO_SFCCard  (131s, exit=0)
             report: ...\Results\TC_004.html
             log:    ...\Results\BatchLogs\Sanity_TC_004_....log
[TIMEOUT  ] TC_009_SCO_SDCCard  (900s, exit=TIMEOUT)
```

The status vocabulary — explain each, they will see all of them:

| Status | What it means | Where to look first |
|---|---|---|
| `PASS` | Report badge says PASSED | nowhere |
| `FAIL` | Report badge says FAILED | the HTML report, first red row |
| `TIMEOUT` | Ran past 15 minutes and was killed | the `.log` file — where did it stop printing? |
| `NO_REPORT` | The script died before it could write a report | the `.log` file — usually an import error or a crash at startup |
| `UNKNOWN` | A report exists but has no badge | the report; usually truncated |

> "`NO_REPORT` almost always means the script crashed before `logger.save()` —
> so go straight to the `.log` file, not the reports folder."

### 3. The BatchLogs `.log` files

Everything the script printed — including the full Python traceback if it
crashed. This is where you go for `TIMEOUT` and `NO_REPORT`.

```powershell
# the most recent log
Get-ChildItem Scripts\SCO_Workspace\Results\BatchLogs\*.log |
    Sort-Object LastWriteTime | Select-Object -Last 1 | Get-Content | Select-Object -Last 60
```

### 4. `batch_summary.html` (from `run_tests.bat`)

`Scripts\generate_batch_report.py` builds an HTML index of the run with a link
to each individual report. It opens automatically at the end of
`run_tests.bat`. Convenient for sharing.

### Honest assessment — say this

> "The reporting is functional, not polished. You get a clear per-test report
> with screenshots, and a clear summary of which tests passed. What it does not
> give you yet is trend history across runs, or a single dashboard across all
> four banners. If you want that, the badge and step counts are already in a
> predictable format in the HTML, so an aggregator is a small piece of work.
> That is a genuine, well-scoped first improvement for this team to own."

---

## Segment 5 — First-line triage (part of Segment 4's time, ~4 min)

Give them this decision tree. It is Day 6 in miniature and it makes them
self-sufficient immediately.

```
Test failed
    │
    ├─ Is there an HTML report?
    │      NO  -> read Results\BatchLogs\<suite>_<tc>_*.log
    │             Python traceback?  -> code/import problem
    │             Stopped mid-way?   -> the lane hung; check the SCO screen
    │
    └─ YES -> open it, find the FIRST red row
              │
              ├─ "No matching record found" / used a fallback
              │        -> data problem: three-key lookup (Day 3)
              │
              ├─ "Missing promotions: [...]"
              │        -> the campaign or the card is not configured as expected
              │           (check the docstring's Pre-requisite section)
              │
              ├─ "could not find control ..." / timeout waiting for a button
              │        -> the UI changed, or a popup was in the way.
              │           Look at the auto-captured screenshot.
              │
              └─ EagleEye verification failed
                       -> the transaction happened but the loyalty engine did
                          not record what we expected. Check
                          C:\Retalix\EEAdapter\Logs\
```

---

## Segment 6 — Recap & homework (5 min)

1. Pre-flight checklist every time. **EFT simulator must be running.**
2. Run from the project root with `.\Scripts\python.exe`.
3. `Run_Suite.bat` for a whole banner; a direct call for one test.
4. The runner resets the SCO between every test — that is what makes it
   unattended.
5. Report → **first red row** → screenshot. `NO_REPORT`/`TIMEOUT` → the `.log`.

**Homework:**

- Run the **Sanity** suite end to end on the lane.
- Open the batch summary and every HTML report it produced.
- For each failure, write one sentence: *what* failed and *at which step*.
  Bring that list to Day 6 — we will triage them together.

---

## Q&A bank

**Q: Can I use the machine while a suite is running?**
A: No. The scripts move the real mouse and send real clicks to the lane. Even
moving a window can break a run. Start it and leave it.

**Q: How long does a full suite take?**
A: Roughly 1.5–3 minutes per scenario including the reset between tests, so
Sanity is about 20–30 minutes and a full Regression run is a couple of hours.
Budget for the 15-minute-per-script cap in the worst case.

**Q: A test passed but I don't believe it. How do I check?**
A: Open the report and read the steps, not just the badge. Look for blue INFO
rows saying something was *not* detected — those do not fail the test by
design. Also check the console/log for `⚠️ No matching record`, which means it
ran on fallback data.

**Q: Can I run just three specific tests?**
A: Yes — use `run_tests.txt`. Comment out with `#` everything you do not want
and run `run_tests.bat`. (Note it only looks in the Regression folder.)
Alternatively run each script directly, one at a time.

**Q: Where do screenshots come from and can I add my own?**
A: Failures capture one automatically. You can force one anywhere with
`logger.take_screenshot("some_name")`. They land in
`Results\<TC_ID>\<name>.png` and the report links to them.

**Q: Should reports be committed to git?**
A: No — `Results\` is gitignored. Reports are evidence of one run on one
machine. If you need to keep one, copy it out to a share or attach it to the
test-management tool.

**Q: The run stopped and the SCO is stuck on a popup. What now?**
A: Run the recovery utility directly:
`.\Scripts\python.exe Scripts\SCO_Workspace\Components\Hard_reset_SCO.py`.
It tries to click its way back to Welcome and, failing that, restarts the SCO
application and logs the lane back in. Full detail on Day 6.

**Q: Why is the same test's report overwritten each run?**
A: The report filename is derived from `TC_ID`, so a re-run replaces it. The
per-run history lives in `BatchLogs\` and in the timestamped
`BatchSummary_*.txt` files. If you need to keep an HTML report, copy it before
re-running.
