"""EP-28K — existence checks become LAW: declared on the op, enforced inside the decide region.

Every probe here is a regression test (the campaign method: a verification probe lands as a
test).

WHAT THIS PASS CLOSES. The port read "is this name taken?" from its own fold and then asked
the gate to act. Those are two steps across the decide region's boundary, so two in-flight
requests for one path both read absent, both decide, and BOTH RECORD — exhibited at
`tests/test_ep28c_w4e.py`, 2-3 in 40 unscheduled. The served state was right (both creates
derive one identity, EP-28I's class-wide law) and the RECORD held an act nobody performed,
which is the inversion this estate has no guard for: every guard runs record -> view.

THE LAW. An op DECLARES a `binding` check over one of its own parameters: what must already
be true of the key that parameter names (`require`), and what this act does to that key
(`effect`). The gate answers it INSIDE the decide region, where check-then-act is atomic BY
CONSTRUCTION — no cross-boundary lock, no region stretched over a second address space.

WHAT THIS DOES TO `design/10` §11.1a, and the row that keeps it from over-reaching. §11.1a
classed the port's precondition outcomes as ABSENCE — a read that answers, producing no
record — and that membership was CONDITIONAL ON NOTHING GOVERNING THE OUTCOME. A declared
check supplies the law, so the classification changes because THE FACT THAT PUT IT THERE
changed. Nothing in §11.1a is overturned and no amendment to it is owed. The clause that
bounds it is asserted rather than stated: an op declaring NO binding check keeps §11.1a's
classification untouched, and `TestAbsenceStaysAbsenceWhereNothingIsDeclared` is the row
that reds if the reclassification ever reaches further than the declaration does.

THE NAMED WRONG REFERENCES THIS BATTERY REFUSES.
  1. IDEMPOTENCE — "create if not exists". The template every storage API teaches, and it is
     the phantom act: state right, record lying. `TestNoPhantomAct` drives an idempotence
     double and reds on the phantom-act clause and no other.
  2. THE CHECK KEPT AT THE PORT TOO, belt and braces. Two enforcers of one rule diverge
     silently and the port's copy still races. `src/bridge/` takes zero lines this pass;
     the retirement is W4e's, against this law, one variable at a time.
  3. THE BLANKET CHECK — every op gains one because uniformity is tidy.
     `TestTheCheckSetComesFromStructure` carries the exclusion reasons per outcome.

Coverage (the EP's named battery):
  T-POPULATIONS            the op population computed from the pack's STRUCTURE (§A51) and
                           reconciled RED-FIRST; the check population read from the PORT's
                           own AST rather than from a remembered list.
  T-CHECK-SET-FROM-STRUCTURE  per-op: the check gained, or the exclusion reason; the changed
                           definitions set-diffed against the enumeration BOTH directions.
  T-CHECK-IN-THE-REGION    two in-flight creates of one path through the GATE: exactly one
                           success and one refusal citing the declared check, with the
                           lifted-out-of-the-region double as the generated red world.
  T-NO-PHANTOM-ACT         a refused act appends no act-record claiming effect; the refusal
                           record cites the check's law.
  T-GUARD-AT-THREE-DOORS   malformed declarations, and an op citing the binding law that
                           declares none, refuse at the installer, at CREATE-OP and at
                           AMEND-OP — plus the can-fail control.
  T-DIFF-IS-THE-CHANGE     the founding diff equals the declared change list exactly, both
                           directions, against the BEFORE pack at a pinned commit.
  T-VERSION-MOVES          `founding_version` reads 1.15.0 in the pack and in the record the
                           installer stamps.
  T-ONE-DERIVATION-TWO-READERS  the gate's live set and the port's namespace fold answer the
                           same question the same way over generated histories, with the two
                           known divergences DRIVEN and declared rather than left to be met.
  T-ERA-PINNED-WORLD-UNTOUCHED  a world founded under the BEFORE pack acts under ITS law: no
                           declaration, no check, no refusal (the two-times law).
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
import threading
import unittest

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(REPO, "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import era_pin                                                    # noqa: E402  (the era-pin home, EP-28Z)
from bridge import custody                                        # noqa: E402
from founding import install as install_module                    # noqa: E402
from founding.install import (                                    # noqa: E402
    FoundingIntegrityError, _validate, load_pack, records as _records,
)
from kernel import opdefs                                         # noqa: E402
from kernel.compose import build_full_kernel                      # noqa: E402
from kernel.errors import OpError                                 # noqa: E402

OWNER = "owner"
PACK_PATH = os.path.join(REPO, "src", "founding", "founding-pack.json")
PORT_PATH = os.path.join(REPO, "src", "bridge", "kernel_port.py")

#: The port-shaped provenance four of the seven namespace ops REQUIRE.
PROV = {"uid": 1000, "gid": 1000, "pid": 42, "window": "test"}

#: [RENAMED 2026-08-15, NOT REVALUED. Board `:575` filed the defect, `:816` verified it
#: against a live 1.24.0, `:841` drew this unit's fence. The four constants below were
#: spelled `BEFORE_COMMIT`, `AFTER_COMMIT`, `NEW_VERSION` and `OLD_VERSION`; those spellings
#: are kept here verbatim so a grep for any of them still lands. NOT ONE VALUE MOVED and no
#: assertion changed meaning.
#:
#: THE DEFECT IS THE NAME, NOT THE VALUE. A constant called `NEW_VERSION` holding 1.15.0 sits
#: NINE founding transitions behind a live 1.24.0, WITH A GREEN TEST UNDER IT — so a reader
#: reaching for "the current founding version" gets a stale one AND an assertion agreeing
#: with it. The rows were always right: they assert about a completed, accepted past, which
#: is what `:575` said when it filed this. A stored label that froze while the world moved is
#: this estate's own class, and a relative name is what defeats it.
#:
#: WHICH TRANSITION, ESTABLISHED BY READING THE CONSUMERS AND NOT ASSUMED FROM THE FILENAME:
#: `TestTheDiffIsTheChange.test_the_before_pack_is_the_one_the_dispatch_anchored` pairs BEFORE
#: with OLD and AFTER with NEW in one row, and the pins measure `050d20e` -> 1.14.0 and
#: `0aa8429` -> 1.15.0 when read at `git show` rather than taken from these comments. That is
#: EP-28K's own move, hence `EP28K_`. NO CONSUMER DISAGREED WITH ANOTHER; one that did would
#: have been a raise, not a choice.
#:
#: THE QUALIFIER IS THE ESTATE'S CONVENTION, CENSUSED BEFORE IT WAS CHOSEN.
#: `tests/test_ep29.py` spells 21 era-pin constants `<UNIT>_BEFORE_COMMIT` / `_BEFORE_VERSION`
#: / `_AFTER_VERSION` / `_AFTER_COMMIT` over `W1A_`, `W1B_`, `W2B_`, `W3A_` and `W3A3_`;
#: `tests/test_ep28n.py` spells its own `EP28N_`. That file is one EP holding many units so
#: its designation is the sub-unit; THIS file is one unit and its designation is EP-28K. The
#: hyphen is dropped because it is not an identifier character. `OLD`/`NEW` became
#: `BEFORE`/`AFTER` on `:780`'s precedent and for its reason: a version and a commit on the
#: same side are ONE era pin, and naming them alike says so. `EP28K_` collided with nothing
#: anywhere in the repo before this pass.
#:
#: `PORT_OUTCOMES` BELOW IS DELIBERATELY UNTOUCHED, AND IT IS THE REASON THIS FILE COULD BE
#: RENAMED AT ALL. `tests/test_ep28n.py:104` reads `from test_ep28k import PORT_OUTCOMES`, so
#: THIS FILE HAS A CROSS-MODULE READER — the fence held only because that reader reads a
#: symbol outside this rename's scope, which `:841` called a promise rather than a fence and
#: therefore stated as a NAMED EXCLUSION. Anyone widening this rename to `PORT_OUTCOMES` reds
#: a file outside the fence. A rename unit's fence is derived from WHO READS THE RENAMED
#: SYMBOLS, never from who imports the file.
#:
#: TWO PROSE MENTIONS WERE RE-SPELLED WITH THE CODE — both documented-flip comments naming
#: the constant they flipped. Leaving them would have left this file describing a name it no
#: longer contains, which is the dangling reference this pass exists to stop.]
#: THE COMMIT THIS PASS OPENED AT — the BEFORE side of the founding diff, pinned so the row
#: compares against a fixed artifact rather than against whatever HEAD holds (§A53: HEAD moves
#: under a session because the timer commits, and cleanliness is judged from `git status`).
EP28K_BEFORE_COMMIT = "050d20e"

#: THIS PASS'S OWN CLOSE — ERA-PINNED BY EP-28N UNDER §A57 [documented flip]. Every row below
#: that describes what EP-28K CHANGED compared a pinned BEFORE against the LIVE pack, so it
#: asserted "the founding looks exactly like this" rather than "EP-28K changed exactly this" —
#: and the first lawful founding move after it therefore reddened rows describing a completed,
#: accepted, unchanged past. This pass's own §5 named that defect and applied the fix to
#: EP-28I; raise 6 of its entry named its own exposure and said a landing pass cannot pin a
#: close commit that does not yet exist. §A57 is the standing clause that fell out of it, and
#: `0aa8429` is this pass's founding-move commit — the first whose `src/founding` tree is the
#: `474f1149…` its close recorded, found by walking the history rather than by being told.
EP28K_AFTER_COMMIT = "0aa8429"

#: THE OP POPULATION, as EP-28I established it and this pass RE-ASSERTS from the structure.
#: Reconciled in `setUp` below and never trusted: a completeness figure stated only in prose is
#: unfalsifiable, which is how "sixty" survived a pre-flight, an authoring and a dispatch note.
DECLARED_POPULATION = 72

EP28K_AFTER_VERSION = "1.15.0"
EP28K_BEFORE_VERSION = "1.14.0"

#: THE LAW WHOSE ACTS MOVE NAMES. Read from the pack in the rows below, never from here — this
#: constant exists so the reader knows which law the enumeration turned out to be about.
NAMESPACE_LAW = "FS-LAW-NAMESPACE"

#: THE CHECK POPULATION, read from the PORT's own `_posix_precondition` and stated per (op,
#: outcome). Every outcome the port produces is here with its disposition, so an exclusion is a
#: claim the pre-flight can re-derive rather than a silence. `errno` is the outcome the port
#: returns today; `key` is the parameter the outcome is about.
#:
#: THE DISPOSITIONS, and each is a reason rather than a label:
#:   DECLARED  — existence-shaped AND its key is a parameter the op already takes, so the law
#:               can name it. These become `binding` checks.
#:   DERIVED-KEY — existence-shaped, but the key is `parent_of(path)`: computed by PATH
#:               ARITHMETIC, which is filesystem grammar. Declaring it would put namespace
#:               spelling into the engine (I5), so it is EXCLUDED and RAISED.
#:   NOT-EXISTENCE — the outcome is about a node's KIND or a directory's CONTENTS, not about
#:               whether a name is bound. A different question needs a different check kind,
#:               and inventing one here would be the blanket-check wrong reference.
PORT_OUTCOMES = (
    ("FILE-CREATE",  "EEXIST",    "path",         "DECLARED"),
    ("FILE-CREATE",  "ENOENT",    "parent(path)", "DERIVED-KEY"),
    ("FILE-CREATE",  "ENOTDIR",   "parent(path)", "NOT-EXISTENCE"),
    ("FILE-MKDIR",   "EEXIST",    "path",         "DECLARED"),
    ("FILE-MKDIR",   "ENOENT",    "parent(path)", "DERIVED-KEY"),
    ("FILE-MKDIR",   "ENOTDIR",   "parent(path)", "NOT-EXISTENCE"),
    ("FILE-SYMLINK", "EEXIST",    "path",         "DECLARED"),
    ("FILE-SYMLINK", "ENOENT",    "parent(path)", "DERIVED-KEY"),
    ("FILE-SYMLINK", "ENOTDIR",   "parent(path)", "NOT-EXISTENCE"),
    ("FILE-RMDIR",   "ENOENT",    "path",         "DECLARED"),
    ("FILE-RMDIR",   "ENOTDIR",   "path",         "NOT-EXISTENCE"),
    ("FILE-RMDIR",   "ENOTEMPTY", "path",         "NOT-EXISTENCE"),
    ("FILE-UNLINK",  "ENOENT",    "path",         "DECLARED"),
    ("FILE-UNLINK",  "EISDIR",    "path",         "NOT-EXISTENCE"),
    ("FILE-RENAME",  "ENOENT",    "path",         "DECLARED"),
    ("FILE-RENAME",  "ENOTEMPTY", "new_path",     "NOT-EXISTENCE"),
    ("FILE-LINK",    "ENOENT",    "target_path",  "DECLARED"),
    ("FILE-LINK",    "EPERM",     "target_path",  "NOT-EXISTENCE"),
    ("FILE-LINK",    "EEXIST",    "new_path",     "DECLARED"),
)

#: THE ENUMERATION'S VERDICT — the binding rows this pass declares, per op, in declaration
#: order because the order is load-bearing: the interpreter runs checks in it, so `FILE-LINK`
#: answers ENOENT before EEXIST exactly as the port does, and `FILE-RENAME` unbinds its source
#: before it binds its destination exactly as the namespace fold does.
#: DOCUMENTED FLIP (EP-28N AMENDMENT 1, 2026-08-05). The three create-family ops each gained
#: a CONTAINER row — the fourth element is `key_of` — because that pass declares the six
#: parent members EP-28K enumerated and left to a later authoring. The rows this pass declared
#: are unchanged and in place; what moved is that the enumeration is no longer complete
#: without the ones after it.
ENUMERATED_ROWS = {
    "FILE-CREATE":  [("path", "unbound", "bind", None),
                     ("path", "bound", None, "container")],
    "FILE-MKDIR":   [("path", "unbound", "bind", None),
                     ("path", "bound", None, "container")],
    "FILE-SYMLINK": [("path", "unbound", "bind", None),
                     ("path", "bound", None, "container")],
    "FILE-RMDIR":   [("path", "bound", "unbind", None)],
    "FILE-UNLINK":  [("path", "bound", "unbind", None)],
    "FILE-RENAME":  [("path", "bound", "unbind", None), ("new_path", None, "bind", None)],
    "FILE-LINK":    [("target_path", "bound", None, None),
                     ("new_path", "unbound", "bind", None)],
}

CHANGED_DEFINITIONS = set(ENUMERATED_ROWS)
def pack_ops(pack):
    """THE POPULATION, READ FROM THE STRUCTURE. Every `CREATE-OP` record IS an op (§A51): no
    name filter, no shape assumption, nothing that could exclude a member without saying so."""
    out = {}
    for step in pack["steps"]:
        for r in step["records"]:
            if r.get("action") == "CREATE-OP":
                pl = r.get("payload") or {}
                out[pl["name"]] = pl["definition"]
    return out


def _name_shape_filtered(pack):
    """THE DOUBLE THAT GENERATES THE RED WORLD for the population clause, carried from EP-28I
    and CITED rather than re-derived: the exact filter that produced "sixty"."""
    return {n: d for n, d in pack_ops(pack).items() if n.isupper() and "-" in n}


def port_outcomes_from_source():
    """THE CHECK POPULATION, READ FROM THE PORT'S OWN AST — every (op, requirement) key of
    `ERRNO_BY_ACT` with the errno it renders, which is what the port DOES rather than what a
    reader remembered. Returns triples in source order.

    DOCUMENTED FLIP — EP-28C W4e, 2026-08-07. THE RETIRED CONSTRUCT THIS ROW WAS READING:
    `_posix_precondition`'s AST, walked for every `return -errno.X`. That function is gone.
    This pass declared eight of its outcomes as law, EP-28N and its AMENDMENT 1 declared the
    remaining eleven, and W4e removed the read once every one of them had a declared check
    behind it and an act-keyed answer at the port.

    THE POPULATION DID NOT GO WITH THE FUNCTION. It moved to the port's OTHER structural
    enumeration — `ERRNO_BY_ACT`, one row per (op, requirement) — and this walks that dict's
    AST. Same nineteen pairs over the same seven ops, still read from the port's source and
    never from a list anybody wrote down. STRICTLY MORE IS RECOVERED than the old walk could
    give: every row also names WHICH REQUIREMENT the outcome is about, which a bare
    `return -errno.EEXIST` never said."""
    tree = ast.parse(open(PORT_PATH, encoding="utf-8").read())
    table = next(n.value for n in ast.walk(tree)
                 if isinstance(n, ast.Assign)
                 and any(getattr(t, "id", None) == "ERRNO_BY_ACT" for t in n.targets))
    out = []
    for key, val in zip(table.keys, table.values):
        out.append((key.elts[0].value, key.elts[1].value,
                    ast.unparse(val).split(".")[-1]))
    return out


def declared_rows(definition):
    # DOCUMENTED FLIP (EP-28N AMENDMENT 1, 2026-08-05): the tuple gained `key_of`. That pass
    # declares binding rows over the key that CONTAINS an act's own key, so a triple could no
    # longer tell a create's own-name row from its container row — and this row's job is that
    # the pack's declarations and the enumeration are the SAME SET, which a tuple that
    # collapses two distinct rows cannot check.
    return [(c.get("key_param"), c.get("require"), c.get("effect"), c.get("key_of"))
            for c in (definition.get("checks") or []) if c.get("check") == "binding"]


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


class TestThePopulationsAreComputedNotCarried(unittest.TestCase):
    """T-POPULATIONS. §A51 made an assertion instead of a sentence, for BOTH halves.

    THE PLACEMENT IS THE CLAUSE (§A48). The reconciliation runs in `setUp`, not as a sibling
    row, because `unittest` orders methods alphabetically and a precedence stated in prose is
    void — a mismatch has to red BEFORE any per-op verdict is read, and the framework
    guarantees that only for `setUp`."""

    def setUp(self):
        # [DOCUMENTED FLIP — EP-29 W1b, 2026-08-12, charter §A57. CAUSE: this pass added two op
        # definitions and moved the founding 1.19.0 -> 1.20.0, so the live pack declares 74
        # CREATE-OP records against this pass's enumerated 72, and `test_the_sixty_five_excluded_
        # ops_carry_no_binding_declaration` computed 67 against its named 65. ASSERTED:
        # `load_pack()`, the LIVE tree. SUPERSEDED: `pack_at(EP28K_AFTER_COMMIT)` — EP-28K's own close
        # commit, the era these binding verdicts were read over. REMAINS TRUE: every per-op
        # verdict below, and the sixty-five figure in the row's own name, which is a fact about
        # THIS era and was never a fact about all future foundings. GIVEN UP: nothing this file
        # claimed live.]
        self.pack = pack_at(EP28K_AFTER_COMMIT)
        self.ops = pack_ops(self.pack)
        self.assertEqual(
            len(self.ops), DECLARED_POPULATION,
            "the pack declares %d CREATE-OP records and this pass was written against %d — "
            "the population is COMPUTED from the structure and reconciled, never carried"
            % (len(self.ops), DECLARED_POPULATION))
        self.outcomes = port_outcomes_from_source()

    def test_the_op_population_reconciles_with_ep28i_and_the_names_are_distinct(self):
        records = [r for r in _records(self.pack) if r.get("action") == "CREATE-OP"]
        self.assertEqual(len(records), DECLARED_POPULATION)
        self.assertEqual(len(self.ops), len(records))

    def test_the_name_shape_filter_still_returns_fewer_and_reds_only_this_clause(self):
        """The generated red world for the population clause, produced through the instrument
        and recorded as output (§A42). Cited from EP-28I rather than re-argued."""
        filtered = _name_shape_filtered(self.pack)
        self.assertLess(len(filtered), len(self.ops))
        self.assertIn("MOUNT", set(self.ops) - set(filtered))

    def test_the_check_population_is_read_from_the_ports_source_not_from_a_list(self):
        """NINETEEN rows over SEVEN ops over SEVEN requirements, rendering SIX errno classes.

        DOCUMENTED FLIP — EP-28C W4e, 2026-08-07. THE RETIRED CONSTRUCT THIS ROW WAS READING:
        the count of `return -errno.X` statements inside `_posix_precondition`. It read
        "THIRTEEN outcomes in code serving NINETEEN pairs, both asserted because the code
        count alone would hide an op (one branch served the three create-family ops)."

        THIRTEEN WAS A PROPERTY OF THE RETIRED FUNCTION'S SHAPE and cannot survive it. What
        the pair of numbers BOUGHT survives, and is what is rebuilt here rather than dropped:
        two countables that can move independently, so a table row silently standing in for
        two distinct outcomes is caught. The surviving second countable is the REQUIREMENT
        set — `binding:unbound` serves four ops, exactly as one branch used to serve three —
        and the errno-class count is added as a third, because it is free."""
        self.assertEqual(len(self.outcomes), 19, self.outcomes)
        self.assertEqual(len(PORT_OUTCOMES), 19)
        self.assertEqual(len({op for op, _r, _e in self.outcomes}), 7)
        self.assertEqual(len({r for _op, r, _e in self.outcomes}), 7)
        self.assertEqual(len({e for _op, _r, e in self.outcomes}), 6)
        self.assertEqual(sorted({e for _op, _r, e in self.outcomes}),
                         sorted({e for _op, e, _k, _d in PORT_OUTCOMES}))
        # STRONGER THAN THE ROW IT REPLACES: the old assertion compared errno SETS, which
        # cannot tell FILE-LINK/EPERM from FILE-UNLINK/EPERM. The pair sets are compared.
        self.assertEqual(sorted({(op, e) for op, _r, e in self.outcomes}),
                         sorted({(op, e) for op, e, _k, _d in PORT_OUTCOMES}))

    def test_every_port_outcome_carries_a_disposition_and_the_arithmetic_closes(self):
        by = {}
        for _op, _errno, _key, disp in PORT_OUTCOMES:
            by[disp] = by.get(disp, 0) + 1
        self.assertEqual(by, {"DECLARED": 8, "DERIVED-KEY": 3, "NOT-EXISTENCE": 8})
        self.assertEqual(sum(by.values()), len(PORT_OUTCOMES))

    def test_the_seven_ops_are_exactly_the_citers_of_the_law_the_checks_cite(self):
        """THE ENUMERATION IS STRUCTURAL, and this is where that is proven rather than said:
        the ops the reading found and the ops citing the law the declared checks cite are the
        SAME SET. That identity is what lets the three-door guard find a future namespace op
        without a list in code."""
        cited = {c.get("cite") for d in self.ops.values()
                 for c in (d.get("checks") or []) if c.get("check") == "binding" and c.get("cite")}
        self.assertEqual(cited, {NAMESPACE_LAW})
        citers = {n for n, d in self.ops.items() if d.get("law_cited") == NAMESPACE_LAW}
        self.assertEqual(citers, set(ENUMERATED_ROWS))
        self.assertEqual(citers, {op for op, _e, _k, _d in PORT_OUTCOMES})


class TestTheCheckSetComesFromStructure(unittest.TestCase):
    """T-CHECK-SET-FROM-STRUCTURE. Per op: the check gained, or the exclusion reason."""

    def setUp(self):
        self.ops = pack_ops(load_pack())

    def test_the_declared_rows_equal_the_enumeration_both_directions(self):
        declared = {n: declared_rows(d) for n, d in self.ops.items() if declared_rows(d)}
        self.assertEqual(set(declared) - set(ENUMERATED_ROWS), set(),
                         "the pack declares a binding the enumeration did not find")
        self.assertEqual(set(ENUMERATED_ROWS) - set(declared), set(),
                         "the enumeration found a binding the pack does not declare")
        for name, rows in ENUMERATED_ROWS.items():
            self.assertEqual(declared[name], rows, name)

    def test_the_sixty_five_excluded_ops_carry_no_binding_declaration(self):
        """The exclusions are a claim, so they are asserted rather than implied by silence."""
        # [DOCUMENTED FLIP — EP-29 W1b, 2026-08-12, charter §A57. CAUSE: this pass added two op
        # definitions, so the excluded set computed 67 against this row's named 65. ASSERTED:
        # `self.ops`, the LIVE tree, via a frozen `DECLARED_POPULATION` of 72.
        #
        # AND THE FIRST FIX WAS WRONG AND IS RECORDED RATHER THAN QUIETLY REPLACED. I first
        # era-pinned this whole class's `setUp` to EP-28K's own EP28K_AFTER_COMMIT, which turned
        # `test_the_declared_rows_equal_the_enumeration_both_directions` RED — a row my
        # founding move had NOT falsified, because EP-28N later added a `container` row to the
        # enumeration that EP-28K's era does not contain. A §A57 sweep may touch only what this
        # pass falsified, and a class-level pin reached further than this pass's own change.
        # SUPERSEDED: the exclusion arithmetic alone, computed from the pack's STRUCTURE rather
        # than from a carried 72 — §A51's doctrine applied to the row that was carrying one, so
        # the live per-op assertion below keeps its full reach over every op that ships.
        # REMAINS TRUE: every excluded op declares no binding row, checked LIVE, including the
        # two this pass added. GIVEN UP: nothing.
        #
        # AND THE ARITHMETIC BELOW IS NOT THE TAUTOLOGY IT LOOKS LIKE, stated because a reader
        # who takes it for one will delete it. |ops - ENUM| == |ops| - |ENUM| holds exactly
        # when ENUM is a SUBSET of ops, so the line asserts that every enumerated op is STILL
        # IN THE PACK and reds if one is ever retired. Driven as a red world in this pass's own
        # file at tests/test_ep29.py::TheEP28KExclusionArithmeticCanStillFail rather than
        # asserted here, because §A57's fence permits no new row in THIS file.]
        excluded = set(self.ops) - set(ENUMERATED_ROWS)
        self.assertEqual(len(excluded), len(self.ops) - len(ENUMERATED_ROWS))
        for name in sorted(excluded):
            self.assertEqual(declared_rows(self.ops[name]), [], name)

    def test_MOUNT_is_excluded_by_structure_and_not_by_anybody_remembering(self):
        """`MOUNT` mints the mount root — the one inode no record describes (EP-28C
        AMENDMENT 7.2) — and it is out of this enumeration because it cites FS-LAW-MOUNT, not
        the namespace law. Named because it is the op a hyphen once hid, and because its
        adjacency is raised rather than taken."""
        self.assertEqual(self.ops["MOUNT"]["law_cited"], "FS-LAW-MOUNT")
        self.assertEqual(declared_rows(self.ops["MOUNT"]), [])

    def test_every_declared_key_param_is_a_parameter_the_op_actually_takes(self):
        for name, rows in ENUMERATED_ROWS.items():
            d = self.ops[name]
            for key, _req, _eff, _of in rows:
                self.assertIn(key, (d.get("params") or {}), "%s / %s" % (name, key))

    def test_the_shipped_pack_validates_whole_under_the_new_clause(self):
        peers = dict(self.ops)
        for name, d in self.ops.items():
            opdefs.validate_definition_shape(_Door(), "FOUNDING", "SYSTEM", name, d, peers)
class _Live(unittest.TestCase):
    """A kernel composed from the SHIPPED founding and nothing else."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep28k-")
        self.record = os.path.join(self.dir, "record.jsonl")
        self.store, self.gate, self.views, self.blobs, self.subs = build_full_kernel(
            self.record, os.path.join(self.dir, "blobs"), os.path.join(self.dir, "vault"))

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def create(self, path, actor=OWNER):
        return self.gate.execute("FILE-CREATE", actor, {"path": path, "provenance": PROV})

    def acts_of(self, action, path=None, key="path"):
        return [e for e in self.store.by_action(action)
                if path is None or (e.get("payload") or {}).get(key) == path]


