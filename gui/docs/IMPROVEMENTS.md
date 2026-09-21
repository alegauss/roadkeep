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

### §RG276 The session screen's arrangement as a settings field

The session screen draws three cards around its stream, what was handed over, what moved
and the files it touched, in a grid `Session.tsx` fixes. Moving them needs the
arrangement kept, and settings.json holds the choices nobody can rebuild by looking.

The field is `sessionLayout`: two ordered lists of card ids, `left` and `right`, named
after the grid's `data-region`s less their prefix: `handed`, `moved`, `files`. The
stream is not in it: it is the editor area, and stays in the middle. The default is
today's grid, so an upgrade changes nothing on screen, and a field arriving with a
default leaves `SETTINGS_VERSION` at 1, as `portfolioOrder` did.

`readSettings` recovers it alone, as it does every field. An unknown id is dropped, a
repeated one keeps its first place, and a known card the file omits goes where the
default puts it, so a card a later build adds still appears. A value that is not two
lists resets under a `Lost` code of its own, with its sentence in both catalogues.

`moveCard(layout, card, side, index)` is the pure move beside the reader, so a drag and
a keyboard call one rule. The `PREFERENCES` row wants each known id exactly once,
stricter than the reader, so nothing written is what the reader would repair. The
bridge, the preload and the main process do not change.

Done when `settings.test.ts` and `preferences.test.ts` hold each recovery, the move, and
a round trip through `settingsText`.

### §RG277 Dragging a session card by its title

VS Code moves a view by dragging its title to the other side bar or along its own. The
session screen's three side cards get the same, over the field RG276 adds.

The drag is `@dnd-kit/core` and `@dnd-kit/sortable`, which the design system already
depends on; they join `packages/ui/package.json` at its pinned versions, so one copy
stays installed. Its `BentoTileGrid` edit mode reorders tiles in one mosaic, which is
not two side bars around a stream.

Each side bar is a sortable list and each card's `PanelTitle` row its handle, a grip
showing on hover and focus. A card dropped on the other side bar lands at the pointer's
index under an insertion line. A side bar left empty gives its column to the stream, and
during a drag is a thin strip that still takes a drop.

The move is drawn first and written after, through `preferring.ts` as `sessionNotes` is.
The task and gate routes read one arrangement, since they are one screen.

The handle is drawn from `xl`, where two side bars exist. At `lg` the side column holds
left then right, and below it RG225's order stands. dnd-kit's keyboard sensor is on,
announcing through the catalogue.

Done when a browser test drags `files` to the top of the left side bar, sees it land and
`savePreference` carry the layout, and sees a remount draw the same.

### §RG278 Moving a card without dragging it, and putting them all back

A drag is not every person's way to move something, and VS Code does not rely on it
alone: a view's title menu has Move View, and the palette has View: Reset View
Locations. The session screen needs both beside the drag RG277 builds.

Each side card's title gets a menu, the design system's `DropdownMenu`, with three
entries: move to the other side bar, move up, move down. An entry that would do nothing,
up on the first card, is not offered. Each calls the `moveCard` RG276 adds and is
written as a drop is, so one path reaches the file.

Resetting writes `DEFAULT_SETTINGS.sessionLayout` back, so the default lives in one
place. It is offered twice: as a command in the shell's `BentoCommandPalette`, where VS
Code puts it, and as a button on the Settings screen beside how a session draws its
notes, where a person looks for what they changed. Neither is offered while the
arrangement already is the default.

The entries, the command and the button come from the catalogue in both languages, and
the menu is reached by Tab from the card's title.

Done when a test moves `handed` to the right side bar through the menu, resets from the
palette, and sees the default drawn and written; and when the accessibility report
beside `npm run shots` names the menu.

### §RG279 Side bars that keep the width they were dragged to

The two side bars are 18rem whatever they hold, the width RG237 gave them. A long path
in the files card is cut, and a person who wants a wider stream has no way to get one.
VS Code lets a side bar's edge be dragged, and the next launch opens at that width.

The design system ships the divider as `ResizablePanelGroup`, `ResizablePanel` and
`ResizableHandle`, over react-resizable-panels. The `xl` grid in `Session.tsx` becomes
one horizontal group of up to three panels, the stream in the middle, imported from the
design system rather than the library, so `package.json` gains nothing.

