# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-28C W4b — THE RENDERING BOUNDARY: where an identity becomes a number, and who owns it.

THE LAW THIS LOWERS IS charter §A52: *a boundary crossed by CONVENTION duplicates its defects
on both sides, and neither side can see the other's.* Its diagnostic is a COUNTABLE — count
the places a value is PARSED; one is a boundary, two is a convention wearing a boundary's
name. This file is that count, asserted structurally, in BOTH languages.

WHAT WAS MEASURED BEFORE THE CHANGE, so the rows below have a subject rather than a claim:

  * `custody._int()` returned **0** on `TypeError`/`ValueError`. A non-numeric identity
    became the single key 0 and a namespace of derived identities collapsed onto it,
    silently.
  * `govosfs.c`'s `rep_num()` returned its `dflt` when `kstrtoll` failed, and `dflt` was 0 at
    every identity call site. **Written by a different hand, in a different language, for a
    different reason, and neither side could see the other's.**
  * And the C side carried the diagnostic INSIDE ONE FILE. The carried figure was "one
    implementation, five call sites"; the measurement is **three independent parse-failure
    sites** — `rep_num`'s `return dflt`, `inode_from_reply`'s `kstrtoll(perm) -> permv = 0`,
    and `govos_readdir`'s `kstrtoul(...) -> ino = 0` — over **eight call expressions**, seven
    of them defaulting to zero. Plus two FOLLOW-ONS that turned the zero into an INVENTED
    value: `i_ino = ino ? ino : get_next_ino()`, and `dir_emit(..., ino ? ino : 1, ...)`,
    which reported an unreadable directory entry to userland AS THE MOUNT ROOT.

THE FIX IS NOT SYMMETRIC REPAIR — IT IS THE REMOVAL OF THE CONVENTION. After this pass the
identity is RENDERED in exactly one place, in one language (`custody.render_ino`), and the C
side only ever PARSES what the brain computed. The boundary is crossed by a shared
DERIVATION instead of by two independent interpretations, which is the only fix §A52 admits.

ONE CONVENTION SURVIVES AND IT IS NAMED RATHER THAN LEFT TO BE FOUND: the mount ROOT is
inode 1 on both sides, because `govos_fill_super` mints the root BEFORE any crossing exists
and therefore cannot be told. That is the item AMENDMENT 7 §7.2 raises; it is RULED here as
SUBSTRATE on `design/36` ADDENDUM K's precedent, and the ruling ships with its own detector
(`TestTheRootIsDeclaredSubstrate`) rather than as a sentence.

WHERE THE RENDERING SITS, and it is a DECLARED DEVIATION from the shape AMENDMENT 7 §7.1
directed — the derivation is in the build entry, and the row
`test_the_two_ports_cannot_render_differently_because_they_share_the_fold` is what the
placement buys.
"""

import os
import re
import shutil
import sys
import tempfile
import threading
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))

from bridge import custody                                        # noqa: E402
from bridge.kernel_port import KernelPort                         # noqa: E402
from bridge.mount import build_brain                              # noqa: E402

GOVOSFS_C = os.path.join(REPO, "planning", "vm", "govosfs", "govosfs.c")

PROV = {"asserted_by": "owner", "source": "test", "could_read": []}
OWNER = "owner"


def _wire(op, cls="DECISION", uid=1000, gid=1000, pid=42, **kw):
    f = {"id": "1", "op": op, "class": cls,
         "uid": str(uid), "gid": str(gid), "pid": str(pid)}
    f.update({k: str(v) for k, v in kw.items()})
    return f


class _Port(unittest.TestCase):
    """A brain composed exactly as the guest's daemon composes it."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="w4b-")
        self.store, self.gate, self.views, self.blobs = build_brain(
            os.path.join(self.dir, "rec.jsonl"), os.path.join(self.dir, "blobs"))
        self.port = KernelPort(self.store, self.gate, self.views, self.blobs)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def call(self, op, cls="DECISION", payload=b"", **kw):
        return self.port.handle(_wire(op, cls, **kw), payload)


# =================================================================================================
# A light STRUCTURAL reader for the C half.
#
# WHY A READER AND NOT A GREP, and the distinction is charter §A51's: a name-pattern filter
# presented as an enumeration returns members that are not members and misses members that are.
# What this reads is the MECHANISM CLASS — the kernel's own string-to-number primitives — and
# WHERE each occurrence SITS, which is a structural fact about the file rather than a guess from
# its vocabulary. The enumerated set is stated as data so a reader can see what it does not cover.
#
# THE HONEST CAP, IN THE READER'S OWN DOCSTRING because a cap in an entry rots. A COMPILED MODULE
# HAS NO RUNTIME SURFACE THE SUITE CAN WALK, so this side of the boundary is read from SOURCE and
# not from behaviour — the exact form W4a retired for Python, kept here because the alternative is
# no guard at all on the half of the boundary where the defect was invisible for a month. A
# conversion reached through a macro, through a helper this set does not name, or through
# hand-rolled digit arithmetic is OUTSIDE what this sees. **The residual that would close it is a
# guard living where the module is BUILT, in the guest, reading the compiled object rather than
# the text — RAISED by this item, never built inside it.**
# =================================================================================================

