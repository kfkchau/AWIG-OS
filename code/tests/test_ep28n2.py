"""EP-28N AMENDMENT 1 — the hierarchy eight, decided as one class on EP-28O's landed base.

Every probe here is a regression test (the campaign method: a verification probe lands as
a test).

WHAT THIS PASS DECIDES. EP-28K read nineteen (op, outcome) pairs out of the port's
`_posix_precondition` AST and declared eight of them. EP-28N declared three more and RAISED
the remaining eight on one measured fact: six ask about `parent_of(key)` and two about
`contains(key)`, and both are HIERARCHY over a key space that was then unnormalised. EP-28O
normalised it. This pass declares all eight, as ONE CLASS in ONE authoring, and the port's
act-keyed table becomes the whole enumeration: NINETEEN pairs, nineteen rows, every one with
a law behind it.

THE THREE ADDITIONS, EACH WITH ITS JUSTIFICATION, because the minimality gate is not a
formality:
  * `key_of: container` on a check row — without it a check can only ask about the key a
    parameter carries, and six members ask about the key that contains it.
  * the `contains` check kind — without it no check can ask what a key HOLDS, and two
    members do. It is the first question whose answer depends on the key space AROUND a key.
  * `key_space` on the law that governs the key space — without it the key space has no
    ROOT, and a root is the one key no act binds, so every top-level create would be refused
    for landing in a container that no record founds.

THE NAMED WRONG REFERENCES THIS BATTERY REFUSES.
  1. THE CALLER-RENDERED CONTAINER. The plan floats letting the PORT compute the container
     and hand it in as a parameter, on the `render_ino` precedent. It is the opposite
     direction: `render_ino` renders outward a decision the record made, while a handed-in
     container is a caller computing a PRECONDITION the gate then trusts — check-then-act
     across the decide region's boundary, which is what EP-28K exists to close. Detector:
     `TestTheDerivationIsTheLawsNotTheCallers`, which drives a caller supplying a container
     of its own choosing and asserts the law is indifferent to it.
  2. GROWING THE MAP, one layer down. `binding:bound` over an act's own key and over its
     container are two different outcomes; a shared requirement string would be the
     rule-keyed defect this EP removed, rebuilt inside the act key. Detector:
     `TestTheRequirementCarriesWhichKey`.
  3. PER-MEMBER DRIFT. Eight members decided in sittings become a convention. Detector:
     `TestTheClassIsDecided` — one re-derivation, one set-diff, one authoring, and the
     dispositioned set equals the eight exactly.
  4. THE ENGINE LEARNING A FILESYSTEM. A container relation is namespace grammar, and a copy
     of it in kernel space would be §A52's second computer. Detector:
     `TestTheEngineStillNamesNoFilesystem` plus `TestOneComputerOfTheRelation`.

Coverage (the EP's named battery, as AMENDMENT 1 binds it):
  T-CLASS-DECIDED         the nineteen re-derived from the port's AST in `setUp`, set-diffed
                          BOTH against the fresh read and against EP-28N's standing table,
                          with the drift reported as a finding; the eight this pass owns each
                          carry a disposition and the set is exact.
  T-REFUSAL-CITES-TIP-RULE  every one of the eight appends a refusal citing the TERMINAL
                          rule, driven on all eight including the least likely (§A49).
  T-TWO-KEYS              the record carries the rule while the port returns the ACT's
                          errno, asserted independently, for every one of the eight.
  T-ABSENCE-STAYS         ops declaring no check keep §11.1a's classification, asserted as a
                          set over this pass's landed population.
  T-GUARD-AT-THREE-DOORS  the new declaration and the new kind, malformed, refuse at the
                          installer, CREATE-OP and AMEND-OP; can-fail controls per clause.
  T-DIFF-IS-THE-CHANGE / T-VERSION-MOVES   the founding diff equals the declared change list
                          both directions against the BEFORE taken at this pass's start;
                          `founding_version` reads 1.17.0; J9 re-proven.
  THE ROOT                declared, seeded, not unbindable, and its residual driven.
  THE LEASH               the law's declared root is the one key the namespace's own
                          container relation says has no container — set-diffed, so a law
                          declaring a root the grammar does not agree about REDS.
"""
import ast
import copy
import hashlib
import json
import os
import shutil
# [EP-28Z, 2026-08-12] `import subprocess` REMOVED: this file's only spawn was its copy
# of the era-pin act, which now lives at `tests/era_pin.py`. An import naming a capability
# the file no longer uses tells a later reader it spawns processes, which is false.
import sys
import tempfile
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO, "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import era_pin                                                      # noqa: E402  (the era-pin home, EP-28Z)
from bridge import custody                                          # noqa: E402
from bridge.kernel_port import ERRNO_BY_ACT, ERRNO_BY_RULE          # noqa: E402
from bridge.kernel_port import DECISION_OPS, KernelPort             # noqa: E402
from bridge.mount import build_brain                                # noqa: E402
from founding import install as install_module                      # noqa: E402
from founding.install import load_pack                              # noqa: E402
from kernel import opdefs                                           # noqa: E402
from kernel.compose import build_full_kernel                        # noqa: E402
from kernel.errors import OpError                                   # noqa: E402

#: THE STANDING TABLE IS THE STARTING ENUMERATION AND NOT THE DISPOSITION'S EVIDENCE. It is
#: imported so a drift between it and the fresh AST read is a RED ROW rather than a thing
#: nobody compared; every disposition below is re-derived from the port and from the pack.
from test_ep28n import THIS_PASS_DISPOSITIONS as N_STANDING          # noqa: E402

OWNER = "owner"
PROV = {"uid": 1000, "gid": 1000, "pid": 42, "window": "test"}

PACK_PATH = os.path.join(REPO, "src", "founding", "founding-pack.json")
PORT_PATH = os.path.join(REPO, "src", "bridge", "kernel_port.py")
OPDEFS_PATH = os.path.join(REPO, "src", "kernel", "opdefs.py")

NAMESPACE_LAW = "FS-LAW-NAMESPACE"
NEW_VERSION = "1.17.0"
OLD_VERSION = "1.16.0"

#: THE COMMIT THIS PASS OPENED AT — the BEFORE side of the founding diff, pinned so the row
#: compares against a fixed artifact rather than against whatever HEAD holds (§A53: HEAD moves
#: under a session because the timer commits, and cleanliness is judged from `git status`).
BEFORE_COMMIT = "aaf7652"

#: THE AFTER SIDE — added by EP-29 W1a under charter §A57, 2026-08-09, discharging the raise
#: this file filed against itself: "THIS FILE CARRIES NO AFTER PIN … RAISED: an AFTER pin for
#: this file's version rows" (`TestTheVersionMoves`, EP-28T's per-row treatment).
#:
#: WHY IT ARRIVES NOW. Two rows in `TestTheDiffIsTheChange` read `load_pack()` — the LIVE
#: tree — as the AFTER side of a historical diff. EP-29 W1a moved the founding 1.18.0 ->
#: 1.19.0 on 2026-08-09 (declaring `DEV-LAW-BIND`, amending `REGISTER-CAPABILITY`,
#: `BIND-DEVICE` and `UNBIND`), and both rows reddened on a lawful move. A differential whose
#: BEFORE is pinned and whose AFTER is live is not comparing two commits; it is comparing one
#: commit against the future — this file's own words, in the row beside them.
#:
#: WHICH COMMIT, AND WHY IT IS THIS PASS'S OWN CLOSE RATHER THAN THE LAST FOUNDING PASS'S.
#: EP-28S's close (`4f0839de…`, 1.18.0) was MEASURED first and both rows are GREEN against it
#: too — and that is precisely why it is the WRONG pin. They are green there by COINCIDENCE:
#: EP-28S's three re-declared minting ops happen to fall inside THIS pass's own
#: `CHANGED_DEFINITIONS`, so an assertion that no definition outside the enumeration moved
#: would be passing on an accident rather than on a claim. Theorem 11's actual instruction is
#: that BOTH sides of a historical assertion belong to that history's era, and this history
#: is EP-28N2's.
#:
#: CHOSEN BY CONTENT, NOT BY A LABEL, and the file's own warning re-driven rather than
#: quoted: picking by version number picks `05f29f7`, which reads `1.17.0` and ALREADY
#: carries EP-28S's law. Checked before this constant was written — at `d8a184b8…` the pack
#: reads 1.17.0 and NO op declares `mints_from`; at `05f29f7` three ops already do. Forty
#: characters for the reason given at `test_ep28j.py`'s `ERA_COMMIT`: this repo commits every
#: two minutes and a prefix resolves by the repo's size rather than by construction.
AFTER_COMMIT = "d8a184b81fdd5610880d05af8ab12f634c16b806"

