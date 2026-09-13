"""EP-28N — the precondition class at FULL WIDTH, and the two keys separated by law.

Every probe here is a regression test (the campaign method: a verification probe lands as
a test).

WHAT THIS PASS DECIDES. EP-28K read nineteen (op, outcome) pairs out of the port's
`_posix_precondition` and declared EIGHT of them as law. The remaining ELEVEN are decided
here, as ONE CLASS and in one authoring — never one member at a time, which is how a
convention gets built instead of a rule (ADDENDUM I.2's family).

THE PARTITION THAT DECIDES IS NOT THE ONE THAT WAS INHERITED, and that is this pass's
central finding. EP-28K partitioned the eleven by the QUESTION each asks — existence of a
derived key (3), or a node's KIND / a container's CONTENTS (8). Re-derived from the port's
AST here, the partition that actually decides is by KEY SPACE:

  * THREE members ask about a key THE OPERATION ALREADY TAKES — `FILE-RMDIR`'s ENOTDIR and
    `FILE-UNLINK`'s EISDIR over `path`, `FILE-LINK`'s EPERM over `target_param`. The law can
    name that key, so these three become a declared `kind` check, and the pass lands them.
  * EIGHT members ask about a key THE ENGINE CANNOT COMPUTE — six about `parent_of(path)`
    and two about `contains(key)`. Both are HIERARCHY over the law's key space, and that key
    space is measured UNNORMALISED (EP-28K's own committed row: `/a` and `/a/` are two keys
    to the law and one name to the namespace fold). A hierarchy relation built over an
    unnormalised key space answers wrongly in exactly the cases already measured as
    divergent, and normalising the key space is a CHANGE to EP-28K's landed law rather than
    an addition to it. So the eight are blocked by ONE fact, that fact is measured rather
    than argued, and they are RAISED with their arithmetic.
    [SUPERSEDED IN ITS SECOND HALF, 2026-08-05, EP-28O — kept because it is the record of
    what blocked the eight and of the raise that unblocked them. The dispositions below are
    UNCHANGED: this pass declared no hierarchy check and EP-28O declares none either. What
    changed is the reason — the law's key derivation now calls the namespace fold's own
    `_norm`, so the key space is normalised and the eight wait on an AUTHORING rather than on
    a key space that could not carry them. The two rows in this file that measured the
    unnormalised space are flipped in place and say so.]

THE TWO KEYS. A refusal's RECORD is keyed by the RULE (`FS-LAW-NAMESPACE` governs a refused
create and a refused unlink of an absent name alike). The PORT's errno is keyed by the ACT:
a refused create is EEXIST and a refused unlink of an absent name is ENOENT, so no row in a
rule-keyed map could ever be right for both. `ERRNO_BY_RULE` was wrong-layer-wrong-key and
not missing a row; `ERRNO_BY_ACT` replaces its port job with ELEVEN rows that the old key
would have collapsed into ONE.

THE NAMED WRONG REFERENCES THIS BATTERY REFUSES.
  1. LAW-SHOPPING (§A56), and its tell is that it is GREEN. `TestTheTwoKeys` asserts the
     citation and the errno INDEPENDENTLY, so a citation chosen for the errno it produces
     greens one clause and reds the other — exhibited as output against a pre-fix
     rule-keyed renderer, which is the world §A56 was found in.
  2. STORING THE CHAIN. `TestTheChainIsComputed` — no chain field in any record schema;
     kill, replay, the derived chains identical; and the CROSS-ERA arm, which is the row.
  3. GROWING THE MAP. An `FS-LAW-NAMESPACE -> <errno>` row would be wrong for one of its
     two acts whichever value it took. `ERRNO_BY_RULE` gains NO row, asserted.
  4. PER-MEMBER DRIFT. One authoring, one class decision, one set-diff — in `setUp`, so a
     drift reds before any disposition is read (§A48).

Coverage (the EP's named battery):
  T-CLASS-DECIDED          the nineteen re-derived from the port's AST in `setUp` and
                           set-diffed against EP-28K's committed table BOTH directions; the
                           eleven each carry a disposition and the dispositioned set equals
                           the eleven exactly.
  T-REFUSAL-CITES-TIP-RULE every rejection of a performed action appends a refusal citing
                           the TERMINAL rule, driven on two members including the least
                           likely.
  T-TWO-KEYS               one refused world per act class: the record carries the rule
                           while the port returns the ACT's errno, asserted independently.
  T-CHAIN-COMPUTED         the chain derives from the tip citation at read time, with the
                           CROSS-ERA arm and its non-vacuity clause.
  T-ABSENCE-STAYS          ops declaring no check keep design/10 §11.1a's classification,
                           asserted as a set over this pass's landed set.
  T-GUARD-AT-THREE-DOORS   the new kind malformed, or absent where the enumeration requires
                           it, refuses at the installer, at CREATE-OP and at AMEND-OP.
  T-DIFF-IS-THE-CHANGE     the founding diff equals the declared change list exactly, both
                           directions, against the BEFORE taken at this session's start.
  T-VERSION-MOVES          `founding_version` reads 1.16.0; J9 re-proven.
"""
import ast
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
from collections.abc import Mapping

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO, "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import era_pin                                                    # noqa: E402  (the era-pin home, EP-28Z)
from founding import install as install_module                    # noqa: E402
from founding.install import (                                    # noqa: E402
    FoundingIntegrityError, _validate, load_pack, records as _records,
)
from bridge import custody                                        # noqa: E402
from kernel import opdefs                                         # noqa: E402
from kernel.compose import build_full_kernel                      # noqa: E402
from kernel.errors import OpError                                 # noqa: E402

#: EP-28K's committed enumeration, IMPORTED FROM ITS OWN FILE rather than copied here. A
#: copy would let the two drift apart silently, and the whole point of the set-diff below is
#: that a drift reds. This is the only thing this battery takes from that one.
from test_ep28k import PORT_OUTCOMES as K_COMMITTED                # noqa: E402

OWNER = "owner"
PACK_PATH = os.path.join(REPO, "src", "founding", "founding-pack.json")
PORT_PATH = os.path.join(REPO, "src", "bridge", "kernel_port.py")

#: The port-shaped provenance four of the seven namespace ops REQUIRE.
PROV = {"uid": 1000, "gid": 1000, "pid": 42, "window": "test"}

#: [RENAMED 2026-08-15, NOT REVALUED — board :836. The four era-pin constants in this block
#: were spelled `NEW_VERSION`, `OLD_VERSION`, `AFTER_COMMIT` and `BEFORE_COMMIT`; the old
#: spellings are written here so a grep for any of them still lands on the thing it names.
#: NOT ONE VALUE MOVED — `1.16.0`, `1.15.0`, `61f38d8` and `28b1070` are byte-identical to
#: what those four names held, and the rename was proved by subtracting itself from the
#: pre-write blob and finding the residue is this comment.
#:
#: THE DEFECT WAS IN-FILE AMBIGUITY, NOT A WRONG ASSERTION. Nothing reddened and no row was
#: wrong. THIS FILE NAMES FOUR FOUNDINGS — 1.13.0, 1.14.0, 1.15.0 and 1.16.0, all four in one
#: list inside `test_THE_FOUNDING_HISTORY_ALONE_CANNOT_DRIVE_THIS_and_that_is_MEASURED` —
#: while a name like `AFTER_COMMIT` says only that it is after SOMETHING. A reader meeting
#: `pack_at(AFTER_COMMIT)` as the fourth entry of a four-era list could not tell WHICH of the
#: four transitions it belonged to without chasing the constant out of the row. The names now
#: carry their transition, so the row can be read where it stands.
#:
#: THE SPELLING IS DERIVED FROM THIS ESTATE'S OWN CONVENTION AND NOT INVENTED. Every era pin
#: in `tests/test_ep29.py` is `<UNIT>_BEFORE_COMMIT` / `<UNIT>_BEFORE_VERSION` /
#: `<UNIT>_AFTER_VERSION` / `<UNIT>_AFTER_COMMIT`, over the unit designations `W1A_`, `W1B_`,
#: `W2B_`, `W3A_` and `W3A3_`. That file is one EP holding many units, so its designation is
#: the sub-unit; THIS file is ONE unit whose designation is EP-28N, spelled `EP28N_` because a
#: hyphen is not an identifier character. `OLD`/`NEW` became `BEFORE`/`AFTER` by the same
#: precedent and for the same reason: a version and a commit on the same side are ONE era pin
#: and now read as one.
#:
#: WHICH TRANSITION THEY NAME WAS ESTABLISHED BY READING THE CONSUMERS, never assumed from
#: this file's name. All twenty consumers belong to EP-28N's own 1.15.0 -> 1.16.0 move, and
#: two clauses in `TestTheDiffIsTheChange` assert the pairing outright rather than leaving it
#: to the reader. No consumer disagreed with another; had one, it would have been a raise.]
EP28N_AFTER_VERSION = "1.16.0"
EP28N_BEFORE_VERSION = "1.15.0"

#: THE COMMIT THIS PASS CLOSED AT — the AFTER side of its own founding diff, pinned by
#: EP-28N AMENDMENT 1 under §A57's backward obligation [documented flip]. The rows below read
#: the LIVE pack, so they asserted what the founding IS rather than what THIS PASS moved it
#: to, and the next lawful move reddened them for describing an accepted past correctly. The
#: first commit whose `src/founding` tree is the `7f4447e0…` this pass's close recorded,
#: found by walking the history rather than by being told.
EP28N_AFTER_COMMIT = "61f38d8"

#: THE COMMIT THIS PASS OPENED AT — the BEFORE side of the founding diff, pinned so the row
#: compares against a fixed artifact rather than against whatever HEAD holds (§A53: HEAD
#: moves under a session because the timer commits, and cleanliness is judged from
#: `git status`).
EP28N_BEFORE_COMMIT = "28b1070"

NAMESPACE_LAW = "FS-LAW-NAMESPACE"

