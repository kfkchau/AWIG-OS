# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-28B — the three raised engine items, as the acceptance battery the EP named before code.

  W1  T-RELEASE-RECORDS-NEVER-REFUSES
      A release RECORDS and is never folded for authority (design/10 §11.1c). Both halves,
      because half of it is the whole point: the record must still exist. The exemption is
      shown to be NARROW — it removes the covering-grant fold and nothing else — and the
      DIVERGENCE row drives the silent default: an op that is a release in fact and does not
      declare itself one keeps folding, which is the fallback value differing from the true
      value with the difference visible.
      Plus the LEASH, which arrived in the same round as the power: the `act_kind` vocabulary
      is closed at all three definition doors, a release may not also be attenuation-family,
      and the CLASS ITSELF IS A COUNTABLE — the exact population is pinned, so a fourth member
      cannot arrive without a deliberate edit another seat reads (charter §A25's template: a
      cheap mechanical count checked by a seat other than the one it constrains).

  W2  T-APPEND-IS-DURABLE (the barrier half; the descriptor half is RAISED, not shipped)
      The barrier is `fdatasync`, the buffer is flushed before it, and it is inside the append.
      The durability claim itself is not testable in this suite — it is proven by cutting the
      guest's power, and the evidence lives in `planning/vm/M3-EVIDENCE.md`. What is testable is
      the mechanism that carries it, which is what a later change would have to move
      deliberately.
      HOLDING THE DESCRIPTOR instead of re-opening per append was written and WITHDRAWN in the
      same session, because the `files.close` conformance row's subject is the process's
      descriptor table and the row does not own it. The one-line repair is in the fixture, which
      is outside this EP's fence, so it is raised. The row below states the hold positively
      rather than leaving it as a missing assertion.

  W3  T-VIEWS-NOT-INVALIDATED-BY-UNRELATED-APPEND
      A COUNTABLE, never a duration (the 2026-07-27 standard). The memo for a fold with a
      declared record subset survives an append that cannot change it; the fold body is counted
      rather than the generation key, because a key that moved while the fold was served from
      cache would make the finding imaginary in one direction and a key that did not move while
      the fold recomputed would make it imaginary in the other. Both are counted.
      The DIVERGENCE row here is the memos with NO declared subset: they keep the global
      counter, so they are invalidated by an append the declared ones ignore — the fallback and
      the specialised answer differing, on the same append, measured.

WHY THERE IS NO SPEED ASSERTION IN THIS FILE. design/36 ADDENDUM L measured the entire
per-act fold budget at 13–23% of a gated act and the authority fold at 0.8–1.7%. W1 is worth
0.41–1.07% and is mandatory as CORRECTNESS; W2 and W3 are ordinary engine waste with measured
sizes. A latency assertion here would be a claim about a virtual disk wearing this build's
name, and every figure this EP produced is filed with its substrate in
`planning/build/MEASUREMENTS.md` instead.
"""

import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from kernel import opdefs                                        # noqa: E402
from kernel import store as store_mod                           # noqa: E402
from kernel.compose import build_full_kernel                    # noqa: E402
from kernel.errors import OpError                               # noqa: E402

#: The release class, ENUMERATED — every op whose whole effect is to end something the caller
#: already lawfully holds. Ruled at EP-28B from `design/10` §11.1c and its 2026-07-30 amendment:
#: membership is by OP DEFINITION and not by served capability, which is why `FILE-UNLOCK` is
#: here while no mount serves a lock yet.
#:
#: THIS LIST IS THE GUARD. It is not documentation of the code — the test below compares it
#: against the founding, both ways, so a new declaration with no entry here fails and an entry
#: here with no declaration fails. `COMMS-CLOSE` and `SESSION-CLOSE` were evaluated against
#: §11.1c's test at EP-28B and RAISED rather than declared; the reasons are in that EP's
#: BUILD-PROGRESS entry, and if either is later ruled IN it joins by an edit here plus a
#: founding bump, seen by whoever reviews it.
RELEASE_OPS = ("FILE-CLOSE", "FILE-UNLOCK")


class KernelCase(unittest.TestCase):
    """A disposable founded world per test. Nothing here touches a live world."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep28b-")
        self.rec = os.path.join(self.dir, "rec.jsonl")
        self.store, self.gate, self.views, self.blobs, _ = build_full_kernel(
            self.rec, os.path.join(self.dir, "blobs"))

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def fold_calls(self, fn):
        """Which acts consulted the covering-grant fold. The fold is spied rather than timed:
        a call count is a fact about structure and a duration is a fact about the box."""
        calls = []
        real = self.views.covers

        def spy(account, action, info_kind, space, as_of=None):
            calls.append(action)
            return real(account, action, info_kind, space, as_of=as_of)
        self.views.covers = spy
        try:
            fn()
        finally:
            self.views.covers = real
        return calls

    def definition_of(self, op):
        return (self.views.op_definitions().get(op) or {}).get("definition") or {}

    def narrow_the_world(self):
        """Revoke the founding openness grant IN THIS DISPOSABLE WORLD, so an uncovered actor
        exists to test with. The EP-25 T-CUSTODY-MATRIX pattern; the live world is never
        touched, and the owner's standing word that the world stays OPEN is about the live
        world, not about a temporary directory this test deletes."""
        self.gate.execute("REVOKE", "owner", {"grant_id": "founding-openness"})
        self.assertNotIn("grant:founding-openness", self.views.grants())

    @staticmethod
    def prov(uid=1000):
        return {"asserted_by": "uid:%d" % uid, "source": "kernel-port",
                "could_read": [], "uid": uid}


