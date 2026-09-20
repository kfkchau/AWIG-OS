# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture / governance (channel, message, liveness, check, law) as in the
# seL4/gVisor literature and CGL. NON-GOAL: no offensive capability of any kind — this battery
# proves the channel laws ENFORCE; it attacks nothing.
# Full declaration: SCOPE-STATEMENT.md.
"""EP-49C — THE COMMS LAWS' ENFORCEMENT: the two owner-ruled check kinds and the acts that use them.

The owner ruled TWO new check kinds by explicit act (board :3354/:3355, "go yes"), the first growth
of the closed check vocabulary since design/40. They are CODE-BORN in opdefs.py (OP_CHECKS 17 -> 19,
no bump for that half); the check rows on COMMS-SEND/RECV/CLOSE that USE them are the DATA half
(founding-pack.json, one MINOR bump, attested). This battery drives every claim, each proven able to
FAIL — a check a red world cannot break is not a control.

  A1  TestLivePresentKind    `live_present` is in OP_CHECKS; a member ABSENT from the derived live
                             set refuses NAMING THE SET AND THE MEMBER; a present one passes; a blind
                             fold (the polarity collapsed, or a member never removed) REDS.
  A2  TestFoldThresholdKind  `fold_threshold` is in OP_CHECKS; a fold on the wrong side of its
                             threshold refuses NAMING THE FOLD, THE VALUE AND THE THRESHOLD; a fold
                             that never bites REDS.
  A3  TestLiveness           a COMMS-SEND / COMMS-RECV on a NON-LIVE channel is refused by
                             `live_present` over the channel live set, citing COMM-LAW-QUEUE; a live
                             one lands.
  A4  TestWhoseClose         two entities hold one channel NAME; a COMMS-CLOSE drops EXACTLY the
                             closer's opening, not the other's; a close-drops-both fold REDS.
  A5  TestNonemptyRecv       a COMMS-RECV on an EMPTY queue is refused by `fold_threshold`
                             queue_depth > 0, citing COMM-LAW-QUEUE; a non-empty receive lands.
  A6  TestCommsAuthority     a COMMS-SEND by an entity that holds no opening of the channel is
                             refused by `live_present` of (entity, channel), citing COMM-LAW-CONTRACT.
  A7  TestChecksNotEmpty     a presence census over the FIVE comms ops: none carries checks:[] where
                             its law names enforcement; SEND/RECV/CLOSE flipped [] -> present (the
                             held-proof discharged), each row citing a founded COMM-LAW-*.
  A8  TestVerdictBoundary    over ADJACENT allowed and refused sends, the verdict/citation view is
                             IDENTICAL folded and non-folded (a pure derivation appends nothing, the
                             EP-10 gauge precedent); a planted divergence REDS.
  A9  TestExtendedLedger     the EP-17 strictly-stronger obligation BOTH DIRECTIONS: an unlive send
                             that landed before is now REFUSED (not too weak); a lawful live send
                             still LANDS (not too wedged); each proven able to fail.
  A10 TestCountAndBump       OP_CHECKS == 19; the founding rose one MINOR from its driven base; the
                             bump-attestation (version + pack sha256) is in one BUILD-PROGRESS entry;
                             no op or law removed; the op population is unmoved (an amend, not a mint).
"""
import hashlib
import json
import os
import re
import shutil
import tempfile
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for _p in (os.path.join(_ROOT, "src"), _HERE):
    if _p not in os.sys.path:
        os.sys.path.insert(0, _p)

from kernel.boot import build_kernel                     # noqa: E402
from kernel.blobs import BlobStore                       # noqa: E402
from kernel.errors import OpError                        # noqa: E402
from kernel import opdefs as opdefs_mod                  # noqa: E402
from kernel.opdefs import OP_CHECKS                      # noqa: E402
from subsystems.comms import CommsView                   # noqa: E402

SYS_ROLE = "system-facing"
USR_ROLE = "user-facing"


