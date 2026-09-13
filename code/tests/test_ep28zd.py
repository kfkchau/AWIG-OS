"""EP-28ZD — CREATE-RULE's DECLARATION MADE TRUE IN THREE DIRECTIONS. Founding 1.20.0 -> 1.21.0.

WHY THIS BATTERY EXISTS, in the establishment's own finding. EP-28ZC drove the shipped
`CREATE-RULE` and found its declaration wrong in both directions and orphaned in a third:

  * SEVEN fields the op WRITES into every record it makes — policy_key, value, when, then,
    polarity, enforcement, enforced_by — appeared in NO params entry at all.
  * SIX fields the founding's own 42 rule records CARRY were written by the op NOWHERE —
    text in all 42, scope in 28, root in 19, tier in 5, protected_packs and key_space in 1
    each — so a law made through the SHIPPED op could never carry its human sentence, could
    never declare its binding scope, could never be a root law, and could never carry a
    tier. A caller supplying them was ACCEPTED and told nothing while every one was dropped.
  * ONE ORPHAN: `exclusive` is carried by ZERO of the 42, the only `payload_from` name with
    no use anywhere in the founding.

EP-28ZC's fence forbade it from writing anything, so its four probes existed ONLY as prose in
its BUILD-PROGRESS entry and it said so: "they will have to be re-driven by whoever takes the
lane." THIS FILE IS THAT LANDING. Every probe below was re-driven at this pass's own hand
against the amended declaration, and the pre-amend answers are quoted beside them from ZC's
entry as the TRACED BEFORE rather than re-run (the before world is reachable, and where the
before is the interesting half it IS re-run here, era-pinned — see `TheTierClaimBecameVisible`).

WHAT THIS PASS DID NOT DO, pinned so no green here is read wider than it is:

  * NO ENGINE LINE MOVED. `gate.py` and every interpreter line are untouched. This changes
    what the operation DECLARES, never how the gate treats what is undeclared, and the
    GENERAL silent acceptance-and-strip of an undeclared name is UNCHANGED and RAISED to the
    campaign close rather than taken here. A row below drives that it still behaves as ZC
    found it, so "unchanged" is measured rather than asserted.
  * THE OTHER TWELVE UNDECLARED LAW IDS are untouched (EP-29 W1a's standing raise).
  * NO CENSUS INSTRUMENT WAS MINTED. EP-28ZC's one-line class figure (8 of 74 ops write a
    field they declare nowhere, 15 such fields, 7 of them here) stands as a line to the
    close's walk family; this file measures ONE op and says so.

THE ONE RESULT THAT READS LIKE A WIDENING AND IS ITS OPPOSITE. Declaring `tier` does not let
this op mint a protected law: it makes the claim VISIBLE to the guard that exists to refuse
it. Before, a call claiming tier constitutional was ACCEPTED and the claim silently dropped,
so the guard never fired and the record simply lost the field. Now the claim reaches the
payload, the constitution guard reads it, and the act REFUSES citing BOOT-INT with the refusal
recorded. That differential is driven on BOTH ERAS below rather than argued from one.
"""
import copy
import hashlib
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import era_pin                                              # noqa: E402  (the era-pin home, EP-28Z)
from founding import install as install_module              # noqa: E402
from kernel.boot import build_kernel                        # noqa: E402
from kernel.errors import OpError                           # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK_PATH = os.path.join(REPO, "src", "founding", "founding-pack.json")

#: THIS pass's own pre-write commit, captured with `git rev-parse HEAD` before any write
#: (§A53 — `git checkout --` no longer undoes a write on this box, so the recovery route is
#: the commit, not the working tree). It is the 1.20.0 ERA: the world this pass moved off.
#: PINNED BY CONTENT, NEVER BY VERSION NUMBER. Choosing a pin by version is `era_pin`'s own
#: stated cap and the estate's most expensive known trap (board :410); the sha256 below is
#: what makes this pin checkable, and `TheEraPinIsSound` checks it rather than trusting it.
BEFORE_COMMIT = "7fc50e4b0de2a880cb933f1343f869d87ef4fbbb"
BEFORE_VERSION = "1.20.0"
BEFORE_PACK_SHA = "d170619962d39ea5b9d317beecf6bb75d4678b0b1784278b150da7688499e00f"
AFTER_VERSION = "1.21.0"