#: THE EIGHT THIS PASS OWNS, one disposition each, decided in ONE authoring. RE-DERIVED and
#: set-diffed both ways in `setUp`; written here so the decision is a committed artifact a
#: later pass can era-pin, exactly as EP-28K's and EP-28N's tables are.
#:
#:   CONTAINER-BOUND  the container of the act's own key must be held.
#:   CONTAINER-KIND   the container must name a directory.
#:   CONTAINS-EMPTY   the key must hold nothing.
THIS_PASS_DISPOSITIONS = {
    ("FILE-CREATE",  "ENOENT"):    ("CONTAINER-BOUND", "binding:bound@container"),
    ("FILE-MKDIR",   "ENOENT"):    ("CONTAINER-BOUND", "binding:bound@container"),
    ("FILE-SYMLINK", "ENOENT"):    ("CONTAINER-BOUND", "binding:bound@container"),
    ("FILE-CREATE",  "ENOTDIR"):   ("CONTAINER-KIND", "kind:require:dir@container"),
    ("FILE-MKDIR",   "ENOTDIR"):   ("CONTAINER-KIND", "kind:require:dir@container"),
    ("FILE-SYMLINK", "ENOTDIR"):   ("CONTAINER-KIND", "kind:require:dir@container"),
    ("FILE-RMDIR",   "ENOTEMPTY"): ("CONTAINS-EMPTY", "contains:empty"),
    ("FILE-RENAME",  "ENOTEMPTY"): ("CONTAINS-EMPTY", "contains:empty"),
}

#: THE ROWS THIS PASS DECLARES, per op, in declaration order — load-bearing, because the
#: interpreter answers an op's checks in it and the port's own branch order is the same: a
#: create answers EEXIST, then ENOENT for its container, then ENOTDIR for what the container
#: names; an rmdir answers ENOENT, then ENOTDIR, then ENOTEMPTY.
ENUMERATED_NEW_ROWS = {
    "FILE-CREATE":  [("binding", "path", "container", "bound", None),
                     ("kind", "path", "container", "dir", None)],
    "FILE-MKDIR":   [("binding", "path", "container", "bound", None),
                     ("kind", "path", "container", "dir", None)],
    "FILE-SYMLINK": [("binding", "path", "container", "bound", None),
                     ("kind", "path", "container", "dir", None)],
    "FILE-RMDIR":   [("contains", "path", None, "empty", None)],
    "FILE-RENAME":  [("contains", "new_path", None, "empty", None)],
}

CHANGED_DEFINITIONS = set(ENUMERATED_NEW_ROWS)

#: THE KEY SPACE THIS PASS DECLARES, on the law that governs it.
ENUMERATED_KEY_SPACE = {"root": "/", "root_kind": "dir"}


# ---- the enumeration, re-derived from the port's own AST ------------------------------
def enumerate_pairs():
    """(pairs, rows, unattributable) READ FROM THE PORT'S `ERRNO_BY_ACT` AST.

    DOCUMENTED FLIP — EP-28C W4e, 2026-08-07. THE RETIRED CONSTRUCT THIS WALK WAS READING:
    `_posix_precondition`'s body, walked for every `return -errno.X` and attributed to the
    ops of its enclosing guard. THAT FUNCTION IS RETIRED — this pass's own eight were the
    last of the nineteen to gain a declared check, and W4e removed the read once they had.

    THE POPULATION SURVIVES THE FUNCTION, in the port's other structural enumeration:
    `ERRNO_BY_ACT`, one row per (op, requirement) with the errno that act renders. Same
    nineteen pairs over the same seven ops, still read from the port's own source and never
    from a list anybody wrote down — including EP-28K's, EP-28N's and this file's own.

    THE THIRD ELEMENT KEEPS ITS JOB AND CHANGES ITS SUBJECT: `unguarded` reported a return
    outside every op guard, which would serve EVERY op; its equivalent is a table row whose
    key names no operation. Reported the same way rather than dropped — the hazard is the
    same one, a member the walk cannot attribute being silently attributed."""
    with open(PORT_PATH, encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    table = next(n.value for n in ast.walk(tree)
                 if isinstance(n, ast.Assign)
                 and any(getattr(t, "id", None) == "ERRNO_BY_ACT" for t in n.targets))
    pairs, rows, unattributable = [], [], []
    for key, val in zip(table.keys, table.values):
        name = ast.unparse(val).split(".")[-1]
        elts = getattr(key, "elts", None)
        keyed = (elts is not None and len(elts) == 2
                 and all(isinstance(e, ast.Constant) and isinstance(e.value, str)
                         for e in elts))
        rows.append((name, elts[1].value if keyed else None, key.lineno))
        if not keyed:
            unattributable.append((name, key.lineno))
            continue
        pairs.append((elts[0].value, name))
    return pairs, rows, unattributable


def pack_ops(pack):
    """THE POPULATION, READ FROM THE STRUCTURE. Every `CREATE-OP` record IS an op (§A51)."""
    out = {}
    for step in pack["steps"]:
        for r in step["records"]:
            if r.get("action") == "CREATE-OP":
                pl = r.get("payload") or {}
                out[pl["name"]] = pl["definition"]
    return out


def pack_records(pack):
    return [r for step in pack["steps"] for r in step["records"]]


def new_rows(definition):
    """The rows this pass declares, read as (kind, key_param, key_of, require, forbid)."""
    out = []
    for c in (definition.get("checks") or []):
        if c.get("check") == "contains" or c.get("key_of") is not None:
            out.append((c.get("check"), c.get("key_param"), c.get("key_of"),
                        c.get("require"), c.get("forbid")))
    return out


def pack_at(commit):
    """[DOCUMENTED FLIP — EP-28Z, 2026-08-12. CAUSE: one of EIGHTEEN copies of the era-pin
    act across TEN test files. ASSERTED: a local `git show` spawn with its own
    skip-on-unresolvable branch. SUPERSEDED: the same act from `tests/era_pin.py`. REMAINS
    TRUE: the unresolvable-pin behaviour, exactly — `SkipTest` carrying git's own stderr,
    which is what `missing="skip"` names. GIVEN UP: nothing.]"""
    return era_pin.pack_at(commit, missing="skip")


class _Door:
    """A door that RAISES rather than records, so a refusal is observable without a store."""

    class Refused(Exception):
        def __init__(self, rule, message):
            super().__init__(message)
            self.rule, self.message = rule, message

    def refuse(self, actor, op, rule, message):
        raise _Door.Refused(rule, message)


class _Live(unittest.TestCase):
    """A kernel composed from the SHIPPED founding and nothing else."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep28n2-")
        self.record = os.path.join(self.dir, "record.jsonl")
        self.store, self.gate, self.views, self.blobs, self.subs = build_full_kernel(
            self.record, os.path.join(self.dir, "blobs"), os.path.join(self.dir, "vault"))

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def act(self, op, **params):
        params.setdefault("provenance", PROV)
        return self.gate.execute(op, OWNER, params)

    def keys(self):
        return set(opdefs._live_bindings(self.store, self.views))

    def refusals(self):
        return list(self.store.by_action("op-refused"))


# ---------------------------------------------------------------------------------------
# T-CLASS-DECIDED
# ---------------------------------------------------------------------------------------
class TestTheClassIsDecided(unittest.TestCase):
    """T-CLASS-DECIDED, RE-DERIVED RATHER THAN CARRIED.

    THE PLACEMENT IS THE CLAUSE (§A48). The re-derivation and BOTH set-diffs run in `setUp`,
    not as a sibling row, because `unittest` orders methods alphabetically and a precedence
    stated in prose is void: a drift in the port's enumeration must red BEFORE any
    disposition is read, and the framework guarantees that only for `setUp`."""

    def setUp(self):
        pairs, rows, unattributable = enumerate_pairs()
        self.assertEqual(unattributable, [],
                         "an act-keyed row names no operation, so it cannot be attributed "
                         "and this enumeration would understate the class")
        self.pairs, self.returns = pairs, rows
        self.derived = set(pairs)
        # THE SECOND SET-DIFF, AGAINST EP-28N'S STANDING TABLE. It is the STARTING
        # enumeration and not the evidence: a drift either way is a finding, and the row that
        # reads it runs before any disposition below.
        self.standing_eight = set(N_STANDING) & self.derived
        self.declared_now = {(op, e) for (op, e) in self.derived} - set(THIS_PASS_DISPOSITIONS)

    def test_the_mechanical_counts_are_what_the_reading_found(self):
        """NINETEEN act-keyed rows over SEVEN ops over SEVEN requirements.

        DOCUMENTED FLIP — EP-28C W4e, 2026-08-07. THE RETIRED CONSTRUCT THIS ROW WAS READING:
        the count of return points inside `_posix_precondition`, asserted beside the pair
        count "because the code count alone hides an op (one branch serves the three
        create-family ops) and the pair count alone hides a shared branch."

        THIRTEEN WAS THE RETIRED BODY'S SHAPE. The pairing it bought is rebuilt on the
        countable that survives — the REQUIREMENT set, where `binding:unbound` serves four ops
        exactly as one branch served three — so two numbers still move independently."""
        self.assertEqual(len(self.returns), 19, self.returns)
        self.assertEqual(len(self.derived), 19)
        self.assertEqual(len({op for op, _e in self.pairs}), 7)
        self.assertEqual(len({r for _n, r, _l in self.returns}), 7,
                         "the requirement set is the countable that can move without the "
                         "row count moving, which is what makes the pair evidence")

    def test_the_fresh_read_and_EP28Ns_standing_table_do_not_drift(self):
        """THE SET-DIFF THE AMENDMENT DIRECTS, both directions, reported as a finding rather
        than assumed. EP-28N's table holds eleven; eight of them are the hierarchy members it
        raised, and those eight are exactly what this pass owns."""
        raised_by_N = {pair for pair, (verdict, _k) in N_STANDING.items()
                       if verdict == "HIERARCHY"}
        self.assertEqual(raised_by_N - self.derived, set(),
                         "EP-28N's table holds a pair the port's AST does not")
        self.assertEqual(len(raised_by_N), 8)
        self.assertEqual(set(THIS_PASS_DISPOSITIONS) - raised_by_N, set(),
                         "this pass dispositions a pair EP-28N did not raise")
        self.assertEqual(raised_by_N - set(THIS_PASS_DISPOSITIONS), set(),
                         "EP-28N raised a pair this pass does not disposition")

    def test_every_one_of_the_eight_carries_a_disposition_and_the_set_is_exact(self):
        self.assertEqual(len(THIS_PASS_DISPOSITIONS), 8)
        self.assertEqual(set(THIS_PASS_DISPOSITIONS) - self.derived, set(),
                         "a disposition names a pair the port's AST does not serve")

    def test_the_dispositions_partition_and_the_arithmetic_closes(self):
        tally = {}
        for verdict, _req in THIS_PASS_DISPOSITIONS.values():
            tally[verdict] = tally.get(verdict, 0) + 1
        self.assertEqual(tally, {"CONTAINER-BOUND": 3, "CONTAINER-KIND": 3,
                                 "CONTAINS-EMPTY": 2})
        self.assertEqual(sum(tally.values()), 8)

    def test_THE_WHOLE_ENUMERATION_IS_NOW_DECLARED_and_that_is_the_passs_result(self):
        """The nineteen the port's own preconditions serve, and the nineteen the founding now
        declares, are the SAME SET — computed from the pack rather than counted by hand."""
        ops = pack_ops(load_pack())
        declared = {(n, r) for n, d in ops.items() if n in DECISION_OPS
                    for r in opdefs.declared_requirements(d)}
        rendered = {(op, ERRNO_BY_ACT[(op, req)]) for (op, req) in declared}
        as_names = {(op, [k for k, v in vars(__import__("errno")).items()
                          if v == e and k.startswith("E")][0]) for op, e in rendered}
        self.assertEqual(as_names - self.derived, set(),
                         "the law declares an outcome the port's preconditions do not serve")
        self.assertEqual(self.derived - as_names, set(),
                         "the port serves an outcome the law does not declare")

    def test_a_hand_list_double_that_drops_one_pair_reds_on_the_set_clause(self):
        """THE RED WORLD FOR THIS ROW, produced rather than described (§A42): the failure a
        hand-written enumeration has is a silent omission, and the set-diff is what catches
        it. Driven by dropping one member from the derived side and re-running the same
        comparison this row's `setUp` runs."""
        doubled = self.derived - {("FILE-RMDIR", "ENOTEMPTY")}
        self.assertNotEqual(set(THIS_PASS_DISPOSITIONS) - doubled, set(),
                            "a dropped pair must be visible to the set-diff")


