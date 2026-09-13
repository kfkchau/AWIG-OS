<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture (seL4/POSIX/OS-textbook) · Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature (kernel, syscall, capability, permission, memory protection). NON-GOAL: no offensive capability of any kind; defines record, gate, view, and kernel-conformance only. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=CANON status=LIVE supersedes=- superseded-by=- verified=2026-07-24 -->
# GOV-OS — Target State: The Governance-Native Host Kernel

**Status:** v1, 2026-07-15. The end state of the HOST-SPINE campaign: the machine whose
own surface — constitution, operations, views, protections — is governed data in its own
record. This is the stepping stone the depth campaign (03 §6: FUSE authority, in-kernel
replacement) rides on; those stages are OUT OF SCOPE here (§12). Execution is sequenced
in `planning/exec/EXECUTION-PLANS.md`; each plan cites the section here it realizes.

**Cold-start read order:** `00-READ-FIRST.md` → `DESIGN-SOUL.md` → `25-VIEW-TREE.md`
(+ `25-view-tree.json`) → `26-KERNEL-DERIVABILITY-AUDIT.md` → `27-FUNDAMENTAL-RULES.md`
→ this doc → your execution plan. Labels per `00-READ-FIRST.md` §6. Owner rulings
control over everything here.

---

## 1. End-state invariants (the campaign is done when ALL hold)

- **I1 One record.** Append-only jsonl, envelope unchanged forever; extensions are new
  payload kinds, never migrations. Single-writer (multi-writer S5 stays deferred,
  ordering fields carried).
- **I2 The gate is the sole appender.** Handlers RETURN the record they intend; only
  `gate.execute` writes. No code path outside the gate can append. [Realized only if
  the owner rules YES on the standing question; EP-01.]
- **I3 The registry is derived.** Every subsystem operation is a definition record
  (CREATE-OP / RETIRE-OP); one generic interpreter executes all of them; boot replays
  the registry from the record. The only code-registered ops are the bootstrap
  constructors themselves.
- **I4 Views are derived AND defined as records.** The master views ship as seeded
  view-definition records; system views derive from masters; every view has a derived
  coverage statement; caches carry visible staleness.
- **I5 Law never in code.** No rule text, no polarity, no action list, no vocabulary
  with governance content lives in engine code. The only closed vocabularies in code
  are ENGINE surfaces (the check vocabulary, the view trigger dimensions), each labeled,
  each growable only by design amendment. Tested by T-NO-LAW-IN-CODE (§11).
- **I6 The constitution is recorded in full form.** Every root law is trigger→outcome
  (§4), not a sentence. The sentence stays as the human-readable `text`.
