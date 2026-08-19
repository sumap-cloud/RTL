# Day 6 — Failures, Maintenance & Handover

**Session goal:** the team knows exactly what to do when a test fails, what is
dependable and what is not, what is still outstanding, and formally takes
ownership.

**After this session they will be able to:**

- Triage any failure to one of five root causes.
- Recover a stuck lane, every time, including a full SCO restart.
- Maintain the suite: data changes, UI changes, new releases.
- Name the known gaps and the recommended order of work.

> Be candid in this session. A handover where the outgoing owner names the weak
> spots is far more credible than one where everything is claimed to work.

---

## Run sheet

| Time | Segment |
|---|---|
| 0–3 min | Recap Day 5; collect their homework docstrings |
| 3–12 min | Failure taxonomy — the five root causes |
| 12–22 min | Recovery: how the lane always gets back to Welcome |
| 22–30 min | What is solid, what is fragile — the honest list |
| 30–38 min | Maintenance playbook + known gaps and backlog |
| 38–45 min | Formal handover checklist + close |
| 45–60 min | Q&A |

---

## Segment 1 — The five root causes (9 min)

> "Every failure you will ever see in this suite is one of five things. Learn
> to sort a failure into the right bucket in under two minutes and you have
> most of the job."

### 1. Data problem — the CSV row was not found or is wrong

**Looks like:** the report runs but the values are wrong; console shows
`⚠️ No matching record`; the test uses a `<FILL_...>` placeholder.

**Fix:** the three-key lookup (Day 3). Check `Banner`, `TC_ID`, `Iteration`
match the CSV exactly, including capitals. Then check the card number is intact
(no `E+12`).

**This is the most common cause and the cheapest to fix.**

### 2. Environment problem — the lane or its simulators are not ready

**Looks like:** `login_pos failed`; the payment never completes; the script
hangs on the tender screen.

**Fix:**

```powershell
Get-Process MultiSimulator, RemedyEFTPOSServer -ErrorAction SilentlyContinue
```

If the EFT simulator is not running, **nothing will ever pay**. Also confirm
the lane is at Welcome and that nobody else is on it.

### 3. State problem — the lane was left dirty by the previous test

**Looks like:** the test fails immediately, or on step 1–2, with a screen that
has nothing to do with the scenario.

**Fix:** run the recovery utility (Segment 2), then re-run the single test on
its own. If it passes in isolation, it was a state problem, not a test problem.

### 4. Business-configuration problem — the campaign or card isn't set up

**Looks like:** `Missing promotions: ['...']`; no Exciting News prompt; points
are zero; an offer never appears.

**Fix:** this is usually **not** a code problem. Read the **Pre-requisite**
section of the script's docstring — it says what must be configured. Then check
the card's actual state and the campaign's date window in EagleEye. Raise it
with the business/config team.

> "This one matters for your credibility. If you report every campaign
> mis-configuration as an automation defect, people stop trusting the reports.
> Check the pre-requisite before you raise a bug."

### 5. UI problem — the SCO application changed

**Looks like:** `could not find control ...`; a timeout waiting for a button
that used to exist; a new popup in the auto-captured screenshot.

**Fix:** dump the screen (Day 5), find the new automation id, update the
**component** (not the test script), and add the finding to
`sco-automation.instructions.md`.

### The triage card — hand this out

```
FAILURE
  │
  ├─ no HTML report?            -> Results\BatchLogs\*.log -> traceback or hang
  │
  └─ open report, FIRST red row
        │
        ├─ "No matching record" / <FILL_>   -> 1. DATA
        ├─ login/pay never completes        -> 2. ENVIRONMENT (simulator!)
        ├─ failed on step 1-2, wrong screen -> 3. STATE (re-run alone)
        ├─ "Missing promotions" / no prompt -> 4. BUSINESS CONFIG (read docstring)
        └─ "could not find control"         -> 5. UI CHANGED (dump + fix component)
```

---

## Segment 2 — Recovery: always getting back to Welcome (10 min)

