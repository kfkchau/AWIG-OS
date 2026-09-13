# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: conformance-harness ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""The three checks of design/10 §3, written once, independent by construction.

  1. ABI identity      — same return, same errno, same visible ordering guarantee,
                         same process-visible side effect.
  2. Recording-class fidelity — the call produced EXACTLY the record its row
                         assigns. "A missing decision, or a decision without a
                         cited rule, fails the audit check even if the ABI check
                         passes" (design/10 §3.2).
  3. Replay invariance — re-deriving the touched subsystem's caches from the
                         record reproduces the post-call state identically.

INDEPENDENCE IS THE POINT, and it is structural rather than promised: each
function takes only the evidence its own leg needs, returns its own verdict, and
no function can see another's result. The runner calls all three and never
short-circuits, so a target that fails one fails exactly one — which is what the
self-test proves (T-HARNESS-COLUMNS-FAIL). Checks 2 and 3 are what make this
instrument OURS: no imported suite runs them, which is why an imported suite's
pass line can never be this acceptance.
"""

from dataclasses import dataclass, field

from . import rows as rows_mod

PASS = "PASS"
FAIL = "FAIL"
NOT_RUN = "NOT-RUN"

#: An observation may never carry a duration (§11.6). Nothing in the probe emits
#: one; this is the rule with teeth on it rather than the rule as a comment.
TIMING_FIELDS = ("elapsed", "duration", "ns", "seconds", "latency", "throughput")

#: design/10 §11.1a. A row whose TESTED OUTCOME is an error return declares which
#: of these three it asserts, and the recording check reads the declaration rather
#: than guessing from the errno. The discriminator is not the errno — it is
#: whether the gate reached a decision, and only the row's author knows that.
OUTCOME_CLASSES = ("REFUSAL", "ABSENCE", "NOT-GOVERNED")

#: The two classes for which a record appearing IS the failure. They are kept
#: apart because "it appends nothing" and "nothing was governed here" are
#: different claims, and a row must say which one it makes.
NO_RECORD_OUTCOMES = ("ABSENCE", "NOT-GOVERNED")

#: What a REFUSAL must have appended, whatever class the row's SUCCESS path
#: carries: §11.1a says a rule-citing DECISION record is REQUIRED. A refusal is
#: precisely the case where a record is most required (P4), so a CACHE-class row
#: whose tested outcome is a refusal still requires one — and must permit it.
REFUSAL_RECORD_CLASSES = ("DECISION", "LAW")

#: design/10 §11.4a. A record kind whose covered act cannot be named by KIND
#: because it is about whatever act was under test — a gate refusal is the case,
#: and it names the refused op in its own payload. Declared by the target, and
#: attributed to the act under test.
ANY_ACT = "*"


@dataclass
class CheckResult:
    check: str
    verdict: str
    detail: list = field(default_factory=list)
    reason: str = None
    #: Anything the check DECLINED to require, and why. A waiver that leaves no
    #: trace is indistinguishable from a check that ran — so every one is written
    #: down on the result that carries it.
    notes: list = field(default_factory=list)

    @property
    def failed(self):
        return self.verdict == FAIL


@dataclass
class RowVerdict:
    row_id: str
    results: list

    @property
    def failed_checks(self):
        return [r.check for r in self.results if r.failed]

    @property
    def verdict(self):
        if any(r.failed for r in self.results):
            return FAIL
        if all(r.verdict == NOT_RUN for r in self.results):
            return NOT_RUN
        return PASS


@dataclass(frozen=True)
class Partition:
    """A row's window, split by WHICH ACT each record is about."""

    subject: tuple = ()          # about the act under test
    elsewhere: tuple = ()        # about an act this row only set up
    foreign: tuple = ()          # about an act this row never performed at all
    undeclared: tuple = ()       # a kind the target's vocabulary does not describe
    not_a_caller_act: tuple = ()  # declared as about no act any caller made


