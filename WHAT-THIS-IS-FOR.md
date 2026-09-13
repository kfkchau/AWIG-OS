# What this is for

Dated 14 September 2026. `STATUS.md` says what is true today; where this page and the code disagree, the code is right.

Every organisation keeps five things in five places: a rulebook, an audit log, an institution, a constitution, and the machine that acts. None of the five is the one that does the acting, and each is kept by a different profession with its own tools. Here they are one record and five names for it. The record is the definitive. Everything else, every screen, every log, every report, is derived from it and can be thrown away and rebuilt, hash for hash. Fix the definitive and the derivative follows.

That is the whole idea. Here is what it is for.

### 1. The decision you have to defend

Eleven months after the fact, an auditor, a court or a freedom-of-information officer asks why a thing was allowed. Today the answer is assembled from emails, memory, and a log that someone with the right access could have edited.

Here the decision is a row. The row names the rule that allowed the act, it was written before the act took effect, and the act happened because the row exists. There is nothing to assemble; you read the row.

Run it: `cd code && python3 seed_demo.py`. Step 2 asks the gate for a new law, shows the check that ran and the row that was appended, and prints the rule the decision cites. Runs today, in the governing layer, on stock Python.

### 2. The no nobody can produce

A regulator asks what the system refused last quarter and why. Today a refusal leaves nothing, or a line in a log beside the system that nobody reads.

Here a no costs a record exactly as a yes does. The refusal is a row with the same fields as an allowed act, the check's own words are inside it, and the caller was handed the same reason as an error, so no program carries on unaware of a no.

Run it: the same demo, step 3. The same check on the same operation, one record later, refuses and writes down why. The shipped suite goes further: `tests/test_instr_refusal_census.py` proves every registered operation can be refused and catches a planted operation that tries to bypass the gate. Runs today.

### 3. The contractor who left

Someone leaves. Their access lives in a dozen copies: groups, tokens, cached permissions, a spreadsheet. You find one of them three months later.

Here nobody holds anything by default. A grant is a row; what is denied is everything not granted, computed, never stored; a revocation is one row and takes effect at the very next act. There is no list to clean because there is no list.

Run it: `python3 run_public_suite.py`, and read `tests/test_ep26.py`, "a revoked chain refuses at the door on the very same act", and `tests/test_ep23.py`, "stale and revoked are two separately observable verdicts". Runs today.

### 4. The machine that was wiped

Ransomware, a lost laptop, the team that left. Today the backup disagrees with the log, both disagree with the database, and someone decides which copy is true.

Here that question cannot arise. Delete everything except the record and the same system comes back: every actor, rule, grant, view and decision, to the same fingerprint. What it rebuilds is the governing state. It does not promise a running program's memory, and it rebuilds content only where the content was written as rows.

Run it: the demo's step 4 destroys the derived world, keeps only the record file, replays it and prints both fingerprints. The suite's `tests/test_ep22.py` does the same for every derived thing. Runs today.

### 5. The AI you let in

You want an AI to work inside the organisation, and you have read the warning that a document it opens can turn it against you. Today the choice is a fence around what it may touch, or nothing.

Here an AI organisation meets the world at two openings only: what it is asked, and what it asks for. Nothing arriving at the second executes until a rule says so, and the pass or the refusal is a row. A turned document arrives at the first opening. Whatever the organisation then wants arrives at the second as a proposal, and taking data out needs a grant nobody wrote, so the proposal comes back as a refusal citing the rule. Contained is not the same as safe: an organisation with a grant can be turned to misuse that grant, and the damage is bounded to what was granted, not to nothing. The page says contained.

Run it: not yet from this repository. The border that makes an outside request a draft the gate decides is built and proven in test worlds between a host and a guest; those tests read a private file and are skipped in the public copy, each skip naming why. The organisation between the two openings is a stand-in pack today. Design 39 section 3 and design 49 to 51 in `design/` state the contract.

---

If you have read this far and thought "so it is a ledger": there is no consensus, no token, and one pen. The point is not that the record cannot be tampered with. The point is that the record is the system.