- **I7 Refusals cite; polarity is positional.** Rule-level ± = do/don't; trigger-level
  − = "this did not happen"; outcome-level − = "refrain from this step".
  **[EXTENDED BY OWNER RULING 1, 2026-08-04 — placed here 2026-08-08 from its
  interim home at `DISPATCH-LEDGER.md:270`, discharging the placement that
  entry named as the architect's: A REFUSED ACT IS ALWAYS RECORDED. The
  citation is the TIP-LEVEL TERMINAL RULE, never the reasoning chain — once
  capillary-level reasoning records exist, the chain is derivable from history
  and always traces the same, so storing it stores something computable. This
  overturned the absence-class doctrine (a precondition answered by a view
  appending nothing): every rejection of an attempted act appends, whatever
  component answers it. Enforced across the port's whole answer set by the
  EP-28K/N law passes and the W4e retirement. NOTE, ruled 2026-08-08: this
  ruling did NOT open §5's check-kind gate — that gate closed by its own
  explicit act; see §5's GATE STATUS.]**
- **I8 The read stack.** Store → master views → system views. Operations consult system
  views (or live checks backed by them); nothing operational queries the raw store.
- **I9 Hot paths record nothing.** Recording scales with governance, never operation.
  View execution and deliveries are derived flows; only governance-grade acts append.
- **I10 Total round-trip.** Kill EVERYTHING derived — registry, view definitions'
  caches, masters, queues — replay from the record file alone, and the machine
  reconstructs identically, including its own operation surface.
- **I11 Power is under law all the way up (three tiers).** Every rule/op_definition
  carries a `tier`: **constitutional** (nobody may change it THROUGH THE SYSTEM, the
  owner included — every attempt refused and recorded), **owner** (only actor "owner":
  core ops, capacity horizons, calibrations), **ordinary** (anyone with a granted
  chain). The five constitutional laws are `CONST-RECORDING-TOTAL` (no act invisible,
  the audit floor cannot be lowered), `CONST-AUTHORITY-ANCHORED` (root never orphaned,
  succession human-only, never to a pure-agentic actor), `CONST-SECRETS` (verify a
  secret, never reveal it, to anyone), `CONST-SELF-PROTECT` (the constitutional records
  refuse their own amendment/retirement — the tier protects itself), and
  `CONST-SYSTEM-FUNCTION` (ruled 2026-07-17; the corpus's boot step 11 restored: no rule
  may destroy the system's capacity to boot from its record or to process rules at
  system level; space-local governance of rule-writing is not this — the untouchables,
  design/30 §3). This is the §0
  cure applied to the apex actor: an owner above the law makes gov-os "Linux with root
  renamed owner." The guarantee is cannot-do-lawfully and cannot-do-quietly, NOT
  cannot-do-on-disk — hand-editing the record file is out of system scope, made
  detectable by the audit mirror now and cryptographic signing later (§7). Enforcement
  ships in EP-05 Phase A (self-protection, core-owner-retirement, audit floor);
  `CONST-AUTHORITY-ANCHORED` and `CONST-SECRETS` are recorded as standing law now and
  enforced when accounts/succession and the secrets vault exist (law may precede its
  machinery — the gateless-intake principle). Three extensions ruled 2026-07-16
  (derivation: `29-TIER-CONSERVATION.md`): **(1) founding-only minting confirmed** —
  constitutional law enters only at genesis, mimicking natural legitimacy; the owner's
  lawful relationship to it is live-under-it or exit, never override. **(2) Tier
  conservation** — the shield never drops: protected definitions amend only by atomic
  in-place supersession (AMEND-OP) with tier carried across; bare retirement, elevation,
  demotion, and any protection gap are refused and recorded (EP-05C). **(3) Vocabulary
  authority is scoped, not privileged** — packs are rewritable within an actor's space or
  power reach and readable only under sight (`PACK-SCOPE`, recorded now, machinery lands
  with accounts/spaces).

> **Amendment (documentation-currency, EP-MAINT-C4-FINDINGS F2 — records code state, no design change).** 2026-09-08: real cryptographic signing is the KEY-MATERIAL-REAL unit (in progress); the live shape is modelled — see gate.py:171.

## 2. The stores

- **Event store** (definitive): as built — seq/record_time minted at append, fsync'd,
  frozen DEEP (payload interiors immutable in memory — EP-02). H1/H2/H3 hold.
- **Blob store** (definitive): content bytes by hash, write-once. Unchanged.
- **Item surface** [RULED — owner, 2026-07-24, pre-campaign-2 ruling sheet D4: "view"]:
  identity/kind/version of things is the derived master item view over creation events
  + blobs, not a third store. The working assumption is CONFIRMED as built; nothing
  changes.

## 3. Record-kind catalogue (end state; all in the ONE stream, class-tagged)

| payload.kind | Class | Appended by | Cites | Content |
|---|---|---|---|---|
| root_rule | LAW | genesis | BOOT-INT | rule_id, polarity, text, and (post EP-06) when/then full form |
| rule (subsystem law) | LAW | AMEND-* ops | its amendment law | rule_id, policy_key, value, exclusive |
| op_definition | LAW | CREATE-OP | CAP-IS-LAW | name, params, checks[], law_cited, decision shape |
| view_definition | LAW | CREATE-VIEW | ROOT-NEG-6 | name, when (trigger ± not), then (move_to), text |
| category_pack | LAW | genesis / amendment | BOOT-INT / amendment law | name, levels[] — all changeable vocabularies incl. the dual-audit action list (EP-02) and the syscall map (EP-02) |
| obligation | LAW | CREATE-OBLIGATION | its law | a temporal do: when (condition incl. elapsed record-time) → then (op invocation); EP-07 |
| verdict | DECISION | COMPARE | comparison law | (a, b, frame, verdict, basis) — frame-carrying, never merged; EP-11 |
| grant / revoke | DECISION | GRANT-READ etc. | SIGHT-IS-LAW | grantee, target — evidence the live permission check walks |
| tick / arrival | INPUT | the clock/watcher source | tick policy / OBS-1 | external happenings; the due() feed |
| decision (per-op) | DECISION | the interpreter | the op's law_cited | as defined by the op_definition |

## 4. The full rule form (end state of every law)

```
{ rule_id, polarity, text,                      # the sentence stays, for humans
  when: [ {pattern…}, {pattern…, not: true} ],  # trigger chain; − = did-not-happen
  then: [ {step…}, {step…, refrain: true} ] }   # outcome sequence; − = do-not-do
```
A trigger pattern tests the closed dimensions (action / actor / object / rule_cited /
refused / payload_kind, per-link negation). An outcome step is one of: append a named
decision (via a defined op), refuse citing a rule, halt a scope, or move info to an
entity (the view primitive). Root laws upgraded to this form in EP-06; where a law's
outcome is structural (e.g. "no authority check → no state change"), the outcome is the
REFUSAL itself, wired explicitly — a law whose outcome cannot be named is a detected
toothless-must, not a silent hole.

## 5. The check vocabulary (the interpreter's complete knowledge; each check = one EP)

| Check | Semantics | Refuses citing | Delivered |
|---|---|---|---|
| require_prior | a record with action=A, payload.F == param must exist | given rule (default ROOT-NEG-1) | BUILT |
| sight | actor was granted read of the target param | SIGHT-IS-LAW | BUILT |
| ceiling | policy_value(key) vs an aggregate (sum of F over action A minus removals via action B, keyed by param) + requested amount | given rule (e.g. MEM-LAW-BUDGET) | EP-04 |
| consistency | proposed rule vs active law, same scope, exclusive conflict | ROOT-NEG-6 | EP-05 (extracted from CREATE-RULE) |
| sop | actor ≠ creator of the object param (maker may not review own object) | SOP | EP-09 |
| due | the obligation's temporal/eventual condition is met (read-only feed for the executor) | — (a feed, not a refusal) | EP-07 |
| entry_ref | the referenced param names an EXISTING dictionary entry (integrity at use — a future sequence position names nothing, so it can never be recorded and can never suppress the entry that later lands there) | DICT-LAW | EP-13B |
| space_tree | the space named as parent exists, and the proposed parent link creates no cycle (nesting is containment; a space naming its own descendant refuses) | BOOT-INT (cycle) / CAP-IS-LAW (unfounded parent) | EP-16 |
| attenuation | [RETIRED 2026-07-25, EP-19 rider R-C: the containment leash lives at the gate chokepoint for every grant-kind record — one law, one home; this check kind had zero citing ops after the move] a non-root actor's created grant is contained WHOLE within at least one covering grant its maker holds | ROOT-NEG-3 | EP-16 → retired EP-19 |
| fingerprint | recompute the declared input-view asOf now and compare its canonical hash to the hash recorded at hand-out; on mismatch refuse citing the staleness rule. Staleness and authority stay two verdicts (design/34 §2): a stale return refuses on staleness even when every act would be lawful, and a revoked chain refuses on authority with the fingerprint passing. The seal is over STATE, not history, so the fold's own derivation decoration is excluded before hashing (design/34 §3; the ABA case turns on it) | staleness rule (founding, EP-23) | EP-23 |
| definition_ref | the referenced param names an EXISTING definition record — reference integrity at use; a dangling ref refuses at the moment of use [GRANDFATHERED: delivered at EP-12 (log `:222`), predating this table's gate law; the doc row landed 2026-08-08 and its "refuses citing" cell landed UNTRACED, completed 2026-08-08 by EP-28V W1 from the check site] | the rule the check declaration names in `cite`, and where it names none, TWO defaults for TWO refusals — ROOT-NEG-1 when the term itself does not resolve to an undisputed dictionary entry (`src/kernel/opdefs.py:1446`) and CAP-IS-LAW when the entry resolves but its `definition_ref` dangles (`:1450`). Traced at the check site 2026-08-08 (EP-28V W1): the founding's only citing definition, USE-TERM, declares no `cite`, so both defaults are what fires today | EP-12 |
| binding | the name↔identity binding state the op declares it requires: `binding:unbound` (the name must be free — the create class) or `binding:bound` (the name must resolve — the remove/rename/link class), with container-scoped variants (`@container`) | FS-LAW-NAMESPACE, errno keyed by the ACT per the two-key law (`ERRNO_BY_ACT`) | EP-28K [GATED — owner-approved 2026-08-08 by explicit act; the Aug-4 ruling did not open the gate. History: the row landed hours earlier marked existence-not-decision, and the gate closed the same day by the owner's word — see the GATE STATUS brackets above] |
| kind | the bound subject's kind requirement: `kind:require:dir` / `kind:forbid:dir` — directory-ness demanded or forbidden for the declared act | FS-LAW-NAMESPACE, errno by act (ENOTDIR / EISDIR) | EP-28K/N [GATED — same act, 2026-08-08] |
| contains | container emptiness required — `contains:empty` for removal or replacement of a directory | FS-LAW-NAMESPACE, errno by act (ENOTEMPTY) | EP-28N [GATED — same act, 2026-08-08] |
| prior_value | the named field INSIDE a cited prior record either HOLDS A VALUE or is DECLARED to hold none: `prior_value:established` / `prior_value:unestablished`. The record is located ONCE by `action` + `field` + `param` (latest seq wins, because a declaration amended later is the one in force) and the field is read OUT OF THAT RECORD by a dotted `value_field` path over mappings. The first kind whose subject is inside a record rather than the record's existence, its actor, an aggregate, or a key's state — and the locate and the read meeting the SAME record is its whole addition, which two `require_prior` rows cannot do because each is an independent existence scan. The value comes from the LAW-DATA and never from a parameter, so nothing the caller passes can move the answer, which is what makes it usable as a fail-closed licence test. THREE refusals and never two: no matching record; the path unresolved (a value this estate leaves UNESTABLISHED is DECLARED so and never omitted, so a silence is not an answer and a default filling it is the fail-open trap); the presence mismatching `require` | the rule the check declaration names in `cite`, with ROOT-NEG-1 the default at all three refusal sites where it names none. The founding's one citing operation names the TIP-LEVEL TERMINAL RULE (`P3-CLOSURE`) rather than the device law, because a licence that cannot compute is absence of permission and what no declaration permits the gate refuses citing that rule (EP-29 ADDENDUM 8 C7, ruled) | EP-29 W3a3 [GATED — owner-ruled 2026-08-14 by explicit act, on EP-29 W3a2's DRIVEN establishment: seventeen formulations spanning all twelve live kinds, minted through the ordinary door and called against the two shipped intake declarations, ZERO separating them, BOTH positive controls separating. The gate was answered BEFORE the kind was written, which is the first time in this table. THE LICENCE IS ONE KIND: no second kind rides it] |
| value_domain | the named param's value is inside an ALLOWED SET the check row declares in its own `domain` list — the GENERAL of which `kind` and `binding` are specials. ABSENT IS NOT IN THE DOMAIN, and the asymmetry is law rather than accident: a param the caller omitted carries `None`, `None` is not a declared value, and the act refuses; an op that wants an omission to be lawful declares a `param_defaults` entry, because a default is a statement the law makes where silence is not. THE DECLARED-SET CONDITION, which entered WITH the owner's act of 2026-08-20 and is not separable from it: the allowed set is DECLARED IN THE CHECK DECLARATION, founding-pinned, and moves only through the ordinary law door — NEVER a reference to mutable data, because a data edit must never silently move what the gate refuses. THE AUTHORING RULE, same act: where a general and its special both express a test, authors use the SPECIAL wherever a specific refusal contract exists — the special carries the errno mapping and the cited rule and the general cannot, so this kind DOES NOT REPLACE `kind` OR `binding` ANYWHERE | the rule the check declaration names in `cite`, with AR-2 the default where it names none (`src/kernel/opdefs.py`, `_value_domain_check`); the founding's one citing declaration, COMMS-OPEN's `role` row, names COMM-LAW-CONTRACT. A malformed declaration refuses at DEFINITION time citing AR-2: no `param`, or a `domain` absent, empty, or not a list (`_require_wellformed_value_domain`, all three doors) | EP-30-C1 delivered the kind, EP-30-C1R delivered this row [GATED — owner-approved 2026-08-20 by explicit act, his words "I yes both", the third answering of this gate and the most evidenced; the row lands with the delivering pass per this table's own direction-is-law discipline] |
| live_slot | the slot the act would take is NOT ALREADY OCCUPIED, and occupancy is COMPUTED at the moment of the act — every `open_action` record naming an instance, minus every `close_action` record that closed it, keyed by `slot_params` — never a stored flag. That is record-the-act-compute-the-view applied to the invariant itself, and it is why the kind counts LIVE openings AT A MOMENT and never openings across a lifetime. The GENERAL of which `binding`'s bound/unbound pair is the name-scoped special; THE AUTHORING RULE stated in the row above binds here identically, so this kind DOES NOT REPLACE `binding` ANYWHERE | the rule the check declaration names in `cite`, with AR-2 the default where it names none (`src/kernel/opdefs.py`, `_live_slot_check`); the founding's one citing declaration, COMMS-OPEN's two-channel row, names COMM-LAW-CONTRACT. A malformed declaration refuses at DEFINITION time citing AR-2: a missing `open_action`, `close_action` or `instance_param` leaves the live set uncomputable, and absent `slot_params` would put every act in one slot, admitting exactly one opening in the whole estate (`_require_wellformed_live_slot`) | EP-30-C1 delivered the kind, EP-30-C1R delivered this row [GATED — owner-approved 2026-08-20 by explicit act, same word, same gate] |
| bound_field | the prior record SELECTED BY A KEY PARAMETER has its declared field EQUAL to a second parameter — the record is BOUND first (located by `action` + key field + the key param's value, latest seq wins), then ONE declared field of THAT record is compared against the second parameter. THE ADDITION IS THE BINDING AND NOTHING ELSE: `require_prior` quantifies over records (THERE EXISTS one whose field equals my value — so a giver holding SOME handle satisfies it for a handle they do not hold) and cannot select; `prior_value` reads a field out of a located record but CANNOT BE TOLD A VALUE TO EXPECT — the value comes from law-data, never a parameter. Neither can express THE RECORD THIS PARAMETER NAMES HAS ITS FIELD EQUAL TO THAT PARAMETER, which is the entitlement question (the giver named in this act is the holder named in that record). CGL derivation per design/40: READ (bound — one selected record, the selection being the new capability) + COMPARE (its field against the second parameter); no new component, a new composition | the rule the check declaration names in `cite`; first user FILE-CUSTODY-TRANSFER citing FS-LAW-CUSTODY-TRANSFER (the giver-holds property); second scheduled user SHM-GRANT at EP-30-C4W (granter-holds) | EP-30-K1 [GATED — owner-approved 2026-08-22 by explicit act, his words verbatim "okay add the 16 make things moving", the FOURTH answering of this gate — AND THE FIRST ANSWERED AFTER ITS KIND HAD LANDED: the amendment shipped ungated (board :2003, the stop at the authoring seat's own hand), the estate's own instrument redded on the divergence (test_checkvocab, board :2008), and the gate was answered with the incident FULLY DISCLOSED — the owner's yes was given over the confessed breach, not over a smoothed record, and this bracket says so because the table's history is the gate's evidence] |

| every_member | EVERY member of a MANY-VALUED parameter satisfies a DECLARED INNER QUESTION — the quantifier, and it is AN AXIS OVER THE VOCABULARY, NEVER A FLAT SPECIAL: its declaration names an inner kind and that kind's own parameters, and the arm hands each member of the set to THE SAME ARMS the other sixteen use, naming ITS OWN CODE NO KIND — so a re-cut of the word list leaves it standing, which is the rebuildability rider BUILT AS DESIGN (the flat special was refused by the rider, not by taste). THE REFUSAL NAMES THE FAILING MEMBER — a refusal saying only "something in this set is wrong" answers two different worlds with one string. THE EMPTY-SET ANSWER IS DECLARED IN EVERY ROW, NEVER DEFAULTED: "every member of nothing passes" is vacuous truth, the fail-open trap dressed as logic, so a declaration missing its empty-set answer REFUSES AT DEFINITION TIME through the malformed-declaration door — value_domain's absent-is-not-in-the-domain law verbatim: a default is a statement the law makes where silence is not | the rule the check declaration names in `cite`; the inner declaration meets its own kind's wellformedness door too (`src/kernel/opdefs.py`, `_require_wellformed_every_member`, `_every_member_check`) | EP-30-K2 [GATED — owner-approved 2026-08-22 by explicit act, his words "go for now", THE FIFTH ANSWERING OF THIS GATE AND THE FIRST ANSWERED BEFORE A WORD OF ITS PLAN EXISTED — the front door used exactly as built, the :2003 lesson paid once and applied. THE APPROVAL IS CONDITIONAL and the condition binds the whole table: THE REBUILDABILITY RIDER (the bracket below) — the owner holds standing intent to re-cut this vocabulary from the four CGL components, and this kind was DESIGNED AS AN AXIS so the re-cut passes through it] |
| live_present | a KEYED MEMBER IS PRESENT in a LIVE SET the record derives — THE POLARITY COMPLEMENT OF `live_slot`: `live_slot` refuses a member that IS present past its slot (at most one live occupant), `live_present` refuses a member that is ABSENT from the live set. The live set is folded generically from the row's declared `open_action` / `close_action` and keyed by `key_params` — every opening minus every close that named it, computed AT THE MOMENT OF THE ACT, never a stored flag — the same fold a subsystem view (comms.py's `live_channels`) makes, computed inside the kind the way `_live_slots` computes `live_slot`'s, never by importing a subsystem, because a check kind is generic vocabulary available to any op. `present` names which key fields the CALL must match (a declared param, or `$actor` — the engine's fact, never the caller's claim) and which stay wildcard, so ONE kind asks channel-liveness (channel present, any holder), whose-close and sending authority ((actor, channel) present); `close_actor_key` sources a key field of the close from the record's ACTOR, which makes a close whose-keyed rather than name-keyed. THE REFUSAL NAMES THE SET AND THE MISSING MEMBER — one string for one world. Not derivable from the seventeen: no kind asked presence-in-a-derived-set at all, and `live_slot` answers occupancy, the inverse question | the rule the check declaration names in `cite`, AR-2 the default where it names none (`src/kernel/opdefs.py`, `_live_present_check`); the founding's citing declarations name COMM-LAW-QUEUE (channel live for a send or receive) and COMM-LAW-CONTRACT (the acting entity holds the channel it sends on or closes). A malformed declaration refuses at DEFINITION time citing AR-2, all three doors (`_require_wellformed_live_present`): no `open_action`/`close_action` and the set cannot be folded; no `key_params` and a member has no identity; no `present` and nothing names the required member; a `present` field outside `key_params`, a `present` source that is neither `$actor` nor a declared parameter (the op-amend param rule made a door check), or a `close_actor_key` outside `key_params` | EP-49C [GATED — owner-approved 2026-09-08 by explicit act, his words "go yes" (board :3354/:3355, on the architect's recommendation YES), THE SIXTH ANSWERING OF THIS GATE and the second answered BEFORE the delivering unit was authored — EP-49C was re-authored on the word and countersigned after it (:3362). The row lands at the architect's hand on the unit's raise #1 (:3431) with the delivering pass, per this table's direction-is-law discipline; CODE-BORN (the pack lists no check vocabulary, :3355), so the kind itself moves no pack version — the citing declarations do, one MINOR under :3069] |
| fold_threshold | a NAMED DERIVED COUNT COMPARED TO A THRESHOLD BY A NAMED OPERATOR — the count is `add_action` records minus `sub_action` records (the subtraction optional), scoped to the act by `key_param` against the records' `key_field`, named by `fold_name` so the refusal can say which fold it read; `queue_depth` (sends minus receives on a channel, above zero for a receive) is exactly this. THE OPERATOR IS A CLOSED SET declared at the engine (`>`, `>=`, `<`, `<=`, `==`, `!=`) and THE THRESHOLD IS AN INTEGER DECLARED IN THE ROW — founding-pinned, moved only through the ordinary law door, never read from mutable data (`value_domain`'s declared-set condition, at this kind, and for the same reason: a data edit must never silently move what the gate refuses). THE REFUSAL NAMES THE FOLD, THE VALUE AND THE THRESHOLD. Not derivable from the seventeen: `ceiling` compares an aggregate PLUS A REQUESTED AMOUNT against a POLICY VALUE read from law-data and never names an operator; no kind counted a fold against a declared threshold at all | the rule the check declaration names in `cite`, AR-2 the default where it names none (`src/kernel/opdefs.py`, `_fold_threshold_check`); the founding's one citing declaration, COMMS-RECV's `queue_depth` row, names COMM-LAW-QUEUE. A malformed declaration refuses at DEFINITION time citing AR-2, all three doors (`_require_wellformed_fold_threshold`): no `add_action` and nothing is counted; no `key_param`/`key_field`/`fold_name` and the fold is unscoped or unnamed; a `key_param` the operation does not declare; an `operator` outside the closed set or a non-integer `threshold` — a comparison that reads as a restriction and admits everything | EP-49C [GATED — same act, 2026-09-08, "go yes" (:3354/:3355); row landed with the delivering pass at the architect's hand (:3431); CODE-BORN, the citing declaration's pack move is the data half] |

