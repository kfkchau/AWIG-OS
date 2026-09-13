# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-28F — the twelve red rows classified, and the absolute-descriptor class measured.

WHAT THIS FILE ESTABLISHES, and the order matters because the last one overturns the
disposition the plan carried.

  W1   Each of the twelve red rows is classified by the mechanism read from its own
       code. The table below IS that classification, held as data so the row set can
       be set-differenced against the enumeration in both directions.

  W1a  The sibling question, answered from the rows themselves. Lines 614, 723, 735
       and 747 of `baselines/host-local/06-files.json` all read `"ret": 3` and only
       747 moved. THE THREE ARE NOT DESCRIPTOR VALUES AT ALL: 614 is a `write`
       byte-count, 723 and 735 are `lseek` file offsets. Only 747 is a `dup2` return.
       The mentor's first reading holds — the occupancy does not reach them — and it
       holds for a stronger reason than "different rows": they are a different KIND
       of number, and no descriptor-table occupancy could ever move them.

  W3   The absolute-descriptor class enumerated across EVERY baseline directory, not
       only the file the ruling cited. `probe._n_fd` already reports descriptors
       RELATIVELY as `fd#N` for `open`, `openat`, `dup` and `pipe_read_fd`, because
       "the integer is an allocation detail" (probe.py:126-131). `dup2` alone uses
       `_n_passthrough`. So across 40 + 42 rows there are exactly two raw descriptor
       integers per directory: `files.dup` step 6's `dup2(fd, 200)`, whose 200 is
       CALLER-CHOSEN and immune to occupancy by construction, and `files.dup` step
       9's `dup2($f, $f)`, which returns `$f`. That single value is the entire class.

  AND THE MEASUREMENT THAT OVERTURNS THE RE-CAPTURE. A fresh capture of `host-local`
  through the harness's own documented procedure is BYTE-FOR-BYTE IDENTICAL to the
  pinned artifact, `"ret": 3` included. The capture path constructs no `EventStore`
  (runner.py:150-168); `fixture_shim.main` constructs one and runs the probe in the
  same process (fixture_shim.py:274, :296). The pinned 3 is CORRECT in the world the
  capture takes it in. It is wrong only when compared against a fixture whose process
  holds a store — and that is the same-process composition, which is a named defect
  with its own home and takes zero lines here.

  So the baseline is NOT STALE and a re-capture changes nothing. That is a conflict
  between the plan and the code; it is logged and raised, never improvised around.

WHAT THIS FILE DOES NOT ASSERT, stated rather than left as an absence. It makes no
claim about the width-1 divergence row, about the substring assertion at
`tests/test_ep28.py:321`, or about the thirteen red stance-4 conformance rows. Each
is a RAISE. It edits no existing test file and no baseline: the classification came
back with ZERO members licensed for re-pinning, and a pass that re-pinned nothing is
this EP's discriminating rule doing exactly what it was written to do.

[DATED NOTE, 2026-08-02 — EP-28H, so the W3 paragraph above is read as EP-28F's
MEASUREMENT and not as a live description of the harness. Everything it states was
true when taken and the disposition it forced has since been carried out: the mentor
ruled that the class be emptied at the reporting scheme rather than re-pinned, `dup2`
joined `_n_fd`, and `host-local` was re-captured through its own procedure. So there
are no longer two raw descriptor integers per directory — there are none in
`host-local` and two in the guest capture, which predates the change and cannot be
retaken from the host. The rows below carry the flip individually; the paragraph is
left standing because it is the evidence the flip was earned.]
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from kernel.store import EventStore  # noqa: E402
from tools.conformance.harness import runner  # noqa: E402

BASELINES = REPO / "tools" / "conformance" / "baselines"


def commit_identity(rev):
    """A REV'S FULL OBJECT NAME — the identity underneath every abbreviation of it.

    THE ONE HOME FOR THE ACT, and it is imported rather than copied: EP-28Z's whole
    debt was one act spelled eighteen ways across ten files, and minting a second such
    family on the day its cousin is being repaired would be the repair building the
    defect. `tests/test_ep28h.py` already imports this module, so the direction is
    precedented and this module imports no test module in return.

    WHY IT EXISTS (MAINT-2; board `:2115` found it, `:2118` made it uniform, `:2122`
    counted it). `git`'s abbreviated hash is a VIEW of a commit, and `git` chooses that
    view's width FROM REPOSITORY SIZE. Thirty seven-character literals were written into
    this suite when the view was seven wide; it is eight wide now, and nothing they guard
    has moved. A row that measures a stored literal against fresh `%h` output therefore
    goes red BECAUSE THE REPOSITORY GREW — a clock nobody set, firing in the layer every
    other verification rests on, and INDISTINGUISHABLE FROM A REAL FAILURE at the point
    where telling the two apart is the whole job.

    Both sides of such a comparison are resolved through here first, so what is compared
    is the COMMIT and never its rendering. The consequence is two-directional and neither
    half alone is the point: a row built this way STILL REDS when its subject genuinely
    MOVES, because the identities differ, and IS SILENT when only the width changes.

    IT RAISES ON AN UNRESOLVABLE REV RATHER THAN RETURNING A SENTINEL. A pin that has
    stopped resolving is a finding; returning the rev unchanged, or None, would let a
    dead pin compare equal to another dead pin and report the silence as a pass — the
    guard deleted while still looking like a guard.
    """
    out = subprocess.run(["git", "rev-parse", rev + "^{commit}"],
                         cwd=str(REPO), capture_output=True, text=True)
    if out.returncode != 0:
        raise AssertionError(
            "%r does not resolve to a commit in this repository: %s"
            % (rev, out.stderr.strip()))
    return out.stdout.strip()


