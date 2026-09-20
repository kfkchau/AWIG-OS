# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-28 W8 — the files speed tension, pinned where the suite can reach it.

W8's product is a DERIVATION about where a gated act's time goes at kernel rate, and its
figures were taken in the guest (`planning/vm/govosfs/w8-speed.py`, evidence in
`planning/vm/M3-EVIDENCE.md` §7 and `planning/build/MEASUREMENTS.md` entry 9). A latency
figure is not a regression test — it moves with the disk. What IS testable, and what this
file pins, is every STRUCTURAL fact the derivation rests on, so that a later change which
would invalidate the derivation shows up as a red test rather than as a stale number:

  1. The class map fixes the record count. A header costs exactly two gated acts because
     `open` and `close` are both DECISION (design/10 §6). Recording less is refused
     (design/32 K3), so the count is not a lever.
  2. Each of those acts costs exactly one DURABLE append, and durability is what the cost
     IS. Proven against a power cut in the guest; pinned here as the mechanism.
  3. The authority fold is NOT where the time is, and the ruled release exemption
     (design/10 §11.1c) is a CORRECTNESS ruling rather than the speed work. Both halves
     are pinned: the fold still runs on a release today, and running it produces the ABI
     divergence §11.1c names.
  4. The exemption must be DECLARED, never borrowed from a field that means something
     else. The shortcut is demonstrated to work — which is why the guard against it is
     needed and why the guard can fail.
  5. The per-act folds read a governance SUBSET (ADDENDUM C's rule, holding) but their
     memo is invalidated by EVERY append, including appends that cannot change them. That
     distinction is the whole of finding 6b, and the two halves are tested apart.

Every test here was run by hand against the live seam or the live brain first.
"""

import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from kernel import store as store_mod                          # noqa: E402
from bridge import host_seam as seam_mod                          # C7 P2 — the barrier now issues from the seam (:3927)
from kernel.errors import OpError                              # noqa: E402
from bridge.kernel_port import KernelPort                      # noqa: E402
from bridge.mount import build_brain                           # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE_C = os.path.join(REPO, "planning", "vm", "govosfs", "govosfs.c")


def _req(op, cls="DECISION", uid=1000, gid=1000, pid=42, **kw):
    f = {"id": "1", "op": op, "class": cls,
         "uid": str(uid), "gid": str(gid), "pid": str(pid)}
    f.update({k: str(v) for k, v in kw.items()})
    return f


class W8Case(unittest.TestCase):
    """A disposable brain, composed exactly as the guest's daemon composes it."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep28w8-")
        self.rec = os.path.join(self.dir, "rec.jsonl")
        self.store, self.gate, self.views, self.blobs = build_brain(
            self.rec, os.path.join(self.dir, "blobs"))
        self.port = KernelPort(self.store, self.gate, self.views, self.blobs)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def call(self, op, cls="DECISION", payload=b"", **kw):
        return self.port.handle(_req(op, cls, **kw), payload)

    def ino(self, path):
        """The number the PORT serves for this path.

        DOCUMENTED FLIP, EP-28C W4b (2026-08-03), applied as ONE change at twenty call
        sites. Every one of them read the literal `2` — the first number the port's own
        `next_ino` stamp handed out — and the stamp is gone: the founding derives the
        identity (`param_defaults {"inode": "$path"}`, class-wide at 1.14.0) and
        `custody.render_ino` renders it. So a later call carries the number the create's
        reply returned, which is exactly what the kernel module carries in `i_ino`. The
        rows' subjects are untouched; what moved is where the number comes from."""
        return self.port.state.lookup(path).ino

    def n(self):
        return len(self.store.all())

    def actions_since(self, mark):
        return [e["action"] for e in self.store.all()[mark:]]


# =====================================================================================
# 1. THE CLASS MAP FIXES THE RECORD COUNT — so the count is not a lever
# =====================================================================================

class TestTheClassMapFixesTheCount(W8Case):
    """design/10 §6 classes `open` and `close` DECISION, so a header costs two gated
    acts. The guest measured exactly that (`recs +2.0/call` on every run). K3 forbids the
    obvious speed move — recording less — so what a header COSTS in records is settled
    law and only what a record costs in time is open."""

    def test_a_header_costs_exactly_two_records_and_both_are_decisions(self):
        self.call("FILE-CREATE", path="/h.h", perm="644")
        mark = self.n()
        self.assertEqual(self.call("FILE-OPEN", path="/h.h", inode=self.ino("/h.h"), flags=0)[0], 0)
        self.assertEqual(self.call("FILE-CLOSE", path="/h.h", inode=self.ino("/h.h"))[0], 0)
        self.assertEqual(self.actions_since(mark), ["FILE-OPEN", "FILE-CLOSE"])

    def test_the_read_between_them_appends_nothing(self):
        """The bytes are STREAM (design/10 §6, read row) and the caller's payload is
        exact. A read served from the record's blob crosses as a FILL and a fill cannot
        decide anything, so the two DECISIONs really are the whole recorded cost."""
        self.call("FILE-CREATE", path="/h.h", perm="644")
        self.call("FILE-WRITE", path="/h.h", inode=self.ino("/h.h"), payload=b"#define X 1\n")
        mark = self.n()
        status, fields, payload = self.port.handle(
            _req("FILL-CONTENT", "FILL", hash=self._hash_of("/h.h")), b"")
        self.assertEqual(status, 0)
        self.assertEqual(payload, b"#define X 1\n")
        self.assertEqual(self.n(), mark)

    def _hash_of(self, path):
        node = self.port.state.lookup(path)
        return node.content_hash

    def test_each_custody_op_appends_exactly_one_record(self):
        """Four ops, four records — the arithmetic behind the guest's `recs +4.0/call`
        for a brand-new file and `+3.0` for one that already existed."""
        # The kwargs are built LAZILY because three of the four now ask the fold for a
        # number the FIRST call is what creates — under the retired stamp the literal `2`
        # could be written before anything existed (EP-28C W4b's flip, same reason as the
        # helper's).
        for op, mk in (("FILE-CREATE", lambda: {"path": "/n.txt", "perm": "644"}),
                       ("FILE-OPEN", lambda: {"path": "/n.txt",
                                              "inode": self.ino("/n.txt"), "flags": 0}),
                       ("FILE-WRITE", lambda: {"path": "/n.txt",
                                               "inode": self.ino("/n.txt")}),
                       ("FILE-CLOSE", lambda: {"path": "/n.txt",
                                               "inode": self.ino("/n.txt")})):
            kw = mk()
            mark = self.n()
            self.assertEqual(self.call(op, payload=b"x", **kw)[0], 0, op)
            self.assertEqual(self.n() - mark, 1, "%s appended %d records" % (op, self.n() - mark))


# =====================================================================================
# 2. ONE ACT, ONE DURABLE APPEND — and durability is what the cost IS
# =====================================================================================

class TestOneActIsOneDurableAppend(W8Case):
    """The guest measured the durable append at 71–85% of a gated act, and a power cut
    proved it is not removable: an unsynced record file did not come back short, IT DID
    NOT COME BACK AT ALL (`planning/vm/govosfs/w8-durability.py`). What is pinned here is
    the mechanism that produces that cost, so the raise about changing it is concrete."""

    def _count_syncs(self, fn):
        """DOCUMENTED FLIP (EP-28B W2): the barrier this counts is `fdatasync`. `fsync` is
        counted too, and expected to be ZERO on this path — otherwise a store that synced twice,
        or that reverted to the stronger barrier, would read as one sync and pass."""
        seen = {"fdatasync": 0, "fsync": 0, "order": []}
        real_fdatasync = seam_mod.os.fdatasync
        real_fsync = seam_mod.os.fsync

        def spy_fdatasync(fd):
            seen["fdatasync"] += 1
            seen["order"].append("fdatasync")
            return real_fdatasync(fd)

        def spy_fsync(fd):
            seen["fsync"] += 1
            seen["order"].append("fsync")
            return real_fsync(fd)
        # THE BRACKET IS THE ACT, NOT `store._append` [DOCUMENTED FLIP, EP-28G, 2026-08-03,
        # mapped to the publish/await split]. It used to wrap `store._append` on the premise
        # that the gate calls it; EP-28G split publication from the durability wait, because
        # the gate must hold the decide region across the first and must not hold it across
        # the second, so the gate now calls `_publish` and then `_await_durable`. A bracket on
        # `_append` after that measures a function nothing on this path calls, and would have
        # gone silently inert. K1(a) is about what reaches the CALLER, so the bracket is the
        # act — which is stronger, because it is the boundary the invariant names.
        seam_mod.os.fdatasync = spy_fdatasync
        seam_mod.os.fsync = spy_fsync
        seen["order"].append("act-enter")
        try:
            fn()
        finally:
            seen["order"].append("act-return")
            seam_mod.os.fdatasync = real_fdatasync
            seam_mod.os.fsync = real_fsync
        return seen

    def test_every_appended_record_costs_exactly_one_sync(self):
        """UNCHANGED IN MEANING, MOVED TO THE NEW BARRIER (EP-28B W2). One act, one durable
        append — the arithmetic W8 measured is untouched by which barrier carries it."""
        self.call("FILE-CREATE", path="/d.txt", perm="644")
        seen = self._count_syncs(
            lambda: [self.call("FILE-OPEN", path="/d.txt", inode=self.ino("/d.txt"), flags=0),
                     self.call("FILE-CLOSE", path="/d.txt", inode=self.ino("/d.txt"))])
        self.assertEqual(seen["fdatasync"], 2,
                         "two gated acts must cost two durable appends, not %d"
                         % seen["fdatasync"])
        self.assertEqual(seen["fsync"], 0,
                         "the record path also called fsync — two barriers is two contracts")

    def test_the_sync_happens_before_the_append_returns(self):
        """K1(a) in its durability half: no effect is released to the caller before its
        covering decision is DURABLY appended.

        RE-AIMED AT THE ACT [DOCUMENTED FLIP, EP-28G, 2026-08-03]. The bracket used to be
        `store._append`, on the reasoning that the gate's answer is formed from what it
        returns. After EP-28G the gate publishes and then waits, so `_append` is no longer on
        this path — and K1(a)'s subject was never that function anyway. It is the EFFECT
        REACHED THE CALLER, and the caller's boundary is the act. The row now brackets the
        act: the covering barrier runs strictly inside it. The name is retained; a rename is
        a scheduling act and is raised, not taken here."""
        self.call("FILE-CREATE", path="/d.txt", perm="644")
        seen = self._count_syncs(
            lambda: self.call("FILE-OPEN", path="/d.txt", inode=self.ino("/d.txt"), flags=0))
        self.assertEqual(seen["order"], ["act-enter", "fdatasync", "act-return"])

    def test_the_record_file_is_opened_once_and_held(self):
        """FLIPPED (EP-28C W3, 2026-08-01), TOGETHER WITH ITS TWIN in `tests/test_ep28b.py`
        (`test_the_held_descriptor_half_landed`). THE FLIP IS THE EVIDENCE.

        This row pinned the opposite for two EPs and was correct to: the store re-opened the
        record file on every append, the guest measured holding the descriptor instead at
        0.1–1.8 ms cheaper, and EP-28B wrote that change and WITHDREW it in the same session
        because the conformance fixture took a descriptor number a row had just freed.
        **EP-28D repaired the fixture and drove BOTH directions**, so the change is safe, and
        EP-28D's verdict carried it here.

        AND THE REASON IT WAS NOT OPTIONAL, in EP-28D's own words: the instrument was
        momentarily occupying a number a row had just released, invisible only because the
        descriptor's lifetime was shorter than the gap between two subject calls — a property
        of the store rather than a guarantee the instrument makes.

        A founded world has already appended, so the descriptor is already held when this act
        runs and the act opens the record file NOT AT ALL. That is the strongest form of the
        statement: the count is zero, not one."""
        opened = []
        real = store_mod.Path.open

        def spy(self_path, *a, **k):
            if str(self_path).endswith("rec.jsonl"):
                opened.append(a[0] if a else k.get("mode"))
            return real(self_path, *a, **k)
        store_mod.Path.open = spy
        try:
            self.call("FILE-CREATE", path="/d.txt", perm="644")
            self.call("FILE-OPEN", path="/d.txt", inode=self.ino("/d.txt"), flags=0)
            self.call("FILE-CLOSE", path="/d.txt", inode=self.ino("/d.txt"))
        finally:
            store_mod.Path.open = real
        self.assertEqual(opened, [], "three gated acts re-opened the record file %d times — "
                                     "the descriptor is not held" % len(opened))

    def test_fdatasync_is_the_barrier_and_that_raise_is_closed(self):
        """FLIPPED (EP-28B W2). `fsync` syncs inode metadata an append-only log does not need
        for retrieval; `fdatasync` syncs the data and the size, which is exactly what a reader
        needs. The guest proved the weaker barrier sufficient across a power cut (300 of 300
        lines survived), and EP-28B re-proved it against a power cut on a world that survives a
        reboot. The source is read as well as the behaviour, because the raise was about a line
        of code and its closure should be visible in the same place."""
        with open(os.path.join(REPO, "src", "kernel", "store.py"), encoding="utf-8") as f:
            src = f.read()
        with open(os.path.join(REPO, "src", "bridge", "host_seam.py"), encoding="utf-8") as f:
            seam_src = f.read()
        # C7 P2 (:3927): the barrier's host call followed the routing into the seam — fdatasync
        # there, and the record pen has no fsync rescue. Re-pointed to the seam and STRENGTHENED
        # with the absence assertion on store.py; the raise's closure is visible where the call is.
        self.assertIn("os.fdatasync(fd)", seam_src)             # the seam performs the fdatasync barrier
        self.assertIn("host().fdatasync(f.fileno())", src)      # store.py issues it through the seam
        self.assertNotIn("os.fdatasync(", src)                  # ABSENCE: no direct barrier remains in the pen
        self.assertNotIn("os.fsync(f.fileno())", src)           # no metadata-sync barrier in the pen (unchanged)


# =====================================================================================
# 3. THE AUTHORITY FOLD IS NOT WHERE THE TIME IS — and §11.1c is a CORRECTNESS ruling
# =====================================================================================

class TestTheReleaseStillFolds(W8Case):
    """design/10 §11.1c, ruled 2026-07-27: a release RECORDS and is never subjected to
    the authority fold, because refusing a release is meaningless and because folding one
    manufactures an ABI divergence.

    DOCUMENTED FLIP (EP-28B W1, 2026-07-30): it IS implemented now. Every assertion in this
    class was written to hold while the ruling was unbuilt and to go red the moment it was
    built, so the flips below ARE the acceptance evidence for W1 rather than a new claim about
    it. The class name is left standing because it is the pin's own history — what changed is
    the world, and a renamed pin would lose the link between the raise and its closure. The
    positive assertions live in `tests/test_ep28b.py`
    (`T-RELEASE-RECORDS-NEVER-REFUSES`)."""

    def _fold_calls(self, fn):
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

    def test_a_release_no_longer_consults_the_authority_fold(self):
        """FLIPPED EXACTLY AS THE PIN DIRECTED (EP-28B W1): "FILE-CLOSE removed from the
        expected list and FILE-OPEN left in it." The custody grant still folds — this is an
        exemption for releases and not a hole in the files family — and the release does not."""
        self.call("FILE-CREATE", path="/r.txt", perm="644")
        calls = self._fold_calls(
            lambda: [self.call("FILE-OPEN", path="/r.txt", inode=self.ino("/r.txt"), flags=0),
                     self.call("FILE-CLOSE", path="/r.txt", inode=self.ino("/r.txt"))])
        self.assertIn("FILE-OPEN", calls)
        self.assertNotIn("FILE-CLOSE", calls,
                         "§11.1c is built: a release is never folded for authority")

    def test_the_module_documents_an_exemption_the_daemon_now_has(self):
        """DOCUMENTED FLIP (EP-28B W1), and the flip is in the MEANING rather than in the
        assertions, which is itself worth recording. `govos_release` says "The daemon skips
        the authority step for this op on the op's own declared kind." When this was written
        that sentence described a mechanism nobody had built. W1 built it, so the RAISE
        resolves by the comment becoming TRUE rather than by the comment being deleted —
        which is what the stopped predecessor derived and what happened.

        Both original assertions still hold unchanged, because the comment names the
        mechanism and not the field, so the second one was never going to move. The pin is
        therefore extended rather than merely re-labelled: the sentence in the module is
        checked against the two things that now make it honest — a declared kind in the
        founding, and a gate that skips on it."""
        with open(MODULE_C, encoding="utf-8") as f:
            # the claim is a block comment, so it arrives wrapped with " * " between its
            # lines; the search is against the unwrapped text, not against the layout
            c = " ".join(f.read().replace("*", " ").split())
        self.assertIn("skips the authority step", c)
        self.assertNotIn("act_kind", c)                 # the comment names the mechanism, not the field
        # and the mechanism the sentence describes now exists, on both halves
        self.assertEqual(
            (self.views.op_definitions()["FILE-CLOSE"]["definition"]).get("act_kind"), "release",
            "the module says the daemon skips on the op's own declared kind — so the op "
            "must declare one, or the comment is describing a mechanism again")
        calls = self._fold_calls(lambda: self.call("FILE-CREATE", path="/m.txt", perm="644")
                                 or self.call("FILE-CLOSE", path="/m.txt", inode=self.ino("/m.txt")))
        self.assertNotIn("FILE-CLOSE", calls)

    def test_a_release_by_an_uncovered_actor_now_succeeds_as_posix_requires(self):
        """DOCUMENTED FLIP (EP-28B W1) — INVERTED, which is the only honest way to move this
        one. It demonstrated §11.1c's reason by showing the divergence happening: a revoked
        chain reaching a `close` refused, and POSIX `close` on a valid descriptor cannot fail
        on permission. W1 removes the divergence, so the same world now produces the ABI's
        answer, and the assertion says so instead of asserting the defect.

        The world is still the disposable one this test throws away and the live openness
        grant is still never touched (the EP-25 T-CUSTODY-MATRIX pattern). What is measured
        first is that the narrowing really bit — `FILE-OPEN` by the same uncovered actor still
        refuses — because a release succeeding in a world where everything succeeds would
        prove nothing at all."""
        self.call("FILE-CREATE", path="/r.txt", perm="644")
        self.gate.execute("REVOKE", "owner", {"grant_id": "founding-openness"})
        self.assertNotIn("grant:founding-openness", self.views.grants())
        prov = {"asserted_by": "uid:1000", "source": "kernel-port",
                "could_read": [], "uid": 1000}
        # THE CONTROL: the custody GRANT still refuses for this actor, so the world is narrowed
        with self.assertRaises(OpError) as caught:
            self.gate.execute("FILE-OPEN", "uid:1000",
                              {"path": "/r.txt", "inode": self.ino("/r.txt"), "flags": 0, "provenance": prov})
        self.assertIn(caught.exception.rule, ("ROOT-NEG-1", "ROOT-NEG-3"))
        # and the RELEASE goes through, because refusing it is what POSIX forbids
        rec = self.gate.execute("FILE-CLOSE", "uid:1000",
                                {"path": "/r.txt", "inode": self.ino("/r.txt"), "provenance": prov})
        self.assertEqual(rec["action"], "FILE-CLOSE")
        self.assertFalse(rec.get("refused"))
        self.assertEqual(rec["rule_cited"], "FS-LAW-PERM")


# =====================================================================================
# 4. THE EXEMPTION MUST BE DECLARED, NEVER BORROWED — the wrong reference, guarded
# =====================================================================================

class TestTheExemptionIsNotBorrowed(W8Case):
    """THE WRONG REFERENCE W8 NAMES, and it is cheap enough to be tempting: declaring
    FILE-CLOSE's `authority_regime` as "attenuation-family" skips the covers check with
    ZERO engine lines, because that branch does nothing for an op that mints no grant and
    founds no space. It would also make the founding record say a release is governed by
    attenuation, which is false. §11.1c names the mechanism exactly — "keyed on the op's
    own declared kind" — and a declared kind is a field with its own name, not an
    existing field pressed into a meaning it does not have. Right behaviour obtained by
    mislabelling data is the stored-table trap in the vocabulary dimension: the answer is
    correct and the record of why is a lie."""

    def _regime_of(self, name):
        d = (self.views.op_definitions().get(name) or {}).get("definition") or {}
        return d.get("authority_regime")

    def test_no_files_op_borrows_the_attenuation_regime(self):
        for op in ("FILE-CLOSE", "FILE-UNLOCK", "FILE-OPEN", "FILE-WRITE"):
            self.assertIsNone(self._regime_of(op),
                              "%s declares an authority_regime — if this is the release "
                              "shortcut, it is refused; §11.1c wants a declared kind" % op)

    def test_the_guard_can_fail_because_the_shortcut_really_works(self):
        """THE CONTROL. A guard that cannot fail is not a guard (the A4b precedent from
        this EP's own amend pass). This shows the borrowed regime DOES skip the fold, in
        a disposable world, which is what makes the guard above worth having."""
        self.call("FILE-CREATE", path="/b.txt", perm="644")
        real = self.views.op_definitions
        calls = []

        def borrowed(as_of=None):
            defs = dict(real(as_of))
            entry = dict(defs["FILE-CLOSE"])
            d = dict(entry["definition"])
            d["authority_regime"] = "attenuation-family"
            entry["definition"] = d
            defs["FILE-CLOSE"] = entry
            return defs
        real_covers = self.views.covers

        def spy(account, action, info_kind, space, as_of=None):
            calls.append(action)
            return real_covers(account, action, info_kind, space, as_of=as_of)
        self.views.op_definitions = borrowed
        self.views.covers = spy
        try:
            self.call("FILE-CLOSE", path="/b.txt", inode=self.ino("/b.txt"))
        finally:
            self.views.op_definitions = real
            self.views.covers = real_covers
        self.assertNotIn("FILE-CLOSE", calls,
                         "the borrowed regime did not skip the fold — then the guard "
                         "above is guarding nothing and this control has found that out")


# =====================================================================================
# 5. THE SUBSET IS RIGHT AND THE INVALIDATION IS NOT — two halves, tested apart
# =====================================================================================

class TestFoldsAreInvalidatedByEveryAppend(W8Case):
    """design/36 ADDENDUM C's rule is MET: every per-act fold reads a governance subset.
    What the guest measured is that the folds still cost 13–16% of an act, and the reason
    is one layer over the rule: the memo is invalidated by EVERY append, so a FILE-OPEN
    — which cannot change one word of law — forces `active_rules` to be recomputed.

    The two halves are tested apart on purpose. Confusing them is how ADDENDUM C's own
    finding was under-scoped once already: the subset being right does not make the cost
    governance-proportional if the invalidation is not.

    DOCUMENTED FLIP (EP-28B W3, 2026-07-30): the second half is FIXED. The class name and the
    docstring above are left standing as the record of the finding, and the two rows below are
    inverted — a custody append no longer invalidates the law memo, and the fold body no longer
    runs. The positive statement of the property, with the undeclared-memo divergence beside it,
    is `T-VIEWS-NOT-INVALIDATED-BY-UNRELATED-APPEND` in `tests/test_ep28b.py`."""

    def _law_subset_size(self):
        return len(self.store.record_projection("law")._seqs)

    def test_the_law_subset_does_not_grow_with_file_traffic(self):
        """ADDENDUM C's rule, holding. Two hundred custody records move the subset by
        nothing, because none of them declares a rule_id."""
        self.call("FILE-CREATE", path="/s.txt", perm="644")
        self.views.active_rules()
        before = self._law_subset_size()
        for i in range(100):
            self.call("FILE-OPEN", path="/s.txt", inode=self.ino("/s.txt"), flags=0)
            self.call("FILE-CLOSE", path="/s.txt", inode=self.ino("/s.txt"))
        self.views.active_rules()
        self.assertEqual(self._law_subset_size(), before)

    def test_a_custody_append_no_longer_invalidates_the_law_memo(self):
        """FLIPPED AS THE PIN DIRECTED (EP-28B W3): "if the raise landed, flip this test."

        `Views._bump` still fires on every append and the APPEND generation still moves on
        every one of them — that is the undeclared memos' key and it is unchanged. What moved
        is that `active_rules` is keyed on its OWN generation now, and a custody record enters
        no law subset. Both counters are read here so the row cannot pass by the global counter
        having stopped moving, which would be a different and much worse change."""
        self.call("FILE-CREATE", path="/s.txt", perm="644")
        self.views.active_rules()
        gen = self.views._memo_gen
        law_gen = self.views._generation_of("active_rules")
        self.call("FILE-OPEN", path="/s.txt", inode=self.ino("/s.txt"), flags=0)
        self.assertGreater(self.views._memo_gen, gen,
                           "the append generation stopped moving — that is not this change")
        self.assertEqual(self.views._generation_of("active_rules"), law_gen,
                         "a custody append still invalidates the law memo")

    def test_the_absence_of_a_recompute_is_real_and_not_only_a_counter_standing_still(self):
        """THE CONTROL, FLIPPED WITH ITS ROW (EP-28B W3). It counted the fold BODY rather than
        the key, because a counter that moved while the fold was served from cache would have
        made the finding imaginary. The same reasoning applies to the fix and is why this row
        survives the flip instead of being deleted: a generation that stands still while the
        fold recomputes anyway would make the FIX imaginary. The body is still what is counted.

        The last two lines keep the column able to fail: a law record lands, and the fold runs."""
        self.call("FILE-CREATE", path="/s.txt", perm="644")
        self.views.active_rules()
        runs = []
        real = self.views._active_rules

        def spy(as_of=None, source=None):
            runs.append(1)
            return real(as_of, source)
        self.views._active_rules = spy
        try:
            self.views.active_rules()                    # memo hit: no recompute
            self.assertEqual(len(runs), 0)
            self.call("FILE-OPEN", path="/s.txt", inode=self.ino("/s.txt"), flags=0)
            self.views.active_rules()                    # after a custody append: still no recompute
            self.assertEqual(len(runs), 0,
                             "the law fold re-derived law that a FILE-OPEN cannot have changed")
            self.gate.execute("CREATE-RULE", "owner",
                              {"rule_id": "W8-PROBE-LAW", "polarity": "-", "when": [],
                               "then": []})
            self.views.active_rules()                    # after a LAW record: recompute
            self.assertGreater(len(runs), 0, "a law record did not invalidate the law memo")
        finally:
            self.views._active_rules = real


if __name__ == "__main__":
    unittest.main()
