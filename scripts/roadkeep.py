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

Since RK176 it also decides *whether* to import the package. The hook runs on every shell
command in a governed project and the harness waits for it, and 148 ms of the 184 ms that
took was spent before the guard looked at anything. So a `guard` payload is screened first
by :mod:`roadkeep.screening`, which imports nothing but the standard library and can only
ever answer "there is certainly nothing here" — every other answer loads the CLI and gets
the same decision it always got.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def run(argv: list[str]) -> int:
    """Answer a screened `guard` without loading the package, or hand over to the CLI.

    Stdin is read here and handed back as a buffer, because a stream is readable once: the
    screen needs the payload and so does :func:`roadkeep.cli._guard`, and passing it as an
    argument would be a second entry point's signature.
    """
    if argv[:1] == ["guard"]:
        from roadkeep.screening import worth_loading  # noqa: PLC0415 - the whole point

        payload = sys.stdin.read()
        if not worth_loading(payload):
            # Silence is the allow, exactly as the guard's own is: nothing on stdout, and
            # exit 0, because the harness reads a non-zero exit as the hook having failed.
            return 0
        sys.stdin = io.StringIO(payload)
    from roadkeep.cli import main  # noqa: PLC0415 - after the screen, never before

    return main(argv)


if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1:]))
