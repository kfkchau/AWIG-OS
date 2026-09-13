# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-30-C3 — HANDING OVER AN OPEN FILE BECOMES AN ACT BETWEEN ENTITIES, RECORDED.

Every row of the plan's §3 and every red world of its §4, each declaring its KIND in its own
docstring (DRIVEN / INSPECTED / ABSENCE), because C0's close found three rows whose text never
said what kind of row they were and every later hand had to re-derive it.

THE RED FACT THIS PASS CURES, stated so a later reader can falsify the claim of cure: the
custody plane held FIFTEEN `FILE-*` actions plus two lock actions, and NOT ONE OF THEM WAS A
TRANSFER BETWEEN PARTIES. The module says what its vocabulary is for in its own comment — the
namespace fold answers what a file IS, the lock fold answers who holds exclusivity over part of
one — and neither can say who holds a handle now. A handover was expressible only as an
attribute mutation on the file, which makes a relation between two parties look like a property
of a third thing that is not a party to it.

WHAT THE FOLD ANSWERS, and it is the thing most likely to be read too widely: WHO HOLDS THIS
HANDLE NOW, for a handle some record has HANDED OVER. A handle opened and never transferred has
no transfer record and the fold says None, which is an answer and not a failure. `FILE-OPEN`
declares no entity, so the opener is not knowable from the record at all — a REAL GAP, RAISED at
this unit's close rather than papered over by inventing a holder here.
"""

import hashlib
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import era_pin                                                   # noqa: E402  (the era-pin home, EP-28Z)
from bridge import custody                                       # noqa: E402
from kernel.blobs import BlobStore                               # noqa: E402
from kernel.boot import build_kernel                             # noqa: E402
from kernel.errors import OpError                                # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK_PATH = os.path.join(REPO, "src", "founding", "founding-pack.json")

#: The world's fixed cast. Named once because four rows share it and a literal repeated at four
#: sites is four places for a typo to become a passing row about the wrong subject.
GIVER, TAKER = "E1", "E2"
DEVICE, DRIVER = "virtio1", "virtio-blk"
HANDLE = "/handed-over.txt"

#: `FILE-OPEN` and `FILE-XATTR-SET` declare `provenance_param` in its MANDATORY string form —
#: not FILE-CREATE's `{"param": ..., "when_absent": "default"}` — so they REFUSE a call that
#: supplies none. DRIVEN before this file was written rather than read off a definition: the
#: first draft omitted it and both acts refused with AR-2.
#:
#: THE TRANSFER OP DELIBERATELY DECLARES NO `provenance_param`, and that is a derivation rather
#: than an omission. Provenance answers WHO ACTED as evidence the port asserted; this act names
#: BOTH PARTIES IN ITS OWN PAYLOAD, which is the whole content of its law. A provenance
#: parameter here would add a third, weaker answer to a question the record already answers
#: exactly — the minimality gate refuses it.
PROV = {"asserted_by": "uid:1000", "source": "kernel-port", "could_read": [], "uid": 1000}


def _pack():
    with open(PACK_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def transfer_definition():
    """FILE-CUSTODY-TRANSFER's definition, read out of the founding pack ITSELF.

    Read from the pack rather than from the live registry for the reason EP-30-C1's own reader
    states: the INSPECTED rows are claims about THE LAW AS WRITTEN, and a registry read would
    pass on a definition the pack does not carry."""
    for step in _pack()["steps"]:
        for record in step.get("records", []):
            payload = record.get("payload")
            if isinstance(payload, dict) and payload.get("name") == "FILE-CUSTODY-TRANSFER":
                return payload["definition"]
    raise AssertionError("FILE-CUSTODY-TRANSFER carries no definition in the founding pack")


def founding_version():
    return _pack()["founding_version"]


def sweep(needle):
    """A1's ONE query shape, used for EVERY needle including the controls.

    ONE SHAPE FOR ABSENCE AND CONTROL ALIKE IS THE WHOLE POINT (`:1706`). If the query is
    mis-built, the CONTROL reads zero and the row fails loudly — instead of the absence reading
    zero and the row passing quietly, which is what a mis-built query looks like when the
    controls run through a different code path.

    POPULATION, DECLARED RATHER THAN APPLIED SILENTLY (`:1816`): `src/` and `tests/`,
    recursive, ARCHIVES EXCLUDED BY PATH. Archives are frozen estate-wide and a needle found in
    one would be a fact about history, not about the tree this unit changed.

    CASE-BLIND, because a zero from a case-sensitive needle is not an absence (`:1863`).

    UNIT OF COUNT: MATCHING LINES, reported PER FILE.

    IT RETURNS FILES AND NOT A TOTAL, AND THAT IS THE WHOLE REASON THIS ROW IS SOUND. A file
    that asserts a needle's absence CONTAINS THAT NEEDLE — in the assertion, and in the prose
    saying what is absent. `tests/` is inside the population, so a total would count this file's
    own text and the row would go red on itself. THE ANSWER IS NOT TO EXCLUDE THIS FILE QUIETLY:
    a self-serving exclusion applied inside the query is exactly the shape that makes an
    absence unfalsifiable. The answer is to report per file, so the row can assert the honest
    claim — *no file except this one* — and a reader can see the exception being made."""
    hits = {}
    for root in ("src", "tests"):
        for dirpath, dirnames, filenames in os.walk(os.path.join(REPO, root)):
            dirnames[:] = [d for d in dirnames if d not in ("archive", "__pycache__")]
            for name in filenames:
                path = os.path.join(dirpath, name)
                n = 0
                try:
                    with open(path, encoding="utf-8", errors="ignore") as fh:
                        for line in fh:
                            if needle.lower() in line.lower():
                                n += 1
                except OSError:
                    continue
                if n:
                    hits[os.path.relpath(path, REPO)] = n
    return hits


#: THIS FILE'S OWN PATH INSIDE THE POPULATION. Named once, used by every row that asserts an
#: absence, so the one exception every such row must make is made in ONE place and is visible.
SELF = os.path.relpath(os.path.abspath(__file__), REPO)


def elsewhere(needle):
    """The sweep's hits EXCLUDING this file — the population an absence claim is really about."""
    return {path: n for path, n in sweep(needle).items() if path != SELF}


