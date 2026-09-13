<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture (seL4/POSIX/OS-textbook) · Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature (kernel, syscall, capability, permission, memory protection). NON-GOAL: no offensive capability of any kind; defines record, gate, view, and kernel-conformance only. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=CANON status=FROZEN supersedes=- superseded-by=- verified=2026-07-24 -->
# GOV-OS — Canonical Glossary (one name per thing)

> **SUPERSESSION NOTE (2026-07-18 line-audit).** CURRENT where it goes, INCOMPLETE by
> growth: the campaign added a large vocabulary this glossary predates — tier
> (constitutional/owner/ordinary), conservation/AMEND-OP, the untouchables, grant/scope/
> space/account, obligation/tick/due, blind-stream, paper-tiger/metabolism, the fold
> library. For a campaign-era term, the defining design doc (25–32) controls; this
> glossary still governs the base field/verb/law-id names it does carry. Naming drift
> is now caught by T-NO-LAW-IN-CODE + the reviews, not this doc alone.

**Status:** v0.1, 2026-07-12. This document ends the naming drift found in the
architecture review: where the shapes book (11) and the operations catalogue (12)
sketched the same thing under two names, the canonical name is fixed HERE, once.
This glossary controls all design documents until seam S1 (the one store
contract) freezes the wire schema — at which point S1 inherits these names.
Nothing here changes any *meaning*; every entry is pure naming. Amending a name
is an amendment to this document, never a silent edit elsewhere.

---

## 1. Envelope field names (canonical, from the shapes book §1.1)

