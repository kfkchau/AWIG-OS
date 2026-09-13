# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: conformance-harness ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-28M — THE DOOR CENSUS.

§A55 asks a standing question after any safety fix: WHAT ELSE REACHES THE SAME
SUBJECT BY A DIFFERENT PATH? This module answers it for the conformance
instrument, and the METHOD is the point.

THE CENSUS IS READ FROM THE HARNESS'S OWN STRUCTURE, NEVER FROM THE DOORS
FINDINGS HAPPENED TO NAME. §A51: an enumeration over a structured artifact
reads the STRUCTURE, not a list someone already had. A census built from the
three known doors would find exactly three by construction and prove nothing —
so the three are this census's FLOOR and its CROSS-CHECK, set-diffed against it
in both directions, and never its source.

Two enumerations, both computed from the AST:

  CENSUS A — ARTIFACT REACH.  Every function operating on a value derived from
  `baselines.baseline_dir`, classified WRITE or READ by the operations it
  performs on that value. Completeness rests on a measured property rather than
  on a promise: `BASELINES_DIR` is referenced inside exactly ONE function, so
  `baseline_dir` is the sole constructor of a path into the pinned tree and
  every reach passes through it.

  CENSUS B — VERDICT REACH.  Every function mentioning the verdict vocabulary,
  with (i) the collections it answers over without proving them non-empty —
  §A38's shape, which is what every door in this lineage has been — and (ii)
  every branch that answers NOT-RUN on an ABSENCE, which is how a leg declines
  without failing.

Each computed member carries a DECLARED disposition: CLOSED (which pass, which
clause), OPEN (raised, with a home), or NOT-A-DOOR (with its structural reason).
The test reds when the computed set and the declared set differ in EITHER
direction — so a fourth path appearing in the code cannot pass unnoticed, and a
declared member vanishing from the code cannot either.

RED WORLDS, both directions (§A42):
  * a census double built from the three known doors alone REDS, because the
    code holds a fourth;
  * a synthetic extra path injected into a COPY of the harness is FOUND, so the
    census cannot miss by construction.
