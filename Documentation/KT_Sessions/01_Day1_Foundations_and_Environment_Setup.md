# Day 1 — Foundations & Environment Setup

**Session goal:** everyone understands *what* we are automating and *why*, and
can build the environment on a fresh machine from scratch.

**After this session they will be able to:**

- Explain what SCO is and how it differs from POS.
- Name every piece of software this project needs and say what each one is for.
- Take a bare Windows machine to the point where a test script will run.
- Clone the repository and verify the setup.

---

## Run sheet

| Time | Segment |
|---|---|
| 0–5 min | Welcome, agenda for all six days, how to ask questions |
| 5–13 min | What is SCO? What is the business risk we are testing? |
| 13–20 min | SCO vs POS — why SCO automation is harder |
| 20–30 min | The software stack: what, why, and where to get it |
| 30–40 min | **Live demo:** setup walkthrough + verification |
| 40–45 min | Recap + homework |
| 45–60 min | Q&A |

---

## Segment 1 — Welcome and the shape of the week (5 min)

Say this:

> "Over six sessions I am going to hand this suite over completely. Day 1 is
> the ground floor — what the system is and how to build a machine that can run
> the tests. Day 2 is the map of the code. Day 3 is the test data and how a
> single test is built. Day 4 is running tests and reading the results. Day 5 is
> how I actually wrote these scripts against a live terminal, which is the part
> you will need if you want to add new ones. Day 6 is what to do when things
> break, plus the known gaps.
>
> Please hold questions until the last fifteen minutes — a lot of what you will
> want to ask on Day 1 is answered on Day 3. If it's a blocker, interrupt me."

Show the index document (`00_KT_Pack_Index.md`) on screen so they can see the
six-day shape.

---

## Segment 2 — What is SCO and what are we protecting? (8 min)

**SCO = Self-Checkout.** The terminal the customer operates themselves in the
store. In this programme it is the **NCR NEXTGENUI** application running on a
Windows lane.

Draw or show this:

```
   Customer                SCO lane (NCR NEXTGENUI)          Back-end
   --------                ------------------------          --------
   scans items       -->   basket / sale mode
   scans loyalty     -->   loyalty prompt          -->   EagleEye (loyalty engine)
   pays by card      -->   tender screen           -->   EFT / payment
   takes receipt     <--   welcome screen          <--   TLog written
```

**What we are actually testing is not "does the till work".** It is
**loyalty**: Everyday Rewards points, offers, campaigns, redemptions,
instant wins, and the prompts the customer sees. That is the risk area — a
mis-configured campaign silently gives away money or fails to reward a
customer, at every lane, in every store.

Key vocabulary to define slowly (they will hear these constantly):

| Term | Plain-English meaning |
|---|---|
| **Banner** | Which brand/retail chain: `SM` (Supermarket/Metro), `NZ` (Countdown, New Zealand), `BigW`. |
| **EDR** | Everyday Rewards — the loyalty card scheme. |
| **EAN** | The barcode number on a product. |
| **Article** | A product. |
| **Segment** | A category the loyalty card belongs to (e.g. QFF = Qantas, SFC = Christmas savings, SDC = staff discount). It changes what prompts appear. |
| **EagleEye (EE)** | The external loyalty/offers engine. It decides points and offers. |
| **TLog** | The transaction log the till writes — the financial record. |
| **Instant Win (IW)** | A promotional prize prompt that can appear mid-transaction. |
| **BNI** | "Buy N Items" style promotion — buy something, get a free product. |
| **Tender** | The payment step / payment method. |

**Why automate this at all?** Because a regression pass is roughly a hundred
scenarios, each one involving scanning items, scanning a specific loyalty card
in a specific state, waiting for a prompt, and reading numbers off a screen. By
hand that is days of work and it is easy to miss a wrong number. Automated, it
runs unattended and produces evidence.

---

## Segment 3 — SCO vs POS: why this was hard (7 min)

This segment matters. It explains why the code looks the way it does, and it
sets realistic expectations.

| | **POS** (cashier till) | **SCO** (self-checkout) |
|---|---|---|
| Screens | Two — cashier screen and customer screen | **One** |
| Development | Put the app on one screen, VS Code on the other. Inspect elements and write code side by side. | You cannot. The app owns the screen. |
| Element discovery | Live, immediate | Dump controls to a file, then read the file |
| Simulators | Fewer | EFT simulator, scanner/keyboard entry simulators — must be triggered as part of the flow |
| Feedback loop | Seconds | Run the script, watch the lane, read the dump, adjust, run again |