# =====================================================================================
# W1 — T-RELEASE-RECORDS-NEVER-REFUSES
# =====================================================================================

class TestAReleaseRecords(KernelCase):
    """THE HALF THAT IS EASY TO LOSE. §11.1c exempts a release from the authority FOLD and
    from nothing else: it still crosses the gate, still appends, still cites its rule, still
    replays. An exemption that quietly became "a release is not a governed act" would delete
    the custody span from the record, and replay could no longer reconstruct which descriptors
    were held — which is the reason the class is DECISION and not CACHE."""

    def test_a_release_appends_one_record_citing_its_rule(self):
        self.gate.execute("FILE-CREATE", "owner", {"path": "/r.txt", "perm": "644",
                                                   "provenance": self.prov()})
        before = len(self.store.all())
        rec = self.gate.execute("FILE-CLOSE", "owner", {"path": "/r.txt", "inode": 2,
                                                        "provenance": self.prov()})
        self.assertEqual(len(self.store.all()) - before, 1)
        self.assertEqual(rec["action"], "FILE-CLOSE")
        self.assertEqual(rec["rule_cited"], "FS-LAW-PERM")
        self.assertFalse(rec.get("refused"))

    def test_the_other_release_also_records(self):
        """FILE-UNLOCK is in the class by its DEFINITION, which is what §11.1c's 2026-07-30
        amendment rules, so it is tested as an op rather than through a mount. No mount serves
        a lock today and `T-FLOCK-RECORDS` is red; neither fact bears on this."""
        self.gate.execute("FILE-CREATE", "owner", {"path": "/u.txt", "perm": "644",
                                                   "provenance": self.prov()})
        rec = self.gate.execute("FILE-UNLOCK", "owner", {"path": "/u.txt", "inode": 2,
                                                         "provenance": self.prov()})
        self.assertEqual(rec["action"], "FILE-UNLOCK")
        self.assertEqual(rec["rule_cited"], "FS-LAW-LOCK")

    def test_the_whole_round_trip_over_a_world_founded_with_the_release_class(self):
        """THE ROUND-TRIP, named in the acceptance battery, run over a world whose genesis
        carries the new declaration. Kill every derived structure — a second kernel over the
        same record file starts with nothing built — and every answer reconstructs, the
        declaration included. A field that entered the founding and did not survive replay
        would be a constitution with a fact only its first process ever knew."""
        prov = self.prov()
        self.gate.execute("FILE-CREATE", "owner", {"path": "/rt.txt", "perm": "644",
                                                   "provenance": prov})
        self.gate.execute("FILE-OPEN", "owner", {"path": "/rt.txt", "inode": 2, "flags": 0,
                                                 "provenance": prov})
        self.gate.execute("FILE-CLOSE", "owner", {"path": "/rt.txt", "inode": 2,
                                                  "provenance": prov})
        self.gate.execute("FILE-UNLOCK", "owner", {"path": "/rt.txt", "inode": 2,
                                                   "provenance": prov})

        def snapshot(views, store):
            return {
                "n": len(store.all()),
                "defs": {k: dict(v.get("definition") or {})
                         for k, v in views.op_definitions().items()},
                "rules": sorted(views.active_rules()),
                "packs": sorted(views.category_packs()),
            }
        before = snapshot(self.views, self.store)
        store2, _gate2, views2, _b, _s = build_full_kernel(
            self.rec, os.path.join(self.dir, "blobs2"))
        self.assertEqual(before, snapshot(views2, store2))
        for op in RELEASE_OPS:
            self.assertEqual(
                (views2.op_definitions()[op]["definition"]).get("act_kind"), "release",
                "%s's declared kind did not survive the replay" % op)

    def test_the_release_span_survives_the_round_trip(self):
        """Kill every derived structure, replay from the file alone, and the release is still
        there. The exemption is at the gate's authority step; it never touched the record."""
        self.gate.execute("FILE-CREATE", "owner", {"path": "/r.txt", "perm": "644",
                                                   "provenance": self.prov()})
        self.gate.execute("FILE-OPEN", "owner", {"path": "/r.txt", "inode": 2, "flags": 0,
                                                 "provenance": self.prov()})
        self.gate.execute("FILE-CLOSE", "owner", {"path": "/r.txt", "inode": 2,
                                                  "provenance": self.prov()})
        replayed = store_mod.EventStore(self.rec)
        self.assertEqual([e["action"] for e in replayed.all()],
                         [e["action"] for e in self.store.all()])
        self.assertEqual([e["action"] for e in replayed.all()][-2:],
                         ["FILE-OPEN", "FILE-CLOSE"])


