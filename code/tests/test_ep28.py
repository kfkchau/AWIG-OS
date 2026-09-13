# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-28 — the in-kernel files seam, tested where the suite can reach it.

WHAT THIS FILE CAN AND CANNOT PROVE, said first because the boundary is the point.

The seam has two halves and they are testable in different places. The KERNEL half is
proven by running it in the guest (`planning/vm/govosfs/m3-acceptance.sh`, evidence in
`planning/vm/M3-EVIDENCE.md`) — it cannot be reached from this suite and pretending
otherwise would be worse than the gap. The USER-SPACE half is ordinary Python and is
tested here, which is exactly why K5 puts the brain in user space: the record machine
stays where the suite can reach it, and what crosses the line is the minimum custody
requires.

So these tests bind the half that holds the law. Every one of them is a probe that was
run by hand against the live seam first, landed here so the evidence outlives the
session.
"""

import errno
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from bridge import custody                                   # noqa: E402
from bridge.kernel_port import (                             # noqa: E402
    DECISION_OPS, KernelPort, WINDOW, build_reply, parse_request,
)
from bridge.mount import build_brain                         # noqa: E402


def _req(op, cls="DECISION", uid=1000, gid=1000, pid=42, **kw):
    f = {"id": "1", "op": op, "class": cls,
         "uid": str(uid), "gid": str(gid), "pid": str(pid)}
    f.update({k: str(v) for k, v in kw.items()})
    return f


class KernelSeamCase(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep28-")
        self.rec = os.path.join(self.dir, "rec.jsonl")
        self.blobdir = os.path.join(self.dir, "blobs")
        self.store, self.gate, self.views, self.blobs = build_brain(self.rec, self.blobdir)
        self.port = KernelPort(self.store, self.gate, self.views, self.blobs)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def call(self, op, cls="DECISION", payload=b"", **kw):
        return self.port.handle(_req(op, cls, **kw), payload)

    def records(self, action=None):
        return [e for e in self.store.all()
                if action is None or e.get("action") == action]


class TestTheWire(KernelSeamCase):
    """The channel's shape. A protocol defect is a custody defect one layer down."""

    def test_header_and_payload_split_on_the_first_newline(self):
        blob = b"id=7\top=FILE-WRITE\tclass=DECISION\tuid=0\n" + b"line one\nline two\n"
        f, p = parse_request(blob)
        self.assertEqual(f["id"], "7")
        self.assertEqual(f["op"], "FILE-WRITE")
        # THE PAYLOAD KEEPS ITS OWN NEWLINES. Splitting on every newline would corrupt
        # exactly the thing a governed write promises to preserve exactly.
        self.assertEqual(p, b"line one\nline two\n")

    def test_payload_bytes_survive_being_arbitrary(self):
        raw = bytes(range(256)) * 4
        blob = b"id=1\top=FILE-WRITE\tclass=DECISION\n" + raw
        _f, p = parse_request(blob)
        self.assertEqual(p, raw)

    def test_tabs_and_newlines_in_a_field_are_escaped_and_recovered(self):
        out = build_reply("3", 0, {"target": "a\tb\nc"})
        f, _p = parse_request(out)
        self.assertEqual(f["target"], "a\tb\nc")

    def test_a_reply_carries_its_payload_after_the_header(self):
        out = build_reply("9", 0, {"hash": "sha256:x"}, b"\x00\x01bytes")
        f, p = parse_request(out)
        self.assertEqual((f["id"], f["status"], f["hash"]), ("9", "0", "sha256:x"))
        self.assertEqual(p, b"\x00\x01bytes")


