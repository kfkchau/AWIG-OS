<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture (seL4/POSIX/OS-textbook) · Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature (kernel, syscall, capability, permission, memory protection). NON-GOAL: no offensive capability of any kind; defines record, gate, view, and kernel-conformance only. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=CANON status=LIVE supersedes=- superseded-by=- verified=2026-09-02 REVISED-PRE-LAUNCH-25 -->
# GOV-OS — Campaign 4: PROOF — cryptographic closure

**Status:** v1 DRAFT, 2026-07-25, written at the owner's commission by the
C3/C4 paper-author session (the seat separate from the sitting mentor), tier
xhigh. **Resolution device, stated up front:** campaign 3 has not run, so this
paper is written under design/32's honesty rule — it binds DIRECTION now; its
EP files are authored at C4 launch; and it is re-priced at the C3 close
(design/32 standing rule 4), exactly as the C2 close re-priced the horizon.
Where a C4 decision depends on a custody surface C3 has not yet built, that
dependence is named in place, never guessed through. Gates: GATE 1 (shape)
and GATE 4 (the invariant→test→EP table, §8b) are carried in this paper;
GATE 2 (two pressure-test passes) is §10; GATE 3 (the owner's ruling) is
OPEN — the ruling list is §11. The sitting mentor reviews against the four
gates before anything dispatches. Owner rulings control. Citations by
doc-number + section. Labels per 00-READ-FIRST §6.

**[PRE-LAUNCH REVISION, 2026-09-02, the architect's hand on the owner's "go
all" — a DATED BLOCK, not a rewrite; every figure below was driven this day
and the board outranks all of it. READ THIS BEFORE §5, because §5's sketch
predates everything here.]**

**1. CAMPAIGN 3 IS CLOSING ON A FULLY-ASSUMED PORT.** Files (EP-25), memory
(EP-31, :2666) and scheduling (EP-32, :2681) are record-governed; the owner
flipped the last real-time assume himself on the measured margin ("flip
yes", :2685, ~1 µs per governed RT decision recording nothing, ~86×/866×
headroom). EP-33A (the fix-pack, countersigned :2686) and EP-33B (the review,
countersigned :2691, grading K1–K12) close the campaign and STOP AT THE
OWNER'S SIGNATURE. This paper's launch re-pricing follows that signature.

**2. C4 NOW CARRIES MORE THAN §5 SKETCHES — all owner-ruled 2026-09-02, all
recorded as schedule-data blocks at this file's END, all entering the plan
list at launch, priced then:** (a) THE IDENTITY SUBSYSTEM (design/43 — layered
identity, occupancy and permission on the Venn2 frame geometry, boundary
classes, act-in-capacity; universal, therefore engine territory, built once
here and consumed by every estate; its D1 must be ruled before schema work);
(b) THE HARDWARE GENESIS ANCHOR (three tiers, sizes driven: anchor ~100 B →
TPM; pack xz 35 KB → UEFI; full seed xz 203 KB → SPI; constitutional
attestation as the new primitive); (c) THE RECOVER CEREMONY (chain-adjudicated
healing, owner-gated splice, never automatic); (d) PERSISTED CHECKPOINT VIEWS
(provenance-verified caches, record always wins); (e) CROSS-ATTESTED VIEW
CHECKPOINTS (Merkle-shaped, damage localizes) under the recovery-capacity law.
**Their common character, which is now C4's:** replace every remaining act of
faith in the system with a check. **Expect the launch re-pricing to CUT** —
scope has grown since this paper was written and the re-pricing exists to say
so.

**3. TWO STANDING CONSTRAINTS BIND EVERY C4 EP, minted after this paper:**
the DISTRIBUTION RIDER (the charter's two-track ruling: nothing built here may
foreclose federation — node identity expressible, timestamps honest, no
alone-forever assumption; pre-addressed, never built early) and the §5
KIND-GATE as always (any new check kind or vocabulary member is the owner's
word; the K2 lesson stands).

**4. FORWARD OBLIGATIONS C4 INHERITS FROM THE C3 CLOSE, none of them C4's to
resolve on its own authority:** EIGHT HELD FAMILY-LAW CREATES (MEM-LAW-ALLOC/
EVICT/PROTECT, SCHED-LAW-ADMIT/HALT/KILL-CHAIN/ORDER/PRIORITY) awaiting one
batched owner word — created at their wiring units when it lands; the
connection retirement DEFERRED by ruling (:2646) against a governed connection
view that CAMPAIGN 5 — NETWORKING, owner-ruled 2026-09-02, seed design/44 —
will build; the held engine findings unchanged (R-A, R-B, R-D engine-wide,
R-E, :2587, the custody dead-citation).

**5. WHAT FOLLOWS C4 (owner-ruled shape, papers unwritten):** C5 networking
(one-machine, design/44), then distribution (beyond-one-machine, its own
track, spikes first), then self-hosting. This paper's attestation primitive is
what distribution will need first; its anchor tier is self-hosting's first
brick. Build accordingly: nothing in C4 should assume it is the last campaign
on this machine.

---

## 1. Sources

The ruled horizon — design/32 §2 (Q1–Q5, resolution MEDIUM, with its honest
caps: algorithms are calibrations; key custody is a human ceremony; a
compromised root key is C2's succession problem in cryptographic form) and
the 2026-07-25 re-pricing (RULED: DEPTH inherits the caller-asserted cap and
builds TOWARD this campaign's closure — this paper is that closure). The
"signing later" annotations across the estate: design/28 §I11 (the guarantee
is cannot-do-lawfully and cannot-do-quietly, NOT cannot-do-on-disk;
hand-editing made detectable by the mirror now, cryptographic signing later)
and design/28 §7's EP-09 annotation (blindness of computation delivered;
physical separation deferred to the signing campaign, where key separation
makes it real). The campaign-2 close: DIGEST-C2 (theorems 7–12; J1 —
verification bottoms out at the founding; succession live with the chain-end
derived; the vault's closure — verify-never-reveal, an absent read op, not a
cipher), R20-2 (the caller-asserted identity cap, owner-ruled to ride to
THIS campaign as the documented boundary), and the V3 re-home question
(verification onto VERIFY-SECRET — rides to C4 by name; challenge-response
primitives arrive here). The two-times law — design/35 (owner-ruled), whose
§6 names the one direction of the deciding-time claim that closes ONLY with
signing. The seal — design/34, RULED adopted, whose §5 names canonical
serialization as TCB-grade discipline. The campaign-3 launch paper —
design/36 (K1–K11; the crossing; the overturn-reach specification; EP-20B +
EP-21..33 — this campaign's numbering continues after it). Wire-at-birth,
carried verbatim (DIGEST-C2 §8). Capacity — design/23 Option C (GS-13 as
compliance's lever; pre-erasure replay reproduces the redacted state).
DOC-GOVERNANCE §3 (erasure is owner-only, ceremonial, and leaves a recorded
scar — the doc estate already lives the GS-13 shape). The version ladder —
design/33 (v0.7 "the sealed kernel": every guarantee upgrades to
cannot-do-undetectably, even on disk). Machine evidence: suite 474 green at
the C2 close; founding v1.6.1; v0.2 official. D4 (sha256 as the current
hash, a reversible calibration — the precedent that algorithms are values,
not law).

## 2. The essence (one paragraph, functional)

Campaign 4 upgrades every guarantee the estate makes from cannot-do-lawfully
and cannot-do-quietly to **cannot-do-undetectably, even on disk**. Today an
alteration of the record file is caught by cross-check — the audit mirror,
replay divergence; after this campaign it is caught by derivation: every new
record carries a hash chaining it to its predecessor, the whole pre-existing
record is sealed under one anchor so the past becomes edit-evident
retroactively, every act arrives signed by a key bound to its account so the
gate stops trusting the caller's word about who is acting (the R20-2
boundary, carried by name since campaign 2, closes here), the store
countersigns what it appends so a decision's claimed deciding time is
bracketed by proof, the two audit streams gain genuinely separate keys, the
engine can cite its own attested digest, and destruction exists only as its
own owner-ceremony that leaves a signed shell proving what was destroyed and
under whose authority without revealing a byte of it. Nothing about the
machine's meaning changes — the record was always the truth; this campaign
makes the truth checkable by arithmetic instead of by trust in the box it
sits on.

## 3. End-state invariants (the campaign is done when ALL hold)

Q1–Q5 carry from design/32 §2, re-derived at full resolution; Q6–Q10 are
this paper's extensions from what campaign 2, design/35, and the campaign-3
paper ruled. SOURCE-DERIVED throughout, cited inline; testability pointers
name §8 battery rows.

- **Q1 — The chained record.** Each record appended after the sealing
  founding carries a store-minted hash of its predecessor; an edit of any
  sealed byte-of-meaning breaks the chain at a provable point. The
  pre-existing record is sealed by ONE anchor record carrying the canonical
  hash of the entire unsigned prefix — history before this campaign becomes
  edit-evident retroactively at the anchor moment, without touching a single
  old record (append-only absolute). What is hashed is the record's
  CANONICAL content, not file accidents: a re-encoding that changes no
  canonical content is not an alteration, and the canonicalization battery
  is what makes that line exact. The chain prices at append rate, which I9
  already bounds — hot paths never hash anything. Envelope note, raised not
  assumed: chain and signature fields are store-minted additions on NEW
  records (the same class as seq/record_time, minted at append); the I1
  exception this needs is the owner's word (§11 item 2).
  → T-CHAIN-HOLDS, T-CHAIN-LOCATES, T-PREFIX-ANCHORED, T-SEAL-RATE.
- **Q2 — Signed acts.** Every act by a key-bound account arrives with the
  invoker's signature over (the draft, its deciding time, its seal where one
  exists); the store's countersignature covers the appended envelope. The
  two signatures carry the two times: the actor's binds the DECIDING claim
  to the key's holder — it cannot move to anyone else and cannot be altered
  after the fact; the store's binds the RECORDING fact. The invoker/actor
  split stands: acts lawfully performed as SYSTEM still carry the invoking
  account's signature in provenance; SYSTEM's own acts (the executor, the
  mirror, the sweep) sign with the system key. → T-SIGNED-DOOR,
  T-CANONICAL-ONE-HASH.
- **Q3 — The engine attests itself.** Boot appends an attestation record
  citing the digest of the engine artifact set that is running, so "which
  engine processed these records" is a citable, replayable fact and
  T-NO-LAW-IN-CODE gains its integrity twin (the shared-digest-function cap
  from the EP-09 review closes: the digest machinery itself is among the
  attested artifacts). What self-attestation on one machine can and cannot
  prove is stated in §9, not implied away. → T-ENGINE-ATTESTS.
- **Q4 — The blind streams are separately keyed.** The EP-09 deferral lands:
  each audit stream signs with its own key; holding one stream's key cannot
  produce the other's signatures; the third-view cross-check is unchanged.
  Blindness of computation (proven in campaign 1) plus key separation is
  what turns one-disk-one-process separation from theatre into a checkable
  property — real exactly to the degree the two keys' CUSTODY is separate,
  which is a deployment choice named in §9. → T-STREAMS-TWO-KEYS.
- **Q5 — GS-13, the one true destruction.** Erasure exists nowhere except as
  its own recorded, owner-only ceremony. The ceremony destroys CONTENT (blob
  bytes), never records; it appends a signed shell proving what was
  destroyed (by hash), under whose authority, when, citing which retention
  rule — revealing nothing (the CONST-SECRETS shape applied to deletion).
  Replay before the erasure point reproduces the redacted state
  (design/23 Option C); the scar is permanent and derivable.
  → T-SHELL-PROVES.
- **Q6 — Identity closes (the R20-2 boundary retires).** For a key-bound
  account, the gate accepts no act without a valid signature from a bound,
  then-valid key: the caller-asserted actor string — campaign 1's honest
  cap, campaign 2's measured boundary, campaign 3's named inheritance —
  retires at the cryptographic door. The flip is per-account and lawful,
  never a flag day: binding a key IS the narrowing act (an account with a
  bound key can no longer act unsigned; an account without one continues
  under the openness grant until the owner narrows) — the EP-17 transition
  lesson applied to signing: one law, visible, no dual-mode gate. Root
  identity keeps its founding shape: the root key is founding-asserted at
  the sealing ceremony — nothing sits above it to verify it against, the
  same self-aware limitation J1 already states for root identity itself.
  → T-SIGNED-DOOR, T-KEY-FLIP-PER-ACCOUNT, the sealed-world matrix.
- **Q7 — The two times become provable.** design/35 §6's open direction
  closes: a claimed deciding time is BRACKETED — it cannot predate the world
  its own pack hash pins (the seal's floor, already law), and it cannot
  postdate the store's countersigned arrival (this campaign's ceiling).
  Within the bracket the time remains the signer's assertion — stated, not
  hidden (§9). Key validity is judged in the legitimacy frame: a signature
  made while its key was bound remains sound evidence of who decided, even
  if the key was later superseded — while the actor's AUTHORITY stays
  evaluated live at effect time, exactly the K7 split. And a key revocation
  whose deciding time precedes already-accepted acts is law-family arriving
  late: it rides the campaign-3 reconciliation sweep unchanged — the
  affected acceptances are re-adjudicated and overturned by the §4b
  machinery of design/36, with nothing new invented (derive, don't add).
  → T-DECIDING-BRACKET, T-KEY-VALIDITY-AS-OF-DECIDING, T-REVOCATION-SWEEPS.
- **Q8 — Every key arrives with its leash.** Key binding, rotation, and
  revocation are recorded acts; rotation and revocation are supersessions
  evaluated live (nothing cascades because nothing downstream was stored —
  theorem 7 applied to keys). The root key's rotation or revocation could
  orphan or move root authority, so those ops wire into the anchor guard AT
  BIRTH (wire-at-birth, carried verbatim): no root key retires without a
  successor key bound through the recorded, human-only succession ceremony
  — CONST-AUTHORITY-ANCHORED in cryptographic form. → T-ROOT-KEY-ANCHORED,
  T-ROTATE-SUPERSEDES.
- **Q9 — Erasable content is blob-homed by construction.** Records are never
  erased, so anything a retention rule could ever reach must live as
  content-addressed blob bytes referenced by hash — never inline in a
  record. This is a placement LAW with a mint-time guard: content of an
  erasable class submitted inline refuses, citing the placement rule.
  Without it, Q5 and Q1 collide (erasing an inline payload would break the
  chain); with it, they compose (the bytes die, the hash and the shell
  remain, the chain never notices). One corollary proven, not assumed:
  GS-13 can never orphan authority, because authority is derived from
  records and records are untouchable by the ceremony.
  → T-ERASABLE-IS-BLOB.
- **Q10 — Campaigns 1–3 survive sealing.** Every I-, J-, and K-invariant
  holds with the sealed machinery loaded. Signatures and chain fields are
  RECORD (data written at append, replayed as data); their verification is
  DERIVED (recomputed on demand); replay therefore verifies every signature
  and every link but re-signs nothing and re-runs no signer — the
  frozen-answer law applied to the campaign's own cryptography. The vault
  stays closed: no read path enters with this campaign (cryptographic
  machinery is exactly the place "let's decrypt it" drift would arrive —
  refused by name). → T-TOTAL-ROUNDTRIP-4, T-VAULT-STILL-CLOSED, the full
  probe ledger at EP-42.

## 4. New record kinds and vocabulary (all in the ONE stream, class-tagged)

| payload.kind | Class | What it founds |
|---|---|---|
| key-bind | LAW | a verification anchor: account ↔ public key, bound at a recorded ceremony; binding is also the per-account enforcement flip (Q6) |
| key-rotate / key-revoke | DECISION | supersession of a binding, evaluated live; root-key cases anchor-wired at birth (Q8); revocation is law-family for the sweep (Q7) |
| chain-anchor | DECISION (SYSTEM, once) | the sealing of the unsigned prefix: the canonical hash of everything before the chain begins (Q1) |
| attestation | DECISION (SYSTEM, at boot) | the running engine's artifact digest set, citing BOOT-INT (Q3) |
| erasure-shell | DECISION (owner ceremony) | the signed scar: what was destroyed (hash), whose authority, when, which retention rule — content absent (Q5) |

What deliberately does NOT enter (minimality gate):

- **Envelope fields, not kinds:** prev-hash and the two signatures are
  store-minted envelope additions on new records — the owner's I1 word
  (§11 item 2), a grow-only addition, never a migration of old records.
- **No certificate tree, no trust store:** a key binds by a recorded act in
  the one store; verification bottoms out at the founding, not at an
  authority above it; revocation is supersession read live from the record
  — the record IS the distribution.
- **Algorithms are calibration values,** not vocabulary: the hash and
  signature algorithm identifiers ride a recorded configuration with a
  named owner (the D4 precedent — sha256 today, replaceable by amendment);
  agility is the ordinary amendment path, and every sealed record names the
  algorithm it was sealed under so a future change never orphans old proofs.
- **The canonical serializer is engine surface** (S-plane), shared with the
  design/34 seal — one serializer, one fuzz battery, two consumers; a
  second serializer anywhere is a defect by construction.

## 5. The EP sketch (numbering continues after design/36's EP-33; sizes and tiers PROPOSED, Estimate — Medium at this distance; every EP file authored at C4 launch, after the C3-close re-pricing)

- **EP-34 — The canonical floor.** M, xhigh. Depends: C4 launch. The one
  canonical serializer promoted to TCB discipline (design/34 §5), its fuzz
  battery (key order, encoding normalization, numeric form — one state one
  hash, never two), and the crypto calibration pack (algorithm identifiers
  as recorded, owner-gated values). Everything above stands on this; a wrong
  canonicalization silently manufactures false mismatches or false holds,
  which is why the tier is not inflated — it is earned.
  Wrong reference (named for the EP file): "just use the JSON dump" — the
  ambient serializer as the canonical form. Taking it erases the exactness
  of the alteration line (Q1's edit-evidence is only as sharp as the
  canonical form) and imports invisible platform variance.
- **EP-35 — The chain and the anchor.** M, xhigh. Depends: EP-34, the
  envelope ruling (§11 item 2). Store-minted prev-hash on new records; the
  chain-anchor sealing the unsigned prefix; chain verification as a derived
  standing check and a committed probe; replay verifies every link and
  mints none.
- **EP-36 — Keys and ceremonies.** L, xhigh. Depends: EP-34. The key-bind /
  rotate / revoke family; the system key held in vault-class custody
  (written at ceremony, used by the store, NO read path — the vault's
  intended-consumer derivation, now for the store's own signing); the root
  key founding-asserted at the sealing ceremony; root rotate/revoke
  anchor-wired at birth; succession gains the key half of its ceremony
  (human-only stands). The V3 re-home question REOPENS here by name
  (verification onto VERIFY-SECRET — challenge-response primitives now
  exist): raised at this EP, one word (§11 item 5).
- **EP-37 — The signed door. THE CAMPAIGN CRUX.** L, xhigh. Depends: EP-35,
  EP-36. The gate's acceptance requires, for key-bound accounts, a valid
  signature from a then-valid bound key; R20-2 closes; the per-account flip
  rides key-bind (Q6); the authorization matrix gains the signature columns
  (valid / absent / wrong key / superseded key / key bound after the act's
  deciding time), each proven able to fail. Strictly-stronger obligation
  (the EP-17 law, verbatim): the old ledger cannot contain cases in the
  signature dimension it could not express — the retirement of the
  caller-asserted acceptance is licensed only by the proof on the EXTENDED
  ledger, both failure directions (too weak: an unsigned act by a keyed
  account still lands; too wedged: an unkeyed account's lawful work stops).
  **THE WRONG REFERENCE THIS CAMPAIGN EXISTS TO REFUSE — the blockchain,
  and its quieter sibling, the PKI hierarchy.** The loud template: chains
  mean consensus, distributed replicas, proof-of-work, tokens. Taking it
  erases the sovereignty the estate is built on (ONE store, one appender,
  order already law — there is no consensus problem here) and imports
  federation concerns that belong to campaign 6. The quiet template, the
  one that will actually fire at this EP: certificate authorities, trust
  stores, session tokens — identity as a tree of authorities above the
  system. Taking it erases J1 (verification bottoms out at the FOUNDING,
  not at a root CA), stores trust state outside the record, and re-invents
  revocation distribution when the record already IS the one place
  revocation is read live. The right derivation: a hash chain and
  signatures over a single sovereign append-only store — the accounting
  and version-control shape, not the cryptocurrency shape; keys bound by
  recorded acts, validity a fold, the complement computed.
- **EP-38 — The two-times closure.** M, xhigh. Depends: EP-37, and
  campaign 3's EP-26 machinery (the sweep). The deciding-time bracket
  enforced at acceptance (pack-hash floor, countersignature ceiling);
  key-validity-as-of-deciding-time; a late-deciding revocation rides the
  design/36 §4b sweep unchanged — the acceptance records it reaches are
  re-adjudicated and overturned by the existing machinery, nothing new.
  Wrong reference: "revocation invalidates retroactively" — voiding every
  past signature of a superseded key. Taking it erases the two frames: a
  signature made under a then-valid key is sound evidence forever; what
  the sweep re-adjudicates is acceptances inside the revocation's reach,
  never the arithmetic of who signed.
- **EP-39 — Two streams, two keys.** M, high. Depends: EP-36. Per-stream
  signing keys with separate custody seams; the third-view cross-check
  unchanged; the physical-separation deferral from EP-09 lands to exactly
  the depth key custody makes real (§9 names the deployment boundary).
- **EP-40 — Engine attestation.** M, high. Depends: EP-34. The boot
  attestation record; the T-NO-LAW-IN-CODE integrity twin; the artifact
  digest discipline (what is in the attested set is enumerated, like K5's
  residence audit).
- **EP-41 — GS-13, the destruction ceremony.** L, xhigh. Depends: EP-35,
  EP-36. The owner-only ceremony op; the signed erasure-shell; the
  blob-homing placement law with its mint guard (Q9); pre/post replay
  semantics (redacted state reproduces); the scar view. Wrong reference:
  crypto-shredding — destroy a key and call the data gone. Taking it
  erases the shell (nothing proves WHAT died under WHOSE authority), turns
  destruction into cipher management, and leaves the bytes in place
  betting on the cipher forever; GS-13 destroys the bytes and keeps the
  proof, which is the opposite trade and the ruled one.
- **EP-42 — Campaign review.** L, xhigh (+ultracode per precedent).
  Depends: all. Two-pass + second-reading; the full probe ledger including
  the campaign-3 additions; the sealed-world matrix with every column
  proven able to fail; T-TOTAL-ROUNDTRIP-4; the vault-still-closed check;
  the paper graded against what held.

## 6. The deferred-to-live ledger (every flip and retirement; strictly-stronger obligations stated)

1. **R20-2 CLOSES** (EP-37): the caller-asserted actor retires at the
   cryptographic door for key-bound accounts. The retirement is licensed
   only by the strictly-stronger proof on the ledger EXTENDED into the
   signature dimension (the EP-17 law), both failure directions tested.
2. **design/35 §6's open direction CLOSES** (EP-38): the deciding-time
   claim gains its ceiling (countersigned arrival) to pair with its floor
   (the pack hash). The residual assertion inside the bracket is a named
   cap (§9), not a silent one.
3. **The EP-09 physical-separation deferral LANDS** (EP-39), to the depth
   key custody makes real; the shared-digest-function cap closes (EP-40:
   the digest machinery is inside the attested set).
4. **"Detectable by the mirror now, signing later" annotations across the
   estate are swept** at the campaign close (design/28 §I11 and kin): the
   promise those lines defer lands here, and the stale-reference law
   requires the sweep the same turn the last EP is accepted.
5. **The V3 re-home question REOPENS by name** (EP-36): verification
   consuming VERIFY-SECRET, parked at the C2 close until challenge-response
   primitives arrive — they arrive here. Raised, one word (§11 item 5).
6. **Explicitly NOT flipped** (guard against helpful drift): the vault
   gains NO read path — its guarantee stays an absent operation, not a
   cipher (the campaign most tempted to break this is this one); the
   openness grant stays untouched (narrowing remains the pilot's recorded
   act); S5 multi-writer stays deferred (the chain is per-store and minted
   at the single appender; campaign 6 consumes these primitives for
   transport authentication — F1 — it is not built here); GS-13 remains
   owner-only and ceremonial (never an automatic capacity lever —
   design/23's division stands).

## 7. What flips ride which campaign boundary (placement, per the brief's discipline)

C4 launches after the C3 close and its re-pricing (standing rule 4); the
order C3→C4 is the ruled default (signing wants to know the final custody
surfaces it seals — design/32 §0), and the swap remains one owner word. If
the owner ever swaps, EP-38 loses its EP-26 dependency and its sweep clause
is re-derived — named now so a swap is priced, not discovered.

## 8. The acceptance battery (named before any code; battery-level names)

T-CHAIN-HOLDS (an edited byte-of-meaning in a sealed test store is detected
by derivation) · T-CHAIN-LOCATES (detection names the exact record where the
chain breaks) · T-PREFIX-ANCHORED (an edit anywhere in the pre-seal prefix
breaks the anchor) · T-CANONICAL-ONE-HASH (the fuzz set: one state never
two hashes, two states never one) · T-SEAL-RATE (sealing cost rides append
rate; hot paths unchanged — measured) · T-SIGNED-DOOR (keyed account:
unsigned refuses, valid passes, wrong key refuses, superseded key refuses
forward) · T-KEY-FLIP-PER-ACCOUNT (binding flips enforcement for that
account alone; unkeyed accounts unaffected — no wedge) ·
T-ROOT-KEY-ANCHORED (root rotate/revoke without a bound successor key
refuses, citing the anchor) · T-ROTATE-SUPERSEDES (rotation is supersession;
nothing cascades; old signatures remain verifiable) ·
T-KEY-VALIDITY-AS-OF-DECIDING (a signature under a then-valid key stands;
authority still evaluated live at effect) · T-DECIDING-BRACKET (a claimed
deciding time outside [its pack's world, its countersigned arrival]
refuses) · T-REVOCATION-SWEEPS (a late-deciding revocation reaches its
window through the design/36 §4b sweep; overturns append; replay identical)
· T-STREAMS-TWO-KEYS (one stream's key cannot produce the other's
signatures; the cross-check view is unchanged) · T-ENGINE-ATTESTS (boot
cites the artifact digest; the T-NO-LAW-IN-CODE twin) · T-SHELL-PROVES
(post-ceremony: the shell verifies — what, whose authority, when, which
rule — content absent; asOf before the ceremony reproduces the redacted
state) · T-ERASABLE-IS-BLOB (erasable-class content submitted inline
refuses at mint, citing the placement law) · T-VAULT-STILL-CLOSED (no read
path entered with the campaign) · T-TOTAL-ROUNDTRIP-4 (kill everything
derived; replay: every link verifies, every signature verifies as recorded
data, nothing re-signs, no signer re-runs).

### 8b. The invariant → tests → EP map (GATE 4)

| Invariant | Battery rows | EPs |
|---|---|---|
| Q1 | T-CHAIN-HOLDS · T-CHAIN-LOCATES · T-PREFIX-ANCHORED · T-SEAL-RATE | 34, 35 |
| Q2 | T-SIGNED-DOOR · T-CANONICAL-ONE-HASH | 34, 36, 37 |
| Q3 | T-ENGINE-ATTESTS | 40 |
| Q4 | T-STREAMS-TWO-KEYS | 39 |
| Q5 | T-SHELL-PROVES | 41 |
| Q6 | T-SIGNED-DOOR · T-KEY-FLIP-PER-ACCOUNT · the sealed-world matrix | 36, 37, 42 |
| Q7 | T-DECIDING-BRACKET · T-KEY-VALIDITY-AS-OF-DECIDING · T-REVOCATION-SWEEPS | 38 |
| Q8 | T-ROOT-KEY-ANCHORED · T-ROTATE-SUPERSEDES | 36 |
| Q9 | T-ERASABLE-IS-BLOB | 41 |
| Q10 | T-TOTAL-ROUNDTRIP-4 · T-VAULT-STILL-CLOSED · the full probe ledger | 42 |

Every row traces to one invariant; every invariant carries at least one
row; EP files may add tests, never subtract these.

## 9. Honest caps and non-goals (named, not hidden)

- **Key custody is a human ceremony no kernel can conjure** (design/32 §2,
  carried). Who physically holds the owner key, the system key's vault
  material, and the successor key is the owner's ceremony design at EP-36 —
  the paper builds the seams, never the custody.
- **A compromised root key is the succession problem in cryptographic
  form** — stated, not solved (design/32 §2, carried verbatim). The
  containment is the anchor wiring (no root key retires without a bound
  successor) and the ceremony; the residual risk is named to any future
  pilot partner, never implied away.
- **Within the bracket, a deciding time is still the signer's assertion.**
  Signing binds the claim to the holder and freezes it; it does not make it
  true. The floor and ceiling are proof; the interior is testimony.
- **Self-attestation on one machine proves citability, not immunity.** The
  attestation record makes the engine version a checkable fact of the
  record; what the platform under it reports is the platform's word.
  Hardware roots of trust are deployment mechanism, not architecture — the
  same division the driver shim drew for physical enforcement.
- **Key separation is as real as custody separation.** On a single-owner
  box, both stream keys sit with one person; the property Q4 delivers is
  that the streams CAN have separate custodians and the checking never
  changes when they do. The deployment picks the custodians.
- **Observer-asserted facts keep a narrower cap.** After signing, an
  observation is provably from its observer and unaltered since; whether
  the sensor read the world correctly remains the sensor's word.
- **Algorithms are calibrations and they date.** Every named algorithm in
  any EP is trained knowledge (Estimate — High, dated); the law is
  agility-by-amendment with per-record algorithm citation, so a future
  migration strands no proof.
- **Signing cost at custody rate is unmeasured** — priced as a measured
  calibration exactly like the two K3 costs, taken from the C3 measurement
  ledger at launch; never resolved by sealing less (the I9 shape:
  cannot-lower-the-floor applies to the chain too).
- **Non-goals:** no encryption-at-rest (the refused reference stands — the
  guarantee is provable integrity and absent read paths, not ciphered
  storage; sight stays a computed governance answer); no consensus, no
  replicas, no tokens (campaign 6 owns transport; sovereignty is absolute);
  no narrowing of the open world; no new comparison or language machinery
  (campaign 5); no dates — gates, not a schedule.
- **What this paper excludes:** written before campaign 3 has run — Arc C
  custody surfaces it will seal are direction, not fact, and this paper
  re-prices at the C3 close (standing rule 4) before any C4 EP file is
  authored; no kernel source, no src/tests/tools were read (the author's
  channels bind); cryptographic engineering detail (key formats, parameter
  sizes) is EP-file material at launch, not paper material now.

## 10. The pressure-test record (GATE 2 — two passes, findings folded visibly)

**Pass one — the design attacked as drafted.** Six findings, all folded:

1. **The chain collided with I1** (envelope unchanged forever). A silent
   envelope extension would have violated the estate's oldest data law.
   Folded: store-minted fields on new records only, grow-only, and the I1
   exception raised to the owner as its own ruling (§11 item 2) — never
   assumed.
2. **GS-13 collided with the chain**: erasing an inline payload would break
   Q1 at the erased record. Folded: the blob-homing placement law (Q9) with
   a mint guard — the bytes die, the hash and shell remain, the chain never
   notices.
3. **A flag-day signature flip would wedge the world** (the EP-17
   transition lesson recurring). Folded: the per-account flip riding
   key-bind (Q6) — binding IS the narrowing act; no dual-mode gate.
4. **The campaign's one wire-at-birth case was findable in advance:** root
   key rotation/revocation can orphan or move root authority. Folded: Q8 —
   anchor-wired in the ops' own definitions, never a later patch.
5. **The store's own signing key had no stated custody** — an unexamined
   "the system just has a key" is exactly a stored secret with a read path.
   Folded: vault-class custody (written at ceremony, used by the store, no
   read path) — the vault's intended-consumer derivation extended to the
   store itself.
6. **Crux selection:** the loud template (blockchain) is not the one that
   fires at build time; the quiet one (PKI/CA trees, trust stores) is.
   Folded: both named in the paper at EP-37, with what each erases.

**Pass two — the semantics the first pass assumed without stating.** Six
findings, all folded:

1. **"Valid signature" as of WHEN was undefined** — revocation read naively
   would void the past (every old signature of a superseded key), or read
   loosely would never bite. Folded: the two-frames split (Q7) — signature
   validity is judged as of deciding time; authority stays live at effect;
   and a late-deciding revocation rides the campaign-3 sweep unchanged.
   This finding is the pass's best: it discovered that C4's key lifecycle
   needs NO new adjudication machinery — design/36 §4b already carries it.
2. **What the anchor hashes was ambiguous** (file bytes vs canonical
   content). File-byte hashing would flag re-encodings that change nothing
   and is hostage to storage accidents. Folded: canonical content, with the
   canonicalization battery as the exactness guarantee (Q1).
3. **Replay's relation to signatures was assumed** — a naive replay that
   re-signs would mint proofs the original world never made. Folded: Q10 —
   signatures and links are RECORD, verification is DERIVED; replay
   verifies everything and signs nothing.
4. **The bracket's two ends were conflated** — the seal's floor was already
   law (design/35 §6); only the ceiling is new here. Folded: Q7 credits the
   floor to standing law and claims only the ceiling, so the campaign's
   delta is stated exactly.
5. **Attestation circularity was unstated** — the engine attesting itself
   with its own digest function proves nothing about the platform beneath.
   Folded: §9's citability-not-immunity cap, and the digest machinery
   placed inside the attested set (closing the EP-09 shared-function cap
   rather than re-importing it).
6. **The C3-dependency of EP-38 was implicit** — if the owner ever swaps
   C3↔C4, the sweep clause has no machinery under it. Folded: §7 names the
   dependency and prices the swap, so a reorder is a decision, not a
   discovery.

**Left as owner judgment (not folded):** the §11 items — each one word.

## 11. The ruling list (GATE 3 — each item self-contained; one word answers)

1. **The paper itself.** This document becomes campaign 4's definitive
   direction: it is re-priced at the campaign-3 close, and its EP files are
   authored at C4 launch. YES = the sitting mentor's four-gate review
   proceeds; the paper binds direction. NO = name the section and this seat
   re-derives it.
2. **The envelope word.** New records gain store-minted proof fields
   (predecessor hash, the two signatures) — the same class as the sequence
   number and record time the store already mints; old records are never
   touched; the unsigned past is sealed by one anchor record. This is the
   one place the campaign needs your exception to "the envelope never
   changes." YES = grow-only proof fields enter at the sealing founding.
   NO = the chain must live outside the envelope and this seat derives that
   variant's weaker guarantee honestly.
3. **The flip shape.** Signature enforcement arrives account by account —
   binding a key is the act that ends unsigned acting for that account;
   nobody else's work changes that day. YES = per-account flip stands.
   NO = direct a single cutover and this seat prices the wedge risk.
4. **The destruction placement law.** Anything a retention rule could ever
   reach must live as hash-referenced content, never inside a record, so
   destruction can kill bytes without touching history. YES = the law and
   its mint-time refusal enter at EP-41. NO = erasure semantics for inline
   content must be re-derived (and will be weaker — stated now).
5. **A reopened rider, worded at EP-36:** whether account verification
   re-homes onto VERIFY-SECRET now that challenge-response primitives
   exist (the V3 question you parked to this campaign). Named now; your
   word due at that EP, not today.
6. **A ceremony named now, designed later:** who holds which keys — yours,
   the system's vault material, the successor's. The paper builds the
   seams; the custody design is your ceremony at EP-36. Nothing to answer
   today.
7. **Order confirmation.** C3 then C4 stands as ruled default; §7 prices
   the swap if you ever want it. Nothing to answer unless you want the
   swap.

---

*Register note: written under REPO-WRITING-GUIDE; checks are readings of
recorded law and prior proofs; tests are coverage, named before code.
Labels: the invariants and their derivations are SOURCE-DERIVED from the
cited rulings and canon; the EP decomposition, sizes, tiers, the placement
law's mint guard, and the per-account flip are PROPOSED with costs stated;
all cryptographic and Linux facts are trained knowledge (Estimate — High)
and date.*

---

## ADDENDUM A — intake for the C3-close re-pricing: what campaign 3 has already ruled or measured that this paper must fold (2026-07-31, the author seat; binds nothing — the close re-prices)

This paper re-prices at the campaign-3 close (design/32 rule 4) before its
four-gate review and any dispatch. Campaign 3 is still running its kernel arc,
but nine of its outcomes already touch this paper and are recorded here so the
re-pricing starts from a list instead of a 17-EP sweep. Each item names its
source; nothing here re-derives.

1. **The campaign claim this paper inherits was RESIZED (2026-07-31, on the
   record at the EP-32 correction).** What C3 completes is every subsystem's
   governance recorded and derived on a Linux that executes it — gov-os the
   authority, Linux the mechanism; a governance-native host kernel is a later
   horizon. The re-pricing reads every Q-invariant against the REAL custody
   surfaces (the record, the module seam, the FUSE/user-space halves), not
   against a from-scratch kernel. Close item 39's sibling-sweep result is the
   input here.
2. **The durability floor and group commit (design/36 ADDENDUM L; EP-28C).**
   The fsync floor is 71–85% of a gated act; group commit amortizes 5.6–13.5×
   with one appender and many submitters. Q1's chaining sits on that same
   append path — the re-pricing must state whether chaining is per-record or
   per-batch at the sync boundary, and what a batch means for the chain's
   verification granularity. This question did not exist when this paper was
   written.
3. **K12 binds every future design (design/36 ADDENDUM S, owner-ruled):** a
   derived answer costs its own dependencies. Chain verification, signature
   checking, and attestation reads are derived answers — each Q-invariant's
   machinery must be priced against K12 at authoring, not discovered
   at measurement.
4. **The two-times bracket has a live substrate now.** EP-26 built acceptance
   by deciding time with the seal; design/35 §6's remaining direction (a
   claimed deciding time running LATER than true) is exactly this campaign's
   signing work. The re-pricing should name EP-26's machinery as the base the
   C4 bracket extends, and check EP-38's sketch against what EP-26 actually
   built rather than what design/36 predicted.
5. **The standing-conditions discipline on published figures** (three
   conditions stand on C3's list at the item-41 ruling). Any C4 acceptance
   that cites C3 numbers inherits their conditions by name.
6. **The wake carve-out and volatile-boundary rulings (design/36 ADDENDUM K;
   EP-31/32 intakes)** bound what "every act" means at the hot paths this
   campaign wants to sign — Q2's "every act by a key-bound account" must be
   read against the fill/decision split those rulings fixed.
7. **The reading discipline this paper will be graded under (charter §A26):**
   the author seat's documented habit is triggers lowered one notch too
   concrete. The re-pricing re-reads every Q-invariant's trigger against its
   law at the same altitude, and the ARCHITECT-HANDOVER's §4 proposals (P1–P8)
   apply to this paper's re-edition if the close adopts them.
8. **Calibration from C3 (for §5's sizes and the campaign's shape):** ~45% EP
   growth mid-campaign, all measurement-driven; fix-first is now a standing
   owner rule (charter §A17); the MAX seat exists (charter §A16). The EP-34..42
   sketch should be re-priced expecting a fix-window per arc rather than
   treating the nine files as a census.
9. **Items already named C4's by earlier rulings, confirmed still riding:**
   R20-2 (the caller-asserted cap — this campaign's crux, EP-37), V3's re-home
   onto VERIFY-SECRET, deciding-timestamp signing (design/35 §6), physical
   audit-stream separation (EP-39's ground), and whatever EP-33A leaves
   explicitly to C4 — the close names that residue.

### ADDENDUM A, items 10–12 — three findings from the author seat's own re-read against the campaign's newest law (2026-07-31; same status: binds nothing, the close re-prices)

10. **Q9's guard sits one notch below Q9's law — the §A26 class, caught by
    the accumulation probe.** The law says "anything a retention rule could
    EVER reach"; the mint guard fires only on content whose erasable CLASS
    is declared at mint. The world the guard misses: a retention rule
    ARRIVING LATER, reaching content already minted inline — the record is
    frozen, the content cannot be moved out, and Q5 meets an immovable
    record exactly as pass-one finding 2 feared. The re-pricing derives the
    wider trigger: either the placement law defaults every payload interior
    that could carry reachable content to blob-homing (the campaign-1
    size-floor blob policy is the existing mechanism to widen), with inline
    reserved for structural governance fields — or the residual is stated
    honestly: content minted inline before its class was erasable is beyond
    the ceremony's reach, named to any pilot partner. One of the two; the
    current text implies the first while guarding only the second.
11. **The countersignature's moment under group commit.** Q2/Q7 predate
    EP-28C. With one `fdatasync` covering N individually-appended records
    and no reply before the covering sync, the store's countersignature —
    Q7's bracket CEILING — should attest the DURABLE record (post-sync),
    not the append: a countersignature riding the reply is automatically
    post-sync under EP-28C invariant 1, and that is the stronger and
    cheaper reading. The re-pricing states it, and states what a batch
    means for countersignature granularity (per-record signature, batch-
    covered durability — the same shape as invariant 3's barrier-over-N).
12. **The red-world law reaches the whole §8 battery** (filed after this
    paper: a passing row proves nothing until the world where it fails is
    EXHIBITED, the red world NAMES which clause it makes fail, and it must
    be unreachable by every clause that already passed). The sealed-world
    matrix's columns already say "proven able to fail"; the re-pricing
    extends that discipline to every battery row — T-CHAIN-HOLDS's red
    world in particular must fail on the CHAIN clause, not on a comparison
    an unsealed store would also catch.

### ADDENDUM A, items 13–14 — two intakes from the 28-series arc (2026-08-06, the author seat; same status: binds nothing, the close re-prices)

13. **Item 2's baseline is re-named by `design/36` ADDENDUM T:**
    concurrency alone collects most of what batching was projected to
    collect — the 5.6×/13.5× band was measured against a ONE-CALLER
    floor that no longer describes the system. Q1's chaining-cost
    projections (per-record vs per-batch at the sync boundary) are
    re-priced against the CONCURRENT width-1 baseline, and any C4 figure
    citing the band carries its baseline by name (T's own rule: a
    projected gain names the baseline it was projected against).
14. **EP-28P (what IDENTITY IS — the mutability question) sits UPSTREAM
    of this campaign's crux.** Q2 binds "every act by a key-bound
    account", and the estate's identity-of-objects question (a mutable
    user-controlled string cannot be a stable identity; owner ruling 2:
    backend ID allocation is ours) is open on the owner's word, with a
    §5-shaped gate because deciding what identity is changes what the
    record means. The re-pricing reads P's outcome — or its open state —
    before pricing anything that signs, chains, or attests over object
    identities; a C4 design inheriting an unstable identity inherits its
    collisions signed.

### ADDENDUM A, item 15 — the inhabitant architecture, OWNER-RULED (2026-08-06; this one binds as a ruling — the close prices against it, not before it)

15. **Every non-system actor — human or AI — stands OUTSIDE the machine;
    the machine is its own only trusted actor.** The ruling, in the
    owner's frame (the TWC precedent — the bank with no counter,
    extended to inhabitants; the AI lives in a glass box):
    - **Actors reach the system only through TUNNELS** — narrow, typed
      channels: a comms tunnel for a human, a code-proposal tunnel for
      an AI org in its box. **Nothing crosses a tunnel.** The system
      READS a proposal and RECITES the act itself through its ordinary
      gate — the proposal is recorded INPUT; the proposer's bytes never
      execute. Recitation stops smuggling; the gate stops unlawful
      acts; both walls are required and neither substitutes for the
      other.
    - **Identity is TUNNEL identity** — issued by the structure, never
      claimed by the actor, never reused: a destroyed box's successor
      gets a NEW identity (EP-28P's rename-recreate family at the
      actor layer).
    - **Permission attaches to the TUNNEL.** The gate matches the
      recited act's demand against the tunnel's rights and recites only
      if the tunnel holds them. An AI tunnel's rights are COMPUTED
      strictly below the associated user's, minus a floor that is
      SYSTEM LAW and not user-waivable: no destruction of the
      associated account; no handing-over of the user's authority (the
      ban binds the USER — a waivable floor ends on one persuasive
      week); material change to another person only on a live human
      click, ONE act per click, never automatable (convenience attacks
      the click before anything else does — no batch approval).
    - **The containing structure lies on no tunnel's path.** Not
      refused — absent.
    - Consequences this paper folds: **(a)** Q2's "every act by a
      key-bound account" gains its actor model — the key binds a
      tunnel; **(b)** the crux proof's load class is machine-rate
      tunnels (one user, many parallel instances — the user cloning
      themselves); **(c)** a future component exists at the tunnel
      mouth — the RECITER, the only component that ever reads AI
      output — and no C4 design may foreclose it; **(d)** an
      externally hosted model makes the tunnel's OUTWARD face a
      disclosure surface (what the dashboard shows the AI is shown to
      the model's host) — noted, not ruled; a locally hosted model
      carries no such surface.

---

**[SCHEDULE DATA, 2026-09-02, the architect's hand, the owner's word
first-party in the architect's chat ("that c4 then"): THE IDENTITY
SUBSYSTEM IS ASSIGNED TO THIS CAMPAIGN.** Seed: design/43
(RULE-USER-IDENTITY-AND-PERMISSION — layered identity master⊃session,
occupancy and permission derivation on the Venn2 frame geometry, boundary
classes, act-in-capacity). It enters C4's plan list when this campaign
authors its EP files — as its own arc or unit rows, sized at that
re-pricing, every new kind or vocabulary member through the design/28 §5
gate as always; design/43's D1 (the master↔session formal home) must be
ruled before its schema work. The universality ruling behind the
placement: identity/occupancy/permission is ENGINE territory — built once
here, consumed by every estate; TWC's tier/scope machinery meanwhile runs
as a DECLARED SCAFFOLD replaced by this subsystem (the first-customer
pattern). This block is schedule data of record, not plan detail — the
WHAT and sizing land at C4 authoring.]**

---

**[SCHEDULE DATA, 2026-09-02, the architect's hand, the owner's word
first-party in the architect's chat ("should we add this genesis in bios +
damage hash match recover thingy in plan then?" — archi recommended yes,
owner's framing adopted): TWO FURTHER C4-ORBIT ITEMS, entering the plan
list at C4 authoring, priced at the launch re-pricing like everything
here.**

**(1) THE HARDWARE GENESIS ANCHOR — three tiers, driven sizes 2026-09-02:**
the anchor (genesis hash + signing pubkey, ~100 bytes → TPM NV with
write-lock, works everywhere); the constitution itself (pack xz ~35 KB →
UEFI variable store, board-dependent, with care); the full seed (engine +
pack + battery, xz ~203 KB → SPI flash free region / coreboot, custom
territory). Boot verifies the pack against the chip before trusting it —
closes the "founding is as good as the pack file at install time" cap —
and TPM attestation over the genesis hash gives CONSTITUTIONAL
ATTESTATION: a deployment proves its rulebook to a stranger, the primitive
the beyond-one-machine track will need. AUTHENTICATED, not encrypted —
the constitution is law, not secret; what must be impossible is silent
replacement. Caps: firmware is hard-not-impossible to write; the seed-in-
flash is a recovery ARTIFACT, not capability (needs a runtime — self-
hosting territory); hardware tiers beyond TPM/UEFI are per-board work.

**(2) THE RECOVER CEREMONY — destruction's mirror twin:** damaged record
segments healed by candidates gathered from replicas / the firmware copy /
full-fidelity projections, ACCEPTED ONLY BY THE CHAIN (a candidate
rehashes into the sealed chain or it is refused), and SPLICED only by an
owner-gated recorded act — a signed splice proving what was restored, from
which sources, against which anchor. NEVER automatic, views NEVER
authoritative (an auto-repair door is a laundering door; a view-driven
repair inverts the truth hierarchy). Lossy views cannot reconstruct — a
sum cannot recover its addends (§A51's own logic) — so recovery coverage
is a design property of which full-fidelity projections exist, stated
honestly per subsystem. Depends on the chain/seal this campaign builds;
composes with (1).]**

---

**[SCHEDULE DATA, 2026-09-02, the architect's hand, the owner's design
first-party in the architect's chat: PERSISTED CHECKPOINT VIEWS — a third
C4-orbit item.** Lower view levels MAY persist to disk for boot/read
efficiency AS DECLARED CACHES WITH PROVENANCE, never a second truth: each
carries (seq N folded to · record chain-head hash at N · own content hash);
boot verifies PROVENANCE not derivation — content hash, then chain-head at
N against the record's chain (O(1) on C4's chain, which is why this rides
C4), then folds only N+1→head via the engine's existing catch-up machinery.
Naive verify-by-recompute is named and refused: it costs what it saves.
Determinism is trusted because it is TESTED (delete-and-replay-identical is
a standing conformance row) and WATCHED (scheduled spot-audit recomputes
one view in full and compares). THE RECORD ALWAYS WINS: any mismatch =
silent rebuild + a RECORDED integrity observation; the view→record
direction stays closed (the recovery ruling's laundering-door logic).
Write at shutdown AND periodically at runtime (crash degrades gracefully
to an older checkpoint, never to wrongness); verification happens AT LOAD.
Which views persist is a PER-VIEW DECLARATION by measured recompute cost
(the owner's three-level default as starting policy). The (seq, chain-head)
pair is the cache's own §A51 population-and-basis statement. Priced at C4
authoring with the other orbit items.]**

**[ADDENDUM TO THE RECOVER + CHECKPOINT-VIEWS ITEMS, 2026-09-02, the
owner's insight first-party (his fanqie analogy — the rime-book method
where no sound is defined absolutely and every pronunciation exists only
as relations to others, a system whose relational redundancy let Middle
Chinese phonology be RECOVERED centuries after every actual sound was
lost, re-anchored via living dialects): THE RECOVERY-CAPACITY LAW —
recovery capacity = CONTENT redundancy × RELATIONAL redundancy. Relations
ADJUDICATE (localize damage, constrain the missing piece's shape, verify
candidates); anchors SUPPLY (replicas, firmware copy, full-fidelity views
— the living dialects). Neither alone recovers. CONCRETE EXTENSION filed
with it: view checkpoints CROSS-ATTEST — a parent view's checkpoint
carries its sub-views' checkpoint hashes, Merkle-shaped down the
hierarchy, so verification failure LOCALIZES to the diverging subtree
instead of merely failing. Cheap (hashes only); gives the master-view
ruling a recovery function for free. Priced with the parent items at C4
authoring.]**

---

**[AS-BUILT / SCHEDULE CONFIRMATION, 2026-09-03, the architect's hand: THE
RECOVERY FAMILY HAS ITS EP NUMBERS.** The ARC R plan list minted at the EP-41
authoring sitting (planning/exec/ARC-R-PLAN-LIST.md) is CONFIRMED and absorbed:
**EP-43 — the recover ceremony** (chain-adjudicated, owner-gated splice; L/xhigh;
depends EP-35, EP-36, EP-41) · **EP-44 — persisted checkpoint views** (provenance
triplet, O(1) head check on this campaign's chain; M/high; depends EP-35, EP-40) ·
**EP-45 — cross-attested checkpoints under the recovery-capacity law** (Merkle-
shaped, damage localizes; M/xhigh; depends EP-43, EP-44). The recovery-capacity
law is an owner-gated founding create joining the batch WHEN EP-45 AUTHORS. NO
EP-46: ARC R folds into EP-42's campaign review (one review per campaign, ruled
at the EP-41 countersign). These numbers answer the owner's question of this
date ("which EP is dat"); the schedule-data blocks above remain the design's
substance — this block only gives them their coordinates.]**

---

**[AS-BUILT / ORBIT POINTER, 2026-09-04, the architect's hand: ITEM 4 IS
RULED AND ITS FAMILY HAS ITS PAPER — design/46-CUSTODY-CONSERVATION.md
(provenance D01/D02, board :2856 and the owner's word of this date). The
destruction orbit above is SUPERSEDED IN ONE RESPECT: there is no delete
function — the vocabulary never contains one (constitutional-class); the one
removal function is the VERIFIED HANDOVER (custody transfer with signed
receipt), and the scar is a DEPARTURE record. EP-41A re-authors to placement
+ vocabulary-door; EP-41B's ceremony re-shapes handover-only; EP-43 and the
handover are one machine in two directions. The production create is MOVER 4
of the serial chain.]**

## AS-BUILT ADDENDUM 2026-09-06 — §9's "no encryption-at-rest" SUPERSEDED BY THE OWNER'S WORD; the modelled-key-material cap stated once

§9 listed **no encryption-at-rest** as a non-goal (2026-09-02). On
2026-09-05/06 the owner asked how disk-level reading is stopped and ruled
content sealing built before the review ("sure now", board :3050, D08.19,
design/43 addendum). **The later word controls; the non-goal is struck as
law and kept as history.** Built as EP-46 (:3107): per-piece keys wrapped
to readers' cards, two derived keys per identity, two fingerprints,
opening is a row, remove-a-reader is a new piece — the full shape.

**THE CAP, stated once for the whole campaign:** every key in this estate
— sign keys, open keys, attestation seals — is MODELLED key material
(opaque strings, shape-true; keys.py:234, seal.py:48). The signed door
checks possession-plus-provenance, not a cryptographic signature; the
seal stops a system-path non-reader and a blob-only reader, NOT a reader
of the whole record on disk. This was always §9's posture ("cryptographic
engineering detail is EP-file material at launch"); it is now named as
the one flip that remains: **KEY-MATERIAL-REAL** — a real cryptographic
library under the whole family at once, a code primitive (no founding
kind, check, or bump), new scope, the owner's word. Until it lands, the
host disk lock is the real protection of content at rest.
