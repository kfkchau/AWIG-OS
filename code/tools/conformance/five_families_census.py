# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (path family, channel, socket/tunnel, shared memory, custody handover, sight, census).
# NON-GOAL: no offensive capability of any kind — this ENUMERATES every op in the registry and
# READS each as exactly ONE of the five path families or as not-a-path, the sibling of the
# effect-order census. It performs no effect, mints no input, drives no attack; it reads source and
# op definitions. Full declaration: SCOPE-STATEMENT.md.
"""P4 · I20 — THE FIVE-FAMILIES CENSUS (the enumerator + family classifier).

The owner's B19/L19/I20 (design/52): information moves by one of FIVE path families —
channels; sockets and tunnels; shared memory; custody handover; sight — and the invariant to
census is "NO SIXTH WAY". This is the sibling of the effect-order census: found once, now found
everywhere. It is an INSTRUMENT over the code (I20: "not a rule the record can check about
itself"), never a founding op or check kind.

WHAT IT CENSUSES
    Every op registered on the gate (`gate.ops` is the completeness guarantee — "the bank has no
    counter", P3). For each op it reads the op's OWN SOURCE — its definition (description, law
    cited, the parameter shape it declares) for a definition-born op, or its handler source for a
    code-registered op — and reads it as exactly one of:

        one of the FIVE FAMILIES  ·  not-a-path  ·  sixth-way (RED)  ·  unknown (RED)

    FAMILY is a POSITIVE reading of the op's declared conduit identity (its name and cited law),
    a CLOSED vocabulary held in ONE place (`_family`), the same discipline as the effect-order
    census's `IRREVERSIBLE_PRIMITIVES`. A new family is a paper change (L19: five families
    today), never a code convenience.

    NOT-A-PATH is also a POSITIVE reading, WITH ITS REASON RECORDED PER OP: the op moves no bytes
    across a boundary (it records a decision or a fact, or acts within one custody). It is NEVER
    the default an unreadable op falls to.

    UNKNOWN (REDS) is the op whose source cannot be read at all — no definition and no readable
    handler source. An unreadable op silently called not-a-path would let a real sixth way hide;
    so an unreadable op is `unknown` and it reds, exactly as the effect-order census reds on a
    handler whose source will not classify.

    SIXTH-WAY (REDS) is the load-bearing failure: an op that MOVES INFORMATION ACROSS A BOUNDARY
    (`_moves_information`) yet fits NONE of the five families. Over the shipped registry this set
    is EMPTY — that is I20 holding. A byte-moving op that fits no family is a FINDING for the
    paper (the five-families set is incomplete), never a census bug to paper over by widening a
    family silently.

WHY THE FAMILY READING AND THE MOVES-INFORMATION READING ARE INDEPENDENT
    The family reading assigns a conduit identity by NAME/LAW. The moves-information reading is a
    SEPARATE, GENERIC detector: does the op carry a content datum to a DISTINCT party (a
    definition-born op declaring `content_params` handed to a `target_param`) or call a real
    byte-transfer primitive (a code-registered op)? The two are independent ON PURPOSE: a byte
    mover the family reading does not recognise trips the generic detector and REDS as a sixth
    way. If the two shared a vocabulary, a new byte-moving primitive fitting no family could never
    surface — the census could not fail.

USAGE
    python3 -m tools.conformance.five_families_census          # print the classification table
    python3 -m tools.conformance.five_families_census --md     # emit the evidence markdown body
"""

