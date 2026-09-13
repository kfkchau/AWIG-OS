#!/usr/bin/env python3
# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""DEFECT 4 — the check-vocabulary comparator (EP-28V W2).

`design/28` §5's table is the LAW for the interpreter's check vocabulary, and its own
sentence is "Adding a check kind is an ENGINE amendment: design-doc change + owner gate,
never a quiet addition." A law requiring a document change, with no instrument checking
the document, is a warning and not a mechanism: four check kinds lived in
`kernel/opdefs.py`'s `OP_CHECKS` and were absent from the table for days.

DIRECTION IS LAW AND IT IS THE ONE THING A READER OF THIS FILE MUST NOT INVERT.
**The table is AUTHORED. It is NEVER generated from `OP_CHECKS`.** Generating it would
make every quiet addition self-documenting and lawful, which is the exact inversion the
gate exists to prevent. The code is the SUBJECT, the table is the LAW, and this module
exists only to make their divergence LOUD. Nothing here writes to `design/28`, and a
future pass that adds a writer has broken the gate rather than improved the tool.

BOTH DIRECTIONS, because a count is the weaker check wearing the stronger one's name:

  code -> doc   a kind in `OP_CHECKS` with no row in the table. Always a defect: the
                whole content of the gate is that a kind arrives with its row.
  doc -> code   a row naming no live kind, UNLESS the row itself carries a
                legitimate-absence status. The status lives in the ROW, so there is no
                side-list here to rot, and a future legitimate absence gets written
                where the reader already stands.

THE LEGITIMATE-ABSENCE MARKERS ARE MATCHED LITERALLY AND CASE-SENSITIVELY, and that is a
design decision rather than laziness (§A64): a row whose status word is NEARLY right —
`[RETIRING`, `[retired`, `(a feed)` — FIRES. An unrecognised wording fires too. The
failure direction is loud-and-wrong, never silent-and-right, because the alternative is a
comparator that a plausible-looking paraphrase can switch off.