class TestAReleaseNeverRefusesForAuthority(KernelCase):
    """The ruling itself, driven in a world narrow enough for the refusal to be possible."""

    def test_both_releases_succeed_for_an_actor_with_no_covering_chain(self):
        self.gate.execute("FILE-CREATE", "owner", {"path": "/r.txt", "perm": "644",
                                                   "provenance": self.prov()})
        self.narrow_the_world()
        for op in RELEASE_OPS:
            rec = self.gate.execute(op, "uid:1000",
                                    {"path": "/r.txt", "inode": 2, "provenance": self.prov()})
            self.assertEqual(rec["action"], op)
            self.assertFalse(rec.get("refused"), op)

    def test_the_control_the_same_actor_is_refused_for_the_custody_grant(self):
        """A pass above means nothing unless the narrowing bit. FILE-OPEN is the symmetric
        act — the custody GRANT — and it refuses for this actor, cited."""
        self.gate.execute("FILE-CREATE", "owner", {"path": "/r.txt", "perm": "644",
                                                   "provenance": self.prov()})
        self.narrow_the_world()
        with self.assertRaises(OpError) as caught:
            self.gate.execute("FILE-OPEN", "uid:1000",
                              {"path": "/r.txt", "inode": 2, "flags": 0,
                               "provenance": self.prov()})
        self.assertIn(caught.exception.rule, ("ROOT-NEG-1", "ROOT-NEG-3"))

    def test_no_release_consults_the_fold_at_all(self):
        """Not "is permitted" — never asked. The fold is the cost and the divergence; skipping
        the refusal while still paying the fold would close half of §11.1c."""
        self.gate.execute("FILE-CREATE", "owner", {"path": "/r.txt", "perm": "644",
                                                   "provenance": self.prov()})
        calls = self.fold_calls(
            lambda: [self.gate.execute(op, "owner",
                                       {"path": "/r.txt", "inode": 2, "provenance": self.prov()})
                     for op in RELEASE_OPS])
        for op in RELEASE_OPS:
            self.assertNotIn(op, calls)


class TestTheExemptionIsNarrow(KernelCase):
    """DESIGNED FOR THE STRETCH. The exemption's blast radius is one fold, and every other
    thing the gate does to a release still happens. Each row below is a governed property a
    careless widening of the branch would take with it."""

    def test_a_release_of_an_unregistered_op_is_still_a_closure_hit(self):
        with self.assertRaises(OpError) as caught:
            self.gate.execute("FILE-DISCARD", "owner", {"path": "/r.txt"})
        self.assertEqual(caught.exception.rule, "P3-CLOSURE")

    def test_a_release_missing_a_required_parameter_is_still_nonconforming(self):
        with self.assertRaises(OpError) as caught:
            self.gate.execute("FILE-CLOSE", "owner", {"inode": 2})
        self.assertEqual(caught.exception.rule, "AR-2")

    def test_a_recorded_dont_law_still_refuses_a_release(self):
        """The full-form pass runs AFTER the authority step, so an exemption from the fold is
        not an exemption from law. A recorded don't aimed at FILE-CLOSE still stops it, and the
        refusal is itself recorded — which is the difference between exempt-from-a-fold and
        ungoverned."""
        self.gate.execute("FILE-CREATE", "owner", {"path": "/r.txt", "perm": "644",
                                                   "provenance": self.prov()})
        self.gate.execute("CREATE-RULE", "owner",
                          {"rule_id": "TEST-NO-CLOSE", "polarity": "-",
                           "text": "no FILE-CLOSE in this disposable world",
                           "when": [{"action": "FILE-CLOSE"}],
                           "then": [{"refuse": "TEST-NO-CLOSE"}]})
        before = len(self.store.all())
        with self.assertRaises(OpError) as caught:
            self.gate.execute("FILE-CLOSE", "owner", {"path": "/r.txt", "inode": 2,
                                                      "provenance": self.prov()})
        self.assertEqual(caught.exception.rule, "TEST-NO-CLOSE")
        # THE REFUSAL IS ITSELF A RECORD, which is the difference between exempt-from-a-fold
        # and ungoverned. The count is not pinned because the two mutually-blind audit mirrors
        # append their own witnesses to the same act; what is pinned is the refusal.
        after = self.store.all()[before:]
        refusals = [e for e in after if e.get("refused")]
        self.assertEqual(len(refusals), 1)
        self.assertEqual(refusals[0]["rule_cited"], "TEST-NO-CLOSE")

    def test_the_attenuation_leash_is_not_bypassed_by_a_release_declaration(self):
        """The placement half of the belt-and-braces. The branch sits INSIDE the covers arm,
        so a definition that declared itself a release while minting a grant-kind record would
        still meet the attenuation leash. Driven through a real amendment rather than argued:
        an op that mints a grant-kind payload AND declares itself a release is still leashed.
        (The definition-time guard refuses the attenuation-family SPELLING of the same idea;
        this row covers the passthrough spelling, which no vocabulary check can see.)"""
        self.gate.execute("CREATE-OP", "owner", {
            "name": "TEST-RELEASE-PASSTHROUGH",
            "definition": {"description": "a release-declared op that mints a grant record",
                           "act_kind": "release", "law_cited": "CAP-IS-LAW",
                           "params": {"grantee": "required"},
                           "payload_from": ["grantee"],
                           # `grantee`: STRUCTURAL — an actor identity, safe inline (census:
                           # GRANT declares `grantee` structural). This CREATE-OP is ADMIT-
                           # intent; the leash refusal it drives is at the ACT, not the door.
                           "structural_params": ["grantee"],
                           "payload_derive": {"kind": {"tpl": "grant"}},
                           "checks": []}})
        self.narrow_the_world()
        with self.assertRaises(OpError):
            self.gate.execute("TEST-RELEASE-PASSTHROUGH", "uid:1000",
                              {"grantee": "uid:1000", "provenance": self.prov()})