def total(needle):
    return sum(sweep(needle).values())


class WorldCase(unittest.TestCase):
    """A world with the changed law installed, plus the helpers the driven rows share."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep30-c3-")
        self.blobs = BlobStore(os.path.join(self.dir, "blobs"))
        self.store, self.gate, self.views = build_kernel(
            os.path.join(self.dir, "record.jsonl"), blobs=self.blobs)
        #: THE LIVE HALF OF A5, and it is wired the way the mount wires its own folds: the
        #: store's ON-APPEND LISTENER, which is what `bridge/records_fs.py` uses to keep
        #: `CustodyState` and `LockTable` current. It NEVER REPLAYS — it sees each record once,
        #: as it lands, and holds nothing else.
        #:
        #: WHY THIS MATTERS MORE THAN IT LOOKS. A5 compares two answers, and if BOTH came from
        #: `fold_custody(store.all())` the row would be one computation run twice: it would
        #: agree with itself no matter what the fold did, which is the exact vacuity R3 names
        #: one layer down. The comparison is only worth something when the two SOURCES differ —
        #: an incremental listener against a replay from empty. That is the EP-24B one-fold
        #: rule: one implementation, two sources, so a divergence can only mean a record was
        #: missed and never that two implementations disagreed.
        self.live = custody.HandleCustody()
        self.store.on_append(self.live.apply)
        import shutil
        self.addCleanup(shutil.rmtree, self.dir, True)

    def replayed(self):
        """The REPLAY half: a fold built from nothing but the record."""
        return custody.fold_custody(self.store.all())

    def establish(self, entity):
        return self.gate.execute("CREATE-ACCOUNT", "owner",
                                 {"account_id": entity, "actor_class": "program"})

    def bind_device(self, device=DEVICE, driver=DRIVER):
        """EP-29's landing: the act that FOUNDS a device identity. Everything downstream
        INHERITS this value; nothing re-derives it."""
        self.gate.execute("REGISTER-CAPABILITY", "owner",
                          {"driver": driver, "device_class": "block"})
        return self.gate.execute("BIND-DEVICE", "owner", {"device": device, "driver": driver})

    def open_handle(self, handle=HANDLE):
        return self.gate.execute("FILE-OPEN", "owner", {"path": handle, "provenance": PROV})

    def world(self):
        """The standing world every driven row starts from: two entities, a bound device, an
        open handle. Built by driving the ordinary door, never by writing records."""
        self.establish(GIVER)
        self.establish(TAKER)
        self.bind_device()
        self.open_handle()

    def hand_over(self, to_entity=TAKER, from_entity=GIVER, device=DEVICE, handle=HANDLE):
        return self.gate.execute("FILE-CUSTODY-TRANSFER", "owner",
                                 {"handle": handle, "from_entity": from_entity,
                                  "to_entity": to_entity, "device": device})

    def transfers(self):
        return self.store.by_action("FILE-CUSTODY-TRANSFER")

    def refusal_of(self, fn, *a, **kw):
        """Drive an act expected to refuse; return (cited rule, message). Fails loudly if the
        act was ADMITTED — a refusal row whose subject was never refused proves nothing."""
        before = len(self.store.by_action("op-refused"))
        try:
            fn(*a, **kw)
        except OpError as exc:
            after = len(self.store.by_action("op-refused"))
            self.assertEqual(after, before + 1,
                             "the act raised but recorded no refusal — a governed refusal is a "
                             "RECORDED rule-citing decision, not an exception")
            return self.store.by_action("op-refused")[-1].get("rule_cited"), str(exc)
        raise AssertionError("the act was ADMITTED where the law requires a refusal")


# =====================================================================================
# A1 — ABSENCE, WITH THE CONTROL THAT PROVES THE QUERY WORKS
# =====================================================================================

class AbsenceAndControlCase(unittest.TestCase):

    def test_a1_the_unix_port_transfer_verb_is_absent_and_the_query_can_find_things(self):
        """A1 — KIND: ABSENCE, carrying its positive control (`:1706`).

        THE SUBJECT IS THE PLAN'S §1 GROUND: `SCM_RIGHTS` reads ZERO across `src/` and `tests/`,
        case-blind. It is STILL zero after this unit builds, and that is not an oversight —
        the architect's scope fence at `:1875` puts the Unix-port `SCM_RIGHTS` shim on the
        conformance harness's own schedule and rules the `08-ipc-comms` rows out of this unit.
        THIS UNIT LANDS THE RECORD-PLANE SEMANTICS; the syscall spelling is a later unit's.

        THE ONE EXCEPTION IS DECLARED AND NOT HIDDEN: this file names the needle, in this
        docstring and in the assertion below, so the claim is *no file EXCEPT THIS ONE*. Made
        visible through `elsewhere()` rather than applied inside the query, because an exclusion
        buried in a matcher is how an absence stops being falsifiable.

        A ZERO PROVES NOTHING WITHOUT A CONTROL, so the same query runs over two needles known
        PRESENT. If the query is mis-built the controls read zero and this row fails — which is
        the direction a check must be able to fail in."""
        self.assertEqual(elsewhere("SCM_RIGHTS"), {},
                         "the Unix-port transfer verb has entered the tree — this unit's scope "
                         "fence (:1875) says it rides the conformance harness's schedule, so a "
                         "non-zero here is a scope question and not a pass")
        # and the exception itself is asserted, so it cannot silently become a blanket skip
        self.assertGreater(total("SCM_RIGHTS"), 0,
                           "this file no longer names the needle it claims is absent — then "
                           "`elsewhere` is excluding nothing and the row above has quietly "
                           "become an unconditional pass")

        for control in ("FILE-CREATE", "FILE-OPEN"):
            self.assertGreater(len(elsewhere(control)), 0,
                               "the control needle %r found NOTHING outside this file, so the "
                               "query is broken and the emptiness above is a fact about the "
                               "query rather than about the tree" % (control,))

    def test_a1_the_sweep_is_case_blind_and_that_is_shown_moving(self):
        """A1's case-blindness, DRIVEN rather than asserted (`:1863`).

        A row that merely called `.lower()` would be a claim about the code. This shows the
        blindness DOING something: the lowercase spelling of a needle written in upper case in
        the tree is found, and it is found in the same numbers."""
        self.assertGreater(total("file-create"), 0,
                           "the lowercase spelling found nothing, so the sweep is not blind to "
                           "case and every absence it reports is unsound")
        self.assertEqual(sweep("file-create"), sweep("FILE-CREATE"))


# =====================================================================================
# A2 — THE FOUNDING MOVES THROUGH ITS OWN FRONT DOOR
# =====================================================================================

class FoundingMovedCase(unittest.TestCase):
    """The §A57 three-row family, plus the law-level rows that make the version row mean
    something. A version row ALONE would go green on an unrelated founding edit."""

    OPENED = (1, 27, 0)          # read from the pack's own key before the first edit

    #: THE COMMIT WHERE THIS UNIT'S MOVE COMPLETED, and it is pinned BY CONTENT rather than by
    #: version number: the pack at this commit is the FIRST to carry 1.28.0, and it is the
    #: commit at which `FILE-CUSTODY-TRANSFER` enters the founding at all — both driven from
    #: the pack's own bytes at the commit and at its parent, never read off a document.
    #: A COMMIT HASH ALONE IS AN ALIAS. `C3_MOVE_PACK_SHA` is what makes it a pin, and the row
    #: below checks it BEFORE reading any version out of it, exactly as tests/test_ep30_c1.py
    #: :310 does. Without that guard this constant names whatever now sits at that hash and the
    #: arithmetic would be about the wrong world while looking green.
    C3_MOVE_COMMIT = "87beceb9d4a85fb1c0386f0892b8be44b19bef62"
    C3_MOVE_PACK_SHA = "958756519be9f3b0c6e2dfc706d372dc026b3552fe5ddc4472017a08da195303"

    def test_a2_the_version_discriminator_moved_by_minor(self):
        """A2 — KIND: DRIVEN. Read from the pack's own key; never carried.

        THE THREE-ROW FAMILY, and each row fails differently on purpose: MAJOR moving is a STOP
        to the owner, MINOR not moving means the pass landed no new surface, and a PATCH left
        standing means the move was spelled as an amendment when it is a new op family. The
        convention is DIGEST-C2_v3's, adopted at EP-19: a new law flipped and a new op family
        bump MINOR.

        [DOCUMENTED FLIP — EP-30-K1R, 2026-08-26, charter §A57 BY FALSIFICATION. CAUSE: RANGE.
        SUBJECT-ERA: HISTORICAL — EP-30-C3's move is FINISHED, and this row's whole subject is
        what THIS UNIT'S PASS did to the founding version.
        CAUSE, DRIVEN AT THE COMPARISON SITE: the row asserts the founding minor is 28 and read
        30. Two different questions were asked of the history and they do not agree, which is
        the finding rather than a detail. WHEN DID TODAY'S VALUE ARRIVE? At `b64defaa`, which is
        EP-30-K2's move — and that answer names the wrong unit. WHAT FIRST FALSIFIED THE ROW?
        `40fddd9c`, EP-30-K1's move, 1.28.0 -> 1.29.0: THE ROW WAS ALREADY FALSE BEFORE K2
        TOUCHED ANYTHING. K2's move deepened a value that was already wrong; it did not falsify
        a true row.
        ASSERTED: the close end read from `founding_version()` — THE LIVE TREE.
        SUPERSEDED: the close end read from the pack at `C3_MOVE_COMMIT`, verified BY DIGEST
        first. A row that declares itself a reading of what THIS pass did, and then reads the
        live tree, is a MOMENT AT ONE END ONLY — its open end silently makes C3's arithmetic a
        claim about every founding move that arrives afterwards, forever. That is not a guard
        that caught something; it is a guard that reds because somebody else moved, which is
        this campaign's open-range family and MAINT-2's class exactly.
        REMAINS TRUE, carrying both its literals unchanged: EP-30-C3 moved the founding by
        exactly one MINOR, 1.27.0 -> 1.28.0, and reset PATCH. The MAJOR stop is unchanged.
        GIVEN UP: nothing this row ever asserted. What it GAINS is invariance to every later
        founding move — the reason this row is EP-30-K1R's and rows 2 and 4 of the same
        population are EP-30-K2R's, per mtr `:2304`: a re-pin may be authored only once, to the
        population that exists after the LAST move, and a repair that reads no later move at
        all cannot be stale on the day it lands.
        THE TECHNIQUE IS tests/test_ep30_c1.py:310-317's, TAKEN WHOLE AND NOT IN HALF. The sha
        guard is not decoration around the pin; it IS the pin. Copying the commit constant
        without it would build something worse than the live read it replaces, because a live
        read at least fails loudly when the world moves.]"""
        self.assertEqual(
            hashlib.sha256(era_pin.blob_at(self.C3_MOVE_COMMIT,
                                           era_pin.PACK_PATH)).hexdigest(),
            self.C3_MOVE_PACK_SHA,
            "the close-era pack is not the bytes EP-30-C3 moved the founding over, so the "
            "commit above is an alias for something else and the arithmetic below is about "
            "the wrong world")
        now = tuple(int(part) for part
                    in era_pin.pack_at(self.C3_MOVE_COMMIT)["founding_version"].split("."))
        self.assertEqual(now[0], self.OPENED[0],
                         "the founding moved by MAJOR — the plan's §8 says stop, to the owner")
        self.assertEqual(now[1], self.OPENED[1] + 1, "expected a MINOR move")
        self.assertEqual(now[2], 0, "a MINOR move resets PATCH")

    def test_a2_the_law_is_declared_and_the_op_cites_it_by_name(self):
        """A2 — KIND: INSPECTED. The version row's meaning.

        A pass can bump a version and land nothing. This asserts the SURFACE the bump is FOR:
        a rule the founding contains, and an operation whose `law_cited` names it. The estate's
        containment line (EP-25 ADDENDUM 4) is that no refusal path may cite a rule name the
        founding does not contain — so the citation and the rule are checked TOGETHER, never
        one without the other."""
        laws = {r["payload"].get("rule_id")
                for step in _pack()["steps"] for r in step.get("records", [])
                if r.get("action") == "CREATE-RULE"}
        self.assertIn("FS-LAW-CUSTODY-TRANSFER", laws,
                      "the operation would cite a rule the founding does not contain")

        definition = transfer_definition()
        self.assertEqual(definition["law_cited"], "FS-LAW-CUSTODY-TRANSFER")
        for check in definition["checks"]:
            self.assertTrue(check.get("cite"), "a check that cites nothing is unrecordable")

    def test_a2_the_op_names_two_parties_a_handle_and_an_inherited_device(self):
        """A2 — KIND: INSPECTED. Identity, not arity.

        A bare count would pass on four WRONG parameters, which is the defect this row exists to
        bar — EP-30-C1's own A1/A2 split, inherited deliberately.

        [DOCUMENTED FLIP — EP-30-K1R, 2026-08-26, charter §A57 BY FALSIFICATION. CAUSE:
        INDEXING. SUBJECT-ERA: LIVE, and deliberately so — unlike its neighbour above, this
        row's subject is the op the estate SHIPS TODAY, and an era-pin here would assert that
        C3 once landed four checks while saying nothing about what the founding now carries.
        CAUSE, DRIVEN AT THE COMPARISON SITE: `by_param["from_entity"]["action"]` read
        'FILE-CUSTODY-TRANSFER' where it expects 'CREATE-ACCOUNT'. EP-30-K1's founding move
        (`40fddd9c`, 1.28.0 -> 1.29.0) shipped a `bound_field` check ON THIS SAME OP declaring
        `param: from_entity`, and `{c["param"]: c for c in checks}` COLLAPSES two checks on one
        param and silently keeps the LAST one written.
        ASSERTED: a dict from param to THE check on it — a one-check-per-param world that was
        never law and was only ever true by accident of how many rows C3 happened to write.
        SUPERSEDED: a dict from param to ALL its checks, and the establishment claim made
        against the `require_prior` rows specifically, with EXACTLY ONE required per param.
        REMAINS TRUE: every literal this row ever asserted — both parties checked against
        CREATE-ACCOUNT/account_id, the handle against FILE-OPEN, the device against BIND-DEVICE.
        GIVEN UP: nothing. THE ROW IS STRICTLY STRONGER AFTER THIS REPAIR, and that is the
        answer to the only real objection to it. Before, a second `require_prior` on a party
        could be added and this row would report whichever was written last — it asserted the
        LAST check, which is not a property anybody chose. Now it asserts that there is EXACTLY
        ONE, so both a REMOVED establishment check and a DUPLICATED one red here, and neither
        did before.
        THE SHARPER HALF OF THE FINDING, kept because it is the reusable part: the arity
        assertion two lines below the collapse PASSED THROUGHOUT. A dict keyed by param hides a
        second check on that param from the count as well as from the read, so the row whose own
        docstring says "identity, not arity" was blind to exactly the event it names.]"""
        definition = transfer_definition()
        self.assertEqual(sorted(definition["params"].items()),
                         [("device", "required"), ("from_entity", "required"),
                          ("handle", "required"), ("to_entity", "required")])
        self.assertEqual(sorted(definition["payload_from"]),
                         ["device", "from_entity", "handle", "to_entity"])

        # EVERY check on each param, never just the last one written. A param may lawfully
        # carry more than one check row and a later kind may add one; what this row asserts is
        # what each param is CHECKED AGAINST, not how many checks a later unit chose to hang
        # on it.
        by_param = {}
        for check in definition["checks"]:
            by_param.setdefault(check["param"], []).append(check)
        self.assertEqual(sorted(by_param), ["device", "from_entity", "handle", "to_entity"])

        #: the establishment claim lives in the `require_prior` rows, so they are selected BY
        #: KIND rather than by position, and EXACTLY ONE is required per param — a second one
        #: would mean the op checks a param against two different foundings.
        founding_check = {}
        for param, checks in by_param.items():
            prior = [c for c in checks if c["check"] == "require_prior"]
            self.assertEqual(len(prior), 1,
                             "%r carries %d require_prior checks, not one — the parameter is "
                             "founded on two different records or on none, and either way this "
                             "row's claim about what founds it is unanswerable"
                             % (param, len(prior)))
            founding_check[param] = prior[0]

        # both PARTIES are checked against the establishment record, which is what makes them
        # parties rather than strings
        for party in ("from_entity", "to_entity"):
            self.assertEqual(founding_check[party]["action"], "CREATE-ACCOUNT")
            self.assertEqual(founding_check[party]["field"], "account_id")
        # the handle is checked against the grant that opened it
        self.assertEqual(founding_check["handle"]["action"], "FILE-OPEN")
        # THE INHERITANCE, STATED IN THE LAW ITSELF: the device is checked against EP-29's
        # landing, so the transfer cannot name a device no binding founded
        self.assertEqual(founding_check["device"]["action"], "BIND-DEVICE")
        self.assertEqual(founding_check["device"]["field"], "device")


# =====================================================================================
# A3 — A TRANSFER APPENDS A DECISION BETWEEN TWO ENTITIES
# =====================================================================================

class TransferRecordedCase(WorldCase):

    def test_a3_a_handover_appends_one_decision_naming_both_entities(self):
        """A3 — KIND: DRIVEN, WITH A POSITIVE CONTROL INSIDE IT.

        PART 1 RUNS FIRST AND IS NOT OPTIONAL. The vacuity mode here is not "an extra record
        sneaks in", it is "the drive never happened" — an empty transfer list passes every
        assertion below by having nothing to iterate."""
        self.world()
        before = len(self.transfers())

        self.hand_over()

        appended = self.transfers()
        self.assertEqual(len(appended) - before, 1,
                         "the handover appended %d decisions, not 1 — every assertion below "
                         "would be about the wrong population" % (len(appended) - before))

        record = appended[-1]
        payload = dict(record["payload"])
        # BOTH parties named IN THE RECORD — the whole difference from an attribute mutation,
        # which names one thing and no parties at all
        self.assertEqual(payload["from_entity"], GIVER)
        self.assertEqual(payload["to_entity"], TAKER)
        self.assertNotEqual(payload["from_entity"], payload["to_entity"],
                            "a handover to the giver is not a handover")
        # the handle's identity carried in the record
        self.assertEqual(payload["handle"], HANDLE)
        # and it cites its rule, which is what makes it a governed decision rather than a write
        self.assertEqual(record["rule_cited"], "FS-LAW-CUSTODY-TRANSFER")

    def test_a3_the_class_map_classifies_the_new_action(self):
        """A3's companion, and it is a real trap rather than a formality: the conformance
        harness reads `CUSTODY_CLASS_MAP` AS DATA and holds no vocabulary of its own, so an
        action absent from it fails check 2 as UNCLASSIFIED. A new action that nobody classified
        is the honest outcome for exactly that — which is why this is asserted and not assumed."""
        self.assertEqual(custody.CUSTODY_CLASS_MAP["FILE-CUSTODY-TRANSFER"], "DECISION")

    def test_a3_the_transfer_fold_is_kept_apart_from_the_namespace_and_lock_folds(self):
        """A3's structural companion. The three action sets answer three DIFFERENT questions and
        the module's own comment says so. Merging them would make one fold react to records that
        cannot change what it serves — and `tests/test_ep25.py` asserts that a refused act
        appends nothing in `CUSTODY_ACTIONS`, a row that would change meaning silently."""
        self.assertNotIn("FILE-CUSTODY-TRANSFER", custody.CUSTODY_ACTIONS)
        self.assertNotIn("FILE-CUSTODY-TRANSFER", custody.LOCK_ACTIONS)
        self.assertIn("FILE-CUSTODY-TRANSFER", custody.CUSTODY_TRANSFER_ACTIONS)


# =====================================================================================
# A4 — THE DEVICE IDENTITY IS INHERITED, NEVER RE-DERIVED
# =====================================================================================

class IdentityInheritedCase(WorldCase):

    def _comparison(self):
        """A4's comparison, ENTRY BY ENTRY, returned as data so the row and its red world read
        the SAME table rather than two implementations of it."""
        founded = {(e.get("payload") or {}).get("device")
                   for e in self.store.by_action("BIND-DEVICE")}
        rows = []
        for e in self.transfers():
            recorded = custody.transferred_device(e)
            rows.append({"handle": (e.get("payload") or {})["handle"],
                         "recorded": recorded,
                         "founded_by_a_binding": recorded in founded})
        return founded, rows

    def test_a4_every_transfer_carries_the_device_identity_the_binding_founded(self):
        """A4 — KIND: DRIVEN. The comparison is stated entry by entry, never as a count.

        EP-30's own clause is the law here, and it is binding: *custody transfers move things BY
        FORMAL NAME — device identity inherited from EP-29's landing, never re-derived
        channel-side.*"""
        self.world()
        self.hand_over()
        self.open_handle("/second.txt")
        self.hand_over(handle="/second.txt", from_entity=TAKER, to_entity=GIVER)

        founded, rows = self._comparison()
        self.assertEqual(len(rows), 2,
                         "the comparison has %d entries — an entry-by-entry claim over fewer "
                         "than the drives performed is about the wrong population" % len(rows))
        self.assertEqual(founded, {DEVICE})
        for row in rows:
            self.assertEqual(row["recorded"], DEVICE,
                             "%s carries device %r, and the binding founded %r"
                             % (row["handle"], row["recorded"], DEVICE))
            self.assertTrue(row["founded_by_a_binding"],
                            "%s names a device no BIND-DEVICE founded" % row["handle"])

    def test_a4_the_channel_side_reads_the_device_and_does_not_resolve_it(self):
        """A4's second half — THE NON-DERIVATION, shown rather than asserted.

        A reader that RESOLVED would not be able to echo a value no binding ever founded; a
        reader that READS returns exactly the bytes the record carries. So handing it a record
        naming an unfounded device separates the two implementations, and nothing else in this
        file does."""
        synthetic = {"action": "FILE-CUSTODY-TRANSFER",
                     "payload": {"handle": "/x", "device": "NO-BINDING-EVER-FOUNDED-THIS"}}
        self.assertEqual(custody.transferred_device(synthetic), "NO-BINDING-EVER-FOUNDED-THIS",
                         "the channel side resolved instead of reading — a resolver could not "
                         "return a value no binding founded, so this reader derives")

    def test_a4_a_device_no_binding_founded_is_refused_at_the_door(self):
        """A4's door half. The inheritance is not a convention the caller may decline: a
        transfer naming an unfounded device is REFUSED, citing the rule."""
        self.world()
        rule, message = self.refusal_of(self.hand_over, device="virtio-never-bound")
        self.assertEqual(rule, "FS-LAW-CUSTODY-TRANSFER")
        self.assertIn("BIND-DEVICE", message)

        # the positive control: the SAME act with the founded device is admitted
        self.hand_over()
        self.assertEqual(len(self.transfers()), 1)


# =====================================================================================
# A5 — THE VIEW IS A FOLD
# =====================================================================================

class ViewIsAFoldCase(WorldCase):

    def test_a5_who_holds_this_handle_now_survives_replay_from_empty(self):
        """A5 — KIND: DRIVEN. Asked twice: once of the running fold, once of a fold rebuilt from
        the record alone, and the second is computed WITHOUT reading any stored holder field.

        THIS IS T-CUSTODY-IS-DERIVED POINTED AT THE NEW QUESTION: kill every derived structure,
        replay the record, and the same answer comes back."""
        self.world()
        self.hand_over()

        # HALF ONE — the LIVE fold, fed incrementally by the store's on-append listener. It has
        # never replayed anything.
        self.assertEqual(self.live.holder_of(HANDLE), TAKER,
                         "the live fold does not answer who holds the handle, so the comparison "
                         "below would be two Nones agreeing — the vacuous pass")
        self.assertGreater(self.live.applied, 0,
                           "the live fold folded NOTHING, so it is not the incremental half and "
                           "this row is comparing a replay against a replay")

        # HALF TWO — a fold built from the record ALONE, from empty.
        replayed = self.replayed()
        self.assertEqual(replayed.holder_of(HANDLE), TAKER)
        self.assertEqual(self.live.snapshot(), replayed.snapshot(),
                         "the incrementally-maintained answer and the replayed answer differ — "
                         "which can only mean a record was missed, never that two "
                         "implementations disagreed about what a record means")

        # NOTHING STORED HOLDS THE ANSWER: no Inode field, no attribute on the file. The only
        # structures that hold it are two folds, and one of them was just built from the record.
        self.assertFalse(hasattr(custody.Inode, "holder"),
                         "an Inode gained a holder field — a stored copy of the record")
        self.assertNotIn("holder", custody.Inode.__slots__)

    def test_a5_a_second_handover_moves_the_answer_latest_wins(self):
        """A5's polarity, and it is the half a reader is most likely to get backwards. Custody
        is the LATEST transfer, never the first and never a set of everyone who has ever held it.

        THE RECORD KEEPS EVERY ACT — that is what an append-only record is — while the DERIVED
        answer is the one in force. EP-30-E1 (`:888`) is the ground: a current holding is
        expressible precisely because the state is written as an amending declaration of the
        SAME action under latest-seq-wins."""
        self.world()
        self.establish("E3")
        self.hand_over()
        self.assertEqual(self.replayed().holder_of(HANDLE), TAKER)

        self.hand_over(from_entity=TAKER, to_entity="E3")

        self.assertEqual(self.replayed().holder_of(HANDLE), "E3")
        self.assertEqual(self.live.holder_of(HANDLE), "E3",
                         "the live half did not follow the second handover — an incremental "
                         "fold that misses a record is the divergence A5 exists to catch")
        self.assertEqual(len(self.transfers()), 2,
                         "both acts are history — the record holds every act, the fold holds "
                         "the one in force")

    def test_a5_an_untransferred_handle_answers_none_and_that_is_an_answer(self):
        """A5's honest edge, asserted so it cannot rot into a surprise. A handle opened and never
        handed over has NO transfer record, so the fold says None. Answering the opener would be
        the fold inventing a holder the record never named — `FILE-OPEN` declares no entity at
        all. RAISED at the close; not papered over here."""
        self.world()
        self.assertIsNone(self.replayed().holder_of(HANDLE))
        self.assertIsNone(self.live.holder_of(HANDLE))


# =====================================================================================
# §4 RED WORLDS — each DIFFERENTIAL, each stating which way its own verdict moves
# =====================================================================================

class R1AttributeShapeRefusedCase(WorldCase):
    """R1 — THE ATTRIBUTE SHAPE IS REFUSED.

    DIRECTION, stated by the row for itself (`:1715`): the verdict moves from ADMITTED (plant
    removed — both parties are established entities) to REFUSED (plant present — the receiver is
    a bare attribute value). The plant is the ATTRIBUTE SPELLING of the handover.

    WHAT MAKES A VALUE AN ATTRIBUTE AND A NAME A PARTY, which is the whole content of the row:
    an attribute value is ANY STRING A CALLER WRITES, and a party is a RECORDED ESTABLISHMENT.
    A law under which any string can receive custody has not established the entity vocabulary —
    it has only declared it — and that is the sentence R1 ends on."""

    def test_r1_a_handover_to_a_bare_attribute_value_is_refused_citing_the_rule(self):
        self.world()

        # CONTROL FIRST (:1706): plant REMOVED, the same act with a PARTY is ADMITTED. Without
        # this the refusal below could be a refusal of everything, and the row would prove
        # nothing about the attribute shape.
        self.hand_over()
        self.assertEqual(len(self.transfers()), 1,
                         "the control act was not admitted, so the refusal below is not "
                         "attributable to the plant and this row STOPS")

        # PLANT: the receiver is a bare value — the attribute spelling. `holder=some-string` is
        # exactly what an xattr write would carry.
        rule, message = self.refusal_of(self.hand_over, to_entity="just-a-string-nobody-established")
        self.assertEqual(rule, "FS-LAW-CUSTODY-TRANSFER",
                         "a property-value receiver raised something other than a cited refusal")
        self.assertIn("entity", message.lower())
        # and nothing was appended for the refused shape
        self.assertEqual(len(self.transfers()), 1)

    def test_r1_the_giver_is_checked_too_so_the_shape_cannot_be_entered_from_either_end(self):
        """R1's mirror. A law that checked only the RECEIVER would still admit a handover FROM a
        bare value, and a transfer with one party is an attribute mutation with a second field."""
        self.world()
        rule, message = self.refusal_of(self.hand_over, from_entity="not-established-either")
        self.assertEqual(rule, "FS-LAW-CUSTODY-TRANSFER")
        self.assertIn("entity", message.lower())

    def test_r1_the_fold_is_unmoved_by_an_attribute_write_on_the_file(self):
        """R1's other end, and it is the one that answers the plan's §2 directly: an ATTRIBUTE
        MUTATION ON THE FILE does not move custody, because custody is not a property of the
        file. Driving the attribute spelling literally — an xattr write — leaves the fold's
        answer exactly where the last recorded DECISION BETWEEN PARTIES put it.

        THE CONTROL IS INSIDE THE ROW: the xattr write is shown LANDING (it is a lawful POSIX
        act and this unit does not forbid it), so the unmoved custody answer is attributable to
        the fold's subject and not to a write that never happened."""
        self.world()
        self.hand_over()
        self.assertEqual(self.replayed().holder_of(HANDLE), TAKER)

        before = len(self.store.by_action("FILE-XATTR-SET"))
        self.gate.execute("FILE-XATTR-SET", "owner",
                          {"path": HANDLE, "name": "user.holder", "value": GIVER,
                           "provenance": PROV})
        self.assertEqual(len(self.store.by_action("FILE-XATTR-SET")) - before, 1,
                         "the attribute write did not land, so this row's claim that it MOVES "
                         "NOTHING is vacuous")

        self.assertEqual(self.replayed().holder_of(HANDLE), TAKER,
                         "an attribute write moved custody — the transfer is spellable as a "
                         "property change and the entity vocabulary is not established")


