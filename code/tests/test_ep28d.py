# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-28D — the conformance instrument repaired by a seat it is not grading.

The acceptance battery the EP names before code:

  W1  T-THE-INSTRUMENT-OWNS-NO-DESCRIPTOR-THE-ROW-FREED
      `files.close`'s subject is that closing a released descriptor NUMBER returns
      EBADF, and its `close` is a SUBJECT call, so the fixture appends a record
      between the row's two closes. A store that opens its write descriptor on
      first append allocates it there — and the lowest free number at that moment
      is exactly the one the first close released. The failure is reproduced in
      BOTH directions rather than described: without the fixture's
      `establish_record_descriptor` the row's EBADF answer disappears and the
      instrument's own record path is the thing that breaks; with it, the row
      answers EBADF and the instrument's descriptor set is unchanged across the
      row. An instrument repair whose failure mode is not reproduced is a repair
      nobody can check.

      THE STORE IS NOT TOUCHED AND IS NOT ALLOWED TO BE. `src/` is a STOP in this
      EP, entire, so the held descriptor arrives here as a TEST DOUBLE over the
      real `EventStore` — one variable changed, the descriptor's lifetime, with the
      record still written by the real `_append`. Re-validating the descriptor and
      reopening on EBADF was written at EP-28B and refused, because it repairs
      another component's double-release silently inside the instrument the
      campaign depends on; the row below pins that no such retry exists.

  W2  T-THE-TARGET-NAMES-THE-WORLD-THAT-EXISTS
      The kernel-mount descriptor's five paths name `<HOME>/govos-m3`, the
      world EP-28B W4 moved to and proved survives a reboot, and no longer name
      `/tmp/govos-m3`, which the guest clears at boot. The two paths inside
      `replay.command` carry no `~`, because they are handed to a subprocess with
      no shell and nothing expands them — the same defect design/10 §11.2b records
      once already, where a `~` in a descriptor addressed a directory literally
      named `~` and the harness reported ABI 40 of 40 against it.

WHAT THIS FILE DOES NOT ASSERT, stated rather than left as an absence. It makes no
claim about the thirteen red rows of EP-28's conformance figures, about the stale
substring assertion at `tests/test_ep28.py:321`, or about anything else visible in
the conformance tree. Each is a RAISE. This seat's whole legitimacy is that it
repairs an instrument it is not being graded by, and the moment it repairs
something it IS graded by, that separation is gone and the repair is worth nothing.

[DATED NOTE, 2026-08-02 — EP-28H, so the paragraph above is read as the record of
EP-28D's fence rather than as a live statement of what is open. Two of the three
things it names have since been taken by other passes: the substring assertion at
`tests/test_ep28.py:321` is re-aimed at the parsed descriptor list by EP-28H item 2,
and this file's own `tearDown` and honest-cap row are EP-28H items 1 and 6. The
thirteen red stance-4 conformance rows remain a raise, homed at EP-33 item 27. The
sentence above was right when written and its subject moved; saying so here is
cheaper than a later reader re-deriving why a closed raise reads as open.]
"""

import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from kernel.store import EventStore  # noqa: E402
from tools.conformance.fixtures import fixture_shim  # noqa: E402
from tools.conformance.harness import probe as probe_mod, rows as rows_mod  # noqa: E402

ROWS_DIR = REPO / "tools" / "conformance" / "rows"
TARGETS_DIR = REPO / "tools" / "conformance" / "targets"
KERNEL_MOUNT = TARGETS_DIR / "ep28-kernel-mount.json"

#: The world EP-28B W4 moved to, and the one it moved off.
WORLD = "<HOME>/govos-m3"
ABANDONED = "/tmp/govos-m3"


class _HeldDescriptorStore(EventStore):
    """The withdrawn change, kept as a TEST DOUBLE so its failure can be driven.

    EP-28B W2 wrote a store that holds its record-file descriptor instead of
    re-opening it per append, measured it, and withdrew it in the same session for
    a reason that had nothing to do with the store. This double reproduces the ONE
    property that mattered — the descriptor is allocated LAZILY, on first append,
    and then HELD — while the record itself is still written by the real
    `EventStore._append`. One variable, which is the same discipline the
    wrong-errno fixture keeps: a difference nobody can localise proves nothing.

    The barrier on the held descriptor is what makes its loss visible, and it is
    the same call the store already issues on the descriptor it opens per append.
    """

    def __init__(self, path):
        super().__init__(path)
        self._held = None

    def _append(self, ev):
        if self._held is None:
            # Lazily allocated, and the number it gets is whatever is lowest-free
            # at this instant — which is the whole finding.
            self._held = open(self.file_path, "a", encoding="utf-8")
        record = super()._append(ev)
        os.fdatasync(self._held.fileno())
        return record

    @property
    def held_fd(self):
        return None if self._held is None else self._held.fileno()

    def close_held(self):
        if self._held is not None:
            try:
                self._held.close()
            except OSError:
                pass
            self._held = None

    def close(self):
        """BOTH descriptors, so one call releases everything this double opened
        [EP-28H item 1, 2026-08-02]. The double adds a descriptor of its own on top of
        the one `EventStore` now holds, and a `tearDown` that closed only the extra one
        left the real store's behind — which is what the eight rows were reporting."""
        self.close_held()
        super().close()


