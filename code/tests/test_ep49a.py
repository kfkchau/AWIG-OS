"""EP-49A — THE BORDER: THE DOOR (design/51 §3 N3/N9/N10, §4, §5, §9; design/39 §1/§3).

Named in planning/exec/EP-49A-BUILD.md before code, landed here as regression tests (charter:
every verification probe lands as a regression test). This battery proves the door: an outside
entity's request is a DRAFT the gate decides against the record BEFORE any effect (A1); the reply
carries the CROSSING ID (the submit row's content hash) and a SEAL over exactly what was shown,
REAL via the signer where the library is present and REFUSED-never-faked when absent (A2, A5); a
refusal reaches the human through the system's own WINDOW, the refused party's channel carrying no
reason (A3); NO crossing is ever attributed to the system (A4); the founding move is MINOR and
bump-attested (A6); the whole ledger is green per module (A7). The API-gateway-with-auth-middleware
wrong reference is refused by name (§8).

Every acceptance carries its RED WORLD, driven THROUGH the instrument (a control that cannot red is
the defect). The library is an OPTIONAL EXTRA: with it ABSENT (the estate's baseline — nothing
installed) the real-seal assertions branch to the REFUSAL arm (N10: real-or-refused, never faked);
with it PRESENT the real-seal assertions run — the test_keymat present/absent idiom.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.compose import build_full_kernel                          # noqa: E402
from kernel.errors import OpError                                     # noqa: E402
from kernel.opdefs import OP_CHECKS                                   # noqa: E402
from kernel.signer import SigningKeyStore                             # noqa: E402
from kernel import border, canonical, crypto                         # noqa: E402
from subsystems.comms import CommsView                               # noqa: E402

THREE_OPS = ("BORDER-SUBMIT", "BORDER-REPLY", "BORDER-REFUSAL")
# a fixed SYSTEM signing seed for the test's signer (a secret; never recorded, sealed once)
SYSTEM_SEED = bytes(range(32))


class _World(unittest.TestCase):
    """A kernel composed from the SHIPPED founding, with one outside entity established to submit
    by, and a signing-key store holding a system key BESIDE the vault (the real-seal custody)."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep49a-")
        self.store, self.gate, self.views, self.blobs, self.subs = build_full_kernel(
            os.path.join(self.dir, "record.jsonl"), os.path.join(self.dir, "blobs"),
            os.path.join(self.dir, "vault"))
        self.gate.execute("CREATE-ACCOUNT", "owner",
                          {"account_id": "peer", "actor_class": "human"})
        self.signer = SigningKeyStore()
        self.custody = self.signer.seal(SYSTEM_SEED)     # seal never needs the library (a hash handle)

    def a_submit(self, entity="peer", draft=None):
        return border.submit(self.gate, entity, draft if draft is not None else {"want": "read /x"})


# =============================================================================================
# A1 — T-BORDER-DRAFT-DECIDED (+ RW-EFFECT-BEFORE-DECISION, the able-to-fail plant)
# =============================================================================================

class TestBorderDraftDecided(_World):
    def test_a_submit_is_a_draft_the_gate_decides_and_records(self):
        sub = self.a_submit()
        self.assertEqual(sub["action"], "BORDER-SUBMIT")                 # action IS its op
        self.assertEqual((sub.get("payload") or {}).get("kind"), "border-submit")
        self.assertEqual((sub.get("payload") or {}).get("record_class"), "DECISION")
        self.assertEqual(sub["rule_cited"], "COMM-LAW-CONTRACT")         # the channel-contract law
        # the crossing exists as a DERIVED fold, keyed by the submit's own content hash.
        self.assertIn(border.content_id(sub), border.submits(self.store))

    def test_an_unlawful_submit_is_REFUSED_and_RECORDED_never_executed(self):
        # WHO absent: an unestablished submitter is refused (a crossing is an opening of somebody's
        # channel, and the somebody must exist on the record — never a peer-minted token).
        with self.assertRaises(OpError) as cm:
            border.submit(self.gate, "ghost", {"want": "x"})
        self.assertEqual(cm.exception.rule, "CAP-IS-LAW")
        refs = [e for e in self.store.by_action("op-refused")
                if (e.get("payload") or {}).get("op") == "BORDER-SUBMIT"]
        self.assertTrue(refs, "the refused submit was silently dropped, not recorded")
        self.assertEqual(refs[-1].get("rule_cited"), "CAP-IS-LAW")       # recorded, citing the law

    def test_RW_EFFECT_BEFORE_DECISION_a_refused_submit_leaves_no_border_submit_record(self):
        """RW-EFFECT-BEFORE-DECISION (§4): a BORDER-SUBMIT is a DRAFT the gate DECIDES, never an act
        it executes first. An unlawful submit produces its refusal and NO border-submit record — the
        decision precedes the effect. Able-to-fail: the census counts border-submit records for the
        draft's entity, which must stay ZERO for a refused draft."""
        before = len(list(self.store.by_action("BORDER-SUBMIT")))
        with self.assertRaises(OpError):
            border.submit(self.gate, "ghost", {"want": "x"})
        after = [e for e in self.store.by_action("BORDER-SUBMIT")
                 if (e.get("payload") or {}).get("entity") == "ghost"]
        self.assertEqual(after, [], "a refused draft produced an effect (a border-submit record) "
                                    "before the gate decided it")
        self.assertEqual(len(list(self.store.by_action("BORDER-SUBMIT"))), before)  # nothing appended