class TestFillsCannotDecide(KernelSeamCase):
    """THE SECOND WRONG REFERENCE'S GUARD, on the user-space side of the line.

    EP-28 names it: a structure below the line that can answer a governance question
    without any record being read. The seam's defence is that the two request classes
    are different code paths and only one of them can reach the gate. These tests hold
    that separation mechanically, so it cannot decay into a convention."""

    def test_no_fill_appends_anything(self):
        self.call("FILE-MKDIR", path="/d", perm="755")
        before = len(self.store.all())
        self.call("FILL-LOOKUP", "FILL", parent=1, name="d")
        self.call("FILL-READDIR", "FILL", ino=1)
        self.call("FILL-CONTENT", "FILL", hash="sha256:absent")
        self.assertEqual(len(self.store.all()), before)

    def test_a_fill_never_reaches_the_gate(self):
        """Poison the gate. Every FILL must still answer, because none of them go
        anywhere near it — and a DECISION must then fail, which proves the poison
        was real and the first half of this test was not vacuous."""
        self.call("FILE-MKDIR", path="/d", perm="755")

        touched = []

        def poisoned(*a, **k):
            touched.append(a[0] if a else "?")
            raise RuntimeError("the gate was reached")

        real_execute, real_refuse = self.gate.execute, self.gate.refuse
        self.gate.execute = poisoned
        self.gate.refuse = poisoned
        try:
            status, fields, _p = self.call("FILL-LOOKUP", "FILL", parent=1, name="d")
            self.assertEqual(status, 0)
            self.assertEqual(fields["type"], "dir")
            status, _f, _p = self.call("FILL-READDIR", "FILL", ino=1)
            self.assertEqual(status, 0)
            self.assertEqual(touched, [], "no FILL may reach the gate")
            # ...and the poison is PROVED REAL by a DECISION hitting it, so the three
            # assertions above are not passing because the gate was never reachable.
            status, _f, _p = self.call("FILE-MKDIR", path="/other", perm="755")
            self.assertEqual(status, -errno.EIO)
            self.assertEqual(touched, ["FILE-MKDIR"])
        finally:
            self.gate.execute, self.gate.refuse = real_execute, real_refuse

    def test_a_fill_answers_data_or_an_errno_and_never_a_permission(self):
        """REPOINTED, NOT WEAKENED — EP-28R W4, mentor-ruled 2026-08-07.

        THE PROPERTY IS THE ROW'S OWN NAME and it has not moved: an absence is answered with
        an errno and with DATA, never with a permission. What moved is the proxy. `fields ==
        {}` stood for "the answer carries nothing that could be a verdict" by carrying
        nothing at all, and that proxy died when EP-28R's ruled obligation put `at_seq` on
        every fold-derived answer INCLUDING both absences — a served state names the record
        position it is a state OF, so staleness is visible in the answer rather than
        inferred, and an absence is a claim about a state exactly as a presence is.

        WHY `at_seq` IS ON THE DATA SIDE OF THIS ROW'S OWN LINE, derived rather than
        tolerated: it is a RECORD COORDINATE. It names a position in the append-only record,
        it is computed from the fold's own progress, and no rule was consulted to produce it.
        A permission would be an answer to "may this actor", and this fill still reaches no
        gate — the row above (`test_a_fill_never_reaches_the_gate`) drives that with the gate
        poisoned, and this row does not restate it.

        STILL AN EXACT SET, so it stays a tripwire rather than becoming an allowlist: a
        SECOND field appearing here reds this row and gets the same derivation `at_seq` just
        had. The coordinate is checked to BE a record coordinate — an integer inside the
        record's own extent — because a field admitted by name only is a field nobody
        checked. What that coordinate MEANS, and its red worlds, are `tests/test_ep28r.py`'s
        `TestTheCOORDINATE`, and are not duplicated here."""
        status, fields, payload = self.call("FILL-LOOKUP", "FILL", parent=1, name="nope")
        self.assertEqual(status, -errno.ENOENT)
        self.assertEqual(set(fields), {"at_seq"},
                         "a fill's absence answer carries a field this separation guard has "
                         "never derived — it is not enough that it is not a permission; "
                         "state what it is and why a fill may answer with it")
        # NON-VACUITY: the record is not empty, so "inside the record's extent" is a real
        # constraint here and not a statement about zero.
        extent = len(self.store.all())
        self.assertGreater(extent, 0)
        self.assertIsInstance(fields["at_seq"], int)
        self.assertFalse(isinstance(fields["at_seq"], bool))
        self.assertTrue(0 <= fields["at_seq"] <= extent,
                        "the one field a fill may answer with is a RECORD COORDINATE, and "
                        "this one names no position the record holds: %r against %d records"
                        % (fields["at_seq"], extent))
        self.assertEqual(payload, b"")


class TestRecordBeforeEffect(KernelSeamCase):
    """K1 on the user-space side: the reply that releases the caller is written only
    after the covering record is durably appended."""

    def test_a_decision_is_appended_before_its_answer_is_formed(self):
        seen = {}
        real = self.gate.execute

        def watched(op, actor, params):
            rec = real(op, actor, params)
            # At the moment execute returns, the record is already on disk: the store
            # appends, flushes and fsyncs inside it. Read the FILE back, not the object.
            with open(self.rec, encoding="utf-8") as f:
                seen["durable"] = any('"FILE-MKDIR"' in ln for ln in f)
            return rec

        self.gate.execute = watched
        try:
            status, _f, _p = self.call("FILE-MKDIR", path="/d", perm="755")
        finally:
            self.gate.execute = real
        self.assertEqual(status, 0)
        self.assertTrue(seen["durable"],
                        "the record must be durable on disk before the reply is formed")

    def test_a_refused_act_leaves_no_effect(self):
        """A refusal changes the record (the refusal is recorded, P4) and changes no
        custody state — the direction that must never invert."""
        real = self.gate.execute

        def refusing(op, actor, params):
            from kernel.errors import OpError
            raise OpError("ROOT-NEG-1", "no chain")

        self.gate.execute = refusing
        try:
            status, _f, _p = self.call("FILE-MKDIR", path="/refused", perm="755")
        finally:
            self.gate.execute = real
        self.assertEqual(status, -errno.EACCES)
        self.assertIsNone(self.port.state.lookup("/refused"))


