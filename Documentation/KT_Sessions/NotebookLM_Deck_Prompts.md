# NotebookLM prompts — turning each KT session into a slide deck

Copy-paste prompts for generating one professional, layman-friendly deck per KT
session. Use one NotebookLM notebook per day, with **only that day's `.md` file**
as the source — mixing all six in one notebook makes the model blend content
across days and the decks lose their focus.

---

## How to use this file

1. Open NotebookLM → **Create new notebook**.
2. **Add source** → upload the single `.md` file for that day.
3. Studio panel → **Slide deck** (or **Report** if slide deck is unavailable in
   your region) → click **Customise / Add instructions**.
4. Paste the **Universal house style** block below, then the **day-specific
   block** underneath it, then generate.
5. If the instruction box rejects the length, use the **Short version** for that
   day instead — it carries the same intent in ~600 characters.

> Generate the six decks **in order**, and skim each one before moving on. If
> Day 1 comes out too technical, tighten the house-style block once and reuse
> the corrected version for the rest.

---

## Universal house style — paste this first, every time

```
AUDIENCE
Build this deck for people who have never done test automation and have never
seen a self-checkout system from the inside. Assume zero programming knowledge.
They are smart professionals, but every technical term is new to them.

LANGUAGE RULES
- Plain, everyday English. Short sentences. No jargon unless you define it in
  the same breath, in brackets, the first time it appears.
- Never assume the reader knows what these mean - always explain on first use:
  automation, script, test case, regression, sanity, component, function,
  repository, commit, virtual environment, CSV, UI element, timeout, flaky.
- Use a real-world analogy for every abstract idea. Prefer supermarket, kitchen,
  car and household analogies because the subject is retail.
- Write for the eye, not the ear. No paragraphs on slides.

SLIDE FORMAT
- 18 to 24 slides. Aim for roughly one slide per 2 minutes of a 45-minute talk.
- Every slide has: a short benefit-led title (max 8 words), then a maximum of
  5 bullets, each a maximum of 12 words.
- Never put a wall of text or a raw code block on a slide. If code matters,
  show at most 3 lines and put a plain-English translation directly beneath it.
- Use tables only when comparing 2 or 3 things, max 4 rows.
- Where a diagram would help, insert a slide that describes the diagram in
  words under the heading "DIAGRAM:" so it can be drawn later. Suggest simple
  shapes only: boxes, arrows, a numbered flow, or a layered stack.

SPEAKER NOTES - THIS IS THE MOST IMPORTANT PART
Under every single slide, write 80 to 150 words of speaker notes in the first
person, exactly as the presenter would say them out loud to the room. Natural
spoken English, not written English. Include the analogy, the "why this
matters" and any warning. The presenter should be able to read these notes
aloud and sound like an expert without adding anything.

STRUCTURE OF THE DECK
1. Title slide: session name, which day of six it is, and one line on what the
   audience will be able to DO by the end.
2. "Where we are in the week" slide: a 6-step tracker with today highlighted.
3. "By the end of this session you will be able to..." - 3 or 4 outcomes,
   written as actions the learner performs, not topics covered.
4. The body content, in the same order as the source document's segments.
5. A "Common mistakes and how to avoid them" slide near the end.
6. A one-slide recap: the 3 things to remember if they forget everything else.
7. A "What you are doing before next session" homework slide.
8. A final "Questions" slide listing 3 questions the audience is likely to ask,
   so the presenter is not caught cold.

TONE
Confident, calm, practical and honest. This is a real system being handed to a
real team - not a sales pitch. Where the source document admits a limitation or
a known gap, keep that honesty in the deck. Do not invent capabilities, numbers,
file names or results that are not in the source. If the source does not say
it, do not put it on a slide.
```

---

## Day 1 — Foundations & Environment Setup

**Source:** `01_Day1_Foundations_and_Environment_Setup.md`