Adding a check kind is an ENGINE amendment: design-doc change + owner gate, never a
quiet addition.

> **[THE REBUILDABILITY RIDER — owner condition, 2026-08-22, given with the
> fifth answering of this gate (the seventeenth kind, quantified membership)
> and binding the WHOLE TABLE: "go for now, but also on the condition that
> these 17 is something we can rebuild later cause I'm keen to rethink that"
> — his words, recorded at the architect's hand. THE CONDITION AS LAW: the
> check vocabulary is REBUILDABLE BY DESIGN. The owner holds standing intent
> to re-derive the word list from the four CGL components (design/40), and
> nothing may harden the menu against that re-cut: every kind keeps its
> derivation row current in design/40; check declarations reference kinds BY
> NAME and stay migratable; no unit may create a dependency that would turn
> a vocabulary re-derivation into a rewrite rather than an ordinary (if
> large) law pass through the founding door. A rebuild, when the owner calls
> it, is a law-era move: declarations re-cut, era rows red and re-pinned by
> the resolution machinery this arc has run four times, this table rebuilt
> with his word on each surviving row. COST NOTE, honest: the re-cut grows
> dearer with every op that declares checks, so the rethink is cheapest
> scheduled early — the natural window is at or after this campaign's
> close.]** An op definition naming an unknown check is refused at definition time.