class TestTheDeclarationIsDeclaredAndNotBorrowed(KernelCase):
    """W8's named wrong reference, still refused after the row it warned about was built. The
    cheap route was to spell FILE-CLOSE's `authority_regime` "attenuation-family", which skips
    the fold with zero engine lines and makes the founding say a release is governed by
    attenuation, which is false."""

    def test_the_two_releases_declare_a_kind_and_no_regime(self):
        for op in RELEASE_OPS:
            d = self.definition_of(op)
            self.assertEqual(d.get("act_kind"), "release", op)
            self.assertIsNone(d.get("authority_regime"),
                              "%s borrowed the regime — the shortcut W8 named is refused" % op)

    def test_the_declaration_is_a_field_of_its_own_in_the_founding_bytes(self):
        """Read from the pack on disk, not from the fold, because the claim is about what the
        constitution's source document SAYS."""
        import json
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "..", "src", "founding", "founding-pack.json"),
                  encoding="utf-8") as fh:
            pack = json.load(fh)
        declared = {}
        for step in pack["steps"]:
            for r in step["records"]:
                p = r.get("payload") or {}
                if p.get("kind") == "op_definition":
                    k = (p["definition"] or {}).get("act_kind")
                    if k is not None:
                        declared[p["name"]] = k
        self.assertEqual(declared, {op: "release" for op in RELEASE_OPS})


class TestTheClassIsACountable(KernelCase):
    """CHARTER §A25's CLOSED-INSTANCE TEMPLATE, applied to a vocabulary rather than a rule: a
    cheap mechanical count, checked by a seat other than the one it constrains. The population
    is written down once, above, and compared against the live founding in BOTH directions —
    so a fourth release cannot be declared without an edit here that a reviewer reads, and this
    list cannot name a member the founding does not declare."""

    def test_the_live_population_is_exactly_the_enumerated_one(self):
        live = sorted(name for name, entry in self.views.op_definitions().items()
                      if ((entry or {}).get("definition") or {}).get("act_kind")
                      == opdefs.RELEASE)
        self.assertEqual(live, sorted(RELEASE_OPS))

    def test_no_op_declares_any_other_kind_of_act(self):
        """The vocabulary has exactly one member today. A second kind arriving unnoticed would
        make the closed vocabulary open by accident."""
        kinds = {((entry or {}).get("definition") or {}).get("act_kind")
                 for entry in self.views.op_definitions().values()}
        self.assertEqual(kinds - {None}, {opdefs.RELEASE})
        self.assertEqual(opdefs.ACT_KINDS, ("release",))


class TestTheDivergenceOfTheSilentDefault(KernelCase):
    """THE DIVERGENCE ROW the build-prompt standard requires of any default path. `act_kind`
    has no default and no policy line: silence means "this op has not stated it is a release",
    so the fold runs. That default is not silently correct, and this drives the case where it
    is WRONG — an op whose effect is exactly FILE-CLOSE's, with the declaration removed, keeps
    folding and keeps the ABI divergence §11.1c names. The fallback value and the true value
    DIFFER and the difference is visible: the same act, the same world, two answers."""

    def _twin_without_the_declaration(self):
        """A twin of FILE-CLOSE, identical in every recorded effect, silent about its kind."""
        d = dict(self.definition_of("FILE-CLOSE"))
        d.pop("act_kind")
        d["description"] = "a release that does not say so — the divergence subject"
        self.gate.execute("CREATE-OP", "owner",
                          {"name": "TEST-CLOSE-UNDECLARED", "definition": d})
        return "TEST-CLOSE-UNDECLARED"

    def test_the_undeclared_twin_folds_where_the_declared_one_does_not(self):
        """Driven as `uid:1000` and not as the owner, because the chain-end is exempt from the
        whole authority step and would show no fold for either op — a green row proving
        nothing. The world stays OPEN here, so both acts SUCCEED and the only difference
        measured is whether the fold was consulted."""
        twin = self._twin_without_the_declaration()
        self.gate.execute("FILE-CREATE", "owner", {"path": "/r.txt", "perm": "644",
                                                   "provenance": self.prov()})
        calls = self.fold_calls(lambda: [
            self.gate.execute("FILE-CLOSE", "uid:1000", {"path": "/r.txt", "inode": 2,
                                                         "provenance": self.prov()}),
            self.gate.execute(twin, "uid:1000", {"path": "/r.txt", "inode": 2,
                                                 "provenance": self.prov()})])
        self.assertNotIn("FILE-CLOSE", calls)
        self.assertIn(twin, calls)

    def test_the_undeclared_twin_refuses_where_posix_forbids_refusal(self):
        """The consequence of the divergence, stated as the ABI answer it produces. Same
        narrowed world, same act, and the twin refuses because nothing declared what it is."""
        twin = self._twin_without_the_declaration()
        self.gate.execute("FILE-CREATE", "owner", {"path": "/r.txt", "perm": "644",
                                                   "provenance": self.prov()})
        self.narrow_the_world()
        rec = self.gate.execute("FILE-CLOSE", "uid:1000",
                                {"path": "/r.txt", "inode": 2, "provenance": self.prov()})
        self.assertFalse(rec.get("refused"))
        with self.assertRaises(OpError) as caught:
            self.gate.execute(twin, "uid:1000",
                              {"path": "/r.txt", "inode": 2, "provenance": self.prov()})
        self.assertIn(caught.exception.rule, ("ROOT-NEG-1", "ROOT-NEG-3"))