#: Descriptor-returning vocabulary entries, split by how `probe.CALLS` normalizes
#: them. The first group is reported RELATIVELY and can never carry an absolute
#: number into a capture.
#:
#: DOCUMENTED FLIP [EP-28H item 3, 2026-08-02]. `dup2` was the single passthrough entry
#: — it is why this file could count the absolute-descriptor class and find exactly one
#: live member per baseline directory. EP-28H's ruled disposition was not to re-pin that
#: member but to EMPTY THE CLASS BY CONSTRUCTION: `dup2` now normalizes through `_n_fd`
#: like every other descriptor-returning call, so the reporting scheme MINTS no absolute
#: number anywhere. The historical value is retained beside the live one, because the
#: rows below are about what the class WAS as much as about what it now is.
RELATIVE_FD_CALLS = ("open", "openat", "dup", "pipe_read_fd", "dup2")
PASSTHROUGH_FD_CALLS = ()
HISTORICAL_PASSTHROUGH_FD_CALLS = ("dup2",)


# ---------------------------------------------------------------------------
# W1 — the classification, held as DATA so it can be differenced rather than read
# ---------------------------------------------------------------------------

#: (test file, test id, mechanism read from the row's own code, class)
#:
#: `class` is the plan's binary: "absolute-fd" licenses a re-pin, "other" returns as
#: its own item with the row byte-unchanged. NOTHING here is "absolute-fd", and the
#: one row that comes closest is recorded with its arithmetic signature SATISFIED and
#: its re-pin refused on a measurement — see `TestTheOneCandidateFailsOnItsArtifact`.
CLASSIFICATION = (
    (
        "tests/test_ep24.py",
        "TestHarnessColumnsFail.test_the_control_passes_every_leg_on_every_active_files_row",
        "asserts report.ok over a verify run; reds because files.dup step 9 returns 4 "
        "against the baseline's pinned 3. The row itself pins NO number — the number "
        "lives in the baseline, and the baseline is correct for the world it was "
        "captured in. The delta is +1 and equals k, so the arithmetic signature is "
        "satisfied; the re-pin is refused because a fresh capture reproduces 3.",
        "other",
    ),
    (
        "tests/test_ep28b.py",
        "TestTheAppendIsStillTheCommit.test_the_buffer_is_flushed_before_the_barrier",
        "slices store.py's source between two literals; the held descriptor removed the "
        "`with self.file_path.open(\"a\"` form, so str.index raises ValueError. A source "
        "LITERAL moved, not a number. Its subject — flush precedes barrier — is unchanged.",
        "other",
    ),
    (
        "tests/test_ep28e.py",
        "TestNoRecordIsReadToServeADirectoryListing.test_a_directory_listing_reads_zero_records",
        "errors in setUp at src/founding/install.py:72, `open(path)` raising EBADF. Passes "
        "when test_ep28e runs alone and errors only in the full suite, so the cause is "
        "cross-file and not this row's. No assertion, no number, nothing to re-pin.",
        "other",
    ),
    (
        "tests/test_ep28d.py",
        "TestEstablishingTheDescriptorFirstRepairsIt.test_the_descriptor_table_is_unchanged_across_the_row",
        "tearDown set-equality on /proc/self/fd; the store now holds its record descriptor "
        "and the battery closes only the double's extra one, never EventStore.close().",
        "other",
    ),
    (
        "tests/test_ep28d.py",
        "TestEstablishingTheDescriptorFirstRepairsIt.test_the_held_number_is_below_every_number_the_row_touches",
        "same tearDown set-equality; the store's held descriptor outlives the test.",
        "other",
    ),
    (
        "tests/test_ep28d.py",
        "TestEstablishingTheDescriptorFirstRepairsIt.test_the_instruments_record_path_survives_the_row",
        "same tearDown set-equality; the store's held descriptor outlives the test.",
        "other",
    ),
    (
        "tests/test_ep28d.py",
        "TestEstablishingTheDescriptorFirstRepairsIt.test_the_row_answers_ebadf_for_its_own_reason",
        "same tearDown set-equality; the store's held descriptor outlives the test.",
        "other",
    ),
    (
        "tests/test_ep28d.py",
        "TestTheOldInterleavingIsReproducedAndCaught.test_the_descriptor_the_store_held_is_the_one_the_first_close_freed",
        "same tearDown set-equality; the store's held descriptor outlives the test.",
        "other",
    ),
    (
        "tests/test_ep28d.py",
        "TestTheOldInterleavingIsReproducedAndCaught.test_the_instruments_own_record_path_is_what_breaks",
        "same tearDown set-equality; the store's held descriptor outlives the test.",
        "other",
    ),
    (
        "tests/test_ep28d.py",
        "TestTheOldInterleavingIsReproducedAndCaught.test_the_rows_ebadf_is_manufactured_and_not_measured",
        "same tearDown set-equality; the store's held descriptor outlives the test.",
        "other",
    ),
    (
        "tests/test_ep28d.py",
        "TestTheRealStoreAsItStands.test_the_row_answers_ebadf_with_the_repair_in_place",
        "same tearDown set-equality, on the REAL EventStore rather than the double.",
        "other",
    ),
    (
        "tests/test_ep28d.py",
        "TestTheRealStoreAsItStands.test_the_row_answers_ebadf_without_it_too_and_that_is_the_honest_cap",
        "asserts the second close answers EBADF and measures None. The row's own name "
        "states its scope — the real store AS IT STANDS — and the store no longer stands "
        "that way. An expired honest cap, which is what an honest cap is for. No number.",
        "other",
    ),
)

