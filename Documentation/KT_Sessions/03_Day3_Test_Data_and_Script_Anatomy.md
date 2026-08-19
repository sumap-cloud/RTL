# Day 3 — Test Data & Script Anatomy

**Session goal:** everyone can change what a test does **without touching any
code**, and can read a test script line by line and explain it.

**After this session they will be able to:**

- Explain the three-key lookup (Banner + TC_ID + Iteration) and find any row.
- Change a card number, a product, or an expected promotion safely.
- Read any `TC_*.py` script and describe what it does.
- Avoid the Excel trap that silently destroys card numbers.

---

## Run sheet

| Time | Segment |
|---|---|
| 0–3 min | Recap Day 2, pick up the three "things I didn't understand" |
| 3–13 min | The CSV: every column explained |
| 13–20 min | The three-key lookup — the single most important mechanism |
| 20–27 min | **⚠️ The Excel trap** and how to edit the CSV safely |
| 27–40 min | **Live:** dissect one test script top to bottom |
| 40–45 min | Recap + homework |
| 45–60 min | Q&A |

---

## Segment 1 — The CSV is the control panel (10 min)

One file drives everything:

```
Scripts\SCO_Workspace\Data\RegressionSale.csv
```

Roughly 273 rows, 20 columns, covering all four banners.

Open it in VS Code (**not Excel** — we get to why shortly) and walk the
columns:

| # | Column | What it means | Example |
|---|---|---|---|
| 1 | **`Banner`** | 🔑 Which brand: `SM`, `NZ`, `BigW` | `SM` |
| 2 | `Module` | Grouping label: `Sanity` or `LPR` (Loyalty/Promotions/Rewards) | `Sanity` |
| 3 | `State` | Bookkeeping — whether the row was built and verified | `Done` |
| 4 | **`TC_ID`** | 🔑 Which test case this row belongs to | `TC_001` |
| 5 | **`Iteration`** | 🔑 Which pass through the scenario (some tests run the same flow several times with different data) | `1` |
| 6 | `Item_EAN` | Products to scan. **Semicolon-separated for multiple items** | `9310072000282;9310072000282` |
| 7 | `Item_type` | Free-text note about the article | `Donation` |
| 8 | `Item_eligible_status` | Whether the article qualifies for the offer | `Eligible` |
| 9 | `Card_number` | The loyalty card to scan — 13 digits | `9353109614779` |
| 10 | `Card_type` | Card scheme/segment: `WRC`, `SFC`, `QFF`, `SDC`, `SFL`, `AirNZ`, `Temporary`, `Locked Fund` | `WRC` |
| 11 | `Card_status` | `ACTIVE`, `SUSPENDED`, `TERMINATED` | `ACTIVE` |
| 12 | `Promotion_description` | Promotion text the script must find on screen. Semicolon-separated | `2x points on Tim Tams` |
| 13 | `Instant_win_offer` | The Instant Win offer expected | |
| 14 | `Instant_win_offer_redeem` | Whether/how it should be redeemed | |
| 15 | `Choice_offer` | The Choice Offer to pick (often an OCR search string like `$10`) | `$10` |
| 16 | `Collectable_offer` | Collectable/stamp offer to redeem | |
| 17 | `Exciting_news_popup` | The "Exciting News" message expected | |
| 18 | `Redeem_amount` | Amount to redeem | `$10` |
| 19 | `Instant_win_notification` | Expected IW notification | |
| 20 | `Notification_message` | Expected notification text | |

Say:

> "Nine times out of ten, when a test needs changing it is one of three cells:
> `Card_number`, `Item_EAN`, or `Promotion_description`. Nothing else. No code."

### A real row, in full

```
Banner                   = SM
Module                   = Sanity
State                    = Done
TC_ID                    = TC_001
Iteration                = 1
Item_EAN                 = 9310072000282        <- Arnott's Tim Tam 200g, $2.40
Card_number              = 9353109614779        <- registered EDR card, <1000 pts
Card_type                = WRC
Card_status              = ACTIVE
...everything else blank...
```

> "Blank means 'this scenario doesn't use that'. A Sanity smoke test just scans
> a product and a card — it does not need instant wins or choice offers, so
> those cells are empty."

---

## Segment 2 — The three-key lookup (7 min)