class R2ReDerivedIdentityRedsCase(WorldCase):
    """R2 — A RE-DERIVED IDENTITY REDS.

    DIRECTION, stated by the row for itself: A4's comparison moves from HOLDS (plant removed) to
    FAILS (plant present). The plant is a CHANNEL-SIDE DERIVATION of the device identity
    standing where the inherited read belongs."""

    def _founded_and_recorded(self):
        founded = {(e.get("payload") or {}).get("device")
                   for e in self.store.by_action("BIND-DEVICE")}
        return founded, [custody.transferred_device(e) for e in self.transfers()]

    def test_r2_a_channel_side_derivation_makes_a4_fail_and_names_the_divergence(self):
        self.world()
        self.hand_over()

        # CONTROL FIRST (:1706): plant REMOVED, A4's comparison HOLDS.
        founded, recorded = self._founded_and_recorded()
        self.assertEqual(recorded, [DEVICE])
        self.assertTrue(all(r in founded for r in recorded),
                        "A4's comparison already fails without the plant, so this red world "
                        "proves nothing and STOPS")

        # PLANT: the channel derives the device from what it can see — the handle — instead of
        # inheriting the value the binding founded. It is internally consistent and stable
        # across runs, which is exactly why nothing else would catch it.
        real = custody.transferred_device

        def derived_channel_side(e):
            handle = (e.get("payload") or {}).get("handle")
            digest = hashlib.blake2b(str(handle).encode("utf-8"), digest_size=4).hexdigest()
            return "dev:" + digest
        custody.transferred_device = derived_channel_side
        self.addCleanup(setattr, custody, "transferred_device", real)

        founded, recorded = self._founded_and_recorded()
        self.assertNotEqual(recorded, [DEVICE],
                            "the plant did not change what the channel answers, so this red "
                            "world proves nothing")
        divergent = [r for r in recorded if r not in founded]
        self.assertEqual(len(divergent), 1,
                         "A4 did not fail under the plant — a derivation that agrees with the "
                         "binding by accident is the coincidence this row exists to exclude")
        # THE DIVERGENCE IS NAMED, not merely counted
        self.assertTrue(divergent[0].startswith("dev:"))
        self.assertNotIn(divergent[0], founded)

    def test_r2_the_derivation_is_invisible_to_the_record_and_the_view(self):
        """R2's sting, and it is the finding the plan's §2 is written around. Under the plant
        the RECORD is unchanged and the derived custody view is unchanged — only the identity
        the channel answers with has moved. Every guard in this estate runs record to view, so
        nothing looks the way this defect points."""
        self.world()
        self.hand_over()
        before_record = [dict(e["payload"]) for e in self.transfers()]
        before_view = self.replayed().holder_of(HANDLE)

        real = custody.transferred_device
        custody.transferred_device = lambda e: "dev:derived"
        self.addCleanup(setattr, custody, "transferred_device", real)

        self.assertEqual([dict(e["payload"]) for e in self.transfers()], before_record,
                         "the record moved — then the defect is visible and this row is about "
                         "something else")
        self.assertEqual(self.replayed().holder_of(HANDLE), before_view)
        # and yet the device the channel answers with is now an invention
        self.assertEqual(self.replayed().device_of(HANDLE), "dev:derived")


