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
* **In, less what the encoder added** — PowerShell opens a pipe with U+FEFF, so the field
  the escape hatch exists to carry arrived refused as `char.invisible`, on the one shell
  that most needs it (RK1023). One mark, at position 1; the same codepoint anywhere else in
  the sentence is still prose no keyboard produces, and is still refused.
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

from roadkeep.cli import EXIT_OK, EXIT_USAGE
from roadkeep.verbs.reading import _force_utf8

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
            f"import sys; from roadkeep.verbs.reading import _force_utf8; _force_utf8(sys.stdout); {write}",
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


# -- a stream this process did not open (RK455) -------------------------------


def used_stdin(monkeypatch, text: str = "a body\n", encoding: str = "cp1252") -> None:
    """The stdin an embedding host hands over: a text stream already read from.

    Which is what an xdist worker has — it is bootstrapped over its own stdin, so fd 0
    arrives read — and `reconfigure` on such a stream raises. Measured with `pytest -n 8`
    before this: nine to sixteen failures out of one line, none about what they assert.
    """
    stream = io.TextIOWrapper(io.BytesIO(text.encode(encoding)), encoding=encoding)
    stream.read(1)
    monkeypatch.setattr(sys, "stdin", stream)


def test_a_verb_that_reads_no_prose_runs_over_a_used_stdin(tmp_path, monkeypatch):
    """The whole defect: `main` hardened the three streams before argparse saw a token, so
    a host handing over a used stdin got a traceback where every verb would have worked."""
    from roadkeep.cli import main

    root = project(tmp_path)
    used_stdin(monkeypatch)
    # A read, because the claim is that the *verb* is reached: this fixture is the encoding
    # suite's and carries drift on purpose, so `lint`'s own exit would be the gate's answer
    # rather than an answer about the stream.
    assert main(["-C", str(root), "list", "--block", "A"]) == EXIT_OK


def test_a_prose_read_is_refused_and_never_assumes_the_strictness(tmp_path, monkeypatch, capsys):
    """Not a bare pass. `errors="strict"` on the way in is what keeps input that is not
    UTF-8 refused rather than repaired — a substituted character round-trips into a governed
    file and stays (L3) — so the read says which stream could not be hardened."""
    from roadkeep.cli import main

    root = project(tmp_path)
    used_stdin(monkeypatch)
    code = main(
        ["-C", str(root), "add", "--block", "A", "--symptom", "A symptom", "--why", "-"]
    )
    assert code == EXIT_USAGE
    said = capsys.readouterr().err
    assert "stdin was already read" in said and "strict UTF-8" in said
    # And it names what to do instead, which is the half a refusal owes (RK16).
    assert "--body-file" in said


def test_a_stream_that_takes_the_hardening_is_unchanged(tmp_path, monkeypatch):
    """The ordinary process, where nothing is lost and nothing is said."""
    from roadkeep.verbs import reading

    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(b"a body\n")))
    assert _force_utf8(sys.stdin, errors="strict") is True
    monkeypatch.setattr(reading, "_STDIN_HARDENED", True)
    assert reading._unhardened() is None


def test_a_stream_that_decodes_nothing_needs_no_hardening(monkeypatch):
    """The narrowing that keeps the refusal about the defect. What `errors="strict"` buys is
    that bytes which are not UTF-8 are refused rather than substituted — and a `StringIO` a
    caller handed over is already `str`, so there is no codec that could be quietly keeping
    cp1252. Without this the guard refused every test and every host that supplies one."""
    assert _force_utf8(io.StringIO("prose")) is True


def test_a_used_stream_already_in_utf8_is_the_same_answer(monkeypatch):
    """It arrives the other way and means the same thing: the reconfigure fails, and there
    was nothing to change."""
    stream = io.TextIOWrapper(io.BytesIO("prose".encode()), encoding="utf-8")
    stream.read(1)
    assert _force_utf8(stream, errors="strict") is True


def test_a_used_stream_keeping_another_codec_is_the_one_that_is_refused(monkeypatch):
    stream = io.TextIOWrapper(io.BytesIO("prose".encode("cp1252")), encoding="cp1252")
    stream.read(1)
    assert _force_utf8(stream, errors="strict") is False


# -- the mark the encoder opened the stream with (RK1023) ---------------------


#: What Windows PowerShell 5.1 puts on the wire ahead of a piped string: `$OutputEncoding`'s
#: UTF-8 encoder writes its preamble, and a native command reads it as the first character.
PREAMBLE = "﻿".encode()


def test_a_field_piped_behind_a_byte_order_mark_is_the_sentence_and_not_a_refusal(tmp_path):
    """The escape hatch, on the shell that needs it most.

    `--why -` exists because a shell eats an apostrophe or a backtick; PowerShell is the one
    that does, and it is also the one that opens the pipe with U+FEFF. Before this the field
    came back refused as `char.invisible` — correct about the codepoint, wrong about who
    wrote it, and naming stdin as the remedy for a byte stdin had just added.
    """
    root = project(tmp_path)
    done = cli(
        root,
        "add",
        "--block",
        "A",
        "--symptom",
        "A second symptom",
        "--why",
        "-",
        stdin=PREAMBLE + "Because the shell's own encoder wrote a byte the author did not.".encode(),
    )
    assert done.returncode == EXIT_OK, done.stderr
    written = (root / "ROADMAP.md").read_bytes()
    assert b"Because the shell's own encoder" in written
    assert PREAMBLE not in written


def test_a_body_piped_behind_a_byte_order_mark_lands_without_it(tmp_path):
    """The other reader, and the one a caller reaches first: a paragraph is the field
    somebody pipes before they ever pipe a sentence."""
    root = project(tmp_path)
    done = cli(
        root,
        "add",
        "--block",
        "A",
        "--symptom",
        "A third symptom",
        "--why",
        "Because of another reason.",
        "--section",
        "RK2",
        "--section-body",
        "-",
        stdin=PREAMBLE + "A rationale whose first byte belongs to the encoder.".encode(),
    )
    assert done.returncode == EXIT_OK, done.stderr
    written = (root / "IMPROVEMENTS.md").read_bytes()
    assert b"A rationale whose first byte" in written
    assert PREAMBLE not in written


def test_the_same_codepoint_inside_the_sentence_is_still_refused(tmp_path):
    """The half that must not move. A mark at position 1 is a byte order mark doing its job;
    the same codepoint further in is prose no keyboard produces, and it round-trips into a
    governed file invisibly. One `removeprefix` and not `utf-8-sig` is exactly this line."""
    root = project(tmp_path)
    before = (root / "ROADMAP.md").read_bytes()
    done = cli(
        root,
        "add",
        "--block",
        "A",
        "--symptom",
        "A fourth symptom",
        "--why",
        "-",
        stdin="Because a mark ﻿ landed where no encoder would have put one.".encode(),
    )
    assert done.returncode == EXIT_USAGE
    assert b"char.invisible" in done.stderr
    assert (root / "ROADMAP.md").read_bytes() == before


def test_only_one_mark_comes_off(tmp_path):
    """Two is one the encoder wrote and one somebody pasted, and the second is still prose.
    Held because `lstrip` and `removeprefix` differ only here, and the difference is a field
    silently losing a character it was meant to be refused for."""
    root = project(tmp_path)
    done = cli(
        root,
        "add",
        "--block",
        "A",
        "--symptom",
        "A fifth symptom",
        "--why",
        "-",
        stdin=PREAMBLE * 2 + "Because the second one is not the encoder's.".encode(),
    )
    assert done.returncode == EXIT_USAGE
    assert b"char.invisible" in done.stderr
