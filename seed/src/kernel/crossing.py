"""gov-os kernel — the crossing: external answers as frozen inputs (EP-23; design/36 K8/K9,
design/34, wall primitives 1, 2, 5, 6).

THE SEAM. An operation may name an executor OUTSIDE the S-plane. Meeting one, the
interpreter does not run a handler to completion: it appends a HAND-OUT DECISION carrying
the sealed, version-pinned question, and the crossing is then OPEN — as a matter of DERIVED
state, not of anything held anywhere. The answer comes back later as an INPUT-class record
that cites the hand-out. Those two records are the whole crossing.

THE REFERENCE THIS MODULE REFUSES: async RPC — a future held in memory awaiting resolution,
a callback registry mapping request-ids to handlers, an in-band correlation token trusted
when it returns. Taking it erases three laws at once.

  REPLAY. A future dies with its process. The record machine must reconstruct every
  in-flight crossing from records alone, so an in-memory registry of open crossings is
  exactly the stored-status shape P2 forbids. Here `crossings()` is a fold: kill it, replay,
  it comes back identical.

  CORRELATION. The store binds request to response by records citing records. An in-band
  token proves nothing, because nothing binds the token to the hand-out except the store's
  own record of it. So the binding is the HAND-OUT RECORD'S SEQ — minted by the store,
  unforgeable by construction, and ambiguous never. An answer may carry whatever token it
  likes in its content; the binding reads the citation and ignores the claim (wall
  primitive 6, T-CORRELATION-DERIVED).

  NEVER RE-RUN THE ANSWERER. A replayed future would call the answerer again. Replay
  consumes the frozen answer as INPUT and never re-invokes anything — the clock-as-sensor
  ruling generalized to every oracle (wall primitive 2; TICK-POLICY is its first instance
  and this is its family).

Suspend is a fold answer. Resume is a fold answer. Nothing waits in memory.

THE SEAL (design/34 §1). fp(S) = H( pack_def_id@version ‖ canonical( fold(record, pack_def,
asOf=S) ) ). Minted at hand-out over the station's DECLARED input-view; recomputed at return
under the SAME pack version; unchanged means the question put to the answerer is again the
current question, so the answer transfers. The pack VERSION is pinned at hand-out rather
than declared on the station, because the version that matters is the one the answerer was
actually shown.

TWO VERDICTS, NEVER MERGED (design/34 §2). Staleness asks whether the judged world is still
the world; authority asks whether the resulting act is lawful NOW. A revoked chain refuses
at the door with the fingerprint HOLDING; a moved read-set refuses on staleness with every
act still lawful. Both run, neither substitutes, and the gate's step order puts authority
first so a revoked chain never comes back labelled stale.

STATE-EQUALITY, NOT HISTORY-EQUALITY (design/34 §3). Write-then-revert inside the read-set
EXECUTES: the question is once again the current question and the excursion is on the record
for audit. Where a station genuinely needs path-sensitivity it declares an INTERVAL GUARD —
a separate, optional view predicate over (hand-out, now], OFF by default. It is deliberately
not folded into the seal: conflating state-validity with path-validity makes both untestable.
"""

from . import canonical

# The two rules this seam's refusals cite. Both are RECORDS in the founding pack (law is
# data, P5); these constants only name them, exactly as gate.py names P3-CLOSURE and AR-2.
CORRELATION_RULE = "CROSSING-CORRELATION"
STALE_RULE = "CROSSING-STALE"

# The three payload kinds of the crossing family. One uniform kind per role, so the gate's
# chokepoint recognises a crossing record by WHAT IT IS. Which STATION a hand-out belongs to
# is the record's ACTION — the natural dimension for a narrowed grant to discriminate on.
HANDOUT_KIND = "crossing-handout"
ANSWER_KIND = "crossing-answer"
CREDENTIAL_KIND = "crossing-credential"

#: The crossing family: records that cite a hand-out and are bound by the store's own
#: correlation law. The gate's chokepoint guard fires on exactly these.
CITING_KINDS = (ANSWER_KIND, CREDENTIAL_KIND)

#: The executor values a station definition may declare. CLOSED, like the check vocabulary
#: and the view-trigger vocabulary: an unknown executor does not exist.
EXECUTORS = ("external",)

#: The pins a station must DECLARE (wall primitive 5). The fourth pin — the context snapshot
#: hash — is the seal, computed at hand-out; it cannot be declared because it is a
#: measurement of the world, not a property of the station.
DECLARED_PINS = ("template", "answerer_identity", "parser")