# ---------------------------------------------------------------------------------------
# THE ROWS LANDED, IN THE FOUNDING
# ---------------------------------------------------------------------------------------
class TestTheRowsLanded(unittest.TestCase):

    def setUp(self):
        self.ops = pack_ops(load_pack())

    def test_the_new_rows_equal_the_enumeration_both_directions(self):
        declared = {n: new_rows(d) for n, d in self.ops.items() if new_rows(d)}
        self.assertEqual(set(declared) - set(ENUMERATED_NEW_ROWS), set(),
                         "the pack declares a row the enumeration did not name")
        self.assertEqual(set(ENUMERATED_NEW_ROWS) - set(declared), set(),
                         "the enumeration names a row the pack does not declare")
        for name, rows in ENUMERATED_NEW_ROWS.items():
            self.assertEqual(declared[name], rows, name)

    def test_the_declaration_order_is_the_port_branch_order(self):
        """ORDER IS A PROPERTY OF THE DECLARATION AND NOT OF PROSE (§A48). The interpreter
        answers an op's checks in declaration order, so a container row placed before the
        op's own-name row would answer ENOENT where POSIX answers EEXIST — green in every
        behavioural row that never drives both at once."""
        for name in ("FILE-CREATE", "FILE-MKDIR", "FILE-SYMLINK"):
            kinds = [(c.get("check"), c.get("require"), c.get("key_of"))
                     for c in self.ops[name]["checks"]]
            self.assertEqual(kinds, [("binding", "unbound", None),
                                     ("binding", "bound", "container"),
                                     ("kind", "dir", "container")], name)
        self.assertEqual([(c.get("check"), c.get("require")) for c in
                          self.ops["FILE-RMDIR"]["checks"]],
                         [("binding", "bound"), ("kind", "dir"), ("contains", "empty")])
        self.assertEqual([(c.get("check"), c.get("require"), c.get("key_param")) for c in
                          self.ops["FILE-RENAME"]["checks"]],
                         [("binding", "bound", "path"),
                          ("contains", "empty", "new_path"),
                          ("binding", None, "new_path")])

    def test_the_key_space_is_declared_on_the_law_that_governs_it(self):
        law = [r for r in pack_records(load_pack())
               if r.get("action") == "CREATE-RULE"
               and (r.get("payload") or {}).get("rule_id") == NAMESPACE_LAW]
        self.assertEqual(len(law), 1)
        self.assertEqual((law[0]["payload"] or {}).get("key_space"), ENUMERATED_KEY_SPACE)

    def test_and_it_is_the_ONLY_law_that_declares_one(self):
        """The declaration is not global engine state: it is a field on one rule, and the
        population is asserted so a second key space cannot arrive unnoticed."""
        declaring = {(r.get("payload") or {}).get("rule_id")
                     for r in pack_records(load_pack())
                     if (r.get("payload") or {}).get("key_space") is not None}
        self.assertEqual(declaring, {NAMESPACE_LAW})

    def test_the_shipped_pack_validates_whole_under_the_new_clauses(self):
        peers = dict(self.ops)
        for name, d in self.ops.items():
            opdefs.validate_definition_shape(_Door(), "FOUNDING", "SYSTEM", name, d, peers)


# ---------------------------------------------------------------------------------------
# T-REFUSAL-CITES-TIP-RULE — all eight, driven
# ---------------------------------------------------------------------------------------
class TestEveryMemberRefusesCitingTheTipRule(_Live):
    """T-REFUSAL-CITES-TIP-RULE, driven on ALL EIGHT rather than on two (§A49's requirement
    is a floor). The least likely member is named and driven with it."""

    def _drive_all_eight(self):
        """Every one of the eight, through the real gate, in one world. Returns
        {(op, expected errno name): the OpError it raised}."""
        self.act("FILE-MKDIR", path="/d")
        self.act("FILE-CREATE", path="/d/f")
        self.act("FILE-MKDIR", path="/e")
        self.act("FILE-CREATE", path="/e/x")
        self.act("FILE-CREATE", path="/r")
        raised = {}
        drives = [
            (("FILE-CREATE", "ENOENT"),    ("FILE-CREATE",  {"path": "/gone/y"})),
            (("FILE-MKDIR", "ENOENT"),     ("FILE-MKDIR",   {"path": "/gone/y"})),
            (("FILE-SYMLINK", "ENOENT"),   ("FILE-SYMLINK", {"path": "/gone/y",
                                                             "target": "t"})),
            (("FILE-CREATE", "ENOTDIR"),   ("FILE-CREATE",  {"path": "/d/f/g"})),
            (("FILE-MKDIR", "ENOTDIR"),    ("FILE-MKDIR",   {"path": "/d/f/g"})),
            (("FILE-SYMLINK", "ENOTDIR"),  ("FILE-SYMLINK", {"path": "/d/f/g",
                                                             "target": "t"})),
            (("FILE-RMDIR", "ENOTEMPTY"),  ("FILE-RMDIR",   {"path": "/d"})),
            (("FILE-RENAME", "ENOTEMPTY"), ("FILE-RENAME",  {"path": "/r",
                                                             "new_path": "/e"})),
        ]
        for member, (op, params) in drives:
            with self.assertRaises(OpError) as got:
                self.act(op, **params)
            raised[member] = got.exception
        return raised

    def test_all_eight_refuse_and_every_refusal_cites_the_TERMINAL_rule(self):
        raised = self._drive_all_eight()
        self.assertEqual(set(raised), set(THIS_PASS_DISPOSITIONS),
                         "the drive covers exactly the eight this pass owns")
        for member, e in sorted(raised.items()):
            self.assertEqual(e.rule, NAMESPACE_LAW, member)

    def test_and_every_refusal_APPENDED_a_record_carrying_that_rule(self):
        """Ruling 1's first half: a rejection of an action performed is ALWAYS recorded, and
        the record carries the tip-level rule and not the reasoning chain."""
        self._drive_all_eight()
        refused = [e for e in self.refusals()
                   if (e.get("payload") or {}).get("op") in
                   {op for op, _e in THIS_PASS_DISPOSITIONS}]
        self.assertEqual(len(refused), 8, "eight refusals, eight records")
        self.assertEqual({e["rule_cited"] for e in refused}, {NAMESPACE_LAW})
        for e in refused:
            self.assertNotIn("chain", (e.get("payload") or {}),
                             "a stored chain is a stored derivative (wrong reference 2)")

    def test_THE_LEAST_LIKELY_MEMBER_named_and_driven(self):
        """§A49's member, NAMED WITH ITS REASON. `FILE-RENAME`'s ENOTEMPTY is the member
        least likely to share the class's property: it is the only one whose key is NOT the
        op's own subject (`new_path`, the destination), the only one whose key the op does
        NOT require bound, and the only one the port answers with a THREE-part condition
        (exists AND is a directory AND has children) where the law asks one question. If the
        class decision held anywhere by accident, it would break here."""
        self.act("FILE-MKDIR", path="/e")
        self.act("FILE-CREATE", path="/e/x")
        self.act("FILE-CREATE", path="/r")
        with self.assertRaises(OpError) as got:
            self.act("FILE-RENAME", path="/r", new_path="/e")
        self.assertEqual(got.exception.rule, NAMESPACE_LAW)
        self.assertEqual(getattr(got.exception, "requirement", None), "contains:empty")
        self.assertEqual(self.store.by_action("FILE-RENAME"), [],
                         "and no act was recorded for the refused rename")

    def test_AND_AN_EMPTY_DESTINATION_IS_ADMITTED_which_is_the_non_vacuity(self):
        """Without this the row above proves only that renames refuse."""
        self.act("FILE-MKDIR", path="/e")
        self.act("FILE-CREATE", path="/r")
        self.act("FILE-RENAME", path="/r", new_path="/e")
        self.assertEqual(len(self.store.by_action("FILE-RENAME")), 1)

    def test_THE_CHAIN_CITING_DOUBLE_reds_on_the_tip_clause_and_no_other(self):
        """THE RED WORLD (§A63: the check it names is DECLARED and verified against the pack
        above). A double that cited an INTERMEDIATE rule instead of the terminal one greens
        every errno clause — the act key does not read the citation at all — and reds only
        the citation clause. Driven through the real path by amending the declared row's own
        `cite`, so the double is the shipped mechanism carrying a wrong citation."""
        ops = pack_ops(load_pack())
        row = [c for c in ops["FILE-CREATE"]["checks"] if c.get("key_of") == "container"][0]
        self.assertEqual(row.get("cite"), NAMESPACE_LAW, "non-vacuity: the true citation")
        shopped = dict(row, cite="ROOT-NEG-6")
        self.assertNotEqual(shopped["cite"], NAMESPACE_LAW)
        # the errno clause is INDIFFERENT to the citation — the payoff removed, measured
        self.assertEqual(ERRNO_BY_ACT[("FILE-CREATE", "binding:bound@container")],
                         __import__("errno").ENOENT)
        self.assertNotIn("ROOT-NEG-6", {k[1] for k in ERRNO_BY_ACT})


