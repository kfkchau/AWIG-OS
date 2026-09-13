<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: design · Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature. NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=DESIGN status=DRAFT supersedes=- superseded-by=- verified=2026-08-22 -->

# design/41 — THE CHECK ARCHITECTURE RE-CUT: from a word list to a coordinate space

STATUS: LIVING DRAFT — owner-initiated 2026-08-22 ("rethink now then").
Evidence folds in as EP-31 (memory) and EP-32 (scheduling) run; the re-cut
EXECUTES at the campaign boundary as a law pass, per the rebuildability
rider (design/28 §5's bracket, the owner's condition of :2039).
OWNER PRE-APPROVAL 2026-08-26, his words: "The vocabulary rebuild - Yes"
(architect's chat, filed on the board the same turn): the boundary
execution is EXECUTE-ON-STANDING-WORD — the close docket no longer
raises it as a decision; each unit of the pass still meets the
countersign stack. This
document is the rethink's spine; the migration is a future unit's plan.
Sources read whole at the architect's hand 2026-08-22 on the owner's
direct word: all nine CGL grammar modules and SCOT core-ontology
(reference/corpus/, read-only). The owner's framing messages are the
definitive; where this document and his words diverge, his words win.

## 1 — THE COMPLAINT THIS ANSWERS, the owner's words

"I don't like the smell of a list that grows randomly without connection
of how the world in this space is constructed." Seventeen check kinds
exist; each is individually justified; the LIST has no architecture. The
week's own evidence: two additions (bound_field, every_member) arrived as
emergencies, and both turned out to be predictable cells of a structure
nobody had drawn.

## 2 — THE FRAME, from CGL and SCOT

Everything is an ACTIVITY: ACTOR–ACTION–OBJECT–TARGET (CGL act01). One
activity exists in three modal positions — act01's own type tags:
    REQ  the activity WANTED        = a rule
    EVT  the activity HAPPENED      = a record
    CAP  the activity POSSIBLE      = a capability, a VIEW over records
A check is SCOT Module 12 instantiated: compare the arriving activity
against REQ-space, reading EVT-space and CAP-space, output same/different
= go/no-go. The universal loop (owner's words): info in → find rules →
operate rules on input → output.

ROLES ARE FUNCTIONAL, NEVER TYPED (SCOT Module 1): entity-vs-resource is
a gradient of self-change capacity, and slot assignment follows what the
thing DOES IN THIS ACTIVITY — a py file spawning subprocesses is an actor
wearing a file's clothes; metadata about a live program is a resource.
The engine already half-knows this (establishment by record, roles per
act); the re-cut makes it law.

## 3 — THE COORDINATE SPACE

A check is an address, not a word:

    DIMENSION 1 — SLOT (act01): which part of the activity is questioned
        actor · action · object · target
        THE ACTION CELL IS THE RELATIONAL ARCHITECTURE — owner-ruled
        2026-08-22: permission is read off the ARCHITECTURE of the
        input, the THREE EDGES of the activity: actor↔object,
        actor↔target, AND object↔target. Not one crossing but the
        whole relational shell (CGL's ST and Venn2 layers are its
        native vocabulary). Existing words already occupy two edges —
        bound_field on actor↔object, sight on actor↔target — and the
        third edge (object↔target: does this thing belong in that
        place) is PRE-ADDRESSED, not yet worded.
    DIMENSION 2 — SOURCE (act01 types = the three fetchers, design/40):
        REQ-space (MATCH the declaration) · EVT-space (READ the record)
        · CAP-space (DERIVE the view)
        The judge is always COMPARE; the loop is always Module 12.
    OPERATOR A — SCOPE (CGL part01, composition): whole · component
        (surface/inside/wireframe/content held in reserve)
        A single-valued subject is component-scope; a collection asked
        entire is whole-scope.
    OPERATOR B — COMBINATION (CGL connection logic): the gate set
        AND · OR · XOR · NAND · NOR over 1/N members
        every_member = AND over N at whole-scope. The quantifier family
        was never a new axis: it is CGL's connection layer applied over
        a composition scope. Future variants (any_member = OR,
        exactly_one = XOR) are pre-addressed, not inventions.

NO POLARITY DIMENSION — owner-ruled 2026-08-22: the engine is
match-permission-only, fail-closed; what no rule states is refused.
Must/must-not vocabulary exists ONLY at the human-law interoperability
layer (twc), as translation, never in the engine. This is SCOT Module 8's
fully-structured end: the observation logic is built into the receiving
system; polarity is an artifact of unstructured law.

## 4 — THE SEVENTEEN AS ADDRESSES (first mapping, to be driven per word)

    value_domain   object × REQ · component        form inside declared set
    kind, binding  object × REQ/CAP · component    declared class; namespace state
    require_prior  object/target × EVT · component existence (unbound READ)
    prior_value    object × EVT · component        field state of located record
    bound_field    actor↔object × EVT · component  entitlement (bound READ)
    live_slot      target × CAP · component        occupancy computed now
    sight          actor↔target × CAP · component  permission-to-read view
    every_member   (any inner cell) × AND-over-N · whole-scope
    ...            full seventeen-row table is the migration unit's A-row,
                   driven against the arms, never asserted here

## 5 — THE DROPDOWN, the owner's request-format instinct

Op declarations ALREADY carry the slots (stamp_actor, object_param,
target_param). A request arrives activity-shaped, so the declaration
PRE-PICKS which cells apply: authoring a check becomes filling exposed
coordinates, not choosing from a list. The gate table (design/28 §5)
remains the owner-gated registry — of ADDRESSES now, with the owner's
word per address; the alarm (test_checkvocab) and the minimality gate
(driven differentials) carry over unchanged.

## 6 — VERIFICATION ORDER IS LAW — owner-ruled 2026-08-22

The gate evaluates in canonical order: ACTOR (identity) → ACTION AS
ARCHITECTURE (the full relational permission, yes/no over the three
edges) → ONLY THEN the CONTENT of object and target (form, state,
existence detail). The owner's words: the action needs to look at
architecture to see the full permission yes/no BEFORE diving into the
content of the object or target. STRUCTURE BEFORE CONTENT — which is
the composition schema's own surface-before-inside applied to
verification: the relational shell is checked whole before any
interior is opened. Consequences: every refusal names the OUTERMOST
failing layer (who, before whether, before what); no content is ever
read for an act whose relational envelope already fails — the gate
never inspects what it was never entitled to reach, which is both a
correctness property and the courtesy the architecture owes the data.

## 7 — WHAT THIS DOES NOT TOUCH

The record plane, replay, attribution, the founding door, the per-word
owner gate, the fail-closed default. The re-cut re-addresses the
QUESTION VOCABULARY only. Everything shipped keeps working through the
migration (era rows red and re-pin by the existing resolution machinery,
four runs of it this arc).

## 8 — THE REST OF THE CORPUS, ASSESSED IN — owner-asked 2026-08-22
("assess if anything else from scot or cgl needs to be brought in")

FOUR ADDITIONS, each derived, none decorative:

8.1 AT — THE ACTION TAGS ARE THE DROPDOWN'S TYPE SYSTEM. Every action
carries its MECE pair (Movement: MV/NM/NA × Transformation: TF/NF/NA).
The tags PREDICT which cells an act exposes: an MV act (send, transfer,
hand over) exposes the relational edges — holding, origin, destination;
a TF act (encrypt, convert) exposes the object's FORM cells; NM+NF
(hold, lock) exposes occupancy and exclusivity. Driven against the
estate's own history: FILE-CUSTODY-TRANSFER is MV/NF and the checks it
actually acquired are exactly the MV set (giver-holds, establishment,
identity-inherited). The dropdown stops being a vision and becomes a
lookup: tag the verb, read off the exposed cells.

8.2 MS + RS + TEMPORAL — THE MEASUREMENT FORECAST, pre-addressing E1/E2
before they arrive. TODAY NO KIND MEASURES ANYTHING — all seventeen are
identity, existence, membership, occupancy; even value_domain is set
membership, never magnitude. Memory (EP-31) brings quotas and sizes —
MS HEIGHT; scheduling (EP-32) brings time bounds — MS LENGTH, and
T-REALTIME-BOUND is already its named gate; distribution/spread is MS
WIDTH, already met as quantity. So the space gains ONE pre-addressed
operator: MEASURE — compare a quantity of the bound subject against a
declared bound — with L/W/H as its three axes. RS's consumability tags
say WHICH objects deplete (a CONSUMABLE grant decrements a quantity, a
NON-CONSUMABLE one persists — quota checks are MEASURE over CO-tagged
subjects). The connection layer's temporal tags (FS/SS/FF/SF)
pre-address SEQUENCE checks — require_prior is a degenerate
finish-to-start, and scheduling will want the rest. NOTHING IS MINTED
HERE; the forecast exists so EP-31/32's demands arrive as addresses,
not emergencies — the bound_field lesson applied forward.

8.3 VENN2 v2 — THE THIRD EDGE'S NATIVE VOCABULARY. When the
object↔target edge is worded ("does this thing belong in that place"),
its relations are the five (UR/AD/IN/NS/EM) under the v2 parametric
containment spec (05_Venn2.../01_venn2_formal_spec_v2.md). Named as
source; nothing built.

8.4 EF — THE ENGINE'S PLACEMENT, one boundary line. The gate occupies
exactly ONE cell of the enforcement schema BY DESIGN: systemic source,
deterrent mechanism, absolute strength, blanket scope. Every other EF
cell — incentives, discretion, graded strengths, escalation chains —
belongs to the human-law interoperability layer, WITH polarity, as the
same ruling already placed it. The engine stays one cell; the interop
layer translates outward.

DELIBERATELY NOT BROUGHT IN: SCOT Modules 13-15 (meta-rules are already
embodied — checks are declared through the founding door under an owner
gate; difference-enablement governs the ESTATE's multi-seat design, not
the check space); Modules 6/9 (about observers, not checks). HONEST
CAP: OGS and OMGS (corpus dirs 02/03) are the governance-stack layer
above the engine and were surveyed, not read whole; if anything there
bears on the check space it would arrive via their activity model, and
that pass is flagged for the migration unit's authoring, not owed now.

## 8b — OPEN QUESTIONS / EVIDENCE PENDING

    Q1  RULED 2026-08-22 — action = relational architecture, three edges
    Q2  RULED 2026-08-22 — order is law: identity → architecture → content
    E1  memory's demands on the space (folds in at EP-31)
    E2  scheduling's demands (folds in at EP-32)
    E3  the seventeen-row address table, driven per arm (migration unit)
