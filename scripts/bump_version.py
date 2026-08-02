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

`--dev` produces a throwaway version for a TestPyPI rehearsal, so the index never
sees a collision. It is written to the working tree and never committed — and it
is deliberately *not* a version `tests/test_packaging.py` accepts, which is why the
workflow runs the suite before this script and not after.

There is no changelog to roll: `docs/CHANGELOG.md` is roadkeep's shipped ledger,
indexed by block and owned by `roadkeep ship` (L1). A release is not an entry in it.

Prints `<old> -> <new>` to stdout, and appends `version=<new>` to $GITHUB_OUTPUT
when running inside GitHub Actions.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODULE = ROOT / "src" / "roadkeep" / "__init__.py"
MANIFEST = ROOT / ".claude-plugin" / "plugin.json"

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
    args = parser.parse_args()

    module_text = MODULE.read_text(encoding="utf-8")
    manifest_text = MANIFEST.read_text(encoding="utf-8")

    current = read_version(module_text)
    new_version = bump(current, args.level)
    written = f"{new_version}.dev{args.dev}" if args.dev else new_version

    print(f"{'.'.join(str(part) for part in current)} -> {written}")

    if args.dry_run:
        return 0

    write(MODULE, _VERSION_RE.sub(f'__version__ = "{written}"', module_text, count=1))

    manifest_new, count = _MANIFEST_RE.subn(rf"\g<lead>{written}\g<tail>", manifest_text, count=1)
    if count == 0:
        raise SystemExit(f'Could not find a `"version": "…"` entry in {MANIFEST}.')
    write(MANIFEST, manifest_new)

    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as handle:
            handle.write(f"version={written}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