#: Payload keys the interpreter owns on a hand-out. A station's own declared payload fields
#: may not use these names (they are the crossing's own vocabulary), and `re_judge` strips
#: them when it reconstructs the original question.
RESERVED = ("kind", "record_class", "station", "input_view", "seal", "pins",
            "credential", "interval_guard", "parent_handout_seq")


# ---- station declaration: refused at DEFINITION time (T-CONTEXT-PINNED) --------------------

def validate_station(gate, actor, opname, name, d):
    """A station definition is checked when it is DEFINED, not when it first hands out.

    Same discipline as the closed check vocabulary: a definition naming an unknown check is
    refused at definition time because a check outside the vocabulary does not exist. A
    station missing a pin is refused for the same reason — without its pins a hand-out is
    unrecordable (attribution would be nominal, wall primitive 5's cost-if-absent), and a
    station that cannot produce a valid hand-out must not be admitted and then fail in
    flight. Cites AR-2, the nonconforming-call citation the unknown-check branch already
    uses: the CALL is malformed, which is a different question from whether the act is
    permitted."""
    ex = d.get("executor")
    if ex not in EXECUTORS:
        gate.refuse(actor, opname, "AR-2",
                    f'unknown executor "{ex}" for operation "{name}" — the executor vocabulary is: '
                    + ", ".join(EXECUTORS))
    c = d.get("crossing") or {}
    view = c.get("input_view")
    if not view or not isinstance(view, str) or not view.startswith("view:") or "@" in view:
        gate.refuse(actor, opname, "AR-2",
                    f'station "{name}" must declare crossing.input_view as "view:<name>" — the '
                    "seal is the hash of that view's content, and its VERSION is pinned at hand-out "
                    "(the version that matters is the one the answerer was shown), never declared")
    for pin in DECLARED_PINS:
        v = c.get(pin)
        if not v or not isinstance(v, str):
            gate.refuse(actor, opname, "AR-2",
                        f'station "{name}" declares no {pin} — every external call is version-pinned '
                        "whole-context (template, answerer identity, parser, and the context seal); "
                        "without all four, attribution is nominal")
        if "@" not in v:
            gate.refuse(actor, opname, "AR-2",
                        f'station "{name}" pins {pin} as {v!r}, which names no version — an unversioned '
                        "pin is not a pin")
    guard = c.get("interval_guard")
    if guard is not None and (not isinstance(guard, str) or not guard.startswith("view:") or "@" in guard):
        gate.refuse(actor, opname, "AR-2",
                    f'station "{name}" declares interval_guard {guard!r} — an interval guard is a view '
                    'predicate named "view:<name>" (its version is pinned at hand-out, like the pack)')


# ---- the pack: what the answerer was shown, computed by the ordinary view engine -----------

def resolve_pack(store, pack_ref):
    """Resolve a pinned view reference "view:<name>@<seq>" to the DEFINING RECORD'S payload.

    The version pin is the seq of the CREATE-VIEW record that defined it. That is exact and
    needs no version registry: a view amended after hand-out is a different definition at a
    different seq, and design/34 §1 says the return recomputes with the SAME pack version —
    so the return reads the definition the answerer was actually shown, not today's. Returns
    None if the reference names no such definition (a dangling pin)."""
    if not isinstance(pack_ref, str) or "@" not in pack_ref:
        return None
    body, _, seq = pack_ref.rpartition("@")
    if not body.startswith("view:") or not seq.isdigit():
        return None
    rec = store.by_seq(int(seq))
    if rec is None or rec["action"] != "CREATE-VIEW":
        return None
    p = rec.get("payload") or {}
    if p.get("kind") != "view_definition" or f"view:{p.get('name')}" != body:
        return None
    return p