#: The kernel's string->number primitives. DATA, so the set is readable and extendable.
C_CONVERSIONS = ("kstrtoll", "kstrtoul", "kstrtol", "kstrtoull", "kstrtouint",
                 "kstrtoint", "kstrtou64", "kstrtos64", "kstrtobool",
                 "simple_strtol", "simple_strtoul", "sscanf")

#: The two functions ALLOWED to convert: the general numeric parse and the identity's own.
#: Every other occurrence is a SECOND interpretation of the same wire, which is the defect.
C_PARSE_FUNCTIONS = ("rep_num", "parse_ino")

_C_FUNC_HEAD = re.compile(r"^[A-Za-z_][A-Za-z0-9_ \t\*]*\b([A-Za-z_][A-Za-z0-9_]*)\s*\(")


def c_code_lines(path):
    """The file's EXECUTABLE lines, with block and line comments blanked out.

    LOAD-BEARING, AND FOR THE REASON `tests/test_ep28g_w5.py` reads Python through `ast`:
    this file DISCUSSES the shapes it refuses. Every deleted construct is quoted in a comment
    beside its replacement — `return dflt;`, `kstrtoul(...) -> ino = 0`,
    `ino ? ino : get_next_ino()` — because a repair that erases the record of what it
    repaired leaves the next reader with no way to tell a fix from a preference. A reader
    that counted those quotations would report the defect it just proved absent."""
    out = []
    in_block = False
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            kept, i = [], 0
            while i < len(line):
                if in_block:
                    end = line.find("*/", i)
                    if end < 0:
                        i = len(line)
                    else:
                        i = end + 2
                        in_block = False
                    continue
                start = line.find("/*", i)
                slash = line.find("//", i)
                if slash >= 0 and (start < 0 or slash < start):
                    kept.append(line[i:slash])
                    break
                if start < 0:
                    kept.append(line[i:])
                    break
                kept.append(line[i:start])
                i = start + 2
                in_block = True
            out.append((n, "".join(kept)))
    return out


def c_code_text(path):
    return "\n".join(code for _n, code in c_code_lines(path))


def c_conversion_sites(path):
    """Every conversion primitive in the file, mapped to the function whose body holds it.

    The enclosing function is found by tracking the most recent DEFINITION HEAD at column 0 —
    in this file's style a definition starts in column 0 and a declaration ends in `;`. It is
    a reading of the file's structure rather than of its words, and the red world below plants
    a real conversion in a real function to prove the reader can fail."""
    sites = []
    current = "<file scope>"
    for n, body in c_code_lines(path):
        if body and body[0] not in " \t\n#" and not body.rstrip().endswith(";"):
            m = _C_FUNC_HEAD.match(body)
            if m:
                current = m.group(1)
        for fn in C_CONVERSIONS:
            if re.search(r"\b%s\s*\(" % fn, body):
                sites.append((n, current, fn))
    return sites


def c_call_statements(path, callee):
    """Every line calling `callee`, with whether the call HEADS a bare expression statement —
    that is, whether its verdict is discarded. A parse that refuses is only a refusal if
    somebody reads the refusal."""
    out = []
    pat = re.compile(r"\b%s\s*\(" % callee)
    for n, body in c_code_lines(path):
        if not pat.search(body):
            continue
        stripped = body.strip()
        out.append((n, stripped, stripped.startswith(callee + "(")))
    return out


# =================================================================================================
# T-ONE-PARSE-SITE — §A52's own countable, in both languages
# =================================================================================================