@dataclass(frozen=True)
class Attribution:
    """design/10 §11.4a: which act each record in a row's window is ABOUT.

    THE DEFECT THIS REPLACES, and it produced two failures from one fold. The
    harness bracketed each driven step and judged the records that landed inside
    it. A governed filesystem does not append in the step that caused the act: a
    folded write's covering decision is emitted at the flush boundary its policy
    names. So the `write` row failed for holding nothing and the `fsync` row
    failed for holding a DECISION fsync never made — the record right, the map
    right, the attribution wrong.

    So a record is attributed by what it is ABOUT. `covers` is the TARGET's own
    declaration — action -> the acts that record kind covers — read as data
    exactly as the class map is, because the meaning of an action name is the
    target's vocabulary and the harness authors none of it. What the row drove is
    the harness's own knowledge: the row says which call is under test, and the
    probe says what each step performs.

    THE COST, STATED RATHER THAN DISCOVERED. A record covering an act the row
    legitimately drove as SETUP is indistinguishable from a spurious record
    covering that same act, and bracket attribution could tell them apart. That
    trade is what §11.4a rules, and it is sound because every covered act has a
    row of its own: the write row judges the write's records, so nothing is
    unjudged — it is judged where it belongs instead of where it landed.
    """

    window: tuple = ()
    #: action -> acts covered. None means the target declared no vocabulary, and
    #: nothing can be attributed at all.
    covers: dict = None
    subject_calls: frozenset = frozenset()
    other_calls: frozenset = frozenset()
    #: Built by `of_subject`: the caller has already attributed, and every record
    #: is the act's own. The runner never uses it — see `of_subject`.
    presumed: bool = False

    @classmethod
    def of_subject(cls, records):
        """These records, taken as the act's own, with no attribution performed.

        It exists for the batteries, which construct the case they mean to judge.
        The RUNNER never builds one: deciding which records are the act's own is
        exactly what §11.4a takes away from the bracket, and a run that presumed
        it would have re-made the defect under a new name.
        """
        return cls(window=tuple(records or ()), presumed=True)

    def covered_acts(self, rec):
        """What act this record is about, read from its own action. None where the
        target's vocabulary does not describe the kind at all."""
        if self.covers is None:
            return None
        action = rec.get("action")
        if action not in self.covers:
            return None
        return tuple(self.covers[action] or ())

    def partition(self):
        if self.presumed:
            return Partition(subject=tuple(self.window))
        subject, elsewhere, foreign, undeclared, inert = [], [], [], [], []
        for rec in self.window:
            acts = self.covered_acts(rec)
            if acts is None:
                undeclared.append(rec)
            elif not acts:
                inert.append(rec)
            elif ANY_ACT in acts or (set(acts) & self.subject_calls):
                subject.append(rec)
            elif set(acts) & self.other_calls:
                elsewhere.append(rec)
            else:
                foreign.append(rec)
        return Partition(
            subject=tuple(subject),
            elsewhere=tuple(elsewhere),
            foreign=tuple(foreign),
            undeclared=tuple(undeclared),
            not_a_caller_act=tuple(inert),
        )


def _as_attribution(value):
    """A sequence means "already attributed"; an Attribution means "attribute
    these". Both are accepted so a battery can state its case directly."""
    if value is None or isinstance(value, Attribution):
        return value
    return Attribution.of_subject(value)


def _walk_keys(obj, out):
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.add(k)
            _walk_keys(v, out)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            _walk_keys(v, out)


def _driver_faults(observed):
    """A row whose probe could not RUN is not a row that passed. Equality between
    two broken observations is the trap this function exists to refuse."""
    faults = []
    if observed is None:
        return ["no observation for this row"]
    if "driver_error" in observed:
        faults.append("driver error: %s" % observed["driver_error"])
    for step in observed.get("steps", []):
        if step.get("unknown_call"):
            faults.append(
                "step %s names %r, which the probe vocabulary does not carry"
                % (step.get("i"), step.get("call"))
            )
        if step.get("bind_error"):
            faults.append("step %s bind error: %s" % (step.get("i"), step["bind_error"]))
        if step.get("exception"):
            faults.append("step %s raised: %s" % (step.get("i"), step["exception"]))
    return faults


