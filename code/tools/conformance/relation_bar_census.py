"""C6a VT-2b — THE RELATION-BAR CENSUS: every relation-minting op passes the chokepoint bar, and
no relation row ever reaches the record past it. ABLE TO FAIL.

Named in planning/exec/VT-2b-ACTOR-TREE-BAR-CHOKEPOINT-BUILD.md (A3) before code; the enumeration
that proves the no-orphan / no-loop bar sits at the WRITE CHOKEPOINT (gate._relation_tree_step) and
that a PASS-THROUGH — a relation row minted past the bar, the cap VT-2 named — is a CAUGHT condition
rather than a silent bypass.

Two readings, one census:

  READING 1 — THE OPS THAT CAN MINT A CONTAINMENT RELATION ROW, EACH SUBJECT TO THE BAR. A relation
  row is a CONTAINMENT (NS/EM) edge with both ends established actors (design/25 v2.1 ruling 23). An
  op is "relation-minting" iff its DEFINITION declares the containment shape — `geometry` a
  structural param AND `subject` + `object` among its params. Every such op is subject to the bar by
  construction: the bar is `gate._relation_tree_step`, an UNCONDITIONAL step in the sole decide path
  (`gate._decide`), keyed on the DERIVED ROW, so any op whose write converges there — every
  registered op — passes under it. Today CREATE-RELATIONSHIP is the only relation-minting op.

  READING 2 — THE RED SET: RELATION ROWS ON THE RECORD PAST THE BAR (able to fail). Every STORED row
  that is a containment relation by SHAPE (payload.geometry in {NS,EM}, both ends established),
  REGARDLESS of the op that minted it, whose group `object` does NOT ground (an orphan, or a loop —
  a cycle never reaches the root, so the grounding fold excludes it). EMPTY on any world the
  chokepoint bar guarded: every orphan / loop was refused at the write, so no ungrounded containment
  row is on the record. NON-EMPTY is a PASS-THROUGH refuted — an op minted a relation row past the
  bar (a handler that appended directly, an external executor). The check CAN FAIL: plant a direct
  `store._append` of an ungrounded containment row (bypassing the decide chain) and this reading
  fires. That is the load-bearing control — a census that cannot fail is the signature defect this
  estate names (STOP condition d).

The census is keyed on the ROW's own geometry + ends, exactly as the chokepoint bar is: it reads the
same derived shape the bar reads, so what the bar lets through and what the census counts as clean
are one definition, never two that could drift.
"""

import argparse
import os
import sys
from collections.abc import Mapping

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from kernel import authority  # noqa: E402


# ---- READING 1: the relation-minting ops, each subject to the chokepoint bar ------------------

def _is_relation_minting(definition):
    """Does an op DEFINITION declare the containment-relation shape? `geometry` structural AND
    `subject` + `object` among its params — the derived row the chokepoint bar keys on. A native
    (boot) op with no definition is reported separately (its handler may mint any shape; the record
    reading is the general net for those)."""
    if not isinstance(definition, Mapping):        # op_definitions yields a mappingproxy, not a dict
        return False
    params = set((definition.get("params") or {}).keys())
    structural = set(definition.get("structural_params") or [])
    return "geometry" in structural and {"subject", "object"} <= params


def relation_minting_ops(gate, views):
    """READING 1 — one row per REGISTERED op that can mint a containment relation row, sorted by
    name. Each: {op, subject_to_bar, why}. `subject_to_bar` is True for every registered op: the bar
    is an unconditional decide step keyed on the derived row, so any op whose write converges at
    `gate._decide` passes under it. The list is the enumeration A3 asks for; today it is
    CREATE-RELATIONSHIP alone."""
    defs = views.op_definitions()
    rows = []
    for op in sorted(gate.ops):
        definition = (defs.get(op) or {}).get("definition") if defs.get(op) else None
        if _is_relation_minting(definition):
            rows.append({"op": op, "subject_to_bar": True,
                         "why": "declares geometry structural + subject/object params; its write "
                                "converges at gate._decide, under gate._relation_tree_step"})
    return rows


# ---- READING 2: the red set — relation rows on the record past the bar (able to fail) ---------

def containment_relation_rows(store, as_of=None):
    """Every STORED row that is a containment relation BY SHAPE — payload.geometry in {NS,EM} and
    BOTH ends established actors — regardless of the action that minted it (the chokepoint bar is
    keyed on the row's own geometry + ends, so the census must be too). Refusal rows carry the
    refused draft NESTED under payload.draft, so their top-level payload has no geometry and they are
    excluded; the explicit `refused` skip is belt-and-braces. Returns dicts {seq, action, subject,
    object}."""
    rows = []
    for e in store.all(as_of):
        if e.get("refused"):
            continue
        p = e.get("payload") or {}
        if p.get("geometry") not in authority.CONTAINMENT_GEOMETRIES:
            continue
        subj, obj = p.get("subject"), p.get("object")
        if authority.is_established(store, subj, as_of) and authority.is_established(store, obj, as_of):
            rows.append({"seq": e.get("seq"), "action": e.get("action"),
                         "subject": subj, "object": obj})
    return rows


def rows_past_the_bar(store, views, as_of=None):
    """THE RED SET (able to fail): every containment relation row ON THE RECORD whose group `object`
    does NOT ground — an orphan reached the write, or a loop (a cycle never reaches the root, so the
    grounding least-fixpoint excludes it). EMPTY when the chokepoint bar caught them all; non-empty
    is a PASS-THROUGH refuted, a finding — never a census bug. Each red row carries `why: orphan`
    (the group does not reach the constitution's root group). Plant a direct `store._append` of an
    ungrounded containment row and this fires — the control that proves the census can red."""
    red = []
    for row in containment_relation_rows(store, as_of):
        if not views.actor_grounded(row["object"], as_of):
            red.append({**row, "why": "orphan"})
    return red


# ---- CLI ---------------------------------------------------------------------------------------

def render_markdown(minting, red):
    out = ["# relation-bar census (C6a VT-2b)", ""]
    out.append("## reading 1 — relation-minting ops, each subject to the chokepoint bar")
    if minting:
        for r in minting:
            out.append(f"- `{r['op']}` — subject_to_bar={r['subject_to_bar']} ({r['why']})")
    else:
        out.append("- (none declare the containment-relation shape)")
    out.append("")
    out.append("## reading 2 — RED SET: relation rows on the record past the bar (empty is required)")
    if red:
        for r in red:
            out.append(f"- seq {r['seq']} `{r['action']}` {r['subject']} in {r['object']} — {r['why']}")
    else:
        out.append("- EMPTY — no ungrounded containment relation row on the record (the bar held)")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="C6a VT-2b relation-bar census")
    ap.add_argument("record", help="path to a record.jsonl to census")
    args = ap.parse_args(argv)
    from kernel.boot import build_kernel
    store, gate, views = build_kernel(args.record)
    minting = relation_minting_ops(gate, views)
    red = rows_past_the_bar(store, views)
    print(render_markdown(minting, red))
    return 1 if red else 0


if __name__ == "__main__":
    sys.exit(main())
