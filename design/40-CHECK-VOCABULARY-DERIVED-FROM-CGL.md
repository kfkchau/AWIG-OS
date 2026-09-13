<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture (seL4/POSIX/OS-textbook) · Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature. NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=CANON status=LIVE supersedes=- superseded-by=- verified=2026-08-20 -->
# GOV-OS — design 40: THE CHECK VOCABULARY AS A DERIVED SURFACE OF CGL

**Provenance: the owner's direction, spoken 2026-08-20 in the architect's chat —
"I want to use cgl lang to do a definitive check and do a derivative connections
so 13 vocab is derived" — restated by the architect, confirmed by the owner, and
authored the same day under his word. The derivation map and the honest caps are
the architect's. STATUS: definitive-layer documentation. It changes NO engine
byte and moves NO founding law; what it changes is what the check vocabulary IS —
an enumerated list becomes a derived surface, and every future vocabulary
question inherits a basis.**

---

## 1 — The question this answers

The gate can refuse an act only in words it knows. Those words — thirteen today,
tabled at `design/28` §5 — were minted one at a time, each through the owner's
explicit gate, each born from the EP that needed it. The list is governed, dated,
and enforced by a comparator. **What it never had is a root.** "Why these
thirteen?" had only a historical answer (these are the ones work needed), and a
new word's yes/no had only the owner's judgement to stand on. This document gives
the vocabulary its root: **CGL is the definitive; the check words are
derivatives; a check word is a CGL definition the kernel happens to enforce.**

## 2 — The definitive relation