The width goes to disk, not to the browser. The library's `autoSaveId` and
`useDefaultLayout` write to `localStorage`, which is not settings.json and not a file a
person can read or edit. The widths are a second settings row, `sessionSides`: each side
bar as a percentage of the group, clamped by the reader to the panels' own minimum and
maximum. They are saved from `onLayoutChanged`, which fires once when the drag ends,
never from `onLayoutChange`, which fires on every pointer move.

A side bar RG277 emptied has no panel and so no handle; its saved width is kept for when
a card comes back to it.

Done when a browser test drags the right handle, sees one `savePreference` call with the
new percentage, and sees a remount draw the same width; and when a file holding 90 per
cent reads back clamped, with its notice.

### §RG280 Created, changed or deleted, off the first answer on a path

Each row of the edited list (RG243) says how many calls named the file and where the
disk has it (RG244), never what the session did to it. A created file reads like one
touched on one line, where VS Code's source-control list answers with a letter.

**The answer is already in the stream.** Claude Code answers an `Edit` or a `Write` with
a `tool_use_result`: `originalFile`, the file before the call, and for a `Write` a
`type` of `create` or `update`. The `returned` act keeps that raw line, so
`originOf(acts, path)` in `core/acts.ts` reads the first answered, successful call on
the path. A `Write`'s `type` decides; an `Edit` changed a file that was there, and a
null `originalFile` is one too large to carry. A line with two `tool_result`s is not
read, since its one `tool_use_result` cannot say whose it is. No answer yet is no mark.

**The disk finishes it.** Was there and missing now is deleted; was there and present is
changed; absent before and present is created; created and missing now is its own word.

**Drawn as a letter and a word** in a `Pill` after the call count, `data-kind` on the
leaf, a deleted file's name struck through. Both catalogues carry the words.

`No git command run by this app` bounds this: the before is Claude Code's answer, never
the repository's.

Done when `acts.test.ts` reads each kind off a captured `Edit` and `Write` line, taken
from a real run as `session-stream.jsonl` was, and `session.test.tsx` draws them.

### §RG281 Appeared, changed or gone, off the watch's own stat

The list of what moved on disk (RG247) holds what no edit call named: a file `rm`
removed, one a generator created, one a formatter rewrote. It says how often each moved
and when, never which it was, the letter RG280 puts on an edited row.

**Not the event's name.** `fs.watch` says `rename` or `change`, and macOS reports most
writes as `rename`. The portable facts are whether the path is there after the event and
when it was born.

**The stat is already made.** `watchSessionRoot` stats each path to drop folders; it now
hands on present and `birthtime` too. `sessionMoves` in `core/watching.ts` keeps the
first birth and the last presence: born at or after the session started is created,
before it is changed, absent at its last move is gone, and born after the start and gone
came and went.

**Where it is wrong, said.** A save that writes a copy and renames it over the file
gives a new birth, so it reads as created. A filesystem with no birth time answers zero,
which reads as changed, never a false new. A file made and removed faster than the stat
reads as gone. The caption, which already calls the list unattributed, says so.

A stat reads no byte, so RG247's rule holds: a name and a clock.

Done when `watching.test.ts` folds each kind and `session-watch-live.test.ts` sees a
created and a deleted file on the real watch.

### §RG282 The file against its original, line by line

The viewer (RG245) shows the file as the disk has it, and above it each call's two
halves (RG246): ten edits are ten blocks, and a formatter run after them is in none. VS
Code shows one comparison, the original beside the file now.

**The original is RG280's.** `originOf` hands the first answer's `originalFile`; a
created file's is empty, every line added. The file now is the read the viewer already
makes, so what changed it after the last call counts too, and a deleted file is an empty
side, every line removed. A file only the watch saw has no original, and the viewer says
so.

**Compared in `core`.** `linesBetween(before, after)` is a pure line comparison: hunks
with both sides' numbers, three unchanged lines around each, the rest folded. `core` has
no dependency and a Myers comparison is small enough to own; past a ceiling on lines
none is made, and the viewer says so.

**Drawn here, not with `BentoDiff`.** VDS140 compares fields word by word; a file
compares by line, with numbers. Inline first, side by side as a toggle that widens the
sheet, each line marked `+` or `−` in text as well as colour, in both grounds. A file
with an original opens on the comparison, the file and the calls in the design system's
`Tabs` beside it. A Markdown file is compared as lines, never rendered.

Done when `compare.test.ts` holds the hunks and `npm run shots` draws a created, a
changed and a deleted file.

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
