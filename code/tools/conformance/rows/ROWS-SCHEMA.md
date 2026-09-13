<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: conformance-harness · Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature (kernel, syscall, capability, permission, memory protection). NON-GOAL: no offensive capability of any kind; defines record, gate, view, and kernel-conformance only. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=CANON status=LIVE supersedes=- superseded-by=- verified=2026-07-26 -->
# The row schema — design/10's map, as the harness's data

**Status:** v2, 2026-07-27 (EP-24D adds `outcome_class`; v1 2026-07-26, EP-24).
`design/10-SYSCALL-CONFORMANCE-MAP.md` is the contract; these files are that
contract in machine-readable form, one file per group, named for the map's own
section numbers. The map controls: where a row and the map disagree, the map is
right and the row is a defect.

**A row is DATA and the harness holds no vocabulary.** Adding a syscall, or
reclassifying one, is an amendment to design/10 with authority (design/10 §3) and
then an edit to these files. It is never a code edit in the harness. The harness
compiles whatever rows it finds into assertions; it knows the five classes and
the six cross-cutting rules, and nothing else about any particular call.

## Fields

| field | meaning |
|---|---|
| `row_id` | Stable identity, `<group>.<name>`. Used for baseline keys and scratch directories. Never reused for a different call. |
| `syscall` | The primary call name, exactly as design/10 column 1 gives it. |
| `variants` | Variant names that ride this primary (design/10 §12: same class, same note). The compiler generates one assertion per variant. |
| `what_it_does` | design/10 column 2, verbatim. |
| `subsystems` | design/10 column 3, as a list. |
| `recording_class` | design/10 column 4, as a LIST of the five class names (`LAW`, `DECISION`, `INPUT`, `CACHE`, `STREAM`). A row that column 4 marks mixed is SPLIT into sub-rows where the map's own note splits it; where the note does not split it, the row is `DISPUTED` and is raised, never guessed. |
| `conformance_note` | design/10 column 5, verbatim. This is the sentence a later reader argues with. |
| `map_ref` | Where in design/10 the row lives. |
| `status` | `ENCODED` (the map settles it) or `DISPUTED` (faithful mechanization needs a judgment the map does not settle — raised, never resolved here). |
| `active` | Whether the row's assertions run today. |
| `activates_at` | The EP at which an inactive row activates. Activation is this one field flipping — never new harness code. |
| `rules` | Overrides on the six cross-cutting rules (§11). Omitted fields take the derived default (below). |
| `record_expectation` | Optional override of the check-2 expectation the class derives. Present only where the map's note states something the class alone does not carry. |
| `probe` | `{"steps": [...]}` — the row's executable assertion, run unprivileged, or `null`. |
| `probe.outcome_class` | design/10 §11.1a. Required on a probe whose TESTED OUTCOME is an error return; one of `REFUSAL`, `ABSENCE`, `NOT-GOVERNED`. It rides the probe rather than the row because a privileged pass tests a different outcome from an unprivileged one (`files.mount` succeeds as root and returns EPERM otherwise), and a declaration attached to the row would bind on an outcome it does not describe. `root_probe` and each entry of `variant_probes` declare their own. |
| `root_probe` | `{"steps": [...]}` — the row's privileged pass, if it has one. It runs only on a target whose descriptor declares the `root` capability; elsewhere it is SKIPPED with that reason, counted, and named in the manifest. It gets its own assertion identity (`<row_id>#root`), so a privileged observation is never merged into an unprivileged one. |
| `probe_absent_reason` | Required when `probe` is null. Says exactly what the limit is. An absent probe is a declared blind spot, never a silent gap. |
| `probe_limits` | What this row's probe does NOT drive, in sentences. A limit that is written down is a coverage statement; the same limit unwritten is a lie by omission. |
| `variant_probes` | `{variant: {"steps": [...]}}` for variants driven separately, so §12's "variants ride their primary" is TESTED rather than assumed. |
| `driven_in_primary` | Variant names exercised inside the primary's own step list (`openat` through a dir_fd, `fchmod` through a descriptor). They are driven — a divergence WOULD be seen — but they have no observation of their own. Counted separately from both "probed" and "undriven", because conflating them either overstates the coverage or understates it. |
| `subject_calls` | Which probe-vocabulary entries in the step list ARE the call under test. Derived by default from the row's syscall and variants; stated only where the map's naming and the available binding differ (`creat`, driven through its documented open-flag equivalent). Everything else in the list is setup, and its records belong to those acts rather than to this row's class. |

## Activation

A group file carries `active` and `activates_at`; a row may override either.
Turning a group on is that ONE field — the rows, their classes, their §11 rules
and their probe steps are all already here as data. Activation is never a change
in the harness.

## The derived defaults (§11, applied by the compiler to every row)

1. **errno identity is load-bearing** — always on. Every step's errno is compared
   by name. No row may turn this off.
6. **Timing is out of contract** — always on, and there is nothing to compare:
   no observation carries a duration.

3. **`/proc` and version values are shape-only** — off by default, on for rows
   whose answer is a live figure of the target (`rules.shape_only`). The probe's
   normalizers already enforce this for stat/statvfs-shaped answers.
2. **Ordering is checked at the guarantee's level** — `rules.ordering` names the
   guarantee (`"append-atomicity"`, `"lock-exclusion"`) or is null. A row with an
   ordering guarantee drives it as a guarantee, never as an interleaving.
4. **Coalescing is a named calibration** — `rules.coalescible` true means check 2
   may not require one record per micro-event. It reads the row's WHOLE record
   window rather than the calling step's bracket, because a folded write's
   covering decision lands in a later bracket by design. What it requires: the
   covering event exists at all; and where FEWER covering events were appended
   than the row drove acts — which is folding, seen from outside by counting, not
   by asking the target — the policy exists (the target declares it) and the
   surviving events cite it. Folding is LICENSED, never mandated: one covering
   event per act, citing no policy, is equally conformant and is what a world
   with the policy superseded to nothing produces.
5. **Payload fidelity is independent of STREAM** — set automatically for any row
   whose class list contains `STREAM`. It forbids inferring a lossy data path
   from the classification, and the probes assert exact bytes on those rows.

## The check-2 expectation each class derives

| class | what check 2 requires of the records appended while the row ran |
|---|---|
| `LAW` | at least one record whose action the TARGET's own class map declares LAW-class, carrying a non-empty rule citation |
| `DECISION` | at least one DECISION-class record, carrying a non-empty rule citation |
| `INPUT` | at least one INPUT-class record |
| `CACHE` | none at all |
| `STREAM` | none required; any record that appears must be STREAM-class and cite a recorded coalescing policy (§11.4) |

For a multi-class row the requirement is the union, and any record whose class is
outside the row's class list fails the check — that is the "exactly the record its
row assigns" half of design/10 §3 check 2.

## What an `outcome_class` changes (design/10 §11.1a)

| declared | what check 2 requires |
|---|---|
| `REFUSAL` | at least one rule-citing `DECISION`- or `LAW`-class record — whatever class the row's success path carries, because a refusal is precisely where a record is most required (P4). Those classes are permitted here as well as required. |
| `ABSENCE` | none at all. The view answered "no such thing" and the call is a read, so a record appearing IS the failure. |
| `NOT-GOVERNED` | none at all. The call never reached a governed decision, so a record appearing IS the failure. |
| absent | the class list's own requirement, in full. |

There is no waiver. The check used to relax its required half whenever every
subject step of a row returned an errno — a property of the ANSWER THE TARGET
GAVE — which switched the audit leg off exactly where a refusal makes it most
necessary. What check 2 requires now comes from the row and only from the row.
