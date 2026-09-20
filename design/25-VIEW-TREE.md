<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture (seL4/POSIX/OS-textbook) · Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature (kernel, syscall, capability, permission, memory protection). NON-GOAL: no offensive capability of any kind; defines record, gate, view, and kernel-conformance only. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=CANON status=LIVE supersedes=- superseded-by=- verified=2026-09-10 -->
# GOV-OS — The Base View Tree (definitive → derived)

---

## VERSION 2 — 2026-09-10, owner-ruled at the architect's seat (board :3739; v2.1 the same day, levels 3 and 4 re-cut, board :3760; v2.2 the third view form, board :3817; v2.3 where its door is, board :3825; v2.4 where the stamp lives, board :3869; v2.5 AS-BUILT across C6a at the review, board :3906 — every clause of VERSION 2 is built as written, the one mechanical delta being ruling 13/15's row = the stamps inside provenance)

**Status:** v2 supersedes the v1 tree below wherever the two differ; v1 stays as
history. Machine form: `25-view-tree-v2.json` (v1's `25-view-tree.json` untouched).
The build that seeds this tree and the loop is design/53 (campaign C6a), running after
C6 closes, on the owner's word of 2026-09-10. Numbers are the tree's ids; they were chat-temporary
ids on 2026-09-09 and are fixed here.

### The purpose, in the owner's words

Views exist "to ensure governance quality, not exhaustive wikipedia brain dump that
is not mece". Every permanent node below answers one governance question; a node
that only re-indexes its parent is the parent again and does not exist.

### The tree (levels 1 to 3 are permanent, on disk, seeded as view rows)

```
L0  RECORD ── definitive; one pen; every row an act under a rule; plus the blobs
│
├── 1  [L1] EVENTS ── rows as happenings                 split by the row's effect
│   ├── 1.1  [L2] rule-changing acts                       create, amend, supersede, withdraw a rule
│   │   ├── 1.1.1  [L3] by programs (S)
│   │   ├── 1.1.2  [L3] by humans (S+U)
│   │   └── 1.1.3  [L3] by AI (U)
│   └── 1.2  [L2] acts under rules                         decisions, refusals, crossings, receipts
│       ├── 1.2.1  [L3] by programs
│       ├── 1.2.2  [L3] by humans
│       └── 1.2.3  [L3] by AI
│
├── 2  [L1] RULES ── rows that bind                       split by liveness
│   ├── 2.1  [L2] active rules
│   │   ├── 2.1.1  [L3] binding programs
│   │   ├── 2.1.2  [L3] binding humans
│   │   ├── 2.1.3  [L3] binding AI
│   │   └── 2.1.4  [L3] binding all actors                 the root and the constitution
│   └── 2.2  [L2] old rules                                superseded or withdrawn, never erased
│       ├── 2.2.1  [L3] bound programs
│       ├── 2.2.2  [L3] bound humans
│       ├── 2.2.3  [L3] bound AI
│       └── 2.2.4  [L3] bound all actors
│
├── 3  [L1] ITEMS ── versioned nouns; one thing, one place     split by liveness
│   ├── 3.1  [L2] active items         current version, in the active view
│   │   ├── 3.1.1  [L3] actors
│   │   │   ├── 3.1.1.1  [L4] programs (S)
│   │   │   ├── 3.1.1.2  [L4] humans (S+U)
│   │   │   └── 3.1.1.3  [L4] AI (U)
│   │   └── 3.1.2  [L3] static
│   │       ├── 3.1.2.1  [L4] content
│   │       ├── 3.1.2.2  [L4] spaces
│   │       ├── 3.1.2.3  [L4] keys
│   │       ├── 3.1.2.4  [L4] tunnels
│   │       └── 3.1.2.5  [L4] devices        (and by cell: S / U-involved, a filter over these)
│   └── 3.2  [L2] old items            previous versions; removed from the active view; never erased
│       ├── 3.2.1  [L3] actors            level 4 as above
│       └── 3.2.2  [L3] static            level 4 as above
│
└── 4  [L1] RELATIONSHIPS ── venn2 rows; one fact, two signed halves   split by liveness
    ├── 4.1  [L2] active relationships
    │   ├── 4.1.1  [L3] actor tree       containment, both ends actors; rooted at the constitution's root group
    │   ├── 4.1.2  [L3] item tree        containment, a static end; rooted at the mother space
    │   └── 4.1.3  [L3] non-tree         touching and declared overlap; names to things; connections
    └── 4.2  [L2] old relationships     ended, withdrawn, or superseded by a later version of the same relation
        ├── 4.2.1  [L3] actor tree
        ├── 4.2.2  [L3] item tree
        └── 4.2.3  [L3] non-tree
          level 4: by frame; computed overlap of two rules' scopes as checks
          invariant: in the governing frame every actor and every static item has AT LEAST ONE parent
          chain reaching the root — many parents lawful; an orphan or a loop is refused at the gate
```

### The rulings this version captures (each is the owner's, 2026-09-09/10; 19–23 are the v2.1 re-cut of levels 3 and 4)

1. **Four master views at level 1: events, rules, items, relationships.** Events and
   items are the one true pair of opposites (assertions over time; versioned nouns —
   v1 ruling 1). Rules are the binding rows on the event side; relationships are the
   graph derived over items. So level 1 is two definitive kinds plus the master each
   throws off. Today's seven seeded masters map onto it: rule master and the two
   registries under 2; actor and resource masters under 3; permission master (the
   grant rows) and relationship master under 4.
2. **Level 2 is one split per node, MECE.** A row either changes a rule or does not
   (the effect field). A rule is active or old. An item can act or cannot. A relation
   is a venn2 row. A product of a parent with a dimension is NOT a child: it is the
   parent re-indexed, and it lives at level 4.
3. **Old rules are a permanent node.** CONFLICT shown, not smoothed: v1 ruling 3 said
   history is never a permanent node; the owner now rules old rules as level 2.
   Later ruling controls. Cheap because the record is append-only: old rules are the
   rules fold without the latest-wins filter. "Stage" (the eight stages) is a
   measurement for metabolism at level 4; active/old is the band governance reads.
4. **Level 3 is one axis everywhere: S/U.** Events and rules split by their actor's
   class (every row has exactly one actor; every actor exactly one class — v1 ruling
   6, the classes are S/U positions). Actors split by class. Static items split by
   their own cell (S | U-involved), because the cell law makes the cell decide who
   may process the item. Two bands at level 3; the four cells at level 4.
5. **Actor top group is the class, never the top organisation.** A person is nested
   in an organisation as chief, in a club as gatekeeper, in a family as father —
   three nestings in three frames. A tree holds an item once, so the item tree
   partitions by the one thing every actor has exactly one of; the group tree lives
   in 4.1 as containment rows. This is why 4 is necessary, not decorative.
6. **Relationships are venn2 rows only, and globally true.** "No such thing as
   within or across records": a relation is one fact with two signed halves, each
   written by its own pen into its own record, and each machine holds both halves
   (its own; the counterpart's as the received signed row). The view never folds two
   records as one; it reads two signed halves. A machine holding only one half has a
   FINDING (venn2's missing expected relation), not a local relation. A relation
   row's frame is the rule it was created under; its reading is that rule's text;
   its roles are the row's actor, object, target; valid time is the creating and
   ending acts; transaction time is the recording moment (the two-clocks law); its
   source is the signature. New fields the row needs today: the geometry and the
   zone; the operation that creates one is named but not live.
7. **Authority is never a relation row.** Parent-child is containment (apple in
   fruit; support team in the IT department). Who commands whom (the chief over the
   support lead) is a rule on the roles plus two occupancies, computed — the
   no-authority-field principle of the foundation. The cgl hierarchy / network /
   system triad is a reading over geometry, not a relation kind.
8. **The three level-2 kinds under 4 answer governance questions.** Tree of actors:
   who a rule reaches through groups. Tree of items: what a rule reaches through
   containers. Connections: who may talk to whom or what — tunnels are root founding
   data, every act is information movement, a crossing is a connection that leaves
   the record; chains of effect are paths computed over connections plus the record's
   own causation, level 4. Exhaustive and exclusive because actors are items:
   containment with both ends actors = 4.1; containment with a static end = 4.2;
   touching = 4.3; possession and occupancy read as touching (venn2 §2.7).
9. **Overlap is never a node.** In OS/software work it is computed (shared pages,
   overlapping leases, ranges, grants). In governance work it is declared where
   scopes are text — a judgment act by a judgment-ready actor, stored as a relation
   row with the overlap geometry under the rule it was declared under, no in-between
   item needed. Either way it feeds the collision checks (contradiction, double
   claim, concentration, conflict of interest); real shared ground is promoted to an
   item in 3 with its own rules (venn2 formal spec §6).
10. **Persistence tiers.** Levels 1–3 permanent, seeded as view rows (v1 "base").
    Level 4 and up computed in memory and saved only when a rule says so (the user
    profile on a laptop is the example) — v1 "working set" and "custom".
11. **An event master is not a view anyone binds to.** Level 1 "events" is the
    definitive; nothing operational reads the raw record (design/28 I8).

19. **Level 2 is liveness on every derived master (v2.1, board :3760).** Rules, items and
    relationships each split into active and old by the one mechanism the rules already use,
    latest-wins over the append-only record. Nothing is erased; removal is leaving the active
    view. Old items are previous versions and removed things; old relationships are ended,
    withdrawn, or superseded by a later version of the same relation. Events do not split
    this way: a happening is never old.
20. **Names are relations, not items.** A rename, a second name, an old name are name-touches-
    thing rows under 4 (non-tree); a retired name is an old relationship. The item is the
    continuity anchor and has one place in 3 whatever it is called.
21. **Level 3 under 3 is actors and static; class, kind and cell are level 4.** The gate reads
    an actor's class off the actor row per act; no permanent view is needed for it. The
    level-4 lists are the owner's: actors by class, static by kind, and by cell as a filter.
22. **Level 3 under 4 is the spec's own line.** Nested and embedded are directional and make
    trees, split by the ends into the actor tree and the item tree; touching and overlapping
    are symmetric and make no tree. A declared overlap is a row and lives in non-tree;
    overlap computed from two rules' scopes stays a check at level 4.
23. **The safe point: many parents, none outside the tree.** In the governing frame every actor
    has at least one group chain reaching the constitution's root group and every static item
    at least one space chain reaching the mother space. Many parents are lawful (the chief of
    an organisation, the gatekeeper of a club, the father of a family is one actor with three
    chains); an orphan or a loop is refused at the gate, as the gate already does for spaces
    (gate.py:501-518). A rule's scope reaches down every chain, which is how permission is
    inherited systematically; two chains reaching one node with colliding rules is the
    overlap check's case. Containment rows in other frames never carry permission.

24. **The third view form (v2.2, board :3817).** The machinery held two row forms, a master
    that binds a fold and a filter over the record's six dimensions, and neither can express
    a parent's output narrowed by one property, which every level-3 node under a master is.
    The July target-state paper ruled the read stack's third level, system views derived from
    masters; this gives it a row form: a DERIVED view names its parent view and one closed
    derived dimension (actor_class, scope_class, item_kind, liveness, tree_kind; grow-only,
    pinned), and the engine serves the parent's output narrowed by it. Level-1 and level-2
    nodes bind folds; every level-3 node is one derive, which is "parent plus exactly one
    move" made a row; level 4 stays computed. The machine form carries seed_form per node as
    the seed's independent oracle. *(v2.3, board :3825, a precision of where the door is:
    the view-creating operation is registered at boot and has no operation definition in the
    constitution, so its door is its own inline refusal, the same door that refuses an
    unknown fold or an unknown trigger dimension. The derived dimensions live in code beside
    the fold set, grow-only and pinned; a derive is refused there when its dimension is
    outside the set, when it names more or fewer than one dimension, when its parent is not
    a view already in the record, or when it rides with a bind or a trigger. The earlier
    wording "declared structural on the operation" carried a definition-born idiom onto an
    operation that has none; the substance, validated before anything is written, is
    unchanged.)*

### The loop — how an act climbs and how the record comes back down (owner-ruled 2026-09-10, board :3743)

*(v2.4, board :3869, a precision of rulings 13 and 17b, where the stamp lives: the stamps are a field the gate adds to the act's own row at the one write, beside provenance, the same class as the invoking account's signature in provenance. They are excluded from the content the invoker signs, because the invoker cannot know them; the store's countersignature covers the recording fact only; a stamp altered in a stored row is caught by the record chain, every row hashing the whole of the one before it. The earlier wording \"as the decider's seal already is\" named a mark this record does not have: the seal inside the signed content is the caller's own field. The substance stands: the stamp is on the act's own row, written once by the gate, never by a caller, and detection never legitimacy.)*

Sources already ruled and standing: the flow ruling of 2026-07-17 (design/31 v3: acts up
through parent gates, each hop checked against its local view; the record broadcasts down
through the masters; views cross-check sideways; the gate alone writes); the two times of
authority, 2026-07-25 (design/35); the four ideas, ruled 2026-07-29 (design/38 and its
addendum: the multi-view stamp stands; the intent cache stands as pipeline; effect before
write refused inside one machine, alive across machines); the fanqie law, 2026-09-02
(dialogue 06; design/37: recovery = content redundancy × relational redundancy; hash
between the item in the view and the item in the record; the first three levels on disk,
verified on load and before shutdown).

12. **The integrating element.** Every derived thing carries a witness of the world it was
    derived from, and every witness is checked against a neighbour, not only against the
    root. The deciding time and the seal are the actor's witness; the stamp is each master
    view's witness; the echo is the record's witness back; the sideways check is neighbour
    against neighbour; the cross-attested checkpoint is the view against the record at rest.
    This is the owner's governance principle turned inward: the master views are the
    machine's separated powers, each a different perspective; the stamp is their guaranteed
    say; the record is the constitution. A view is a small governance body of its own.
13. **The three times, placed.** Deciding time: on the act, signed (built). View-checked
    time: the stamp a master view puts on the act as it climbs — the view's identity, the
    hash of what it saw, the record version it saw it at (ruled, not built). Finalised
    time: the record's echo retiring the view's pending entry — a change in the view's own
    pipeline, never on a record row (ruled as pipeline). The recording time stays the sole
    order anchor, minted at the write.
14. **Detection, never legitimacy.** A stamp adds no legitimacy: inside one machine every
    view derives from the same record, so three views agreeing is one derivation done three
    times, and no number of views outvotes the record. A view's refusal to stamp is an early
    answer and a fact for the gate, never a veto. Where a class of act must carry named
    stamps before the gate accepts it, that is a rule, metabolised like any rule, never a
    property of the view. The stamps do not protect against a lawfully signed bad rule.
15. **The rogue-chief test.** A row coming down that the master views its reach touches never
    stamped is flagged as unseen. The organisation never saw it; if the constitution keeps
    announcing what no view stamped, the constitution machine has gone rogue.
16. **Okay-or-not is local; a rule change is final only at the record.** A local NO is always
    safe (a must-not fails closed; the brake carries a frozen view of only the must-nots).
    A local YES is final for an effect that can be undone and provisional for one that
    cannot — the line is what the reconciliation sweep can still repair; an overturn cannot
    reach what was consumed. A rule change binds from its deciding moment, is final only when
    the record has it, and binds a view only when the broadcast reaches it. A remote decider
    (a laptop against a cloud record) may act on its local answer before the record writes;
    inside one machine that is refused as pointless. More tiers of view for safety: in memory
    free; a permanent tier is one view-definition row, never a change to the masters or the
    founding.
17. **Witnesses, not walls; and the local slice.** More witnesses catch a tamper with a view
    or a path; a tamper with the record is caught by the cross-attested checkpoints and the
    hardware anchor. The wall is the gate as the only pen, the append-only record, the
    anchor; a program is an actor whose acts cross the gate and are paired by class. A local
    view is a slice of the top three levels cut for one session (the rules binding this
    actor and its groups; the rules binding its programs and their connections; the items it
    holds), carrying the record version it was cut from and its hash, checked on reconnect,
    its must-nots live while cut off — the personal local rule view of design/35, session-
    scoped.
17b. **Where the stamp lives (precision, board :3800).** The stamps travel with the act and are
    written into the act's own row at the one write, as the decider's seal and deciding time
    already are; a witness a restart can erase is not a witness. The view's pending copy is
    pipeline state retired by the echo; the finalised time stays off every row (13); a stamp on
    the row adds no legitimacy (14). The unseen and sideways checks are then record folds that
    survive a restart. The stamps list is one structural envelope field, a founding move.

18. **The costs, named.** The stamp ceremony is governance-rate work; the class of act decides
    who is stamped, and cache-fill acts get none. The climb does not exist today — the write
    path is one hop to the gate — so building the stamp means building the intake pipeline
    the acts pass through: a write-path change, not a view change.

### Honest caps

- The multi-view stamp (13–15) and the local slice (17) are ruled, not built; the stamp is
  the view-tree campaign's write-path unit (design/53 VT-6).
- Today only the seven masters are rows; every system view is a code function
  (roughly ninety in views.py). This version, like v1, states derivation and naming;
  seeding levels 1–3 as rows is design/53's work, and it changes what views are
  called and derived from, not what the gate consults or in what order.
- The v2.0 level-3 S/U axis under 3 moved to level 4 at v2.1 on the owner's word; the
  event and rule sides keep their class split at level 3.
- Extending the no-orphan / no-loop refusal from spaces to actors is unbuilt; the campaign
  carries it.
- Static items' cell (3.2) presumes each item kind carries or derives a cell; today
  blobs are U-involved and keys, spaces, tunnels, devices are S by their creating
  operation's declared cell — derivation, not a new field, until a case needs one.
- The two venn2 chat captures in the corpus were not read for this version.

---

## VERSION 1 (2026-07-15) — kept as history; superseded above where they differ

**Status:** v1, 2026-07-15. Owner-ruled in session (see rulings inside
`25-view-tree.json`, the structured source of truth for the tree). This doc is the
plain-language companion. The JSON is written to be ingestible later as the seed
view-req records, since view definitions are themselves REQ-form records
(cgl canonical doc 3).

## The rulings this captures

1. **Two definitive stores only.** Event store (assertions over time) and item store
   (versioned nouns). Relationship is the derived master graph, never stored.
2. **Numbering = derivation.** Each child is its parent plus exactly one move:
   a filter, a product (x), or a split. Parentage is not exclusive; the tree shows
   the primary deriving logic.
3. **Active-only.** `[a]` views hold current state only. History, asOf, trends are
   once-off queries against the store, never permanent nodes.
4. **Functional necessity only.** The base tree holds only what the kernel cannot
   run without. Everything else is a custom view, created through the view req view
   (1.1.1.3), permanent only if a req says so.
5. **Deontics (owner, 2026-07-15):** dos = must-happen (condition hits, the system
   makes it happen). Don'ts = must-not-happen (condition hits, the system prevents
   it). **May is not a rule class**: it is the residual space computed per call.
   Permission is a live matching function, never a stored list — a stored
   permission list is a snapshot of a moving calculation and rots on any law change.
   Default-deny = the root don'ts (no authorising chain → no act); a grant creates
   the chain that un-matches the root don't.
6. **Actor classes are S/U positions** (system = pure S, human = S+U, agentic = U);
   device and process are tags inside system actors, not classes.
7. **Space's only intrinsic dimension is persistence** (permanent vs non-permanent).
   Every other cut (sharing, capacity, location) is a product with other branches.
8. **File and memory region are one item type** (content-housing); which one it
   "is" derives from its space's persistence. mmap is the conventional kernel's own
   accidental admission of this.

## The tree (short form; JSON is authoritative)

```
1 EVENT STORE                      definitive
1.1 req view                       all prescriptive events, all lifecycle states
1.1.1 active req view [a]          in power now
1.1.1.1 active dos view [a]        must-happen: timers, handlers, bindings, routing
1.1.1.1.1 compliance view [a]      actor x active dos
1.1.1.1.1.1 local duty profile [a] one actor's standing obligations
1.1.1.2 active donts view [a]      must-not: root donts, firewall, filters, locks, limits
1.1.1.3 view req view [a]          governs all custom views: creation, refresh, broadcast
1.2 activity log view              the happenings
1.2.1 governance activity log [a]  rule-citing acts: decisions, grants, refusals
1.2.2 wait/wake view [a]           who is blocked on which condition

2 ITEM STORE                       definitive
2.1 action view [a]                the registry: registered verbs, not retired
2.2 resource view [a]              actable-on, actor-inclusive
2.2.1 actor view [a]               system (S) / human (S+U) / agentic (U)
2.2.2 system information view [a]  info about info
2.2.2.1 information space view [a] permanent / non-permanent
2.2.2.2 scope item view [a]        view list · content-housing · system policy items
2.2.2.3 content item view [a]      the actual bytes
2.2.3 tunnel item view [a]         valid message paths

3 RELATIONSHIP VIEW [a]            derived master graph, frame-scoped
3.1 parent-child [a]               containment family; walkable chains
3.2 contact [a]                    touching/overlapping family
```

## Live checks (functions, not views)

permission() · sight() · authority() · due() · wake() · consistency() — each
consults base views and walks relations at call time. Signatures and returns in
the JSON.

## Tiers

- **Base** (this tree): permanent, workered.
- **Working set**: hot products composed from base, ephemeral caches, no
  governance machinery on the hot path (runnable set, memory map, paths,
  bindings, topology, headroom).
- **Custom**: everything else, via the view req view only.

## Companion

The exhaustive kernel derivability audit (every conventional-kernel concept
expressed over this base) is `26-KERNEL-DERIVABILITY-AUDIT.md`.
