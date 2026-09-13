<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture (seL4/POSIX/OS-textbook) · Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature (kernel, syscall, capability, permission, memory protection). NON-GOAL: no offensive capability of any kind; defines record, gate, view, and kernel-conformance only. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=CANON status=LIVE supersedes=- superseded-by=- verified=2026-07-24 -->
# GOV-OS — The Fundamental Rules (the recorded constitution)

**Status:** v1, 2026-07-15. The rules layer that animates the base view tree
(`25-VIEW-TREE.md`) — what must be recorded at genesis, and how operations and
views become governed data instead of engine code. Grounded in the running
proving example (`apps/cgl-app`: `core/store.js` boot(), `core/views.js`
viewDefinitions/executeView/coverageStatement, `scripts/seed-function-library.js`)
and the corpus boot sequence (`venn2-foundational` §09). Labels per
`00-READ-FIRST.md` §6.

## 0. The principle

Law never lives in engine code; code never carries governance value (P5). The
engine is one generic interpreter; every behavior it exhibits beyond
interpretation entered the record as a governed act. cgl-app proves this shape
runs: its constitution is the first records in its store, its functions are
`definition` events executed by one matcher, its custom views are records the
engine loads. gov-os lowers the same shape to the kernel.

## 1. The genesis pack (what PC_RUNTIME records before handing off)

Order matters; each mint may only reference what already exists (referential
integrity from the first record).

1. **Founding designation** — the owner chain-end. All authority chains
   terminate here (chainDepth 0).
2. **SYSTEM actor** — the sole governed-state writer after boot.
3. **owner actor + owner tunnel** — the registered instruction path
   (CREATE-TUNNEL: sender owner, target SYSTEM, permitted: instruction
   information). OWNER/ADMIN never mutates directly; SYSTEM records.
