<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture (seL4/POSIX/OS-textbook) · Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature (kernel, syscall, capability, permission, memory protection). NON-GOAL: no offensive capability of any kind; defines record, gate, view, and kernel-conformance only. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=CANON status=LIVE supersedes=- superseded-by=- verified=2026-07-24 -->
# GOV-OS — The Base View Tree (definitive → derived)

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
