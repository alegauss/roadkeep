# Improvements

## Block A — The client (payloads in, types out)

## Block B — Discovery (which checkouts on this machine are governed)

## Block C — The portfolio (many backlogs in one view)

## Block D — The project surface (one backlog, read)

## Block E — The write path (the app composes an argv; the command writes)

## Block F — The agent surface (handing one task to Claude Code)

### §RG274 Continued in VS Code, by the session's own id

The Claude Code extension registers a URI handler. Read in 2.1.274's `extension.js`:
`vscode://anthropic.claude-code/open` takes `session` and `prompt`, drops a `session`
that does not parse as an id, and runs `claude-vscode.primaryEditor.open`, which creates
a panel. A `prompt` is only typed into the input box, never sent. Every session record
here already carries its `sessionId`.

**Measured before it was built, and it did not answer.** On 2026-09-17, on Windows with
2.1.274 installed and a real session of this repository: the folder link and then the
session link, the same link again through `code --open-url`, and a third once VS Code
had remembered the permission. No panel opened on any of the three, and nothing said
why. So this is not an action to offer yet — a button that does nothing is worse than no
button.

**What it is once it answers.** Offered on a session that is not running, beside RG269's
reply: two processes appending one transcript is what that avoids. Nothing is sent from
here, and continuing is the person's next message, typed there. `shell` opens it with
`shell.openExternal` and spawns nothing, with no `code` on PATH; the action is offered
only where `app.getApplicationNameForProtocol` names a `vscode:` handler. Turns taken in
VS Code are in the transcript, so a later reply from here carries them, but this
screen's stream does not show them.

**What a resume asks first.** Why the panel never opened, which window answers a link,
and whether the session's own folder has to be open in it.

### §RG278 Resetting the session cards from the command palette

VS Code offers View: Reset View Locations from its command palette. The session screen's
cards have the title menu and the Settings button that part of this line built
(`session-cards.tsx`, `Settings.tsx`), and no palette command.

The palette cannot hold one yet. `BentoCommandPalette` takes the nav surfaces and one
product `group`, and the line search already fills that group: a command put in it would
be listed under the heading that counts the backlogs searched. A nav item is a route and
not an action.

So this half waits on the design system: a second group, or a list of commands the
palette matches like its surfaces. When that ships, the command calls the `putCardsBack`
in `Settings.tsx`, which writes `DEFAULT_SETTINGS.sessionLayout` back whole, and is not
offered while `sameLayout` says the arrangement is the default. Its name comes from the
catalogue in both languages.

Done when a test moves `handed` through the menu, resets from the palette, and sees the
default drawn and written.

### §RG299 A block around Prose, not a paragraph

`Prose` draws a `div` holding one `p` per paragraph. `explained.tsx` puts it inside a
`p` in three places — the headline, each place under where the work lands, each
non-goal's account — so the page holds a `div` and a `p` inside a `p`. React reports
both as invalid HTML on every answer drawn, and a browser may close the outer paragraph
early.

**A block around a block.** The three wrappers become `div`s with the same classes: the
wrapper carries the size and the colour, and `Prose` carries the paragraphs.

**Caught where it can be.** jsdom builds the tree as React wrote it and says nothing, so
the explanation's tests gain an assertion that no `p` in the dialog holds a `p` or a
`div`.

Done when that assertion holds for a gloss filling every slot, and the running window
logs no nesting error when an answer is drawn.

### §RG301 The module that outgrew the question it was named for

`gloss-process.ts` was one question asked of Claude Code and everything in it was named
after that question. RG291 added a second — a walkthrough over a shipped commit — and it
is asked through `askGloss`, with a `GlossCall`, answering a `GlossRead` over a
`GlossRun`. Nothing about the mechanism is a gloss: it is one read-only query, a schema,
a tool list and a gate.

**The file is right and the words are wrong.** A second module would duplicate a hundred
lines of spawn plumbing under Electron — the pipes, the `error` that means no `claude`,
the abort a cancel turns into — which is the drift the one call exists to prevent. So
this is a rename and not a split: the module keeps its shape and loses the name of the
first question that used it.