class TestOneParseSitePerBoundary(_Port):
    """THE COUNTABLE: the identity is parsed in exactly ONE place on each side of the boundary,
    and RENDERED in exactly one place in the whole estate."""

    # ---- the C side: structural ----------------------------------------------------------
    def test_the_subject_is_not_empty_so_the_rows_below_cannot_pass_over_nothing(self):
        """§A38: a check whose pass condition is an absence must prove its subject non-empty."""
        sites = c_conversion_sites(GOVOSFS_C)
        self.assertGreaterEqual(len(sites), 2,
                                "the reader found almost no conversions — it is reading the "
                                "wrong file or the wrong shape, and the row below would pass "
                                "over an empty subject")
        self.assertEqual({s[1] for s in sites}, set(C_PARSE_FUNCTIONS))

    def test_every_conversion_primitive_in_the_module_sits_in_a_parse_function(self):
        stray = [s for s in c_conversion_sites(GOVOSFS_C) if s[1] not in C_PARSE_FUNCTIONS]
        self.assertEqual(stray, [],
                         "a string-to-number conversion outside %s — a SECOND interpretation "
                         "of the same wire, which is exactly §A52's shape" % (C_PARSE_FUNCTIONS,))

    def test_RED_WORLD_a_planted_conversion_outside_the_parse_functions_is_caught(self):
        """GENERATED AND ITS OUTPUT KEPT (§A42): a real copy of the module, one real
        conversion added in a real function, read by the real reader."""
        src = open(GOVOSFS_C, encoding="utf-8").read()
        needle = "static int govos_rmdir(struct inode *dir, struct dentry *dentry)\n{\n"
        self.assertIn(needle, src, "the plant site moved — the red world must be re-aimed")
        planted = src.replace(
            needle, needle + "\tunsigned long decoy;\n\n\tkstrtoul(\"1\", 10, &decoy);\n", 1)
        tmp = tempfile.mkdtemp(prefix="w4b-cred-")
        try:
            p = os.path.join(tmp, "govosfs.c")
            open(p, "w", encoding="utf-8").write(planted)
            stray = [s for s in c_conversion_sites(p) if s[1] not in C_PARSE_FUNCTIONS]
            self.assertEqual([(s[1], s[2]) for s in stray], [("govos_rmdir", "kstrtoul")],
                             "the reader did not see the planted conversion — the row above "
                             "is green about nothing")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_no_identity_parse_in_the_module_discards_its_verdict(self):
        calls = (c_call_statements(GOVOSFS_C, "rep_ino")
                 + c_call_statements(GOVOSFS_C, "parse_ino"))
        self.assertTrue(calls, "no identity parse call found — this row has no subject")
        self.assertEqual([(n, t) for n, t, d in calls if d], [],
                         "an identity parse whose answer is thrown away — a refusal nobody "
                         "reads is not a refusal")

    def test_the_module_holds_no_default_on_a_failed_parse_anywhere(self):
        """The two shapes that WERE there, gone, asserted on the source that no longer holds
        them. Both were real lines in this file and both are quoted in this pass's entry."""
        src = c_code_text(GOVOSFS_C)
        for gone in ("ino ? ino : get_next_ino()", "ino ? ino : 1",
                     "permv = 0;", "return dflt;"):
            self.assertNotIn(gone, src,
                             "%r is a parse failure answering with a value — the class this "
                             "pass deletes rather than repairs" % gone)

    # ---- the Python side: BEHAVIOURAL, per W4a's ruling ----------------------------------
    def test_every_wire_route_that_needs_an_identity_goes_through_the_one_parse(self):
        """W4a's discipline applied one item later: the property is observed on the EXECUTING
        path, never on the text. A refusing double installed at the ONE parse must change
        EVERY route's answer — a route that still answers 0 is a route parsing on its own."""
        self.assertEqual(self.call("FILE-MKDIR", path="/d")[0], 0)
        dino = self.port.state.lookup("/d").ino
        routes = [
            ("FILL-LOOKUP", dict(cls="FILL", parent=1, name="d")),
            ("FILL-READDIR", dict(cls="FILL", ino=dino)),
            ("FILE-PERM", dict(path="/d", inode=dino, perm="700")),
        ]
        for op, kw in routes:
            self.assertEqual(self.call(op, **kw)[0], 0, "%s must answer with the real parse" % op)

        real = custody.parse_ino
        custody.parse_ino = lambda _v: (_ for _ in ()).throw(
            custody.UnparseableRecordValue("the double refuses every identity"))
        try:
            for op, kw in routes:
                with self.assertRaises(custody.UnparseableRecordValue,
                                       msg="%s answered while the ONE parse refused — it "
                                           "reads the wire's identity somewhere else" % op):
                    self.port._fill(op, _wire(op, **kw)) if kw.get("cls") == "FILL" \
                        else self.port._params_for(op, _wire(op, **kw), b"")
        finally:
            custody.parse_ino = real

    def test_the_two_ports_cannot_render_differently_because_they_share_the_fold(self):
        """WHAT THE PLACEMENT BUYS, and the reason for this pass's declared deviation from
        the directed shape. `custody.Inode` renders the recorded identity ONCE, at the fold's
        ingestion, so `records_fs.getattr`'s `st_ino` and `kernel_port`'s wire `ino` read the
        SAME field of the SAME node. Two ports rendering one op differently is unstatable
        rather than merely unlikely — there is no second rendering to disagree with."""
        self.call("FILE-MKDIR", path="/d")
        node = self.port.state.lookup("/d")
        fresh = custody.fold(self.store.all()).lookup("/d")
        self.assertEqual(node.ino, fresh.ino)
        self.assertEqual(node.ino, custody.render_ino(node.identity))
        self.assertEqual(self.port._node_fields(node)["ino"], node.ino)