#: THIS PASS'S OWN AFTER ERA, added by EP-29 W2b on 2026-08-13 under charter §A57 — a landing
#: pass cannot pin a close commit that does not exist yet, so the pin is placed by the NEXT
#: founding move. It is the last commit at which the shipped founding still read 1.21.0,
#: captured with `git rev-parse HEAD` before W2b's first write (§A53). Nine rows below read the
#: LIVE tree for this pass's AFTER side, which was correct exactly until a later founding pass
#: ran; W2b moved the founding to 1.22.0 and falsified all nine. They read this era instead.
#: PINNED BY CONTENT, NEVER BY VERSION NUMBER, on this file's own stated ground: the blob at
#: this rev hashes to the sha256 below, which is the pack sha EP-28ZD's close recorded as its
#: AFTER. Checked rather than trusted — `tests/test_ep29.py::TheW2bSweep` verifies both the
#: digest and that the commit it planted here is the one it verified, because §A57's fence
#: permits no NEW row in a swept file and the check therefore lives in the sweeping pass's own.
AFTER_COMMIT = "3d187e217705bbf5d851c5d5f71cde8d19d6227d"
AFTER_PACK_SHA = "d079b573ba9e28d1b623033b5779662e4e8bc9282254c0f4423756b29e2fe4aa"

#: The three sections a field can be DECLARED in, read out of the interpreter rather than
#: listed from memory: `params` (a caller supplies it), `param_defaults` (the engine fills it
#: when absent), `payload_derive` (the engine computes it, from a named source).
DECLARING_SECTIONS = ("params", "param_defaults", "payload_derive")

#: EP-28ZC's SEVEN — written by the op, declared nowhere before this pass.
THE_SEVEN = ("policy_key", "value", "when", "then", "polarity", "enforcement", "enforced_by")

#: EP-28ZC's SIX — carried by the founding's own rule records, written by the op nowhere
#: before this pass, with the per-field counts its census took and this file re-takes.
THE_SIX = {"text": 42, "scope": 28, "root": 19, "tier": 5,
           "protected_packs": 1, "key_space": 1}

#: The ORPHAN, and its READER — the disposition rule's whole hinge. `exclusive` is written by
#: the op and carried by none of the 42, so the rule asks one question: is it READ by
#: anything? It is. `opdefs.py:1028` reads it back off PRIOR records to discharge ROOT-NEG-6,
#: the law this op cites. Written-by-nothing AND read-by-nothing would be REMOVED; a live
#: reader means DECLARED with that reader cited, which is what this pass did.
THE_ORPHAN = "exclusive"


