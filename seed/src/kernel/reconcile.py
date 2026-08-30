"""gov-os kernel — the two times of authority and the reconciliation sweep (EP-26;
design/35, design/36 K7/K10 and §4b as corrected by its ADDENDUM A and ADDENDUM E).

THE LAW THIS LOWERS. Every judged or authorised act has two times. The DECIDING time is
the moment the thing became authorised in the decider's hands, and that is where
legitimacy is created. The RECORDING time is the moment the store wrote it, and that is
where order is created. `record_time` stays the sole total-order anchor of the log; this
module never touches order. It governs VALIDITY, which was never the order's job.

THE REFERENCE THIS MODULE REFUSES, named because it is the one that fires. Arrival-order
adjudication — last-writer-wins, commit-timestamp semantics, "the store saw it first so it
wins". Taking it erases the owner's ruling outright: the act decided at 9:00 and arriving
at 10:00 stands against the 9:15 rule that arrived at 9:30. And its family member,
compensation-by-edit: rollback frameworks that reconcile by editing state or re-rendering
history as though the act never happened. Taking that erases append-only. An overturn is an
appended decision acting FORWARD; an asOf answer from before the overturn still shows the
act's effect, because order is untouched and validity is what changed.

THE SPLIT IS THE DESIGN, and implementing it uniformly in either direction is the quiet
third form of the same error. LAW is evaluated as of the deciding time; AUTHORITY is
evaluated live at effect time. Everything-as-of-deciding-time would let a revoked chain act
on stale power. Everything-live would judge an old-decided act by law it demonstrably could
not see. Two verdicts, two records, never merged (design/34 §2 generalized). The
counterfactual world this module builds (`world_for`) is that split, lowered into one
selection rule.

THE TIE RULE BINDS BOTH DOORS (design/36 ADDENDUM A.1). A law-family record whose deciding
time EQUALS an act's deciding time is not in force for that act. The sweep's rule and the
acceptance rule are one rule stated once and applied twice: the same helper answers both,
so there is no second comparison that could disagree.

TERMINATION, AND THE REASON THAT CARRIES IT (design/36 ADDENDUM A.2). Not the monotone
argument §4b.5 gives — admission is the gate's whole check set and a ceiling check moves the
other way under exclusion, so the admission predicate is not monotone in the record. The
guarantee is simpler and stronger: the only thing a sweep ever produces is an overturn, an
overturn is never withdrawn, so the overturned set is monotone non-decreasing inside a
candidate set that is FINITE and FIXED. At most one round per candidate. The candidate set
is fixed because the sweep's own overturns are d = r acts recorded after r(L), which §4b.1
puts outside the sweep's business — the sweep does not chase its own output.

TWO-PHASE, AND FORCED RATHER THAN CHOSEN (design/36 ADDENDUM E.2). The anchor guard can
refuse at the fixed point, and an act once overturned is never un-overturned. A sweep that
had already committed overturns and then refused would leave authority orphaned with the
record saying so — accepted-but-cannot-honour, which this estate refuses outright. So the
ROUNDS COMPUTE (exclusion is a derivation over a set and needs nothing appended to see its
own effect), the guard runs on the computed post-state, and only then does the sweep COMMIT.
A refusal means nothing was appended.
"""

from . import authority
from . import crossing
from .errors import OpError
from .gate import Gate
from .views import Views

#: The three rules this seam's refusals and overturns cite. All three are RECORDS in the
#: founding pack (law is data, P5); these constants only name them, exactly as gate.py names
#: P3-CLOSURE and crossing.py names CROSSING-CORRELATION.
ACCEPT_RULE = "TWO-TIMES-ACCEPT"
OVERTURN_RULE = "TWO-TIMES-OVERTURN"
SEAL_BOUND_RULE = "TWO-TIMES-SEAL-BOUND"
SESSION_RULE = "SESSION-DECLARED"

#: The anchor law the computed guard refuses under. Its trigger is CORRECTED here, not
#: widened: the invariant was always effect-level (design/36 ADDENDUM E.1).
ANCHOR_RULE = "CONST-AUTHORITY-ANCHORED"

#: The payload kinds this EP founds.
OVERTURN_KIND = "overturn"
SESSION_KIND = "session"

#: The observe seam's marked substitution (design/36 EP-22 RAISED-BY-DESIGN 4). A window that
#: reported no time of its own had submission time stood in, and SAID SO. v1 treats a marked
#: substitution as d = r — conservative, no counterfactual standing — and the mentor owns any
#: stronger reading (EP-26 RAISED-BY-DESIGN 3).
SUBMISSION_SUBSTITUTED = "submission-substituted"

#: Refusals whose cause is the CALL rather than the world. A nonconforming call does not
#: become conforming because law changed, so these are never re-ask cases.
CALL_CONFORMANCE_RULES = ("P3-CLOSURE", "AR-2")

#: THE DECIDING-TIME PRECISION, stated because this EP makes the field load-bearing
#: (design/36 ADDENDUM A.1 second half). `occurrence_time` is minted by `store._append` as
#: `datetime.now(timezone.utc).isoformat()` — ISO-8601 UTC at MICROSECOND resolution. design/11
#: §1.1 specifies the field as "may be vague" and that specification is unchanged; what is
#: pinned here is the resolution the ENGINE writes and compares at. At microsecond resolution a
#: tie is a genuine corner case rather than a whole tick of traffic, so the strict comparison
#: exempts a corner and not a population — which is the condition A.1 set for proceeding rather
#: than stopping. Comparison is lexicographic over the ISO string, which is order-preserving
#: only for a fixed offset; every time this engine mints carries `+00:00`, and a caller-supplied
#: time in another offset is normalised by `_instant` before any comparison.
DECIDING_TIME_PRECISION = "ISO-8601 UTC, microsecond"


# ---- the two times, read off a record -------------------------------------------------------