#: THE ELEVEN THIS PASS OWNS, one verdict each, decided in one authoring.
#:
#:   DECLARED-KIND   the question is about a key THE OP ALREADY TAKES, so the law can name
#:                   it. Lands as a `kind` check row.
#:   HIERARCHY       the question is about `parent_of(key)` or `contains(key)`. Both need a
#:                   hierarchy relation over the law's key space; that key space was measured
#:                   unnormalised at this pass, so the relation would have answered wrongly in
#:                   exactly the cases already measured as divergent. RAISED with its
#:                   arithmetic, not taken — and the raise was taken up by EP-28O, which
#:                   normalised the key space. The verdicts here are the record of THIS
#:                   pass's decision and do not move.
THIS_PASS_DISPOSITIONS = {
    ("FILE-CREATE",  "ENOENT"):    ("HIERARCHY", "parent_of(path)"),
    ("FILE-MKDIR",   "ENOENT"):    ("HIERARCHY", "parent_of(path)"),
    ("FILE-SYMLINK", "ENOENT"):    ("HIERARCHY", "parent_of(path)"),
    ("FILE-CREATE",  "ENOTDIR"):   ("HIERARCHY", "parent_of(path)"),
    ("FILE-MKDIR",   "ENOTDIR"):   ("HIERARCHY", "parent_of(path)"),
    ("FILE-SYMLINK", "ENOTDIR"):   ("HIERARCHY", "parent_of(path)"),
    ("FILE-RMDIR",   "ENOTEMPTY"): ("HIERARCHY", "contains(path)"),
    ("FILE-RENAME",  "ENOTEMPTY"): ("HIERARCHY", "contains(new_path)"),
    ("FILE-RMDIR",   "ENOTDIR"):   ("DECLARED-KIND", "path"),
    ("FILE-UNLINK",  "EISDIR"):    ("DECLARED-KIND", "path"),
    ("FILE-LINK",    "EPERM"):     ("DECLARED-KIND", "target_path"),
}

#: THE KIND ROWS THIS PASS DECLARES, per op, in declaration order — which is load-bearing:
#: the interpreter runs an op's checks in it, so `FILE-RMDIR` answers "the name is not
#: there" before "the name is not a directory", and `FILE-LINK` answers about its target
#: before its new name, exactly as the port's own branch order does.
ENUMERATED_KIND_ROWS = {
    "FILE-RMDIR":  [("path", "dir", None)],
    "FILE-UNLINK": [("path", None, "dir")],
    "FILE-LINK":   [("target_path", None, "dir")],
}

#: WHAT KIND EACH BINDING ACT GIVES THE KEY IT BINDS. Read from the declarations by the
#: fold; enumerated here so the reading is a claim the pre-flight can re-derive.
ENUMERATED_BINDS_KIND = {
    "FILE-CREATE":  {"param": "node_type"},
    "FILE-MKDIR":   {"literal": "dir"},
    "FILE-SYMLINK": {"literal": "link"},
    "FILE-RENAME":  {"from_key": "path"},
    "FILE-LINK":    {"from_key": "target_path"},
}

CHANGED_DEFINITIONS = set(ENUMERATED_KIND_ROWS) | set(ENUMERATED_BINDS_KIND)


# ---- the enumeration, re-derived from the port's own AST -----------------------------
# `_ops_of_test` STOOD HERE AND IS REMOVED WITH ITS SUBJECT (EP-28C W4e, 2026-08-07). It read
# the op names an `if` test admits — `op == "X"` or `op in ("X", "Y")` — so that an
# unrecognised guard could never be read as "all ops" or "no ops" by accident. Its only
# caller was the walk over `_posix_precondition`'s branches, and that function is retired.
# THE PROTECTION IT SUPPLIED DID NOT GO WITH IT: the same failure — a member the walk cannot
# attribute being silently attributed — is `enumerate_pairs`'s third return value below,
# which reports any act-keyed row whose key does not name an operation.


def enumerate_pairs():
    """(pairs, rows, unattributable) READ FROM THE PORT'S `ERRNO_BY_ACT` AST.

    DOCUMENTED FLIP — EP-28C W4e, 2026-08-07. THE RETIRED CONSTRUCT THIS WALK WAS READING:
    `_posix_precondition`'s body, walked for every `return -errno.X` and attributed to the
    ops of its enclosing `if op ==` / `if op in` guard. THAT FUNCTION IS RETIRED. This pass
    declared eleven of its outcomes as law, EP-28K had declared eight before it, EP-28N
    AMENDMENT 1 completed the container rows, and W4e removed the read once every one of the
    nineteen had a declared check behind it.

    THE POPULATION SURVIVES THE FUNCTION. It lives in the port's other structural
    enumeration — `ERRNO_BY_ACT`, one row per (op, requirement) carrying the errno that act
    renders — and this walks that dict's AST. Same nineteen pairs over the same seven ops,
    still read from the port's own source and never from a list anybody wrote down,
    including EP-28K's, this file's, and the mentor's. Each row now also carries WHICH
    REQUIREMENT it is about, which a bare `return -errno.EEXIST` never said.

    THE THIRD ELEMENT KEEPS ITS JOB AND CHANGES ITS SUBJECT. `unguarded` reported a return
    outside every op guard — one that would serve EVERY op, so a table swallowing it would
    understate the class. Its equivalent here is a table row whose key names no operation:
    anything that is not a two-element tuple of string constants. Reported the same way
    rather than dropped, because the hazard is identical — a member the walk cannot
    attribute must never be silently attributed."""
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


def kind_rows(definition):
    return [(c.get("key_param"), c.get("require"), c.get("forbid"))
            for c in (definition.get("checks") or []) if c.get("check") == "kind"]


def binding_rows(definition):
    return [c for c in (definition.get("checks") or []) if c.get("check") == "binding"]


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


class TestTheClassIsDecided(unittest.TestCase):
    """T-CLASS-DECIDED.

    THE PLACEMENT IS THE CLAUSE (§A48). The re-derivation and the set-diff run in `setUp`,
    not as a sibling row, because `unittest` orders methods alphabetically and a precedence
    stated in prose is void: a drift in the port's enumeration must red BEFORE any
    disposition is read, and the framework guarantees that only for `setUp`."""

    def setUp(self):
        pairs, rows, unattributable = enumerate_pairs()
        self.assertEqual(unattributable, [],
                         "an act-keyed row names no operation, so it cannot be attributed "
                         "and this enumeration would understate the class")
        self.pairs = pairs
        self.returns = rows
        committed = {(op, e) for op, e, _k, _d in K_COMMITTED}
        derived = set(pairs)
        self.assertEqual(derived - committed, set(),
                         "the port's AST holds a pair EP-28K's committed table does not")
        self.assertEqual(committed - derived, set(),
                         "EP-28K's committed table holds a pair the port's AST does not")
        self.k_declared = {(op, e) for op, e, _k, d in K_COMMITTED if d == "DECLARED"}
        self.remaining = committed - self.k_declared

    def test_the_mechanical_counts_are_what_the_reading_found(self):
        """NINETEEN act-keyed rows over SEVEN ops over SEVEN requirements.

        DOCUMENTED FLIP — EP-28C W4e, 2026-08-07. THE RETIRED CONSTRUCT THIS ROW WAS READING:
        the count of return points inside `_posix_precondition`. It read "THIRTEEN return
        points in code serving NINETEEN (op, outcome) pairs over SEVEN ops — asserted
        separately, because the code count alone hides an op (one branch serves the three
        create-family ops) and the pair count alone hides a shared branch."

        THIRTEEN WAS THE SHAPE OF THE RETIRED FUNCTION'S BODY and dies with it. What the
        separate countables BOUGHT does not die and is rebuilt: two numbers that move
        independently, so neither a shared member nor a missing one can hide behind the
        other. The surviving second countable is the REQUIREMENT set — `binding:unbound`
        serves four ops here exactly as one branch served three there."""
        self.assertEqual(len(self.returns), 19, self.returns)
        self.assertEqual(len(set(self.pairs)), 19)
        self.assertEqual(len({op for op, _e in self.pairs}), 7)
        self.assertEqual(len({r for _n, r, _l in self.returns}), 7,
                         "the requirement set is the countable that can move without the "
                         "row count moving, which is what makes the pair evidence")

    def test_the_eleven_this_pass_owns_are_exactly_what_K_left(self):
        self.assertEqual(len(self.k_declared), 8)
        self.assertEqual(len(self.remaining), 11)

    def test_every_one_of_the_eleven_carries_a_disposition_and_the_set_is_exact(self):
        self.assertEqual(set(THIS_PASS_DISPOSITIONS) - self.remaining, set(),
                         "a disposition names a pair this pass does not own")
        self.assertEqual(self.remaining - set(THIS_PASS_DISPOSITIONS), set(),
                         "a pair this pass owns carries no disposition")

    def test_the_dispositions_partition_by_KEY_SPACE_and_the_arithmetic_closes(self):
        tally = {}
        for verdict, _key in THIS_PASS_DISPOSITIONS.values():
            tally[verdict] = tally.get(verdict, 0) + 1
        self.assertEqual(tally, {"DECLARED-KIND": 3, "HIERARCHY": 8})
        self.assertEqual(sum(tally.values()), len(self.remaining))

    def test_the_declared_three_ask_about_a_key_their_own_op_takes(self):
        """The discriminator, asserted rather than asserted-about: each DECLARED-KIND
        member's key is a parameter its op actually declares, so the law can name it."""
        ops = pack_ops(pack_at(EP28N_AFTER_COMMIT))
        for (op, _errno), (verdict, key) in THIS_PASS_DISPOSITIONS.items():
            if verdict != "DECLARED-KIND":
                continue
            self.assertIn(key, (ops[op].get("params") or {}), "%s / %s" % (op, key))

    def test_the_hierarchy_eight_ask_about_a_key_no_parameter_carries(self):
        """The other half of the same discriminator. `parent_of(path)` and `contains(key)`
        are RELATIONS over the key space, not parameters, and no op declares one — TRUE AT
        THIS PASS, which is why the pack is read at this pass's own close commit. EP-28N
        AMENDMENT 1 declares all eight as rows whose key is DERIVED from a parameter rather
        than carried by one, which is the shape this row measured the absence of."""
        ops = pack_ops(pack_at(EP28N_AFTER_COMMIT))
        for (op, _errno), (verdict, key) in THIS_PASS_DISPOSITIONS.items():
            if verdict != "HIERARCHY":
                continue
            self.assertTrue(key.startswith("parent_of(") or key.startswith("contains("), key)
            self.assertNotIn(key, (ops[op].get("params") or {}), "%s / %s" % (op, key))

    def test_a_hand_list_double_that_drops_one_pair_reds_on_the_set_clause(self):
        """THE RED WORLD FOR THIS ROW, produced rather than described (§A42): the failure a
        hand-written enumeration has is a silent omission, and the set-diff is what catches
        it. Driven by dropping one member from the derived side and re-running the same
        comparison this row's `setUp` runs."""
        committed = {(op, e) for op, e, _k, _d in K_COMMITTED}
        doubled = set(self.pairs) - {("FILE-LINK", "EPERM")}
        self.assertNotEqual(committed - doubled, set(),
                            "a dropped pair must be visible to the set-diff")


