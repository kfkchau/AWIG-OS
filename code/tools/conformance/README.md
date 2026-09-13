<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: conformance-harness · Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature (kernel, syscall, capability, permission, memory protection). NON-GOAL: no offensive capability of any kind; defines record, gate, view, and kernel-conformance only. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=CANON status=LIVE supersedes=- superseded-by=- verified=2026-07-26 -->
# The conformance harness — the campaign's standing instrument (EP-24)

**Status:** v2, 2026-07-27 (EP-24D: the subject check, the subject lifecycle, the
§11.1a outcome classes, and §11.4's fold leg reading the row's window; v1
2026-07-26, EP-24). `design/10-SYSCALL-CONFORMANCE-MAP.md` is the
contract; this tree is that contract made runnable. Every custody EP's acceptance
consumes it: EP-25's mount is the first, EP-28's in-kernel filesystem the next,
and the subsystem EPs after that activate their own groups.

## The one-paragraph version

Each row of design/10 is an executable assertion with three independent checks —
the ABI answered identically, the record the row's class assigns actually
appended, and the post-call state reproducible by replaying the record. The
harness runs those assertions against two kinds of target. Against a STOCK kernel
it captures what Linux answered and pins it as committed, dated, sha-summed text.
Against a GOVERNED target it judges: the pinned answers plus the two legs no
imported suite runs.

## Running it

```bash
python3 -m tools.conformance.harness.runner list
python3 -m tools.conformance.harness.runner capture --target ep21-ubuntu-guest
python3 -m tools.conformance.harness.runner verify  --target <governed> --baseline ep21-ubuntu-guest
```

`capture` refuses a governed target and `verify` refuses a stock one. `verify`
exits 1 when any row fails and **2 when it refuses to run at all** — a subject it
could not establish, or a scratch it found dirty. The two are kept apart because
"rows failed" and "this run never happened" are different facts.

## The tree

```
rows/        design/10's rows as data, one file per section of the map.
             ROWS-SCHEMA.md is the field-by-field contract.
harness/     rows.py     the row compiler: rows -> assertions (+ §11, + §12 variants)
             probe.py    the one program that drives the calls ON a target
             checks.py   the three checks of design/10 §3, independent by construction
             targets.py  what a target is and how the harness reaches it
             baselines.py capture, pin, sha-verify, load
             runner.py   the dual-target CLI
targets/     one descriptor per target. Two stock, five self-test fixtures, two
             mounts. Each governed one declares its `subject` (the path and the
             filesystem that must serve it), its `class_map` and its `covers_map`.
             ep25-custody-covers.json is the covers map both M2 worlds share,
             because both run the same mount.
baselines/   the pinned captures. Committed text; MANIFEST.json sums them.
fixtures/    the self-test's governed targets — one correct, three deliberately
             wrong, and one that defers its emission to a later step the way a
             folded write does.
```

Evidence for the first capture and the self-test:
`planning/vm/CONFORMANCE-BASELINE-EVIDENCE.md`. Regression battery:
`tests/test_ep24.py` and `tests/test_ep24d.py`.

## Four properties worth knowing before you change anything

**The rows are DATA and the harness holds no syscall vocabulary.** Adding a
syscall or reclassifying one is an amendment to design/10 with authority, then an
edit in `rows/`. If a row needs a code change in `harness/` to compile, the row
is written wrongly. The one table in the harness that names syscalls is
`probe.DRIVES`, and it says only which vocabulary entry calls what — never what
any of them means.

**The baselines are pinned, structurally.** `verify` reads a capture off disk by
name and builds a transport to the GOVERNED target only. There is no argument,
flag, or fallback by which it could reach a live stock kernel — proven with the
lab guest powered off, and re-proven in the suite by poisoning every route to one.
`load()` recomputes every sha256 first, so a baseline that changed since capture
refuses rather than quietly becoming the new truth.