# =================================================================================================
# T-NO-SILENT-ZERO — the divergence law: the input that answered 0 now refuses
# =================================================================================================

class TestTheSilentZeroIsDeletedNotRepaired(_Port):
    """THE STANDING DIVERGENCE LAW, with the two outcomes forced apart in one world: the
    value that used to answer 0 and the value that answers honestly, side by side."""

    UNREADABLE = ("/some/path", "abc", "", None, [], {"a": 1}, "12x")

    def test_a_value_that_used_to_answer_zero_now_refuses_and_names_itself(self):
        for v in self.UNREADABLE:
            with self.assertRaises(custody.UnparseableRecordValue,
                                   msg="%r answered instead of refusing" % (v,)):
                custody._num(v, "a probe value")

    def test_a_value_that_can_be_read_is_read_unchanged(self):
        """THE OTHER ARM. A refusal that refused everything would be no better than a zero
        that answered everything, so the two outcomes are driven in the same row."""
        for v, expect in ((7, 7), ("7", 7), ("0", 0), (-3, -3), (" 42 ", 42)):
            self.assertEqual(custody._num(v, "a probe value"), expect)

    def test_the_identity_parse_refuses_zero_because_zero_was_the_collapse(self):
        self.assertEqual(custody.parse_ino("5"), 5)
        for v in ("0", 0, "-1"):
            with self.assertRaises(custody.UnparseableRecordValue):
                custody.parse_ino(v)

    def test_the_port_answers_EPROTO_where_it_used_to_act_on_a_zero(self):
        """THE SAME DIVERGENCE AT THE PORT'S OWN SURFACE, driven through the real handler.
        Before: `custody._int("abc")` was 0, the act proceeded, and a record was appended
        naming inode 0. Now the request never becomes a question and NOTHING is appended."""
        self.call("FILE-MKDIR", path="/d")
        mark = len(self.store.all())
        self.assertEqual(self.call("FILE-PERM", path="/d", inode="abc", perm="700")[0],
                         -71, "EPROTO")
        self.assertEqual(len(self.store.all()), mark,
                         "an unreadable wire appended a record — the act was performed on a "
                         "value nobody could read")

    def test_an_unknown_but_readable_number_is_ESTALE_and_not_EPROTO(self):
        """The two refusals are DIFFERENT INFORMATION and the port keeps them apart: one says
        the wire is broken, the other says the world moved."""
        self.assertEqual(self.call("FILE-PERM", path="/d", inode=987654321, perm="700")[0],
                         -116, "ESTALE")


# =================================================================================================
# T-PORT-DERIVES-NOTHING — AMENDMENT 5's stamp removal, contained in this scope
# =================================================================================================