#: DOCUMENTED FLIP (EP-28N AMENDMENT 1, 2026-08-05). Three more ops declare a `kind` row —
#: the create family's container-is-a-directory question — so the pack is read at THIS PASS'S
#: OWN close commit rather than live, by §A57's backward obligation. The three rows below are
#: this pass's and are unchanged; what moved is that they are no longer all of them.
ENUMERATED_KIND_ROWS_AT_THIS_PASS = ENUMERATED_KIND_ROWS


class TestTheKindRowsLanded(unittest.TestCase):
    """The three DECLARED-KIND members, in the founding."""

    def setUp(self):
        self.ops = pack_ops(pack_at(EP28N_AFTER_COMMIT))

    def test_the_kind_rows_equal_the_enumeration_both_directions(self):
        declared = {n: kind_rows(d) for n, d in self.ops.items() if kind_rows(d)}
        self.assertEqual(set(declared) - set(ENUMERATED_KIND_ROWS), set(),
                         "the pack declares a kind check the enumeration did not find")
        self.assertEqual(set(ENUMERATED_KIND_ROWS) - set(declared), set(),
                         "the enumeration found a kind check the pack does not declare")
        for name, rows in ENUMERATED_KIND_ROWS.items():
            self.assertEqual(declared[name], rows, name)

    def test_each_kind_row_sits_after_the_binding_row_over_the_same_key(self):
        """DECLARATION ORDER IS THE ANSWER ORDER. A key that is not bound has no kind, so a
        kind check answering first would report "not a directory" about a name that is not
        there — a true sentence about the wrong question, and the wrong errno at the port."""
        for name, rows in ENUMERATED_KIND_ROWS.items():
            checks = self.ops[name].get("checks") or []
            for key, _req, _forbid in rows:
                bound_at = [i for i, c in enumerate(checks)
                            if c.get("check") == "binding" and c.get("key_param") == key
                            and c.get("require") == "bound"]
                kind_at = [i for i, c in enumerate(checks)
                           if c.get("check") == "kind" and c.get("key_param") == key]
                self.assertTrue(bound_at, "%s declares no bound requirement over %s"
                                % (name, key))
                self.assertLess(bound_at[0], kind_at[0], name)

    def test_every_kind_row_names_a_key_its_op_takes_and_writes(self):
        for name, rows in ENUMERATED_KIND_ROWS.items():
            d = self.ops[name]
            written = d.get("payload_from") or list((d.get("params") or {}).keys())
            for key, _req, _forbid in rows:
                self.assertIn(key, (d.get("params") or {}), "%s / %s" % (name, key))
                self.assertIn(key, written, "%s / %s" % (name, key))

    def test_every_kind_row_cites_the_law_that_governs_the_act(self):
        """§A56, at the declaration rather than at the outcome: the cite is the law the
        NAMESPACE acts are under, and it is the same one EP-28K's binding rows cite. A row
        citing something else would be a citation chosen for what it produces."""
        for name in ENUMERATED_KIND_ROWS:
            for c in (self.ops[name].get("checks") or []):
                if c.get("check") == "kind":
                    self.assertEqual(c.get("cite"), NAMESPACE_LAW, name)
                    self.assertEqual(self.ops[name]["law_cited"], NAMESPACE_LAW, name)

    def test_every_binding_act_that_binds_a_key_says_what_kind_it_binds(self):
        """THE CLASS CLAUSE, not the member list. A bind that declares no kind leaves the
        key kindless, so every later kind check answers about a namespace it is not in —
        silently, and worse the longer it runs. The guard is at the three doors; this row is
        the shipped pack meeting it."""
        for name, d in self.ops.items():
            for c in binding_rows(d):
                if c.get("effect") == "bind":
                    self.assertIn(name, ENUMERATED_BINDS_KIND, name)
                    self.assertEqual(c.get("binds_kind"), ENUMERATED_BINDS_KIND[name], name)

    def test_the_engine_names_no_filesystem_anywhere(self):
        """I5, asserted rather than intended. The kind vocabulary — "dir", "link", "file",
        "fifo" — appears ONLY in law-data. `opdefs.py` compares strings it was handed and
        holds no namespace grammar, exactly as EP-28K left it."""
        with open(os.path.join(REPO, "src", "kernel", "opdefs.py"), encoding="utf-8") as fh:
            src = fh.read()
        tree = ast.parse(src)
        literals = {n.value for n in ast.walk(tree)
                    if isinstance(n, ast.Constant) and isinstance(n.value, str)}
        for word in ("dir", "link", "fifo", "directory", "path", "/"):
            self.assertNotIn(word, literals,
                             "opdefs.py holds the string %r — the engine is naming a "
                             "filesystem" % word)


class TestTheDiffIsTheChange(unittest.TestCase):
    """T-DIFF-IS-THE-CHANGE. The founding CHANGED — this pass's required outcome — and the
    proof is the diff's exact shape, set-diffed BOTH directions against the pack as it stood
    at the commit this session opened at."""

    def setUp(self):
        self.now = pack_ops(pack_at(EP28N_AFTER_COMMIT))       # era-pinned, EP-28N AMENDMENT 1
        self.before = pack_ops(pack_at(EP28N_BEFORE_COMMIT))

    def test_the_before_pack_is_the_one_the_dispatch_anchored(self):
        """Non-vacuity: a diff against the wrong BEFORE proves nothing — and, since the era
        pin, a diff against the wrong AFTER proves nothing either, so both ends are named."""
        self.assertEqual(pack_at(EP28N_BEFORE_COMMIT)["founding_version"], EP28N_BEFORE_VERSION)
        self.assertEqual(pack_at(EP28N_AFTER_COMMIT)["founding_version"], EP28N_AFTER_VERSION)
        self.assertEqual(len(self.before), 72)

    def test_exactly_the_enumerated_definitions_moved_and_nothing_else(self):
        moved = {n for n in self.now if self.now[n] != self.before.get(n)}
        self.assertEqual(moved - CHANGED_DEFINITIONS, set(),
                         "a definition outside the enumeration changed")
        self.assertEqual(CHANGED_DEFINITIONS - moved, set(),
                         "an enumerated definition did not change")

    def test_the_only_difference_in_each_moved_definition_is_its_checks_list(self):
        for name in sorted(CHANGED_DEFINITIONS):
            now, before = dict(self.now[name]), dict(self.before[name])
            now.pop("checks"), before.pop("checks")
            self.assertEqual(now, before, name)

    def test_no_op_was_added_or_removed(self):
        self.assertEqual(set(self.now), set(self.before))

    def test_nothing_outside_the_op_definitions_moved(self):
        """The pack holds rules, packs, views, actors and a grant as well as ops. THE
        `rule-errno` PACK IS THE ONE TO WATCH and it is inside this clause: this pass
        derived its disposition and did NOT retire its namespace row, so this row is what
        says so."""
        def non_ops(pack):
            return [r for r in _records(pack) if r.get("action") != "CREATE-OP"]
        self.assertEqual(non_ops(pack_at(EP28N_AFTER_COMMIT)), non_ops(pack_at(EP28N_BEFORE_COMMIT)))


class _Live(unittest.TestCase):
    """A kernel composed from the SHIPPED founding and nothing else."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep28n-")
        self.record = os.path.join(self.dir, "record.jsonl")
        self.store, self.gate, self.views, self.blobs, self.subs = build_full_kernel(
            self.record, os.path.join(self.dir, "blobs"), os.path.join(self.dir, "vault"))

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def act(self, op, **params):
        params.setdefault("provenance", PROV)
        return self.gate.execute(op, OWNER, params)

    def refusals(self):
        return [e for e in self.store.by_action("op-refused")]


class TestTheVersionMoves(unittest.TestCase):
    """T-VERSION-MOVES. MINOR on the ruled discriminator: a new declared check kind plus a
    new REFUSAL is law-surface — a reader must re-read the law before writing against it —
    and nothing existing breaks, because the ops gain declarations this pass writes.

    ERA-PINNED BY EP-28N AMENDMENT 1 UNDER §A57 [documented flip], by the same idiom and for
    the same reason this pass applied to EP-28K's copy one dispatch ago. The base class went
    with the pin: a pinned document needs no live world to read it."""

    def test_the_pack_declares_the_new_version(self):
        self.assertEqual(pack_at(EP28N_AFTER_COMMIT)["founding_version"], EP28N_AFTER_VERSION)

    def test_the_installer_stamps_it_into_the_founding_designation(self):
        """Driven on a world founded from THIS PASS'S pack, by the era-pinning idiom."""
        era = pack_at(EP28N_AFTER_COMMIT)
        d = tempfile.mkdtemp(prefix="ep28n-ver-")
        saved = install_module.load_pack
        install_module.load_pack = lambda path=None: era
        try:
            store, _g, _v, _b, _s = build_full_kernel(
                os.path.join(d, "record.jsonl"), os.path.join(d, "blobs"),
                os.path.join(d, "vault"))
        finally:
            install_module.load_pack = saved
            shutil.rmtree(d, ignore_errors=True)
        fs = store.by_action("FOUND-STORE")[0]
        self.assertEqual((fs.get("payload") or {}).get("founding_version"), EP28N_AFTER_VERSION)

    def test_J9_the_same_version_may_not_name_two_distinct_foundings(self):
        """RE-PROVEN, not assumed: the guard answers about the bytes on disk rather than
        about a field the pack declares about itself."""
        from test_founding_is_logged import audit, entries_naming, pack_facts
        facts = pack_facts()
        with open(PACK_PATH, "rb") as fh:
            self.assertEqual(facts["sha256"], hashlib.sha256(fh.read()).hexdigest())
        self.assertTrue(audit()["logged"],
                        "the founding moved and no single log entry names both facts")
        self.assertEqual(entries_naming("## nothing here\n", EP28N_AFTER_VERSION, facts["sha256"]), [])


