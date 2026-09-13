#!/usr/bin/env python3
# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (claim, proving test, designed-not-built). NON-GOAL: no offensive capability of any
# kind — this MAPS the public README's own words to the tests that prove them; it edits no words
# (the owner owns the words) and drives no code. Full declaration: SCOPE-STATEMENT.md.
"""EP-INSTRUMENTS-1 · I6 — THE PUBLIC-CLAIM CENSUS (the map).

Every claim the public README makes is mapped to the TEST that proves it, or tagged "designed,
not built". The words stay the owner's; the MAP is the instrument (the docmap precedent,
tools/docmap/inventory.py — a fold over a document's own markers, nothing maintained by hand that
the document already states).

WHAT IT CENSUSES
    The public README is `awig-deploy/awig-code/README.md` — the AWIG-OS public seed, the estate's
    actual public artifact. Its section "What this code does, and what it does not" is the claim
    surface. Each bullet is a claim (or several); each claim is mapped here to:
        - a PROVING TEST id (module[.Class[.method]]), which must RESOLVE to a real test, or
        - the sentinel "designed-not-built", for a claim the README itself marks as not-yet.

THE STANDING GUARD
    (a) every claim's QUOTE is a verbatim substring of the README (the map can never drift from the
        words); (b) every claim bullet in the section is COVERED by at least one claim (a new or
        changed bullet reds — "reds on a claim with neither a test nor a tag"); (c) every proving
        test id RESOLVES (a renamed/deleted test reds).

USAGE
    python3 -m tools.docmap.claim_census            # print the map
    python3 -m tools.docmap.claim_census --md       # emit the evidence markdown body
"""

