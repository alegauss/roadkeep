// The copy lives here and nowhere else. Every section component imports a value from this
// module and only renders it, so a claim is an array element a reviewer can check against the
// tool rather than a string welded into the markup that displays it. The composition — which
// section, in which order, and the illustrative chrome — lives in the JSX; this file is the
// words.
//
// Fragments carrying inline code or emphasis are modelled as a small tagged run list (`Rich`)
// rather than raw HTML, so a section renders them without dangerouslySetInnerHTML and the twin
// generator has a structure to convert rather than markup to parse. Terminal blocks are the
// same idea one register down: a line is a list of runs carrying the colour class the theme
// gives it, so a transcript is data and not a `<pre>` somebody edits with the highlighting.
//
// Every transcript below was produced by running the command against this repository or a
// scaffolded one. That is a claim the disclaimer makes to a reader, so it is one this file
// has to keep true: a pasted output that drifts is prose with a shelf life, and the area next
// door (site/docs) is where output is generated from a real run instead.

export type Run =
  | string
  | { code: string }
  | { b: string }
  | { i: string }
  | { a: string; href: string };

export type Rich = Run[];

/** A run inside a terminal transcript, tagged with the class that colours it. */
export type TermRun =
  | string
  | { g: string }
  | { c: string }
  | { no: string }
  | { ok: string }
  | { dim: string }
  | { b: string };

export type TermLine = TermRun[];

export type Terminal = { title: string; lines: TermLine[] };

/* ------------------------------------------------------------------ meta + chrome */

export const meta = {
  title: "roadkeep — stop paying tokens to keep your docs",
  description:
    "A Claude Code plugin that turns the format of your ROADMAP.md, CHANGELOG.md, IMPROVEMENTS.md, STRATEGY.md, DEFERRED.md and DECISIONS.md into a schema a command enforces — so keeping them is procedural and deterministic instead of context the model spends remembering, reading and checking.",
  og: {
    title: "roadkeep — stop paying tokens to keep your docs",
    description:
      "Claude Code should spend its context on the work, not on policing your docs. One call writes the line; one exit code decides whether anything drifted.",
  },
} as const;

export const repoUrl = "https://github.com/alegauss/roadkeep";
export const parentUrl = "https://alegauss.github.io/";
export const pypiUrl = "https://pypi.org/project/roadkeep/";

// The nav is anchors on one page plus one link that leaves it: /roadkeep/docs/ is a separate
// build under the same base, so it is written as a path and there is no route for it here.
export const nav = {
  brand: "roadkeep",
  parent: { pre: "part of", name: "alegauss", href: parentUrl },
  links: [
    { href: "#why", label: "Why it exists" },
    { href: "#agents", label: "Claude Code" },
    { href: "#strengths", label: "Strengths" },
    { href: "#compare", label: "Compare" },
    { href: "#install", label: "Install" },
    { href: "/roadkeep/docs/", label: "Docs" },
  ],
  cta: { href: repoUrl, label: "★ GitHub" },
} as const;

/* ------------------------------------------------------------------ hero */

export const hero = {
  badge: "A Claude Code plugin · Python ≥3.11 · zero dependencies · Apache-2.0",
  headline: {
    lead: "Claude Code should spend its context on the work,",
    accent: "not on policing your docs.",
  },
  sub: [
    "roadkeep turns the format of your ",
    { b: "ROADMAP.md" },
    ", ",
    { b: "CHANGELOG.md" },
    ", ",
    { b: "IMPROVEMENTS.md" },
    ", ",
    { b: "STRATEGY.md" },
    ", ",
    { b: "DEFERRED.md" },
    " and ",
    { b: "DECISIONS.md" },
    " into a schema a command enforces. So keeping them stops being something the model has to remember, read and judge, and becomes what a tool does: ",
    { b: "procedural, deterministic, and paid for once" },
    ".",
  ] as Rich,
  note: "One call writes the line. One exit code decides whether anything drifted.",
  ctas: [
    { href: "#install", label: "Install the plugin →", kind: "primary" },
    { href: repoUrl, label: "★ View on GitHub", kind: "ghost" },
  ],
  chips: [
    { icon: "🧠", text: [{ b: "Context stays on the task" }, ", not on the format"] as Rich },
    { icon: "🗂", text: [{ b: "Your existing Markdown" }, " — no migration"] as Rich },
    { icon: "🚫", text: [{ b: "Zero" }, " runtime dependencies"] as Rich },
    { icon: "⛔", text: ["Hand-edits ", { b: "denied at the source" }] as Rich },
    { icon: "🔧", text: [{ b: "64 MCP tools" }, ", schemas derived from your config"] as Rich },
  ],
} as const;

/* ------------------------------------------------------------------ the context ledger */