class TestTheLeashArrivedWithThePower(KernelCase):
    """DESIGN-SOUL §2: every new power arrives with its own leash in the same round. The power
    is a field that removes a governance fold; the leash is that the field's vocabulary is
    CLOSED and refused at definition time, at all three doors, and that a self-contradicting
    declaration is unrepresentable rather than merely unlikely."""

    def _create(self, name, **extra):
        # `path`: STRUCTURAL — a namespace path is a governance field safe inline (census:
        # every file op classifies `path` structural), and this op's own shape declares it
        # inline via `object_param`-less `payload_from`. [design/46 member-2 vocabulary door,
        # archi :2956 RULING 1: classify per field by true nature.] The refusal fixtures below
        # (misspelt/both-kinds) refuse at the act_kind leash, which runs before this door.
        d = {"description": "a probe", "law_cited": "CAP-IS-LAW",
             "params": {"path": "required"}, "payload_from": ["path"], "checks": [],
             "structural_params": ["path"]}
        d.update(extra)
        return self.gate.execute("CREATE-OP", "owner", {"name": name, "definition": d})

    def test_an_unknown_kind_is_refused_at_create_op(self):
        with self.assertRaises(OpError) as caught:
            self._create("TEST-MISSPELT", act_kind="relase")
        self.assertEqual(caught.exception.rule, "AR-2")
        self.assertNotIn("TEST-MISSPELT", self.views.op_definitions())

    def test_an_unknown_kind_is_refused_at_amend_op(self):
        """The second door. A guard at two of three doors guards nothing (EP-27B's lesson),
        and an op can acquire a field by amendment as easily as at birth."""
        self._create("TEST-AMENDABLE")
        d = dict(self.definition_of("TEST-AMENDABLE"))
        d["act_kind"] = "disposal"
        with self.assertRaises(OpError) as caught:
            self.gate.execute("AMEND-OP", "owner",
                              {"name": "TEST-AMENDABLE", "definition": d})
        self.assertEqual(caught.exception.rule, "AR-2")
        self.assertIsNone(self.definition_of("TEST-AMENDABLE").get("act_kind"))

    def test_an_unknown_kind_is_refused_at_the_founding_door(self):
        """The third door, which validated nothing until EP-27B and is the one a later
        campaign's seeded definition arrives through. Driven against the installer's own door
        object, with the real vocabulary function."""
        from founding.install import _FoundingDoor, FoundingIntegrityError
        door = _FoundingDoor("step 08-op-definitions", "TEST-SEEDED")
        with self.assertRaises(FoundingIntegrityError) as caught:
            opdefs.validate_definition_shape(
                door, "founding", "PC_RUNTIME", "TEST-SEEDED",
                {"law_cited": "CAP-IS-LAW", "act_kind": "relinquish", "checks": []})
        self.assertIn("act_kind", str(caught.exception))

    def test_a_release_may_not_also_be_attenuation_family(self):
        """The contradiction made unrepresentable. The attenuation family WRITES the power
        structure, and an op that releases and also does something else is not a release."""
        with self.assertRaises(OpError) as caught:
            self._create("TEST-BOTH", act_kind="release",
                         authority_regime="attenuation-family")
        self.assertEqual(caught.exception.rule, "AR-2")

    def test_a_well_formed_declaration_still_passes_the_door(self):
        """THE CONTROL. A guard that refuses everything is not a guard. A new op declaring
        itself a release, truthfully, is admitted and is exempted — which is also the proof
        that the class is populated by DEFINITION and needs no engine change to grow."""
        self._create("TEST-LAWFUL-RELEASE", act_kind="release")
        self.gate.execute("FILE-CREATE", "owner", {"path": "/r.txt", "perm": "644",
                                                   "provenance": self.prov()})
        self.narrow_the_world()
        rec = self.gate.execute("TEST-LAWFUL-RELEASE", "uid:1000",
                                {"path": "/r.txt", "provenance": self.prov()})
        self.assertFalse(rec.get("refused"))


# =====================================================================================
# W2 — T-APPEND-IS-DURABLE-AND-THE-DESCRIPTOR-IS-HELD
# =====================================================================================