def pack_content(store, views, pack_ref, as_of=None):
    """The CONTENT of a pinned view, asOf a point — the thing the seal hashes.

    Two shapes, because the estate's view engine has two. A MASTER (one that binds an
    S-plane fold) answers with derived STATE; a FILTER view answers with the records its
    trigger matched, which is HISTORY — so those are folded LATEST-WINS PER OBJECT down to
    their payloads, which is the state of the objects the view watches. That fold is not a
    new mechanism: it is the shape `active_rules`, `roles`, `spaces` and `_resources` all
    already use, with the envelope's ordering fields left where they belong.

    Both shapes then pass through `strip_derivation`: a fold's `seq` decoration is the
    record's ORDER, and design/34 §3 rules a fingerprint state-equal and not history-equal.
    Sealing order would turn the ruled ABA behaviour into its opposite.

    Raises LookupError on a dangling pin — callers refuse; nothing guesses."""
    d = resolve_pack(store, pack_ref)
    if d is None:
        raise LookupError(f"{pack_ref} names no view definition — the pinned pack does not resolve")
    if d.get("bind"):
        fold = views._fold(d["bind"])
        if fold is None:
            raise LookupError(f"{pack_ref} binds fold {d['bind']!r}, which is not in the fold library")
        value = fold(as_of)
    else:
        from .views import _matches                  # lazy: views imports this module's folds
        latest = {}
        for e in store.all(as_of):
            if _matches(e, d.get("when") or {}):
                latest[e.get("object")] = e.get("payload") or {}
        value = latest
    return canonical.strip_derivation(value)


def seal_of(store, views, pack_ref, as_of=None):
    """fp(S) = H( pack_def_id@version ‖ canonical( fold(record, pack_def, asOf=S) ) ), design/34 §1.
    The pack reference is hashed WITH the content: two different views that happen to answer
    the same today are not the same question."""
    return canonical.canonical_hash({"pack": pack_ref, "content": pack_content(store, views, pack_ref, as_of)})


# ---- the crossing folds: suspend and resume are fold answers -------------------------------

def handout_at(store, seq):
    """The hand-out record at `seq`, or None. The crossing's identity IS this seq: it is
    minted by the store at append, so no caller can choose it, forge it, or collide it."""
    if not isinstance(seq, int) or isinstance(seq, bool):
        return None
    rec = store.by_seq(seq)
    if rec is None or (rec.get("payload") or {}).get("kind") != HANDOUT_KIND:
        return None
    return rec


def crossings(store, as_of=None):
    """Every crossing, DERIVED: {handout_seq: {...}} with its state computed, never stored.

      open       — handed out, no answer cites it, no re-judge supersedes it
      answered   — an answer-returned INPUT cites it
      superseded — a later hand-out names it as parent (a re-judge after a stale return)

    Three states, all differences between records. Kill this and replay: identical."""
    out = {}
    for e in store.all(as_of):
        p = e.get("payload") or {}
        if p.get("kind") == HANDOUT_KIND:
            out[e["seq"]] = {"handout_seq": e["seq"], "station": p.get("station"),
                             "input_view": p.get("input_view"), "seal": p.get("seal"),
                             "pins": dict(p.get("pins") or {}),
                             "interval_guard": p.get("interval_guard"),
                             "credential": dict(p.get("credential") or {}) or None,
                             "parent_handout_seq": p.get("parent_handout_seq"),
                             "answered_by": None, "superseded_by": None,
                             "credential_verified": None, "state": "open"}
    for e in store.all(as_of):
        p = e.get("payload") or {}
        kind, ref = p.get("kind"), p.get("handout_seq")
        if kind == ANSWER_KIND and ref in out and out[ref]["answered_by"] is None:
            out[ref]["answered_by"] = e["seq"]
            out[ref]["state"] = "answered"
        elif kind == CREDENTIAL_KIND and ref in out:
            out[ref]["credential_verified"] = (p.get("result") == "MATCH")
        elif kind == HANDOUT_KIND and p.get("parent_handout_seq") in out:
            parent = out[p["parent_handout_seq"]]
            if parent["superseded_by"] is None:
                parent["superseded_by"] = e["seq"]
                if parent["state"] == "open":
                    parent["state"] = "superseded"
    return out


def state_of(store, handout_seq, as_of=None):
    """One crossing's correlation state: missing | open | answered | superseded. ONE
    computation, consulted by BOTH enforcement points on the write path (the station's
    declared check inside the handler, and the gate's chokepoint guard after it) — one law,
    one home, two places it binds."""
    c = crossings(store, as_of).get(handout_seq)
    return "missing" if c is None else c["state"]


def open_crossings(store, as_of=None):
    """The IN-FLIGHT view: hand-outs minus answers minus re-judges. This is the whole of
    "what is suspended" — a difference between records, held nowhere."""
    return {s: c for s, c in crossings(store, as_of).items() if c["state"] == "open"}