class TestOwnershipIsDerived(KernelSeamCase):
    """THE DEFECT T-CUSTODY-IS-DERIVED FOUND, and the derivation that closed it.

    Until EP-28 the custody fold read an inode's owner from the create record's PAYLOAD,
    which carries none — the creating uid is in the record's PROVENANCE. Every created
    file therefore folded back as owned by root. No leg of the instrument could see it:
    EP-25's mount answered `stat` with `node.uid or os.getuid()`, a server-wide fallback
    that happened to equal the creator; the recording leg saw a complete record; and the
    replay leg never compared ownership. It surfaced the moment the subsystem went below
    the syscall line, where the kernel reports real per-inode ownership and there is no
    server uid to fall back to."""

    def test_a_created_file_folds_back_owned_by_its_creator(self):
        self.call("FILE-CREATE", path="/f.txt", perm="644", uid=4321, gid=8765)
        replayed = custody.fold(self.store.all())
        node = replayed.lookup("/f.txt")
        self.assertIsNotNone(node)
        self.assertEqual((node.uid, node.gid), (4321, 8765),
                         "ownership must be derivable from the record alone")

    def test_a_directory_folds_back_owned_by_its_creator(self):
        self.call("FILE-MKDIR", path="/d", perm="755", uid=1234, gid=1234)
        node = custody.fold(self.store.all()).lookup("/d")
        self.assertEqual((node.uid, node.gid), (1234, 1234))

    def test_a_chown_is_a_recorded_transfer_and_the_fold_applies_it(self):
        """RE-POINTED 2026-07-29 (documented flip). This row read "an explicit payload
        owner still wins over provenance", which described a two-source fold: a payload
        owner consulted first, provenance behind it. design/10 §11.4b removed the first
        source, so the old wording now names a mechanism that no longer exists. What the
        row actually binds is untouched and is the thing worth binding: a `chown` is a
        recorded ownership-TRANSFER decision, its payload uid is that decision's own
        content, and the fold applies it at the point in the record where it happened —
        which is not a default standing behind a create."""
        # DOCUMENTED FLIP, EP-28C W4b (2026-08-03): the literal `inode=2` was the number the
        # PORT's own stamp produced, and the stamp is gone — the founding derives the
        # identity and the port renders it, so the number a later call carries is the one the
        # create's reply returned. The row's subject is untouched; what moved is where the
        # number comes from, which is the whole of W4b.
        _st, created, _p = self.call("FILE-CREATE", path="/f.txt", perm="644",
                                     uid=1000, gid=1000)
        node = custody.fold(self.store.all()).lookup("/f.txt")
        self.assertEqual((node.uid, node.gid), (1000, 1000), "the creator owns it")
        self.call("FILE-CHOWN", path="/f.txt", inode=created["ino"], uid=7, gid=9, pid=1)
        node = custody.fold(self.store.all()).lookup("/f.txt")
        self.assertEqual((node.uid, node.gid), (7, 9), "the transfer is applied where recorded")

    def test_the_fold_is_the_same_answer_incremental_or_from_scratch(self):
        """One derivation, two record sources — the EP-24B rule. A divergence here
        could only mean a record was missed, never that two implementations disagreed."""
        self.call("FILE-MKDIR", path="/d", perm="700", uid=1000, gid=1000)
        self.call("FILE-CREATE", path="/d/f", perm="640", uid=1000, gid=1000)
        self.call("FILE-WRITE", payload=b"bytes", path="/d/f", inode=3)
        self.assertEqual(self.port.state.snapshot(),
                         custody.fold(self.store.all()).snapshot())