#: The twelve, as the EP enumerates them. Held separately from the table on purpose:
#: a table that supplied its own expectation could not be differenced against anything.
ENUMERATED_TWELVE = frozenset(
    (
        ("tests/test_ep24.py",
         "TestHarnessColumnsFail.test_the_control_passes_every_leg_on_every_active_files_row"),
        ("tests/test_ep28b.py",
         "TestTheAppendIsStillTheCommit.test_the_buffer_is_flushed_before_the_barrier"),
        ("tests/test_ep28e.py",
         "TestNoRecordIsReadToServeADirectoryListing.test_a_directory_listing_reads_zero_records"),
        ("tests/test_ep28d.py",
         "TestEstablishingTheDescriptorFirstRepairsIt.test_the_descriptor_table_is_unchanged_across_the_row"),
        ("tests/test_ep28d.py",
         "TestEstablishingTheDescriptorFirstRepairsIt.test_the_held_number_is_below_every_number_the_row_touches"),
        ("tests/test_ep28d.py",
         "TestEstablishingTheDescriptorFirstRepairsIt.test_the_instruments_record_path_survives_the_row"),
        ("tests/test_ep28d.py",
         "TestEstablishingTheDescriptorFirstRepairsIt.test_the_row_answers_ebadf_for_its_own_reason"),
        ("tests/test_ep28d.py",
         "TestTheOldInterleavingIsReproducedAndCaught.test_the_descriptor_the_store_held_is_the_one_the_first_close_freed"),
        ("tests/test_ep28d.py",
         "TestTheOldInterleavingIsReproducedAndCaught.test_the_instruments_own_record_path_is_what_breaks"),
        ("tests/test_ep28d.py",
         "TestTheOldInterleavingIsReproducedAndCaught.test_the_rows_ebadf_is_manufactured_and_not_measured"),
        ("tests/test_ep28d.py",
         "TestTheRealStoreAsItStands.test_the_row_answers_ebadf_with_the_repair_in_place"),
        ("tests/test_ep28d.py",
         "TestTheRealStoreAsItStands.test_the_row_answers_ebadf_without_it_too_and_that_is_the_honest_cap"),
    )
)


def _table_rows(table=CLASSIFICATION):
    return frozenset((f, t) for f, t, _m, _c in table)


