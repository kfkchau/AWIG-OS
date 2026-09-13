<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: build-planning · Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature (kernel, syscall, capability, permission, memory protection). NON-GOAL: no offensive capability of any kind; defines record, gate, view, and kernel-conformance only. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=CANON status=LIVE supersedes=- superseded-by=- verified=2026-07-24 -->
# Judged-state fingerprint — the derivation [SOLVED, pending owner ruling]

**Status:** v1, 2026-07-22, derivation sitting per the touchpoint reference §13
queue item 1 ("SOLVE not specify"). NOT for kernel-building sessions; the
occupant-agnostic landing (§6) is carried into `planning/WALL-PRIMITIVES-HANDOVER.md`
and that carried form is the only sanctioned route into the build. Labels per
the contract; the core definition is SOURCE-DERIVED from standing estate law,
the policy defaults are PROPOSED with costs.

## 0. The problem, exactly

A judgment is requested at hand-out time (store head S₀) and returns later
(head S₁), with lawful writes in between. Two questions were previously
conflated and must not be:

- **Ordering** — which record is first — is already settled by the record's
  total order (record_time / seq). Not this document's problem.
- **Staleness** — does the world the judge reasoned about still exist — is this
  document's problem: what exactly is fingerprinted at S₀, and what "still
  holds" means at S₁.

## 1. The definition (SOURCE-DERIVED)

The judgment is a function of exactly what it was shown: the carrier =
template@version + the context pack, where the pack is COMPUTED by a recorded,
deterministic view-fold (least-context, recorded by hash — standing law).
Therefore:

> **The fingerprint is the canonical hash of the judgment's declared input-view.**
> fp(S) = H( pack_def_id@version ‖ canonical_serialization( fold(record, pack_def, asOf=S) ) )
>
> Mint fp(S₀) at hand-out (it is the context_pack_hash already being recorded,
> promoted to a checked value). At return, recompute fp(S₁) with the SAME
> pack_def@version. **"Still holds" ⟺ fp(S₁) = fp(S₀).**

No new store, no new machinery: the fold is the ordinary view engine, the hash
is recorded in the existing DECISION record at hand-out, the check is one
recomputation at return.

**Why this is the right boundary and not an approximation:**

- **Sufficient.** If the recomputed pack is bit-identical, the question put to
  the judge is again the current question; the verdict transfers. (We never
  re-run the judge to check this — the judge's own nondeterminism is a
  different problem, owned by the acceptance/calibration loop.)
- **Necessary and minimal.** State outside the pack's read-set was, by
  least-context construction, never available to the judge — a change there
  cannot invalidate the judgment's *reasoning*. Invalidating on it would be
  false staleness (and at OS scale, livelock: any unrelated write would void
  every outstanding judgment). The read-set is already recorded; do not invent
  a broader "relevant state" concept (minimality gate).

## 2. The division of labor (the load-bearing separation)

Staleness is NOT the only check at return — and must not try to be:

| Question at return | Owner of the check | Outcome on failure |
|---|---|---|
| Is the judged world still the world? | **Fingerprint** (this doc) | `stale` → abort or re-judge, never silent execute |
| Is the resulting act lawful NOW? | **The gate**, ordinary live evaluation (chain, scope, tier, untouchables — revocation is instant because nothing was stored) | ordinary refusal citing rule |

A capability revoked mid-flight does not stale the judgment — the judgment was
sound; the power to act on it is gone. That is a refusal record, not a
staleness record, and the two carry different information. Conversely, a
changed judged-world with intact capabilities is stale even though every act
would be lawful. Both checks run; neither substitutes.

**Corollary (what belongs in the pack):** if the judgment *interprets law*,
the law it interprets belongs in its pack — then a mid-flight amendment of that
law correctly stales the judgment. Pack scoping is therefore a definition gate
(human), and under-scoping is the one failure fingerprints cannot catch (§5).

## 3. Concurrent lawful amendments — the complete taxonomy

Every possible interleaving falls into exactly one row; nothing needs
case-by-case law:

1. **Write outside the read-set** → fp unchanged → verdict executes (gate still
   enforces current law). Correct by §1-necessity.
2. **Write inside the read-set** → fp differs → stale. Policy per station
   (§4): re-judge (default) or abort.
3. **Write to execution preconditions only** (revoked grant, retired op,
   changed scope) → fp holds, gate refuses at the ordinary hop → refusal
   citing rule. Row 3 is the gate's row, not the fingerprint's.

