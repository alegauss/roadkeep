# Roadmap (active backlog)

## Priority

## Block A — The client (payloads in, types out)

- 📋 **RG158** (deps: RG141 ✅) **two live assertions pass unchecked: a picked line with no tier, and a combined filter that selects nothing** — RG141 made tier nullable and moved the filter off Block A, and neither assertion was tightened after it. → §RG158
- 📋 **RG159** (deps: RG142 ✅) **the empty-brief contract asserts lacking on a fixture that never has any, so no lacking line is ever read** — Array.isArray on a field that defaults to an empty list cannot fail, and no fixture requires what the caller lacks. → §RG159
- 📋 **RG160** (deps: RG137 ✅) **openHere's own unheld wiring is never run by a test, since RG137's live case rebuilds it by hand** — The test wires unheldAmong around openProject itself, so the production line can break with every test green. → §RG160

## Block B — Discovery (which checkouts on this machine are governed)

- 📋 **RG164** (deps: —) **the carrier keeps its catalogue in memory, so RG14's record is never written and every launch walks every root first** — catalogueFrom reads a record back and nothing in shell writes one, so the first screen waits on the disk and a missing project is forgotten at quit. → §RG164
- 📋 **RG169** (deps: —) **a root is added two levels deep and no control changes it, so worktrees three levels down still need the settings file** — The strip draws each root's depth and offers no way to move it, though addRoot already replaces a depth in place and keeps the order. → §RG169

## Block C — The portfolio (many backlogs in one view)

- 📋 **RG147** (deps: RG145 ✅, RG20 ✅, RG150, a grouped palette) **the palette says it finds a line in every backlog and lists only surfaces, so search over all projects reaches no one** — RG20's search reaches no screen, and the package palette only filters nav items. → §RG147
- 📋 **RG166** (deps: RG144 ✅) **every row's gate reads unknown, since the ledger RG18 built is fed by nothing a window runs** — recordGate and gateHealth are pure and tested, and no process runs lint for the portfolio or hands a verdict to the renderer. → §RG166
- 📋 **RG167** (deps: RG144 ✅) **a row is read once, so a line shipped in a terminal leaves the portfolio stale until the window reopens** — RG144 tells a screen when a project's files move, and the portfolio subscribes to nothing, so its counts outlive the backlog they came from. → §RG167

## Block D — The project surface (one backlog, read)

- ⏳ **RG28** (deps: roadkeep RK1677) **the deferred store has no order, so which pause has stood longest is a question only a terminal can ask** — How long each pause has stood, which --stale orders by and prints for a terminal, putting none of it in the payload. → §RG28
- 📋 **RG148** (deps: RG145 ✅, RG21 ✅, RG22 ✅, RG74 ✅) **a project cannot be opened in the window, so its lines, blocks and filters exist only as readers in core** — Projeto.dc.html draws one backlog as rows with readiness in the engine's words, and nothing routes from a portfolio row to it. → §RG148
- 📋 **RG149** (deps: RG148, RG27 ✅) **the changelog, decisions, improvements and deferred tabs are drawn as labels with nothing behind them** — RG27 and RG28 shipped readers for the ledger, the decisions and the paused lines, and the project surface draws only the roadmap. → §RG149
- 📋 **RG150** (deps: RG148, RG23 ✅, RG24 ✅, RG76 ✅) **a task opens nowhere in the window, so brief's join of deps, design and binding lists is read by nobody** — Tarefa.dc.html draws the detail as one brief read, and detailFrom already returns every part of it. → §RG150

## Block E — The write path (the app composes an argv; the command writes)

- 📋 **RG151** (deps: RG148, RG32 ✅, RG34 ✅, RG36 ✅, RG165) **no screen composes a write, so a line is still filed in a terminal though its budget, argv and doors are built** — Escrita.dc.html draws the form with counters, the command before it runs and the refusal's doors, and block E shipped each. → §RG151
- 📋 **RG152** (deps: RG151, RG33 ✅, RG165) **Run the gate is a button with nothing behind it, so a finding and the doors it names are still read in a terminal** — RG33 shipped findings as actions, and no screen draws one; the write path's doors column is the shape to reuse, not a second one. → §RG152
- 📋 **RG165** (deps: —) **a door the engine offers cannot run from a window, since the bridge refuses a verb or option its tables never compose** — A door is the engine's own argv, and RG143's guard runs only what VERBS and WRITES spell, so criterion add and install are withheld. → §RG165

## Block F — The agent surface (handing one task to Claude Code)

- 📋 **RG153** (deps: RG150, RG144 ✅, RG40 ✅, RG41 ✅) **nothing in the window hands a task to Claude Code or shows the session, so block F's acts and landings reach no one** — Sessao.dc.html draws the handover, the stream as acts and what moved in the backlog beside it, and every reader for them has shipped. → §RG153