#: THE CHAIN, DERIVED AT READ TIME AND STORED NOWHERE (EP-28N, ruling 1's second half).
#:
#: THE PRECONDITION IS STATED HERE BECAUSE IT IS THE TRUE REASON THE CHAIN IS COMPUTABLE:
#: THE LAW IS ITSELF IN THE APPEND-ONLY RECORD, so the law era at record time is recoverable
#: for any record ever written. "It always traces the same way" is a WEAKER claim — true of
#: this estate today and silently false the day a law enters by a path that is not a record,
#: or the day one law's citation is superseded, which is exactly what the cross-era row below
#: drives. `as_of` is not an optimisation here; it is the whole derivation.
def rule_chain(store, rule_id, as_of=None):
    """From a tip rule to its root, following each rule's OWN recorded citation.

    Nothing new is stored to make this work: every `CREATE-RULE` record already carries the
    rule it was made under, which is the estate's own minimal-primitive method applied to its
    own law. A rule that cites itself is a root and the chain grounds there; a rule with no
    record grounds too, and says so by simply ending."""
    seen, chain = set(), []
    while rule_id is not None and rule_id not in seen:
        seen.add(rule_id)
        chain.append(rule_id)
        recs = [e for e in store.by_action("CREATE-RULE", as_of)
                if (e.get("payload") or {}).get("rule_id") == rule_id]
        if not recs:
            break
        nxt = max(recs, key=lambda e: e["seq"]).get("rule_cited")
        if nxt == rule_id:
            break
        rule_id = nxt
    return chain


def _chain_from_the_LIVE_law(store, rule_id, _as_of=None):
    """THE DOUBLE (§A42). Identical to `rule_chain` in a single-era world and WRONG across
    eras, because it reads the law as it stands now rather than as it stood when the record
    was written. It is unreachable by every single-era clause, which is exactly why the
    cross-era arm exists."""
    return rule_chain(store, rule_id, None)


def is_root(store, rule_id, as_of=None):
    recs = [e for e in store.by_action("CREATE-RULE", as_of)
            if (e.get("payload") or {}).get("rule_id") == rule_id]
    return bool(recs) and (max(recs, key=lambda e: e["seq"]).get("payload") or {}).get("root") is True


class TestTheRefusalCitesTheTipRule(_Live):
    """T-REFUSAL-CITES-TIP-RULE. Every rejection of a performed action APPENDS, and what it
    cites is the TIP-LEVEL TERMINAL RULE: the law that governs the act, at the capillary end
    of the chain rather than anywhere up it.

    §A49 — THE LEAST LIKELY MEMBER IS `FILE-LINK`'s EPERM, AND IT IS DRIVEN. Least likely on
    three counts, each of which is a way it could have been missed: it is the only member of
    the eleven whose POSIX answer is EPERM rather than a namespace errno, so a reader
    pattern-matching on errnos would file it elsewhere; it is the only one whose key is
    neither `path` nor the op's object, so a reading keyed on `path` skips it; and it is
    reachable only in the window after its op's FIRST binding requirement passes and before
    its SECOND is asked, so a row driving one requirement per op never reaches it."""

    def _refuse(self, op, **params):
        with self.assertRaises(OpError) as raised:
            self.act(op, **params)
        return raised.exception, self.store.by_action("op-refused")[-1]

    def _world(self):
        self.act("FILE-MKDIR", path="/d")
        self.act("FILE-CREATE", path="/f")

    def test_all_three_declared_members_append_a_refusal_citing_the_TERMINAL_rule(self):
        self._world()
        before = len(self.store.by_action("op-refused"))
        cases = [("FILE-RMDIR", {"path": "/f"}),                                  # not a dir
                 ("FILE-UNLINK", {"path": "/d"}),                                 # is a dir
                 ("FILE-LINK", {"target_path": "/d", "new_path": "/n"})]          # LEAST LIKELY
        for op, params in cases:
            _err, rec = self._refuse(op, **params)
            self.assertEqual(rec["rule_cited"], NAMESPACE_LAW, op)
            self.assertEqual(rec["rule_cited"],
                             self.views.op_definitions()[op]["definition"]["law_cited"], op)
        self.assertEqual(len(self.store.by_action("op-refused")), before + 3,
                         "non-vacuity: three rejections, three appended refusals")

    def test_the_cited_rule_is_a_TIP_and_not_anywhere_up_the_chain(self):
        """TERMINAL means the capillary end: the cited rule is not itself a root, and the
        chain from it still has somewhere to go. Both halves, because either alone admits
        the citation this pass refuses."""
        self._world()
        _err, rec = self._refuse("FILE-RMDIR", path="/f")
        cited = rec["rule_cited"]
        self.assertFalse(is_root(self.store, cited),
                         "a refusal citing a ROOT law has cited the top of the chain")
        chain = rule_chain(self.store, cited, rec["seq"])
        self.assertEqual(chain[0], cited)
        self.assertGreater(len(chain), 1, "the tip must have somewhere to trace to")
        self.assertTrue(is_root(self.store, chain[-1]), chain)

    def test_A_CHAIN_CITING_DOUBLE_reds_the_tip_clause_and_no_other(self):
        """THE RED WORLD, produced through the real path (§A42). A synthetic namespace op
        whose check cites BOOT-INT — a rule genuinely UP this act's own chain, which is what
        makes it the tempting error rather than an obvious one. The refusal still appends and
        is still cited, so the appending clause and the citing clause both stay green; what
        reds is the TIP clause, and only it."""
        self._world()
        d = {"law_cited": NAMESPACE_LAW, "description": "a chain-citing double",
             "params": {"path": "required"}, "object_param": "path", "payload_from": ["path"],
             # `path`: STRUCTURAL — namespace path, inline shape. ADMIT-intent (this CREATE-OP
             # must succeed; the refusal this row drives is at the ACT's binding check, not the
             # definition door). [design/46 member-2 vocabulary door, archi :2956 RULING 1.]
             "structural_params": ["path"],
             "checks": [{"check": "binding", "key_param": "path", "require": "bound",
                         "cite": "BOOT-INT"}]}
        self.gate.execute("CREATE-OP", OWNER, {"name": "NSDOUBLE", "definition": d})
        before = len(self.store.by_action("op-refused"))
        with self.assertRaises(OpError):
            self.gate.execute("NSDOUBLE", OWNER, {"path": "/gone"})
        rec = self.store.by_action("op-refused")[-1]
        self.assertEqual(len(self.store.by_action("op-refused")), before + 1,
                         "the appending clause is GREEN in the double")
        self.assertIsNotNone(rec["rule_cited"], "the citing clause is GREEN in the double")
        self.assertTrue(is_root(self.store, rec["rule_cited"]),
                        "and the TIP clause is what reds: a root law was cited")
        self.assertEqual(rule_chain(self.store, rec["rule_cited"], rec["seq"]), ["BOOT-INT"],
                         "the chain from a root is one link — there is nowhere to trace")


