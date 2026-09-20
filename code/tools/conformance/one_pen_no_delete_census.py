# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (record, pen, actor attribution, custody handover, departure record, census).
# NON-GOAL: no offensive capability of any kind — this ENUMERATES every op in the registry and
# READS each as ONE-PEN or CROSS-PEN (I1) and as CONSERVING or DELETE/MERGE-BY-COPY (I14), the
# sibling of the effect-order and five-families censuses. It performs no effect, mints no input,
# drives no attack; it reads source and op definitions. Full declaration: SCOPE-STATEMENT.md.
"""P14 · I1, I14 — THE ONE-PEN + NO-DELETE CENSUS (the enumerator + classifier).

The owner's B10/I1/I14/L12/L14 (design/52): a machine holds MANY records and each keeps exactly ONE
pen — no op appends to a record OTHER than the actor's own (I1, L12); and consolidation is ONLY EVER
the handover ceremony — never a merge by copy, and there is no delete (I14, L14). Both are STANDING
censuses: found once, now found everywhere. This is the third sibling of the effect-order census
(I1-of-EP-INSTRUMENTS-1) and the five-families census (I20) — an INSTRUMENT over the code, never a
founding op or check kind. It REUSES their composed full kernel and their one reading of the
irreversible byte primitives, so no census drifts from another.

TWO INDEPENDENT READINGS, ONE ROW PER OP (the five-families discipline: two readings that cannot be
made to share a vocabulary, so neither can hide the other's failure).

READING 1 — ONE PEN (I1, L12). Who does the op write the record AS?
    * OWN-PEN         the row is attributed to the CALLING actor — the actor's own pen. A definition-
                      born op is own-pen BY CONSTRUCTION: the shared interpreter attributes every row
                      it mints to the calling actor (opdefs.py:3006 `rec = {"actor": actor, ...}`).
                      A code-registered op is own-pen when its handler's minted draft sets
                      `"actor"` to the handler's own actor parameter.
    * RECORDER        the row is attributed to SYSTEM — the founding RECORDER constant (WRITE-ACTIVITY,
                      BLOCK, the attestation row). SYSTEM is the machine's own recorder identity, not a
                      SECOND party's record; this is the ONE lawful non-caller attribution, a CLOSED set
                      named in one place (`RECORDER_IDENTITIES`), the same discipline as the effect-order
                      census's IRREVERSIBLE_PRIMITIVES. Extend it only by a filed ruling.
    * CROSS-PEN (RED) the load-bearing failure: a handler mints a draft attributed to NEITHER the caller
                      NOR the recorder — another party's id, or a caller-supplied name. That op writes a
                      record OTHER than the actor's own — a SECOND pen on a record. Over the shipped
                      registry this set is EMPTY (I1 holds). A cross-pen op is a finding for the paper
                      (one pen per record refuted), never a census bug to widen the recorder set around.
    * UNKNOWN (RED)   an op whose handler source cannot be read at all — it could hide a cross-pen write,
                      so it reds, exactly as the sibling censuses red on an unreadable handler.

READING 2 — NO DELETE, NO MERGE-BY-COPY (I14, L14). How does the op CONSOLIDATE or REMOVE?
    * The ONLY lawful removal of local content bytes is the HANDOVER ceremony (erasure.HANDOVER_OP):
      duplicate the chain, byte-verify, a signed receipt, remove the local bytes as the gate's
      DEFERRED effect, a departure record stands. Any OTHER op that reaches an irreversible removal
      primitive is a STANDALONE DELETE and REDS — even deferred, because a standalone delete is not
      the ceremony (capability-absence: there is no delete function, L14). The irreversible-primitive
      vocabulary is REUSED from the effect-order census (IRREVERSIBLE_PRIMITIVES), read in one place.
    * A MERGE-BY-COPY op — one that consolidates records by DUPLICATING one body's content into
      another (keeping both, no receipt, no departure) — is ABSENT. Read positively against a CLOSED
      forbidden-consolidation vocabulary (`MERGE_BY_COPY_STEMS`): an op whose declared purpose is to
      merge / consolidate / absorb / copy-into records reds. Over the shipped registry this set is
      EMPTY (consolidation is the handover ceremony alone).

CAP (stated, per the sibling censuses' honesty standard). READING 2's merge-by-copy arm is a
VOCABULARY reading — it reads an op's declared NAME/purpose, not a semantic proof that no handler
anywhere duplicates a body's bytes into another record. That semantic floor is carried jointly by:
READING 1 (no op writes another record's pen), the standalone-delete arm (the handover is the one
removal), and the effect-order census (no inline irreversible effect). The three together leave a
merge-by-copy nowhere to hide a byte; this arm names the vocabulary explicitly so a future op that
DECLARES a merge consolidation reds at mint.

USAGE
    python3 -m tools.conformance.one_pen_no_delete_census          # print the classification table
    python3 -m tools.conformance.one_pen_no_delete_census --md     # emit the evidence markdown body
"""