**What it becomes is the open half.** `askQuestion` over a `Question` is one reading;
`ask` beside the existing `askGloss` is another, keeping the gloss's own door. Whatever
it is, `GLOSS_TOOLS` and `GLOSS_TURNS` go with it, `gloss-live.test.ts` and
`walkthrough-live.test.ts` both call it, and `glosses.ts` holds the one option typed as
`GlossCall`. `ReadOutcome` is taken in `core`, so a `ReadCall` here would be a second
meaning of one word a package over.

Done when no name on the path a walkthrough takes says gloss, both live files and
`glosses.ts` call it by that name, and the gloss's own module still reads as the one
question it is.

## Block G — The shell (an executable now, a service later)

### §RG49 The signature, and what it needs that code cannot supply

Signing is not work that can be finished by writing anything: it needs a certificate
somebody bought, held somewhere a build can reach. So the line states the requirement
and is set aside for a caller that says it has one, rather than coming back as the next
ready task forever. What can be built without it is the pipeline that would use it, and
the about surface saying plainly that this build is unsigned — which is the honest half
and is worth having on its own.

### §RG298 The switches declared before the first start

`dev.ts` starts the window with `let child = start()` and declares the switches `start`
passes a few lines later. The bundle turns both into `var`, so the first call reads
`switches` as `undefined` and Electron opens with no `--remote-debugging-port`. Only a
window the watcher restarts gets it, which is why touching a source under
`packages/shell/src` made port 9333 answer when RG297's waiting dialog was looked at.

**Declared before the first start.** The switches move above `start()`, where the
compiler holding source order is the whole fix.

**Held by the test that already attaches.** `playwright-mcp-live.test.ts` holds that
Playwright MCP reaches this app; it reaches a restarted window. It gains the case the
skill actually describes: `npm run dev:inspect`, nothing touched, and the port answers.

Done when a freshly started `npm run dev:inspect` answers on 9333 before any source
changes.

### §RG300 Why a kept gloss needs a picture of its own

`TASK_SHOTS` opens the explain dialog twice, and both times on a gloss the scripted
agent has just answered. A fresh answer is neither stale nor written under an earlier
shape, so the two notices that say a kept gloss is old are drawn by nothing any picture
shows — the state exists only in jsdom, which lays nothing out, and that is the gap `npm
run shots` was built to close.

**A third state, not a third surface.** The shots harness already photographs the
dialog; what it lacks is a run where the store holds something. The cheapest honest way
is what RG287 keeps anyway: write a gloss into the machine's own file before the
capture, with a shape this build has widened past and a line the fixture then leaves
alone, and open the dialog on it. The capture is `explain-old` beside `explain` and
`explain-where`, so one name covers both sentences and neither needs its own run.

**Both sentences in one picture is the point.** They are two blocks stacked in the same
place, each a border and a tinted panel, and the layout question is what they do to each
other and to what follows at 400 wide. A state that showed one would answer half of it.

Done when a shots run writes `project-task.explain-old.*` in both grounds, both
languages and both widths, its axe scan is clean, and the picture shows both notices
above the reading they are about.

## Block H — The look (a design system for governed prose)

### §RG62 Joining the checks the other consoles already answer to

Depending on the design system is half of consuming it. The other half is the two
mechanisms Shio and Dumont run.

**The gate is done.** `viglet-ds-check-duplicates` is wired into `npm run lint` over the
three source roots, and a test plants a duplicate and requires it to be found — because
a gate pointed at the wrong directory reports a clean tree in exactly the same words as
a clean tree, which is what both consoles learned the hard way.

**Registration is not, and is deliberately not.** The package's `consumers.json` is the
declared set it holds itself to, and its own reasoning says prose naming a subset as
though it were the whole is a test failure. The entry this app wants is:

```
{ "id": "roadkeep-gui", "name": "roadkeep", "package": "@rk/ui",
  "framework": "vite", "chrome": "console",
  "entries": [".", "./styles", "./fonts", "./preset"] }
```