> **[GATE STATUS, placed 2026-08-08 by the architect seat — the placement the
> ledger's own entry named as owed. THIS GATE IS LIVE, not silently open.** An
> owner ruling of 2026-08-04 sits at `DISPATCH-LEDGER.md:270` — by that entry's
> own words an INTERIM home — and a seat read it as discharging this gate
> ("answers wider than the gate asked"). **The mentor has ruled the gate NOT
> DISCHARGED:** that bridging clause is a seat's inference from adjacency, and
> this gate's whole content is "never a quiet addition" — a seat concluding
> "this was not really an addition" is that addition's exact shape. **The
> ratification question is with the owner. On his word: ratified → the ruling
> is written HERE in full, where this reader stands; declined → this gate
> stays LIVE and the ledger entry remains what it is on its face — an errno-law
> ruling that never touched this gate. Until then, no check kind is added on
> the strength of the ledger entry.]**

> **[THE GATE IS ANSWERED — OWNER-RULED 2026-08-08, his word given directly
> in the architect chat: THE THREE CHECK KINDS (`binding`, `kind`,
> `contains`) ARE APPROVED AS OF TODAY, BY EXPLICIT ACT. THE AUG-4 RULING
> DID NOT OPEN THIS GATE.** The bridging claim ("answers wider than the gate
> asked") is thereby REFUTED WITH A RULING rather than left as a seat's
> inference: adjacency is not authorization, a broad ruling does not
> pre-approve the implementation vocabulary it later needs, and
> implementation consequences return through their own gate — at the cost
> this instance measured: one sentence. The ledger entry at
> `DISPATCH-LEDGER.md:270` stays what it is on its face — an errno-law
> ruling; its §5-placement claim dissolves with the bridge, and ruling 1's
> permanent home is a SEPARATE placement at the refusal-recording doctrine,
> owed by the architect seat, flagged not silent. `definition_ref` stands
> grandfathered and needed no word.]**

> **[THE ENFORCER, ruled owed 2026-08-08 — a law requiring a document change,
> with no instrument checking the document, is a warning and not a mechanism
> (this estate's own sentence, arriving at its own vocabulary control; the
> drift it failed to catch: FOUR check kinds live in `OP_CHECKS` and absent
> from this table for days). EP-28V builds the comparator: `OP_CHECKS` and
> this table SET-DIFFED BOTH DIRECTIONS, red on divergence, with this table's
> own rows carrying legitimate-absence status in place (`due` is a feed;
> `attenuation` is retired) so the diff needs no side-list. DIRECTION IS LAW:
> this table is AUTHORED, never generated from the code — generating it would
> make every quiet addition self-documenting and lawful, which is the exact
> inversion the gate exists to prevent. The code is the subject; the table is
> the law; the comparator makes their divergence loud.]**

> **[THE GATE IS ANSWERED AGAIN — OWNER-RULED 2026-08-20 (UTC), his word given
> first-party in the architect chat: "I yes both." THE TWO CHECK KINDS
> `value_domain` (the value is inside an allowed set) AND `live_slot` (the
> slot is currently occupied) ARE APPROVED BY EXPLICIT ACT, discharging the
> :1564 gate — the third answering of this gate, and the most evidenced: the
> builder drove all thirteen existing kinds and recorded why each fails; both
> kinds derive from CGL (design/40 §5/§8 — the pack node and module_slot
> occupancy, existing CGL machinery); both are the generals of admitted
> specials (`kind`, `binding`). TWO RIDERS ENTER WITH THE WORDS, part of this
> act and not separable from it: (1) THE DECLARED-SET CONDITION —
> `value_domain`'s allowed set is DECLARED IN THE CHECK DECLARATION,
> founding-pinned, moved only through the ordinary law door, NEVER a
> reference to mutable data; a value_domain check referencing editable data
> is unlawful by this act's own words, because a data edit must never
> silently move what the gate refuses. (2) THE AUTHORING RULE — where a
> general and its special both express a test, authors use the SPECIAL
> wherever a specific refusal contract exists (the special carries the errno
> mapping and cited rule; the general cannot). The table rows for the two
> kinds land with the delivering law pass (the C1-resolution unit), per this
> table's own direction-is-law discipline; until delivery the kinds are
> APPROVED and UNBUILT, and the comparator's defect-4 reading of exactly
> these two names is the expected state, not a drift.
> CORRECTED 2026-08-20 (UTC), same day, at the mentor's :1605 raise, the
> wrong word standing above per the standing law: UNBUILT is FALSE OF THE
> ENGINE and was never checked at this hand — driven at the mentor's:
> OP_CHECKS imports at FIFTEEN kinds with both new words in it,
> well-formedness gates and evaluators for both sit on the declaration and
> dispatch paths, and COMMS-OPEN in the live pack carries three real checks
> where it carried the empty list. THE TRUE STATE: the kinds are BUILT IN
> THE ENGINE (the subject) and UNROWED IN THIS TABLE (the law); what lands
> with the delivering law pass is THE ROW, and defect 4's two hits read
> exactly that — "in OP_CHECKS, NO ROW in §5's table" — the enforcer
> reporting code-ahead-of-law, which is the very condition it was built to
> make loud. A builder reads: the engine you will meet is BUILT and
> EVALUATING; the absent thing is this table's two rows; finding the built
> engine is NOT an S-stop.]**

> **[THE TABLE HAS A ROOT — owner-directed 2026-08-20, authored the same day:
> `design/40-CHECK-VOCABULARY-DERIVED-FROM-CGL.md`. CGL is the definitive and
> these words are derivatives: each row's SEMANTICS decomposes into CGL
> primitives (the derivation map is design/40 §3; what does not derive is §4,
> kept visible). The boundary, stated there and binding here: CGL says what a
> word MEANS; this table says when the gate may REFUSE with it; the refusal
> layer (cited rules, errno law, fail-closed discipline) never derives. The
> gate below is UNCHANGED — a new word still enters only by the owner's
> explicit act — but it now arrives WITH its CGL decomposition attached, or
> with the finding that it has none (design/40 §6).]**

> **[THE GATE IS ANSWERED A SIXTH TIME — OWNER-RULED 2026-09-08, his word
> given first-party in the architect chat: "go yes", on the architect's
> recommendation YES (board :3354/:3355). THE TWO CHECK KINDS `live_present`
> (a keyed member is present in a derived live set) AND `fold_threshold` (a
> named derived count against a declared threshold) ARE APPROVED BY EXPLICIT
> ACT — the first growth of this vocabulary since design/40 was authored, and
> the first kinds whose need was NAMED BY A PAPER before a unit existed
> (design/51 §4: the comms laws' liveness, whose-close, non-empty receive and
> sending authority, which the seventeen question-kinds could not ask). THE
> WORD PRECEDED THE UNIT: EP-49C was re-authored on it and countersigned after
> it (:3362), so the :2003 shape — a kind landing ahead of its gate — did not
> recur. Both kinds are CODE-BORN (this estate's pack lists no check
> vocabulary; :3355), so the kinds themselves move no pack version; the
> declarations that cite them are the data half and moved the pack one MINOR
> under :3069. THE TWO RIDERS OF 2026-08-20 BIND HERE VERBATIM: the declared-set
> condition (a threshold or a key set is declared in the row, never a reference
> to mutable data) and the authoring rule (where a special carries a refusal
> contract, the special is used — `live_present` does not replace `binding`
> anywhere, `fold_threshold` does not replace `ceiling` anywhere). The
> rebuildability rider stands: both derivations are recorded in design/40 in
> this same act, both declarations name their kind BY NAME, and neither
> evaluator names another kind. The rows above landed at the architect's hand
> on the delivering unit's raise (:3431), with the delivering pass, per
> direction-is-law.]**
[Rows added 2026-07-24 (EP-13B W5, dispute integrity) and 2026-07-25 (EP-16 X1,
the authority ops as definition records — owner gate: the campaign-2 rulings; swept
by the mentor on each verdict). The same EP-16 amendment added `object_derive` — a
templated-object-id INTERPRETER capability, not a check kind; recorded here so the
interpreter's complete knowledge stays enumerable in one place.]

## 6. Views end state

- **Masters as records:** the five masters (relationship, rule/REQ, actor, resource,
  permission) plus the two registries (op_definitions, view list) are seeded at genesis
  as view-definition records and executed by the one engine. Engine functions remain
  only as the folds the definitions bind to (the S-plane).
- **System views:** derived from masters, never from the store; the fast per-actor and
  per-subsystem slices operations consult (I8).
- **The standing push (worker v1):** an on-append worker matches each new record
  against active view definitions with a `then.move_to`; matches are delivered into
  DERIVED per-channel queues (queues are views — killing them and replaying rebuilds
  them; delivery appends nothing). Governance-grade deliveries MAY be evented per a
  recorded materialization policy — a calibration with a named owner, never a default.
  Flood guard: workers run at append (governance rate), never per read.
- **Coverage + staleness:** every view answers coverage (derived from its definition)
  and carries derived_at metadata; a mandated view that has not run within its mandate
  is a detected paper tiger (EP-10 pairs this with metabolism).

## 7. Protection end state (the moat's separation half)

- **Two mutually blind audit streams:** two independent digest streams over
  governance-relevant acts (the action list = a category_pack, not code), neither
  readable by the other's writer, cross-checked by a third view. Divergence = alarm,
  routed to the owner. [Annotation, EP-09 review 2026-07-17: the load-bearing property
  is BLINDNESS OF COMPUTATION (neither stream ever digests the other), delivered in
  EP-09; physical separate-files is theatre on one disk written by one process and is
  deferred to the signing campaign, where key separation makes it real.]
- **SOP wired:** review/approve-class ops carry the `sop` check — the maker of an
  object cannot be the actor of its review. Enforced per-op, not aspirational.
- **The watched can brake the watchers:** any watched actor may invoke HALT-WATCHER
  (a governed op) freezing the watcher's ops pending owner resolution — recorded,
  rule-cited, and itself audit-mirrored.
- **Sight per consuming op:** every op whose definition names a readable target
  carries the `sight` check. CONSUME stops being the lone demonstrator.

## 8. Governance health (the metabolism half)

- **Metabolism gauge:** intake rate vs retirement rate of law records, windowed over
  record-time, per subsystem — the governance-debt dashboard as a view definition.
- **Paper-tiger view:** mandated views (a view req with a refresh mandate) that never
  ran. Same fold family as boot-integrity: a rule about the system × what the system did.
- **Toothless-must view:** laws claiming absolute force whose outcome step is empty —
  after EP-06 makes outcomes explicit, this is a pure derivation.

## 9. Comparison layer v1 (the compare-without-merging half)

A COMPARE op produces a verdict record: (a, b, frame, verdict, basis). Verdicts from
different frames NEVER contradict — both kept, no merger. Same-frame incompatibility is
a detected contradiction routed to the owner queue. This is the CGL federation ABI's
kernel seed: sovereign records comparing by carrying their frame. Scope v1: within one
record; cross-instance transport stays with S6 (out of scope).

## 10. What stays code forever (the S-plane), and its guard

The store, the gate's interpreter, the fold machinery, the live-check engines, the six
view-trigger dimensions, the check vocabulary, and the tier ladder
(constitutional/owner/ordinary — the LEVEL NAMES are engine surface; which records carry
which tier, and what each tier protects, is data in the record). Zero governance value; one
grep-verifiable write path. **T-NO-LAW-IN-CODE:** an automated test greps the engine
for rule texts, polarities, action-name lists, and vocabulary literals with governance
content; the only permitted hits are the labeled boot FALLBACKS and the two engine
vocabularies. A new hit fails the suite.

## 11. Acceptance battery additions (each EP names its tests; the battery-level names)

T-GATE-SOLE-APPENDER · T-DEEP-FREEZE · T-PACKS-CARRY-POLICY (dual-audit list + syscall
map as records) · T-CORE-MIGRATED (×5, per core: identical behavior on the existing
suite with ops as records) · T-CEILING-CHECK · T-RULES-FULL-FORM (root laws execute
their outcomes) · T-OBLIGATION-FIRES (an elapsed-time review fires from replay alone —
seam S3 acceptance) · T-WAIT-WAKE · T-MASTERS-AS-RECORDS · T-PUSH-DELIVERS (and:
kill queues, replay, identical) · T-DUAL-BLIND (streams diverge → alarm) · T-SOP-WIRED
· T-BRAKE-WATCHER · T-METABOLISM · T-PAPER-TIGER · T-VERDICT-FRAMES (cross-frame kept,
same-frame flagged) · T-TOTAL-ROUNDTRIP (I10).

## 12. Out of scope (the depth campaign, unchanged)

Full FUSE authority beyond the flat-namespace proof; the in-kernel VFS replacement and
the four subsystems behind it; the multi-writer sequencer (S5) and federation transport
(S6); GS-13 erasure implementation; module signing; the /proc byte-level port. Each has
its owner-gated entry in the roadmap (`planning/10-BUILD-ROADMAP.md`).

## 13. Honest caps

The push worker's cost under load is unmeasured (correctness specified; calibration is
an owner ruling from evidence). The ceiling check's semantics are the one fresh
derivation in the campaign (EP-04, xhigh). The comparison layer v1 is deliberately
minimal — the full CGL grammar stack stays in cgl-app until the kernel needs it. The
item-surface assumption (§2) was ruled CONFIRMED by the owner 2026-07-24 (a derived
view, not a third store) — no longer open.
