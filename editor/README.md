# roadkeep, where the file is open

The backlog this workspace governs, as a tree: grouped by block, ready before blocked, with
the blocker named on the lines that are not. Selecting a row reveals it in the roadmap.

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

A `roadkeep.toml` in the workspace — the extension activates on nothing else — and a
`roadkeep` it can run. It looks for the `roadkeep.command` setting first, then `roadkeep` on
PATH, then `python -m roadkeep.cli`. When none of them answers it says so in the tree rather
than showing an empty one, because an empty backlog is a claim a failed read cannot make.