def _instant(value):
    """One comparable instant from a recorded time string. Normalised to UTC so a
    caller-supplied `+08:00` time compares correctly against the engine's `+00:00` mints — a
    lexicographic string compare would put the same moment in two places. Returns None for
    anything unparseable, and every caller treats None as "no distinct deciding time" rather
    than guessing."""
    if not isinstance(value, str) or not value:
        return None
    import datetime
    try:
        t = datetime.datetime.fromisoformat(value)
    except ValueError:
        return None
    if t.tzinfo is None:
        t = t.replace(tzinfo=datetime.timezone.utc)
    return t.astimezone(datetime.timezone.utc)


def _payload(record):
    """A record's payload AS A MAPPING, or empty. A governed record's payload must be a
    well-formed object and the constitution guard refuses one that is not (AR-2) — but that
    guard runs LATER in the pipeline than the acceptance step, so a caller-passed list or scalar
    reaches here first. Reading it as empty lets the malformed act travel to the branch that
    exists to refuse it, cited, instead of crashing on the way (P4-REFUSE: fail loud and cite,
    never crash; the R23 regression is this exact shape one step earlier in the pipeline)."""
    p = record.get("payload")
    return p if hasattr(p, "get") else {}


def recording_time(record):
    """WHERE ORDER IS CREATED. Untouched by everything in this module."""
    return _instant(record.get("record_time"))


def deciding_time(record):
    """WHERE LEGITIMACY IS CREATED — `occurrence_time`, made load-bearing for adjudication by
    this EP (design/35 §5: no envelope change; what changed is that adjudication reads it).

    A MARKED SUBSTITUTION IS TREATED AS d = r. The observe seam marks an occurrence_time it
    stood in for a window that reported none. Reading that stand-in as a deciding time would
    give an observation counterfactual standing it never earned, so the record's own honesty
    mark is honoured and the recording time answers instead."""
    if _payload(record).get("time_source") == SUBMISSION_SUBSTITUTED:
        return recording_time(record)
    return _instant(record.get("occurrence_time")) or recording_time(record)


def is_law_family(record):
    """Is this a LAW-family record? THE FOLD'S OWN RULE, unchanged (store.is_law_record,
    views._active_rules): a record IS law iff its payload declares a `rule_id` —
    self-declaration, never an action-name list, so a future subsystem's law op is recognised
    without this predicate learning its verb."""
    return _payload(record).get("rule_id") is not None


def in_force_at(law_record, deciding):
    """THE TIE RULE, in ONE place so both doors cannot disagree (design/36 ADDENDUM A.1).

    Is `law_record` in force for an act decided at `deciding`? Strictly: a law decided at
    exactly the act's own deciding moment is NOT in force for it. The derivation is the
    owner's: legitimacy is created at the deciding moment, the decider at that instant could
    not have been shown the law, and its seal pins a world that cannot contain the law — so
    holding the act to it would hold a decision to law it demonstrably could not see."""
    if deciding is None:
        return True                      # no distinct deciding time -> the live fold, unfiltered
    d_law = deciding_time(law_record)
    return d_law is None or d_law < deciding


# ---- the counterfactual world: THE SPLIT, lowered into one selection rule --------------------

class WorldStore:
    """The record as ONE act's admission saw it — a read-only projection presenting the store's
    own read surface so the gate's checks and every fold run against it WITHOUT ONE LINE
    CHANGING. That is EP-24B's standing law (one implementation, two record sources) extended
    from a fold to the whole admission test: two implementations could diverge in logic as well
    as in world, and no test could attribute a divergence to either.

    THE SELECTION RULE IS THE LAW/AUTHORITY SPLIT:

      * a LAW-family record is in this world iff its deciding time is strictly before the act's
        (`in_force_at`) — law as of deciding time. This is how a late-arriving law that the act
        never saw at its own recording time is nonetheless present here, which is the whole
        mechanism of reach;
      * every other record is in this world iff it precedes the act in the record — authority
        live at effect time. The grant fold, the space tree, the account surface and the
        crossing state all answer as they did at the act's own door;
      * minus the EXCLUDED set — the acts this sweep has already overturned. Exclusion is how
        transitive reach is computed rather than stored: an act admitted under a grant that is
        now excluded fails its admission on recomputation, and nothing anywhere holds a
        dependency link.

    Implementing either half uniformly is the wrong reference wearing a third face, and is
    refused by this rule being ONE rule with two branches rather than a policy switch."""

    def __init__(self, store, law_asof, arrival_seq, excluded=(), head_seq=None):
        self._store = store
        self._law_asof = law_asof
        self._arrival_seq = arrival_seq
        self._excluded = frozenset(excluded)
        self._head = head_seq if head_seq is not None else len(store.events)
        self.events = [e for e in store.events if self._selects(e)]
        self._by_seq = {e["seq"]: e for e in self.events}
        self._by_action = {}
        for e in self.events:
            self._by_action.setdefault(e["action"], []).append(e)
        self._projections = {}

    def _selects(self, e):
        seq = e["seq"]
        if seq > self._head or seq in self._excluded:
            return False
        if is_law_family(e):
            return in_force_at(e, self._law_asof)
        return seq < self._arrival_seq

    # ---- the store's own read surface ----
    def all(self, as_of_seq=None):
        if as_of_seq is None:
            return list(self.events)
        return [e for e in self.events if e["seq"] <= as_of_seq]

    def by_action(self, action, as_of_seq=None):
        arr = self._by_action.get(action, [])
        if as_of_seq is None:
            return list(arr)
        return [e for e in arr if e["seq"] <= as_of_seq]

    def by_seq(self, seq):
        return self._by_seq.get(seq)

    def find(self, pred, as_of_seq=None):
        return [e for e in self.all(as_of_seq) if pred(e)]

    def last(self, pred, as_of_seq=None):
        m = self.find(pred, as_of_seq)
        return m[-1] if m else None

    def on_append(self, fn):
        """A counterfactual world is never appended to. Accepting the registration and doing
        nothing keeps `Views` constructible over it without a second Views implementation."""

    def record_projection(self, name):
        from .store import PROJECTIONS, StaleIndex
        cls = PROJECTIONS.get(name)
        if cls is None:
            raise StaleIndex(f"there is no record projection named {name!r}")
        p = self._projections.get(name)
        if p is None:
            p = self._projections[name] = cls(self)
        return p

    def governance_index(self):
        return self.record_projection("authority")