**This is the mechanism the whole suite depends on. Do not rush it.**

Every test script begins with three constants:

```python
TC_ID     = "TC_007_VerifyTieredSpendCampaignWithRegisteredCard"
BANNER    = "SM"
ITERATION = 1
```

Every time it wants a value, it calls:

```python
get_csv_value("saledata", BANNER, TC_ID, ITERATION, "Card_number")
```

`Read_csv.py` then finds the **one row** where all three match, and returns
that column.

Draw it:

```
   Script says:  BANNER="SM"  TC_ID="TC_007_..."  ITERATION=1
                          │
                          ▼
   CSV row:  SM | LPR | Done | TC_007_... | 1 | 93100... | ... | 93531...
                                                              │
                                          "Card_number"  ─────┘
                          │
                          ▼
   Script gets:  "9353109614779"
```

### ⚠️ The four rules of the lookup

Write these on the whiteboard. Every "my test isn't using my data" problem is
one of these:

1. **It is case-sensitive.** `SM` ≠ `sm`. `BigW` ≠ `BIGW`.
2. **The `TC_ID` must match exactly, character for character.** Trailing
   spaces count. `&` is not `And`.
3. **`Iteration` is compared as text.** `1` works; `01` does not.
4. **If no row matches, the script does not crash.** It quietly falls back to a
   hardcoded value inside the script — so the test *runs*, but **with the wrong
   data**. This is the most dangerous failure mode in the whole suite.

On point 4, show the pattern that every script uses:

```python
def _get_value(column, fallback):
    """Read from the local CSV; return the fallback on any error."""
    try:
        val = get_csv_value("saledata", BANNER, TC_ID, ITERATION, column)
        if val and not val.startswith("Error") and val != "No matching record found.":
            return val
    except Exception:
        pass
    return fallback

CARD_CODE = _get_value("Card_number", "<FILL_QFF_CARD_NUMBER>")
```

Say:

> "The fallback exists so a missing row doesn't blow up a two-hour batch run.
> The cost is that a typo in the `TC_ID` gives you a green-looking run against
> stale data. **Always check the console output — it prints
> `✅ Found value: ...` when the CSV was used, and
> `⚠️ No matching record` when it fell back.**"

### How to check every script resolves

Show them this — it is the fastest health check in the project:

```powershell
cd "C:\Pywin\RTL Automation"
.\Scripts\python.exe -c "import csv,re,pathlib;R=pathlib.Path('Scripts/SCO_Workspace');rows=list(csv.DictReader(open(R/'Data/RegressionSale.csv',encoding='utf-8-sig')));keys={(r['Banner'].strip(),r['TC_ID'].strip()) for r in rows};[print(s,':',sum(1 for f in sorted((R/'Testing'/s).glob('TC_*.py')) if (lambda t:(re.search(r'^BANNER\s*=\s*\"([^\"]+)\"',t,re.M) and re.search(r'^TC_ID\s*=\s*\"([^\"]+)\"',t,re.M) and (re.search(r'^BANNER\s*=\s*\"([^\"]+)\"',t,re.M).group(1),re.search(r'^TC_ID\s*=\s*\"([^\"]+)\"',t,re.M).group(1)) in keys))(f.read_text(encoding='utf-8'))),'/',len(list((R/'Testing'/s).glob('TC_*.py')))) for s in ['Sanity','Regression','BigW','NZ']]"
```

Expected today: `Sanity 11/11`, `Regression 36/37`, `BigW 31/32`, `NZ 19/19`.
The two misses are the deliberate `TC_028` placeholder in Regression and BigW —
Day 6 explains it.

---

## Segment 3 — ⚠️ The Excel trap (7 min)

**This is the single most damaging thing anyone can do to this project, and it
takes one double-click.**

> "If you open `RegressionSale.csv` in Excel and save it, Excel decides a
> 13-digit card number is a very large number and rewrites it in scientific
> notation. `9355215896056` becomes `9.35522E+12`. The digits are gone. The
> file still looks fine. Every affected test then scans a card number that does
> not exist."

This has already happened once to this project — **20 card numbers were
destroyed** and had to be reconstructed one by one by cross-referencing the
values still present in the test scripts. It took hours, and one of them could
only be resolved by hand.

### The rules