def live_pack():
    with open(PACK_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def pack_at(commit):
    """The era's own law, read out of git through the ONE home (charter §A57 (1a): a pass
    meeting the duty IMPORTS `tests/era_pin.py` and never re-derives it)."""
    return era_pin.pack_at(commit)


def create_rule_definition(pack):
    for st in pack["steps"]:
        for r in st["records"]:
            pl = r.get("payload") or {}
            if pl.get("kind") == "op_definition" and pl.get("name") == "CREATE-RULE":
                return pl["definition"]
    raise AssertionError("op:CREATE-RULE has no definition in this pack")


def rule_records(pack):
    return [r for st in pack["steps"] for r in st["records"]
            if r.get("action") == "CREATE-RULE"]


def written_fields(d):
    """WHAT THE OP WRITES, read out of the interpreter's own line rather than assumed:
    `opdefs.py:1530` builds the payload from `payload_from`, falling back to the params keys
    when it is absent. Everything else the interpreter honours is a DECLARED producer and is
    counted on the declared side, never here."""
    return set(d.get("payload_from") or (d.get("params") or {}).keys())


def declared_anywhere(d):
    out = set()
    for section in DECLARING_SECTIONS:
        out |= set(d.get(section) or {})
    return out


def section_of(d, field):
    """WHICH SECTION a field is declared in — the half C1 requires stated rather than left to
    a set difference, because 'declared' with no section is how the first draft of this amend
    put six fields in the wrong one and printed an empty diff anyway."""
    return tuple(s for s in DECLARING_SECTIONS if field in (d.get(s) or {}))


class _World:
    """A booted world. `pack` may be a dict, installed INSTEAD of the live one by substituting
    the installer's own loader — the ONE loader handed a different source.

    THE REASON THE LOADER IS SUBSTITUTED AND NOT THE PATH, recorded because this pass got it
    wrong first and the wrong version was CONFIDENT: `install.load_pack(path=PACK_PATH)` binds
    its default at DEFINITION time, so reassigning `install_module.PACK_PATH` after import
    changes nothing and both eras boot from the live tree. The arm reported
    `founding_version=1.21.0` for a world it labelled 1.20.0, and only printing the version
    caught it. Every era world below therefore asserts WHICH LAW FOUNDED IT before it asserts
    anything about that law."""

    def __init__(self, pack=None):
        self.dir = tempfile.mkdtemp(prefix="ep28zd-")
        self.path = os.path.join(self.dir, "record.jsonl")
        if pack is None:
            self.store, self.gate, self.views = build_kernel(self.path)
        else:
            original = install_module.load_pack
            install_module.load_pack = lambda *a, **k: copy.deepcopy(pack)
            try:
                self.store, self.gate, self.views = build_kernel(self.path)
            finally:
                install_module.load_pack = original

    def founded_under(self):
        fs = [e for e in self.store.all() if e["action"] == "FOUND-STORE"][0]
        return dict(fs["payload"])["founding_version"]

    def rule(self, actor="owner", **params):
        return self.gate.execute("CREATE-RULE", actor, params)

    def refusals(self):
        return [e for e in self.store.all() if e.get("refused")]


# =================================================================================================
# C1 — THE DECLARATION MATCHES THE TRUTH IN ALL THREE DIRECTIONS
# =================================================================================================

class TheThreeSetDiffsClose(unittest.TestCase):
    """C1. Three diffs, each required to print EMPTY or to be RESOLVED by a stated rule.

    THE FIRST DIFF IS `WRITTEN` AGAINST `DECLARED-ANYWHERE`, NOT AGAINST `params`, and the
    difference is this pass's own history: an earlier draft assigned the seven to `params` and
    the six to `payload_from`, which leaves the six WRITTEN-BUT-UNDECLARED IN PARAMS after its
    own amend — the defect recreated for exactly the fields the amend exists to add. A diff
    that counts a field declared in ANY section, with its section stated, cannot leave that
    residue; a diff against one section can."""

    def setUp(self):
        self.d = create_rule_definition(live_pack())

    def test_diff_1_every_WRITTEN_field_is_DECLARED_somewhere(self):
        residue = sorted(written_fields(self.d) - declared_anywhere(self.d))
        self.assertEqual(residue, [], "written and declared nowhere: %r" % residue)

    def test_diff_1_states_each_field_SECTION_and_no_field_is_sectionless(self):
        for f in sorted(written_fields(self.d)):
            self.assertNotEqual(section_of(self.d, f), (),
                                "%r is written and sits in no declaring section" % f)

    def test_diff_2_every_field_the_42_CARRY_is_DECLARED_somewhere(self):
        """The mirror direction — the one EP-28ZC found and nobody had named. POPULATION: the
        42 CREATE-RULE records in the shipped founding. BASIS: the union of their payload
        keys."""
        # [DOCUMENTED FLIP — EP-29 W2b, 2026-08-13, charter §A57. CAUSE: W2b declares
        # DEV-LAW-INTAKE, so the live founding carries 43 CREATE-RULE records. ASSERTED:
        # `live_pack()`. SUPERSEDED: `pack_at(AFTER_COMMIT)`, this pass's own era. REMAINS
        # TRUE: every field the 42 carried was declared somewhere by this pass's amendment,
        # which is a fact about 42 records at one commit and was never a fact about whatever
        # the founding grows to. GIVEN UP: nothing — the live population is walked by
        # `test_ep29.py::TheFoundingMovedAtW2b`, which asserts 42 -> 43 and re-validates.]
        recs = rule_records(pack_at(AFTER_COMMIT))
        self.assertEqual(len(recs), 42, "the population moved; every count below is about 42")
        carried = set()
        for r in recs:
            carried |= set(r["payload"])
        residue = sorted(carried - declared_anywhere(self.d))
        self.assertEqual(residue, [], "carried by the founding and declared nowhere: %r"
                         % residue)

    def test_diff_3_the_ORPHAN_is_exactly_one_name_and_it_is_exclusive(self):
        """A `payload_from` name carried by ZERO of the 42. `occurrence_time` is deliberately
        NOT in this set and the reason is the class rather than a courtesy: it is not a
        `payload_from` name at all — it is consumed by `occurrence_time_param`, which writes
        the record's own time FIELD and not its payload."""
        recs = rule_records(live_pack())
        carried = set()
        for r in recs:
            carried |= set(r["payload"])
        orphans = sorted(n for n in written_fields(self.d) if n not in carried)
        self.assertEqual(orphans, [THE_ORPHAN])
        self.assertNotIn("occurrence_time", written_fields(self.d))

    def test_the_diffs_CAN_REPORT_A_DIVERGENCE(self):
        """§7.1's rule, at the instrument rather than at the subject: a diff that cannot print
        non-empty proves nothing by printing empty. Each is driven against a SYNTHETIC
        definition carrying a planted hole."""
        planted = copy.deepcopy(self.d)
        planted["payload_from"] = list(planted["payload_from"]) + ["planted_undeclared"]
        self.assertEqual(sorted(written_fields(planted) - declared_anywhere(planted)),
                         ["planted_undeclared"])
        stripped = copy.deepcopy(self.d)
        del stripped["params"]["text"]
        self.assertIn("text", written_fields(stripped) - declared_anywhere(stripped))
        self.assertEqual(section_of(stripped, "text"), ())


class TheSevenAndTheSixAreNamedSets(unittest.TestCase):
    """C1. EP-28ZC named both sets and the counts; this pass RE-TOOK every figure by parsing
    rather than carrying them, and pins them so a later reader checks the list, never the
    claim."""

    def setUp(self):
        self.live = create_rule_definition(live_pack())
        self.before = create_rule_definition(pack_at(BEFORE_COMMIT))

    def test_the_SEVEN_were_undeclared_before_and_are_params_now(self):
        before_undeclared = written_fields(self.before) - declared_anywhere(self.before)
        self.assertEqual(sorted(before_undeclared), sorted(THE_SEVEN))
        for f in THE_SEVEN:
            self.assertIn("params", section_of(self.live, f),
                          "%r is parameter-shaped — a caller supplies it and the op writes "
                          "exactly what arrived — so it belongs in params" % f)

    def test_the_SIX_were_written_NOWHERE_before_and_are_params_and_written_now(self):
        self.assertEqual(sorted(set(THE_SIX) - written_fields(self.before)),
                         sorted(THE_SIX), "a field of the six was already written before")
        for f in THE_SIX:
            self.assertIn("params", section_of(self.live, f))
            self.assertIn(f, written_fields(self.live))

    def test_the_SIX_carry_the_counts_the_establishment_took(self):
        # [DOCUMENTED FLIP — EP-29 W2b, 2026-08-13, charter §A57. CAUSE: W2b's new law record
        # carries `text`, taking that count from 42 to 43. ASSERTED: `live_pack()`.
        # SUPERSEDED: `pack_at(AFTER_COMMIT)`. REMAINS TRUE: THE_SIX's counts are the
        # establishment's census of the 42 as they stood, and this row is what re-takes them.]
        recs = rule_records(pack_at(AFTER_COMMIT))
        for f, n in THE_SIX.items():
            got = sum(1 for r in recs if f in r["payload"])
            self.assertEqual(got, n, "%s: %d of 42, establishment said %d" % (f, got, n))

    def test_the_two_historical_spellings_are_both_true_of_one_definition(self):
        """EP-28ZC reported SEVEN and EIGHT and refused to reconcile them, which was right:
        seven is `payload_from` minus params-union-param_defaults (the union the estate's own
        four definition-time validators apply), eight is minus the literal words of `params`,
        and `exclusive` is the whole difference. Pinned here against the BEFORE era so the
        pair stays checkable after the live answer became zero."""
        d = self.before
        params_only = written_fields(d) - set(d.get("params") or {})
        union = written_fields(d) - (set(d.get("params") or {})
                                     | set(d.get("param_defaults") or {}))
        self.assertEqual(len(params_only), 8)
        self.assertEqual(len(union), 7)
        self.assertEqual(sorted(params_only - union), [THE_ORPHAN])


class TheFormsAreExplicit(unittest.TestCase):
    """C1 — `params` with an EXPLICIT form, no bare forms. The vocabulary is the pack's own
    and is READ from it rather than declared here, so a future third form is visible."""

    def test_every_CREATE_RULE_param_carries_a_form_from_the_packs_own_vocabulary(self):
        pack = live_pack()
        vocabulary = set()
        for st in pack["steps"]:
            for r in st["records"]:
                d = (r.get("payload") or {}).get("definition")
                if isinstance(d, dict):
                    vocabulary |= set((d.get("params") or {}).values())
        self.assertEqual(sorted(vocabulary), ["optional", "required"],
                         "the params form vocabulary grew; this row's premise moved")
        for name, form in create_rule_definition(pack)["params"].items():
            self.assertIn(form, ("optional", "required"),
                          "%r carries a bare or unknown form %r" % (name, form))

    def test_only_rule_id_is_REQUIRED_so_no_existing_caller_became_nonconforming(self):
        """`optional` is the TRUE statement about this op and `required` would be a WIDENING
        of the law: the gate refuses AR-2 on an absent `required` name (gate.py:801-809), so
        one `required` here would make every existing bare caller nonconforming. The precedent
        is exact — v1.19.0 declared REGISTER-CAPABILITY's two undeclared fields OPTIONAL for
        this reason and RAISED the widening rather than taking it."""
        params = create_rule_definition(live_pack())["params"]
        self.assertEqual(sorted(k for k, v in params.items() if v == "required"), ["rule_id"])


class TheOrphanWasDisposedByTheReadProbe(unittest.TestCase):
    """C1 — the orphan rule, DRIVEN and not argued: written-by-nothing AND read-by-nothing is
    REMOVED; read-by-anything is DECLARED with its reader cited. Disposing it without the
    probe REDS, so the probe is the row."""

    def test_the_orphan_is_written_by_the_op_and_carried_by_none_of_the_42(self):
        d = create_rule_definition(live_pack())
        self.assertIn(THE_ORPHAN, written_fields(d))
        self.assertEqual(sum(1 for r in rule_records(live_pack())
                             if THE_ORPHAN in r["payload"]), 0)

    def test_the_orphan_HAS_A_LIVE_READER_and_the_probe_is_a_refusal_that_needs_it(self):
        """THE PROBE. The reader is `opdefs.py:1028`, which reads `exclusive` back off PRIOR
        records through `views.active_rules`. It is driven rather than cited: the clash
        refusal below exists ONLY because the first rule's `exclusive` reached the record."""
        w = _World()
        w.rule(rule_id="PROBE-EXCL", policy_key="probe:key", value=7, exclusive=True)
        self.assertEqual(w.views.policy_value("probe:key"), 7)
        with self.assertRaises(OpError) as cm:
            w.rule(rule_id="PROBE-CLASH", policy_key="probe:key", value=9)
        self.assertEqual(cm.exception.rule, "ROOT-NEG-6")

    def test_the_probe_CAN_COME_BACK_THE_OTHER_WAY(self):
        """Non-vacuity: the same second call passes when the first rule is NOT exclusive, so
        the refusal above is attributable to the orphan's value and not to the shape of the
        call."""
        w = _World()
        w.rule(rule_id="PROBE-OPEN", policy_key="open:key", value=7, exclusive=False)
        w.rule(rule_id="PROBE-OPEN-2", policy_key="open:key", value=9)
        self.assertEqual(w.views.policy_value("open:key"), 9)

    def test_the_orphan_KEPT_its_default_so_a_bare_call_still_writes_false(self):
        w = _World()
        rec = w.rule(actor="SYSTEM", rule_id="PROBE-BARE-EXCL")
        self.assertIs(rec["payload"][THE_ORPHAN], False)


# =================================================================================================
# C2 — THE DRIVEN CONSEQUENCE: a law made through the op carries its sentence
# =================================================================================================

class TheLawMadeThroughTheOpCarriesItsSentence(unittest.TestCase):
    """C2, against EP-28ZC's traced before. ITS drive of this exact call was ACCEPTED and wrote
    `{enforced_by, enforcement, exclusive, polarity, policy_key, rule_id, then, value, when}` —
    nine keys, all four supplied fields gone, `views.root_rules()` returning `[]` for it."""

    def test_text_scope_and_root_are_WRITTEN_and_root_rules_RETURNS_the_law(self):
        w = _World()
        rec = w.rule(rule_id="ZD-TEXTED",
                     text="a human sentence, supplied by the caller",
                     scope="space:root", root=True,
                     polarity="-", then=[{"refuse": "ZD-TEXTED"}])
        p = rec["payload"]
        self.assertEqual(p["text"], "a human sentence, supplied by the caller")
        self.assertEqual(p["scope"], "space:root")
        self.assertIs(p["root"], True)
        got = [r for r in w.views.root_rules() if r["rule_id"] == "ZD-TEXTED"]
        self.assertEqual(len(got), 1, "root_rules() does not return the created law")
        self.assertEqual(got[0]["text"], "a human sentence, supplied by the caller")

    def test_the_SAME_CALL_against_the_BEFORE_era_drops_all_of_it(self):
        """The differential's other half, RE-RUN rather than quoted, because the before world
        is reachable and a differential with one measured side is one side."""
        w = _World(pack_at(BEFORE_COMMIT))
        self.assertEqual(w.founded_under(), BEFORE_VERSION)   # which law founded this world
        rec = w.rule(rule_id="ZD-TEXTED",
                     text="a human sentence, supplied by the caller",
                     scope="space:root", root=True,
                     polarity="-", then=[{"refuse": "ZD-TEXTED"}])
        for f in ("text", "scope", "root"):
            self.assertNotIn(f, rec["payload"], "the before era wrote %r" % f)
        self.assertEqual([r for r in w.views.root_rules() if r["rule_id"] == "ZD-TEXTED"], [])

    def test_a_bare_call_writes_every_declared_field_and_the_count_is_arithmetic(self):
        """ZC drove NINE keys on a bare call and read the consequence off it: a reader cannot
        tell 'not supplied' from 'supplied as null'. That property is UNCHANGED and only its
        width moved, so it is pinned rather than left to be rediscovered."""
        w = _World()
        rec = w.rule(actor="SYSTEM", rule_id="ZD-BARE")
        d = create_rule_definition(live_pack())
        self.assertEqual(sorted(rec["payload"]), sorted(written_fields(d)))
        self.assertEqual(len(rec["payload"]), 15)
        before = _World(pack_at(BEFORE_COMMIT))
        self.assertEqual(len(before.rule(actor="SYSTEM", rule_id="ZD-BARE")["payload"]), 9)


class TheTierClaimBecameVisible(unittest.TestCase):
    """C2's sharpest consequence, and the one that must not be misread. Driven on BOTH eras.

    A protected tier was never mintable through this op. What changed is WHERE that is
    answered: the claim used to be dropped by the interpreter before any guard saw it, and it
    is now refused BY THE GUARD, recorded, citing the law."""

    def test_the_BEFORE_era_ACCEPTED_the_claim_and_silently_dropped_it(self):
        w = _World(pack_at(BEFORE_COMMIT))
        self.assertEqual(w.founded_under(), BEFORE_VERSION)
        rec = w.rule(actor="SYSTEM", rule_id="law:fake-const", policy_key="z", value=1,
                     tier="constitutional")
        self.assertNotIn("tier", rec["payload"])
        self.assertEqual(w.refusals(), [])

    def test_the_LIVE_era_REFUSES_the_claim_and_RECORDS_the_refusal(self):
        # [DOCUMENTED FLIP — EP-29 W2b, 2026-08-13, charter §A57. CAUSE: a world booted from
        # the LIVE tree now stamps 1.22.0, so the guard here reads a version this class does
        # not describe. ASSERTED: `_World()`. SUPERSEDED: `_World(pack_at(AFTER_COMMIT))`.
        # REMAINS TRUE, and the row stays a genuine two-era comparison rather than one reading
        # wearing two labels: the era pair BEFORE/AFTER is what this class exists to contrast.
        # GIVEN UP: nothing — that the refusal still stands under the LIVE law is carried by
        # this pass's own battery, which boots the live tree and drives its refusals.]
        w = _World(pack_at(AFTER_COMMIT))
        self.assertEqual(w.founded_under(), AFTER_VERSION)
        with self.assertRaises(OpError) as cm:
            w.rule(actor="SYSTEM", rule_id="law:fake-const", policy_key="z", value=1,
                   tier="constitutional")
        self.assertEqual(cm.exception.rule, "BOOT-INT")
        self.assertEqual(len(w.refusals()), 1)
        self.assertNotIn("law:fake-const", w.views.active_rules())

    def test_a_NON_protected_tier_is_accepted_and_written(self):
        """Non-vacuity: the refusal above is about the CLAIM's value, not about `tier` being
        declared. An ordinary tier lands, which is the repair working."""
        w = _World()
        rec = w.rule(actor="SYSTEM", rule_id="law:ordinary-tier", policy_key="z", value=1,
                     tier="ordinary")
        self.assertEqual(rec["payload"]["tier"], "ordinary")

    def test_the_constitution_is_still_unamendable_through_the_system(self):
        w = _World()
        with self.assertRaises(OpError) as cm:
            w.rule(rule_id="CONST-SELF-PROTECT", policy_key="x", value=1)
        self.assertEqual(cm.exception.rule, "BOOT-INT")


class DeclaringScopeOpensNoNewReach(unittest.TestCase):
    """A worry answered by measurement rather than by reasoning: does declaring `scope` give a
    caller a binding reach it did not have? No. The interpreter's GENERAL `space` passthrough
    (opdefs.py:1589-1590) already carried a caller's space into the payload, and both the
    act-space fold and the law-reach test already preferred `scope` over `space`. This pass
    gives the founding's own spelling — 28 of the 42 records use `scope` — to a path that was
    already there."""

    def _scoped(self, pack):
        w = _World(pack)
        w.gate.execute("CREATE-SPACE", "owner",
                       {"name": "space:sub", "parent": w.views.mother_space()})
        rec = w.rule(rule_id="ZD-SCOPED", policy_key="sp", value=1,
                     space="space:sub", scope="space:sub")
        return w, rec

    def test_the_BEFORE_era_already_reached_a_subspace_through_space(self):
        w, rec = self._scoped(pack_at(BEFORE_COMMIT))
        self.assertEqual(w.founded_under(), BEFORE_VERSION)
        self.assertEqual(rec["payload"].get("space"), "space:sub")
        self.assertIsNone(rec["payload"].get("scope"), "the before era wrote scope")
        self.assertEqual(w.gate._act_space(rec, dict(rec["payload"])), "space:sub")
        self.assertNotEqual(w.views.mother_space(), "space:sub")

    def test_the_LIVE_era_reaches_the_SAME_space_and_now_records_the_spelling(self):
        # [DOCUMENTED FLIP — EP-29 W2b, 2026-08-13, charter §A57. CAUSE: the founding moved
        # 1.21.0 -> 1.22.0, so `_scoped(None)` boots a world stamping a version this class
        # does not describe. ASSERTED: `None`, meaning the live tree. SUPERSEDED:
        # `pack_at(AFTER_COMMIT)`. REMAINS TRUE: the scope spelling landed at EP-28ZD's era
        # and is a fact about that era.]
        w, rec = self._scoped(pack_at(AFTER_COMMIT))
        self.assertEqual(w.founded_under(), AFTER_VERSION)
        self.assertEqual(rec["payload"].get("space"), "space:sub")
        self.assertEqual(rec["payload"].get("scope"), "space:sub")
        self.assertEqual(w.gate._act_space(rec, dict(rec["payload"])), "space:sub")


class TheUnchangedBehavioursAreMEASURED(unittest.TestCase):
    """The not-claimed block, driven. A pass that says 'the engine is untouched' and measures
    nothing has made a claim about the thing it did not look at."""

    def test_an_UNDECLARED_name_is_still_dropped_silently_and_the_act_accepted(self):
        """EP-28ZC drive 3. UNCHANGED and deliberately so: the general silent
        acceptance-and-strip is a check-shaped question RAISED to the close, not taken here."""
        w = _World()
        rec = w.rule(actor="SYSTEM", rule_id="ZD-STRAY", not_a_declared_field="x")
        self.assertNotIn("not_a_declared_field", rec["payload"])
        self.assertEqual(w.refusals(), [])

    def test_the_BOOT_INT_untouchables_floor_still_fires_through_polarity_and_when(self):
        """EP-28ZC's fourth probe. It reads two fields off the draft payload, and both were
        among the undeclared seven — so this refusal existed only because the op wrote fields
        it declared nowhere. Declaring them changes nothing about it, measured."""
        w = _World()
        with self.assertRaises(OpError) as cm:
            w.rule(rule_id="ZD-BRICK", polarity="-", when=[{"action": "CREATE-RULE"}])
        self.assertEqual(cm.exception.rule, "BOOT-INT")

    def test_the_op_SET_did_not_move_this_pass(self):
        def ops(pack):
            return {r["payload"]["name"] for st in pack["steps"] for r in st["records"]
                    if r.get("action") == "CREATE-OP"}
        # [DOCUMENTED FLIP — EP-29 W2b, 2026-08-13, charter §A57. CAUSE: W2b adds
        # DECLARE-INTAKE, so the LIVE op set is 75 against this pass's 74. ASSERTED:
        # `live_pack()`. SUPERSEDED: `pack_at(AFTER_COMMIT)`. REMAINS TRUE, and this is the
        # exact class §A57 (1) was repaired for — the row is correct about the world it was
        # written in and only a pass ADDING AN OP falsifies it, which is why adjacency finds
        # the wrong set. GIVEN UP: nothing; W2b asserts its own op delta in its own file.]
        self.assertEqual(ops(pack_at(AFTER_COMMIT)), ops(pack_at(BEFORE_COMMIT)),
                         "this pass added or removed an op; it amends ONE declaration")


# =================================================================================================
# C3 — THE LAW-PASS FLOOR
# =================================================================================================

class TheFoundingMoved(unittest.TestCase):
    """C3. The founding MOVES and BYTE-UNCHANGED IS THE FAILING OUTCOME for a law pass — the
    inverse of EP-28ZB, EP-28ZC and EP-29 W1c, all of which required it byte-unchanged."""

    def test_the_founding_is_NOT_byte_unchanged(self):
        era = era_pin.blob_at(BEFORE_COMMIT, era_pin.PACK_PATH)
        with open(PACK_PATH, "rb") as fh:
            live = fh.read()
        self.assertNotEqual(hashlib.sha256(era).hexdigest(),
                            hashlib.sha256(live).hexdigest(),
                            "the founding is byte-unchanged after a LANDED law pass")

    def test_the_version_moved_exactly_one_MINOR(self):
        # [DOCUMENTED FLIP — EP-29 W2b, 2026-08-13, charter §A57. CAUSE: the founding moved
        # 1.21.0 -> 1.22.0. ASSERTED: `live_pack()` as this pass's AFTER. SUPERSEDED:
        # `pack_at(AFTER_COMMIT)`. REMAINS TRUE: EP-28ZD moved the founding exactly one MINOR,
        # 1.20.0 -> 1.21.0, which is a fact about two commits and never about today's tree —
        # the same correction this pass itself made to EP-29 W1b one pass back.]
        self.assertEqual(pack_at(BEFORE_COMMIT)["founding_version"], BEFORE_VERSION)
        self.assertEqual(pack_at(AFTER_COMMIT)["founding_version"], AFTER_VERSION)

    def test_the_designation_record_carries_the_NEW_version(self):
        # [DOCUMENTED FLIP — EP-29 W2b, 2026-08-13, charter §A57. CAUSE: a world booted from
        # the live tree stamps 1.22.0. ASSERTED: `_World()`. SUPERSEDED:
        # `_World(pack_at(AFTER_COMMIT))`, and the row stays TWO-SIDED — a pack read out of
        # git on one side, a designation stamped by the installer on the other.]
        self.assertEqual(_World(pack_at(AFTER_COMMIT)).founded_under(), AFTER_VERSION)

    def test_the_step_count_did_not_move(self):
        """A MINOR here adds no step: the amend edits one record in place. Stated so a later
        pass reading '25 steps' knows this pass is not why."""
        # [DOCUMENTED FLIP — EP-29 W2b, 2026-08-13, charter §A57. CAUSE: W2b adds TWO steps,
        # 08k-device-intake-ops and 08l-device-intake-declarations, so the live count is 27.
        # ASSERTED: `live_pack()` twice. SUPERSEDED: `pack_at(AFTER_COMMIT)` twice. REMAINS
        # TRUE AND IS NOW LOAD-BEARING IN THE WAY ITS DOCSTRING INTENDED: this row exists so a
        # later reader knows EP-28ZD is not why the step count is what it is, and W2b IS why
        # it moved off 25 — which this flip records at the row rather than leaving to be
        # rediscovered.]
        self.assertEqual(len(pack_at(AFTER_COMMIT)["steps"]),
                         len(pack_at(BEFORE_COMMIT)["steps"]))
        self.assertEqual(len(pack_at(AFTER_COMMIT)["steps"]), 25)


class TheVersionQuestionWasEXECUTEDAndTookMINOR(unittest.TestCase):
    """C3's ruled test, BUILDER-EXECUTED and not reasoned: loads -> MINOR; does not load ->
    MAJOR -> STOP TO THE MENTOR. It answered MINOR on both arms, and both are kept as standing
    rows so anyone later re-checks the answer rather than takes it. MAJOR has never been taken
    in this estate."""

    def test_ARM_1_the_1_20_0_pack_byte_unchanged_STILL_LOADS(self):
        install_module._validate(install_module.records(pack_at(BEFORE_COMMIT)))

    def test_ARM_2_the_42_GENESIS_RECORDS_LOAD_UNDER_THE_AMENDED_DECLARATION(self):
        """The EP's own spelling of the question, and the one that is actually about this
        pass: the amended declaration governs the op, and the 42 rule records must still land
        with the six fields they carry intact."""
        # [DOCUMENTED FLIP — EP-29 W2b, 2026-08-13, charter §A57. CAUSE: W2b declares a 43rd
        # law, so a world booted from the live tree holds 43 CREATE-RULE records. ASSERTED:
        # `_World()`. SUPERSEDED: `_World(pack_at(AFTER_COMMIT))`. REMAINS TRUE: the ruled
        # version test EP-28ZD executed took MINOR over the 42 as they stood at its own close,
        # which is what a ruled test's answer is about. GIVEN UP: nothing — W2b executes the
        # same ruled test over 43 in its own file, and the loader's ability to refuse is
        # driven there against W2b's own new definition.]
        w = _World(pack_at(AFTER_COMMIT))
        recs = [e for e in w.store.all() if e["action"] == "CREATE-RULE"]
        self.assertEqual(len(recs), 42)
        for f, n in THE_SIX.items():
            self.assertEqual(sum(1 for e in recs if f in e["payload"]), n,
                             "%s did not survive the founding" % f)
        self.assertEqual(len(w.views.root_rules()), 19)

    def test_the_loader_that_accepted_them_CAN_REFUSE(self):
        """Without this the two rows above are an instrument that cannot report its own
        failure. The plant is put on THIS op's own definition, so the control exercises the
        record this pass edited rather than some other."""
        p = pack_at(BEFORE_COMMIT)
        for st in p["steps"]:
            for r in st["records"]:
                if (r.get("payload") or {}).get("name") == "CREATE-RULE":
                    r["payload"]["definition"]["checks"] = [
                        {"check": "planted_unknown_kind", "cite": "ROOT-NEG-6"}]
        with self.assertRaises(Exception) as ctx:
            install_module._validate(install_module.records(p))
        self.assertIn("planted_unknown_kind", str(ctx.exception))


class TheEraPinIsSound(unittest.TestCase):
    """§A57 (1a) and `era_pin`'s own cap. The pin is checked BY CONTENT, and the read is the
    ONE home's — this module spawns no git of its own, which `tests/test_ep28z.py`'s census
    enforces suite-wide rather than this file asserting it about itself."""

    def test_the_pin_resolves_to_the_CONTENT_it_claims(self):
        blob = era_pin.blob_at(BEFORE_COMMIT, era_pin.PACK_PATH)
        self.assertEqual(hashlib.sha256(blob).hexdigest(), BEFORE_PACK_SHA)

    def test_the_pin_carries_no_carriage_return(self):
        """The property `tests/test_ep28z.py` checks across the pins it registers. This pin is
        NOT in that registry — and neither is EP-29 W1b's, which is the standing raise that
        the registry claims 'every pin this suite holds' with no mechanism behind it. Checked
        here so this pass's own pin is not the unchecked one, without editing a foreign
        registry to do it."""
        self.assertNotIn(b"\r", era_pin.blob_at(BEFORE_COMMIT, era_pin.PACK_PATH))

    def test_this_modules_pack_at_DELEGATES_to_the_home_rather_than_resembling_it(self):
        """CAUGHT IN THIS FILE'S OWN FIRST DRAFT: the row here read
        `assertIs(era_pin.pack_at, era_pin.pack_at)`, which is a sentence with a colon in it —
        no result could make it speak against the claim (§7.1's first disguise). Delegation is
        checked by SUBSTITUTING the home's reader and requiring this module's answer to move.
        A re-derived local implementation would not move, and would red here."""
        original = era_pin.pack_at
        sentinel = {"founding_version": "SENTINEL-NOT-A-VERSION"}
        try:
            era_pin.pack_at = lambda *a, **k: sentinel
            self.assertIs(pack_at(BEFORE_COMMIT), sentinel,
                          "pack_at does not go through the home — the idiom was re-derived")
        finally:
            era_pin.pack_at = original
        self.assertEqual(pack_at(BEFORE_COMMIT)["founding_version"], BEFORE_VERSION)
        self.assertEqual(era_pin.PACK_PATH, "src/founding/founding-pack.json")


if __name__ == "__main__":
    unittest.main()
