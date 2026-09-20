# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (cell, declared structure, identity replay, judgment count, census). NON-GOAL: no
# offensive capability of any kind — this ENUMERATES every op in the registry and READS each op's
# DECLARED cell (S | U | U{s} | S{u}) as founding data, confirms a declared-S op replays to
# identity, and DERIVES a constitution's judgment count from declared enforcement. It performs no
# effect, mints no input, drives no attack; it reads source, op definitions, and a read-only
# sibling pack. Full declaration: SCOPE-STATEMENT.md.
"""P4b · L28 — THE CELL CENSUS (L28 as an instrument; the fifth sibling census).

The owner's L28 (design/52): every operation (and station) declares its CELL — one of a CLOSED set
of four — S (structured both sides), U (judgment both sides), U{s} (judgment over structured input),
S{u} (structured over judgment input). The cell is FOUNDING DATA declared per operation (P8), NEVER
derived from field shapes: a text field carries a name as easily as a judgment, so a shape can never
tell S from U. This instrument is the sibling of the five-families census: found once (in P8's
founding door and the pairing machinery), now found everywhere, evidence-pinned, with controls that
can red.

WHAT IT CENSUSES  (over the WHOLE composed kernel — the same registry the five-families census reads)

  A1  COMPLETENESS — every op the founding CELL LAW binds carries a DECLARED cell.
        Two populations, kept distinct and both named:
          declared ops  — the founding-declared (definition-born) operations. The cell law (L28,
                          P8) binds these: each declares a cell in the closed set, or its
                          declaration is a FINDING (a missing/ill-formed cell is never defaulted
                          to S — a silent default is a program holding judgment, which L28 forbids).
          system ops    — code-registered kernel/bootstrap primitives (no definition record). These
                          are the recorder's OWN mechanics (archi precision 3, P8 :3688; install.py
                          "a runtime extension op is not the pack the law binds"): OUTSIDE the
                          founding cell law. Reported BY NAME, never a finding, never guessed.
        Completeness = enumeration (P3, "the bank has no counter"): one row per registered op.

  A2  A DECLARED-S OP REPLAYS TO IDENTITY (else a finding). The estate's founding property is that
        a record is a pure function of its inputs (kill the registry, replay, identical —
        test_ep14). A declared-S op is taken to replay unless its OWN definition honestly flags
        `replays_to_identity: false`; such an op is `declared S but actually U` — a FINDING, not a
        silent program holding judgment. A declared-JUDGMENT op is validated to its schema and NEVER
        scored by the machine (L28, "store the score, never the verdict"). The read-side guard is
        the estate's own (kernel.views.op_replays_to_identity / declared_s_findings), reused here.

  A3  TWO JUDGMENT COUNTS, EACH WITH ITS WORLD, AND THEY DO NOT SHARE A SOURCE — the finding
        (archi :3711) this delta answers. A constitution's judgment count is over its RULES; a
        rule's cell follows its ENFORCEMENT: a rule enforced by a check row of a CLOSED kind is
        S-enforced (every check kind is a mechanic by construction); a rule carrying NO such check
        is judgment-enforced (its enforcement is a judgment or a gate).

        A3-OUTSIDE — the OUTSIDE constitution's count (apps/pwc-app, read-only, the pack P5
        supplies), labelled honestly INFERRED-from-shape. This figure reads the derived pack's
        `enforced_by`, which `test_ep51.derive_twc_pack` SETS from `_needs_kinds(blob)` — the
        CANDIDATE_KINDS shape regexes (test_ep51:139-145). So this count and the "lexical" count
        are ONE count read twice: their MATCH is a tautology, not an independent agreement, and
        the earlier claim that "markers were retired" was false as built. It is retained because it
        is the only OUTSIDE reading available today: pwc rules declare no cell and carry no check
        rows (the R31 batch founds no checks — CREATE-ACCOUNT/CREATE-ROLE/CREATE-SPACE/GRANT only),
        so a TRUE declared-cell or enforcement count for the OUTSIDE constitution is not possible
        here — it is owed to the TWC/P9 line, not this delta. Published WITH ITS WORLD (the pwc
        law-book hash, the R31 batch hash, the row count, the TWC version) and labelled inferred.

        A3-GOV-OS — THIS constitution's own count, GENUINELY DERIVED FROM ENFORCEMENT. gov-os's own
        active law rules DO carry real check rows: an op's `checks` row names a `check` in the
        CLOSED OP_CHECKS vocabulary and a `cite` naming the rule it enforces. A gov-os rule cited by
        such a closed-kind check row is S-enforced; a rule with no such check row is
        judgment-enforced-or-deferred. This reads the op check rows (kernel.opdefs.OP_CHECKS +
        op_definitions), NEVER the shape regexes — the two counts are INDEPENDENT by construction,
        which is the independence the finding named as missing. Published beside the OUTSIDE figure,
        with its own world (founding version, closed-kind vocabulary size, rule population).

USAGE
    python3 -m tools.conformance.cell_census          # print the cell table + the derived counts
    python3 -m tools.conformance.cell_census --md     # emit the evidence markdown body
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(os.path.dirname(_HERE))
_SRC = os.path.join(_REPO, "src")
_TESTS = os.path.join(_REPO, "tests")
for _p in (_SRC, _REPO, _TESTS):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# The census kernel is the effect-order census's own composed full kernel — REUSED, never
# re-authored: the cell census and the five-families census sit over the SAME registry by
# construction, so neither can drift from the other.
from tools.conformance.effect_order_census import build_full_kernel_for_census

# The closed cell set (L28) is named in ONE place — the op-META door's own constant. READ, never
# re-declared (a second copy is a second law). A cell outside this set is ill-formed.
from kernel.opdefs import CELL, CELL_SET, OP_CHECKS

# The three judgment cells: a cell with ANY U on either side. A pure-S cell is the only structured
# one. Derived from the closed set, not a second list to keep in step.
JUDGMENT_CELLS = tuple(c for c in CELL_SET if "U" in c)


# ---- reading one op's declared cell ---------------------------------------------------------

def cell_of(definition):
    """The op's DECLARED cell (founding data), or None. READ off the declaration — NEVER inferred
    from field shapes (L28). A definition-born op declares its cell in its META; None means the
    declaration is absent or ill-formed."""
    if not definition:
        return None
    cell = definition.get(CELL)
    return cell if cell in CELL_SET else None


def classify_cell(op, definition, is_definition_born, replays):
    """Read one op and return its census row.
      kind      'declared' (the founding cell law binds it) | 'system' (code-registered/bootstrap,
                outside the law).
      cell      the declared cell (S|U|U{s}|S{u}) or None.
      finding   True iff a DECLARED op has no well-formed cell (completeness finding) OR a
                declared-S op does not replay to identity (the honesty guard). A system op is never
                a finding — it is outside the law and reported by name.
    """
    if not is_definition_born:
        return {"op": op, "kind": "system", "cell": None, "replays": None, "finding": False,
                "reason": "code-registered kernel/bootstrap primitive — outside the founding cell law (no declared cell required)"}
    cell = cell_of(definition)
    if cell is None:
        return {"op": op, "kind": "declared", "cell": None, "replays": None, "finding": True,
                "reason": "a declared operation with NO well-formed cell — a founding-data gap (L28: never defaulted to S)"}
    if cell == "S" and replays is False:
        return {"op": op, "kind": "declared", "cell": cell, "replays": False, "finding": True,
                "reason": "declared S but does NOT replay to identity — 'declared S, actually U' (a mis-declaration)"}
    return {"op": op, "kind": "declared", "cell": cell, "replays": (replays if cell == "S" else None),
            "finding": False,
            "reason": ("declared %s; replays to identity" % cell) if cell == "S"
                      else ("declared %s (judgment) — validated to schema, never scored" % cell)}


# ---- enumerate + classify the live registry -------------------------------------------------

def census_from(op_names, defs, replay_of):
    """The census kernel, taking its inputs directly so a control can PLANT into `defs`.
      op_names   the full registered op population (gate.ops).
      defs       op_definitions() (definition-born ops -> {'definition': {...}}); a name absent
                 here is a system/code-registered op.
      replay_of  op_name -> bool|None : the declared-S replay reading (True replays, False a
                 finding); None for non-S / unknowable.
    One row per registered op, sorted by name."""
    rows = []
    for op in sorted(op_names):
        entry = defs.get(op)
        is_born = entry is not None
        definition = (entry or {}).get("definition") if is_born else None
        rows.append(classify_cell(op, definition, is_born, replay_of.get(op)))
    return rows


def census(gate, views):
    """The census over the live composed kernel: one row per registered op. The declared cell is
    READ from op_definitions (founding data); the replay reading is the estate's own guard."""
    defs = views.op_definitions()
    replay_of = {}
    for op, entry in defs.items():
        cell = cell_of((entry or {}).get("definition"))
        if cell == "S":
            replay_of[op] = views.op_replays_to_identity(op)
    return census_from(set(gate.ops), defs, replay_of)