def check_abi(assertion, observed, baseline):
    """Check 1. The baseline is a PINNED capture; nothing here reads a live stock
    system, and this function is given no way to."""
    if not assertion.has_probe:
        return CheckResult(
            "abi-identity",
            NOT_RUN,
            reason=assertion.probe_absent_reason or "no probe on this row",
        )
    if baseline is None:
        return CheckResult(
            "abi-identity", NOT_RUN, reason="no pinned baseline for this row"
        )

    detail = []
    # §11.3 and §11.6 are enforced against the observation itself, not assumed.
    keys = set()
    _walk_keys(observed, keys)
    timing = sorted(k for k in keys if k in TIMING_FIELDS)
    if timing:
        detail.append("observation carries timing fields %s — §11.6 puts timing out of contract" % timing)
    if assertion.rules.shape_only:
        dynamic = sorted(k for k in keys if k in rows_mod.DYNAMIC_FIELDS)
        if dynamic:
            detail.append(
                "shape-only row carries dynamic fields %s — §11.3 promises shape and schema, not values"
                % dynamic
            )

    obs_steps = observed.get("steps", [])
    base_steps = baseline.get("steps", [])
    if len(obs_steps) != len(base_steps):
        detail.append(
            "step count %d vs pinned %d" % (len(obs_steps), len(base_steps))
        )
    for i, (o, b) in enumerate(zip(obs_steps, base_steps)):
        if o.get("call") != b.get("call"):
            detail.append("step %d: call %r vs pinned %r" % (i, o.get("call"), b.get("call")))
            continue
        if o.get("errno") != b.get("errno"):
            detail.append(
                "step %d (%s): errno %s vs pinned %s — §11.1, errno identity is load-bearing"
                % (i, o.get("call"), o.get("errno"), b.get("errno"))
            )
        if o.get("ret") != b.get("ret"):
            detail.append(
                "step %d (%s): return %r vs pinned %r"
                % (i, o.get("call"), o.get("ret"), b.get("ret"))
            )
    if observed.get("state") != baseline.get("state"):
        obs_state = observed.get("state") or {}
        base_state = baseline.get("state") or {}
        for name in sorted(set(obs_state) | set(base_state)):
            if obs_state.get(name) != base_state.get(name):
                detail.append(
                    "side effect %r: %r vs pinned %r"
                    % (name, obs_state.get(name), base_state.get(name))
                )
    # Driver faults come LAST in the report and first in importance: a step that
    # could not run is not a step that agreed, so equality between two broken
    # observations must never read as a pass. They are listed after the
    # divergences because a fault is usually the CONSEQUENCE of one — a step that
    # failed leaves the name it was going to bind unbound — and a report that
    # leads with the consequence hides the cause.
    for side, obs in (("target", observed), ("baseline", baseline)):
        for fault in _driver_faults(obs):
            detail.append("%s: %s" % (side, fault))
    return CheckResult("abi-identity", FAIL if detail else PASS, detail)


def _cites_policy(rec, policies):
    """Does this record NAME one of the policies the target declares?

    §11.4 says the folding "cites a recorded policy with a named owner"; it does
    not say through which field, and the estate's own records cite in two places
    for two different things — `rule_cited` carries the rule the act applied
    (a write cites its permission rule), while the fold names the granularity
    policy it folded under. So the question asked here is the one §11.4 actually
    asks: does the record name the policy. It is answered by looking, not by
    knowing a field name, which keeps the harness free of the target's vocabulary.
    """
    if isinstance(rec, str):
        return rec in policies
    if isinstance(rec, dict):
        return any(_cites_policy(v, policies) for v in rec.values())
    if isinstance(rec, (list, tuple)):
        return any(_cites_policy(v, policies) for v in rec)
    return False