Say this plainly:

> "On POS you can see the application and your editor at the same time, so
> finding a button takes seconds. On SCO the application is full screen on the
> only screen there is. To find out what a button is called I had to run a
> script that walks the whole UI tree and writes it to a file, then read the
> file, then change my code, then run it again. Every single element. That is
> why this project has a `dump_screen` utility and a `ScreenCache` folder —
> those exist purely to make the invisible visible."

Also mention: **the simulators**. Several scenarios need a barcode or a card
number typed into a simulator window, and the EFT simulator must stay running
because it is what auto-approves the card payment. This is covered properly on
Day 5.

---

## Segment 4 — The software stack (10 min)

Everything needed is already sitting in `C:\Pywin` on this machine. Show the
folder.

| Installer | What it is | Why we need it | Required? |
|---|---|---|---|
| `python-3.12.4-amd64.exe` | Python 3.12.4 | The language everything is written in. **Must be this version** — the virtual environment in the repo was created from it. | **Yes** |
| `Git-2.55.0.2-64-bit.exe` | Git | Getting the code from GitHub and pushing changes back. | **Yes** |
| `winsdksetup.exe` | Windows SDK | Gives you **`inspect.exe`** — the Microsoft tool that lets you point at any Windows control and read its automation id. This is *the* debugging tool for UI automation. | **Yes** |
| `tesseract-ocr-w64-setup-5.5.0.20241111.exe` | Tesseract OCR | Some SCO text is drawn as an image, not as a readable control. We screenshot it and read the text with OCR. Install to `C:\Program Files\Tesseract-OCR` and add to PATH. | **Yes** |
| `VSCodeUserSetup-x64-1.121.0.exe` | VS Code | The editor. Not needed to *run* tests, needed to *work on* them. | Recommended |
| `PowerShell-7.4.6-win-x64.msi` | PowerShell 7 | Nicer shell. Windows PowerShell 5 also works. | Optional |
| `MicrosoftEdgeEnterpriseX86.msi` | Edge | Only used by legacy browser-based checks. | Optional |

The Python packages sit on top:

| Package | Why |
|---|---|
| **`pywinauto`** | **The core of everything.** Lets Python find and click Windows controls. |
| `pywin32`, `comtypes` | Windows API plumbing that pywinauto uses. |
| `pytesseract`, `Pillow`, `opencv-python`, `numpy` | Screenshots and OCR. |
| `requests` | Talking to EagleEye/HTTP endpoints. |
| `pytest`, `pytest-html` | Only used by the older POS half of the repo. The SCO suite has its own runner. |

**Offline install matters.** Store machines are usually firewalled. The repo
ships every wheel it needs in `Offline_lib\offline_packages\`, so you can
install with no internet:

```powershell
cd "C:\Pywin\RTL Automation"
Scripts\pip.exe install --no-index --find-links=Offline_lib\offline_packages -r Offline_lib\requirements.txt
```

### ⚠️ The one structural fact everybody trips over

Say this slowly and show `pyvenv.cfg`:

> "The repository folder **is** the Python virtual environment. There is no
> `.venv` sub-folder. `C:\Pywin\RTL Automation\pyvenv.cfg` proves it. That
> means the Python you must use is `.\Scripts\python.exe`, and it means the
> project code lives *inside* the venv's `Scripts` folder, at
> `Scripts\SCO_Workspace`. It is unusual. Do not try to 'tidy' it — a lot of
> paths depend on it."

```
C:\Pywin\RTL Automation\        <- git repo AND virtual environment
├── pyvenv.cfg                  <- the proof
├── Scripts\
│   ├── python.exe              <- USE THIS PYTHON, always
│   ├── pip.exe
│   └── SCO_Workspace\          <- our actual project code
├── Lib\site-packages\          <- installed packages
└── Documentation\
```

---

## Segment 5 — Live demo: setup from scratch (10 min)

Follow `Documentation\NEW_MACHINE_SETUP.md` on screen. Do not read it out —
*do* it, and narrate.

```powershell
# 1. Confirm the base Python is present and is 3.12.4
& "C:\Program Files\Python312\python.exe" --version

# 2. Clone the repository (only on a genuinely new machine)
cd C:\Pywin
git clone https://github.com/sumap-cloud/RTL.git "RTL Automation"