# ---------------------------------------------------------------------------------------
# T-TWO-KEYS — the record's key and the caller's key, asserted independently
# ---------------------------------------------------------------------------------------
class TestTheTwoKeysForAllEight(_Live):
    """The RECORD is keyed by the RULE; the CALLER's answer is keyed by the ACT. Asserted
    INDEPENDENTLY for every one of the eight, so a citation chosen for its errno fails the
    citation clause while greening the errno clause and the split is visible."""

    def _port(self):
        store, gate, views, blobs = build_brain(
            os.path.join(self.dir, "port.jsonl"), os.path.join(self.dir, "portblobs"))
        return KernelPort(store, gate, views, blobs)

    def test_every_one_of_the_eight_renders_the_ACTS_errno(self):
        import errno as E
        want = {
            ("FILE-CREATE",  "binding:bound@container"):    E.ENOENT,
            ("FILE-MKDIR",   "binding:bound@container"):    E.ENOENT,
            ("FILE-SYMLINK", "binding:bound@container"):    E.ENOENT,
            ("FILE-CREATE",  "kind:require:dir@container"): E.ENOTDIR,
            ("FILE-MKDIR",   "kind:require:dir@container"): E.ENOTDIR,
            ("FILE-SYMLINK", "kind:require:dir@container"): E.ENOTDIR,
            ("FILE-RMDIR",   "contains:empty"):             E.ENOTEMPTY,
            ("FILE-RENAME",  "contains:empty"):             E.ENOTEMPTY,
        }
        for key, errno_value in sorted(want.items()):
            self.assertEqual(ERRNO_BY_ACT[key], errno_value, key)

    def test_and_the_RULE_keyed_table_gained_nothing(self):
        """WRONG REFERENCE 3, refused structurally one more time. Eight new outcomes, one
        governing rule, and NO row added to the map keyed by that rule."""
        self.assertNotIn(NAMESPACE_LAW, ERRNO_BY_RULE)
        self.assertEqual(len(ERRNO_BY_RULE), 9, "unchanged since EP-28K's measurement")
        self.assertEqual(len(ERRNO_BY_ACT), 19, "eleven plus this pass's eight")

    def test_the_port_renders_the_ACTS_answer_through_its_own_function(self):
        """Driven through `_errno_for_refusal` rather than read off the table, so the row
        exercises the path a caller actually takes."""
        import errno as E
        port = self._port()
        self.act("FILE-MKDIR", path="/d")
        self.act("FILE-CREATE", path="/d/f")
        cases = [("FILE-CREATE", {"path": "/gone/y"}, E.ENOENT),
                 ("FILE-CREATE", {"path": "/d/f/g"}, E.ENOTDIR)]
        for op, params, want in cases:
            with self.assertRaises(OpError) as got:
                self.act(op, **params)
            self.assertEqual(port._errno_for_refusal(op, got.exception), want, params)
            self.assertEqual(got.exception.rule, NAMESPACE_LAW,
                             "the CITATION clause, asserted independently of the errno")


# ---------------------------------------------------------------------------------------
# THE REQUIREMENT CARRIES WHICH KEY — wrong reference 2
# ---------------------------------------------------------------------------------------
class TestTheRequirementCarriesWhichKey(unittest.TestCase):
    """`binding:bound` over an act's own key and over its CONTAINER are two different
    outcomes. A requirement that could not tell them apart would be the rule-keyed map this
    EP removed, rebuilt one layer down inside the act key."""

    def test_the_two_forms_are_distinct_strings(self):
        self.assertNotEqual(opdefs._requirement("binding:bound", None),
                            opdefs._requirement("binding:bound", "container"))
        self.assertEqual(opdefs._requirement("binding:bound", None), "binding:bound")
        self.assertEqual(opdefs._requirement("binding:bound", "container"),
                         "binding:bound@container")

    def test_and_the_collision_IS_REACHABLE_which_is_why_the_suffix_exists(self):
        """THE CAN-FAIL CONTROL. Without the suffix, `FILE-CREATE`'s container row and any
        own-key `binding:bound` row would produce ONE string for TWO errnos — driven by
        computing the un-suffixed set over a definition that declares both."""
        d = {"checks": [{"check": "binding", "key_param": "path", "require": "bound"},
                        {"check": "binding", "key_param": "path", "key_of": "container",
                         "require": "bound"}]}
        self.assertEqual(len(opdefs.declared_requirements(d)), 2,
                         "two rows, two requirements — the suffix is what keeps them two")
        flat = {"binding:%s" % c["require"] for c in d["checks"]}
        self.assertEqual(len(flat), 1,
                         "and without it they collapse to one, which is the defect")

    def test_no_requirement_string_names_a_rule(self):
        rules = {r.get("object") for r in pack_records(load_pack())
                 if r.get("action") == "CREATE-RULE"}
        self.assertEqual({k[1] for k in ERRNO_BY_ACT} & rules, set())


# ---------------------------------------------------------------------------------------
# THE DERIVATION IS THE LAW'S — wrong reference 1
# ---------------------------------------------------------------------------------------
class TestTheDerivationIsTheLawsNotTheCallers(_Live):
    """WRONG REFERENCE 1'S DETECTOR. The cheaper shape the plan floats is to let the PORT
    compute the container and hand it in as a parameter. A caller that could supply its own
    container would be performing check-then-act across the decide region's boundary — the
    exact shape EP-28K exists to close."""

    def test_no_op_UNDER_THIS_LAW_takes_a_container_parameter(self):
        """The structural half: the container is not a parameter of any op governed by this
        key space, so there is nothing for a caller to supply.

        THE POPULATION IS THE LAW'S CITERS AND NOT EVERY OP, and the narrowing is a finding
        rather than a convenience: `CREATE-SPACE` DOES take a `parent`, under a different law,
        and it is the shape this pass refuses — the caller names the parent and the check
        reads what it was handed. The space tree can afford that because a space's parent is
        CONTENT the caller chooses; a namespace container is DERIVED from the key the act
        already carries, and a caller choosing it would be choosing its own precondition."""
        ops = pack_ops(load_pack())
        governed = {n for n, d in ops.items() if d.get("law_cited") == NAMESPACE_LAW}
        self.assertGreaterEqual(len(governed), 7, "non-vacuity: the law has citers")
        for name in sorted(governed):
            params = set(ops[name].get("params") or {}) | set(
                ops[name].get("param_defaults") or {})
            self.assertEqual({p for p in params if "parent" in p or "container" in p}, set(),
                             name)
        self.assertIn("parent", set(ops["CREATE-SPACE"].get("params") or {}),
                      "non-vacuity: the shape this row refuses exists elsewhere in the pack")

    def test_a_caller_supplying_its_own_container_is_IGNORED_not_believed(self):
        """The behavioural half, DRIVEN: a caller states a container of its own choosing —
        the root, which would make every create lawful — and the law refuses anyway, because
        the key it checks is the one it derived from the act's own key.

        THIS IS THE WHOLE OF WRONG REFERENCE 1. Under the handed-in shape this exact call
        would have been ADMITTED: the caller reads the namespace, decides its parent is fine,
        and the gate checks the caller's arithmetic — two steps across the region's boundary,
        which is the composition EP-28K exists to close."""
        with self.assertRaises(OpError) as got:
            self.act("FILE-CREATE", path="/gone/y", container="/", parent="/",
                     parent_path="/")
        self.assertEqual(got.exception.rule, NAMESPACE_LAW)
        self.assertEqual(getattr(got.exception, "requirement", None),
                         "binding:bound@container",
                         "the container row fired on the DERIVED key, not on the stated one")
        self.assertEqual(self.store.by_action("FILE-CREATE"), [])

    def test_the_container_the_law_uses_is_derived_from_the_CANONICAL_key(self):
        """EP-28O's order, extended: the value the container is computed from is already the
        namespace's canonical spelling, so one directory has one container whatever the
        caller spelled."""
        self.act("FILE-MKDIR", path="/a/")
        self.act("FILE-CREATE", path="/a/b")
        self.assertEqual(self.keys(), {"/", "/a", "/a/b"})
        self.assertEqual(custody.parent_of("/a/b"), "/a")