def fingerprint(store, views, handout_seq, as_of=None):
    """Is the judged world still the world? A PURE READ, answerable at any time and by
    anyone — which is what makes staleness and authority two separately observable verdicts
    rather than one merged outcome (design/34 §2). Recomputes the pinned pack asOf `as_of`
    (head by default) and compares to the hash recorded at hand-out.

    Audit property (design/34 §6): the mint is DERIVABLE from the record by replay, so a
    hand-out's seal can be proven honest after the fact. The fingerprint is checked data,
    never trusted data."""
    h = handout_at(store, handout_seq)
    if h is None:
        return {"resolves": False, "holds": False, "recorded_seal": None, "current_seal": None,
                "pack": None, "reason": "no hand-out at that seq"}
    p = h.get("payload") or {}
    pack = p.get("input_view")
    try:
        current = seal_of(store, views, pack, as_of)
    except LookupError as exc:
        return {"resolves": False, "holds": False, "recorded_seal": p.get("seal"),
                "current_seal": None, "pack": pack, "reason": str(exc)}
    return {"resolves": True, "holds": current == p.get("seal"), "recorded_seal": p.get("seal"),
            "current_seal": current, "pack": pack, "reason": None}


def interval_moved(store, handout_seq, as_of=None):
    """The OPTIONAL interval guard (design/34 §3), OFF unless a station declares one: did any
    record matching the declared predicate land in (hand-out, now]? This is path-sensitivity,
    kept deliberately OUTSIDE the seal — the seal answers state-validity, this answers
    path-validity, and conflating them makes both untestable. Returns None when no guard is
    declared."""
    h = handout_at(store, handout_seq)
    if h is None:
        return None
    guard = (h.get("payload") or {}).get("interval_guard")
    if not guard:
        return None
    d = resolve_pack(store, guard)
    if d is None:
        return {"moved": False, "resolves": False, "guard": guard, "hits": []}
    from .views import _matches
    hits = [e["seq"] for e in store.all(as_of)
            if e["seq"] > handout_seq and _matches(e, d.get("when") or {})]
    return {"moved": bool(hits), "resolves": True, "guard": guard, "hits": hits}


def stale_crossings(store, views, as_of=None):
    """Open crossings whose judged world has moved. DERIVED — not read off refusal records.

    A refusal record is evidence that someone tried to return; whether a crossing IS stale is
    a question about the world, answerable before anyone tries and after everyone stops. P2
    in its plainest form: compute the state, never store it."""
    out = {}
    for seq, c in open_crossings(store, as_of).items():
        fp = fingerprint(store, views, seq, as_of)
        if not fp["holds"]:
            out[seq] = {**c, "fingerprint": fp}
    return out


# ---- policy on stale, v1 (design/34 §4, lowered minimally) ---------------------------------

def _policy(views, key, station, as_of=None):
    """A per-station policy value with a default, both RECORDED (law is data, P5): the
    station-specific key wins, else the founding default. Retry budgets are policy records
    with a named owner — never constants in code."""
    v = views.policy_value(f"{key}:{station}", as_of)
    return v if v is not None else views.policy_value(f"{key}-default", as_of)


def retry_state(store, views, handout_seq, as_of=None):
    """What v1 policy says about a stale crossing: the station's stale policy, its retry
    budget, how many re-judges this chain has already spent, and whether one remains.
    Attempts are COUNTED from the parent chain in the record — no attempt counter exists."""
    h = handout_at(store, handout_seq)
    if h is None:
        return None
    p = h.get("payload") or {}
    station = p.get("station")
    spent, node, seen = 0, p.get("parent_handout_seq"), set()
    while node is not None and node not in seen:
        seen.add(node)
        spent += 1
        parent = handout_at(store, node)
        node = (parent.get("payload") or {}).get("parent_handout_seq") if parent else None
    budget = _policy(views, "crossing-retry-budget", station, as_of)
    policy = _policy(views, "crossing-stale-policy", station, as_of)
    budget = 0 if budget is None else int(budget)
    return {"station": station, "policy": policy, "budget": budget, "spent": spent,
            "remaining": max(0, budget - spent),
            "may_re_judge": policy == "re-judge" and spent < budget}