# 3. Create the virtual environment IN the repo folder
cd "C:\Pywin\RTL Automation"
& "C:\Program Files\Python312\python.exe" -m venv .

# 4. Install the packages offline
Scripts\pip.exe install --no-index --find-links=Offline_lib\offline_packages -r Offline_lib\requirements.txt
```

Then **verify** — this is the part to emphasise, because "it installed" is not
the same as "it works":

```powershell
cd "C:\Pywin\RTL Automation"

# venv Python is the right version
.\Scripts\python.exe --version                       # -> Python 3.12.4

# pywinauto imports
.\Scripts\python.exe -c "import pywinauto; print(pywinauto.__version__)"

# OCR is on PATH
tesseract --version

# The test-data file is present and readable
.\Scripts\python.exe -c "import csv;print(sum(1 for _ in open(r'Scripts\SCO_Workspace\Data\RegressionSale.csv',encoding='utf-8-sig'))-1,'data rows')"

# The automation can actually see the SCO window
.\Scripts\python.exe -c "from pywinauto import Application; a=Application(backend='uia').connect(title_re='.*NCR NEXTGENUI.*',timeout=10); print('Connected to the SCO')"
```

If that last line prints `Connected to the SCO`, the machine is ready.

**Also show `inspect.exe` once**, briefly — open it, hover over an SCO button,
and point at the `AutomationId` field. Say:

> "That `AutomationId` is the name our code uses to find that button. Remember
> this tool. On Day 5 it is how we will find a new one."

---

## Segment 6 — Recap & homework (5 min)

Recap in one breath:

1. We automate the **SCO loyalty journey**, not just "the till".
2. SCO is one screen, which is why the code has dump/cache utilities.
3. Python 3.12.4 + pywinauto + Tesseract + Windows SDK.
4. **The repo folder is the venv. Always use `.\Scripts\python.exe`.**
5. Always work with `C:\Pywin\RTL Automation` as your current directory.

**Homework (15 minutes):**

- Clone the repo onto your own machine.
- Run the five verification commands above (all except the SCO connection —
  that only works on the lane machine).
- Open `Scripts\SCO_Workspace\Data\RegressionSale.csv` in a text editor
  (**not Excel** — Day 3 explains why) and just look at it.

---

## Q&A bank

**Q: Do we all need the SCO lane to work on this?**
A: No. You can read code, edit data and review reports anywhere. You only need
the lane to *run* a test, because the script drives a real application. In
practice one lane is shared, and we book it.

**Q: Why Python and not Selenium / Playwright / Cypress?**
A: Those drive web browsers. The SCO is a native Windows desktop application,
so it needs a Windows UI automation library. `pywinauto` speaks Microsoft UI
Automation, which is the same technology screen readers use.

**Q: Can we upgrade Python to the latest version?**
A: Not casually. The virtual environment and the shipped offline wheels are
built for 3.12.4 — for example the `pywin32` and `numpy` wheels are
`cp312` builds. If you upgrade, you must rebuild the venv and re-download every
wheel. There is no benefit today.

**Q: Why is the project inside the `Scripts` folder? That looks wrong.**
A: It is unusual, and it is because the virtual environment was created *in*
the repository root rather than in a sub-folder. It works, and moving it now
would break paths in the batch files, the VS Code tasks and the runner. It is
documented so nobody is surprised. Treat it as a quirk, not a bug to fix
during handover.

**Q: What if the machine has no internet at all?**
A: That is the normal case and it is handled. Every Python package is
pre-downloaded into `Offline_lib\offline_packages\`, and the installers are in
`C:\Pywin`. Copy both to a USB stick and you can build a machine with no
network.

**Q: How long does a full setup take?**
A: About 30–45 minutes on a clean machine, most of which is the installers.

**Q: Who owns the SCO lane and what happens if someone else is using it?**
A: The lane is shared hardware. Tests drive the real UI, so two people cannot
run at once — one will make the other fail. Agree a booking convention on
day one; a shared calendar is enough.

**Q: Is any of this hooked up to CI?**
A: There is a GitHub Actions self-hosted runner set up, but only for the older
POS half of the repo, and it runs a single test. The SCO suite is run manually
or via the batch launcher. See `Documentation/GitHub_Actions_Setup_Guide.md`.
Extending CI to SCO is a reasonable future improvement, but it needs a
dedicated lane that nobody else touches.
