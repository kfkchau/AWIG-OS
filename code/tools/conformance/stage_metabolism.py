# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (rule lifecycle stage, per-body clock, recording moment, local dwell, causal order,
# census). NON-GOAL: no offensive capability of any kind — this COMPUTES a metabolism VIEW (local
# dwell per stage per body on that body's own recording moment) and CENSUSES that no metabolism or
# comparison view folds two bodies' clocks into one interval or instant (I23 limb 3). It reads
# record_time and the crossing/receipt, mints nothing, drives no attack, adds no row field. Full
# declaration: SCOPE-STATEMENT.md.
"""C6 P15 · B7 metabolism + I23 limb-3 census — the per-body local-dwell VIEW and its census.

Two deliverables, one instrument (the I2/I20 kind, the sibling of the effect-order and
five-families censuses):

  (1) THE METABOLISM VIEW — rule metabolism read HONESTLY across two clocks (SPIKE-4 FINDINGS §4;
      design/52 B7:56, B14:63, I23:95). A stage's cost is its LOCAL DWELL: the interval between two
      arrivals at the SAME body, both timestamped by THAT ONE body's own `record_time` (minted at
      append, never supplied — `src/kernel/store.py:1000`), a true local metric monotone within one
      record. The end-to-end relation is a CAUSAL ORDER witnessed by the crossing/receipt binding
      ("B received after A sent", `src/kernel/border.py` content_id/receipt), NEVER a subtractable
      duration. No figure spans two bodies' clocks as a bare number (I23 limb 3).

  (2) THE LIMB-3 CENSUS — an INSTRUMENT over the views (NOT a rule the record checks about itself,
      SPIKE-4 §3): it reads every metabolism/comparison view and REFUSES any that subtracts one
      body's `record_time` from another's as though they shared a clock. The single sanctioned place
      a `record_time` subtraction may happen is `local_interval`, which asserts SAME BODY at runtime;
      a view that writes the subtraction itself (`other.record_time - mine.record_time`) is the
      cross-clock fold, and the census REDS on exactly that shape — the sibling discipline to the
      effect-order census's one deferred site and the five-families census's one closed vocabulary.

THE STAGE PIN IS ASSERTED, NOT PROVED (design/52 B7 SOURCE-DERIVED note; intake:144 / §11:243 — the
eight-stage mapping is "a first derivation for the owner's correction, not law", and five documents
of the lifecycle corpus were unread by its author). The eight stages are PINNED to kinds of EXISTING
row (announcement = a propagated rule row; reporting = a submission row; monitoring = views over
enforcement records, i.e. NOT A ROW; analysis = a separate proposal record; environment change =
rows by non-body actors; communication = not gov-os's). A pin is a chosen mapping asserted; the row
shape's field census is UNCHANGED and no stage adds a row field (I9:81).

NO NEW founding vocabulary, NO NEW ROW FIELD (I9), NO NEW CHECK KIND (I23), NO PACK EDIT. The
send-time-claim value (§11:227) that would let a cross-body figure be a NAMED attributed estimate is
a founding param amendment riding P8 — named here, minted by nobody (SPIKE-4 §5). The default view
ships local dwell + causal order and needs it not.

USAGE
    python3 -m tools.conformance.stage_metabolism            # print the census + stage pin
    python3 -m tools.conformance.stage_metabolism --md       # emit the evidence markdown body
"""

import ast
import datetime
import inspect
import os
import sys
import textwrap

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(os.path.dirname(os.path.dirname(_HERE)), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)


# =================================================================================================
# THE STAGE PIN — the eight lifecycle stages read as kinds of EXISTING row (asserted, not proved).
# =================================================================================================
# design/52 B7:56 names the mapping; §11:243 rules it "a first derivation ... not law". Each gov-os
# stage is a kind of row already in the ledger, identified by EXISTING record fields only — the
# closed set below is a subset of the shipped record's own top-level fields (store.py `_append_one`:
# action, actor, target, payload, ...). A stage adds NO field (I9): `reads_fields` names only fields
# a fresh record already carries, and the pin introduces none. `communication` is recorded as NOT a
# gov-os stage (B7: "communication is not gov-os's") — pinned to no row kind on purpose.
STAGE_PIN = {
    "announcement": {
        "row_kind": "a propagated rule row",
        "reads_fields": ("action", "payload"),
        "reason": "the rule row itself, propagated to a body's inbox — an existing row whose action "
                  "carries the rule; no new field (B7, I9)",
        "gov_os_stage": True,
    },
    "reporting": {
        "row_kind": "a submission row (BORDER-SUBMIT)",
        "reads_fields": ("action", "target", "payload"),
        "reason": "a submission into the decision machine's inbox — the existing crossing submit row "
                  "(border.py BORDER-SUBMIT), no new field",
        "gov_os_stage": True,
    },
    "monitoring": {
        "row_kind": "views over enforcement records (NOT a row)",
        "reads_fields": (),
        "reason": "monitoring is a VIEW over enforcement records, not a row and not a new field — a "
                  "fold, killed and replayed identical",
        "gov_os_stage": True,
    },
    "analysis": {
        "row_kind": "a separate proposal record",
        "reads_fields": ("action", "payload"),
        "reason": "analysis is a separate record, proposals only — an existing row kind, no new field",
        "gov_os_stage": True,
    },
    "environment": {
        "row_kind": "rows by non-body actors",
        "reads_fields": ("actor",),
        "reason": "environment change is recorded as rows whose ACTOR is a non-body actor — the "
                  "existing actor field distinguishes it, no new field",
        "gov_os_stage": True,
    },
    "communication": {
        "row_kind": "not gov-os's",
        "reads_fields": (),
        "reason": "communication is NOT a gov-os stage (B7): pinned to no row kind — the pin records "
                  "the exclusion rather than inventing a row for it",
        "gov_os_stage": False,
    },
}