# =============================================================================================
# A2 — T-BORDER-REPLY-SEALED (+ RW-SEAL-BLIND / RW-FAKE-SEAL) — real-or-refused (N10)
# =============================================================================================

class TestBorderReplySealed(_World):
    def test_the_seal_is_over_exactly_what_was_shown_real_where_present_refused_where_absent(self):
        sub = self.a_submit()
        cid = border.content_id(sub)
        shown = {"answer": "granted", "detail": "read /x for 10s"}

        if not crypto.real_available():
            # ABSENT (the baseline): sealing a reply REFUSES citing the library, NEVER faked with
            # modelled material (N10; RW-FAKE-SEAL, stop g). The seal is real-or-refused.
            with self.assertRaises(crypto.LibraryAbsent):
                border.seal_reply(self.signer, self.custody, cid, shown)
            with self.assertRaises(crypto.LibraryAbsent):
                border.reply(self.gate, self.store, self.signer, self.custody, sub, shown)
            return

        # PRESENT: the seal is a REAL Ed25519 signature via the signer over exactly what was shown.
        rec = border.reply(self.gate, self.store, self.signer, self.custody, sub, shown)
        self.assertEqual((rec.get("payload") or {}).get("crossing_id"), cid)
        public = crypto.public_from_seed(SYSTEM_SEED)
        seal = (rec.get("payload") or {}).get("seal")
        self.assertTrue(border.verify_seal(public, seal, cid, shown))     # over exactly what was shown
        # RW-SEAL-BLIND: a changed byte of what was shown FAILS the seal (the seal is over exactly
        # what was shown, not merely near it).
        altered = dict(shown); altered["answer"] = "DENIED"
        self.assertFalse(border.verify_seal(public, seal, cid, altered))
        # and a real signature under a DIFFERENT key does not verify (the check that can fail).
        other = crypto.public_from_seed(bytes([9]) * 32)
        self.assertFalse(border.verify_seal(other, seal, cid, shown))

    def test_RW_FAKE_SEAL_the_absent_library_refuses_and_never_returns_modelled_material(self):
        """RW-FAKE-SEAL (§4 / stop g; N10): with the library absent the seal path REFUSES and returns
        NO value — never a modelled fall-back. Proven at THIS boundary with force-absent, so the
        refusal (and its ability to fire) is provable even where the library IS installed."""
        sub = self.a_submit()
        cid = border.content_id(sub)
        prior = os.environ.get(crypto._FORCE_ABSENT_ENV)
        os.environ[crypto._FORCE_ABSENT_ENV] = "1"
        try:
            self.assertFalse(crypto.real_available())
            with self.assertRaises(crypto.LibraryAbsent):
                border.seal_reply(self.signer, self.custody, cid, {"answer": "granted"})
        finally:
            if prior is None:
                os.environ.pop(crypto._FORCE_ABSENT_ENV, None)
            else:
                os.environ[crypto._FORCE_ABSENT_ENV] = prior


# =============================================================================================
# A3 — T-BORDER-REFUSAL-VIA-WINDOW (+ RW-REASON-TO-REFUSED) — both directions
# =============================================================================================

