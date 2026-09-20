# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-30-C0 — the durability barrier moves to the engine, and the substrate stops being
unobservable.

Plan: `planning/exec/EP-30-C0.md`, countersigned whole-plan at board `:1502`
(sha256 4d3ad228…, 19,713 B; §3 sub-digest 303cad0a…, 8,350 B).

THE LAW THIS FILE CHECKS IS AN ORDERING, NOT A MECHANISM: **content durable before the
record that names it.** Every row below drives that ordering rather than reading it out
of the source, because the ordering is a RUNTIME property — `:1438`, a row is driveable
iff its subject is present, and the calls are present only while `put` runs.

The red worlds (§4 of the plan) live at the bottom and share the row function with the
green ones. That sharing is the point: R1, R2 and R4 apply the SAME verdict function to
a different world, so a row that cannot be made to red by breaking the very thing it
asserts is visible as a row that asserts nothing.

WHAT THESE ROWS WATCH, SAID PLAINLY, BECAUSE THE DISTINCTION COST THIS PASS A STOP.
A2, A3 and the red worlds watch BEHAVIOUR — a recorded call order at runtime. Move the
barrier to another module, another function, another file, and they still pass, because
they never look at where the code lives. A1 and A4's population row watch TEXT — two
substrings in a docstring, and the literal `BlobStore(` at three sites. A SITE-WATCHER
CANNOT TELL A DEFECT FROM A CURE: a regression and a lawful relocation both delete the
site it looks at. That is not hypothetical here — this unit's own lawful move tripped a
site-watching row in another EP's file, and that row's message concluded a falsehood it
could not distinguish from a relocation. So: the failure messages below name what was
observed and stop there. A FAILURE MESSAGE IS A CLAIM AND IT MUST BE NO STRONGER THAN
THE ASSERTION THAT PRODUCES IT.
"""

import hashlib
import os
import shutil
import stat
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))

from kernel import blobs as blobs_mod                          # noqa: E402
from kernel.blobs import BlobStore                             # noqa: E402
from bridge import host_seam as seam_mod                       # C7 P2 (:3927) — the barrier's host calls now issue from the seam  # noqa: E402


#: Evidence printing is gated so the two full-suite arms stay quiet; the ASSERTIONS are
#: never gated. The dedicated evidence drive sets EP30C0_VERBOSE=1 and captures stdout.
VERBOSE = os.environ.get("EP30C0_VERBOSE") == "1"


def _say(*parts):
    if VERBOSE:
        print(*parts)


# ---------------------------------------------------------------------------
# THE RECORDER — an `os` stand-in that records the barrier calls and delegates the rest.
# ---------------------------------------------------------------------------

class _RecordingFile:
    """Wraps the real file object so `write` and `flush` land in the same call list as
    the `os` calls. Without this the recorded order would begin at the fsync and the
    row could not tell `write -> flush -> fsync` from `flush -> write -> fsync`."""

    def __init__(self, real, calls):
        self._real = real
        self._calls = calls

    def write(self, b):
        self._calls.append("write")
        return self._real.write(b)

    def flush(self):
        self._calls.append("flush")
        return self._real.flush()

    def fileno(self):
        return self._real.fileno()

    def close(self):
        return self._real.close()

    def __enter__(self):
        self._real.__enter__()
        return self

    def __exit__(self, *exc):
        return self._real.__exit__(*exc)


class RecordingOS:
    """A stand-in for the `os` module that records exactly the calls the ordering law
    names, and delegates everything else to the real module.

    THE FILE fsync AND THE PARENT-DIRECTORY fsync ARE TOLD APART BY `fstat` ON THE
    DESCRIPTOR, NEVER BY CALL POSITION. A positional guess would make the row's own
    ordering claim circular — it would be reading the order it is trying to establish.
    """

    def __init__(self, real=os):
        self._real = real
        self.calls = []

    def __getattr__(self, name):                 # O_WRONLY, path, makedirs, stat, ...
        return getattr(self._real, name)

    def fdopen(self, fd, *a, **kw):
        return _RecordingFile(self._real.fdopen(fd, *a, **kw), self.calls)

    def fsync(self, fd):
        is_dir = stat.S_ISDIR(self._real.fstat(fd).st_mode)
        self.calls.append("fsync(parent dir)" if is_dir else "fsync(file)")
        return self._real.fsync(fd)

    def replace(self, src, dst):
        self.calls.append("replace(tmp, final)")
        return self._real.replace(src, dst)


#: The hand-computed literal of plan §3 A2. Not derived from the subject.
EXPECTED_ORDER = ["write", "flush", "fsync(file)", "replace(tmp, final)", "fsync(parent dir)"]


def barrier_verdict(calls):
    """THE ROW ITSELF. A2 applies it to the engine; R1, R2 and R4 apply it to worlds.

    Returns (verdict, detail). The detail names WHICH way the world diverged, because
    "same calls, wrong order" and "a call is missing" are different findings and R2
    exists precisely to separate them.
    """
    if calls == EXPECTED_ORDER:
        return "MET", "call order matches the hand-computed literal"
    if not calls:
        return "UNMET", ("NO CALLS RECORDED AT ALL — the barrier did not run, or the "
                         "recorder was not live. An empty call list is not a passing "
                         "absence; it is an untested row.")
    if sorted(calls) == sorted(EXPECTED_ORDER):
        # A FAILURE MESSAGE IS A CLAIM AND IT MUST BE NO STRONGER THAN THE ASSERTION THAT
        # PRODUCES IT. What is established here is that the same calls occurred in a
        # different sequence — NOT that the bytes ended up durable, which is true of R2's
        # world but not of every permutation this branch catches.
        return "UNMET", ("ORDER WRONG — every expected call is present exactly once and "
                         "only the SEQUENCE differs. got %s" % (" -> ".join(calls),))
    missing = [c for c in EXPECTED_ORDER if c not in calls]
    extra = [c for c in calls if c not in EXPECTED_ORDER]
    return "UNMET", ("CALLS DIFFER — missing %s, unexpected %s. got %s"
                     % (missing or "none", extra or "none", " -> ".join(calls) or "<empty>"))


def drive_put(store, data, recorder=None):
    """Drive `BlobStore.put` under a recording `os` and return (hash, calls).

    The seam is the module global `bridge.host_seam.os` — C7 P2 (:3927) routed the
    blobs barrier's host calls (write-once, file/parent fsync, replace, remove) into the
    seam performer, so the recorder is planted there and the store is driven exactly as it
    ships. Patching it means the production code needs no injection point of its own.
    """
    recorder = recorder if recorder is not None else RecordingOS()
    real = seam_mod.os
    seam_mod.os = recorder
    try:
        h = store.put(data)
    finally:
        seam_mod.os = real
    return h, list(recorder.calls)


class _TmpMixin:
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="ep30c0-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def blobdir(self, name="blobs"):
        return os.path.join(self.tmp, name)


# ---------------------------------------------------------------------------
# A1 — THE LAW IS STATED AS ORDERING, NOT AS MECHANISM
# ---------------------------------------------------------------------------

ORDERING_SENTENCE = "CONTENT DURABLE BEFORE THE RECORD THAT NAMES IT"


class A1LawStatedAsOrdering(unittest.TestCase):
    """The docstring is read from the LIVE module object, not from the file — the
    docstring a consumer actually gets is the one on the imported module."""

    def test_module_docstring_states_the_ordering_in_these_words(self):
        doc = blobs_mod.__doc__ or ""
        hits = [ln.strip() for ln in doc.splitlines() if ORDERING_SENTENCE in ln]
        _say("A1 ORDERING SENTENCE:", hits[0] if hits else "<ABSENT>")
        self.assertTrue(hits, "module docstring does not carry %r" % ORDERING_SENTENCE)

    def test_module_docstring_says_the_mechanism_is_not_the_law(self):
        doc = blobs_mod.__doc__ or ""
        low = doc.lower()
        # A DOCSTRING NAMING ONE MECHANISM AS THE LAW IS UNMET: the next subsystem would
        # inherit this implementation's accidents as requirements.
        # The messages name the SUBSTRING that is absent, not the meaning. Absence of a
        # phrase is not absence of the idea, and the assertion only reaches the phrase.
        self.assertIn("any implementation", low,
                      "the substring 'any implementation' is absent from the module "
                      "docstring")
        self.assertIn("an implementation", low,
                      "the substring 'an implementation' is absent from the module "
                      "docstring")
        shown = [ln.strip() for ln in doc.splitlines()
                 if "any implementation" in ln.lower() or "an implementation" in ln.lower()]
        for ln in shown:
            _say("A1 IMPLEMENTATION-IS-NOT-THE-LAW:", ln)
        self.assertTrue(shown)


# ---------------------------------------------------------------------------
# A2 — THE BARRIER IS IN THE ENGINE AND IT IS DRIVEN, NOT INSPECTED
# ---------------------------------------------------------------------------

class A2BarrierOrderDriven(_TmpMixin, unittest.TestCase):

    def test_put_records_the_hand_computed_call_order(self):
        store = BlobStore(self.blobdir())
        h, calls = drive_put(store, b"a2-payload")
        verdict, detail = barrier_verdict(calls)
        _say("A2 CALL ORDER:", " -> ".join(calls) or "<empty>")
        _say("A2 EXPECTED   :", " -> ".join(EXPECTED_ORDER))
        _say("A2 VERDICT    :", verdict, "|", detail)
        self.assertEqual(verdict, "MET", detail)
        # POPULATION: one `put` of new bytes. BASIS: the recorded call order.
        self.assertEqual(store.get(h), b"a2-payload")

    def test_the_bytes_land_under_their_content_name(self):
        store = BlobStore(self.blobdir())
        h, _ = drive_put(store, b"a2-payload")
        self.assertTrue(store.has(h))
        # No temp file survives the barrier.
        leftovers = [p for p, _, fs in os.walk(self.blobdir()) for f in fs if f.endswith(".part")]
        self.assertEqual(leftovers, [], "a .part temp file outlived put()")


# ---------------------------------------------------------------------------
# A3 — DEDUP STILL SHORT-CIRCUITS, WITH THE POSITIVE CONTROL FIRST
# ---------------------------------------------------------------------------

class A3DedupWithPositiveControl(_TmpMixin, unittest.TestCase):

    def test_positive_control_then_the_silent_second_put(self):
        store = BlobStore(self.blobdir())

        # (1) POSITIVE CONTROL — NOT OPTIONAL. Only a non-empty first list proves the
        # recorder is recording; without it the second list's emptiness is
        # indistinguishable from a drive that never happened (`:1461`, `:1446`).
        h1, first = drive_put(store, b"a3-payload")
        _say("A3 (1) FIRST PUT  :", " -> ".join(first) or "<empty>")
        self.assertTrue(first, "POSITIVE CONTROL FAILED: the recorder recorded nothing on "
                               "the first put, so the second put's empty list would prove "
                               "nothing at all")
        verdict, detail = barrier_verdict(first)
        self.assertEqual(verdict, "MET", "positive control must be A2's literal order: " + detail)

        # (2) the second put of identical bytes
        h2, second = drive_put(store, b"a3-payload")
        _say("A3 (2) SECOND PUT :", " -> ".join(second) or "<empty>")
        _say("A3 VERDICT        : same hash", h1 == h2, "| second-put calls", second)
        self.assertEqual(h1, h2)
        self.assertEqual(second, [], "dedup fired the barrier a second time: %s" % (second,))


# ---------------------------------------------------------------------------
# A4 — THE COMPOSITION IS ASSERTABLE
# ---------------------------------------------------------------------------

def guarantee_of(store):
    """The question a store answers about ITSELF. Not `isinstance`: the defect being
    cured is that a composition change moves consumers silently, and a class-name check
    moves with the change."""
    return getattr(store, "durability_guarantee", None)


def check_site(site, store):
    """Returns (verdict, detail). The detail NAMES THE SITE — R3 requires the failure to
    say which composition handed over an unguaranteed store."""
    want = getattr(blobs_mod, "CONTENT_DURABLE_BEFORE_RECORD", "<constant absent>")
    got = guarantee_of(store)
    if got == want and got != "<constant absent>":
        return "MET", "%s reports %r" % (site, got)
    return "UNMET", ("site %s handed over a store whose durability guarantee is %r, "
                     "expected %r" % (site, got, want))


def retake_composition_sites():
    """RE-TAKEN BY GREP AT THE BUILD AND NEVER CARRIED FROM THE PLAN (`:1359`).

    Scoped to `src/` exactly as the plan's own command is, so this test file's own
    occurrences cannot enter its own population — a pipeline that counts itself is the
    estate's oldest counting defect.
    """
    found = []
    for root, dirs, files in os.walk(os.path.join(REPO, "src")):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", "archive")]
        for fn in sorted(files):
            if not fn.endswith(".py"):
                continue
            path = os.path.join(root, fn)
            with open(path, encoding="utf-8") as fh:
                for n, line in enumerate(fh, 1):
                    if "BlobStore(" in line and "class " not in line:
                        found.append((os.path.relpath(path, REPO), n, line.strip()))
    return sorted(found)


class A4CompositionAssertable(_TmpMixin, unittest.TestCase):

    def test_the_three_sites_are_re_taken_not_carried(self):
        sites = retake_composition_sites()
        for f, n, text in sites:
            _say("A4 SITE (re-taken):", "%s:%d" % (f, n), "|", text)
        # THIS ASSERTION WATCHES A SITE, AND A SITE-WATCHER CANNOT TELL A DEFECT FROM A
        # CURE — both a silently dropped composition and a lawful consolidation change
        # the count. The message therefore reports the population and stops; what the
        # change MEANS is not reachable from a grep and is not claimed here.
        self.assertEqual(len(sites), 3,
                         "the composition population is %d, not 3, on this tree: %s"
                         % (len(sites), sites))
        self.assertEqual(sorted(f for f, _, _ in sites),
                         ["src/bridge/mount.py", "src/bridge/replay_snapshot.py",
                          "src/kernel/compose.py"])

    def test_kernel_compose_site_answers_the_durability_question(self):
        from kernel.compose import build_full_kernel
        rec = os.path.join(self.tmp, "k.jsonl")
        _s, _g, _v, blobs, _sv = build_full_kernel(rec, self.blobdir("k"))
        verdict, detail = check_site("src/kernel/compose.py", blobs)
        _say("A4 compose.py :", verdict, "|", detail)
        self.assertEqual(verdict, "MET", detail)

    def test_bridge_mount_site_answers_the_durability_question(self):
        from bridge.mount import build_brain
        rec = os.path.join(self.tmp, "m.jsonl")
        _s, _g, _v, blobs = build_brain(rec, self.blobdir("m"))
        verdict, detail = check_site("src/bridge/mount.py", blobs)
        _say("A4 mount.py   :", verdict, "|", detail)
        self.assertEqual(verdict, "MET", detail)

    def test_replay_snapshot_site_answers_the_durability_question(self):
        """The third site constructs its store inside a function and returns nothing, so
        the instance is CAPTURED at construction. That is a drive of the site — the line
        executes — and not a reading of it."""
        from bridge import replay_snapshot
        built = []
        real = blobs_mod.BlobStore

        class Capturing(real):
            def __init__(self, *a, **kw):
                super().__init__(*a, **kw)
                built.append(self)

        blobs_mod.BlobStore = Capturing
        try:
            replay_snapshot.snapshot(os.path.join(self.tmp, "absent.jsonl"),
                                     self.blobdir("r"), root="/")
        finally:
            blobs_mod.BlobStore = real
        self.assertEqual(len(built), 1, "the site did not construct exactly one store")
        verdict, detail = check_site("src/bridge/replay_snapshot.py", built[0])
        _say("A4 replay_snapshot.py:", verdict, "|", detail)
        self.assertEqual(verdict, "MET", detail)


# ---------------------------------------------------------------------------
# A5 — THE SILENT-INHERITANCE POPULATION IS NAMED AND RE-TAKEN, NOT CARRIED
# ---------------------------------------------------------------------------

class A5SilentInheritancePopulation(unittest.TestCase):

    def test_the_build_brain_population_is_taken_and_printed_here(self):
        """THE ROW DOES NOT ASSERT A FIGURE. It asserts the figure is TAKEN AND PRINTED
        at the build — the intake's EIGHT is exactly the number nobody re-took for three
        weeks, and a row asserting NINETEEN would rot the same way."""
        tests_dir = os.path.join(REPO, "tests")
        hits = []
        for root, dirs, files in os.walk(tests_dir):
            dirs[:] = [d for d in dirs if d not in ("__pycache__", "archive")]
            for fn in sorted(files):
                if not fn.endswith(".py"):
                    continue
                path = os.path.join(root, fn)
                with open(path, encoding="utf-8", errors="replace") as fh:
                    if "build_brain" in fh.read():
                        hits.append(os.path.relpath(path, REPO))
        hits = sorted(hits)
        _say("A5 CMD: grep -rln 'build_brain' tests/ --include=*.py | grep -v archive | wc -l")
        _say("A5 POPULATION (taken at this build):", len(hits))
        for h in hits:
            _say("A5   ", h)
        _say("A5 INTAKE SAID: 8   | AT AUTHORING: 19   | NOW:", len(hits))
        self.assertGreater(len(hits), 0, "the population is empty, which falsifies the "
                                         "premise that anything inherits silently")


# ---------------------------------------------------------------------------
# A6 — design/39 §2's ROW VOCABULARY, AS CLAIMS THAT RED ON SILENT ACCOMMODATION
# ---------------------------------------------------------------------------
#
# ENTITY  — identity is the recorded establishment. Permission rows land HERE.
# PROCESS — the entity's current incarnation in RAM. Incarnation rows land HERE.
# CUSTODY — files and folders the entity holds, as EVENTS. File-holding rows land HERE.
#
# design/39 §2 and §7. A later EP-30-C unit CITES these three names rather than
# re-deriving them; the claims below are what makes the citation mean something.

ENTITY = "ENTITY"
PROCESS = "PROCESS"
CUSTODY = "CUSTODY"
VOCABULARY = (ENTITY, PROCESS, CUSTODY)


class LawfulWorld:
    """Record the act, compute the view — applied to the word "program" itself."""

    def __init__(self):
        self.acts = []

    def do(self, *act):
        self.acts.append(tuple(act))
        return self

    # --- derivations, every one computed from the acts and nothing stored -----
    def entity_exists(self, e):
        return any(a[0] == "ESTABLISH" and a[1] == e for a in self.acts)

    def rights_of(self, e):
        return sorted({a[2] for a in self.acts if a[0] == "GRANT" and a[1] == e})

    def incarnations_of(self, e):
        live = []
        for a in self.acts:
            if a[0] == "INCARNATE" and a[1] == e:
                live.append(a[2])
            elif a[0] == "EXIT" and a[2] in live:
                live.remove(a[2])
        return live

    def entity_of_process(self, pid):
        for a in self.acts:
            if a[0] == "INCARNATE" and a[2] == pid:
                return a[1]
        return None

    def rights_of_process(self, pid):
        e = self.entity_of_process(pid)
        return self.rights_of(e) if e else []

    def custody_history(self, path):
        return [(a[0], a[1]) for a in self.acts if a[0] in ("TAKE", "RELEASE") and a[2] == path]

    def custodian_of(self, path):
        holder = None
        for kind, who in self.custody_history(path):
            holder = who if kind == "TAKE" else None
        return holder


class EntityCollapsedIntoProcess(LawfulWorld):
    """THE ACCOMMODATION design/39 §2 EXISTS TO FORBID: the permission row lands on the
    incarnation that was running when it was granted, so it dies with that pid."""

    def _incarnation_live_at(self, e, idx):
        live = []
        for a in self.acts[:idx]:
            if a[0] == "INCARNATE" and a[1] == e:
                live.append(a[2])
            elif a[0] == "EXIT" and a[2] in live:
                live.remove(a[2])
        return live[-1] if live else None

    def rights_of(self, e):
        live = self.incarnations_of(e)
        out = set()
        for idx, a in enumerate(self.acts):
            if a[0] == "GRANT" and a[1] == e:
                holder = self._incarnation_live_at(e, idx)
                if holder is not None and holder in live:
                    out.add(a[2])          # the right lives only while ITS pid does
        return sorted(out)


class ProcessCollapsedIntoEntity(LawfulWorld):
    """The mirror accommodation: identity IS the incarnation, so the entity ceases when
    its last process exits and there is nothing left to inherit from."""

    def entity_exists(self, e):
        return bool(self.incarnations_of(e))


class CustodyCollapsedIntoAttribute(LawfulWorld):
    """Custody stored as an attribute instead of derived from events: the current holder
    survives, the HISTORY does not, and "who held this before" becomes unanswerable."""

    def _stored(self, path):
        """The attribute, overwritten on every transfer. Reads the acts directly rather
        than through `custody_history` — routing it through the override would recurse,
        which is its own small lesson about deriving from a thing you have replaced."""
        holder = None
        for a in self.acts:
            if a[0] == "TAKE" and a[2] == path:
                holder = a[1]
            elif a[0] == "RELEASE" and a[2] == path:
                holder = None
        return holder

    def custody_history(self, path):
        holder = self._stored(path)
        return [("TAKE", holder)] if holder else []


def claim_entity(world):
    """ENTITY: a permission granted to the entity SURVIVES the incarnation that used it
    and is inherited by the next one. A pid has no record to derive from."""
    w = world().do("ESTABLISH", "pwc").do("INCARNATE", "pwc", 101)
    w.do("GRANT", "pwc", "read:/ledger")          # granted while pid 101 is the incarnation
    w.do("EXIT", "pwc", 101).do("INCARNATE", "pwc", 202)
    if "read:/ledger" not in w.rights_of("pwc"):
        return "UNMET", "the right did not survive the death of pid 101 — ENTITY collapsed into PROCESS"
    if "read:/ledger" not in w.rights_of_process(202):
        return "UNMET", "the new incarnation did not inherit the entity's right"
    return "MET", "right survives pid 101 and is inherited by pid 202"


def claim_process(world):
    """PROCESS: incarnations are distinct and countable, and the ENTITY OUTLIVES THEM —
    an incarnation row must never be usable as identity."""
    w = world().do("ESTABLISH", "pwc")
    w.do("INCARNATE", "pwc", 101).do("INCARNATE", "pwc", 202)
    if sorted(w.incarnations_of("pwc")) != [101, 202]:
        return "UNMET", "the two incarnations are not distinct: %s" % (w.incarnations_of("pwc"),)
    w.do("EXIT", "pwc", 101).do("EXIT", "pwc", 202)
    if not w.entity_exists("pwc"):
        return "UNMET", "the entity ceased when its last incarnation exited — PROCESS collapsed into ENTITY"
    return "MET", "two distinct incarnations, and the entity outlives both"


def claim_custody(world):
    """CUSTODY: holding is an EVENT, so the current holder is computed AND the prior
    holder is answerable. A stored attribute answers the first and loses the second."""
    w = world().do("ESTABLISH", "a").do("ESTABLISH", "b")
    w.do("TAKE", "a", "/x").do("RELEASE", "a", "/x").do("TAKE", "b", "/x")
    if w.custodian_of("/x") != "b":
        return "UNMET", "the current holder is not derived correctly: %r" % (w.custodian_of("/x"),)
    if len(w.custody_history("/x")) != 3:
        return "UNMET", ("the history is not answerable — %d events, expected 3. CUSTODY "
                         "collapsed into a stored attribute" % len(w.custody_history("/x")))
    return "MET", "current holder derived, and all three custody events answerable"


CLAIMS = ((ENTITY, claim_entity, EntityCollapsedIntoProcess),
          (PROCESS, claim_process, ProcessCollapsedIntoEntity),
          (CUSTODY, claim_custody, CustodyCollapsedIntoAttribute))


class A6RowVocabularyEstablished(unittest.TestCase):

    def test_the_three_terms_are_named_vocabulary(self):
        _say("A6 VOCABULARY:", VOCABULARY)
        self.assertEqual(VOCABULARY, ("ENTITY", "PROCESS", "CUSTODY"))
        self.assertEqual(len(CLAIMS), 3)

    def test_each_claim_is_green_on_the_lawful_world(self):
        for name, claim, _collapse in CLAIMS:
            verdict, detail = claim(LawfulWorld)
            _say("A6 %-8s CLEAN :" % name, verdict, "|", detail)
            self.assertEqual(verdict, "MET", "%s: %s" % (name, detail))

    def test_each_claim_reds_when_its_distinction_is_collapsed(self):
        """THE ACCOMMODATION THIS ROW EXISTS TO CATCH. A claim that stays green under its
        own collapse is not carrying the distinction it names."""
        for name, claim, collapse in CLAIMS:
            verdict, detail = claim(collapse)
            _say("A6 %-8s COLLAPSED:" % name, verdict, "|", detail)
            self.assertEqual(verdict, "UNMET",
                             "%s stayed green with its distinction collapsed: %s" % (name, detail))


# ---------------------------------------------------------------------------
# §4 RED WORLDS — the same row function, applied to broken worlds
# ---------------------------------------------------------------------------

def _hash_of(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


class _WorldStore(BlobStore):
    """Base for the red worlds. Each overrides `put` with a DIFFERENT barrier and is
    driven through the same recorder and judged by the same `barrier_verdict`."""


class R1NoParentFsync(_WorldStore):
    """R1 — the parent-directory fsync neutered. The bytes are durable; the NAME is not."""

    def put(self, data):
        h = _hash_of(data)
        p = self._path(h)
        if p.exists():
            return h
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_name(p.name + ".part")
        fd = seam_mod.os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
        with seam_mod.os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            seam_mod.os.fsync(f.fileno())
        seam_mod.os.replace(str(tmp), str(p))
        return h                                    # <- the parent fsync is GONE


class R2RenameBeforeFileFsync(_WorldStore):
    """R2 — THE ONE THAT MATTERS. Every call is present and every byte is durable; only
    the ORDER is wrong. A row green here is testing presence, not ordering."""

    def put(self, data):
        h = _hash_of(data)
        p = self._path(h)
        if p.exists():
            return h
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_name(p.name + ".part")
        fd = seam_mod.os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
        f = seam_mod.os.fdopen(fd, "wb")
        try:
            f.write(data)
            f.flush()
            seam_mod.os.replace(str(tmp), str(p))  # <- RENAME FIRST
            seam_mod.os.fsync(f.fileno())          # <- then the file fsync
        finally:
            f.close()
        dfd = seam_mod.os.open(str(p.parent), os.O_RDONLY)
        try:
            seam_mod.os.fsync(dfd)
        finally:
            os.close(dfd)
        return h


class R4FileAndParentInOrder(_WorldStore):
    """R4's near-miss control, the MUST half: a store that fsyncs both in the right order
    must SATISFY the row. A row that reds on any nearby change is measuring its fixture."""

    def put(self, data):
        return BlobStore.put(self, data)


class RedWorlds(_TmpMixin, unittest.TestCase):

    def _drive(self, cls, name):
        store = cls(self.blobdir(name))
        h, calls = drive_put(store, b"red-world-payload")
        verdict, detail = barrier_verdict(calls)
        _say("%s CALLS  :" % name, " -> ".join(calls) or "<empty>")
        _say("%s VERDICT:" % name, verdict, "|", detail)
        return store, h, calls, verdict, detail

    def test_R1_missing_parent_fsync_reds_and_names_the_missing_call(self):
        _s, _h, calls, verdict, detail = self._drive(R1NoParentFsync, "R1")
        self.assertEqual(verdict, "UNMET", "A ROW THAT CANNOT BE MADE TO RED BY REMOVING "
                                           "THE VERY CALL IT ASSERTS HAS ASSERTED NOTHING")
        self.assertIn("fsync(parent dir)", detail)
        self.assertNotIn("fsync(parent dir)", calls)

    def test_R2_wrong_order_reds_with_every_byte_durable(self):
        store, h, calls, verdict, detail = self._drive(R2RenameBeforeFileFsync, "R2")
        self.assertEqual(verdict, "UNMET", "the row passed a world whose ONLY defect is "
                                           "the order — it is testing presence, not ordering")
        self.assertIn("ORDER WRONG", detail)
        # the bytes really are all written and all durable in this world
        self.assertEqual(sorted(calls), sorted(EXPECTED_ORDER))
        self.assertEqual(store.get(h), b"red-world-payload")

    def test_R3_a_site_composed_without_a_guarantee_reds_and_names_the_site(self):
        class NoGuaranteeStore:
            pass
        verdict, detail = check_site("src/kernel/compose.py", NoGuaranteeStore())
        _say("R3 VERDICT:", verdict, "|", detail)
        self.assertEqual(verdict, "UNMET")
        self.assertIn("src/kernel/compose.py", detail)
        # and the same substitution is caught at each of the three sites
        for site in ("src/bridge/mount.py", "src/bridge/replay_snapshot.py"):
            v, d = check_site(site, NoGuaranteeStore())
            self.assertEqual(v, "UNMET")
            self.assertIn(site, d)

    def test_R4_near_miss_pair_discriminates(self):
        # the MUST-NOT half: file fsync present, parent absent
        _s, _h, _c, v_bad, _d = self._drive(R1NoParentFsync, "R4-must-not")
        # the MUST half: both, in the right order
        _s2, _h2, _c2, v_good, d_good = self._drive(R4FileAndParentInOrder, "R4-must")
        _say("R4 PAIR: must-not =", v_bad, "| must =", v_good)
        self.assertEqual(v_bad, "UNMET")
        self.assertEqual(v_good, "MET", d_good)

    def test_R5_entity_collapsed_into_process_reds_naming_the_collapse(self):
        verdict, detail = claim_entity(EntityCollapsedIntoProcess)
        _say("R5 VERDICT:", verdict, "|", detail)
        self.assertEqual(verdict, "UNMET")
        self.assertIn("ENTITY collapsed into PROCESS", detail)
        # a permission row landing on a process is the thing an entity can inherit and a
        # pid cannot — design/39 §2 and §7.
        self.assertEqual(claim_entity(LawfulWorld)[0], "MET")


if __name__ == "__main__":
    unittest.main(verbosity=2)