## Block G — The shell (an executable now, a service later)

- ⏳ **RG49** (deps: RG46 ✅) (requires: signing-cert) **the executable is unsigned, so Windows tells a person the app is untrusted before it opens** — The certificate itself, chosen from docs/SIGNING.md, and the build wired to sign with it. → §RG49
- 📋 **RG128** (deps: RG120 ✅, roadkeep RK1678) **a checkout busy when the probe runs is skipped, so the launcher answers from a cache 446 versions old** — Resolution takes the first engine that answers, so a session can be briefed by a copy nobody chose. → §RG128
- 📋 **RG154** (deps: RG50 ✅, RG162) (requires: published-artifact) **the update check has only met answers written by hand, never GitHub's own for a published release** — No release is published yet, so the shape it reads and the page it opens are held by fakes until the first one exists. → §RG154
- 📋 **RG155** (deps: RG50 ✅) **the release-page guard compares a string prefix, so a release URL with dot segments opens another repository** — The URL comes off a network answer, and the browser normalises the dot segments after the guard approved the string. → §RG155
- 📋 **RG156** (deps: RG50 ✅) **the update check tells a build ahead of every release it is the newest, and hides why a check failed** — An ahead build reads as current and loses the version found, undici keeps the real cause on error.cause, and a body timeout reads as not JSON. → §RG156
- 📋 **RG157** (deps: RG50 ✅) **the tag-against-manifest check is tested by its text, so an inverted condition or a lost exit still passes** — The test finds the step's strings in ci.yml and never runs the script, which is the part that refuses. → §RG157
- 📋 **RG161** (deps: —) **the signing procedure breaks the Windows CI job on one route and leaves the app exe unsigned on another** — Certum's subject name is committed to the builder config, SignPath signs only the installer, and three sentences beside it are false. → §RG161
- 📋 **RG162** (deps: —) **no LICENSE file ships and every build says 0.0.0, so the first release the maintainer decided on cannot be cut** — SignPath needs a recognised licence file, and ci.yml refuses a tag naming a version the manifest does not carry. → §RG162

## Block H — The look (a design system for governed prose)

- 📋 **RG168** (deps: —) **an unreadable row's reason is composed in English in core, so a Portuguese window shows it untranslated** — Resolution and the opening write their own sentences into Unreadable.message, and the row draws that field whatever language is speaking. → §RG168

## Done when — Block A

- **The client runs with no Electron and no React** The transport is one interface, so
  the same reads answer in a main process, in a test runner and behind an HTTP handler
  without a line of the client changing.
- **Every payload this app reads is asserted against a live roadkeep** A key renamed
  upstream goes red in this project's own CI and not in a user's window, which is the
  promise roadkeep's editor surface already holds for its own client.
- **A refusal arrives as the field it is about** Every write returns a code and a field,
  so an over-length symptom is shown on the symptom box and never reaches the person as
  a paragraph of English in a toast.
- **No argv this app builds is ever handed to a shell** Every call spawns with shell
  false and argv as an array, and a test passes a string of metacharacters through the
  transport and asserts it arrives as one argument with nothing executed.

## Done when — Block B

- **The project list is the person's statement, never a scan's discovery** Roots, depth
  and what to skip are chosen and persisted, so nothing walks a drive unasked and no
  project appears that somebody did not name.
- **Which copy of roadkeep answered is on screen for every project** engines says three
  copies may differ and the unsurvivable thing is not knowing which one wrote, so the
  version, its home and its verdict sit beside the counts.
- **A path with no roadkeep is rejected by a probe, not by a failed read** A scan over
  hundreds of directories stays bounded and each rejection has a reason, so what looking
  costs is a function of candidates and never of files.

## Done when — Block C

- **Every number on this screen is one a verb printed** Counts, the next ready line and
  gate status come from stats, pick and lint, so nothing is summed across projects in a
  way no single project could reproduce.
- **A cold start over twenty projects is bounded and says what it is doing** Reads run
  in parallel under a ceiling and are cached against the files they came from, and a
  project still answering is drawn as pending rather than as zero.

## Done when — Block D

- **A task opens with everything starting it costs** The detail is brief's own join: the
  deps, the design section, what shipping it unblocks, and the criteria and non-goals
  that bind it, so the screen is one read and not six.
- **Readiness is never derived in this app** Whether a line is ready, blocked or waiting
  on a requirement comes from deps and pick, because a resolver rewritten in a client is
  the one that disagrees in silence.
- **The prose is shown as the file stores it** A section renders from the payload's own
  body with its wrapping intact, so what a reviewer reads on screen is what lint
  measured and what the commit will diff.

## Done when — Block E