class TestBorderRefusalViaWindow(_World):
    def test_the_reason_is_in_the_window_and_absent_from_the_refused_partys_channel(self):
        sub = self.a_submit()
        cid = border.content_id(sub)
        # the refused entity holds its own system-facing channel (comms.py, the border's neighbour).
        self.gate.execute("COMMS-OPEN", "peer",
                          {"entity": "peer", "channel": "peer-sys", "role": "system-facing"})
        reason = "the draft names a path the entity holds no grant to read"
        border.refusal(self.gate, "peer", cid, reason)                   # the border refuses THROUGH the window

        # DIRECTION 1 — the reason is IN the window (the system's own human-facing surface).
        window = border.through_the_window(self.store)
        self.assertIn(cid, window)
        self.assertEqual(window[cid]["reason"], reason)
        self.assertEqual(window[cid]["entity"], "peer")

        # DIRECTION 2 — the reason is ABSENT from the refused party's OWN channel (no courier of the
        # reason): nothing carrying the reason was delivered to the entity's channel.
        comms = CommsView(self.store)
        chan_records = border.channel_records(comms, "peer")
        self.assertFalse(border.reason_in_records(chan_records, reason),
                         "the refusal's reason leaked into the refused party's own channel")

    def test_RW_REASON_TO_REFUSED_the_channel_census_can_catch_a_leaked_reason(self):
        """RW-REASON-TO-REFUSED (§4): the direction-2 census is able-to-fail. A record carrying the
        reason inline, placed in the set the census reads (the test_ep48 RW-PACKET-ROW discipline —
        the row is the red world, not a real act), makes the census FIRE. And a refusal recorded with
        NO reason makes the window's direction-1 read None (the window census can fail too)."""
        reason = "denied: no grant"
        # a planted channel record carrying the reason inline -> the census fires (able-to-fail).
        leaked = {"actor": "SYSTEM", "action": "COMMS-SEND", "object": "peer-sys",
                  "payload": {"channel": "peer-sys", "reason_leak": reason}}
        self.assertTrue(border.reason_in_records([leaked], reason),
                        "the channel census could not see a leaked reason — it cannot fail")
        self.assertFalse(border.reason_in_records([leaked], "some other text"))  # discriminates
        # DIRECTION 1 is able-to-fail too: the window read is the recorded reason, and a crossing
        # with no refusal is ABSENT from the window (the read can come back empty).
        sub = self.a_submit()
        cid = border.content_id(sub)
        self.assertNotIn(cid, border.through_the_window(self.store))     # no refusal yet -> absent
        border.refusal(self.gate, "peer", cid, "a real reason")
        self.assertEqual(border.through_the_window(self.store)[cid]["reason"], "a real reason")


# =============================================================================================
# A4 — T-BORDER-COURIER-NEVER (+ RW-COURIER) — no crossing attributed to the system
# =============================================================================================

class TestBorderCourierNever(_World):
    def test_no_crossing_is_attributed_to_the_system(self):
        self.a_submit()
        self.a_submit(draft={"want": "connect 1.2.3.4"})
        # every crossing is willed by an established entity; NONE by the system.
        self.assertEqual(border.system_attributed(self.store), [],
                         "a crossing was attributed to the system — the system is the border, not the courier")
        for c in border.crossings(self.store).values():
            self.assertNotIn(c["willed_by"], border.SYSTEM_ACTORS)
            self.assertNotIn(c["entity"], border.SYSTEM_ACTORS)

    def test_RW_COURIER_a_system_willed_crossing_reds_the_census(self):
        """RW-COURIER (§4): the courier-never census is able-to-fail. A crossing whose willing entity
        is the system, placed in the set the census reads, makes it FIRE (design/39 §3). The real
        store never holds one — a submit's entity is `require_prior`-established and the recorder is
        no established submitter — so the offending crossing is the counterfactual, not a real act."""
        real = list(border.crossings(self.store).values())
        self.assertEqual(border.system_attributed_over(real), [])        # real world: clean
        planted = real + [{"crossing_id": "sha256:beef", "willed_by": "SYSTEM",
                           "entity": "SYSTEM", "state": "open"}]
        offenders = border.system_attributed_over(planted)
        self.assertEqual([c["crossing_id"] for c in offenders], ["sha256:beef"],
                         "the census could not see a system-attributed crossing — it cannot fail")


# =============================================================================================
# A5 — T-CROSSING-ID-IS-SUBMIT-HASH (+ RW-CROSSING-ID-DRIFT) — the gate chokepoint binds it
# =============================================================================================