class TestThePortStampsNothing(_Port):

    def test_the_stamping_site_is_gone_and_the_law_derives_the_identity(self):
        """[EP-28T, 2026-08-08 — `AppendNothing` PER ROW.]

        ASSERTED (2026-08-03, EP-28C W4b): each birth record carries the identity THE FOUNDING
        derived — under founding 1.14.0-1.17.0 that was `param_defaults {"inode": "$path"}`, so
        the recorded value was the path.
        SUPERSEDED (2026-08-08, EP-28S, founding 1.18.0): the three minting ops declare
        `mints_from: record_coordinate`, take no `inode` parameter and drop `inode` from
        `payload_from`. A birth record now carries NO identity at all; the fold derives it from
        the act's own position.
        REMAINS TRUE, separated out and STILL ASSERTED, and it is this row's whole subject —
        THE PORT STAMPS NOTHING. That property did not weaken, it got STRONGER: the old form
        proved the recorded number was not one this process chose; the new form proves there is
        no number in the record for a process to have chosen. Both halves are asserted below,
        because "no identity recorded" and "the identity is derived" are two facts and only the
        pair says the stamp is gone rather than merely different."""
        self.call("FILE-MKDIR", path="/p")
        self.call("FILE-CREATE", path="/q.txt")
        self.call("FILE-SYMLINK", path="/l", target="q.txt")
        births = [e for e in self.store.all()
                  if e["action"] in ("FILE-CREATE", "FILE-MKDIR", "FILE-SYMLINK")]
        self.assertEqual(len(births), 3, "non-vacuity: the three births are in the record")
        got = {(e["action"], (e["payload"] or {}).get("inode")) for e in births}
        self.assertEqual(got, {("FILE-MKDIR", None), ("FILE-CREATE", None),
                               ("FILE-SYMLINK", None)},
                         "a birth record must carry NO identity — there is nothing here for "
                         "this process to have chosen")
        # AND THE IDENTITY IS DERIVED RATHER THAN ABSENT: the fold names each birth by its own
        # record coordinate, so the three are distinct and each is its act's own position.
        derived = {(e["payload"] or {})["path"]: custody.formal_name(e["seq"]) for e in births}
        for path, name in derived.items():
            self.assertEqual(self.port.state.lookup(path).identity, name, path)
        self.assertEqual(len(set(derived.values())), 3, "two births share one identity")

    def test_the_record_speaks_ONE_identity_language_across_a_node_s_whole_life(self):
        """[EP-28T, 2026-08-08 — `AppendNothing` PER ROW.]

        ASSERTED (2026-08-03): every act touching a node — its create and its later opens and
        writes — records the SAME identity spelling, `/f.txt`, so a reader comparing
        `payload.inode` across a node's life sees one value.
        SUPERSEDED (2026-08-08, EP-28S): the BIRTH act records no identity at all, while later
        acts still carry whatever the caller handed in, which for the port is the RENDERING.
        So the record now holds two shapes: absent at birth, an integer afterwards.
        REMAINS TRUE, separated out and STILL ASSERTED: the node has ONE identity across its
        whole life, and every later act that names one names THAT one. What moved is WHERE the
        birth's identity is written — it is derived from the record rather than copied into it
        — so the row reads the birth from the fold and the later acts from the payload, and
        asserts the single value across both. THE PROPERTY IS UNCHANGED; ONLY ITS TWO SOURCES
        ARE NOW DIFFERENT, which is worth stating because two sources agreeing is stronger
        evidence than one source repeating itself."""
        self.call("FILE-CREATE", path="/f.txt")
        node = self.port.state.lookup("/f.txt")
        ino = node.ino
        self.call("FILE-OPEN", path="/f.txt", inode=ino, flags=0)
        self.call("FILE-WRITE", path="/f.txt", inode=ino, payload=b"x")
        birth = [e for e in self.store.all() if e["action"] == "FILE-CREATE"]
        self.assertEqual(len(birth), 1, "non-vacuity: the birth is in the record")
        self.assertIsNone((birth[0]["payload"] or {}).get("inode"),
                          "the birth act must name no identity")
        self.assertEqual(node.identity, custody.formal_name(birth[0]["seq"]),
                         "the fold names the birth by the birth's own coordinate")
        later = {(e["payload"] or {}).get("inode") for e in self.store.all()
                 if e["action"] in ("FILE-OPEN", "FILE-WRITE")}
        self.assertTrue(later, "non-vacuity: there are later acts naming an identity")
        self.assertEqual(later, {ino},
                         "a later act names an identity the node does not have")

    def test_CONCURRENT_creates_through_the_port_record_distinct_per_path_identities(self):
        """AMENDMENT 5's acceptance, driven. The old `_params_for` read `state.next_ino` at
        `:426` — BEFORE `gate.execute` — so two threads carried one number before either
        entered the gate, and no gate-level region could serialize a read outside it. With
        the read gone the identities are per-path BY CONSTRUCTION."""
        paths = ["/c%02d" % i for i in range(24)]
        errors = []

        def run(path):
            try:
                self.call("FILE-CREATE", path=path)
            except BaseException as exc:                       # noqa: BLE001
                errors.append(exc)

        threads = [threading.Thread(target=run, args=(p,)) for p in paths]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(errors, [])
        # [EP-28T, 2026-08-08 — `AppendNothing` PER ROW.]
        # ASSERTED (2026-08-03): 24 concurrent creates each RECORD their own path as their
        #   identity, so the recorded set equals the path set and no two share a rendering.
        # SUPERSEDED (2026-08-08, EP-28S): a birth records no identity, so the recorded set is
        #   24 Nones and `sorted()` cannot even order them — this row raised a TypeError rather
        #   than failing an assertion, which is what an obsolete READ looks like next to an
        #   obsolete CLAIM.
        # REMAINS TRUE, separated out and STILL ASSERTED, and it is AMENDMENT 5's actual
        #   acceptance: 24 concurrent creates produce 24 DISTINCT identities and 24 distinct
        #   renderings, with no thread carrying a number another thread also carried. The
        #   property is now stronger and its reason is better: distinctness used to rest on the
        #   PATHS being distinct, and now rests on the record positions being distinct, which
        #   holds even for 24 concurrent creates of ONE path. The identities are read from the
        #   fold, which is where they now live.
        births = [e for e in self.store.all() if e["action"] == "FILE-CREATE"]
        self.assertEqual(len(births), len(paths), "non-vacuity: every create is in the record")
        self.assertEqual({(e["payload"] or {}).get("inode") for e in births}, {None},
                         "a birth record must carry no identity")
        identities = [custody.formal_name(e["seq"]) for e in births]
        self.assertEqual(len(set(identities)), len(paths), "two creates shared one identity")
        self.assertEqual(sorted((e["payload"] or {})["path"] for e in births), sorted(paths))
        rendered = {custody.render_ino(i) for i in identities}
        self.assertEqual(len(rendered), len(paths), "two identities shared one rendering")
        served = {self.port.state.lookup(p).ino for p in paths}
        self.assertEqual(served, rendered,
                         "the served numbers are not the ones the record derives")

    def test_RED_WORLD_the_port_stamped_and_gate_derived_values_are_driven_apart(self):
        """AMENDMENT 5's divergence world: one act, two candidate identities, forced to
        DIFFER, and the gate's is the one that lands. The stamp is re-created in a double so
        the comparison is between two behaviours rather than between a behaviour and a
        memory."""
        real = self.port._params_for
        stamped_params = []

        def stamping(op, f, payload):
            out = real(op, f, payload)
            if op in ("FILE-CREATE", "FILE-MKDIR", "FILE-SYMLINK"):
                out["inode"] = 4242                            # what the retired stamp did
                # EP-28T: the double RECORDS that it fired, so the can-fail clause below is a
                # fact about the double rather than an inference from the record it no longer
                # reaches. ONE entry — the port calls this once per act, and the double is
                # installed for exactly one act. (First take of this line said two, from a
                # guess rather than a drive; the clause below went red and named the count,
                # which is the whole reason a can-fail clause states an integer.)
                stamped_params.append(out["inode"])
            return out

        self.port._params_for = stamping
        try:
            self.call("FILE-MKDIR", path="/stamped")
        finally:
            self.port._params_for = real
        self.call("FILE-MKDIR", path="/derived")
        # [EP-28T, 2026-08-08 — `AppendNothing` PER ROW, and this is the sharpest member.]
        # ASSERTED (2026-08-03): with the retired stamp re-created in a double, the stamped
        #   act records 4242 and the shipped act records the gate's derivation `/derived` —
        #   two candidate identities forced to DIFFER, with the gate's the one that lands.
        # SUPERSEDED (2026-08-08, EP-28S): the minting ops dropped `inode` from `payload_from`,
        #   so a value the double puts into the params is DROPPED on the way to the record. The
        #   stamped act records None. The row reds on its own can-fail clause — "the double
        #   must really stamp" — which is the correct behaviour for a control whose sabotage
        #   has become impossible.
        # REMAINS TRUE, separated out and STILL ASSERTED, and STRICTLY STRONGER: the divergence
        #   is still driven and the two candidates still differ, but the finding has moved up a
        #   level. It used to be "the gate's derivation wins the race against a stamp"; it is
        #   now "A STAMP CANNOT REACH THE RECORD AT ALL." The double is kept rather than
        #   deleted, because a control proving the sabotage is now INERT is the evidence that
        #   the door is shut — deleting it would leave the claim resting on a reading of the
        #   founding instead of on a driven act.
        # AND THE CAN-FAIL CLAUSE IS KEPT, INVERTED: the double is proven to still run and to
        #   still put 4242 into the params, so "the stamp did not land" is a fact about the
        #   payload declaration and not about a double that quietly stopped firing.
        self.assertEqual(stamped_params, [4242],
                         "the double did not actually stamp — this world proves nothing")
        by_path = {(e["payload"] or {})["path"]: (e["payload"] or {}).get("inode")
                   for e in self.store.all() if e["action"] == "FILE-MKDIR"}
        self.assertIsNone(by_path["/stamped"],
                          "a caller's stamp reached the record — the payload declaration is "
                          "no longer the door it is relied on to be")
        self.assertIsNone(by_path["/derived"], "a birth record must carry no identity")
        st = custody.fold(self.store.all())
        self.assertNotEqual(st.names["/stamped"], 4242,
                            "the stamped value became the served identity")
        self.assertNotEqual(st.names["/stamped"], st.names["/derived"],
                            "the two acts must still be two distinct nodes")


