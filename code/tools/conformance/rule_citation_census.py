# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (cited rule, local resolution, received row, active constitution view, cache-kill
# recompute, census). NON-GOAL: no offensive capability of any kind — this READS a child's own
# record and confirms every cited rule resolves inside that record, and that the served
# constitution recomputes from the child's received+adopted rows alone. It performs no effect,
# mints no input, drives no attack; it reads a store and P10's derived views. Full declaration:
# SCOPE-STATEMENT.md.
"""C6 P9 · I6 — THE RULE-CITATION-LOCALITY CENSUS (the two-reading record census).

design/52 I6: CITED RULES ARE ALWAYS LOCAL. Check, its two halves:
    (1) every rule_cited in the child resolves inside the child's OWN record — no rule_cited
        resolves only to a foreign (parent) record;
    (2) the active constitution recomputed from the child's received+adopted rows ALONE equals the
        SERVED constitution (the cache-kill form) — no served rule lacks a received+adopted origin,
        and no received+adopted rule is absent from the served view.

A STANDING census, the P4b/one-pen/five-families sibling: found once, now found everywhere. It is an
INSTRUMENT over a child's RECORD (a store + P10's derived views), never a founding op or check kind,
and it lives in tools/ (NOT an attested member — no ATTESTED_MEMBERS rider fires; the census is a
tool, not a kernel engine module). P10's border machinery (received_parent_rules, adoptions,
active_constitution) is READ and REUSED — this census re-authors none of it, so it cannot drift from
the view it censuses.

TWO INDEPENDENT READINGS, the five-families discipline (two readings that cannot be made to share a
vocabulary, so neither can hide the other's failure):

READING 1 — EVERY rule_cited RESOLVES LOCALLY (I6 half 1). For every record carrying a rule_cited,
    the cited rule resolves inside the child's own record iff:
      * it is a LOCAL RULE ID — a member of the child's live constitution (views.active_rules: every
        founding, native and ADOPTED rule the child holds; an adoption lands here under its own
        rule_id), OR
      * it is a LOCAL RECEIVED-COPY HASH — the content hash of a parent rule the child holds as a
        RECEIVED ROW (border.received_parent_rules; B4's citation-by-the-local-copy form, "sha256:…").
    FOREIGN (RED): a rule_cited that resolves to NEITHER — a rule only a parent's record holds, cited
    without the child's own local copy. Over a real child record this set is EMPTY (I6 holds). A
    planted record whose rule_cited names a foreign rule fires it (the check that can fail).

READING 2 — RECOMPUTE-FROM-RECEIVED+ADOPTED == SERVED (I6 half 2, the cache-kill). The active
    constitution is a computed VIEW (border.active_constitution) — a received parent rule is IN it
    IFF a child adoption act cites it by hash. This reading recomputes that intersection from the raw
    received + adopted rows INDEPENDENTLY and compares it to the SERVED view:
      * SERVED-WITHOUT-ORIGIN (RED): a rule_hash in the served constitution that is NOT (received AND
        adopted) — a served rule with no received+adopted origin (a phantom the fold would never
        mint).
      * RECOMPUTED-ABSENT-FROM-SERVED (RED): a received+adopted rule_hash absent from the served view.
    Both empty over a real store (the served view IS the intersection). A planted divergence in either
    direction fires it (the check that can fail).

CAP (the sibling censuses' honesty standard). READING 1 reads the record's OWN rule_cited scalars and
resolves them against the child's live constitution and received rows; it does not prove a foreign
record does or does not also hold a same-named rule — locality is "resolves HERE", the property I6
states. READING 2 compares the SERVED view to an INDEPENDENT recompute from the same rows; it proves
the served view carries no phantom and omits no adopted rule, the cache-kill property. The two red
sets are empty over a real child record; the able-to-fail controls (a planted foreign citation, a
planted divergence) show each reading CAN red.

USAGE
    python3 -m tools.conformance.rule_citation_census          # census a demonstrative child, print
    python3 -m tools.conformance.rule_citation_census --md     # emit the evidence markdown body
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(os.path.dirname(os.path.dirname(_HERE)), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from kernel import border                              # noqa: E402  (received_parent_rules, adoptions, active_constitution — READ, never re-authored)


# ---- the local-rule universe: what a rule_cited may resolve TO, inside the child's own record ----

def local_rule_ids(views, as_of=None):
    """THE CHILD'S LIVE CONSTITUTION as a set of rule ids — every founding, native and ADOPTED rule
    the child holds (views.active_rules; an adoption act is a CREATE-RULE landing under its own
    rule_id, so adopted parent rules are here). A rule_cited naming one of these resolves LOCALLY."""
    return set(views.active_rules(as_of).keys())


def local_received_hashes(store, as_of=None):
    """THE CHILD'S LOCAL RECEIVED COPIES as a set of content hashes — every parent rule the child
    holds as a received row (border.received_parent_rules, keyed by the rule's content hash). A
    rule_cited that is a CITATION BY HASH (B4's local-copy form) resolves LOCALLY iff its hash is
    here — the child cites its OWN copy, never the parent's record."""
    return set(border.received_parent_rules(store, as_of).keys())


# ---- READING 1 — every rule_cited resolves locally (a pure predicate, able to fail) --------------

def foreign_citations(records, rule_ids, received_hashes):
    """THE RED SET for I6 half 1: every record whose `rule_cited` resolves to NEITHER a local rule id
    NOR a local received-copy hash — a cited rule only a foreign record holds. A PURE predicate over
    an iterable of records plus the child's local universe (rule_ids, received_hashes), so it can be
    handed a planted foreign citation and MUST fire (the five-families able-to-fail discipline).
    Records with no rule_cited are skipped (nothing is cited). Returns a list of
    {seq, action, rule_cited}."""
    out = []
    for e in records:
        cited = e.get("rule_cited")
        if cited is None:
            continue
        if cited in rule_ids or cited in received_hashes:
            continue                                    # resolves locally
        out.append({"seq": e.get("seq"), "action": e.get("action"), "rule_cited": cited})
    return out


# ---- READING 2 — recompute-from-received+adopted == served (a pure predicate, able to fail) ------

def recompute_divergences(served, received, adopted):
    """THE RED SETS for I6 half 2 (the cache-kill): compare the SERVED active constitution to an
    INDEPENDENT recompute from the raw received + adopted rows. A PURE predicate over three inputs
    (served/received/adopted, each a dict keyed by rule hash), so a planted divergence in either
    direction can be handed in and MUST fire. Returns
    {served_without_origin, recomputed_absent_from_served}, each a sorted list of rule hashes.

      * served_without_origin       — a served rule with NO received+adopted origin (a phantom).
      * recomputed_absent_from_served — a received+adopted rule ABSENT from the served view.
    Both empty => the served view is exactly the received∩adopted intersection (I6 half 2 holds)."""
    recompute = {h for h in received if h in adopted}
    served_hashes = set(served)
    return {"served_without_origin": sorted(served_hashes - recompute),
            "recomputed_absent_from_served": sorted(recompute - served_hashes)}


# ---- the census over a real child record ---------------------------------------------------------

def census(store, views, as_of=None):
    """Run both readings over a real child record. Returns
        {records, foreign, divergences, rule_ids, received_hashes, served, counts}
    with the red sets EMPTY over a well-formed child record."""
    records = store.all(as_of)
    rule_ids = local_rule_ids(views, as_of)
    received = border.received_parent_rules(store, as_of)
    adopted = border.adoptions(store, as_of)
    served = border.active_constitution(store, as_of)
    foreign = foreign_citations(records, rule_ids, set(received.keys()))
    divergences = recompute_divergences(served, received, adopted)
    counts = {
        "records": len(records),
        "cited": sum(1 for e in records if e.get("rule_cited") is not None),
        "local_rule_ids": len(rule_ids),
        "received": len(received),
        "adopted": len(adopted),
        "served": len(served),
        "foreign": len(foreign),
        "served_without_origin": len(divergences["served_without_origin"]),
        "recomputed_absent_from_served": len(divergences["recomputed_absent_from_served"]),
    }
    return {"records": records, "foreign": foreign, "divergences": divergences,
            "rule_ids": rule_ids, "received_hashes": set(received.keys()), "served": served,
            "counts": counts}


def is_green(result):
    """The census is GREEN iff all three red sets are empty (I6 holds over this record)."""
    c = result["counts"]
    return c["foreign"] == 0 and c["served_without_origin"] == 0 and c["recomputed_absent_from_served"] == 0


# ---- a demonstrative child record (the CLI subject: a real received+adopted path) ----------------

def _demo_child():
    """Build a child body that RECEIVES and ADOPTS one parent rule and receives another it does not
    adopt — a real record exercising both readings. Reuses P10's border machinery (receive/adopt) and
    the modelled parent countersign; the census reads the result, it does not re-author the path."""
    import tempfile
    from kernel.compose import build_full_kernel
    from kernel import keys
    d = tempfile.mkdtemp(prefix="p9-rule-citation-census-")
    store, gate, views, _blobs, _subs = build_full_kernel(
        os.path.join(d, "record.jsonl"), os.path.join(d, "blobs"), os.path.join(d, "vault"))
    gate.execute("CREATE-ACCOUNT", "owner", {"account_id": "child", "actor_class": "ai"})
    parent_key = "ed25519-pub:parent"
    parent_name = border.from_body_name(parent_key, "sha256:" + "beef" * 16)
    declare = border.submit(gate, "child", {"handshake_relation": {"parent": parent_name}}, actor="child")
    rid = border.content_id(declare)
    adopted_rule = {"actor": "parent", "action": "CREATE-RULE", "object": "PARENT-SPEND", "target": None,
                    "payload": {"rule_id": "PARENT-SPEND", "scope": "spend", "policy_key": "govern",
                                "value": "the-rule-body"}, "seq": 1000, "record_time": "2026-09-10T00:00:00Z"}
    unadopted_rule = {"actor": "parent", "action": "CREATE-RULE", "object": "PARENT-TRADE", "target": None,
                      "payload": {"rule_id": "PARENT-TRADE", "scope": "trade", "policy_key": "govern",
                                  "value": "the-rule-body"}, "seq": 1001, "record_time": "2026-09-10T00:00:00Z"}
    border.receive_parent_rule(gate, views, rid, adopted_rule, keys.countersign(adopted_rule, parent_key))
    border.receive_parent_rule(gate, views, rid, unadopted_rule, keys.countersign(unadopted_rule, parent_key))
    border.adopt_received_rule(gate, border.content_id(adopted_rule), "child-obeys-spend", scope="spend")
    return store, views


# ---- the evidence table (a persisted artifact) ---------------------------------------------------

def render_markdown(result):
    c = result["counts"]
    out = []
    out.append("<!-- GENERATED by tools/conformance/rule_citation_census.py — do not hand-edit. -->")
    out.append("<!-- Regenerate: python3 -m tools.conformance.rule_citation_census --md -->")
    out.append("")
    out.append("# I6 · Rule-citation-locality census — a child's own record")
    out.append("")
    out.append("Every rule a child obeys is cited inside the child's OWN record (design/52 I6): every "
               "`rule_cited` resolves to a local rule id (its live constitution) or a local received "
               "copy (a parent rule the child holds as a received row, cited by hash — B4), and the "
               "served active constitution recomputes from the child's received+adopted rows alone "
               "(the cache-kill form). This census reads a demonstrative child that received two "
               "parent rules and adopted one. All three red sets are empty below.")
    out.append("")
    out.append("Records: **%d** (cited **%d**). Local rule ids: **%d**. Received rows: **%d**, "
               "adopted: **%d**, served: **%d**." % (
                   c["records"], c["cited"], c["local_rule_ids"], c["received"], c["adopted"],
                   c["served"]))
    out.append("")
    out.append("READING 1 — foreign citations (must be zero): **%d**." % c["foreign"])
    out.append("READING 2 — served-without-origin (must be zero): **%d**; "
               "recomputed-absent-from-served (must be zero): **%d**." % (
                   c["served_without_origin"], c["recomputed_absent_from_served"]))
    out.append("")
    out.append("## Foreign citations (%d — must be zero)" % c["foreign"])
    out.append("")
    if result["foreign"]:
        out.append("| seq | action | rule_cited |")
        out.append("|---|---|---|")
        for r in result["foreign"]:
            out.append("| %s | %s | %s |" % (r["seq"], r["action"], r["rule_cited"]))
    else:
        out.append("_none — every rule_cited resolves inside the child's own record._")
    out.append("")
    out.append("## Recompute divergences (must be zero both directions)")
    out.append("")
    d = result["divergences"]
    out.append("* served-without-origin: %s" % (d["served_without_origin"] or "_none_"))
    out.append("* recomputed-absent-from-served: %s" % (d["recomputed_absent_from_served"] or "_none_"))
    out.append("")
    out.append("## Served active constitution (received+adopted rules in force)")
    out.append("")
    out.append("| rule hash | rule id | scope | mode |")
    out.append("|---|---|---|---|")
    for h, v in result["served"].items():
        out.append("| %s | %s | %s | %s |" % (h[:19] + "…", v.get("adopted_by"), v.get("scope"),
                                              v.get("mode")))
    out.append("")
    return "\n".join(out)


EVIDENCE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(_HERE)),
    "planning", "evidence", "P9-RULE-CITATION", "rule-citation-locality.md")


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv[1:])
    store, views = _demo_child()
    result = census(store, views)
    c = result["counts"]
    if "--md" in argv:
        print(render_markdown(result))
        return 0
    print("censused %d records (%d cited); foreign %d (must be 0); "
          "served-without-origin %d (must be 0); recomputed-absent %d (must be 0); green=%s"
          % (c["records"], c["cited"], c["foreign"], c["served_without_origin"],
             c["recomputed_absent_from_served"], is_green(result)))
    print("  local rule ids %d; received %d; adopted %d; served %d"
          % (c["local_rule_ids"], c["received"], c["adopted"], c["served"]))
    return 0 if is_green(result) else 1


if __name__ == "__main__":
    sys.exit(main())
