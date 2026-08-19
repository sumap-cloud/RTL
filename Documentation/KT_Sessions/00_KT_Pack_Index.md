# RTL SCO Automation — Knowledge Transfer Pack

**Audience:** a team that is new to test automation and new to this project.
**Format:** 6 sessions × 1 hour. ~40–45 minutes of content + 10–15 minutes Q&A.
**Delivery:** Google Meet, screen shared from the SCO test machine.

---

## How to use this pack

Each day has its own document. Every document is written as a **presenter
script**, not as reference material. It contains:

| Section | What it is for |
|---|---|
| **Session goal** | One sentence you read out at the start. |
| **What they will be able to do afterwards** | Sets expectations. Read it out. |
| **Run sheet** | Minute-by-minute timings so you never run over. |
| **Talking points** | What to actually say, in order, in plain language. |
| **Live demo** | Exact commands to type. Practise these once before the session. |
| **Whiteboard / diagram** | What to draw or show on screen. |
| **Hands-on** | A small task the audience does themselves. |
| **Q&A bank** | Questions they are likely to ask, with model answers. |
| **Homework** | Something small before the next session. |

> **Presenter tip:** you do not need to memorise this. Keep the document open on
> a second screen and work down it. The timings in the run sheet are the only
> thing you must watch.

### Presenting with slides

These documents are presenter scripts, not slides. To generate a slide deck per
session, see **[`NotebookLM_Deck_Prompts.md`](NotebookLM_Deck_Prompts.md)** — a
ready-made prompt for each day that produces a beginner-friendly deck with
speaker notes under every slide.

Present from the deck; keep the day's `.md` open on your second screen for the
run sheet, exact commands and Q&A bank. Send **both** to the team afterwards —
the deck is for the room, the `.md` is what they live on later.

---

## The six sessions

| Day | Document | Theme |
|---|---|---|
| 1 | [`01_Day1_Foundations_and_Environment_Setup.md`](01_Day1_Foundations_and_Environment_Setup.md) | What SCO is, what we automate, and getting a machine from bare Windows to a working setup. |
| 2 | [`02_Day2_Architecture_and_Repo_Tour.md`](02_Day2_Architecture_and_Repo_Tour.md) | How the repository is laid out and why. The component layer. |
| 3 | [`03_Day3_Test_Data_and_Script_Anatomy.md`](03_Day3_Test_Data_and_Script_Anatomy.md) | The CSV is the control panel. How a test script is built out of components. |
| 4 | [`04_Day4_Running_Tests_and_Reading_Reports.md`](04_Day4_Running_Tests_and_Reading_Reports.md) | Running one test, running a suite, and reading the HTML reports and logs. |
| 5 | [`05_Day5_Live_Build_Methodology.md`](05_Day5_Live_Build_Methodology.md) | How these scripts were actually written — the live-build method — and how to write a new one. |
| 6 | [`06_Day6_Failures_Maintenance_and_Handover.md`](06_Day6_Failures_Maintenance_and_Handover.md) | When tests fail: triage, recovery, maintenance, known gaps, and the formal handover. |

---

## The honest framing (read this before Day 1)

You are handing over a suite that was **built in roughly ten days, on four
different machines, against a live retail system, by someone who was new to the
domain.** That is worth saying out loud on Day 1, calmly and without apology.

The right message is:

> "This suite gives you a working, repeatable way to exercise the SCO loyalty
> journeys end to end. A solid core of scenarios run reliably today. Some of
> the more complex ones depend on live card balances and campaign
> configuration, so they need attention. Everything is structured so you can
> extend it — the components, the data, and the reporting are all separated
> deliberately. By the end of these six sessions you will be able to run it,
> read it, fix it and add to it."

That is a true statement, and it is a strong one. It sets the team up to own
the suite rather than to expect a finished product.

**Do not** promise that every scenario passes every time. **Do** be explicit
about which ones are dependable and which ones are known to be fragile — Day 6
covers exactly this, with a named list.

---

## Prerequisites for the sessions

Before Day 1, make sure:

- The SCO lane is available and at the **Welcome** screen.
- The EFT simulator (`RemedyEFTPOSServer` + `MultiSimulator.exe`) is running —
  card payments are auto-approved by it, and nothing works without it.
- You have `C:\Pywin\RTL Automation` open in VS Code.
- You can reach `https://github.com/sumap-cloud/RTL`.
- The installer pack in `C:\Pywin` is intact (Python, Tesseract, Git, VS Code,
  Windows SDK, Edge, PowerShell).
- You have run one full Sanity suite recently so you know its current state and
  will not be surprised live.

---

## Materials to send the team

Send these **after** each session, not before — otherwise they read ahead and
stop listening:

1. The day's markdown document (this pack).
2. The recording of the session.
3. The homework task.

At the end of Day 6, send the whole pack plus:

- `Documentation/NEW_MACHINE_SETUP.md` (setup, already in the repo)
- `Documentation/GitHub_Actions_Setup_Guide.md` (CI, already in the repo)
- `Scripts/SCO_Workspace/Team_Automation_Guide.md` (day-to-day guide)
- `Scripts/SCO_Workspace/sco-automation.instructions.md` (**the domain
  knowledge file — this is the single most valuable document in the repo**)

---

## Q&A hygiene

- Take questions in the last 10–15 minutes, not throughout — otherwise Day 1
  will consume Day 3's content.
- If you do not know an answer, say **"I'll confirm and come back to you on
  that at the start of tomorrow's session."** Then actually open the next
  session with the answer. This builds more credibility than guessing.
- Keep a shared "Open Questions" document. Add every unanswered question to it
  live, on screen. Close them out as you go. Hand it over on Day 6.