def _fold_leg(assertion, exp, records, class_map, coalescing_policies, subject_acts):
    """§11 rule 4, verbatim: "A test may assert that the *policy exists and is
    cited*, not that every micro-event has its own record."

    IT READS THE RECORDS ATTRIBUTED TO THE ACT UNDER TEST, wherever in the row
    they landed — which is no longer a rule of its own but the ordinary reading of
    §11.4a. The fold was the first deferred-emission shape anyone measured; the
    attribution that repairs it repairs the class.

    AND IT DOES NOT REQUIRE FOLDING, which is the other half of reading §11.4
    correctly. Folding is licensed, never mandated: a world whose coalescing policy
    has been superseded to nothing appends one covering decision per write and is
    exactly as conformant. So the leg asks the question the map asks, in this
    order:

      1. Is the covering event there at all? Not requiring a record PER EVENT is
         not the same as requiring none.
      2. Were FEWER covering events appended than the row drove acts? That, and
         only that, is folding observed from outside — and the harness can see it
         because it knows what the row drove and what the record holds, neither of
         which is the target's vocabulary.
      3. If folded: the policy must EXIST (declared) and be CITED by the surviving
         events. A fold nobody owns is the silent loss the rule forbids.
    """
    detail = []
    classified = [(class_map.get(r.get("action")), r) for r in records]
    covering = [(c, r) for c, r in classified if c in exp.required_classes]

    if assertion.rules.coalescible:
        if not covering:
            detail.append(
                "no %s-class covering event appears anywhere in this row's window — "
                "§11.4 licenses folding the granularity, never losing the event"
                % ", ".join(exp.required_classes)
            )
        elif subject_acts is not None and len(covering) < subject_acts:
            names = sorted(
                "%s(%s)" % (r.get("action"), r.get("record_id")) for _c, r in covering
            )
            if not coalescing_policies:
                detail.append(
                    "the row drove %d acts and %d covering event(s) were appended, so "
                    "the granularity was FOLDED — and the target declares no "
                    "coalescing policy for it to cite. §11.4 makes folding a NAMED "
                    "calibration, never a silent loss." % (subject_acts, len(covering))
                )
            else:
                uncited = [
                    "%s(%s)" % (r.get("action"), r.get("record_id"))
                    for _c, r in covering
                    if not _cites_policy(r, coalescing_policies)
                ]
                if uncited:
                    detail.append(
                        "the row drove %d acts and %d covering event(s) were appended, "
                        "so the granularity was FOLDED, and %s cites no recorded "
                        "coalescing policy: nothing in it names one of %s. Covering "
                        "events seen: %s"
                        % (subject_acts, len(covering), uncited,
                           list(coalescing_policies), names)
                    )
    # The forbidden direction, for any row a STREAM class puts under §11.4: a
    # sampled aggregate that appears and cites nothing recorded is a fold nobody
    # owns.
    uncited_stream = [
        r.get("action")
        for c, r in classified
        if c == "STREAM" and not _cites_policy(r, coalescing_policies)
    ]
    if uncited_stream:
        detail.append(
            "STREAM-class records %s cite no recorded coalescing policy (declared: %s) "
            "— §11.4 makes folding a named calibration, never a silent loss"
            % (uncited_stream, list(coalescing_policies))
        )
    return detail


