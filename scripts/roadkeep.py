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
    hook = argv[:1] == ["guard"]
    try:
        if hook:
            from roadkeep.screening import worth_loading  # noqa: PLC0415 - the whole point

            payload = sys.stdin.read()
            if not worth_loading(payload):
                # Silence is the allow, exactly as the guard's own is: nothing on stdout, and
                # exit 0, because the harness reads a non-zero exit as the hook having failed.
                return 0
            sys.stdin = io.StringIO(payload)
        from roadkeep.cli import main  # noqa: PLC0415 - after the screen, never before
    except SyntaxError as error:
        # The one path where this tool stopped explaining itself (RK1179). An edit in progress
        # in the *answering* checkout reached a caller in another repository as a nine-line
        # traceback ending `IndentationError: unexpected indent`, which says nothing about which
        # copy answered, that the copy is what is wrong rather than the call, or that the
        # caller's own files were untouched. `engines` answers the neighbouring question and
        # cannot help here: reaching it needs this import.
        return _unparsable(error, hook=hook)

    return main(argv)


def _unparsable(error: SyntaxError, *, hook: bool) -> int:
    """Say that the checkout which answered does not parse, and which file it was (RK1179).

    Exit 2, the code every other unanswerable call here gets: the command did not run, and a
    caller reading 1 would take it for a verdict about the repository's own contents (RK86).

    **Silent under `guard`.** A hook that fires on every turn degrades to *unenforced* and never
    to a broken session, which is the launcher's own second rule — a refusal printed there is
    read by the harness as the hook having failed, so what a broken engine must not do is take
    the turn down with it. The caller who typed a command gets the sentence; the caller who
    typed nothing gets silence, and `engines` is the read that says why.
    """
    if hook:
        return 0
    where = Path(__file__).resolve().parents[1]
    # The one line of the traceback that identifies anything, spelled as every other position
    # this tool prints is — `file:line:column`, which an editor opens.
    at = f"{error.filename}:{error.lineno}:{error.offset}" if error.filename else "unknown"
    print(
        f"roadkeep: the checkout that answered does not parse, so no command ran:\n"
        f"  engine   {where}\n"
        f"  file     {at}\n"
        f"  said     {error.msg}\n"
        f"  note     nothing was written, and your own files were not read — this is the "
        f"tool's own source, mid-edit or half-checked-out\n"
        f"  reads    `roadkeep engines` says which three copies can answer, from a checkout "
        f"that parses",
        file=sys.stderr,
    )
    return 2

if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1:]))