```
Now build the Day 1 deck: "Foundations and Environment Setup" - session 1 of 6.

Cover, in this order:
1. What a self-checkout is from the automation point of view, and what business
   risk we are protecting: loyalty points, offers and discounts being applied
   correctly at the checkout. Make the audience feel why a wrong discount at a
   self-checkout matters to a real customer and to the business.
2. Why automating a self-checkout is harder than automating a normal
   application: one single touchscreen instead of two screens, hardware
   simulators for the scanner and card reader, and no ability to see the app
   and the code side by side. Use an analogy for this.
3. The software stack - what each tool is and, in one sentence each, what job
   it does and why we could not do without it: Python, pywinauto, Tesseract OCR,
   Git, VS Code, the Windows SDK and its inspect tool.
4. The setup walkthrough as a numbered, screenshot-ready checklist.

MUST NOT BE LOST:
- The virtual environment warning. The repository folder IS the virtual
  environment. Give this its own slide with a clear DO and DO NOT. Explain a
  virtual environment with an analogy - a toolbox that belongs to this one job
  so it never clashes with another job on the same machine.
- The verification checks after install, presented as a "how do I know it
  worked?" slide with the expected result beside each check.

Finish with a homework slide: set up your own machine end to end and run the
verification checks before Day 2.
```

**Short version** (if the instruction box is length-limited):

```
Day 1 of 6: Foundations and Environment Setup. Total beginners, zero coding
knowledge, plain English, analogies throughout, 18-24 slides, max 5 bullets of
12 words per slide, no code walls. Under every slide write 80-150 words of
first-person speaker notes the presenter reads aloud. Cover: what self-checkout
automation protects and why it matters commercially; why SCO is harder than a
normal app (one touchscreen, hardware simulators); what each tool does (Python,
pywinauto, Tesseract OCR, Git, VS Code, Windows SDK); the setup checklist. Give
the "repo folder IS the virtual environment" warning its own slide. End with
outcomes, common mistakes, a 3-point recap and homework.
```

---

## Day 2 — Architecture & Repository Tour

**Source:** `02_Day2_Architecture_and_Repo_Tour.md`

```
Now build the Day 2 deck: "Architecture and Repository Tour" - session 2 of 6.

The single goal of this session: after it, someone can open the project folder
and know where to look for anything. Build every slide towards that.

Cover, in this order:
1. The five-layer architecture. Give this a DIAGRAM slide - a vertical stack of
   five labelled boxes with arrows showing what calls what, and one plain-English
   sentence per layer. Then a second slide that walks one real action down
   through all five layers so they see it working.
2. A folder-by-folder tour. Present this as a table: folder name, what lives in
   it, and "when would I open this?" - that last column is the one that makes it
   stick.
3. The component layer. This is the heart of the session. Explain reusable
   components with an analogy: a recipe book of steps that every test borrows,
   so a step is written once and fixed once. Show why this matters commercially -
   when the application changes a button, we edit ONE file, not fifty tests.
   Group the components by what they do rather than listing all of them.
4. One suite per banner - Sanity, SM, Metro, BigW and NZ, plus a legacy
   Regression folder. Explain what each is for, when you would run it, and the
   key idea that the same code serves all of them because only the data changes
   between them. Mention that SM and Metro were split out of the old combined
   Regression folder so each banner owns its own data.

MUST NOT BE LOST:
- The difference between Sanity and Regression, in one line each, in the words
  a manager would use. Sanity = is the system alive. Regression = did anything
  we already fixed break again.
- The idea that a test script contains no knowledge of buttons or screens; it
  only orders components around. Say this at least twice.
```

**Short version:**

```
Day 2 of 6: Architecture and Repository Tour. Absolute beginners, plain English,
analogies, 18-24 slides, max 5 bullets of 12 words, no code walls. Under every
slide write 80-150 words of first-person speaker notes to read aloud. Goal: after
this session anyone can open the folder and know where to look. Cover: the
five-layer architecture as a labelled DIAGRAM plus one action traced through all
five layers; a folder tour as a table with a "when would I open this?" column;
reusable components explained as a shared recipe book, and why that means fixing
a changed button once instead of fifty times; the suites (Sanity, SM, Metro,
BigW, NZ, plus legacy Regression) and when to run each. End with a 3-point recap
and homework.
```

---

## Day 3 — Test Data & Script Anatomy

