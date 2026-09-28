"""The engine's address before RK1699, kept so a launcher committed then still finds it (RK1705).

RK1699 moved the plugin payload into `plugin/`, and with it the engine to
`plugin/scripts/roadkeep.py`. Every adopter keeps the `.claude/hooks/roadkeep-launch.py` that
`install --committed` wrote, and one written before the move looks for `scripts/roadkeep.py`
at the top of a checkout and nowhere else. Measured on 2026-09-25: two adopters naming this
checkout resolved nothing — the server exited 2 and was noticed, and the guard exited 0 in
silence and was not, so for hours no hand edit of a governed file was refused.

So the old path answers, by running the new one: nothing here but the hand-over, so the
arguments, exit codes and refusals stay the engine's. A launcher refreshed by `install
--committed` finds `plugin/` itself, and `lint` names a stale one as `install.stale`; this file
is for the ones nobody has refreshed yet.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1] / "plugin" / "scripts" / "roadkeep.py"

if __name__ == "__main__":
    sys.argv[0] = str(ENGINE)
    runpy.run_path(str(ENGINE), run_name="__main__")