# =================================================================================================
# T-ALLOCATOR-POISONED-NOT-STALE — `custody.py:320`'s guard made to RED rather than skip
# =================================================================================================

class TestTheAllocatorRefusesRatherThanGoingStale(_Port):

    def test_a_derived_identity_makes_the_mark_unusable_rather_than_stale(self):
        st = custody.CustodyState()
        self.assertEqual(custody.mint_ino(st), 2, "an untouched namespace still allocates")
        st.apply({"action": "FILE-MKDIR", "actor": OWNER,
                  "payload": {"path": "/d", "inode": "/d", "perm": "755"}})
        self.assertIsNone(st.next_ino)
        with self.assertRaises(custody.AllocatorNotTracking):
            custody.mint_ino(st)

    def test_THE_OTHER_ARM_an_allocator_minted_world_still_advances_exactly_as_before(self):
        """The divergence's green side. Without it, a mark that refused everything would pass
        the row above and break every stamping caller in the estate."""
        st = custody.CustodyState()
        for n in (2, 3, 4):
            st.apply({"action": "FILE-MKDIR", "actor": OWNER,
                      "payload": {"path": "/d%d" % n, "inode": n, "perm": "755"}})
        self.assertEqual(st.next_ino, 5)
        self.assertEqual(custody.mint_ino(st), 5)
        self.assertEqual(st.next_ino, 6)

    def test_THE_SHAPE_THAT_WAS_THERE_the_old_guard_would_have_SKIPPED_and_said_nothing(self):
        """THE EXHIBITION, so the repair is comparable to what it replaced rather than only
        described. The retired expression is evaluated here against the same world: it is
        False, it does nothing, the mark stays at its old value, and the namespace it claims
        to track has moved past it — with nothing red anywhere."""
        st = custody.CustodyState()
        derived, mark_before = "/d", st.next_ino
        skipped = isinstance(derived, int) and derived >= st.next_ino   # the retired guard
        self.assertFalse(skipped, "the retired guard's own expression, on the new law")
        self.assertEqual(st.next_ino, mark_before,
                         "and it changed nothing: the mark is stale, not refused, and the "
                         "next stamping caller would hand out a number already in use")