class TestTwelveClassified(unittest.TestCase):
    """T-TWELVE-CLASSIFIED — the table's row set equals the twelve, differenced in
    BOTH directions. A count match is not a set match, which is the lesson this arc
    filed against itself twice."""

    def test_the_table_covers_the_twelve_in_both_directions(self):
        got = _table_rows()
        self.assertEqual(got - ENUMERATED_TWELVE, frozenset(),
                         "classified a row the enumeration does not name")
        self.assertEqual(ENUMERATED_TWELVE - got, frozenset(),
                         "the enumeration names a row the table does not classify")
        self.assertEqual(len(CLASSIFICATION), 12)

    def test_a_table_missing_one_row_is_CAUGHT(self):
        """THE RED WORLD, produced through the same difference the row above runs.
        A guard whose failure branch never executes has never been tested."""
        doubled = tuple(r for r in CLASSIFICATION if "test_ep28b" not in r[0])
        self.assertEqual(len(doubled), 11)
        missing = ENUMERATED_TWELVE - _table_rows(doubled)
        self.assertEqual(len(missing), 1, "the difference must NAME the dropped row")
        self.assertIn("tests/test_ep28b.py", {f for f, _t in missing})

    def test_every_row_carries_a_mechanism_and_a_class_from_the_permitted_set(self):
        for path, test_id, mechanism, cls in CLASSIFICATION:
            self.assertIn(cls, ("absolute-fd", "other"), test_id)
            self.assertGreater(len(mechanism), 60,
                               "%s carries no mechanism worth the name" % test_id)
            self.assertTrue(path.startswith("tests/"), path)


# ---------------------------------------------------------------------------
# W1a — the sibling question, answered from the rows themselves
# ---------------------------------------------------------------------------


def _steps_by_line(path):
    """Map each `"ret": ...` line number to the call that produced it, by walking the
    file's own text alongside the parsed document. The question is about LINES, so the
    answer is read at lines rather than reconstructed from the object."""
    text = Path(path).read_text(encoding="utf-8")
    lines = text.split("\n")
    out = {}
    call = None
    for i, line in enumerate(lines, start=1):
        s = line.strip()
        if s.startswith('"call":'):
            call = json.loads("{" + s.rstrip(",") + "}")["call"]
        elif s.startswith('"ret":') and call is not None:
            out[i] = call
    return out


class TestTheSiblingsWereNeverTheClass(unittest.TestCase):
    """W1a — why three identical pins did not move, established from the rows.

    THE ANSWER IS THE MENTOR'S FIRST READING AND IT IS STRONGER THAN 'DIFFERENT ROWS'.
    The three siblings are not descriptor numbers at all. 614 is the byte count a
    `write` returned; 723 and 735 are the offsets `lseek` returned. Only 747 is a
    descriptor. No descriptor-table occupancy can move a byte count or a file offset,
    so the shift is UNIFORM over the class and the class never contained them.

    A row that LOOKS like the class is not a member of it — recorded here as a
    countable rather than as a reading, because the reading is what the plan warned
    would be over-applied."""

    BASELINE = BASELINES / "host-local" / "06-files.json"

    def setUp(self):
        self.by_line = _steps_by_line(self.BASELINE)

    def test_the_four_identical_pins_are_four_different_kinds_of_number(self):
        self.assertEqual(self.by_line.get(614), "write",
                         "line 614's `ret` is a byte count, not a descriptor")
        self.assertEqual(self.by_line.get(723), "lseek",
                         "line 723's `ret` is a file offset, not a descriptor")
        self.assertEqual(self.by_line.get(735), "lseek",
                         "line 735's `ret` is a file offset, not a descriptor")
        self.assertEqual(self.by_line.get(747), "dup2",
                         "line 747's `ret` is the only descriptor of the four")

    def test_all_four_still_read_three_so_the_question_is_about_kind_not_value(self):
        """The premise the question rests on, pinned: if one of these ever stops
        reading 3 the sibling question has a different answer and must be re-asked.

        DOCUMENTED FLIP [EP-28H item 3, 2026-08-02] — and it is the premise coming true
        rather than breaking. REFUTED TEXT, RETAINED: the row asserted all FOUR lines
        read `"ret": 3`. Line 747 no longer does, because it is the ONE of the four
        that is a descriptor: `dup2` joined the relative scheme, the host-local baseline
        was re-captured through its own procedure, and 747 now reads `"ret": "fd#3"`.
        The other three are a byte count and two file offsets and are untouched by a
        reporting change that only reaches descriptors — WHICH IS THE SIBLING ANSWER,
        now visible as a difference in the artifact instead of only as a reading."""
        lines = self.BASELINE.read_text(encoding="utf-8").split("\n")
        for n in (614, 723, 735):
            self.assertEqual(lines[n - 1].strip(), '"ret": 3', "line %d" % n)
        self.assertEqual(lines[747 - 1].strip(), '"ret": "fd#3"',
                         "the one descriptor of the four now reports relatively")

    def test_a_byte_count_and_an_offset_are_unreachable_by_occupancy(self):
        """The mechanism stated as a property rather than as prose: the three siblings
        sit on calls whose return value is a function of the FILE, and the one that
        moved sits on a call whose return value is a function of the descriptor TABLE."""
        self.assertNotIn(self.by_line[614], HISTORICAL_PASSTHROUGH_FD_CALLS + RELATIVE_FD_CALLS)
        self.assertNotIn(self.by_line[723], HISTORICAL_PASSTHROUGH_FD_CALLS + RELATIVE_FD_CALLS)
        self.assertNotIn(self.by_line[735], HISTORICAL_PASSTHROUGH_FD_CALLS + RELATIVE_FD_CALLS)
        # DOCUMENTED FLIP [EP-28H item 3, 2026-08-02]: the one descriptor of the four was
        # the passthrough entry and is now a relative one. It is in BOTH lists — the
        # historical one because that is what made it the class, the live one because
        # that is what emptied it — and the three siblings are in neither, then or now.
        self.assertIn(self.by_line[747], HISTORICAL_PASSTHROUGH_FD_CALLS)
        self.assertIn(self.by_line[747], RELATIVE_FD_CALLS)