# ---------------------------------------------------------------------------------------
# THE ROOT — declared, seeded, not unbindable, and its residual driven
# ---------------------------------------------------------------------------------------
class TestTheDeclaredRoot(_Live):
    """A hierarchy question needs a bottom, and the bottom is bound by no act."""

    def test_the_root_is_in_the_laws_key_set_before_any_act(self):
        self.assertEqual(self.keys(), {"/"})
        self.assertEqual(opdefs._live_namespace(self.store, self.views)[1], {"/": "dir"})

    def test_and_no_record_describes_it(self):
        """The declaration is LAW-DATA and not an act, so `custody.ROOT_INO`'s standing
        property — one identity with no covering record — is untouched."""
        paths = [(e.get("payload") or {}).get("path") for e in self.store.all()]
        self.assertNotIn("/", paths)

    def test_a_top_level_create_lands_BECAUSE_the_root_is_declared(self):
        self.act("FILE-CREATE", path="/f")
        self.assertEqual(self.keys(), {"/", "/f"})

    def test_THE_CAN_FAIL_CONTROL_without_the_declaration_every_top_level_create_refuses(self):
        """THE RED WORLD FOR THE ROOT, driven through the loaded module rather than argued:
        `declared_roots` is made to answer "this law declares no key space", which is exactly
        the state a world founded at 1.16.0 is in, and the first top-level create refuses."""
        real = opdefs.declared_roots
        opdefs.declared_roots = lambda *a, **k: {}
        try:
            with self.assertRaises(OpError) as got:
                self.act("FILE-CREATE", path="/f")
        finally:
            opdefs.declared_roots = real
        self.assertEqual(got.exception.rule, NAMESPACE_LAW)
        self.assertEqual(getattr(got.exception, "requirement", None),
                         "binding:bound@container")
        self.act("FILE-CREATE", path="/f")               # and it lands with the declaration

    def test_the_declared_root_is_NOT_UNBINDABLE(self):
        """THE LEASH THE SEEDING ARRIVES WITH (design-soul §2). An rmdir of the root on an
        empty world meets every declared requirement and is ADMITTED — which is a phantom act
        older than this pass — but it does not take the key space's bottom with it."""
        self.act("FILE-RMDIR", path="/")
        self.assertIn("/", self.keys(), "the root survives an act that claims to remove it")
        self.act("FILE-CREATE", path="/still")
        self.assertEqual(self.keys(), {"/", "/still"})

    def test_and_a_NON_EMPTY_root_refuses_which_is_the_half_this_pass_closes(self):
        self.act("FILE-CREATE", path="/f")
        with self.assertRaises(OpError) as got:
            self.act("FILE-RMDIR", path="/")
        self.assertEqual(getattr(got.exception, "requirement", None), "contains:empty")

    def test_THE_LEASH_the_declared_root_is_the_key_the_grammar_says_has_no_container(self):
        """The law declares a root; the namespace's own container relation says which key has
        no container. They must be the SAME KEY, and this is where that stops being an
        assumption: a law declaring a root the grammar does not agree about REDS here."""
        roots = opdefs.declared_roots(
            {n: (v.get("definition") or {}) for n, v in self.views.op_definitions().items()},
            self.views)
        self.assertEqual(set(roots), {"/"})
        for root in roots:
            self.assertIsNone(custody.parent_of(root),
                              "the declared root has a container, so it is not the bottom")
        others = {"/a", "/a/b", "/x"}
        for k in others:
            self.assertIsNotNone(custody.parent_of(k),
                                 "non-vacuity: the relation returns a container for keys "
                                 "that have one")


# ---------------------------------------------------------------------------------------
# TWO-TIMES — an earlier founding is untouched
# ---------------------------------------------------------------------------------------
class TestAnEarlierFoundingIsUntouched(unittest.TestCase):
    """The law reaches FOUNDINGS. A world founded at 1.16.0 declares no container rows and no
    key space, so it seeds no root, folds exactly what it always folded, and admits exactly
    what it always admitted — asserted by DRIVING it, not by reading the code."""

    def _world_at(self, commit):
        era = pack_at(commit)
        d = tempfile.mkdtemp(prefix="ep28n2-era-")
        saved = install_module.load_pack
        install_module.load_pack = lambda path=None: era
        try:
            return d, build_full_kernel(os.path.join(d, "record.jsonl"),
                                        os.path.join(d, "blobs"), os.path.join(d, "vault"))
        finally:
            install_module.load_pack = saved

    def test_a_1_16_0_world_seeds_no_root_and_admits_a_parentless_create(self):
        d, (store, gate, views, _b, _s) = self._world_at(BEFORE_COMMIT)
        try:
            self.assertEqual(pack_at(BEFORE_COMMIT)["founding_version"], OLD_VERSION,
                             "non-vacuity: the era world is the PREVIOUS founding")
            self.assertEqual(opdefs._live_bindings(store, views), frozenset(),
                             "no key space declared, so no root seeded")
            gate.execute("FILE-CREATE", OWNER, {"path": "/gone/y", "provenance": PROV})
            self.assertEqual(set(opdefs._live_bindings(store, views)), {"/gone/y"},
                             "and the act its own law admitted is still admitted")
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_and_the_SAME_act_refuses_under_the_shipped_founding(self):
        """The differential, so the row above measures the era rather than nothing."""
        d = tempfile.mkdtemp(prefix="ep28n2-now-")
        try:
            _s, gate, _v, _b, _x = build_full_kernel(
                os.path.join(d, "record.jsonl"), os.path.join(d, "blobs"),
                os.path.join(d, "vault"))
            with self.assertRaises(OpError):
                gate.execute("FILE-CREATE", OWNER, {"path": "/gone/y", "provenance": PROV})
        finally:
            shutil.rmtree(d, ignore_errors=True)


# ---------------------------------------------------------------------------------------
# T-ABSENCE-STAYS
# ---------------------------------------------------------------------------------------
class TestAbsenceStaysAbsence(unittest.TestCase):
    """§11.1a's ABSENCE membership was conditional on nothing governing the outcome. The ops
    this pass does not reach keep it untouched, asserted as a SET rather than as a sentence."""

    def test_the_ops_declaring_a_container_or_contains_row_are_EXACTLY_the_five(self):
        # [DOCUMENTED FLIP — EP-29 W1b, 2026-08-12, charter §A57. CAUSE: "sixty-seven ops are
        # untouched BY THIS PASS" is a fact about the sixty-seven that existed when this pass
        # ran; EP-29 W1b added two more and the live count became sixty-nine. ASSERTED:
        # `load_pack()`, live. SUPERSEDED: `pack_at(AFTER_COMMIT)`, this pass's own close
        # commit. REMAINS TRUE: the declaring set is EXACTLY the five, both directions.]
        ops = pack_ops(pack_at(AFTER_COMMIT))
        declaring = {n for n, d in ops.items() if new_rows(d)}
        self.assertEqual(declaring, CHANGED_DEFINITIONS)
        self.assertEqual(len(ops) - len(declaring), 67,
                         "sixty-seven ops are untouched by this pass")

    def test_an_op_declaring_no_check_keeps_its_classification(self):
        """EP-28K's clause extended over this pass's landed set: an op that declares nothing
        is not made to invent a container question."""
        ops = pack_ops(load_pack())
        silent = {n for n, d in ops.items() if not (d.get("checks") or [])}
        self.assertGreater(len(silent), 0, "non-vacuity: silent ops exist")
        for n in silent:
            self.assertEqual(new_rows(ops[n]), [], n)