"""

import ast
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HARNESS = REPO / "tools" / "conformance" / "harness"

if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

#: Operations that MUTATE the thing they are called on. A member performing any
#: of these on a baseline path is a WRITE path into a pinned artifact.
MUTATORS = frozenset({
    "mkdir", "write_text", "write_bytes", "unlink", "rmdir", "touch",
    "symlink_to", "hardlink_to", "rename", "replace", "chmod",
})
VERDICT_VOCAB = frozenset({"PASS", "FAIL", "NOT_RUN"})
VERDICT_ACCESSORS = frozenset({"verdict", "failed", "ok", "failed_checks"})


# ---------------------------------------------------------------------------
# the computation — AST, not grep, because the question is about STRUCTURE
# ---------------------------------------------------------------------------


def _leftmost_name(node):
    """The name a path-shaped expression is rooted at: `d`, `d / n`,
    `(d / n).parent`, `d.foo()` all root at `d`."""
    while True:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            node = node.value
        elif isinstance(node, ast.BinOp):
            node = node.left
        elif isinstance(node, ast.Subscript):
            node = node.value
        elif isinstance(node, ast.Call):
            node = node.func
        else:
            return None


def _functions(tree, module):
    out = {}

    def walk(node, prefix):
        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                out["%s.%s" % (prefix, child.name)] = child
                walk(child, "%s.%s" % (prefix, child.name))
            elif isinstance(child, ast.ClassDef):
                walk(child, "%s.%s" % (prefix, child.name))

    walk(tree, module)
    return out


def _harness_functions(root):
    fns = {}
    for p in sorted(Path(root).glob("*.py")):
        fns.update(_functions(ast.parse(p.read_text()), p.stem))
    return fns


def _ops_on(fn, seeds):
    """Every attribute call made on a value derived from `seeds`, plus the
    (callee, argument position) pairs such a value is handed into.

    Taint propagates through `/`, attribute access and subscripting — all of
    which keep a path a path — and STOPS at a call, because a call on a path
    returns something that is not one (`read_text()` is content, not a path).
    """
    tainted = set(seeds)
    for _ in range(8):
        grew = False
        for node in ast.walk(fn):
            if isinstance(node, ast.Assign) and not isinstance(node.value, ast.Call):
                if _leftmost_name(node.value) in tainted:
                    for t in node.targets:
                        if isinstance(t, ast.Name) and t.id not in tainted:
                            tainted.add(t.id)
                            grew = True
        if not grew:
            break
    ops, handed_to = set(), []
    for node in ast.walk(fn):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Attribute) and _leftmost_name(node.func.value) in tainted:
            ops.add(node.func.attr)
        for i, arg in enumerate(node.args):
            if _leftmost_name(arg) in tainted:
                handed_to.append((ast.unparse(node.func), i))
    return ops, handed_to


def _resolve(callee, fns):
    tail = callee.split(".")[-1]
    for q in sorted(fns):
        if q.split(".")[-1] == tail:
            return q
    return None


def census_a(root):
    """ARTIFACT REACH, and the sole-constructor property it rests on."""
    fns = _harness_functions(root)

    holders = sorted(
        q for q, fn in fns.items()
        if any(isinstance(n, ast.Name) and n.id == "BASELINES_DIR" for n in ast.walk(fn))
    )

    members, frontier = {}, []
    for q, fn in fns.items():
        seeds = {
            t.id
            for n in ast.walk(fn)
            if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call)
            and _resolve(ast.unparse(n.value.func), {"x.baseline_dir": None}) is not None
            and ast.unparse(n.value.func).split(".")[-1] == "baseline_dir"
            for t in n.targets if isinstance(t, ast.Name)
        }
        if not seeds:
            continue
        ops, handed = _ops_on(fn, seeds)
        members[q] = {"how": "calls baseline_dir", "ops": tuple(sorted(ops)),
                      "kind": "WRITE" if ops & MUTATORS else "READ"}
        frontier.extend((q, h) for h in handed)

    for _round in range(4):
        nxt = []
        for src, (callee, pos) in frontier:
            target = _resolve(callee, fns)
            if target is None or target in members:
                continue
            args = fns[target].args.args
            if pos >= len(args):
                continue
            ops, handed = _ops_on(fns[target], {args[pos].arg})
            if not ops:
                continue
            members[target] = {"how": "given a baseline path by %s" % src,
                               "ops": tuple(sorted(ops)),
                               "kind": "WRITE" if ops & MUTATORS else "READ"}
            nxt.extend((target, h) for h in handed)
        if not nxt:
            break
        frontier = nxt
    return {"sole_constructor": holders, "members": members}


def _collection_of(node):
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return ast.unparse(node.operand)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("any", "all"):
        inner = node.args[0] if node.args else None
        if isinstance(inner, (ast.GeneratorExp, ast.ListComp)):
            return "%s(%s)" % (node.func.id, ast.unparse(inner.generators[0].iter))
        return "%s(%s)" % (node.func.id, ast.unparse(inner)) if inner is not None else None
    if isinstance(node, (ast.ListComp, ast.GeneratorExp, ast.SetComp)):
        return ast.unparse(node.generators[0].iter)
    return None


def _proven_non_empty(fn):
    out = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.If) and isinstance(node.test, ast.UnaryOp) and isinstance(node.test.op, ast.Not):
            if any(isinstance(s, (ast.Raise, ast.Return)) for s in node.body):
                out.add(ast.unparse(node.test.operand))
    return out


def _answers_not_run_on_absence(fn):
    """Branches that answer NOT-RUN because something is ABSENT. This is how a
    leg DECLINES without failing, and a decline that reaches the run's answer
    unchanged is the shape of every door in this lineage."""
    out = set()
    for node in ast.walk(fn):
        if not isinstance(node, ast.If):
            continue
        test = ast.unparse(node.test)
        absence = (
            (isinstance(node.test, ast.UnaryOp) and isinstance(node.test.op, ast.Not))
            or (isinstance(node.test, ast.Compare)
                and any(isinstance(c, ast.Is) for c in node.test.ops)
                and "None" in ast.unparse(node.test.comparators[0]))
            or "all(" in test
        )
        if not absence:
            continue
        for stmt in ast.walk(node):
            if isinstance(stmt, ast.Return) and stmt.value is not None:
                if "NOT_RUN" in ast.unparse(stmt.value):
                    out.add(test)
    return out


def census_b(root):
    """VERDICT REACH: every verdict site, what it aggregates over unproven, and
    where it answers NOT-RUN on an absence."""
    found = {}
    for q, fn in _harness_functions(root).items():
        is_site = any(
            (isinstance(n, ast.Name) and n.id in VERDICT_VOCAB)
            or (isinstance(n, ast.Attribute) and n.attr in (VERDICT_VOCAB | VERDICT_ACCESSORS))
            for n in ast.walk(fn)
        )
        if not is_site:
            continue
        proven = _proven_non_empty(fn)
        sites = []
        for node in ast.walk(fn):
            if isinstance(node, ast.Return) and node.value is not None:
                sites.append(node.value)
            elif isinstance(node, (ast.If, ast.IfExp)):
                sites.append(node.test)
        unproven = set()
        for site in sites:
            for sub in [site] + list(ast.walk(site)):
                coll = _collection_of(sub)
                if coll is None:
                    continue
                bare = coll.split("(", 1)[1][:-1] if coll.startswith(("any(", "all(")) else coll
                if bare not in proven:
                    unproven.add(coll)
        found[q] = {
            "aggregates_unproven": tuple(sorted(unproven)),
            "proven_non_empty": tuple(sorted(proven)),
            "not_run_on_absence": tuple(sorted(_answers_not_run_on_absence(fn))),
        }
    return found


# ---------------------------------------------------------------------------
# THE DECLARED CENSUS — every computed member, with its disposition
# ---------------------------------------------------------------------------

CLOSED, OPEN, NOT_A_DOOR = "CLOSED", "OPEN", "NOT-A-DOOR"

#: CENSUS A — every path reaching a pinned artifact.
DECLARED_A = {
    "baselines.write_capture": (
        "WRITE", CLOSED,
        "DOOR 1 and DOOR 3's write half. EP-28L: a capture matching zero groups "
        "STOPS before resolving a path. EP-28M: a capture that would leave a held "
        "file unnamed STOPS before mkdir and before every write_text.",
    ),
    "baselines.load": (
        "READ", CLOSED,
        "DOOR 1 and DOOR 3's read half. EP-28L: an empty `files` map REFUSES. "
        "EP-28M: a file the map names nowhere REFUSES; the other direction — a "
        "name with no file — is the per-file check inside the sum loop.",
    ),
    "baselines.artifact_members": (
        "READ", NOT_A_DOOR,
        "EP-28M's own accounting helper. It reads a directory listing and "
        "performs no mutation and no verdict; it is one side of the accounting "
        "the two members above enforce.",
    ),
}

#: CENSUS B — every verdict site. The two facts recorded per member are what the
#: computation returns; the disposition is this pass's reading of them.
DECLARED_B = {
    "runner.Report.ok": (
        CLOSED,
        "DOOR 2. EP-28M: `ok` REFUSES over an empty verdict list, at the site "
        "that manufactures the vacuous answer rather than at its caller.",
    ),
    "runner.Report.failed": (
        NOT_A_DOOR,
        "The filter `ok` is computed from. Its emptiness is answered one level "
        "up, where the answer is given — guarding both would be one condition "
        "spelled twice.",
    ),
    "runner.Report.summary": (
        NOT_A_DOOR,
        "Counts for the report text. It states the NOT-RUN tally rather than "
        "absorbing it, and no exit code is derived from it.",
    ),
    "runner.Report.text": (
        NOT_A_DOOR,
        "Rendering. It carries every count to the reader, including the ones "
        "the run's answer ignores — which is why DOOR 4 below is visible in the "
        "text and invisible in the exit code.",
    ),
    "runner._dispatch": (
        CLOSED,
        "The exit register. `0 if report.ok else 1` now reads a guarded `ok`, and "
        "EP-28M added `SelectionError` and `BaselineError` to `main`'s refusal "
        "clause so a refusal exits 2 rather than 1.",
    ),
    "checks.CheckResult.failed": (
        NOT_A_DOOR,
        "One leg's own verdict, compared to a constant. It aggregates nothing.",
    ),
    "checks.RowVerdict.failed_checks": (
        NOT_A_DOOR,
        "Reporting only: the names of a row's failing legs. Nothing derives a "
        "verdict or an exit code from it.",
    ),
    "checks.RowVerdict.verdict": (
        OPEN,
        "DOOR 4 — RAISED, NOT CLOSED, and this pass's fence forbids closing it "
        "(EP-28M RAISED-BY-DESIGN). A row whose legs all declined verdicts "
        "NOT-RUN, and a row whose pin-comparing leg declined while another leg "
        "passed verdicts PASS. Either way no leg FAILED, so `Report.ok` is TRUE "
        "and the run exits 0. HOME: the pass that rules what coverage a run must "
        "prove before it may answer.",
    ),
    "checks.check_abi": (
        OPEN,
        "DOOR 4's ENTRANCE, and the one that matters: `baseline is None` answers "
        "NOT-RUN, so a selected row absent from the pinned artifact is never "
        "compared to anything. NOT REACHABLE TODAY AND THE FIGURE IS TAKEN, NOT "
        "REASONED TO: every one of the 40 active probe-carrying rows is pinned "
        "in BOTH committed baselines, measured both directions. It becomes "
        "reachable the moment a governed target declares root — `host-local` "
        "does not pin `files.mount#root` or `files.umount#root`, and every "
        "governed target declares no capabilities today — or the moment the row "
        "set grows past a baseline. The manifest's `skipped` list records why "
        "each was not captured and NOTHING AT VERIFY TIME READS IT. "
        "HOME: with the row above.",
    ),
    "checks.check_recording_class": (
        OPEN,
        "DOOR 4's second entrance: `attribution is None` answers NOT-RUN when "
        "the target exposes no record. A governed target with no record source "
        "passes the vocabulary check (which fires only when a record IS exposed) "
        "and is then judged on the ABI leg alone. HOME: with the row above.",
    ),
    "checks.check_replay": (
        OPEN,
        "DOOR 4's third entrance: `replayed_state is None` answers NOT-RUN when "
        "the target offers no replay. HOME: with the row above.",
    ),
}

#: THE THREE KNOWN DOORS — the census's FLOOR and its CROSS-CHECK, never its
#: source. Each names the census member it lands on.
KNOWN_DOORS = {
    "DOOR 1 — capture over a pin": "baselines.write_capture",
    "DOOR 2 — verify over an empty selection": "runner.Report.ok",
    "DOOR 3 — the valid-but-partial group set": "baselines.load",
}


class TestTheDoorCensus(unittest.TestCase):
    """T-DOOR-CENSUS. Every code path reaching a pinned artifact or computing a
    verdict over one, enumerated from the harness's structure."""

    def test_baseline_dir_is_the_SOLE_constructor_of_a_pinned_path(self):
        """The property completeness rests on. If `BASELINES_DIR` were read
        anywhere else, a reach could bypass `baseline_dir` and CENSUS A would be
        a list of the reaches that happen to use the front door."""
        a = census_a(HARNESS)
        self.assertEqual(
            a["sole_constructor"], ["baselines.baseline_dir"],
            "more than one function constructs a path into the pinned tree",
        )

    def test_CENSUS_A_matches_its_declaration_in_both_directions(self):
        computed = census_a(HARNESS)["members"]
        self.assertEqual(
            set(computed), set(DECLARED_A),
            "CENSUS A drifted: computed-not-declared=%s declared-not-computed=%s"
            % (sorted(set(computed) - set(DECLARED_A)), sorted(set(DECLARED_A) - set(computed))),
        )
        for name, info in sorted(computed.items()):
            self.assertEqual(info["kind"], DECLARED_A[name][0], "%s changed kind" % name)

    def test_CENSUS_A_holds_exactly_one_WRITE_path(self):
        """The whole capture-side hazard has ONE door into it, and that is a
        measured fact rather than a design intention."""
        computed = census_a(HARNESS)["members"]
        writes = sorted(q for q, i in computed.items() if i["kind"] == "WRITE")
        self.assertEqual(writes, ["baselines.write_capture"])

    def test_CENSUS_B_matches_its_declaration_in_both_directions(self):
        computed = census_b(HARNESS)
        self.assertEqual(
            set(computed), set(DECLARED_B),
            "CENSUS B drifted: computed-not-declared=%s declared-not-computed=%s"
            % (sorted(set(computed) - set(DECLARED_B)), sorted(set(DECLARED_B) - set(computed))),
        )

    def test_the_run_level_answer_now_proves_its_SUBJECT_and_the_row_level_one_does_not(self):
        """The residual, stated as a measurement rather than inferred.

        The subject `ok` must prove non-empty is `self.verdicts` — the set the
        answer is computed over. `not self.failed` stays an aggregation over an
        unproven collection AND THAT IS CORRECT: an empty `failed` is what
        "nothing failed" MEANS, and requiring it non-empty would require a
        failure. This distinction is the whole of §A38 — the subject, not the
        answer — and the computation held it against a first draft of this row
        that asserted the wrong one."""
        computed = census_b(HARNESS)
        self.assertIn("self.verdicts", computed["runner.Report.ok"]["proven_non_empty"])
        self.assertEqual(computed["runner.Report.ok"]["aggregates_unproven"], ("self.failed",))
        row = computed["checks.RowVerdict.verdict"]
        self.assertIn("any(self.results)", row["aggregates_unproven"])
        self.assertEqual(row["proven_non_empty"], (), "DOOR 4's site proves nothing")

    def test_the_NOT_RUN_sources_are_enumerated_rather_than_remembered(self):
        """Three legs decline on an absence, and a fourth site absorbs the
        declines. Computed, so a fifth cannot be added silently."""
        computed = census_b(HARNESS)
        decliners = sorted(q for q, i in computed.items() if i["not_run_on_absence"])
        self.assertEqual(
            decliners,
            ["checks.RowVerdict.verdict", "checks.check_abi",
             "checks.check_recording_class", "checks.check_replay"],
        )
        self.assertIn("baseline is None", computed["checks.check_abi"]["not_run_on_absence"])