class TestTheCheckIsInTheRegion(_Live):
    """T-CHECK-IN-THE-REGION. Two in-flight creates of ONE path through the GATE.

    THE ROW DRIVES THE GATE, NOT THE PORT, deliberately: `src/bridge/` is outside this fence
    and its own precondition still stands, so a port-level drive would be measuring the thing
    this pass did not build. What is under test is whether the LAW makes check-then-act one
    unit."""

    def _race(self, path, n=2):
        start = threading.Barrier(n)
        out = []
        lock = threading.Lock()

        def one():
            start.wait()
            try:
                rec = self.gate.execute("FILE-CREATE", OWNER, {"path": path, "provenance": PROV})
                with lock:
                    out.append(("ok", rec["seq"]))
            except OpError as e:
                with lock:
                    out.append(("refused", e.rule))

        threads = [threading.Thread(target=one) for _ in range(n)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        return out

    def test_exactly_one_create_succeeds_and_the_other_refuses_citing_the_declared_check(self):
        out = self._race("/race.txt")
        self.assertEqual(len(out), 2, "non-vacuity: both callers ran and reported")
        self.assertEqual(sorted(k for k, _v in out), ["ok", "refused"])
        self.assertEqual([v for k, v in out if k == "refused"], [NAMESPACE_LAW],
                         "the refusal must cite the law the DECLARED CHECK names")
        self.assertEqual(len(self.acts_of("FILE-CREATE", "/race.txt")), 1,
                         "two callers, ONE recorded create")

    def test_the_refusal_is_a_full_record_and_names_the_op_it_refused(self):
        self.create("/x.txt")
        with self.assertRaises(OpError):
            self.create("/x.txt")
        refusals = [e for e in self.store.by_action("op-refused")
                    if (e.get("payload") or {}).get("op") == "FILE-CREATE"]
        self.assertEqual(len(refusals), 1)
        self.assertEqual(refusals[0]["rule_cited"], NAMESPACE_LAW)
        self.assertTrue(refusals[0]["refused"])

    def test_THE_RED_WORLD_the_check_lifted_OUT_of_the_region_reproduces_the_stop_two_shape(self):
        """§A42, and the red world is produced THROUGH the instrument rather than resembled:
        the same gate, the same op definitions, the same fold — with the liveness read taken
        BEFORE `execute` and the in-region check neutered, which is precisely the port's
        composition. Both callers pass, both record, and the row that would have caught it is
        the one this pass moved."""
        real = opdefs._binding_check
        opdefs._binding_check = lambda *a, **k: None
        try:
            path = "/lifted.txt"
            start = threading.Barrier(2)
            seen, lock, out = [], threading.Lock(), []

            def one():
                live = opdefs._live_bindings(self.store, self.views)   # the read, OUTSIDE
                with lock:
                    seen.append(path in live)
                start.wait()                                          # both reads done first
                if path in live:
                    with lock:
                        out.append("EEXIST")
                    return
                rec = self.gate.execute("FILE-CREATE", OWNER,         # the act, separately
                                        {"path": path, "provenance": PROV})
                with lock:
                    out.append(rec["seq"])

            threads = [threading.Thread(target=one) for _ in range(2)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
        finally:
            opdefs._binding_check = real
        self.assertEqual(seen, [False, False], "both callers read the name as free")
        self.assertNotIn("EEXIST", out, "neither caller was told the name was taken")
        self.assertEqual(len(self.acts_of("FILE-CREATE", "/lifted.txt")), 2,
                         "THE STOP-TWO SHAPE: one path, TWO records, nothing refused")

    def test_the_check_runs_where_the_region_is_held(self):
        """Structural, and it is the property the row above measures behaviourally: the check
        body observes the decide region held on its own thread. A check that could answer with
        the region released would be the port's composition wearing the gate's name."""
        from kernel.gate import decide_region_held
        held = []
        real = opdefs._binding_check

        def watched(*a, **k):
            held.append(decide_region_held())
            return real(*a, **k)

        opdefs._binding_check = watched
        try:
            self.create("/held.txt")
        finally:
            opdefs._binding_check = real
        # DOCUMENTED FLIP (EP-28N AMENDMENT 1, 2026-08-05): a create now runs TWO binding
        # checks — its own name and its container — so the observation list is two long. The
        # property is unchanged and is asserted the way it was meant: EVERY observation is
        # `True`, and the count is asserted separately so a check that stopped running could
        # not pass by leaving an empty list.
        self.assertEqual(len(held), 2, "both declared binding checks ran")
        self.assertEqual(set(held), {True}, "the declared check ran outside the decide region")


class TestNoPhantomAct(_Live):
    """T-NO-PHANTOM-ACT. IDEMPOTENCE IS REFUSED, and this is why in one row: it makes the
    STATE right and leaves the RECORD holding an act that did not happen."""

    def test_a_refused_create_appends_no_act_record_claiming_effect(self):
        """THE CLAIM IS ABOUT ACT-RECORDS, NOT ABOUT RECORD COUNT, and the difference is the
        row. A refusal is a full record AND the dual-audit mirror witnesses it, so the ledger
        grows by more than one — which is P7 working, not a phantom. What must not appear is a
        `FILE-CREATE` claiming an effect that did not occur."""
        first = self.create("/p.txt")
        before = len(self.store.all())
        with self.assertRaises(OpError):
            self.create("/p.txt")
        added = self.store.all()[before:]
        self.assertTrue(added, "non-vacuity: the refused act appended something")
        self.assertEqual([e["action"] for e in added if e["action"] in ENUMERATED_ROWS], [],
                         "a refused act appended a record claiming its own effect")
        self.assertEqual(len([e for e in added if e["action"] == "op-refused"]), 1)
        creates = self.acts_of("FILE-CREATE", "/p.txt")
        self.assertEqual([e["seq"] for e in creates], [first["seq"]],
                         "one name, one create record — no phantom act")

    def test_THE_RED_WORLD_an_idempotent_double_reds_the_phantom_act_clause_and_no_other(self):
        """The named wrong reference, driven. With the refusal removed the second create
        REPORTS SUCCESS and the served state is still correct — the fold binds one name to one
        identity either way — so the ONLY thing that moved is the record."""
        self.create("/i.txt")
        real = opdefs._binding_check
        opdefs._binding_check = lambda *a, **k: None
        try:
            self.create("/i.txt")                       # idempotent: no refusal, "success"
        finally:
            opdefs._binding_check = real
        self.assertEqual(len(self.acts_of("FILE-CREATE", "/i.txt")), 2,
                         "the phantom act: a second create recorded for one name")
        state = custody.fold(self.store.all())
        self.assertTrue(state.exists("/i.txt"),
                        "and the SERVED STATE is right, which is why nothing else reds")
        self.assertEqual(len(state.names), 2, "root plus the one node — one name, one node")


class TestAbsenceStaysAbsenceWhereNothingIsDeclared(_Live):
    """THE §11.1a CLAUSE, ASSERTED RATHER THAN STATED (EP-28K :111-112).

    §11.1a's ABSENCE membership was CONDITIONAL on nothing governing the outcome. A declared
    check supplies the law, so the classification changes because the fact that put it there
    changed — nothing in §11.1a is overturned. The bound is the half that has to be checked:
    an op declaring NO binding check keeps §11.1a's classification untouched. Without this
    row, conditional membership would reclassify the whole family by side effect."""

    def test_an_op_that_declares_no_binding_check_appends_nothing_on_the_same_condition(self):
        """`FILE-PERM` names a path that is not bound. It declares no binding check, so the
        gate asks no existence question and no refusal is recorded — §11.1a class 2, intact."""
        before = len(self.store.all())
        self.gate.execute("FILE-PERM", OWNER, {"path": "/nowhere.txt", "perm": "600",
                                               "provenance": PROV})
        after = self.store.all()
        self.assertEqual([e["action"] for e in after[before:]], ["FILE-PERM"],
                         "an undeclared op gained a refusal it never declared")

    def test_the_reclassification_reaches_exactly_the_ops_that_declare(self):
        defs = {n: (v.get("definition") or {}) for n, v in self.views.op_definitions().items()}
        declaring = {n for n, d in defs.items() if declared_rows(d)}
        self.assertEqual(declaring, set(ENUMERATED_ROWS))
        self.assertNotIn("FILE-PERM", declaring)
        self.assertNotIn("FILE-WRITE", declaring)

    def test_the_ports_own_absence_reads_are_RETIRED_and_the_conditional_half_is_not(self):
        """DOCUMENTED FLIP — EP-28C W4e, 2026-08-07. THE RETIRED CONSTRUCT THIS ROW WAS
        READING: two substring pins on `kernel_port.py` — the call site's banner "A POSIX
        PRECONDITION THE VIEW ANSWERS IS AN ABSENCE" and the text "def
        _posix_precondition" — under the claim "`src/bridge/` took ZERO LINES, so every
        outcome §11.1a classed as an absence at the PORT is still answered there, still
        appending nothing. The retirement is W4e's."

        W4e IS THIS PASS AND THE RETIREMENT LANDED, so the row asserts the other side of its
        own sentence. BOTH PINS ARE KEPT AND INVERTED rather than deleted, because a pin that
        simply disappears cannot tell a retirement from a rename.

        AND THE CLASS'S OWN CLAIM IS UNTOUCHED, which is why only this row moves: §11.1a's
        conditional membership still holds for an op that declares no binding check, and the
        two rows above assert it against the live gate. The retirement reaches the outcomes
        that GAINED a declaration and reaches nothing else."""
        src = open(PORT_PATH, encoding="utf-8").read()
        self.assertNotIn("A POSIX PRECONDITION THE VIEW ANSWERS IS AN ABSENCE", src)
        self.assertNotIn("def _posix_precondition", src)
        # NON-VACUITY: an assertion that two strings are absent passes just as well against
        # an empty file, a moved file, or a typo in the path. The subject is proven present.
        self.assertGreater(len(src), 1000, "the port's source was not read at all")
        self.assertIn("ERRNO_BY_ACT", src,
                      "the act-keyed table this pass's rendering rests on is gone too, so "
                      "the absences above are about the wrong file")
def _namespace_op_without_a_binding():
    """An op citing the namespace law that says nothing about what it does to a name — the
    class hazard, not an instance: the fold is built from these declarations, so an act that
    moves a name without declaring it makes every later existence check answer about a
    namespace it is not in."""
    return {"law_cited": NAMESPACE_LAW, "description": "a test-world namespace op",
            "params": {"path": "required"}, "object_param": "path",
            "payload_from": ["path"], "checks": []}


#: DOCUMENTED FLIP (EP-28N): a bind under this law must now say what CLASS it gives the name
#: it takes, so these synthetic ops declare one or the three doors refuse them — which is that
#: pass's class clause meeting this pass's own fixtures, exactly as EP-28K's clause met the
#: shipped pack. The class is a MADE-UP WORD on purpose: the engine holds no vocabulary of its
#: own, so a class it has never seen is admitted and compared like any other string.
_A_CLASS = {"literal": "a-thing-this-test-world-invented"}


def _namespace_op_with_a_binding():
    d = _namespace_op_without_a_binding()
    d["checks"] = [{"check": "binding", "key_param": "path", "require": "unbound",
                    "effect": "bind", "cite": NAMESPACE_LAW, "binds_kind": _A_CLASS}]
    # `path`: STRUCTURAL — a namespace path, safe inline (census: every file op classifies
    # `path` structural; this op's shape is inline via `object_param`/`payload_from`).
    # Classified ONLY here, on the ADMIT-intent op; the binding-less refusal fixture stays
    # unclassified — it refuses at the check-row leash, which runs before the vocabulary door.
    # [design/46 member-2 vocabulary door, archi :2956 RULING 1: per-field true nature.]
    d["structural_params"] = ["path"]
    return d


def _malformed(**over):
    row = {"check": "binding", "key_param": "path", "require": "unbound", "effect": "bind",
           "cite": NAMESPACE_LAW, "binds_kind": _A_CLASS}
    row.update(over)
    d = _namespace_op_without_a_binding()
    d["checks"] = [row]
    return d


class TestTheGuardAtThreeDoors(_Live):
    """T-GUARD-AT-THREE-DOORS. ONE VALIDATION, THREE DOORS (design/36 ADDENDUM I.3). A guard at
    two of three doors guards nothing, and the founding installer is the door all seventy-two
    live definitions actually came through."""

    def _peers(self):
        peers = {n: (v.get("definition") or {})
                 for n, v in self.views.op_definitions().items()}
        return peers

    def test_door_one_the_founding_installer_refuses_the_whole_founding(self):
        recs = [{"actor": "SYSTEM", "action": "CREATE-OP", "object": "op:NS",
                 "rule_cited": "CAP-IS-LAW",
                 "payload": {"kind": "op_definition", "name": "NS",
                             "definition": _malformed(require="maybe")}}]
        with self.assertRaises(FoundingIntegrityError) as raised:
            _validate(recs)
        self.assertIn("binding", str(raised.exception))
        self.assertIn("the whole founding is refused", str(raised.exception))

    def test_door_one_also_refuses_a_namespace_op_that_declares_NOTHING(self):
        """THE ABSENCE HALF, and it is the guard that closes the class rather than its
        members. The peers come from the pack itself, so the law whose acts move names is
        discovered rather than named in code."""
        recs = [r for r in _records(load_pack()) if r.get("action") == "CREATE-OP"]
        recs.append({"actor": "SYSTEM", "action": "CREATE-OP", "object": "op:NS",
                     "rule_cited": "CAP-IS-LAW",
                     "payload": {"kind": "op_definition", "name": "NS",
                                 "definition": _namespace_op_without_a_binding()}})
        with self.assertRaises(FoundingIntegrityError) as raised:
            _validate(recs)
        self.assertIn("declares no binding", str(raised.exception))

    def test_door_two_create_op_refuses_cited_and_recorded(self):
        before = len(self.store.by_action("op-refused"))
        with self.assertRaises(OpError) as raised:
            self.gate.execute("CREATE-OP", OWNER,
                              {"name": "NS", "definition": _namespace_op_without_a_binding()})
        self.assertEqual(raised.exception.rule, "AR-2")
        self.assertEqual(len(self.store.by_action("op-refused")), before + 1)
        self.assertFalse(self.gate.has("NS"))

    def test_door_three_amend_op_refuses(self):
        self.gate.execute("CREATE-OP", OWNER,
                          {"name": "NS", "definition": _namespace_op_with_a_binding()})
        self.assertTrue(self.gate.has("NS"))
        with self.assertRaises(OpError) as raised:
            self.gate.execute("AMEND-OP", OWNER,
                              {"name": "NS", "definition": _namespace_op_without_a_binding()})
        self.assertEqual(raised.exception.rule, "AR-2")

    def test_a_wellformed_namespace_op_is_admitted_at_all_three_doors(self):
        """The positive half: a guard whose only evidence is that nothing refused it has not
        been shown to admit anything either."""
        opdefs.validate_definition_shape(_Door(), "FOUNDING", "SYSTEM", "NS",
                                         _namespace_op_with_a_binding(), self._peers())
        self.gate.execute("CREATE-OP", OWNER,
                          {"name": "NS", "definition": _namespace_op_with_a_binding()})
        self.assertTrue(self.gate.has("NS"))

    def test_each_malformation_refuses_for_its_own_stated_reason(self):
        cases = {
            "names no key_param": _malformed(key_param=None),
            "which this operation does not take": _malformed(key_param="absent_param"),
            "is not a state a key can be in": _malformed(require="maybe"),
            "is not something an": _malformed(effect="rebind"),
            "requires nothing and does nothing": _malformed(require=None, effect=None),
        }
        for fragment, d in cases.items():
            with self.assertRaises(_Door.Refused) as raised:
                opdefs.validate_definition_shape(_Door(), "CREATE-OP", OWNER, "NS", d,
                                                 self._peers())
            self.assertIn(fragment, raised.exception.message, fragment)

    def test_THE_CAN_FAIL_CONTROL_the_guard_neutered_admits_the_malformed_definition(self):
        """Without this the passing rows above prove only that nothing refused, which is not
        the same as there being something that would."""
        real = opdefs._require_wellformed_binding
        opdefs._require_wellformed_binding = lambda *a, **k: None
        try:
            opdefs.validate_definition_shape(_Door(), "CREATE-OP", OWNER, "NS",
                                             _malformed(require="maybe"), self._peers())
        finally:
            opdefs._require_wellformed_binding = real
        with self.assertRaises(_Door.Refused):
            opdefs.validate_definition_shape(_Door(), "CREATE-OP", OWNER, "NS",
                                             _malformed(require="maybe"), self._peers())

    def test_the_installer_and_the_gate_run_the_SAME_function(self):
        self.assertIs(install_module.validate_definition_shape,
                      opdefs.validate_definition_shape)


class TestOneDerivationTwoReaders(_Live):
    """THE LEASH THIS POWER ARRIVES WITH (design-soul §2). The gate now answers "is this name
    bound?" and the port's namespace fold has always answered it. Two readers of one record is
    P2 working; two readers that DISAGREE is the failure, and it would present as lawful acts
    refused or racy acts admitted. So the equality is asserted over generated histories rather
    than assumed, and the two places they are known to differ are DRIVEN and declared."""

    def live_at_the_gate(self):
        """DOCUMENTED FLIP (EP-28N AMENDMENT 1, 2026-08-05): the DECLARED ROOT is subtracted
        here exactly as `live_at_the_port` has always subtracted it, because this class
        compares the two readers and a root present in one side's raw answer and stripped
        from the other's would make every comparison below false for a reason that is not a
        divergence. The root's arrival in the law's key set is asserted un-subtracted in the
        root row below, which that pass FLIPPED rather than adjusted."""
        return set(opdefs._live_bindings(self.store, self.views)) - {"/"}

    def live_at_the_port(self):
        return set(custody.fold(self.store.all()).names) - {"/"}

    def _history(self):
        """Every namespace shape the seven ops can make, including the ones that refuse."""
        g = self.gate.execute
        g("FILE-MKDIR", OWNER, {"path": "/d", "provenance": PROV})
        g("FILE-CREATE", OWNER, {"path": "/d/a", "provenance": PROV})
        g("FILE-CREATE", OWNER, {"path": "/b", "provenance": PROV})
        g("FILE-SYMLINK", OWNER, {"path": "/s", "target": "/b", "provenance": PROV})
        g("FILE-LINK", OWNER, {"target_path": "/b", "new_path": "/h", "provenance": PROV})
        g("FILE-RENAME", OWNER, {"path": "/h", "new_path": "/h2", "provenance": PROV})
        g("FILE-UNLINK", OWNER, {"path": "/h2", "provenance": PROV})
        g("FILE-CREATE", OWNER, {"path": "/h2", "provenance": PROV})     # re-create after unlink
        g("FILE-RENAME", OWNER, {"path": "/h2", "new_path": "/b",        # rename OVER a live name
                                 "provenance": PROV})
        for bad in (("FILE-CREATE", {"path": "/b"}),
                    ("FILE-UNLINK", {"path": "/gone"}),
                    ("FILE-RMDIR", {"path": "/gone"}),
                    ("FILE-RENAME", {"path": "/gone", "new_path": "/x"}),
                    ("FILE-LINK", {"target_path": "/gone", "new_path": "/x"}),
                    ("FILE-LINK", {"target_path": "/b", "new_path": "/b"})):
            with self.assertRaises(OpError):
                g(bad[0], OWNER, dict(bad[1], provenance=PROV))
        # DOCUMENTED FLIP (EP-28N). This line read `rmdir /d/a` and its comment said "rmdir a
        # file: lawful here" — TRUE under this pass's law, which asks only whether a name is
        # bound, and FALSE under EP-28N's, which asks what the name names. The sentence being
        # falsified is that pass's whole subject, so the act moves to a directory rather than
        # the assertion moving: the row's job is that every declared row is DRIVEN, and it is.
        # SECOND DOCUMENTED FLIP ON THE SAME LINE (EP-28N AMENDMENT 1, 2026-08-05). `/d`
        # holds `/d/a`, and that pass declares an rmdir's `contains` requirement — so the
        # directory has to be emptied before it is removed. The ACT moved again rather than
        # the assertion, for the reason above: the row's job is that every declared row is
        # DRIVEN, and emptying it drives one more of them.
        g("FILE-UNLINK", OWNER, {"path": "/d/a", "provenance": PROV})    # empty it first
        g("FILE-RMDIR", OWNER, {"path": "/d", "provenance": PROV})       # rmdir a DIRECTORY
        return self.live_at_the_gate()

    def test_the_two_readers_agree_over_a_history_that_uses_every_declared_row(self):
        gate = self._history()
        self.assertGreater(len(gate), 0, "non-vacuity: the world holds bound names")
        self.assertEqual(gate, self.live_at_the_port())

    def test_every_declared_row_was_actually_exercised_by_that_history(self):
        """A differential over a history that never drives a row proves nothing about it."""
        self._history()
        driven = {e["action"] for e in self.store.all() if e["action"] in ENUMERATED_ROWS}
        self.assertEqual(driven, set(ENUMERATED_ROWS))
        refused = {(e.get("payload") or {}).get("op")
                   for e in self.store.by_action("op-refused")}
        self.assertEqual(refused & set(ENUMERATED_ROWS), set(ENUMERATED_ROWS) - {"FILE-MKDIR",
                                                                                 "FILE-SYMLINK"})

    def test_THE_KNOWN_DIVERGENCE_the_root_IS_NOW_DECLARED_and_the_gate_is_TOLD(self):
        """DOCUMENTED FLIP (EP-28N AMENDMENT 1, 2026-08-05).

        WHAT IT SAID: `/` is the one inode no record describes; the port's fold seeds it, the
        gate reads the RECORD and has never been told about it, so the two readers diverge at
        the root and `FILE-RMDIR /` refuses for lack of a binding.

        WHAT CHANGED, AND IT IS THAT PASS'S WHOLE PREMISE: a hierarchy question needs a
        bottom, and the bottom is bound by NO act — so the LAW declares it, on the rule that
        governs the key space, and the fold seeds it from that declaration. The root is now in
        the law's key set. The record still describes no root: the declaration is law-data and
        not an act, so `custody.ROOT_INO`'s "one identity with no covering record" is
        untouched.

        AND THE DIVERGENCE IS NOT CLOSED, IT MOVED — asserted rather than left to be assumed.
        `FILE-RMDIR /` on an EMPTY world is still ADMITTED and still appends an act with no
        effect, because a declared root cannot be unbound. That is the same phantom-act shape
        this file's own class refuses, it is older than this pass, and it is RAISED there
        rather than closed here."""
        self.assertIn("/", opdefs._live_bindings(self.store, self.views),
                      "the law declares its key space's root")
        self.assertIn("/", custody.fold(self.store.all()).names)
        self.assertNotIn("/", [(e.get("payload") or {}).get("path") for e in self.store.all()],
                         "and no record describes it — the declaration is law-data, not an act")
        self.gate.execute("FILE-CREATE", OWNER, {"path": "/x", "provenance": PROV})
        with self.assertRaises(OpError) as raised:
            self.gate.execute("FILE-RMDIR", OWNER, {"path": "/", "provenance": PROV})
        self.assertEqual(raised.exception.rule, NAMESPACE_LAW)
        self.assertEqual(getattr(raised.exception, "requirement", None), "contains:empty",
                         "and the refusal is now the CONTAINS row rather than a missing bind")

    def test_AND_THE_ROOT_PHANTOM_ACT_IS_OLDER_THAN_THIS_PASS_AND_IS_NOT_CLOSED(self):
        """THE RESIDUAL, DRIVEN RATHER THAN DESCRIBED (EP-28N AMENDMENT 1, §A24). On an EMPTY
        world `FILE-RMDIR /` meets every declared requirement — the root is bound, it names a
        directory, it holds nothing — so it is ADMITTED and appends. It was admitted before
        this pass too, for the opposite reason: the root was absent from the key set, so the
        fold dropped the act's effect. Either way the record holds an act that changed
        nothing, which is the phantom shape `TestNoPhantomAct` refuses for every other key.

        WHAT THIS PASS DOES GUARANTEE is the half that would have been catastrophic: a
        declared root is NOT UNBOUND by such an act, so the key space keeps its bottom and
        every later act under it still has somewhere to land. Both halves asserted."""
        rec = self.gate.execute("FILE-RMDIR", OWNER, {"path": "/", "provenance": PROV})
        self.assertEqual(rec["action"], "FILE-RMDIR",
                         "an act nothing performed, appended — the residual, not a fix")
        self.assertIn("/", opdefs._live_bindings(self.store, self.views),
                      "and the root survives it: a declared root is not unbindable")
        self.gate.execute("FILE-CREATE", OWNER, {"path": "/still", "provenance": PROV})

    def test_THE_KNOWN_DIVERGENCE_IS_CLOSED_two_spellings_are_one_key_and_one_name(self):
        """DOCUMENTED FLIP (EP-28O, 2026-08-05). This row asserted THE SECOND DIVERGENCE and
        it is the one that mattered to whoever retires the port's read.

        WHAT IT SAID: the engine holds no path grammar, so `/a/` and `/a` are two keys to the
        law and ONE name to the namespace fold — the gate ADMITS the second create, the fold
        binds one name over the other, and the first node is left alive in the inode table
        with no name reaching it. That was measured, and it is what blocked EP-28N's eight.

        WHAT CHANGED: the law's key derivation now calls the fold's own `_norm`, so the two
        spellings are ONE key. The second create is REFUSED as the duplicate it always was,
        no orphan node is left, and the two readers this class exists to compare agree here
        as they do everywhere else. The drive is unchanged and the outcome is the opposite,
        which is what makes this a flip and not a deletion."""
        self.gate.execute("FILE-CREATE", OWNER, {"path": "/a", "provenance": PROV})
        with self.assertRaises(OpError) as raised:
            self.gate.execute("FILE-CREATE", OWNER, {"path": "/a/", "provenance": PROV})
        self.assertEqual(raised.exception.rule, NAMESPACE_LAW)
        self.assertEqual({"/a"}, self.live_at_the_gate(), "the gate holds ONE key")
        state = custody.fold(self.store.all())
        self.assertEqual(set(state.names) - {"/"}, {"/a"}, "and the fold holds that one name")
        self.assertEqual(len(state.inodes), 2,
                         "root plus ONE node: no second node is left with no name reaching it")
        self.assertEqual(len(self.acts_of("FILE-CREATE", "/a")), 1)
        self.assertEqual(len(self.acts_of("FILE-CREATE", "/a/")), 0,
                         "and NO act was recorded under the spelling that was refused")


class TestTheErrnoTheRefusalWillCarry(unittest.TestCase):
    """THE SEAM THIS PASS HANDS TO W4e, MEASURED RATHER THAN PREDICTED, and it is what §13
    says perishes: a wrong errno recorded into a conformance pin stops being cheap to fix.

    A declared refusal reaches userland through the rule it cites, and both mapping sources
    say EACCES for the namespace law: `kernel_port.ERRNO_BY_RULE` carries no row for it and
    falls back to EACCES, and the `rule-errno` pack declares EACCES. POSIX wants EEXIST on a
    create over a held name and ENOENT on an unlink of an absent one.

    IT IS INVISIBLE TODAY, WHICH IS THE WHOLE PROBLEM. The port's own precondition answers
    first and returns the right errno, so nothing anywhere shows the gap. It becomes visible —
    and pinnable — the moment that read retires, which is the very next item. The rows below
    drive both worlds so the difference is output rather than argument.

    [THE SEAM WAS TAKEN — EP-28C W4e, 2026-08-07. The paragraph above is kept as the record
    of what this pass handed on, and it is now history: the read RETIRED, so there is one
    world and not two, and the errno the refusal carries is observable through the real path
    with nothing suppressed. Both rows below flip accordingly and neither is deleted — a row
    that only ever measured a defect leaves no evidence the defect closed.]

    THE TEMPTATION THIS PASS REFUSED, named so the next reader does not re-find it: the check
    could have cited ROOT-NEG-6, which the pack maps to EEXIST, and the errno would have come
    out right. That is choosing a citation for the errno it produces rather than for the law
    that governs the act, and a record whose cited rule was picked to steer a return value is
    the audit answering the wrong question forever."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep28k-errno-")
        from bridge.mount import build_brain
        from bridge.kernel_port import KernelPort
        self.store, self.gate, self.views, self.blobs = build_brain(
            os.path.join(self.dir, "rec.jsonl"), os.path.join(self.dir, "blobs"))
        self.port = KernelPort(self.store, self.gate, self.views, self.blobs)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def wire(self, op, **kw):
        f = {"id": "1", "op": op, "class": "DECISION", "uid": "1000", "gid": "1000", "pid": "42"}
        f.update({k: str(v) for k, v in kw.items()})
        return self.port.handle(f, b"")[0]

    def test_the_caller_gets_the_posix_errno_with_no_test_side_mutation_at_all(self):
        """DOCUMENTED FLIP — EP-28C W4e, 2026-08-07. THE RETIRED CONSTRUCT THIS ROW WAS
        READING: nothing structural — it was NAMED for the retired construct
        (`with_the_ports_read_LIVE`) and its message said "the port's precondition is
        untouched by this pass". Both are repealed facts, and a row whose name asserts one is
        worse than a stale header, which merely lags.

        THE CLAIM IS UNCHANGED AND IS NOW STRONGER FOR BEING PLAINER: the caller gets the
        POSIX errno, through the real path, with nothing suppressed or wrapped anywhere. That
        is what distinguishes it from the row below, which drives two acts under one rule to
        prove the ACT key is deciding."""
        import errno as E
        self.assertEqual(self.wire("FILE-CREATE", path="/a"), 0)
        self.assertEqual(self.wire("FILE-CREATE", path="/a"), -E.EEXIST,
                         "the gate's declared check answers, and the act-keyed table renders")

    def test_with_the_ports_read_RETIRED_the_refusal_carries_THE_ACTS_OWN_ERRNO(self):
        """DOCUMENTED FLIP (EP-28N) — THIS ROW IS THE MEASUREMENT THAT MOVED, and it is kept
        in place rather than deleted because a row that only ever measured a defect leaves no
        evidence the defect closed (ADDENDUM M's discipline).

        AS WRITTEN BY EP-28K it asserted EACCES both ways and was named for it: the refusal
        reached userland through the RULE it cited, one rule governed both acts, and both
        mapping sources said EACCES where POSIX says EEXIST and ENOENT. That was the finding
        and §A56's own occasion.

        EP-28N RE-KEYED THE PORT'S RENDERING ON THE ACT, so the same two worlds now return
        what POSIX gives them. The rule the record cites is UNCHANGED — that is the point of
        the two keys — and `test_both_mapping_sources_agree_on_EACCES_so_neither_is_a_typo`
        below still passes UNTOUCHED, which is now this row's companion evidence rather than
        its corroboration: the rule-keyed sources still say EACCES, and the port no longer
        asks them.

        SECOND DOCUMENTED FLIP — EP-28C W4e, 2026-08-07. THE RETIRED CONSTRUCT THIS ROW WAS
        READING: `self.port._posix_precondition`, read into `real` and monkeypatched to a
        `lambda op, f: None` so the row could stand in W4e's world before W4e existed. That
        attribute is gone, so the read raised `AttributeError` while the row's own assertions
        would all have passed — which is exactly the shape AMENDMENT 11.1 item 4 named.

        W4e'S WORLD IS NOW THE ONLY WORLD. The suppression is deleted rather than kept as a
        no-op: a wrapper that stands for a variable nobody varies is a lie in the code. What
        the row asserts is untouched, and every assertion below is the one it always made."""
        import errno as E
        self.assertEqual(self.wire("FILE-CREATE", path="/a"), 0)
        again = self.wire("FILE-CREATE", path="/a")
        absent = self.wire("FILE-UNLINK", path="/gone")
        self.assertEqual(again, -E.EEXIST, "a refused create is EEXIST, keyed by the ACT")
        self.assertEqual(absent, -E.ENOENT, "a refused unlink of an absent name is ENOENT")
        self.assertNotEqual(again, -E.EACCES, "the rule-keyed answer is no longer taken")
        self.assertNotEqual(absent, -E.EACCES)
        self.assertNotEqual(again, absent,
                            "non-vacuity: ONE RULE governs both acts, so two different "
                            "answers is the whole claim and one answer would be the defect")

    def test_both_mapping_sources_agree_on_EACCES_so_neither_is_a_typo(self):
        from bridge.kernel_port import ERRNO_BY_RULE
        self.assertNotIn(NAMESPACE_LAW, ERRNO_BY_RULE,
                         "the port's table has no row for the namespace law, so it defaults")
        rows = [dict(l) for l in self.views.category_packs()["rule-errno"]["levels"]
                if l["rule"] == NAMESPACE_LAW]
        self.assertEqual([r["errno"] for r in rows], ["EACCES"])


class TestTheDiffIsTheChange(unittest.TestCase):
    """T-DIFF-IS-THE-CHANGE. The founding CHANGED — that is this pass's required outcome — and
    the proof is not stillness but the diff's exact shape, set-diffed BOTH directions against
    the pack as it stood at the commit this session opened at."""

    def setUp(self):
        # ERA-PINNED ON BOTH SIDES (EP-28N, §A57) — the NOW side was `load_pack()`.
        self.now = pack_ops(pack_at(EP28K_AFTER_COMMIT))
        self.before = pack_ops(pack_at(EP28K_BEFORE_COMMIT))

    def test_the_before_pack_is_the_one_the_dispatch_anchored(self):
        """Non-vacuity: a diff against the wrong BEFORE proves nothing, and against the wrong
        AFTER it proves something about somebody else's pass. Both anchors are the versions
        this pass's close recorded, checked before any difference is read."""
        self.assertEqual(pack_at(EP28K_BEFORE_COMMIT)["founding_version"], EP28K_BEFORE_VERSION)
        self.assertEqual(pack_at(EP28K_AFTER_COMMIT)["founding_version"], EP28K_AFTER_VERSION)
        self.assertEqual(len(self.before), DECLARED_POPULATION)

    def test_exactly_the_enumerated_definitions_moved_and_nothing_else(self):
        moved = {n for n in self.now if self.now[n] != self.before.get(n)}
        self.assertEqual(moved - CHANGED_DEFINITIONS, set(),
                         "a definition outside the enumeration changed")
        self.assertEqual(CHANGED_DEFINITIONS - moved, set(),
                         "an enumerated definition did not change")

    def test_the_only_difference_in_each_moved_definition_is_its_checks_list(self):
        for name in sorted(CHANGED_DEFINITIONS):
            now, before = dict(self.now[name]), dict(self.before[name])
            self.assertEqual(before.get("checks"), [], name)
            now.pop("checks"), before.pop("checks")
            self.assertEqual(now, before, name)

    def test_no_op_was_added_or_removed(self):
        self.assertEqual(set(self.now), set(self.before))

    def test_nothing_outside_the_op_definitions_moved(self):
        """The pack holds rules, packs, views, actors and a grant as well as ops. A change
        list naming ops proves nothing about them unless they are diffed too."""
        def non_ops(pack):
            return [r for r in _records(pack) if r.get("action") != "CREATE-OP"]
        self.assertEqual(non_ops(pack_at(EP28K_AFTER_COMMIT)), non_ops(pack_at(EP28K_BEFORE_COMMIT)))


class TestTheVersionMoves(unittest.TestCase):
    """T-VERSION-MOVES. MINOR, on the discriminator EP-28I filed: does the version tell a
    reader they must RE-READ THE LAW before writing against it? A new declared check kind plus
    a new REFUSAL is law-surface; nothing existing breaks, because the ops gain declarations
    this pass writes and the port's duplicate checks are untouched until W4e retires them.

    ERA-PINNED BY EP-28N UNDER §A57 [documented flip]. These rows read the LIVE pack and the
    LIVE world, so they asserted what the founding IS rather than what THIS PASS moved it to —
    and the next lawful move reddened them for describing an accepted past correctly. The base
    class went with the pin: a live world is no longer needed to read a pinned document."""

    def test_the_pack_declares_the_new_version(self):
        self.assertEqual(pack_at(EP28K_AFTER_COMMIT)["founding_version"], EP28K_AFTER_VERSION)

    def test_the_installer_stamps_it_into_the_founding_designation(self):
        """Driven on a world founded from THIS PASS'S pack, by the era-pinning idiom
        `TestEraPinnedWorldsAreUntouched` uses: the stamping is a property of the installer
        meeting a version, and pinning the version is what keeps the property from being
        re-stated as a claim about whatever ships next."""
        era = pack_at(EP28K_AFTER_COMMIT)
        d = tempfile.mkdtemp(prefix="ep28k-ver-")
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
        self.assertEqual((fs.get("payload") or {}).get("founding_version"), EP28K_AFTER_VERSION)

    def test_J9_the_same_version_may_not_name_two_distinct_foundings(self):
        """RE-PROVEN, not assumed: the guard is the log-side instrument, and it answers about
        the bytes on disk rather than about a field the pack declares about itself.

        VERSION-AGNOSTIC SINCE EP-28N [documented flip], AND THE REPAIR IS A SECOND INSTANCE
        OF ONE EP-28I ALREADY MADE. J9's standing property is not about any pass's number: it
        is that the founding ON DISK, at whatever version, is named with its own sha256 in one
        log entry. EP-28I's builder repaired exactly this row in exactly this way and wrote
        down why; this pass's copy re-introduced the pin. The repair was applied to an
        INSTANCE and not to the CLASS, which is why it had to be made twice."""
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


class TestEraPinnedWorldsAreUntouched(unittest.TestCase):
    """THE TWO-TIMES LAW, driven. A founding change reaches FOUNDINGS; the record is never
    rewritten. A world founded under the BEFORE pack carries ITS definitions, so no binding is
    declared there, no check runs, and the acts this law would refuse are still admitted —
    which is what "acts stand under the law of their deciding time" means when it is a
    property of the machine rather than a sentence."""

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="ep28k-era-")
        self.pack = pack_at(EP28K_BEFORE_COMMIT)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def _era_world(self):
        """The era-pinning idiom is `tests/test_ep14.py`'s: the module-global READER is
        repointed for the call and restored. Repointing `PACK_PATH` does NOT work and the
        reason is worth one line, because it fails silently into the LIVE pack: `load_pack`'s
        path default is bound at definition time, so a later assignment to the module global
        changes nothing and the world founds at whatever ships."""
        saved = install_module.load_pack
        install_module.load_pack = lambda path=None: self.pack
        try:
            return build_full_kernel(os.path.join(self.dir, "record.jsonl"),
                                     os.path.join(self.dir, "blobs"),
                                     os.path.join(self.dir, "vault"))
        finally:
            install_module.load_pack = saved

    def test_a_world_founded_at_the_old_law_declares_no_binding_and_refuses_nothing(self):
        store, gate, views, _blobs, _subs = self._era_world()
        self.assertEqual(
            (store.by_action("FOUND-STORE")[0]["payload"] or {}).get("founding_version"),
            EP28K_BEFORE_VERSION)
        defs = {n: (v.get("definition") or {}) for n, v in views.op_definitions().items()}
        self.assertEqual({n for n, d in defs.items() if declared_rows(d)}, set())
        self.assertEqual(opdefs._live_bindings(store, views), frozenset(),
                         "no declaration, no fold — the law reaches foundings, not records")
        gate.execute("FILE-CREATE", OWNER, {"path": "/e.txt", "provenance": PROV})
        gate.execute("FILE-CREATE", OWNER, {"path": "/e.txt", "provenance": PROV})
        self.assertEqual(len([e for e in store.by_action("FILE-CREATE")
                              if (e["payload"] or {}).get("path") == "/e.txt"]), 2,
                         "the old law's world still admits what the new law refuses")


if __name__ == "__main__":
    unittest.main()
