"""The stdio hardening, held against the environment that broke it (RK337).

A capture from an adopting project recorded `lint` dying with `UnicodeEncodeError:
surrogates not allowed`, under `PYTHONIOENCODING=utf-8:surrogateescape`. By the time `report`
re-ran the command it exited 0, so the stored file carries exit 0, no traceback, and a `why`
blaming a strict encode in `config.py` — a module that opens its file `rb`, hands it to
`tomllib`, and encodes nothing. That diagnosis is not reproducible and it is wrong; what is
checkable is the surface the crash *class* needs, which is what this file is.

`main` reconfigures all three streams to UTF-8 in its first three statements — strict in,
`backslashreplace` out. Nothing in the rest of the suite declares a stdio encoding, so the
hardening was attested only by the absence of mojibake in tests that inherit a clean
environment: it could stop working without anything going red. Every test here runs the CLI
in **its own process, with an encoding declared, and reads the result as bytes** — decoding
the output in the parent would put the assertion behind a second codec and answer about that
one instead.

Four properties, and one boundary:

* **Out** — stdout and stderr carry UTF-8 whatever the environment declared, so a marker and
  an em dash survive `ascii` and `cp1252`, on the answer path and on the refusal path.
* **In** — a piped body is decoded as UTF-8 and not as the declared codec, which is the
  defect the hardening was written for: a cp1252 read of one em dash is three characters that
  then round-trip out of the governed file forever (L3).
* **In, strictly** — input the declared codec would have *repaired* into lone surrogates is
  refused, exit 2, nothing written. A substituted character in a governed file is worse than
  a refusal, and this is the half `utf-8:surrogateescape` attacks.
* **Escaped, not fatal** — a lone surrogate reaching stdout is `\\udcff` and exit 0. The
  control run reproduces the field's exact message, so the assertion is about the `errors=`
  choice rather than about a message being absent.
* **The boundary is not closed** — the hardening is `main`'s, so interpreter startup and
  every import still print through whatever the environment declared. The last test states
  that as a fact rather than leaving it to be assumed either way.
"""

from __future__ import annotations

import io
import os
import subprocess
import sys
from pathlib import Path

import pytest

from roadkeep.cli import EXIT_OK, EXIT_USAGE, _force_utf8

PACKAGE = Path(__file__).resolve().parents[1] / "src"

#: The two codepoints every assertion here is about, as the bytes a UTF-8 stream writes: the
#: marker, which no single-byte codec can encode at all, and the em dash, which cp1252 *can* —
#: at a different byte, which is what makes a wrong decode silent rather than loud.
MARKER = "📋".encode()
DASH = "—".encode()

#: One task, so `list` has a line to print and the printed line carries both codepoints.
ROADMAP = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: —) **A symptom** — Because of a reason.
"""

IMPROVEMENTS = """# Improvements