class R3ViewCannotBeStoredStateCase(WorldCase):
    """R3 — THE VIEW CANNOT BE STORED STATE.

    DIRECTION, stated by the row for itself: A5's two halves move from AGREE (plant removed) to
    DIVERGE (plant present). The plant is a STORED HOLDER FIELD written by the execute path,
    which a replay from empty cannot reproduce because replay does not run the execute path."""

    def test_r3_a_stored_holder_field_makes_the_replay_half_diverge(self):
        self.world()
        self.hand_over()

        # CONTROL FIRST (:1706): plant REMOVED, the live half and the replay half AGREE.
        self.assertEqual(self.live.holder_of(HANDLE), TAKER)
        self.assertEqual(self.live.snapshot(), self.replayed().snapshot(),
                         "the halves already disagree without the plant, so this red world "
                         "proves nothing and STOPS")

        # PLANT: the fold stops DERIVING the holder from the record. The live view keeps the
        # answer it is already holding — which is precisely what a STORED HOLDER FIELD is: a
        # value the running view has and the record cannot reproduce. Nothing about the record
        # changes; only where the answer comes from does.
        real_apply = custody.HandleCustody.apply
        custody.HandleCustody.apply = lambda self, e: None
        self.addCleanup(setattr, custody.HandleCustody, "apply", real_apply)

        replayed_under_plant = custody.fold_custody(self.store.all())

        self.assertEqual(self.live.holder_of(HANDLE), TAKER,
                         "the live view lost its answer too, so the divergence below is not "
                         "between a stored answer and a derived one")
        self.assertIsNone(replayed_under_plant.holder_of(HANDLE),
                          "the plant did not stop the fold deriving, so this red world proves "
                          "nothing")
        self.assertNotEqual(self.live.holder_of(HANDLE), replayed_under_plant.holder_of(HANDLE),
                            "A5 did not fail under the plant — the two halves still agree, "
                            "which is the vacuous pass this row exists to exclude")
        self.assertNotEqual(self.live.snapshot(), replayed_under_plant.snapshot())

    def test_r3_agreement_between_two_reads_of_one_stored_field_is_not_evidence(self):
        """R3's own sentence, made mechanical: *a view that agrees with itself because it read
        the same stored field twice has proved nothing.*

        THE DEMONSTRATION IS THE POINT AND IT IS NOT A RESTATEMENT. Two reads of ONE structure
        agree unconditionally — they agree even when the record underneath says nothing at all.
        Driven here by asking the SAME live view twice while the record that would justify it is
        empty, so the agreement is shown to carry NO information about the record. That is why
        A5's two halves come from two SOURCES and never from one structure read twice."""
        self.world()
        self.hand_over()

        # one structure, asked twice: unconditional agreement
        self.assertEqual(self.live.holder_of(HANDLE), self.live.holder_of(HANDLE))

        # and the same question against an EMPTY record derives None — a fact the two agreeing
        # reads above are structurally incapable of noticing
        self.assertIsNone(custody.fold_custody([]).holder_of(HANDLE),
                          "an empty record derived a holder, so the fold is not reading the "
                          "record at all and A5's second half proves nothing")