# ---- the finding sets ------------------------------------------------------------------------

def declared_rows(rows):
    return [r for r in rows if r["kind"] == "declared"]


def system_rows(rows):
    return [r for r in rows if r["kind"] == "system"]


def completeness_findings(rows):
    """THE A1 RED SET: a DECLARED op with no well-formed cell. Empty over the real founding (every
    declared op carries a cell); a declared op missing one reds (founding-data gap)."""
    return [r for r in rows if r["kind"] == "declared" and r["cell"] is None]


def replay_findings(rows):
    """THE A2 RED SET: a declared-S op that does NOT replay to identity — 'declared S, actually U'.
    Empty over the real founding (every gov-os op is a structured record-mechanic that replays); a
    planted mis-declaration (`replays_to_identity: false`) reds it."""
    return [r for r in rows if r["kind"] == "declared" and r["cell"] == "S" and r["replays"] is False]


def op_judgment_count(rows):
    """THE OP-LEVEL judgment count DERIVED FROM DECLARED CELLS: declared ops whose cell has any U
    (U | U{s} | S{u}). Over gov-os's own registry this is 0 — every op is a structured
    record-mechanic; judgment lives at stations, not in the recorder's ops."""
    return [r for r in rows if r["kind"] == "declared" and r["cell"] in JUDGMENT_CELLS]


