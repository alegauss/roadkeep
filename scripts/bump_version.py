#!/usr/bin/env python
"""Pick the next version, in the two files that state one. Standard library only.

Used by `.github/workflows/publish.yml` so that every release run derives its own
number instead of asking a human to type one — and, more to the point, instead of
asking a human to *remember* that the number lives in two places:

    src/roadkeep/__init__.py    __version__, which `pyproject.toml` reads by AST
    .claude-plugin/plugin.json  the version `/plugin install` shows

`tests/test_plugin.py` asserts those two agree, so bumping one is a failing build,
not a wrong release. Both are rewritten by a targeted substitution rather than by a
serialiser: the rest of each file has to come back byte-identical (L3), which
`json.dump` over a parsed manifest cannot promise.

    python scripts/bump_version.py --level patch            # 0.1.0 -> 0.1.1
    python scripts/bump_version.py --level minor            # 0.1.1 -> 0.2.0
    python scripts/bump_version.py --level patch --dry-run  # print, change nothing
    python scripts/bump_version.py --level patch --dev 42   # 0.1.1.dev42
    python scripts/bump_version.py --level patch --for-commit   # the pre-commit hook's

`--dev` produces a throwaway version for a TestPyPI rehearsal, so the index never
sees a collision. It is written to the working tree and never committed — and it
is deliberately *not* a version `tests/test_packaging.py` accepts, which is why the
workflow runs the suite before this script and not after.

There is no changelog to roll: `docs/CHANGELOG.md` is roadkeep's shipped ledger,
indexed by block and owned by `roadkeep ship` (L1). A release is not an entry in it.

`--for-commit` is the pre-commit hook's mode, and the reason the decision it needs
lives here rather than in shell (RK398). The hook may only stage an edit it wrote
itself, and "did this hook write it" is a question about the *version string alone*:
a file whose only difference from the index is the number is this hook's own work
from a run that could not stage, and a file differing by anything wider is somebody
else's. Only the regexes above can tell those apart, so the comparison is made where
they are. The number is derived from the **index**, never from the working tree, which
is what stops the two from drifting apart commit after commit.

It exits 3 — never 1, which means "nothing was written" — where the tree carries more
than the number, so the hook can bump the checkout and stage nothing.

Prints `<old> -> <new>` to stdout, and appends `version=<new>` to $GITHUB_OUTPUT
when running inside GitHub Actions.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODULE = ROOT / "src" / "roadkeep" / "__init__.py"
MANIFEST = ROOT / ".claude-plugin" / "plugin.json"

#: What the two files are called from the repository root, for `git show :<path>`.
TRACKED = ("src/roadkeep/__init__.py", ".claude-plugin/plugin.json")

#: The exit code that says the number was written and may **not** be staged (RK398). Not 1,
#: which the hook reads as "nothing was written" and reports as a failure to bump.
FOREIGN = 3

#: What both version strings are replaced by before two texts are compared: a file whose
#: only difference from the index is the number masks to the same thing.
_MASK = "\x00version\x00"

# The trailing [^"]* tolerates a rehearsal suffix such as .dev42: a TestPyPI run leaves
# one behind in the working tree, and the next run must still parse it.
_VERSION_RE = re.compile(r'^__version__ = "(\d+)\.(\d+)\.(\d+)[^"]*"$', re.MULTILINE)
_MANIFEST_RE = re.compile(r'^(?P<lead>\s*"version":\s*")[^"]*(?P<tail>")', re.MULTILINE)


def read_version(text: str) -> tuple[int, int, int]:
    match = _VERSION_RE.search(text)
    if not match:
        raise SystemExit(f'Could not find a `__version__ = "X.Y.Z"` line in {MODULE}.')
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def bump(current: tuple[int, int, int], level: str) -> str:
    major, minor, patch = current
    if level == "major":
        return f"{major + 1}.0.0"
    if level == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def write(path: Path, text: str) -> None:
    """`newline="\\n"` on purpose: this runs on Windows too, and a release must not be
    the commit that rewrites a file's line endings."""
    path.write_text(text, encoding="utf-8", newline="\n")