def _open_descriptors():
    """The process's own descriptor table, read from the kernel's answer rather than
    from anything this file tracked.

    AND THE MEASUREMENT SUBTRACTS ITS OWN DESCRIPTOR, which is not a nicety — it is
    §11.2b firing a seventh time, inside this file, found by driving the
    reproduction. Reading `/proc/self/fd` requires a descriptor ON `/proc/self/fd`,
    so the enumeration lists the enumeration: a plain `os.listdir("/proc/self/fd")`
    answers `{0, 1, 2, 3}` on a process holding only the standard three, and the
    row's `open` then appears to have been given 4 when the kernel gave it 3. The
    first version of this file measured that way and reported the mechanism absent
    when it was present. The descriptor is opened explicitly here for the one reason
    that an explicit one can be NAMED and removed; an implicit one cannot.

    So the enumeration excludes, BY WHAT THEY POINT AT, every descriptor that is a
    handle on the descriptor table — the one the listing opened, and the duplicate
    `fdopendir` makes of it. Excluding a NUMBER instead was tried first and was
    wrong twice over: it left the duplicate behind, and a number is exactly the
    thing under measurement here.
    """
    table = "/proc/%d/fd" % os.getpid()
    out = set()
    for name in os.listdir("/proc/self/fd"):
        try:
            target = os.readlink("/proc/self/fd/" + name)
        except OSError:
            continue  # gone between the listing and the read: the listing's own
        if target == table:
            continue
        out.add(name)
    return out


def close_row():
    """The `files.close` assertion, compiled the way the harness compiles it. Rows
    are data; this test authors none."""
    _groups, all_rows = rows_mod.load_all(str(ROWS_DIR))
    for a in all_rows:
        if a.row_id == "files.close":
            return a
    raise AssertionError("no files.close row — the row this EP is about is gone")