**The instrument establishes its subject, and leaves it as it found it.**
design/10 §11.2b. Before any row runs, `verify` confirms that the target's
declared path is served by the filesystem its descriptor names — read from
`/proc/self/mountinfo`, the kernel's own answer, never the target's word for it —
and ABORTS otherwise, because a pass against an absent subject is indistinguishable
from success. The probe's scratch is then established CLEAN (created if absent,
refused by name if it holds anything) and torn down after, so a run cannot leave a
mountpoint in a state that blocks the next mount. Three runs during EP-25 reported
on a plain host directory; the third one's leftovers then made the mount
unraisable. `~` in any descriptor path is expanded before use — one became a
directory literally named `~`, and the harness reported ABI 40 of 40 against it.
A fixture is stood up by the self-test (`fixtures.stand_up`), never by the
instrument: "the mount was not raised" and "the harness made something to measure"
must not be the same code path.

**The class map belongs to the TARGET.** The harness reads `action -> recording
class` from the target's own declaration. A record the target did not classify
fails check 2 as unclassified; the harness never guesses. That is why this tree
imports nothing from `src/` and why EP-25's mount, and the in-kernel module after
it, can be judged by the same instrument without either being rebuilt for it.

**A record is judged on the act it COVERS, never on the step it landed in**
(design/10 §11.4a). A governed target does not append in the step that caused the
act: a folded write's covering decision arrives at the flush boundary its policy
names, so bracketing each step failed the write row for holding nothing and the
fsync row for holding a DECISION fsync never made — one fold, two failures, in
opposite directions. So check 2 reads the row's whole window and asks what each
record is ABOUT. The answer comes from a second target-declared map alongside the
class map: `covers_map`, `action -> the acts that kind covers`. The class map says
what a record IS; this says what it is ABOUT; both are the target's vocabulary and
the harness authors neither. An empty list declares a kind about no act any caller
made (the port's own bookkeeping); `"*"` declares a kind that names its own act in
its payload, which is the shape of a gate refusal. What the ROW drove is the
harness's own knowledge: the row says which call is under test, and `probe.PERFORMS`
says what each vocabulary entry performs — deliberately generous, because a missing
entry there turns a legitimate record into a false finding while a spare one costs
only detection power.

A governed target that exposes a record and declares no covers map is REFUSED, not
judged by landing point as a fallback. Three consequences are worth knowing before
you read a figure: a record about an act the row only set up is excluded with a
note and judged on that act's own row; a record about an act the row never
performed FAILS; and a spurious record covering an act the row did legitimately
drive is no longer separable from the real one — which is sound only because every
covered act has a row of its own, so nothing goes unjudged, it is judged where it
belongs. The window's boundary is the last step's bracket, so a record landing
after it is outside — `files.close` is the row where that shows, and it is raised
as a finding about the row's evidence rule rather than quietly widened away.

**External test programs are workload, never the judge.** Adopting an existing
kernel or filesystem suite as the oracle is the refused reference: it checks the
ABI leg and knows nothing of the five recording classes or of replay, which are
exactly what makes a swap a GOVERNED swap. A third-party program may be driven
under the harness as an ABI exerciser, named as such. Its pass line is never the
acceptance.

## The honest boundary, today

Checks 2 and 3 have run against the EP-25 mount, subject established, and the
figures are in `planning/vm/CONFORMANCE-BASELINE-EVIDENCE.md` §2. Every figure
taken before that subject check existed is uncitable, including figures already in
the build log (design/10 §11.2b states the cost once).

Two limits stated rather than assumed away. The scratch lifecycle is established
for LOCAL transports only; an ssh target makes a fresh uuid-named directory on the
target per run and addresses no mountpoint of this host's, and the subject check
refuses such a target rather than reporting on a subject it cannot establish. And
the subject check binds `verify`; a stock `capture` has no governed subject to
establish, so it keeps the scratch half and not the first half.

Of the 102 compiled files-group rows, 40 are driven by their own probe, 28 more
are driven inside a primary's step list, and 34 are not driven at all — each of
those with a written reason. Eight primaries are marked DISPUTED, where faithful
mechanization needs a judgment design/10 does not settle; the map's words are
encoded as written and the question is raised, never resolved here.
