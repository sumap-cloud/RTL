# Day 2 — Architecture & Repository Tour

**Session goal:** everyone can open the repository and know where to look for
anything, and understands the one idea the whole design rests on — **reusable
components**.

**After this session they will be able to:**

- Navigate the repo without help.
- Explain the layered design: data → components → test scripts → runner → reports.
- Name the components that matter and say what each does.
- Understand why the same scenario exists four times (once per banner).

---

## Run sheet

| Time | Segment |
|---|---|
| 0–3 min | Recap Day 1, answer any question carried over |
| 3–10 min | The five-layer picture (whiteboard first, code second) |
| 10–20 min | Folder-by-folder tour, live in VS Code |
| 20–33 min | The component layer in detail |
| 33–41 min | How the four banner suites relate; the ScreenCache |
| 41–45 min | Recap + homework |
| 45–60 min | Q&A |

---

## Segment 1 — The five-layer picture (7 min)

**Draw this before you show any code.** If they hold this picture, everything
else lands.

```
  ┌──────────────────────────────────────────────────────────────┐
  │ 5. REPORTS            Results\<TC_ID>.html  + screenshots     │
  │                       Results\BatchLogs\*.log                 │
  └───────────────▲──────────────────────────────────────────────┘
                  │  logger.log(...)
  ┌───────────────┴──────────────────────────────────────────────┐
  │ 4. RUNNERS            Run_Suite.bat / run_all_<Suite>.py      │
  │                       Components\Batch_runner.py              │
  │                       + reset to Welcome between every test   │
  └───────────────▲──────────────────────────────────────────────┘
                  │  runs each script as its own process
  ┌───────────────┴──────────────────────────────────────────────┐
  │ 3. TEST SCRIPTS       Testing\<Suite>\TC_xxx_....py           │
  │                       "the recipe" — no UI code, just steps   │
  └───────────────▲──────────────────────────────────────────────┘
                  │  calls
  ┌───────────────┴──────────────────────────────────────────────┐
  │ 2. COMPONENTS         Components\*.py                         │
  │                       "the verbs" — add_item, scan_loyalty,   │
  │                       complete_transaction, ...               │
  │                       ALL pywinauto lives here                │
  └───────────────▲──────────────────────────────────────────────┘
                  │  reads
  ┌───────────────┴──────────────────────────────────────────────┐
  │ 1. DATA               Data\RegressionSale.csv                 │
  │                       card numbers, EANs, expected promos     │
  └──────────────────────────────────────────────────────────────┘
```

The single most important sentence of the whole handover:

> **"A test script never talks to the screen directly. It only calls
> components. And it never contains its own data — it reads the CSV. That
> separation is what makes this maintainable."**

Explain the payoff concretely:

- The card-payment button changes name in a new SCO release → you fix
  `Complete_transaction.py` **once** and all ~97 scripts are fixed.
- A test card expires → you change **one cell** in the CSV, no code at all.

---

## Segment 2 — Folder tour, live in VS Code (10 min)

Open the repo and walk the tree. Narrate as you go — do not just show it.

```
C:\Pywin\RTL Automation\
├── Run_Suite.bat                   ← double-click launcher, pick a banner
├── run_tests.bat / run_tests.txt   ← older list-driven runner (Regression only)
├── pyvenv.cfg                      ← proof the repo IS the venv
├── Documentation\
│   ├── NEW_MACHINE_SETUP.md
│   ├── GitHub_Actions_Setup_Guide.md
│   └── KT_Sessions\                ← this pack
├── Offline_lib\                    ← every python package, pre-downloaded
├── Lib\, Include\, Scripts\python.exe  ← the virtual environment itself
└── Scripts\
    ├── generate_batch_report.py
    ├── POS_Workspace\              ← the OLDER, separate POS project
    └── SCO_Workspace\              ← ★ everything we care about
        ├── Components\             ← the reusable building blocks
        │   └── ScreenCache\        ← JSON "fingerprints" of SCO screens
        ├── Data\
        │   └── RegressionSale.csv  ← ★ ALL test data, for every banner
        ├── Testing\
        │   ├── Sanity\             ← 11 quick smoke tests
        │   ├── Regression\         ← Supermarket / Metro, ~37 scripts
        │   ├── BigW\               ← BigW banner, ~32 scripts
        │   └── NZ\                 ← Countdown / New Zealand, 19 scripts
        ├── Results\                ← HTML reports + screenshots (NOT in git)
        ├── Team_Automation_Guide.md
        └── sco-automation.instructions.md   ← ★ the domain knowledge file
```

Three things to call out loudly:

1. **`POS_Workspace` is a different, older project.** Same repository, separate
   codebase, uses pytest. We are not handing that over here. Don't confuse the
   two — both have an `Add_item.py`.
