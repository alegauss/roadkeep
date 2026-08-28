"""Adopt this tool onto a repository that already has a backlog, and record what it printed.

Adoption is the path with the most friction and the least prose (RK1406). A project that
already has a `ROADMAP.md` scaffolds or adopts, declares the roles it wants, and only then
finds out what its existing files break — and what decides the adoption is not the command
list, which the README already gives. It is **what the first commands print on files that were
already there**.

So this is a run rather than a description. It builds a throwaway repository with a genuinely
drifted roadmap in it, executes the adoption in order, and emits every command with the output
it actually produced. `site/docs/scripts/walkthrough.mjs` renders that into a page and
`tests/test_walkthrough.py` executes it, so a refusal whose wording changed fails a build
instead of misleading a reader.

**The throwaway tree is built with `tempfile`, never with a shell.** A path composed in Git
Bash reaches Python as a name Windows has not got, and the run then measures nothing while
looking exactly like a run that measured something. Every command is given `-C <that tree>` for
the same reason: a walkthrough that quietly answered about *this* repository would be a page of
plausible output about the wrong project.

Emits JSON on stdout and writes nothing outside its temporary directory.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

#: The roadmap an adopter actually has: no blocks, ids that are not this tool's shape, one
#: line carrying a paragraph where a sentence belongs, and a marker nobody agreed on. Every
#: one of these produces a finding, which is the point — a clean fixture would walk an adopter
#: through a path they will not be on.
DRIFTED = """# Roadmap

## Block A — Search

- 📋 **PROJ1** **Search is slow** — We should look at making the search faster because users
  have complained about it several times now, and the index rebuild takes most of a minute on
  the larger tenants, which we think is the root cause but have not confirmed yet.
- 📋 **PROJ2** **Login sometimes fails after a deploy** — Nobody has reproduced it.
- ✅ **PROJ3** **The parser was two versions behind** — Upgraded, and the vendored copy removed.
"""

HERE = Path(__file__).resolve().parent.parent


@dataclass
class Step:
    """One command, and what it printed when it was actually run."""

    #: What a reader would type, with the throwaway directory left out — `-C` is how this
    #: script points the tool at the sample and is not part of what an adopter does.
    command: str
    #: Why this step is here, written once. The output is captured; this is not.
    what: str
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    #: Files the step wrote, as the tree held them afterwards, where that is the point of it.
    wrote: dict[str, str] = field(default_factory=dict)


def _run(tree: Path, argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "roadkeep.cli", "-C", str(tree), *argv],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=HERE,
        env=_environment(),
    )


#: What must not reach a published page, and is therefore taken **out** of the environment.
#: `CLAUDE_CONFIG_DIR` would make `engines` report this machine's plugin install; the two git
#: identity pairs would put whoever built the site into a commit the sample makes.
_DROPPED = (
    "CLAUDE_CONFIG_DIR",
    "GIT_AUTHOR_NAME",
    "GIT_AUTHOR_EMAIL",
    "GIT_COMMITTER_NAME",
    "GIT_COMMITTER_EMAIL",
    "ROADKEEP_SRC",
)


def _environment() -> dict[str, str]:
    """The environment, less the few names that would leak this machine into the output.

    **A denylist and not an allowlist**, which is the correction: keeping seven names looked
    tidy and starved Windows of the rest, so a subprocess expanded `%SystemDrive%` literally
    and created a directory by that name in this repository. An ordinary machine is what the
    walkthrough should exercise; the scrubbed one is a test's job, and stripping `PATH` had
    already cost `lint --baseline` its ability to find git.
    """
    import os  # noqa: PLC0415 - this script's only use of the environment

    out = {
        name: value for name, value in os.environ.items() if name not in _DROPPED
    }
    out["PYTHONPATH"] = str(HERE / "src")
    out["PYTHONIOENCODING"] = "utf-8"
    return out


#: The configuration an adopter writes by hand, and the reason this walkthrough has a hand
#: edit in the middle of it: `init` scaffolds `roadkeep.toml` **and** the files it declares, so
#: it refuses outright where the roadmap already exists — and `declare` adds a role rather than
#: choosing a prefix. A project with a backlog already in it therefore writes this file itself.
#: Shown rather than smoothed over, because it is the step an adopter hits and the one no
#: command list mentions.
CONFIG = """prefix = "PROJ"