class TestTheBrainHoldsNothingItDidNotOpen(unittest.TestCase):
    """A1 (EP-28 ADDENDUM 7) — the finding, and the correction the measurement forced.

    R-1 recorded that a refused `-EBUSY` attach leaks a module reference, so `rmmod` fails
    afterwards. Driven in the guest on 6.8.0-134-generic, the refused path leaves the
    refcount exactly where it was and the module unloads cleanly; that row is now in the
    battery (`T-REFUSAL-CONSERVES`) and it passes. **The measurement R-1 reported was real
    and its attribution was wrong**, which is §11.1d's shape one layer over: a symptom is
    not evidence of a mechanism until the mechanism is shown to have happened.

    WHAT ACTUALLY HELD THE MODULE. The acceptance battery holds a descriptor open on the
    mount (`exec 9<`) so it can prove a warm read answers with the brain detached, and then
    starts a new brain while it is open. The brain INHERITS fd 9; the shell's later
    `exec 9<&-` closes only the shell's copy; the brain holds a file on the governed mount
    for the rest of its life. Observed on the guest: `pid 1111 (python3) fd 9 ->
    /tmp/govos-m3/mnt/w/a.txt`, `umount: target is busy`, `rmmod: module is in use` — and
    all three clear the instant the brain is killed.

    WHY THE FIX IS THE DAEMON'S. The mount cannot be taken down while any process holds a
    file on it, and it cannot be served without the brain — so a descriptor the brain holds
    is one nobody can make it release. That makes T-LOCAL-FALLBACK's property depend on how
    the brain happened to be started, which is not a property at all."""

    def _child(self, fd, extra=""):
        src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
        script = (
            "import os, sys\n"
            "sys.path.insert(0, %r)\n"
            "fd = %d\n"
            "seen = os.path.exists('/proc/self/fd/%%d' %% fd)\n"
            "from bridge.kernel_port import _close_inherited_descriptors\n"
            "%s"
            "still = os.path.exists('/proc/self/fd/%%d' %% fd)\n"
            "sys.stdout.write('%%s|%%s|%%s\\n' %% (seen, still, targets))\n"
        ) % (src, fd, extra)
        out = subprocess.run([sys.executable, "-c", script], capture_output=True,
                             text=True, close_fds=False)
        self.assertEqual(out.returncode, 0, out.stderr)
        seen, still, targets = out.stdout.strip().split("|", 2)
        return seen == "True", still == "True", targets

    def test_a_descriptor_the_brain_never_opened_is_closed_and_named(self):
        d = tempfile.mkdtemp(prefix="ep28-a1-")
        try:
            path = os.path.join(d, "held-on-the-mount.txt")
            with open(path, "w") as f:
                f.write("a file the brain was handed and never asked for\n")
            fd = os.open(path, os.O_RDONLY)
            os.set_inheritable(fd, True)
            try:
                inherited, still, targets = self._child(
                    fd, "targets = [t for _f, t in _close_inherited_descriptors()]\n")
            finally:
                os.close(fd)
            # THE CONTROL FIRST: without it, `still is False` could mean the descriptor
            # was never inherited and the closing code never ran on anything.
            self.assertTrue(inherited, "the hazard must be real before the fix is evidence")
            self.assertFalse(still, "the brain must not keep a descriptor it never opened")
            self.assertIn("held-on-the-mount.txt", targets,
                          "and it must SAY what it closed — a silent close trades one "
                          "invisible defect for another")
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_the_daemons_own_log_descriptors_survive(self):
        """0, 1 and 2 are the daemon's log. Closing those would make the brain silent,
        which is the failure EP-28 R-4 already paid for once."""
        d = tempfile.mkdtemp(prefix="ep28-a1b-")
        try:
            fd = os.open(os.path.join(d), os.O_RDONLY)
            os.set_inheritable(fd, True)
            try:
                _seen, _still, targets = self._child(
                    fd,
                    "closed = _close_inherited_descriptors()\n"
                    "targets = sorted(f for f, _t in closed)\n"
                    "assert os.path.exists('/proc/self/fd/1'), 'stdout was closed'\n"
                    "assert os.path.exists('/proc/self/fd/2'), 'stderr was closed'\n")
            finally:
                os.close(fd)
            # A VALUE COMPARISON, NOT A SUBSTRING TEST [EP-28H item 2, 2026-08-02].
            # `targets` is a rendered LIST and the three lines that stood here asserted
            # `"1" not in targets` against its TEXT, so the row passed only while every
            # inherited descriptor was a single digit: at `'[12]'` the digit "1" is
            # found inside "12" and the row reported a closed stdin that was never
            # closed. The subject is which DESCRIPTORS were closed, so it is asked of
            # the descriptors — parsed back to the numbers the child sent.
            closed_fds = [int(t) for t in targets.strip("[] \n").split(",") if t.strip()]
            self.assertNotIn(0, closed_fds)
            self.assertNotIn(1, closed_fds)
            self.assertNotIn(2, closed_fds)
        finally:
            shutil.rmtree(d, ignore_errors=True)


class _SpyPayload(dict):
    """A payload that reports every key the fold asks it for.

    THE ADDENDUM C GUARD SHAPE, pointed at ownership: call structure, never source text.
    A grep for `uid` in custody.py would pass a fold that reached for the attribute under
    another spelling or through another dict; observing what the fold actually READS
    catches every spelling, including one nobody has written yet."""

    def __init__(self, inner, seen):
        super().__init__(inner)
        self._seen = seen

    def get(self, key, default=None):
        self._seen.append(key)
        return super().get(key, default)

    def __getitem__(self, key):
        self._seen.append(key)
        return super().__getitem__(key)


def _watched(records):
    """The same records, with every payload watching what the fold asks it for.
    Returns (records, keys_read_by_action)."""
    seen = {}
    out = []
    for e in records:
        e = dict(e)
        action = e.get("action")
        seen.setdefault(action, [])
        e["payload"] = _SpyPayload(e.get("payload") or {}, seen[action])
        out.append(e)
    return out, seen