# ---- A3: the OUTSIDE constitution's judgment count, INFERRED-from-shape (not enforcement) ----

def _lazy_derive_twc_pack():
    """Import the read-only pwc-app derived pack P5 supplies. Returns the pack dict, or None if the
    sibling app is not present or the derivation is unavailable (the census's A1/A2 still run)."""
    try:
        from test_ep51 import derive_twc_pack  # the estate's single, read-only derivation
    except Exception:
        return None
    try:
        return derive_twc_pack()
    except Exception:
        return None


def constitution_judgment_count(pack, as_of_head=None, founding_version=None):
    """A3-OUTSIDE — the OUTSIDE constitution's judgment count over its RULES, labelled honestly
    INFERRED-from-shape (archi :3711). It reads the derived pack's `enforced_by`, which
    `test_ep51.derive_twc_pack` SETS from the CANDIDATE_KINDS shape regexes — so this figure and the
    `lexical` figure below are ONE count read twice and their `match` is a TAUTOLOGY, not an
    independent agreement (the honest gov-os enforcement count lives in `gov_os_constitution_count`,
    read from real op check rows and independent of these regexes). The computation is UNCHANGED
    from before the relabel — only what it is called and described has changed. Returns the counts
    and the (tautological) comparison to the lexical count, each WITH ITS WORLD."""
    if pack is None:
        return None
    rows = pack["rows"]
    rules = [r for r in rows if r["class"] != "context"]            # references are context, not rules
    u_enforced = [r for r in rules if r["enforced_by"] == "judgment"]
    s_enforced = [r for r in rules if r["enforced_by"] == "structured"]
    context = [r for r in rows if r["class"] == "context"]          # non-rule, no check row
    lexical = pack["unstructured"]["count"]                          # test_ep51's shape-match count
    derived = len(u_enforced)
    return {
        "derived_judgment_count": derived,       # U-enforced RULES (no closed-kind check)
        "s_enforced_rules": len(s_enforced),
        "rules": len(rules),
        "context_rows": len(context),            # references: no check, NOT rules (disclosed, not counted)
        "all_no_check": len(u_enforced) + len(context),   # every enforced_by 'judgment' row (rules + context)
        "lexical_count": lexical,                # the shape-match count (INFERRED-from-shape)
        "match": derived == lexical,
        "world": {
            "outside_pack": pack["pack"], "version": pack["version"],
            "derived_from": pack["source"],       # law_book_sha256 + batch_sha256 + row counts
            "gov_os_as_of_head": as_of_head, "founding_version": founding_version,
        },
    }