#: The record's own top-level field census, read from the shipped store shape (store.py
#: `_append_one`). The stage pin adds NO field: every `reads_fields` entry is a member of this set.
#: Read from a fresh record at check time (the test does this) so a real drift in the row shape is
#: caught rather than a re-typed constant going stale.
KNOWN_RECORD_FIELDS = frozenset({
    "record_id", "seq", "record_time", "submission_time", "occurrence_time", "origin",
    "actor", "action", "object", "target", "rule_cited", "evidence_summary", "provenance",
    "content_form", "refs", "payload",
})


def stage_pin_fields():
    """Every record field the stage pin reads — a subset of the shipped row shape (I9). No stage
    names a field the record does not already carry; the pin adds none."""
    out = set()
    for spec in STAGE_PIN.values():
        out.update(spec["reads_fields"])
    return out


# =================================================================================================
# THE METABOLISM VIEW — local dwell per body on that body's own clock, plus the causal order.
# =================================================================================================

class Arrival:
    """One stage-row's ARRIVAL at ONE body, carrying that body's own recording moment. `body` is the
    body's name (its identity); `record_time` is the ISO recording moment MINTED by that body's store
    at append (store.py:1000 — never supplied). Two arrivals compared for a local dwell must be the
    SAME body: the dwell is a metric only within one body's own clock (B14, I23)."""

    __slots__ = ("body", "stage", "record_time")

    def __init__(self, body, stage, record_time):
        self.body = body
        self.stage = stage
        self.record_time = record_time


class CrossClockFold(Exception):
    """Raised by the sanctioned interval sink when handed two arrivals from DIFFERENT bodies — the
    runtime floor of I23 limb 3 (no view subtracts one body's clock from another's). The census is
    the static floor over the views; this is the dynamic floor at the one place a subtraction lives."""


def _parse_moment(iso):
    """Parse a body's own recording moment (an ISO-8601 string, store.py `_now_iso`) to a datetime.
    A pure read of ONE body's clock value — it folds nothing."""
    return datetime.datetime.fromisoformat(iso)


def local_interval(earlier, later):
    """THE ONE SANCTIONED PLACE A `record_time` SUBTRACTION HAPPENS — and it is guarded to be SAME
    BODY. Returns the local dwell (a `timedelta`) between two arrivals at the SAME body, on that one
    body's own clock. Handed two bodies, it RAISES `CrossClockFold` rather than fold two clocks
    (I23 limb 3, the runtime floor). Every metabolism/comparison view routes its interval math
    THROUGH here and never writes the subtraction itself; the census reds on any view that does — the
    exact sibling of the effect-order census exempting only the one deferred site."""
    if earlier.body != later.body:
        raise CrossClockFold(
            "local_interval was handed two arrivals from DIFFERENT bodies (%r, %r): a dwell is a "
            "metric only within ONE body's own clock; across two bodies time is a causal order, "
            "never a subtractable quantity (design/52 B14/I23 limb 3)" % (earlier.body, later.body))
    # the subtraction — the estate's ONLY record_time arithmetic, here and same-body-guarded.
    return _parse_moment(later.record_time) - _parse_moment(earlier.record_time)