class TestOwnershipIsDerivedFromTheCoveringDecision(KernelSeamCase):
    """A4 (EP-28 ADDENDUM 8 §8.2) — the repaired ownership fold, both halves.

    THE RULE (design/10 §11.4b, OWNER-RULED 2026-07-29): the owner of a thing is the
    actor at the head of the recorded delegation chain on the covering decision. There is
    no ownership FIELD, so a default has nowhere to live, and **a fold reading an
    ownership attribute is the defect whether or not its value is currently right**.

    WHY BOTH HALVES AND NOT JUST THE FIRST. The value half (A4a) proves this fold answers
    correctly today. It would also pass a second fallback that merely defaulted more
    cleverly — which is the whole history of R-2, where `node.uid or os.getuid()` agreed
    with the truth on every test that ever ran. The structural half (A4b) is what makes
    the class untestable-away: it fails on ANY read of an ownership attribute, whatever
    that read would have returned."""

    # ---- A4a: the value half — two values that CANNOT coincide ----------------------
    def test_a4a_the_recorded_owner_and_the_running_process_cannot_coincide(self):
        """The divergence test in its strict form (BUILD-PROMPT-STANDARD, 2026-07-29): the
        two possible sources are FORCED to differ, so the assertion is about which one is
        being read rather than about a value they happen to share."""
        mine = os.getuid()
        other = 4321 if mine != 4321 else 4322
        self.assertNotEqual(other, mine,
                            "the fixture is only evidence while the two identities differ")
        self.call("FILE-CREATE", path="/f.txt", perm="644", uid=other, gid=8765)
        node = custody.fold(self.store.all()).lookup("/f.txt")
        self.assertEqual((node.uid, node.gid), (other, 8765),
                         "the fold must answer the RECORDED owner, not the running identity")
        self.assertNotEqual(node.uid, mine)

    def test_a4a_root_is_a_real_owner_and_zero_is_a_real_uid(self):
        """THE CASE THE RETIRED FALLBACK GOT WRONG, and the only case where `x or default`
        ever diverges. A file the record says root created folds back owned by root. Under
        `node.uid or os.getuid()` this answered whoever was running the mount, because
        `0 or 1000` is `1000` — root was read as "unset" by an operator that cannot tell
        an absent value from a zero one."""
        self.assertNotEqual(os.getuid(), 0,
                            "this row is only evidence when the suite is not running as root")
        self.call("FILE-CREATE", path="/r.txt", perm="644", uid=0, gid=0)
        node = custody.fold(self.store.all()).lookup("/r.txt")
        self.assertEqual((node.uid, node.gid), (0, 0))

    def test_a4a_the_port_reports_the_folds_answer_and_not_its_own_identity(self):
        """The same divergence one layer up, where R-2 actually hid. The FUSE port's
        `getattr` is the surface a program reads `st_uid` from; it must hand back what the
        fold derived, unmodified."""
        from bridge.mount import build_mount

        d = tempfile.mkdtemp(prefix="ep28-a4a-")
        try:
            fs, store, _g, _v, _b = build_mount(os.path.join(d, "rec.jsonl"),
                                                os.path.join(d, "blobs"))
            # Driven directly, libfuse's context is unset and reads 0/0/0, so this mount
            # records root as the creator — the exact shape that made the fallback silent.
            ctx_uid = fs._ctx()[0]
            self.assertNotEqual(ctx_uid, os.getuid(),
                                "the fixture is only evidence while the two identities differ")
            fh = fs.create("/owned.txt", 0o644)
            fs.release("/owned.txt", fh)
            self.assertEqual(fs.getattr("/owned.txt")["st_uid"], ctx_uid)
            self.assertEqual(custody.fold(store.all()).lookup("/owned.txt").uid, ctx_uid)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_a4a_the_root_is_the_one_inode_no_record_describes(self):
        """THE DIVERGENCE TEST FOR THE DEFAULT THAT SURVIVED, and it exists because
        removing the other one broke the mount.

        `node.uid or os.getuid()` was doing two unrelated jobs. As a fallback for every
        inode it was the masking construct §11.4b removes. But the ROOT has no FILE-CREATE
        behind it — the mount exists before anything is created in it — so the fold has
        nothing to say about who owns it and answers 0, and reporting that made the mount
        root a 0755 directory owned by uid 0 to a caller who is not uid 0. The kernel then
        denied every write into it before the server was asked, and eight of EP-25's
        unmodified-program rows went red.

        So the remaining default is SCOPED to the one question the record does not answer,
        and this row forces the two answers apart: a recorded inode owned by root reports
        0, while the unrecorded root reports the serving identity. They cannot coincide,
        so the row is red the moment the scope widens back out."""
        from bridge.mount import build_mount

        d = tempfile.mkdtemp(prefix="ep28-a4root-")
        try:
            fs, store, _g, _v, _b = build_mount(os.path.join(d, "rec.jsonl"),
                                                os.path.join(d, "blobs"))
            serving = os.getuid()
            self.assertNotEqual(serving, 0,
                                "this row is only evidence when the suite is not root")
            fh = fs.create("/recorded.txt", 0o644)
            fs.release("/recorded.txt", fh)
            recorded_owner = fs._ctx()[0]
            self.assertEqual(recorded_owner, 0,
                             "driven directly, the port's context is unset and records 0 — "
                             "which is what makes this a divergence rather than a coincidence")

            self.assertEqual(fs.getattr("/recorded.txt")["st_uid"], recorded_owner,
                             "an inode the record describes reports what the record says")
            self.assertEqual(fs.getattr("/")["st_uid"], serving,
                             "the root, which no record describes, reports the serving identity")
            self.assertNotEqual(fs.getattr("/")["st_uid"],
                                fs.getattr("/recorded.txt")["st_uid"],
                                "the two answers must be told apart, or the scope has widened")
            # AND THE CONSEQUENCE THAT MADE IT MATTER: the root must be writable by the
            # caller the kernel will present, or nothing can be created in the mount at all.
            self.assertEqual(custody.fold(store.all()).lookup("/").ino, custody.ROOT_INO)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    # ---- A4b: the structural half — the fold reads NO ownership attribute -----------
    def test_a4b_the_fold_takes_no_payload_at_all_so_a_default_has_nowhere_to_live(self):
        """The signature IS the guarantee. A payload argument is the place a default can
        be written; with no such argument, reintroducing one cannot be a quiet edit."""
        import inspect

        self.assertEqual(list(inspect.signature(custody._creator).parameters), ["e"])

    def test_a4b_no_ownership_attribute_is_read_from_a_create(self):
        """Observed, not grepped: fold a real record with every payload watching, and
        assert that no create-family record was ever asked for an owner."""
        self.call("FILE-MKDIR", path="/d", perm="755", uid=1000, gid=1000)
        self.call("FILE-CREATE", path="/d/f", perm="644", uid=1000, gid=1000)
        self.call("FILE-SYMLINK", path="/d/l", target="f", uid=1000, gid=1000)

        watched, seen = _watched(self.store.all())
        st = custody.fold(watched)
        self.assertIsNotNone(st.lookup("/d/f"), "the fold must have actually run")
        for action in ("FILE-CREATE", "FILE-MKDIR", "FILE-SYMLINK"):
            self.assertTrue(seen.get(action), "%s must have been folded" % action)
            for attr in ("uid", "gid", "owner"):
                self.assertNotIn(attr, seen[action],
                                 "the fold asked a %s for `%s` — that is the defect "
                                 "whether or not its value was right (design/10 §11.4b)"
                                 % (action, attr))

    def test_a4b_the_watcher_can_fail_because_a_chown_does_read_one(self):
        """THE CONTROL, and the row above is worthless without it. A `FILE-CHOWN` payload
        legitimately carries uid and gid — it is an ownership-TRANSFER decision, and its
        content is the decision. The same watcher sees that read. So a silent watcher over
        a create means the create was not asked, not that the watcher cannot see."""
        # DOCUMENTED FLIP, EP-28C W4b (2026-08-03) — the same one-line reason as the three
        # rows above: `inode=2` was the port's own stamp, and the stamp is gone.
        _st, created, _p = self.call("FILE-CREATE", path="/f.txt", perm="644",
                                     uid=1000, gid=1000)
        self.call("FILE-CHOWN", path="/f.txt", inode=created["ino"], uid=7, gid=9, pid=1)

        watched, seen = _watched(self.store.all())
        custody.fold(watched)
        self.assertIn("uid", seen.get("FILE-CHOWN", []),
                      "the watcher must be able to observe an ownership-attribute read")
        self.assertNotIn("uid", seen.get("FILE-CREATE", []))

    def test_a4b_the_answer_is_a_function_of_the_covering_decisions_provenance(self):
        """The positive half of "computes from the covering decision": hold the payload
        constant, change only the covering decision's recorded provenance, and the owner
        changes. Nothing else in the record moved."""
        self.call("FILE-CREATE", path="/a.txt", perm="644", uid=1111, gid=1111)
        self.call("FILE-CREATE", path="/b.txt", perm="644", uid=2222, gid=2222)
        st = custody.fold(self.store.all())
        a, b = st.lookup("/a.txt"), st.lookup("/b.txt")

        recs = [e for e in self.store.all() if e.get("action") == "FILE-CREATE"]
        pa = {k: v for k, v in (recs[0].get("payload") or {}).items() if k != "path"}
        pb = {k: v for k, v in (recs[1].get("payload") or {}).items() if k != "path"}
        pa.pop("inode", None), pb.pop("inode", None)
        self.assertEqual(pa, pb, "the two payloads must be identical but for identity")
        self.assertEqual((a.uid, b.uid), (1111, 2222))