def re_judge(gate, store, views, actor, handout_seq):
    """Mint a fresh crossing at the CURRENT head for a stale one, parent-linked.

    Never silent execute; never silent drop (design/34 §4). The stale refusal is already
    recorded citing the staleness rule before this runs — this is the recorded remedy, an
    ordinary gated act that re-asks the same question against the world as it now is. On a
    policy of abort, or on budget exhaustion, it returns None and the case surfaces on the
    re-ask view: the stale refusal stands and a human decides.

    The original question is reconstructed FROM THE RECORD (the hand-out's own declared
    payload fields), not from anything a caller kept."""
    h = handout_at(store, handout_seq)
    if h is None:
        return None
    rs = retry_state(store, views, handout_seq, None)
    if not rs["may_re_judge"]:
        return None
    p = h.get("payload") or {}
    station = p.get("station")
    d = (views.op_definitions().get(station) or {}).get("definition") or {}
    fields = d.get("payload_from") or list((d.get("params") or {}).keys())
    params = {f: p.get(f) for f in fields if f not in RESERVED}
    params["parent_handout_seq"] = handout_seq
    return gate.execute(station, actor, params)


def needing_reask(store, views, as_of=None):
    """Stale crossings the machine may not retry — the case SURFACES for a human re-ask
    (design/34 §4's escalation floor). A derived view; it appends nothing."""
    out = {}
    for seq, c in stale_crossings(store, views, as_of).items():
        rs = retry_state(store, views, seq, as_of)
        if rs and not rs["may_re_judge"]:
            out[seq] = {**c, "retry": rs}
    return out


def flutter(store, as_of=None):
    """HOT-READ-SET FLUTTER, surfaced as a view (design/34 §4). A pack whose inputs change
    faster than answer latency produces repeated re-judges on one station. That is a DESIGN
    SMELL — the pack is over-broad, or the station belongs on a coarser view — and the right
    response is to see it, never to weaken the check. {station: re-judges}."""
    out = {}
    for c in crossings(store, as_of).values():
        if c["parent_handout_seq"] is not None:
            out[c["station"]] = out.get(c["station"], 0) + 1
    return out


# ---- the hand-out: what the interpreter appends when it meets an external executor ---------

def handout_fields(gate, store, views, actor, opname, d, p_in):
    """The crossing fields of a hand-out DECISION. Everything the RETURN will need is written
    HERE, into the record: the pinned pack, the seal, the four pins, the interval guard and
    the credential. The return then reads the record and consults nothing that could have
    moved — which is why replay reconstructs a return identically."""
    c = d.get("crossing") or {}
    name = c["input_view"].split(":", 1)[1]
    defn = views.view_definitions().get(name)
    if defn is None:
        gate.refuse(actor, opname, "CAP-IS-LAW",
                    f'station {opname} declares input view "{c["input_view"]}", which is not a defined '
                    "view — the seal is the hash of that view's content, so a hand-out with no pack is "
                    "unrecordable (accepted-but-cannot-honour refuses)")
    pack_ref = f"{c['input_view']}@{defn['seq']}"
    try:
        seal = seal_of(store, views, pack_ref)
    except LookupError as exc:
        gate.refuse(actor, opname, "CAP-IS-LAW", f"{opname}: {exc}")
    fields = {"kind": HANDOUT_KIND, "record_class": "DECISION", "station": opname,
              "input_view": pack_ref, "seal": seal,
              "pins": {**{k: c[k] for k in DECLARED_PINS}, "context": seal}}
    if c.get("interval_guard"):
        gname = c["interval_guard"].split(":", 1)[1]
        gdef = views.view_definitions().get(gname)
        if gdef is None:
            gate.refuse(actor, opname, "CAP-IS-LAW",
                        f'station {opname} declares interval guard "{c["interval_guard"]}", which is not '
                        "a defined view")
        fields["interval_guard"] = f"{c['interval_guard']}@{gdef['seq']}"
    if c.get("credential"):
        # THE VAULT FINDS ITS CONSUMER (design/31 J8; K8). The station names a SEALED secret;
        # the hand-out records WHICH credential this crossing is answered under, by its sealed
        # HASH. The value is not read here and cannot be: the vault's surface is seal + compare
        # and nothing else. A station naming a credential that was never sealed refuses rather
        # than handing out a call it cannot authenticate (accepted-but-cannot-honour refuses).
        h = views.sealed_secret_hash(c["credential"], p_in.get("space"))
        if h is None:
            gate.refuse(actor, opname, "CONST-SECRETS",
                        f'station {opname} presents credential {c["credential"]!r}, which is not sealed '
                        "in this space — a crossing is never handed out under a credential that does not exist")
        fields["credential"] = {"name": c["credential"], "secret_hash": h}
    if p_in.get("parent_handout_seq") is not None:
        fields["parent_handout_seq"] = p_in["parent_handout_seq"]
    return fields