**Source:** `03_Day3_Test_Data_and_Script_Anatomy.md`

```
Now build the Day 3 deck: "Test Data and Script Anatomy" - session 3 of 6.
This is the most practical session of the week - the audience will use this
knowledge weekly. Make it extremely concrete.

Open with a short "what changed since Day 2" slide: the Supermarket and Metro
tests, which used to share one folder, are now two separate suites with their
own data, and reports are now saved in a folder per suite so the suites cannot
overwrite each other's results. Two slides maximum on this.

Cover, in this order:
1. The CSV file as the control panel of the whole suite. Analogy: the dashboard
   of a machine - you change the settings there, you do not rewire the machine.
   Land the payoff hard: you can change what a test buys, which card it scans
   and what it expects, WITHOUT touching a single line of code. Include the
   per-banner row counts as a small table.
2. How a test finds its row: the three keys - Banner, TC_ID and Iteration.
   Give this a DIAGRAM slide showing a script reaching into the file and pulling
   out one row. Make clear that Banner is what keeps Supermarket and Metro
   apart even though the scripts are identical.
3. THE MOST IMPORTANT SLIDE OF THE WHOLE WEEK - the Excel trap. Opening this
   file in Excel and saving it silently destroys 13-digit card numbers by
   rewriting them in scientific notation, and the file still looks perfectly
   fine afterwards. This has already damaged this project once and 20 card
   numbers had to be rebuilt by hand. Give it a full slide with a red warning
   treatment, a before/after example of a card number being destroyed, a clear
   DO and DO NOT table, and the one command that detects the damage.
4. The silent-fallback danger: if a script cannot find its data row it does NOT
   crash - it quietly uses a built-in default value and the test still passes.
   A green result can therefore be meaningless. Then present the health-check
   tool as the cure, with what a good result and a bad result look like.
5. The anatomy of a test script, broken into its blocks, each block explained in
   one plain sentence - what it is for, not how it works. Emphasise that the
   parts are always in the same order, so once you can read one script you can
   read all of them.

MUST NOT BE LOST:
The two warnings above are the reason this session exists. If anything gets cut
for length, cut the script anatomy detail, never the Excel trap or the silent
fallback.
```

**Short version:**

```
Day 3 of 6: Test Data and Script Anatomy. Beginners, plain English, analogies,
18-24 slides, max 5 bullets of 12 words, no code walls. Under every slide write
80-150 words of first-person speaker notes. Cover: the CSV as the control panel
you change WITHOUT touching code; the three-key lookup (Banner, TC_ID,
Iteration) as a DIAGRAM; then the two critical warnings, each on its own strongly
designed slide - (1) opening the CSV in Excel silently destroys 13-digit card
numbers into scientific notation and has already cost this project 20 cards,
with the detection command; (2) if a script cannot find its data row it does not
crash, it quietly uses a default and still passes, so a green result can be
meaningless - and the health-check tool that catches it. Then the standard
blocks of a test script. End with common mistakes, a 3-point recap and homework.
```

---

## Day 4 — Running Tests & Reading Reports

**Source:** `04_Day4_Running_Tests_and_Reading_Reports.md`

```
Now build the Day 4 deck: "Running Tests and Reading Reports" - session 4 of 6.
Treat this as an operator's manual. The audience should be able to run a full
suite unsupervised and correctly explain the result to their manager.

Cover, in this order:
1. The pre-flight checklist - what must be true before you press go. Present it
   as a tick-list slide. Include the point that the lane must be on the Welcome
   screen before a run starts, and why.
2. Running one single test - the command, what you will see happening on the
   screen, and roughly how long to expect it to take.
3. Running a whole suite - the menu launcher and its six options (Sanity, SM,
   Metro, BigW, NZ, and the legacy Regression), choosing a banner, and what
   "unattended" really means in practice.
4. Reading the output, which is the core of the session:
   - Where the report and the log files are written, including that each suite
     now has its own results folder so SM and Metro results never collide
   - How to read the pass/fail summary
   - How to open one failed test and find the exact step that failed
   - What the screenshots are for and when they are captured
5. First-line triage: given a failure, the audience should be able to decide
   which of these it is - a genuine defect, a data problem, a timing problem,
   an environment problem, or a stuck lane - BEFORE escalating to anyone.
   Present this as a decision-flow DIAGRAM.

MUST NOT BE LOST:
- The habit of always running from the project root folder, and what goes wrong
  if you do not.
- That the same test number exists in several suites, so "the TC_004 report"
  is ambiguous - always say which banner.
- The message that a failing test is information, not a disaster, and that
  raising a defect without triaging first wastes everyone's time. Say this
  warmly - these are beginners and their instinct will be to panic.
```