# ---- A3-GOV-OS: THIS constitution's judgment count, GENUINELY derived from enforcement ---------
# Independent of the OUTSIDE figure by construction (archi :3711): it reads gov-os's OWN op check
# rows — each row's `check` is a member of the CLOSED OP_CHECKS vocabulary and its `cite` names the
# rule it enforces — NEVER the CANDIDATE_KINDS shape regexes. The two sources share no code path and
# no vocabulary.

NON_RULE_KINDS = ("op_definition", "view_definition")


def gov_os_closed_kind_cited_rules(op_defs):
    """The rule_ids that a REAL check row of a CLOSED kind CITES, read from gov-os's OWN op
    definitions. Each op's `checks` list carries rows; a row whose `check` is a member of the closed
    OP_CHECKS vocabulary and which names a `cite` enforces that cited rule by machinery. Returns the
    set of cited rule_ids. This is the estate's enforcement machinery READ DIRECTLY — it never
    touches _needs_kinds / CANDIDATE_KINDS / derive_twc_pack (the OUTSIDE figure's source)."""
    cited = set()
    for entry in op_defs.values():
        definition = (entry or {}).get("definition") or {}
        for chk in (definition.get("checks") or []):
            if chk.get("check") in OP_CHECKS and chk.get("cite"):
                cited.add(chk["cite"])
    return cited


def gov_os_rule_population(active_rules):
    """gov-os's OWN law rules: the active-rule fold MINUS the recorder's own definitions
    (op_definition / view_definition are the recorder's mechanics, not law rules — the same
    exclusion toothless_musts makes). Returns rule_id -> rule. A control can PLANT into the returned
    dict to move the enforcement count."""
    return {rid: r for rid, r in active_rules.items() if r.get("kind") not in NON_RULE_KINDS}


def gov_os_constitution_count(rules, cited, founding_version=None):
    """A3-GOV-OS — this constitution's judgment count, GENUINELY DERIVED FROM ENFORCEMENT and
    INDEPENDENT of the OUTSIDE pack's shape regexes (archi :3711). Over gov-os's own law rules:
      S-enforced        — the rule is CITED by a check row of a CLOSED kind (real machinery).
      judgment/deferred — the rule has NO such check row (its enforcement is a judgment or a gate).
    `cited` is the set from gov_os_closed_kind_cited_rules (op check rows), NEVER from _needs_kinds /
    CANDIDATE_KINDS. Takes its inputs directly so a control can plant a no-check rule and move the
    count. Published WITH ITS WORLD (founding version, closed-kind vocabulary size, rule
    population) — every coordinate STABLE (it moves only on a founding change, which is exactly when
    this reading should move; the gov-os git HEAD is deliberately not pinned)."""
    s_enforced = sorted(rid for rid in rules if rid in cited)
    judgment = sorted(rid for rid in rules if rid not in cited)
    return {
        "judgment_count": len(judgment),        # rules with NO closed-kind check row
        "s_enforced": len(s_enforced),
        "rules": len(rules),
        "closed_kinds": len(OP_CHECKS),          # the CLOSED enforcement vocabulary's size
        "judgment_rule_ids": judgment,
        "s_enforced_rule_ids": s_enforced,
        "world": {
            "constitution": "gov-os (this estate's own record)",
            "source": "op check rows: check in OP_CHECKS (closed) + cite naming an active_rules rule",
            "founding_version": founding_version,
            "closed_kinds": len(OP_CHECKS),
            "rule_population": len(rules),
        },
    }


