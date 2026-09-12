# Roadmap (active backlog)

## Priority

## Block A — The client (payloads in, types out)

## Block B — Discovery (which checkouts on this machine are governed)

## Block C — The portfolio (many backlogs in one view)

- 📋 **RG147** (deps: RG145 ✅, RG20 ✅, RG150 ✅, a grouped palette) **the palette says it finds a line in every backlog and lists only surfaces, so search over all projects reaches no one** — RG20's search reaches no screen, and the package palette only filters nav items. → §RG147

## Block D — The project surface (one backlog, read)

- 📋 **RG170** (deps: roadkeep list with readiness) **list prints no readiness per line, so every row costs a deps read and startable only cannot be offered** — Readiness is the engine's word, and a list of eight hundred is eight hundred reads before the column is full. → §RG170

## Block E — The write path (the app composes an argv; the command writes)

## Block F — The agent surface (handing one task to Claude Code)

- 📋 **RG190** (deps: —) **a handover landing after the reader left the task screen moves the window to the session anyway** — Every read on that screen gives its answer up on unmount, and the one callback that navigates does not. → §RG190

## Block G — The shell (an executable now, a service later)

- ⏳ **RG49** (deps: RG46 ✅) (requires: signing-cert) **the executable is unsigned, so Windows tells a person the app is untrusted before it opens** — The certificate itself, chosen from docs/SIGNING.md, and the build wired to sign with it. → §RG49
- 📋 **RG128** (deps: RG120 ✅, roadkeep RK1678) **a checkout busy when the probe runs is skipped, so the launcher answers from a cache 446 versions old** — Resolution takes the first engine that answers, so a session can be briefed by a copy nobody chose. → §RG128
- 📋 **RG154** (deps: RG50 ✅, RG162 ⏳) (requires: published-artifact) **the update check has only met answers written by hand, never GitHub's own for a published release** — No release is published yet, so the shape it reads and the page it opens are held by fakes until the first one exists. → §RG154
- ⏳ **RG162** (deps: —) (requires: maintainer-release) **no LICENSE file ships and every build says 0.0.0, so the first release the maintainer decided on cannot be cut** — Pushing main and the tag v0.1.0, which drafts the release, and publishing that draft: both are the maintainer's to make. → §RG162

## Block H — The look (a design system for governed prose)

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
- **A live assertion cannot pass on an empty list or a null field** An `every` is
  preceded by the count that makes it mean something, and a field the engine may answer
  null with is asserted by its type — `not.toBe('')` is true of null. Both were found
  passing against nothing: RG163 for a marker nothing carried, RG158 for a filter pair
  and a tier.

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
- **A location this app acts on is parsed, never matched as a string** A URL or a path
  from a network answer, a config or a page is compared through the parser that will
  resolve it — scheme, host, credentials, normalised path — because a prefix is not a
  location and the dot segments are normalised after a string check has said yes
  (RG155).

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

## Done when — RG62

- **The duplicates gate runs here and is proven to be looking** It is in `npm run lint`
  over the three source roots, and a test plants a component the package exports and
  requires the gate to report it with the import that replaces it — because a gate aimed
  at the wrong directory says exactly what a clean tree says.

## Done when — RG49

- **The released installer and executable carry a valid signature**
  Get-AuthenticodeSignature reads Valid on the installer and on the roadkeep.exe inside
  it, the signer is the name that route signs under — the foundation on SignPath, an
  Open Source Developer on Certum, neither being the manifest's — and the build line
  says signed.

## Done when — RG162

- **v0.1.0 is a published release, cut from this commit** The tag reaches the remote,
  the package job builds both installers against a manifest that matches it, and a
  person reads the draft the release job leaves and publishes it. Pushing and publishing
  are the maintainer's acts, which is why this is what is left rather than something a
  commit could finish.

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