# ---------------------------------------------------------------------------
# W3 — the class enumerated across EVERY baseline directory
# ---------------------------------------------------------------------------


def _fd_returning_steps(doc):
    for row_id, row in doc["rows"].items():
        for step in row.get("steps", []):
            if step.get("call") in RELATIVE_FD_CALLS + PASSTHROUGH_FD_CALLS:
                yield row_id, step


def _absolute_fd_values(directory):
    """Every descriptor-returning step in this capture whose `ret` is an ABSOLUTE
    number — the class, read off the artifact rather than off the vocabulary table.
    Reading it this way is what lets the enumeration survive the reporting change: a
    capture taken under either construction is measured the same way."""
    doc = json.loads((directory / "06-files.json").read_text(encoding="utf-8"))
    found = []
    for row_id, step in _fd_returning_steps(doc):
        ret = step["ret"]
        if ret is None or (isinstance(ret, str) and ret.startswith("fd#")):
            continue
        found.append((directory.name, row_id, step.get("i"), ret))
    return sorted(found)


#: THE CARVE-OUT, AND IT IS A TABLE OF EXACTLY TWO STEPS IN EXACTLY ONE DIRECTORY
#: [EP-28H item 3, 2026-08-02]. `baselines/ep21-ubuntu-guest/` is a HISTORICAL capture,
#: taken under the old construction on the guest, and EP-28H's own RAISED-BY-DESIGN
#: names it: it cannot be re-captured from the host — a guest capture needs the guest —
#: so it is stale-by-known-cause, stated, never hand-edited. Its consumer is named
#: rather than left to a category-person: the next pass with a guest window, which is
#: EP-28C's resumed W4-W8.
#:
#: The table is asserted EQUAL to what the enumeration finds, both directions, so it
#: cannot silently grow to cover a new absolute value and cannot silently outlive the
#: guest re-capture: when that capture lands, this row reds and the carve-out is deleted.
STALE_BY_KNOWN_CAUSE = (
    ("ep21-ubuntu-guest", "files.dup", 6, 200),
    ("ep21-ubuntu-guest", "files.dup", 9, 3),
)