class TestTheAppendIsStillTheCommit(KernelCase):
    """THE BARRIER, and what is pinned is the MECHANISM rather than a duration.

    W8's sentence rules this section and is carried verbatim: the sync is not a cost to trade,
    it is what makes the record exist. An append that is not durable is not an append. So the
    barrier moved from `fsync` to `fdatasync` — which asks the disk for the data and the file
    size instead of the data, the size and the inode timestamps no reader of an append-only
    record needs — and nothing about the durability was traded for it. The durability CLAIM is
    proven by cutting the guest's power, not here; the evidence is in
    `planning/vm/M3-EVIDENCE.md`, re-taken on a world that survives a reboot.

    W2's OTHER HALF, holding the descriptor instead of re-opening per append, is RAISED AND NOT
    SHIPPED. It was written and withdrawn in the same session: the `files.close` conformance
    row's subject is that closing a released descriptor NUMBER returns EBADF, the fixture appends
    a record between that row's two closes, and a lazily opened write descriptor claims exactly
    the number the first close freed. The repair is one line in the fixture, which is outside
    this EP's fence. `tests/test_ep28_w8.py`'s per-append-open pin therefore STANDS unflipped,
    and the row below states the same fact positively so a reader of this file is not left to
    infer a hold from an absence."""

    def test_the_barrier_is_inside_the_append_and_is_fdatasync(self):
        """THE BARRIER IS INSIDE THE ACT, and the act is what a caller waits on.

        RE-AIMED TO THE ACT'S BOUNDARY [DOCUMENTED FLIP, EP-28G, 2026-08-03, mapped to the
        publish/await split]. The row used to bracket `store._append`, on the premise that
        the gate calls it — and the premise ended when EP-28G separated publication from the
        durability wait, because the gate must hold the decide region across the first and
        must not hold it across the second, so it calls `_publish` and then `_await_durable`.
        Bracketing `_append` after that measures a function nothing on this path calls.

        THE PROPERTY IS UNCHANGED AND THE SUBJECT IS STRICTLY BETTER. Invariant 1 is that no
        reply releases before the sync covering its record, and the reply a caller sees is
        `gate.execute` returning — never an internal append returning. So the bracket moved
        to the boundary the invariant is actually about. `store._append` still syncs before
        it returns, for every caller that uses it, and `test_ep28c_w1` asserts that."""
        order = []
        real_fdatasync = store_mod.os.fdatasync

        def spy_sync(fd):
            order.append("fdatasync")
            return real_fdatasync(fd)
        store_mod.os.fdatasync = spy_sync
        order.append("enter")
        try:
            self.gate.execute("FILE-CREATE", "owner", {"path": "/d.txt", "perm": "644",
                                                       "provenance": self.prov()})
        finally:
            store_mod.os.fdatasync = real_fdatasync
        order.append("return")
        self.assertEqual(order, ["enter", "fdatasync", "return"])
        self.assertEqual(order.count("fdatasync"), 1,
                         "the act issued %d barriers — one act, one covering barrier"
                         % order.count("fdatasync"))

    def test_the_buffer_is_flushed_before_the_barrier(self):
        """The ordering that makes the barrier real. Python buffers the write; a barrier issued
        before the buffer reaches the kernel would sync nothing and report success — a wrong
        answer in the costume of a right one, in the one place the estate can least afford it.

        RE-AIMED AT BEHAVIOUR [EP-28H item 5, 2026-08-02, a documented flip mapped to EP-28C's
        HELD W1]. REFUTED VEHICLE, RETAINED so the correction is readable against what it
        corrects: this row used to slice `store.py`'s own source from the literal
        `with self.file_path.open("a"` to `record = _freeze(record)` and assert that
        `f.flush()` appeared before `os.fdatasync(f.fileno())` in that text. EP-28C W1 moved
        the barrier to the batch boundary and W3 gave the store a held descriptor, so the
        `with` form is gone and `str.index` raised — WHILE THE PROPERTY WAS NEVER BROKEN.

        A ROW THAT ASSERTS SOURCE TEXT BREAKS ON EVERY LAWFUL REFACTOR AND SAYS NOTHING ABOUT
        THE PROPERTY IT NAMES, so the literal is not repaired: the row asks the question the
        property is actually about. WHEN THE BARRIER IS ISSUED, IS THE RECORD ALREADY IN THE
        FILE? Read through an INDEPENDENT descriptor opened inside the barrier itself, so the
        answer comes from the kernel rather than from this process's buffer — a store that
        synced before flushing would be syncing a file the record had not reached, and this
        read would not find it."""
        seen = []
        real_fdatasync = store_mod.os.fdatasync

        def spy_sync(fd):
            with open(self.rec, encoding="utf-8") as fh:
                seen.append(fh.read())
            return real_fdatasync(fd)

        store_mod.os.fdatasync = spy_sync
        try:
            rec = self.gate.execute("FILE-CREATE", "owner", {"path": "/f.txt", "perm": "644",
                                                             "provenance": self.prov()})
        finally:
            store_mod.os.fdatasync = real_fdatasync
        self.assertTrue(seen, "no barrier was issued at all, so there was no ordering to check")
        self.assertIn('"record_id":"%s"' % rec["record_id"], seen[-1],
                      "the barrier was issued while the record was still in user space")

    def test_every_record_reaches_the_file_whole_and_replays(self):
        """Twenty records, read back by a second store over the same file: the two agree
        exactly. No truncation, no lost newline — the weaker barrier still forces the data and
        the size, which is precisely what a reader needs to find a line and read it whole."""
        before = [e["seq"] for e in self.store.all()]
        for i in range(20):
            self.store._append({"actor": "SYSTEM", "action": "probe",
                                "rule_cited": "M1-OBSERVATION", "payload": {"i": i}})
        replayed = store_mod.EventStore(self.rec)
        self.assertEqual([e["seq"] for e in replayed.all()],
                         before + list(range(len(before) + 1, len(before) + 21)))
        self.assertEqual([e["action"] for e in replayed.all()],
                         [e["action"] for e in self.store.all()])

    def test_there_is_no_rescue_path_to_the_stronger_barrier(self):
        """ST-A, no silent fallbacks, at the one place it would be most tempting. A store whose
        barrier depends on which branch it took has two durability contracts and no way to say
        which one a given record got."""
        with open(store_mod.__file__, encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn("os.fdatasync(f.fileno())", src)
        self.assertNotIn("os.fsync", src)
        self.assertNotIn('getattr(os, "fdatasync"', src)

    def test_the_held_descriptor_half_landed(self):
        """FLIPPED (EP-28C W3, 2026-08-01), TOGETHER WITH ITS TWIN in `tests/test_ep28_w8.py`
        (`test_the_record_file_is_opened_once_and_held`). THE FLIP IS THE EVIDENCE, and the
        row that stood here named its own expiry: *the descriptor half landed after all —
        then flip this row and the W8 pin together, and say so.* It landed; this says so.

        The descriptor half was raised at EP-28B rather than shipped, because the conformance
        fixture claimed the descriptor number a `files.close` row had just freed. EP-28D
        repaired the fixture, drove both directions, and carried the change to EP-28C. Three
        appends now open the record file ZERO times, because the store opened it once when it
        first had something to write and has held it since."""
        opens = []
        real = store_mod.Path.open

        def spy(self_path, *a, **k):
            if str(self_path).endswith("rec.jsonl"):
                opens.append(a[0] if a else k.get("mode"))
            return real(self_path, *a, **k)
        store_mod.Path.open = spy
        try:
            for i in range(3):
                self.store._append({"actor": "SYSTEM", "action": "probe",
                                    "rule_cited": "M1-OBSERVATION"})
        finally:
            store_mod.Path.open = real
        self.assertEqual(opens, [],
                         "three appends re-opened the record file %d times — the descriptor "
                         "half did not land" % len(opens))


# =====================================================================================
# W3 — T-VIEWS-NOT-INVALIDATED-BY-UNRELATED-APPEND
# =====================================================================================

class ViewsCase(KernelCase):
    """Counting helpers. Every assertion in this section is a COUNTABLE — recomputations, never
    milliseconds (the 2026-07-27 standard). A timing assertion here would pass on a fast box,
    fail on a loaded one, get marked flaky, and the property would be open again under a green
    suite."""

    def counted(self, fold):
        """Count how many times a fold's BODY runs. The body and not the generation key: a key
        that moved while the fold was served from cache would make a finding imaginary in one
        direction, and a key that stood still while the fold recomputed would make the FIX
        imaginary in the other. The body is the only thing that settles both."""
        runs = []
        real = getattr(self.views, "_" + fold)

        def spy(as_of=None, source=None):
            runs.append(1)
            return real(as_of, source)
        setattr(self.views, "_" + fold, spy)
        self.addCleanup(lambda: setattr(self.views, "_" + fold, real))
        return runs

    def custody_traffic(self, n=10):
        """Records the per-act path generates and that no per-act fold can depend on."""
        for i in range(n):
            self.gate.execute("FILE-OPEN", "owner", {"path": "/w.txt", "inode": 2, "flags": 0,
                                                     "provenance": self.prov()})
            self.gate.execute("FILE-CLOSE", "owner", {"path": "/w.txt", "inode": 2,
                                                      "provenance": self.prov()})


class TestTheFoldsSurviveUnrelatedTraffic(ViewsCase):
    """THE ACCEPTANCE ROW. ADDENDUM C's guard raised to the altitude of the law it was written
    for: the law is that a fold on the gate's per-act path does not grow with record count, and
    a memo invalidated by unrelated traffic reintroduces the growth by a route the subset test
    never looks at. The subset being right and the invalidation being wrong are different
    things, and this is the second one."""

    def setUp(self):
        super().setUp()
        self.gate.execute("FILE-CREATE", "owner", {"path": "/w.txt", "perm": "644",
                                                   "provenance": self.prov()})

    def test_no_per_act_fold_recomputes_across_twenty_custody_records(self):
        for fold in sorted(self.views.PER_ACT_FOLDS):
            getattr(self.views, fold)()
        runs = {fold: self.counted(fold) for fold in sorted(self.views.PER_ACT_FOLDS)}
        self.custody_traffic(10)
        for fold in sorted(self.views.PER_ACT_FOLDS):
            getattr(self.views, fold)()
            self.assertEqual(len(runs[fold]), 0,
                             "%s re-derived itself across custody traffic it cannot depend on"
                             % fold)

    def test_the_column_can_fail_a_record_in_the_subset_does_recompute(self):
        """A guard that cannot fail is not a guard. One record per fold, chosen as the thing
        that fold's own predicate selects, and each fold recomputes for its own and for no
        other — which also shows the three generations are independent rather than one counter
        with a new name."""
        for fold in sorted(self.views.PER_ACT_FOLDS):
            getattr(self.views, fold)()
        runs = {fold: self.counted(fold) for fold in sorted(self.views.PER_ACT_FOLDS)}
        self.gate.execute("CREATE-RULE", "owner", {"rule_id": "PROBE-LAW", "polarity": "-",
                                                   "when": [], "then": []})
        for fold in sorted(self.views.PER_ACT_FOLDS):
            getattr(self.views, fold)()
        self.assertGreater(len(runs["active_rules"]), 0,
                           "a law record did not invalidate the law fold")
        self.assertEqual(len(runs["category_packs"]), 0,
                         "a law record invalidated the vocabulary fold")

    def test_the_answers_are_identical_to_the_unaccelerated_fold_after_the_traffic(self):
        """The memo is an ACCELERATION or it does not ship (P2). After the traffic that no
        longer invalidates it, every memoised answer still equals the answer computed from the
        record with no memo at all — so nothing is being served that the record contradicts."""
        served = {fold: getattr(self.views, fold)()
                  for fold in sorted(self.views.PER_ACT_FOLDS)}
        self.custody_traffic(10)
        for fold, answer in served.items():
            self.assertEqual(answer, self.views.view_fold(fold),
                             "%s served an answer the record does not compute" % fold)
            self.assertEqual(answer, self.views.view_fold(fold, accelerated=False),
                             "%s disagrees with the whole-record oracle" % fold)

    def test_killing_the_memo_changes_no_answer(self):
        """Round-trip law on this surface: delete every derived structure and recompute."""
        self.custody_traffic(3)
        before = {fold: getattr(self.views, fold)()
                  for fold in sorted(self.views.PER_ACT_FOLDS)}
        self.views._memo.clear()
        self.views._subset_gens.clear()
        for name in list(self.store._projections):
            self.store._projections[name].kill()
        after = {fold: getattr(self.views, fold)()
                 for fold in sorted(self.views.PER_ACT_FOLDS)}
        self.assertEqual(before, after)


class TestTheUndeclaredMemosKeepTodaysBehaviour(ViewsCase):
    """THE DIVERGENCE ROW for W3's default path. Three memos declare no record subset —
    `founding_prefix`, `accounts`, `chain_end` — and they fall back to the global append
    generation, so they are invalidated by an append the declared folds ignore. The fallback and
    the specialised answer DIFFER, on the same append, and this measures the difference rather
    than asserting that it is harmless.

    Silence meaning "everything invalidates me" is the closed direction on purpose: a fold
    nobody has analysed is never quietly exempted, so the cost of not analysing one is a
    recompute and never a stale answer."""

    UNDECLARED = ("founding_prefix", "accounts", "chain_end")

    def test_the_undeclared_memos_are_still_invalidated_by_every_append(self):
        self.gate.execute("FILE-CREATE", "owner", {"path": "/w.txt", "perm": "644",
                                                   "provenance": self.prov()})
        for name in self.UNDECLARED:
            self.assertNotIn(name, self.views.PER_ACT_FOLDS)
        before = {name: self.views._generation_of(name) for name in self.UNDECLARED}
        declared_before = {f: self.views._generation_of(f)
                           for f in self.views.PER_ACT_FOLDS}
        self.custody_traffic(2)
        for name in self.UNDECLARED:
            self.assertGreater(self.views._generation_of(name), before[name],
                               "%s stopped being invalidated — it declares no subset, so the "
                               "closed answer is that it recomputes" % name)
        for fold, gen in declared_before.items():
            self.assertEqual(self.views._generation_of(fold), gen,
                             "%s moved on custody traffic" % fold)

    def test_an_undeclared_memo_recomputes_where_a_declared_one_does_not(self):
        """The divergence driven through the fold bodies, not the counters. `accounts` reads the
        whole record and is invalidated; `active_rules` reads a subset and is not. Same append."""
        self.gate.execute("FILE-CREATE", "owner", {"path": "/w.txt", "perm": "644",
                                                   "provenance": self.prov()})
        self.views.accounts()
        self.views.active_rules()
        law_runs = self.counted("active_rules")
        acct_runs = []
        real = self.views._accounts

        def spy(as_of=None):
            acct_runs.append(1)
            return real(as_of)
        self.views._accounts = spy
        try:
            self.custody_traffic(1)
            self.views.accounts()
            self.views.active_rules()
        finally:
            self.views._accounts = real
        self.assertGreater(len(acct_runs), 0, "the undeclared memo did not recompute")
        self.assertEqual(len(law_runs), 0, "the declared memo recomputed")


class TestNoSecondRecognitionRuleWasWritten(ViewsCase):
    """EP-24B's one-implementation law, applied one layer up. The invalidation consults the SAME
    predicate the projection selects on, so a divergence between the subset and the invalidation
    is not merely unlikely — there is no second opinion for it to be a divergence from. Checked
    structurally, because that is the only way to check "there is no second implementation"."""

    def test_the_invalidation_reads_the_projections_own_predicates(self):
        from kernel import store as sm
        from kernel import views as vm
        for fold, projection in self.views.PER_ACT_FOLDS.items():
            self.assertIn(projection, sm.PROJECTIONS, fold)
        with open(vm.__file__, encoding="utf-8") as fh:
            src = fh.read()
        body = src[src.index("    def _bump("):src.index("    def _generation_of(")]
        self.assertIn("PROJECTIONS[projection]._selects(e)", body)
        for own in ("rule_id", "category_pack", "CREATE-OP", "action ==", "payload"):
            self.assertNotIn(own, body,
                             "the invalidation grew its own recognition rule (%r) — that is a "
                             "second opinion about what a law record is" % own)

    def test_every_declared_fold_has_a_generation_and_no_others_do(self):
        for fold in sorted(self.views.PER_ACT_FOLDS):
            self.views._generation_of(fold)
        self.gate.execute("CREATE-RULE", "owner", {"rule_id": "PROBE-2", "polarity": "-",
                                                   "when": [], "then": []})
        self.assertEqual(set(self.views._subset_gens), set(self.views.PER_ACT_FOLDS))


class TestTheMemoIsBoundedByFoldsAndNotByTraffic(ViewsCase):
    """The 64-entry clear-everything cap is gone and this is why that is safe rather than a leak.
    One live entry per memoised fold: a superseded key is dropped when its replacement is
    stored. Under the old cap, traffic would have cleared the very memos W3 exists to keep,
    roughly every sixty appends — the fix would have looked like it was working while delivering
    a fraction of what it claims, which is the class of defect this estate calls a wrong answer
    in the costume of a right one."""

    def test_the_memo_never_holds_two_entries_for_one_fold(self):
        self.gate.execute("FILE-CREATE", "owner", {"path": "/w.txt", "perm": "644",
                                                   "provenance": self.prov()})
        names = []
        for i in range(40):
            self.gate.execute("CREATE-RULE", "owner", {"rule_id": "PROBE-%d" % i,
                                                       "polarity": "-", "when": [], "then": []})
            self.views.active_rules()
            self.views.accounts()
            names = [k.rsplit(":", 1)[0] for k in self.views._memo]
            self.assertEqual(len(names), len(set(names)),
                             "the memo holds two generations of one fold: %r" % names)
        self.assertLessEqual(len(self.views._memo), 8)

    def test_the_key_shape_still_carries_the_generation(self):
        """`tests/test_ep24b.py` guards that no authority fold's answer is memoised by reading
        these keys with a `<fold>:` prefix. A bare-name key would have made that guard stop
        matching silently, which is why the shape is pinned here rather than left to habit."""
        self.views.active_rules()
        self.assertTrue(all(":" in k and k.rsplit(":", 1)[1].isdigit()
                            for k in self.views._memo), dict(self.views._memo).keys())


if __name__ == "__main__":
    unittest.main()