class DescriptorCase(unittest.TestCase):
    """One `files.close` run, driven through the FIXTURE'S OWN wrapper so the
    interleaving is the real one and not a re-enactment of it."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep28d-")
        self.record = Path(self.dir) / "record.jsonl"
        self.scratch = os.path.join(self.dir, "scratch")
        os.makedirs(self.scratch, exist_ok=True)
        self.assertion = close_row()
        self._stores = []
        self._fds_at_entry = _open_descriptors()

    def tearDown(self):
        """THE BATTERY OWNS NOTHING ON ITS SUBJECT, and this EP is the last place
        that could be left to good intentions: its whole subject is an instrument
        that failed exactly this rule. A held descriptor left behind by one test
        occupies a low number in the next one, the row's `open` is handed a higher
        one, and the interleaving stops reproducing — which is how a battery
        measuring descriptors makes its own findings depend on test order. Found
        that way, by this file, on this file.

        AND IT CLOSES THE REAL STORE, NOT ONLY THE DOUBLE'S EXTRA DESCRIPTOR
        [EP-28H item 1, 2026-08-02]. When this file was written, `EventStore`
        re-opened the record file per append and owned no descriptor between them, so
        closing the double's held one was closing everything the test had opened.
        EP-28C W3 gave the real store a HELD descriptor, and from that moment the
        assertion below started reporting a TRUE fact: every test in this class ended
        holding one more descriptor than it started with, and the next test started
        higher (the leaked numbers ran 7, 10, 12, 13, 14, 16, 17, 18 in the reading
        this repair was measured against). THE ASSERTION DID NOT MOVE AND MUST NOT —
        it is the proof the lifecycle was fixed, not the thing that was wrong.

        `EventStore.close()` is idempotent and releases the held descriptor, so the
        close is deterministic here rather than left to a finalizer at some later
        collection point. THAT IS NOT A FIX FOR THE FINALIZER: the product defect
        (an abandoned store closing a raw descriptor NUMBER at an arbitrary GC point,
        `src/kernel/store.py:563`) is untouched by this line and is carried as an
        intake at `planning/exec/EP-28C.md` AMENDMENT 4 §4.2. This removes the
        estate's own OCCASION for it and says nothing about a deployed process.
        """
        for store in self._stores:
            store.close()
        shutil.rmtree(self.dir, ignore_errors=True)
        self.assertEqual(
            _open_descriptors(),
            self._fds_at_entry,
            "this test ended holding descriptors it did not start with",
        )

    def held_store(self):
        store = _HeldDescriptorStore(self.record)
        self._stores.append(store)
        return store

    def real_store(self):
        """The store this file does not double, REGISTERED so `tearDown` closes it
        [EP-28H item 1, 2026-08-02]. Constructing one directly and walking away was
        how the real store's held descriptor escaped the battery's own rule."""
        store = EventStore(self.record)
        self._stores.append(store)
        return store

    def run_close_row(self, store, establish):
        """Run the row exactly as `fixture_shim.main` runs it, with the one
        difference this test exists to vary: whether the store's descriptor was
        established before the row.

        The descriptor table is read at every step boundary from `/proc/self/fd`,
        through the probe's own hook, so the numbers below are the kernel's answer
        and not this file's bookkeeping. A descriptor is reported to a row by its
        allocation order rather than its integer (`probe._n_fd`), which is right for
        a conformance answer and is exactly what this measurement needs to go
        around.
        """
        if establish:
            fixture_shim.establish_record_descriptor(store)
        state = {"assertion": self.assertion, "pending": []}
        by_row = {self.assertion.row_id: self.assertion}
        original = fixture_shim.wrap_calls(store, by_row, state, "correct", {})
        seen = {}

        def hook(when, _row, i, _step):
            seen[(when, i)] = _open_descriptors()

        fds_before = _open_descriptors()
        try:
            obs = probe_mod.run_row(
                {"row_id": self.assertion.row_id, "steps": self.assertion.probe["steps"]},
                self.scratch,
                str(self.record),
                hook=hook,
            )
        finally:
            probe_mod.CALLS.clear()
            probe_mod.CALLS.update(original)
        return obs, {"before": fds_before, "after": _open_descriptors(), "steps": seen}

    @staticmethod
    def second_close(obs):
        """Step 2 is the row's subject: the second close of a number the first
        close released. Its errno IS the row's answer."""
        step = obs["steps"][2]
        assert step["call"] == "close", step
        return step["errno"]

    @staticmethod
    def appended_during(obs, i):
        """Did a record land inside this step's own bracket? The probe takes the
        bracket either side of the call, and the fixture appends only after the call
        RETURNS — so a step that raised cannot have grown its bracket."""
        before, after = obs["steps"][i]["rec"]
        return after > before

    def row_descriptor(self, fds):
        """The number the row's `open` was given, as the difference the kernel
        reports across that one step."""
        opened = fds["steps"][("after", 0)] - fds["steps"][("before", 0)]
        self.assertEqual(len(opened), 1, "step 0 opened %r" % (opened,))
        return int(next(iter(opened)))


