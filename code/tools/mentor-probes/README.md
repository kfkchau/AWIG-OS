<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature (kernel, syscall, capability, permission, memory protection). NON-GOAL: no offensive capability of any kind; defines record, gate, view, and kernel-conformance only. Full declaration: SCOPE-STATEMENT.md. -->
# The Mentor Probe Library

**What this is.** The campaign-1 mentor's adversarial probes, committed so the seat's
accumulated adversarial-probe findings outlive any session (the R14 rule applied to the
reviewer itself). Every ship-blocker this campaign caught — the brick, the granter
forgery, the reboot divergence, the silencing, the master demotion — was found by a
probe in these families, NOT by the builders' own tests. A successor mentor RUNS these;
inventing new ones on top is the bonus, not the baseline.

**How to use (the review drill).**
1. Run the suite yourself first; reconcile the count exactly.
2. Run every probe file here: `python3 tools/mentor-probes/<file>.py` — each prints
   PASS/FAIL per probe and exits non-zero on any FAIL. A FAIL is a finding, not a
   broken probe (check the probe's assumptions in its docstring before celebrating
   either way — one EP-10 "failure" was the reviewer misreading a return shape).
3. For the EP under review, write 2–5 NEW probes in its spirit: ask what a hostile
   nobody, a careless owner, and a REBOOT would each do to the new surface. Those are
   the three archetypes that found everything.
4. Any new probe that finds something becomes a regression test in `tests/` (builder's
   fix) AND joins this library if the pattern generalizes.

**The three archetypes behind every family:**
- **The hostile nobody** — an ordinary actor pushing every new power to its edge
  (mint, supersede, forge, silence, brick).
- **The careless owner** — legitimate wide power used through the documented path,
  checking the protection SURVIVES the amendment (retire+recreate, amend-in-place).
- **The reboot** — kill everything derived, replay from the record, demand identity.
  Divergence between live and replayed state is a finding EVERY time (the half-fix
  class: three were caught this way).

**Files:**
- `constitution_probes.py` — tier minting/laundering/elevation/demotion, forge ops,
  data-passthrough insertion, the untouchables floor (brick both directions), the
  lifecycle-pack floor, malformed payloads.
- `conservation_probes.py` — core amendment tier conservation, bare-retire refusal,
  master-view supersession/demotion, worker coherence across amendment, the bare-kernel
  content-amendment refusal, reboot round-trips for all of the above.
- `obligation_probes.py` — forged fired-markers (silencing), re-arm by amendment,
  never-twice-per-version, payloadless-outcome evidence, refused-firing isolation,
  replay-alone firing.
- `separation_probes.py` — blind-stream mutual blindness (both directions), brake
  freezes with the record never dark, unbrakables refuse (not accept-and-ignore),
  SOP maker-refusal, cross-check divergence detection.
- `dictionary_comparison_probes.py` — [line added 2026-07-24 at reconciliation; the
  set was added by the EP-13 review but this list was never extended] frame-carrying
  verdicts (same-frame flagged, cross-frame kept unmerged), dictionary
  latest-undisputed-wins and dispute routing, definition-reference integrity at use
  including live code ops, append-nothing reads, replay identity.

**Standing cautions for the successor:**
- Probes build fresh kernels in temp dirs — they never touch a real record.
- After ANY probe finds something: verify it in the actual code before writing the
  finding (the log points, the code answers), and re-run the whole suite after any fix.
- If a probe file itself errors (imports, signatures), the kernel's surface moved —
  that is ALSO information: update the probe deliberately and log the change; a probe
  library that silently rots is a paper tiger.