class TestTheKnownDoorsAreTheFloorAndNotTheSource(unittest.TestCase):
    """The three known doors are set-diffed against the census in BOTH
    directions. A census that came out at exactly three would have proved
    nothing except that it was built from the three."""

    def test_every_known_door_lands_on_a_census_member(self):
        members = set(census_a(HARNESS)["members"]) | set(census_b(HARNESS))
        missing = {d: m for d, m in KNOWN_DOORS.items() if m not in members}
        self.assertEqual(missing, {}, "a known door lands on no census member")

    def test_the_census_is_NOT_exhausted_by_the_three_known_doors(self):
        """The direction that matters. A fourth door found here is this pass
        succeeding."""
        declared_doors = (
            {q for q, v in DECLARED_A.items() if v[1] in (CLOSED, OPEN)}
            | {q for q, v in DECLARED_B.items() if v[0] in (CLOSED, OPEN)}
        )
        beyond = declared_doors - set(KNOWN_DOORS.values())
        self.assertTrue(
            beyond,
            "the census found exactly the three doors it was cross-checked "
            "against, which is what a census built from a list looks like",
        )

    def test_the_OPEN_members_are_raised_with_a_home_and_none_is_closed_here(self):
        """EP-28M RAISED-BY-DESIGN: an OPEN door the census finds is raised,
        never closed opportunistically inside this fence. The row enforces that
        every OPEN member carries a home rather than a promise."""
        opens = {q: v for q, v in DECLARED_B.items() if v[0] == OPEN}
        self.assertTrue(opens, "no OPEN member — see the row above")
        for q, (_status, reason) in sorted(opens.items()):
            self.assertIn("HOME:", reason, "%s is OPEN with no home" % q)

    def test_the_doors_this_pass_closed_are_named_individually(self):
        """§A55: an acceptance names WHICH DOOR it closed, never the procedure
        it sits in. Structural, so the claim cannot widen in prose."""
        closed_here = sorted(
            q for q, v in list(DECLARED_A.items())
            if v[1] == CLOSED and "EP-28M" in v[2]
        ) + sorted(
            q for q, v in DECLARED_B.items()
            if v[0] == CLOSED and "EP-28M" in v[1]
        )
        self.assertEqual(
            closed_here,
            ["baselines.load", "baselines.write_capture",
             "runner.Report.ok", "runner._dispatch"],
        )