## Block A — The model
"""

CONFIG = (
    'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
    'improvements = "IMPROVEMENTS.md"\n'
)

#: Every stdio encoding a session can declare that is not this tool's own. `ascii` cannot spell
#: either codepoint; `cp1252` can spell one of them at the wrong byte; the third is the one the
#: field capture recorded, and the only one whose *error handler* invents characters.
HOSTILE = ("ascii", "cp1252", "utf-8:surrogateescape")


def project(tmp_path: Path) -> Path:
    """A governed project whose every file is UTF-8 on disk — written in binary, because
    `write_text` would take its encoding from the same locale this file is about."""
    for name, body in (
        ("roadkeep.toml", CONFIG),
        ("ROADMAP.md", ROADMAP),
        ("CHANGELOG.md", "# Changelog\n\n## Block A — The model\n"),
        ("IMPROVEMENTS.md", IMPROVEMENTS),
    ):
        (tmp_path / name).write_bytes(body.encode())
    return tmp_path


def cli(
    root: Path, *args: str, encoding: str | None = None, stdin: bytes = b""
) -> subprocess.CompletedProcess[bytes]:
    """The CLI in its own process, with a declared stdio encoding, captured as bytes.

    `capture_output` and no `text=`: the question is which bytes the child wrote, and decoding
    them here would answer about the parent's codec. `PYTHONIOENCODING` is the whole subject —
    it is the one knob that reaches the interpreter before any line of this package runs.
    """
    environment = {**os.environ, "PYTHONPATH": str(PACKAGE)}
    if encoding is not None:
        environment["PYTHONIOENCODING"] = encoding
    return subprocess.run(
        [sys.executable, "-m", "roadkeep.cli", *args],
        cwd=root,
        input=stdin,
        capture_output=True,
        check=False,
        env=environment,
    )


@pytest.mark.parametrize("encoding", HOSTILE)
def test_stdout_carries_utf8_whatever_the_environment_declared(tmp_path, encoding):
    """The answer path. `ascii` cannot encode a marker, so without the hardening this is not a
    wrong byte but a dead command — which is the shape the field report described."""
    done = cli(project(tmp_path), "list", "--block", "A", encoding=encoding)
    assert done.returncode == EXIT_OK, done.stderr
    assert MARKER in done.stdout
    assert DASH in done.stdout


@pytest.mark.parametrize("encoding", HOSTILE)
def test_stderr_carries_utf8_whatever_the_environment_declared(tmp_path, encoding):
    """The refusal path, which is the one an agent reads most and the one no other test in the
    suite watches for encoding: `add`'s over-length report spells its arithmetic with an em
    dash, so a refusal is a second place the same crash class lives."""
    done = cli(
        project(tmp_path),
        "add",
        "--block",
        "A",
        "--symptom",
        "A symptom",
        "--why",
        "word " * 60,
        encoding=encoding,
    )
    assert done.returncode == EXIT_USAGE
    assert DASH in done.stderr


def test_a_piped_body_is_read_as_utf8_and_not_as_the_declared_codec(tmp_path):
    """The defect the hardening was written for, from the other side.

    cp1252 is the Windows console default and it decodes every byte of a UTF-8 em dash into a
    character of its own, so the body lands in the governed file as mojibake — and L3 then
    preserves it, byte for byte, forever. The assertion is on the file rather than on the
    command's own echo: what round-trips is what was written.
    """
    root = project(tmp_path)
    body = (
        "A rationale carrying an em dash — and a marker 📋, so a cp1252 read of this "
        "sentence is three characters where one belongs."
    ).encode()
    done = cli(
        root,
        "add",
        "--block",
        "A",
        "--symptom",
        "A second symptom",
        "--why",
        "Because of another reason.",
        "--section",
        "RK2",
        "--section-body",
        "-",
        encoding="cp1252",
        stdin=body,
    )
    assert done.returncode == EXIT_OK, done.stderr
    written = (root / "IMPROVEMENTS.md").read_bytes()
    assert DASH in written
    assert MARKER in written
    # Named explicitly, because the pass above is also what a *lossless* wrong decode looks
    # like: this is the byte sequence cp1252 would have produced for the em dash.
    assert "—".encode("utf-8").decode("cp1252").encode() not in written


def test_undecodable_input_is_refused_rather_than_repaired(tmp_path):
    """`utf-8:surrogateescape` is the environment the capture recorded, and its error handler is
    the reason this matters: it turns an undecodable byte into a lone surrogate that reads as a
    character right up to the moment something encodes it. `main` reconfigures stdin **strict**
    so the byte is refused at the door, exit 2, and nothing is written — a repaired character
    in a governed file is a defect L3 makes permanent, where a refusal costs one call.
    """
    root = project(tmp_path)
    before = (root / "IMPROVEMENTS.md").read_bytes()
    done = cli(
        root,
        "add",
        "--block",
        "A",
        "--symptom",
        "A second symptom",
        "--why",
        "Because of another reason.",
        "--section",
        "RK2",
        "--section-body",
        "-",
        encoding="utf-8:surrogateescape",
        stdin=b"A body carrying an undecodable byte \xff and enough prose after it to be a sentence.",
    )
    assert done.returncode == EXIT_USAGE
    assert b"0xff" in done.stderr
    assert (root / "IMPROVEMENTS.md").read_bytes() == before


def test_a_lone_surrogate_on_stdout_is_escaped_and_not_fatal():
    """The field's exact message, reproduced — and then not raised.

    Two runs of the same write. The first hardens the stream the way `main` does and the
    surrogate arrives as its `\\udcff` escape; the second asks for `strict`, which is what
    `PYTHONIOENCODING=utf-8` alone gives, and dies with `surrogates not allowed`. The control
    is the assertion: without it this test would pass against a stream that never saw a
    surrogate, and the property under test is the `errors=` argument rather than the call.
    """
    write = "sys.stdout.write('a lone surrogate \\udcff here')"
    hardened = subprocess.run(
        [
            sys.executable,
            "-c",
            f"import sys; from roadkeep.cli import _force_utf8; _force_utf8(sys.stdout); {write}",
        ],
        capture_output=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(PACKAGE), "PYTHONIOENCODING": "utf-8"},
    )
    assert hardened.returncode == EXIT_OK, hardened.stderr
    assert b"\\udcff" in hardened.stdout

    strict = subprocess.run(
        [
            sys.executable,
            "-c",
            f"import sys; sys.stdout.reconfigure(encoding='utf-8', errors='strict'); {write}",
        ],
        capture_output=True,
        check=False,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    assert strict.returncode != EXIT_OK
    assert b"surrogates not allowed" in strict.stderr


def test_a_stream_that_cannot_be_reconfigured_is_left_alone():
    """`main` runs on whatever the three names hold, and that is not always a `TextIOWrapper`:
    under a harness that captured them, or a caller that replaced them, `reconfigure` is simply
    absent. The hardening is best-effort by construction — the alternative is a tool that
    cannot start under its own test runner — so the guard is what is asserted here.
    """
    plain = io.StringIO()
    _force_utf8(plain)
    _force_utf8(object())
    plain.write("no reconfigure, no crash, and no encoding to check")
    assert plain.getvalue().startswith("no reconfigure")


def test_importing_the_package_hardens_nothing():
    """Where the covered surface starts, stated rather than assumed.

    The three calls are in `main`, so interpreter startup, every import and anything an import
    prints go through the environment's codec. This is the honest boundary and not a defect to
    fix by moving the calls to module scope: import-time side effects on `sys.stdout` reach
    every embedder of this package, and nothing here prints at import. The test exists so that
    a future print-at-import is a red in the file that explains why.
    """
    done = subprocess.run(
        [sys.executable, "-c", "import roadkeep.cli, sys; print(sys.stdout.encoding)"],
        capture_output=True,
        check=True,
        env={**os.environ, "PYTHONPATH": str(PACKAGE), "PYTHONIOENCODING": "ascii"},
    )
    assert done.stdout.strip() == b"ascii"