**Short version:**

```
Day 4 of 6: Running Tests and Reading Reports. Beginners, plain English,
18-24 slides, max 5 bullets of 12 words, no code walls. Under every slide write
80-150 words of first-person speaker notes. Treat it as an operator's manual -
by the end they can run a suite unsupervised and explain the result to a manager.
Cover: the pre-flight tick-list including "lane must be on the Welcome screen";
running a single test and what you will see; running a full suite from the menu
launcher; where reports, logs and screenshots are written and how to open a
failed test and find the exact failing step; and first-line triage as a decision
DIAGRAM sorting a failure into genuine defect, data, timing, environment or stuck
lane. Stress running from the project root. Reassure them that a failing test is
information, not a disaster. End with a 3-point recap and homework.
```

---

## Day 5 — The Live-Build Methodology

**Source:** `05_Day5_Live_Build_Methodology.md`

```
Now build the Day 5 deck: "The Live-Build Methodology - how to write a new test"
- session 5 of 6. This session teaches a way of working, not a list of facts.
Structure it as a story: here was the problem, here is the method that solved it,
here is how you use it yourself.

Cover, in this order:
1. The core problem, stated honestly: on a self-checkout you cannot see the
   application and your code at the same time, the screen is a single
   touchscreen, hardware has to be simulated, and you cannot know what the next
   screen will look like until you are standing on it. Writing a whole test in
   advance and hoping it runs does not work here.
2. The discovery toolkit - the small set of techniques for finding out what is
   actually on the screen in front of you, each explained in plain terms with
   what it gives you back.
3. The live-build loop itself, as a numbered DIAGRAM: perform ONE step against
   the real lane, watch what actually happens, capture the screen, confirm the
   step worked, write that step into the script, record any new data into the
   CSV, then move to the next step. Never write step 2 before step 1 is proven.
4. A worked example that walks through building the first few steps of a new
   test using the loop.

MUST NOT BE LOST:
- The single most important principle: one step at a time, proven against the
  real system before it is written down. Give it its own slide and repeat it in
  the recap.
- The rule that any new data discovered during the build - a card number, a
  product barcode - goes straight into the CSV, never hardcoded into the script.
- Frame this honestly as the method that made a large suite possible in a very
  short timeframe on an unfamiliar system. It is a genuine engineering
  contribution, so present it with quiet confidence, not as a workaround.
```

**Short version:**

```
Day 5 of 6: The Live-Build Methodology - how to write a new test. Beginners,
plain English, 18-24 slides, max 5 bullets of 12 words. Under every slide write
80-150 words of first-person speaker notes. Structure it as a story: the problem,
the method, how to use it. Cover: why you cannot pre-write a self-checkout test
(one touchscreen, simulated hardware, unknown next screen); the discovery
toolkit for seeing what is really on screen; then the live-build loop as a
numbered DIAGRAM - perform ONE step on the real lane, watch it, capture the
screen, confirm it worked, write that step, record any new data into the CSV,
then move on, never writing step 2 before step 1 is proven; then a worked
example. Give "one step at a time, proven before written" its own slide and
repeat it in the recap. Stress that new data goes into the CSV, never hardcoded.
```

---

## Day 6 — Failures, Maintenance & Handover

**Source:** `06_Day6_Failures_Maintenance_and_Handover.md`

