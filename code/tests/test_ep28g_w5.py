# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-28G W5 — ASSUMPTIONS AND SKIPS, DECLARED (the scaling rule, §A33).

A declaration in an entry is read once; a declaration that can RED is read every time. So the
scale assumptions this EP's rows were taken under, and the conditions its derivation depends
on, are written here as assertions wherever an assertion is possible, and as a named skip
where it is not.

THE THREE WRONG REFERENCES THIS PLAN NAMES also get their structural detectors here, because
each is an absence and an absence needs a home that can fail:

  1. THE BIG LOCK — the region held across the durability wait. Its detectors are the pair in
     `test_ep28g_w1.py` (the universal at the barrier) and `test_ep28g_w4.py` (the
     existential). Cited here, not rebuilt.
  2. RESERVATION STATE — allocating ahead of the record. Detector: no allocation state
     outside the fold, structurally, on the files this EP touched.
  3. OPTIMISTIC CONCURRENCY — decide freely, detect the collision, retry. Detector: no retry
     loop in what this EP built, and refusal citations deterministic under interleaving (the
     behavioural half is `test_ep28g_w2.py`'s determinism row).
"""

import ast
import hashlib
import importlib.util
import os
import shutil
import sys
import tempfile
import traceback
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))

from kernel import commit as commit_mod                          # noqa: E402
from kernel import gate as gate_mod                              # noqa: E402
from kernel import store as store_mod                            # noqa: E402
from kernel.compose import build_full_kernel                     # noqa: E402

#: WHAT THIS EP'S ROWS WERE EXERCISED AGAINST, stated as data so it is checkable rather than
#: remembered. Store sizes are RECORD COUNTS and submitter counts are THREADS; both are
#: countables and neither is a duration.
EXERCISED = {
    "store_sizes_records": (0, 137, 167),      # a bare store; a founded world; a founded
                                               # world after this EP's own concurrent drives
    "submitter_counts": (1, 2, 3, 4, 6, 8),
    "widths": ("shipped (16)", "GOVOS_COMMIT_WIDTH=1"),
    "world_lifetime": "one process, disposable temp directories, never reused",
    "substrate": "the host filesystem under /tmp on this laptop",
}

#: WHAT THE FAST LOOP SKIPS, each with the reason it is not this EP's to close.
SKIPPED = {
    "the kernel channel's many-in-flight":
        "EP-28C W4's, in the guest. This EP is engine work on the host suite: no kernel code "
        "was compiled, loaded or run, and the guest was untouched.",
    "the physical-disk substrate":
        "the standing §A33 condition. ADDENDUM L's floor is a property of a qcow2 image on "
        "virtio, and every figure this estate holds carries its substrate or it is a claim "
        "about a virtual disk passed off as a claim about gov-os.",
    "reboot-class durability":
        "the power-cut battery is EP-28C W5's and runs in the guest. This EP asserts the "
        "ORDER of a barrier and a reply, never that a cut leaves what it should.",
    "submitter counts beyond eight":
        "the counts above are what the rows drive. Nothing here claims a curve.",
    "the blob composition":
        "RAISED BY DESIGN. Prefix durability is structural for the RECORD FILE alone; content "
        "blobs are a second file, so the composition -- content durable before the record that "
        "names it -- is a SEPARATE property and the law of it is EP-30's intake. "
        "[UPDATED EP-30-C1R, 2026-08-21, board :1506. This entry read 'the governed path "
        "already writes blob-durable-before-record at mount.py:49-69, and NO TEST ASSERTS "
        "THAT COMPOSITION'. BOTH HALVES WERE FALSE BY THEN: EP-30-C0 moved the barrier out of "
        "the bridge into `kernel.blobs.BlobStore.put`, and the span was stale the moment it "
        "was written -- cite by SYMBOL never by SPAN (:1359). The composition IS now asserted, "
        "by `test_the_blob_composition_DURABLY_ORDERS_CONTENT_BEFORE_THE_RECORD_NAMING_IT` in "
        "this file, as a PROPERTY and not as a site. WHAT STAYS OPEN AND IS WHY THIS ENTRY "
        "STAYS: that row observes the ORDER durability arrives in; it does not assert that a "
        "power cut leaves what it should, which is the reboot-class skip above.]",
}


class DeclarationsCase(unittest.TestCase):

    def test_the_single_record_file_condition_on_prefix_durability_holds_here(self):
        """THE CONDITION THE WHOLE DERIVATION RESTS ON, asserted rather than assumed: the
        region may end before the barrier because durability arrives in FILE ORDER, and that
        is structural for ONE append-only file written by one writer through one held
        descriptor. It is not structural for two files.

        So: exactly one write site, one barrier site, one open site, and the barrier's subject
        is the descriptor that site holds. `test_ep28c_w1` asserts the same counts for its own
        reason; asserting them here too is deliberate — this EP's derivation depends on them,
        and a dependency stated only in prose is a dependency nobody re-checks."""
        src = open(store_mod.__file__, encoding="utf-8").read()
        self.assertEqual(src.count("self._fh.write("), 1)
        self.assertEqual(src.count("os.fdatasync("), 1)
        self.assertEqual(src.count('self.file_path.open("a"'), 1)

    #: THE ORDER THE COMPOSITION MUST PRODUCE, stated as data so the predicate below reads
    #: as a property and not as a spelling of three syscalls: the blob's BYTES are made
    #: durable, then the blob's NAME is made durable, and only then is the record that names
    #: the blob made durable. A reader recovering after a cut at any point never meets a
    #: record naming content that is not there.
    BLOB_BEFORE_RECORD = ("the blob's bytes", "the blob's name", "the record naming it")

    def _durability_order(self, tmp, suppress_blob_barrier=False):
        """DRIVE ONE GOVERNED ACT THAT CONTENT-ADDRESSES ITS PAYLOAD AND REPORT THE ORDER
        DURABILITY ACTUALLY ARRIVED IN. The subject is the COMPOSITION — whatever module the
        barrier lives in — because that is what the property is about.

        `suppress_blob_barrier` is the regression this row exists to catch, PRODUCED rather
        than described: the blob barrier removed from the composition with nothing replacing
        it. THE REMOVAL IS AT THE CALL SITE AND NEVER AT THE OBSERVER — a first draft of this
        row suppressed the fsync inside the wrapper while still recording it, so the trace
        was unchanged and the control could not fail. Its own red world caught that, which is
        the whole reason the red world is here."""
        record, blobdir = os.path.join(tmp, "rec.jsonl"), os.path.join(tmp, "blobs")
        store, gate, _views, blobs, _v = build_full_kernel(record, blobdir)
        self.addCleanup(store.close)
        if suppress_blob_barrier:
            def _put_with_no_barrier(data):
                """`BlobStore.put` with BOTH durability waits deleted and nothing else
                changed: the bytes land, the name lands, neither is forced. The path is
                taken from the store's own resolver so this world differs from the real one
                in the barrier and in nothing else."""
                if isinstance(data, str):
                    data = data.encode("utf-8")
                digest = "sha256:" + hashlib.sha256(data).hexdigest()
                path = blobs._path(digest)
                path.parent.mkdir(parents=True, exist_ok=True)
                with open(str(path), "wb") as fh:
                    fh.write(data)
                return digest
            blobs.put = _put_with_no_barrier
        gate.execute("CREATE-ACCOUNT", "SYSTEM",
                     {"account_id": "w5", "actor_class": "process"})
        gate.execute("COMMS-OPEN", "w5",
                     {"channel": "sock:w5", "entity": "w5", "role": "user-facing"})
        seen, real_fsync, real_fdatasync = [], os.fsync, os.fdatasync

        def _named(fd):
            try:                                  # the descriptor's own path, at call time
                return os.readlink("/proc/self/fd/%d" % fd)
            except OSError:                       # pragma: no cover - unreachable on Linux
                return ""

        def _fsync(fd):
            path = _named(fd)
            if path.startswith(blobdir):
                seen.append("the blob's name" if os.path.isdir(path) else "the blob's bytes")
            return real_fsync(fd)

        def _fdatasync(fd):
            if _named(fd) == record:
                seen.append("the record naming it")
            return real_fdatasync(fd)

        os.fsync, os.fdatasync = _fsync, _fdatasync
        try:
            sent = gate.execute("COMMS-SEND", "w5",
                                {"channel": "sock:w5", "message": "durable-before", "to": "w5"})
        finally:
            os.fsync, os.fdatasync = real_fsync, real_fdatasync
        self.assertTrue(blobs.has(sent["payload"]["message_hash"]),
                        "the act did not content-address its payload, so this drive says "
                        "nothing about the composition")
        return tuple(seen)

    def test_the_blob_composition_DURABLY_ORDERS_CONTENT_BEFORE_THE_RECORD_NAMING_IT(self):
        """[REWRITTEN AS A PROPERTY ASSERTION — EP-30-C1R, 2026-08-21, on the ruling at board
        `:1506`, and it is NOT a cause-mapped repair. Renamed from
        `test_the_blob_composition_is_an_assumption_and_is_NOT_asserted_by_this_ep`.

        WHAT WAS WRONG WITH THE ROW, in its own ruling's words: its INTENT was to keep an open
        item visible; its MECHANISM was to assert a SITE — that `src/bridge/mount.py` exists
        and that the literal `fsync` appears in its body. Those are not the same thing, and
        the gap was the whole defect. A TRIPWIRE THAT WATCHES A SITE CANNOT DISTINGUISH THE
        DEFECT FROM THE CURE, BECAUSE BOTH MOVE THE SITE: EP-30-C0 moved the barrier INTO
        `src/kernel/blobs.py`, which is the raise being RESOLVED, and the row reddened with a
        message — "the blob path named by the raise no longer syncs" — that is true in that
        world and in the regression world and means opposite things in the two.

        THE CURE IS `:1359` ONE LEVEL UP: cite by SYMBOL never by SPAN became CITE BY
        PROPERTY, NEVER BY SITE. The property is the ORDERING — content durable before the
        record that names it — and it PASSES after C0 while still REDDING on the regression,
        which is one assertion separating both directions where the old row separated
        neither. THE NOTIFICATION HALF IS KEPT: the declaration still stands in `SKIPPED`, so
        a later reader still meets the open item rather than a green suite that never
        mentioned it.

        A9, BEFORE AND AFTER, PLAINLY: BEFORE this row claimed `mount.py` exists and contains
        the string `fsync`. AFTER it claims the governed composition makes content durable
        before the record naming it. THAT IS A CHANGED CLAIM AND IT IS THE RULING, not a
        range closure — which is exactly why `:1573` CLAIM 3 kept this id out of the
        cause-mapped sweep and why a sweep touching it would be `:1516`'s deletion under
        another name."""
        self.assertIn("the blob composition", SKIPPED)
        tmp = tempfile.mkdtemp(prefix="ep28g-w5-durable-")
        self.addCleanup(shutil.rmtree, tmp, True)
        self.assertEqual(self._durability_order(tmp), self.BLOB_BEFORE_RECORD,
                         "the governed composition no longer makes content durable before "
                         "the record that names it — a reader recovering after a cut can "
                         "meet a record naming content that is not there")
        # THE SAME ASSERTION, DRIVEN AGAINST THE REGRESSION IT EXISTS TO CATCH. Without this
        # the green above cannot distinguish "the property holds" from "the drive never
        # looked", which is the failure the old site-row shipped with.
        gone = tempfile.mkdtemp(prefix="ep28g-w5-nobarrier-")
        self.addCleanup(shutil.rmtree, gone, True)
        self.assertEqual(self._durability_order(gone, suppress_blob_barrier=True),
                         ("the record naming it",),
                         "removing the blob barrier did not change what this row observes, "
                         "so its green above proves nothing")

    def test_the_exercised_scale_is_what_the_rows_actually_drive(self):
        """The declaration checked against the world rather than trusted: a founded world is
        the size this file claims, within the tolerance a growing founding pack allows."""
        d = tempfile.mkdtemp(prefix="ep28g-w5-")
        self.addCleanup(shutil.rmtree, d, True)
        store, gate, views, blobs, _ = build_full_kernel(
            os.path.join(d, "rec.jsonl"), os.path.join(d, "blobs"))
        self.addCleanup(store.close)
        founded = len(store.all())
        self.assertGreater(founded, 100,
                           "a founded world holds %d records and this EP's declaration says "
                           "about 137 — the declared scale has drifted" % founded)
        self.assertLess(founded, 400, founded)
        self.assertIn(1, EXERCISED["submitter_counts"],
                      "the single-caller case must be among what was exercised, because it "
                      "is the case the whole estate ran on until this EP")

    def test_the_skips_are_named_and_none_of_them_is_silently_closed(self):
        """A skip with no reason is a skip nobody can re-open. Each entry carries why it is
        not this EP's, and the kernel-channel entry is the one that matters: this pass loaded
        nothing anywhere."""
        for name, reason in SKIPPED.items():
            self.assertGreater(len(reason), 40, "%r is skipped without a reason" % name)
        self.assertIn("the kernel channel's many-in-flight", SKIPPED)
        self.assertIn("EP-28C W4", SKIPPED["the kernel channel's many-in-flight"])


class RefusedReferencesCase(unittest.TestCase):
    """THE THREE WRONG REFERENCES, with the detectors the plan names. Each is an ABSENCE, and
    an absence asserted over an empty subject passes vacuously (§A38) — so every row below
    first proves its subject is non-empty."""

    TOUCHED = ("gate.py", "store.py", "commit.py")

    def _sources(self):
        out = {}
        for name in self.TOUCHED:
            path = os.path.join(REPO, "src", "kernel", name)
            out[name] = open(path, encoding="utf-8").read()
        return out

    @staticmethod
    def _identifiers(src):
        """Every identifier in the EXECUTABLE BODY, read through `ast` so comments and
        docstrings are outside the subject by construction — the EP-28C reader's distinction,
        and it is load-bearing here because these files DISCUSS the traps they refuse."""
        names = set()
        for node in ast.walk(ast.parse(src)):
            for attr in ("id", "attr", "name", "arg"):
                v = getattr(node, attr, None)
                if isinstance(v, str):
                    names.add(v.lower())
        return names

    def test_the_subject_is_not_empty(self):
        srcs = self._sources()
        for name, src in srcs.items():
            self.assertGreater(len(self._identifiers(src)), 50,
                               "%s parsed to almost nothing — the guards below would pass "
                               "over an empty subject" % name)

    def test_trap_two_no_allocation_state_outside_the_fold(self):
        """RESERVATION STATE, refused. The template is to fix a duplicate-identity race by
        pre-allocating numbers the record does not carry — a counter, a reservation table.
        Taking it erases the record as the sole allocator: kill the process, replay, and the
        reservations are gone while the records cite them.

        This EP did not take it, and it did not need to: the ruling that sent the port's
        `next_ino` back to EP-28C W4 is the same shape — the fix REMOVES the bad allocation
        rather than stretching a lock over it, because `FILE-CREATE`'s own definition maps an
        absent inode to `"$path"`, unique per path BY CONSTRUCTION."""
        for name, src in self._sources().items():
            names = self._identifiers(src)
            for token in ("reserve", "reservation", "preallocate", "pre_allocate",
                          "next_ino", "allocate_id", "pending_ids"):
                self.assertNotIn(token, names,
                                 "%s defines or reads %r — allocation state the record "
                                 "cannot derive" % (name, token))

    def test_trap_three_no_retry_loop_in_what_this_ep_built(self):
        """OPTIMISTIC CONCURRENCY, refused. The template from every database: let decides
        race, catch the conflict at append, re-run the loser. Taking it erases what a refusal
        IS here — the gate refuses citing a rule, deterministically from the record and the
        act, never 'try again, the world moved'. A retried decide is a decision whose recorded
        basis depends on scheduler timing.

        AND ADDENDUM 1 MAKES IT UNSTATABLE RATHER THAN MERELY UNWANTED: the decision IS the
        record, so there is no decide separate from the record to retry. A retry is a
        DIFFERENT record produced against a different world."""
        for name, src in self._sources().items():
            names = self._identifiers(src)
            for token in ("retry", "retries", "attempt_again", "backoff", "reattempt"):
                self.assertNotIn(token, names,
                                 "%s defines or reads %r — the loser of a race is being "
                                 "re-run instead of refused" % (name, token))

    def test_red_world_a_decoy_carrying_both_traps(self):
        """RED WORLD for the two structural guards, GENERATED and run through the SAME reader
        and the SAME assertions — a guard whose failing case was never exhibited is a guard
        nobody has seen fail. Written as a decoy IN CODE rather than in a comment, which is
        the distinction the reader makes."""
        decoy = ("def mint(table):\n"
                 "    reservation = table.reserve()\n"
                 "    for retry in range(3):\n"
                 "        pass\n"
                 "    return reservation\n")
        names = self._identifiers(decoy)
        with self.assertRaises(AssertionError):
            self.assertNotIn("reserve", names, "allocation state the record cannot derive")
        with self.assertRaises(AssertionError):
            self.assertNotIn("retry", names, "the loser of a race is being re-run")
        # AND THE COMPLEMENT: the same tokens in a COMMENT are not the machinery.
        commented = "# no reserve table and no retry loop lives here\ndef mint():\n    return None\n"
        self.assertNotIn("reserve", self._identifiers(commented))
        self.assertNotIn("retry", self._identifiers(commented))

    def test_the_region_carries_no_governance_content(self):
        """The construct is ENGINE, not law-data: it changes no verdict, no citation, no
        record content and no order. Asserted the way EP-28C asserted it of the calibration —
        the construct's own body cannot reach a rule, a grant, an actor or a refusal."""
        tree = ast.parse(open(gate_mod.__file__, encoding="utf-8").read())
        region = next(n for n in ast.walk(tree)
                      if isinstance(n, ast.ClassDef) and n.name == "DecideRegion")
        # IDENTIFIERS, not a dump: a dump carries the DOCSTRING, and this class's docstring
        # explains what the region is for in exactly the vocabulary the guard forbids. A
        # guard that reds when someone improves a comment is a guard that will be deleted.
        names = set()
        for node in ast.walk(region):
            for attr in ("id", "attr", "name", "arg"):
                v = getattr(node, attr, None)
                if isinstance(v, str):
                    names.add(v.lower())
        self.assertTrue(names, "the region's body parsed to nothing")
        for token in ("rule", "grant", "actor", "refuse", "cite", "record", "views"):
            self.assertNotIn(token, names,
                             "the region's body reaches %r — an engine construct carrying "
                             "governance content" % token)

    #: The only sanctioned callers of a PRIVATE route into the record — the same set
    #: `tests/test_sole_appender.py` names for `_append`, carried here verbatim rather than
    #: re-derived, because two copies of one fact drift and this one is a copy on purpose:
    #: the guard over there cannot be edited from this fence.
    SANCTIONED = {"kernel/store.py", "kernel/gate.py", "founding/install.py",
                  "kernel/protection.py"}

    def test_the_new_private_route_arrives_with_the_same_leash_as_the_old_one(self):
        """EVERY NEW POWER ARRIVES WITH ITS OWN LEASH IN THE SAME ROUND (DESIGN-SOUL §2).

        THE HOLE THIS CLOSES, stated plainly because it is this EP's own making: EP-28G
        created `store._publish` — a SECOND private route into the record — and the estate's
        sole-appender guard (`tests/test_sole_appender.py`) keys on the literal `._append(`.
        It still passes; it simply cannot see the new route. An unsanctioned file could call
        `store._publish(` and bypass the gate with every existing guard green. That is this
        estate's own recurring defect — an instrument reporting something other than its
        subject — and it would have been created by the pass that is supposed to be careful.

        MEASURED, so the raise carries its residual: there is NO live bypass today. `_publish(`
        appears in `gate.py` (the gate's one write, sanctioned) and in `store.py` (its own
        definition, and `_append`'s use of it) and NOWHERE ELSE.

        THE EXISTING GUARD IS NOT EDITED FROM HERE. It is not falsified — it passes — so it
        is outside this EP's documented-flip clause, and the enumeration binds. Extending its
        token set is RAISED. This row is the leash landing in the fence that reaches it."""
        routes = ("._append(", "._publish(")
        rogue = {}
        for root, _dirs, files in os.walk(os.path.join(REPO, "src")):
            for name in sorted(files):
                if not name.endswith(".py"):
                    continue
                path = os.path.join(root, name)
                rel = os.path.relpath(path, os.path.join(REPO, "src")).replace(os.sep, "/")
                if rel in self.SANCTIONED:
                    continue
                body = open(path, encoding="utf-8").read()
                hit = [r for r in routes if r in body]
                if hit:
                    rogue[rel] = hit
        self.assertEqual(rogue, {},
                         "unsanctioned direct callers of a private record route (they bypass "
                         "the gate): %r" % rogue)

    def test_red_world_a_rogue_caller_of_the_NEW_route_is_caught(self):
        """RED WORLD, GENERATED, and it is the whole point: a file reaching `._publish(` is
        caught by the row above. Run through the SAME predicate the row uses, on a decoy, so
        what is proven is that the new route is guarded rather than that the old one is."""
        routes = ("._append(", "._publish(")
        decoy = "def sneak(store, draft):\n    return store._publish(draft)\n"
        hit = [r for r in routes if r in decoy]
        with self.assertRaises(AssertionError):
            self.assertEqual(hit, [], "unsanctioned direct caller of a private record route")
        # AND THE OLD ROUTE'S OWN RED, so the pair is symmetric.
        decoy_old = "def sneak(store, draft):\n    return store._append(draft)\n"
        self.assertEqual([r for r in routes if r in decoy_old], ["._append("])
        # AND THE COMPLEMENT: a file naming neither is clean.
        self.assertEqual([r for r in routes if r in "def clean():\n    return None\n"], [])

    def test_the_new_private_route_is_covered_by_the_estates_sole_appender_guard(self):
        """DISCHARGED 2026-08-03 by EP-28C W4a, and FLIPPED here rather than deleted, per
        that EP's AMENDMENT 6 §6.2 — "the G builder's standing raise-row flips as the
        discharge evidence, a documented flip mapped to this item."

        WHAT THIS ROW USED TO SAY, kept because a withdrawn expectation is worth more on the
        record than an absent one: it asserted that `tests/test_sole_appender.py` still named
        `._append(` and not `._publish(`, so that extending the guard's token set would RED it
        and announce its own closure (§A47). It fired. It fired for the right reason and by
        the wrong mechanism, and that is the finding underneath the discharge.

        THE MECHANISM WAS ITSELF A TEXT PROXY OVER THE GUARD FILE. The repair ruled at the
        EP-28G close was NOT to add a second literal — it was to retire the scan and assert
        the property on BEHAVIOUR. A discharge that REMOVES text proxies rather than adding
        one is invisible to a trigger that watches for a token appearing. This one only
        reddened because the re-aimed file happens to carry `._publish(` inside a red-world
        decoy, which is luck rather than design: had the decoy assembled the attribute name
        at run time — as one of the three now does — the raise would have been discharged in
        full with this row still green about an open item. An expiring row inherits the
        blindness of whatever it keys on.

        WHAT IT ASSERTS NOW is the discharge itself, by EXECUTION rather than by reading the
        guard's text: a rogue reaching the route THIS EP CREATED is caught by the estate's
        guard. Same subject, no proxy."""
        # `discover -s tests` puts this directory on the path; a direct
        # `python3 -m unittest tests.test_ep28g_w5` does not. Both invocations run this row.
        if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import test_sole_appender as guard

        root = tempfile.mkdtemp(prefix="ep28g-discharge-")
        self.addCleanup(shutil.rmtree, root, True)
        with open(os.path.join(root, "rogue_module.py"), "w", encoding="utf-8") as f:
            f.write(guard.ROGUE_NEW_ROUTE)
        d = tempfile.mkdtemp()
        store, _gate, _views, _blobs, _sv = build_full_kernel(
            os.path.join(d, "record.jsonl"), os.path.join(d, "blobs"))
        self.addCleanup(store.close)
        stacks = []
        store.on_append(lambda _rec: stacks.append(traceback.extract_stack()))

        spec = importlib.util.spec_from_file_location(
            "ep28g_discharge_rogue", os.path.join(root, "rogue_module.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        before = len(store.all())
        mod.sneak(store, {"actor": "rogue", "action": "SNEAK", "rule_cited": "ROOT-NEG-1"})
        store._await_durable()

        self.assertEqual(len(store.all()), before + 1,
                         "the rogue did not append — this row would prove nothing")
        self.assertEqual(guard.unsanctioned_entries(stacks, root), ["rogue_module.py"],
                         "the estate's sole-appender guard does not catch a rogue reaching "
                         "the route EP-28G created — the raise is NOT discharged")

    def test_the_calibration_is_untouched_by_this_ep(self):
        """The lever's own constants, unchanged: this EP moved where a record is published,
        not how wide a batch may be or how long the window is."""
        self.assertEqual(commit_mod.BATCH_WIDTH_CAP, 16)
        self.assertEqual(commit_mod.BATCH_WINDOW_S, 0.002)
        self.assertEqual(commit_mod.WIDTH_ENV, "GOVOS_COMMIT_WIDTH")
        self.assertEqual(commit_mod.WINDOW_ENV, "GOVOS_COMMIT_WINDOW_MS")


if __name__ == "__main__":
    unittest.main()