class TestTheTwoKeys(_Live):
    """T-TWO-KEYS. ONE REFUSED WORLD PER ACT CLASS, with the CITATION and the ERRNO asserted
    INDEPENDENTLY — which is the whole instrument. A citation chosen for the errno it produces
    greens one clause and reds the other, and the split is what makes §A56 visible to a
    machine rather than only to a seat that thought to ask."""

    def setUp(self):
        super().setUp()
        from bridge.kernel_port import KernelPort
        from bridge.mount import build_brain
        self.pdir = tempfile.mkdtemp(prefix="ep28n-port-")
        self.pstore, self.pgate, self.pviews, self.pblobs = build_brain(
            os.path.join(self.pdir, "rec.jsonl"), os.path.join(self.pdir, "blobs"))
        self.port = KernelPort(self.pstore, self.pgate, self.pviews, self.pblobs)

    def tearDown(self):
        shutil.rmtree(self.pdir, ignore_errors=True)
        super().tearDown()

    def wire(self, op, **kw):
        f = {"id": "1", "op": op, "class": "DECISION", "uid": "1000", "gid": "1000",
             "pid": "42"}
        f.update({k: str(v) for k, v in kw.items()})
        return self.port.handle(f, b"")[0]

    def retired(self):
        """W4e's world. It used to be REACHED by suppressing the read; it is now simply the
        world, and this method asserts that rather than simulating it.

        DEFECT FOUND AND FIXED — EP-28C W4e, 2026-08-07, and it is worth naming because no
        instrument could see it. The body was
        `self.port._posix_precondition = lambda op, f: None`. After the retirement that line
        SUCCEEDS: assigning an attribute Python has never heard of is legal, so the helper
        went on binding a stray lambda that nothing calls, the three rows below went on
        passing, and the full-suite inventory of the retirement's blast radius did not list
        this line at all. A monkeypatch whose SUBJECT has gone is invisible in exactly the
        direction that matters — it keeps the row green while the row stops measuring what
        its name says. (The same construct READ rather than written — `real =
        self.port._posix_precondition` in `tests/test_ep28k.py` — raised `AttributeError` and
        was caught immediately. The read is the safe spelling; the write is not.)"""
        assert not hasattr(self.port, "_posix_precondition"), (
            "the port holds a precondition read again, so these rows are measuring the "
            "port's answer and not the law's")

    def test_a_refused_create_carries_the_rule_on_the_record_and_EEXIST_to_the_caller(self):
        import errno as E
        self.assertEqual(self.wire("FILE-CREATE", path="/a"), 0)
        self.retired()
        answer = self.wire("FILE-CREATE", path="/a")
        rec = self.pstore.by_action("op-refused")[-1]
        # CLAUSE ONE — the RECORD, keyed by the RULE.
        self.assertEqual(rec["rule_cited"], NAMESPACE_LAW)
        # CLAUSE TWO — the CALLER, keyed by the ACT. Asserted separately and on purpose.
        self.assertEqual(answer, -E.EEXIST)

    def test_a_refused_unlink_of_an_absent_name_carries_the_SAME_rule_and_ENOENT(self):
        import errno as E
        self.retired()
        answer = self.wire("FILE-UNLINK", path="/gone")
        rec = self.pstore.by_action("op-refused")[-1]
        self.assertEqual(rec["rule_cited"], NAMESPACE_LAW)
        self.assertEqual(answer, -E.ENOENT)

    def test_ONE_RULE_governs_every_act_class_and_the_answers_differ(self):
        """The non-vacuity clause for the pair above, and the finding in one row: six acts,
        six POSIX answers, ONE cited rule. A rule-keyed map cannot express that, which is why
        the missing row was the symptom and the KEY was the defect."""
        import errno as E
        self.assertEqual(self.wire("FILE-CREATE", path="/a"), 0)
        self.assertEqual(self.wire("FILE-MKDIR", path="/d"), 0)
        self.retired()
        answers = {
            "create over a held name": self.wire("FILE-CREATE", path="/a"),
            "unlink an absent name": self.wire("FILE-UNLINK", path="/gone"),
            "rmdir a non-directory": self.wire("FILE-RMDIR", path="/a"),
            "unlink a directory": self.wire("FILE-UNLINK", path="/d"),
            "link to a directory": self.wire("FILE-LINK", target_path="/d", new_path="/n"),
            "link over a held name": self.wire("FILE-LINK", target_path="/a", new_path="/a"),
        }
        self.assertEqual(sorted(answers.values()),
                         sorted([-E.EEXIST, -E.ENOENT, -E.ENOTDIR, -E.EISDIR, -E.EPERM,
                                 -E.EEXIST]))
        self.assertEqual(len(set(answers.values())), 5)
        cited = {e["rule_cited"] for e in self.pstore.by_action("op-refused")}
        self.assertEqual(cited, {NAMESPACE_LAW},
                         "one rule governs every one of them, on the record")

    def test_THE_LAW_SHOPPING_DOUBLE_greens_the_errno_clause_and_REDS_the_citation(self):
        """§A56 EXHIBITED THROUGH SHIPPED CODE, and it is this pass's sharpest row.

        THE TEMPTATION EP-28K'S BUILDER REFUSED: cite `ROOT-NEG-6`, which the recorded
        `rule-errno` pack maps to EEXIST, and a RULE-KEYED renderer produces the right
        observable. Driven here against `kernel.syscall_port`, which is a real, shipped,
        rule-keyed renderer reading that very pack — so the payoff is measured rather than
        described.

        AND THE HALF THAT IS THIS PASS'S OWN RESULT: under the ACT-KEYED rendering the shopped
        citation buys NOTHING. The false citation used to produce the correct observable —
        that was the incentive, and it ran exactly backwards. Re-keying does not merely make
        law-shopping detectable; it removes what there was to shop for."""
        from kernel.syscall_port import SyscallPort
        rule_keyed = SyscallPort(self.gate, self.views)._errno_for
        # THE ERRNO CLAUSE GREENS under a rule-keyed renderer: the shopped rule maps to the
        # answer POSIX wants for a refused create.
        self.assertEqual(rule_keyed("ROOT-NEG-6"), "EEXIST")
        # THE CITATION CLAUSE REDS: the law that GOVERNS a namespace act is not that rule,
        # read from the op's own definition rather than from anybody's memory.
        governs = self.views.op_definitions()["FILE-CREATE"]["definition"]["law_cited"]
        self.assertEqual(governs, NAMESPACE_LAW)
        self.assertNotEqual("ROOT-NEG-6", governs)
        # AND THE ACT KEY IS INDIFFERENT TO THE CITATION, which is the payoff removed.
        from bridge.kernel_port import ERRNO_BY_ACT
        import errno as E
        self.assertEqual(ERRNO_BY_ACT[("FILE-CREATE", "binding:unbound")], E.EEXIST)
        # DOCUMENTED FLIP (EP-28N AMENDMENT 1, 2026-08-05). The requirement vocabulary grew
        # by the eight hierarchy members' two forms and by `contains:empty`, and the derived
        # ones carry `@container` — which is THIS ROW'S OWN CLAIM extended: a key that names
        # WHAT THE ACT REQUIRED must also name WHICH KEY it required it of, or the create
        # family's own-name row and its container row collide on one string. The property is
        # asserted as a property rather than as a fixed set, so the next member joins without
        # a re-listing, and the "no key names a rule" half is asserted directly.
        self.assertEqual({k[1].split("@")[0].split(":")[0] for k in ERRNO_BY_ACT},
                         {"binding", "kind", "contains"},
                         "every key names WHAT THE ACT REQUIRED and no key names a rule")
        rules = {(e.get("payload") or {}).get("rule_id")
                 for e in self.store.by_action("CREATE-RULE")}
        self.assertEqual({k[1] for k in ERRNO_BY_ACT} & rules, set(),
                         "and no requirement string is a rule id")

    def test_the_rule_keyed_table_gained_NO_row_for_the_namespace_law(self):
        """WRONG REFERENCE 3, refused structurally. Rows added to a wrong-key map rebuild the
        defect with better coverage; the map is left exactly as EP-28K measured it."""
        from bridge.kernel_port import ERRNO_BY_ACT, ERRNO_BY_RULE
        self.assertNotIn(NAMESPACE_LAW, ERRNO_BY_RULE)
        self.assertEqual(len(ERRNO_BY_RULE), 9, "unchanged since EP-28K's measurement")
        # DOCUMENTED FLIP (EP-28N AMENDMENT 1): 11 -> 19, which is the whole enumeration. The
        # claim this row makes is about the RULE-KEYED map gaining nothing, and that half is
        # untouched; the act-keyed count moved because the eight landed.
        self.assertEqual(len(ERRNO_BY_ACT), 19)
        self.assertEqual({op for op, _r in ERRNO_BY_ACT},
                         set(ENUMERATED_KIND_ROWS) | set(ENUMERATED_BINDS_KIND) | {"FILE-RMDIR"})

    def test_a_refusal_that_named_no_requirement_still_takes_the_rule_keyed_path(self):
        """NOT A FALLBACK BUT A DIFFERENT QUESTION, asserted so the distinction is not left to
        the prose. An unregistered operation is refused under P3-CLOSURE, whose errno the RULE
        does determine because no act could make it anything else — and those rows were always
        right, which is why they are untouched."""
        import errno as E
        self.assertEqual(self.wire("FILE-NONSENSE", path="/x"), -E.ENOSYS)