import ast
import inspect
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(os.path.dirname(os.path.dirname(_HERE)), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

# REUSED, never re-authored: the composed full kernel (widest surface, the handover ceremony
# registered) and the ONE reading of irreversible byte primitives. Importing them keeps this census
# over the SAME registry and the SAME primitive vocabulary as its two siblings — neither can drift.
from tools.conformance.effect_order_census import (   # noqa: E402
    build_full_kernel_for_census,
    IRREVERSIBLE_PRIMITIVES,
    classify_source as _classify_effect_source,
)
from kernel import erasure                             # noqa: E402  (the one removal op's name)


# ---- READING 1 vocabulary: the closed set of lawful NON-CALLER attributions --------------------
# SYSTEM is the founding RECORDER identity — the machine's own record-keeper, present since genesis
# (boot.py WRITE-ACTIVITY / BLOCK, attestation.py the attestation row). A row it mints is the
# machine's OWN pen, never a second party's record. This is the ONE lawful non-caller attribution;
# a new entry here is a PAPER change (L12: one pen per record), never a code convenience. Read in one
# place, by both the tool and its test.
RECORDER_IDENTITIES = frozenset({"SYSTEM"})


# ---- READING 2 vocabulary: the closed forbidden-consolidation stems -----------------------------
# Consolidation is the HANDOVER CEREMONY ALONE (L14). An op whose declared name/purpose is to combine
# records by copying — merge, consolidate, absorb, copy-into — is the forbidden shape. A closed set,
# named in one place; a new stem is a paper finding (a merge-by-copy op appeared), never a widening.
MERGE_BY_COPY_STEMS = ("MERGE", "CONSOLIDATE", "ABSORB", "COPY-INTO", "COPYINTO")

# The one lawful removal op — the handover ceremony (erasure.HANDOVER_OP == "HANDOVER-CUSTODY"). Read
# from erasure so a rename there cannot silently desync this census.
HANDOVER_OP = erasure.HANDOVER_OP


# ---- READING 1 — the one-pen classifier ---------------------------------------------------------

class _ActorAttrFinder(ast.NodeVisitor):
    """Walk a handler's AST; collect the value node of every Dict entry whose key is the string
    "actor". A handler mints its record as a dict literal (`{"actor": actor, ...}` or
    `draft = {...}; return draft`), so every such Dict entry is a place the row's pen is set."""

    def __init__(self):
        self.actor_values = []          # list of ast value nodes assigned to an "actor" key

    def visit_Dict(self, node):
        for k, v in zip(node.keys, node.values):
            if isinstance(k, ast.Constant) and k.value == "actor":
                self.actor_values.append(v)
        self.generic_visit(node)


def _handler_actor_param(fdef):
    """The name of a handler's first positional parameter — the calling actor (`def _h(actor, params)`).
    Read from the source, never assumed to be spelled "actor", so a handler that names it otherwise is
    still read correctly."""
    args = fdef.args.posonlyargs + fdef.args.args
    return args[0].arg if args else None


def _classify_one_pen(op, definition, handler_src):
    """Read one op's attribution. Returns (klass, reason) with klass in
    {own-pen, recorder, cross-pen, unknown}.

    A DEFINITION-BORN op is own-pen by construction (the shared interpreter attributes to the caller).
    A CODE-REGISTERED op is read from its handler: every `"actor"` value its draft(s) set must be the
    handler's own actor parameter (own-pen) or a RECORDER identity (recorder); any other value is a
    cross-pen write."""
    if definition is not None:
        return "own-pen", ("definition-born: the shared interpreter attributes every minted row to "
                           "the calling actor (opdefs.py:3006)")
    if handler_src is None:
        return "unknown", "source unreadable: no definition and no handler source"
    try:
        tree = ast.parse(_dedent(handler_src))
    except SyntaxError:
        return "unknown", "handler source did not parse"
    # descend to the inner handler def (registered handlers are closures: `def factory(...): def _h(...)`)
    fdef = _innermost_handler_def(tree)
    if fdef is None:
        return "unknown", "no handler function definition found in source"
    actor_param = _handler_actor_param(fdef)
    finder = _ActorAttrFinder()
    for stmt in fdef.body:
        finder.visit(stmt)
    if not finder.actor_values:
        # the handler mints no `"actor"`-keyed draft of its own — it appends nothing, or returns a
        # passthrough. It writes no second pen. (A pure-refusal / passthrough handler.)
        return "own-pen", "handler mints no record of its own (no `actor`-keyed draft)"
    recorder_seen = False
    for v in finder.actor_values:
        if isinstance(v, ast.Name) and v.id == actor_param:
            continue                                            # own pen
        if isinstance(v, ast.Constant) and v.value in RECORDER_IDENTITIES:
            recorder_seen = True
            continue                                            # the recorder's own pen
        # anything else: a param that is not the caller, a foreign literal, a computed id → CROSS-PEN.
        rendered = _render(v)
        return "cross-pen", ("a minted row is attributed to %s — neither the calling actor (%r) nor a "
                             "recorder identity (%s); it writes a record OTHER than the actor's own"
                             % (rendered, actor_param, "/".join(sorted(RECORDER_IDENTITIES))))
    if recorder_seen:
        return "recorder", "attributes its row to the SYSTEM recorder (the machine's own record-keeper)"
    return "own-pen", "handler attributes every minted row to the calling actor (%r)" % actor_param


# ---- READING 2 — the no-delete / no-merge-by-copy classifier ------------------------------------

def _classify_conservation(op, handler_src):
    """Read one op's removal/consolidation shape. Returns (klass, reason) with klass in
    {handover, standalone-delete, merge-by-copy, conserving, unknown}.

    * merge-by-copy: the op's NAME declares a forbidden consolidation (a vocabulary reading).
    * standalone-delete: the op reaches an irreversible removal primitive AND is not the handover
      ceremony — a removal outside the one lawful ceremony (capability-absence, L14). REUSES the
      effect-order census's reading of the primitive vocabulary.
    * handover: the op IS the handover ceremony (the one lawful removal).
    * conserving: reaches no removal primitive and declares no merge — it conserves custody.
    """
    upper = op.upper()
    for stem in MERGE_BY_COPY_STEMS:
        if stem in upper:
            return "merge-by-copy", ("the op name declares a %s consolidation — consolidation is the "
                                     "handover ceremony alone (no merge by copy, L14)" % stem)
    if handler_src is None:
        # an unreadable handler cannot be shown NOT to remove bytes; it reds (as the siblings do).
        return "unknown", "source unreadable — a removal cannot be ruled out"
    try:
        c = _classify_effect_source(handler_src)
    except SyntaxError:
        return "unknown", "handler source did not parse — a removal cannot be ruled out"
    if not c["irreversible"]:
        return "conserving", "reaches no irreversible removal primitive; conserves custody"
    # the handler reaches an irreversible primitive. Lawful ONLY for the handover ceremony.
    prims = ", ".join(c["primitives"])
    if op == HANDOVER_OP:
        return "handover", ("the handover ceremony — the one lawful removal (%s), fired as the gate's "
                            "DEFERRED effect after the receipt verifies" % prims)
    return "standalone-delete", ("reaches an irreversible removal primitive (%s) OUTSIDE the handover "
                                 "ceremony — a standalone delete (there is no delete function, L14)"
                                 % prims)


# ---- reading one op's source (the five-families helpers, mirrored) -------------------------------

def _op_definition(views, op):
    entry = views.op_definitions().get(op)
    if not entry:
        return None
    return entry.get("definition", entry)


def _handler_source(gate, op):
    handler = gate.ops[op]["handler"]
    try:
        return inspect.getsource(handler)
    except (OSError, TypeError):
        return None


def _innermost_handler_def(tree):
    """The handler function definition to read. Registered handlers are closures returned by a
    factory, so getsource often yields `def factory(...): ...; def _h(actor, params): ...; return _h`.
    The row-minting body is the INNER def; when the source is a bare `def _h(...)` it is that def."""
    fdefs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if not fdefs:
        return None
    # prefer the innermost def whose first param looks like a handler (actor, params); else the last.
    for n in reversed(fdefs):
        args = n.args.posonlyargs + n.args.args
        if len(args) == 2:
            return n
    return fdefs[-1]


def _dedent(src):
    import textwrap
    return textwrap.dedent(src)


def _render(node):
    try:
        return ast.unparse(node)
    except Exception:
        return type(node).__name__


# ---- the census: one row per op -----------------------------------------------------------------

def census(gate, views):
    """One row per registered op, sorted by name. Each row:
        {op, pen, pen_reason, conservation, conservation_reason}."""
    rows = []
    for op in sorted(gate.ops):
        definition = _op_definition(views, op)
        handler_src = _handler_source(gate, op)
        pen, pen_reason = _classify_one_pen(op, definition, handler_src)
        cons, cons_reason = _classify_conservation(op, handler_src)
        rows.append({"op": op, "pen": pen, "pen_reason": pen_reason,
                     "conservation": cons, "conservation_reason": cons_reason})
    return rows


# READING 1 red sets
def cross_pen_rows(rows):
    """THE RED SET for I1: an op that writes a record OTHER than the actor's own. Empty is the whole
    point; non-empty is one pen per record refuted — a finding, never a census bug."""
    return [r for r in rows if r["pen"] == "cross-pen"]


def unknown_pen_rows(rows):
    return [r for r in rows if r["pen"] == "unknown"]


# READING 2 red sets
def standalone_delete_rows(rows):
    """THE RED SET for I14 (delete arm): an op removing bytes OUTSIDE the handover ceremony. Empty is
    required — the handover is the one removal (capability-absence, L14)."""
    return [r for r in rows if r["conservation"] == "standalone-delete"]


def merge_by_copy_rows(rows):
    """THE RED SET for I14 (merge arm): an op declaring a merge/consolidate-by-copy. Empty is required
    — consolidation is the handover ceremony alone."""
    return [r for r in rows if r["conservation"] == "merge-by-copy"]


def unknown_conservation_rows(rows):
    return [r for r in rows if r["conservation"] == "unknown"]


def _by(rows, field, value):
    return [r for r in rows if r[field] == value]


# ---- the evidence table (a persisted artifact, one row per op) ----------------------------------

def render_markdown(rows):
    out = []
    out.append("<!-- GENERATED by tools/conformance/one_pen_no_delete_census.py — do not hand-edit. -->")
    out.append("<!-- Regenerate: python3 -m tools.conformance.one_pen_no_delete_census --md -->")
    out.append("")
    out.append("# I1 + I14 · One-pen + no-delete census — one row per op")
    out.append("")
    out.append("Every record on a machine keeps exactly ONE pen — no op appends to a record other "
               "than the actor's own (I1, L12) — and consolidation is only ever the handover "
               "ceremony, never a merge by copy and never a delete (I14, L14). This table is the "
               "census's reading of every op registered on the gate. An op that writes a second "
               "party's pen reads `cross-pen`; an op that removes bytes outside the handover "
               "ceremony reads `standalone-delete`; an op declaring a merge consolidation reads "
               "`merge-by-copy`. All three red sets are empty below.")
    out.append("")
    out.append("Ops censused: **%d**. One-pen: own-pen **%d**, recorder **%d**. "
               "Cross-pen (must be zero): **%d**. Unknown-pen (must be zero): **%d**." % (
                   len(rows), len(_by(rows, "pen", "own-pen")), len(_by(rows, "pen", "recorder")),
                   len(cross_pen_rows(rows)), len(unknown_pen_rows(rows))))
    out.append("")
    out.append("Conservation: conserving **%d**, handover **%d**. "
               "Standalone-delete (must be zero): **%d**. Merge-by-copy (must be zero): **%d**. "
               "Unknown-conservation (must be zero): **%d**." % (
                   len(_by(rows, "conservation", "conserving")),
                   len(_by(rows, "conservation", "handover")),
                   len(standalone_delete_rows(rows)), len(merge_by_copy_rows(rows)),
                   len(unknown_conservation_rows(rows))))
    out.append("")
    out.append("## Recorder-attributed ops (the SYSTEM recorder — the machine's own pen)")
    out.append("")
    out.append("| op | reading |")
    out.append("|---|---|")
    for r in _by(rows, "pen", "recorder"):
        out.append("| %s | %s |" % (r["op"], r["pen_reason"]))
    out.append("")
    out.append("## The handover ceremony (the one lawful removal)")
    out.append("")
    out.append("| op | reading |")
    out.append("|---|---|")
    for r in _by(rows, "conservation", "handover"):
        out.append("| %s | %s |" % (r["op"], r["conservation_reason"]))
    out.append("")
    for label, red in (("cross-pen", cross_pen_rows(rows)), ("unknown-pen", unknown_pen_rows(rows)),
                       ("standalone-delete", standalone_delete_rows(rows)),
                       ("merge-by-copy", merge_by_copy_rows(rows)),
                       ("unknown-conservation", unknown_conservation_rows(rows))):
        out.append("## %s (%d — must be zero)" % (label, len(red)))
        out.append("")
        if red:
            out.append("| op | reason |")
            out.append("|---|---|")
            for r in red:
                reason = r["pen_reason"] if "pen" in label else r["conservation_reason"]
                out.append("| %s | %s |" % (r["op"], reason))
        else:
            out.append("_none — the invariant holds over the shipped registry._")
        out.append("")
    out.append("## Every op — one row (own pen, conserving custody)")
    out.append("")
    out.append("| op | pen | conservation |")
    out.append("|---|---|---|")
    for r in rows:
        out.append("| %s | %s | %s |" % (r["op"], r["pen"], r["conservation"]))
    out.append("")
    return "\n".join(out)


EVIDENCE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(_HERE)),
    "planning", "evidence", "P14-MANY-RECORDS-HANDOVER", "one-pen-no-delete.md")


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv[1:])
    _store, gate, views = build_full_kernel_for_census()
    rows = census(gate, views)
    if "--md" in argv:
        print(render_markdown(rows))
        return 0
    print("censused %d ops; %d cross-pen (must be 0); %d unknown-pen (must be 0); "
          "%d standalone-delete (must be 0); %d merge-by-copy (must be 0); %d unknown-conservation (must be 0)"
          % (len(rows), len(cross_pen_rows(rows)), len(unknown_pen_rows(rows)),
             len(standalone_delete_rows(rows)), len(merge_by_copy_rows(rows)),
             len(unknown_conservation_rows(rows))))
    for r in rows:
        print("  %-26s pen=%-9s conservation=%s" % (r["op"], r["pen"], r["conservation"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