2. **`Results\` is not in git.** Reports are evidence of a run on a machine, not
   source code. `.gitignore` excludes it. If you want to keep a report, copy it
   out.
3. **`sco-automation.instructions.md` is the crown jewels.** Every hard-won fact
   about how this SCO behaves is in there — which payment button works, which
   popups block which buttons, why `is_enabled()` lies. Read it. Keep it
   updated. It is worth more than the code.

---

## Segment 3 — The component layer (13 min)

This is the heart of the session. There are ~29 components. Do **not** read the
list out. Group them and show two or three real ones.

### The transaction journey, in components

```
login_pos()                       connect to the SCO, confirm it is idle
      │
add_item(eans, card)              scan one or more products into the basket
      │
scan_loyalty_salemode(card)       ── scan loyalty BEFORE the pay button
   or scan_loyalty_tenderprompt(card)  ── or AFTER it (different flow!)
      │
move_to_tendermode()              get from basket to the payment screen
      │
redeem_*()                        offers / vouchers / instant wins, if the
                                  scenario needs them
      │
complete_transaction()            pay by card and finish
      │
verify_eagleeye_logs()            prove the loyalty engine saw it correctly
```

### The full component catalogue (hand out, don't read)

**Getting started / finishing**

| Component | Function | What it does |
|---|---|---|
| `Login_POS.py` | `login_pos()` | Connects to the NCR NEXTGENUI window and confirms it is idle. Also stamps the EagleEye log start time. |
| `Complete_transaction.py` | `complete_transaction()` | Pays by card (EFT) and drives the transaction to completion, handling receipt prompts and popups. |
| `Void_transaction.py` | `void_transaction(user, pass, reason)` | Cancels a transaction. |
| `Save_transaction.py` | `save_transaction(user, pass, ...)` | Suspends a transaction so it can be recalled later. |
| `Recall_transaction.py` | `recall_transaction(user, pass, index)` | Brings a suspended transaction back. |

**Basket and loyalty**

| Component | Function | What it does |
|---|---|---|
| `Add_item.py` | `add_item(eans, card)` | Scans a semicolon-separated list of EANs into the basket. |
| `Scan_item.py` | `scan_item(app, ean, label)` | Scans one item (lower-level). |
| `Add_loyalty_card.py` | `add_loyalty_card(card)` | Adds a loyalty card. |
| `Scan_loyalty_salemode.py` | `scan_loyalty_salemode(card)` | Scans loyalty **while still in the basket**. |
| `Scan_loyalty_tenderprompt.py` | `scan_loyalty_tenderprompt(card)` | Clicks Pay, waits for the loyalty prompt, scans there. **Do not call `move_to_tendermode()` before this — it presses Pay itself.** |

**Navigation between screens**

| Component | Function |
|---|---|
| `Move_to_tendermode.py` | `move_to_tendermode(skip_choice_offer)` — basket → payment screen |
| `Move_back_to_salemode.py` | `move_back_to_salemode()` — payment screen → basket |
| `Screen_identifier.py` | `identify_screen(win)`, `dump_screen(win)`, `wait_for_screen(...)` |

**Offers, rewards and promotions**

| Component | Function |
|---|---|
| `Redeem_choice_offer.py` | `redeem_choice_offer(offer)` |
| `Redeem_collectable_offer.py` | `redeem_collectable_offer(type, list)` |
| `Redeem_instant_win.py` | `handle_instant_win_approval(...)`, `handle_instant_win_notification(...)`, `handle_instant_win_saved(...)` |
| `Redeem_reward_voucher.py` | `redeem_reward_voucher(...)` |
| `Verify_exciting_news_prompt.py` | `verify_exciting_news_prompt(timeout)` |
| `Promotion_details.py` | `get_promotion_details(list)`, `get_points_collected()` |
| `Total_amount_details.py` | totals and balance-due readers |

**Verification**

| Component | Function |
|---|---|
| `Verify_EagleEye_logs.py` | `verify_eagleeye_logs(...)`, `verify_offers_in_ee_log(...)`, `verify_card_in_ee_log(...)` — reads the real EagleEye adapter log on disk and proves the events happened |

**Data**

| Component | Function |
|---|---|
| `Read_csv.py` | `get_csv_value(source, banner, tc_id, iteration, column)` |
| `Update_csv.py` | `update_csv_value(source, banner, tc_id, iteration, column, value)` |

**Infrastructure / recovery**

| Component | Function |
|---|---|
| `report.py` | `logger` — the shared HTML report logger |
| `Batch_runner.py` | `run_suite(dir, name)` — the engine behind every "run all" |
| `Reset_to_welcome.py` | `reset_to_welcome()` — click our way back to the Welcome screen |
| `Hard_reset_SCO.py` | `ensure_welcome_screen()`, `hard_reset_sco()` — restart the SCO app and log the lane back in when clicking is not enough |
| `global_instance.py` | `reset_state()` — shared state between components (the window handle, EagleEye timestamps) |
| `Ensure_services_stopped.py`, `Ensure_EFTSimulator_closed.py` | process/service control — ⚠️ **never call these before a payment**, they kill the simulator that approves the card |

### Show one component for real

Open `Components\Read_csv.py` — it is only ~65 lines and it is the easiest one
to understand. Walk through `get_csv_value()`:

> "It opens the CSV, walks the rows, and returns the first row where
> **Banner**, **TC_ID** and **Iteration** all match. Three keys. Remember those
> three — tomorrow they are the whole session."

Then open `Components\Screen_identifier.py` and show `dump_screen()`:

> "This is the tool I mentioned yesterday. It walks every visible control in
> the SCO window and prints its automation id, type and text. On a one-screen
> terminal this is how you see what you are working with."

---

## Segment 4 — Four suites, one codebase (8 min)

```
Testing\
├── Sanity\      11 scripts   quick smoke — run this first, every day
├── Regression\  37 scripts   Supermarket / Metro  (Banner = "SM")
├── BigW\        32 scripts   BigW                 (Banner = "BigW")
└── NZ\          19 scripts   Countdown / NZ       (Banner = "NZ")
```

**Why the same scenario appears more than once.** The *business flow* is
identical across banners, but the *data* is not — different loyalty cards,
different products, different campaigns. So the script is duplicated per banner
and the only meaningful difference is one line:

```python
TC_ID     = "TC_007_VerifyTieredSpendCampaignWithRegisteredCard"
BANNER    = "SM"        # <- "BigW" in the BigW copy, "NZ" in the NZ copy
ITERATION = 1
```

That one line selects a different row of the CSV, and therefore a different
card and different products.

Be honest about the trade-off:

> "Duplicating the script per banner is not the most elegant design — a single
> script parameterised by banner would be cleaner. It was done this way because
> the banners were built on different machines at different times, and it does
> have one real advantage: you can change a BigW scenario without any risk of
> breaking Supermarket. If you ever consolidate them, do it deliberately and
> re-run everything."

### The ScreenCache

Open `Components\ScreenCache\` and show `welcome_screen.json`.

> "The SCO doesn't tell us what screen it is on. So we fingerprint each screen:
> 'if these controls are visible, and these other ones are not, it is the
> Welcome screen'. That is all these JSON files are. `identify_screen()` checks
> the live window against every fingerprint and returns the best match. It is
> how the recovery script knows whether it has finished."

Current fingerprints: `welcome_screen`, `sale_mode`, `select_payment`,
`loyalty_prompt`, `redemption_prompt`, `credential_entry`, `assistance_needed`,
`subscription_prompt`, `gc_activation_required`, `gc_scam_popup`.

---

## Segment 5 — Recap & homework (4 min)

1. Five layers: **data → components → test scripts → runners → reports**.
2. Test scripts contain **no UI code and no data**. Ever.
3. `Components\` is where all pywinauto lives — fix once, fixes everywhere.
4. Four suites, one per banner, differing mainly by the `BANNER` line.
5. `sco-automation.instructions.md` is the domain knowledge — read it.

**Homework (20 minutes):**

- Read `Scripts\SCO_Workspace\sco-automation.instructions.md` end to end.
  Write down three things you did not understand — we will cover them tomorrow.
- Open any script in `Testing\Regression\` and try to describe, in one
  sentence per line, what its imports tell you it is going to do.

---

## Q&A bank

**Q: Why is there so much duplicated code between the four suites?**
A: Because the banners were built at different times on different machines,
and because keeping them separate means a change for one banner cannot break
another. It is a deliberate trade-off, not an accident. If you consolidate,
consolidate one scenario at a time and re-run all four suites.

**Q: What is `POS_Workspace` and do we own it?**
A: It is the older Point-of-Sale automation project that shares this
repository. It uses pytest and Allure. It is not part of this handover. Be
careful when searching the repo — file names overlap.

**Q: Can I just edit a component to make my test pass?**
A: You *can*, and sometimes that is exactly right — but remember a component is
used by up to ninety-seven scripts. Before changing one, ask "is this fixing
the component, or is this fixing my scenario?" If it is the latter, the change
belongs in your test script or in the CSV.

**Q: What is `global_instance.py` for?**
A: A few things must be shared between components during a run — the handle to
the SCO window, and the timestamp we started watching the EagleEye log from.
Rather than pass them through every function, they live in one module that
everything imports.

**Q: Why does `Results\` sometimes appear in odd places?**
A: It used to. The report logger resolved its output folder relative to
whatever directory you launched Python from, so running a script from inside
`Testing\NZ` created a second `Results` folder there. That is fixed — the
folder is now resolved from the code's own location. If you see a stray nested
`Results` folder, it is left over from before; delete it.

**Q: How do I find which component handles a particular popup?**
A: Search the repo for the popup's text, or for the `auto_id` you saw in
`inspect.exe`. Most popups are handled either in `Complete_transaction.py` or
in `Move_to_tendermode.py`, and the common ones are documented in
`sco-automation.instructions.md`.

**Q: Is there a test for the components themselves?**
A: No unit tests — the components only have meaning against a live SCO. The
Sanity suite is effectively the component smoke test: if `login_pos`,
`add_item`, `scan_loyalty_*` and `complete_transaction` are broken, every
Sanity scenario fails immediately. That is why you run Sanity first.