class R4AbsenceControlCanFailCase(unittest.TestCase):
    """R4 — THE ABSENCE CONTROL CAN FAIL.

    DIRECTION, stated by the row for itself: the SAME query returns ZERO on a coined token and
    NON-ZERO on a needle known present. The 'plant' here is the choice of needle, and the
    verdict moves with it — which is what proves A1's zero is a fact about the tree rather than
    a fact about the query."""

    def test_r4_a_coined_token_reads_zero_and_a_known_needle_does_not(self):
        coined = "ZZ-COINED-TOKEN-NO-HAND-EVER-WROTE-THIS"
        self.assertEqual(elsewhere(coined), {},
                         "a token nobody wrote was FOUND outside this file — the sweep matches "
                         "things that are not there and every absence it reports is void")
        # the coined token IS in this file, which is what makes the exclusion above a real
        # exclusion rather than a no-op dressed as one
        self.assertEqual(sorted(sweep(coined)), [SELF])
        self.assertGreater(len(elsewhere("FILE-CREATE")), 0,
                           "the query found nothing it was meant to find, so its emptiness is "
                           "a fact about the query")

    def test_r4_the_verb_this_unit_minted_is_now_present_and_that_is_the_query_moving(self):
        """R4's sharpest half, and it is the one that proves the sweep is live on THIS unit's
        own subject rather than on a needle chosen because it is easy.

        The verb read ZERO before this unit's first edit — driven and dated at
        `planning/evidence/EP-30-C3/A1-ABSENCE-AND-CONTROL.txt` — and reads NON-ZERO now. The
        same query, the same population, a verdict that MOVED because the tree moved.

        AND IT IS ASSERTED OUTSIDE THIS FILE, which is the half that carries the weight: a verb
        present only in the row that looks for it would be this file talking to itself."""
        found = elsewhere("FILE-CUSTODY-TRANSFER")
        self.assertGreater(len(found), 0,
                           "the verb this unit minted is not in the tree outside this file — "
                           "either the unit landed nothing or the sweep cannot see what it "
                           "landed")
        self.assertIn("src/bridge/custody.py", found,
                      "the verb is not in the custody plane it was minted for")
        self.assertIn("src/founding/founding-pack.json", found,
                      "the verb is not in the founding — then it entered by some door other "
                      "than the front one")


if __name__ == "__main__":
    unittest.main()