EVERY FINDING HERE IS AN ABSENCE, so a broken comparator returns exactly the clean result
a healthy one returns, and a zero closes a question that a wrong number would reopen.
`positive_control()` therefore runs on EVERY invocation, not once: it plants a known
divergence of each shape into synthetic copies and requires the comparator to find them.
A zero that is not backed by a passing control is reported as UNINTERPRETABLE and is
never reported as a count.
"""
import ast
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OPDEFS = os.path.join(ROOT, 'src', 'kernel', 'opdefs.py')
DESIGN28 = os.path.join(ROOT, 'design', '28-TARGET-STATE-HOST-KERNEL.md')

#: The §5 section this comparator's law lives in. Anchored on the heading text, so a
#: renumbering is a loud failure rather than a silent read of the wrong table.
SECTION_HEADING = '## 5. The check vocabulary'

#: Closed vocabulary of legitimate-absence statuses, matched LITERALLY in the row's own
#: text. Extended only by writing the new status into a row AND adding it here — which is
#: deliberately two acts, because this list is a ceiling on the comparator's silence.
LEGITIMATE_ABSENCE_MARKERS = (
    '[RETIRED',                  # a kind withdrawn by design amendment (`attenuation`)
    '(a feed, not a refusal)',   # a read-only feed that never refuses (`due`)
)

_NAME_RE = re.compile(r'^[a-z][a-z0-9_]*$')


class CheckVocabError(Exception):
    """A structural refusal. The comparator never degrades to a partial answer: if it
    cannot establish either side, it says so and stops, because a partial set produces a
    clean-looking set-difference that is silently wrong in both directions."""


# --------------------------------------------------------------------------- the code side

def check_kinds_from_source(src_text):
    """The check kinds the ENGINE declares, read by AST from `opdefs.py`'s source.

    AST and not grep, because the question is about STRUCTURE — what are the members of
    this tuple — and grep would answer about text: `OP_CHECKS` appears in this module's
    own comments, in `boot.py`, and in four test files. The AST reads the thing; a grep
    pattern is a list of what you believe is in it.

    Refuses loudly on anything it cannot read exactly: no assignment, more than one, a
    non-tuple, or a non-string element. Each of those would otherwise yield a set that is
    merely SMALLER than the truth, and a smaller code side hides a missing row.
    """
    tree = ast.parse(src_text)
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == 'OP_CHECKS':
                    found.append(node.value)
    if not found:
        raise CheckVocabError("no assignment to OP_CHECKS found in the engine source")
    if len(found) > 1:
        raise CheckVocabError(
            f"{len(found)} assignments to OP_CHECKS found; the check vocabulary has one home")
    value = found[0]
    if not isinstance(value, ast.Tuple):
        raise CheckVocabError(
            f"OP_CHECKS is a {type(value).__name__}, not a literal tuple — this comparator "
            "reads the declaration and cannot evaluate a computed one")
    kinds = []
    for elt in value.elts:
        if not (isinstance(elt, ast.Constant) and isinstance(elt.value, str)):
            raise CheckVocabError("OP_CHECKS holds a non-string-literal element")
        kinds.append(elt.value)
    if len(set(kinds)) != len(kinds):
        raise CheckVocabError(f"OP_CHECKS holds a duplicate kind: {kinds}")
    return tuple(kinds)


# --------------------------------------------------------------------------- the law side

def check_rows_from_doc(doc_text):
    """The rows of `design/28` §5's check-vocabulary table, as (name, whole-row-text).

    The whole row travels with the name because the legitimate-absence status lives IN
    the row — that is what keeps this comparator free of a side-list that would rot.
    """
    lines = doc_text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith(SECTION_HEADING):
            start = i
            break
    if start is None:
        raise CheckVocabError(
            f"section heading {SECTION_HEADING!r} not found — the comparator will not guess "
            "which table carries the check vocabulary")

    rows = []
    seen_header = False
    for line in lines[start + 1:]:
        if line.startswith('## '):
            break
        stripped = line.strip()
        if not stripped.startswith('|'):
            continue
        cells = stripped.split('|')
        if len(cells) < 6:
            raise CheckVocabError(
                f"malformed row in the §5 table (expected 4 cells, got {len(cells) - 2}): "
                f"{stripped[:80]!r}")
        name = cells[1].strip()
        if not seen_header:
            if name != 'Check':
                raise CheckVocabError(
                    f"§5's table does not open with a 'Check' column; found {name!r}")
            seen_header = True
            continue
        if set(name) <= {'-', ':'} and name:
            continue                                  # the header separator
        if not _NAME_RE.match(name):
            raise CheckVocabError(
                f"§5 row names {name!r}, which is not a check-kind identifier — a row this "
                "comparator cannot name is a row it cannot police")
        rows.append((name, stripped))
    if not seen_header:
        raise CheckVocabError("§5 carries no table")
    if not rows:
        raise CheckVocabError("§5's table carries no rows")
    names = [n for n, _ in rows]
    if len(set(names)) != len(names):
        raise CheckVocabError(f"§5's table names a check kind twice: {names}")
    return rows


def has_legitimate_absence(row_text):
    """Does this row declare, in its own text, why it names no live check kind?"""
    return any(marker in row_text for marker in LEGITIMATE_ABSENCE_MARKERS)


# --------------------------------------------------------------------------- the set-diff

def defect4(src_text, doc_text):
    """SET-DIFF BOTH DIRECTIONS. Returns (undocumented, unbacked).

    undocumented — kinds the engine declares with no row in §5's table.
    unbacked     — rows naming no live kind and carrying no legitimate-absence status.
    """
    kinds = check_kinds_from_source(src_text)
    rows = check_rows_from_doc(doc_text)
    documented = {name for name, _ in rows}
    undocumented = [k for k in kinds if k not in documented]
    live = set(kinds)
    unbacked = [name for name, text in rows
                if name not in live and not has_legitimate_absence(text)]
    return undocumented, unbacked


# --------------------------------------------------------------- the control, every run

#: A synthetic engine source and a synthetic §5 table carrying ONE planted divergence of
#: each shape, plus the two shapes that must NOT fire and the near-misses that must.
_CONTROL_SRC = 'OP_CHECKS = ("alpha", "planted_undocumented_kind")\n'

_CONTROL_DOC = f"""{SECTION_HEADING} (synthetic — the positive control)