def build_gov_os_count():
    """Assemble the A3-GOV-OS result over the live composed kernel — gov-os's own rules and its own
    op check rows. Reads views only; never the OUTSIDE pack."""
    _store, gate, views = build_full_kernel_for_census()
    rules = gov_os_rule_population(views.active_rules())
    cited = gov_os_closed_kind_cited_rules(views.op_definitions())
    _head, founding = _gov_os_world()
    return gov_os_constitution_count(rules, cited, founding_version=founding)


# ---- the evidence table (one row per op, a persisted artifact) -------------------------------

def _gov_os_world():
    """The observing world: the gov-os HEAD and founding version, for the A3 publication. Best-effort;
    None where unreadable (the evidence still renders)."""
    head = founding = None
    try:
        import subprocess
        head = subprocess.check_output(["git", "-C", _REPO, "rev-parse", "HEAD"],
                                       text=True).strip()
    except Exception:
        head = None
    try:
        import json
        with open(os.path.join(_SRC, "founding", "founding-pack.json"), encoding="utf-8") as fh:
            founding = json.load(fh).get("founding_version")
    except Exception:
        founding = None
    return head, founding


def render_markdown(rows, a3):
    out = []
    out.append("<!-- GENERATED by tools/conformance/cell_census.py — do not hand-edit. -->")
    out.append("<!-- Regenerate: python3 -m tools.conformance.cell_census --md -->")
    out.append("")
    out.append("# L28 · Cell census — every op's declared cell, the judgment count derived from it")
    out.append("")
    out.append("Every operation declares its CELL as founding data (design/52 L28): "
               "S structured-both-sides, U judgment-both, U{s} judgment over structured input, "
               "S{u} structured over judgment input. The cell is DECLARED, never derived from field "
               "shapes. This table is the census's reading of every op registered on the gate. A "
               "DECLARED op with no well-formed cell, or a declared-S op that does not replay to "
               "identity, would RED the census; system (code-registered) ops are outside the "
               "founding cell law and reported by name.")
    out.append("")
    dr = declared_rows(rows)
    sr = system_rows(rows)
    cf = completeness_findings(rows)
    rf = replay_findings(rows)
    ojc = op_judgment_count(rows)
    out.append("Ops censused: **%d** (declared **%d**, system **%d**). "
               "Completeness findings (must be zero): **%d**. "
               "Declared-S replay findings (must be zero): **%d**. "
               "Op-level judgment cells (declared U-involved): **%d**." % (
                   len(rows), len(dr), len(sr), len(cf), len(rf), len(ojc)))
    out.append("")

    out.append("## declared operations — the cell law binds these (%d)" % len(dr))
    out.append("")
    out.append("| op | cell | reading |")
    out.append("|---|---|---|")
    for r in dr:
        out.append("| %s | %s | %s |" % (r["op"], r["cell"] if r["cell"] else "—", r["reason"]))
    out.append("")

    out.append("## system operations — outside the founding cell law (%d)" % len(sr))
    out.append("")
    out.append("Read positively: each op below is a code-registered kernel/bootstrap primitive — "
               "the recorder's own mechanics (archi P8 precision 3). No declared cell is required "
               "of it; it is named here, never guessed, never a finding.")
    out.append("")
    out.append("| op | reason |")
    out.append("|---|---|")
    for r in sr:
        out.append("| %s | %s |" % (r["op"], r["reason"]))
    out.append("")

    out.append("## completeness findings (%d — must be zero)" % len(cf))
    out.append("")
    if cf:
        out.append("| op | reason |")
        out.append("|---|---|")
        for r in cf:
            out.append("| %s | %s |" % (r["op"], r["reason"]))
    else:
        out.append("_none — every declared operation carries a well-formed cell._")
    out.append("")

    out.append("## declared-S replay findings (%d — must be zero)" % len(rf))
    out.append("")
    if rf:
        out.append("| op | reason |")
        out.append("|---|---|")
        for r in rf:
            out.append("| %s | %s |" % (r["op"], r["reason"]))
    else:
        out.append("_none — every declared-S op replays to identity (the estate's founding property)._")
    out.append("")

    outside = (a3 or {}).get("outside")
    gov_os = (a3 or {}).get("gov_os")

    out.append("## judgment counts by enforcement — two constitutions, two independent sources (A3)")
    out.append("")
    out.append("A constitution's judgment count is over its RULES; a rule's cell follows its "
               "ENFORCEMENT — a rule enforced by a check row of a CLOSED kind is S-enforced, a rule "
               "with no such check is judgment-enforced. Two constitutions are read here, and (the "
               "finding archi :3711 answers) they DO NOT share a source: gov-os's own count reads "
               "REAL op check rows; the OUTSIDE count is inferred from shape regexes and is honestly "
               "labelled so.")
    out.append("")

    out.append("### A3-GOV-OS — this constitution's count, GENUINELY enforcement-derived")
    out.append("")
    gw = gov_os["world"]
    out.append("gov-os's own law rules carry real check rows: an op's `checks` row names a `check` "
               "in the CLOSED `OP_CHECKS` vocabulary and a `cite` naming the rule it enforces. A "
               "rule cited by such a closed-kind check row is S-enforced; a rule with no such check "
               "row is judgment-enforced-or-deferred. This reads the op check rows directly, NEVER "
               "the outside pack's shape regexes.")
    out.append("")
    out.append("- **Judgment-enforced-or-deferred rules (no closed-kind check row): %d**" % gov_os["judgment_count"])
    out.append("- S-enforced rules (cited by a closed-kind check row): **%d**  ·  rules total: **%d**" % (
        gov_os["s_enforced"], gov_os["rules"]))
    out.append("- Read from real machinery: the CLOSED `OP_CHECKS` vocabulary (**%d** kinds) + "
               "op_definitions' `checks`/`cite`. NOT `_needs_kinds` / `CANDIDATE_KINDS`." % gov_os["closed_kinds"])
    out.append("")
    # STABLE coordinates only: founding version + closed-kind vocabulary size + rule population.
    # Each moves only on a FOUNDING change (a rule, a check kind, a cite) — exactly when this reading
    # should move. The gov-os git HEAD is deliberately not pinned (it moves on every autosync commit;
    # a pin that reds because the repo moved rather than the subject moved is the git-hash-width
    # hazard the estate has paid for).
    out.append("**World named.** Constitution: gov-os (this estate's own record); source: op check "
               "rows (`check` in the closed OP_CHECKS + `cite` naming an active rule); closed-kind "
               "vocabulary: **%d**; rule population: **%d**; observing gov-os founding: %s." % (
                   gw["closed_kinds"], gw["rule_population"], (gw["founding_version"] or "?")))
    out.append("")

    out.append("### A3-OUTSIDE — the outside (pwc/TWC) constitution's count, INFERRED-from-shape")
    out.append("")
    if outside is None:
        out.append("_the outside constitution's derived pack is unavailable (apps/pwc-app not "
                   "present beside gov-os) — the outside figure is not read in this world; A1/A2 "
                   "and the gov-os count above stand on the live registry._")
    else:
        w = outside["world"]
        src = w["derived_from"]
        out.append("This figure is INFERRED-from-shape, NOT enforcement-derived: it reads the "
                   "derived pack's `enforced_by`, which `test_ep51.derive_twc_pack` SETS from the "
                   "`CANDIDATE_KINDS` shape regexes. So this count and the `lexical` count are ONE "
                   "count read twice — their MATCH is a TAUTOLOGY, not independent agreement. It is "
                   "retained because it is the only OUTSIDE reading possible today: pwc rules "
                   "declare no cell and carry no check rows (the R31 batch founds no checks), so a "
                   "TRUE declared-cell or enforcement count for the OUTSIDE constitution is owed to "
                   "the TWC/P9 line, not this delta.")
        out.append("")
        out.append("- **Inferred-from-shape judgment count: %d**" % outside["derived_judgment_count"])
        out.append("- Structured-shape rules: **%d**  ·  rules total: **%d**" % (outside["s_enforced_rules"], outside["rules"]))
        out.append("- Lexical shape-match count (test_ep51 CANDIDATE_KINDS — the SAME regex source): **%d**" % outside["lexical_count"])
        out.append("- **%s** — the inferred count %s the lexical count (a tautology: one source read twice)." % (
            "MATCH" if outside["match"] else "DIVERGENCE (a FINDING — published, not smoothed)",
            "EQUALS" if outside["match"] else "DIFFERS FROM"))
        out.append("- Disclosed, not counted as rules: **%d** context (reference) rows carry no "
                   "check row and are not rules; counting every no-check row (rules + context) "
                   "would give **%d**." % (outside["context_rows"], outside["all_no_check"]))
        out.append("")
        # STABLE coordinates only — the pwc law-book/batch hashes (a read-only sibling) and the
        # founding version. The gov-os git HEAD is NOT pinned here (git-hash-width hazard, as above).
        out.append("**World named.** Outside pack: `%s` v%s; pwc law-book sha256 `%s`; R31 batch "
                   "sha256 `%s`; law rows %d. Observing gov-os founding: %s." % (
                       w["outside_pack"], w["version"],
                       src.get("law_book_sha256", "?"), src.get("batch_sha256", "?"),
                       src.get("law_rows", 0), (w["founding_version"] or "?")))
    out.append("")
    return "\n".join(out)