export const why = {
  eyebrow: "Why it exists",
  heading: "Keeping docs is work Claude Code should not be paying for",
  intro: [
    "Every rule an agent has to ",
    { b: "remember" },
    ", every file it has to ",
    { b: "read to answer a question" },
    ", and every judgement a reviewer then has to ",
    { b: "re-check" },
    " is context and wall-clock spent on bookkeeping. roadkeep moves all three into a subprocess.",
  ] as Rich,
  columns: ["What a turn needs", "Without roadkeep", "With roadkeep"],
  rows: [
    {
      ask: "“What should I work on next?”",
      was: [
        "Read the backlog end to end — ",
        { b: "~5k tokens" },
        " in this repository, every time it is asked",
      ] as Rich,
      now: [
        { code: "brief" },
        " returns the line, its rationale, deps, blockers and the non-goals in ",
        { b: "one tool result" },
      ] as Rich,
    },
    {
      ask: "“What is the format here?”",
      was: [
        "Rules in a resident instruction file — the one measured below reached ",
        { b: "186 KB, ≈46k tokens on every turn" },
      ] as Rich,
      now: [
        "A ",
        { b: "trigger-loaded skill" },
        ": read on the turns that write a governed file, ",
        { b: "zero on the turns that don't" },
      ] as Rich,
    },
    {
      ask: "“Is this line valid?”",
      was: [
        "The model judges the prose, then a human judges the model — ",
        { b: "two soft verdicts" },
      ] as Rich,
      now: [
        { code: "lint" },
        " exits ",
        { b: "0 or 1" },
        " and names ",
        { code: "file:line:column" },
        " — no judgement, no sampling, same answer every run",
      ] as Rich,
    },
    {
      ask: "“This line is too long.”",
      was: [
        "Delete a turn of finished prose and write it again — ",
        { b: "the expensive half of the turn is already spent" },
      ] as Rich,
      now: [
        "The field is refused ",
        { b: "before the sentence exists" },
        ": exit 2 names the limit, and nothing was written",
      ] as Rich,
    },
    {
      ask: "“Can I trust that answer?”",
      was: [
        "Re-open the file to verify what the last command said — ",
        { b: "paying the read anyway" },
      ] as Rich,
      now: [
        "Every ",
        { code: "--json" },
        " answer carries ",
        { b: "which file and which line" },
        " it came from, so auditing costs nothing",
      ] as Rich,
    },
    {
      ask: "“Ship it.”",
      was: [
        "Three hand-edits across three files, plus every dependent's annotation — ",
        { b: "and one of them gets forgotten" },
      ] as Rich,
      now: [
        { code: "ship <id>" },
        ": one call, ",
        { b: "all of them or none" },
        ", dependents re-annotated",
      ] as Rich,
    },
  ],
  note: [
    "Same repository, same rules. What changes is ",
    { b: "who pays" },
    ": a context window, or a dependency-free subprocess that answers in milliseconds and is ",
    { b: "done thinking about it" },
    ".",
  ] as Rich,
} as const;

/* ------------------------------------------------------------------ the mechanism */

export const mechanism = {
  eyebrow: "Where the tokens actually go",
  heading: "Every backlog rots the same way",
  intro: [
    "Not from neglect — from an author who knows more than the line allows, and a rule that only a reviewer holds. When that author is a model, the rot is ",
    { b: "billed twice" },
    ": once to write it, once to read it back.",
  ] as Rich,
  note: [
    "One task, ",
    { b: "T1" },
    ", written both ways — hand-edited on the left, through ",
    { code: "add" },
    " on the right. Same repository, same rule, same intent.",
  ] as Rich,
  bad: {
    tag: "BY HAND",
    label: "A format nobody enforces",
    lines: [
      ["- 📋 ", { b: "T1" }, " Refactor the cache layer. We looked at three"],
      ["  options here and the reason we went with the second is"],
      ["  that the first would require touching the scheduler,"],
      ["  which nobody owns anymore, and the third needs a"],
      ["  migration. Note that Marc raised the same concern last"],
      ["  quarter, and the benchmark he attached is still the"],
      ["  best evidence we have."],
    ] as TermLine[],
    points: [
      [
        { b: "396 characters" },
        " against a one-sentence rule — and ",
        { b: "nothing objected" },
        ".",
      ],
      ["Named after its fix, so the line can never be falsified — only abandoned."],
      [
        "The rationale landed where the reader is, so ",
        { b: "every later turn re-reads it" },
        ".",
      ],
      ["Finding this task again means reading the file: ", { b: "~5k tokens per ask" }, "."],
    ] as Rich[],
  },
  good: {
    tag: "THROUGH add",
    label: "A format that is a schema",
    lines: [
      ["$ roadkeep ", { g: "add" }, ' --block A --symptom "…" --why "…"'],
      [{ no: "roadkeep: refused, nothing written:" }],
      ["  why: 305 characters, limit is 200"],
      ["  why: why is one sentence; a second is the signal"],
      ["       it belongs in the section this line points at"],
      ["  line: rendered line is 396, limit is 320"],
      ["                                    ", { dim: "exit 2" }],
      [""],
      ["$ roadkeep ", { g: "add" }, ' --block A --symptom "…" --why "…"'],
      ["- 📋 ", { b: "T1" }, " (deps: —) ", { b: "Every read of the cache layer" }],
      [{ b: "  serialises through one lock" }, " — the second option"],
      ["  avoids touching the scheduler nobody owns, and"],
      ["  needs no migration. → §T1"],
      [{ ok: "event    T1  Block A  open" }],
    ] as TermLine[],
    points: [
      [
        { b: "185 characters" },
        ", refused twice before it existed — the retry cost a field, not a turn.",
      ],
      [
        "The marker, the ",
        { code: "(deps: —)" },
        " annotation and the ",
        { code: "→ §T1" },
        " pointer are ",
        { b: "derived" },
        ".",
      ],
      [
        "The rationale went to the file the pointer names, where ",
        { b: "nothing loads it by accident" },
        ".",
      ],
      [
        "The ",
        { code: "event" },
        " line is the whole payload a hook needs — ",
        { b: "no file to re-read" },
        ".",
      ],
    ] as Rich[],
  },
  quote: {
    lines: ["“The saving is the analysis,", "not the characters.”"],
    body: [
      "A linter reports ",
      { i: "after" },
      " the prose exists — the tokens are spent and the author is asked to delete work they just did. A field with ",
      { code: "maxLength: 200" },
      " refuses first. Same rule, two orders of magnitude cheaper, and it turns an analytical act (",
      { i: "“is this too long, and what would I cut?”" },
      ") into a procedural one (",
      { i: "“call add”" },
      ").",
    ] as Rich,
  },
} as const;