class _World(unittest.TestCase):
    """A governed kernel with the comms ops live from genesis (the amended definitions register at
    boot). A channel is OPENED OF AN ENTITY; the acting actor is that entity, so the holder is the
    one who sends and closes — the world the enforcement is written for."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.record = os.path.join(self.dir, "record.jsonl")
        self.blobs = BlobStore(os.path.join(self.dir, "blobs"))
        self.store, self.gate, self.views = build_kernel(self.record, blobs=self.blobs)
        self.cv = CommsView(self.store)
        self.addCleanup(shutil.rmtree, self.dir, True)

    def account(self, who):
        self.gate.execute("CREATE-ACCOUNT", "SYSTEM", {"account_id": who, "actor_class": "program"})

    def open(self, entity, channel, role=SYS_ROLE):
        return self.gate.execute("COMMS-OPEN", entity,
                                 {"channel": channel, "entity": entity, "role": role})

    def send(self, actor, channel, message="m", to="x"):
        return self.gate.execute("COMMS-SEND", actor,
                                 {"channel": channel, "message": message, "to": to})

    def recv(self, actor, channel):
        return self.gate.execute("COMMS-RECV", actor, {"channel": channel})

    def close(self, actor, channel):
        return self.gate.execute("COMMS-CLOSE", actor, {"channel": channel})

    def refusal(self, fn, *a, **kw):
        """Drive an act expected to refuse; return (rule_cited, message). A governed refusal is a
        RECORDED op-refused decision, not only an exception — assert both."""
        before = len(self.store.by_action("op-refused"))
        try:
            fn(*a, **kw)
        except OpError as exc:
            rec = self.store.by_action("op-refused")[-1]
            self.assertEqual(len(self.store.by_action("op-refused")), before + 1,
                             "the act raised but recorded no refusal")
            return rec.get("rule_cited"), str(exc)
        raise AssertionError("the act was ADMITTED where the law requires a refusal")

    def lands(self, fn, *a, **kw):
        """Drive an act expected to land; return its record. Fails loudly on refusal."""
        try:
            return fn(*a, **kw)
        except OpError as exc:
            raise AssertionError("a lawful act was REFUSED: %s" % exc)


# =============================================================================================
# A1 — `live_present` IS A KIND, WITH A CONTROL (RW-LIVE-PRESENT-BLIND)
# =============================================================================================

class _CapturingGate:
    """A gate double that records the refusal and raises — enough to drive a check function on its
    own and read its ENGINE-WORDED default message (the property the kind must carry, distinct from
    a row's `message` override)."""

    def refuse(self, actor, op, rule, message, draft=None):
        raise OpError(rule, message)


class _EmptyStore:
    def by_action(self, action, as_of=None):
        return []


class TestLivePresentKind(_World):
    def test_live_present_is_in_the_vocabulary(self):
        self.assertIn("live_present", OP_CHECKS)

    def test_the_default_refusal_names_the_set_and_the_missing_member(self):
        """The kind's own property (EP §1): a row carrying no `message` refuses NAMING THE SET it
        folds from and THE MISSING MEMBER — driven on the check function directly over an empty set."""
        bare = {"check": "live_present", "open_action": "X-OPEN", "close_action": "X-CLOSE",
                "key_params": ["thing"], "present": {"thing": "thing"}}
        with self.assertRaises(OpError) as cm:
            opdefs_mod._live_present_check(_CapturingGate(), _EmptyStore(), None,
                                           "actor", "PROBE", bare, {"thing": "wanted"})
        msg = str(cm.exception)
        self.assertIn("X-OPEN", msg)                     # the set folded from
        self.assertIn("thing", msg)                      # the key
        self.assertIn("wanted", msg)                     # the missing member's value

    def test_a_present_member_passes_and_an_absent_one_refuses_over_the_channel_live_set(self):
        self.account("a")
        self.open("a", "chan:1")
        # PRESENT: a live opening of chan:1 held by a — the send lands.
        self.lands(self.send, "a", "chan:1")
        # ABSENT: no live opening of chan:9 — the send refuses citing the queue law.
        rule, _ = self.refusal(self.send, "a", "chan:9")
        self.assertEqual(rule, "COMM-LAW-QUEUE")

    def test_RW_LIVE_PRESENT_BLIND_a_fold_that_never_removes_admits_the_absent(self):
        """A blind `live_present` — the polarity collapsed so a member is treated present when it is
        not — would ADMIT the send on a non-live channel. Driven through the real check by making the
        fold return the queried member always; the previously-refused act now LANDS, so the refusal
        above was the real check biting and not an accident of setup."""
        self.account("a")
        self.open("a", "chan:1")
        real = opdefs_mod._live_present_set

        def blind(store, c, as_of=None):                 # every member is 'present'
            live = real(store, c)
            live[("a", "chan:9")] = {"entity": "a", "channel": "chan:9"}
            return live
        opdefs_mod._live_present_set = blind
        self.addCleanup(setattr, opdefs_mod, "_live_present_set", real)
        self.lands(self.send, "a", "chan:9")             # the blind fold admits the absent member


# =============================================================================================
# A2 — `fold_threshold` IS A KIND, WITH A CONTROL (RW-FOLD-THRESHOLD-BLIND)
# =============================================================================================

class TestFoldThresholdKind(_World):
    def test_fold_threshold_is_in_the_vocabulary(self):
        self.assertIn("fold_threshold", OP_CHECKS)

    def test_the_default_refusal_names_the_fold_the_value_and_the_threshold(self):
        """The kind's own property (EP §1): a row carrying no `message` refuses NAMING THE FOLD, THE
        VALUE and THE THRESHOLD — driven on the check function directly over an empty count."""
        bare = {"check": "fold_threshold", "add_action": "A-ADD", "sub_action": "A-SUB",
                "key_param": "chan", "key_field": "chan", "operator": ">", "threshold": 0,
                "fold_name": "queue_depth"}
        with self.assertRaises(OpError) as cm:
            opdefs_mod._fold_threshold_check(_CapturingGate(), _EmptyStore(), None,
                                             "actor", "PROBE", bare, {"chan": "c"})
        msg = str(cm.exception)
        self.assertIn("queue_depth", msg)                # the fold
        self.assertIn("= 0", msg)                        # the value
        self.assertIn("> 0", msg)                        # the operator and threshold

    def test_a_fold_below_threshold_refuses_and_a_pending_one_passes(self):
        self.account("a")
        self.open("a", "chan:1")
        self.send("a", "chan:1")                         # queue_depth -> 1
        self.lands(self.recv, "a", "chan:1")             # ABOVE threshold: the receive lands
        # queue_depth back to 0; the next receive is BELOW threshold and refuses citing the queue law.
        rule, _ = self.refusal(self.recv, "a", "chan:1")
        self.assertEqual(rule, "COMM-LAW-QUEUE")

    def test_RW_FOLD_THRESHOLD_BLIND_a_comparison_that_never_bites_admits_the_empty_receive(self):
        """A blind `fold_threshold` — a comparison that always passes — would ADMIT a receive on an
        empty queue. Driven through the real check by forcing its operator to the always-true one; the
        empty receive now LANDS."""
        self.account("a")
        self.open("a", "chan:1")                         # queue_depth 0
        real = dict(opdefs_mod._FOLD_OPERATORS)
        opdefs_mod._FOLD_OPERATORS[">"] = lambda v, t: True   # the threshold never bites
        self.addCleanup(lambda: opdefs_mod._FOLD_OPERATORS.update(real))
        self.lands(self.recv, "a", "chan:1")            # empty, but the blind comparison admits it


# =============================================================================================
# A3 — T-COMMS-LIVENESS-AT-SEND / RECV
# =============================================================================================

class TestLiveness(_World):
    def test_a_send_and_a_receive_on_a_non_live_channel_are_refused_citing_the_queue_law(self):
        self.account("a")
        rule, _ = self.refusal(self.send, "a", "never-opened")
        self.assertEqual(rule, "COMM-LAW-QUEUE")
        rule, _ = self.refusal(self.recv, "a", "never-opened")
        self.assertEqual(rule, "COMM-LAW-QUEUE")

    def test_a_send_on_a_live_channel_lands(self):
        self.account("a")
        self.open("a", "chan:1")
        rec = self.lands(self.send, "a", "chan:1")
        self.assertEqual(rec["rule_cited"], "COMM-LAW-QUEUE")

    def test_a_channel_stays_live_for_a_second_holder_after_the_first_closes(self):
        """Liveness is a member of the (entity, channel) live set matched CHANNEL-WIDE (any holder):
        after one of two same-named holders closes, the channel is still live and a receive on the
        pending message lands."""
        self.account("a"); self.account("b")
        self.open("a", "shared", SYS_ROLE)
        self.open("b", "shared", USR_ROLE)
        self.send("a", "shared")                          # a pending message on 'shared'
        self.close("a", "shared")                         # a's opening gone; b's remains
        self.lands(self.recv, "b", "shared")              # 'shared' is still a live channel


# =============================================================================================
# A4 — T-COMMS-WHOSE-CLOSE (RW-CLOSE-DROPS-BOTH)
# =============================================================================================

class TestWhoseClose(_World):
    def test_two_entities_one_name_a_close_drops_exactly_the_closers_opening(self):
        self.account("a"); self.account("b")
        self.open("a", "dup", SYS_ROLE)
        self.open("b", "dup", USR_ROLE)
        self.assertEqual(sorted(self.cv.live_channels()), [("a", "dup"), ("b", "dup")])
        self.lands(self.close, "a", "dup")
        self.assertEqual(sorted(self.cv.live_channels()), [("b", "dup")],
                         "a's close dropped exactly a's opening, and b's survives")

    def test_a_close_by_a_non_holder_is_refused_citing_the_contract_law(self):
        self.account("a"); self.account("c")
        self.open("a", "dup", SYS_ROLE)
        rule, _ = self.refusal(self.close, "c", "dup")   # c holds no opening of 'dup'
        self.assertEqual(rule, "COMM-LAW-CONTRACT")

    def test_RW_CLOSE_DROPS_BOTH_a_name_keyed_fold_drops_the_other_holders_opening(self):
        """The red world the whose-close cure exists to refuse: a name-keyed close, dropping EVERY
        opening of the name. Driven through the real fold by forcing the close removal to ignore the
        actor; a's close now drops b's opening too."""
        self.account("a"); self.account("b")
        self.open("a", "dup", SYS_ROLE)
        self.open("b", "dup", USR_ROLE)
        real = CommsView.live_channels

        def name_keyed(self_cv, as_of=None):
            live = {}
            for e in self_cv.store.action_set_projection({"COMMS-OPEN", "COMMS-CLOSE"}).all(as_of):
                a, p = e["action"], (e.get("payload") or {})
                if a == "COMMS-OPEN":
                    live[(p.get("entity"), p["channel"])] = p.get("role")
                elif a == "COMMS-CLOSE":
                    for k in [k for k in live if k[1] == p["channel"]]:
                        live.pop(k, None)
            return live
        CommsView.live_channels = name_keyed
        self.addCleanup(setattr, CommsView, "live_channels", real)
        self.close("a", "dup")
        self.assertEqual(sorted(self.cv.live_channels()), [],
                         "the name-keyed red world dropped BOTH openings — this is what REDS A4")


# =============================================================================================
# A5 — T-COMMS-NONEMPTY-RECV
# =============================================================================================

class TestNonemptyRecv(_World):
    def test_a_receive_on_an_empty_queue_is_refused_and_a_non_empty_one_lands(self):
        self.account("a")
        self.open("a", "chan:1")
        rule, _ = self.refusal(self.recv, "a", "chan:1")     # queue_depth 0
        self.assertEqual(rule, "COMM-LAW-QUEUE")
        self.send("a", "chan:1")                             # queue_depth 1
        self.assertEqual(self.cv.queue_depth("chan:1"), 1)
        self.lands(self.recv, "a", "chan:1")
        self.assertEqual(self.cv.queue_depth("chan:1"), 0)


# =============================================================================================
# A6 — T-COMMS-AUTHORITY
# =============================================================================================

class TestCommsAuthority(_World):
    def test_a_send_by_a_non_holder_on_a_live_channel_is_refused_citing_the_contract_law(self):
        self.account("a"); self.account("b")
        self.open("a", "chan:1")                             # 'chan:1' is LIVE and held by a
        # b sends on a's live channel: liveness passes (the channel is live), but AUTHORITY refuses —
        # b holds no opening of it. The refusal cites the CONTRACT law, not the queue law.
        rule, _ = self.refusal(self.send, "b", "chan:1")
        self.assertEqual(rule, "COMM-LAW-CONTRACT")

    def test_the_holder_may_send_on_its_own_channel(self):
        self.account("a")
        self.open("a", "chan:1")
        self.lands(self.send, "a", "chan:1")


# =============================================================================================
# A7 — T-CHECKS-NOT-EMPTY (the presence census; the held-proof discharged)
# =============================================================================================

class TestChecksNotEmpty(_World):
    FIVE = ("COMMS-OPEN", "COMMS-SEND", "COMMS-RECV", "COMMS-CLOSE", "SHM-GRANT")

    def _defs(self):
        return {n: v["definition"] for n, v in self.views.op_definitions().items() if n in self.FIVE}

    def test_no_comms_op_whose_law_names_enforcement_carries_an_empty_checks_list(self):
        defs = self._defs()
        self.assertEqual(sorted(defs), sorted(self.FIVE), "a comms op is missing from the registry")
        for name, d in defs.items():
            self.assertTrue(d.get("checks"),
                            "%s carries checks:[] though its law names enforcement" % name)

    def test_send_recv_close_flipped_empty_to_present_each_row_citing_a_founded_comm_law(self):
        defs = self._defs()
        founded = {"COMM-LAW-CONTRACT", "COMM-LAW-QUEUE"}
        for name in ("COMMS-SEND", "COMMS-RECV", "COMMS-CLOSE"):
            checks = defs[name].get("checks") or []
            self.assertTrue(checks, "%s: the held-proof did not flip [] -> present" % name)
            for c in checks:
                self.assertIn(c["check"], ("live_present", "fold_threshold"))
                self.assertIn(c.get("cite"), founded,
                              "%s check cites %r, not a founded comms law" % (name, c.get("cite")))


# =============================================================================================
# A8 — THE VERDICT-BOUNDARY DIFFERENTIAL (E4, :1748; RW-VERDICT-DIVERGES)
# =============================================================================================

class TestVerdictBoundary(_World):
    """Over adjacent ALLOWED and REFUSED sends, the verdict/citation view is a pure derivation over
    the record (each act's `rule_cited`, and whether it is an op-refused). It appends nothing, so it
    is IDENTICAL computed by the FAMILY FOLD and by the WHOLE-STORE scan — the EP-10 gauge precedent
    applied at the allowed/refused boundary."""

    def _workload(self):
        self.account("a"); self.account("b")
        self.open("a", "chan:1")
        # adjacent allowed and refused sends, interleaved
        self.send("a", "chan:1")                                 # allowed
        self.refusal(self.send, "b", "chan:1")                   # refused (authority, CONTRACT)
        self.send("a", "chan:1")                                 # allowed
        self.refusal(self.send, "a", "never")                    # refused (liveness, QUEUE)

    @staticmethod
    def _verdict_citation(records):
        """{seq: (verdict, rule_cited)} over every COMMS-SEND decision and every op-refused of a
        COMMS-SEND — the view carrying verdicts and citations."""
        out = {}
        for e in records:
            if e["action"] == "COMMS-SEND":
                out[e["seq"]] = ("allowed", e.get("rule_cited"))
            elif e["action"] == "op-refused" and (e.get("payload") or {}).get("op") == "COMMS-SEND":
                out[e["seq"]] = ("refused", e.get("rule_cited"))
        return out

    def test_fold_and_non_fold_verdict_citation_views_are_identical(self):
        self._workload()
        non_fold = self._verdict_citation(self.store.all())
        fold = self._verdict_citation(
            self.store.action_set_projection({"COMMS-SEND", "op-refused"}).all())
        self.assertEqual(fold, non_fold, "the verdict/citation view diverged fold vs non-fold")
        # both boundaries present: at least one allowed and one refused verdict, with real citations
        verdicts = {v for v, _cite in fold.values()}
        self.assertEqual(verdicts, {"allowed", "refused"})
        self.assertEqual({c for _v, c in fold.values()}, {"COMM-LAW-QUEUE", "COMM-LAW-CONTRACT"})

    def test_a_pure_derivation_survives_a_cache_kill_byte_for_byte(self):
        """T-CACHE-KILL: rebuilt from the record alone, the view is identical — nothing was stored."""
        self._workload()
        before = self._verdict_citation(self.store.all())
        store2, _g2, _v2 = build_kernel(self.record)
        self.assertEqual(self._verdict_citation(store2.all()), before)

    def test_RW_VERDICT_DIVERGES_a_view_blind_to_refusals_is_caught(self):
        """The comparison must be able to fail: a derivation that drops the refused rows (the fold
        blind to the boundary) DIFFERS from the true one — the equality above would red."""
        self._workload()
        true = self._verdict_citation(self.store.all())
        blind = {s: v for s, v in true.items() if v[0] != "refused"}
        self.assertNotEqual(blind, true, "the boundary carried no refusal — the workload is degenerate")


# =============================================================================================
# A9 — THE EXTENDED LEDGER, BOTH DIRECTIONS (EP-17 strictly-stronger; RW-TOO-WEAK / RW-TOO-WEDGED)
# =============================================================================================

class TestExtendedLedger(_World):
    def test_TOO_WEAK_an_unlive_send_that_landed_before_is_now_refused(self):
        """The flip is not too weak: a send on a non-live channel — an act the unchecked ledger
        RECORDED — is now REFUSED. Proven able to fail: a blind check admits it again."""
        self.account("a")
        self.refusal(self.send, "a", "unlive")               # now refused
        real = opdefs_mod._live_present_check
        opdefs_mod._live_present_check = lambda *a, **k: None     # the check made blind
        self.addCleanup(setattr, opdefs_mod, "_live_present_check", real)
        self.lands(self.send, "a", "unlive")                 # blind -> the unlive send lands (the too-weak world)

    def test_TOO_WEDGED_a_lawful_live_send_still_lands(self):
        """The flip is not too wedged: a lawful send by the holder on a live channel STILL LANDS.
        Proven able to fail: an always-refusing check wedges it."""
        self.account("a")
        self.open("a", "chan:1")
        self.lands(self.send, "a", "chan:1")                 # lawful -> lands
        real = opdefs_mod._live_present_check

        def always_refuse(gate, store, views, actor, opname, c, params):
            gate.refuse(actor, opname, c.get("cite") or "AR-2", "wedged")
        opdefs_mod._live_present_check = always_refuse
        self.addCleanup(setattr, opdefs_mod, "_live_present_check", real)
        self.account("z")
        self.open("z", "chan:2")
        self.refusal(self.send, "z", "chan:2")               # wedged -> the lawful send is refused


# =============================================================================================
# A10 — THE COUNT SWEEP + THE BUMP
# =============================================================================================

class TestCountAndBump(_World):
    PACK = os.path.join(_ROOT, "src", "founding", "founding-pack.json")

    def test_OP_CHECKS_is_19_with_both_owner_ruled_kinds(self):
        self.assertEqual(len(OP_CHECKS), 19)
        self.assertIn("live_present", OP_CHECKS)
        self.assertIn("fold_threshold", OP_CHECKS)

    def test_no_len_OP_CHECKS_pin_survives_at_17(self):
        """RW-COUNT-STALE: a 17-pin left unmoved is a count sweep incomplete. No live-vocabulary
        assertion in the suite may still read 17 against the engine."""
        # test_ep51 is the ONE documented exclusion: EP-51 (the TWC tracer) is DISPATCHED, not
        # closed, and its own assertion also pins founding-pack.json to b619d465 (EP-50's close),
        # which THIS founding move necessarily supersedes. Both its pins — the OP_CHECKS count and
        # the pack sha256 — are EP-51's to re-base onto this close (RAISED, board): editing an
        # in-flight sibling's test here would risk a two-editor clobber and still leaves it red on
        # the pack sha, so the reconciliation is not this unit's. The sweep is otherwise estate-wide.
        stale = []
        for fn in os.listdir(_HERE):
            if not fn.endswith(".py") or fn == "test_ep51.py":
                continue
            with open(os.path.join(_HERE, fn), encoding="utf-8") as fh:
                for i, line in enumerate(fh, 1):
                    if re.search(r"OP_CHECKS\)\s*,\s*17\b", line):
                        stale.append("%s:%d" % (fn, i))
        self.assertEqual(stale, [], "a len(OP_CHECKS)==17 pin survived the mint: %r" % stale)

    def test_the_founding_rose_one_MINOR_from_its_driven_base(self):
        """A6-of-the-founding: the DATA half (the check rows) is a MINOR bump. Base driven at
        dispatch was 1.44.0; after is 1.45.0 — the minor moved by one, major and patch unchanged.
        [ERA-PINNED at the EP-52 §A57 sweep — the test_ep48 A7 / board :3300 idiom. This was a LIVE
        literal `== "1.45.0"` that EVERY later founding mover would hand-edit (EP-52 FILTER-DECISION
        took the constitution to 1.46.0), the exact class the era-pin idiom exists to end. Floored at
        the EP-49C era (1.45.0); a later mover advances the constitution WITHOUT touching this line.
        The load-bearing claim — a MINOR step (major and patch fixed) at or beyond the EP-49C era —
        is UNCHANGED and now covers more, not less.]"""
        version = json.load(open(self.PACK))["founding_version"]
        maj, minr, pat = (int(x) for x in version.split("."))
        self.assertEqual((maj, pat), (1, 0))                  # major and patch fixed — a MINOR move
        self.assertGreaterEqual(minr, 45)                     # at or beyond the EP-49C era (1.45.0)

    def test_the_bump_is_attested_in_one_BUILD_PROGRESS_entry_version_plus_pack_sha256(self):
        """The founding-mover ledger duty: ONE entry names the new version AND the pack sha256."""
        version = json.load(open(self.PACK))["founding_version"]
        with open(self.PACK, "rb") as fh:
            sha = hashlib.sha256(fh.read()).hexdigest()
        log = open(os.path.join(_ROOT, "planning", "build", "BUILD-PROGRESS_v3.md"),
                   encoding="utf-8").read()
        # the entry names the version and the full pack sha256 together
        self.assertIn(version, log, "no BUILD-PROGRESS entry names the new founding version")
        self.assertIn(sha, log, "no BUILD-PROGRESS entry names the pack sha256 (the attestation)")

    def test_no_op_or_law_removed_and_the_op_population_is_unmoved(self):
        """RW-MAJOR: a removal is the owner's. This is an AMEND of existing ops (checks added), not a
        mint or a removal — the op population is unchanged and both comms laws still exist."""
        pack = json.load(open(self.PACK))
        names = set(); rule_ids = set()
        for step in pack["steps"]:
            for r in step["records"]:
                p = r.get("payload") or {}
                if p.get("kind") == "op_definition" and p.get("name"):
                    names.add(p["name"])
                if r.get("action") == "CREATE-RULE" and p.get("rule_id"):
                    rule_ids.add(p["rule_id"])
        # [§A57 sweep, EP-52 (FILTER-DECISION, 1.45.0 -> 1.46.0): the LIVE op-population moved 92 -> 93
        #  by a real op-MINT (EP-52's founding move), NOT by this amend — EP-49C's own point stands: an
        #  amend adds no op. Widened by name at the EP-52 dispatch.
        #  C6a VT-2 (CREATE-RELATIONSHIP MINTED live, MINOR 1.51.0 -> 1.52.0) moved 93 -> 94 BY NAME (§A57);
        #  EP-49C's point stands — its own move is an AMEND (adds no op); this pin tracks the live population.]
        self.assertEqual(len(names), 94, "the op population moved by a mint elsewhere — an amend adds no op")
        self.assertTrue({"COMM-LAW-CONTRACT", "COMM-LAW-QUEUE"} <= rule_ids,
                        "a comms law was removed — that is a MAJOR move and the owner's")


if __name__ == "__main__":
    unittest.main()