class CounterfactualRefusal(Exception):
    """A refusal that DID NOT HAPPEN — the answer to "would this act be admitted in that
    world", carried out of the gate's own checks without a record being written. A
    counterfactual that appended its refusals would be a sweep fabricating history."""

    def __init__(self, rule, message):
        super().__init__(f"{rule}: {message}")
        self.rule = rule
        self.message = message


class DryGate(Gate):
    """THE GATE'S OWN ADMISSION TEST, run without a write. A SUBCLASS and not a copy: every
    check body is the gate's, inherited unchanged, so "the one interpreter is the matcher"
    (§4b.2) is structural rather than promised. Exactly two things differ — the views it reads
    (a counterfactual world) and what a refusal does (raise, never append)."""

    def __init__(self, gate, world_views):
        self.store = world_views.store
        self.ops = gate.ops
        self.views = world_views
        self.blobs = gate.blobs
        self.vault = gate.vault

    def refuse(self, actor, op, rule, message, draft=None):
        raise CounterfactualRefusal(rule, message)


def _thaw(obj):
    """A recorded record is frozen all the way down (store._freeze), and the gate's checks test
    `isinstance(payload, dict)` — a MappingProxyType is not a dict, so a frozen payload would
    read as ABSENT and every payload-shaped check would silently pass. Thaw before re-running
    them; a silently-skipped check is a wrong answer wearing the costume of a right one."""
    from types import MappingProxyType
    if isinstance(obj, (dict, MappingProxyType)):
        return {k: _thaw(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_thaw(v) for v in obj]
    return obj


def draft_of(record):
    """The recorded act, back in the shape the gate judged: the envelope minus what the STORE
    minted at append (`seq`, `record_time`). Order is the store's and is never re-judged."""
    d = _thaw(record)
    d.pop("seq", None)
    d.pop("record_time", None)
    return d


def world_for(store, record, excluded=(), head_seq=None, law_asof=None):
    """The world one recorded act's admission is re-run in. `law_asof` defaults to the act's
    own deciding time; a caller passing it explicitly is the acceptance step at the door,
    where the arrival has no seq yet."""
    if law_asof is None:
        law_asof = deciding_time(record)
    arrival = record.get("seq")
    if arrival is None:
        arrival = len(store.events) + 1
    return Views(WorldStore(store, law_asof, arrival, excluded, head_seq))


def admits(gate, world_views, record, opname=None):
    """Re-run THE GATE'S OWN ADMISSION TEST on a recorded act, in a given world.

    The four steps are the gate's, in the gate's own order, called on the gate's own methods
    through a dry `self`. The handler's internal checks are NOT re-run and that is a stated
    boundary, not an omission: §4b.2 rules that the rule's trigger chain, its scope and space
    containment do all the narrowing, and those are exactly these four. Re-running a handler
    would also mean re-supplying parameters the record does not carry — and must not carry,
    since a secret candidate never lands on the record (CONST-SECRETS).

    Returns (permitted, rule, message)."""
    draft = draft_of(record)
    actor = record["actor"]
    name = opname or record["action"]
    dry = DryGate(gate, world_views)
    try:
        dry._authority_step(actor, name, draft)
        crossing.correlation_guard(dry, dry.store, actor, name, draft)
        dry._full_form_pass(actor, name, draft)
        dry._constitution_guard(actor, name, draft)
    except CounterfactualRefusal as exc:
        return False, exc.rule, exc.message
    return True, None, None


# ---- the seal bound (design/35 §6) -----------------------------------------------------------

def seal_bound(store, views, record):
    """A CLAIMED DECIDING TIME CANNOT PREDATE THE WORLD ITS OWN SEAL PINS.

    Deciding timestamps are caller-asserted until campaign 4 signs them (design/35 §6, the
    stated cap). The seal bounds how far a claim can run BACKWARD, in one direction and
    honestly: the hand-out recorded the canonical hash of exactly what the decider was shown,
    so the world that hash pins has a first moment, and a decision cannot be claimed at 9:00
    over a world that only came into existence at 9:10.

    The check is existential rather than exact: is there ANY store state at or before the
    claimed time whose pinned pack hashes to the recorded seal? If there is none, the claim is
    impossible and refuses. Existence — not "the earliest" — is the honest form, because a
    read-set that changed away and back (design/34 §3's ruled ABA case) genuinely held the
    sealed content more than once, and picking one of those moments would refuse a claim that
    is true.

    Returns (ok, reason). A record carrying no seal is unbounded in this direction and says so;
    the other direction closes with cryptographic signing in campaign 4."""
    p = _payload(record)
    seal, pack = p.get("seal"), p.get("input_view")
    if not seal or not pack:
        return True, None
    claimed = deciding_time(record)
    if claimed is None:
        return True, None
    pinned = crossing.resolve_pack(store, pack)
    if pinned is None:
        return True, None                    # a dangling pin is the crossing seam's refusal, not this one
    first_seq = int(pack.rpartition("@")[2])
    for e in store.all():
        if e["seq"] < first_seq:
            continue
        if recording_time(e) is not None and recording_time(e) > claimed:
            break                            # every remaining world came into being after the claim
        try:
            if crossing.seal_of(store, views, pack, as_of=e["seq"]) == seal:
                return True, None
        except LookupError:
            continue
    return False, (
        f"claims deciding time {record.get('occurrence_time')} over pack {pack}, whose sealed "
        f"content {seal} did not exist in any store state at or before that moment — a decision "
        f"cannot be claimed over a world that had not yet come into being")


def seal_bound_check(gate, store, views, actor, opname, draft):
    """The seal bound, AT THE CHOKEPOINT. Fires only on an arrival that carries BOTH a distinct
    deciding time and a seal — a synchronous hand-out seals the world it is being minted in, so
    there is nothing to bound. Refuses citing the seal-bound rule, which is its own rule and not
    the staleness rule: staleness asks whether the judged world is still the world, this asks
    whether the claimed moment could have seen that world at all."""
    if not isinstance(draft.get("payload"), dict) or not carries_deciding_time(draft):
        return
    ok, reason = seal_bound(store, views, draft)
    if not ok:
        gate.refuse(actor, opname, SEAL_BOUND_RULE, reason, draft=draft)


# ---- the acceptance step (W1) ----------------------------------------------------------------

def carries_deciding_time(draft):
    """Does this ARRIVAL carry a deciding time distinct from its recording? Only such arrivals
    take the acceptance path; everything else is the degenerate case the existing world is made
    of — a synchronous S-plane act decides and appends in one act, so d = r by construction and
    the live fold IS the as-of-d fold. The fast path is therefore not an optimisation but the
    same rule at its degenerate point, which is why the whole existing suite is byte-identical
    with the step live."""
    if _payload(draft).get("time_source") == SUBMISSION_SUBSTITUTED:
        return False
    return _instant(draft.get("occurrence_time")) is not None


def acceptance_law(views, draft):
    """THE LAW IN FORCE AS OF THIS ARRIVAL'S DECIDING TIME — the ordinary law fold, pointed at d
    instead of at the head. One fold, one filter, and the filter is `in_force_at`, the same
    helper the sweep's candidate rule uses. That identity IS design/36 ADDENDUM A.1's
    correction: one rule stated once and applied twice, so no two comparisons exist that could
    resolve the same pair of facts two ways."""
    d = deciding_time(draft) if carries_deciding_time(draft) else None
    if d is None:
        return views.active_rules()
    live = views.active_rules()
    out = {}
    for rid, rule in live.items():
        rec = views.store.by_seq(rule.get("seq"))
        if rec is None or in_force_at(rec, d):
            out[rid] = rule
    return out


# ---- the sweep (W3) --------------------------------------------------------------------------

def crossed_the_gate(e, founding_end):
    """DID THIS RECORD CROSS THE GATE? Only a record that did has an ADMISSION for a
    counterfactual to re-evaluate, and §4b.2's reach test is exactly "re-evaluating X's
    admission flips the recorded outcome". A record appended outside the gate has no recorded
    outcome to flip.

    Exactly two things append outside it, and the gate's own constitution guard already names
    them both: "Genesis and the dual-audit mirror append directly via store._append, bypassing
    the gate, so the founding and the mirror are exempt." So this reads the same two facts the
    estate already computes rather than carrying a list of its own:

      THE FOUNDING — the contiguous founding prefix (views.founding_prefix_end, the walk
        `_anchor_ids` has always done). Sweeping genesis would ask whether the founding was
        permitted by the world the founding created, which has no answer, and the first smoke
        run of this sweep did exactly that: every founding record refused for want of a grant
        that the founding itself was in the middle of minting.

      THE MIRROR — a dual-audit record, recognised by its own `payload.stream` declaration,
        which is the SAME self-declaration the protection layer uses to keep the two streams
        blind to each other. Recognition by what the record says it is, never by an action-name
        list in code."""
    if e["seq"] <= founding_end:
        return False
    return _payload(e).get("stream") not in ("dual-audit", "dual-audit-b")


def _is_bookkeeping(e):
    """Records that are not ACTS in the sweep's sense: refusals (their direction is the re-ask
    view, never an overturn) and the overturns a sweep itself appends."""
    if e.get("refused"):
        return True
    return _payload(e).get("kind") == OVERTURN_KIND


def candidates(store, law_record, head_seq=None, founding_end=0):
    """THE CANDIDATE INTERVAL (§4b.1). Recorded acts X with r(X) < r(L) and d(X) > d(L),
    strictly on both sides.

    Acts with d(X) <= d(L) STAND: legitimacy created at a moment binds acts decided strictly
    after it. Acts arriving after r(L) are never the sweep's business — the ordinary door
    adjudicates them at their own acceptance against the law as of THEIR deciding time, which
    now includes L. That second half is why the candidate set is FIXED for the sweep's life
    (design/36 ADDENDUM A.2): the sweep's own overturns are d = r acts recorded after r(L), so
    §4b.1's own boundary puts them outside, and the sweep does not chase its own output."""
    d_law = deciding_time(law_record)
    r_law = law_record["seq"]
    head = head_seq if head_seq is not None else r_law
    already = overturned_targets(store)
    out = []
    for e in store.all():
        if e["seq"] >= r_law or e["seq"] > head:
            break
        if _is_bookkeeping(e) or not crossed_the_gate(e, founding_end):
            continue
        if e["seq"] in already:
            continue                      # once overturned, never re-judged and never re-overturned
        d = deciding_time(e)
        if d is not None and d_law is not None and d > d_law:
            out.append(e)
    return out


def refusal_candidates(store, law_record, founding_end=0):
    """The other direction's candidates: recorded REFUSALS inside the same interval. A refusal
    is never overturned — an overturn cannot perform an act that never happened, and a record
    claiming an effect that did not occur is the one forbidden lie (§4b.4, RULED)."""
    d_law = deciding_time(law_record)
    r_law = law_record["seq"]
    out = []
    for e in store.all():
        if e["seq"] >= r_law:
            break
        if not e.get("refused") or e["seq"] <= founding_end:
            continue
        if e.get("rule_cited") in CALL_CONFORMANCE_RULES:
            continue
        d = deciding_time(e)
        if d is not None and d_law is not None and d > d_law:
            out.append(e)
    return out


def compute(gate, store, views, law_record, head_seq=None):
    """PHASE ONE: the rounds COMPUTE (design/36 ADDENDUM E.2). Nothing is appended here, and
    that is forced rather than chosen — the guard downstream can refuse, and a sweep that had
    already committed and then refused would leave authority orphaned with the record saying
    so. §4b.5's "until a round appends nothing" reads "until a round ADDS NOTHING TO THE
    COMPUTED OVERTURN SET".

    Returns {"overturned": [entries in record order], "rounds": n, "candidates": n}."""
    head = head_seq if head_seq is not None else law_record["seq"]
    cands = candidates(store, law_record, head, views.founding_prefix_end())
    standing_exclusions = overturned_targets(store)   # what earlier sweeps already settled
    overturned = {}                       # target seq -> entry, THIS sweep only
    rounds = 0
    while True:
        rounds += 1
        added = []
        for X in cands:
            if X["seq"] in overturned:
                continue
            world = world_for(store, X, excluded=standing_exclusions | set(overturned),
                              head_seq=head)
            ok, rule, message = admits(gate, world, X)
            if not ok:
                added.append((X, rule, message))
        if not added:
            break
        previous = list(overturned)
        for X, rule, message in added:
            reaching = _reaching_ancestor(gate, store, X, overturned, previous, head, law_record)
            overturned[X["seq"]] = {
                "target_seq": X["seq"],
                "target_deciding_time": X.get("occurrence_time"),
                "reaching_seq": reaching["seq"],
                "reaching_deciding_time": reaching.get("occurrence_time"),
                "basis": "direct" if reaching["seq"] == law_record["seq"] else "transitive",
                "round": rounds,
                "cite": rule,
                "message": message,
            }
    return {"overturned": [overturned[s] for s in sorted(overturned)],
            "rounds": rounds, "candidates": len(cands)}


def _reaching_ancestor(gate, store, X, overturned, previous_round_set, head, law_record):
    """A TRANSITIVE OVERTURN CITES ITS ANCESTOR, NOT THE LAW (design/36 ADDENDUM A.3; §5's
    record-kind form controls over §4b.3's narrower wording).

    A round-one overturn is reached by L directly: the world gained exactly one thing, so
    nothing else can have flipped it. A later round's overturn fell because an act it depended
    on was excluded, and citing L for that would be a citation that does not carry its own
    refusal — every refusal cites the rule that refused it (P4).

    WHICH ancestor is COMPUTED, never stored: re-admit each of the previous round's exclusions
    ALONE and see which one puts X back. The chain from any transitive overturn back to L is
    then walkable on the record rather than asserted."""
    if not previous_round_set:
        return law_record
    for anc in sorted(previous_round_set):
        trial = (set(overturned) | overturned_targets(store)) - {anc}
        world = world_for(store, X, excluded=trial, head_seq=head)
        ok, _, _ = admits(gate, world, X)
        if ok:
            return store.by_seq(anc)
    return law_record


# ---- the anchor guard, COMPUTED (W4; design/36 ADDENDUM E.1) ---------------------------------

def _rootless(world):
    """THE CHAINS WITH NOTHING ABOVE THEM, in one world. Two ways a chain loses its root, and
    both are conditions the estate's own law already forbids at mint:

      SPACE — a live grant or role naming a space that does not reach the mother. That is
        gate._constitution_guard's N3 branch verbatim ("authority never orphans"), refused at
        creation for EVERY actor. Overturning a mid-tree space creation puts the record into
        exactly the state N3 exists to keep it out of, and no ordinary act can produce it
        because a space is never retired.

      MAKER — a live grant whose MAKER no longer holds authority tracing to the root. That is
        attenuation read downward: a grant is never wider than its maker, so a grant whose
        maker holds nothing is power delegated by someone who has none. Grounded as a fixpoint
        on the root and the founding anchors, exactly as verification bottoms out at the
        founding (views._verified_accounts) — a cycle of makers never grounds, so it never
        enters, and mutual delegation cannot manufacture a root.

    INERT UNDER THE FOUNDING OPENNESS GRANT, like every other authority leash in this estate:
    the openness grant's maker is a founding anchor and it reaches everyone, so every maker
    holds a rooted grant and nothing is ever rootless until the owner narrows. A narrowed world
    observes both directions."""
    ground = set(world._anchor_ids()) | {world.chain_end(), "SYSTEM"}
    live = world.grants()
    makers = {}
    for gid, g in live.items():
        rec = world.store.by_seq(g.get("seq"))
        makers[gid] = rec["actor"] if rec is not None else None
    holds = {}
    for gid, g in live.items():
        holds.setdefault(g.get("grantee"), []).append(gid)
    rooted, changed = set(), True
    while changed:
        changed = False
        for gid in live:
            if gid in rooted:
                continue
            m = makers[gid]
            if m in ground or any(h in rooted for h in holds.get(m, []) + holds.get("*", [])):
                rooted.add(gid)
                changed = True
    out = []
    mother = world.mother_space()
    for gid, g in live.items():
        sp = g.get("space")
        if sp is not None and not world.space_reaches(mother, sp):
            out.append({"kind": "grant", "id": gid, "space": sp, "why": "space"})
        elif gid not in rooted:
            out.append({"kind": "grant", "id": gid, "maker": makers[gid], "why": "maker"})
    for rid, r in world.roles().items():
        sp = r.get("space")
        if sp is not None and not world.space_reaches(mother, sp):
            out.append({"kind": "role", "id": rid, "space": sp, "why": "space"})
    return out


def anchor_verdict(store, views, excluded, head_seq=None):
    """THE GUARD'S TRIGGER IS COMPUTED, NOT MATCHED.

    §4b.7 named three kinds of target — a handover, a succession, a root grant — and that was
    an effect-level invariant lowered into a kind-match. The owner ruled it a CORRECTION rather
    than a widening (design/36 ADDENDUM E.1): the invariant was always CONST-AUTHORITY-ANCHORED
    — no chain left rootless, root never moved — and the narrow trigger was the thing that
    needed justifying and never had it. So this function READS NO ACT KIND. It asks the anchor
    law's own two questions of the sweep's POST-STATE.

    IT ASKS THEM DIFFERENTIALLY, and that is derived rather than softened. The question is what
    THIS SWEEP would do, so both limbs compare the post-state against the pre-state. Asked
    absolutely, the maker limb would refuse sweeps for a condition ORDINARY operation creates
    freely — a revoke supersedes and nothing cascades, so a live grant whose maker's own grant
    was revoked is an everyday state of this record, not damage. A guard that refused every
    sweep over a world with an ordinary revoke in it would be unusable, and would be enforcing
    an invariant the estate does not hold. What the anchor law forbids is a sweep ENDING a
    chain, and that is a difference.

    THE FIXED POINT IS THE RIGHT PLACE, and for the reason that produced the correction:
    orphaning is EMERGENT across the transitive rounds. A chain can be ended one ordinary
    overturn at a time with no single step touching an anchor act of any kind, so a per-overturn
    guard sees nothing wrong at every step of a sweep that finishes with authority orphaned.
    Checking earlier than the fixed point would also OVER-refuse, since a chain can be
    transiently rootless mid-round and whole again by the end.

    Returns (ok, reason, detail)."""
    head = head_seq if head_seq is not None else len(store.events)
    post = Views(WorldStore(store, None, head + 1, excluded, head))
    pre = Views(WorldStore(store, None, head + 1, (), head))

    before, after = pre.chain_end(), post.chain_end()
    detail = {"root_before": before, "root_after": after, "orphaned": []}
    if before != after:
        return False, (
            f"the sweep's post-state moves root authority from {before!r} to {after!r} — root "
            "moves only by the recorded succession ceremony, never as the side effect of a "
            "reconciliation, so this sweep routes to the owner rather than ending the chain it "
            "stands on"), detail

    was = {(o["kind"], o["id"]) for o in _rootless(pre)}
    now = [o for o in _rootless(post) if (o["kind"], o["id"]) not in was]
    if now:
        detail["orphaned"] = now
        names = ", ".join(f"{o['kind']} {o['id']} ({o['why']})" for o in now[:4])
        return False, (
            f"the sweep's post-state would leave authority with nothing above it: {names} — the "
            "chain below each of these ends where the sweep cut it, and root authority is never "
            "orphaned. Nothing is appended; the sweep routes to the owner naming the chain it "
            "would have ended"), detail
    return True, None, detail


def guard_declared(views, opname="OVERTURN"):
    """Is the anchor guard wired into this op's OWN DEFINITION? Read from the definition record
    (`definition.anchor_guard`), exactly as the authority regime is read from it — data over
    code, so a cold reader of the founding pack sees the leash. Wire-at-birth (DIGEST-C2 §8)
    means the leash is part of the op's definition in the round the op is created, never a
    later patch."""
    d = (views.op_definitions().get(opname) or {}).get("definition") or {}
    return d.get("anchor_guard")


def overturn_guard(gate, store, actor, opname, draft):
    """THE ANCHOR LEASH AT THE WRITE CHOKEPOINT — not in a handler.

    The campaign-1 theorem, applied again: enforcement lives where every write converges. A
    leash inside OVERTURN's handler is reached past by any other op that mints an overturn-kind
    record — the EP-18 R-A finding exactly. So this fires on ANY op minting one.

    It evaluates the SWEEP'S post-state, never this record's alone. The record declares the
    sweep it belongs to, so every overturn in one commit asks about the SAME final post-state
    and no intermediate round is ever guarded — which is what stops the over-refusal E.1 names
    (a chain transiently rootless mid-round and whole again by the end). A lone hand-rolled
    overturn declares a sweep of one, and its own post-state IS its fixed point."""
    p = draft.get("payload") if isinstance(draft.get("payload"), dict) else None
    if p is None or p.get("kind") != OVERTURN_KIND:
        return
    if not guard_declared(gate.views, draft.get("action") or opname):
        return
    declared = p.get("sweep") or [p.get("target_seq")]
    excluded = {s for s in declared if isinstance(s, int)}
    excluded |= {t for t in overturned_targets(store)}
    ok, reason, detail = anchor_verdict(store, gate.views, excluded)
    if not ok:
        gate.refuse(actor, opname, ANCHOR_RULE, reason, draft=draft)


def overturned_targets(store, as_of=None):
    """Every act the record says has been overturned — a fold, never a stored flag."""
    out = set()
    for e in store.all(as_of):
        p = _payload(e)
        if p.get("kind") == OVERTURN_KIND and isinstance(p.get("target_seq"), int):
            out.add(p["target_seq"])
    return out


# ---- phase two: the commit -------------------------------------------------------------------

def run(gate, store, views, law_record, head_seq=None):
    """THE SWEEP, WHOLE. Compute the rounds, guard the post-state, then commit in one act.

    A refusal means NOTHING was appended and the whole sweep routes to the owner. That is not a
    policy choice: an act once overturned is never un-overturned, so a partially committed
    sweep that then refused would leave the record asserting an orphaned authority it cannot
    honour.

    The overturns cross the gate as ORDINARY GOVERNED ACTS and therefore meet every standing
    check — the protected-core floor and the conservation law included. Stated here rather than
    left to inference (design/36 ADDENDUM A.4's second half), because a system act above the
    protected core would gap a shield the conservation law says is never gapped."""
    head = head_seq if head_seq is not None else len(store.events)
    computed = compute(gate, store, views, law_record, head)
    entries = computed["overturned"]
    excluded = {e["target_seq"] for e in entries} | overturned_targets(store)
    ok, reason, detail = anchor_verdict(store, views, excluded, head)
    result = {"law_seq": law_record["seq"], "rounds": computed["rounds"],
              "candidates": computed["candidates"], "computed": entries,
              "committed": [], "refused": None, "anchor": detail,
              "re_ask": re_ask_cases(gate, store, views, law_record, excluded, head)}
    if not ok:
        result["refused"] = {"rule": ANCHOR_RULE, "reason": reason}
        return result
    sweep = [e["target_seq"] for e in entries]
    drafts = [(e, _overturn_params(e, law_record, sweep)) for e in entries]
    # THE COMMIT IS PRE-CHECKED, WHOLE, BEFORE ANY OF IT LANDS. The sweep's overturns cross the
    # gate as ordinary governed acts, so a recorded structural don't over OVERTURN — or any
    # other standing check — can refuse one. Discovering that halfway through the commit would
    # leave a PARTIAL sweep on the record, which is the very shape the two-phase structure
    # exists to make impossible. So every planned overturn is put through the gate's own
    # admission test dry first, and one refusal refuses the whole sweep with nothing appended.
    for e, params in drafts:
        world = Views(WorldStore(store, None, len(store.events) + 1, (), len(store.events)))
        probe = {"actor": "SYSTEM", "action": "OVERTURN", "object": f"record:{e['target_seq']}",
                 "rule_cited": OVERTURN_RULE,
                 "payload": dict(params, kind=OVERTURN_KIND, record_class="DECISION")}
        ok, rule, message = admits(gate, world, dict(probe, seq=len(store.events) + 1),
                                   opname="OVERTURN")
        if not ok:
            result["refused"] = {"rule": rule, "reason": message}
            return result
    for e, params in drafts:
        result["committed"].append(gate.execute("OVERTURN", "SYSTEM", params)["seq"])
    return result


def _overturn_params(entry, law_record, sweep):
    return {"target_seq": entry["target_seq"], "reaching_seq": entry["reaching_seq"],
            "target_deciding_time": entry["target_deciding_time"],
            "reaching_deciding_time": entry["reaching_deciding_time"],
            "sweep": sweep, "law_seq": law_record["seq"], "round": entry["round"],
            "basis": entry["basis"], "reason": entry["message"]}


def pending(gate, store, views, as_of=None):
    """EVERY SWEEP THE RECORD IMPLIES, RECOMPUTED — including the ones that REFUSED.

    A refused sweep appends nothing (ADDENDUM E.2: a refusal means nothing was appended), so
    there is no record of it to read. That is not a thing going quiet: it is the estate's own
    answer applied to itself — do not store it, COMPUTE it. Anyone holding the record can
    recompute every law-family arrival's sweep and see its verdict, including the chain a
    refused one would have ended. Nothing is stored and nothing can rot."""
    out = []
    for e in store.all(as_of):
        if not is_law_family(e):
            continue
        d, r = deciding_time(e), recording_time(e)
        if d is None or r is None or not (d < r):
            continue
        computed = compute(gate, store, views, e, e["seq"])
        excluded = {x["target_seq"] for x in computed["overturned"]}
        ok, reason, detail = anchor_verdict(store, views, excluded, e["seq"])
        out.append({"law_seq": e["seq"], "rounds": computed["rounds"],
                    "would_overturn": [x["target_seq"] for x in computed["overturned"]],
                    "committed": sorted(t for t in overturned_targets(store, as_of)
                                        if t in excluded),
                    "anchor_ok": ok, "anchor_reason": reason, "anchor": detail})
    return out


# ---- the RE-ASK view (W5; §4b.4 RULED) -------------------------------------------------------

def re_ask_cases(gate, store, views, law_record, excluded, head_seq=None):
    """DIRECTION TWO: a refusal that would now permit. NOTHING IS APPENDED.

    An overturn cannot perform an act that never happened, and a record claiming an effect that
    did not occur is the one forbidden lie. So the case surfaces here and the remedy is
    re-submission at the current head, by the actor, through the ordinary door (RULED, owner,
    2026-07-26, design/36 §11 item 4).

    Two bases, both honest and both labelled, because they are not equally strong:

      re-evaluated — the refusal recorded the DRAFT it refused (every refusal at the gate's own
        steps does), so its admission is re-run in the sweep's world and the case appears only
        if it now permits;
      surfaced — the refusal fired inside a handler check, before a draft existed, so its
        parameters are not on the record and cannot be: a secret candidate never lands there.
        The case is surfaced for a human rather than computed, and says so. This is the class
        design/36 ADDENDUM A.2 names — a refusal that depended on a limit another act had
        already consumed, where excluding the consuming act would free the limit."""
    founding_end = views.founding_prefix_end()
    if not excluded and not candidates(store, law_record, None, founding_end):
        return []
    out = []
    for R in refusal_candidates(store, law_record, founding_end):
        p = _payload(R)
        drafted = p.get("draft")
        case = {"refusal_seq": R["seq"], "op": p.get("op"), "actor": R.get("target"),
                "rule_cited": R.get("rule_cited"), "law_seq": law_record["seq"]}
        if drafted:
            world = world_for(store, dict(drafted, seq=R["seq"]), excluded=excluded,
                              head_seq=head_seq)
            ok, _, _ = admits(gate, world, dict(drafted, seq=R["seq"]), opname=p.get("op"))
            if not ok:
                continue
            case["basis"] = "re-evaluated"
        else:
            case["basis"] = "surfaced"
        out.append(case)
    return out


def re_ask(store, views, gate=None, as_of=None):
    """THE STANDING RE-ASK VIEW: every sweep's re-ask cases, derived from the record. Kill it,
    replay, identical — it holds nothing."""
    out = []
    for e in store.all(as_of):
        if not is_law_family(e):
            continue
        d, r = deciding_time(e), recording_time(e)
        if d is None or r is None or not (d < r):
            continue
        excluded = {t["target_seq"] for t in _overturns_of_law(store, e["seq"], as_of)}
        if gate is None:
            for R in refusal_candidates(store, e, views.founding_prefix_end(as_of)):
                p = _payload(R)
                out.append({"refusal_seq": R["seq"], "op": p.get("op"), "actor": R.get("target"),
                            "rule_cited": R.get("rule_cited"), "law_seq": e["seq"],
                            "basis": "surfaced"})
        else:
            out.extend(re_ask_cases(gate, store, views, e, excluded, as_of))
    return out


def _overturns_of_law(store, law_seq, as_of=None):
    out = []
    for e in store.all(as_of):
        p = _payload(e)
        if p.get("kind") == OVERTURN_KIND and p.get("law_seq") == law_seq:
            out.append(dict(p))
    return out


# ---- the EXPOSURE view (W5; §4b.6 RULED) -----------------------------------------------------

def exposure(store, as_of=None):
    """WHO CONSUMED WHAT, UNDER WHICH OVERTURNED ACT.

    The sweep reconciles STATE. What was already consumed under a since-overturned act — bytes
    read, an answer delivered — is out of mechanical reach, and the owner ruled that no stronger
    mechanical remedy is wanted (design/36 §11 item 3, RULED 2026-07-26). The remedy is human
    judgment on the deontic side; what the machine owes is the honest list.

    Derived from two record facts and nothing else: an overturn names its target, and a CONSUME
    names its object. A consumption is exposed iff it consumed the overturned act's object at or
    after the act itself."""
    overturns = {}
    for e in store.all(as_of):
        p = _payload(e)
        if p.get("kind") == OVERTURN_KIND and isinstance(p.get("target_seq"), int):
            overturns[p["target_seq"]] = e["seq"]
    out = []
    if not overturns:
        return out
    targets = {}
    for seq, overturn_seq in overturns.items():
        target = store.by_seq(seq)
        if target is not None and target.get("object") is not None:
            targets.setdefault(target["object"], []).append((seq, overturn_seq))
    for e in store.all(as_of):
        if e["action"] != "CONSUME":
            continue
        for seq, overturn_seq in targets.get(e.get("object"), []):
            if e["seq"] >= seq:
                out.append({"consumer": e["actor"], "object": e.get("object"),
                            "consumed_seq": e["seq"], "overturned_seq": seq,
                            "overturn_seq": overturn_seq})
    return out


# ---- the session registry (W2; K10) ----------------------------------------------------------

def sessions(store, as_of=None):
    """SESSIONS ARE KNOWN CONTACT POINTS — a derived registry, never a stored table.

    A decider's live working context is two records: a session-open naming the account and its
    DECLARED read-set, and a session-close. Live-or-closed is the difference between them; kill
    this fold and replay and it comes back identical.

    THE READ-SET IS DECLARED, AND DECLARED IS DERIVED NECESSITY RATHER THAN LAZINESS. Reads
    append nothing by design (I9), so the store CANNOT compute what a session has looked at.
    The seal is what makes under-declaration harmless to legitimacy and merely inconvenient: a
    session that under-declares gets fewer pushes and its decisions still face the seal at
    acceptance (design/36 K10).

    The read-set is stored as view REFS and resolved at use — a resolved copy would be a
    frozen derivative of a definition that can be amended."""
    out = {}
    for e in store.all(as_of):
        p = _payload(e)
        if p.get("kind") != SESSION_KIND:
            continue
        sid = p.get("session_id")
        if sid is None:
            continue
        if p.get("event") == "open":
            out[sid] = {"session_id": sid, "account": p.get("account") or e["actor"],
                        "read_set": list(p.get("read_set") or []), "opened_seq": e["seq"],
                        "closed_seq": None, "state": "live"}
        elif p.get("event") == "close" and sid in out:
            out[sid]["closed_seq"] = e["seq"]
            out[sid]["state"] = "closed"
    return out


def live_sessions(store, as_of=None):
    return {s: c for s, c in sessions(store, as_of).items() if c["state"] == "live"}


def session_read_set(store, views, session_id, as_of=None):
    """Resolve a session's DECLARED read-set at use. A ref that names no live view definition
    resolves to None and says so — a dangling declaration is visible, never silently empty."""
    s = sessions(store, as_of).get(session_id)
    if s is None:
        return None
    defs = views.view_definitions(as_of)
    out = {}
    for ref in s["read_set"]:
        name = ref.split(":", 1)[1] if ref.startswith("view:") else ref
        out[ref] = defs.get(name)
    return out


# ---- the sweep's own products, as views ------------------------------------------------------

def overturns(store, as_of=None):
    """Every overturn on the record, in record order. A DERIVED reading of appended decisions —
    the acts and their overturns are both permanently on the record."""
    out = []
    for e in store.all(as_of):
        p = _payload(e)
        if p.get("kind") == OVERTURN_KIND:
            out.append({"overturn_seq": e["seq"], **{k: v for k, v in _thaw(p).items()
                                                     if k not in ("kind", "record_class")}})
    return out


def standing(store, seq, as_of=None):
    """Does the recorded act at `seq` still stand? The reconciled answer, computed forward from
    the overturn's own record_time. An asOf BEFORE the overturn still answers True, because
    order is untouched and validity is what changed — two frames, two answers, no
    contradiction."""
    return seq not in overturned_targets(store, as_of)


class Deferred:
    """A law-family submission held while a sweep runs (design/36 ADDENDUM A.5). Replay
    reproduces whatever record order occurred either way; what serialization buys is that two
    identical INPUTS cannot produce two different results depending on the interleaving, and
    the estate's determinism standard is stronger than replay-determinism alone."""

    __slots__ = ("op", "actor", "params", "record")

    def __init__(self, op, actor, params):
        self.op, self.actor, self.params, self.record = op, actor, params, None


def submit(gate, op, actor, params):
    """THE SERIALIZED DOOR for a law-family submission. A sweep in flight holds the arrival;
    the sweep reaches its fixed point and commits, and only then is the held arrival accepted —
    so the next sweep computes its candidates from the settled record."""
    if getattr(gate, "_sweep_active", 0):
        d = Deferred(op, actor, params)
        gate._law_queue.append(d)
        return d
    return gate.execute(op, actor, params)
