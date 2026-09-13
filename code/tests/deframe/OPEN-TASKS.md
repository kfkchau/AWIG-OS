<!-- gov-os provenance · systems-architecture documentation · the open-items list for the documentation-register work. -->
<!-- doc: class=CANON status=LIVE supersedes=- superseded-by=- verified=2026-07-25 -->
# GOV-OS — De-framing: what is not finished

The state at 2026-07-25, after the four-layer scan and the `_v3` de-frame pass. What is done,
and what is still open. Ordered by what blocks the most.

## Done (for reference)

- All changed/new docs scanned against the four layers; ranked; five shared roots named.
- 29 docs de-framed as `_v3` copies (Layers 1–3 removed, Layer 4 kept), fidelity-checked by
  diff — every change confirmed meaning-preserving, three phrasing slips corrected.
- The 29 pre-`_v3` originals moved to `tests/archive/` (four kept as `.pre-v3` where a true
  original was already archived). Working folders now hold the `_v3` versions.
- A private reference dashboard of the scan exists (by-document and by-layer views).

## Open — highest first

**1. The working docs are named `X_v3.md`, not `X.md` — cross-references now dangle.**
By instruction, the `_v3` files were kept as-is (no rename) and the canonical `X.md` names were
moved to `tests/archive/`. So every place that points at a canonical name — the ~130 in-repo
cross-references, the EP session-prompt paths, `DOC-MAP.md`, the design and planning indexes,
and the `_v3` docs' own references to sibling docs — now resolves to a file that lives in
`tests/archive/`, not the working folder. This has to be settled before the docs are used for
real work. Two clean ways: (a) rename each `_v3` to its canonical name and re-archive the old
canonical (the promotion the earlier v2 pass did); or (b) leave the `_v3` names and rewrite the
references to match. Option (a) is far less work and keeps every existing pointer valid. Until
one is chosen, treat the `_v3` set as a staged, not-yet-wired result.

**2. Root 4 — the disclaimer header and scope-statement denials (repo-wide, held out).**
The line-1 "NON-GOAL: no offensive capability of any kind" appears on ~90 files, and negated
denials sit in `00-READ-FIRST.md` §4b ("no exploits, no malware, no intrusion, no evasion") and
the "threat models = drift" standing guards. These read as a trigger themselves (a denial keeps
the terms in context). This pass deliberately left them alone — it is a separate, repo-wide
decision. The fix: state scope positively (what the work does — records, gates, views, kernel
conformance) and drop the negations. Decide, then sweep. `tests/deframe/DEFRAME-SOP.md` §2/§3
carries the reasoning; the new positive-form header on the three `tests/deframe/` docs is a
worked example of the target style.

**3. Three earlier-de-framed docs were not re-scanned this round.** `15-FAILURE-BOOK`,
`MENTOR-HANDOVER`, `MENTOR-LETTER` were de-framed in the earlier v2 pass and are the current
canonical; they were not in this round's changed set, so they were not re-checked against the
four layers. Likely light, but unverified. Optional: run one scan agent over them for residue.

**4. The archive syncs to the remote.** `tests/archive/` is not git-ignored, so the
frame-heavy pre-`_v3` originals (and the `.pre-v3` copies) push on the next autosync — the very
register this work removes still leaves the machine. Also `tests/deframe/DEFRAME-SOP.md`
necessarily contains the trigger-term inventory. Decide whether to keep these local-only (add
`tests/archive/` — and possibly `tests/deframe/` — to `.gitignore`, the pattern `planning/
private/` already uses). This is a persistent-config change; make it deliberately.

**5. The remote's public/private status is contradictory in the repo's own files.** The
`.gitignore` comments say twice that the repo "auto-pushes to a **public** remote"; `BUILD_LOG.md`
and the handover call `<REPO-URL>` a **private** repo. This decides whether the
archived originals are publicly visible. Check the actual git remote and reconcile the wording.

## Not open (recorded so they are not re-raised)

- Whether to fully strip the `R20-x` finding numbers or expand the matrix act-tokens —
  **accepted as-is** (numbers kept as work-item handles; tokens kept as table identifiers).
- The CLEAN docs (`28`, `34`, `PWC-GAPMAP`, `DOC-GOVERNANCE`, `00-PLANNING-INDEX`, the four
  `.claude/agents/gov-*` definitions) — nothing to do; the review tooling is anti-register and
  will not regenerate the frame.

---

# DISPOSITIONS [added 2026-07-31 — this file sat outside every read path for six days and its items were untracked]

**1 — the `_v3` naming and the ~130 dangling cross-references: CLOSED 2026-07-26.**
The owner chose a third option this file did not list: **restore pointer STUBS at
the canonical names**, pointing at the `_v3` bodies — restore, not repoint, per
`DOC-GOVERNANCE` §3 step 3. **So the instruction below to "treat the `_v3` set as a
staged, not-yet-wired result" has been FALSE since 2026-07-26**, and the estate has
built on those files for a week. Verified: `MENTORSHIP-CHARTER.md`,
`EXECUTION-PLANS.md` and `DOC-MAP.md` are 13-line stubs pointing at their `_v3`
bodies, and no citation dangles.

**2 — the disclaimer header and the negated denials: REFUSED, owner-ruled
2026-07-31. THE HEADERS STAY.** This file proposed dropping the
`NON-GOAL: no offensive capability of any kind` line and the `00-READ-FIRST` §4b
denials, on the reasoning that a denial keeps the trigger terms in context.
**The owner's ruling is that those headers are load-bearing for a reason this file
did not weigh: they are what keeps this work legible to an AI safety classifier,
and the owner has direct experience of sessions being flagged without them.**
`action-gate.md` exists because that happened. **The header is not decoration and it
is not register — it is the mechanism that lets the work proceed at all.** Not to be
revisited.

**3 — three docs never re-scanned: OPEN**, optional, low value. Carried to EP-33.

**4 and 5 — the archive syncing to the remote, and the public/private
contradiction: BOTH CLOSED 2026-07-31.** **The remote is PRIVATE** and this laptop
is the single source of truth. The `.gitignore`'s three "public" comments and
`BUILD_LOG`'s heading were corrected the same day. **So `tests/archive/` and
`tests/deframe/` syncing is a mirror rather than an exposure, and no `.gitignore`
change is needed.** Charter §A37.

**And the finding about this file itself, recorded here because it is where the next
reader will meet it: a file named `OPEN-TASKS.md`, outside every map and every read
path, is where work goes to be forgotten.** It is now in the generated document
inventory and cannot vanish again.