| ✅ Do | ❌ Don't |
|---|---|
| Edit in VS Code, Notepad++, or any plain-text editor | Open it in Excel and hit Save |
| If you must use a spreadsheet: **Google Sheets** with the columns pre-set to *Plain text*, then export CSV | Double-click the file in Explorer |
| Commit the change to git immediately so you have a diff | Leave it uncommitted |
| Run the health check above afterwards | Assume it is fine because it opens |

### How to spot the damage

```powershell
cd "C:\Pywin\RTL Automation"
Select-String -Path "Scripts\SCO_Workspace\Data\RegressionSale.csv" -Pattern "E\+\d"
```

No output = clean. Any output = a card number has been destroyed. Recover with
`git checkout` or from the timestamped backups sitting next to the CSV
(`RegressionSale.backup_*.csv`).

### Changing data the safe way — do this live

1. Open the CSV in VS Code.
2. `Ctrl+F`, search for the `TC_ID`.
3. Change the one cell.
4. Save.
5. `git diff` — confirm **only** the cell you meant to change is different.

> "That `git diff` step is not optional. It is the thing that catches Excel."

---

## Segment 4 — Anatomy of a test script (13 min)

Open `Testing\Regression\TC_004_VerifyMultiplierOfferForEligibleProductsAndBasketValue.py`
and go through it in five blocks.

### Block 1 — The docstring: the human specification

```python
"""
Scenario:
    Verify that the product points multiplier offer is applied correctly for
    eligible products when a QFF (segment 104) EDR card is scanned...

Pre-requisite:
    QFF (Qantas) EDR card configured with a product-level points multiplier...

Steps automated:
    1.  Login to SCO.
    2.  Scan eligible articles...
    ...

Data source:
    Local CSV: Data/RegressionSale.csv — TC_ID = "...", Banner = "SM", Iteration = 1.
"""
```

> "Read this first, always. It tells you the business scenario, what must be
> configured before the test can pass, the exact steps, and which CSV row it
> uses. If a test fails, the **Pre-requisite** section is usually the answer."

### Block 2 — Path setup (identical in every script)

```python
import sys
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent.parent   # -> SCO_Workspace

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
```

> "Boilerplate. It lets `from Components...` work no matter where the script is
> launched from. Copy it verbatim into any new script."

### Block 3 — Imports: the script's table of contents

```python
from Components.Login_POS import login_pos
from Components.Add_item import add_item
from Components.Scan_loyalty_tenderprompt import scan_loyalty_tenderprompt
from Components.Promotion_details import get_promotion_details
from Components.Verify_exciting_news_prompt import verify_exciting_news_prompt
from Components.Complete_transaction import complete_transaction
from Components.Verify_EagleEye_logs import verify_eagleeye_logs
from Components.Read_csv import get_csv_value
from Components.report import logger
```

> "You can tell exactly what this test does from the imports alone: log in,
> scan items, scan loyalty at the tender prompt, check promotions, check the
> exciting-news popup, pay, verify EagleEye. That readability is the point of
> the component design."

### Block 4 — Identity and data

```python
TC_ID     = "TC_004_VerifyMultiplierOfferForEligibleProductsAndBasketValue"
BANNER    = "SM"
ITERATION = 1

logger.set_tc_id(TC_ID)          # <- decides the report filename

EAN_LIST   = _get_value("EAN_Codes", None) or _get_value("Item_EAN", "<FILL_EAN_LIST>")
CARD_CODE  = _get_value("Card_number", "<FILL_QFF_CARD_NUMBER>")
PROMO_LIST = _get_value("Promotion_description", "")
```

Two things to point out:

- `logger.set_tc_id(TC_ID)` is what names the report file
  `Results\TC_004_....html`. Change `TC_ID` and the report name changes too.
- `EAN_Codes` is tried before `Item_EAN` because the older POS project used a
  different column name. Harmless, but it explains the odd double lookup.

### Block 5 — The body: try / except / finally

