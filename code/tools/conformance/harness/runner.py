# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: conformance-harness ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""The dual-target runner.

    --capture  drive the rows against a named STOCK target and pin the answers
    --verify   drive the rows against a named GOVERNED target and judge it
               against a pinned capture plus the record and replay legs
    --list     what the rows compile to, and the coverage statement

The two modes do not share a code path into the world, and that is deliberate.
`capture` builds a transport to a stock target and writes files. `verify` reads
a pinned capture off disk and builds a transport to the GOVERNED target only —
there is no argument, flag, or fallback by which it could reach a live stock
system, which is what makes T-CONFORMANCE-BASELINE-PINNED a structural property
rather than a habit.
"""

import argparse
import dataclasses
import json
import sys
from pathlib import Path

if __package__ in (None, ""):  # runnable as a script as well as a module
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
    from tools.conformance.harness import baselines, checks, probe, rows as rows_mod, targets
else:
    from . import baselines, checks, probe, rows as rows_mod, targets

ROOT_SUFFIX = "#root"

#: The clause every refusal below cites, written once so the three cannot drift
#: apart. §A38 at the VERDICT layer, and it is the fourth member of a family:
#: the founding block's `ls-files >= 1`, T-MINT-SET-ENUMERATED's population
#: clause, the manifest's `files` map (EP-28L), and now the ROW SELECTION.
#: `Report.ok` is `not self.failed` — correct logic over the wrong subject when
#: the subject can be empty. The guard is right about the rows it has; this
#: clause makes it impossible to have none silently.
NON_EMPTY_SELECTION_CLAUSE = (
    "A verdict computed over an empty set of rows is a verdict about nothing. "
    "`Report.ok` is `not self.failed`; an empty verdict list holds no failures; "
    "so the run prints `rows: 0 PASS / 0 FAIL / 0 NOT-RUN` and the exit register "
    "returns 0. The SUBJECT of the run's answer is proven non-empty before that "
    "answer is computed (EP-28M; §A38 at the verdict layer)."
)


class SelectionError(RuntimeError):
    """A run whose selection has no subject.

    It is NOT a row verdict, and `main` keeps that distinction: exit 2 says this
    run never happened, exit 1 says rows failed. Reading a refusal as a failure —
    or as a pass — is the confusion design/10 §11.2b exists to end.
    """


def root_assertion(a):
    """The privileged pass of a row is its own assertion identity, so every leg
    downstream stays uniform and a root observation is never silently merged into
    an unprivileged one. Its §11.1a declaration comes from the root probe's own
    words: the privileged pass tests a different outcome, and a declaration made
    about the unprivileged one says nothing true about it."""
    return dataclasses.replace(
        a,
        row_id=a.row_id + ROOT_SUFFIX,
        probe=a.root_probe,
        root_probe=None,
        outcome_class=rows_mod.outcome_class(a.root_probe),
    )


def select_records(assertion, observed, record_source, mark=None):
    """The row's whole record window: everything appended while its steps ran,
    read from the probe's OWN brackets.

    IT IS THE WHOLE ROW AND NOT THE SUBJECT'S BRACKET, because §11.4a attributes a
    record by what it COVERS rather than by where it landed, and a governed target
    does not append in the step that caused the act — a folded write's covering
    decision arrives at the flush boundary its policy names. Narrowing the window
    to the subject's own bracket would decide the attribution question by timing
    before anything got to read the record.

    The window is taken from the brackets rather than from a line-count mark
    because a mark is a number about a file that a target may legitimately replace
    between the mark and the read — and a window computed from a stale mark comes
    back EMPTY, which reads exactly like a row that recorded nothing. The brackets
    are taken by the thing performing the act, on the target, and cannot go stale.

    ITS BOUNDARY IS A STATED LIMIT: a record landing after the last step's bracket
    closes is outside it, and `files.close` is the row where that shows (FUSE's
    release is not synchronous with close(2)). That is a finding about the row's
    evidence rule, raised at EP-24D R-2, not something this window quietly widens.
    """
    if observed is None:
        return []
    indices = set()
    bracketed = False
    for step in observed.get("steps", []):
        if "rec" not in step:
            continue
        bracketed = True
        before, after = step["rec"]
        indices.update(range(before, after))
    if not bracketed:
        # The target's record was not visible to the probe, so the honest fallback
        # is everything appended since the mark.
        return record_source.since(mark or 0)
    return record_source.select(sorted(indices))


def acts_driven(assertion, observed):
    """Every act the row performed on the target, and which of them are the act
    UNDER TEST. Returns (subject, other).

    Both halves are the harness's own knowledge and neither is the target's word
    for anything: the row says which call it is about (`subject_calls`), and the
    probe says what each step performs (`probe.performs`). §11.4a needs both — the
    subject set to recognise the act's own records, the other set to recognise a
    record about an act the row merely set up rather than one about an act that
    never happened here at all.
    """
    subject_vocab = assertion.subject_calls(probe.DRIVES)
    #: THE ACT UNDER TEST IS THE ROW'S OWN CALL AND ITS VARIANTS, never everything
    #: its subject step happens to perform. `dup2` closes the descriptor it lands
    #: on and `listdir` opens the directory it reads, and a record about those
    #: closes and opens is about a close and an open — which is why both rows are
    #: CACHE-only and neither is failed by them. Reading a step's incidental acts
    #: into the subject would fail exactly those rows, on records that belong to
    #: the close and open rows.
    subject = {sc for sc in (probe.DRIVES.get(n) for n in subject_vocab) if sc}
    other = set()
    for step in (observed or {}).get("steps", []):
        other.update(probe.performs(step.get("call")))
    return frozenset(subject), frozenset(other - subject)


def subject_acts(assertion, observed):
    """How many acts of the call under test this row actually performed.

    It is the other half of seeing a fold from outside: the harness knows what the
    row drove and what the record holds, and fewer covering events than acts is
    folding — observed, not asked of the target. Steps that returned an errno are
    not acts: nothing happened for them to record.
    """
    if observed is None:
        return None
    subjects = assertion.subject_calls(probe.DRIVES)
    return sum(
        1
        for s in observed.get("steps", [])
        if s.get("call") in subjects and s.get("errno") is None and "exception" not in s
    )


def select(all_rows, groups=None, row_ids=None, include_inactive=False):
    out = []
    for r in all_rows:
        if groups and r.group not in groups:
            continue
        if row_ids and r.row_id not in row_ids:
            continue
        if not r.active and not include_inactive:
            continue
        out.append(r)
    return out


# ---------------------------------------------------------------------------
# capture
# ---------------------------------------------------------------------------


def capture(target_name, rows_dir=None, baselines_base=None, targets_dir=None,
            groups=None, captured_at=None):
    target = targets.Target.load(target_name, targets_dir)
    if target.kind != "stock":
        raise targets.TargetError(
            "capture runs against a STOCK target; %r is %r. A governed target is "
            "judged (--verify), never used as its own baseline." % (target_name, target.kind)
        )
    all_groups, all_rows = rows_mod.load_all(rows_dir)
    selected = select(all_rows, groups=groups)

    # A capture is a run like any other: it establishes its subject where the
    # descriptor states one, and it leaves the scratch as it found it.
    if target.spec.get("subject"):
        target.establish_subject()
    target.establish_scratch()
    try:
        user_rows = [a for a in selected if a.has_probe]
        obs, identity = target.run_probes(user_rows)

        root_identity, root_obs = None, {}
        root_rows = [a for a in selected if a.has_root_probe]
        skipped = []
        if root_rows:
            if target.can_root:
                root_obs, root_identity = target.run_probes(root_rows, as_root=True)
                root_obs = {k + ROOT_SUFFIX: v for k, v in root_obs.items()}
            else:
                for a in root_rows:
                    skipped.append(
                        {
                            "row_id": a.row_id + ROOT_SUFFIX,
                            "reason": "target %r declares no root capability; the "
                            "privileged pass of this row is not captured here"
                            % target_name,
                        }
                    )
    finally:
        target.teardown_scratch()
    cov = rows_mod.coverage(selected)
    for entry in cov["active_unprobed"]:
        skipped.append({"row_id": entry["row_id"], "reason": entry["reason"]})

    by_group = {}
    for a in selected:
        payload = by_group.setdefault(
            a.group, {"group": a.group, "target": target_name, "rows": {}}
        )
        if a.row_id in obs:
            payload["rows"][a.row_id] = obs[a.row_id]
        rk = a.row_id + ROOT_SUFFIX
        if rk in root_obs:
            payload["rows"][rk] = root_obs[rk]
    by_group = {g: p for g, p in by_group.items() if p["rows"]}

    d, manifest = baselines.write_capture(
        target_name,
        target.spec,
        by_group,
        identity,
        root_identity,
        cov,
        skipped,
        base=baselines_base,
        captured_at=captured_at,
    )
    return d, manifest


# ---------------------------------------------------------------------------
# verify
# ---------------------------------------------------------------------------


def verify(target_name, baseline_name, rows_dir=None, baselines_base=None,
           targets_dir=None, groups=None, row_ids=None):
    """Judge a governed target. `baseline_name` names a PINNED capture on disk;
    nothing in this function can reach a live stock system."""
    pinned = baselines.load(baseline_name, baselines_base)  # data, read from disk

    target = targets.Target.load(target_name, targets_dir)
    if target.kind != "governed":
        raise targets.TargetError(
            "verify runs against a GOVERNED target; %r is %r" % (target_name, target.kind)
        )
    # THE SELECTION IS RESOLVED AND PROVEN NON-EMPTY BEFORE THE SUBJECT IS
    # TOUCHED. Two reasons, and the second is why this reads before
    # `establish_subject` rather than after it. First, the clause's own words:
    # the selection is proven non-empty BEFORE any verdict is computed, and a
    # `--group` or `--row` matching nothing is a caller error that costs the
    # caller nothing to be told. Second, `establish_scratch`'s teardown lives in
    # the `finally` of the run loop below — a refusal raised between the two
    # would leave the scratch standing, and §11.2b's second half says a run
    # leaves the subject as it found it. Reading the rows touches no target.
    _all_groups, all_rows = rows_mod.load_all(rows_dir)
    selected = select(all_rows, groups=groups, row_ids=row_ids)

    assertions = []
    for a in selected:
        if a.has_probe:
            assertions.append(a)
        if a.has_root_probe and target.can_root:
            assertions.append(root_assertion(a))

    if not selected:
        raise SelectionError(
            "verify against target %r selected ZERO rows, so there is nothing to "
            "judge and the run would report `0 PASS / 0 FAIL / 0 NOT-RUN` and "
            "exit 0. groups=%r rows=%r matched no active row. Check the values "
            "against what `conformance list` reports: group ids carry their "
            "number, so the files group is `06-files` and not `files`, and a "
            "group that has not activated yet holds no active rows at all. %s"
            % (target_name, groups, row_ids, NON_EMPTY_SELECTION_CLAUSE)
        )
    if not assertions:
        raise SelectionError(
            "verify against target %r selected %d row(s) and NONE of them is "
            "drivable here: no selected row carries a probe, and no selected "
            "row's privileged pass is available on a target declaring "
            "capabilities %r. Zero assertions produce zero verdicts, which the "
            "report would render as a clean run. %s"
            % (target_name, len(selected), sorted(target.capabilities),
               NON_EMPTY_SELECTION_CLAUSE)
        )

    # THE SUBJECT IS ESTABLISHED BEFORE ANY ROW RUNS, and a failure here aborts
    # rather than producing verdicts. design/10 §11.2b: a pass against an absent
    # subject is worse than a failure, being indistinguishable from success.
    subject = target.establish_subject()
    target.establish_scratch()

    record_source = target.record_source
    class_map = target.class_map or {}
    covers_map = target.covers_map
    if record_source is not None and covers_map is None:
        # A record the instrument cannot attribute is a record it cannot report
        # on. §11.2b's discipline, pointed at the target's DECLARATION rather than
        # at its subject: refuse the run rather than judge by landing point again.
        raise targets.VocabularyError(
            "target %r exposes a record and declares no covers map. design/10 "
            "§11.4a attributes each record to the act it covers, read from the "
            "record's own action — and what an action is ABOUT is the target's "
            "vocabulary, which it has not declared. The run REFUSES." % target_name
        )
    replayer = target.replayer
    record_file = record_source.path_on_target if record_source else None

    verdicts = []
    try:
        for a in assertions:
            mark = record_source.mark() if record_source else None
            obs_map, _meta = target.run_probes([a], record_file=record_file)
            observed = obs_map.get(a.row_id)
            attribution = None
            if record_source:
                subject_calls, other_calls = acts_driven(a, observed)
                attribution = checks.Attribution(
                    window=tuple(select_records(a, observed, record_source, mark)),
                    covers=covers_map,
                    subject_calls=subject_calls,
                    other_calls=other_calls,
                )
            replayed = (
                replayer.snapshot(a.row_id, {"observed": observed})
                if replayer.available
                else None
            )
            verdicts.append(
                checks.run_row_checks(
                    a,
                    observed,
                    pinned.get(a.row_id),
                    attribution,
                    class_map,
                    replayed_state=replayed,
                    coalescing_policies=target.coalescing_policies,
                    subject_acts=subject_acts(a, observed),
                )
            )
    finally:
        target.teardown_scratch()
    return Report(target_name, baseline_name, pinned, verdicts, selected, subject)


class Report:
    def __init__(self, target_name, baseline_name, pinned, verdicts, selected, subject=None):
        self.target_name = target_name
        self.baseline_name = baseline_name
        self.pinned = pinned
        self.verdicts = verdicts
        self.selected = selected
        #: What was established before the rows ran. It goes in the report because
        #: a figure whose subject cannot be named is a figure nobody can cite.
        self.subject = subject or {}

    @property
    def failed(self):
        return [v for v in self.verdicts if v.verdict == checks.FAIL]

    @property
    def ok(self):
        """The run's answer, and it REFUSES to have one over an empty verdict
        list.

        This is the site, not the caller. `verify` above cannot produce an empty
        report any more, but a guard placed only there would leave `ok` itself
        still willing to answer TRUE because nothing failed rather than because
        anything passed — and `ok` is what the exit register at `_dispatch`
        reads. The clause goes where the vacuous answer is manufactured.
        """
        if not self.verdicts:
            raise SelectionError(
                "this report holds ZERO row verdicts for target %r against "
                "baseline %r, so `ok` would be TRUE because nothing failed "
                "rather than because anything passed. %s"
                % (self.target_name, self.baseline_name, NON_EMPTY_SELECTION_CLAUSE)
            )
        return not self.failed

    def summary(self):
        counts = {checks.PASS: 0, checks.FAIL: 0, checks.NOT_RUN: 0}
        legs = {}
        for v in self.verdicts:
            counts[v.verdict] += 1
            for r in v.results:
                legs.setdefault(r.check, {checks.PASS: 0, checks.FAIL: 0, checks.NOT_RUN: 0})
                legs[r.check][r.verdict] += 1
        return {"rows": counts, "legs": legs}

    def text(self):
        lines = [
            "conformance verify: target=%s baseline=%s" % (self.target_name, self.baseline_name),
            "  baseline captured %s on %s" % (self.pinned.captured_at, self.pinned.kernel),
            "  subject %s served by %s (declared %s)"
            % (
                self.subject.get("path", "(none established)"),
                self.subject.get("served_by", "?"),
                self.subject.get("declared", "?"),
            ),
            "",
        ]
        for v in self.verdicts:
            if v.verdict == checks.PASS:
                continue
            lines.append("%-40s %s" % (v.row_id, v.verdict))
            for r in v.results:
                if r.verdict == checks.PASS:
                    continue
                lines.append("    %-20s %s%s" % (r.check, r.verdict, (" — " + r.reason) if r.reason else ""))
                for d in r.detail:
                    lines.append("        %s" % d)
        s = self.summary()
        lines.append("")
        lines.append(
            "rows: %d PASS / %d FAIL / %d NOT-RUN"
            % (s["rows"][checks.PASS], s["rows"][checks.FAIL], s["rows"][checks.NOT_RUN])
        )
        for leg, c in sorted(s["legs"].items()):
            lines.append(
                "  %-20s %d PASS / %d FAIL / %d NOT-RUN"
                % (leg, c[checks.PASS], c[checks.FAIL], c[checks.NOT_RUN])
            )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# cli
# ---------------------------------------------------------------------------


def main(argv=None):
    p = argparse.ArgumentParser(prog="conformance", description=__doc__)
    sub = p.add_subparsers(dest="mode", required=True)

    c = sub.add_parser("capture", help="drive the rows against a stock target and pin the answers")
    c.add_argument("--target", required=True)
    c.add_argument("--group", action="append", dest="groups")

    v = sub.add_parser("verify", help="judge a governed target against a pinned capture")
    v.add_argument("--target", required=True)
    v.add_argument("--baseline", required=True)
    v.add_argument("--group", action="append", dest="groups")
    v.add_argument("--row", action="append", dest="row_ids")
    v.add_argument("--json", action="store_true")

    lst = sub.add_parser("list", help="what the rows compile to")
    lst.add_argument("--json", action="store_true")
    lst.add_argument("--all", action="store_true", help="include inactive rows")

    args = p.parse_args(argv)

    try:
        return _dispatch(args)
    except (targets.SubjectError, targets.VocabularyError, SelectionError,
            baselines.BaselineError) as e:
        # The abort is loud and it is NOT a row verdict. Exit code 2 says "this run
        # never happened"; exit code 1 says "rows failed". Reading a refusal as a
        # failure, or as a pass, is the confusion §11.2b exists to end.
        #
        # `SelectionError` and `BaselineError` join the two that were here because
        # every refusal in this instrument now belongs to one class: the run has
        # no subject. Left out, a selection that matched nothing and a baseline
        # that pins nothing would leave `main` as a traceback and exit 1 —
        # reporting ROWS FAILED for a run in which no row ran, which is exactly
        # the reading the two exit codes exist to keep apart.
        print("conformance: REFUSED — %s" % e)
        return 2


def _dispatch(args):
    if args.mode == "capture":
        d, manifest = capture(args.target, groups=args.groups)
        print("captured to %s" % d)
        print("  at %s" % manifest["captured_at"])
        u = (manifest.get("target_identity") or {}).get("uname") or {}
        print("  kernel %s %s %s" % (u.get("sysname"), u.get("release"), u.get("machine")))
        for name, meta in sorted(manifest["files"].items()):
            print("  %s  rows=%d  sha256=%s" % (name, meta["rows"], meta["sha256"]))
        if manifest["skipped"]:
            print("  skipped %d row(s), each with its reason in the manifest" % len(manifest["skipped"]))
        return 0

    if args.mode == "verify":
        report = verify(args.target, args.baseline, groups=args.groups, row_ids=args.row_ids)
        if args.json:
            print(json.dumps(
                {
                    "target": report.target_name,
                    "baseline": report.baseline_name,
                    "summary": report.summary(),
                    "rows": [
                        {
                            "row_id": v.row_id,
                            "verdict": v.verdict,
                            "checks": [dataclasses.asdict(r) for r in v.results],
                        }
                        for v in report.verdicts
                    ],
                },
                indent=1,
                sort_keys=True,
            ))
        else:
            print(report.text())
        return 0 if report.ok else 1

    groups, all_rows = rows_mod.load_all()
    shown = all_rows if args.all else rows_mod.active_rows(all_rows)
    cov = rows_mod.coverage(all_rows)
    if args.json:
        print(json.dumps(cov, indent=1, sort_keys=True))
        return 0
    for g, meta in sorted(groups.items()):
        print("%-22s %-10s activates_at=%s" % (g, "ACTIVE" if meta.get("active") else "inactive", meta.get("activates_at")))
    print()
    for r in shown:
        print(
            "%-34s %-10s %-22s probe=%s%s"
            % (
                r.row_id,
                "/".join(r.recording_class),
                r.syscall,
                "yes" if r.has_probe else "NO",
                " +root" if r.has_root_probe else "",
            )
        )
    print()
    print(json.dumps({k: v for k, v in cov.items() if k not in ("probe_limits",)}, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