> "This was the hardest problem in the whole project, and it is the one that
> makes an unattended run possible. If a test dies halfway through a
> transaction, the lane is left on a basket or a payment screen or a popup.
> Every remaining test then fails for a reason that has nothing to do with what
> it is testing."

### Stage 1 — soft reset: `Reset_to_welcome.py`

Clicks its way out. It loops up to 25 times:

1. Identify the current screen (via the ScreenCache fingerprints).
2. If it is Welcome — done.
3. If it is the "Assistance Needed / Cancel Purchase" store-approval popup,
   decline it specifically (it needs a store login, not a plain click).
4. Otherwise click the first recognised recovery control it can find, in
   priority order:
   - **abort the sale**: `CancelAllBtn`, `GS1VoidAllButton`, `GoBackBtn`, …
   - **dismiss a popup**: `ASAOKButton`, `OK_Button`, `No_Button`, …
   - **leave an overlay**: `ExitUNavButton`, `CancelUNavButton`
5. Re-identify and go again.

It always exits 0 and prints either `RESET: SUCCESS` or `RESET: FAILED`.

### Stage 2 — hard reset: `Hard_reset_SCO.py`

**Why it exists — be honest about this:**

> "Clicking is not always enough. There is a store-approval popup that
> regenerates itself indefinitely once the lane is in that state — I proved
> that live. The soft reset declines it correctly, and it comes straight back.
> No amount of clicking fixes it. The only reliable answer is to restart the
> SCO application."

What it does:

```
  Stop  (updated).bat          kill pipeserver, SSCOUI, scotappu, POS shell
        │  wait ~12s
  Start (updated).bat          relaunch pipeserver, SSBPLUS, SSCOUI, scotappu
        │  wait for the NCR NEXTGENUI window (up to 3 min)
  dismiss the launch popup     click OK
        │
  the lane comes up "Lane Closed"
  store login                  click StoreLogin -> operator id -> password
        │
  verify the Welcome screen
```

Run it directly whenever a lane is stuck:

```powershell
cd "C:\Pywin\RTL Automation"
.\Scripts\python.exe Scripts\SCO_Workspace\Components\Hard_reset_SCO.py
```

The batch runner calls this automatically: it runs the soft reset after every
test and escalates to the hard reset only when the soft reset did not report
success.

**Configuration — no code edit required:**

| Environment variable | Default |
|---|---|
| `SCO_LAUNCH_DIR` | `C:\BAU SCO Automation\SCO Application Launch` |
| `SCO_START_BAT` | `Start (updated).bat` |
| `SCO_STOP_BAT` | `Stop (updated).bat` |
| `SCO_STORE_USER` | `ms` |
| `SCO_STORE_PASS` | (as set in `Complete_transaction.py`) |
| `SCO_DISABLE_HARD_RESET` | unset. Set to `1` to keep soft-reset-only behaviour while debugging |

```powershell
$env:SCO_STORE_USER = "yourid"
$env:SCO_STORE_PASS = "yourpassword"
.\Scripts\python.exe Scripts\SCO_Workspace\Components\Hard_reset_SCO.py
```

### ⚠️ Open item — hand this over explicitly

> "The store login after a restart is the one part I could not get to work
> end to end. Logging in with `ms` on the Lane Closed screen was rejected in my
> testing — the screen silently returns to the id prompt with no error. The
> restart itself works, the popup dismissal works, the login screen is reached
> correctly, and the credentials are now overridable by environment variable so
> no code change is needed. **What is needed is a set of store credentials that
> are valid on this lane, confirmed manually first.** I have deliberately
> capped it at two attempts so a real store account cannot be locked out. This
> is the top item on the backlog."

If the login is rejected, the fallback is manual: run the two `.bat` files
yourself, click OK, log the lane in by hand, and restart the batch.

---

## Segment 3 — What is solid and what is not (8 min)

> "I am going to be straight with you about this. This suite was built in
> around ten days against a live system by someone new to the domain. There is
> a solid core that runs reliably, and there is a tail of complex scenarios
> that need attention. Knowing which is which is more useful to you than a
> claim that everything works."

