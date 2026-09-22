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

### §RG303 The reply, kept in the stream it was sent to

**The record is the lines, so the reply has to be one.** `Reply` clears its box on a
started resume (RG269) and nothing else happens: the words go out as argv to `--resume`,
and the next act in the stream is the agent answering something the page never carried.
A reload, a second window and the reader after the fact all meet the same gap.

Drawn from the component's own state it would not be a record — it would die on reload
and never reach the other windows, which read this session off the same published lines.

**So the shell writes it where every other line goes.** `reply` pushes a line onto
`session.lines` and publishes it with its index, exactly as `onLine` does, before the
turn spawns. One path, so what the record carries and what a live window hears cannot
disagree.

**A line of this app's own type, never a forged `user` one.** The agent may echo the
prompt itself, and a synthetic `user` line would be indistinguishable from it and drawn
twice. A type this app owns cannot collide: `readSessionLine` answers `other` for one it
does not know, `askOf` does not match it, and `actsOf` reads it as an act of its own
kind — the person's words, drawn as what somebody typed and never folded into the notes
(RG208).

Not a chat log. The first turn's brief belongs to the handed-over card and stays there,
and a permission answer is drawn on its question (RG272).

### §RG304 Enter sends the reply, Shift+Enter breaks the line

**The box is a `Textarea` with no keys of its own.** Every answer costs a reach for the
mouse, in the one place where somebody is mid-sentence and a stopped session waits on
them — the box takes focus for that reason when a turn ended waiting (RG268).

Enter sends and Shift+Enter writes a newline, which is what every message box and the
terminal this window replaces already teach. The newline is not lost, it moves to the
modifier, where somebody writing a paragraph looks for it.

**Sending from the key is sending from the button, not a second path.** `send` stays the
one function, and the handler holds the conditions the button is disabled by — empty
after a trim, or already sending — so a held Enter cannot start two turns.

**A composing key is not a send.** `isComposing` on the native event is the one check
that keeps an IME's own Enter from committing a half-written word as a reply; a
`keydown` mid-composition carries it, and nothing else this app draws has to know about
it.

The rule is this box's alone. A door's prose blank (RG261) is one blank of several with
a take button of its own, and Enter there would hand over a form somebody is still
filling in.

Asserted with a real key press in the browser suite rather than in jsdom: what is in
question is the key reaching a focused box, which is the half jsdom does not have.

### §RG305 What is lost when the window closes, and what is not

`will-quit` waits for every session to exit, and that is right: on Windows a process
killed but not yet gone still holds its project as a working directory. The loss is not
the kill. It is that `createSessions` keeps its sessions in a `Map` and writes nothing,
so the key, the root, the line, every line the stream read and the `sessionId` the
outcome carried go with the process.

The agent's own transcript does not. A session runs the person's `claude` in the
environment RG205 composed, so Claude Code writes its record where it always does and
resuming from that root still reads it. What this app cannot do is name the session,
having never kept the id.

So the work is a store beside the settings, the readings and the glosses — this app's
own file, in the same shape — holding one record per session: the key, the root, the id,
what it was handed, when it started, the lines and the outcome. Read at start-up,
offered as sessions that stopped. `reply` already continues one by its `sessionId`, so
what is owed here is the record surviving and not a second way to carry on.

A local file, like every other one this app keeps: nothing is sent anywhere.

### §RG306 Telling your own claim from a stranger's, after a restart

A claim names nobody, and RG175 closed exactly this gap while the window lives: `held`
stays empty for a line this very window claimed a minute ago, so `alreadyRunning` reads
the session record instead, and the offer returns when the session ends rather than on a
timer kept here.

A quit takes that record. `close` kills the process and leaves the claim standing on
purpose — the session may have moved the line, and releasing it would undo a state
nobody reviewed — so the claim outlives the one thing that knew whose it was. Reopening,
`handOver` reads `held` and says the line is held by another worker, which is what it
truthfully says about a second session in the same checkout. The two read alike, and the
person waits out the expiry on a line nobody else ever touched.

Releasing a claim at the quit is the wrong answer and stays refused. What is missing is
the recognition: with RG305's record on disk, a held line whose claim came from this
machine's own stopped session is named as that, with what it was doing and how it ended
beside it. Handing it over again is then a judgement somebody makes, not a guess — and
nothing re-dates the claim, which stays an expiry the engine owns.

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

## Block I — Validation (the list a person works through)
