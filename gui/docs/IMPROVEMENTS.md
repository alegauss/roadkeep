# Improvements

## Block A — The client (payloads in, types out)

## Block B — Discovery (which checkouts on this machine are governed)

## Block C — The portfolio (many backlogs in one view)

## Block D — The project surface (one backlog, read)

## Block E — The write path (the app composes an argv; the command writes)

## Block F — The agent surface (handing one task to Claude Code)

### §RG273 Carried by the Agent SDK, read by the same record

A session is `claude -p` plus a line protocol this app writes by hand: the prompt as a
`user` line, a question as `control_request`, its answer as `control_response`, standard
input closed at `result`. RG272 adds the permission half.
`@anthropic-ai/claude-agent-sdk` is that protocol, published: `query()` takes the
prompt, `cwd` and `resume`, yields each message as the object the stream line held, and
calls `canUseTool` where the project's rules fall through to a question.

**Only `startSession` changes.** Each message the SDK yields goes into the same `offer`
as the line it was, so `readSessionLine`, the record and every screen read what they
read today. `canUseTool` writes the question line RG272's reader takes and resolves on
the person's answer; cancel is the SDK's abort. `core` keeps describing the call as data
and never imports the SDK.

**The person's `claude`, never the bundled one.** The SDK installs a native Claude Code
per platform as an optional dependency. `pathToClaudeCodeExecutable` is always the
candidate RG43 resolved, for the reason `agent-candidates.ts` gives. `files` in
`electron-builder.yml` is an allow-list, so the platform package never ships, and a live
test holds that.

**Settings named, not defaulted.** `settingSources` is passed as `user`, `project` and
`local` rather than left to a default that has changed before, and `env` whole as RG205
composes it, since the SDK replaces the environment rather than merging.

**The scripted agent answers `initialize`.** The SDK opens with a control request
RG210's replay never saw.

On ship: --recorded-in packages/shell/src/session-process.ts

### §RG274 Continued in VS Code, by the session's own id

The Claude Code extension registers a URI handler. Read in 2.1.274's `extension.js`:
`vscode://anthropic.claude-code/open` takes `session` and `prompt`, drops a `session`
that does not parse as an id, and opens that session in an editor tab. A `prompt` is
only typed into the input box, never sent. Every session record here already carries its
`sessionId`.

**Offered on a session that is not running.** Stopped, finished or failed, beside
RG269's reply: two processes appending one transcript is what this avoids. Nothing is
sent from here, and continuing is the person's next message, typed there.

**`shell` opens it, and spawns nothing.** `shell.openExternal`, with no `code` looked up
on PATH. Both links are composed beside that call, and a unit test holds their spelling.
The action is offered only where `app.getApplicationNameForProtocol` names a `vscode:`
handler, so a machine without VS Code learns it from the button and not from an
operating-system dialog.

**Which window answers is unproven, and is measured first.** The handler resumes from
the session list of the window that received the link, and a session is listed under the
folder it ran in. So `vscode://file/<root>` opens first, then the session link, and a
real window has to show the session opening there, not in whichever window last had
focus.

**The record stops at the hand-off.** Turns taken in VS Code are in the transcript, so a
later reply from this window carries them, but this screen's stream does not show them.

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
