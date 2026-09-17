# Improvements

## Block A — The client (payloads in, types out)

## Block B — Discovery (which checkouts on this machine are governed)

## Block C — The portfolio (many backlogs in one view)

## Block D — The project surface (one backlog, read)

## Block E — The write path (the app composes an argv; the command writes)

## Block F — The agent surface (handing one task to Claude Code)

### §RG269 Answering is resuming

A headless session ends its turn at its first question, and the only way to answer it
today is a terminal, the project's folder and a session id this window never shows.
Claude Code already has the door: `claude -p <reply> --resume <session_id>` with the
same stream flags, run from the same root, continues the conversation with everything it
had.

`core` gains the resume form of `sessionCall`, the one flag added being the session's
own id. The reply is the person's words, sent verbatim and never framed: `promptFor`
frames a payload, and a reply is not one. `No field this app composes` bounds it without
forbidding it, since a reply is no governed field and the session still writes through
the verbs.

`Sessions.reply(key, text)` continues the same record: the same key, the lines keeping
their indexes, the outcome back to null and the root watched again. It refuses an empty
reply, a session still running, a key naming nothing and a session that never named its
id. Before resuming, the line's brief is read again, and a line another holder took
since is refused with the holder named, as a handover is.

The screen draws a reply box under the stream once a session that named its id has
ended, beside its last words, and the side panel stops repeating those words. A session
that ended `waiting` (RG268) opens with the box focused.

### §RG270 A grant is the person's, for one turn

Headless Claude Code has nobody to ask, so a call the project's settings do not allow is
refused and the turn goes on without it. The refusals arrive on the `result` line and
RG268 keeps them on the outcome; nothing draws them, and a person who would allow the
edit has no way to say so.

Each refusal is drawn under the ended session: the tool, what it would have touched, a
path for a file edit and a command for Bash, and a link to its call in the stream. Each
has a checkbox, and the reply RG269 sends passes `--allowedTools` naming the checked
tools, for that resumed turn and no other.

`sessionCall` decides no permission, and that stands: here the person decides, one turn
at a time. So never a `--permission-mode`, never a skip of permissions, never a tool
nobody was refused, and nothing written to the project's `.claude` settings, which are
the project's. The grant names a tool and not a rule spelled from its input, since
composing a permission grammar would be this app deciding what a rule means.

A grant with no words sends the sentence the wording table holds for it, placed in the
box before sending, so what the session reads is still the person's to change. A refusal
left unchecked stays listed, and is refused again if the session calls it again.

### §RG271 Rendered where a person reads, raw where a tool measures

An agent writes Markdown for a terminal that renders it, and the stream draws it as
characters: bold as asterisks, code as backticks. commitclerk's T65 ended on two
numbered choices a reader had to decode before choosing.

`No Markdown parsed in this app` bounds this and does not forbid it: its reason is facts
read off a governed file, and nothing is read out of these words. The rule for every
surface is to render what an agent wrote for a person to read, and keep raw what a gate
measures, a commit diffs, a line number points into or a verb reads back.

| Surface                                 | Drawn    | Because                                   |
| --------------------------------------- | -------- | ----------------------------------------- |
| A session's words and its last word     | rendered | nothing measures, stores or diffs them    |
| A tool call's input and output          | raw      | a command and its output are data         |
| A file in the viewer                    | raw      | RG246's edits point at its line numbers   |
| A design section                        | raw      | the gate counts it and a commit diffs it  |
| A symptom, a why, a governed file       | raw      | a verb wrote it and reads it back         |
| The raw line                            | raw      | it is the stream as it arrived            |

The design system ships no renderer, so `ui` takes `react-markdown` with `remark-gfm`:
no raw HTML, no image fetched, a link through the guard's external opener. Elements take
the design system's type and tokens in both grounds, and a wide code block scrolls
inside the stream, never the page.

On ship: `non-goal amend` narrows the lead to governed files and fields, quoting this
rule.

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
