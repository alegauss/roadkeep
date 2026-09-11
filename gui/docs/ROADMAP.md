# Roadmap (active backlog)

## Priority

## Block A — The client (payloads in, types out)

- 📋 **RG179** (deps: —) **an amend that changes deps or requires reads as unreadable, though the file was already written** — AmendPayload.was is declared a map of strings and the engine answers a list for a list field, which RG159 met the first time anything sent the flag. → §RG179
- 📋 **RG188** (deps: —) **a payload key spelled __proto__ is dropped by the dictionary reader, so a count vanishes and the read still answers ok** — The keys are a project's own markers and non-goal leads, and the sibling reader beside it has none of this. → §RG188
- 📋 **RG189** (deps: —) **a cache entry refreshed against a new stamp keeps its old place, so eviction takes the entries being used most** — A Map set on a key it already holds does not move it, which is what the hit branch beside it deletes first to avoid. → §RG189

## Block B — Discovery (which checkouts on this machine are governed)

- 📋 **RG169** (deps: —) **a root is added two levels deep and no control changes it, so worktrees three levels down still need the settings file** — The strip draws each root's depth and offers no way to move it, though addRoot already replaces a depth in place and keeps the order. → §RG169
- 📋 **RG180** (deps: —) **nothing says when the walk behind the remembered record landed, so a project found or lost shows on the next ask** — RG164 answers the record at once and walks behind it, and RG144's subscription now exists to say the fold changed something. → §RG180

## Block C — The portfolio (many backlogs in one view)

- 📋 **RG147** (deps: RG145 ✅, RG20 ✅, RG150 ✅, a grouped palette) **the palette says it finds a line in every backlog and lists only surfaces, so search over all projects reaches no one** — RG20's search reaches no screen, and the package palette only filters nav items. → §RG147
- 📋 **RG187** (deps: RG166 ✅) **the carrier gates every project as it opens, so a cold start over seventeen starts seventeen lints at once** — Each project's pool bounds its own reads, and nothing bounds how many projects gate together. → §RG187

## Block D — The project surface (one backlog, read)

- 📋 **RG170** (deps: roadkeep list with readiness) **list prints no readiness per line, so every row costs a deps read and startable only cannot be offered** — Readiness is the engine's word, and a list of eight hundred is eight hundred reads before the column is full. → §RG170
- 📋 **RG171** (deps: —) **the improvements tab names each design by its pointer and not its heading, so two designs look alike until opened** — The heading is the name a design's author gave it, and list carries only the pointer, so the tab shows an id where it could say what the design is. → §RG171
- 📋 **RG173** (deps: —) **a dep or a chain hop on the task screen is text, so reaching the line it names means going back through the project** — The brief says which ids are tasks here, and each already has a route that opens it as one read. → §RG173
- 📋 **RG174** (deps: —) **a line's own criteria never reach its task screen, so what the ship must check reads as the block's finish line alone** — Brief sends done_when_own beside the block's leads and the reader declares only the second, so the leads ship --checked names go unshown. → §RG174

## Block E — The write path (the app composes an argv; the command writes)

- 📋 **RG181** (deps: —) **the door keep holds every batch a session offered, since only a file moving drops one** — A window re-reading a failing gate adds a batch per read, and a project whose files sit still never drops any of them. → §RG181
- 📋 **RG182** (deps: —) **the filing form asks nobody what the block already delivered, so the window spends an id the terminal would question** — The read before an add is delivered --near, and a line filed from a screen never gets it. → §RG182
- 📋 **RG185** (deps: RG152 ✅) **the gate surface runs lint every time it opens, though the ledger already holds a verdict the files have not moved under** — The carrier asks needsGate before every run it starts, and the surface asks neither it nor the ledger. → §RG185

## Block F — The agent surface (handing one task to Claude Code)

- 📋 **RG175** (deps: —) **a line this window handed over is offered to a second session, since the claim it took names nobody** — The engine refuses the second claim, so nothing is taken twice, but the offer stands where the window already knows a session is running. → §RG175
- 📋 **RG178** (deps: —) **the sessions list asks once when it opens, so one that ends while it stands still reads as running** — Every line and ending is published on the session topic already, but a subscription takes one key and a list wants every session, including one started after it asked. → §RG178
- 📋 **RG190** (deps: —) **a handover landing after the reader left the task screen moves the window to the session anyway** — Every read on that screen gives its answer up on unmount, and the one callback that navigates does not. → §RG190

## Block G — The shell (an executable now, a service later)

- ⏳ **RG49** (deps: RG46 ✅) (requires: signing-cert) **the executable is unsigned, so Windows tells a person the app is untrusted before it opens** — The certificate itself, chosen from docs/SIGNING.md, and the build wired to sign with it. → §RG49
- 📋 **RG128** (deps: RG120 ✅, roadkeep RK1678) **a checkout busy when the probe runs is skipped, so the launcher answers from a cache 446 versions old** — Resolution takes the first engine that answers, so a session can be briefed by a copy nobody chose. → §RG128
- 📋 **RG154** (deps: RG50 ✅, RG162 ⏳) (requires: published-artifact) **the update check has only met answers written by hand, never GitHub's own for a published release** — No release is published yet, so the shape it reads and the page it opens are held by fakes until the first one exists. → §RG154
- ⏳ **RG162** (deps: —) (requires: maintainer-release) **no LICENSE file ships and every build says 0.0.0, so the first release the maintainer decided on cannot be cut** — Pushing main and the tag v0.1.0, which drafts the release, and publishing that draft: both are the maintainer's to make. → §RG162
- 📋 **RG184** (deps: —) **a source file carrying control characters passes every gate, so an invisible byte reaches a commit** — Five NULs sat in a template literal through typecheck, oxlint, prettier and the whole suite. → §RG184

## Block H — The look (a design system for governed prose)

- 📋 **RG172** (deps: RG168 ✅) **a listing narrower than its file, and a failed update check, are explained in English whatever the window speaks** — Both sentences are built in code and drawn as they are, and five more core helpers compose ones the next screen would draw the same way. → §RG172
- 📋 **RG176** (deps: —) **the pseudo-locale run draws the portfolio alone, so three of this window's four surfaces are never read for a literal** — A project, a task and a session each arrived after RG51's run was written, and a string typed into any of them passes it. → §RG176
- 📋 **RG177** (deps: —) **a time is written in the desktop's locale and not the window's, so a Portuguese window dates a file in English** — The session's file stamps are the first times this app draws, and they go through toLocaleString with no tag while every sentence beside them follows the chosen locale. → §RG177
- 📋 **RG183** (deps: —) **a catalogue key no screen says is never reported, so a string both locales declare can be dead** — RG125 catches a key one locale misses, and nothing catches one nobody uses. → §RG183
- 📋 **RG186** (deps: —) **the duplicates gate matches on export, so a screen redeclaring a design-system name for its own use passes it** — A copy nobody exports is the ordinary shape of one, and it drifts where nothing can point at it. → §RG186
- 📋 **RG191** (deps: RG168 ✅) **a screen drawing a field this app wrote in English passes every run that does not reach the state showing it** — Each of those fields has a code beside it and a docstring saying so, which is a shape one pass over the sources can refuse. → §RG191

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