def local_dwell_per_stage(arrivals):
    """METABOLISM, PER BODY: given the arrivals AT ONE BODY (its own stage-rows, each on its own
    `record_time`), return the local dwell between each successive pair — a stage's cost as a true
    local metric. Every interval is same-body by construction (the caller passes one body's
    arrivals) and is computed through `local_interval`, never by a raw subtraction. Returns a list
    of {from_stage, to_stage, body, dwell_seconds}."""
    bodies = {a.body for a in arrivals}
    if len(bodies) > 1:
        raise CrossClockFold(
            "local_dwell_per_stage was given arrivals from more than one body %r — metabolism is "
            "PER BODY; call it once per body (I23 limb 3)" % sorted(bodies))
    ordered = sorted(arrivals, key=lambda a: a.record_time)
    out = []
    for earlier, later in zip(ordered, ordered[1:]):
        dwell = local_interval(earlier, later)          # sanctioned, same-body
        out.append({"from_stage": earlier.stage, "to_stage": later.stage,
                    "body": earlier.body, "dwell_seconds": dwell.total_seconds()})
    return out


def causal_order(submit_record, receipt_record):
    """THE END-TO-END RELATION, HONESTLY: a causal ORDER, not a metric. "B received after A sent" is
    witnessed by the crossing/receipt binding — B's receipt cites the CONTENT HASH of A's submit
    (border.content_id, which EXCLUDES record_time), so the receipt binds the submit and the send
    causally PRECEDES the receipt. Returns an ordered list of (body, stage) — an ORDER, with NO
    cross-clock number. Reads border.py's own binding, reused, never re-authored. Returns None if the
    receipt does not bind the submit (no causal edge to assert)."""
    from kernel import border
    if not border.receipt_binds_row(receipt_record, submit_record):
        return None
    sender = (submit_record.get("actor") or "A")
    receiver = (receipt_record.get("actor") or "B")
    # the order is the causal witness only — send precedes receipt because the receipt is OF the send.
    return [(sender, "reporting-send"), (receiver, "reporting-receipt")]


# =================================================================================================
# THE LIMB-3 CENSUS — an instrument over the views (the I2/I20 kind). No new check kind.
# =================================================================================================
#: The metabolism/comparison views this module ships — the census's subject. Named in ONE place
#: (the effect-order census's discipline). A new view is added here and is censused; the sanctioned
#: sink `local_interval` is NOT a view (it is the one exempt site) and never appears in this list.
METABOLISM_VIEWS = ("local_dwell_per_stage", "causal_order")


class _RecordTimeFoldFinder(ast.NodeVisitor):
    """Walk a view's AST; RED on any `record_time` subtraction the view writes itself — the
    cross-clock fold. A `Sub` BinOp (or an augmented `-=`) whose operand subtree reads `record_time`
    (an attribute `.record_time` or a subscript `['record_time']`) is the forbidden shape. The
    sanctioned `local_interval` is the ONLY place this subtraction may live, and it is NOT censused
    as a view — so an honest view (which CALLS local_interval and never subtracts) carries none of
    these, and a planted view (which writes `other.record_time - mine.record_time`) carries one."""

    def __init__(self):
        self.folds = []          # list of reason strings, one per fold site

    @staticmethod
    def _reads_record_time(node):
        for sub in ast.walk(node):
            if isinstance(sub, ast.Attribute) and sub.attr == "record_time":
                return True
            if isinstance(sub, ast.Subscript):
                key = sub.slice
                if isinstance(key, ast.Constant) and key.value == "record_time":
                    return True
        return False

    def visit_BinOp(self, node):
        if isinstance(node.op, ast.Sub) and (
                self._reads_record_time(node.left) or self._reads_record_time(node.right)):
            self.folds.append(
                "a view subtracts `record_time` directly (not through the same-body-guarded "
                "`local_interval`) — a cross-clock fold (I23 limb 3)")
        self.generic_visit(node)

    def visit_AugAssign(self, node):
        if isinstance(node.op, ast.Sub) and (
                self._reads_record_time(node.target) or self._reads_record_time(node.value)):
            self.folds.append(
                "a view subtracts `record_time` in place (`-=`) outside `local_interval` — a "
                "cross-clock fold (I23 limb 3)")
        self.generic_visit(node)


def classify_view(view_src):
    """Read one view's source; return {folds: bool, reasons: [...]}. `folds` is True iff the view
    writes a `record_time` subtraction itself (the cross-clock fold). Mirrors the effect-order
    census's `classify_source`: a single mechanical question over the AST, a closed forbidden shape."""
    tree = ast.parse(textwrap.dedent(view_src))
    finder = _RecordTimeFoldFinder()
    finder.visit(tree)
    return {"folds": bool(finder.folds), "reasons": finder.folds}


def _view_source(name, module=None):
    """The source of a named view function in this module (or a supplied module, for a planted
    behavioural control). None if it cannot be read."""
    mod = module if module is not None else sys.modules[__name__]
    fn = getattr(mod, name, None)
    if fn is None:
        return None
    try:
        return inspect.getsource(fn)
    except (OSError, TypeError):
        return None


