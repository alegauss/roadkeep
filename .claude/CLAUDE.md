# roadkeep — Claude Code

All project guidelines, conventions and design laws are in the shared agents file:

@../agents.md

<!-- Under .claude/ and not at the root: this repository is the plugin, so every root file
ships in the payload, where a root CLAUDE.md is the one file the loader warns is not
context (RK323). `./.claude/CLAUDE.md` is read exactly the same way in this checkout and
is no plugin surface there. Moving it back re-adds the warning. -->