class TestDoorFourIsRaisedWithItsReachabilityMEASURED(unittest.TestCase):
    """DOOR 4 is RAISED, not closed — EP-28M's fence forbids closing an OPEN
    door the census finds. What this row adds is the half a raise usually
    lacks: the residual stated as a MEASUREMENT that reds when it goes live,
    rather than as prose a later reader has to re-derive.

    §A51's second half: a completeness figure in prose, against a subject the
    reader computes, is unfalsifiable. This row computes it."""

    def _sets(self):
        import json

        from tools.conformance.harness import rows as rows_mod

        _groups, all_rows = rows_mod.load_all()
        active = [r for r in all_rows if r.active]
        probed = {r.row_id for r in active if r.has_probe}
        root_probed = {r.row_id + "#root" for r in active if r.has_root_probe}
        pinned = {}
        for name in ("host-local", "ep21-ubuntu-guest"):
            path = REPO / "tools" / "conformance" / "baselines" / name / "06-files.json"
            pinned[name] = set(json.loads(path.read_text())["rows"])
        return probed, root_probed, pinned

    def test_every_probe_carrying_active_row_is_PINNED_in_both_baselines(self):
        """The measurement, both directions. While it holds, DOOR 4's
        unprivileged entrance is unreachable; when it stops holding, this row
        reds and names the rows that made it reachable."""
        probed, _root, pinned = self._sets()
        self.assertEqual(len(probed), 40, "the probed population moved")
        for name, keys in sorted(pinned.items()):
            self.assertTrue(keys, "%s pins N > 0 rows" % name)
            self.assertEqual(
                probed - keys, set(),
                "%s does not pin %s — DOOR 4's `baseline is None` branch is now "
                "REACHABLE through them, and a verify naming one reports PASS or "
                "NOT-RUN on a row it never compared to anything"
                % (name, sorted(probed - keys)),
            )

    def test_a_real_verify_carries_NO_declined_legs_TODAY(self):
        """The bound on DOOR 4's raise, landed as a row because it was run as a
        probe while the entry was being written.

        The raise says closing DOOR 4 is a COVERAGE POLICY rather than a
        subject-emptiness guard, and the honest question about any such policy
        is what it would red. Measured here rather than estimated: a real verify
        against the one governed target drivable on this box returns every leg
        PASS and no leg NOT-RUN. **When that stops being true this row reds, and
        the raise's bound has moved.**"""
        from tools.conformance.harness import runner as runner_mod

        base = REPO / "tools" / "conformance"
        report = runner_mod.verify(
            "fixture-correct", "host-local",
            rows_dir=base / "rows", baselines_base=base / "baselines",
            targets_dir=base / "targets",
            row_ids=["files.mkdir", "files.write", "files.open"],
        )
        summary = report.summary()
        self.assertEqual(summary["rows"], {"PASS": 3, "FAIL": 0, "NOT-RUN": 0})
        declined = sum(c["NOT-RUN"] for c in summary["legs"].values())
        total = sum(sum(c.values()) for c in summary["legs"].values())
        self.assertEqual(total, 9, "three rows, three legs each")
        self.assertEqual(
            declined, 0,
            "%d of %d leg results now DECLINE, so a policy failing a declined "
            "leg would red this verify — DOOR 4's raise is bounded by this "
            "figure and the figure has moved" % (declined, total),
        )
        self.assertTrue(report.ok)

    def test_the_ROOT_pass_is_where_it_becomes_reachable_FIRST(self):
        """And the residual, measured rather than promised: `host-local` does
        NOT pin the two root rows, so a governed target that declared root
        would add two assertions with no pin behind them. Every governed target
        declares no capabilities today, which is the only thing holding it."""
        import json

        _probed, root_probed, pinned = self._sets()
        self.assertEqual(sorted(root_probed), ["files.mount#root", "files.umount#root"])
        self.assertEqual(root_probed - pinned["host-local"], root_probed)
        rooted = sorted(
            p.stem
            for p in (REPO / "tools" / "conformance" / "targets").glob("*.json")
            if json.loads(p.read_text()).get("kind") == "governed"
            and "root" in (json.loads(p.read_text()).get("capabilities") or [])
        )
        self.assertEqual(
            rooted, [],
            "governed target(s) %s declare root, so DOOR 4 is now reachable "
            "through the two unpinned root rows" % rooted,
        )