class TestTheOldInterleavingIsReproducedAndCaught(DescriptorCase):
    """W1's failure mode, driven — and DRIVING IT CORRECTED THE RAISE THAT NAMED IT.

    EP-28B's raise says the row's EBADF answer disappears. Reproduced here, it does
    not: the row still reports EBADF at step 2, and that is WORSE rather than
    better. The row's `close` succeeds, because the number it is given is now the
    store's live descriptor; the EBADF the row reports is raised afterwards by the
    instrument's own barrier on the descriptor the row just closed. So the ABI leg
    sees the pinned answer and passes, and what it passed on is the instrument's
    failure wearing the subject's answer — §11.2b's "indistinguishable from
    success" in its exact form.

    The discriminator is the instrument's own evidence, and it is exact: a `close`
    that raises appends nothing, so a step whose record bracket GREW is a step whose
    close returned. Steps 3 and 4 close 4095 and -1 and are genuine EBADFs with
    brackets that do not grow. Step 2's grows.
    """

    def test_the_rows_ebadf_is_manufactured_and_not_measured(self):
        store = self.held_store()
        obs, _fds = self.run_close_row(store, establish=False)
        self.assertEqual(self.second_close(obs), "EBADF", "the pinned answer, apparently")
        self.assertTrue(
            self.appended_during(obs, 2),
            "no record landed in step 2's bracket — then the second close really did "
            "fail and this interleaving no longer reproduces",
        )
        for genuine in (3, 4):
            self.assertEqual(obs["steps"][genuine]["errno"], "EBADF")
            self.assertFalse(
                self.appended_during(obs, genuine),
                "step %d is a genuine EBADF and appended a record" % genuine,
            )

    def test_the_descriptor_the_store_held_is_the_one_the_first_close_freed(self):
        """The mechanism itself, not its symptom: the number the store ended up
        holding is the number the row's `open` was given."""
        store = self.held_store()
        _obs, fds = self.run_close_row(store, establish=False)
        self.assertEqual(
            store.held_fd,
            self.row_descriptor(fds),
            "the store held %r and the row opened %r"
            % (store.held_fd, self.row_descriptor(fds)),
        )

    def test_the_instruments_own_record_path_is_what_breaks(self):
        """The other half of §11.2b's damage, and the half the apparent pass hides:
        the row's second close closed the STORE's descriptor, so the next append is
        the one that gets EBADF. Reported here rather than rescued, because
        rescuing it is the refused repair."""
        store = self.held_store()
        self.run_close_row(store, establish=False)
        with self.assertRaises(OSError) as ctx:
            store._append({"actor": "fixture-target", "action": "probe",
                           "rule_cited": "FIXTURE-CUSTODY-1"})
        self.assertEqual(ctx.exception.errno, 9, "EBADF is errno 9; got %r" % ctx.exception)


class TestEstablishingTheDescriptorFirstRepairsIt(DescriptorCase):
    """The same store, the same row, the same wrapper — with the one line the EP
    directs. This is the acceptance: the row passes BECAUSE the fixture no longer
    takes a descriptor number the subject just freed."""

    def test_the_row_answers_ebadf_for_its_own_reason(self):
        """AND THE SECOND HALF OF THIS ASSERTION IS THE WHOLE OF IT. `errno EBADF`
        alone passes in BOTH worlds — that is the finding of the class above — so an
        acceptance row that checked only the errno could not tell the ruled reason
        from the manufactured one. The bracket is what tells them apart: a `close`
        that raises appends nothing, so step 2's window must NOT grow.

        Checked by neutering `establish_record_descriptor` and watching this row go
        red, which the errno-only form did not."""
        store = self.held_store()
        obs, _fds = self.run_close_row(store, establish=True)
        self.assertEqual(self.second_close(obs), "EBADF")
        self.assertFalse(
            self.appended_during(obs, 2),
            "a record landed in the second close's bracket, so that close RETURNED "
            "and the EBADF came from somewhere other than the subject",
        )

    def test_the_held_number_is_below_every_number_the_row_touches(self):
        """WHY it works, asserted rather than assumed: the descriptor is allocated
        before the row exists, so the row's own numbers are above it and the number
        the row frees is not a number the instrument wants."""
        store = self.held_store()
        _obs, fds = self.run_close_row(store, establish=True)
        self.assertLess(store.held_fd, self.row_descriptor(fds))

    def test_the_instruments_record_path_survives_the_row(self):
        store = self.held_store()
        self.run_close_row(store, establish=True)
        record = store._append({"actor": "fixture-target", "action": "probe",
                                "rule_cited": "FIXTURE-CUSTODY-1"})
        self.assertEqual(record["action"], "probe")

    def test_the_descriptor_table_is_unchanged_across_the_row(self):
        """§11.2b's second half — leave the subject as it was found — read off the
        kernel's own answer. This row's subject IS the descriptor table, so an
        instrument that ends the row holding a number it did not hold at the start
        has changed the thing it measured.

        The second assertion is what makes the first discriminating: equality alone
        also holds when the row TOOK the instrument's descriptor, because the table
        then returns to its starting shape by the wrong route. So the descriptor the
        instrument established must still be the instrument's at the end of the
        row — asserted by using it, not by inspecting it."""
        store = self.held_store()
        _obs, fds = self.run_close_row(store, establish=True)
        self.assertEqual(fds["after"], fds["before"])
        os.fdatasync(store.held_fd)
        self.assertIn(str(store.held_fd), fds["after"])