def check_recording_class(assertion, attribution, class_map, coalescing_policies=(),
                          outcome_class=None, subject_acts=None):
    """Check 2. `attribution` is the row's record window plus what each record in
    it is ABOUT (§11.4a); `class_map` is the TARGET's own declaration of which
    recording class each action belongs to. The harness holds no action vocabulary
    — it reads the target's, exactly as it reads design/10's classes from the rows.

    THE RECORDS JUDGED HERE ARE THE ONES ATTRIBUTED TO THE ACT UNDER TEST, not the
    ones that landed in its bracket. A record about an act the row only set up
    belongs to that act's own row and is excluded with a note; a record about an
    act this row never performed is a FAILURE, and so is a record whose kind the
    target's vocabulary never declared — an instrument that cannot say what a
    record is about must not quietly drop it.

    `outcome_class` is the row's own §11.1a declaration, present only on a row
    whose tested outcome is an error return. It is DATA the row carries, never a
    property computed from the observation — and that is the whole repair. The
    check used to waive its required half whenever every subject step returned an
    errno, which waived it exactly where P4 makes a record MOST required: a mount
    that refuses for real, with its refusals exempt from the recording check, is a
    custody claim whose audit leg is switched off precisely where custody is being
    asserted. There is no waiver left; a row that says nothing binds in full.

    `subject_acts` is how many acts the row actually drove — the other half of
    seeing a fold from outside.
    """
    attribution = _as_attribution(attribution)
    if attribution is None:
        return CheckResult(
            "recording-class",
            NOT_RUN,
            reason="target exposes no record; the check needs the store the target runs on",
        )
    if outcome_class is not None and outcome_class not in OUTCOME_CLASSES:
        raise ValueError(
            "outcome class %r is outside design/10 §11.1a's three (%s)"
            % (outcome_class, ", ".join(OUTCOME_CLASSES))
        )
    exp = assertion.record_expectation
    detail = []
    notes = []
    classified = []

    part = attribution.partition()
    records = part.subject
    for rec in part.undeclared:
        detail.append(
            "record %r is not in the target's covers map, so what act it is about "
            "cannot be read — §11.4a attributes a record from its own action, and "
            "an action the target never declared says nothing" % rec.get("action")
        )
    for rec in part.foreign:
        detail.append(
            "record %r covers %s, and this row drove no such act: the record is "
            "about something that did not happen here"
            % (rec.get("action"), list(attribution.covered_acts(rec)))
        )
    if part.elsewhere:
        notes.append(
            "%d record(s) are about acts this row only set up (%s) and are judged "
            "on those acts' own rows, never on this one (§11.4a)"
            % (len(part.elsewhere),
               sorted({r.get("action") for r in part.elsewhere}))
        )
    if part.not_a_caller_act:
        notes.append(
            "%d record(s) of kind %s are declared by the target as about no act a "
            "caller made, so they are attributed to no row"
            % (len(part.not_a_caller_act),
               sorted({r.get("action") for r in part.not_a_caller_act}))
        )
    for rec in records:
        action = rec.get("action")
        cls = class_map.get(action)
        if cls is None:
            detail.append(
                "record %r has no class in the target's class map — an unclassified "
                "record cannot be shown to be the record the row assigns" % action
            )
            continue
        classified.append((cls, rec))

    seen = {c for c, _ in classified}
    permitted = list(exp.permitted_classes)
    if outcome_class == "REFUSAL":
        # §11.1a class 1: the gate decided no, and a rule-citing DECISION record is
        # REQUIRED. That requirement is the row's, whatever class its success path
        # carries — so the refusal record is both required and permitted here.
        permitted = sorted(set(permitted) | set(REFUSAL_RECORD_CLASSES))

    outside = sorted(c for c in seen if c not in permitted)
    if outside:
        detail.append(
            "records of class %s appeared, which this row does not assign (row assigns %s)"
            % (outside, list(assertion.recording_class))
        )

    if outcome_class in NO_RECORD_OUTCOMES:
        # §11.1a classes 2 and 3. Both require no record; they are kept apart
        # because they make different claims, so the failure says which claim broke.
        why = {
            "ABSENCE": "the row declares ABSENCE — the view answered 'no such thing' "
            "and the call is a read, so a record appearing IS the failure",
            "NOT-GOVERNED": "the row declares NOT-GOVERNED — the call never reached a "
            "governed decision at all, so a record appearing IS the failure",
        }[outcome_class]
        if classified:
            detail.append(
                "%s: %d record(s) appended (%s)"
                % (why, len(classified), sorted({r.get("action") for _c, r in classified}))
            )
    elif exp.coalescing_policy_required or assertion.rules.coalescible:
        detail.extend(
            _fold_leg(
                assertion,
                exp,
                records,
                class_map,
                coalescing_policies,
                subject_acts,
            )
        )
    elif outcome_class == "REFUSAL":
        if not any(c in REFUSAL_RECORD_CLASSES for c in seen):
            detail.append(
                "the row declares REFUSAL and no %s-class record was appended — a "
                "refusal is precisely where a rule-citing record is most required "
                "(§11.1a class 1, P4)" % " or ".join(REFUSAL_RECORD_CLASSES)
            )
    else:
        missing = [c for c in exp.required_classes if c not in seen]
        if missing:
            detail.append(
                "no %s-class record was appended, and the row assigns it"
                % ", ".join(missing)
            )

    if exp.rule_citation_required or outcome_class == "REFUSAL":
        for cls, rec in classified:
            if cls in ("LAW", "DECISION") and not rec.get("rule_cited"):
                detail.append(
                    "%s-class record %r cites no rule — a decision without a cited "
                    "rule fails the audit check even when the ABI check passes"
                    % (cls, rec.get("action"))
                )
    if (
        set(assertion.recording_class) == {"CACHE"}
        and classified
        and outcome_class != "REFUSAL"
    ):
        # A CACHE-only row that appended anything at all has failed, whatever the
        # class: I9 says recording scales with governance, never operation. A row
        # that is CACHE *and* STREAM is not this case — §11.4 lets a sampled
        # aggregate exist there, and the fold leg is what binds it. A row whose
        # tested outcome is a REFUSAL is not this case either: its record is
        # required by §11.1a, not forbidden by its success-path class.
        detail.append(
            "a CACHE-only row appended %d record(s); the row assigns none"
            % len(classified)
        )
    return CheckResult("recording-class", FAIL if detail else PASS, detail, notes=notes)