class TestTheAbsoluteDescriptorClassIsOneValue(unittest.TestCase):
    """W3's enumeration, over every baseline directory rather than the one the ruling
    cited.

    DOCUMENTED FLIP [EP-28H item 3, 2026-08-02]. REFUTED TEXT, RETAINED: *"The harness
    already reports descriptors relatively; `dup2` is the single exception, and only one
    of its two uses carries a number occupancy can move."* The exception is gone. EP-28H
    made `dup2` report relatively and re-captured `host-local` through its own procedure,
    so the class is EMPTY BY CONSTRUCTION in every capture taken from now on — the
    reporting scheme mints no absolute descriptor number anywhere. What remains is one
    historical capture that predates the construction and cannot be retaken here."""

    def _dirs(self):
        found = sorted(p for p in BASELINES.iterdir() if (p / "06-files.json").exists())
        self.assertGreaterEqual(len(found), 2,
                                "the enumeration must cover every baseline directory, "
                                "and it found fewer than the two that exist")
        return found

    def test_every_descriptor_return_is_relative_except_dup2(self):
        """Now: every descriptor return is relative, and the only absolute values left
        anywhere are the carved-out two, each named with its cause and its consumer."""
        for d in self._dirs():
            for entry in _absolute_fd_values(d):
                self.assertIn(
                    entry, STALE_BY_KNOWN_CAUSE,
                    "%s recorded an absolute descriptor number with no named cause; "
                    "probe._n_fd reports descriptors by allocation order" % (entry,))

    def test_the_class_has_exactly_one_member_per_directory(self):
        """DOCUMENTED FLIP [EP-28H item 3, 2026-08-02]. REFUTED TEXT, RETAINED: *"THE
        WHOLE CLASS, counted. `dup2(fd, 200)` returns the caller's own 200 and is immune
        to occupancy by construction; `dup2($f, $f)` returns whatever $f is."* The count
        per directory was two, of which one was occupancy-bound. It is now ZERO in the
        capture taken under the new construction, and the historical capture still
        carries both — which is the whole shape of this item: the definitive was fixed
        and the derivative followed, everywhere the derivative could be re-taken."""
        live = _absolute_fd_values(BASELINES / "host-local")
        self.assertEqual(live, [], "host-local was re-captured under the relative "
                                   "reporting and must carry no absolute descriptor")
        historical = _absolute_fd_values(BASELINES / "ep21-ubuntu-guest")
        self.assertEqual([tuple(e) for e in historical], list(STALE_BY_KNOWN_CAUSE))

    def test_the_carve_out_is_exactly_its_subject_in_both_directions(self):
        """§A38 on the carve-out itself: a named exception that is never differenced
        against what it excuses grows quietly. The set found across EVERY directory must
        equal the table, both ways — so an absolute value appearing anywhere new reds
        here, and the table outliving the guest re-capture reds here too."""
        found = set()
        for d in self._dirs():
            found.update(_absolute_fd_values(d))
        self.assertEqual(found - set(STALE_BY_KNOWN_CAUSE), set(),
                         "an absolute descriptor number with no named cause")
        self.assertEqual(set(STALE_BY_KNOWN_CAUSE) - found, set(),
                         "the carve-out names a value that no longer exists — the guest "
                         "capture landed and this table is what expires with it")

    def test_the_relative_guarantee_has_its_own_dedicated_row(self):
        """The compensating control probe._n_fd names: the lowest-available guarantee,
        which IS ABI, is asserted as a BOOLEAN by `fd_exact` rather than as a number.
        So the estate already knows the property is relative — the one absolute value
        is the exception, not the design."""
        for d in self._dirs():
            doc = json.loads((d / "06-files.json").read_text(encoding="utf-8"))
            exact = [s for row in doc["rows"].values() for s in row.get("steps", [])
                     if s.get("call") == "fd_exact"]
            self.assertEqual(len(exact), 1, d.name)
            self.assertIs(exact[0]["ret"], True, d.name)


# ---------------------------------------------------------------------------
# k, MEASURED INDEPENDENTLY — never inferred from the deltas
# ---------------------------------------------------------------------------


def _open_descriptors():
    """The process's own table, from the kernel's answer, minus the handle the reading
    itself needs. Excluded by WHAT IT POINTS AT rather than by number, because a number
    is the thing under measurement — EP-28D's correction, carried."""
    table = "/proc/%d/fd" % os.getpid()
    out = set()
    for name in os.listdir("/proc/self/fd"):
        try:
            target = os.readlink("/proc/self/fd/" + name)
        except OSError:
            continue
        if target == table:
            continue
        out.add(name)
    return out


class TestTheStoresOccupancyIsMeasuredNotInferred(unittest.TestCase):
    """`k` is the store's descriptor occupancy, enumerated from the kernel's own answer.
    The plan is explicit that it is never inferred from the deltas it is used to check —
    a `k` read off the deltas would make the uniformity row a tautology."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep28f-")
        self.record = Path(self.dir) / "rec.jsonl"
        self.record.write_text("", encoding="utf-8")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.dir, ignore_errors=True)

    def measure_k(self):
        before = _open_descriptors()
        store = EventStore(self.record)
        store._append({"actor": "ep28f", "action": "probe", "rule_cited": "FIXTURE-CUSTODY-1"})
        held = _open_descriptors() - before
        store.close()
        return len(held), _open_descriptors() - before

    def test_k_is_one_and_the_store_releases_it(self):
        k, after_close = self.measure_k()
        self.assertEqual(k, 1, "the store's descriptor occupancy")
        self.assertEqual(after_close, set(),
                         "EventStore.close() must release the held descriptor")

    def test_a_store_nobody_writes_to_holds_nothing(self):
        """The descriptor is opened on the FIRST APPEND, not at construction — which is
        why the suite's thousands of disposable read-only worlds hold none."""
        before = _open_descriptors()
        store = EventStore(self.record)
        self.assertEqual(_open_descriptors() - before, set())
        store.close()


# ---------------------------------------------------------------------------
# the two guards, exercised on doubles — including their red worlds
# ---------------------------------------------------------------------------


def uniform_delta(repins, k):
    """T-REPIN-DELTA-IS-UNIFORM's predicate. Every re-pinned value must satisfy
    `new == old + k` with `k` the same across the whole class. Returns the offenders."""
    return [r for r in repins if r["new"] != r["old"] + k]