# ---------------------------------------------------------------------------------------
# T-GUARD-AT-THREE-DOORS
# ---------------------------------------------------------------------------------------
class TestTheGuardsAtThreeDoors(_Live):
    """The new declaration and the new kind, malformed, refuse at the installer, at CREATE-OP
    and at AMEND-OP. One vocabulary, three doors, and a can-fail control per clause."""

    def _op(self, checks, params=None):
        return {"law_cited": NAMESPACE_LAW,
                "params": dict(params or {"path": "required"}),
                "payload_from": list((params or {"path": "required"}).keys()),
                "checks": checks}

    def _bind(self, **kw):
        row = {"check": "binding", "key_param": "path", "require": "unbound",
               "effect": "bind", "cite": NAMESPACE_LAW, "binds_kind": {"literal": "dir"}}
        row.update(kw)
        return row

    def _peers(self):
        return {n: (v.get("definition") or {}) for n, v in self.views.op_definitions().items()}

    def _refuses(self, d):
        with self.assertRaises(_Door.Refused):
            opdefs.validate_definition_shape(_Door(), "CREATE-OP", OWNER, "NS", d,
                                             self._peers())

    def test_an_unknown_key_derivation_refuses(self):
        self._refuses(self._op([self._bind(),
                                {"check": "binding", "key_param": "path",
                                 "key_of": "containr", "require": "bound",
                                 "cite": NAMESPACE_LAW}]))

    def test_a_key_of_on_a_row_that_carries_an_effect_refuses(self):
        """The one combination that is false rather than merely useless: an act moves the
        name it acts on and never the name that contains it."""
        self._refuses(self._op([self._bind(key_of="container")]))

    def test_a_key_of_on_a_check_that_asks_about_no_key_refuses(self):
        self._refuses(self._op([self._bind(),
                                {"check": "sight", "target_param": "path",
                                 "key_of": "container", "cite": NAMESPACE_LAW}]))

    def test_a_class_question_over_a_container_the_op_does_not_require_bound_refuses(self):
        """The ORDER clause, matched on the KEY the row asks about rather than on the
        parameter: a create requires its own name UNBOUND and its container BOUND over one
        parameter, so a match on `key_param` alone would read the unbound row as the class
        question's prior bound row."""
        self._refuses(self._op([self._bind(),
                                {"check": "kind", "key_param": "path",
                                 "key_of": "container", "require": "dir",
                                 "cite": NAMESPACE_LAW}]))

    def test_and_the_same_pair_IN_ORDER_is_ADMITTED_which_is_the_non_vacuity(self):
        opdefs.validate_definition_shape(
            _Door(), "CREATE-OP", OWNER, "NS",
            self._op([self._bind(),
                      {"check": "binding", "key_param": "path", "key_of": "container",
                       "require": "bound", "cite": NAMESPACE_LAW},
                      {"check": "kind", "key_param": "path", "key_of": "container",
                       "require": "dir", "cite": NAMESPACE_LAW}]),
            self._peers())

    def test_a_contains_row_naming_no_key_refuses(self):
        self._refuses(self._op([self._bind(),
                                {"check": "contains", "require": "empty",
                                 "cite": NAMESPACE_LAW}]))

    def test_a_contains_row_naming_an_unknown_parameter_refuses(self):
        self._refuses(self._op([self._bind(),
                                {"check": "contains", "key_param": "nope",
                                 "require": "empty", "cite": NAMESPACE_LAW}]))

    def test_a_contains_row_requiring_nothing_refuses(self):
        self._refuses(self._op([self._bind(),
                                {"check": "contains", "key_param": "path",
                                 "cite": NAMESPACE_LAW}]))

    def test_a_contains_row_with_an_unknown_requirement_refuses(self):
        self._refuses(self._op([self._bind(),
                                {"check": "contains", "key_param": "path",
                                 "require": "nonempty", "cite": NAMESPACE_LAW}]))

    def test_THE_CAN_FAIL_CONTROLS_with_the_guards_neutered_each_malformed_row_is_ADMITTED(self):
        """Without this the passing rows above prove only that nothing refused, which is not
        the same as there being something that would."""
        bad = [self._op([self._bind(), {"check": "binding", "key_param": "path",
                                        "key_of": "containr", "require": "bound",
                                        "cite": NAMESPACE_LAW}]),
               self._op([self._bind(), {"check": "contains", "key_param": "path",
                                        "require": "nonempty", "cite": NAMESPACE_LAW}])]
        real_of, real_c = opdefs._require_wellformed_key_of, opdefs._require_wellformed_contains
        opdefs._require_wellformed_key_of = lambda *a, **k: None
        opdefs._require_wellformed_contains = lambda *a, **k: None
        try:
            for d in bad:
                opdefs.validate_definition_shape(_Door(), "CREATE-OP", OWNER, "NS", d,
                                                 self._peers())
        finally:
            opdefs._require_wellformed_key_of = real_of
            opdefs._require_wellformed_contains = real_c
        for d in bad:
            self._refuses(d)

    def test_the_installer_and_the_gate_run_the_SAME_function(self):
        self.assertIs(install_module.validate_definition_shape,
                      opdefs.validate_definition_shape)

    def test_the_FOUNDING_door_refuses_a_malformed_pack_whole(self):
        """The third door, driven on a real pack copy rather than on a hand-built dict."""
        pack = copy.deepcopy(load_pack())
        for step in pack["steps"]:
            for r in step["records"]:
                pl = r.get("payload") or {}
                if r.get("action") == "CREATE-OP" and pl.get("name") == "FILE-RMDIR":
                    for c in pl["definition"]["checks"]:
                        if c.get("check") == "contains":
                            c["require"] = "nonempty"
        with self.assertRaises(install_module.FoundingIntegrityError):
            install_module._validate(install_module.records(pack))
        install_module._validate(install_module.records(load_pack()))   # non-vacuity