class TestTheDeclaredChecksRefuseAndRECORD(KernelSeamCase):
    """THE CLASS IS RENAMED AND NOT ONLY FLIPPED — EP-28C W4e, 2026-08-07, on the mentor's
    ruling. It was `TestPosixPreconditionsAppendNothing`, and its docstring asserted
    design/10 §11.1a classes 2 and 3 as this estate then read them: "an ABSENCE and a
    NOT-GOVERNED outcome append nothing, and a record appearing for one of them is the
    failure." A class whose NAME says `AppendNothing` while its rows assert appending
    carries a repealed law in its name, which is worse than a stale header — a header lags,
    a name is read as the claim.

    WHAT OVERTURNED IT: owner ruling 1, made law by EP-28K and completed by EP-28N and its
    AMENDMENT 1. These outcomes are not absences; each is a DECLARED check on its op
    definition, the gate decides it inside the decide region, and a declared refusal
    RECORDS. W4e retired the port's read that used to answer first, so the declared check is
    what every row below now meets.

    §11.1a IS NOT REPEALED WHOLESALE, and the boundary is worth stating here because this
    file is where a reader meets it: its conditional membership still holds for an outcome
    NOTHING declares — `tests/test_ep28k.py::TestAbsenceStaysAbsenceWhereNothingIsDeclared`
    drives `FILE-PERM` against the live gate and it still appends nothing.

    THE ONE FACT THE OLD READING WAS RIGHT ABOUT SURVIVES UNCHANGED: the emptiness question
    cannot be answered below the line. `simple_empty` reads the DENTRY CACHE, and under
    lookup-on-demand that cache holds only the names somebody has already asked for, so a
    directory whose children were never looked up reads as empty down there while the record
    says otherwise. It is now the `contains:empty` check's, above the line as it always was
    and inside the region as it was not.

    THE DELTA IS ASSERTED BY NAME AND NOT BY COUNT. Each row appends exactly three records:
    the `op-refused` the declared check makes, plus the mirror's two blind streams
    (`src/kernel/protection.py:106`, `:121`), which fire on any audited action by standing
    law. `before + 3` would pass just as well on three of anything."""

    #: The three records a declared refusal leaves, IN ORDER. Named rather than counted, so a
    #: row cannot go green on the right arithmetic and the wrong records.
    REFUSAL_DELTA = ["op-refused", "dual-audit-record", "dual-audit-b-record"]

    def assert_declared_refusal(self, before, status, want_errno):
        self.assertEqual(status, -want_errno)
        added = [e["action"] for e in self.store.all()[before:]]
        self.assertEqual(sorted(added), sorted(self.REFUSAL_DELTA),
                         "a declared refusal appends its own record plus the mirror's two "
                         "streams, and nothing else")
        refusal = [e for e in self.store.all()[before:] if e["action"] == "op-refused"][-1]
        self.assertEqual(refusal["rule_cited"], "FS-LAW-NAMESPACE",
                         "the refusal cites the declared law, which is what makes it the "
                         "gate's answer rather than a port's invention")

    def test_rmdir_of_a_non_empty_directory_refuses_AND_records(self):
        self.call("FILE-MKDIR", path="/d", perm="755")
        self.call("FILE-CREATE", path="/d/f", perm="644")
        before = len(self.store.all())
        status, _f, _p = self.call("FILE-RMDIR", path="/d")
        self.assert_declared_refusal(before, status, errno.ENOTEMPTY)

    def test_create_over_an_existing_name_refuses_AND_records(self):
        self.call("FILE-CREATE", path="/f", perm="644")
        before = len(self.store.all())
        status, _f, _p = self.call("FILE-CREATE", path="/f", perm="644")
        self.assert_declared_refusal(before, status, errno.EEXIST)

    def test_unlink_of_a_directory_refuses_AND_records(self):
        self.call("FILE-MKDIR", path="/d", perm="755")
        before = len(self.store.all())
        status, _f, _p = self.call("FILE-UNLINK", path="/d")
        self.assert_declared_refusal(before, status, errno.EISDIR)

    def test_a_create_under_a_missing_parent_refuses_AND_records(self):
        before = len(self.store.all())
        status, _f, _p = self.call("FILE-CREATE", path="/nowhere/f", perm="644")
        self.assert_declared_refusal(before, status, errno.ENOENT)


