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

### §RG285 An Explain button, and a dialog written for somebody new

**Where it is.** An Explain action in the task hero's `HeroActions`, beside Copy the
brief and Hand over, opening the design system's `Dialog`, wide and scrolling. Disabled,
with its reason, where RG43 found no `claude`.

**Its states.** Asking: a `Skeleton` in the answer's shape, and Cancel. Answered: the
headline large, then today and after, the steps as an ordered list, the terms, the risks
and what done looks like, each string through `Prose` (RG271). Failed: the failure's own
sentence, and Try again. Every word of the frame in both catalogues.

**Its author, named.** The footer says Claude Code {version} and {model} wrote this, in
{language}, from the brief of {id}, and that it is not part of the backlog. `No engine
the reader cannot name` is about roadkeep's copy, and its reason holds here too: two
models may explain one task two ways.

`No field this app composes` bounds this: the gloss is Claude Code's, shown and never
written, and nothing copies it into a symptom, a why or a section. `No write to a
governed file` holds with it.

**Its screens.** A task-surface state in `shots-plan.ts` opens the dialog, as the
session's `file` state opens its sheet, and the scripted agent answers it.

Done when `task.test.tsx` draws each state off the stub bridge and `npm run shots` shows
the dialog in both grounds, both languages and both widths.

### §RG286 The picture: facts off the brief, captions off the gloss

Drawn as paragraphs, a gloss is a longer design. A task is grasped at a glance by its
shape: what it waits on and what waits on it, before against after, the path of steps.

**Facts off the brief, words off the gloss.** The chain `deps → this line → unblocks` is
drawn from `depsResolved` and `unblocks`, each node with its marker and readiness; the
gloss's keyed items caption the nodes, and one it skipped keeps its symptom. The binding
leads are cards over their meanings. No node is the agent's: `readGloss` dropped what
the brief lacks.

**The rest are shapes this app owns.** Today and after as two panels and an arrow; the
steps as a numbered path, across when wide and down when narrow; the terms as a glossary
grid; each risk a callout. React and inline SVG over the design system's tokens, so both
grounds hold without a second palette.

**No diagram the agent writes.** Mermaid or SVG in the answer is a program the window
would run, which `skipHtml` (RG271) and the script policy refuse; fixed slots keep every
gloss legible.

Each shape has its words beside it, and the chain reads as a list to a screen reader.

Done when the shots and their accessibility report are clean, and a test draws a node
the gloss never named.

On ship: --decides "A gloss is drawn in shapes this app owns, never in a diagram an
agent wrote"

### §RG287 Kept per brief and language, reused, and regenerated on demand

A gloss costs a wait and the person's tokens, and closing the dialog throws it away.
Kept, reopening a task shows it at once and asks Claude Code nothing.

**Kept in its own file.** `core/glosses.ts` holds each gloss by root, id and language
tag, beside the brief it answered; `shell/glosses-file.ts` keeps them in `glosses.json`
under `userData`, written by rename as `readings-file.ts` writes, so a restart keeps
them too. Not `settings.json`, whose header holds no cached answer, and nothing in the
project's tree. Bounded, the oldest dropped first.

**Stale is a comparison, not a clock.** A kept gloss stands while the brief's line,
design, deps and binding lists equal the ones it answered; `glossStands()` is that
comparison, as `readingStands()` is RG251's. A stale gloss is still shown, under a
notice that the task changed since.

**The language is part of the key.** A window switched to another language has no gloss
in it, so opening the dialog asks anew, and switching back finds the first one kept.

**Regenerate, always there.** A Regenerate button in the dialog's footer asks again and
replaces the kept gloss: for a stale one, and for a person who wants another reading of
a task that did not change.

Done when `glosses.test.ts` holds a gloss across a reopen, reads it stale once the
brief's design moved, and keeps two languages apart; and `task.test.tsx` shows a kept
gloss with no call made, and Regenerate making one.

### §RG288 Reading the files the design names

A gloss from the brief alone restates the design in plainer words. What a newcomer also
wants is where the change lands: which files, what they do today, what moves. The design
names them, and reading them is the depth.

**Three tools, all reads.** The RG284 call lists `Read`, `Grep` and `Glob` as its
`tools`: still no `Bash`, no edit, no MCP server, and `dontAsk` refuses anything else
without a question nobody would answer. The frame adds one instruction: read what the
design names before explaining, and say for each place what it does now and what the
task changes there.

**The `where` slot.** The schema gains `where`, each item a path and its account; the
picture draws them as one lane per top-level folder, since which folders a project has
is its own and never this app's list.

**Progress, at last.** A read is a `tool_use` in the stream, so while asking, the dialog
names each file as it is read — the only progress a structured answer has.

A deeper gloss is a slower one, and RG287 is what pays for it once per brief.

Done when the captured stream reads at least one file and the picture draws its lane.

## Block G — The shell (an executable now, a service later)

### §RG49 The signature, and what it needs that code cannot supply

Signing is not work that can be finished by writing anything: it needs a certificate
somebody bought, held somewhere a build can reach. So the line states the requirement
and is set aside for a caller that says it has one, rather than coming back as the next
ready task forever. What can be built without it is the pipeline that would use it, and
the about surface saying plainly that this build is unsigned — which is the honest half
and is worth having on its own.

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
