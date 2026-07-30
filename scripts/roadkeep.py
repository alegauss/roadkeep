"""Run the CLI from the source tree beside this file, with nothing installed (RK57).

The plugin ships `src/roadkeep/` and then declares a hook and an MCP server. Both used to
call the `roadkeep` console script, which exists only after `pip install roadkeep` *and* only
if the interpreter's scripts directory is on PATH — so `/plugin install` could succeed while
neither surface started. This launcher removes both conditions: the plugin's own root is
substituted into the command by the harness, and the package it already carries is right here.

`src` goes **first** on `sys.path`, ahead of anything installed. A plugin that silently ran an
older installed copy is the hardest kind of stale, because `/plugin` would report this
version while another one answered.

Not a second entry point: it resolves an import path and calls :func:`roadkeep.cli.main`, so
the arguments, the exit codes and the refusals are the console script's own.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from roadkeep.cli import main  # noqa: E402 - the path above is what makes this importable

if __name__ == "__main__":
    raise SystemExit(main())
