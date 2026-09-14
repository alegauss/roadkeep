# Improvements

## Block A — The client (payloads in, types out)

## Block B — Discovery (which checkouts on this machine are governed)

## Block C — The portfolio (many backlogs in one view)

## Block D — The project surface (one backlog, read)

## Block E — The write path (the app composes an argv; the command writes)

## Block F — The agent surface (handing one task to Claude Code)

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

### §RG232 The one-off failure, kept

During RG226 one full `npm test` drew `task.test.tsx`'s *leads from Open to the line at
its own route* red. It was green alone and green since: six runs of the file, and four
whole fast suites, all under load. The message is gone — a fast run prints a failure and
keeps nothing.

RG226 fixed three tests of this shape by finding what each really waited on: a gate that
had not run, a directory Windows announced, a process still standing. Its done-when
asked for a hundred green fast runs and it shipped on four, so this is the part nobody
has shown.

**The first move is to keep the evidence, not to guess.** The suite can write a
machine-readable report per run, so a failure that happens once leaves its message and
its assertion behind. Then run the fast suite under load until the test goes red.

Fix it where RG226 fixed the others: `findByRole` waits on a deadline, and a deadline on
a loaded worker is what breaks, but what it should wait on is the click reaching the
route — a fact the router can be asked for.

And if twenty loaded runs stay green, say so on the line with the number: a one-off
closed with its evidence beats a timeout raised to bury it.

Done when the test has been made to fail on purpose and then waits on a fact, or the
line is closed as unreproducible with the count of runs behind it.

### §RG233 One commit rule, not two

`CLAUDE.md`'s *One task, one commit* says `run-commit.cmd -m "<title>"`, never `git
commit` by hand. The `roadkeep-gui-roadmap-docs` skill says the opposite and gives its
reason: `git add -- <this task's paths>` then `git commit -F <message file>`, "not
`run-commit.cmd`, whose `git add *` takes the whole tree", because another session works
this same checkout. That happened on 2026-09-09: one commit carried another session's
docs, and both messages then described something they did not hold.

Both files are loaded every turn, so whichever is read first decides, and the reader
cannot tell which is stale. Every commit in block H followed the skill.

**The skill's rule is the one with a measurement behind it, so `CLAUDE.md`'s row is what
gives way.** Its commit row should say one task one commit, staged by its own paths, and
name the shared checkout as the reason — short, since the long form is the skill's job.

What is lost is worth saying: `run-commit.cmd` writes the commit body from the staged
diff, and staging by path means writing it by hand. That is a trade to state in the row,
not to leave for the next reader to rediscover.

The other way out is a tool that stages only the paths it is given, which would let both
files agree on `run-commit.cmd`. It lives outside this repo, in `D:\Dev\bin`, so it is
not this line's to change — name it and leave it.

Done when the two say one thing and the row names why.