def check_replay(assertion, live_state, replayed_state):
    """Check 3. The post-call state as the target serves it, against the state
    re-derived from the record alone. This is the leg the journaling-filesystem
    template dies on: a passthrough with a log beside it passes checks 1 and 2 and
    fails here, because its truth was never in the record."""
    if replayed_state is None:
        return CheckResult(
            "replay-invariance",
            NOT_RUN,
            reason="target offers no replay; the check needs derived state killed and rebuilt from the record",
        )
    if live_state == replayed_state:
        return CheckResult("replay-invariance", PASS)
    detail = []
    live = live_state or {}
    replayed = replayed_state or {}
    for name in sorted(set(live) | set(replayed)):
        if live.get(name) != replayed.get(name):
            detail.append(
                "%r: live %r vs replayed-from-record %r"
                % (name, live.get(name), replayed.get(name))
            )
    return CheckResult("replay-invariance", FAIL, detail)


def run_row_checks(assertion, observed, baseline, attribution, class_map, live_state=None,
                   replayed_state=None, coalescing_policies=(), subject_acts=None):
    """All three, always, in order, with no short-circuit anywhere. A failing leg
    never suppresses another leg's verdict — which is the property the self-test
    exists to prove.

    Nothing here computes whether the call succeeded. What check 2 requires comes
    from the ROW (its class list and its §11.1a declaration), never from the answer
    the target gave — an instrument that relaxed its own requirement because the
    subject failed would be asking the subject what to demand of it.
    """
    if live_state is None and observed is not None:
        live_state = observed.get("state")
    return RowVerdict(
        assertion.row_id,
        [
            check_abi(assertion, observed, baseline),
            check_recording_class(
                assertion,
                attribution,
                class_map,
                coalescing_policies,
                outcome_class=assertion.outcome_class,
                subject_acts=subject_acts,
            ),
            check_replay(assertion, live_state, replayed_state),
        ],
    )