### Tier A — dependable core

Simple, deterministic flows: log in → scan → loyalty → pay → verify EagleEye.
No offer redemption, no timing windows, no OCR.

| Suite | Scenarios |
|---|---|
| **Sanity** | TC_001, TC_003, TC_004, TC_005, TC_006, TC_007, TC_010, TC_011 |
| **Regression** | TC_02, TC_003, TC_005, TC_006, TC_007, TC_09, TC_0011, TC_037, TC_039, TC_049, TC_050 |
| **NZ** | TC_02, TC_003, TC_007, TC_09, TC_050 |

> "These are the ones to run as your daily smoke test, and the ones to use as
> reference when you write something new."

### Tier B — depends on live business configuration

Campaign and offer scenarios: multiplier, continuity, tiered spend, market-day,
open offers, stamp cards. **The automation is sound; whether they pass depends
on the campaign being active and the card being in the right state.** Failures
here are usually root cause 4, not a code defect.

Examples: Regression TC_004, TC_08A, TC_022, TC_038, TC_023, TC_024, and their
BigW/NZ equivalents.

### Tier C — fragile, needs work

| Group | Scenarios | Why fragile |
|---|---|---|
| **Instant Win** | TC_018, TC_019, TC_020, TC_021, TC_040, TC_041 | The IW prompt is probabilistic and its exact form varies. Multiple popups chain together. Several still carry `TODO` markers. |
| **Card / coupon locking, 3-minute windows** | TC_012, TC_013, TC_014, TC_015 | Real wall-clock timing against a live engine. Slow and inherently flaky. |
| **Save & recall** | TC_016 | Longest flow in the suite; suspends and recalls a transaction; most steps, most to go wrong. |
| **BNI free-product** | TC_025, TC_026, TC_027 | Depend on promotion configuration and on multiple prompts appearing in the right order. |
| **Cross-Tasman** | TC_042, TC_043 | Cross-border card behaviour; `TODO` markers remain. |
| **BigW suite as a whole** | all 32 | Started, then paused when priorities moved. The scripts are clones of the Supermarket suite pointed at BigW data. **They have not been validated end to end on a BigW lane.** Treat the whole suite as unproven until it has had one clean run. |

Say this plainly:

> "The BigW suite is the biggest unknown. It is structurally correct — it now
> reads BigW data rather than Supermarket data, which it did not before — but
> nobody has watched all thirty-two run on a BigW lane. Your first BigW run
> will find things. That is expected, and it is a bounded piece of work rather
> than a rewrite."

---

## Segment 4 — Maintenance playbook & backlog (8 min)

### The four routine maintenance jobs