/* ------------------------------------------------------------------ inside Claude Code */

export const surfaces = {
  eyebrow: "Inside Claude Code",
  heading: ["Four surfaces, so the cheap path ", { i: "is" }, " the correct one"] as Rich,
  intro: [
    "An agent bypasses any format with one ",
    { code: "Edit" },
    ", because ",
    { code: "Edit" },
    " is cheaper than reading a ",
    { code: "--help" },
    ". The plugin removes that trade instead of losing it: the tool call arrives ",
    { b: "pre-described" },
    ", and the hand-edit comes back ",
    { b: "naming the command that replaces it" },
    ".",
  ] as Rich,
  terminal: {
    title: "PreToolUse — Edit on docs/ROADMAP.md",
    lines: [
      [{ no: "Edit refused" }, ": docs/ROADMAP.md is this project's"],
      ["roadmap, and roadkeep owns its writes."],
      [""],
      ["Call instead, from the project root:"],
      ["  roadkeep ", { g: "add" }, ' --block <x> --symptom "…" --why "…"'],
      ["        ", { c: "a new task line, fields refused at input" }],
      ["  roadkeep ", { g: "status" }, " <id> <marker>"],
      ["        ", { c: "a marker, and only in this file" }],
      ["  roadkeep ", { g: "ship" }, " <id>"],
      ["        ", { c: "ledger entry, line gone, section dropped" }],
    ] as TermLine[],
  } as Terminal,
  hook: {
    kicker: "1 · the hook",
    heading: "A denial that costs one line, not a turn",
    body: [
      "A refusal with no next step is one an agent routes around, burning the turn to find its own way in. This one ",
      { b: "is the instruction" },
      " — command and flags included — so complying is less work than retrying. A second hook runs ",
      { code: "lint" },
      " before the turn ends, so drift is caught ",
      { b: "by the agent that can still fix it" },
      " instead of by a human, tomorrow.",
    ] as Rich,
  },
  cards: [
    {
      kicker: "2 · the MCP server",
      heading: "The schema arrives with the tool",
      body: [
        { b: "64 tools" },
        " over stdio — the whole write path and the whole query surface — with an input schema ",
        { i: "derived" },
        " from your ",
        { code: "roadkeep.toml" },
        ": ",
        { code: "maxLength" },
        " is this project's field limits, ",
        { code: "enum" },
        " its markers, ",
        { code: "pattern" },
        " its id shape. ",
        { b: "No flags to recall, no round trip to a usage string" },
        " — a wrong argument is refused by the protocol. Every description is held to a character budget ",
        { code: "lint" },
        " enforces, so the surface cannot quietly grow into the context it was meant to save.",
      ] as Rich,
    },
    {
      kicker: "3 · the skill",
      heading: "Rules that load only on the turns that need them",
      body: [
        "The whole write path lives in a ",
        { b: "trigger-loaded skill" },
        ", read when a governed file is in play and ",
        { b: "costing nothing on every other turn" },
        ". It ships with the plugin, so the standard is the same text in every project rather than a paragraph each repo re-invents in the file that always loads.",
      ] as Rich,
    },
    {
      kicker: "4 · the slash commands",
      heading: "Silence is the allow, and every failure allows",
      body: [
        { code: "/roadkeep:add" },
        ", ",
        { code: ":ship" },
        ", ",
        { code: ":pick" },
        " and ",
        { code: ":lint" },
        " are there for the person driving. The guard behind all of it returns only ",
        { code: "deny" },
        ", never ",
        { code: "allow" },
        ", so it never waves through the permission rules you set — and a broken config, bad JSON or a missing path ",
        { b: "lets the write through" },
        ": a guard that denied on its own errors would turn one typo into a repository nobody can edit.",
      ] as Rich,
    },
  ],
  note: [
    "Four surfaces, ",
    { b: "one engine" },
    ": every one dispatches through the same parser a terminal uses, so there is one set of refusals to trust and one place a rule can change. A fifth is for the person in the editor — a ",
    { b: "VS Code extension" },
    " showing the backlog as a tree, ready before blocked, with the blocker named. It carries ",
    { b: "no rule of its own" },
    ": every row is a payload ",
    { code: "roadkeep" },
    " printed, so a project whose prefix, markers or limits differ needs nothing changed in it.",
  ] as Rich,
} as const;

/* ------------------------------------------------------------------ strengths */