```python
try:
    if not login_pos():
        raise RuntimeError("login_pos failed — aborting test.")

    add_item(EAN_LIST, CARD_CODE)

    if not scan_loyalty_tenderprompt(CARD_CODE):
        raise RuntimeError("scan_loyalty_tenderprompt failed — aborting test.")

    _, _, promo_descs, promo_prices, _, missing = get_promotion_details(PROMO_LIST)
    if not missing:
        logger.log("✅ Step 5 — multiplier offer verified on screen.", status="pass")
    else:
        logger.log(f"❌ Step 5 — Missing promotions: {missing}.", status="fail")

    ...
    if not complete_transaction():
        raise RuntimeError("complete_transaction failed — aborting test.")

    ee_result = verify_eagleeye_logs(expect_wallet_open=True, expect_wallet_settle=True)

except Exception as e:
    logger.log(f"❌ Unexpected error: {e}", status="fail")
    logger.take_screenshot("Unexpected_Error")

finally:
    logger.save()
    print(f"\nReport saved to: {logger.updated_path}")
```

Explain the three statuses — they decide the colour in the report and the
overall pass/fail:

| `status=` | Meaning | Effect |
|---|---|---|
| `"pass"` | This check succeeded | green row |
| `"fail"` | This check failed | red row, **and the whole report is marked FAILED**, and a screenshot is taken automatically |
| `"info"` | Noted, not judged | blue row, no effect on the verdict |

> "One `status='fail'` anywhere makes the whole test FAIL. That is why things
> that legitimately vary — like a popup that only appears if the card crossed
> 2000 points this run — are logged as `info`, not `fail`."

And the `finally:` block:

> "`logger.save()` is in `finally`, so the report is written even when the test
> crashes. You always get evidence."

---

## Segment 5 — Recap & homework (5 min)

1. `Data\RegressionSale.csv` is the control panel. Most changes are one cell.
2. **Banner + TC_ID + Iteration** — three keys, case-sensitive, exact.
3. No match = silent fallback to hardcoded data. **Watch the console.**
4. **Never open the CSV in Excel.**
5. Script anatomy: docstring → path setup → imports → identity/data → try/except/finally.

**Homework (30 minutes):**

- Pick any `TC_*.py` in `Testing\NZ\`. Find its row in the CSV using the three
  keys. Write down the card number and the EANs it will use.
- Change one `Promotion_description` cell in a scratch copy of the CSV, run
  `git diff`, then `git checkout` to undo it. Get comfortable with that loop.

---

## Q&A bank

**Q: My test isn't picking up the data I changed. Why?**
A: Almost always the three-key lookup. Check, in order: (1) is `Banner` exactly
right including capitals, (2) does `TC_ID` in the script match the CSV
character for character, (3) is `Iteration` the same. Then run the test and
look for `✅ Found value:` versus `⚠️ No matching record` in the console.

**Q: What is `Iteration` actually for?**
A: Some scenarios do the same flow more than once with different data — for
example "lock the coupon within 3 minutes" needs several passes. Each pass is
one row, numbered 1, 2, 3, 4. The script sets `ITERATION` to say which pass it
is running.

**Q: Can two rows have the same Banner + TC_ID + Iteration?**
A: They shouldn't. The loader takes the first match, so a duplicate silently
shadows the second. If data seems stale, search the CSV for the TC_ID and count
the rows.

**Q: Why are the fallback values still in the scripts if the CSV always works?**
A: History — early on the data lived on a network share that was often
unreachable. They are now a safety net. They are also genuinely useful as
documentation: the fallback is the value that was verified live when the script
was written.

**Q: Can we move the data into a proper database or Excel workbook?**
A: You could, and `Read_csv.py` is the only place that would need to change —
that is exactly why the lookup is behind a single function. But CSV in git
gives you free version history and readable diffs, which has already saved this
project once. Do not change it without a strong reason.

**Q: How do I add data for a brand-new test case?**
A: Copy an existing row for a similar scenario, change `TC_ID` to your new one,
set `Banner` and `Iteration`, then fill in the card and EANs. Save from a text
editor. Then confirm with the health-check command from Segment 2.

**Q: What is `Module` = `LPR`?**
A: Loyalty / Promotions / Rewards — the functional area. `Sanity` marks the
smoke-test rows. It is a label for humans; no code branches on it.

**Q: Something wrote to the CSV during a test run. Is that expected?**
A: Yes — `Update_csv.py` lets a script write a value back, for example a
transaction number needed by a later step. It writes to the local file
atomically (temp file then rename) so a crash cannot leave a half-written CSV.
If it reports "Permission denied", somebody has the CSV open in Excel.