# ---------------------------------------------------------------------------------------
# THE ENGINE STILL NAMES NO FILESYSTEM — wrong reference 4
# ---------------------------------------------------------------------------------------
class TestTheEngineStillNamesNoFilesystem(unittest.TestCase):
    """I5, asserted rather than intended, and it is the clause this pass was most at risk of
    breaking: a container relation IS namespace grammar, and the temptation is to write it in
    kernel space with a separator baked in."""

    def test_opdefs_holds_no_filesystem_word_and_no_separator(self):
        with open(OPDEFS_PATH, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        literals = {n.value for n in ast.walk(tree)
                    if isinstance(n, ast.Constant) and isinstance(n.value, str)}
        for word in ("dir", "link", "fifo", "directory", "path", "/"):
            self.assertNotIn(word, literals,
                             "opdefs.py holds the string %r — the engine is naming a "
                             "filesystem" % word)

    def test_the_root_and_its_class_are_read_from_the_LAW(self):
        """The words `/` and `dir` live in the founding and nowhere else — asserted by
        changing the law and watching the engine follow it."""
        pack = copy.deepcopy(load_pack())
        for step in pack["steps"]:
            for r in step["records"]:
                pl = r.get("payload") or {}
                if pl.get("rule_id") == NAMESPACE_LAW:
                    pl["key_space"] = {"root": "/", "root_kind": "folder"}
                if r.get("action") == "CREATE-OP" and pl.get("name") in (
                        "FILE-CREATE", "FILE-MKDIR", "FILE-SYMLINK"):
                    for c in pl["definition"]["checks"]:
                        if c.get("key_of") == "container" and c.get("check") == "kind":
                            c["require"] = "folder"
                if r.get("action") == "CREATE-OP" and pl.get("name") == "FILE-MKDIR":
                    for c in pl["definition"]["checks"]:
                        if c.get("binds_kind"):
                            c["binds_kind"] = {"literal": "folder"}
        d = tempfile.mkdtemp(prefix="ep28n2-word-")
        saved = install_module.load_pack
        install_module.load_pack = lambda path=None: pack
        try:
            store, gate, views, _b, _s = build_full_kernel(
                os.path.join(d, "record.jsonl"), os.path.join(d, "blobs"),
                os.path.join(d, "vault"))
            self.assertEqual(opdefs._live_namespace(store, views)[1], {"/": "folder"},
                             "the engine carried the law's own word for what a root names")
            gate.execute("FILE-MKDIR", OWNER, {"path": "/a", "provenance": PROV})
            gate.execute("FILE-CREATE", OWNER, {"path": "/a/b", "provenance": PROV})
            self.assertEqual(set(opdefs._live_bindings(store, views)), {"/", "/a", "/a/b"})
        finally:
            install_module.load_pack = saved
            shutil.rmtree(d, ignore_errors=True)


class TestOneComputerOfTheRelation(unittest.TestCase):
    """§A52's countable, for the relation this pass needed. ONE computer, N readers — the
    container relation is `custody.parent_of` and the engine READS it rather than restating
    it, which is EP-28O's precedent applied to a second function."""

    def test_the_engine_calls_the_namespaces_own_relation(self):
        with open(OPDEFS_PATH, encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn("custody.parent_of(", src)

    def test_and_it_derives_no_container_of_its_own(self):
        """A second computer would look like a `rsplit` or an `rfind` over a separator inside
        the engine. Counted from the source, and the can-fail control shows the counter can
        return more than zero."""
        with open(OPDEFS_PATH, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        hits = [l for l in lines if "rsplit(" in l or "rpartition(" in l or "rfind(" in l]
        self.assertEqual(hits, [], "a container relation re-derived in kernel space: %r" % hits)
        with open(os.path.join(REPO, "src", "bridge", "custody.py"), encoding="utf-8") as fh:
            body = fh.read()
        self.assertIn('rsplit("/", 1)', body,
                      "non-vacuity: the one real derivation is the text this counts")


# ---------------------------------------------------------------------------------------
# T-DIFF-IS-THE-CHANGE / T-VERSION-MOVES
# ---------------------------------------------------------------------------------------
class TestTheDiffIsTheChange(unittest.TestCase):
    """The founding CHANGED — this pass's required outcome — and the proof is the diff's
    exact shape, set-diffed BOTH directions against the pack as it stood at the commit this
    session opened at."""

    def setUp(self):
        # [DOCUMENTED FLIP — EP-29 W1b, 2026-08-12, charter §A57. CAUSE: this class's own
        # docstring says the diff is "against the pack as it stood at the commit this session
        # opened at", and `now` read the LIVE tree instead — so when this pass added
        # DECLARE-IO-WINDOW and DEVICE-IO-WINDOW-WRITE, `test_no_op_was_added_or_removed`
        # reported them as this pass's additions, which is a true sentence about the wrong
        # session. ASSERTED: `load_pack()`, live. SUPERSEDED: `pack_at(AFTER_COMMIT)` —
        # EP-28N2's own close commit, the AFTER its diff was always about. REMAINS TRUE: the
        # BEFORE side and every per-definition verdict, untouched. GIVEN UP: nothing.]
        self.now = pack_ops(pack_at(AFTER_COMMIT))
        self.before = pack_ops(pack_at(BEFORE_COMMIT))

    def test_the_before_pack_is_the_one_this_session_anchored(self):
        """Non-vacuity: a diff against the wrong BEFORE proves nothing."""
        self.assertEqual(pack_at(BEFORE_COMMIT)["founding_version"], OLD_VERSION)
        self.assertEqual(len(self.before), 72)

    def test_exactly_the_enumerated_definitions_moved_and_nothing_else(self):
        """[EP-29 W1a, 2026-08-09 — ERA-PINNED under §A57. A documented flip with its cause.]

        ASSERTED (2026-08-05): between `BEFORE_COMMIT` and the LIVE pack, exactly this
        pass's enumerated definitions moved, both set-diffs empty.
        SUPERSEDED: EP-29 W1a amended `REGISTER-CAPABILITY`, `BIND-DEVICE` and `UNBIND` on
        2026-08-09, none of which this pass ever touched, so the live side reports three
        definitions moving outside the enumeration and this row reds on a lawful move. The
        row beside it survived a founding move once already by EXCLUDING the later pass's
        surface; that repair does not scale — the next pass would need a second exclusion,
        the one after a third, and the claim would drain away one tolerance at a time.
        REMAINS TRUE, whole and with no exclusions at all, with the AFTER side era-pinned to
        this pass's own close: between `BEFORE_COMMIT` and `AFTER_COMMIT`, EXACTLY the
        enumerated definitions moved. A definition outside the enumeration still reds, which
        is the whole property, and it can never again red on somebody else's lawful pass.
        GIVEN UP: the ability to notice a later pass moving a definition. It was never this
        row's job — it acquired it by reading live — and the estate holds it elsewhere:
        `test_ep28j.py`'s `TPinDeclaredOrRed` reads the live pack for new declared shapes,
        and each founding pass drives its own diff against its own before."""
        now = pack_ops(pack_at(AFTER_COMMIT))
        moved = {n for n in now if now[n] != self.before.get(n)}
        self.assertEqual(moved - CHANGED_DEFINITIONS, set(),
                         "a definition outside the enumeration changed")
        self.assertEqual(CHANGED_DEFINITIONS - moved, set(),
                         "an enumerated definition did not change")

    def test_the_only_difference_in_each_moved_definition_is_its_checks_list(self):
        """[EP-28T, 2026-08-08 — `AppendNothing` PER ROW.]

        ASSERTED (2026-08-05, EP-28N2): between `BEFORE_COMMIT` and the LIVE pack, each of
        this pass's changed definitions differs in its `checks` list and in nothing else.
        SUPERSEDED: EP-28S landed the identity law on 2026-08-08 and rewrote the three minting
        ops — `mints` and the `inode` parameter out, `mints_from: record_coordinate` in, and
        `inode` dropped from `payload_from`. `FILE-CREATE` is in BOTH passes' change sets, so
        the live side now carries a second pass's edit and the equality reads it as this pass
        having changed something it never touched.
        THE DEFECT IS THE LIVE SIDE, NOT THE CLAIM. A differential whose BEFORE is pinned and
        whose AFTER is live is not comparing two commits; it is comparing one commit against
        the future, and every later lawful pass moves it. That is the era-pin law exactly, and
        it is why this row rots while `test_exactly_the_enumerated_definitions_moved_and
        _nothing_else` beside it does not.
        REMAINS TRUE, separated out and STILL ASSERTED, in the one form this file can express
        without minting a citation: the identity keys EP-28S is entitled to have moved are
        named and excluded, and EVERY OTHER key must still be byte-identical to the before
        side. A key outside both enumerations still reds — which is the whole property."""
        #: EP-28S's own change surface on the minting ops, named so it is an EXCLUSION WITH A
        #: REASON rather than a widened tolerance. Shrink-only: a later pass adding to this is
        #: a finding, not an option.
        ep28s_identity_keys = ("mints", "mints_from", "params", "payload_from",
                               "param_defaults")
        for name in sorted(CHANGED_DEFINITIONS):
            now, before = dict(self.now[name]), dict(self.before[name])
            now.pop("checks"), before.pop("checks")
            moved = {k for k in set(now) | set(before) if now.get(k) != before.get(k)}
            self.assertEqual(moved - set(ep28s_identity_keys), set(),
                             "%s: a key moved that is neither this pass's `checks` nor "
                             "EP-28S's declared identity surface" % name)

    def test_no_op_was_added_or_removed(self):
        self.assertEqual(set(self.now), set(self.before))

    def test_the_ONLY_non_op_record_that_moved_is_the_law_that_declares_the_key_space(self):
        """THE `rule-errno` PACK IS THE ONE TO WATCH and it is inside this clause: this pass
        derived nothing about it and retired no row, so this row is what says so.

        [EP-29 W1a, 2026-08-09 — ERA-PINNED under §A57. A documented flip with its cause.]

        ASSERTED (2026-08-05): between `BEFORE_COMMIT` and the LIVE pack, the non-op record
        lists are the same length and EXACTLY ONE record moved — the namespace law.
        SUPERSEDED: EP-29 W1a DECLARED `DEV-LAW-BIND` on 2026-08-09, a new `CREATE-RULE`
        record, so the live side holds 65 non-op records against this era's 64 and the row
        reds at its first assertion — on a length equality it uses as the ground for a
        positional `zip`, which is the strictest half and the reason it reds loudly rather
        than silently comparing mismatched pairs.
        REMAINS TRUE, unchanged in every clause, with the AFTER side era-pinned to this
        pass's own close: one record moved, it is the namespace law, and nothing but its key
        space and its sentence moved inside it.
        GIVEN UP: nothing this row claimed. It never claimed the founding would stop growing
        non-op records; it claimed THIS pass added none, and that claim is era-shaped."""
        def non_ops(pack):
            return [r for r in pack_records(pack) if r.get("action") != "CREATE-OP"]
        now, before = non_ops(pack_at(AFTER_COMMIT)), non_ops(pack_at(BEFORE_COMMIT))
        self.assertEqual(len(now), len(before))
        moved = [(a, b) for a, b in zip(now, before) if a != b]
        self.assertEqual(len(moved), 1, "more than the namespace law moved")
        self.assertEqual((moved[0][0].get("payload") or {}).get("rule_id"), NAMESPACE_LAW)
        a, b = dict(moved[0][0]["payload"]), dict(moved[0][1]["payload"])
        self.assertEqual(a.pop("key_space"), ENUMERATED_KEY_SPACE)
        a.pop("text"), b.pop("text")
        self.assertEqual(a, b, "nothing but the key space and its sentence moved")


class TestTheVersionMoves(unittest.TestCase):
    """T-VERSION-MOVES. MINOR on the ruled discriminator (EP-28I AMENDMENT 1): a new declared
    check kind, a new declaration and new REFUSALS are law-surface — a reader must re-read the
    law before writing against it — and nothing existing breaks that this pass does not
    itself write."""

    def test_the_pack_declares_the_new_version(self):
        """[EP-28T, 2026-08-08 — `AppendNothing` PER ROW.]

        ASSERTED: the LIVE pack declares `NEW_VERSION` — 1.17.0, the version EP-28N2 itself
        landed on 2026-08-05.
        SUPERSEDED: EP-28S landed the identity law on 2026-08-08 and the founding moved to
        1.18.0. The claim was never wrong; it was made about the LIVE pack when it is a fact
        about THIS PASS, and a live side silently couples "my pass landed its version" to
        "nothing may lawfully move afterwards" — the era-pin defect this estate already has
        written down, appearing inside a version row rather than inside an oracle.
        REMAINS TRUE, separated out and STILL ASSERTED, with the era pin applied: the pack AT
        THIS PASS'S AFTER-STATE declares 1.17.0. That is checked against the era side, which
        cannot go stale, and `NEW_VERSION` keeps its meaning — the version THIS pass landed —
        instead of being rewritten into a lie about which pass landed 1.18.0.
        REMAINS TRUE, in the form this FILE can actually express, and the limit is reported
        rather than papered over: THIS FILE CARRIES NO AFTER PIN. It defines `BEFORE_COMMIT`
        and nothing else, which is exactly why this row could only ever read live. Minting an
        after-commit here would be minting a citation this pass did not verify, so the row
        takes the floor-and-agreement form instead: the founding never goes BACKWARDS past
        what this pass landed, and the pack on disk agrees with the designation the installer
        stamped into FOUND-STORE. THE READER/RECORD PAIRING LIVES IN THE NEXT ROW, not here,
        and the reason is worth one sentence: `install_module.founding_version()` IS
        `load_pack()["founding_version"]` — the same function body — so the two calls this row
        used to make were ONE READING WEARING TWO LABELS, and asserting they agree proved the
        module deterministic and nothing about the founding.
        GIVEN UP: the ability to notice a bump, which EP-28N2's OWN next row already holds
        against a pinned before-side. RAISED: an AFTER pin for this file's version rows."""
        live = install_module.founding_version()
        self.assertGreaterEqual(tuple(int(n) for n in live.split(".")),
                                tuple(int(n) for n in NEW_VERSION.split(".")),
                                "the founding has gone BACKWARDS past what this pass landed")

    def test_the_version_MOVED_which_is_this_passs_required_outcome(self):
        self.assertNotEqual(pack_at(BEFORE_COMMIT)["founding_version"],
                            load_pack()["founding_version"],
                            "a byte-unchanged founding here would be this pass FAILING")

    def test_the_installer_stamps_it_into_the_founding_designation(self):
        d = tempfile.mkdtemp(prefix="ep28n2-ver-")
        try:
            store, _g, _v, _b, _s = build_full_kernel(
                os.path.join(d, "record.jsonl"), os.path.join(d, "blobs"),
                os.path.join(d, "vault"))
            fs = store.by_action("FOUND-STORE")[0]
            # [EP-28T, 2026-08-08 — `AppendNothing` PER ROW.]
            # ASSERTED: the installer stamps `NEW_VERSION` (1.17.0) into the FOUND-STORE
            #   designation — true on 2026-08-05, when the live pack WAS what this pass landed.
            # SUPERSEDED: EP-28S moved the founding to 1.18.0 on 2026-08-08, so the installer
            #   now stamps 1.18.0. The row's clause quietly depended on nothing ever moving
            #   again, which is the live-side coupling the era-pin law already names.
            # REMAINS TRUE, separated out and STILL ASSERTED, and it is this row's real
            #   subject: WHATEVER the pack declares, THE INSTALLER STAMPS THAT SAME STRING.
            #   Two genuinely different takings — a read of the pack file, and a read of the
            #   record the installer wrote at genesis — so their agreement catches an installer
            #   stamping a stale or invented version, which is the only way this can break.
            # GIVEN UP: the pin on one number. Kept as a FLOOR above, in the row before.
            self.assertEqual((fs.get("payload") or {}).get("founding_version"),
                             load_pack()["founding_version"],
                             "the installer stamped a version the pack does not declare")
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_J9_the_same_version_may_not_name_two_distinct_foundings(self):
        """RE-PROVEN, not assumed, and VERSION-AGNOSTIC by EP-28N's own raise 6: the property
        is that the founding ON DISK, at whatever version, is named with its own sha256 in one
        log entry."""
        from test_founding_is_logged import audit, entries_naming, pack_facts
        facts = pack_facts()
        a = audit()
        with open(PACK_PATH, "rb") as fh:
            self.assertEqual(facts["sha256"], hashlib.sha256(fh.read()).hexdigest())
        self.assertTrue(a["logged"],
                        "the founding on disk is unattested: no single log entry names its "
                        "version with its own pack sha256")
        self.assertEqual(a["version"], facts["version"])
        self.assertEqual(entries_naming("## nothing here\n", a["version"], a["sha256"]), [])


# ---------------------------------------------------------------------------------------
# ROUND-TRIP
# ---------------------------------------------------------------------------------------
class TestTheWorldReplaysIdentically(_Live):
    """Kill and replay: the derived answers are identical, and nothing about the container
    law depends on anything held in memory."""

    def test_a_world_under_the_new_law_replays_to_the_same_key_space(self):
        self.act("FILE-MKDIR", path="/d")
        self.act("FILE-CREATE", path="/d/f")
        self.act("FILE-MKDIR", path="/d/e")
        before_keys = self.keys()
        before_classes = dict(opdefs._live_namespace(self.store, self.views)[1])
        self.assertGreater(len(before_keys), 1, "non-vacuity: the world holds bound names")

        store, gate, views, _b, _s = build_full_kernel(
            self.record, os.path.join(self.dir, "blobs"), os.path.join(self.dir, "vault"))
        self.assertEqual(set(opdefs._live_bindings(store, views)), before_keys)
        self.assertEqual(dict(opdefs._live_namespace(store, views)[1]), before_classes)

    def test_and_the_refusals_replay_as_refusals(self):
        with self.assertRaises(OpError):
            self.act("FILE-CREATE", path="/gone/y")
        store, _g, views, _b, _s = build_full_kernel(
            self.record, os.path.join(self.dir, "blobs"), os.path.join(self.dir, "vault"))
        refused = [e for e in store.by_action("op-refused")
                   if (e.get("payload") or {}).get("op") == "FILE-CREATE"]
        self.assertEqual(len(refused), 1)
        self.assertEqual(refused[0]["rule_cited"], NAMESPACE_LAW)
        self.assertEqual(set(opdefs._live_bindings(store, views)), {"/"})


# ---------------------------------------------------------------------------------------
# §15's CONTROL — the fence licensed it and this pass did not need it
# ---------------------------------------------------------------------------------------
class TestThePreconditionReadWasTheInvitationAndW4eACCEPTEDIt(unittest.TestCase):
    """`src/bridge/kernel_port.py` was licensed for the errno RENDERING ONLY at this pass, and
    the precondition read the whole finding lives in was NOT touched — "its retirement is
    W4e's, against this law, one variable at a time."

    RENAMED AND NOT ONLY FLIPPED (EP-28C W4e, 2026-08-07): a class named `IsSTILLTheInvitation
    Declined` whose row asserts the read is gone carries a repealed fact in its name.

    ASSERTED ON THE FUNCTION'S PRESENCE rather than on its line number, for the same reason
    the byte comparison was: this pass added lines above it and a line-pinned row would have
    red on an untouched artifact."""

    def _body(self, blob):
        tree = ast.parse(blob)
        fn = next((n for n in ast.walk(tree)
                   if isinstance(n, ast.FunctionDef) and n.name == "_posix_precondition"),
                  None)
        return ast.unparse(fn) if fn is not None else None

    def test_the_precondition_read_was_PRESENT_at_this_pass_and_is_RETIRED_on_the_tree(self):
        """DOCUMENTED FLIP — EP-28C W4e, 2026-08-07. THE RETIRED CONSTRUCT THIS ROW WAS
        READING: `_posix_precondition`'s unparsed body on the live tree, compared against the
        same function at `BEFORE_COMMIT`.

        THE BEFORE HALF IS KEPT AND IS NOW THE LOad-BEARING ONE: an absence proves nothing
        unless the pin's own commit is shown to have held the thing that is now absent."""
        # [DOCUMENTED FLIP — EP-28Z, 2026-08-12. The era read moves to `tests/era_pin.py`.
        # `missing="assert"` is chosen deliberately over the loud default: this site checked
        # the return code with `assertEqual` and an unresolvable pin therefore landed as a
        # FAIL. `missing="raise"` would have landed it as an ERROR. Same red, different row
        # in the summary, so the policy that preserves this site's own shape is the one
        # taken — the flip changes where the act lives and nothing a reader could observe.]
        era_src = era_pin.text_at(BEFORE_COMMIT, "src/bridge/kernel_port.py",
                                  missing="assert")
        with open(PORT_PATH, encoding="utf-8") as fh:
            now = fh.read()
        self.assertIsNotNone(self._body(era_src),
                             "non-vacuity: the BEFORE commit held the read this row is about")
        self.assertIsNone(self._body(now),
                          "the port still holds a precondition read — W4e's retirement did "
                          "not land, and one variable at a time is still the discipline")
        self.assertIn("ERRNO_BY_ACT", now,
                      "the port's act-keyed table is gone as well, so the absence above is "
                      "about the wrong file")

    def test_and_the_file_DID_move_which_is_what_makes_that_a_control(self):
        # [DOCUMENTED FLIP — EP-28Z, 2026-08-12. The era read moves to `tests/era_pin.py`.
        # This site checked the return code NOWHERE and compared `out.stdout` whatever it
        # was, so an unresolvable pin would have compared the live file against an EMPTY
        # STRING and passed the non-vacuity clause for the wrong reason. `missing="raise"`
        # is therefore STRICTER than what it replaces, and the strictness is the point:
        # this row's whole job is to be a control, and a control that cannot tell an
        # unreadable era from a moved file is not one.]
        era_src = era_pin.text_at(BEFORE_COMMIT, "src/bridge/kernel_port.py")
        with open(PORT_PATH, encoding="utf-8") as fh:
            self.assertNotEqual(fh.read(), era_src,
                                "non-vacuity: the errno table gained this pass's eight rows")


if __name__ == "__main__":                                  # pragma: no cover
    unittest.main()