export const strengths = {
  eyebrow: "Strengths",
  heading: "Eight ways a turn gets cheaper",
  intro: [
    "Each one is a property the tool can be held to — ",
    { b: "a test, an exit code or a schema" },
    ", not a promise in a README.",
  ] as Rich,
  cards: [
    {
      icon: "⚡",
      kicker: "The whole point",
      heading: "Ask instead of read",
      body: [
        "Every question is a command — ",
        { code: "pick" },
        ", ",
        { code: "brief" },
        ", ",
        { code: "deps" },
        ", ",
        { code: "show" },
        ", ",
        { code: "stats" },
        ", ",
        { code: "origin" },
        " — answering inside ",
        { b: "one tool result" },
        ". Finding one ready task by reading the backlog cost ",
        { b: "~5k tokens" },
        " here; ",
        { code: "brief" },
        " starts the same task and adds the deps, the blockers and the non-goals.",
      ] as Rich,
    },
    {
      icon: "🔌",
      kicker: "Nothing resident",
      heading: "The rules cost nothing on the turns that don't write",
      body: [
        "The write path is a ",
        { b: "trigger-loaded skill" },
        ", not a paragraph in an instruction file that every turn pays for. And the instruction files themselves get a ",
        { b: "line and byte budget lint enforces" },
        " — because the one measured below reached 186 KB while declaring a limit about itself.",
      ] as Rich,
    },
    {
      icon: "🎯",
      kicker: "Deterministic, not judged",
      heading: "The verdict is an exit code",
      body: [
        { code: "lint" },
        " exits ",
        { b: "0 or 1" },
        " and names ",
        { code: "file:line:column" },
        ". The model does not decide whether the file conforms, and does not need to be trusted about it: same file, same answer, ",
        { b: "every run" },
        ". Every query takes ",
        { code: "--json" },
        " carrying file and line, so nothing is re-read to be believed.",
      ] as Rich,
    },
    {
      icon: "🛑",
      kicker: "Refused, not reviewed",
      heading: "The cheapest refusal is the one before the prose",
      body: [
        "Fields are validated at insertion and the write is ",
        { b: "all-or-nothing" },
        ": an over-length ",
        { code: "why" },
        " exits 2 naming the length and the limit, and ",
        { b: "nothing reaches the file" },
        ". A retry costs a field. A review costs the turn that wrote it.",
      ] as Rich,
    },
    {
      icon: "🧾",
      kicker: "One call, three files",
      heading: "No multi-file edit to get right",
      body: [
        { code: "ship <id>" },
        " writes the ledger entry, clears the roadmap line, drops the rationale section and re-annotates every dependent — ",
        { b: "all of them or none" },
        ". Four edits an agent would otherwise plan, execute and verify become one command and one event line.",
      ] as Rich,
    },
    {
      icon: "🪶",
      kicker: "No setup turn",
      heading: "argparse and tomllib. That is the whole stack.",
      body: [
        { b: "Zero runtime dependencies" },
        " — not ",
        { code: "click" },
        ", not ",
        { code: "pydantic" },
        ". Nothing to resolve means one ",
        { code: "uvx" },
        " line runs the gate with no install and no checkout, and it governs ",
        { b: "the Markdown you already have" },
        ": no migration, no store, no service.",
      ] as Rich,
    },
    {
      icon: "📐",
      kicker: "The config is governed too",
      heading: "A limit is declared against the reading that decides it",
      body: [
        { code: "config" },
        " prints every table, key and default your ",
        { code: "roadkeep.toml" },
        " may carry. ",
        { code: "govern <key> <n>" },
        " takes the ",
        { b: "reading and the number in one call" },
        " — and ",
        { b: "refuses a limit the corpus already breaks" },
        ", because one whose first act is a finding is one somebody lowers, reads the report and raises again. ",
        { code: '--because "…"' },
        " keeps your argument in comments ",
        { b: "above the number" },
        ", and the read hands it back.",
      ] as Rich,
    },
    {
      icon: "🤝",
      kicker: "More than one session",
      heading: "Two agents on one tree do not collide",
      body: [
        { code: "claim" },
        " says which lines a worker is holding and ",
        { b: "what its commit owns" },
        "; every write prints the ",
        { code: "git add --" },
        " line for exactly what it wrote. So a second session's work is not swept into your commit, and a line somebody else is on comes back named rather than silently overwritten. ",
        { code: "merge" },
        " is git's own driver for a governed file: ",
        { b: "entries by id" },
        ", so two branches appending under one heading is two additions and not a conflict.",
      ] as Rich,
    },
  ],
} as const;

/* ------------------------------------------------------------------ the differentiator */