# =================================================================================================
# T-RENDER-IS-A-FUNCTION — the rendering's own properties, including its stated cap
# =================================================================================================

class TestTheRenderingIsAFunction(unittest.TestCase):

    def test_it_is_deterministic_across_processes_and_not_python_s_own_hash(self):
        """THE NEAREST WRONG REFERENCE, refused by measurement. `hash()` is randomized per
        process, so a rendering built on it would give one file two inode numbers across a
        brain restart. This asserts a FIXED value, which only a process-stable digest can
        produce — the row would red under any per-process seed."""
        self.assertEqual(custody.render_ino("/a"), 7816720163859614224)
        self.assertEqual(custody.render_ino("/some/deep/path.txt"), 7015693968716057640)

    def test_the_two_number_spaces_are_disjoint_by_construction(self):
        for path in ("/a", "/b", "/x/y/z", "/" + "q" * 200):
            n = custody.render_ino(path)
            self.assertGreaterEqual(n, custody.RENDER_FLOOR)
            self.assertLess(n, 1 << 63, "must fit `long long` on the wire and `unsigned "
                                        "long` in the module")
        for legacy in (1, 2, 3, 4096):
            self.assertEqual(custody.render_ino(legacy), legacy)
            self.assertLess(legacy, custody.RENDER_FLOOR)

    def test_the_root_renders_to_one_under_both_of_its_spellings(self):
        self.assertEqual(custody.render_ino(custody.ROOT_INO), custody.ROOT_INO)
        self.assertEqual(custody.render_ino("/"), custody.ROOT_INO)

    def test_an_identity_the_estate_has_no_derivation_for_refuses(self):
        for v in (None, True, 3.5, b"/a", ("/a",)):
            with self.assertRaises(custody.UnrenderableIdentity):
                custody.render_ino(v)

    def test_the_stated_cap_is_measured_rather_than_asserted(self):
        """§A46: no adjective a measurement cannot support. The claim is 'collisions are
        possible in principle and were not observed', and this is the measurement behind it."""
        seen = {}
        for i in range(20000):
            p = "/d%d/f%d.txt" % (i % 97, i)
            n = custody.render_ino(p)
            self.assertNotIn(n, seen, "collision between %r and %r" % (seen.get(n), p))
            seen[n] = p
        self.assertEqual(len(seen), 20000)

    def test_RED_WORLD_a_collision_REFUSES_at_the_fold_rather_than_overwriting(self):
        """The cap turned into a detectable condition. A rendering that collides is driven
        through a double, and the fold refuses instead of filing one node under another's
        number — which is the silent collapse this whole pass exists to delete, arriving
        through the one door that could still produce it."""
        st = custody.CustodyState()
        real = custody.render_ino
        custody.render_ino = lambda ident: real(ident) if isinstance(ident, int) else 9_000_000_007
        try:
            st.apply({"action": "FILE-MKDIR", "actor": OWNER,
                      "payload": {"path": "/a", "inode": "/a", "perm": "755"}})
            with self.assertRaises(custody.UnrenderableIdentity):
                st.apply({"action": "FILE-MKDIR", "actor": OWNER,
                          "payload": {"path": "/b", "inode": "/b", "perm": "755"}})
        finally:
            custody.render_ino = real
        self.assertEqual([n.identity for n in st.inodes.values() if n.ino != custody.ROOT_INO],
                         ["/a"], "the second node must not have replaced the first")

    def test_re_creating_a_path_after_unlinking_it_is_NOT_a_collision(self):
        """The row that keeps the collision guard from being a false alarm: same identity,
        same number, and the estate's ordinary create-unlink-create cycle."""
        st = custody.CustodyState()
        for _ in range(3):
            st.apply({"action": "FILE-CREATE", "actor": OWNER,
                      "payload": {"path": "/f", "inode": "/f"}})
            st.apply({"action": "FILE-UNLINK", "actor": OWNER, "payload": {"path": "/f"}})
        self.assertEqual(len(st.inodes), 2)                     # the root and /f