def indexed(relative: str) -> str | None:
    """The file as the index holds it, or None where git cannot say.

    None is every reason at once — no git, no repository, a path never added — and they all
    mean the same thing to the caller: there is nothing to compare the tree against, so
    nothing may be staged.
    """
    try:
        finished = subprocess.run(
            ["git", "-C", str(ROOT), "show", f":{relative}"],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except OSError:
        return None
    return finished.stdout if finished.returncode == 0 else None


def masked(text: str) -> str:
    """The text with its version string blanked, so two of them compare by everything else.

    Both patterns over both files: each matches only its own, and one function that does not
    have to be told which file it is holding is one fewer thing to pass around.

    Line endings are normalised because they are git's business and not this comparison's:
    the blob is stored with LF and a Windows checkout reads back CRLF, so a raw compare
    would call every file foreign on the platform this hook was measured on.
    """
    text = _VERSION_RE.sub(f'__version__ = "{_MASK}"', text, count=1)
    text = _MANIFEST_RE.sub(rf"\g<lead>{_MASK}\g<tail>", text, count=1)
    return text.replace("\r\n", "\n")


def _for_commit(level: str) -> tuple[str, bool]:
    """The number this commit gets, and whether the hook may stage it (RK398).

    Derived from the **index** and not from the working tree, which is the whole repair.
    RK320's guard refused to stage a file carrying an edit it did not write, and then wrote
    the bump into the tree unconditionally — so its own write was that edit on the next run,
    and the refusal re-armed itself for ever. Measured over eight commits in one session:
    the checkout reached 0.1.392 while HEAD still said 0.1.388.

    So what is asked is not *is this file dirty* but *is the difference the number*. A tree
    that masks to the index is this hook's own earlier bump, however far it has drifted, and
    the number derived from the index puts it back on the sequence the commits are in. A file
    differing by anything wider is the case RK320 measured, and stays refused.
    """
    blobs = [indexed(relative) for relative in TRACKED]
    if any(blob is None for blob in blobs):
        # Nothing to compare against, so nothing may be staged — and the tree's own number
        # still moves, because RK153 is about the plugin the running session loads.
        return bump(read_version(MODULE.read_text(encoding="utf-8")), level), False

    module_blob, manifest_blob = blobs
    ours = all(
        masked(path.read_text(encoding="utf-8")) == masked(blob)
        for path, blob in ((MODULE, module_blob), (MANIFEST, manifest_blob))
    )
    if not ours:
        return bump(read_version(MODULE.read_text(encoding="utf-8")), level), False
    return bump(read_version(module_blob), level), True


def main() -> int:
    parser = argparse.ArgumentParser(description="Pick the next version.")
    parser.add_argument(
        "--level",
        choices=("patch", "minor", "major"),
        default="patch",
        help="Which part of the version to increment (default: patch).",
    )
    parser.add_argument(
        "--dev",
        default=None,
        help="Build a throwaway X.Y.Z.devN version for a rehearsal upload.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print the result, write nothing.")
    parser.add_argument(
        "--for-commit",
        action="store_true",
        help="Derive the number from the index, and exit 3 where the tree carries more.",
    )
    args = parser.parse_args()

    module_text = MODULE.read_text(encoding="utf-8")
    manifest_text = MANIFEST.read_text(encoding="utf-8")

    current = read_version(module_text)
    stageable = True
    if args.for_commit:
        new_version, stageable = _for_commit(args.level)
    else:
        new_version = bump(current, args.level)
    written = f"{new_version}.dev{args.dev}" if args.dev else new_version

    print(f"{'.'.join(str(part) for part in current)} -> {written}")

    if args.dry_run:
        return 0 if stageable else FOREIGN

    write(MODULE, _VERSION_RE.sub(f'__version__ = "{written}"', module_text, count=1))

    manifest_new, count = _MANIFEST_RE.subn(rf"\g<lead>{written}\g<tail>", manifest_text, count=1)
    if count == 0:
        raise SystemExit(f'Could not find a `"version": "…"` entry in {MANIFEST}.')
    write(MANIFEST, manifest_new)

    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as handle:
            handle.write(f"version={written}\n")

    return 0 if stageable else FOREIGN


if __name__ == "__main__":
    sys.exit(main())