export const compare = {
  eyebrow: "The differentiator",
  heading: "Everything else in this space reports. roadkeep refuses.",
  paragraphs: [
    [
      "Linters, kanban files, ADR sets — all of them are read ",
      { b: "after" },
      " the text exists. That is one position on a timeline, and for a model it is the expensive one: the report arrives when the output tokens are already spent.",
    ],
    [
      "roadkeep is the only one that sits ",
      { b: "at the write path" },
      ", which is also the only position from which an ",
      { i: "agent" },
      " can be constrained cheaply. And a line that never got long is a line ",
      { b: "nothing has to re-read" },
      " — the saving compounds on every later turn, not just the one that wrote it.",
    ],
  ] as Rich[],
  terminal: {
    title: "the timeline of one line",
    lines: [
      [{ g: "roadkeep add" }, "     ", { c: "← refuses here.  paid: one field" }],
      ["   │"],
      ["   ├─ the turn writes the prose"],
      ["   ├─ ", { dim: "Vale / markdownlint" }, "  ", { c: "← reports here" }],
      ["   ├─ ", { dim: "pull request review" }, "  ", { c: "← reports here" }],
      ["   └─ ", { dim: "…6 months of backlog" }, " ", { c: "← nobody reports" }],
      ["                    ", { c: "paid: the turn — then paid again" }],
      ["                    ", { c: "      to read it back, every turn" }],
    ] as TermLine[],
  } as Terminal,
  table: {
    eyebrow: "Honest comparison",
    heading: "The space around this is not empty",
    intro: [
      "So the comparison is a narrow one, and each of these is ",
      { b: "good at what it does" },
      ".",
    ] as Rich,
    columns: ["Tool", "What it does well", "Why roadkeep is not it"],
    rows: [
      {
        who: ["markdownlint"] as Rich,
        good: "Structure and style of Markdown",
        why: [
          "Explicitly ",
          { b: "not prose" },
          " — it will never tell you a sentence is too long",
        ] as Rich,
      },
      {
        who: ["Vale"] as Rich,
        good: "Prose rules and style guides",
        why: [
          "A linter: it reports ",
          { b: "after the text exists" },
          ", which is the cost being avoided",
        ] as Rich,
      },
      {
        who: ["Backlog.md, taskmd, the markdown-task family"] as Rich,
        good: "Mature task management, kanban, MCP",
        why: [
          "One ",
          { code: ".md" },
          " ",
          { b: "file per task" },
          ", with acceptance criteria and DoD — more room, and more room invites more prose",
        ] as Rich,
      },
      {
        who: ["ADR / MADR"] as Rich,
        good: "Rationale that survives; superseded is never deleted",
        why: [
          "roadkeep keeps the decision too — ",
          { b: "one line, not one file" },
          ", written by the ",
          { code: "ship" },
          " that took it. An ADR set grows ",
          { b: "monotonically" },
          "; that curve ",
          { i: "is" },
          " the 539 KB below",
        ] as Rich,
      },
      {
        who: ["Jira, Linear, GitHub Issues"] as Rich,
        good: "Planning across a company, at scale",
        why: [
          "A backlog that lives in a service is one an agent ",
          { b: "cannot grep" },
          " — and every read is a round trip",
        ] as Rich,
      },
    ],
    note: [
      "roadkeep composes with all five. It owns four files; it asks for nothing else.",
    ] as Rich,
  },
} as const;

/* ------------------------------------------------------------------ how it works */

export const howItWorks = {
  eyebrow: "How it works",
  heading: "A whole task is four calls",
  intro: [
    "Nothing to learn and nothing to remember — a shape: ",
    { b: "ask what to work on" },
    ", ",
    { b: "write the line" },
    ", ",
    { b: "ship it" },
    ", ",
    { b: "prove nothing drifted" },
    ".",
  ] as Rich,
  steps: [
    {
      verb: "brief",
      body: [
        "What to work on and ",
        { b: "everything it costs to start it" },
        " — line, rationale, deps resolved, blockers, non-goals.",
      ] as Rich,
    },
    {
      verb: "add",
      body: [
        "Compose the line. The ",
        { b: "field" },
        " is refused, never the sentence — and the id, pointer and annotations are derived.",
      ] as Rich,
    },
    {
      verb: "ship <id>",
      body: [
        "Three edits across three files, ",
        { b: "all of them or none" },
        ", plus every dependent's annotation.",
      ] as Rich,
    },
    {
      verb: "lint",
      body: [
        "Exit ",
        { b: "1" },
        " when anything drifted, naming ",
        { code: "file:line:column" },
        ". That exit code is the contract.",
      ] as Rich,
    },
  ],
  terminal: {
    title: "the same task T1, from picked to gated",
    lines: [
      [
        "$ roadkeep ",
        { g: "brief" },
        "        ",
        { c: "# the whole start of a task, in one tool result" },
      ],
      ["T1  Block A  📋  ready  docs/ROADMAP.md:5"],
      ["  picked   lowest ready id"],
      ["  symptom  Every read of the cache layer serialises through one lock"],
      [
        "  why      the second option avoids touching the scheduler nobody owns, and needs no migration.",
      ],
      ["  unblocks 1 of 1 open: T2"],
      [
        "  not      No cache rewrite                 ",
        { c: "# the non-goals, every time" },
      ],
      ["  not      No new dependency"],
      [""],
      ["### §T1 One lock, three options              ", { c: "# its rationale, inlined" }],
      [""],
      ["One lock serialises every read, so the second option is chosen because it avoids"],
      ["the scheduler nobody owns and needs no migration."],
      [""],
      ["$ roadkeep ", { g: "ship" }, " T1      ", { c: "# three files, one transaction" }],
      ["T1 → docs/CHANGELOG.md:5 under Block A"],
      ["  removed  docs/ROADMAP.md:5"],
      ["  dropped  §T1 (5-9) from docs/IMPROVEMENTS.md"],
      ["  derived  T2 (dep annotations re-derived)"],
      ["  event    T1  Block A  open"],
      [""],
      ["$ roadkeep ", { g: "lint" }, "         ", { c: "# the gate, before the turn ends" }],
      ["docs/ROADMAP.md, docs/CHANGELOG.md, docs/IMPROVEMENTS.md:"],
      ["2 line(s), 1 section(s), ", { ok: "clean" }, "            ", { c: "# exit 0" }],
    ] as TermLine[],
  } as Terminal,
  note: [
    "That is a task started ",
    { b: "without opening a file" },
    ". Every command takes ",
    { code: "--json" },
    " carrying which file and which line the answer came from — because an answer an agent cannot audit gets verified by reading the file, which is the cost the command existed to remove.",
  ] as Rich,
} as const;

/* ------------------------------------------------------------------ the decision, kept */