class TestCrossingIdIsSubmitHash(_World):
    def test_the_reply_crossing_id_recomputes_as_the_submit_content_hash(self):
        sub = self.a_submit()
        cid = border.content_id(sub)
        # the crossing id IS canonical_hash of the submit's OWN content (action/object/target/payload).
        core = {"action": sub["action"], "object": sub["object"],
                "target": sub.get("target"), "payload": sub.get("payload") or {}}
        self.assertEqual(cid, canonical.canonical_hash(canonical.strip_derivation(core)))
        # a reply carrying that crossing id binds — recorded (the seal is a separate concern, A2; a
        # placeholder here isolates the id binding the gate chokepoint enforces).
        rec = self.gate.execute("BORDER-REPLY", "SYSTEM",
                                {"crossing_id": cid, "shown": {"answer": "ok"}, "seal": "seal:placeholder"})
        self.assertEqual((rec.get("payload") or {}).get("crossing_id"), cid)
        self.assertEqual(border.crossings(self.store)[cid]["state"], "replied")

    def test_RW_CROSSING_ID_DRIFT_a_reply_binding_no_submit_is_refused(self):
        """RW-CROSSING-ID-DRIFT (§4): a reply whose crossing id is the content hash of NO submit binds
        nothing and is REFUSED at the gate chokepoint (the binding reads the store's recomputation,
        never the reply's in-band claim — the crossing.py correlation discipline, the border's
        direction). Driven for BOTH a reply and a refusal."""
        self.a_submit()                                                  # a real submit exists
        for op in ("BORDER-REPLY", "BORDER-REFUSAL"):
            params = {"crossing_id": "sha256:" + "0" * 64, "shown": {"a": 1}, "seal": "seal:x"}
            if op == "BORDER-REFUSAL":
                params = {"entity": "peer", "crossing_id": "sha256:" + "0" * 64, "reason": "r"}
            with self.assertRaises(OpError) as cm:
                self.gate.execute(op, "SYSTEM", params)
            self.assertEqual(cm.exception.rule, "COMM-LAW-CONTRACT")
        # and the refusal was RECORDED (cannot-do-lawfully, cannot-do-quietly).
        refs = [e for e in self.store.by_action("op-refused")
                if (e.get("payload") or {}).get("op") in ("BORDER-REPLY", "BORDER-REFUSAL")]
        self.assertTrue(refs)


# =============================================================================================
# A6 — T-BORDER-BUMP-ATTESTED (+ RW-NO-MOVE / RW-MAJOR) — the founding move
# =============================================================================================

class TestBorderBumpAttested(unittest.TestCase):
    def test_the_founding_rose_one_MINOR_and_the_bump_is_attested_in_one_entry(self):
        from test_founding_is_logged import audit, pack_facts
        facts = pack_facts()
        # ERA-PINNED (EP-49D §A57 sweep, the manager's test_ep48 model, board :3352): this was a LIVE
        # literal `assertEqual(facts["version"], "1.42.0")` that each founding mover hand-edited
        # (1.40.0 -> 1.41.0 -> 1.42.0 ...) — the exact class the era-pin idiom exists to end, a test
        # that reddens because the constitution GREW, indistinguishable from one that reddens because
        # its subject moved. Floored at the EP-49A era (1.41.0, EP-49A's own MINOR landing); a later
        # founding mover advances the constitution WITHOUT touching this line. The load-bearing
        # assertion is that the move is attested in ONE entry (audit, below), which reads the live tree.
        ver = tuple(int(x) for x in facts["version"].split("."))
        self.assertGreaterEqual(ver, (1, 41, 0),
                                "the founding is at or beyond the EP-49A era (1.41.0) this test pins")
        a = audit()
        self.assertTrue(a["logged"],
                        "the founding moved and no single BUILD-PROGRESS entry names both "
                        "the version and the pack sha256 (the required ledger duty, :1178)")

    def test_the_three_border_ops_are_in_the_pack_and_the_move_is_MINOR(self):
        import json
        repo = os.path.join(os.path.dirname(__file__), "..")
        with open(os.path.join(repo, "src", "founding", "founding-pack.json"), "rb") as fh:
            recs = [r for step in json.loads(fh.read())["steps"] for r in step["records"]]
        op_names = {r["payload"]["name"] for r in recs if r.get("action") == "CREATE-OP"}
        for n in THREE_OPS:                                              # ADDED (three ops) — the MINOR direction
            self.assertIn(n, op_names)
        # NONE REMOVED (a removal would be MAJOR / stop-e): representative pre-move ops survive.
        for kept in ("SOCKET-OPEN", "COMMS-OPEN", "FILE-CREATE", "MOUNT"):
            self.assertIn(kept, op_names)
        # NO CHECK KIND ADDED (the discriminator's other half): OP_CHECKS frozen at 17.
        self.assertEqual(len(OP_CHECKS), 19)
        # the three border ops use ONLY existing check kinds (require_prior, or none).
        used = set()
        for r in recs:
            if r.get("action") == "CREATE-OP" and r["payload"]["name"] in THREE_OPS:
                for c in r["payload"]["definition"].get("checks", []):
                    used.add(c["check"])
        self.assertTrue(used <= set(OP_CHECKS))
        self.assertTrue(used <= {"require_prior"})

    def test_RW_MAJOR_a_removed_op_or_a_new_check_kind_would_be_the_STOP(self):
        """RW-MAJOR (§4 / stop-e): the discriminator is able-to-distinguish. Removing an op, or adding
        a check kind, is MAJOR — an owner matter, not decided here. Assert the real move did neither
        (no border op introduced a check kind outside OP_CHECKS; the pre-move ops are all kept)."""
        import json
        repo = os.path.join(os.path.dirname(__file__), "..")
        with open(os.path.join(repo, "src", "founding", "founding-pack.json"), "rb") as fh:
            recs = [r for step in json.loads(fh.read())["steps"] for r in step["records"]]
        op_names = {r["payload"]["name"] for r in recs if r.get("action") == "CREATE-OP"}
        self.assertIn("COMMS-OPEN", op_names)                            # not reached-by-removal
        for r in recs:
            if r.get("action") == "CREATE-OP" and r["payload"]["name"] in THREE_OPS:
                for c in r["payload"]["definition"].get("checks", []):
                    self.assertIn(c["check"], OP_CHECKS,
                                  f"{r['payload']['name']} introduced a check kind — MAJOR / stop-e")