class TestTheCensusCanFailInBothDirections(unittest.TestCase):
    """§A42. A census whose red world cannot be produced has a failure branch
    that has never run."""

    def _double(self, tmp):
        dst = Path(tmp) / "harness"
        shutil.copytree(HARNESS, dst, ignore=shutil.ignore_patterns("__pycache__"))
        return dst

    def test_THE_RED_WORLD_a_census_of_the_three_known_doors_alone_REDS(self):
        """A census double whose declared table is the three known doors reds
        on the structure clause, because the code holds more paths than that.
        This is the row that makes "there is no fourth" a measurement rather
        than an assurance."""
        computed = set(census_a(HARNESS)["members"]) | set(census_b(HARNESS))
        three_only = set(KNOWN_DOORS.values())
        self.assertNotEqual(
            computed, three_only,
            "a three-door census would have matched the structure, which would "
            "mean the structure holds exactly three paths",
        )
        self.assertTrue(computed - three_only)

    def test_THE_CONTROL_a_synthetic_extra_write_path_is_FOUND(self):
        """The other direction, and it is the one that proves the census is not
        blind: a new function reaching the pinned tree, injected into a COPY of
        the harness, appears in CENSUS A as a WRITE without anything being told
        about it."""
        with tempfile.TemporaryDirectory() as tmp:
            dst = self._double(tmp)
            src = (dst / "baselines.py").read_text()
            src += (
                "\n\ndef synthetic_fourth_path(target_name, base=None):\n"
                "    d = baseline_dir(target_name, base)\n"
                "    d.mkdir(parents=True, exist_ok=True)\n"
                "    (d / MANIFEST_NAME).write_text('{}')\n"
                "    return d\n"
            )
            (dst / "baselines.py").write_text(src)
            members = census_a(dst)["members"]
            self.assertIn("baselines.synthetic_fourth_path", members)
            self.assertEqual(members["baselines.synthetic_fourth_path"]["kind"], "WRITE")
            self.assertNotEqual(
                set(members), set(DECLARED_A),
                "the injected path did not move the census, so the census would "
                "not have caught it",
            )

    def test_THE_CONTROL_a_synthetic_verdict_site_is_FOUND(self):
        """The same control on CENSUS B: a new function answering over an
        unproven collection of verdicts appears without being listed."""
        with tempfile.TemporaryDirectory() as tmp:
            dst = self._double(tmp)
            src = (dst / "checks.py").read_text()
            src += (
                "\n\ndef synthetic_verdict(results):\n"
                "    return not [r for r in results if r.verdict == FAIL]\n"
            )
            (dst / "checks.py").write_text(src)
            computed = census_b(dst)
            self.assertIn("checks.synthetic_verdict", computed)
            self.assertTrue(computed["checks.synthetic_verdict"]["aggregates_unproven"])

    def test_the_SOLE_CONSTRUCTOR_clause_can_fail(self):
        """And the property CENSUS A's completeness rests on is falsifiable
        too: a second reader of `BASELINES_DIR`, injected into a copy, reds
        the clause."""
        with tempfile.TemporaryDirectory() as tmp:
            dst = self._double(tmp)
            src = (dst / "runner.py").read_text()
            src += (
                "\n\ndef synthetic_bypass(name):\n"
                "    from tools.conformance.harness.baselines import BASELINES_DIR\n"
                "    return (BASELINES_DIR / name).read_text()\n"
            )
            (dst / "runner.py").write_text(src)
            self.assertNotEqual(
                census_a(dst)["sole_constructor"], ["baselines.baseline_dir"],
                "a second reader of BASELINES_DIR did not red the clause",
            )


if __name__ == "__main__":
    unittest.main()