class TestTheRealStoreAsItStands(DescriptorCase):
    """The store this repair does NOT touch, pinned so the fence is visible in the
    battery.

    REFUTED TEXT, RETAINED AND DATED [EP-28H item 6, 2026-08-02 — the `_index`-comment
    precedent: a superseded statement is kept beside its correction, because the
    correction is only readable against what it corrects]. This class was written
    saying: *"`EventStore._append` re-opens the record file per append, so its claim on
    the freed number is released before the row's next step — which is why the row is
    green today, and is a property of a descriptor's LIFETIME rather than a guarantee
    the instrument was making."*

    THAT ENDED WITH EP-28C W3. The real store now opens its record descriptor lazily
    and HOLDS it (`src/kernel/store.py:559-564`), so the claim on the freed number is
    NOT released before the row's next step — and the sentence's own last clause is
    what came true: the row was green on a property of a descriptor's LIFETIME, the
    lifetime changed, and the row moved. An honest cap that names its own scope is
    what lets the change be read as a change rather than as a failure."""

    def test_the_row_answers_ebadf_with_the_repair_in_place(self):
        store = self.real_store()
        obs, fds = self.run_close_row(store, establish=True)
        self.assertEqual(self.second_close(obs), "EBADF")
        self.assertEqual(fds["after"], fds["before"])

    def test_the_row_answers_ebadf_without_it_too_and_that_is_the_honest_cap(self):
        """RE-AIMED AT THE STORE AS IT NOW STANDS [EP-28H item 6, 2026-08-02, a
        documented flip mapped to EP-28C's HELD W3].

        REFUTED TEXT, RETAINED: *"Said plainly so no reader takes this EP for a red row
        turned green: with the store as it stands the row already answered EBADF, and
        what the repair changes is which world can break it. A guard whose present
        effect is zero is still a guard — and it is checkable, which is what the two
        classes above are for."*

        THE STORE NO LONGER STANDS THAT WAY, and this row's own name scoped it to a
        store that did. The sequence is unchanged and its ENDING is not. `files.close`
        opens a descriptor, closes it, and closes it again; its `close` is a subject
        call, so the fixture appends between the two closes; that append is this
        store's FIRST, so the lazy open happens there and is handed the lowest free
        number — which is exactly the one the first close just released. What changed
        is what happens NEXT. The per-append store closed that descriptor again the
        instant the append returned, so the number was free once more and the row's
        second close answered EBADF. The store that HOLDS it does not, so the second
        close lands on a LIVE descriptor and SUCCEEDS. The assertion below reads that
        off the store rather than describing it: the number the store ends up holding
        IS the number the row's `open` was given.

        MEASURED OCCUPANCY-INDEPENDENTLY: the old answer failed identically at three
        different ambient occupancies and failed with this row run ALONE in a fresh
        process, which is the lowest occupancy there is. Neither of this pass's named
        world variables reaches it, and neither does `tearDown` — `tearDown` runs after
        the answer has already been measured.

        SO THE GUARD'S PRESENT EFFECT IS NO LONGER ZERO, and that is the fact worth
        keeping rather than the row worth retiring. Rows 1 and 2 of this class are now
        the same row driven with and without `establish_record_descriptor`: with it the
        subject answers EBADF, without it the answer is None. The failure mode
        `TestTheOldInterleavingIsReproducedAndCaught` reproduces with a TEST DOUBLE is
        the REAL store's behaviour now.

        THE NAME IS RETAINED DELIBERATELY and no longer describes the answer. It is the
        record of an honest cap expiring, which is what an honest cap is for; renaming
        it is a scheduling act and is RAISED, not taken here.

        AND THE CAP ON WHAT THIS PROVES, stated so a green suite cannot be read as more
        than it is: this shares a ROOT with the finalizer defect carried at
        `planning/exec/EP-28C.md` AMENDMENT 4 §4.2 — a raw descriptor NUMBER is not a
        stable identity — and it is a DIFFERENT EXHIBITION of it. This row going green
        discharges nothing of that intake."""
        store = self.real_store()
        obs, fds = self.run_close_row(store, establish=False)
        self.assertIsNone(
            self.second_close(obs),
            "the second close answered %r; with the held descriptor it lands on a LIVE "
            "descriptor and returns" % (self.second_close(obs),),
        )
        # THE MECHANISM, NOT THE SYMPTOM: the number the store holds is the number the
        # row's `open` was given and its first close released.
        self.assertEqual(store._fh.fileno(), self.row_descriptor(fds))