import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
for _p in (os.path.join(_ROOT, "src"), os.path.join(_ROOT, "tests")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

PUBLIC_README = os.path.join(_ROOT, "awig-deploy", "awig-code", "README.md")
CLAIM_SECTION_HEADING = "## What this code does, and what it does not"

DESIGNED_NOT_BUILT = "designed-not-built"

# One row per claim. `quote` is a VERBATIM substring of the public README; `proving` is a test id
# that must resolve, or DESIGNED_NOT_BUILT. Adding a claim to the README adds a bullet the coverage
# guard flags until a row here maps it.
CLAIMS = [
    # ---- bullet 1: the door, derived state, reconstruction ----
    {"id": "door-records-the-rule",
     "quote": "Every action goes through one door and is written down with the rule that allowed or refused it",
     "proving": "test_instr_refusal_census.TestI4RefusalCensus.test_every_registered_op_is_refusable",
     "note": "every op flows through the gate and is refusable, the rule cited on the record"},
    {"id": "state-is-derived",
     "quote": "Every current state is worked out from the record; nothing is stored that could be worked out",
     "proving": "test_ep23.TestCanonicalOneStateOneHash",
     "note": "one state, one canonical hash — the view is computed, not stored"},
    {"id": "rebuild-fingerprints-match",
     "quote": "Delete everything except the record, rebuild, and the fingerprints match",
     "proving": "test_ep14.TestFoundingRoundTrip.test_founded_record_replays_and_rebuild_adds_nothing",
     "note": "the founding roundtrip: replay the record, rebuild adds nothing"},
    # ---- bullet 2: tamper-evidence, signing, attestation, no-delete, recovery, content locks ----
    {"id": "keyed-account-signs",
     "quote": "A keyed account signs its actions",
     "proving": "test_w4_first_key.TestW4FirstKey",
     "note": "the first bound key: a keyed account's acts carry a verified signature"},
    {"id": "checks-own-code-at-startup",
     "quote": "The program checks its own code at startup",
     "proving": "test_ep40",
     "note": "the engine attestation — the digest of the running engine becomes a fact of the record"},
    {"id": "no-delete-only-handover",
     "quote": "the only removal is a handover with a signed receipt",
     "proving": "test_maint_outside_1.TestB1RefusedHandoverKeepsBytes.test_b1_success_still_removes_and_records_the_departure",
     "note": "the handover ceremony: bytes depart only under a verified receipt, recorded as a departure"},
    {"id": "recover-to-sound-point",
     "quote": "A damaged record is repaired back to a sound point under three checks, never by cutting history off",
     "proving": "test_maint_outside_1.TestB4ServedStateIsRecovered.test_b4_served_state_is_the_recovered_one",
     "note": "recover-to-checkpoint: the served state is the recovered base, history intact"},
    {"id": "content-locked-to-readers",
     "quote": "Stored content is locked to its readers",
     "proving": "test_ep25",
     "note": "content addressing + the read-set: stored content is bound to who may read it"},
    # ---- bullet 3: the honest not-yet (the README's own 'what it does not') ----
    {"id": "locks-not-real-yet",
     "quote": "The locks are not real yet",
     "proving": DESIGNED_NOT_BUILT,
     "note": "the README's own disclosure: every key is a stand-in of the right shape, real "
             "cryptographic key material is the next unit"},
    # ---- bullet 4: the honest single-machine cap ----
    {"id": "two-machines-later",
     "quote": "have only been tested on one machine",
     "proving": DESIGNED_NOT_BUILT,
     "note": "the README's own cap: the mutual-attestation twin is proven on one machine; two is "
             "later work"},
]


def load_readme():
    with open(PUBLIC_README, encoding="utf-8") as f:
        return f.read()


def claim_bullets(readme_text):
    """The bullet lines under the claim section — the claim surface. A bullet is a line beginning
    '- ' (after the heading, until the next '## '). Multi-sentence bullets carry several claims."""
    lines = readme_text.splitlines()
    out = []
    in_section = False
    for ln in lines:
        if ln.strip() == CLAIM_SECTION_HEADING:
            in_section = True
            continue
        if in_section and ln.startswith("## "):
            break
        if in_section and ln.startswith("- "):
            out.append(ln[2:].strip())
    return out


def missing_quotes(readme_text):
    """Claims whose quote is NOT a verbatim substring of the README (the map drifted from words)."""
    return [c["id"] for c in CLAIMS if c["quote"] not in readme_text]


def unresolvable_tests():
    """Claims whose proving test id does NOT resolve to a real test."""
    loader = unittest.TestLoader()
    bad = []
    for c in CLAIMS:
        if c["proving"] == DESIGNED_NOT_BUILT:
            continue
        try:
            suite = loader.loadTestsFromName(c["proving"])
            if suite.countTestCases() == 0 or loader.errors:
                bad.append(c["id"])
        except Exception:
            bad.append(c["id"])
        # a load error accumulates on the loader; clear it for the next claim
        loader.errors = []
    return bad


def unproven_claims():
    """Claims with NEITHER a proving test nor the designed-not-built tag."""
    return [c["id"] for c in CLAIMS
            if not c["proving"] or (c["proving"] != DESIGNED_NOT_BUILT and not c["proving"].strip())]


def uncovered_bullets(readme_text):
    """Claim bullets in the README the map does NOT cover — a NEW public claim with no test/tag.
    A bullet is covered if at least one claim's quote is a substring of it."""
    quotes = [c["quote"] for c in CLAIMS]
    out = []
    for bullet in claim_bullets(readme_text):
        if not any(q in bullet for q in quotes):
            out.append(bullet[:80])
    return out


def render_markdown():
    readme = load_readme()
    out = []
    out.append("<!-- GENERATED by tools/docmap/claim_census.py --md — do not hand-edit. -->")
    out.append("")
    out.append("# I6 · Public-claim census — every public claim mapped to its proof")
    out.append("")
    out.append("The public README (`awig-deploy/awig-code/README.md`, the AWIG-OS public seed) makes "
               "these claims. Each is mapped to the test that proves it, or tagged designed-not-built "
               "where the README itself says the thing is not yet built. The words are the owner's; "
               "the map is the instrument.")
    out.append("")
    proven = sum(1 for c in CLAIMS if c["proving"] != DESIGNED_NOT_BUILT)
    dnb = sum(1 for c in CLAIMS if c["proving"] == DESIGNED_NOT_BUILT)
    out.append(f"Claims mapped: **{len(CLAIMS)}** ({proven} proven by test, {dnb} designed-not-built). "
               f"Claim bullets in the README: **{len(claim_bullets(readme))}**. "
               f"Uncovered bullets (must be 0): **{len(uncovered_bullets(readme))}**.")
    out.append("")
    out.append("| claim | proving test / tag | what it proves |")
    out.append("|---|---|---|")
    for c in CLAIMS:
        proving = "_designed, not built_" if c["proving"] == DESIGNED_NOT_BUILT else "`%s`" % c["proving"]
        out.append(f"| \"{c['quote'][:56]}…\" | {proving} | {c['note']} |")
    out.append("")
    return "\n".join(out)


# ============================================================================
# EP-I6B — THE CENSUS EXTENDS TO THE SHIPPED PUBLIC FRONT PAGES
# ============================================================================
# I6 above censuses the estate's own embedded public seed (awig-deploy/awig-code/README.md).
# This section extends the SAME instrument to the three SHIPPED public front pages of the
# separate public repository `../awig-os/` — its README, STATUS and ARCHITECTURE. Every checkable
# behaviour claim in those three is mapped to a proving test id that RESOLVES, or is pinned as a
# gap row (DESIGNED_NOT_BUILT where the doc itself says not-yet, or STATED_GAP where the claim is
# not machine-checkable) carrying its reason. The public pages are READ ONLY here — this maps
# their words, it edits no word (the words are the owner's; the public repo is EP-RELEASE-COPYOUT's).

STATED_GAP = "stated-gap"          # a claim that is not machine-checkable; carries its reason in `why`

# The three shipped public front pages, resolved as siblings of this repo's root (`../awig-os/`).
FRONT_PAGES = {
    "README":       os.path.normpath(os.path.join(_ROOT, "..", "awig-os", "README.md")),
    "STATUS":       os.path.normpath(os.path.join(_ROOT, "..", "awig-os", "STATUS.md")),
    "ARCHITECTURE": os.path.normpath(os.path.join(_ROOT, "..", "awig-os", "ARCHITECTURE.md")),
}

# STATUS.md is the shipped status INVENTORY: its claim surface is genuinely bulleted, so a NEW
# bullet claim added under any of these headings that no row maps REDS (the coverage guard, the
# analog of I6's uncovered_bullets). README and ARCHITECTURE are narrative; their checkable claims
# are curated rows pinned by the exact-set regenerate guard — see render_front_markdown / the
# honest cap in the evidence. A prose claim-extractor would be a heuristic that cannot soundly
# fail, so coverage-by-bullet is anchored only where the document actually bullets its claims.
STATUS_CLAIM_SECTIONS = (
    "## What exists but you cannot try yet",
    "## Designed on paper, not built",
    "## What is not true yet",
)

# One row per public claim. `quote` is a VERBATIM substring of the named `doc`; `proving` is a test
# id that must resolve, DESIGNED_NOT_BUILT (the doc's own not-yet), or STATED_GAP (not machine-
# checkable). Every non-test row MUST carry a non-empty `why`. Adding a claim, dropping a mapping,
# or drifting a quote all RED (verbatim guard + unproven guard + exact-set regenerate guard).
_REFUSAL = "test_instr_refusal_census.TestI4RefusalCensus.test_every_registered_op_is_refusable"
_DERIVED = "test_ep23.TestCanonicalOneStateOneHash"
_REBUILD = "test_ep14.TestFoundingRoundTrip.test_founded_record_replays_and_rebuild_adds_nothing"
_SIGN    = "test_w4_first_key.TestW4FirstKey"
_ATTEST  = "test_ep40"
_HANDOVER = "test_maint_outside_1.TestB1RefusedHandoverKeepsBytes.test_b1_success_still_removes_and_records_the_departure"
_RECOVER = "test_maint_outside_1.TestB4ServedStateIsRecovered.test_b4_served_state_is_the_recovered_one"
_CONTENT = "test_ep25"
_TAMPER  = "test_ep42_review.TestSealedWorldProbesLandAsRegressions.test_chain_red_world_detects_and_locates"
_AMEND   = "test_ep08b.TestB2ConservationReachesMasters.test_a_non_owner_superseding_a_master_refuses_and_records"
_ONEFMT  = "test_op_defs.TestOpDefinitions.test_define_and_execute_end_to_end"

FRONT_CLAIMS = [
    # ---------- STATUS.md — "What you can try today" (prose; curated) ----------
    {"id": "status-try-allow-refuse", "doc": "STATUS",
     "quote": "It performs one action the rulebook allows and writes down what it did and which rule allowed it",
     "proving": _REFUSAL, "why": "every op crosses the gate and is recorded with its rule; the forbidden one is refused and recorded"},
    {"id": "status-try-rebuild", "doc": "STATUS",
     "quote": "rebuilds itself from the record alone, and shows that the rebuilt copy is identical to the original",
     "proving": _REBUILD, "why": "the founding roundtrip: replay the record, the rebuild adds nothing, fingerprints match"},
    {"id": "status-eight-checks", "doc": "STATUS",
     "quote": "check 6 deliberately breaks one value to prove the checks can fail",
     "proving": STATED_GAP, "why": "the eight checks live in the SHIPPED, generated code/check.py, not the private suite; "
     "the suite proves the underlying behaviours (refusal census, founding roundtrip), and the shipped check-harness "
     "is EP-RELEASE-COPYOUT's artifact, not a test id resolvable here"},
    # ---------- STATUS.md — "What exists but you cannot try yet" (bulleted; coverage-guarded) ----------
    {"id": "status-tamper-evident", "doc": "STATUS",
     "quote": "The written record is tamper-evident",
     "proving": _TAMPER, "why": "the sealed chain: mutate a committed record and verify_chain returns not-ok AND locates the break"},
    {"id": "status-keys-sign", "doc": "STATUS",
     "quote": "An account with a key cannot act without signing",
     "proving": _SIGN, "why": "the first bound key: a keyed account's acts carry a verified signature"},
    {"id": "status-self-check", "doc": "STATUS",
     "quote": "The program checks its own code at startup and writes the fingerprint into the record",
     "proving": _ATTEST, "why": "the engine attestation — the digest of the running engine becomes a fact of the record"},
    {"id": "status-no-delete", "doc": "STATUS",
     "quote": "The only way anything leaves is a formal handover to another party, who signs a receipt",
     "proving": _HANDOVER, "why": "the handover ceremony: bytes depart only under a verified receipt, recorded as a departure"},
    {"id": "status-content-locked", "doc": "STATUS",
     "quote": "Stored content is locked so that only its intended readers can open it",
     "proving": _CONTENT, "why": "content addressing + the read-set: stored content is bound to who may read it"},
    {"id": "status-recover", "doc": "STATUS",
     "quote": "the system repairs it back to the last point that three independent checks agree on, or stops and asks",
     "proving": _RECOVER, "why": "recover-to-checkpoint: the served state is the recovered base, history intact"},
    {"id": "status-rulebook-same-door", "doc": "STATUS",
     "quote": "The rulebook itself can only be changed through the same door as everything else",
     "proving": _AMEND, "why": "amending a master rule goes through the ordinary door; a non-owner supersession is refused AND recorded"},
    # ---------- STATUS.md — "Designed on paper, not built" (the doc's own not-yet) ----------
    {"id": "status-dnb-network", "doc": "STATUS",
     "quote": "Connecting machines over a network",
     "proving": DESIGNED_NOT_BUILT, "why": "STATUS lists it under 'Designed on paper, not built'"},
    {"id": "status-dnb-several-machines", "doc": "STATUS",
     "quote": "Several machines, each keeping its own record",
     "proving": DESIGNED_NOT_BUILT, "why": "STATUS lists it under 'Designed on paper, not built'"},
    {"id": "status-dnb-ai-team", "doc": "STATUS",
     "quote": "The AI team that is meant to work inside it",
     "proving": DESIGNED_NOT_BUILT, "why": "STATUS lists it under 'Designed on paper, not built'"},
    {"id": "status-dnb-own-hardware", "doc": "STATUS",
     "quote": "Running on its own hardware without Linux underneath",
     "proving": DESIGNED_NOT_BUILT, "why": "STATUS lists it under 'Designed on paper, not built'"},
    # ---------- STATUS.md — "What is not true yet" (honest caps) ----------
    {"id": "status-locks-not-real", "doc": "STATUS",
     "quote": "The locks are not real yet",
     "proving": DESIGNED_NOT_BUILT, "why": "the doc's own not-yet: keys are placeholders of the right shape, real encryption is the next unit"},
    {"id": "status-one-machine", "doc": "STATUS",
     "quote": "One machine, one user",
     "proving": STATED_GAP, "why": "a testing-condition cap (every speed figure is from one computer, one user); "
     "a statement about how figures were gathered, not a code behaviour a test asserts"},
    {"id": "status-record-vs-view", "doc": "STATUS",
     "quote": "The record can be wrong while every view of it is right",
     "proving": STATED_GAP, "why": "the disclosed W4e finding: two concurrent creates once produced two entries for one act; "
     "every guard runs record->view, so this direction is a stated caution the doc itself raises, not a machine-guarded behaviour"},
    {"id": "status-rename-replay", "doc": "STATUS",
     "quote": "A known defect: rename and replay",
     "proving": STATED_GAP, "why": "a disclosed known defect in save-by-rename (two entries merged on rebuild); "
     "the shipped demo stops at `git add` to avoid it — a shipped-demo behaviour, not a private-suite assertion"},
    {"id": "status-not-attacked", "doc": "STATUS",
     "quote": "Nobody has attacked it yet",
     "proving": STATED_GAP, "why": "a statement about what has not yet happened (no adversarial testing performed); not machine-checkable"},
    {"id": "status-admin-can-edit", "doc": "STATUS",
     "quote": "An administrator can edit the file",
     "proving": STATED_GAP, "why": "a platform limitation: root can mutate the file; the detection half ('the chain will show where') "
     "is covered by status-tamper-evident, and prevention is an acknowledged cap no software layer can close"},
    {"id": "status-two-watchdogs-one-machine", "doc": "STATUS",
     "quote": "The two watchdogs have only been tested on one machine",
     "proving": DESIGNED_NOT_BUILT, "why": "the mutual-attestation twin is proven on one machine; two-machine independence is later work"},
    # ---------- STATUS.md — "How we know" (the test-count disclosure) ----------
    {"id": "status-test-count", "doc": "STATUS",
     "quote": "the private repository runs 3,677 automated tests in 133 files",
     "proving": STATED_GAP, "why": "a dated, machine-named count the doc itself disclaims ('any test count you see from us names "
     "the machine it ran on'); pinning a test to an exact count would red on every suite change — the pinned-figure antipattern the estate forbids"},

    # ---------- README.md — §6 'The machine' / 'Where this stands' (narrative; curated) ----------
    {"id": "readme-one-record-truth", "doc": "README",
     "quote": "one record as the only truth",
     "proving": _DERIVED, "why": "one state, one canonical hash — the served view is computed from the record, not stored"},
    {"id": "readme-act-cites-rule", "doc": "README",
     "quote": "every act a row citing its rule, refusals recorded the same way",
     "proving": _REFUSAL, "why": "every op flows through the gate and is recorded with the rule that allowed or refused it"},
    {"id": "readme-rebuild-hash", "doc": "README",
     "quote": "the whole world rebuilt from the record alone, hash for hash",
     "proving": _REBUILD, "why": "the founding roundtrip: rebuild from the record alone, fingerprints match"},
    {"id": "readme-chained-sealed", "doc": "README",
     "quote": "The record is chained and sealed",
     "proving": _TAMPER, "why": "the sealed chain detects and locates a mutation to a committed record"},
    {"id": "readme-keys-are-rows", "doc": "README",
     "quote": "keys are rows",
     "proving": _SIGN, "why": "a bound key is a record row; a keyed account's acts carry a verified signature"},
    {"id": "readme-engine-attests", "doc": "README",
     "quote": "the engine attests itself at boot",
     "proving": _ATTEST, "why": "the engine attestation — the running engine's digest becomes a fact of the record at boot"},
    {"id": "readme-no-delete", "doc": "README",
     "quote": "there is no delete: the constitution says so",
     "proving": _HANDOVER, "why": "the only removal is a handover under a verified receipt, recorded as a departure"},
    {"id": "readme-amend-count", "doc": "README",
     "quote": "thirty-nine amendments in",
     "proving": STATED_GAP, "why": "a dated count of law amendments ('since 24 July 2026'); the through-the-door mechanism is "
     "mapped by status-rulebook-same-door, but the exact number is a moving dated figure, not a stable test"},
    {"id": "readme-key-standin", "doc": "README",
     "quote": "Every key in this release is a stand-in of the right shape, not real cryptography",
     "proving": DESIGNED_NOT_BUILT, "why": "the README's own not-yet disclosure: real cryptographic key material is the next unit"},
    {"id": "readme-two-commands", "doc": "README",
     "quote": "you can check it in two commands",
     "proving": STATED_GAP, "why": "a claim about the SHIPPED seed_demo/check harness (code/), EP-RELEASE-COPYOUT's generated artifact; "
     "the private suite proves the behaviours (status-try-allow-refuse, status-try-rebuild), not the shipped two-command wrapper"},

    # ---------- ARCHITECTURE.md — §1 commitments, §4 seed, §5 warning (narrative; curated) ----------
    {"id": "arch-one-rule-format", "doc": "ARCHITECTURE",
     "quote": "There is no privileged rule syntax for privileged actors",
     "proving": _ONEFMT, "why": "an authored op-definition becomes law in the same executable rule format and cites its law like any builtin — one format, no privileged syntax"},
    {"id": "arch-full-traceability", "doc": "ARCHITECTURE",
     "quote": "No permission executes without leaving a verifiable form",
     "proving": _REFUSAL, "why": "every op flows through the gate and leaves a recorded decision or refusal"},
    {"id": "arch-everything-information", "doc": "ARCHITECTURE",
     "quote": "Nothing operationally relevant is opaque",
     "proving": STATED_GAP, "why": "a system-wide design principle, not a single behaviour; its concrete instances (state derived "
     "from the record, permission traceability) are separately mapped and tested"},
    {"id": "arch-ai-organisation", "doc": "ARCHITECTURE",
     "quote": "AI capability is structured as an organisation, not an oracle",
     "proving": DESIGNED_NOT_BUILT, "why": "STATUS lists 'The AI team that is meant to work inside it' under designed-on-paper-not-built"},
    {"id": "arch-two-points", "doc": "ARCHITECTURE",
     "quote": "a narrow, default-closed tunnel to the system, and an air-gapped read of user text",
     "proving": DESIGNED_NOT_BUILT, "why": "the AI organisation's two contact points are part of the not-yet-built AI organisation"},
    {"id": "arch-glassbox", "doc": "ARCHITECTURE",
     "quote": "inspectable from outside and structurally bounded from inside",
     "proving": DESIGNED_NOT_BUILT, "why": "the glass-box containment of the AI organisation, which STATUS marks not-yet-built"},
    {"id": "arch-reference-model", "doc": "ARCHITECTURE",
     "quote": "a running reference model, in the verified-kernel tradition",
     "proving": STATED_GAP, "why": "a build-method/lineage claim (reference-model-first, clean-room, Linux-compatible-not-Linux); "
     "a statement about HOW the system is built, not a runtime behaviour a test asserts"},
    {"id": "arch-seed-verifiable-trace", "doc": "ARCHITECTURE",
     "quote": "one permission runs and leaves a verifiable trace",
     "proving": _REFUSAL, "why": "the milestone-0 seed behaviour: a permission runs and leaves a recorded, verifiable trace through the gate"},
    {"id": "arch-key-warning", "doc": "ARCHITECTURE",
     "quote": "Every key in this release is a stand-in of the right shape, not real cryptography",
     "proving": DESIGNED_NOT_BUILT, "why": "ARCHITECTURE's own one-warning: real cryptographic key material is the next unit"},
    {"id": "arch-suite-not-ship", "doc": "ARCHITECTURE",
     "quote": "the full test suite does not ship, only the eight checks",
     "proving": STATED_GAP, "why": "a what-ships/provenance statement; the shipped check harness is EP-RELEASE-COPYOUT's artifact, not a test id"},
    {"id": "arch-commit-private", "doc": "ARCHITECTURE",
     "quote": "belongs to the private repository and cannot be looked up from here",
     "proving": STATED_GAP, "why": "a provenance statement about the render-stamp commit; not a code behaviour a test asserts"},
]

_GAP_SENTINELS = (DESIGNED_NOT_BUILT, STATED_GAP)


def front_page_path(doc):
    try:
        return FRONT_PAGES[doc]
    except KeyError:
        raise KeyError("unknown public front page %r (known: %s)" % (doc, sorted(FRONT_PAGES)))


def load_front_page(doc):
    with open(front_page_path(doc), encoding="utf-8") as f:
        return f.read()


def _front_docs_text():
    """Read all three front pages once; a per-doc dict of text. Raises if any is missing (a red:
    the census cannot run without the public tree it censuses)."""
    return {doc: load_front_page(doc) for doc in FRONT_PAGES}


def front_missing_quotes(docs_text=None):
    """Front claims whose quote is NOT a verbatim substring of their named front page (drift)."""
    docs_text = docs_text if docs_text is not None else _front_docs_text()
    return [c["id"] for c in FRONT_CLAIMS if c["quote"] not in docs_text[c["doc"]]]


def front_unresolvable_tests():
    """Front claims whose proving test id does NOT resolve to a real test (gap rows skipped)."""
    loader = unittest.TestLoader()
    bad = []
    for c in FRONT_CLAIMS:
        if c["proving"] in _GAP_SENTINELS:
            continue
        try:
            suite = loader.loadTestsFromName(c["proving"])
            if suite.countTestCases() == 0 or loader.errors:
                bad.append(c["id"])
        except Exception:
            bad.append(c["id"])
        loader.errors = []
    return bad


def front_unproven_claims():
    """Front claims with NO valid mapping: neither a proving test nor a gap sentinel carrying a
    non-empty reason. A planted claim added with an empty mapping REDS here."""
    out = []
    for c in FRONT_CLAIMS:
        proving = c.get("proving")
        if not proving:
            out.append(c["id"])
        elif proving in _GAP_SENTINELS and not (c.get("why") or "").strip():
            out.append(c["id"])
    return out


def status_claim_bullets(status_text):
    """The `- ` bullet lines under STATUS.md's three claim-inventory headings — the machine-readable
    claim surface. A new bullet added under any of them is a new public claim the map must cover."""
    lines = status_text.splitlines()
    out = []
    in_section = False
    for ln in lines:
        stripped = ln.strip()
        if stripped in STATUS_CLAIM_SECTIONS:
            in_section = True
            continue
        if in_section and ln.startswith("## "):
            in_section = False
            continue
        if in_section and ln.startswith("- "):
            out.append(ln[2:].strip())
    return out


def front_uncovered_status_bullets(status_text=None):
    """STATUS claim bullets the map does NOT cover — a NEW public claim with no test/gap row.
    A bullet is covered if at least one STATUS front-claim's quote is a substring of it."""
    status_text = status_text if status_text is not None else load_front_page("STATUS")
    quotes = [c["quote"] for c in FRONT_CLAIMS if c["doc"] == "STATUS"]
    out = []
    for bullet in status_claim_bullets(status_text):
        if not any(q in bullet for q in quotes):
            out.append(bullet[:80])
    return out


def _proving_cell(c):
    if c["proving"] == DESIGNED_NOT_BUILT:
        return "_designed, not built_"
    if c["proving"] == STATED_GAP:
        return "_stated gap_"
    return "`%s`" % c["proving"]


def render_front_markdown():
    docs_text = _front_docs_text()
    out = []
    out.append("<!-- GENERATED by tools/docmap/claim_census.py --md-front — do not hand-edit. -->")
    out.append("")
    out.append("# I6B · Public front-page claim census — every public claim mapped to its proof")
    out.append("")
    out.append("The three SHIPPED public front pages of `../awig-os/` (`README.md`, `STATUS.md`, "
               "`ARCHITECTURE.md`) make these claims. Each checkable behaviour claim is mapped to the "
               "test that proves it, or pinned as a gap row: _designed, not built_ where the doc itself "
               "says the thing is not yet built, or _stated gap_ where the claim is not machine-checkable "
               "(with its reason). The words are the owner's; the public pages are read-only; the map is "
               "the instrument.")
    out.append("")
    by_test = sum(1 for c in FRONT_CLAIMS if c["proving"] not in _GAP_SENTINELS)
    dnb = sum(1 for c in FRONT_CLAIMS if c["proving"] == DESIGNED_NOT_BUILT)
    gap = sum(1 for c in FRONT_CLAIMS if c["proving"] == STATED_GAP)
    uncovered = len(front_uncovered_status_bullets(docs_text["STATUS"]))
    out.append(f"Public claims mapped: **{len(FRONT_CLAIMS)}** ({by_test} proven by test, "
               f"{dnb} designed-not-built, {gap} stated-gap). "
               f"STATUS claim bullets: **{len(status_claim_bullets(docs_text['STATUS']))}**. "
               f"Uncovered STATUS bullets (must be 0): **{uncovered}**.")
    out.append("")
    out.append("Coverage note (honest cap): a NEW bullet claim added under STATUS.md's claim-inventory "
               "headings that no row maps REDS (the coverage guard). README.md and ARCHITECTURE.md are "
               "narrative, not bulleted inventories; their checkable claims are pinned by the exact-set "
               "regenerate guard and the verbatim-quote guard, not by prose extraction — a prose "
               "claim-extractor would be a heuristic that cannot soundly fail.")
    out.append("")
    for doc in ("README", "STATUS", "ARCHITECTURE"):
        out.append(f"## `../awig-os/{doc}.md`")
        out.append("")
        out.append("| claim (verbatim quote) | proving test / gap | what it proves / why not checkable |")
        out.append("|---|---|---|")
        for c in FRONT_CLAIMS:
            if c["doc"] != doc:
                continue
            out.append(f"| \"{c['quote']}\" | {_proving_cell(c)} | {c['why']} |")
        out.append("")
    return "\n".join(out)


def main(argv=None):
    argv = list(argv if argv is not None else sys.argv[1:])
    if "--md" in argv:
        print(render_markdown())
        return 0
    if "--md-front" in argv:
        print(render_front_markdown())
        return 0
    readme = load_readme()
    print(f"{len(CLAIMS)} claims; missing_quotes={missing_quotes(readme)}; "
          f"unresolvable={unresolvable_tests()}; uncovered_bullets={len(uncovered_bullets(readme))}")
    docs_text = _front_docs_text()
    print(f"{len(FRONT_CLAIMS)} front claims; front_missing_quotes={front_missing_quotes(docs_text)}; "
          f"front_unresolvable={front_unresolvable_tests()}; "
          f"front_unproven={front_unproven_claims()}; "
          f"front_uncovered_status_bullets={len(front_uncovered_status_bullets(docs_text['STATUS']))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