# ---- the fingerprint check kind (design/34 §6, verbatim) -----------------------------------

def check_fingerprint(gate, store, views, actor, opname, c, p_in):
    """"Recompute the declared input-view asOf now; compare canonical hash to the hash
    recorded at hand-out; on mismatch refuse citing the staleness rule."

    Returns the verdict fields the interpreter stamps into the accepted record, so a passed
    check is VISIBLE on the record rather than inferred from the absence of a refusal.

    The correlation branch refuses citing the CORRELATION rule, not the staleness rule: an
    answer that names no open hand-out has not gone stale, it has failed to bind. Two rules,
    two failures, never one blurred citation."""
    seq = p_in.get(c.get("crossing_param", "handout_seq"))
    state = state_of(store, seq)
    if state != "open":
        gate.refuse(actor, opname, c.get("cite_correlation") or CORRELATION_RULE,
                    f"cites hand-out {seq!r}, which is {state} — an answer binds only to an OPEN "
                    "hand-out, and it binds by the STORE'S citation (an in-band token carries no binding)")
    fp = fingerprint(store, views, seq)
    if not fp["resolves"]:
        gate.refuse(actor, opname, c.get("cite_correlation") or CORRELATION_RULE,
                    f"hand-out {seq} pins pack {fp['pack']!r}, which does not resolve: {fp['reason']}")
    if not fp["holds"]:
        gate.refuse(actor, opname, c.get("cite") or STALE_RULE,
                    f"the judged world moved: pack {fp['pack']} sealed {fp['recorded_seal']} at hand-out "
                    f"and computes {fp['current_seal']} now — the question put to the answerer is no "
                    "longer the current question")
    guard = interval_moved(store, seq)
    if guard and guard["moved"]:
        gate.refuse(actor, opname, c.get("cite_interval") or c.get("cite") or STALE_RULE,
                    f"interval guard {guard['guard']} matched records {guard['hits']} inside "
                    f"(hand-out {seq}, now] — this station declared path-sensitivity, so a read-set that "
                    "returned to its sealed state is still refused (state-equal, path-moved)")
    return {"fingerprint_check": "pass", "fingerprint_seal": fp["current_seal"]}


# ---- the gate's chokepoint guard ------------------------------------------------------------

def correlation_guard(gate, store, actor, opname, draft):
    """CORRELATION INTEGRITY, AT THE WRITE CHOKEPOINT — not in a handler.

    The campaign-1 theorem, applied: enforcement lives where every write converges. A leash
    that lives in one op's handler is bypassed by any other op that mints the same record
    shape — that is the EP-18 R-A finding (GRANT's containment reached past by a passthrough
    route), and the answer to it there was to move the leash to the gate so it fires on ANY
    op minting a grant-kind record. This fires on ANY op minting a crossing-family record.

    Two refusals, two rules:
      * a crossing record citing no OPEN hand-out — the correlation rule. This is where "the
        store binds request to response" is actually enforced.
      * an ANSWER carrying no fingerprint verdict — the staleness rule. An acceptance that
        ran no seal check has not been shown to be fresh, and every hand-out carries a seal
        by construction (the pins are mandatory at definition time), so there is no lawful
        answer without one. Without this line the check kind is only as binding as the ops
        that remember to declare it, which is the R-A shape exactly.

    The in-band claim is IGNORED here, deliberately and visibly: an answer may carry any
    token it likes in its content; this reads `handout_seq`, the store's own citation."""
    p = draft.get("payload") if isinstance(draft.get("payload"), dict) else None
    if p is None or p.get("kind") not in CITING_KINDS:
        return
    seq = p.get("handout_seq")
    state = state_of(store, seq)
    if state != "open":
        gate.refuse(actor, opname, CORRELATION_RULE,
                    f"a {p['kind']} record cites hand-out {seq!r}, which is {state} — the store binds "
                    "request to response by records citing records; an unbound or already-closed "
                    "citation carries nothing")
    if p["kind"] == ANSWER_KIND and p.get("fingerprint_check") != "pass":
        gate.refuse(actor, opname, STALE_RULE,
                    "an external answer is accepted only against the world it was judged in, and this "
                    "acceptance carries no fingerprint verdict — the seal was never checked")