| Canonical name | NOT this | Meaning |
|---|---|---|
| `record_id` | — | stable record identity |
| `seq` | — | total order, minted at append by the sequencer |
| `record_time` | — | sole total-order anchor |
| `submission_time` | — | monotonic per origin, never globally ordered |
| `origin.subsystem_id` | `origin` alone | which origin wrote it |
| `origin.built_id` | `built-ID` in prose is fine | the tiebreak key: origin creation order |
| `actor` | — | AAOT actor |
| `action` | `verb`, `op` | AAOT action — a registered operation name (§2) |
| `object` | — | AAOT object |
| `target` | — | AAOT target (nullable) |
| **`rule_cited`** | ~~`cited_rule`~~ (doc 12's sketch) | the LAW record this decision applied or refused under — mandatory on every DECISION and refusal |
| **`evidence_summary`** | ~~`evidence`~~ (doc 12's sketch) | the embedded aggregate a decision acted on, when it relied on sampled stream evidence |
| `provenance` | — | sight-gate input: what the writer could read |
| `payload` | — | class-specific body; large payloads blob-referenced by hash |
| `content_form`, `refs[]`, `occurrence_time`, `recorder_id`, `asserted_by`, `confidence_tier` | — | supporting fields, per 02 §1.1 |
| `refused` | `blocked`, `denied` | boolean marker on a refusal record |

## 2. Operation names (the `action` values)

**Rule:** the twelve bootstrap operations keep their corpus-verbatim UPPERCASE
names (they are quoted from the foundational import pack, frozen-layer style).
All kernel operations use kebab-case, named as registered at the gate — doc 12's
forms are canonical; doc 11's UPPERCASE sketches (`SCHEDULE-ADMIT`, `MEM-EVICT`,
`FILE-WRITE`, `DEVICE-BIND`, `COMMS-SEND`, `SHM-GRANT`) are superseded by the
mapping below.

**Bootstrap (verbatim, unchanged):** `READ`, `FOLLOW`, `CREATE-INFO`,
`CREATE-ACTIVITY`, `CREATE-RELATIONSHIP`, `CREATE-RULE`, `CREATE-ACTOR`,
`CREATE-TUNNEL`, `WRITE-ACTIVITY`, `CHECK-RULE`, `CHECK-CONTRADICTION`, `BLOCK`.

**Scheduling:** `admit-process` (⇦ SCHEDULE-ADMIT), `deschedule` (⇦ DESCHEDULE),
`set-priority`, `halt`, `kill`, `standby`.

**Memory:** `grant-mapping` (⇦ MEM-GRANT), `protect-region`, `evict-page`
(⇦ MEM-EVICT), `amend-budget`, `oom-decision`.

**Files:** `create` (⇦ FILE-CREATE), `write` (⇦ FILE-WRITE), `link`
(⇦ FILE-LINK), `unlink` (⇦ FILE-UNLINK), `change-permission`
(⇦ FILE-PERM-CHANGE), `mount`, `unmount` — doc 12 §3's registered names,
exactly as written there.

**Devices:** `register-driver` (a LAW amendment), `bind-device` (⇦ DEVICE-BIND),
`unbind` (⇦ DEVICE-UNBIND), `grant-capability` — doc 12 §4's names.

**Comms:** `open-channel` (⇦ COMMS-OPEN), `close` (⇦ COMMS-CLOSE), `send`
(⇦ COMMS-SEND), `receive` (⇦ COMMS-RECV), `grant-shared-region` (⇦ SHM-GRANT)
— doc 12 §5's names. **Known required addition to doc 12:** `revoke-shared-region`
(⇦ SHM-REVOKE) — its record shape exists (doc 11 §3.6) but the operation entry is
missing from the catalogue; adding it is a catalogue amendment per doc 12's own
growth rule (cross-cutting invariant 3), flagged here rather than silently patched.

**Inputs (recorded arrivals; `actor` = the external source):** `irq-arrival`,
`io-completion`, `timer-tick`, `packet-arrival`.

## 3. LAW identifier scheme

**Canonical:** `law:<scope>@<version>` — e.g. `law:sched-policy@7`,
`law:mem-budget:cgroup:web@3`, `law:perm:/var/log@5`, `cap:driver:nvme0@1`
(capability registrations keep the `cap:` prefix). Doc 11's form is canonical.

**Doc 12's handles** (`SCHED-LAW-ADMIT`, `MEM-LAW-ALLOC`, `FS-LAW-*`, …) are
**aliases** — readable shorthand for whichever `law:…@v` record fills that role
in a given instance. In any record, `rule_cited` carries the `law:…@v` id, never
the alias. Aliases may appear in prose and documentation only.

**Root rules keep their verbatim corpus names** as ids in the root namespace:
`ROOT-NEG-1/3/4/5/6`, `BOOT-INT`, `P3-CLOSURE`, `P4-REFUSE`, `SIGHT-IS-LAW`,
`CAP-IS-LAW`, `SOP` — these are boot-established LAW records whose ids are their
names (versioned like any law: `ROOT-NEG-1@1`).

## 4. The five recording classes (already consistent — restated for one-stop reference)

`LAW` / `DECISION` / `INPUT` (the three recorded classes) · `CACHE` / `STREAM`
(never appended). Meanings per `03-TARGET-STATE-ARCHITECTURE.md` §2 — that
section is the authority; no document may redefine a class.

## 5. Resolved inconsistencies (the review findings, closed)

1. `cited_rule` (12) vs `rule_cited` (11) → **`rule_cited`** everywhere.
2. `evidence` (12) vs `evidence_summary` (11) → **`evidence_summary`**.
3. UPPERCASE kernel verbs (11) vs kebab-case ops (12) → **kebab-case**, mapping
   in §2; bootstrap ops stay verbatim UPPERCASE.
4. `SCHED-LAW-*` handles (12) vs `law:…@v` ids (11) → ids canonical, handles are
   documentation aliases (§3).
5. Stale citation `03-TARGET-STATE-KERNEL` in 11 §6 → corrected in place to
   `03-TARGET-STATE-ARCHITECTURE.md` (2 occurrences), plus a stray code fence
   removed.

**Honest cap:** this glossary reconciles the *design* documents. The wire-level
schema (encodings, hash algorithm, field order) is still seam S1's job; S1 must
inherit these names or amend this document explicitly.