| Check | Semantics | Refuses citing | Delivered |
|---|---|---|---|
| alpha | a kind that is live and documented | SOME-RULE | EP-00 |
| planted_unbacked_row | a row naming no live kind and claiming no status | SOME-RULE | EP-00 |
| planted_retired_row | [RETIRED 2026-01-01] withdrawn by amendment | — | EP-00 |
| planted_feed_row | a read-only feed | — (a feed, not a refusal) | EP-00 |
| planted_near_miss_retiring | [RETIRING 2026-01-01] the status word is nearly right | — | EP-00 |
| planted_near_miss_lowercase | [retired 2026-01-01] the status word is nearly right | — | EP-00 |
| planted_near_miss_feed | a read-only feed | — (a feed) | EP-00 |

## 6. the next section
"""

_CONTROL_EXPECT_UNDOCUMENTED = ['planted_undocumented_kind']
_CONTROL_EXPECT_UNBACKED = ['planted_unbacked_row', 'planted_near_miss_retiring',
                            'planted_near_miss_lowercase', 'planted_near_miss_feed']


def positive_control():
    """Demonstrate the comparator finds KNOWN-PRESENT cases of every shape it reports.

    Returns (ok, detail). DEFECT 4's finding is an ABSENCE, so a structurally broken
    comparator returns the same clean zero a healthy one returns — and a zero reads as a
    discovery ("none exist") where a wrong number would invite a second look. This runs
    on every invocation rather than once, because the reader of a given run needs the
    control that run's zero rests on, not a control some earlier run passed.
    """
    try:
        undocumented, unbacked = defect4(_CONTROL_SRC, _CONTROL_DOC)
    except CheckVocabError as exc:
        return False, f"control raised {type(exc).__name__}: {exc}"
    if undocumented != _CONTROL_EXPECT_UNDOCUMENTED:
        return False, (f"planted undocumented kind not found as expected: "
                       f"{undocumented!r} != {_CONTROL_EXPECT_UNDOCUMENTED!r}")
    if unbacked != _CONTROL_EXPECT_UNBACKED:
        return False, (f"planted unbacked rows not found as expected: "
                       f"{unbacked!r} != {_CONTROL_EXPECT_UNBACKED!r}")
    return True, (f"{len(_CONTROL_EXPECT_UNDOCUMENTED)} planted undocumented kind + "
                  f"{len(_CONTROL_EXPECT_UNBACKED)} planted unbacked rows (3 near-misses) "
                  f"found; 2 legitimate-absence rows correctly silent")


# --------------------------------------------------------------------------- the reporter

def report(src_path=OPDEFS, doc_path=DESIGN28):
    """The lines `inventory.py` prints. Never raises: a structural refusal is reported."""
    ok, detail = positive_control()
    lines = []
    if not ok:
        lines.append("DEFECT 4 — check vocabulary vs design/28 §5    : UNINTERPRETABLE")
        lines.append(f"    positive control FAILED — {detail}")
        lines.append("    a zero from a comparator whose control fails is not a count")
        return lines, False
    try:
        with open(src_path, encoding='utf-8') as fh:
            src_text = fh.read()
        with open(doc_path, encoding='utf-8') as fh:
            doc_text = fh.read()
        undocumented, unbacked = defect4(src_text, doc_text)
    except (OSError, CheckVocabError) as exc:
        lines.append("DEFECT 4 — check vocabulary vs design/28 §5    : UNINTERPRETABLE")
        lines.append(f"    {type(exc).__name__}: {exc}")
        return lines, False
    total = len(undocumented) + len(unbacked)
    lines.append(f"DEFECT 4 — check vocabulary vs design/28 §5    : {total}")
    for k in undocumented:
        lines.append(f"    in OP_CHECKS, NO ROW in §5's table       : {k}")
    for n in unbacked:
        lines.append(f"    row in §5, NOT in OP_CHECKS and no status: {n}")
    lines.append(f"    positive control PASSED — {detail}")
    return lines, True


if __name__ == '__main__':
    import sys
    out, healthy = report()
    print('\n'.join(out))
    sys.exit(0 if healthy else 2)
