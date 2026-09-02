"""Order a block's delivered claims by a sentence about to be proposed (RK442).

`delivered` is one of the two reads before an `add`, and it was the last query answering by
printing the file: `delivered B` is 103 lines and 9,773 bytes spent to decide one question,
which is L5 unapplied to its own verb. What the author actually asks is *does this collide
with something already shipped*, and the entries that could answer it are a handful.

So the entries are ranked against the proposed sentence and the nearest few are printed.
Measured on the `superseded by` pairs this ledger records — the only cases where the right
answer is known — nine of eleven true partners land inside the five, seven of them first,
against blocks of 36 to 227 entries. Five lines instead of a hundred, same recall.

**What is ranked is both prose fields and not the symptom alone** (RK1477). Two authors writing
the same defect share their subject and almost none of their words; where they agree is the
`why`, which names the flags and verbs at issue by their spelling. Joining it moved six of
eleven inside the five to nine, and the worst reached rank from 11 to 3.

**The two out of reach are not misses** (RK1183). A retirement may name the task that
delivered the larger half of a claim rather than the one whose symptom matches: RK1182 names
RK1152, and this read places RK348 first — whose sentence is nearly RK1182's own, and which
delivered the other half. The reach is over pairs whose *sentences* are the pair, which is what
a proposal about to be written has, so `tests/test_ranking.py` holds the count as a floor and
publishes what is out of reach rather than exempting it by name.

Three constraints are the whole design, and each is a thing this deliberately does not do:

* **It never refuses and never warns.** RK441 measured that the absolute score separates
  nothing — two of the true pairs score below the 13th percentile of the top-1 score a
  proposal with *no* duplicate produces, so a threshold catching them all flags 419 of 426.
  The absence of a gate is a known result and not caution, and it is why :func:`nearest`
  returns an *order* and no number: publishing a score invites the threshold the measurement
  rules out. Relative order inside one query carries signal; the score does not travel
  between queries.
* **It stores no index.** BM25 rebuilt per call costs 0.23 ms over these 426 entries and
  0.73 ms over Turing's 892 — a second store would buy nothing and cost L2.
* **It takes no dependency.** The ranking below is stdlib. Lucene is a JVM and every Python
  index is a wheel, in a tool whose whole promise is `argparse` + `tomllib`.

The no-model non-goal is not reached. Nothing here writes prose or judges meaning; it orders
lines that already exist by word overlap, and the answer is unchanged in kind — the author
still reads it and still decides.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Sequence

#: Runs of letters and digits, lowercased. Not a stemmer and not a stopword list: both are
#: judgements about a language, and the corpora this reads are four projects' English plus
#: whatever identifiers their symptoms carry. BM25's own idf already discounts a word that
#: is in every entry, which is the whole of what a stopword list would have bought here.
_WORD = re.compile(r"[0-9a-z]+")

#: How many entries `delivered --near` prints. Five, because the worst of the pairs where the
#: right answer is known lands at #3 — so five is the recall of a hundred with two ranks of
#: headroom, and the figure moves only if a pair is ever found further down. It has not: the
#: eleven pairs this ledger now records reached #11 and #32 before :func:`claim` joined the
#: `why` to the corpus (RK1477), which bought the headroom rather than spending it.
#: Not configuration (L6): a project declares its limits, and this is a property of how far
#: down the true answer has ever been, which a project cannot know about its own ledger.
NEAREST = 5

#: How many an `add` volunteers beside the line it just wrote (RK1370). Three and not
#: :data:`NEAREST`, because the two answer different callers: that one is asked for and sized
#: for recall, and this one arrives unrequested on every `add`, so it is sized to be read. The
#: worst of the pairs where the right answer is known lands at #2, so three keeps every pair
#: this ledger knows about with a rank of headroom — nine of eleven, where the symptom alone
#: kept six (RK1477). An `add` joins the `why` on the query side too, which :func:`claim` says
#: is an argument and not a reading: what that caller holds is an author's own sentence.
#: Not configuration (L6), for the reason the number above is not.
#:
#: **Unfiltered, like the read it volunteers.** A first cut dropped entries sharing no word
#: with the symptom, so an `add` nobody had a neighbour for would say nothing. Measured against
#: this ledger it did not work and could not: a query about a leaking kitchen floor keeps three
#: of Block C's entries on `the`, `is` and `an`, and the one term that discriminates — `floor`,
#: in one entry of 137 — is indistinguishable at that door from `filed` or `delivered`. Which
#: is RK441's own finding arriving from the other side: no threshold separates a duplicate from
#: a neighbour, so a filter here would be the impossible gate rebuilt as a silence. The rows are
#: the same rows `--near` prints, and the sentence above them says what the order is not.
VOLUNTEERED = 3

#: Saturation and length normalisation, at the figures BM25 is published with. Not
#: configuration (L6): a project declares how long its lines may be, and these are
#: properties of the ranking rather than of the backlog it is run over.
_K1 = 1.5
_B = 0.75


def words(text: str) -> list[str]:
    """The tokens a sentence contributes, in order of appearance."""
    return _WORD.findall(text.lower())


def claim(symptom: str, why: str) -> str:
    """The text one entry contributes to the ranking: **both** of its prose fields (RK1477).

    The corpus was symptoms alone, and a second author writing the same defect writes a
    different sentence about it — `budget states the allowance and cannot be handed a draft`
    against `budget says what a why is allowed and nothing measures the why about to be
    written`. Same subject, almost no shared words, and `budget` is in most of that block so
    its idf is near zero. The re-filing ranked 7th of 155.

    The `why` is where those two agree: it says *what the reader needed and did not get*, and
    it names flags and verbs by their spelling, which is the vocabulary two authors do share.
    Measured over the eleven `superseded by` pairs this ledger records, joining it **to the
    corpus** moves six inside `NEAREST` to nine, with the worst reached rank 11 → 3; the two
    never reached are RK1182→RK1152 and RK1257→RK1204, which name the task that delivered the
    larger half of a claim rather than the one whose sentence matches — out of reach of word
    overlap in either shape, and not a regression this join introduced.

    **The query side of it is not measurable here**, and the figures above are the corpus join
    alone for that reason. A retired entry's `why` is written at the retirement and describes
    its partner, quoting that entry's own sentence: RK1456's names RK1190 and then restates it.
    So the eleven queries whose answer is known are the one population where joining the query
    would be scoring the ground truth, and `tests/test_ranking.py` holds the corpus shape.
    `add` joins it anyway, that caller's `why` being an author's own sentence about a line
    nothing has superseded — an argument, and said to be one.

    Joined with a space and never concatenated: the two fields are separate sentences and a
    tokeniser splitting on non-alphanumerics would fuse the last word of one to the first of
    the other. Empty halves fall out, so an entry or a query with only a symptom is exactly
    what it was before.
    """
    return f"{symptom} {why}".strip()


def nearest(query: str, corpus: Sequence[str], count: int) -> tuple[int, ...]:
    """The indices of the ``count`` entries of ``corpus`` closest to ``query``, nearest first.

    Indices and not scores, and not the strings either: the caller holds the entries and
    everything about them the answer has to print, and what this knows is only the order.
    That is also the shape RK441 argues for — a caller handed a score is one turn from a
    threshold the measurement says cannot exist.

    Ties keep the corpus's own order, which is the ledger's, so two entries a query cannot
    separate are printed in the order they shipped rather than in whatever order a sort
    happened to leave them. An entry sharing no word with the query scores zero and is
    still returned where the count is not filled: "these are the nearest" is true of a
    block whose every entry is far, and dropping them would make an empty answer mean two
    things again — nothing near, and nothing at all.
    """
    if count <= 0 or not corpus:
        return ()
    documents = [words(text) for text in corpus]
    scored = _scores(words(query), documents)
    order = sorted(range(len(corpus)), key=lambda index: (-scored[index], index))
    return tuple(order[:count])


def _scores(query: Sequence[str], documents: Sequence[Sequence[str]]) -> list[float]:
    """BM25 for one query over a corpus built for it and thrown away.

    Okapi BM25, which is fifty lines here because the corpus is small enough to hold in a
    list: the inverse document frequency of each query term, weighted by how often the term
    occurs in the entry and damped by how long that entry is against the average. A term the
    query repeats counts once — a symptom is one sentence, and a word said twice in it is
    emphasis rather than evidence.
    """
    total = len(documents)
    lengths = [len(document) for document in documents]
    average = sum(lengths) / total if total else 0.0
    counted = [Counter(document) for document in documents]
    scores = [0.0] * total
    for term in dict.fromkeys(query):
        holding = sum(1 for count in counted if term in count)
        if not holding:
            continue
        # The +0.5 terms are the published smoothing, and the outer 1 + … is what keeps a
        # term present in every entry at zero rather than negative: a word the whole block
        # shares is no evidence, and evidence *against* is not a thing word overlap knows.
        idf = math.log(1 + (total - holding + 0.5) / (holding + 0.5))
        for index, count in enumerate(counted):
            frequency = count.get(term, 0)
            if not frequency:
                continue
            damping = _K1 * (1 - _B + _B * lengths[index] / average) if average else _K1
            scores[index] += idf * frequency * (_K1 + 1) / (frequency + damping)
    return scores