def missing_citation(repins):
    """T-REPIN-CITES-ITS-MECHANISM's predicate. A re-pin without its absolute-fd
    citation AND its world declaration fails structurally."""
    return [r for r in repins
            if not r.get("mechanism") or not r.get("world")]


class TestTheGuardsCanFire(unittest.TestCase):
    """§A38, applied to this file's own absence-shaped rows: the re-pin set is EMPTY,
    so every guard over it passes vacuously. A check whose pass condition is the
    absence of output cannot tell 'nothing was wrong' from 'nothing was looked at' —
    so each guard is driven over a generated set that CONTAINS its red world, and the
    emptiness is asserted separately."""

    K = 1

    GOOD = {"row": "files.dup#9", "old": 3, "new": 4,
            "mechanism": "absolute descriptor number shifted by the store's occupancy",
            "world": "subject and store share one OS process; the store holds k=1"}

    def test_the_uniformity_guard_passes_a_true_member(self):
        self.assertEqual(uniform_delta([self.GOOD], self.K), [])

    def test_the_uniformity_guard_REDS_on_a_delta_that_is_not_k(self):
        """THE GENERATED RED WORLD. A row failing for a real reason will essentially
        never differ from its pin by exactly k, so a misclassification that satisfies
        the citation guard is caught here and nowhere else."""
        impostor = dict(self.GOOD, old=3, new=9)
        offenders = uniform_delta([self.GOOD, impostor], self.K)
        self.assertEqual(len(offenders), 1)
        self.assertEqual(offenders[0]["new"], 9)

    def test_the_citation_guard_REDS_on_a_repin_with_its_citation_stripped(self):
        stripped = dict(self.GOOD)
        stripped["mechanism"] = ""
        offenders = missing_citation([self.GOOD, stripped])
        self.assertEqual(len(offenders), 1)

    def test_the_citation_guard_REDS_on_a_repin_with_no_world_declared(self):
        """§A39 at the pin: a new pin without its world is the old defect with a newer
        date, so the world line is not optional and the guard says so."""
        worldless = dict(self.GOOD)
        del worldless["world"]
        self.assertEqual(len(missing_citation([worldless])), 1)

    def test_this_EP_re_pinned_NOTHING_and_that_is_the_result(self):
        """The classification returned zero members licensed for re-pinning. Asserted
        beside the four rows above, which prove the guards can fire — so this emptiness
        is a measured outcome and not an unexercised check."""
        repinned = [r for r in CLASSIFICATION if r[3] == "absolute-fd"]
        self.assertEqual(repinned, [], "no row was licensed for a re-pin")
        self.assertEqual(uniform_delta([], self.K), [])
        self.assertEqual(missing_citation([]), [])


# ---------------------------------------------------------------------------
# the measurement that overturns the re-capture
# ---------------------------------------------------------------------------


class TestTheOneCandidateFailsOnItsArtifact(unittest.TestCase):
    """The `files.dup` step 9 value is the class's ONLY candidate and its arithmetic
    signature is satisfied — 4 == 3 + k. The re-pin is still refused, and the reason is
    a measurement rather than a judgement: THE PINNED ARTIFACT IS WHAT ITS OWN CAPTURE
    PROCEDURE PRODUCES TODAY.

    The capture path builds no store (`runner.capture`); `fixture_shim.main` builds one
    and runs the probe in the same process. The pinned 3 is right in the world it was
    taken in and wrong only across a composition boundary the comparison does not model.
    Re-pinning it to 4 would make the committed artifact disagree with the procedure
    that produces it, and would write the fixture's composition into the STOCK kernel's
    baseline — the instrument pinning its own setup, one layer deeper."""

    def test_a_fresh_capture_reproduces_the_pinned_baseline_byte_for_byte(self):
        """§A39: this check CREATES the world it reads. It captures into a temporary
        baselines base and never touches the committed artifact or the warm fixture
        world at /tmp/govos-conformance."""
        pinned = (BASELINES / "host-local" / "06-files.json").read_bytes()
        base = tempfile.mkdtemp(prefix="ep28f-capture-")
        try:
            runner.capture("host-local", baselines_base=base)
            fresh = (Path(base) / "host-local" / "06-files.json").read_bytes()
        finally:
            import shutil
            shutil.rmtree(base, ignore_errors=True)
        self.assertEqual(
            fresh, pinned,
            "a fresh capture differs from the pinned artifact — if this ever reds, the "
            "baseline IS stale and the re-capture the plan directed becomes executable")

    def test_the_arithmetic_signature_of_the_one_candidate_is_satisfied(self):
        """Recorded rather than hidden, because it is the fact that makes the refusal
        interesting: the candidate passes the uniformity guard and is still not
        re-pinned. The guard is necessary and it is not sufficient."""
        candidate = {"row": "files.dup#9", "old": 3, "new": 4,
                     "mechanism": "shifted by the store's occupancy",
                     "world": "same-process composition, k=1"}
        self.assertEqual(uniform_delta([candidate], 1), [])
        self.assertEqual(missing_citation([candidate]), [])

    def test_the_capture_path_constructs_no_store(self):
        """Structural, and it is the whole reason the re-capture is a no-op: a capture
        holds no store, so the descriptor the row opens is the one the baseline pinned."""
        src = Path(runner.__file__).read_text(encoding="utf-8")
        body = src[src.index("def capture("):src.index("def verify(")]
        self.assertNotIn("EventStore", body)
        self.assertNotIn("fixture_shim", body)