`accent` is the field to stop at. Every one of the six consumers records `cool`, and the
file says so on purpose: the accent was made a token so a product could re-key without
forking a header, and none had. This app has — amber, in its own `:root`. So adding it
is not a row, it is the first case that file was written to anticipate, and the parity
digest is then required to carry that set.

That is a commit in somebody else's repository with a consequence for five other apps,
which is why it is written down here rather than made quietly.

## Block I — Validation (the list a person works through)

### §RG293 The list, beside the ledger it comes from

`ProjectTabs` already draws the four governed files beside the roadmap, the changelog
among them as `list --role changelog`. What is shipped and unlooked-at is a narrowing of
that same file, so it belongs there: one more tab reading `unvalidated`, not a second
window and not a filter nobody finds.

**Newest first**, against the block order every other tab uses. The reason is the
deferred tab's: what somebody will actually validate is what they just shipped, while
they still remember what it was for, and block order buries that under whatever Block A
left behind.

**A row is the id, the symptom and the block, and opening one is what asks.** Nothing is
asked for a list being scrolled past — the same rule the improvements tab follows for
its sections, and the reason a walkthrough costs tokens is the reason it is never
speculative.

An empty list is a state and says so: every entry since validation started has a
verdict, which is the screen this whole block exists to produce.

Done when the tab draws a fixture's unvalidated entries newest first, an empty one says
so, and the shots read in both grounds, both languages and at both widths.

### §RG294 Saying what happened

The walkthrough is a read; this is the write it exists for. Under the steps, three
answers — **it worked**, **it did not**, **there is nothing to see** — each opening the
same small form for one sentence: what the person did and what they saw.

**The sentence is required.** A verdict with no account is a tick box, and a ledger full
of bare verdicts is the thing this block was meant to replace. The engine holds the
limit and this app does not copy it: a refused sentence comes back as its code and
field, and the door marks it, which is RG5 working exactly as it was built to.

**`nothingToSee` pre-selects the third**, with the agent's own sentence already in the
box to accept or rewrite. That is the only place this app suggests an answer, and it
suggests the one that costs least to be wrong about — a walkthrough that was wrongly
skipped is a row somebody re-opens, not a false claim in the ledger.

On success the row leaves the list, because the list is a query and not a state this app
keeps.

Done when each of the three verdicts reaches a fixture ledger, and a sentence the engine
refuses marks the field rather than closing the sheet.

### §RG295 The defect a failure found

Somebody who says *it did not work* has just written the symptom of a task. Sending them
to the filing form to type it again is how the finding gets lost: they are
mid-procedure, not mid-backlog, and the sentence they already wrote is the one worth
keeping.

**One call files both.** The engine writes the verdict and the open line in a single
transaction, so this app passes the sentence it already holds and composes nothing — no
second call, no window where the verdict landed and the line did not. Where the
project's engine is older than the flag, `capabilities` withholds the offer and the
verdict is recorded alone; the app never simulates a transaction with two writes.

**The symptom is the person's, unedited.** `Filing` is offered afterwards to amend the
line, never before to compose it: a form standing in front of the sentence is a form
that stops somebody reporting.

Done when a failed verdict leaves both the verdict and a new open line under the same
block in a fixture, and a project whose engine lacks the flag leaves only the verdict,
with the offer absent rather than refused.

### §RG296 Where somebody is owed a walkthrough

The portfolio is why this app exists: twenty backlogs, one view. A row says what is open
and what is next, and after this block the number that matters most is a third one —
what shipped and nobody has looked at. That is where the work now is, and it is
invisible until somebody opens the project one at a time, which is the reading this
screen was built to replace.

**Off the count the engine already answers**, so this is a field on a row and not a
second read. The portfolio composes its rows from one call per project, and a call per
project is the cost RG7 and RG8 exist to hold down.

**Withheld, not zeroed**, on a project whose engine cannot say. A blank reads as *this
build does not answer that*; a `0` would be a claim, and the wrong one — an old engine
has no verdicts precisely because it has no way to record any.

Done when a fixture with two unvalidated entries draws the figure, a project on an older
engine draws none, and the shots read at both widths.