import ast
import inspect
import os
import sys
import textwrap

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(os.path.dirname(os.path.dirname(_HERE)), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

# The census kernel is the effect-order census's own composed full kernel — the widest byte/world
# surface (sockets, devices, mounts, the handover ceremony). REUSED, never re-authored: the two
# censuses sit over the SAME registry by construction, so neither can drift from the other.
from tools.conformance.effect_order_census import build_full_kernel_for_census


# ---- the five path families: a CLOSED vocabulary, read in ONE place -------------------------
# design/52 B19 (68), I20 (92), L19 (117): "channels; sockets and tunnels; shared memory; custody
# handover; sight", the invariant "no sixth way". Each family is a POSITIVE reading of an op's
# DECLARED conduit identity — its name and, where it corroborates, its cited law. Extend this only
# by a filed ruling: a sixth entry here is a PAPER change (L19), not a code convenience, and it is
# named in ONE place, read by both the tool and its test.
FIVE_FAMILIES = (
    "channels",
    "sockets-and-tunnels",
    "shared-memory",
    "custody-handover",
    "sight",
)

# custody-handover members: the custody plane's byte-and-authority handovers, the cross-border
# submit/reply/refusal, and the receiver's receipt (design/51 N3/N9, design/46).
_CUSTODY_OPS = frozenset({
    "HANDOVER", "HANDOVER-CUSTODY", "FILE-CUSTODY-TRANSFER",
    "BORDER-SUBMIT", "BORDER-REPLY", "BORDER-REFUSAL", "RECEIPT",
})

# shared-memory members not caught by the MEM- stem: the share grant and the uid mapping.
_SHMEM_OPS = frozenset({"SHM-GRANT", "MAP-UID"})

# sight members: an op whose recorded act is a READER GAINING VIEW OF information — a served view,
# an aggregate of delivered reads, an opened sealed piece, a read into active context, a review.
# (GRANT-READ and CONSUME cite the sight law but RECORD a grant / a gated action — they serve no
# view to a reader, so they are not-a-path: moves-information reads False for them.)
_SIGHT_OPS = frozenset({
    "FILE-READ-AGGREGATE", "VIEW-SERVICE", "REVIEW", "READ", "OPEN-CONTENT",
})


def _family(op, law):
    """The POSITIVE family reading. Returns (family, reason) or (None, None). Reads the op's own
    declared identity — its name and cited law — against the closed vocabulary above."""
    if op.startswith("COMMS-"):
        return "channels", "COMMS-* channel op (%s): a message conduit between named endpoints" % law
    if op.startswith("SOCKET-"):
        return "sockets-and-tunnels", "SOCKET-* wire op (%s): a socket/tunnel conduit" % law
    if op.startswith("MEM-") or op in _SHMEM_OPS:
        return "shared-memory", "region/share/uid op (%s): a shared-memory conduit" % law
    if op in _CUSTODY_OPS:
        return "custody-handover", "custody/border/receipt op (%s): bytes or authority change custody" % law
    if op in _SIGHT_OPS:
        return "sight", "sight op (%s): a reader gains view of information" % law
    return None, None


# ---- the moves-information detector: GENERIC, independent of the family reading --------------
# A closed set of byte-transfer PRIMITIVES a code-registered handler calls to hand content to
# another party. Named in ONE place (as the effect-order census names IRREVERSIBLE_PRIMITIVES);
# a new transfer primitive that no entry names is exactly what the sixth-way class must catch.
BYTE_TRANSFER_PRIMITIVES = frozenset({
    "hand_off",   # blobs.hand_off — transfer custody of bytes to a receiver (design/46)
    "sendall",    # a real wire send of bytes to a peer
})


class _TransferFinder(ast.NodeVisitor):
    """Walk a handler's AST; note any call to a byte-transfer primitive."""

    def __init__(self):
        self.hit = False

    def visit_Call(self, node):
        fn = node.func
        name = fn.attr if isinstance(fn, ast.Attribute) else (fn.id if isinstance(fn, ast.Name) else None)
        if name in BYTE_TRANSFER_PRIMITIVES:
            self.hit = True
        self.generic_visit(node)


def _moves_information(definition, handler_src):
    """POSITIVE, GENERIC reading: does this op carry a content datum ACROSS A BOUNDARY to a
    distinct party? Returns (bool, reason).

      definition-born: it declares `content_params` (a content datum) handed to a `target_param`
        (a second, distinct endpoint). Content alone is not a crossing — FILE-WRITE carries
        content into the actor's OWN custody and declares no target, so it moves nothing across a
        boundary. A distinct endpoint alone is not a crossing either — FILE-LINK names a target
        path but carries no content datum to it.
      code-registered: its handler calls a byte-transfer primitive (BYTE_TRANSFER_PRIMITIVES).
    """
    if definition:
        if definition.get("content_params") and definition.get("target_param"):
            return True, "content_params carried to a distinct target_param (a boundary crossing)"
    if handler_src:
        try:
            tree = ast.parse(textwrap.dedent(handler_src))
        except SyntaxError:
            tree = None
        if tree is not None:
            finder = _TransferFinder()
            finder.visit(tree)
            if finder.hit:
                return True, "handler calls a byte-transfer primitive (%s)" % "/".join(sorted(BYTE_TRANSFER_PRIMITIVES))
    return False, ""


# ---- reading one op's source ----------------------------------------------------------------

def _op_definition(views, op):
    """The op's definition dict (definition-born ops), or None (code-registered ops).
    `op_definitions()` is definition-born only, so a code-registered op returns None here and is
    read through its handler source instead."""
    entry = views.op_definitions().get(op)
    if not entry:
        return None
    return entry.get("definition", entry)


def _handler_source(gate, op):
    """The op's handler source, or None if it cannot be read (builtins/C, or an unreadable
    closure). For a definition-born op this is the shared generic interpreter; the FAMILY and
    MOVES-INFORMATION readings for such ops come from the DEFINITION, not this shared body."""
    handler = gate.ops[op]["handler"]
    try:
        return inspect.getsource(handler)
    except (OSError, TypeError):
        return None


def classify(op, definition, handler_src, law):
    """Read one op and return {op, class, reason}. `class` is one of the five families, or
    'not-a-path', or 'sixth-way', or 'unknown'."""
    # UNKNOWN first: an op with no readable source of ANY kind cannot be classified, and calling
    # it not-a-path would let an unreadable byte-mover hide (precision 2). It REDS.
    if definition is None and handler_src is None:
        return {"op": op, "class": "unknown", "reason": "source unreadable: no definition and no handler source"}
    fam, freason = _family(op, law)
    if fam is not None:
        return {"op": op, "class": fam, "reason": freason}
    moves, mreason = _moves_information(definition, handler_src)
    if moves:
        # a byte mover fitting no family — a SIXTH WAY. It reds. (A real one is a paper finding,
        # not a census bug: see STOP condition (b) in the plan.)
        return {"op": op, "class": "sixth-way", "reason": "moves information across a boundary but fits no family: " + mreason}
    # NOT-A-PATH, positively: it fits no family AND moves no bytes across a boundary.
    return {"op": op, "class": "not-a-path",
            "reason": "records a decision/fact under %s; moves no content across a boundary (moves-information reads False)" % (law or "no cited law")}


# ---- enumerate + classify the live registry --------------------------------------------------

def census(gate, views):
    """The census: one row per registered op, sorted by name.
    Each row: {op, class, reason}."""
    rows = []
    for op in sorted(gate.ops):
        definition = _op_definition(views, op)
        handler_src = _handler_source(gate, op)
        law = (definition or {}).get("law_cited") if definition else (gate.ops[op].get("meta") or {}).get("law_cited")
        rows.append(classify(op, definition, handler_src, law))
    return rows


def family_rows(rows, family):
    return [r for r in rows if r["class"] == family]


def sixth_way_rows(rows):
    """THE RED SET: an op that moves information across a boundary yet fits no family. Empty over
    the shipped registry is the whole point; non-empty is a sixth way — I20 refuted, a finding."""
    return [r for r in rows if r["class"] == "sixth-way"]


def unknown_rows(rows):
    """THE OTHER RED SET: an op whose source could not be read at all. Empty is required; a
    non-empty set is an unreadable op that could hide a byte-move (precision 2)."""
    return [r for r in rows if r["class"] == "unknown"]


def not_a_path_rows(rows):
    return [r for r in rows if r["class"] == "not-a-path"]


# ---- the evidence table (one row per op, a persisted artifact) -------------------------------

def render_markdown(rows):
    out = []
    out.append("<!-- GENERATED by tools/conformance/five_families_census.py — do not hand-edit. -->")
    out.append("<!-- Regenerate: python3 -m tools.conformance.five_families_census --md -->")
    out.append("")
    out.append("# I20 · Five-families census — one row per op, no sixth way")
    out.append("")
    out.append("Every way information moves is one of FIVE path families (design/52 B19/L19): "
               "channels; sockets and tunnels; shared memory; custody handover; sight. This table "
               "is the census's reading of every op registered on the gate. An op that moves "
               "information across a boundary yet fits no family would read as `sixth-way` and RED "
               "the census (I20 refuted); an op whose source cannot be read would read as "
               "`unknown` and RED it. Both sets are empty below.")
    out.append("")
    counts = {f: len(family_rows(rows, f)) for f in FIVE_FAMILIES}
    out.append("Ops censused: **%d**. By family: %s. Not-a-path: **%d**. "
               "Sixth-way (must be zero): **%d**. Unknown (must be zero): **%d**." % (
                   len(rows),
                   ", ".join("%s **%d**" % (f, counts[f]) for f in FIVE_FAMILIES),
                   len(not_a_path_rows(rows)),
                   len(sixth_way_rows(rows)),
                   len(unknown_rows(rows)),
               ))
    out.append("")
    for family in FIVE_FAMILIES:
        fr = family_rows(rows, family)
        out.append("## %s (%d)" % (family, len(fr)))
        out.append("")
        out.append("| op | reading |")
        out.append("|---|---|")
        for r in fr:
            out.append("| %s | %s |" % (r["op"], r["reason"]))
        out.append("")
    out.append("## not-a-path (%d)" % len(not_a_path_rows(rows)))
    out.append("")
    out.append("Read positively: each op below fits no family AND moves no content across a "
               "boundary. The reason states what it does instead.")
    out.append("")
    out.append("| op | reason |")
    out.append("|---|---|")
    for r in not_a_path_rows(rows):
        out.append("| %s | %s |" % (r["op"], r["reason"]))
    out.append("")
    out.append("## sixth-way (%d — must be zero)" % len(sixth_way_rows(rows)))
    out.append("")
    sw = sixth_way_rows(rows)
    if sw:
        out.append("| op | reason |")
        out.append("|---|---|")
        for r in sw:
            out.append("| %s | %s |" % (r["op"], r["reason"]))
    else:
        out.append("_none — I20 holds over the shipped registry._")
    out.append("")
    out.append("## unknown (%d — must be zero)" % len(unknown_rows(rows)))
    out.append("")
    uk = unknown_rows(rows)
    if uk:
        out.append("| op | reason |")
        out.append("|---|---|")
        for r in uk:
            out.append("| %s | %s |" % (r["op"], r["reason"]))
    else:
        out.append("_none — every op's source was read._")
    out.append("")
    return "\n".join(out)


EVIDENCE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(_HERE)),
    "planning", "evidence", "P4-FIVE-FAMILIES-CENSUS", "five-families.md")


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv[1:])
    _store, gate, views = build_full_kernel_for_census()
    rows = census(gate, views)
    if "--md" in argv:
        print(render_markdown(rows))
        return 0
    print("censused %d ops; %d sixth-way (must be 0); %d unknown (must be 0)" % (
        len(rows), len(sixth_way_rows(rows)), len(unknown_rows(rows))))
    for family in FIVE_FAMILIES:
        print("  %-20s %s" % (family, ", ".join(r["op"] for r in family_rows(rows, family))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