class TestClosureAndProvenance(KernelSeamCase):
    def test_an_unregistered_op_is_refused_and_the_refusal_is_recorded(self):
        """P3, the bank with no counter: an unregistered operation does not exist. And
        P4: the refusal is recorded, citing its rule, rather than vanishing."""
        status, _f, _p = self.call("FILE-FORGE", path="/x")
        self.assertEqual(status, -errno.ENOSYS)
        refusals = self.records("op-refused")
        self.assertTrue(refusals)
        # The rule is cited on the ENVELOPE, which is where the estate puts a citation;
        # the payload names the op that did not exist.
        self.assertEqual(refusals[-1]["rule_cited"], "P3-CLOSURE")
        self.assertEqual(refusals[-1]["payload"]["op"], "FILE-FORGE")

    def test_the_port_records_its_own_window_and_the_uid_as_evidence(self):
        """K6: the kernel-asserted uid is EVIDENCE recorded as evidence, and the window
        says WHICH port asserted it — a different window from the FUSE port's, because
        two windows onto one machine must be tellable apart in the record."""
        self.call("FILE-MKDIR", path="/d", perm="755", uid=1000, gid=1000, pid=77)
        rec = self.records("FILE-MKDIR")[-1]
        prov = rec["provenance"]
        self.assertEqual(prov["window"], WINDOW)
        self.assertEqual(prov["window"], "kernel-port@1")
        self.assertEqual((prov["uid"], prov["gid"], prov["pid"]), (1000, 1000, 77))
        self.assertEqual(prov["source"], "kernel-port")

    def test_the_actor_is_derived_from_recorded_mapping_acts_not_a_table(self):
        """A uid<->account synchronised table would be a stored identity status. The
        mapping is recorded acts and the answer is a fold, recomputed every act."""
        self.assertEqual(self.port._actor(1000), "uid:1000")
        # MAP-UID declares a provenance parameter and the envelope router REFUSES a call
        # that omits it (EP-27B) — a minted provenance would read as though the port had
        # stated something it never observed. So the mapping act carries its own.
        self.gate.execute("MAP-UID", "owner", {
            "uid": 1000, "account": "acct:alice",
            "provenance": {"asserted_by": "owner", "source": "test",
                           "could_read": [], "window": WINDOW},
        })
        self.assertEqual(self.port._actor(1000), "acct:alice")