class TestTheFourSubjectFilesAreUnchanged(unittest.TestCase):
    """T-OTHERS-UNTOUCHED — every row classified `other` is byte-unchanged. All twelve
    are `other`, so all four files must be untouched.

    DOCUMENTED FLIP [EP-28H items 1, 5 and 6, 2026-08-02]. REFUTED VEHICLE, RETAINED:
    the row measured the four files against the dispatch commit `0a7637c` and a MOVING
    HEAD. Its subject is EP-28F's own conduct — *this pass touched none of them* — and
    that is a fact about a finished range of history, not about every commit that will
    ever follow. Measured the old way it reds the moment any later pass lawfully edits
    one of the four, which is what EP-28H did: `test_ep28d.py` gained the `tearDown`
    close and the re-aimed honest cap, `test_ep28b.py` gained the re-aimed flush row.

    A ROW WHOSE WORLD IS A PAST EVENT PINS THE RANGE THAT EVENT HAPPENED IN. The range
    is EP-28F's dispatch commit to the commit its work landed in, and inside it the
    four files are byte-identical — the same claim, now unbreakable by anyone else's
    lawful work and still false if EP-28F had touched them."""

    DISPATCH_HEAD = "0a7637c"
    #: The commit EP-28F's work landed in — the only commit that touches
    #: `tests/test_ep28f.py`, which is the file EP-28F created.
    LANDED_AT = "208a1ee"
    FILES = ("tests/test_ep24.py", "tests/test_ep28b.py",
             "tests/test_ep28d.py", "tests/test_ep28e.py")

    def test_no_subject_file_moved_since_the_dispatch_commit(self):
        for path in self.FILES:
            out = subprocess.run(
                ["git", "diff", "--stat", self.DISPATCH_HEAD, self.LANDED_AT, "--", path],
                cwd=str(REPO), capture_output=True, text=True)
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertEqual(out.stdout.strip(), "",
                             "%s moved inside EP-28F's own range; every `other` row was "
                             "to be byte-unchanged" % path)

    def test_the_range_is_the_one_EP_28F_ran_in(self):
        """§A39 on the row above: the claim is only as good as the range it is taken
        over, so the range is asserted rather than assumed. `LANDED_AT` must be the
        commit that created this very file, and it must be a descendant of the dispatch
        commit — otherwise the diff above could be empty for the wrong reason."""
        created = subprocess.run(
            ["git", "log", "--format=%h", "--diff-filter=A", "--",
             "tests/test_ep28f.py"],
            cwd=str(REPO), capture_output=True, text=True)
        self.assertEqual(created.returncode, 0, created.stderr)
        # [MAINT-2, 2026-08-26. THE ROW ASSERTED STRING EQUALITY OF AN ABBREVIATION where
        # it meant COMMIT IDENTITY. `%h` emits eight characters on this repository and
        # `LANDED_AT` is seven, so the assertion could not succeed while `208a1ee` and
        # `208a1ee3` ARE THE SAME COMMIT. Both sides now resolve to full object names. The
        # claim is unchanged and strictly stronger: the length test is gone, the identity
        # test is not, and the row still reds if this file gains a second creating commit
        # or if the one it has is not `LANDED_AT`.]
        self.assertEqual([commit_identity(h) for h in created.stdout.split()],
                         [commit_identity(self.LANDED_AT)],
                         "this file's creating commit is not LANDED_AT")
        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", self.DISPATCH_HEAD, self.LANDED_AT],
            cwd=str(REPO), capture_output=True, text=True)
        self.assertEqual(ancestor.returncode, 0,
                         "the dispatch commit is not an ancestor of the landing commit")

    def test_the_files_named_are_the_files_the_twelve_live_in(self):
        """§A38: the check above passes by producing no output, so its subject is
        proven non-empty here — the four names are exactly the table's own files."""
        self.assertEqual(set(self.FILES), {f for f, _t, _m, _c in CLASSIFICATION})


if __name__ == "__main__":
    unittest.main()