[files]
roadmap = "docs/ROADMAP.md"
changelog = "docs/CHANGELOG.md"
improvements = "docs/IMPROVEMENTS.md"
"""

#: The second hand edit, and the one the gate asks for by name. This backlog was written
#: without a dependency annotation, so every bullet fails a grammar that expects one — which
#: `lint` reports as `grammar.unreadable`: the rule is wrong here, not the lines. `[grammar]`
#: is how a project says which fields its records actually carry.
GRAMMAR = """
[grammar.roadmap]
drop = ["deps"]
"""


def _write(tree: Path, name: str, body: str, what: str) -> Step:
    """A step that is an edit rather than a command — what the adopter types into a file."""
    path = tree / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8", newline="\n")
    return Step(command="", what=what, wrote={name: body.strip()})


#: What the throwaway tree is called on the page. The real one is a `tempfile` directory under
#: whoever's machine ran the build, so leaving it in would publish a username, and would make
#: every run differ from the last for a reason that is not about the tool.
SAMPLE = "/your/project"


def _redact(text: str, tree: Path) -> str:
    """Take this machine out of the output, in every spelling the tool prints it.

    Four, and the fourth is why this is a loop rather than one `replace`: the **resolved** path.
    `tempfile` hands back `C:\\tmp\\…` where that directory is a junction, and the verbs report
    what they resolved — so a redaction keyed on the handed-back path alone left absolute paths
    on the page while looking like it had worked.

    Case-insensitively on Windows, where two spellings of one path differ only in case and the
    one printed is not always the one composed here.
    """
    resolved = tree.resolve()
    spellings = [
        str(tree),
        tree.as_posix(),
        str(tree).replace("\\", "\\\\"),
        str(resolved),
        resolved.as_posix(),
        str(resolved).replace("\\", "\\\\"),
    ]
    for spelling in sorted(set(spellings), key=len, reverse=True):
        text = re.sub(re.escape(spelling), SAMPLE, text, flags=re.IGNORECASE)
    return text


def _step(tree: Path, argv: list[str], what: str, *, shows: tuple[str, ...] = ()) -> Step:
    found = _run(tree, argv)
    step = Step(
        command="roadkeep " + " ".join(argv),
        what=what,
        stdout=_redact(found.stdout.strip(), tree),
        stderr=_redact(found.stderr.strip(), tree),
        exit_code=found.returncode,
    )
    for name in shows:
        path = tree / name
        if path.exists():
            step.wrote[name] = _redact(path.read_text(encoding="utf-8").strip(), tree)
    return step


def _commit(root: Path) -> None:
    """Make the sample a repository with one commit in it, quietly.

    Its identity is set here rather than taken from the machine: the walkthrough is published,
    and a run that borrowed whoever built it would put their name in a page.
    """
    git = shutil.which("git")
    if git is None:  # pragma: no cover - the walkthrough simply omits the baseline step
        return
    for argv in (
        ["init", "-q"],
        ["config", "user.email", "adopter@example.com"],
        ["config", "user.name", "An Adopter"],
        ["add", "-A"],
        ["-c", "commit.gpgsign=false", "commit", "-q", "-m", "the backlog as it was"],
    ):
        subprocess.run([git, "-C", str(root), *argv], capture_output=True, check=False)


def walk() -> list[Step]:
    """The adoption, in the order somebody does it, against a tree that is genuinely drifted."""
    root = Path(tempfile.mkdtemp(prefix="roadkeep-walkthrough-"))
    try:
        docs = root / "docs"
        docs.mkdir()
        (docs / "ROADMAP.md").write_text(DRIFTED, encoding="utf-8", newline="\n")
        # The two files the configuration will declare beside the roadmap. Empty headings, the
        # way an adopter's would be: this project keeps a backlog and has never had the other
        # two, which is the ordinary starting point rather than a contrived one.
        (docs / "CHANGELOG.md").write_text("# Shipped\n", encoding="utf-8", newline="\n")
        (docs / "IMPROVEMENTS.md").write_text(
            "# Design notes\n", encoding="utf-8", newline="\n"
        )
        # A real repository, because `lint --baseline` resolves a revision and the whole point
        # of that step is what it forgives. A tree with no history answers "not a revision this
        # repository knows", which is correct and is not the lesson.
        _commit(root)

        steps = [
            _step(
                root,
                ["adopt", "docs/ROADMAP.md"],
                "Measure before changing anything. This is the number the decision should be "
                "made against — how many of the lines already there a limit would refuse, and "
                "what the spread is. Nothing is written.",
            ),
            _step(
                root,
                ["init", "--prefix", "TASK"],
                "The wrong command, shown because it is the one everybody reaches for first. "
                "`init` scaffolds, and this project already has the file — so it refuses "
                "without writing anything and names the read that measures what is there.",
            ),
            _write(
                root,
                "roadkeep.toml",
                CONFIG,
                "So the configuration is written by hand — the first of two steps here that "
                "are not commands. `init` writes the file *and* the files it declares, so it "
                "will not touch a project that already has one, and `declare` adds a role "
                "rather than choosing a prefix. The prefix is the one the ids already spell, "
                "so nothing is renumbered.",
            ),
            _step(
                root,
                ["lint"],
                "The first run, and it reports one finding about the **rule** rather than a "
                "list about the lines. This backlog was written without a dependency "
                "annotation, so every bullet fails a grammar that expects one — and a file "
                "where nothing survives is not one somebody hand-edited.",
            ),
            _write(
                root,
                "roadkeep.toml",
                CONFIG + GRAMMAR,
                "The second hand edit, which the finding asked for by name. `[grammar]` is how "
                "a project says which fields its records actually carry — the sixth law "
                "applied to the shape of a line, not just to its limits.",
            ),
            _step(
                root,
                ["lint"],
                "Now the real work list. Every finding names the file, the line and the "
                "command that closes it — and the exit code is 1, which is what makes this a "
                "gate rather than advice.",
            ),
            _step(
                root,
                ["lint", "--fix"],
                "The mechanical half, repaired. Only the derived is touched — an annotation, a "
                "marker's codepoint, whitespace — because the tool never writes prose.",
            ),
            _step(
                root,
                ["list"],
                "What the tool now reads out of a file it did not write. The lines it could "
                "not parse are reported rather than silently dropped, which is how a filtered "
                "listing is stopped from looking complete when it is not.",
            ),
        ]

        # The first ordinary session, which is where the friction adopters actually report is:
        # not the install, but the first write made by hand out of habit.
        steps.append(
            _step(
                root,
                [
                    "block", "add", "A", "--title", "Search",
                    "--organise", "changelog", "--organise", "improvements",
                ],
                "The roadmap declares this block and the two new files do not, so the first "
                "`ship` would have nowhere to put its entry and the first design nowhere to "
                "go. One call declares it wherever it is missing and says which files it "
                "touched. A heading is declared and never invented by a write — a write that "
                "invented one would file the text where nothing looks for it.",
            )
        )
        steps.append(
            _step(
                root,
                [
                    "add",
                    "--block",
                    "A",
                    "--symptom",
                    "The index rebuild blocks every write for most of a minute",
                    "--why",
                    "Search is the feature tenants notice first, and a rebuild that holds the "
                    "write lock makes the whole application look down while it runs.",
                    "--section",
                    "The rebuild holds the write lock",
                    "--section-body",
                    "The rebuild takes an exclusive lock for its whole run, so every write "
                    "queues behind it. Nothing about the index needs that: the writes it "
                    "blocks are to unrelated tables, and the lock is the one line nobody "
                    "revisited when the tenants got larger.",
                ],
                "The first line written through the tool, with its design in the same call. "
                "The id is derived, the pointer is derived, the annotation is derived — and "
                "the format is checked here rather than reported later.",
                shows=("docs/ROADMAP.md",),
            )
        )
        steps.append(
            _step(
                root,
                [
                    "add",
                    "--block",
                    "A",
                    "--symptom",
                    "Search is slow and this sentence is deliberately far longer than the "
                    "limit this project just declared for itself, which is the whole point",
                    "--why",
                    "Because a refusal is what an adopter meets first, and what it says is "
                    "what decides whether the tool is worth the trouble.",
                ],
                "And the refusal. It arrives **before** the prose is composed to fill a line "
                "that would not fit — it names the limit, where the limit is declared, how "
                "much to cut, and that the rest belongs in the rationale rather than being "
                "compressed away. Exit code 2: what has to change is the input, not the file.",
            )
        )
        steps.append(
            _step(
                root,
                ["ship", "PROJ4", "--why", "The rebuild takes a shared lock and writes to a "
                 "side index, so nothing queues behind it."],
                "And the door out. One write moves the line into the ledger, drops the "
                "rationale section the design lived in, and re-derives every annotation that "
                "was waiting on it — so the files never describe a state that did not ship.",
                shows=("docs/ROADMAP.md",),
            )
        )
        steps.append(
            _step(
                root,
                ["lint", "--baseline", "HEAD"],
                "The answer to standing debt. A repository adopting the tool has years of "
                "lines that were never written against these rules, and being refused by all "
                "of them at once is where an adoption stops. This forgives what was already "
                "there by name and gates only what this tree adds.",
            )
        )
        return steps
    finally:
        shutil.rmtree(root, ignore_errors=True)


def main() -> int:
    print(json.dumps([asdict(step) for step in walk()], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