def census(views=METABOLISM_VIEWS, module=None):
    """THE CENSUS: one row per metabolism/comparison view, sorted by name.
    Each row: {view, folds, reasons}. The shipped views carry `folds=False` — no view folds two
    clocks. A view whose source cannot be read reds as `unreadable` (it could hide a fold), the
    sibling of the five-families census's `unknown`."""
    rows = []
    for name in sorted(views):
        src = _view_source(name, module)
        if src is None:
            rows.append({"view": name, "folds": True,
                         "reasons": ["source unreadable — an unreadable view could hide a fold"]})
            continue
        c = classify_view(src)
        c["view"] = name
        rows.append(c)
    return rows


def folding_views(rows):
    """THE RED SET: any view that folds two bodies' clocks. Empty over the shipped views is the whole
    point; non-empty is I23 limb 3 violated — a view subtracting one body's clock from another's."""
    return [r for r in rows if r["folds"]]


# ---- the evidence table (one row per view + the stage pin, a persisted artifact) ----------------

def render_markdown(rows=None):
    if rows is None:
        rows = census()
    fold = folding_views(rows)
    out = []
    out.append("<!-- GENERATED by tools/conformance/stage_metabolism.py — do not hand-edit. -->")
    out.append("<!-- Regenerate: python3 -m tools.conformance.stage_metabolism --md -->")
    out.append("")
    out.append("# P15 · Stage metabolism — the per-body local-dwell view and the I23 limb-3 census")
    out.append("")
    out.append("Rule metabolism read HONESTLY across two clocks (design/52 B7/B14/I23; SPIKE-4 §4): "
               "a stage's cost is its LOCAL DWELL — the interval between two arrivals at the SAME "
               "body on that one body's own `record_time` — and the end-to-end relation is a CAUSAL "
               "ORDER (the crossing/receipt binding), never a cross-clock duration. The census below "
               "is an instrument over the views (the I2/I20 kind); a view that subtracts one body's "
               "clock from another's would read `folds` and RED it.")
    out.append("")
    out.append("## The stage pin — lifecycle stages as kinds of existing row (asserted, not proved)")
    out.append("")
    out.append("design/52 B7 names this mapping and §11:243 rules it \"a first derivation ... not "
               "law\" (five documents of the lifecycle corpus, D08.28, were unread by its author). "
               "The stages B7 names in-tree are pinned below; naming the remainder of the eight from "
               "an unread corpus would be invention, not a pin. A pin is a chosen mapping ASSERTED; "
               "the row shape's field census is UNCHANGED and no stage adds a row field (I9).")
    out.append("")
    out.append("| stage | gov-os stage? | row kind | record fields read (all existing) |")
    out.append("|---|---|---|---|")
    for stage in STAGE_PIN:
        spec = STAGE_PIN[stage]
        gov = "yes" if spec["gov_os_stage"] else "no (B7: not gov-os's)"
        fields = ", ".join(spec["reads_fields"]) if spec["reads_fields"] else "_none (a view/exclusion)_"
        out.append("| %s | %s | %s | %s |" % (stage, gov, spec["row_kind"], fields))
    out.append("")
    out.append("Fields the pin reads: **%s** — all members of the shipped row shape; the pin adds "
               "**0** fields (I9)." % (", ".join(sorted(stage_pin_fields())) or "none"))
    out.append("")
    out.append("## The limb-3 census — one row per metabolism/comparison view")
    out.append("")
    out.append("Views censused: **%d**. Folding views (must be zero): **%d**. The one sanctioned "
               "place a `record_time` subtraction happens is `local_interval`, guarded SAME BODY at "
               "runtime; it is not a view and is not censused." % (len(rows), len(fold)))
    out.append("")
    out.append("| view | folds two clocks? |")
    out.append("|---|---|")
    for r in rows:
        verdict = "**YES — cross-clock fold**" if r["folds"] else "no (routes through local_interval)"
        out.append("| %s | %s |" % (r["view"], verdict))
    out.append("")
    return "\n".join(out)


EVIDENCE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(_HERE)),
    "planning", "evidence", "P15-STAGE-METABOLISM", "stage-metabolism.md")


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv[1:])
    rows = census()
    if "--md" in argv:
        print(render_markdown(rows))
        return 0
    fold = folding_views(rows)
    print("censused %d metabolism/comparison views; %d folding two clocks (must be 0)"
          % (len(rows), len(fold)))
    for r in rows:
        print("  %-24s %s" % (r["view"], "FOLDS" if r["folds"] else "ok"))
    print("stage pin: %d stages; fields read: %s; new fields: 0"
          % (len(STAGE_PIN), ", ".join(sorted(stage_pin_fields()))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