- **Every input knows its budget before a word is typed** budget answers what the field
  has left on this line and the box counts down against it, while add still decides, so
  a refusal is rare and never a surprise.
- **A write is one command, shown before it runs** The argv the app composed is visible
  and copyable, so what happened is reproducible in a terminal and a person can read it
  before approving it.
- **The gate is a surface and not a report** A finding is drawn with its code, its file
  and line and the doors it names; a door the tool marked complete runs as one action
  and an incomplete one asks for the words only a person writes.

## Done when — Block F

- **A session starts from a brief, not from a prompt somebody typed** What is handed
  over is the payload brief returned for that task, so the agent begins with the design,
  the deps and the non-goals rather than a sentence about them.
- **What the session did to the backlog is visible without leaving the task** The
  governed files are watched while a session runs, so a marker moved or a line shipped
  appears beside the stream that caused it.
- **A held line is named before a second session is offered it** Claims are read and
  shown, so one task is never handed to two authors and a live claim is never re-dated
  to keep it.

## Done when — Block G

- **The renderer touches no filesystem and no process** Context isolation on, node
  integration off and one narrow typed channel, so the half a service would run in a
  browser already runs with a browser's powers.
- **Turning this into a service costs the transport and nothing else** The client's
  interface is the seam and a test runs the same reads over a transport that is not a
  process, so the claim is proven rather than intended.
- **A user can say which build they are running and where it came from** The version,
  its commit and its origin are on screen, and an unsigned artefact says so rather than
  being shipped quietly past a warning.

## Done when — Block H

- **Long prose is legible at the length the format allows** A 320-character line, a
  250-word section and a ten-item non-goal list are the real shapes, so the type scale
  and the measure are chosen against those and not against a mockup.
- **Every string a person reads is in a catalogue** English is the base and a second
  locale is a file, so a screen written today does not have to be reopened to be
  translated.
- **Nothing is told by colour alone, in either ground** Contrast is met in light and in
  dark and a status carries a shape or a word as well as a hue, because a marker set is
  emoji and a colour-only state is one some readers never see.
- **A section is drawn in the text face, with the file's own wrapping kept** The
  wrapping is what lint measured, so re-flowing it shows a reviewer something the commit
  will not diff. The breaks were made for a monospace measure and the face is not mono,
  so a ragged right margin is the deliberate cost; docs/design/Tarefa.dc.html draws it.

## Done when — RG28

- **A pause carries how long it has stood** The order --stale computes arrives in the
  payload rather than on stderr, so a screen draws the oldest pause first and never
  invents an order the reading does not support.

## Done when — RG62

- **The duplicates gate runs here and is proven to be looking** It is in `npm run lint`
  over the three source roots, and a test plants a component the package exports and
  requires the gate to report it with the import that replaces it — because a gate aimed
  at the wrong directory says exactly what a clean tree says.

## Done when — RG49

- **The released installer and executable carry a valid signature**
  Get-AuthenticodeSignature reads Valid on both, the signer is the name the manifest
  gives, and the build line says signed.

## Non-goals

- **No Markdown parsed in this app** Every fact shown comes off a payload some verb
  printed, so a reader that parses the file is the second implementation roadkeep exists
  to remove and is wrong the first time the grammar moves.
- **No write to a governed file** The app composes an argv and the command writes, so
  the parse-render round trip stays the tool's and two writers never share one file.
- **No rule compiled into the client** No marker, id shape, limit, block label or
  governed filename as a literal: those are per-project configuration, and a copy of one
  in a reader breaks L6 from the outside instead of the inside.
- **No engine the reader cannot name** Which copy of roadkeep answered is part of every
  answer; nothing is bundled and nothing is chosen silently, because three copies may
  differ and only naming which one wrote survives that.
- **No store of its own** A cache mirrors files and is invalidated by them, so nothing
  this app holds is ever the truth about a backlog: the repository is the store, and a
  second one is a state that can disagree.
- **No field this app composes** A person types and an agent may author through the
  command; the app measures a draft against the budget and never writes a symptom, a why
  or a rationale, which is L4 held one surface out.
- **No dates, estimates, velocity or burndown** A marker is maturity and not a schedule,
  so a chart of progress over time needs a field roadkeep refuses to store and this app
  would have to invent one to draw it.
- **No git command run by this app** Staging, committing and pushing are the person's;
  the app prints the scope a claim declares and stops there, so a write nobody reviewed
  is never one click away.
- **No account, no auth and no remote store in the desktop build** The service comes
  later as a transport swapped under the same client, and building identity now prices a
  user that does not exist against a design nobody has tested.
- **No issue tracker, and no export to one** A backlog that lives in a service is one an
  agent cannot grep, which is roadkeep's own refusal; a view over the files is not a
  bridge out of them.