EVIDENCE_PATH = os.path.join(_REPO, "planning", "evidence", "P4b-CELL-CENSUS", "cell-census.md")


def build_a3():
    """Assemble BOTH A3 figures over the live world, kept in ONE dict but from TWO independent
    sources: `gov_os` reads gov-os's own op check rows (genuinely enforcement-derived); `outside`
    reads the pwc-derived pack's `enforced_by` (inferred-from-shape, or None if pwc-app is absent).
    They share no source (archi :3711)."""
    pack = _lazy_derive_twc_pack()
    head, founding = _gov_os_world()
    outside = constitution_judgment_count(pack, as_of_head=head, founding_version=founding)
    return {"gov_os": build_gov_os_count(), "outside": outside}


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv[1:])
    _store, gate, views = build_full_kernel_for_census()
    rows = census(gate, views)
    a3 = build_a3()
    if "--md" in argv:
        print(render_markdown(rows, a3))
        return 0
    print("censused %d ops (declared %d, system %d); %d completeness findings (must be 0); "
          "%d replay findings (must be 0); %d op-level judgment cells" % (
              len(rows), len(declared_rows(rows)), len(system_rows(rows)),
              len(completeness_findings(rows)), len(replay_findings(rows)), len(op_judgment_count(rows))))
    g = a3["gov_os"]
    print("  A3-GOV-OS (enforcement-derived): %d judgment/deferred rules, %d S-enforced, %d rules "
          "(read from op check rows, OP_CHECKS)" % (g["judgment_count"], g["s_enforced"], g["rules"]))
    outside = a3["outside"]
    if outside is not None:
        print("  A3-OUTSIDE (inferred-from-shape): %d judgment count vs lexical %d -> %s (tautology: "
              "one source read twice)" % (
                  outside["derived_judgment_count"], outside["lexical_count"],
                  "MATCH" if outside["match"] else "DIVERGENCE"))
    else:
        print("  A3-OUTSIDE unavailable (apps/pwc-app not present)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