export const decisions = {
  eyebrow: "The decision, kept",
  heading: "The rationale is deleted. The decision it reached is not.",
  intro: [
    { code: "ship" },
    " drops the design section — that is the point, and it is why ",
    { b: "IMPROVEMENTS.md" },
    " does not become the 539 KB below. But the ",
    { i: "verdict" },
    " inside it outlives the work, and it used to go wherever the author happened to put it.",
  ] as Rich,
  terminal: {
    title: "one transaction, four files",
    lines: [
      [
        "$ roadkeep ",
        { g: "ship" },
        ' T1 --why "…" ',
        { g: "--decides" },
        ' "…"',
      ],
      ["T1 → docs/CHANGELOG.md:5 under Block A"],
      ["  removed  docs/ROADMAP.md:5"],
      ["  dropped  §T1 (5-8) from docs/IMPROVEMENTS.md"],
      [{ b: "  decided  docs/DECISIONS.md:5" }],
      ["  stage    git add -- docs/CHANGELOG.md docs/DECISIONS.md"],
      ["                      docs/ROADMAP.md docs/IMPROVEMENTS.md"],
      ["  event    T1  Block A  live"],
      [""],
      ["$ roadkeep ", { g: "supersede" }, " T1 --by T2"],
      ["docs/DECISIONS.md:5  T1 superseded by T2"],
      [
        "  - ",
        { dim: "🗑" },
        " ",
        { b: "T1" },
        " ",
        { b: "Every read of the cache layer serialises" },
      ],
      [
        { b: "    through one lock" },
        " — Reads go through a striped lock;",
      ],
      ["    the scheduler is not touched ", { dim: "(superseded by T2)" }, "."],
      [{ ok: "  kept" }, "     T2 stands and T1 is history — nothing"],
      ["           in this file is ever deleted"],
    ] as TermLine[],
  } as Terminal,
  card: {
    kicker: "DECISIONS.md · a governed role",
    heading: "An ADR that is one line, written by the command that took it",
    body: [
      "A decision cannot be filed after the fact, because after the fact is when nobody remembers it — so it is ",
      { b: "taken with the same call that deletes the design" },
      ", in the same transaction. ",
      { code: "supersede" },
      " marks one replaced by another and ",
      { b: "deletes nothing" },
      ": the row stays, marked 🗑, carrying the id that replaced it. ",
      { code: "reversals" },
      " reads them back — what this ledger already decided and undid, with the argument.",
    ] as Rich,
    aside: [
      "And it is optional. ",
      { code: "declare decisions" },
      " adds the role to a project already configured; a repository that wants none never sees it.",
    ] as Rich,
  },
} as const;

/* ------------------------------------------------------------------ the problem, measured */

export const evidence = {
  eyebrow: "The problem, measured",
  heading: "This did not start as an idea",
  intro: [
    "It started as three readings from ",
    { b: "a real production repository" },
    " where every one of these files declared a format, none of them enforced it, and an agent paid for all three.",
  ] as Rich,
  ruleLabel: "Declared rule:",
  readings: [
    {
      file: "docs/ROADMAP.md",
      figure: "142",
      unit: "words",
      caption: [
        "average, across 92 task lines — worst line ",
        { b: "1406 characters" },
      ] as Rich,
      rule: ["one sentence per task."] as Rich,
    },
    {
      file: "agents.md",
      figure: "186",
      unit: "KB",
      caption: ["≈ ", { b: "46k tokens" }, ", loaded on every single turn"] as Rich,
      rule: ["an index, nothing more."] as Rich,
    },
    {
      file: "docs/IMPROVEMENTS.md",
      figure: "539",
      unit: "KB",
      caption: [
        "in a sibling project — rationale that was ",
        { b: "never dropped" },
      ] as Rich,
      rule: ["rationale for ", { i: "unshipped" }, " work."] as Rich,
    },
  ],
  finding: {
    lead: [
      {
        b: "The finding that decided the design: six of the eight worst lines were written in the session that then diagnosed the problem.",
      },
    ] as Rich,
    body: [
      "This is not inattention. An author — human or model — who has the whole design in working memory will write it down where the reader is. An instruction to be terse does not survive the moment its author knows more than the line allows. So roadkeep also holds a ",
      { b: "byte and line budget" },
      " on the instruction files nobody edits on purpose.",
    ] as Rich,
  },
} as const;

/* ------------------------------------------------------------------ install */