| Job | Where | How |
|---|---|---|
| **A test card expired / a product changed** | `Data\RegressionSale.csv` | Change the cell in a text editor. `git diff`. Commit. **No code.** |
| **A button changed name after an SCO release** | `Components\<the relevant one>.py` | Dump the screen, find the new `auto_id`, update the component once. Add the finding to `sco-automation.instructions.md`. |
| **A new popup appears mid-flow** | usually `Complete_transaction.py` or `Move_to_tendermode.py` | Add it to the dismissal list. If it is a whole new screen, `dump_and_cache()` a fingerprint for it. |
| **A new scenario is needed** | `Testing\<Suite>\` + CSV | Follow Day 5. Data row first, then one step at a time. |

### The monthly / per-release checklist

1. Run **Sanity** first. If Sanity fails, stop — something structural broke.
2. Run each banner suite.
3. Triage failures into the five buckets before raising anything.
4. Update `sco-automation.instructions.md` with anything new you learned.
5. Commit the CSV, the scripts and the ScreenCache together.

### What was fixed during this handover — state it, so they know the baseline

| Fix | Why it mattered |
|---|---|
| **20 card numbers repaired** in the CSV | Excel had rewritten them as `9.35522E+12`; those tests were scanning cards that do not exist. Recovered by cross-referencing each test's own verified values. |
| **Sanity now reads the CSV** | All 11 Sanity scripts silently used hardcoded fallbacks because the CSV keys did not match their `TC_ID`. Rows keyed to the scripts were added. Sanity is now **11/11**. |
| **BigW now reads BigW data** | 31 of 32 BigW scripts declared `BANNER="SM"`, so the "BigW suite" was testing Supermarket data. BigW rows were created and the scripts corrected. |
| **`TC_004` had a syntax error** | A stray leading space on line 1 meant the Regression copy could **never run at all**. Fixed. |
| **`TC_ID` mismatches fixed** | `&` vs `And`, and a truncated `TC_025`, meant those scripts never found their data. |
| **No more network dependency** | `Update_csv.py` wrote to an SMB share on another machine, using a password committed in the source. It now writes the local CSV atomically. **Change that password if it was ever real.** |
| **Reports no longer land in the wrong folder** | The logger resolved its output folder from the current directory; running a script from inside `Testing\NZ` created a nested `Results` folder and the batch summary found nothing. It is now resolved from the code's own location. |
| **`TC_028` no longer reports a false PASS** | It was a 0-byte file. An empty Python file exits 0, so the runner counted it as passing. It is now an explicit "not implemented" stub that exits non-zero, and it is commented out of `run_tests.txt`. The scenario is genuinely covered by `TC_08A`. |
| **5 implemented tests were being skipped** | `TC_035`, `TC_036`, `TC_037`, `TC_039`, `TC_049` existed but were missing from `run_tests.txt`. Added. |
| **`Hard_reset_SCO.py` added** | Escalation from soft reset to a full SCO restart, wired into the batch runner. |
| **`Run_Suite.bat` added** | One double-click launcher with a menu for all four banners. The old `run_tests.bat` only ever ran Regression. |
| **Stale docs corrected** | Script docstrings and the domain-knowledge file said the data came from an SMB share. They now say local CSV. |

Verification baseline after these fixes — **every real script resolves to real
local data**:

```
Sanity      11/11
Regression  36/37     (the 1 is the TC_028 placeholder)
BigW        31/32     (the 1 is the TC_028 placeholder)
NZ          19/19
```

### Recommended backlog, in priority order

1. **Get store login working after a restart** (see Segment 2). Until this is
   done, a hard reset needs a human. Highest value fix in the project.
2. **One clean validation run of the BigW suite** on a BigW lane. Fix what it
   finds.
3. **Close out the `TODO` markers** — mostly TLog apportionment checks that were
   scoped but not implemented. Search the repo for `TODO:` to list them.
4. **Stabilise the Instant Win group** (TC_018–TC_021, TC_040, TC_041).
5. **Repository cleanup.** The root has accumulated debug artefacts —
   `debug_*.png`, `pos_screenshot_*.png`, zero-byte `_*.py` scratch scripts,
   `tmp*.csv`. The empty `Testing\Steps\` folder and the obsolete
   `setup_*_csv_data.py` seeders (which still target the retired network share
   and contain a hardcoded password) should go. None of it affects execution;
   all of it confuses a newcomer.
6. **A cross-run reporting dashboard.** The per-test HTML and the batch summary
   are good; trend across runs is missing. The PASS/FAIL badge is in a
   predictable format, so an aggregator is a small, well-scoped job.
7. **Consider consolidating the four suites** into one parameterised set. Only
   do this after 1–4, and one scenario at a time.

---

## Segment 5 — Formal handover (7 min)

### The artefacts

| What | Where |
|---|---|
| Source of truth | `https://github.com/sumap-cloud/RTL` |
| Setup guide | `Documentation\NEW_MACHINE_SETUP.md` |
| CI guide | `Documentation\GitHub_Actions_Setup_Guide.md` |
| **This KT pack** | `Documentation\KT_Sessions\` |
| Day-to-day guide | `Scripts\SCO_Workspace\Team_Automation_Guide.md` |
| **Domain knowledge** | `Scripts\SCO_Workspace\sco-automation.instructions.md` |
| Test data | `Scripts\SCO_Workspace\Data\RegressionSale.csv` (+ timestamped backups beside it) |
| Installers | `C:\Pywin\*.exe`, `*.msi` |
| Offline packages | `Offline_lib\offline_packages\` |

### Handover checklist — walk through it on screen and tick it off live

- [ ] Team has GitHub access to `sumap-cloud/RTL` (write).
- [ ] At least two team members have built a machine from scratch and run a test.
- [ ] Team has access to the SCO lane and a booking convention is agreed.
- [ ] Team has run the **Sanity** suite themselves, unattended, start to finish.
- [ ] Team has read `sco-automation.instructions.md`.
- [ ] Team knows the CSV/Excel rule and has seen the corruption check command.
- [ ] Team has recovered a deliberately stuck lane with `Hard_reset_SCO.py`.
- [ ] Working store credentials for the lane are identified and recorded
      securely (**open item**).
- [ ] Backlog above is agreed and owned.
- [ ] Open-Questions document is closed out and handed over.
- [ ] A named owner exists for the suite.

### Closing words — suggested

> "What you are getting is a working automation suite for the SCO loyalty
> journeys across four banners, built on a component architecture that lets you
> fix a UI change in one place, and driven entirely from one CSV so most changes
> need no code at all. It has a dependable core that runs reliably today, and a
> documented list of what still needs work — I would rather hand you an honest
> map than a clean-looking one.
>
> The most valuable things in the repository are not the test scripts. They are
> `sco-automation.instructions.md` — every hard-won fact about how this
> terminal actually behaves — and the live-build method from Day 5, which is
> how you add anything new. Look after both and this suite will keep growing.
>
> I will stay reachable for questions while you settle in. Everything I know is
> written down in these six documents."

---

## Q&A bank

**Q: A test failed. Is it a bug in the app or a bug in the automation?**
A: Use the five buckets. Buckets 1, 3 and 5 are automation/environment. Bucket
4 is configuration. Only after you have excluded all four should you raise it
as an application defect — and by then you will have a screenshot and a step
log to attach, which makes for a very strong bug report.

**Q: What do we do if the whole suite fails on Monday morning?**
A: Do not start debugging test scripts. Check in this order: (1) is the lane at
Welcome, (2) is the EFT simulator running, (3) run one Sanity test on its own.
A whole-suite failure is nearly always environmental. If Sanity TC_001 passes
alone, the problem is state or sequencing, not the tests.

**Q: How do we stop tests interfering with each other?**
A: They already can't, structurally — each runs as its own process and the lane
is reset to Welcome between every one. What they do share is the *live cards*.
Two tests using the same card in the same run can consume each other's offers.
If you see that, give the scenarios different cards in the CSV.

**Q: Can we run this overnight?**
A: Yes, that is what the batch runner is designed for. The caveats are: nobody
can use the lane, the hard-reset store login needs to be working first,
and someone should check the summary in the morning rather than assuming.

**Q: How do we add a new banner?**
A: Copy the closest existing suite folder, change `BANNER` in each script, and
add rows to the CSV for that banner. `Run_Suite.bat` and `Batch_runner.py`
discover suites by folder, so you also add one menu entry. That is genuinely
all — which is the payoff of the design.

**Q: The password in `Update_csv.py` — was that real?**
A: It was a service account for the old network share. That share is no longer
used and the credential has been removed from the code, but **it is still in
the git history**. If it was a real credential, it must be rotated. Treat that
as an action item, not a formality.

**Q: What happens when the SCO application is upgraded?**
A: Run Sanity first. Expect some `could not find control` failures — those are
root cause 5. Dump the affected screens, update the automation ids in the
components, refresh any ScreenCache fingerprints that no longer match, and
record what changed in `sco-automation.instructions.md`. Because the ids live
in the components and not in the scripts, this is usually a handful of edits,
not ninety-seven.

**Q: We are not confident we can maintain this. What is the minimum viable
level?**
A: Run Sanity daily and the Tier A list per release. That alone gives real
regression coverage of the core loyalty journeys and needs nothing more than
Day 4's skills. Grow into Tier B and C from there.
