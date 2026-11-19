# roadkeep, where the file is open

The roadkeep activity-bar container holds one view per question:

- **Backlog** — the open lines, grouped by block under each block's heading, ready before
  blocked, with the blocker named on the lines that are not. How many lines are open, by
  marker, is in the view's header. Selecting a row reveals it in the roadmap.
- **Designs** — the design sections, found by a word, an id or a heading through
  `section find` across every prose file. Selecting one opens it as a read-only preview.

In the Backlog view, where the project declares a deferred store, each block also holds a
collapsed **Deferred** node: every paused line with the reason it was set aside, revealed in
the store when selected, with a resume action beside it. Hovering a line shows its reason and the opening of its design section; the book icon beside
it opens the whole section as a read-only Markdown preview, read from `section show`. A line
with no design says so and names `section add`.

It carries **no rule** — no limit, no marker set, no id shape and no Markdown parser. Every
row is read from a payload `roadkeep` printed, so what you see is what the command that owns
the files says, and a project whose prefix, markers or limits differ needs nothing changed
here.

## Installing

Build the archive from this repository — no node, no toolchain:

```
python scripts/build_vsix.py
code --install-extension dist/alegauss.roadkeep-<version>.vsix
```

Developing it needs neither: open the repository and press <kbd>F5</kbd>, or copy this
folder into your editor's extensions directory.

## What it needs

A `roadkeep.toml` in the workspace — the extension activates on nothing else — and the
`roadkeep.command` setting, which is **required**:

```json
{ "roadkeep.command": "roadkeep" }
```

It is not resolved from PATH, from a virtualenv or from a cache, and that is deliberate.
Three copies of this tool can already be in play — the plugin, the action CI gates on, and
whatever you run — and `engines` exists because they may differ. A view is a fourth, and one
that guessed would show findings your commits will not produce; you would learn that when a
hook denied a write the panel called fine. So it asks, and the status bar names which copy
answered and whether the three agree; clicking it re-reads both the engine and the backlog.

When a read fails it says so in the tree rather than showing an empty one, because an empty
backlog is a claim a failed read cannot make.

Saving a governed file re-reads the backlog and the gate. Which copy answered is asked once
per window — that is a fact about the installation, not about the file — and the refresh
button in the view title asks it again, which is what you press after an upgrade.