export const install = {
  eyebrow: "Get started",
  heading: "Two commands, and the repository carries the rest",
  intro: [
    "Python ≥3.11 and nothing to resolve. ",
    { b: "Nothing is installed and nothing joins your PATH" },
    " — and it reads the Markdown you already have, so there is no migration to plan.",
  ] as Rich,
  steps: [
    {
      heading: "Install the plugin, in Claude Code",
      body: [
        "Hook, MCP server, skill and slash commands — the enforcement point ",
        { b: "an agent cannot route around" },
        ", and the schema it calls with. ",
        { b: "The package ships inside it" },
        ", so there is no second thing to install: ",
        { code: "roadkeep guard" },
        " and ",
        { code: "roadkeep mcp" },
        " ",
        { i: "are" },
        " the CLI, and the plugin already carries it.",
      ] as Rich,
      commands: [
        "/plugin marketplace add alegauss/roadkeep",
        "/plugin install roadkeep@alegauss",
      ],
      after: [
        [
          "From a shell instead, the same two with ",
          { code: "claude plugin … --scope project" },
          " write both declarations into that repository's ",
          { code: ".claude/settings.json" },
          " — commit it and ",
          { b: "every clone is wired" },
          ", with no per-machine step.",
        ],
      ] as Rich[],
    },
    {
      heading: "Measure before you commit to it",
      body: [
        { code: "adopt" },
        " runs the schema over the backlog you already have and reports the delta: what parses, the longest ",
        { code: "symptom" },
        ", ",
        { code: "why" },
        " and rendered line against their limits, the markers to declare. It ",
        { b: "writes nothing and never exits 1" },
        " — an estimate that is a gate is one you took too late. It runs ",
        { i: "before" },
        " the project is governed, so it is the one step that wants a shell.",
      ] as Rich,
      commands: [
        "uvx roadkeep adopt docs/ROADMAP.md --prefix XX",
        "uvx roadkeep adopt docs/IMPROVEMENTS.md --sections --with docs/STRATEGY.md",
      ],
      after: [
        [
          "Both halves, because both are limits you have to declare — and the numbers ",
          { code: "[limits]" },
          " gets set from come from ",
          { b: "your" },
          " corpus rather than copied from this one.",
        ],
        [
          "No ",
          { code: "uv" },
          " on the machine? The plugin you just installed carries the same engine, so nothing has to be fetched: ",
          { code: "python ~/.claude/plugins/marketplaces/alegauss/scripts/roadkeep.py adopt …" },
          ".",
        ],
      ] as Rich[],
    },
    {
      heading: "Declare the format once",
      body: [
        { code: "init" },
        " writes ",
        { code: "roadkeep.toml" },
        " — your prefix, paths, markers and limits — and the governed files it declares. ",
        { b: "No starter task and no prose" },
        ": a title, the blocks you name, and where the non-goals go. On a repository with no backlog yet, this is the only step of the two you need.",
      ] as Rich,
      commands: ['uvx roadkeep init --prefix XX --block "A — <label>"'],
      after: [
        [
          "Everything a ",
          { i: "task" },
          " needs afterwards is already in the tools the plugin installed — ",
          { code: "add" },
          ", ",
          { code: "status" },
          ", ",
          { code: "ship" },
          ", ",
          { code: "brief" },
          ", ",
          { code: "pick" },
          ", ",
          { code: "lint" },
          " — validating against the schema ",
          { code: "roadkeep.toml" },
          " just declared. No shell, no ",
          { code: "PATH" },
          ".",
        ],
        [
          "Nothing here is one-way. ",
          { code: "declare <role>" },
          " adds a governed file to a project that is already configured — a strategy document, a deferred list, the decisions above — writing its file and the one key, and leaving every other byte of your config alone. ",
          { code: "govern" },
          " moves the numbers afterwards, against the reading that decides each one.",
        ],
      ] as Rich[],
    },
  ],
  gate: {
    heading: "Make it a gate",
    body: [
      "The same command in CI and at the commit — ",
      { b: "a gate that runs in one place is a gate with a documented bypass" },
      ". ",
      { code: "--fix" },
      " repairs only what the format derives and leaves every editorial finding to a human.",
    ] as Rich,
    terminal: {
      title: ".github/workflows/gate.yml · .pre-commit-config.yaml",
      lines: [
        [
          "- uses: ",
          { g: "alegauss/roadkeep@v0.2.0" },
          " ",
          { c: "# the action this repo ships" },
        ],
        [""],
        ["repos:"],
        ["  - repo: https://github.com/alegauss/roadkeep"],
        [
          "    rev: v0.2.0                   ",
          { c: "# a release tag; main tracks unreleased" },
        ],
        ["    hooks:"],
        ["      - id: ", { g: "roadkeep-lint" }, "          ", { c: "# or roadkeep-lint-fix" }],
      ] as TermLine[],
    } as Terminal,
  },
  foot: [
    "Or keep it to one command in an existing pipeline, with no plugin and no checkout: ",
    { code: "uvx roadkeep lint" },
    " — exit ",
    { b: "0" },
    " clean, ",
    { b: "1" },
    " drifted. It is on ",
    { a: "PyPI", href: pypiUrl },
    ", so that line resolves a name and not a URL, and ",
    { code: "pip install roadkeep" },
    " pulls the package alone — zero runtime dependencies means there is nothing else to resolve.",
  ] as Rich,
  // Written as a sentence rather than as another button, and this is the reason: the nav and
  // both calls to action are subtrees the Markdown twin drops whole, so a reader that is not a
  // browser would have finished this page without ever learning the area exists. A paragraph
  // survives the conversion, which is the only shape of link that reaches them.
  docs: [
    "What each verb takes, what every finding code means and what an adoption actually printed are in the ",
    { a: "documentation area", href: "/roadkeep/docs/" },
    " — generated from this parser and this gate rather than written beside them, so a page cannot state a flag the tool does not answer. ",
    { b: "Evaluation comes before installation" },
    ", so it reads without one.",
  ] as Rich,
} as const;

/* ------------------------------------------------------------------ laws and non-goals */