class TestTheSameLawAsEP25(KernelSeamCase):
    """The transport changed; none of the law did. These bind that claim."""

    def test_the_in_kernel_port_uses_the_SAME_op_definitions_as_the_fuse_mount(self):
        """No founding bump is taken by this EP, and it is a derivation rather than a
        convenience: an op whose definition differed below the line would assert that a
        kernel-resident write is a different governed act from a user-space one."""
        defined = set(self.views.op_definitions())
        for op in DECISION_OPS:
            self.assertIn(op, defined, "%s must already exist in the founding" % op)

    def test_content_goes_full_fidelity_to_a_content_addressed_blob(self):
        raw = bytes(range(256)) * 8
        # DOCUMENTED FLIP, EP-28C W4b (2026-08-03) — see the chown row above for the reason.
        _st, created, _p = self.call("FILE-CREATE", path="/f", perm="644")
        self.call("FILE-WRITE", payload=raw, path="/f", inode=created["ino"])
        node = custody.fold(self.store.all()).lookup("/f")
        self.assertTrue(node.content_hash)
        self.assertEqual(self.blobs.get(node.content_hash), raw)

    def test_killing_every_derived_structure_and_replaying_gives_the_same_answer(self):
        """T-CUSTODY-IS-DERIVED, in the half this suite can reach: the port's own state
        is a fold, and a fresh port built on the same record serves identically."""
        # DOCUMENTED FLIP, EP-28C W4b (2026-08-03), AND THIS ONE WAS GREEN FOR THE WRONG
        # REASON THE MOMENT THE STAMP WENT: with `inode=3` naming nothing, the write refused
        # ESTALE and the row still passed, because a snapshot compared against a snapshot
        # agrees perfectly about a world where nothing was written. Named rather than quietly
        # repaired — a replay row whose subject silently emptied is the exact shape this
        # estate keeps finding, and it was found here by the change rather than by a reader.
        self.call("FILE-MKDIR", path="/d", perm="755", uid=1000, gid=1000)
        _st, created, _p = self.call("FILE-CREATE", path="/d/f", perm="644",
                                     uid=1000, gid=1000)
        self.call("FILE-WRITE", payload=b"content", path="/d/f", inode=created["ino"])
        self.call("FILE-SYMLINK", path="/d/l", target="f", uid=1000, gid=1000)
        before = self.port.state.snapshot()

        store2, gate2, views2, blobs2 = build_brain(self.rec, self.blobdir)
        port2 = KernelPort(store2, gate2, views2, blobs2)
        self.assertEqual(port2.state.snapshot(), before)

    def test_a_fill_content_answers_by_the_hash_the_record_carries(self):
        """The whole difference from the journaling filesystem: nothing asks the host
        what a path contains; the blob store is asked for a hash the record named."""
        # DOCUMENTED FLIP, EP-28C W4b (2026-08-03) — see the chown row above for the reason.
        _st, created, _p = self.call("FILE-CREATE", path="/f", perm="644")
        self.call("FILE-WRITE", payload=b"exact bytes", path="/f", inode=created["ino"])
        node = self.port.state.lookup("/f")
        status, _f, payload = self.call("FILL-CONTENT", "FILL", hash=node.content_hash)
        self.assertEqual(status, 0)
        self.assertEqual(payload, b"exact bytes")


class TestTheBrainComposesOneMachine(unittest.TestCase):
    def test_build_brain_imports_no_fuse(self):
        """The in-kernel daemon runs in a guest where fusepy is not installed, so the
        transport being genuinely retired is proven by the module that no longer imports
        it. `bridge.mount.build_brain` and `bridge.kernel_port` must both be importable
        with `fuse` made unavailable."""
        import importlib

        saved = sys.modules.pop("fuse", None)
        blocker = object()
        sys.modules["fuse"] = None      # a None entry makes `import fuse` raise
        try:
            for name in ("bridge.mount", "bridge.kernel_port"):
                mod = sys.modules.get(name)
                if mod is not None:
                    importlib.reload(mod)
            d = tempfile.mkdtemp(prefix="ep28-nofuse-")
            try:
                from bridge.mount import build_brain as bb
                store, gate, views, blobs = bb(os.path.join(d, "r.jsonl"),
                                               os.path.join(d, "b"))
                self.assertTrue(store.all())
            finally:
                shutil.rmtree(d, ignore_errors=True)
        finally:
            del sys.modules["fuse"]
            if saved is not None:
                sys.modules["fuse"] = saved
            for name in ("bridge.mount", "bridge.kernel_port"):
                if sys.modules.get(name) is not None:
                    importlib.reload(sys.modules[name])
            del blocker


if __name__ == "__main__":
    unittest.main()