class TestTheChainIsComputed(_Live):
    """T-CHAIN-COMPUTED. Ruling 1's second half: the record cites the tip, and the chain is
    DERIVED from history — never stored, because a stored chain is a stored derivative."""

    def _refuse_at(self):
        self.act("FILE-CREATE", path="/a")
        with self.assertRaises(OpError):
            self.act("FILE-CREATE", path="/a")
        return self.store.by_action("op-refused")[-1]

    def test_NO_RECORD_ANYWHERE_CARRIES_A_CHAIN(self):
        """The structural half of wrong reference 2, over a driven world rather than over the
        schema someone remembers."""
        self._refuse_at()
        banned = {"chain", "rule_chain", "reasoning_chain", "derivation", "chain_of_reasoning"}

        def keys(o):
            # `Mapping`, NOT `dict`, and the reason is the one `opdefs.router_param`'s own
            # comment gives: a record read back off the store is FROZEN (H1) and arrives as a
            # `mappingproxy`, so an `isinstance(o, dict)` walk returns NOTHING and this row
            # would pass over an empty set — a guard that reads as thorough and inspects
            # nothing. Caught by the non-vacuity clause below, which is what it is for.
            if isinstance(o, Mapping):
                for k, v in o.items():
                    yield k
                    yield from keys(v)
            elif isinstance(o, (list, tuple)):
                for v in o:
                    yield from keys(v)
        seen = {k for e in self.store.all() for k in keys(e)}
        self.assertGreater(len(seen), 0, "non-vacuity: the world holds records with fields")
        self.assertEqual(seen & banned, set(), sorted(seen & banned))

    def test_the_chain_is_derived_at_read_time_from_the_tip_alone(self):
        rec = self._refuse_at()
        chain = rule_chain(self.store, rec["rule_cited"], rec["seq"])
        self.assertEqual(chain, [NAMESPACE_LAW, "BOOT-INT"])

    def test_kill_the_derivation_replay_the_record_the_chains_are_identical(self):
        """P2, on this derivation as on every other. The chain is recomputed from a store
        rebuilt out of the record file alone, with nothing carried across."""
        rec = self._refuse_at()
        before = rule_chain(self.store, rec["rule_cited"], rec["seq"])
        d2 = tempfile.mkdtemp(prefix="ep28n-replay-")
        try:
            shutil.copy(self.record, os.path.join(d2, "record.jsonl"))
            store2, _g, _v, _b, _s = build_full_kernel(
                os.path.join(d2, "record.jsonl"), os.path.join(d2, "blobs"),
                os.path.join(d2, "vault"))
            self.assertEqual(rule_chain(store2, rec["rule_cited"], rec["seq"]), before)
        finally:
            shutil.rmtree(d2, ignore_errors=True)

    def test_THE_CROSS_ERA_ARM_a_record_yields_the_chain_AS_IT_WAS_THEN(self):
        """THE ROW. A single-era world satisfies every clause above vacuously; this is the one
        that is not vacuous, and the reason it works is the clause's own precondition — the
        LAW IS ITSELF IN THE RECORD, so the era at record time is recoverable.

        NON-VACUITY IS ASSERTED BEFORE THE COMPARISON IS READ: the world must hold the tip
        rule under at least two eras, with different citations, or the comparison compares a
        thing with itself."""
        first = self._refuse_at()
        self.act("CREATE-RULE", rule_id=NAMESPACE_LAW, polarity="-", enforcement="live",
                 enforced_by="re-recorded at runtime, so this world holds two law eras")
        with self.assertRaises(OpError):
            self.act("FILE-CREATE", path="/a")
        second = self.store.by_action("op-refused")[-1]

        eras = [(e["seq"], e["rule_cited"]) for e in self.store.by_action("CREATE-RULE")
                if (e.get("payload") or {}).get("rule_id") == NAMESPACE_LAW]
        self.assertEqual(len(eras), 2, "NON-VACUITY: two law eras for one tip rule")
        self.assertNotEqual(eras[0][1], eras[1][1],
                            "NON-VACUITY: the two eras must cite differently or the chain "
                            "cannot differ and this row proves nothing")

        self.assertEqual(rule_chain(self.store, first["rule_cited"], first["seq"]),
                         [NAMESPACE_LAW, "BOOT-INT"])
        self.assertEqual(rule_chain(self.store, second["rule_cited"], second["seq"]),
                         [NAMESPACE_LAW, "ROOT-NEG-6", "BOOT-INT"])

        # THE DOUBLE. Identical in a single-era world — every clause above passes under it —
        # and wrong here, which is what makes the arm load-bearing rather than decorative.
        self.assertEqual(_chain_from_the_LIVE_law(self.store, second["rule_cited"]),
                         rule_chain(self.store, second["rule_cited"], second["seq"]))
        self.assertNotEqual(_chain_from_the_LIVE_law(self.store, first["rule_cited"]),
                            rule_chain(self.store, first["rule_cited"], first["seq"]))

    def test_THE_FOUNDING_HISTORY_ALONE_CANNOT_DRIVE_THIS_and_that_is_MEASURED(self):
        """THE HONEST CAP, made a row rather than a sentence. The plan pointed the cross-era
        arm at this arc's own founding history (1.13.0 -> 1.16.0). Those four foundings are
        RULE-IDENTICAL — the same forty-one law records citing the same rules — because every
        pass in this arc changed OP DEFINITIONS and none changed a law's citation. So an arm
        driven only on the founding history would compare a chain with itself and pass
        vacuously, and the arm above is driven on the record's own law era instead."""
        def rules_of(pack):
            return [(r.get("object"), r.get("rule_cited")) for r in _records(pack)
                    if r.get("action") == "CREATE-RULE"]
        # ERA-PINNED (EP-28N AMENDMENT 1, §A57): the fourth era read the LIVE pack, so it
        # named whatever founding ships rather than the one this pass measured. Pinned to
        # this pass's own close commit; the arithmetic and the claim are unchanged.
        eras = [pack_at("a6a20f3^"), pack_at("a6a20f3"), pack_at("0aa8429"),
                pack_at(EP28N_AFTER_COMMIT)]
        versions = [p["founding_version"] for p in eras]
        self.assertEqual(versions, ["1.13.0", "1.14.0", "1.15.0", "1.16.0"],
                         "non-vacuity: four DISTINCT foundings")
        self.assertEqual(len(rules_of(eras[0])), 41)
        for p in eras[1:]:
            self.assertEqual(rules_of(p), rules_of(eras[0]),
                             "a founding in this arc changed a law's citation after all")


class TestAbsenceStaysAbsence(_Live):
    """T-ABSENCE-STAYS. EP-28K's clause EXTENDED over this pass's landed set, asserted as a
    SET rather than restated as a sentence: §11.1a's ABSENCE membership was conditional on
    nothing governing the outcome, and the ops this pass does not reach keep it untouched."""

    def test_the_ops_declaring_a_kind_check_are_EXACTLY_the_three(self):
        ops = pack_ops(pack_at(EP28N_AFTER_COMMIT))          # era-pinned, EP-28N AMENDMENT 1
        declaring = {n for n, d in ops.items() if kind_rows(d)}
        self.assertEqual(declaring, set(ENUMERATED_KIND_ROWS))
        self.assertEqual(len(ops) - len(declaring), 69,
                         "sixty-nine ops are untouched by this pass's classification change")

    def test_an_op_declaring_no_kind_check_appends_and_refuses_nothing(self):
        """Driven on `FILE-PERM`, which names a path, cites the permission law and declares
        neither a binding nor a kind — so §11.1a's classification of its outcomes is exactly
        where EP-28K left it and exactly where §11.1a put it."""
        self.act("FILE-MKDIR", path="/d")
        before = len(self.store.by_action("op-refused"))
        self.act("FILE-PERM", path="/d", perm="700")
        self.assertEqual(len(self.store.by_action("op-refused")), before,
                         "an op declaring nothing refuses nothing")
        self.assertEqual(len(self.acts("FILE-PERM")), 1)

    def acts(self, action):
        return self.store.by_action(action)


class TestTheGuardAtThreeDoors(_Live):
    """T-GUARD-AT-THREE-DOORS. ONE VALIDATION, THREE DOORS (design/36 ADDENDUM I.3), and the
    founding installer is the door all seventy-two live definitions actually came through."""

    def _peers(self):
        return {n: (v.get("definition") or {})
                for n, v in self.views.op_definitions().items()}

    def _op(self, checks):
        # `path`/`other`/`class_of`: all STRUCTURAL — a namespace path and two optional
        # governance scalars, each safe inline. The op's own shape is decisive here: it
        # declares them inline via `object_param: "path"` and `payload_from`, so the inline
        # shape classifies them structural regardless of any name-mirror. The refusal fixtures
        # that share this builder refuse at the check-row leash (or run classify-inert on direct
        # `validate_definition_shape` calls), before the vocabulary door. [design/46 member-2,
        # archi :2956 RULING 1: per-field true nature; inline shape overrides a name-mirror.]
        return {"law_cited": NAMESPACE_LAW, "description": "a test-world namespace op",
                "params": {"path": "required", "other": "optional", "class_of": "optional"},
                "object_param": "path", "payload_from": ["path", "other", "class_of"],
                "structural_params": ["path", "other", "class_of"],
                "checks": checks}

    def _bind(self, **over):
        row = {"check": "binding", "key_param": "path", "require": "bound", "effect": "bind",
               "cite": NAMESPACE_LAW, "binds_kind": {"literal": "a-class"}}
        row.update(over)
        return row

    def _kind(self, **over):
        row = {"check": "kind", "key_param": "path", "require": "a-class",
               "cite": NAMESPACE_LAW}
        row.update(over)
        return row

    def test_each_malformation_refuses_for_its_own_stated_reason(self):
        cases = {
            "names no key_param": [self._bind(), self._kind(key_param=None)],
            "which this operation does not take":
                [self._bind(), self._kind(key_param="absent_param")],
            "never writes to": [self._bind(), self._kind(key_param="unwritten")],
            "requires nothing and forbids nothing":
                [self._bind(), self._kind(require=None)],
            "may not both require and forbid":
                [self._bind(), self._kind(forbid="other-class")],
            "an empty one is unrecordable": [self._bind(), self._kind(require="")],
            "does not require that key to be bound":
                [self._bind(require="unbound"), self._kind()],
            "is answered BEFORE": [self._kind(), self._bind()],
            "sits on a check that binds no key": [self._bind(),
                                                  self._kind(binds_kind={"literal": "x"})],
            "must name exactly one source":
                [self._bind(binds_kind={"literal": "a", "param": "other"}), self._kind()],
            "which this operation does not take'":
                [self._bind(binds_kind={"param": "nope"}), self._kind()],
            "an empty class is unrecordable":
                [self._bind(binds_kind={"literal": ""}), self._kind()],
        }
        for fragment, checks in cases.items():
            d = self._op(checks)
            if fragment == "never writes to":
                d["params"]["unwritten"] = "optional"
            with self.assertRaises(_Door.Refused) as raised:
                opdefs.validate_definition_shape(_Door(), "CREATE-OP", OWNER, "NS", d,
                                                 self._peers())
            self.assertIn(fragment.rstrip("'"), raised.exception.message, fragment)

    def test_THE_CLASS_CLAUSE_a_bind_that_says_no_class_under_a_class_governed_law_refuses(self):
        """The clause that closes the CLASS rather than its members. The ops that must declare
        are found STRUCTURALLY — they are the ops citing the law that some peer's own class
        check cites — so a namespace op added next campaign cannot omit what the installer
        refuses to load, and nothing in the engine names a filesystem to find them."""
        d = self._op([self._bind(binds_kind=None)])
        del d["checks"][0]["binds_kind"]
        with self.assertRaises(_Door.Refused) as raised:
            opdefs.validate_definition_shape(_Door(), "CREATE-OP", OWNER, "NS", d,
                                             self._peers())
        self.assertIn("without saying what class it gives it", raised.exception.message)

    def test_the_class_clause_is_SILENT_where_no_peer_asks_a_class_question(self):
        """The other side of the same clause, and the reason it is scoped to the law rather
        than to every binding anywhere: an op binding a key in a key space nobody asks class
        questions about is not made to invent one."""
        d = self._op([self._bind(cite="FS-LAW-MOUNT")])
        del d["checks"][0]["binds_kind"]
        d["law_cited"] = "FS-LAW-MOUNT"
        opdefs.validate_definition_shape(_Door(), "CREATE-OP", OWNER, "NS", d, self._peers())

    def test_door_one_the_founding_installer_refuses_the_whole_founding(self):
        recs = [{"actor": "SYSTEM", "action": "CREATE-OP", "object": "op:NS",
                 "rule_cited": "CAP-IS-LAW",
                 "payload": {"kind": "op_definition", "name": "NS",
                             "definition": self._op([self._bind(), self._kind(require="")])}}]
        with self.assertRaises(FoundingIntegrityError) as raised:
            _validate(recs)
        self.assertIn("unrecordable", str(raised.exception))

    def test_door_two_create_op_refuses_cited_and_recorded(self):
        before = len(self.store.by_action("op-refused"))
        d = self._op([self._bind(), self._kind(key_param="absent_param")])
        with self.assertRaises(OpError) as raised:
            self.gate.execute("CREATE-OP", OWNER, {"name": "NS", "definition": d})
        self.assertEqual(raised.exception.rule, "AR-2")
        self.assertEqual(len(self.store.by_action("op-refused")), before + 1)
        self.assertFalse(self.gate.has("NS"))

    def test_door_three_amend_op_refuses(self):
        good = self._op([self._bind(), self._kind()])
        self.gate.execute("CREATE-OP", OWNER, {"name": "NS", "definition": good})
        self.assertTrue(self.gate.has("NS"))
        with self.assertRaises(OpError) as raised:
            self.gate.execute("AMEND-OP", OWNER,
                              {"name": "NS",
                               "definition": self._op([self._bind(), self._kind(require="")])})
        self.assertEqual(raised.exception.rule, "AR-2")

    def test_a_wellformed_op_is_ADMITTED_at_all_three_doors(self):
        """The positive half: a guard whose only evidence is that nothing refused it has not
        been shown to admit anything either. The class here is a word the engine has never
        seen, which is I5 asserted rather than intended."""
        good = self._op([self._bind(), self._kind()])
        opdefs.validate_definition_shape(_Door(), "FOUNDING", "SYSTEM", "NS", good,
                                         self._peers())
        self.gate.execute("CREATE-OP", OWNER, {"name": "NS", "definition": good})
        self.assertTrue(self.gate.has("NS"))

    def test_THE_CAN_FAIL_CONTROL_the_guard_neutered_admits_the_malformed_definition(self):
        """Without this the passing rows above prove only that nothing refused, which is not
        the same as there being something that would."""
        bad = self._op([self._bind(), self._kind(require="")])
        real = opdefs._require_wellformed_kind
        opdefs._require_wellformed_kind = lambda *a, **k: None
        try:
            opdefs.validate_definition_shape(_Door(), "CREATE-OP", OWNER, "NS", bad,
                                             self._peers())
        finally:
            opdefs._require_wellformed_kind = real
        with self.assertRaises(_Door.Refused):
            opdefs.validate_definition_shape(_Door(), "CREATE-OP", OWNER, "NS", bad,
                                             self._peers())

    def test_the_installer_and_the_gate_run_the_SAME_function(self):
        self.assertIs(install_module.validate_definition_shape,
                      opdefs.validate_definition_shape)