export const laws = {
  eyebrow: "The six laws",
  heading: "A change that breaks one is wrong, even if requested",
  intro: [
    "L4 is the one people try to relax first. A generator that writes the symptom for you would reintroduce ",
    { b: "exactly the drift this exists to stop" },
    ".",
  ] as Rich,
  items: [
    {
      id: "L1",
      text: [
        "The format is a schema, ",
        { b: "enforced where the text is created" },
        "; ",
        { code: "lint" },
        " is only the backstop.",
      ] as Rich,
    },
    {
      id: "L2",
      text: [
        { b: "The store is the repository" },
        " — Markdown, greppable, diffable. No database, no service.",
      ] as Rich,
    },
    {
      id: "L3",
      text: [
        { b: "Round-trip or don't write" },
        " — parse → render → byte-identical.",
      ] as Rich,
    },
    {
      id: "L4",
      text: [{ b: "The tool never writes prose" }, " — it validates and renders."] as Rich,
    },
    {
      id: "L5",
      text: [{ b: "Query instead of read" }, " — every question is a command."] as Rich,
    },
    {
      id: "L6",
      text: [
        { b: "Configuration, not convention" },
        " — prefix, paths, markers and limits are per project.",
      ] as Rich,
    },
  ],
} as const;

export const nonGoals = {
  eyebrow: "Non-goals",
  heading: "These are binding, and half the point",
  intro: [
    "What a tool refuses to become is the reason it stays small enough to trust.",
  ] as Rich,
  items: [
    [
      { b: "No web UI and no server." },
      " Files and a CLI; the MCP server binds nothing and stores nothing.",
    ],
    [
      { b: "No issue-tracker sync." },
      " A backlog that lives in a service is one an agent cannot ",
      { code: "grep" },
      ".",
    ],
    [
      { b: "No model and no prompts inside the tool." },
      " It validates and renders; it never writes the symptom or the rationale.",
    ],
    [{ b: "No dates, quarters or estimates." }, " A marker is maturity, not a schedule."],
  ] as Rich[],
} as const;

/* ------------------------------------------------------------------ proof + closing */

export const proof = {
  eyebrow: "Proof, not a promise",
  heading: "The format is proven by the artefact, not asserted in a README",
  paragraphs: [
    [
      { code: "roadkeep lint" },
      " must pass on this repository's own ",
      { code: "docs/" },
      ", under this repository's own ",
      { code: "roadkeep.toml" },
      ", and the test suite asserts it. A limit that cannot express these lines is ",
      { b: "the wrong limit, not a set of wrong lines" },
      " — and round-trip is a property test over real roadmaps, including two this project does not own: parse → render → ",
      { b: "byte-identical" },
      ", or the write is refused.",
    ],
    [
      "And when the tool is what is wrong, the refusal says so: every failure prints the ",
      { code: "report" },
      " line that files it — the argv, the config, the governed files — ",
      { b: "as facts a replay re-runs" },
      " against whatever tree is there later. A bug report that is a paragraph is one nobody can reproduce; this one is an input.",
    ],
  ] as Rich[],
} as const;

export const closing = {
  heading: "Give Claude Code its context back",
  body: [
    "One config file, four commands, and a plugin that makes calling them cheaper than editing the file by hand. The format stops being something a turn ",
    { b: "spends tokens remembering, writing and checking" },
    ", and becomes something a subprocess decides — while your Markdown stays greppable, diffable and readable by anyone who never installs this.",
  ] as Rich,
  ctas: [
    { href: "#install", label: "Install the plugin →", kind: "primary" },
    { href: "/roadkeep/docs/", label: "Read the docs →", kind: "ghost" },
    { href: repoUrl, label: "★ Star it on GitHub", kind: "ghost" },
  ],
} as const;

/* ------------------------------------------------------------------ sponsor + footer */

// Generated from alegauss.github.io/sponsor.json by scripts/sync-sponsor.mjs. Edit the JSON,
// not this block. Kept as rendered markup on purpose: a runtime fetch would keep the sponsor
// out of the HTML that crawlers and LLMs actually read.
export const sponsor = {
  label: "Sponsored by",
  name: "Viglet",
  href: "https://www.viglet.org",
  mark: { src: "/roadkeep/viglet/viglet-logo.png", alt: "Viglet logo" },
  blurbLead:
    "Open source search and content tools for organisations with a lot to publish — run on your own servers, with no per-user licence. More at ",
  blurbLink: { label: "viglet.org", href: "https://www.viglet.org" },
  products: [
    {
      href: "https://turing.viglet.org",
      src: "/roadkeep/viglet/turing-logo.png",
      alt: "Viglet Turing ES logo",
      name: "Viglet Turing ES",
      note: "so visitors find what they came for, with AI answers drawn only from your own content",
    },
    {
      href: "https://shio.viglet.org",
      src: "/roadkeep/viglet/shio-logo.png",
      alt: "Viglet Shio CMS logo",
      name: "Viglet Shio CMS",
      note: "so a new page goes live the same day, reviewed and approved by your own team",
    },
  ],
} as const;

export const footer = {
  brand: "roadkeep",
  links: [
    { href: repoUrl, label: "GitHub" },
    { href: "/roadkeep/docs/", label: "Docs" },
    { href: `${repoUrl}/blob/main/docs/ROADMAP.md`, label: "Roadmap" },
    { href: `${repoUrl}/blob/main/docs/CHANGELOG.md`, label: "Changelog" },
    { href: `${repoUrl}/blob/main/docs/IMPROVEMENTS.md`, label: "Design rationale" },
    { href: "/roadkeep/llms.txt", label: "llms.txt" },
  ],
  disclaimer:
    "Every command output on this page was run against this repository or a scaffolded one. Shipped as a Claude Code plugin; not affiliated with, endorsed by, or sponsored by Anthropic. “Claude” and “Claude Code” are trademarks of Anthropic. © 2026 Alexandre Oliveira. Apache-2.0.",
} as const;