# =================================================================================================
# T-ROOT-IS-DECLARED-SUBSTRATE — AMENDMENT 7 §7.2's intake, RULED and DETECTED
# =================================================================================================

class TestTheRootIsDeclaredSubstrate(_Port):
    """`governed-state = f(LAW, DECISIONS, INPUTS)` does not hold for the mount root: it is
    in the state and in no decision, and `MOUNT` is not in `CUSTODY_ACTIONS` at all.

    THE DISPOSITION TAKEN IS THE SUBSTRATE EXCLUSION, ruled by derivation at `custody.ROOT_INO`
    and RAISED for the owner's word. What makes it a ruling rather than an excuse is that it
    is COUNTED: exactly one identity in a folded state may lack a covering record, and a
    second one reds. The estate's own detector — kill everything derived, replay from the
    record alone — is what these rows run."""

    def _covering(self):
        """[EP-28T, 2026-08-08 — `AppendNothing`, and the treatment lands in the HELPER because
        that is where the obsolete read is.]

        ASSERTED (2026-08-03): the set of identities a record covers is the set of `inode`
        values the birth acts carry.
        SUPERSEDED (2026-08-08, EP-28S): birth acts carry no `inode`, so this returned `{None}`
        and `render_ino(None)` refused — the row raised rather than failing, which is again an
        obsolete READ rather than an obsolete claim.
        REMAINS TRUE and STILL ASSERTED, unchanged in substance: an identity is COVERED when a
        birth record founds it. What moved is how the covering identity is obtained from the
        record — derived from the act's own coordinate instead of read out of its payload. The
        two-case form is kept rather than assuming the new law, so a world holding pre-1.18.0
        records (which DO name identities) is covered by exactly the same helper."""
        out = set()
        for e in self.store.all():
            if e["action"] not in ("FILE-CREATE", "FILE-MKDIR", "FILE-SYMLINK"):
                continue
            named = (e["payload"] or {}).get("inode")
            out.add(named if named is not None else custody.formal_name(e["seq"]))
        return out

    def test_exactly_one_identity_in_a_replayed_state_has_no_covering_record(self):
        for p in ("/a", "/b", "/c"):
            self.call("FILE-MKDIR", path=p)
        replayed = custody.fold(self.store.all())
        covered = {custody.render_ino(i) for i in self._covering()}
        uncovered = set(replayed.inodes) - covered
        self.assertEqual(uncovered, {custody.ROOT_INO},
                         "the substrate exclusion is EXACTLY the root — anything else in the "
                         "state and in no decision is a finding, not an exclusion")

    def test_the_detector_can_fail_when_a_second_uncovered_identity_appears(self):
        """The row above is worthless without this one: a state carrying a node no record
        describes must show up as a SECOND member, so the exclusion cannot silently widen."""
        replayed = custody.fold(self.store.all())
        smuggled = custody.Inode(4242, custody.KIND_DIR, 0o755)
        replayed.inodes[smuggled.ino] = smuggled
        uncovered = set(replayed.inodes) - {custody.render_ino(i) for i in self._covering()}
        self.assertEqual(uncovered, {custody.ROOT_INO, 4242})

    def test_the_C_HALF_CANNOT_BE_TOLD_which_is_why_the_exclusion_is_structural(self):
        """The reason the ruling is not merely convenient. `govos_fill_super` mints the root
        before any crossing exists, so there is no moment at which the brain could state it —
        the number has to be known to both halves independently, which is what makes it
        SUBSTRATE rather than a decision somebody forgot to record."""
        src = c_code_text(GOVOSFS_C)
        self.assertIn("root = govos_make_inode(sb, 1, S_IFDIR | 0755,", src)
        head = src.split("static int govos_fill_super")[1].split("d_make_root")[0]
        self.assertNotIn("govos_call", head)
        self.assertNotIn("govos_fill", head)
        self.assertEqual(custody.ROOT_INO, 1, "and the two halves must agree on the number")


if __name__ == "__main__":
    unittest.main()