**The ABA case (state changed away and back):** fp(S₁) = fp(S₀) even though
history moved. This EXECUTES, and that is correct semantics, not a loophole:
fingerprint equality is **state-equality, not history-equality** — the question
the judge answered is once again the current question, and the excursion is on
the record for audit. Where a station genuinely needs path-sensitivity ("no
intervening write by X in (S₀,S₁]"), that is a different, optional check — an
ordinary view predicate over the interval, declared per station
(**interval-guard**), off by default per the minimality gate. Do not fold it
into the fingerprint; conflating state-validity with path-validity is how both
become untestable.

## 4. Policy on stale (PROPOSED defaults; owner calibration)

- Default: **re-judge** — re-mint at current head (new crossing, parent-linked
  to the stale one), within the station's recorded retry budget.
- On budget exhaustion: **abort to the escalation ladder** (the standing
  retry / regenerate / diagnose / human ladder). Never silent execute; never
  silent drop — the stale refusal is recorded citing the staleness rule.
- Cost if the default is wrong: excess re-judging on hot read-sets (a
  backpressure/budget matter — primitive 8's lane, not new fingerprint law).
- **Hot-read-set flutter** (a pack whose inputs change faster than judgment
  latency → livelock of re-judges) is detectable from the record (repeated
  stale records on one station) and is a design smell: the pack is over-broad
  or the station belongs on a coarser view. Surface it as a view; do not
  "fix" it by weakening the check.

## 5. Honest caps

- **Under-scoped packs are out of reach.** If the pack never encoded what
  mattered, fp cannot save the verdict. That is the definition gate (human),
  and it is exactly the same cap the least-context law already carries.
- **Judge nondeterminism untouched.** Same pack, different verdict on re-run is
  a calibration/acceptance matter — fingerprints check the question, not the
  answerer.
- **Canonicalization is TCB-grade.** The serialization under the hash must be
  canonical (key order, encoding normalization) with the same discipline as
  the boundary reparser; a non-canonical serializer manufactures false stales
  (or worse, false holds) invisibly. Its test battery ships with the check.
- Determinism of the fold is assumed — and is already proven estate law
  (replay-identity), so the assumption is load-bearing but not new.

## 6. The kernel landing (occupant-agnostic — the form carried into the handover)

The primitive costs the wall almost nothing because every part already exists
in its vocabulary:

> **One new check kind** — `fingerprint` — beside require_prior / sight /
> ceiling / consistency / sop / due: "recompute the declared input-view asOf
> now; compare canonical hash to the hash recorded at hand-out; on mismatch
> refuse citing the staleness rule."

Requires only: a recorded pack-def reference + a recorded hash (both already in
the hand-out DECISION shape) + the deterministic view engine (exists). The
recomputation runs in the slow governance lane (returns are never hot-path), so
K3/I9 are untouched. Audit property: fp(S₀) is *derivable* from the record by
replay — the mint can be proven honest after the fact; the fingerprint is
checked data, never trusted data.

## 7. Acceptance tests (named before code)

- **T-FP-HOLDS** — untouched read-set across the crossing → verdict executes;
  the applied record carries `fingerprint_check: pass`.
- **T-FP-STALE** — mutate any pack input mid-crossing → return refuses citing
  the staleness rule; re-judge fires within budget, parent-linked.
- **T-FP-ORTHOGONAL-REFUSAL** — revoke the seat's grant mid-crossing, read-set
  untouched → fp passes AND the gate refuses on authority: two distinct
  records, staleness never claimed.
- **T-FP-ABA** — write-then-revert inside the read-set → executes (state-equal),
  interval history intact on the record; with an interval-guard declared, the
  same case refuses.
- **T-FP-REPLAY** — kill everything derived, replay: every fingerprint mint,
  check, stale-refusal and re-judge reconstructs identically (the answer
  consumed as INPUT, the answerer never re-run).
- **T-FP-CANONICAL** — the serialization fuzz set (key order, unicode
  normalization, numeric form) never yields two hashes for one state or one
  hash for two states.

---

## ADDENDUM — 2026-07-25 — RULED: adopted as the backstop of the two-times law (dated addendum)

The owner ruled the larger law this derivation sits inside:
`design/35-TWO-TIMES-OF-AUTHORITY.md` — deciding time carries legitimacy,
recording time carries order; acceptance is a legitimacy-transfer test
adjudicated by deciding time + authority, with THIS document's seal as the
proof of what the decider was shown. The fingerprint lands as the check kind
this document's §6 specifies, as the backstop for the race the session-aware
push cannot close. The C3 launch paper carries both documents together.

---

## ADDENDUM 1 — a fold's derivation decoration is order, not state (2026-07-26, sitting mentor, at the EP-23 verdict)

Appended as a dated addendum on the live canon. Law, and read as part of §3.

**What EP-23 found while landing the seal.** A fold's answer arrives decorated
with fields describing WHERE AND WHEN the answer came from rather than WHAT the
answer IS. The store's `seq` is the instance that surfaced: hash the fold's
output with `seq` included and a write-then-revert inside the read-set produces
a different hash, so the crossing refuses. That is §3's ruled ABA case turned
into its exact opposite, silently, by a field nobody thought of as content.
The builder found it, excluded `seq` by name citing §3, and asked whether the
sentence deserves to be a rule rather than a module comment.

It does, and in a form wider than the instance, because the instance is not
what will recur.

**The rule.** A fold's DERIVATION DECORATION is order and provenance, never
state. Anything the fold adds to describe the answer's position in the record,
its origin, or its recomputation is excluded from the canonical form before
hashing; only what the answer asserts about the world is hashed. `seq` is the
first instance and is excluded by name. Every exclusion is named and cited, so
the canonical form stays a closed enumeration rather than a growing habit.

**Why this is the correct level.** §3 rules that fingerprint equality is
state-equality, not history-equality. A decoration field is history by
definition — it says where the answer sat, not what it says. Hashing it makes
every crossing over that fold history-sensitive, which contradicts §3 for
every future fold at once rather than for one. The two-times law names the
same division at the record's own level: `record_time` and `seq` carry ORDER,
deciding time carries legitimacy, and order was never the fold's subject.

**The cost of leaving it as a convenience, stated because it is the reason
this is filed:** the next fold that decorates its answer with some other
derivation field makes every crossing over it history-sensitive, and the
symptom is false stales that nobody can trace to a cause. A false stale is the
recoverable direction; the same mistake in the other direction, excluding
something that IS state, manufactures false holds and lets a stale decision
execute. Both are why the canonical form's exclusions are enumerated and cited
rather than judged case by case.