4. **The mother space** — the root info space; every later space nests under it
   (the space tree's genesis).
5. **The root rules, with polarity** — dos ('+') and don'ts ('−') as records
   carrying plain text (§2). Law as data from the first breath.
6. **Category packs** — actor classes (S / S+U / U), geometry (five codes),
   strength levels, zone qualifiers: changeable vocabularies, never enums in
   code.
7. **Bootstrap op definitions** — the twelve constructors as definition records
   (§3), the seed of ops-as-data.
8. **Base view definitions** — the tree's master views as view-definition
   records (§4), executed by the one engine.

Genesis is idempotent: seeding checks the record, never re-seeds.

## 2. The root rules (SOURCE-DERIVED: venn2-foundational §09 + doc 12 §0; polarity per the deontic ruling 2026-07-15)

Don'ts ('−') — must-not-happen; the gate's overrides; default-deny is these:

- `ROOT-NEG-1` — no valid authorising rule chain → no state-changing activity.
- `ROOT-NEG-3` — sender not authorised for this operation → no governed write.
- `ROOT-NEG-4` — no authority check performed → no state-changing activity.
- `ROOT-NEG-5` — no event record producible → no valid state-changing activity.
- `ROOT-NEG-6` — no contradiction check → no activation of a new/changed rule.
- `BOOT-INT` — no change that destroys a boot condition (the eight minimum
  conditions of venn2-foundational §08).
- `P3-CLOSURE` — an unregistered operation does not exist → Closure Hit,
  recorded.
- `SIGHT-IS-LAW` — no acting on what the actor could not lawfully read.
- `CAP-IS-LAW` — no capability without a recorded amendment with named
  authority.
- `SOP` — no maker reviews or acts on its own object.

Dos ('+') — must-happen; condition hits, the system makes it happen:

- `P4-REFUSE` — a failed gate refuses and cites its rule; never improvises.
- `SYS-RECORD` — SYSTEM may record any activity as evidence (recording is not
  permission to perform).
- `OWNER-TUNNEL` — owner may send instruction information to SYSTEM through
  the owner tunnel; SYSTEM reads and follows valid owner messages.

"May" appears nowhere as a stored class: the may-space is computed by the live
permission check (25-view-tree.json live_checks) — grants enter as recorded
acts that create the chain un-matching `ROOT-NEG-1`; the permission list is
derived, never authored (B05; cgl-app permissionList).

## 3. Operations as definition records (the ops-as-data migration)

**Now (built):** handlers are Python closures registered at boot; the registry
is enumerable (P3 holds) but adding an op is a code edit.

**Target (this layer):** an operation is a definition record —
`{op_key, params (name/type/required), law_cited, decision_shape,
refusal_conditions}` — appended by a `CREATE-RULE`-class amendment with named
authority. The gate becomes one generic interpreter: validate params per the
definition, run the refusal conditions (live checks against dos/don'ts +
chains), append the decision shape. Registering an op = a recorded amendment;
retiring one = a recorded retirement; the action view (tree 2.1) derives the
registry from these records. Closure Hit is unchanged: no definition record →
the op does not exist.

**What stays code, honestly:** the interpreter, the store, the live-check
engines — the S-plane, zero governance value, one grep-verifiable write path.
Predicates inside definitions start as a closed vocabulary the interpreter
knows (budget-ceiling, capability-exists, sight-check...), per the
adopted-definitives principle [B09]; a predicate AST (cgl-app matchPattern
class) is the growth path, not the v1 requirement.

**Migration order:** new ops enter as definitions first; the five cores'
existing handlers migrate one core at a time behind unchanged tests (the
hollow-out pattern applied to the kernel's own surface).

## 4. Views as definition records (the view-req mechanics)

Per canonical-03 (view definitions are REQ-form records) and the running
example (cgl-app viewDefinitions/executeView/coverageStatement/createDerived):

- A view definition is a record: name, input scope (filters over
  form/action/actor/space/frame), derivation rule, output spec, materialization
  policy (ephemeral | governance-grade), refresh mandate.
- One engine loads and executes definitions; it never hardcodes an arrangement.
- The **coverage statement is derived from the definition** — every view
  confesses what it chose not to look at, mechanically.
- Caches are generation-keyed on the store version with visible `derived_at`
  staleness (the sanctioned cache-of-a-live-computation; the worker tree [B04]
  plugs in here later).
- The base tree's masters ship as seeded view definitions at genesis (§1.8);
  hot working-set products (runnable, maps, paths) stay ephemeral folds outside
  governance machinery (doc 17).

## 5. The item-store reconciliation [PROPOSED — owner ruling wanted]

The scan surfaced one structural tension: the tree holds an item store as a
second definitive; cgl-app derives items as a view over creation events (ids
minted from the creating record, versions by replay). Proposed dissolution:
the second **definitive** is only the content blob store (bytes by hash —
irreducible, already built); the item **surface** (identity, kind, version)
is the master item view derived from creation events. Tree node 2 stands as
the surface; the minimality gate is satisfied; the proving example is matched.
Cost if wrong: if item lookup by view proves too slow at kernel rate, the item
view materializes harder — a cache decision, never a schema change.

## 6. Acceptance (named before code, per 19-)

- `T-CONSTITUTION-RECORDED` — a fresh kernel's record contains the founding
  designation, SYSTEM, owner+tunnel, mother space, and every §2 rule with
  polarity and text; a root-rules view derives them back.
- `T-GENESIS-IDEMPOTENT` — build / reload / explicit genesis never double-seed.
- `T-OP-AMENDMENT` — an op added as a definition record executes through the
  generic interpreter; an op retired by record refuses with Closure Hit.
- `T-VIEW-DEF-EXECUTES` — a view definition record executes; its coverage
  statement derives from the definition alone.
- `T-NO-LAW-IN-CODE` — grep-level: no rule text, no polarity, no vocabulary
  enum carries governance content in engine code (boot fallbacks excepted,
  labeled).

## 7. Build order

1. Genesis upgrade: record the full constitution (§1 items 1–6) + root-rules
   view. Smallest slice, no behavior change to existing ops.
2. View definitions: the record shape + executeView + coverage (§4), custom
   views first, masters seeded as definitions after.
3. Ops as definitions: interpreter + closed predicate vocabulary, one new op
   end-to-end, then core-by-core migration (§3).

Each step lands with its own tests, green before the next (ST-B).

## 8. Fail-closed derives per subsystem (2026-08-13, ruled at the :698 raise; placed HERE because the failure mode is a reading order)

**FAIL-CLOSED IS A RELATION TO THE LAW'S OBJECT, NOT A DIRECTION.**
Each subsystem fails toward the state that preserves what its own law
protects — and the direction INVERTS across subsystems. Files fail
closed by recording MORE: the protected object is completeness of
record, so on doubt, keep everything. Devices fail closed by REFUSING
at the coarser grade and never by recording more: the protected
object is I9 — recording scales with governance, never with traffic —
so per-interrupt recording IS the failure, not the safety.

A subsystem declaring its granularity DERIVES its direction from its
own law's object. Inheriting a direction from the nearest existing
law text is the wrong-reference class at the design layer: the
file-system sentence is the older and more-read one, and it points
the wrong way for any subsystem whose hazard is volume. Ruled when
the second subsystem's law inverted the first's and nothing outside
the device law's own text said so.