```
Now build the Day 6 deck: "Failures, Maintenance and Handover" - session 6 of 6,
the final session. This is a handover, so the tone is honest and confident: here
is what works, here is what does not, here is exactly how you look after it.
Do not soften the limitations - the credibility of the whole week depends on
this session being straight with the audience.

Cover, in this order:
1. The five root causes of a failing test, each with how to recognise it and
   what to do first. Make this a table or a decision DIAGRAM they can screenshot
   and pin up.
2. Recovery - how a stuck lane is brought back to the Welcome screen, and the
   escalation from a gentle recovery to a full restart of the checkout
   application. Include the known limitation around the lane login honestly.
3. What is solid and what is not. Keep the source document's tiered honesty
   exactly as it is written - which scenarios are dependable, which are
   sensitive to timing or data, and which are not finished. Frame it as
   "so you know where to spend your attention first", not as an apology.
4. The maintenance playbook - the routine jobs, and for each one: where you go,
   what you change, and whether it needs code or only data. Emphasise how many
   of them need no code at all.
5. The prioritised backlog - what the next team should do first, and why that
   order.
6. The formal handover - what is being handed over, where everything lives,
   and where to look things up after these sessions end.

MUST NOT BE LOST:
- The list of fixes made during handover, presented as "here is the baseline you
  are starting from" - including that some tests were previously passing on the
  wrong data or passing without running at all, and that this is now detectable
  with a single command.
- The monthly / per-release checklist, as a clean numbered slide they can follow
  without any other document open.
- End on a genuinely strong closing slide: what the team can now do, where to
  get help, and the first three things they should do on Monday morning.
```

**Short version:**

```
Day 6 of 6, the final session: Failures, Maintenance and Handover. Beginners,
plain English, 18-24 slides, max 5 bullets of 12 words. Under every slide write
80-150 words of first-person speaker notes. Tone: honest and confident - what
works, what does not, how to look after it. Cover: the five root causes of a
failing test as a pin-up-able DIAGRAM; how a stuck lane is recovered and escalated
to a full restart, including the known login limitation stated honestly; which
scenarios are dependable, which are sensitive, and which are unfinished, framed
as "where to spend your attention first"; the maintenance playbook showing how
many jobs need only data and no code; the prioritised backlog; and the formal
handover. Include the fixes made during handover as "the baseline you start
from", and the per-release checklist as a clean numbered slide. Close with what
the team can now do and their first three actions on Monday.
```

---

## After NotebookLM generates each deck — a 5-minute check

NotebookLM is good, but it will drift. Check these before you present:

| Check | Why |
|---|---|
| Every file path, command and number matches the source `.md` | The model paraphrases paths and rounds numbers. Anything it invented will be exposed the moment you demo it live. |
| The Day 3 Excel warning survived and is prominent | It is the highest-value slide in the entire pack. |
| The Day 6 limitations were not quietly polished away | Models optimise for positivity. Your credibility depends on those staying in. |
| Speaker notes exist under **every** slide | This is what lets you present material you built quickly, with authority. |
| No slide has more than ~5 bullets | If it does, split it — a crowded slide is where an audience stops listening. |
| Nothing on a slide contradicts a `.md` file | The team will read the `.md` files afterwards. Any mismatch costs you trust. |

**Do not delete the `.md` files after generating the decks.** The decks are for
the room; the `.md` files are the reference the team lives on afterwards. Send
both.

---

## One extra deck worth generating

After the six, make a **7th short deck for management or stakeholders** from
`00_KT_Pack_Index.md` plus `06_Day6_Failures_Maintenance_and_Handover.md`:

```
Build a short executive briefing deck - 8 to 10 slides maximum - for senior
stakeholders who will never run a test themselves and have five minutes.

Answer only these questions, one per slide, in business language with no
technical detail at all:
- What was built, and what business risk does it reduce?
- What is the coverage - how many scenarios, across which banners?
- What is the current confidence level - what is dependable today, and what
  still needs work? Be straight about this.
- What does the receiving team now own, and what have they been trained on?
- What are the top three risks to this continuing to work?
- What is needed next, and from whom?

Confident, factual, no jargon, no hype. Speaker notes of 80-120 words under each
slide. Do not invent any number that is not in the source.
```

This is the deck that protects you. It puts the scope, the honest confidence
level and the open risks on the record, in your words, at handover time.