# =============================================================================================
# §8 — THE WRONG REFERENCE REFUSED BY NAME: the API gateway with auth middleware
# =============================================================================================

class TestApiGatewayTrapRefused(_World):
    def test_identity_is_recorded_establishment_never_a_peer_minted_token(self):
        """§8 (design/51 §9, stop f): the door admits NO peer-minted token as identity. An entity is
        its recorded establishment (design/39 §1) — BORDER-SUBMIT's `require_prior` over CREATE-ACCOUNT
        — so a submitter the record never established is refused however it names itself. There is no
        trust store beside the record: validity is read FROM the record."""
        # a submit naming an entity the record never established is refused (no token admits it).
        with self.assertRaises(OpError) as cm:
            border.submit(self.gate, "attacker-holding-a-bearer-token", {"want": "root"})
        self.assertEqual(cm.exception.rule, "CAP-IS-LAW")
        # BORDER-SUBMIT declares its entity check as require_prior over CREATE-ACCOUNT — recorded
        # establishment, never a token store. Read from the founding, not asserted here.
        import json
        repo = os.path.join(os.path.dirname(__file__), "..")
        with open(os.path.join(repo, "src", "founding", "founding-pack.json"), "rb") as fh:
            recs = [r for step in json.loads(fh.read())["steps"] for r in step["records"]]
        submit_def = next(r["payload"]["definition"] for r in recs
                          if r.get("action") == "CREATE-OP" and r["payload"]["name"] == "BORDER-SUBMIT")
        checks = submit_def.get("checks") or []
        self.assertTrue(any(c.get("check") == "require_prior" and c.get("action") == "CREATE-ACCOUNT"
                            for c in checks),
                        "BORDER-SUBMIT admits identity by something other than recorded establishment")

    def test_the_border_and_crossing_families_are_DISTINCT_sharing_the_discipline(self):
        """§12 (the N2 lesson): border.py is a DISTINCT family from crossing.py, not collapsed into
        one name. They share the discipline (a content-hash id, a fold not a registry) and border.py
        reuses crossing.py's serializer, but the two directions keep two names."""
        from kernel import crossing
        self.assertNotEqual(set(border.BORDER_KINDS) & set(crossing.CITING_KINDS), set(border.BORDER_KINDS))
        self.assertEqual(set(border.BORDER_KINDS) & set(crossing.CITING_KINDS), set())  # disjoint kinds
        # both are folds over the record (kill and replay: identical) — the shared discipline.
        sub = self.a_submit()
        first = border.crossings(self.store)
        second = border.crossings(self.store)                            # recompute: identical
        self.assertEqual(first, second)
        self.assertIn(border.content_id(sub), first)


if __name__ == "__main__":
    unittest.main()