class TestTwoReadersOfTheCLASS(_Live):
    """THE LEASH THIS POWER ARRIVES WITH (design-soul §2), and it is the same leash EP-28K's
    row put on the binding fold, one question over.

    The gate now folds "what does this name name?" out of the DECLARATIONS, and the port's
    namespace fold has always answered it from a MAP IN CODE (`custody.apply`'s
    action -> kind literal). Two readers of one record is P2 working; two readers that
    DISAGREE would present as lawful acts refused and unlawful acts admitted, so the equality
    is asserted over a generated history rather than assumed."""

    def classes_at_the_gate(self):
        """DOCUMENTED FLIP (EP-28N AMENDMENT 1, 2026-08-05): the DECLARED ROOT is subtracted,
        exactly as `classes_at_the_port` has always subtracted it. The gate now folds a class
        for the root because the law declares one; the port excludes the root as substrate.
        Comparing them without the symmetry would make every row here fail for the one name
        that is not a divergence. The root's own class is asserted in `test_ep28n2.py`."""
        return {k: v for k, v in opdefs._live_namespace(self.store, self.views)[1].items()
                if k != "/"}

    def classes_at_the_port(self):
        state = custody.fold(self.store.all())
        return {name: state.inodes[ino].kind for name, ino in state.names.items()
                if name != "/"}

    def _history(self):
        self.act("FILE-MKDIR", path="/d")
        self.act("FILE-CREATE", path="/f")
        self.act("FILE-CREATE", path="/p", node_type="fifo")
        self.act("FILE-SYMLINK", path="/s", target="/f")
        self.act("FILE-LINK", target_path="/f", new_path="/h")
        self.act("FILE-RENAME", path="/d", new_path="/d2")
        self.act("FILE-RENAME", path="/h", new_path="/h2")

    def test_the_two_readers_agree_about_every_live_name(self):
        self._history()
        gate = self.classes_at_the_gate()
        self.assertGreater(len(gate), 0, "non-vacuity: the world holds classified names")
        self.assertEqual(gate, self.classes_at_the_port())

    def test_the_history_exercises_all_three_declaration_sources(self):
        """A differential over a history that never drives a source proves nothing about it,
        and `from_key` is the one a reading would skip: it is the only source whose value the
        act does not carry."""
        self._history()
        gate = self.classes_at_the_gate()
        self.assertEqual(gate["/d2"], "dir", "literal, CARRIED through a rename (from_key)")
        self.assertEqual(gate["/p"], "fifo", "param — the record says what was created")
        self.assertEqual(gate["/s"], "link", "literal")
        self.assertEqual(gate["/h2"], gate["/f"], "from_key — a second name for one thing")

    def test_A_RENAMED_DIRECTORY_IS_STILL_A_DIRECTORY_which_is_why_from_key_exists(self):
        """The row that says why the third source is not decoration. Without it a rename would
        drop the class, and the next act over the renamed name would be refused for being
        something it never stopped being."""
        self._history()
        self.act("FILE-RMDIR", path="/d2")
        self.assertNotIn("/d2", self.classes_at_the_gate())

    def test_the_gate_folds_the_class_from_LAW_and_the_port_from_a_LIST_IN_CODE(self):
        """The divergence risk named rather than left implicit, which is what makes the
        equality row above worth running: these two agree today by measurement, not by
        construction, because only one of them reads the declarations."""
        with open(os.path.join(REPO, "src", "bridge", "custody.py"), encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn('"FILE-CREATE": KIND_FILE, "FILE-MKDIR": KIND_DIR', src,
                      "the port still maps action -> kind in code; when that changes, the "
                      "equality row above is what catches it")


class TestTheHierarchyEightAreBlockedByOneMeasuredFact(_Live):
    """THE EIGHT THIS PASS DOES NOT DECLARE, and the fact that blocked them — MEASURED, so the
    disposition was falsifiable rather than an author's preference.

    Six ask about `parent_of(key)` and two about `contains(key)`. Both are HIERARCHY over the
    law's key space, and hierarchy needs that key space to be normalised.

    BOTH ROWS BELOW ARE DOCUMENTED FLIPS (EP-28O, 2026-08-05). They measured a key space that
    was unnormalised; the law's key derivation now calls the namespace fold's own `_norm`, so
    the same drives measure the opposite and say so at the line. The DISPOSITIONS above do not
    move: this pass declared no hierarchy check, EP-28O declares none either, and what the
    eight wait on is now an authoring rather than a key space that could not carry them."""

    def test_THE_BLOCKING_FACT_IS_REMOVED_the_laws_key_space_is_normalised_DRIVEN(self):
        """DOCUMENTED FLIP (EP-28O). This read `..._the_laws_key_space_is_unnormalised_DRIVEN`
        and asserted two keys to the law against one name to the fold. The second spelling is
        now REFUSED as the duplicate it always was, and the two readers hold one key and one
        name. The drive is unchanged; the outcome is the opposite, which is what makes this a
        flip rather than a deletion."""
        self.act("FILE-MKDIR", path="/a")
        with self.assertRaises(OpError):
            self.act("FILE-MKDIR", path="/a/")
        # SECOND DOCUMENTED FLIP (EP-28N AMENDMENT 1): the DECLARED ROOT joins the key set,
        # so the assertion names it. One key was the claim and one key is still the claim —
        # the root is not a spelling of `/a`, it is the key space's declared bottom.
        self.assertEqual(opdefs._live_bindings(self.store, self.views), frozenset({"/", "/a"}),
                         "the law holds ONE key, plus the key space's declared root")
        self.assertEqual(set(custody.fold(self.store.all()).names) - {"/"}, {"/a"},
                         "and the fold holds that same one name")

    def test_and_the_consequence_IS_GONE_the_arithmetic_that_refused_a_lawful_act_closes(self):
        """DOCUMENTED FLIP (EP-28O), and it is the arithmetic this pass raised, closed.

        A directory made as `/a/` was served as `/a` and keyed `/a/`, so a parent check over
        `FILE-CREATE /a/b` would have computed `parent_of("/a/b") = "/a"`, failed to find it,
        and REFUSED a create into a directory that plainly exists. The key is now `/a` and the
        parent is found. The check is STILL not declared — that is the authoring EP-28O
        unblocks rather than performs — so the create is admitted here for the same reason it
        always was, and the assertion that moved is the one about the key.

        THIRD FLIP, AND IT CLOSES THE SENTENCE (EP-28N AMENDMENT 1, 2026-08-05): "the check is
        STILL not declared" is what that pass declares. The container row now exists, the
        parent IS found, and the create is admitted BECAUSE the check passes rather than
        because nothing asked. The drive is unchanged; what moved is why it succeeds, and
        that is now asserted instead of assumed."""
        self.act("FILE-MKDIR", path="/a/")
        keys = opdefs._live_bindings(self.store, self.views)
        self.assertEqual(set(keys), {"/", "/a"}, "the law holds the CANONICAL key")
        self.assertEqual(set(custody.fold(self.store.all()).names) - {"/"}, {"/a"},
                         "the fold serves the directory under that same name")
        parent_of = "/a/b".rsplit("/", 1)[0] or "/"
        self.assertEqual(parent_of, "/a")
        self.assertIn(parent_of, keys,
                      "so a parent check would now find the directory the create lands in")
        self.act("FILE-CREATE", path="/a/b")      # still admitted, because no such check
        self.assertEqual(len(self.store.by_action("FILE-CREATE")), 1)   # exists yet

    def test_the_eight_are_the_set_and_nothing_slid_into_or_out_of_it(self):
        blocked = {pair for pair, (v, _k) in THIS_PASS_DISPOSITIONS.items() if v == "HIERARCHY"}
        self.assertEqual(len(blocked), 8)
        parents = {p for p in blocked if THIS_PASS_DISPOSITIONS[p][1].startswith("parent_of")}
        contains = {p for p in blocked if THIS_PASS_DISPOSITIONS[p][1].startswith("contains")}
        self.assertEqual(len(parents), 6)
        self.assertEqual(len(contains), 2)
        self.assertEqual(parents | contains, blocked)

    def test_the_LAW_now_answers_all_eight_and_the_port_answers_none_of_them(self):
        """DOCUMENTED FLIP — EP-28C W4e, 2026-08-07. THE RETIRED CONSTRUCT THIS ROW WAS
        READING: `enumerate_pairs()` over `_posix_precondition`'s AST, under the claim "these
        eight are not open holes today, they are the PORT's — exactly as all nineteen were
        before EP-28K ... the port's precondition is byte-untouched by this pass."

        THE SEAM THIS PASS HANDED ON HAS BEEN TAKEN. EP-28N AMENDMENT 1 declared the eight,
        and W4e retired the read, so all nineteen outcomes are the LAW's and none is the
        port's. The row keeps its subject — the outcome classes are unchanged, which is what
        "nothing regressed" always meant — and adds the half that is now checkable: the port
        holds no precondition read at all."""
        outcomes = {e for _op, e in enumerate_pairs()[0]}
        self.assertEqual(outcomes, {"EEXIST", "ENOENT", "ENOTDIR", "ENOTEMPTY", "EISDIR",
                                    "EPERM"},
                         "the six outcome classes are unchanged by the retirement")
        from bridge.kernel_port import KernelPort
        self.assertFalse(hasattr(KernelPort, "_posix_precondition"),
                         "the port still holds a precondition read, so the eight are still "
                         "answered twice and this row's premise is wrong")


class TestThePortRefusesToServeALawItCannotRender(unittest.TestCase):
    """THE LEASH THE ACT-KEYED TABLE ARRIVES WITH. A table that silently defaults on a
    requirement it lacks is the defect this pass closes wearing a different key, so the port
    computes its own coverage FROM THE LAW at construction and refuses to serve rather than
    discovering the gap at a caller."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep28n-cover-")

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def _port(self):
        from bridge.kernel_port import KernelPort
        from bridge.mount import build_brain
        store, gate, views, blobs = build_brain(
            os.path.join(self.dir, "rec.jsonl"), os.path.join(self.dir, "blobs"))
        return KernelPort(store, gate, views, blobs)

    def test_the_shipped_founding_is_fully_renderable(self):
        self.assertIsNotNone(self._port())

    def test_THE_CAN_FAIL_CONTROL_a_missing_row_refuses_the_port_at_construction(self):
        """Without this the row above proves only that nothing raised."""
        import bridge.kernel_port as kp
        saved = dict(kp.ERRNO_BY_ACT)
        kp.ERRNO_BY_ACT.pop(("FILE-LINK", "kind:forbid:dir"))
        try:
            with self.assertRaises(kp.PortCannotRenderTheLaw) as raised:
                self._port()
            self.assertIn("FILE-LINK", str(raised.exception))
        finally:
            kp.ERRNO_BY_ACT.clear()
            kp.ERRNO_BY_ACT.update(saved)

    def test_the_coverage_is_computed_from_the_LAW_and_not_from_a_list(self):
        from bridge.kernel_port import DECISION_OPS, ERRNO_BY_ACT
        from kernel.opdefs import declared_requirements
        # THE SET EQUALITY IS THE PROPERTY AND IT READS THE LIVE PACK ON PURPOSE: this row
        # says the port's table and the founding's own declarations agree, and pinning it to
        # a past era would stop it saying that about what ships. The COUNT is era-pinned
        # instead (EP-28N AMENDMENT 1 raised it 11 -> 19), so the row still fails if the two
        # diverge and no longer fails merely because the law grew.
        ops = pack_ops(load_pack())
        needed = {(n, r) for n, d in ops.items() if n in DECISION_OPS
                  for r in declared_requirements(d)}
        self.assertEqual(needed, set(ERRNO_BY_ACT),
                         "the table and the law's own declared requirements are the same set")
        at_this_pass = {(n, r) for n, d in pack_ops(pack_at(EP28N_AFTER_COMMIT)).items()
                        if n in DECISION_OPS for r in declared_requirements(d)}
        self.assertEqual(len(at_this_pass), 11)


class TestThePreconditionReadWasTheInvitationAndW4eACCEPTEDIt(unittest.TestCase):
    """§15's CONTROL AT THIS PASS, NOW DISCHARGED. This pass's fence licensed
    `src/bridge/kernel_port.py` for the errno RENDERING ONLY and left the precondition read
    the whole finding lives in untouched — "its retirement is W4e's, against this law, one
    variable at a time."

    THE CLASS IS RENAMED AND NOT ONLY FLIPPED (EP-28C W4e, 2026-08-07). A class named
    `IsTheInvitationDECLINED` whose row now asserts the read is GONE carries a repealed fact
    in its name, which is worse than a stale header — a header merely lags, a name is read as
    the claim.

    THE ASSERTION IS STILL ON THE FUNCTION'S BYTES AND NOT ON ITS LINE NUMBER, which is the
    point worth reading twice. The plan names the read at `:380`; this pass added lines above
    it and it began at `:473`. A row pinned to a line number would have gone red on a file
    whose licensed-but-untouched artifact did not change one character. The same reasoning is
    why the retirement is asserted STRUCTURALLY below rather than by grepping for a string."""

    def test_the_read_was_PRESENT_at_this_passs_commit_and_is_RETIRED_on_the_tree(self):
        """DOCUMENTED FLIP — EP-28C W4e, 2026-08-07. THE RETIRED CONSTRUCT THIS ROW WAS
        READING: `next(... n.name == "_posix_precondition")` over the live tree, compared
        byte-for-byte against the same function at `EP28N_BEFORE_COMMIT`.

        BOTH HALVES ARE KEPT. The BEFORE half is the non-vacuity clause and it matters MORE
        after the flip than before it: an assertion that a function is absent from the tree
        passes just as well against a file that never held it, a moved file, or a typo in the
        path. Proving the pin's own commit HELD the function is what makes the absence
        evidence."""
        def read_of(src):
            tree = ast.parse(src)
            fn = next((n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
                       and n.name == "_posix_precondition"), None)
            return ast.get_source_segment(src, fn) if fn is not None else None
        # [DOCUMENTED FLIP — EP-28Z, 2026-08-12. The era read moves to `tests/era_pin.py`,
        # the one home; `missing="skip"` is the same skip-on-unresolvable branch by name.
        # The era's own bytes, not this file's spelling of how to get them.]
        era_src = era_pin.text_at(EP28N_BEFORE_COMMIT, "src/bridge/kernel_port.py", missing="skip")
        with open(PORT_PATH, encoding="utf-8") as fh:
            live = fh.read()
        before = read_of(era_src)
        self.assertIsNotNone(before, "non-vacuity: the BEFORE read was found")
        self.assertGreater(len(before), 0, "non-vacuity: the BEFORE read is not empty")
        self.assertIsNone(read_of(live),
                          "the port still holds a precondition read — W4e's retirement did "
                          "not land, and this file's disposition is still owed")
        # AND THE FILE IS THE ONE THIS ROW MEANS: an absence over an unparseable or renamed
        # artifact would satisfy the clause above for the wrong reason.
        self.assertIn("ERRNO_BY_ACT", live, "the port's act-keyed table is gone as well, so "
                                            "the absence above is about the wrong file")


class TestTheRuleErrnoPackDispositionWasDerivedNotAssumed(_Live):
    """THE `rule-errno` PACK: what of it retires, and under what showing. DERIVED HERE, and
    the derivation says NOTHING RETIRES IN THIS PASS.

    The pack's `FS-LAW-NAMESPACE -> EACCES` row is the wrong key doing the port's job, and
    this pass replaced that job at ONE of the pack's two consumer surfaces. Retiring the row
    would move the OTHER consumer — `kernel.syscall_port`, outside this fence — from EACCES,
    which is wrong, to EINVAL, which is wrong AND worse. A retirement whose replacement is
    proven at one consumer and absent at another is not strictly stronger, so it is not
    taken; it is measured and RAISED."""

    def test_the_pack_still_declares_the_row_so_the_retirement_is_visibly_NOT_taken(self):
        rows = [dict(l) for l in self.views.category_packs()["rule-errno"]["levels"]
                if l["rule"] == NAMESPACE_LAW]
        self.assertEqual([r["errno"] for r in rows], ["EACCES"])

    def test_THE_DIVERGENCE_THIS_LEAVES_measured_rather_than_described(self):
        """Two ports, one refusal, two answers — and the arithmetic of the cost of closing it
        the other way. This is §A55's "what else reaches the same subject by a different path"
        as a row instead of a sentence."""
        from kernel.syscall_port import SyscallPort
        import errno as E
        self.assertEqual(SyscallPort(self.gate, self.views)._errno_for(NAMESPACE_LAW), "EACCES")
        from bridge.kernel_port import ERRNO_BY_ACT
        self.assertEqual(ERRNO_BY_ACT[("FILE-CREATE", "binding:unbound")], E.EEXIST)

    def test_and_removing_the_row_would_make_the_other_consumer_WORSE_driven(self):
        """The arithmetic behind "not strictly stronger", driven rather than asserted: with
        the row absent the rule-keyed renderer answers EINVAL, which names no precondition at
        all. That is the measurement that decides the disposition."""
        from kernel.syscall_port import SyscallPort
        port = SyscallPort(self.gate, self.views)
        self.assertEqual(port._errno_for(NAMESPACE_LAW), "EACCES")
        self.assertEqual(port._errno_for("A-RULE-THE-PACK-DOES-NOT-CARRY"), "EINVAL")


if __name__ == "__main__":
    unittest.main()