CGL's meaning layer (cgl-app: `ARCHITECTURE_MEANING_LAYER.md`,
`DICTIONARY_GUIDE.md`, `DECOMPOSITION_METHOD.md`) holds the primitives of
governed meaning: **event patterns** (AAOT templates with variables and
quantifiers) · **packs** (owner-editable enumerations) · **derived views**
(derive-don't-store, latest-undisputed-wins, conflicts retained) · **the tag
layer** (what kind of thing a term is) · **reference traversal** · **dependency
types with deadlines** · **frames and same-frame conflict**. Its blackbox
principle: a vague load-bearing term is unopened reasoning packed into one word,
and the cure is minting a *definition* — a pattern over events with typed slots.

**Every check word is exactly such a blackbox term, and its semantics is already
a pattern over records.** The kernel evaluates these patterns at the gate; CGL
names what they mean. The relation, stated once: **CGL says what a word MEANS;
design/28 §5 says when the gate may REFUSE with it; the engine merely evaluates.
Meaning derives from CGL. Refusal law (which rule is cited, which errno, fail-
closed discipline) is gov-os law layered ON the meaning — it does not derive
from CGL and is not claimed to.**

## 3 — The derivation map (the thirteen, each opened)

Six CGL primitive families cover the vocabulary. Per word: its CGL decomposition,
in CGL's own terms.

**Family 1 — EXISTENCE OF A PATTERN** (a quantified event pattern matches the
record as-of now):

1. **`require_prior`** — ∃ an event with action=A and payload.F=param. The
   simplest CGL definition possible: one existence quantifier over one AAOT
   pattern.
2. **`entry_ref`** — ∃ a live `dictionary_entry` the param names. The most
   CGL-native word in the kernel: its subject IS CGL's own dictionary store
   shape.
3. **`definition_ref`** — the same pattern over `definition` records.
   **FINDING (minimality):** `entry_ref` and `definition_ref` are ONE CGL
   derivation with two populations. Two kernel words, one meaning.
4. **`space_tree`** (first half) — ∃ the named parent space.

**Family 2 — LOCATE-AND-READ** (latest matching event, then read inside it):

5. **`prior_value`** — locate the latest event by (action, field, param) —
   CGL's latest-undisputed-wins — then read a dotted path out of THAT event's
   payload. The declared-none case (`unestablished` stated, never omitted) is
   CGL's closed-box honesty: absence is asserted, never defaulted. The
   three-refusal fail-closed discipline is gov-os refusal law on top (§2's
   boundary).

**Family 3 — DERIVED-VIEW STATE** (a predicate over a view computed from
events):

6. **`sight`** — membership in the derived permission list (grants minus
   revocations). cgl-app's `permissionList` is the cited proving example of
   exactly this shape (`design/27`): derived, never authored.
7. **`binding`** — the name→identity binding view, container-scoped:
   `unbound` = no live binding holds the name, `bound` = one does.
8. **`space_tree`** (second half) — acyclicity of the containment graph, a
   predicate over reference traversal.

**Family 4 — AGGREGATE VERSUS DATUM** (a fold over events compared to a
recorded value):

9. **`ceiling`** — sum of F over action A minus removals via action B, keyed by
   param, plus the requested amount, compared to `policy_value(key)`. An
   aggregate view against a recorded policy datum.
10. **`contains`** — the containment count view at zero (`contains:empty`). An
    aggregate predicate with the datum fixed at 0.

**Family 5 — TAG / DOMAIN MEMBERSHIP** (a value against an enumerated set):

11. **`kind`** — the bound subject's kind-tag required in, or forbidden from,
    {dir}. CGL's tag layer ("what kind of thing is this") with require/forbid
    polarity over a one-member set.

**Family 6 — RELATIONAL AND TEMPORAL CONSTRAINTS:**

12. **`sop`** — two patterns joined on the object (its creation event, the
    acting event) with an inequality on the actor slot: maker ≠ reviewer.
13. **`consistency`** — same-frame incompatibility between a proposed rule and
    active law of the same scope. This IS CGL's conflict machinery — conflicts
    retained, same-frame incompatibility flagged, different frames never
    contradicting — evaluated at the gate instead of the owner queue.
14. **`due`** — the dependency layer verbatim: CGL's `dep_type`
    (FS/SS/FF/SF) with `gate` and `deadline`, read as a feed. The one word that
    answers instead of refusing, because it derives from CGL's dependency
    payload, which is a relation, not a prohibition.

*(Fourteen rows listed because `space_tree` decomposes into two families; the
kernel words number thirteen live, `attenuation` retired 2026-07-25 — its
containment-coverage meaning derives from reference traversal and moved to the
gate chokepoint, which is why retiring the WORD lost no MEANING.)*

## 4 — What does NOT derive, kept visible

- **`fingerprint`** derives at the meaning level ("the derived view now equals
  the derived view I was shown") — view equality across time is CGL — but its
  MECHANISM (canonical serialization, hashing, the seal-over-state-not-history
  exclusion of the fold's derivation decoration) is engine machinery with no
  CGL counterpart and no need of one. The word derives; its implementation is
  honestly S-plane.
- **The refusal layer never derives** (§2's boundary, restated as a cap): which
  rule a refusal cites, the two-key errno law, fail-closed three-way refusals —
  gov-os law, not CGL meaning. A reader deriving THOSE from CGL has
  over-derived.
- **No instrument checks this map yet.** The comparator (defect 4) checks code
  against the §5 table; nothing checks the §5 table against this derivation.
  The map is authored and read-verifiable; a mechanical check is a close
  question, not assumed.

## 5 — The two pending words, run through the definitive check first

The gate at board `:1564` asks yes/no on `value_domain` and `live_slot`. Under
this document's check, both derive — and both are GENERALS whose SPECIALS are
already in the vocabulary:

- **`value_domain`** ("the value is inside an allowed set") = Family 5, pack
  membership — CGL's packs are exactly owner-editable allowed-sets. **`kind` is
  `value_domain` specialised to the kind-tag and the set {dir}.**
- **`live_slot`** ("the slot is currently occupied") = Family 3, derived-view
  state — occupancy of a role-slot in a live set computed from open/close
  events. **`binding` is `live_slot` specialised to the namespace (name-slots,
  container-scoped).**

**So a YES does not admit alien words: it names two general shapes the
vocabulary already contains as specials.** Stated for the owner's decision, not
in place of it — the gate remains his explicit act, and adjacency to this
document is not authorization (design/28 §5's own ruling).

## 6 — The amended gate form (what every future word owes)

A new check word arrives at the owner's gate **with its CGL decomposition
attached** — which family, which primitives, which existing words are its
specials or generals — or with the finding that it does not decompose, which is
itself the most important fact a gate could receive. The decomposition is a
BASIS for the owner's word, never a substitute for it. The builder's
all-thirteen-checked discipline (each existing word tried and its failure
stated, the `:1564` form) stays required alongside.

## 7 — Honest caps

1. **Documentation-plane only.** No engine byte moves under this document.
   `T-NO-LAW-IN-CODE` and the S-plane ruling (`design/28` §10) stand untouched;
   the interpreter still executes a closed set of checks; the CGL grammar stack
   stays in cgl-app until the kernel needs it (`design/28` §13, unchanged).
2. **Direction of dependency:** this document READS cgl-app and cites it. It
   creates no code dependency, no import, no shared artifact. If cgl-app's
   meaning layer moves, this map can go stale — it carries dated readings, and
   its staleness is ordinary document staleness, not law breakage.
3. **The minimality findings (§3's entry_ref/definition_ref, §5's
   kind/binding-as-specials) are FINDINGS, not directives.** Nothing merges,
   retires, or renames any live word on this document's strength. If the close
   ever prices vocabulary consolidation, it starts from these findings and
   goes through the owner's gate like everything else.
4. **The map's verification is by reading** — both sides are documents. A
   mechanical map-checker is deliberately not commissioned here (the ADDITION
   GATE binds; the close may weigh it).

---

## 8 — The thirteen in FULL CGL (owner-directed 2026-08-20: "both the word and the gate questions need to be in full cgl lang")

**The legend, read from the app, not invented** (`core/store.js:11-27`,
`core/views.js:307-430` — the pattern node types the interpreter actually
evaluates): `aaot(A, Act, O, T)` — one event pattern over the four slots,
variables in CAPS bind by equality · `history(·)` — ∃past (the `history` node;
negate for absence) · `not(·)` · `all(·,·)` — AND with threaded bindings ·
`seq(·,·)` — ordered · `pack(x ∈ P)` — membership in a category pack (the
`pack` node) · `latest-undisputed(·)` — the dictionary fold's own locate
discipline · `view(·)` / `as-of(t)` — derive-don't-store over the store
contract's as-of reconstruction · venn2 geometry over slot pairs:
`UR/AD/IN/NS/EM` (nested/embedded are the containment states) · statement
modes from the pack: `occurred / required / prohibited / permitted`.

**THE GATE FORM, once for all thirteen:** every check word is a `rule_content`
sentence — `mode:required` over its pattern. The act is `permitted` where the
pattern holds and refused where it fails, the refusal citing the rule
design/28 §5 names (the refusal layer, which never derives — §2).

    require_prior(Act, x)
      ≔ history( aaot(A:_, Act:Act, O:x) )

    prior_value(Act, x, path, require)
      ≔ read-slot( latest-undisputed( history( aaot(Act:Act, O:x) ) ), path )
        — three refusals: no match · path unresolved (absence is DECLARED,
        never defaulted — the closed-box rule) · presence ≠ require

    sight(A, O)
      ≔ A ∈ view:permission-list(O)
        — expanded: history( aaot(Act:GRANT, O:O, T:A) )
          ∧ not( history-after( aaot(Act:REVOKE, O:O, T:A) ) )

    sop(A, O)
      ≔ not( history( aaot(A:A, Act:CREATE, O:O) ) )
        — the maker-inequality is one negated pattern: the acting actor must
        FAIL to bind the creation event's actor slot

    ceiling(key, req)
      ≔ measure: Σ view(F over Act:A) − Σ view(F over Act:B), keyed
        + req ≤ policy_value(key)
        — an aggregate VIEW against a recorded datum (cgl-grammar-measurement)

    consistency(r)
      ≔ ∃ active L: frame(L) = frame(r)
        ∧ geometry( scope(r), scope(L) ) ∈ {IN, NS, EM}
        ∧ polarity(r) = ¬polarity(L)   ⇒ same-frame conflict
        — venn2 verbatim: scopes intersecting or nested, polarities opposed,
        ONE frame. Different frames never contradict — CGL's own law

    due(X→Y)
      ≔ dep( type ∈ pack:dep-types {FS,SS,FF,SF}, gate, deadline ) met
        — CGL's dependency payload verbatim; a FEED (answers, never refuses)

    entry_ref(t)
      ≔ latest-undisputed( history( aaot(Act:ASSERT-ENTRY, O:t) ) ) exists
    definition_ref(d)
      ≔ latest-undisputed( history( aaot(Act:DEFINE, O:d) ) ) exists
        — ONE formulation, two populations (§3's minimality finding, now
        visible as one line differing in one literal)

    space_tree(s, p)
      ≔ history( aaot(Act:CREATE-SPACE, O:p) )
        ∧ not( NS-path( p ↝ s ) )
        — containment IS the O-T slot carrying geometry NS; the cycle check
        is acyclicity of the NS-graph under reference traversal

    binding(n @ c, state)
      ≔ slot-occupancy( name-slot n in container c )
        — occupied ≔ latest slot event is populate, not exclude;
        binding:unbound ≔ ¬occupied · binding:bound ≔ occupied
        — CGL's module_slot kind, applied to the namespace

    kind(x, require|forbid, dir)
      ≔ pack( class(x) ∈ {dir} )   with require/forbid polarity
        — the tag layer read through the pack node

    contains(c, empty)
      ≔ not( ∃ x: geometry(x, c) ∈ {NS, EM} in the live view )
        — emptiness is the absence of any live containment relation into c

    fingerprint(v, h)
      ≔ view(v, as-of:now) ≡ view(v, as-of:handout)
        — as-of reconstruction is store-contract line 2; the HASH that makes
        the comparison cheap is engine mechanism (§4, unchanged)

**The two pending words, in full CGL — and the §5 finding sharpens into a
fact about the interpreter itself:**

    value_domain(x, P)   ≔ pack( x ∈ P )
    live_slot(s)         ≔ slot-occupancy( s )

`value_domain` is not merely derivable — **it is the `pack` node the CGL
pattern interpreter already evaluates** (`views.js`, the `case 'pack'` arm).
`live_slot` is not merely derivable — **it is CGL's `module_slot` occupancy,
an existing payload kind** (the `role` definition's own note: "owner-slot
occupancy via APPOINT/HIRE"). A YES at the gate would give kernel names to
two constructs CGL already executes by machinery.

**Honest caps for this section:** the compact notation above maps 1:1 to the
store's pattern AST (`aaot`/`history`/`not`/`all`/`seq`/`pack` are the
interpreter's literal node names; `latest-undisputed`, views, and geometry
are fold-layer, which is where CGL itself evaluates aggregates). The kernel
does NOT execute these ASTs — the engine keeps its thirteen hardcoded checks
(§7 cap 1, unchanged); these formulations are the definitive's statement of
what each check MEANS, in the definitive's own grammar.

---

## 9 — The four components as ROOT-LANGUAGE definitions, and every word annotated by which component does the job (owner-directed 2026-08-20)

**The four, in CGL's own definition shape** (term · params · yields · closure):

    MATCH(pattern) → bool
      ∃past over an AAOT pattern; closed under ¬ and ∧ (the interpreter's
      history/not/all/seq nodes). Interrogates THE RECORD's existence facts.
    READ(locator, path) → value | UNESTABLISHED
      locate ONE record by latest-undisputed, read a dotted path INSIDE it.
      Distinct from MATCH because it returns a value from one located record,
      not a truth about existence — the property prior_value's addition
      turned on. Absence is DECLARED, never defaulted.
    DERIVE(view, as-of) → value | set | graph
      the fold layer: live sets, aggregates, permission lists, containment
      graphs — derive-don't-store over the store contract's as-of.
    COMPARE(x, op, datum|set) → bool
      op ∈ {=, ≤, ∈}; the datum or set is DECLARED IN LAW, never a mutable
      reference (the §5-condition, load-bearing here).

**The shell, stated once and NOT a component:** every word wraps its pipeline
in `mode:required`, refusing citing the design/28 §5 rule — the refusal layer,
which never derives (§2).

**Every word is a PIPELINE ENDING IN A BOOLEAN.** The component doing the
decisive work is tagged; the annotated vocabulary:

    require_prior    ≔ MATCH[ history(aaot(A:_, Act:Act, O:x)) ]
    sop              ≔ MATCH[ ¬history(aaot(A:A, Act:CREATE, O:O)) ]
    prior_value      ≔ READ[ latest-undisputed locate, path ] → COMPARE[ presence = require ]
    entry_ref        ≔ DERIVE[ dictionary view ] → COMPARE[ t resolves ]
    definition_ref   ≔ DERIVE[ definitions view ] → COMPARE[ d resolves ]
    sight            ≔ DERIVE[ permission-list(O) ] → COMPARE[ A ∈ · ]
    binding          ≔ DERIVE[ name-slot view @ c ] → COMPARE[ occupancy = state ]
    kind             ≔ DERIVE[ resolve subject ] → COMPARE[ class ∈ {dir}, polarity ]
    ceiling          ≔ DERIVE[ Σgrants − Σremovals, keyed ] → COMPARE[ +req ≤ policy_value ]
    contains         ≔ DERIVE[ live containment of c ] → COMPARE[ count = 0 ]
    space_tree       ≔ MATCH[ parent exists ] ∧ DERIVE[ NS-graph ] → COMPARE[ ∄ path p↝s ]
    consistency      ≔ DERIVE[ active law, one frame ] → COMPARE[ geometry ∈ {IN,NS,EM} ∧ polarity opposed ]
    fingerprint      ≔ DERIVE[ view(v) as-of now ] → COMPARE[ ≡ sealed handout value ]
    due (feed)       ≔ DERIVE[ dependency state ] with MATCH[ end-event ] inside — answers, never refuses
    ---- pending, the :1564 gate ----
    value_domain     ≔ COMPARE[ x ∈ P ]                       (pure — see the finding below)
    live_slot        ≔ DERIVE[ slot view ] → COMPARE[ occupied ]
    ---- retired ----
    attenuation      ≔ DERIVE[ coverage geometry ] → COMPARE[ NS whole ] — meaning moved to the gate chokepoint

**Three findings the annotation surfaces, and the first is the sharpest fact
yet about the pending gate:**

1. **`value_domain` is the vocabulary's first PURE COMPARE — and that is
   exactly why the thirteen could not express it.** Every existing word
   touches the record first (MATCH, READ, or DERIVE opens the pipeline);
   value_domain's subject is the CALLER'S OWN PARAMETER against declared
   law — no record interrogation at all. The thirteen are
   record-interrogators; this is the first act-interrogator. The builder's
   all-thirteen-failed finding is this structural fact wearing work clothes.
2. **The modal pipeline is DERIVE→COMPARE (nine of fourteen).** The
   vocabulary is overwhelmingly "compute the view, test the state" — the
   estate's record→view law expressed as a usage census.
3. **READ appears exactly once** (prior_value, the newest pre-pending word).
   As law-data grows richer, the basis predicts more READ-shaped words —
   the gate should expect them and this section is their template.

**Cap:** the annotation is the derivation map of §8 re-cut by component; the
two are one content at two granularities, and any future edit touches both or
neither.

**[§9 AMENDED 2026-08-21, on the owner's probe — "isn't match and compare the
same thing?" — and the probe re-cut the basis better than the section had it.
AT THE OPERATOR LAYER HE IS RIGHT: MATCH decomposes to ∃ + TEST — a search
quantifier over the record plus a fit-test, and the fit-test is comparison. So
the deep structure is ONE JUDGE, THREE FETCHERS: one relational core, TEST
(=, ≤, ∈, fits-form), does ALL the judging; the record reaches it by three
paths — search (MATCH's ∃), a targeted read inside one record (READ), or a
computed view (DERIVE) — and the act's own parameters arrive free, no fetch.
Every check word is fetchers feeding the judge once, inside the refusal shell.
This makes §9's finding 1 exact: value_domain is the word with ZERO fetchers.
THE OWNER'S ASYMMETRY INTUITION, kept with its refinement: match IS
asymmetric by level — an instance against a FORM one level up, a pattern
being a container of possible instances (his container/content law) — while
compare is level-flat; but compare is not only equality (≤ and ∈ are
compares). THE ONTOLOGICAL GROUND WAS ALREADY IN HIS OWN CORPUS: venn2
deliberately excludes equality from its five geometry states (guardrail 33.3,
store.js:16 — "identity belongs to a separate layer") — set-relations
between extensions and identity/value tests live in different layers, which
is this distinction ruled years before the question was asked. STANDING:
the OPERATIONAL cut stays four (it matches the engine, where matchPattern
fuses search and test); the ONTOLOGICAL cut is 1+3 (it matches the meaning,
and it is the owner's). One content, two granularities, edited together.]**

## 10 — The reading pin, and the two standing risks closed

**RISK 1 — THE MOVING CORPUS, closed BY CONTENT.** This document's claims
about CGL rest on a specific reading, now pinned the way this estate pins
everything that matters — by digest, with the commit as alias:

    cgl-app @ git f143384d (alias; the digests are the coordinates)
    core/store.js                    sha256 23a8e6d2… (boot vocabulary, slots,
                                     geometry, guardrail 33.3)
    core/views.js                    sha256 efc185c5… (the pattern node types,
                                     matchPattern, the folds)
    ARCHITECTURE_MEANING_LAYER.md    sha256 e68d3675… (the meaning-layer map)
    DICTIONARY_GUIDE.md              sha256 cf4210e1… (tag/function layers)
    data/dictionary/events.jsonl     SAMPLED for the definition SHAPE only
                                     (three events quoted §2/§8); its churn is
                                     live data and immaterial to the map

**What the pin makes impossible, and who absorbs it:** silent rot. If
cgl-app moves, the map does not become quietly wrong — it becomes CHECKABLY
STALE: recompute the digests, and a mismatch names exactly which surface
moved. The duty on mismatch: re-verify the map against the moved bytes and
file the delta as a dated amendment — never edit the map silently, never
ignore the mismatch. Absorbed by this document's author at each re-reading;
cost, four hash commands.

**RISK 2 — FRAME-SEDUCTION, closed BY LAW rather than by one seat's habit.**
The hazard: a future EP author grounds a REFUSAL row in this document's
meaning-language instead of design/28 §5's refusal law — meaning-speak in
refusal-land, mis-rooted at birth. The guard is now a shape-law bracket in
`planning/method/EP-SHAPE.md` (filed 2026-08-21, same act as this section):
A ROW THAT GROUNDS A REFUSAL CITES REFUSAL LAW — design/28 §5 or the rule
the check declaration names; a refusal row citing design/40 is MIS-ROOTED
and the countersign refuses it. design/40 is citable in plans for MEANING
(direction, derivation, vocabulary questions) — never as the ground of a
refusal. The mechanical half (a grep-shaped row for the reading-list
instrument: population = plan rows citing design/40, relation = is the
citation a refusal ground) rides the close beside the map-checker — one
instrument, two questions, per the ruled reading-list class. Until it lands,
the bracket binds at every countersign, which is where mis-rooting is
cheapest to catch and where this estate has caught everything else this week.

**[SIXTEENTH WORD — `bound_field`, derivation recorded 2026-08-22 in the
same act as the owner's gate word, so the four-explain-all property
stays VERIFIED rather than asserted. THE DERIVATION: READ (bound — the
fetcher aimed at ONE record, selected by a key parameter; the BINDING
is the entire novelty) + COMPARE (the judge over that record's declared
field against a second parameter). NO NEW COMPONENT. Its nearest
sibling `require_prior` is READ (unbound — any record) + COMPARE
(existence-equality); the difference is the READ's aim, not the
alphabet. The gate history: owner-approved 2026-08-22, the fourth
answering, design/28 §5's table carries the full bracket including the
disclosed ungated landing. The derivation map's population is now
SIXTEEN words over the same FOUR components, and this bracket is the
standing instruction that every future word lands its derivation row
HERE in the same act as its gate word — a vocabulary whose derivations
lag its words is design/40 rotting into a slogan.]**

**[SEVENTEENTH WORD — `every_member`, derivation recorded 2026-08-25 in
discharge of K2's A6(a) row; the gate word was the owner's "go for
now" at the fifth answering, given BEFORE authoring. THE DERIVATION:
this word adds NO COMPONENT AND NO CELL — it is an OPERATOR PAIR from
the grammar's own layers: COMPOSITION (part01) supplies the SCOPE
(the question asked at the WHOLE of a collection rather than at a
component), and CONNECTION LOGIC supplies the GATE (AND over N
members). every_member = AND-over-whole-scope, applied to ANY inner
cell — its arm hands each member to the same fetcher-and-judge arms
every other word compiles to, and names no word in its own code. THE
PRE-ADDRESSED SIBLINGS, stated so they arrive as coordinates and not
emergencies: any_member = OR, exactly_one = XOR — the connection
layer's remaining gates over the same scope. The four components stand
untouched at SEVENTEEN words; the axis is the first member of the
OPERATOR band this document's §9 cut anticipated, and the
rebuildability rider is why it exists in axis form at all.]**

**[EIGHTEENTH WORD — `live_present`, derivation recorded 2026-09-08 in the
same act as the design/28 §5 row, on the owner's gate word "go yes" of the
same day (board :3354/:3355, the sixth answering, given BEFORE the
delivering unit EP-49C was authored). THE DERIVATION: DERIVE[ live-set
view — every `open_action` record minus every `close_action` record that
named it, keyed by `key_params` ] → COMPARE[ the member the call names
by `present` IS IN the set ]. NO NEW COMPONENT, NO NEW CELL: it is
`live_slot`'s derivation with the judge's polarity inverted —
`live_slot` = DERIVE[ slot view ] → COMPARE[ occupied ], refusing
presence past a slot; `live_present` = DERIVE[ the same fold ] →
COMPARE[ present ], refusing absence. The one addition beyond the
inversion is where the compared member's identity comes from: a
declared parameter, or `$actor` (the engine's fact), so a single word
asks liveness, whose-close and authority by choosing which key fields
the call must match. Family 3 (derived-view membership), the family
`live_slot` and `binding` already sit in.]**

**[NINETEENTH WORD — `fold_threshold`, derivation recorded 2026-09-08 in
the same act, same gate word. THE DERIVATION: DERIVE[ a named count —
`add_action` records minus `sub_action` records, scoped by `key_param`
against `key_field` ] → COMPARE[ the count against a DECLARED integer
threshold by a DECLARED operator from the engine's closed set ]. NO NEW
COMPONENT: its nearest sibling `ceiling` is DERIVE[ aggregate ] +
READ[ policy value ] → COMPARE[ aggregate plus requested amount, at most
the policy value ]; the difference is that the threshold and the operator
are DECLARED IN THE ROW rather than read from law-data at the act, and
no requested amount enters — which is what makes it the fail-closed
non-empty guard (sends minus receives above zero before a receive) and
what `ceiling`, built to bound a budget, could not express. Family 2
(derived aggregate against a bound). The four components stand untouched
at NINETEEN words; both words entered WITH their derivations, as the
sixteenth word's bracket instructs.]**