class TestTheRepairTookNoneOfTheRefusedShapes(unittest.TestCase):
    """The wrong references, pinned. A repair of an instrument is worth nothing if
    it works by making the instrument tolerant of the condition instead of not
    creating it."""

    def setUp(self):
        self.src = Path(fixture_shim.__file__).read_text()

    def test_the_establish_call_precedes_the_row_loop(self):
        """Structural, because the ORDER is the whole repair: a line that
        establishes the descriptor after the first row runs establishes nothing."""
        call = self.src.index("establish_record_descriptor(store)")
        loop = self.src.index('for row in plan["rows"]:')
        self.assertLess(call, loop)

    def test_nothing_retries_an_append_or_revalidates_a_descriptor(self):
        """The refused repair, named at EP-28B and named again in this EP: making
        the descriptor survive the row by re-validating it and reopening on EBADF
        would have silently repaired another component's double-release inside the
        instrument the campaign depends on.

        Asserted on the FUNCTION's executable body rather than on the file, because
        the file's prose has to be free to explain the refusal it is refusing."""
        body = self.src[self.src.index("def establish_record_descriptor"):]
        body = body[body.index('"""', body.index('"""') + 3) + 3:]
        body = body[:body.index("\ndef ")]
        for banned in ("except", "while ", "errno", "fstat", "os.open", "try"):
            self.assertNotIn(banned, body, "the repair's body names %r" % banned)
        self.assertEqual(1, body.count("store._append("), body)

    def test_the_whole_fixture_holds_no_recovery_path_on_a_bad_descriptor(self):
        """The same refusal at file scope, on the one token that could only appear
        in a recovery path: the fixture imports no `errno` and catches no OSError."""
        self.assertNotIn("import errno", self.src)
        self.assertNotIn("except OSError", self.src)

    def test_the_establishing_record_is_outside_every_classification(self):
        """It is appended before the first step of the first row, so no bracket can
        contain it — and it is deliberately absent from the class map, exactly as
        the row-state record is, so a change that ever moved it inside a bracket
        would be REFUSED as unclassified rather than pass."""
        self.assertNotIn(fixture_shim.READY_ACTION, fixture_shim.CLASS_MAP)
        self.assertNotIn(fixture_shim.READY_ACTION, fixture_shim.COVERS_MAP)


class TestTheTargetNamesTheWorldThatExists(unittest.TestCase):
    """W2. Five paths, one world, and the reason the form is absolute."""

    def setUp(self):
        self.text = KERNEL_MOUNT.read_text()
        self.spec = json.loads(self.text)

    def test_no_path_field_names_the_abandoned_world(self):
        for label, value in self._paths():
            self.assertNotIn(ABANDONED, value, label)

    def test_all_five_paths_name_the_relocated_world(self):
        paths = self._paths()
        self.assertEqual(len(paths), 5, "the count this EP names is five: %r" % (paths,))
        for label, value in paths:
            self.assertTrue(value.startswith(WORLD + "/"), "%s: %r" % (label, value))

    def test_the_subject_is_still_the_module_and_not_a_directory(self):
        """The relocation must not have quietly turned the subject into an ordinary
        directory — which is the state §11.2b exists because of."""
        self.assertEqual(self.spec["subject"]["fstype"], "govosfs")

    def test_the_replay_command_carries_no_tilde(self):
        """It is handed to a subprocess with no shell, so nothing expands a `~`
        there. A `~` in a descriptor path became a directory literally named `~`
        once, and the harness reported ABI 40 of 40 against it."""
        for arg in self.spec["replay"]["command"]:
            self.assertNotIn("~", arg)

    def test_the_file_says_why_the_form_is_absolute(self):
        """Half a file expanding and half not is the trap; the file states which
        fields expand and which do not, so the next seat does not have to measure
        it again."""
        self.assertIn("no shell and no expansion", self.spec["world_note"])

    def _paths(self):
        cmd = self.spec["replay"]["command"]
        return [
            ("subject.path", self.spec["subject"]["path"]),
            ("transport.scratch", self.spec["transport"]["scratch"]),
            ("record.jsonl", self.spec["record"]["jsonl"]),
            ("replay.command record", cmd[3]),
            ("replay.command blobs", cmd[4]),
        ]


if __name__ == "__main__":
    unittest.main()
