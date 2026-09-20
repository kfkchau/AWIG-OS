#!/usr/bin/env python3
# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-28U — the board as a COMPUTED VIEW over `planning/build/BOARD-EVENTS.log`.

THE FIRST LAW OF THIS MODULE, and it is the one a later reader must never relax:
**THIS TOOL IS A VIEW. IT READS THE EVENTS FILE AND WRITES NOTHING — not to that file,
not to any file.** `BOARD-GRAMMAR.md`'s founding refusal is that a board PARSED from the
prose record needs judgment per entry, and three seats' parsers are three boards, which
is the census defect rebuilt at the planning layer. So this module folds EVENTS ONLY and
NEVER parses prose. A future pass that reaches into `BUILD-PROGRESS_v3.md` to recover a
state has rebuilt the defect this instrument exists to retire.

`tests/test_board_tool.py` asserts the no-writer property STRUCTURALLY, by AST, with a
planted writer proving the guard fires.

WHAT THE FOLD IS, in the order the events are applied:

  1. The SEED BLOCK, located by its MARKER LINES IN THE BODY — never by the file's
     header. The header is a LABEL and it has been wrong: on 2026-08-08 it read
     "(not yet written)" over a seed block written twelve lines below it. A fold that
     believed the header would have refused a healthy file. `T-BOARD-HEADER-IS-NOT-
     LOAD-BEARING` drives a lying header and a true header against otherwise identical
     bodies and requires the same board.
  2. Every NON-SEED event in FILE ORDER — the lines before the seed (early adoption,
     which the seed confirms) and then the lines after it.

WHAT THE FOLD DOES WITH EACH EVENT. Latest state per item wins, with the ONE exception
`BOARD-GRAMMAR.md` §3 states: an item may carry `OWED` and `HELD` together and the fold
SHOWS THE PAIR, never picks one (the hold names the trigger, the debt names who moves).

  PROGRESS verbs  AUTHORED PRE-FLIGHTED DISPATCHED STOPPED RESUMED ACCEPTED CLOSED
                  RELEASED RULED CORRECTED(...)      -> become the item's current state
  PENDING verbs   HELD(on: X)  OWED(by: S, act: A)   -> STAND OPEN alongside the state

DERIVED HERE AND NOT READ FROM THE SPEC — declared loudly because a reader must be able
to attack it rather than inherit it. `BOARD-GRAMMAR.md` says a pending may stand; it does
NOT say when a pending is DISCHARGED, and a fold cannot exist without an answer:

  * a later PENDING of the SAME KIND supersedes an earlier one of that kind;
  * any later PROGRESS event on the item CLOSES every open pending on that item;
  * a `CORRECTED` that resolves to a pending VOIDS that pending.

Every discharge is SHOWN in `--ep`'s history as `closed by line N`, so the derivation is
auditable at the output rather than buried in this docstring.

`CORRECTED(supersedes: <date+verb>)` REPLACES ITS TARGET — and the key does not always
identify one. EP-28J carries two same-date `OWED` events and three same-date `CORRECTED`
events, so `supersedes: 2026-08-08 OWED` has two candidates and
`supersedes: 2026-08-08 CORRECTED` has three. Five of the live `CORRECTED` events carry
no `<date+verb>` at all (`supersedes: none — addition`). Resolution is therefore a
REPORTED QUALITY, never a silent pick:

  RESOLVED     exactly one earlier event on the item matches -> that event is VOIDED
  AMBIGUOUS    more than one matches -> the LATEST is voided AND THE TOOL SAYS SO
  UNRESOLVED   none matches -> nothing is voided AND THE TOOL SAYS SO

Treating an unresolvable reference as a MALFORMED LINE was rejected: it would make the
instrument refuse the very log it was built to read. That is a derivation, it is raised
in this pass's entry, and one constant flips it if the mentor rules the other way.

REFUSAL IS LOUD AND NAMES ITS LINE NUMBER. A line this module cannot read EXACTLY is
never skipped: no partial fold, no best effort. Verbs are matched LITERALLY and
CASE-SENSITIVELY (§A64), so `HOLD(on: x)`, `HELD (on: x)`, `held(on: x)` and `CLOSE` all
REFUSE. The failure direction is loud-and-wrong rather than silent-and-right, because a
tolerant matcher is a board that quietly loses an item.

UNKNOWN-ITEM REFUSES LOUDLY. Absence of events reads as not-started ONLY because the
seed is complete over every item that has state — seed completeness is LOAD-BEARING — so
a name the fold has never seen is reported as UNKNOWN-ITEM and never borrows that
guarantee.

EVERY FINDING THIS TOOL REPORTS IS A SET OR A COUNT OVER AN ABSENCE, so a structurally
broken fold returns exactly the clean answer a healthy one returns. `positive_control()`
therefore runs on EVERY INVOCATION, not once: it folds a synthetic log carrying a known
case of every shape and requires every one of them found. A count not backed by a passing
control is printed as UNINTERPRETABLE and is never printed as a number.

THE AMBIGUITY DUTY (EP-28W W4 — `BOARD-GRAMMAR.md` §1's pair law, clause 3). While TWO OR
MORE pendings stand open on one item, an ending event that names NONE of them resolves to
more than one candidate, so the fold REPORTS THE AMBIGUITY AND CLOSES NOTHING; both states
stay displayed. An ending NAMES one by the only mechanism the closed verb set has —
`CORRECTED(supersedes: <date+verb>)` resolving to that pending — and then exactly that one
closes and the other STANDS. With ONE pending open, an ending resolves deterministically
and closes it, byte-for-byte the behaviour this tool shipped at EP-28U: naming becomes
mandatory exactly where determinism ends, and standing history keeps its meaning.

THE EXIT-CODE CONTRACT, DECLARED (EP-28W W3). A caller distinguishes success from refusal
from input-error from crash by the code alone:

  0  the query answered
  1  NOT RETURNED DELIBERATELY BY ANYTHING HERE — it is the interpreter's uncaught-
     exception code. Seeing 1 means this tool crashed, which is a defect to report.
  2  REFUSED: the log could not be read, or a line could not be read EXACTLY, or the
     positive control failed. Nothing is folded. (Note: `argparse`'s own usage errors
     also leave with 2. That collision predates this contract and is reported, not
     quietly repaired — see EP-28W's entry.)
  3  UNKNOWN-ITEM: a name the fold has never seen. NOT "not-started".
  4  `--owner-table`, stopped by EP-28U's builder at a conflict with `BOARD-GRAMMAR` §7.
  5  BAD ARGUMENT: an argument this tool cannot use, refused with a named reason. It is
     distinct from every code above AND from 1, which is the whole point: before EP-28W a
     non-date `--stale` argument died in a raw traceback, so input-error was
     byte-identical to a crash.

THE RECORD-PLANE VERBS (EP-28X W2/W3 — `BOARD-GRAMMAR.md` §1's sizing ruling, 2026-08-09).
The closed set was COMPLETE IN ITS PLANE (item lifecycle) and the estate stretched it to a
SECOND plane: acts about the RECORD ITSELF. Three verbs enter force here, and they are
HISTORY ONLY — they append to an item's history and they are NOT the item's state:

  NOTED                       a plain addition or finding. Supersedes nothing, opens
                              nothing, ends nothing; THE CLAUSE CARRIES THE FACT. It is
                              also the lawful OVERFLOW: when no verb fits, NOTED plus the
                              act in the clause, and the gap filed. Borrowing a neighbour
                              is what produced sixteen-plus unresolved references and two
                              minted compounds in one day.
  SEATED(kind: continuation | substitution)
                              a seat holding anew, stating honestly WHICH. The kind set is
                              CLOSED and LITERAL: `replacement` refuses, bare `SEATED`
                              refuses.
  DISAMBIGUATED(ending: <date+verb>, ended: <state>)
                              says which open state a PAST ending ended. See below.

A HISTORY-ONLY EVENT MAY BE AN ITEM'S FIRST EVENT, and that is not a curiosity — the
queued intake lines per `BOARD-EVENTS.log:247` are exactly that shape for four items the
fold has never seen. Such an item has HISTORY AND NO STATE, and it is displayed as
`NO STATE EVENT` rather than crashing on a `None`. Nothing here invents a state for it.

DISAMBIGUATED, AND WHY IT REFUSES WHERE `CORRECTED` MERELY REPORTS. `CORRECTED`'s
supersedes-reference is PROVENANCE: lossy is acceptable, the state travels on the next
line, and the mentor ruled the standing unresolved set STANDS. `DISAMBIGUATED`'s reference
IS ITS ENTIRE SEMANTIC CONTENT — a DISAMBIGUATED that cannot act is not informational
residue, it is A STATE CLAIM THAT FAILED WHILE LOOKING LIKE ONE THAT LANDED. So:

  * the `ending:` reference must resolve to EXACTLY ONE earlier event on that item — zero
    or two-or-more REFUSES THE FOLD WHOLE, naming the DISAMBIGUATED's line;
  * `ended:` must name a member of THAT ENDING'S CANDIDATE SET — the pendings standing
    open at the ending's own position — else the fold REFUSES WHOLE;
  * on success the ending folds AS OF ITS OWN POSITION as having ended exactly the named
    state, every other pending STANDS, the ending's AMBIGUOUS-ENDING report DROPS, and
    NOTHING opens or closes at the DISAMBIGUATED's own line.

"As of its own position" is the whole of it: the resolution is applied where the ending
sits in the fold, so every later event sees the state the record now says was ended. A
resolution that only stamped a line number would leave a later ending still reported
ambiguous over a state the record has since said was closed.

THE DISCRIMINATOR (EP-28Y — `BOARD-GRAMMAR.md` §1's discriminator ruling, 2026-08-09). The
verb above had its first real use on 2026-08-09 and it REFUSED: `2026-08-08 PRE-FLIGHTED`
names TWO events on `EP-28J`, and repeated pre-flights are this estate's normal gait, so
the collision is the COMMON case and not the corner. The ruling is the identity law
arriving at the record's own events — `<date+verb>` is an ALIAS and aliases collide; the
event's IDENTITY is its CONTENT; a line number is a ROLE. So a `DISAMBIGUATED` reference
may carry `digest:<hex-prefix>` of the EVENT LINE'S OWN CONTENT DIGEST, computed by the
ANCHOR'S ALGORITHM — `content_digest` over a one-line list, never a second algorithm — and:

  * REQUIRED where `<date+verb>` resolves to two or more events on the item;
  * VALIDATED ALWAYS WHEN PRESENT, which is the wider half and the one that matters most:
    a digest carried on an UNAMBIGUOUS reference is checked and refuses whole on mismatch.
    The grammar's words are "a required-but-absent, UNMATCHED, or twice-matched digest
    REFUSES THE FOLD WHOLE", with "unmatched" unqualified — and because `--ep` prints
    digests so references are COPIED rather than computed, a carried digest is the COMMON
    case. Ignoring one at count 1 would have made the taught path the unchecked path.
  * TWICE-MATCHED refuses whole and NAMES the collision. Never longest-match, never
    first-match. This is what makes a SHORT prefix safe: uniqueness is enforced by the
    refusal, never by the printed length.
  * A line number may RIDE beside the alias and never binds alone — it already did, via
    the tolerant reference match, and it is pinned by a row here so this pass cannot have
    quietly taken it away.

The digest's SUBJECT is the event line as the fold reads it (surrounding whitespace
stripped, which is what `read_event_lines` hands the parser). Every change to any field
moves it; a change to the line's outer whitespace does not, and does not change the event.

THE PAIRED FILING (EP-30-R4 — the convention at `BOARD-EVENTS.log:1134`, its ceiling at
`:1136`, the tool pass ruled at `:1138`). One decision is lawfully filed TWICE, on two
items, when two seats each witness it — and the estate had no mechanism that paired them,
so a half-ended ruling folded as two clean states and read as deliberate. The convention
makes the pair GREPPABLE; it does not make a half-ending FAIL. This is the enforcement
layer, and it is a REPORT and never a refusal: two endings cannot land in one append, so a
pair is lawfully half-ended for the width of one hand and a fold that refused there would
take the record plane down between two lawful appends.

  `PAIRS(item: <ITEM>, event: <date> <VERB>[, digest:<hex>])`, CLAUSE-INITIAL ONLY.

  * IT CARRIES THE ITEM because the existing reference grammar cannot. `CORRECTED`'s
    `supersedes:` resolves against EARLIER EVENTS ON ITS OWN ITEM, and a pair is across
    items by definition, so an item-less reference would resolve against the wrong
    population — and a reference that finds the WRONG thing is worse than one that finds
    nothing.
  * IT RE-SPELLS NOTHING. `<date> <VERB>` is `RE_SUPERSEDES_KEY` and the discriminator is
    `split_digest_field`, both reused verbatim. A second spelling for one discriminator
    would be a second identity for one object.
  * IT IS LEGAL ONLY AT POSITION 0 OF THE CLAUSE, and that is the load-bearing choice. A
    clause is free prose. `digest:` is found anywhere in its reference because a reference
    is a short field; a token found anywhere in a CLAUSE is a token PROSE CAN MINT, and
    this estate has already paid for that shape twice — the absence test that inverted as
    the absence was documented, and a grep that matched its own shell. Anchoring at
    position 0 makes prose-about-pairing STRUCTURALLY INCAPABLE of becoming a pairing, and
    the standing control drives that by position alone.

  RESOLUTION, and it is deliberately a HYBRID of the two treatments already in this module,
  each half taken where its reason applies:

    RESOLVED     exactly one earlier event on the NAMED item matches the alias
    UNRESOLVED   none matches, or the item is one the fold has never seen -> REPORTED to
                 the writer and folded as no state, which is the treatment `supersedes:`
                 already gets: the filing still carries its own state on its own line
    REFUSES      two or more match and NO discriminator is carried; or a carried
                 discriminator is unmatched, twice-matched, or disagrees with its alias.
                 A pairing that could mean either of two events has not named one, and the
                 discriminator is the escape the identity law already provides

DERIVED HERE AND NOT READ FROM ANY SPEC — declared loudly, as this module's discharge rules
were, so a later reader can attack it rather than inherit it. `:1138` rules the shape as "a
named pair with one side ended and the other open" and NOTHING IN THE ESTATE DEFINES WHAT
ENDS AN ITEM. A fold cannot exist without an answer, and every answer that classifies verbs
into terminal and non-terminal would mint a closed set this pass has no licence for. So:

  A PAIRED FILING STILL STANDS when the fold still holds it as live — it is the item's
  current STATE, or it is an OPEN PENDING on that item. It has ENDED when it is neither,
  which is to say a later lifecycle event has moved past it.

That is entirely the fold's existing structure and it mints nothing. It also reproduces the
instance that caused this pass, in all three of its phases: `OWNER-PAUSE` opened at `:1100`
and `BUILD-LINE` at `:1101` — BOTH STANDING, silent, work in progress; `:1110` closed the
first and left the second standing — HALF-ENDED, reported, for the twenty-four lines and one
dispatch that nobody saw; `:1134` ended the second — BOTH ENDED, silent again. The two
`NOTED` lines on `OWNER-PAUSE` at `:1102` and `:1105` do NOT end it, and they cannot, because
the record-plane branch never lets them become a state. ONE CAP, STATED: neither `:1100` nor
`:1101` carries the token and neither ever can, because the record is append-only. This
check therefore lands with a live population of ZERO and stays there until the next paired
decision is filed, which is why its silence is EARNED IN THE CONTROL and never inferred here.

THE ANCHOR (EP-28X W4 — `BOARD-GRAMMAR.md` §1a and its hole-fix, 2026-08-09). §1a rested on
"every prefix is immutable BY CONSTRUCTION", and this record is NOT strictly append-only:
two removal markers stand in it, both lawful under the unparseable-line precedent, and a
removal inside [1..N] silently changes what N names. So THE COORDINATE IS A CONTENT DIGEST
of [1..N] and the line count is its human-readable ALIAS — name by identity what is fixed,
by role what moves. EVERY fold prints `(N, sha256:...)`. `--at N` folds exactly the prefix
[1..N]. `--anchor <digest>` re-checks a prior taking and REFUSES WHOLE naming BOTH digests
on a mismatch, never proceeding on a changed subject. Appends BEYOND N are lawful and
invisible to an anchored prefix fold, which is the property that retires the quiet-record
window. THE ALGORITHM IS PRINTED BESIDE EVERY ANCHOR: a digest whose algorithm is unstated
is a number, not an anchor.
"""
import argparse
import datetime
import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EVENTS = os.path.join(ROOT, 'planning', 'build', 'BOARD-EVENTS.log')

#: The DECLARED exit codes. Named constants rather than literals at the return sites,
#: because the contract is a set and a set needs one home. `1` is absent ON PURPOSE: it
#: belongs to the interpreter, this tool never chooses it, and a code chosen equal to it
#: would make an input error byte-identical to a crash.
EXIT_OK = 0
EXIT_REFUSED = 2
EXIT_UNKNOWN_ITEM = 3
EXIT_OWNER_TABLE_STOP = 4
EXIT_BAD_ARGUMENT = 5

#: Every code this tool can DELIBERATELY leave with, plus the interpreter's 1. A new code
#: is added here first, and the suite requires `EXIT_BAD_ARGUMENT` to be outside every
#: other member — a collision is a red, never a choice.
DECLARED_EXIT_CODES = {
    EXIT_OK: 'the query answered',
    1: "the interpreter's uncaught-exception code — never chosen here",
    EXIT_REFUSED: 'REFUSED: unreadable log, unreadable line, or a failed control',
    EXIT_UNKNOWN_ITEM: 'UNKNOWN-ITEM: a name the fold has never seen',
    EXIT_OWNER_TABLE_STOP: '--owner-table, stopped at a conflict with BOARD-GRAMMAR §7',
    EXIT_BAD_ARGUMENT: 'BAD ARGUMENT: refused with a named reason',
}

#: The seed block is located by these MARKERS IN THE BODY. Never by the file's header —
#: the header is a label, it has been false, and a fold that reads it is a fold a
#: mislabelled file can break. `END` is tested first because it contains the start text.
SEED_START_MARK = 'SEED BLOCK'
SEED_END_MARK = 'END SEED BLOCK'

#: `BOARD-GRAMMAR.md` §1's CLOSED verb set, extended only by ruling. Bare verbs are
#: matched by EXACT STRING EQUALITY; the three parameterised verbs by the patterns below.
#: Nothing here is a prefix match and nothing is case-folded — see §A64.
BARE_VERBS = (
    'AUTHORED',
    'PRE-FLIGHTED',
    'DISPATCHED',
    'STOPPED',
    'RESUMED',
    'ACCEPTED',
    'CLOSED',
    'RELEASED',
    'RULED',
    'NOTED',
    #: RULED into the set at `BOARD-EVENTS.log:969` (BOARD-GRAMMAR §1), HISTORY-ONLY. The
    #: countersign is a STANDING lifecycle act — recurring, refusable, digest-binding —
    #: and an overflow used routinely is a verb wearing `NOTED`'s clothes. It sits beside
    #: `NOTED` because both are record-plane; it is in `HISTORY_ONLY_KINDS` below, which
    #: is what makes that structural rather than a claim in this comment.
    'COUNTERSIGNED',
)

RE_HELD = re.compile(r'^HELD\(on: (?P<trigger>.+)\)$')
RE_OWED = re.compile(r'^OWED\(by: (?P<seat>[^,]+), act: (?P<act>.+)\)$')
RE_CORRECTED = re.compile(r'^CORRECTED\(supersedes: (?P<target>.+)\)$')
RE_SEATED = re.compile(r'^SEATED\(kind: (?P<kind>[^)]+)\)$')
RE_DISAMBIGUATED = re.compile(
    r'^DISAMBIGUATED\(ending: (?P<ending>[^,]+), ended: (?P<ended>[A-Z][A-Z-]*)\)$')

#: `SEATED`'s kind set, CLOSED and LITERAL. `replacement` is the obvious near-miss and it
#: refuses here rather than folding as something it resembles.
SEATED_KINDS = ('continuation', 'substitution')

#: A `supersedes:` value in the shape the grammar specifies: a date then a verb token.
#: Anything else parses as a well-formed line whose reference is UNRESOLVED.
RE_SUPERSEDES_KEY = re.compile(r'^(?P<date>\d{4}-\d{2}-\d{2})\s+(?P<verb>[A-Z][A-Z-]*)')

RE_DATE = re.compile(r'^\d{4}-\d{2}-\d{2}$')

PENDING_KINDS = ('HELD', 'OWED')

#: THE RECORD-PLANE VERBS. They append to history and they are NOT the item's state: they
#: open nothing, end nothing, and close no pending. The fold's third branch exists for
#: exactly this, so "history only" is a PROPERTY OF THE STRUCTURE rather than a promise in
#: a docstring — a `NOTED` cannot end a pending because the ending branch never sees it.
HISTORY_ONLY_KINDS = ('NOTED', 'SEATED', 'DISAMBIGUATED', 'COUNTERSIGNED')

#: THE ANCHOR'S ALGORITHM, NAMED. It is printed beside every anchor because a digest whose
#: algorithm is unstated is a number, not an anchor. Standard library only.
ANCHOR_ALGO = 'sha256'
#: The `--anchor` value's shape: a sha256 hex digest, lower case, 64 characters.
RE_ANCHOR = re.compile(r'^[0-9a-f]{64}$')

#: THE DISCRIMINATOR FIELD, spelled EXACTLY (EP-28Y). Case-sensitive and space-sensitive,
#: like every other token in this grammar — §A64, and the ruling's own cap: "the refusal
#: is the reason the gaps are visible at all; the answer is never to loosen".
DIGEST_FIELD = 'digest:'
#: The field is FOUND case-insensitively and ACCEPTED only in its exact spelling. Found
#: loosely so a near-miss can be REFUSED: a `Digest:` merely not-found would ride on as
#: trailing alias text and be IGNORED — a reference that LOOKS like it carries a
#: discriminator and does not, which is the silent half of the failure C2b closes.
RE_DIGEST_FIELD = re.compile(r'(?i)digest\s*:\s*(?P<value>\S*)')
#: A discriminator VALUE: lower-case hex, at least one character. No maximum and no
#: minimum beyond one, because SHORTNESS IS NOT THE HAZARD — a prefix too short to be
#: unique is TWICE-MATCHED and refuses whole by name. A length rule here would be a second
#: guarantee competing with the one the ruling actually gives.
RE_DIGEST_VALUE = re.compile(r'^[0-9a-f]+$')
#: THE PAIRING TOKEN'S OPENING LITERAL (EP-30-R4), matched EXACTLY, CASE-SENSITIVELY, and
#: ONLY AT POSITION 0 OF THE CLAUSE. Nothing here is case-folded and nothing is found
#: mid-clause: a clause is free prose, and a token prose can mint is a token this plan's own
#: board events would mint by discussing it.
PAIR_TOKEN = 'PAIRS('
#: The token's fields. `item:` takes no comma (the comma IS the field separator) and the
#: reference takes everything to the closing paren, so `event: <date> <VERB> digest:<hex>`
#: and `event: <date> <VERB>, digest:<hex>` are ONE grammar read by ONE splitter — the
#: separator is not a second spelling of the discriminator, and `digest:` itself is spelled
#: by `split_digest_field` and nowhere else. NOT anchored at the end: the clause carries
#: the token AND the prose that explains it.
RE_PAIRS = re.compile(r'^PAIRS\(item: (?P<item>[^,)]+), event: (?P<event>[^)]+)\)')

#: How many hex characters `--ep` PRINTS. CHOSEN AT THIS PASS AND SAID SO: the anchor
#: prints all 64 and this tool has never stated a prefix length, so nothing was reused
#: here but the ALGORITHM. 12 hex characters is 48 bits over a record of a few hundred
#: lines — short enough to copy, and its uniqueness is enforced by the twice-matched
#: refusal above rather than by this number.
EVENT_DIGEST_PREFIX_LEN = 12

#: THE GLUED-LINE ROSTER (C7-MAINT-BOARD-GLUED-LINES). A prior append that landed WITHOUT
#: its trailing newline glued the next event onto its physical line, so ONE physical line
#: holds TWO terminal events; the fold, reading one event per line, lost the second. The
#: repair NEVER rewrites the record (append-only) and NEVER auto-splits: a byte-level
#: "split every EVT header" detector cannot tell a genuine terminal glue from an EVT string
#: quoted inside a body. :963 quotes a full `COUNTERSIGNED` event mid-body then resumes its
#: narrative -- grammatically it is a complete terminal remainder (COUNTERSIGNED is in the
#: closed set) and a splitter would FABRICATE a phantom act; :4289 carries a partial
#: "EVT | 20" header and a splitter would BRICK on its impossible date. So the four genuine
#: glues are PINNED by line number AND content hash; each is read as its two events, both
#: citing the physical line as coordinate. Any OTHER line whose bytes parse as a
#: full-grammar terminal remainder ALARMS for a hand check and is NEVER split. The hash is
#: `line_digest` -- the anchor's own algorithm, never a second one -- so a pin that no
#: longer matches is a line that MOVED or CHANGED and ALARMS rather than reading a blind
#: offset. The record is append-only, so these line numbers do not shift under lawful
#: appends. Digests verified once at the builder's hand (C7-MAINT-BOARD-GLUED-LINES; mgr's
#: :4514 corrected roster, archi's :4515 WHAT).
PINNED_GLUED_LINES = {
    4236: '0a05755f80a285cf1636d979a5434abdc1c8f7f20870b7a1605e1f9bc9c7d808',
    4248: 'b6546a8b416f06f9af70b72b35aeb50b549fe3b1a4744472a258f6cfbe674391',
    4256: '9b4c52b45a4046adc8225481d0f45de9a1b825199afc0d2f75c49124008b2e2d',
    4361: '44d82f2650bfbbd41f0025a4c1bbf773c369110e9769afd7c499fce18c87ac34',
}

#: THE KNOWN-BENIGN ROSTER (same unit). :963 is a SINGLE `mtr` event whose body QUOTES a
#: full EVT header ("... EP-30-R1 | COUNTERSIGNED | archi | ...") and then RESUMES its
#: narrative. It is grammatically INDISTINGUISHABLE from a genuine glue -- exactly one
#: full-grammar terminal remainder, `COUNTERSIGNED` being in the closed set -- which is the
#: whole reason a live splitter is refused (mgr's :4514 STOP: the :4289 roster wrongly named
#: :963 a glue and omitted the real :4361). It is hand-ruled BODY TEXT: never split, never
#: alarmed. Pinned by hash so that if the line ever changes it ALARMS instead of staying
#: silently exempt.
PINNED_BENIGN_LINES = {
    963: '29e9bbf32f426ac69fe65286ce15a1e469b181218236a3bffedcc2cf7365a8e5',
}

#: The opening of an EVT header, found ANYWHERE on a physical line. Offset 0 is the line's
#: own event; any LATER occurrence is a CANDIDATE second-event boundary, tested for real by
#: parsing both sides (never trusted from the byte match alone).
RE_EVT_HEADER = re.compile(r'EVT\s*\|')


def content_digest(lines):
    """The CONTENT DIGEST of a prefix of the record — the coordinate §1a's hole-fix ruled.

    THE SUBJECT IS THE LINE LIST, which is what `N` addresses, so the digest and its alias
    are functions of one object. CAP, stated rather than left for a reader to discover:
    the lines arrive from `splitlines()`, so line ENDINGS are already normalised and a
    pure CRLF/LF change does not move this digest. Every change that alters, removes or
    reorders a LINE does move it, which is the surgery §1a needs made loud.
    """
    joined = '\n'.join(lines) + '\n'
    return hashlib.new(ANCHOR_ALGO, joined.encode('utf-8')).hexdigest()


def line_digest(text):
    """The CONTENT DIGEST of ONE event line — the discriminator's coordinate (EP-28Y).

    THE ANCHOR'S OWN ALGORITHM, REUSED AND NOT RE-CHOSEN: `content_digest` over a one-line
    list. A second hash here would be a second identity for the same record, which is the
    defect the identity law exists to prevent. The subject is the line AS THE FOLD READS
    IT — `read_event_lines` hands the parser a stripped line, so this is stripped too and
    the two can never disagree about what was digested.
    """
    return content_digest([text.strip()])


def digest_prefix(text):
    """What `--ep` prints and what a seat copies. See `EVENT_DIGEST_PREFIX_LEN`."""
    return line_digest(text)[:EVENT_DIGEST_PREFIX_LEN]


def split_digest_field(text, lineno):
    """Split a reference into (alias text, discriminator or None). SHAPE ONLY.

    The same split `parse_anchor_argument` makes for the anchor, and for the same reason:
    a MALFORMED value is a defect of the line and a NON-MATCHING one is a finding about
    the record. They are refused in different places so a reader can tell them apart.
    """
    hits = list(RE_DIGEST_FIELD.finditer(text))
    if not hits:
        return text, None
    if len(hits) > 1:
        raise BoardRefusal(
            lineno,
            'the reference %r carries %d discriminator fields. An event has ONE identity, '
            'so a reference naming two is either a duplicate or a contradiction and this '
            'fold refuses whole rather than choosing which one it meant.'
            % (text, len(hits)))
    hit = hits[0]
    value = hit.group('value')
    if hit.group(0) != DIGEST_FIELD + value:
        raise BoardRefusal(
            lineno,
            'the discriminator is spelled %r and the grammar spells it %r — exactly, with '
            'no space and no capital. It is refused here rather than left unrecognised, '
            'because an unrecognised one would ride on as alias text and be IGNORED: a '
            'reference that LOOKS like it carries a discriminator and does not.'
            % (hit.group(0), DIGEST_FIELD + '<hex-prefix>'))
    if not RE_DIGEST_VALUE.match(value):
        raise BoardRefusal(
            lineno,
            'the discriminator value %r is not a lower-case hex prefix of a %s digest. '
            'The value is matched LITERALLY: an upper-case or empty one refuses here '
            'rather than folding as something it resembles.' % (value, ANCHOR_ALGO))
    alias = (text[:hit.start()] + ' ' + text[hit.end():]).strip()
    return alias, value


def anchor_text(meta):
    """The one line every fold prints. `N` is the ALIAS; the digest is the coordinate."""
    return ('ANCHOR (N=%d, %s:%s) — this answer is about exactly lines [1..%d] of %s. '
            'N is the human-readable ALIAS of the digest, which is the coordinate.'
            % (meta['anchor_n'], meta['anchor_algo'], meta['anchor_digest'],
               meta['anchor_n'], meta['path']))


class BoardRefusal(Exception):
    """Raised instead of skipping anything. Carries the line number where it refused."""

    def __init__(self, lineno, reason):
        self.lineno = lineno
        self.reason = reason
        super().__init__('line %s: %s' % (lineno, reason))


class BadArgument(Exception):
    """An argument this tool cannot use. Carries the OPTION and a NAMED reason.

    Separate from `BoardRefusal` because the two are different findings about different
    subjects: a refusal says the RECORD could not be read exactly, a bad argument says the
    CALLER handed this tool something it cannot use. They leave with different codes so a
    caller can tell them apart without reading text.
    """

    def __init__(self, option, value, reason):
        self.option = option
        self.value = value
        self.reason = reason
        super().__init__('%s %r: %s' % (option, value, reason))


def parse_date_argument(option, text):
    """A caller-supplied date, or REFUSE by name. Never lets a `ValueError` escape.

    Before EP-28W this validation did not exist and `--stale EP-29` reached
    `datetime.date(*[int(p) for p in ...])`, which raised a raw `ValueError` and left with
    the interpreter's 1 — so a caller could not tell a typed argument from a crashed tool.
    Both halves are checked here: the SHAPE (a wrong shape is what a mistyped item name
    looks like) and the CALENDAR (`2026-13-45` has the right shape and is not a date).
    """
    if not RE_DATE.match(text):
        raise BadArgument(
            option, text,
            'this is not a YYYY-MM-DD date. This tool reads dates only here — an item '
            'name, a bare word or an empty string cannot be one, and it refuses rather '
            'than guessing what you meant.')
    try:
        return datetime.date(*[int(part) for part in text.split('-')])
    except ValueError as exc:
        raise BadArgument(
            option, text,
            'this has a date\'s SHAPE and is not a calendar date (%s).' % exc)


def parse_at_argument(text):
    """`--at N`, or REFUSE by name. The bound against end-of-file is checked at the read,
    where the record's length is known; the SHAPE is checked here, before anything opens.
    """
    if not re.match(r'^[0-9]+$', text.strip()):
        raise BadArgument(
            '--at', text,
            'this is not a line number. A prefix bound is a positive whole number of '
            'lines — a date, a name or a negative reads as a different question and this '
            'tool refuses rather than guessing which.')
    value = int(text.strip())
    if value < 1:
        raise BadArgument(
            '--at', text,
            'a prefix must hold at least one line. [1..0] names nothing, and a fold of '
            'nothing is not a smaller answer, it is a different one.')
    return value


def parse_anchor_argument(text):
    """`--anchor DIGEST`, or REFUSE by name. Shape only — the COMPARISON is a finding
    about the RECORD and leaves with the refusal code, not with this one."""
    if not RE_ANCHOR.match(text.strip()):
        raise BadArgument(
            '--anchor', text,
            'this is not a %s digest (64 lower-case hex characters). The anchor a fold '
            'prints is the value to pass here; the line COUNT is its alias and is not '
            'the coordinate.' % ANCHOR_ALGO)
    return text.strip()


class Event(object):
    __slots__ = ('lineno', 'date', 'item', 'verb', 'kind', 'seat', 'clause',
                 'trigger', 'owed_by', 'act', 'supersedes', 'in_seed',
                 'voided_by', 'closed_by', 'resolution', 'ending', 'candidates',
                 'seated_kind', 'dis_ending', 'dis_ended', 'candidate_events',
                 'disambiguated_by', 'dis_alias', 'dis_digest', 'raw',
                 'pair_item', 'pair_ref', 'pair_alias', 'pair_digest',
                 'pair_target', 'pair_resolution')

    def __init__(self, lineno, date, item, verb, kind, seat, clause):
        self.lineno = lineno
        self.date = date
        self.item = item
        self.verb = verb
        self.kind = kind          # one of BARE_VERBS, or 'HELD' / 'OWED' / 'CORRECTED'
        self.seat = seat
        self.clause = clause
        self.trigger = None       # HELD only
        self.owed_by = None       # OWED only
        self.act = None           # OWED only
        self.supersedes = None    # CORRECTED only
        self.in_seed = False
        self.voided_by = None     # lineno of the CORRECTED that replaced this event
        self.closed_by = None     # lineno of the event that discharged this pending
        self.resolution = None    # CORRECTED only: RESOLVED / AMBIGUOUS / UNRESOLVED
        self.ending = None        # ending events only: 'AMBIGUOUS' / 'NAMED' / 'SINGLE'
        self.candidates = ()      # the open pending kinds this ending could have meant
        self.seated_kind = None   # SEATED only: 'continuation' / 'substitution'
        self.dis_ending = None    # DISAMBIGUATED only: the reference AS WRITTEN
        self.dis_ended = None     # DISAMBIGUATED only: the state it says that ending ended
        self.dis_alias = None     # DISAMBIGUATED only: the reference with the digest removed
        self.dis_digest = None    # DISAMBIGUATED only: the discriminator, or None
        self.raw = None           # the line AS THE FOLD READ IT — the digest's subject
        self.pair_item = None     # PAIRS only: the OTHER item this filing pairs to
        self.pair_ref = None      # PAIRS only: the reference AS WRITTEN
        self.pair_alias = None    # PAIRS only: the reference with the discriminator removed
        self.pair_digest = None   # PAIRS only: the discriminator, or None
        self.pair_target = None   # PAIRS only: the event it resolved to, or None
        self.pair_resolution = None   # PAIRS only: RESOLVED / UNRESOLVED
        self.candidate_events = ()   # ending events: the OPEN PENDING EVENTS at its position
        self.disambiguated_by = None  # ending events: lineno of the DISAMBIGUATED that named it

    @property
    def digest(self):
        """THIS EVENT'S IDENTITY (EP-28Y). The alias is `<date+verb>`; this is the thing."""
        return line_digest(self.raw)

    @property
    def is_pending(self):
        return self.kind in PENDING_KINDS

    @property
    def is_history_only(self):
        """RECORD-PLANE. Appends to history; never the item's state, never an ending."""
        return self.kind in HISTORY_ONLY_KINDS

    def one_line(self):
        tail = (' | ' + self.clause) if self.clause else ''
        return '%s | %s | %s | %s%s' % (self.date, self.item, self.verb, self.seat, tail)


def parse_event_line(text, lineno):
    """Parse ONE `EVT` line, or REFUSE naming this line number. Never returns partial."""
    fields = text.split('|')
    if len(fields) < 5:
        raise BoardRefusal(
            lineno,
            'an EVT line has 5 or 6 fields (EVT | date | item | VERB | seat [| clause]); '
            'found %d' % len(fields))
    if len(fields) > 6:
        # The clause may legitimately contain a pipe; re-split keeping the clause whole.
        fields = text.split('|', 5)
    head = fields[0].strip()
    if head != 'EVT':
        raise BoardRefusal(lineno, 'first field is %r, not %r' % (head, 'EVT'))

    date = fields[1].strip()
    item = fields[2].strip()
    verb = fields[3].strip()
    seat = fields[4].strip()
    clause = fields[5].strip() if len(fields) == 6 else ''

    # The COLUMN-SHIFT detector, and it is deliberately two-sided: field 2 must BE a date
    # and field 3 must NOT be one. A log whose date slid one column right satisfies
    # neither, and a bare "is field 2 a date" test would let the other direction through.
    if not RE_DATE.match(date):
        raise BoardRefusal(lineno, 'field 2 is %r, which is not a YYYY-MM-DD date '
                                   '(a shifted column looks exactly like this)' % date)
    if RE_DATE.match(item):
        raise BoardRefusal(lineno, 'field 3 is %r, which is a date; the item name column '
                                   'has been shifted' % item)
    try:
        datetime.date(*[int(p) for p in date.split('-')])
    except ValueError:
        raise BoardRefusal(lineno, 'field 2 %r is not a real calendar date' % date)
    if not item:
        raise BoardRefusal(lineno, 'item name is empty')
    if not seat:
        raise BoardRefusal(lineno, 'seat is empty')
    if RE_DATE.match(seat):
        raise BoardRefusal(lineno, 'field 5 is %r, which is a date, not a seat' % seat)

    ev = _classify_verb(verb, lineno)
    ev.lineno, ev.date, ev.item, ev.seat, ev.clause = lineno, date, item, seat, clause
    ev.raw = text
    _attach_pair_reference(ev, clause, lineno)
    return ev


def _attach_pair_reference(ev, clause, lineno):
    """Read a CLAUSE-INITIAL `PAIRS(...)` token, or leave the event unpaired (EP-30-R4).

    THE ANCHOR IS THE WHOLE DESIGN AND IT IS ONE LINE OF CODE: a clause that does not
    START with the token literal carries no pairing, whatever else it contains. Prose
    ABOUT pairing — including every board event this pass itself filed — is therefore
    structurally incapable of minting one, rather than merely discouraged from it.

    A clause that DOES start with the token and cannot then be read EXACTLY is REFUSED,
    naming its line. That is this module's first law applied one level in: a near-miss
    SPELLING mints nothing (it is not the token), but a malformed instance of the REAL
    token is a line the fold cannot read exactly, and no partial fold is taken.
    """
    if not clause.startswith(PAIR_TOKEN):
        return
    match = RE_PAIRS.match(clause)
    if match is None:
        raise BoardRefusal(
            lineno,
            'the clause opens with %r and this fold cannot read it as a pairing. The shape '
            'is %s and every part of it is matched LITERALLY — one space after each colon, '
            'a comma between the two fields, and a closing paren. It refuses here rather '
            'than folding as an unpaired clause, because a filing whose author believed it '
            'named its pair and did not is exactly the half-ending this check exists to '
            'report.'
            % (PAIR_TOKEN, 'PAIRS(item: <ITEM>, event: <date> <VERB>[, %s<hex>])'
               % DIGEST_FIELD))
    pair_item = match.group('item').strip()
    reference = match.group('event').strip()
    if not pair_item:
        raise BoardRefusal(lineno, 'the pairing names no item. A pair is ACROSS items and '
                                   'an item-less reference resolves against the wrong '
                                   'population.')
    if not reference:
        raise BoardRefusal(lineno, 'the pairing names no event on %r' % pair_item)
    alias, digest = split_digest_field(reference, lineno)
    if not alias:
        raise BoardRefusal(
            lineno,
            'the pairing carries a discriminator and NO <date+verb> alias. A bare digest '
            'NEVER BINDS ALONE (BOARD-GRAMMAR §1): the alias is what a human reads and the '
            'two must agree.')
    ev.pair_item = pair_item
    ev.pair_ref = reference
    ev.pair_alias = alias
    ev.pair_digest = digest


def _classify_verb(verb, lineno):
    """Match the CLOSED verb set literally and case-sensitively, or REFUSE."""
    if verb in BARE_VERBS:
        return Event(lineno, None, None, verb, verb, None, None)
    m = RE_HELD.match(verb)
    if m:
        ev = Event(lineno, None, None, verb, 'HELD', None, None)
        ev.trigger = m.group('trigger').strip()
        if not ev.trigger:
            raise BoardRefusal(lineno, 'HELD names no trigger')
        return ev
    m = RE_OWED.match(verb)
    if m:
        ev = Event(lineno, None, None, verb, 'OWED', None, None)
        ev.owed_by = m.group('seat').strip()
        ev.act = m.group('act').strip()
        if not ev.owed_by or not ev.act:
            raise BoardRefusal(lineno, 'OWED names no seat or no act')
        return ev
    m = RE_CORRECTED.match(verb)
    if m:
        ev = Event(lineno, None, None, verb, 'CORRECTED', None, None)
        ev.supersedes = m.group('target').strip()
        if not ev.supersedes:
            raise BoardRefusal(lineno, 'CORRECTED names no target')
        return ev
    m = RE_SEATED.match(verb)
    if m:
        ev = Event(lineno, None, None, verb, 'SEATED', None, None)
        ev.seated_kind = m.group('kind').strip()
        if ev.seated_kind not in SEATED_KINDS:
            raise BoardRefusal(
                lineno,
                'SEATED kind %r is not in the CLOSED kind set %s. The set is matched '
                'LITERALLY: `replacement` is a near-miss for `substitution` and refuses '
                'here rather than folding as the word it resembles.'
                % (ev.seated_kind, list(SEATED_KINDS)))
        return ev
    m = RE_DISAMBIGUATED.match(verb)
    if m:
        ev = Event(lineno, None, None, verb, 'DISAMBIGUATED', None, None)
        ev.dis_ending = m.group('ending').strip()
        ev.dis_ended = m.group('ended').strip()
        if not ev.dis_ending or not ev.dis_ended:
            raise BoardRefusal(lineno, 'DISAMBIGUATED names no ending or no ended state')
        # THE DISCRIMINATOR, SHAPE-CHECKED HERE (EP-28Y). Only this verb's reference gains
        # it: `CORRECTED`'s provenance reference is lossy BY RULING and gains nothing.
        ev.dis_alias, ev.dis_digest = split_digest_field(ev.dis_ending, lineno)
        if not ev.dis_alias:
            raise BoardRefusal(
                lineno,
                'the reference carries a discriminator and NO <date+verb> alias. A line '
                'number or a bare digest NEVER BINDS ALONE (BOARD-GRAMMAR §1): the alias '
                'is what a human reads and the two must agree.')
        return ev
    raise BoardRefusal(
        lineno,
        'verb %r is not in the CLOSED set (BOARD-GRAMMAR.md §1). The set is matched '
        'LITERALLY and CASE-SENSITIVELY, so a near-miss spelling refuses here rather '
        'than folding as something it resembles.' % verb)


def _terminal_remainder_splits(text, lineno):
    """Offsets where `text` divides into TWO complete lawful events: a complete PREFIX and a
    complete TERMINAL REMAINDER running to the line's end. NON-REFUSING by construction -- a
    candidate boundary whose prefix or remainder does not parse EXACTLY is simply not a
    split, it is body text -- so `EVT | 20` mid-body (a partial header, bad date) yields no
    split and can never brick the fold. This is the recognition the whole unit turns on, and
    it DELIBERATELY cannot tell a genuine glue from a full event quoted inside a body (:963);
    that judgement belongs to the pinned rosters above, never to this function.
    """
    offsets = []
    for match in RE_EVT_HEADER.finditer(text):
        i = match.start()
        if i == 0:
            continue
        try:
            parse_event_line(text[:i].strip(), lineno)
            parse_event_line(text[i:].strip(), lineno)
        except BoardRefusal:
            continue
        offsets.append(i)
    return offsets


def read_events(path, at=None):
    """Read the log into (events, meta). REFUSES; never returns a partial fold.

    `at` is the PREFIX BOUND of §1a: the fold reads lines [1..at] and NOTHING BEYOND, so
    appends landing during an arm cannot perturb the taking. `at` beyond end-of-file is a
    BAD ARGUMENT — a caller asking about a coordinate the record does not have is told
    about the argument, with the code that says so, and never handed the whole file
    instead. `at` is refused BEFORE any folding, for the same reason `--stale`'s is.
    """
    with open(path, 'r', encoding='utf-8') as handle:
        raw = handle.read().splitlines()
    if at is not None:
        if at > len(raw):
            raise BadArgument(
                '--at', at,
                'the record holds %d line(s), so there is no prefix [1..%d]. This tool '
                'refuses rather than quietly folding the whole file, because a caller '
                'asking about a coordinate that does not exist would then receive an '
                'answer about a different one.' % (len(raw), at))
        raw = raw[:at]
    return read_event_lines(raw, path)


def read_event_lines(raw, label):
    """The whole read path, over LINES ALREADY IN MEMORY.

    Split out from `read_events` for ONE reason and it is the module's first law: the
    positive control needs to fold a synthetic log, and a control that wrote that log to
    a temp file would make this tool a WRITER. It is the same door the file path uses —
    the control exercises the real reader, not a second one.
    """
    seed_start = seed_end = None
    for idx, text in enumerate(raw, start=1):
        stripped = text.strip()
        if not stripped.startswith('#'):
            continue
        if SEED_END_MARK in stripped:
            if seed_end is not None:
                raise BoardRefusal(idx, 'a second END SEED BLOCK marker')
            seed_end = idx
        elif SEED_START_MARK in stripped:
            if seed_start is not None:
                raise BoardRefusal(idx, 'a second SEED BLOCK marker')
            seed_start = idx

    if seed_start is None:
        raise BoardRefusal(0, 'no SEED BLOCK marker in the body. The fold starts at the '
                              'seed and ABSENCE OF EVENTS READS AS NOT-STARTED ONLY '
                              'BECAUSE THE SEED IS COMPLETE; without the seed that '
                              'reading has no ground and this tool will not guess one.')
    if seed_end is None:
        raise BoardRefusal(seed_start, 'a SEED BLOCK marker with no END SEED BLOCK marker')
    if seed_end < seed_start:
        raise BoardRefusal(seed_end, 'END SEED BLOCK appears before SEED BLOCK')

    events = []
    glue_notices = []
    glue_alarms = []
    for idx, text in enumerate(raw, start=1):
        stripped = text.strip()
        if not stripped or stripped.startswith('#'):
            continue
        splits = _terminal_remainder_splits(stripped, idx)
        pinned_glue = idx in PINNED_GLUED_LINES
        pinned_benign = idx in PINNED_BENIGN_LINES
        if pinned_glue or pinned_benign:
            roster = PINNED_GLUED_LINES if pinned_glue else PINNED_BENIGN_LINES
            want = roster[idx]
            got = line_digest(stripped)
            if got != want:
                # A PINNED LINE MOVED OR CHANGED (stop condition b). Never a blind offset
                # read: ALARM, name the line, and fold it as ONE event so the fold stays
                # readable and nothing is fabricated. Re-pinning is a hand act under a ruling.
                glue_alarms.append(
                    ':%d - a PINNED %s line no longer matches its content hash (want '
                    '%s:%s, got %s:%s): the line moved or changed. Folded as a SINGLE event '
                    'and NOT split at a blind offset; hand-verify and re-pin.'
                    % (idx, 'GLUED' if pinned_glue else 'BENIGN',
                       ANCHOR_ALGO, want[:16], ANCHOR_ALGO, got[:16]))
                seg_events = [parse_event_line(stripped, idx)]
            elif pinned_glue:
                if len(splits) != 1:
                    # A matching-hash glue pin resolves to exactly one terminal-remainder
                    # split (verified at the builder's hand). A departure is an alarm, never
                    # a guess between offsets.
                    glue_alarms.append(
                        ':%d - a pinned GLUED line whose hash matches did not split into '
                        'exactly two events (%d split point(s)); folded as a single event, '
                        'hand-verify.' % (idx, len(splits)))
                    seg_events = [parse_event_line(stripped, idx)]
                else:
                    off = splits[0]
                    first = parse_event_line(stripped[:off].strip(), idx)
                    second = parse_event_line(stripped[off:].strip(), idx)
                    seg_events = [first, second]
                    glue_notices.append(
                        ':%d - one physical line holds 2 terminal events, read as two, the '
                        'record never rewritten: [%s | %s | %s] + [%s | %s | %s].'
                        % (idx, first.item, first.verb, first.seat,
                           second.item, second.verb, second.seat))
            else:
                # PINNED BENIGN: a full event is quoted inside this body and it is hand-ruled
                # body text. Folded as ONE event, never split, never alarmed.
                seg_events = [parse_event_line(stripped, idx)]
        elif splits:
            # A CANDIDATE OUTSIDE THE PINNED ROSTER. After the append gate self-heals a
            # missing terminator (A1) such a line should be impossible, so this is a
            # hand-verified addition under a new ruling or the gate's own failure surfacing.
            # It is NEVER split and NEVER fabricated: folded as ONE event, the fold stays
            # readable, and the line is named for a hand check.
            glue_alarms.append(
                ':%d - a full-grammar TERMINAL REMAINDER was found on a line OUTSIDE the '
                'pinned glued roster. It is NOT split and NOT folded as a second event; the '
                'fold stays readable. Hand-verify: a new genuine glue (re-pin under a '
                'ruling) or the append gate failed.' % idx)
            seg_events = [parse_event_line(stripped, idx)]
        else:
            seg_events = [parse_event_line(stripped, idx)]
        for ev in seg_events:
            ev.in_seed = seed_start < idx < seed_end
            events.append(ev)

    meta = {
        'path': label,
        'lines': len(raw),
        'anchor_n': len(raw),
        'anchor_algo': ANCHOR_ALGO,
        'anchor_digest': content_digest(raw),
        'events': len(events),
        'seed_start': seed_start,
        'seed_end': seed_end,
        'seed_events': sum(1 for e in events if e.in_seed),
        'pre_seed_events': sum(1 for e in events if e.lineno < seed_start),
        'post_seed_events': sum(1 for e in events if e.lineno > seed_end),
        'glue_notices': glue_notices,
        'glue_alarms': glue_alarms,
    }
    return events, meta


class ItemState(object):
    def __init__(self, name):
        self.name = name
        self.history = []
        self.state = None          # latest STATE-BEARING event; None if only record-plane
        self.last_event = None     # latest event of ANY kind, including history-only
        self.pendings = {}         # 'HELD' / 'OWED' -> the open Event
        self.ambiguous = []        # CORRECTED events whose reference had >1 candidate
        self.unresolved = []       # CORRECTED events whose reference matched nothing
        self.ambiguous_endings = []  # (event, candidate kinds) — clause 3 of the pair law
        self.pairs = []            # events on this item carrying a RESOLVED PAIRS token
        self.unresolved_pairs = []   # events whose PAIRS token matched no earlier event

    @property
    def last_date(self):
        return self.history[-1].date if self.history else None

    def open_pendings(self):
        return [self.pendings[k] for k in PENDING_KINDS if k in self.pendings]


def fold(events):
    """Fold seed first (it is the founding), then every other event in FILE ORDER."""
    ordered = [e for e in events if e.in_seed] + [e for e in events if not e.in_seed]
    resolutions = _resolve_disambiguations(ordered)
    _resolve_pairs(ordered)
    board = {}
    for ev in ordered:
        item = board.setdefault(ev.item, ItemState(ev.item))
        if ev.pair_resolution == 'RESOLVED':
            item.pairs.append(ev)
        elif ev.pair_resolution == 'UNRESOLVED':
            item.unresolved_pairs.append(ev)
        named = None
        if ev.kind == 'CORRECTED':
            named = _apply_supersedes(item, ev)
        if ev.is_history_only:
            # THE THIRD BRANCH, and it is what makes "history only" structural rather than
            # asserted: a record-plane verb never reaches the pending branch and never
            # reaches the ending branch, so it CANNOT open or close anything, and it does
            # not become the item's state below.
            pass
        elif ev.is_pending:
            prior = item.pendings.get(ev.kind)
            if prior is not None:
                prior.closed_by = ev.lineno
            item.pendings[ev.kind] = ev
        else:
            _apply_ending(item, ev, named, resolutions.get(id(ev)))
        item.history.append(ev)
        item.last_event = ev
        if not ev.is_history_only:
            item.state = ev
    return board


def _pin_by_digest(ev, ordered, candidates):
    """Pin a reference by its DISCRIMINATOR — the event's CONTENT (EP-28Y).

    Matched over EVERY event the fold holds and not only over the alias's candidates, so
    a prefix that is not unique in the RECORD is twice-matched and refuses. A prefix
    checked only inside the candidate set would be an identity that means different things
    in different neighbourhoods, which is not an identity.

    The alias must then AGREE: the pinned event must be one the `<date+verb>` names. The
    ruling lets a line number ride beside the digest as the human-readable alias, and an
    alias nobody checks is a comment — a reader would be reading one event while the fold
    acted on another.

    A THIN WRAPPER SINCE EP-30-R4, AND THE SIGNATURE IS DELIBERATELY UNCHANGED: the pairing
    reference needs the SAME identity rule against a DIFFERENT item, so the rule moved to
    `_pin_reference_by_digest` and this door stayed exactly where it was. One rule, two
    callers, no second spelling — and the suite's two red worlds still neuter the
    DISAMBIGUATED path by replacing this name, which is the path they are about.
    """
    return _pin_reference_by_digest(ev.lineno, ev.dis_digest, ev.dis_alias, ev.item,
                                    ordered, candidates)


def _pin_reference_by_digest(lineno, want, alias, item_name, ordered, candidates):
    """THE IDENTITY RULE ITSELF, over any reference that carries a discriminator."""
    matched = [e for e in ordered if e.digest.startswith(want)]
    if not matched:
        raise BoardRefusal(
            lineno,
            'the discriminator %s%s matches NO event line in this record. A digest is the '
            'event\'s identity, so an unmatched one names nothing at all — and it refuses '
            'HERE whether or not the alias %r would have resolved on its own. A carried '
            'digest is CHECKED ALWAYS (BOARD-GRAMMAR §1: "unmatched ... refuses the fold '
            'whole", unqualified), because `--ep` prints digests so they are copied, and '
            'a stale copy that folded silently would make the taught path the unchecked '
            'one.' % (DIGEST_FIELD, want, alias))
    if len(matched) > 1:
        raise BoardRefusal(
            lineno,
            'the discriminator %s%s matches %d event lines (%s) and it must match exactly '
            'one. THIS FOLD NEVER TAKES THE LONGEST MATCH AND NEVER TAKES THE FIRST: a '
            'prefix short enough to collide has not identified anything, and lengthening '
            'it is the writer\'s act, not this tool\'s. `--ep` prints %d characters, which '
            'is enough here.'
            % (DIGEST_FIELD, want, len(matched),
               ', '.join(':%d' % m.lineno for m in matched), EVENT_DIGEST_PREFIX_LEN))
    target = matched[0]
    if target not in candidates:
        raise BoardRefusal(
            lineno,
            'the discriminator %s%s pins the event at :%d, and the alias %r names %d '
            'earlier event(s) on %s — the pinned event is not among them. THE ALIAS AND '
            'THE DIGEST DISAGREE, and this fold refuses whole rather than acting on one '
            'while a reader reads the other. A line number or a date+verb rides beside '
            'the digest as the HUMAN-READABLE ALIAS (BOARD-GRAMMAR §1); an alias nobody '
            'checks is a comment.'
            % (DIGEST_FIELD, want, target.lineno, alias, len(candidates), item_name))
    return target


def _resolve_pairs(ordered):
    """Pin every clause-initial `PAIRS(...)` to at most one earlier event (EP-30-R4).

    Annotates the token-carrying events in place; folds NOTHING. A pairing is a NAMING and
    never a state claim, which is why an unresolvable one is REPORTED where a
    `DISAMBIGUATED`'s is refused: the filing still carries its own state on its own line,
    exactly as a `CORRECTED` with a free-text `supersedes:` does.

    CANDIDATES ARE STRICTLY EARLIER, by the same rule `_resolve_disambiguations` uses. The
    convention at `:1134` is that the SECOND filing names the FIRST, so a forward reference
    is not a pairing this record can have; it reports UNRESOLVED rather than reaching ahead.
    """
    positions = {id(e): i for i, e in enumerate(ordered)}
    for ev in ordered:
        if ev.pair_item is None:
            continue
        here = positions[id(ev)]
        key = RE_SUPERSEDES_KEY.match(ev.pair_alias)
        candidates = []
        if key is not None:
            want_date, want_verb = key.group('date'), key.group('verb')
            candidates = [e for e in ordered
                          if e.item == ev.pair_item and positions[id(e)] < here
                          and e.date == want_date and e.kind == want_verb]
        if ev.pair_digest is not None:
            # VALIDATED ALWAYS, exactly as the discriminator ruling has it everywhere else:
            # an unmatched or twice-matched digest, or one whose alias names a different
            # event, REFUSES WHOLE — whether or not the alias would have resolved alone.
            ev.pair_target = _pin_reference_by_digest(
                ev.lineno, ev.pair_digest, ev.pair_alias, ev.pair_item, ordered, candidates)
            ev.pair_resolution = 'RESOLVED'
        elif len(candidates) > 1:
            raise BoardRefusal(
                ev.lineno,
                'the pairing names %d events on %s (%s) and it must name EXACTLY ONE. A '
                'pairing that could mean either of two filings has not named one, and this '
                'fold refuses whole rather than pairing to whichever it met first. THE '
                'DISCRIMINATOR IS REQUIRED HERE (BOARD-GRAMMAR §1): carry '
                '`%s<hex-prefix>`, and `--ep %s` prints the prefix of every one of these '
                'so it is COPIED, not computed. The candidates are %s.'
                % (len(candidates), ev.pair_item,
                   ', '.join(':%d' % c.lineno for c in candidates), DIGEST_FIELD,
                   ev.pair_item,
                   ', '.join(':%d %s%s' % (c.lineno, DIGEST_FIELD, digest_prefix(c.raw))
                             for c in candidates)))
        elif len(candidates) == 1:
            ev.pair_target = candidates[0]
            ev.pair_resolution = 'RESOLVED'
        else:
            # NAMES NOTHING THIS FOLD HAS SEEN — an unknown item, or an alias no earlier
            # event on a known item matches. REPORTED to the writer and folded as no state.
            ev.pair_resolution = 'UNRESOLVED'


def _pair_side_stands(item, ev):
    """DOES THE RECORD STILL HOLD THIS FILING AS LIVE? (EP-30-R4, derived — see the module
    docstring, where the derivation is declared so it can be attacked rather than inherited.)

    TRUE when the filing is the item's current STATE, or is an OPEN PENDING on it. FALSE
    when a later lifecycle event has moved past it. Nothing here classifies verbs into
    terminal and non-terminal: that would mint a closed set this pass has no licence for,
    and it is not needed — the fold already knows what it still holds.
    """
    if item is None:
        return False
    if item.state is ev:
        return True
    return any(pend is ev for pend in item.open_pendings())


def half_ended_pairs(board):
    """Named pairs with ONE side standing and the other ended. Rows, never a count.

    A pair not yet ended ANYWHERE is work in progress and is not a defect. A pair ended on
    BOTH sides is a decision correctly closed twice. Only the disagreement is reported, and
    it is reported at EVERY taking rather than discovered by a reader with fresh eyes.
    """
    rows = []
    for name in sorted(board):
        item = board[name]
        for ev in item.pairs:
            target = ev.pair_target
            other = board.get(target.item)
            here = _pair_side_stands(item, ev)
            there = _pair_side_stands(other, target)
            if here != there:
                rows.append((item, ev, here, other, target, there))
    return rows


def _resolve_disambiguations(ordered):
    """Pin every DISAMBIGUATED to EXACTLY ONE earlier event, or REFUSE THE FOLD WHOLE.

    Returns {id(target_event): (disambiguated_event, ended_state)}.

    THE REFERENCE IS THIS VERB'S ENTIRE SEMANTIC CONTENT, which is why this is a refusal
    and `CORRECTED`'s unresolved reference is a report: a `CORRECTED` that cannot pin its
    target still carries its own state on its own line, and the mentor ruled the standing
    unresolved set STANDS. A `DISAMBIGUATED` that cannot pin its target says NOTHING —
    it is a state claim that failed while looking like one that landed, and the record
    would then hold less than the truth in the file built so that cannot happen.
    """
    positions = {id(e): i for i, e in enumerate(ordered)}
    resolutions = {}
    claimed = {}
    for ev in ordered:
        if ev.kind != 'DISAMBIGUATED':
            continue
        key = RE_SUPERSEDES_KEY.match(ev.dis_alias)
        if key is None:
            raise BoardRefusal(
                ev.lineno,
                'DISAMBIGUATED names the ending %r, which is not a <date+verb> reference '
                '(BOARD-GRAMMAR.md §1). This verb\'s reference IS its whole content, so a '
                'reference this fold cannot read refuses the file rather than folding as '
                'a claim that quietly did nothing.' % ev.dis_ending)
        want_date, want_verb = key.group('date'), key.group('verb')
        here = positions[id(ev)]
        candidates = [e for e in ordered
                      if e.item == ev.item and positions[id(e)] < here
                      and e.date == want_date and e.kind == want_verb]
        if ev.dis_digest is not None:
            target = _pin_by_digest(ev, ordered, candidates)
        elif len(candidates) != 1:
            raise BoardRefusal(
                ev.lineno,
                'DISAMBIGUATED(ending: %s) resolves to %d earlier event(s) on %s and it '
                'must resolve to EXACTLY ONE%s. Zero means it names nothing; two or more '
                'means it does not say which. Either way it is a state claim that cannot '
                'act, and the fold refuses WHOLE rather than letting it read as landed.%s'
                % (ev.dis_ending, len(candidates), ev.item,
                   '' if not candidates else ' (lines %s)'
                   % ', '.join(':%d' % c.lineno for c in candidates),
                   '' if len(candidates) < 2 else
                   ' THE ALIAS IS AMBIGUOUS AND THE DISCRIMINATOR IS REQUIRED HERE '
                   '(BOARD-GRAMMAR §1): carry `%s<hex-prefix>`, and `--ep %s` prints the '
                   'prefix of every one of these so it is COPIED, not computed. The '
                   'candidates are %s.'
                   % (DIGEST_FIELD, ev.item,
                      ', '.join(':%d %s%s' % (c.lineno, DIGEST_FIELD, digest_prefix(c.raw))
                                for c in candidates))))
        else:
            target = candidates[0]
        prior = claimed.get(id(target))
        if prior is not None:
            raise BoardRefusal(
                ev.lineno,
                'the ending at :%d was already disambiguated at :%d (ended: %s) and this '
                'line disambiguates it again (ended: %s). DERIVED HERE, declared loudly so '
                'it can be attacked rather than inherited: one past ending ended ONE state, '
                'so a second resolution of it is either a duplicate or a contradiction, '
                'and this record is repaired by CORRECTED rather than by re-stating. '
                'Refusing whole is the estate\'s standing preference over proceeding on a '
                'subject that carries two incompatible claims.'
                % (target.lineno, prior[0].lineno, prior[1], ev.dis_ended))
        claimed[id(target)] = (ev, ev.dis_ended)
        resolutions[id(target)] = (ev, ev.dis_ended)
    return resolutions


def _apply_ending(item, ev, named, resolution=None):
    """THE PAIR LAW'S CLAUSE 3 (`BOARD-GRAMMAR.md` §1). An ending event, applied.

    `resolution` is a later `DISAMBIGUATED` naming THIS ending, applied HERE — at the
    ending's own position — rather than at the DISAMBIGUATED's. That placement is the
    whole of EP-28X W3: every later event then sees the state the record says was ended,
    where a resolution that only stamped a line number would leave a later ending still
    reported ambiguous over a state the record has since said was closed.

    THREE CASES, and the boundary between them is where DETERMINISM ENDS rather than
    anywhere chosen:

      NAMED      the ending named one pending — the only mechanism the closed verb set
                 has for that is `CORRECTED(supersedes: <date+verb>)` resolving to it,
                 and `_apply_supersedes` has already closed exactly that one. EVERY OTHER
                 PENDING STANDS. Before EP-28W the branch below then closed the others
                 too, so a `CORRECTED` naming the HELD silently also ended the OWED.
      AMBIGUOUS  two or more pendings stand open and the ending names none of them. It
                 resolves to more than one candidate, so NOTHING IS CLOSED, the candidate
                 set is recorded against the ending's own line, and both states stay
                 displayed. The fold reports; it never picks.
      SINGLE     one pending (or none) stands open. An unnamed ending resolves to exactly
                 one candidate, so it closes it — byte-for-byte the EP-28U behaviour, and
                 that is clause 3's own boundary: standing history keeps its meaning.
    """
    open_now = item.open_pendings()
    ev.candidate_events = tuple(open_now)
    if resolution is not None:
        dis, ended = resolution
        allowed = (named,) if named is not None else tuple(p.kind for p in open_now)
        if ended not in allowed:
            raise BoardRefusal(
                dis.lineno,
                'DISAMBIGUATED says the ending at :%d ended %r, and %r is not in that '
                'ending\'s candidate set %s — the pendings standing open at ITS OWN '
                'position. A resolution naming a state that was not a candidate does not '
                'resolve anything, so the fold refuses WHOLE rather than recording a '
                'closure the record never had a candidate for.'
                % (ev.lineno, ended, ended, list(allowed) or ['(none open)']))
        ev.ending = 'NAMED'
        ev.candidates = (ended,)
        ev.disambiguated_by = dis.lineno
        for open_ev in open_now:
            if open_ev.kind == ended:
                open_ev.closed_by = ev.lineno       # AS OF THE ENDING'S OWN POSITION.
                if item.pendings.get(ended) is open_ev:
                    del item.pendings[ended]
        return                                      # every other pending STANDS.
    if named is not None:
        ev.ending = 'NAMED'
        ev.candidates = (named,)
        return
    if len(open_now) >= 2:
        ev.ending = 'AMBIGUOUS'
        ev.candidates = tuple(p.kind for p in open_now)
        item.ambiguous_endings.append((ev, ev.candidates))
        return                                   # CLOSES NOTHING. This is the whole rule.
    ev.ending = 'SINGLE'
    ev.candidates = tuple(p.kind for p in open_now)
    for open_ev in open_now:
        open_ev.closed_by = ev.lineno
    item.pendings.clear()


def _apply_supersedes(item, ev):
    """Void the target of a CORRECTED, and REPORT when the key does not identify one.

    RETURNS the KIND of the open pending this event named, or None. That return is what
    makes clause 3 decidable: a `CORRECTED` resolving to an open pending IS an ending that
    names the one it ends, and it is the only naming mechanism the closed verb set has.
    """
    key = RE_SUPERSEDES_KEY.match(ev.supersedes)
    if key is None:
        ev.resolution = 'UNRESOLVED'
        item.unresolved.append(ev)
        return None
    want_date, want_verb = key.group('date'), key.group('verb')
    candidates = [e for e in item.history
                  if e.date == want_date and e.kind == want_verb and e.voided_by is None]
    if not candidates:
        ev.resolution = 'UNRESOLVED'
        item.unresolved.append(ev)
        return None
    target = candidates[-1]
    target.voided_by = ev.lineno
    named = None
    if target.kind in PENDING_KINDS and item.pendings.get(target.kind) is target:
        target.closed_by = ev.lineno
        del item.pendings[target.kind]
        named = target.kind
    if len(candidates) > 1:
        ev.resolution = 'AMBIGUOUS'
        item.ambiguous.append((ev, len(candidates)))
    else:
        ev.resolution = 'RESOLVED'
    return named


# ---------------------------------------------------------------------------
# THE POSITIVE CONTROL. It runs on EVERY invocation, never once.
#
# Everything this tool reports is a set or a count over an ABSENCE — no stale items, no
# unknown names, no malformed lines — so a structurally broken fold returns exactly the
# clean answer a healthy one returns, and a zero closes a question a wrong number would
# reopen. The control folds a synthetic log holding a KNOWN-PRESENT case of every shape
# and requires each one found; a failure makes every count UNINTERPRETABLE.
# ---------------------------------------------------------------------------

CONTROL_LOG = """\
# synthetic — planted by positive_control(), never read from disk
EVT | 2026-03-01 | CTRL-EARLY | AUTHORED | ctl | pre-seed early adoption, folded after the seed
# ==================== SEED BLOCK ====================
EVT | 2026-02-01 | CTRL-A | AUTHORED | ctl |
EVT | 2026-02-01 | CTRL-STALE | HELD(on: a world that has not moved) | ctl |
EVT | 2026-02-01 | CTRL-PAIR | AUTHORED | ctl |
# ================== END SEED BLOCK ==================
EVT | 2026-03-01 | CTRL-A | PRE-FLIGHTED | ctl |
EVT | 2026-03-01 | CTRL-A | DISPATCHED | ctl |
EVT | 2026-03-01 | CTRL-A | STOPPED | ctl |
EVT | 2026-03-01 | CTRL-A | RESUMED | ctl |
EVT | 2026-03-01 | CTRL-A | RULED | ctl |
EVT | 2026-03-01 | CTRL-A | RELEASED | ctl |
EVT | 2026-03-01 | CTRL-A | ACCEPTED | ctl |
EVT | 2026-03-01 | CTRL-A | CLOSED | ctl |
EVT | 2026-03-01 | CTRL-PAIR | HELD(on: CTRL-A) | ctl | waits on the world
EVT | 2026-03-01 | CTRL-PAIR | OWED(by: ctl, act: sit down and do it) | ctl | waits on a seat
EVT | 2026-03-01 | CTRL-SUP | AUTHORED | ctl | the target
EVT | 2026-03-02 | CTRL-SUP | CORRECTED(supersedes: 2026-03-01 AUTHORED) | ctl | replaces it
EVT | 2026-03-02 | CTRL-SUP | CORRECTED(supersedes: a free-text reference) | ctl |
EVT | 2026-03-01 | CTRL-AMBIG | HELD(on: a world) | ctl | the pair, half one
EVT | 2026-03-01 | CTRL-AMBIG | OWED(by: ctl, act: a ruling) | ctl | the pair, half two
EVT | 2026-03-02 | CTRL-AMBIG | ACCEPTED | ctl | names NEITHER -> AMBIGUOUS, closes nothing
EVT | 2026-03-01 | CTRL-NAMED | HELD(on: a world) | ctl | the pair, half one
EVT | 2026-03-01 | CTRL-NAMED | OWED(by: ctl, act: a ruling) | ctl | the pair, half two
EVT | 2026-03-02 | CTRL-NAMED | CORRECTED(supersedes: 2026-03-01 HELD) | ctl | names the HELD
EVT | 2026-03-01 | CTRL-SINGLE | HELD(on: a world) | ctl | ONE state open
EVT | 2026-03-02 | CTRL-SINGLE | ACCEPTED | ctl | deterministic -> closes it, as at EP-28U
EVT | 2026-03-01 | CTRL-NOTE | AUTHORED | ctl | a state that must be left exactly alone
EVT | 2026-03-01 | CTRL-NOTE | HELD(on: a world) | ctl | a pending that must be left open
EVT | 2026-03-02 | CTRL-NOTE | NOTED | ctl | the OVERFLOW clause: an act with no verb, filed
EVT | 2026-03-02 | CTRL-NOTE | SEATED(kind: continuation) | ctl | same seat, post-compaction
EVT | 2026-03-02 | CTRL-NOTE | SEATED(kind: substitution) | ctl | a different reasoner
EVT | 2026-03-02 | CTRL-NOTE | COUNTERSIGNED | ctl | planted on the item holding an OPEN HELD, so a countersign that is NOT history-only would END it
EVT | 2026-03-01 | CTRL-NEWITEM | NOTED | ctl | a record-plane FIRST event: history, no state
EVT | 2026-03-01 | CTRL-DIS | HELD(on: a world) | ctl | the pair, half one
EVT | 2026-03-01 | CTRL-DIS | OWED(by: ctl, act: a ruling) | ctl | the pair, half two
EVT | 2026-03-02 | CTRL-DIS | ACCEPTED | ctl | ambiguous when written
EVT | 2026-03-04 | CTRL-DIS | DISAMBIGUATED(ending: 2026-03-02 ACCEPTED, ended: HELD) | ctl | it ended the HELD; the OWED STANDS
EVT | 2026-03-01 | CTRL-DIS2 | HELD(on: a world) | ctl | the pair, half one
EVT | 2026-03-01 | CTRL-DIS2 | OWED(by: ctl, act: a ruling) | ctl | the pair, half two
EVT | 2026-03-02 | CTRL-DIS2 | ACCEPTED | ctl | ambiguous when written
EVT | 2026-03-03 | CTRL-DIS2 | RULED | ctl | a SECOND ending, ambiguous until the resolve lands
EVT | 2026-03-04 | CTRL-DIS2 | DISAMBIGUATED(ending: 2026-03-02 ACCEPTED, ended: HELD) | ctl | AS OF :ACCEPTED, so the RULED now sees ONE open state
EVT | 2026-03-01 | CTRL-PAIR-CLEAN-A | RULED | ctl | one decision, filed by the seat that witnessed it
EVT | 2026-03-01 | CTRL-PAIR-CLEAN-B | STOPPED | ctl | PAIRS(item: CTRL-PAIR-CLEAN-A, event: 2026-03-01 RULED) the SAME decision, filed by the other seat that witnessed it
EVT | 2026-03-02 | CTRL-PAIR-CLEAN-A | CLOSED | ctl | ended here
EVT | 2026-03-02 | CTRL-PAIR-CLEAN-B | RESUMED | ctl | AND ended here — a decision filed twice, ended twice. THE CHECK MUST BE SILENT
EVT | 2026-03-01 | CTRL-PAIR-HALF-A | RULED | ctl | one decision, filed by the seat that witnessed it
EVT | 2026-03-01 | CTRL-PAIR-HALF-B | STOPPED | ctl | PAIRS(item: CTRL-PAIR-HALF-A, event: 2026-03-01 RULED) the SAME decision, filed by the other seat that witnessed it
EVT | 2026-03-02 | CTRL-PAIR-HALF-A | CLOSED | ctl | ended HERE AND NOWHERE ELSE — the half-ending. THE CHECK MUST SPEAK, ONCE
EVT | 2026-03-01 | CTRL-PAIR-OPEN-A | RULED | ctl | one decision, filed by the seat that witnessed it
EVT | 2026-03-01 | CTRL-PAIR-OPEN-B | STOPPED | ctl | PAIRS(item: CTRL-PAIR-OPEN-A, event: 2026-03-01 RULED) the SAME decision, filed by the other seat; neither side has ended. THE CHECK MUST BE SILENT — work in progress is not a defect
EVT | 2026-03-01 | CTRL-PAIR-POS-A | RULED | ctl | the ENDED half of the position battery's pair
EVT | 2026-03-02 | CTRL-PAIR-POS-A | CLOSED | ctl | ended, so any pairing to its RULED is half-ended THE MOMENT ONE IS MINTED
"""

#: Every verb of the CLOSED set must appear in the control log, so a verb added to the
#: set without a planted case fails here rather than shipping unexercised.
_CONTROL_VERB_KINDS = tuple(BARE_VERBS) + PENDING_KINDS + ('CORRECTED', 'SEATED',
                                                          'DISAMBIGUATED')

#: THE NEAR-MISS SET USES THE RECORD'S OWN MINTS VERBATIM. `NOTED-AS-RULED` and
#: `NOTED-PENDING-AS-RULED` are not synthetic look-alikes: they are the two compounds the
#: mentor and the architect actually wrote on 2026-08-09, when the right verb existed and
#: was not in force. They stand in `BOARD-EVENTS.log` today as removal-marker comments.
#: THE DEFECT THIS PASS EXISTS TO END IS THE CONTROL THAT GUARDS ITS ENDING — a seat that
#: knows the correct word and cannot write it invents something adjacent, where a seat
#: with no word stops and asks, so arming `NOTED` must not arm anything that merely looks
#: like it.
CONTROL_NEAR_MISSES = (
    ('EVT | 2026-03-01 | CTRL-A | NOTED-AS-RULED | ctl |',
     "the mentor's REAL mint of 2026-08-09"),
    ('EVT | 2026-03-01 | CTRL-A | NOTED-PENDING-AS-RULED | ctl |',
     "the architect's REAL mint of 2026-08-09"),
    ('EVT | 2026-03-01 | CTRL-A | noted | ctl |', 'lower-case noted'),
    ('EVT | 2026-03-01 | CTRL-A | NOTED. | ctl |', 'NOTED with a trailing full stop'),
    ('EVT | 2026-03-01 | CTRL-A | SEATED | ctl |', 'SEATED naming no kind'),
    ('EVT | 2026-03-01 | CTRL-A | SEATED(kind: replacement) | ctl |',
     'SEATED with a kind outside the closed set'),
    ('EVT | 2026-03-01 | CTRL-A | SEATED(kind: Continuation) | ctl |',
     'SEATED with a capitalised kind'),
    ('EVT | 2026-03-01 | CTRL-A | SEATED(kind: ) | ctl |', 'SEATED with an empty kind'),
    ('EVT | 2026-03-01 | CTRL-A | DISAMBIGUATED | ctl |',
     'DISAMBIGUATED naming neither ending nor state'),
    ('EVT | 2026-03-01 | CTRL-A | DISAMBIGUATED(ending: 2026-03-01 ACCEPTED) | ctl |',
     'DISAMBIGUATED naming no ended state'),
    ('EVT | 2026-03-01 | CTRL-A | DISAMBIGUATED(ended: HELD) | ctl |',
     'DISAMBIGUATED naming no ending'),
    ('EVT | 2026-03-01 | CTRL-A | '
     'DISAMBIGUATED(ending: 2026-03-01 ACCEPTED, ended: held) | ctl |',
     'DISAMBIGUATED with a lower-case state'),
    # THE DISCRIMINATOR'S NEAR MISSES (EP-28Y). A field spelled nearly right must REFUSE
    # rather than go unrecognised, because unrecognised means IGNORED — the reference then
    # looks like it carries an identity and does not.
    ('EVT | 2026-03-01 | CTRL-A | DISAMBIGUATED(ending: 2026-03-01 ACCEPTED digest:, '
     'ended: HELD) | ctl |', 'a discriminator with an EMPTY value'),
    ('EVT | 2026-03-01 | CTRL-A | DISAMBIGUATED(ending: 2026-03-01 ACCEPTED digest:zzzz, '
     'ended: HELD) | ctl |', 'a discriminator that is not hex'),
    ('EVT | 2026-03-01 | CTRL-A | DISAMBIGUATED(ending: 2026-03-01 ACCEPTED digest:ABC123, '
     'ended: HELD) | ctl |', 'an UPPER-CASE discriminator value'),
    ('EVT | 2026-03-01 | CTRL-A | DISAMBIGUATED(ending: 2026-03-01 ACCEPTED Digest:abc123, '
     'ended: HELD) | ctl |', 'the discriminator token CAPITALISED'),
    ('EVT | 2026-03-01 | CTRL-A | DISAMBIGUATED(ending: 2026-03-01 ACCEPTED digest: abc123, '
     'ended: HELD) | ctl |', 'a SPACE between the discriminator token and its value'),
    ('EVT | 2026-03-01 | CTRL-A | DISAMBIGUATED(ending: 2026-03-01 ACCEPTED digest:abc '
     'digest:def, ended: HELD) | ctl |', 'TWO discriminators on one reference'),
    ('EVT | 2026-03-01 | CTRL-A | DISAMBIGUATED(ending: digest:abc123, ended: HELD) '
     '| ctl |', 'a discriminator with NO alias beside it — it never binds alone'),
    # `COUNTERSIGNED`'s near misses (:969). THE RECORD'S OWN MINT IS THE FIRST OF THEM:
    # `COUNTERSIGN` is the bare stem a seat reaches for, and the compound `COUNTER-SIGNED`
    # is the hyphenated form `PRE-FLIGHTED` makes look lawful. The set is matched literally
    # and case-sensitively, so all four refuse HERE rather than folding as the real verb.
    ('EVT | 2026-03-01 | CTRL-A | COUNTERSIGN | ctl |', 'COUNTERSIGN for COUNTERSIGNED'),
    ('EVT | 2026-03-01 | CTRL-A | countersigned | ctl |', 'lower-case countersigned'),
    ('EVT | 2026-03-01 | CTRL-A | COUNTER-SIGNED | ctl |',
     'COUNTER-SIGNED, the hyphenated form PRE-FLIGHTED makes look lawful'),
    ('EVT | 2026-03-01 | CTRL-A | COUNTERSIGNED. | ctl |',
     'COUNTERSIGNED with a trailing full stop'),
    ('EVT | 2026-03-01 | CTRL-A | CLOSE | ctl |', 'CLOSE for CLOSED'),
    ('EVT | 2026-03-01 | CTRL-A | closed | ctl |', 'lower-case closed'),
    ('EVT | 2026-03-01 | CTRL-A | PREFLIGHTED | ctl |', 'PREFLIGHTED for PRE-FLIGHTED'),
    ('EVT | 2026-03-01 | CTRL-A | HOLD(on: x) | ctl |', 'HOLD for HELD'),
    ('EVT | 2026-03-01 | CTRL-A | HELD (on: x) | ctl |', 'HELD with a space'),
    ('EVT | 2026-03-01 | CTRL-A | HELD(on:x) | ctl |', 'HELD with no space after colon'),
    ('EVT | 2026-03-01 | CTRL-A | OWED(by: ctl) | ctl |', 'OWED naming no act'),
    ('EVT | 2026-03-01 | CTRL-A | ACCEPTED. | ctl |', 'a trailing full stop'),
    ('EVT | CTRL-A | 2026-03-01 | CLOSED | ctl |', 'the date column shifted right'),
    ('EVT | 2026-03-01 | 2026-03-02 | CLOSED | ctl |', 'the item column holding a date'),
    ('EVT | 2026-03-01 | CTRL-A | CLOSED', 'too few fields'),
    # THE PAIRING TOKEN'S SHAPE (EP-30-R4). A clause that OPENS with the token literal and
    # cannot then be read exactly REFUSES — a near-miss SPELLING is not the token and mints
    # nothing, but a malformed instance of the REAL token is a line the fold cannot read,
    # and a writer who believed the pairing landed would otherwise never learn it did not.
    ('EVT | 2026-03-01 | CTRL-A | AUTHORED | ctl | PAIRS(item: CTRL-A)',
     'a pairing naming no event'),
    ('EVT | 2026-03-01 | CTRL-A | AUTHORED | ctl | PAIRS(event: 2026-03-01 RULED)',
     'a pairing naming no item — a pair is ACROSS items'),
    ('EVT | 2026-03-01 | CTRL-A | AUTHORED | ctl | '
     'PAIRS(item:CTRL-A, event: 2026-03-01 RULED)', 'no space after the item field'),
    ('EVT | 2026-03-01 | CTRL-A | AUTHORED | ctl | '
     'PAIRS(item: CTRL-A, event: 2026-03-01 RULED', 'an unclosed pairing'),
    ('EVT | 2026-03-01 | CTRL-A | AUTHORED | ctl | '
     'PAIRS(item: CTRL-A, event: 2026-03-01 RULED Digest:abc123)',
     'the discriminator token CAPITALISED inside a pairing'),
    ('EVT | 2026-03-01 | CTRL-A | AUTHORED | ctl | '
     'PAIRS(item: CTRL-A, event: 2026-03-01 RULED digest: abc123)',
     'a SPACE between the discriminator token and its value inside a pairing'),
    ('EVT | 2026-03-01 | CTRL-A | AUTHORED | ctl | '
     'PAIRS(item: CTRL-A, event: digest:abc123)',
     'a pairing discriminator with NO alias beside it — it never binds alone'),
)

#: A7 AND R4's SUBJECT, BUILT ONCE SO THE POSITION CASES DIFFER BY POSITION ALONE. The
#: token text below is the ONLY source for every row in the battery, so a near-miss cannot
#: quietly drift into naming a different item or a different event than the real token does.
CONTROL_PAIR_TOKEN = 'PAIRS(item: CTRL-PAIR-POS-A, event: 2026-03-01 RULED)'
CONTROL_PAIR_TAIL = ('a clause DISCUSSING the pairing convention — which is the shape of '
                     'every board event this pass itself filed')

#: §A64 ON THE TOKEN ITSELF. Each of these MINTS NOTHING and none of them refuses: they are
#: not the token, and nothing in this grammar is case-folded, prefix-matched or
#: whitespace-tolerant. Their non-vacuity is the position-0 world driven beside them, where
#: the SAME row with the REAL token does mint.
#: The token's body, taken as a SLICE of the real token so a near-miss cannot drift into
#: naming a different item or event. NOT `str.replace` — the module's own no-writer AST
#: guard reads `.replace()` as a file-writing construct, correctly and by design (it is
#: `os.replace`), and the cure for a guard firing on this side is on THIS side. That guard
#: caught it at the first run and the tuple below is what it caught.
_PAIR_TOKEN_BODY = CONTROL_PAIR_TOKEN[len(PAIR_TOKEN):]
CONTROL_PAIR_NEAR_MISSES = (
    ('Pairs(' + _PAIR_TOKEN_BODY, 'Pairs( — the opening case-folded'),
    ('PAIRS (' + _PAIR_TOKEN_BODY, 'PAIRS ( — a space before the paren'),
    ('PAIR(' + _PAIR_TOKEN_BODY, 'PAIR( — the singular stem'),
    ('-' + CONTROL_PAIR_TOKEN, 'the REAL token at POSITION 1 rather than 0'),
)


#: THE DISCRIMINATOR'S CONTROL LINES (EP-28Y), appended to the control log by the control
#: itself because THE REFERENCE MUST CARRY A DIGEST THE TOOL COMPUTED. A hard-coded digest
#: would prove that a constant matches a constant; computing it here and pasting it into a
#: reference drives the round trip the ruling actually asks for — print and parse as ONE
#: contract. The SHAPE is the one the live record holds right now: two same-date same-verb
#: endings on one item, which is why `2026-08-08 PRE-FLIGHTED` refused on EP-28J.
CONTROL_COLLISION = (
    'EVT | 2026-03-01 | CTRL-DIG | HELD(on: a world) | ctl | the pair, half one',
    'EVT | 2026-03-01 | CTRL-DIG | OWED(by: ctl, act: a ruling) | ctl | the pair, half two',
    'EVT | 2026-03-02 | CTRL-DIG | ACCEPTED | ctl | the FIRST of two same-date same-verb',
    'EVT | 2026-03-02 | CTRL-DIG | ACCEPTED | ctl | the SECOND — the alias now names TWO',
    'EVT | 2026-03-01 | CTRL-DIG1 | HELD(on: a world) | ctl | the pair, half one',
    'EVT | 2026-03-01 | CTRL-DIG1 | OWED(by: ctl, act: a ruling) | ctl | the pair, half two',
    'EVT | 2026-03-02 | CTRL-DIG1 | ACCEPTED | ctl | the ONLY match for its alias',
)
#: A well-formed discriminator that matches NOTHING — the digest of a line that is not in
#: the control log. Asserted unmatched before it is used, so the row cannot go vacuous.
CONTROL_ABSENT_LINE = 'EVT | 2026-03-02 | CTRL-DIG1 | ACCEPTED | ctl | NOT IN ANY LOG'


def _control_disambiguation(item, reference):
    return ('EVT | 2026-03-04 | %s | DISAMBIGUATED(ending: %s, ended: HELD) | ctl | '
            'the collision, resolved by CONTENT' % (item, reference))


def _control_digest_world(*extra):
    """Fold the control log plus the collision lines plus whatever a row appends."""
    lines = CONTROL_LOG.splitlines() + list(CONTROL_COLLISION) + list(extra)
    events, _ = read_event_lines(lines, '<control>')
    return fold(events), events


def _control_pair_world(*extra):
    """Fold the control log plus whatever a pairing row appends. NO collision lines: the
    pairing battery's subject is POSITION, and a world carrying more than it needs makes a
    differential harder to read without making it stronger."""
    lines = CONTROL_LOG.splitlines() + list(extra)
    events, _ = read_event_lines(lines, '<control>')
    return fold(events), events


def _control_pair_row(clause):
    """ONE row, ONE item, ONE verb — so every case in the battery differs from every other
    ONLY in its clause. `CTRL-PAIR-POS-B` has no other event, so this filing STANDS, and
    `CTRL-PAIR-POS-A`'s `RULED` has ENDED: any pairing minted between them is half-ended by
    construction, which is what makes a silent row mean the token did not mint."""
    return 'EVT | 2026-03-01 | CTRL-PAIR-POS-B | STOPPED | ctl | %s' % clause


def _pair_row_names(rows):
    """A half-ended-pair report as (this item, the item it names) — never a count."""
    return sorted((row[0].name, row[4].item) for row in rows)


def _control_refuses(*extra):
    """True when this world REFUSES. Used only where a refusal IS the asserted property."""
    try:
        _control_digest_world(*extra)
    except BoardRefusal:
        return True
    return False


#: THE ECHO'S CLAUSE-BLINDNESS CONTROL (EP-30-R5). ONE EVENT BODY, TWO CLAUSES. The two
#: worlds folded below differ IN PROSE AND IN NOTHING ELSE — same date, same item, same
#: verb, same seat, same position — so an echo that read prose would answer differently
#: and an echo that reads the VERB answers identically. That differential is the whole
#: property, and it is driven rather than inspected.
#:
#: THE SHAPE IS THE LIVE RECORD'S OWN, not a synthetic look-alike: `:853`'s `RULED` ends
#: an `OWED` under a clause opening "BOTH MANAGER INSTRUMENTS STAY OPEN AS BOOKED DEBT",
#: and `:1182`'s `CORRECTED` ends the very `HELD` its clause says stands. Three careful
#: seats wrote clauses their verbs contradicted; a report that agreed with either clause
#: would reproduce the exact defect this report exists to catch.
CONTROL_ECHO_OPENER = ('EVT | 2026-03-01 | CTRL-ECHO | OWED(by: ctl, act: a booked debt) '
                       '| ctl | the state the NEXT line ends, whatever that line says')
CONTROL_ECHO_HEAD = 'EVT | 2026-03-02 | CTRL-ECHO | RULED | ctl | '
CONTROL_ECHO_DENYING = ('THE DEBT STAYS OPEN AND NOTHING HERE ENDS IT — a clause that '
                        'CONTRADICTS its own verb, which is :853 and :1182 in the record')
CONTROL_ECHO_AGREEING = 'the debt is discharged here — a clause that AGREES with its verb'


def _control_echo_world(*extra):
    """The digest world plus the echo's own opener. ONE DOOR, never a second reader — the
    collision lines ride along because the echo's REFERENCE battery needs exactly the
    same two same-date same-verb events the discriminator battery already plants."""
    return _control_digest_world(CONTROL_ECHO_OPENER, *extra)


def _echo_subject_refuses(events, reference):
    """True when this reference cannot name a subject. Used only where the REFUSAL is the
    asserted property. It catches `BadArgument` ALONE ON PURPOSE: no `BoardRefusal` may
    escape `resolve_echo_subject`, so a row that passed by catching one would be reporting
    a record finding as an argument finding."""
    try:
        resolve_echo_subject(events, reference)
    except BadArgument:
        return True
    return False


def _state_signature(item, attribution=None):
    """What a NOTED or a SEATED must not move: the item's STATE, its OPEN pendings, AND
    THE COORDINATE PRINTED BESIDE THE STATE (EP-28ZB C2).

    THE FOURTH FIELD IS THE REPAIR'S WHOLE POINT. The invariant named the state and the
    pendings and stopped there, so the printed attribution sat OUTSIDE it — which is
    precisely why this control watched a record-plane verb move the seat and line beside a
    state word and reported the board identical. A cell no invariant covers is a cell that
    can drift without anything going red.

    `attribution` is injectable so the guard can be driven against an attribution OTHER
    than the shipped one. That is not a test seam for its own sake: the behaviour this
    field exists to catch stops existing the moment it is repaired, so the only way to
    show the field CAN fail is to hand it a synthetic attribution that fails. The control
    does exactly that at every invocation.
    """
    if attribution is None:
        attribution = _printed_attribution
    at = attribution(item)
    return (item.state.verb if item.state is not None else None,
            sorted(p.verb for p in item.open_pendings()),
            len(item.ambiguous_endings),
            (at.date, at.seat, at.lineno) if at is not None else None)


def positive_control():
    """Return (ok, notes). Runs every invocation; a failure voids every count."""
    notes = []
    try:
        events, meta = read_event_lines(CONTROL_LOG.splitlines(), '<control>')
        board = fold(events)
    except BoardRefusal as exc:
        return False, ['the control log itself REFUSED: %s' % exc]

    kinds_seen = set(e.kind for e in events)
    missing = [k for k in _CONTROL_VERB_KINDS if k not in kinds_seen]
    if missing:
        return False, ['the control log plants no case of: %s' % ', '.join(missing)]
    notes.append('%d planted events, every one of the %d closed verbs exercised'
                 % (len(events), len(_CONTROL_VERB_KINDS)))

    if 'CTRL-EARLY' not in board:
        return False, ['the pre-seed early-adoption line was not folded']
    if board['CTRL-A'].state.kind != 'CLOSED':
        return False, ['latest-state-wins failed on CTRL-A: got %s'
                       % board['CTRL-A'].state.kind]

    pair = board['CTRL-PAIR'].open_pendings()
    if sorted(p.kind for p in pair) != ['HELD', 'OWED']:
        return False, ['the planted OWED+HELD pair was not SHOWN AS A PAIR: got %s'
                       % [p.kind for p in pair]]
    notes.append('planted OWED+HELD pair shown as a pair, never picked between')

    sup = board['CTRL-SUP']
    voided = [e for e in sup.history if e.voided_by is not None]
    if len(voided) != 1 or voided[0].kind != 'AUTHORED':
        return False, ['the planted CORRECTED did not void exactly its target']
    if len(sup.unresolved) != 1:
        return False, ['the planted free-text supersedes was not reported UNRESOLVED']
    notes.append('planted CORRECTED voided its target; planted free-text reference '
                 'reported UNRESOLVED rather than silently ignored')

    # THE AMBIGUITY DUTY, exercised at EVERY INVOCATION (EP-28W W4). All three cases are
    # planted, because the rule is a BOUNDARY and a control that plants only the new side
    # cannot show the boundary is in the right place. NON-VACUITY (item 21): each pair is
    # asserted OPEN before the ending is read — a comparison over an empty candidate set
    # proves nothing, and "both states closed" and "no states existed" look identical from
    # the other end.
    ambig = board['CTRL-AMBIG']
    if sorted(p.kind for p in ambig.open_pendings()) != ['HELD', 'OWED']:
        return False, ['the planted AMBIGUOUS ending CLOSED a state by pick: %s remain'
                       % [p.kind for p in ambig.open_pendings()]]
    if len(ambig.ambiguous_endings) != 1:
        return False, ['the planted unnamed ending over an open pair was not REPORTED '
                       'ambiguous: %d report(s)' % len(ambig.ambiguous_endings)]
    if sorted(ambig.ambiguous_endings[0][1]) != ['HELD', 'OWED']:
        return False, ['the reported candidate set is not the open pair: %s'
                       % (ambig.ambiguous_endings[0][1],)]
    named = board['CTRL-NAMED']
    still_open = [p.kind for p in named.open_pendings()]
    if still_open != ['OWED']:
        return False, ['the planted NAMED ending did not end exactly what it named: '
                       'open %s (expected only OWED)' % still_open]
    if named.ambiguous_endings:
        return False, ['a NAMED ending was reported ambiguous']
    single = board['CTRL-SINGLE']
    if single.open_pendings() or single.ambiguous_endings:
        return False, ['single-state inference MOVED: an unnamed ending over ONE open '
                       'state must close it exactly as it did before EP-28W']
    notes.append('planted ambiguous ending closed NOTHING and reported both candidates; '
                 'planted named ending closed only what it named; single-state '
                 'inference unchanged')

    # THE RECORD-PLANE VERBS, exercised at EVERY INVOCATION (EP-28X W2/W3). The claim is
    # BOARD IDENTITY, so it is proved by a DIFFERENTIAL rather than by inspection: fold
    # the same log with every `NOTED` and `SEATED` removed and require the two boards to
    # agree on every item the second one has. Reading the fold's branches would prove that
    # this fold does not change state; folding both worlds proves that THE BOARD does not.
    fresh, _ = read_event_lines(CONTROL_LOG.splitlines(), '<control>')
    without = fold([e for e in fresh
                    if e.kind not in ('NOTED', 'SEATED', 'COUNTERSIGNED')])
    for name, item in sorted(without.items()):
        if _state_signature(board[name]) != _state_signature(item):
            return False, ['a NOTED or SEATED CHANGED the board at %s: %r with them, %r '
                           'without' % (name, _state_signature(board[name]),
                                        _state_signature(item))]
    # THE ATTRIBUTION GUARD IS ITSELF EXERCISED (EP-28ZB C2), and it has to be, because
    # the differential above now carries the printed coordinate and therefore reports
    # SILENCE for a defect that no longer exists. Silence from a guard nobody has watched
    # fail is worth nothing. So the PRE-REPAIR attribution — the last event of ANY kind —
    # is driven here as a SYNTHETIC against the same two worlds, and it is REQUIRED to be
    # caught. The synthetic is passed in rather than restored in the code: the shipped
    # behaviour is gone and reviving it to test it would be the defect walking back in.
    #
    # THE EXPECTED CATCH IS NAMED rather than counted-as-nonzero. CTRL-NOTE carries a
    # HELD followed by a NOTED and two SEATED, so under the old attribution its bracket
    # moved from the HELD to the last SEATED while its state stayed HELD — this record's
    # planted instance of the live defect. An empty catch means the guard cannot fail; a
    # DIFFERENT catch means this control's own plant has moved and the row is no longer
    # about what it says it is.
    shipped = lambda it: it.last_event
    caught = sorted(name for name, item in without.items()
                    if _state_signature(board[name], shipped)
                    != _state_signature(item, shipped))
    if caught != ['CTRL-NOTE']:
        return False, ['THE ATTRIBUTION GUARD DOES NOT CATCH THE DEFECT IT EXISTS FOR: '
                       'driven against the pre-repair attribution the differential '
                       'flagged %r, expected exactly [\'CTRL-NOTE\'] — so its silence '
                       'under the shipped attribution proves nothing' % (caught,)]
    ctrl_note_at = _printed_attribution(board['CTRL-NOTE'])
    if ctrl_note_at is not board['CTRL-NOTE'].state:
        return False, ["the printed attribution is not the STATE'S OWN event on an item "
                       'whose last events are record-plane: printed :%d, state at :%d'
                       % (ctrl_note_at.lineno, board['CTRL-NOTE'].state.lineno)]
    if board['CTRL-NEWITEM'].state is not None:
        return False, ['CTRL-NEWITEM gained a state, so the fallback below is no longer '
                       'being exercised by a stateless item']
    if _printed_attribution(board['CTRL-NEWITEM']) \
            is not board['CTRL-NEWITEM'].last_event:
        return False, ['THE STATELESS FALLBACK DID NOT STAND: an item with record-plane '
                       'history and NO state must still attribute to its last event, '
                       'which is the fault-case the coordinate cell has always answered']
    notes.append('the printed coordinate ENTERED the record-plane invariant, and the '
                 'guard was driven against the PRE-REPAIR attribution and CAUGHT it at '
                 'CTRL-NOTE; the stateless fallback stood')

    extra = sorted(set(board) - set(without))
    if extra != ['CTRL-NEWITEM']:
        return False, ['the record-plane differential added items it should not: %s'
                       % extra]
    if board['CTRL-NEWITEM'].state is not None:
        return False, ['a record-plane FIRST event gave its item a STATE: %s'
                       % board['CTRL-NEWITEM'].state.verb]
    note = board['CTRL-NOTE']
    # The NOTED and both SEATED lines are the LAST events on this item, so if a
    # record-plane verb could become a state this is where it would show. The state must
    # still be the last LIFECYCLE event, which on this item is the HELD.
    if note.state.kind in HISTORY_ONLY_KINDS or note.state.kind != 'HELD':
        return False, ['a record-plane verb became the item STATE: %s' % note.state.kind]
    # NON-VACUITY (item 21): identity over an item with nothing open proves nothing.
    if [p.kind for p in note.open_pendings()] != ['HELD']:
        return False, ['NON-VACUITY: CTRL-NOTE held no open state across the NOTED, so '
                       'the identity above compares over nothing']
    if [e.kind for e in note.history].count('SEATED') != 2:
        return False, ['both SEATED kinds were not folded into history']
    # `COUNTERSIGNED` (:969) is NAMED here and not merely counted above, because the
    # differential's silence is only worth something if this item actually carries the
    # verb: a plant that drifted off CTRL-NOTE would leave the row comparing over an
    # item the new verb never touched.
    if [e.kind for e in note.history].count('COUNTERSIGNED') != 1:
        return False, ['the planted COUNTERSIGNED is not on CTRL-NOTE, so the '
                       'record-plane differential does not exercise it']
    notes.append('planted NOTED, both SEATED kinds and COUNTERSIGNED folded as HISTORY '
                 'ONLY — board identical with and without them, over an item holding OPEN '
                 'state; a record-plane FIRST event made an item with history and NO state')

    dis = board['CTRL-DIS']
    if [p.kind for p in dis.open_pendings()] != ['OWED']:
        return False, ['the planted DISAMBIGUATED did not end exactly the state it named: '
                       'open %s (expected only OWED)'
                       % [p.kind for p in dis.open_pendings()]]
    if dis.ambiguous_endings:
        return False, ["the resolved ending's AMBIGUOUS-ENDING report did not DROP"]
    resolved = [e for e in dis.history if e.kind == 'HELD'][0]
    ending_line = [e for e in dis.history if e.kind == 'ACCEPTED'][0].lineno
    if resolved.closed_by != ending_line:
        return False, ['the resolution was recorded at the DISAMBIGUATED line rather '
                       "than AS OF THE ENDING'S OWN POSITION: closed by %s, ending at %s"
                       % (resolved.closed_by, ending_line)]
    dis2 = board['CTRL-DIS2']
    if dis2.open_pendings() or dis2.ambiguous_endings:
        return False, ['THE DOWNSTREAM HALF FAILED: with the first ending resolved AS OF '
                       'ITS POSITION, the later ending saw ONE open state and closed it. '
                       'Open %s, %d ambiguity report(s)'
                       % ([p.kind for p in dis2.open_pendings()],
                          len(dis2.ambiguous_endings))]
    notes.append('planted DISAMBIGUATED ended exactly the state it named AS OF THE '
                 "ENDING'S OWN POSITION, the other pending STOOD, the ambiguity report "
                 'DROPPED, and a later ending on a second item then folded over ONE '
                 'candidate rather than two')

    # THE ANCHOR (EP-28X W4), controlled WITHOUT reading the record it anchors — a control
    # must not depend on the subject it is controlling for.
    probe = ['a', 'b', 'c', 'd']
    if content_digest(probe) == content_digest(probe[:3] + ['CHANGED']):
        return False, ['the content digest did not move when a line CHANGED']
    if content_digest(probe) == content_digest(['a', 'b', 'd']):
        return False, ['the content digest did not move when a line was REMOVED — which '
                       'is the exact surgery §1a exists to make loud']
    grown = probe + ['e', 'f']
    if content_digest(probe[:2]) != content_digest(grown[:2]):
        return False, ['an APPEND BEYOND THE PREFIX moved an anchored prefix digest, so '
                       'the property that retires the quiet-record window does not hold']
    notes.append('anchor digest (%s) moves on a changed line and on a REMOVED line, and '
                 'does NOT move when the record grows BEYOND the anchored prefix'
                 % ANCHOR_ALGO)

    # ORDERING, DELIBERATE AND STATED: the anchor block above runs FIRST because the
    # discriminator is built on `content_digest` and a neuter of that function must be
    # reported by the guard that names it. Run the other way round, EP-28X's digest-blind
    # red world is caught here instead and reads as a discriminator defect.
    #
    # THE DISCRIMINATOR (EP-28Y W2/W3), exercised at EVERY INVOCATION and proved by a
    # DIFFERENTIAL rather than by inspection: the SAME log folded twice, once with each
    # colliding ending's own digest, must resolve A DIFFERENT ENDING EACH TIME. A control
    # that planted one digest and checked it resolved could not tell content-matching from
    # first-match, and first-match is what the ruling refuses by name.
    bare_board, bare_events = _control_digest_world()
    collision = [e for e in bare_events if e.item == 'CTRL-DIG'
                 and e.date == '2026-03-02' and e.kind == 'ACCEPTED']
    # NON-VACUITY (item 21): the collision must BE a collision, and both states must stand
    # open, BEFORE anything resolves either. "Both resolved" and "nothing to resolve" look
    # identical from the far end.
    if len(collision) != 2:
        return False, ['NON-VACUITY: the planted alias names %d event(s), not the TWO the '
                       'discriminator exists for' % len(collision)]
    if len(bare_board['CTRL-DIG'].ambiguous_endings) != 2:
        return False, ['NON-VACUITY: the planted collision produced %d ambiguous ending(s), '
                       'not 2' % len(bare_board['CTRL-DIG'].ambiguous_endings)]
    first, second = collision[0], collision[1]
    if first.digest == second.digest:
        return False, ['two DIFFERENT event lines produced the SAME content digest, so the '
                       'discriminator does not discriminate']
    if not _control_refuses(_control_disambiguation('CTRL-DIG', '2026-03-02 ACCEPTED')):
        return False, ['REQUIRED-BUT-ABSENT: a bare alias over the planted collision did '
                       'not refuse the fold whole']
    resolved = {}
    for label, want in (('first', first), ('second', second)):
        ref = '2026-03-02 ACCEPTED %s%s' % (DIGEST_FIELD, digest_prefix(want.raw))
        world, evs = _control_digest_world(_control_disambiguation('CTRL-DIG', ref))
        pinned = [e for e in evs if e.item == 'CTRL-DIG'
                  and e.ending == 'NAMED' and e.disambiguated_by is not None]
        if [p.lineno for p in pinned] != [want.lineno]:
            return False, ['the discriminator did not pin BY CONTENT: the %s ending\'s own '
                           'digest resolved %s, not :%d — a first-match or a longest-match '
                           'would look exactly like this'
                           % (label, [p.lineno for p in pinned] or 'nothing', want.lineno)]
        resolved[label] = world
    if [p.kind for p in resolved['second']['CTRL-DIG'].open_pendings()] != ['OWED']:
        return False, ['pinning the SECOND ending left the wrong state open']
    if len(resolved['second']['CTRL-DIG'].ambiguous_endings) != 1:
        return False, ['pinning the SECOND ending did not leave the FIRST reported '
                       'ambiguous, so the two worlds are not distinguishable']
    if resolved['first']['CTRL-DIG'].ambiguous_endings:
        return False, ['pinning the FIRST ending left an ambiguity report standing']
    # TWICE-MATCHED. One hex character over %d planted events collides by PIGEONHOLE — 16
    # possible values, more events than that — so this world is never accidentally vacuous.
    short = digest_prefix(first.raw)[:1]
    shares = [e for e in bare_events if e.digest.startswith(short)]
    if len(shares) < 2:
        return False, ['NON-VACUITY: the one-character prefix %r matches %d event line(s), '
                       'so the twice-matched world below is not a collision' % (short,
                                                                                len(shares))]
    if not _control_refuses(_control_disambiguation(
            'CTRL-DIG', '2026-03-02 ACCEPTED %s%s' % (DIGEST_FIELD, short))):
        return False, ['TWICE-MATCHED: a prefix matching %d event lines did not refuse the '
                       'fold whole' % len(shares)]
    # VALIDATED ALWAYS. The alias below names EXACTLY ONE event, so the digest is not
    # required — and a wrong one still refuses. This is the half the plan narrowed at
    # authoring and repaired at pre-flight, and it is the COMMON path: `--ep` prints
    # digests so seats copy them, and a copied digest goes stale silently or not at all.
    single = [e for e in bare_events if e.item == 'CTRL-DIG1' and e.kind == 'ACCEPTED']
    if len(single) != 1:
        return False, ['NON-VACUITY: the single-candidate control is not single: %d'
                       % len(single)]
    absent = digest_prefix(CONTROL_ABSENT_LINE)
    if any(e.digest.startswith(absent) for e in bare_events):
        return False, ['NON-VACUITY: the "matches nothing" discriminator matches something']
    good = _control_digest_world(_control_disambiguation(
        'CTRL-DIG1', '2026-03-02 ACCEPTED %s%s' % (DIGEST_FIELD,
                                                   digest_prefix(single[0].raw))))[0]
    if [p.kind for p in good['CTRL-DIG1'].open_pendings()] != ['OWED']:
        return False, ['a MATCHING digest on an unambiguous reference did not resolve it']
    if not _control_refuses(_control_disambiguation(
            'CTRL-DIG1', '2026-03-02 ACCEPTED %s%s' % (DIGEST_FIELD, absent))):
        return False, ['VALIDATED ALWAYS FAILED: a WRONG digest on an UNAMBIGUOUS '
                       'reference folded silently. Required when ambiguous, validated '
                       'always — BOARD-GRAMMAR §1 says "unmatched", unqualified.']
    # ALIAS AND DIGEST MUST AGREE. A digest that pins a real event the alias does not name
    # is a reference whose two halves say different things.
    if not _control_refuses(_control_disambiguation(
            'CTRL-DIG1', '2026-03-02 ACCEPTED %s%s' % (DIGEST_FIELD,
                                                       digest_prefix(first.raw)))):
        return False, ['a digest pinning an event the ALIAS does not name folded anyway']
    # THE LINE-NUMBER ALIAS RIDES (BOARD-GRAMMAR §1: "a line number MAY ride beside it").
    # It rode before this pass through the tolerant reference match; the control pins it so
    # this pass cannot have quietly taken away a form the grammar permits.
    rode = _control_digest_world(_control_disambiguation(
        'CTRL-DIG1', '2026-03-02 ACCEPTED at line %d %s%s'
        % (single[0].lineno, DIGEST_FIELD, digest_prefix(single[0].raw))))[0]
    if [p.kind for p in rode['CTRL-DIG1'].open_pendings()] != ['OWED']:
        return False, ['a line number riding beside the digest broke the reference']
    notes.append('discriminator pinned BY CONTENT — each of two same-date same-verb '
                 'endings resolved by ITS OWN digest and never the other; the bare alias '
                 'over that collision REFUSED; a %d-char prefix matching %d lines REFUSED; '
                 'a WRONG digest on an UNAMBIGUOUS reference REFUSED (validated always, '
                 'not only when required); an alias/digest disagreement REFUSED; a line '
                 'number rode beside the digest without binding alone'
                 % (len(short), len(shares)))

    # THE PAIRED FILING (EP-30-R4), exercised at EVERY INVOCATION AND IN BOTH DIRECTIONS.
    # A report class that CANNOT FIRE and a report class that fires on PROSE are both silent
    # failures, and this is the only place either would show. SILENCE IS EARNED HERE: a row
    # that drove only the speaking direction would have proved the check can fire and
    # proved NOTHING about the silence it produces every other day of its life.
    #
    # NON-VACUITY FIRST, per item 21 and for a reason specific to this class: the live
    # record is append-only, so the pair that CAUSED this pass predates its own token and
    # can never carry it. This check therefore lands with a live population of ZERO — and a
    # check whose only exercise is its own plant is exactly the disguise this estate has
    # spent a fortnight hunting. So each planted pair is asserted to BE the shape it is
    # named for BEFORE anything is read off the report.
    for label, carrier, want_here, want_there in (
            ('CLEAN (both sides ended)', 'CTRL-PAIR-CLEAN-B', False, False),
            ('HALF-ENDED (one ended, one standing)', 'CTRL-PAIR-HALF-B', True, False),
            ('BOTH-OPEN (neither ended)', 'CTRL-PAIR-OPEN-B', True, True)):
        # `.get`, NOT `[...]`, AND THE REASON IS R1's FINDING RATHER THAN CAUTION: driven
        # with the plants removed, an indexed lookup raised a KeyError THROUGH `main`, which
        # leaves with the interpreter's 1 — the one code this module's exit contract says it
        # never chooses, and the code that means "this tool crashed". A control whose
        # failure mode collides with a crash cannot report a missing plant AS a missing
        # plant. It is named here instead.
        if carrier not in board:
            return False, ['the control log plants no %s pair: %s is absent, so the '
                           'half-ended-pair check ships UNEXERCISED' % (label, carrier)]
        planted = board[carrier].pairs
        if len(planted) != 1 or planted[0].pair_target is None:
            return False, ['NON-VACUITY: the planted %s pairing on %s did not RESOLVE, so '
                           'the report below is about nothing' % (label, carrier)]
        ref = planted[0]
        here = _pair_side_stands(board[carrier], ref)
        there = _pair_side_stands(board[ref.pair_target.item], ref.pair_target)
        if (here, there) != (want_here, want_there):
            return False, ['NON-VACUITY: the planted %s pair is not that shape — this side '
                           'stands=%s, the other stands=%s' % (label, here, there)]
    base_rows = half_ended_pairs(board)
    base_names = _pair_row_names(base_rows)
    if base_names != [('CTRL-PAIR-HALF-B', 'CTRL-PAIR-HALF-A')]:
        return False, ['THE HALF-ENDED-PAIR CHECK REPORTED %r. It must report EXACTLY the '
                       'half-ended pair and must be SILENT on the clean pair and on the '
                       'both-open pair, which are planted beside it for that reason'
                       % (base_names,)]
    row = base_rows[0]
    # The reported OTHER side must be the RULED itself — the filing the pairing named — and
    # not merely some event on that item. A row that named the item and not the event would
    # send a writer back to the fold it is already holding.
    named = board['CTRL-PAIR-HALF-A'].history[0]
    if (row[2], row[5]) != (True, False) or row[4] is not named:
        return False, ['the half-ended report named the wrong side or the wrong event: '
                       'this side stands=%s, other stands=%s, other event :%d (the pairing '
                       'names :%d)' % (row[2], row[5], row[4].lineno, named.lineno)]

    # POSITION IS THE WHOLE CLAIM, so it is driven BY POSITION ALONE: one token, one row,
    # one item, one verb — the token at the START of the clause and the SAME token later in
    # the SAME clause, with the same bytes in a different order.
    at_zero = _control_pair_world(_control_pair_row(
        CONTROL_PAIR_TOKEN + ' ' + CONTROL_PAIR_TAIL))[0]
    as_prose = _control_pair_world(_control_pair_row(
        CONTROL_PAIR_TAIL + ' ' + CONTROL_PAIR_TOKEN))[0]
    minted = base_names + [('CTRL-PAIR-POS-B', 'CTRL-PAIR-POS-A')]
    if _pair_row_names(half_ended_pairs(at_zero)) != sorted(minted):
        return False, ['A CLAUSE-INITIAL TOKEN DID NOT MINT A PAIR, so every silence below '
                       'is the silence of a check that cannot fire: got %r'
                       % (_pair_row_names(half_ended_pairs(at_zero)),)]
    if _pair_row_names(half_ended_pairs(as_prose)) != base_names:
        return False, ['PROSE MINTED A PAIR: the same token later in the same clause '
                       'reported %r. Every board event discussing this convention — this '
                       'pass\'s own filings included — would mint phantom pairs'
                       % (_pair_row_names(half_ended_pairs(as_prose)),)]
    for clause, why in CONTROL_PAIR_NEAR_MISSES:
        world = _control_pair_world(_control_pair_row(clause + ' ' + CONTROL_PAIR_TAIL))[0]
        if _pair_row_names(half_ended_pairs(world)) != base_names:
            return False, ['NEAR-MISS MINTED A PAIR (§A64): %s' % why]

    # THE REFERENCE, EACH CASE NAMED INDIVIDUALLY. An unknown item is a REPORT — the
    # `supersedes:` treatment, because the filing still carries its own state on its own
    # line. An ambiguous alias REFUSES — a pairing that could mean either of two filings has
    # not named one — and the discriminator is the escape the identity law already provides.
    unknown = _control_pair_world(_control_pair_row(
        'PAIRS(item: CTRL-NOBODY-EVER, event: 2026-03-01 RULED) names an item this fold '
        'has never seen'))[0]
    if 'CTRL-NOBODY-EVER' in unknown:
        return False, ['a pairing to an unknown item CREATED that item']
    if len([e for n in unknown for e in unknown[n].unresolved_pairs]) != 1:
        return False, ['a pairing naming an unknown item was SILENTLY IGNORED rather than '
                       'reported UNRESOLVED']
    if _pair_row_names(half_ended_pairs(unknown)) != base_names:
        return False, ['an UNRESOLVED pairing folded a pair anyway']
    collide = [e for e in _control_digest_world()[1] if e.item == 'CTRL-DIG'
               and e.date == '2026-03-02' and e.kind == 'ACCEPTED']
    if len(collide) != 2:
        return False, ['NON-VACUITY: the alias the pairing battery collides on names %d '
                       'event(s), not two' % len(collide)]
    if not _control_refuses(_control_pair_row(
            'PAIRS(item: CTRL-DIG, event: 2026-03-02 ACCEPTED) the alias names TWO')):
        return False, ['AMBIGUOUS PAIRING: an alias naming two events on the named item did '
                       'not refuse the fold whole']
    pinned = _control_digest_world(_control_pair_row(
        'PAIRS(item: CTRL-DIG, event: 2026-03-02 ACCEPTED %s%s) pinned by CONTENT'
        % (DIGEST_FIELD, digest_prefix(collide[1].raw))))[0]
    got = [e.pair_target.lineno for e in pinned['CTRL-PAIR-POS-B'].pairs]
    if got != [collide[1].lineno]:
        return False, ['the pairing discriminator did not pin BY CONTENT: the SECOND '
                       'ending\'s own digest resolved %s, not :%d — a first-match would '
                       'look exactly like this' % (got or 'nothing', collide[1].lineno)]
    single = [e for e in _control_digest_world()[1] if e.item == 'CTRL-DIG1'
              and e.kind == 'ACCEPTED']
    if len(single) != 1:
        return False, ['NON-VACUITY: the single-candidate pairing control is not single']
    if _control_refuses(_control_pair_row(
            'PAIRS(item: CTRL-DIG1, event: 2026-03-02 ACCEPTED %s%s) a MATCHING digest'
            % (DIGEST_FIELD, digest_prefix(single[0].raw)))):
        return False, ['a MATCHING discriminator on an unambiguous pairing refused']
    if not _control_refuses(_control_pair_row(
            'PAIRS(item: CTRL-DIG1, event: 2026-03-02 ACCEPTED %s%s) a WRONG digest'
            % (DIGEST_FIELD, digest_prefix(CONTROL_ABSENT_LINE)))):
        return False, ['VALIDATED ALWAYS FAILED for the pairing: a WRONG discriminator on '
                       'an UNAMBIGUOUS reference folded silently']
    notes.append('THE HALF-ENDED-PAIR CHECK drove BOTH DIRECTIONS: a planted CLEAN pair '
                 '(both sides ended) and a planted BOTH-OPEN pair reported NOTHING, and the '
                 'planted HALF-ENDED pair reported EXACTLY ONE line naming both items and '
                 'both coordinates; one token minted a pair at POSITION 0 of a clause and '
                 'minted NOTHING later in the SAME clause; %d near-miss spellings minted '
                 'nothing; an unknown-item pairing REPORTED unresolved and folded no pair; '
                 'an ambiguous alias REFUSED and its discriminator then pinned the SECOND '
                 'of two BY CONTENT; a wrong discriminator on an unambiguous pairing '
                 'REFUSED' % len(CONTROL_PAIR_NEAR_MISSES))

    # THE ECHO — THE STATE-DELTA REPORT (EP-30-R5), exercised at EVERY INVOCATION.
    #
    # THE COVERAGE CLAUSE ABOVE CANNOT REACH THIS, AND THAT IS REPORTED RATHER THAN
    # REPAIRED HERE. `_CONTROL_VERB_KINDS` requires a planted case of every VERB, and the
    # echo adds NO VERB — the ruling put the cure at the effect layer and not the
    # vocabulary layer on purpose. So a feature that is not a verb ships unexercised as
    # far as that clause is concerned, and only a hand-written battery like this one
    # catches it. Named here so the gap is a finding in the record and not a silence.
    #
    # THE FIRST ROW IS THE PASS: TWO WORLDS THAT DIFFER ONLY IN PROSE MUST ECHO THE SAME.
    # A report that agreed with a clause would look correct on every event whose author
    # got the verb right, which is most of them, and would be wrong on exactly the three
    # the ruling rests on.
    denying, denying_events = _control_echo_world(CONTROL_ECHO_HEAD + CONTROL_ECHO_DENYING)
    agreeing, agreeing_events = _control_echo_world(CONTROL_ECHO_HEAD
                                                    + CONTROL_ECHO_AGREEING)
    opener = [e for e in denying_events if e.item == 'CTRL-ECHO' and e.kind == 'OWED']
    ruling = [e for e in denying_events if e.item == 'CTRL-ECHO' and e.kind == 'RULED']
    agreed = [e for e in agreeing_events if e.item == 'CTRL-ECHO' and e.kind == 'RULED']
    if len(opener) != 1 or len(ruling) != 1 or len(agreed) != 1:
        return False, ['the echo control did not plant exactly one OWED and one RULED on '
                       'CTRL-ECHO: %d, %d (and %d in the agreeing world)'
                       % (len(opener), len(ruling), len(agreed))]
    # NON-VACUITY, THREE WAYS. A differential over a line compared with itself proves
    # nothing; an ENDED row over a pending that was never open is about nothing; and two
    # worlds at different coordinates are not a prose differential.
    if ruling[0].raw == agreed[0].raw:
        return False, ['NON-VACUITY: the two clause worlds planted the SAME line, so the '
                       'differential below compares a line with itself']
    if (ruling[0].lineno, ruling[0].date, ruling[0].item, ruling[0].kind,
            ruling[0].seat) != (agreed[0].lineno, agreed[0].date, agreed[0].item,
                                agreed[0].kind, agreed[0].seat):
        return False, ['NON-VACUITY: the two clause worlds differ in more than PROSE, so '
                       'an identical echo would not prove the clause went unread']
    if opener[0].closed_by != ruling[0].lineno:
        return False, ['NON-VACUITY: the planted RULED did not end the planted OWED, so '
                       'the ENDED row below is about nothing']
    ended_lines = echo_lines(denying, denying_events, ruling[0])
    agree_lines = echo_lines(agreeing, agreeing_events, agreed[0])
    # THE DIFFERENTIAL HAS EXACTLY ONE EXEMPT ROW AND THE EXEMPTION IS ITSELF A PROPERTY.
    # The SUBJECT row prints the event's DIGEST, which is the digest of the WHOLE LINE and
    # therefore MOVES WITH THE CLAUSE — correctly, because an event's identity is its
    # content (EP-28Y). So this row drives both halves at once: THE IDENTITY MUST MOVE
    # WITH THE PROSE and THE EFFECT MUST NOT. The first run of this control caught the
    # author conflating them, which is the only reason a reader should trust the second.
    subj_here = [i for i, ln in enumerate(ended_lines) if '  SUBJECT :' in ln]
    subj_there = [i for i, ln in enumerate(agree_lines) if '  SUBJECT :' in ln]
    if subj_here != subj_there or len(subj_here) != 1:
        return False, ['the echo printed %r SUBJECT row(s) against %r, so the differential '
                       'below has no stable exemption' % (subj_here, subj_there)]
    cut = subj_here[0]
    if ended_lines[:cut] + ended_lines[cut + 1:] != agree_lines[:cut] + agree_lines[cut + 1:]:
        return False, ['THE ECHO READ THE CLAUSE. Two events identical in date, item, '
                       'verb, seat and position and differing ONLY IN PROSE echoed '
                       'different EFFECTS — which is the exact defect this report exists '
                       'to catch, shipped inside the cure']
    if ended_lines[cut] == agree_lines[cut]:
        return False, ['NON-VACUITY: the SUBJECT row did not move between two DIFFERENT '
                       'lines, so the identity printed beside the effect is not the '
                       'event\'s content and the exemption above is hiding nothing']
    for token in (':%d' % ruling[0].lineno, ruling[0].date, ruling[0].item,
                  ruling[0].verb, ruling[0].seat):
        if token not in ended_lines[cut] or token not in agree_lines[cut]:
            return False, ['the SUBJECT row differs in more than the DIGEST — %r is not '
                           'in both' % token]
    hit = [ln for ln in ended_lines if ln.strip().startswith('ENDED ')]
    if len(hit) != 1:
        return False, ['the echo of an ending reported %d ENDED row(s), not 1' % len(hit)]
    named_rows = ' '.join(ended_lines)
    if (opener[0].verb not in named_rows or 'CTRL-ECHO' not in named_rows
            or ':%d' % opener[0].lineno not in named_rows):
        return False, ['the ENDED row did not name WHICH state, ON WHICH item, and WHERE '
                       'it was opened: %r' % (ended_lines,)]
    if [ln for ln in ended_lines if 'MOVED NOTHING' in ln]:
        return False, ['an ENDING echoed MOVED NOTHING — the three shapes are not '
                       'distinguishable, so no row below can tell them apart']

    # OPENED. The same planted OWED, read from the other end.
    opened_lines = echo_lines(denying, denying_events, opener[0])
    if not [ln for ln in opened_lines if ln.strip().startswith('OPENED ')]:
        return False, ['a PENDING echoed no OPENED row: %r' % (opened_lines,)]
    if 'CTRL-ECHO' not in ' '.join(opened_lines):
        return False, ['the OPENED row did not name the item']

    # MOVED NOTHING, and the item that held NO STATE AT ALL — R5's own shape, which is
    # the live `:1174` instance: a record-plane FIRST event on an item the fold had never
    # seen. A silent answer here is indistinguishable from a broken echo.
    newitem = [e for e in denying_events if e.item == 'CTRL-NEWITEM']
    if len(newitem) != 1 or not newitem[0].is_history_only:
        return False, ['NON-VACUITY: CTRL-NEWITEM is not one record-plane event, so the '
                       'MOVED NOTHING row below is not about a history-only verb']
    if denying['CTRL-NEWITEM'].state is not None:
        return False, ['NON-VACUITY: CTRL-NEWITEM gained a STATE, so the "held no state" '
                       'row below is not about a stateless item']
    moved_lines = echo_lines(denying, denying_events, newitem[0])
    if not [ln for ln in moved_lines if 'MOVED NOTHING' in ln]:
        return False, ['A HISTORY-ONLY VERB ECHOED SILENCE. A silent answer for a verb '
                       'that opened and ended nothing is indistinguishable from a broken '
                       'echo, and it would have said nothing at all about :1174']
    if 'NO STATE EVENT' not in ' '.join(moved_lines):
        return False, ['the echo of an event on an item that HELD NO STATE did not say '
                       'so: %r' % (moved_lines,)]
    if [ln for ln in moved_lines if ln.strip().startswith('ENDED')]:
        return False, ['a RECORD-PLANE verb echoed an ENDING']

    # THE REMAINING BRANCHES, EACH DRIVEN SO NONE SHIPS UNEXERCISED. A branch nobody has
    # watched produce output is a branch whose first reader is a seat mid-filing.
    #   STANDS OPEN   the other half of OPENED — CTRL-PAIR's HELD is never closed, where
    #                 CTRL-ECHO's OWED is, so the two arms are driven from two plants.
    #   VOIDED        a CORRECTED whose target was NOT a pending: it ends no state and it
    #                 is not history-only, so without this row it would echo an effect
    #                 list of nothing, which is A4's third-arm argument one category over.
    #   CLOSED NOTHING an AMBIGUOUS ending. The fold reports and never picks, and an echo
    #                 that stayed silent would read as "this ending ended nothing" when
    #                 the truth is "this ending could not say which".
    standing = [e for e in denying_events if e.item == 'CTRL-PAIR' and e.kind == 'HELD']
    if len(standing) != 1 or standing[0].closed_by is not None:
        return False, ['NON-VACUITY: CTRL-PAIR\'s HELD is not a single STILL-OPEN pending, '
                       'so the STANDS OPEN arm below is not about a standing state']
    if 'STANDS OPEN' not in ' '.join(echo_lines(denying, denying_events, standing[0])):
        return False, ['a pending that is STILL OPEN did not echo as standing']
    if 'closed it at :%d' % ruling[0].lineno not in ' '.join(opened_lines):
        return False, ['a pending a LATER event closed did not name that later event, so '
                       'the two OPENED arms are not distinguishable']
    sup = [e for e in denying_events if e.item == 'CTRL-SUP' and e.kind == 'CORRECTED'
           and e.resolution == 'RESOLVED']
    if len(sup) != 1:
        return False, ['NON-VACUITY: the VOIDED row needs exactly one RESOLVED CORRECTED '
                       'on CTRL-SUP and found %d' % len(sup)]
    voided_lines = echo_lines(denying, denying_events, sup[0])
    if not [ln for ln in voided_lines if ln.strip().startswith('VOIDED')]:
        return False, ['a CORRECTED that superseded a NON-PENDING echoed no VOIDED row, '
                       'so a lifecycle verb that ended no state echoed an EMPTY effect '
                       'list — indistinguishable from a broken echo']
    if [ln for ln in voided_lines if ln.strip().startswith('ENDED')]:
        return False, ['voiding a NON-PENDING was echoed as ENDING A STATE']
    ambig = [e for e in denying_events if e.item == 'CTRL-AMBIG'
             and e.ending == 'AMBIGUOUS']
    if len(ambig) != 1:
        return False, ['NON-VACUITY: the CLOSED NOTHING row needs exactly one AMBIGUOUS '
                       'ending on CTRL-AMBIG and found %d' % len(ambig)]
    ambig_lines = echo_lines(denying, denying_events, ambig[0])
    if 'CLOSED NOTHING' not in ' '.join(ambig_lines):
        return False, ['an AMBIGUOUS ending did not echo that it closed nothing']
    if [ln for ln in ambig_lines if ln.strip().startswith('ENDED')]:
        return False, ['an AMBIGUOUS ending echoed an ENDING — the fold closed nothing '
                       'and the echo must not claim otherwise']

    # THE SUBJECT REFERENCE. The record's own grammar, driven over the WIDER population an
    # echo resolves against — and each near-miss named individually rather than counted.
    if resolve_echo_subject(denying_events, '') is not ruling[0]:
        return False, ['THE DEFAULT SUBJECT IS NOT THE LAST EVT LINE of the folded '
                       'prefix, which is the line a filing hand has just written']
    collide = [e for e in denying_events if e.item == 'CTRL-DIG'
               and e.date == '2026-03-02' and e.kind == 'ACCEPTED']
    if len(collide) != 2:
        return False, ['NON-VACUITY: the alias the echo battery collides on names %d '
                       'event(s), not two' % len(collide)]
    if len([e for e in denying_events
            if e.date == '2026-03-02' and e.kind == 'ACCEPTED']) < 2:
        return False, ['NON-VACUITY: the ambiguous-alias world is not ambiguous']
    if not _echo_subject_refuses(denying_events, '2026-03-02 ACCEPTED'):
        return False, ['AN AMBIGUOUS ALIAS WITH NO DISCRIMINATOR DID NOT REFUSE — an echo '
                       'that could be about either of two events is about neither']
    for label, want in (('first', collide[0]), ('second', collide[1])):
        got = resolve_echo_subject(denying_events, '2026-03-02 ACCEPTED %s%s'
                                   % (DIGEST_FIELD, digest_prefix(want.raw)))
        if got is not want:
            return False, ['the echo\'s discriminator did not pin BY CONTENT: the %s '
                           'event\'s own digest resolved :%d, not :%d — a first-match '
                           'would look exactly like this'
                           % (label, got.lineno, want.lineno)]
    short = digest_prefix(collide[0].raw)[:1]
    if len([e for e in denying_events if e.digest.startswith(short)]) < 2:
        return False, ['NON-VACUITY: the one-character prefix %r is not a collision in '
                       'this world' % short]
    if not _echo_subject_refuses(denying_events, '2026-03-02 ACCEPTED %s%s'
                                 % (DIGEST_FIELD, short)):
        return False, ['TWICE-MATCHED: a one-character prefix matching several event '
                       'lines did not refuse']
    solo = [e for e in denying_events if e.date == '2026-03-02' and e.kind == 'RULED']
    if len(solo) != 1:
        return False, ['NON-VACUITY: the unambiguous-reference control is not '
                       'unambiguous: %d candidate(s)' % len(solo)]
    if resolve_echo_subject(denying_events, '2026-03-02 RULED %s%s'
                            % (DIGEST_FIELD, digest_prefix(solo[0].raw))) is not solo[0]:
        return False, ['a MATCHING discriminator on an UNAMBIGUOUS echo reference did not '
                       'resolve it']
    if not _echo_subject_refuses(denying_events, '2026-03-02 RULED %s%s'
                                 % (DIGEST_FIELD, digest_prefix(CONTROL_ABSENT_LINE))):
        return False, ['VALIDATED ALWAYS FAILED for the echo: a WRONG discriminator on an '
                       'UNAMBIGUOUS reference resolved silently']
    if not _echo_subject_refuses(denying_events, '2026-03-02 ACCEPTED %s%s'
                                 % (DIGEST_FIELD, digest_prefix(solo[0].raw))):
        return False, ['an echo reference whose ALIAS and DISCRIMINATOR name DIFFERENT '
                       'events resolved anyway']
    if any(e.date == '2026-03-09' for e in denying_events):
        return False, ['NON-VACUITY: the "names nothing" alias below names something']
    if not _echo_subject_refuses(denying_events, '2026-03-09 CLOSED'):
        return False, ['an alias naming NO event in the folded prefix resolved anyway']
    if not _echo_subject_refuses(denying_events, 'the last one'):
        return False, ['a reference that is not a <date+verb> at all resolved anyway — a '
                       'SECOND reference form has entered this tool']
    notes.append('THE ECHO — the STATE-DELTA REPORT — drove all three effect shapes '
                 '(ENDED naming the state, the item and where it was opened; OPENED; and '
                 'MOVED NOTHING on a record-plane verb over an item holding NO STATE), '
                 'plus a pending STILL STANDING against one a later event closed, a '
                 'CORRECTED that VOIDED a non-pending, and an AMBIGUOUS ending echoing '
                 'CLOSED NOTHING; and it '
                 'proved CLAUSE-BLINDNESS by DIFFERENTIAL: two events identical in date, '
                 'item, verb, seat and position and differing ONLY IN PROSE echoed '
                 'byte-identically, one clause DENYING what its verb did and one AGREEING '
                 '— which is :853 and :1182 in the live record; the subject resolved by '
                 'the RECORD\'S OWN reference grammar over the WHOLE record, defaulting '
                 'to the LAST EVT LINE, with an ambiguous alias REFUSING, each of two '
                 'colliding events pinned BY ITS OWN CONTENT, a %d-char prefix REFUSING, '
                 'a WRONG digest on an UNAMBIGUOUS reference REFUSING, an alias/digest '
                 'disagreement REFUSING, an alias naming nothing REFUSING, and a non-'
                 '<date+verb> form REFUSING' % len(short))

    stale = stale_items(board, '2026-03-01')
    if [s[0] for s in stale] != ['CTRL-STALE']:
        return False, ['the planted stale item was not found: got %s'
                       % [s[0] for s in stale]]
    notes.append('planted stale item found at a known age')

    if 'CTRL-NOBODY-EVER' in board:
        return False, ['an item nobody planted appeared in the board']

    for text, why in CONTROL_NEAR_MISSES:
        try:
            parse_event_line(text, 1)
        except BoardRefusal:
            continue
        return False, ['NEAR-MISS ACCEPTED (§A64): %s' % why]
    notes.append('%d near-miss lines all REFUSED (nearly-right verbs, shifted columns)'
                 % len(CONTROL_NEAR_MISSES))
    return True, notes


# ---------------------------------------------------------------------------
# QUERIES
# ---------------------------------------------------------------------------

def stale_items(board, since):
    """Items whose LAST EVENT is strictly before `since`. Returns (name, age, who)."""
    ref = datetime.date(*[int(p) for p in since.split('-')])
    out = []
    for name in sorted(board):
        item = board[name]
        last = item.last_date
        if last is None:
            continue
        last_d = datetime.date(*[int(p) for p in last.split('-')])
        if last_d >= ref:
            continue
        who = []
        for pend in item.open_pendings():
            if pend.kind == 'OWED':
                who.append('OWED by %s — %s' % (pend.owed_by, pend.act))
            else:
                who.append('HELD on %s' % pend.trigger)
        out.append((name, (ref - last_d).days, ' + '.join(who) or '—'))
    return out


def resolve_echo_subject(events, reference):
    """THE ECHO'S SUBJECT (EP-30-R5 A3) — resolved by THE RECORD'S OWN REFERENCE GRAMMAR.

    THE THIRD CALLER OF ONE RULE, NEVER A SECOND SPELLING. `RE_SUPERSEDES_KEY` reads the
    `<date> <VERB>` alias, `split_digest_field` splits the discriminator, and
    `_pin_reference_by_digest` applies the identity law — the same three the
    `DISAMBIGUATED` and `PAIRS` references already use, called verbatim. A second
    reference form in this tool would be a second identity for one object.

    AN EMPTY REFERENCE MEANS THE LAST `EVT` LINE OF THE FOLDED PREFIX, which is the line a
    filing hand has just written and the case the `:1180` discipline exists for. `events`
    arrives from `read_event_lines` in FILE ORDER, so its last element is that line. THE
    FOLD'S ORDER IS SEED-FIRST AND IS A DIFFERENT SEQUENCE; it is deliberately not used
    here, because "the last line I appended" is a fact about the FILE.

    POPULATION, STATED RATHER THAN LEFT IN A COMPREHENSION (§A51): EVERY event the fold
    holds. The two existing callers narrow to one item and to strictly-earlier positions
    because a `supersedes:` and a `PAIRS(...)` are written FROM a position INSIDE the
    record; an echo is asked FROM OUTSIDE it and has neither an own item nor an own
    position. THE RULE IS THE SAME AND THE POPULATION IS WIDER.

    IT RAISES `BadArgument` AND NEVER `BoardRefusal`, AND THAT RE-CLASS IS DELIBERATE. The
    reference arrives on the COMMAND LINE and the record folded cleanly, while
    `EXIT_REFUSED`'s own contract sentence is "Nothing is folded" — returning it here
    would tell a caller the record is unreadable when the only unreadable thing is the
    caller's own argument. The identity rule is REUSED VERBATIM and only its REPORTING
    CHANNEL changes: the shared reason text travels intact, framed by one line of this
    caller's own context, because that text says "earlier event(s) on <item>" in the
    narrower callers' words and re-wording it inside the shared rule would fork the rule.
    """
    if not reference:
        if not events:
            raise BadArgument(
                '--echo', reference,
                'the folded prefix holds NO event line, so there is no last one to echo. '
                'Name a subject, or fold a prefix that contains one.')
        return events[-1]
    try:
        alias, want = split_digest_field(reference, 0)
    except BoardRefusal as exc:
        raise BadArgument('--echo', reference, exc.reason)
    key = RE_SUPERSEDES_KEY.match(alias)
    if key is None:
        raise BadArgument(
            '--echo', reference,
            'this is not a <date> <VERB> reference (BOARD-GRAMMAR §1). The echo names an '
            'event by THE GRAMMAR THE RECORD ALREADY USES and by no other form: '
            '`YYYY-MM-DD VERB` with an optional `%s<hex-prefix>` discriminator, which '
            '`--ep <ITEM>` prints beside every row so it is COPIED and never computed. A '
            'bare line number is not a reference here — a line number is a ROLE.'
            % DIGEST_FIELD)
    want_date, want_verb = key.group('date'), key.group('verb')
    candidates = [e for e in events
                  if e.date == want_date and e.kind == want_verb]
    if want is not None:
        try:
            return _pin_reference_by_digest(0, want, alias, 'the whole record',
                                            events, candidates)
        except BoardRefusal as exc:
            raise BadArgument(
                '--echo', reference,
                'the echo resolves over EVERY event the fold holds, not only over earlier '
                'events on one item. ' + exc.reason)
    if not candidates:
        raise BadArgument(
            '--echo', reference,
            'the alias %r names NO event in the folded prefix. It is not a report about '
            'the record, which read cleanly — it is a subject this caller named and this '
            'fold does not hold. If the event is real, it is past the `--at` bound.'
            % alias)
    if len(candidates) > 1:
        raise BadArgument(
            '--echo', reference,
            'the alias %r names %d events (%s) and an echo must be ABOUT ONE. An alias '
            'collides — the estate\'s normal gait puts many events under one date and one '
            'verb — so the discriminator is REQUIRED here, exactly as it is on every other '
            'reference in this grammar: carry `%s<hex-prefix>`. `--ep <ITEM>` prints the '
            'prefix of every row. The candidates are %s.'
            % (alias, len(candidates), ', '.join(':%d' % c.lineno for c in candidates),
               DIGEST_FIELD,
               ', '.join(':%d %s %s%s' % (c.lineno, c.item, DIGEST_FIELD,
                                          digest_prefix(c.raw))
                         for c in candidates)))
    return candidates[0]


def echo_effect(board, events, subject):
    """WHAT ONE EVENT DID — read from THE FOLD and from the event's VERB. Never from prose.

    THIS IS THE `:1180` DISCIPLINE INSTRUMENTED. That discipline asked the filing hand to
    fold the item and decide what its own append had done; three careful seats and one
    filter failed at the DECIDING step, and one of the three had written the law between
    the second failure and the third. The interpretation moves here.

    IT READS THE SAME FOLD THE BOARD PRINTS, and that is a choice against the obvious
    alternative. Differencing two bounded folds — `--at N-1` against `--at N`, which is
    how this pass's own plan hand-computed its expectations — would answer without the
    record's later corrections: a `DISAMBIGUATED` says which state a PAST ending ended,
    AS OF THAT ENDING'S OWN POSITION, and a prefix that stops at the ending cannot see it.
    Two answers about one record is the census defect this module exists to retire, so the
    echo reads the fold the board reads and there is one answer.

    POPULATION AND BASIS for each row, per §A51:

      ENDED    every event whose `closed_by` is this line. BASIS: the fold's own
               annotation, set in exactly three places — a later pending superseding an
               earlier one of its kind, `_apply_ending`, and `_apply_supersedes`. Taken
               over EVERY event and not narrowed to the subject's item, because a
               narrowing that later stopped being true would UNDER-report in silence.
      OPENED   the subject itself, when it is a pending. BASIS: `is_pending`.
      VOIDED   every event this line superseded that is not already an ENDED row. BASIS:
               the fold's `voided_by`. A `CORRECTED` whose target was not a pending ended
               no state and still did something, and a report that stayed silent there
               would be indistinguishable from a broken echo — A4's own argument, one
               category over.
      STATE    the item's state-bearing event before this line and after it. BASIS: the
               item's history in FOLD ORDER. `None` on either side is a REAL answer: an
               item may carry record-plane history and no lifecycle event at all.

    THE SUBJECT IS IN ITS ITEM'S HISTORY BY CONSTRUCTION — `fold` appends every event to
    the item it names — so no branch here guards against its absence. A guard for a
    condition that cannot arise is a check that cannot fail, and this module has spent a
    fortnight hunting those.
    """
    item = board[subject.item]
    before = None
    for ev in item.history:
        if ev is subject:
            break
        if not ev.is_history_only:
            before = ev
    ended = [e for e in events
             if e.closed_by == subject.lineno and e is not subject]
    voided = [e for e in events
              if e.voided_by == subject.lineno and not any(e is x for x in ended)]
    return {
        'subject': subject,
        'state_before': before,
        'state_after': before if subject.is_history_only else subject,
        'ended': ended,
        'opened': subject if subject.is_pending else None,
        'voided': voided,
        'moved_nothing': subject.is_history_only,
        'ended_nothing_ambiguous': subject.ending == 'AMBIGUOUS',
    }


def _echo_state_word(ev):
    """One side of the state delta. `None` is a REAL answer, not a missing one."""
    if ev is None:
        return 'NO STATE EVENT'
    return '%s (:%d)' % (ev.verb, ev.lineno)


def echo_lines(board, events, subject):
    """THE ECHO'S OWN OUTPUT — VERDICT ONLY, THE CLAUSE DELIBERATELY EXCLUDED.

    Split from `print_echo` for one reason and it is the control's: the clause-blindness
    property is proved by folding TWO WORLDS THAT DIFFER ONLY IN PROSE and requiring the
    SAME answer, and a comparison that carried the prose would differ by construction and
    prove nothing. `print_echo` quotes the clause AFTER these lines, under a label saying
    it was not read — the pass's whole argument, in the layout.
    """
    fx = echo_effect(board, events, subject)
    sub = fx['subject']
    out = [
        'ECHO — WHAT THIS EVENT DID, computed from THE FOLD and THE VERB alone.',
        '  BOARD-GRAMMAR (:1172): THE VERB OUTRANKS THE CLAUSE. No prose is matched and',
        '  no intent is inferred, so an event whose CLAUSE CONTRADICTS ITS VERB echoes',
        '  what the verb DID and never what the sentence claims.',
        '',
        '  SUBJECT :%d  %s%s  %s | %s | %s | %s'
        % (sub.lineno, DIGEST_FIELD, digest_prefix(sub.raw), sub.date, sub.item,
           sub.verb, sub.seat),
        '',
    ]
    for pend in fx['ended']:
        out.append('  ENDED    %s' % pend.verb)
        out.append('           on %s, opened at :%d' % (pend.item, pend.lineno))
    if fx['ended'] and sub.disambiguated_by is not None:
        out.append('           WHICH state it ended is THE RECORD\'S OWN answer: the '
                   'DISAMBIGUATED at :%d' % sub.disambiguated_by)
        out.append('           named it, and every other pending stood.')
    if fx['opened'] is not None:
        out.append('  OPENED   %s' % sub.verb)
        if sub.closed_by is None:
            out.append('           on %s, and it STANDS OPEN at this taking.' % sub.item)
        else:
            out.append('           on %s. A LATER event closed it at :%d — that is that '
                       'event\'s' % (sub.item, sub.closed_by))
            out.append('           effect and not this one\'s.')
    for tgt in fx['voided']:
        out.append('  VOIDED   the event at :%d (%s) on %s' % (tgt.lineno, tgt.verb,
                                                               tgt.item))
        out.append('           — superseded as provenance. No state ended here.')
    if fx['ended_nothing_ambiguous']:
        # LABELLED `CLOSED NOTHING` AND NOT `ENDED NOTHING`, DELIBERATELY. A reader's
        # filter for the ENDED rows is `startswith('ENDED')`, and a row that began with
        # the same word while meaning its opposite is the broken-filter class this estate
        # has paid for repeatedly — including once inside the very discipline this report
        # instruments. The prefixes are made DISJOINT rather than left to care.
        out.append('  CLOSED NOTHING — this ending names none of {%s}, which stand'
                   % ', '.join(sub.candidates))
        out.append('           open together. The fold REPORTS and never picks.')
    if fx['moved_nothing']:
        out.append('  MOVED NOTHING')
        out.append('           %s is RECORD-PLANE: it opened no state, it ended no state,'
                   % sub.verb)
        out.append('           and it is not this item\'s state. THE LINE LANDED AND THE '
                   'BOARD')
        out.append('           DID NOT MOVE.')
    out.append('  STATE    %s' % sub.item)
    out.append('           %s   ->   %s' % (_echo_state_word(fx['state_before']),
                                            _echo_state_word(fx['state_after'])))
    if fx['state_after'] is None:
        out.append('           THE ITEM HELD NO STATE before this line and holds none '
                   'after it.')
        out.append('           That is a LAWFUL record and not a fault: an item may carry '
                   'record-plane')
        out.append('           history and no lifecycle event at all.')
    return out


def print_echo(board, events, reference):
    """The echo, printed. The CLAUSE is quoted last and labelled as unread."""
    subject = resolve_echo_subject(events, reference)
    for line in echo_lines(board, events, subject):
        print(line)
    print('')
    print('  CLAUSE — QUOTED HERE AND READ NOWHERE. Every line above was computed '
          'without it.')
    print('  %s' % (subject.clause or '(this event carries no clause)'))
    return EXIT_OK


def _printed_attribution(item):
    """THE EVENT WHOSE SEAT AND COORDINATE PRINT BESIDE THE STATE WORD (EP-28ZB C1).

    A state word and a coordinate printed side by side READ AS ONE CLAIM: that seat, on
    that line, produced that state. `last_event` is the latest event of ANY KIND, so where
    a record-plane verb lands after a state it took the bracket with it and the pair said
    something nobody did — the state's word beside another act's author. The two planes
    are already separated in `print_item`, which annotates the same line RECORD-PLANE;
    only this summary paired them.

    WHERE A STATE EXISTS its own event is the attribution, and nothing else can be: the
    coordinate is a claim ABOUT THE STATE and must therefore come from it.

    WHERE THERE IS NO STATE the `last_event` fallback STANDS BYTE-FOR-BYTE, and it is not
    a leftover. An item may carry record-plane history and no state at all — the queued
    intake lines per `BOARD-EVENTS.log:247` are exactly that shape — and a cell reading
    `item.state.date` would leave with the interpreter's 1 on a LAWFUL record. That is the
    fault-case the old comment named, it is still real, and the branch that answers it is
    unchanged. Repairing the attribution does not license removing it.
    """
    if item.state is not None:
        return item.state
    return item.last_event


def _state_cell(item):
    """The item's state cell. An item MAY have no state — see the note below.

    A record-plane verb (`NOTED`, `SEATED`, `DISAMBIGUATED`) is history and not state, so
    an item whose ONLY events are record-plane has HISTORY AND NO STATE. That is not a
    curiosity: the queued intake lines per `BOARD-EVENTS.log:247` are exactly that shape
    for four items the fold has never seen. It is displayed as what it is. Nothing here
    invents a state, and nothing here crashes on the absence of one.
    """
    if item.state is None:
        parts = ['NO STATE EVENT — %d record-plane event(s), no lifecycle event'
                 % len(item.history)]
        shown = set()
    else:
        parts = [item.state.verb]
        shown = {item.state.lineno}
    for pend in item.open_pendings():
        if pend.lineno not in shown:
            parts.append('OPEN: ' + pend.verb)
    return '  '.join(parts)


def print_board(board, meta):
    print('BOARD — folded from %s (%d lines, %d events, seed at %d-%d)'
          % (meta['path'], meta['lines'], meta['events'],
             meta['seed_start'], meta['seed_end']))
    print('%d items. Absence of events reads as NOT-STARTED, and that reading rests '
          'ENTIRELY on the seed being complete.' % len(board))
    print('')
    width = max(len(n) for n in board) if board else 4
    for name in sorted(board):
        item = board[name]
        # THE COORDINATE COMES FROM THE STATE'S OWN EVENT where there is a state, and
        # falls back to the last event of any kind ONLY where there is none (EP-28ZB C1).
        # It read `item.last_event` unconditionally, which is why a NOTED landing after a
        # state printed that state's word beside the NOTED's seat and line. The fallback
        # is kept exactly as it was and for exactly its old reason: an item may carry
        # record-plane history and no state at all, and a cell that read `item.state.date`
        # would leave with the interpreter's 1 on a LAWFUL record.
        last = _printed_attribution(item)
        print('%-*s  %s  [%s %s :%d]' % (width, name, _state_cell(item),
                                         last.date, last.seat, last.lineno))
    _print_reference_report(board)


def print_item(board, name):
    if name not in board:
        print('UNKNOWN-ITEM: %r' % name)
        print('The fold has NEVER SEEN this name. THIS IS NOT "NOT-STARTED".')
        print('Absence of events reads as not-started only for names the seed covers, '
              'and no unknown name borrows that guarantee.')
        return EXIT_UNKNOWN_ITEM
    item = board[name]
    print('%s — %s' % (name, _state_cell(item)))
    print('')
    for ev in item.history:
        marks = []
        if ev.voided_by is not None:
            marks.append('VOID, superseded by line %d' % ev.voided_by)
        if ev.closed_by is not None:
            marks.append('closed by line %d' % ev.closed_by)
        if ev.resolution in ('AMBIGUOUS', 'UNRESOLVED'):
            marks.append('reference %s' % ev.resolution)
        if ev.ending == 'AMBIGUOUS':
            marks.append('ENDING AMBIGUOUS — names none of {%s}; NOTHING closed'
                         % ', '.join(ev.candidates))
        elif ev.ending == 'NAMED' and ev.disambiguated_by is not None:
            marks.append('ended the %s, said so by the DISAMBIGUATED at :%d; every other '
                         'pending stands' % (ev.candidates[0], ev.disambiguated_by))
        elif ev.ending == 'NAMED' and ev.candidates:
            marks.append('ends the %s it NAMES; every other pending stands'
                         % ev.candidates[0])
        if ev.kind in HISTORY_ONLY_KINDS:
            marks.append('RECORD-PLANE — history only; opens nothing, ends nothing, '
                         'and is not this item\'s state')
        if ev.kind == 'DISAMBIGUATED':
            marks.append('resolves the ending %r as having ended %s, AS OF THAT ENDING\'S '
                         'OWN POSITION' % (ev.dis_ending, ev.dis_ended))
        suffix = ('   <- ' + '; '.join(marks)) if marks else ''
        # THE EXHIBITION (EP-28Y W3). The token printed is the token a reference carries,
        # byte for byte, so a discriminator is COPIED and never computed by hand. Print
        # and parse are ONE CONTRACT and the standing control drives the round trip.
        print('  :%-4d %s%s  %s%s' % (ev.lineno, DIGEST_FIELD, digest_prefix(ev.raw),
                                      ev.one_line(), suffix))
    return 0


def print_stale(board, meta, since):
    rows = stale_items(board, since)
    dates = sorted(set(e.date for item in board.values() for e in item.history))
    print('STALE — items with no event since %s' % since)
    print('')
    print('  THIS FLAG IS AN INVITATION TO A LOOK. IT IS NEVER A VERDICT. It cannot')
    print('  tell a correctly-waiting item from a forgotten one, and it does not try.')
    print('  CAPS ON THIS OUTPUT, stated because a writer of events needs them more')
    print('  than a reader of the board does:')
    print('   1. RESOLUTION IS THE DATE FIELD, WHOLE DAYS. THIS LOG HOLDS %d DISTINCT '
          'DATE(S)' % len(dates))
    print('      (%s .. %s). An item touched ten times'
          % (dates[0] if dates else '-', dates[-1] if dates else '-'))
    print('      on one date and an item touched once are INDISTINGUISHABLE here. At')
    print('      one distinct date this query cannot discriminate at all, and a zero')
    print('      below means that and not "nothing is stale".')
    print('   2. AGE IS MEASURED FROM THE ITEM\'S LAST EVENT TO %s — the reference you'
          % since)
    print('      passed, NOT a wall clock. Nothing here reads the system time.')
    print('   3. AN ITEM WITH NO EVENTS CANNOT APPEAR. A thing nobody ever recorded is')
    print('      invisible to a staleness query by construction.')
    print('   4. WHO comes from the item\'s OPEN pendings only. A stale item carrying no')
    print('      OWED and no HELD shows "—" — that is a gap in the RECORD, not an item')
    print('      that waits on nobody.')
    print('')
    if not rows:
        print('  (no items) — and read cap 1 before reading that as good news.')
    else:
        width = max(len(r[0]) for r in rows)
        for name, age, who in rows:
            print('  %-*s  %4d day(s)   %s' % (width, name, age, who))
    _print_reference_report(board)


def _print_ambiguous_endings(board):
    """WRITER-FACING. Endings that could not say which pending they ended.

    This is the pair law's clause 3 arriving as OUTPUT rather than as an announcement. It
    names the ITEM, the ENDING EVENT'S LINE and the CANDIDATE SET, which is exactly what a
    writer needs to file the `CORRECTED` that resolves it. Nothing here is closed by pick,
    so the board above shows both states standing — the report explains why.
    """
    rows = [(n, ev, cands) for n in sorted(board)
            for ev, cands in board[n].ambiguous_endings]
    if not rows:
        return
    print('')
    print('FOR THE WRITER OF EVENTS — %d ending(s) that named none of two-or-more open '
          'states.' % len(rows))
    print('  NOTHING WAS CLOSED BY ANY OF THESE. Both states stand on the board above, '
          'because the record does not say which one ended and this fold does not pick.')
    print('  BOARD-GRAMMAR §1: while two or more states stand open on one item, an event '
          'that ends one NAMES the one it ends.')
    for name, ev, cands in rows:
        print('  AMBIGUOUS-ENDING :%-4d %s -> %s could have ended any of {%s}'
              % (ev.lineno, name, ev.verb, ', '.join(cands)))


def _print_pair_report(board):
    """WRITER-FACING. THE THIRD REPORT CLASS (EP-30-R4), beside AMBIGUOUS and UNRESOLVED.

    Both of those resolve WITHIN ONE ITEM — `UNRESOLVED` reads "matches no earlier event on
    this item" — and a pair is across items by definition, so neither could ever express
    this. It is a REPORT and never a refusal: two endings cannot land in one append, and a
    fold that refused between two lawful appends would take the record plane down for the
    width of one hand.

    IT NAMES BOTH SIDES AND BOTH COORDINATES, never a count. A count tells a reader that
    something is wrong and not where, which sends the reader back to the fold they are
    already holding.
    """
    rows = half_ended_pairs(board)
    if rows:
        print('')
        print('FOR THE WRITER OF EVENTS — %d NAMED PAIR(S) WITH ONE SIDE ENDED AND THE '
              'OTHER STILL STANDING.' % len(rows))
        print('  One decision is lawfully filed TWICE when two seats each witness it, and '
              'A DECISION FILED TWICE NEEDS ITS ENDING FILED TWICE. The fold has no notion '
              'that two items track one decision except the one each clause declares, so '
              'a half-ended ruling folds as two clean states and reads as deliberate.')
        print('  NOTHING HERE IS A REFUSAL AND NOTHING WAS CLOSED. A pair is lawfully '
              'half-ended for the width of one hand between two appends; what this reports '
              'is a half-ending THAT PERSISTED TO THIS TAKING.')
        for item, ev, here, other, target, there in rows:
            print('  HALF-ENDED-PAIR :%-4d %s %s %s   <->   :%-4d %s %s %s'
                  % (ev.lineno, item.name, ev.verb, 'STANDS' if here else 'ENDED',
                     target.lineno, target.item, target.verb,
                     'STANDS' if there else 'ENDED'))
    unres = [(n, ev) for n in sorted(board) for ev in board[n].unresolved_pairs]
    if unres:
        print('')
        print('FOR THE WRITER OF EVENTS — %d PAIRING(S) THIS FOLD COULD NOT PIN TO AN '
              'EVENT.' % len(unres))
        print('  The board above is unaffected in its STATE — a pairing is a NAMING and '
              'never a state claim. What is lost is the pair, so the half-ending check '
              'above cannot see either side of it.')
        for name, ev in unres:
            print('  PAIR-UNRESOLVED :%-4d %s -> %r names no earlier event on %r'
                  % (ev.lineno, name, ev.pair_ref, ev.pair_item))


def _print_reference_report(board):
    """WRITER-FACING. The references this fold could not pin down, named for the seat
    that wrote them — a reader of the board cannot act on these and a writer can."""
    _print_ambiguous_endings(board)
    _print_pair_report(board)
    amb = [(n, ev, k) for n in sorted(board) for ev, k in board[n].ambiguous]
    unres = [(n, ev) for n in sorted(board) for ev in board[n].unresolved]
    if not amb and not unres:
        return
    print('')
    print('FOR THE WRITER OF EVENTS — %d CORRECTED reference(s) this fold could not '
          'pin to exactly one event.' % (len(amb) + len(unres)))
    print('  The board above is unaffected in its STATE; what is lost is which earlier '
          'event each of these replaced.')
    for name, ev, count in amb:
        print('  AMBIGUOUS  :%-4d %s -> %d candidates; the LATEST was voided'
              % (ev.lineno, name, count))
    for name, ev in unres:
        print('  UNRESOLVED :%-4d %s -> %r matches no earlier event on this item'
              % (ev.lineno, name, ev.supersedes))


OWNER_TABLE_STOP = """\
--owner-table IS NOT BUILT, AND THAT IS A STOP RAISED BY EP-28U's BUILDER, NOT AN OMISSION.

EP-28U's W2 directs an `item | with | state` table, an `OWNER` marker in a `with` column,
and a `Closed since <date>` line, citing BOARD-GRAMMAR.md §7 as its source.

BOARD-GRAMMAR.md §7 AS IT STANDS SAYS THE OPPOSITE, IN ITS OWN WORDS:
    "NO `Line` header, NO `with` column, NO `Closed since` line — those belong to the
     arc board the owner rejected."

Both are dated 2026-08-08 and the record says which came first: EP-28U was authored at
commit dfb38c3 (08:02:20), and §7 carried the `with` + `Closed since` shape AT THAT
COMMIT — so W2 is a faithful copy of the spec as it then stood. §7 was marked
PROVISIONAL/CONFLICT at 28d7a9a (08:08:20) and REPLACED at 9aa8b42 (08:10:19) by a spec
derived from the owner-approved example artifact, which refuses that shape by name.

Building W2 as written would ship the owner-REJECTED board a second time; §7's own
history records that it was shipped once already and corrected the same night. So it is
not built. The stop is raised to the mentor with the coordinates above.

WHAT §7 ACTUALLY ASKS THIS TOOL FOR, derived and stated so the ruling is cheap: "The
state column is FOLDED from planning/build/BOARD-EVENTS.log once tools/board lands; the
what-it's-for sentences are STABLE and human-written." That is a STATE COLUMN keyed by
item name — which `--board` already emits — and NOT a table. The residual needs a
decision rather than evidence: the events file knows NO arc membership and NO purpose
sentence, so even a correct §7 emitter cannot build those rows here. It can supply the
state column only, and the caller must own the rows.
"""


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog='tools/board/board.py',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='The board as a COMPUTED VIEW over planning/build/BOARD-EVENTS.log. '
                    'READS ONLY — this tool writes nothing, anywhere.',
        epilog='EXIT CODES, DECLARED:\n' + '\n'.join(
            '  %d  %s' % (code, DECLARED_EXIT_CODES[code])
            for code in sorted(DECLARED_EXIT_CODES)))
    ap.add_argument('--events', default=EVENTS, help='path to the events log')
    ap.add_argument('--board', action='store_true', help='every item, current state')
    ap.add_argument('--ep', metavar='ITEM',
                    help="one item's state and event history. Each row carries the "
                         "event's %s<hex-prefix> — COPY it into a DISAMBIGUATED reference "
                         "where <date+verb> names more than one event (BOARD-GRAMMAR §1)."
                         % DIGEST_FIELD)
    ap.add_argument('--echo', nargs='?', const='', metavar='REF',
                    help='WHAT AN EVENT DID — the state-delta report (:1192). With no REF '
                         'the subject is the LAST EVT line of the folded prefix, which is '
                         'the line a filing hand has just written. REF is `<date> <VERB>` '
                         'with the optional %s<hex-prefix> discriminator — THE RECORD\'S '
                         'OWN reference grammar and not a second one. The VERB is read '
                         'and the CLAUSE never is.' % DIGEST_FIELD)
    ap.add_argument('--stale', nargs='?', const='', metavar='DATE',
                    help='items with no event since DATE (default: the newest date in '
                         'the log). AN INVITATION TO A LOOK, NEVER A VERDICT.')
    ap.add_argument('--owner-table', action='store_true',
                    help='STOPPED by EP-28U`s builder — run it to read why')
    # `--at` AND `--anchor` ARE TAKEN AS STRINGS AND VALIDATED HERE, NOT BY `argparse`.
    # `type=int` would hand a bad value to argparse's own usage error, which leaves with
    # 2 — this tool's REFUSAL code. EP-28W raised that collision and it is not this pass's
    # to repair; it is this pass's not to CREATE A SECOND INSTANCE OF.
    ap.add_argument('--at', metavar='N',
                    help='fold exactly the prefix [1..N] of the record and nothing '
                         'beyond it (BOARD-GRAMMAR §1a). Appends past N are lawful and '
                         'invisible to the answer.')
    ap.add_argument('--anchor', metavar='DIGEST',
                    help='re-check a prior taking: REFUSES WHOLE, naming both digests, '
                         'if the folded content no longer matches this %s digest.'
                         % ANCHOR_ALGO)
    args = ap.parse_args(argv)

    if args.owner_table:
        print(OWNER_TABLE_STOP, end='')
        return EXIT_OWNER_TABLE_STOP

    # THE TOOL APPLIES ITS OWN STANDARD TO ITS OWN ARGUMENTS (EP-28W W3). Validated HERE,
    # before the log is read, because a caller who mistyped an argument should not be told
    # about the record: the finding belongs to the input, and the code says so.
    at = None
    try:
        if args.stale:
            parse_date_argument('--stale', args.stale)
        if args.at is not None:
            at = parse_at_argument(args.at)
        if args.anchor is not None:
            parse_anchor_argument(args.anchor)
    except BadArgument as bad:
        print('REFUSED — %s %r: %s' % (bad.option, bad.value, bad.reason))
        print('This is a BAD ARGUMENT and it leaves with %d, which is distinct from '
              'every other code this tool returns AND from the interpreter\'s 1. A '
              'caller can tell input-error from refusal from crash.'
              % EXIT_BAD_ARGUMENT)
        print('  --stale with NO argument is valid: it uses the newest date in the '
              'log.')
        return EXIT_BAD_ARGUMENT

    ok, notes = positive_control()
    if not ok:
        print('UNINTERPRETABLE — the positive control FAILED, so no count from this run '
              'means anything and none is printed.')
        for note in notes:
            print('  ' + note)
        return EXIT_REFUSED

    try:
        events, meta = read_events(args.events, at=at)
        board = fold(events)
    except BadArgument as bad:
        # `--at` BEYOND END-OF-FILE. It is an INPUT error, not a record one: the record is
        # fine and the coordinate asked about is not in it.
        print('REFUSED — %s %r: %s' % (bad.option, bad.value, bad.reason))
        print('This is a BAD ARGUMENT and it leaves with %d.' % EXIT_BAD_ARGUMENT)
        return EXIT_BAD_ARGUMENT
    except BoardRefusal as exc:
        print('REFUSED at %s:%d — %s' % (args.events, exc.lineno, exc.reason))
        print('Nothing is folded. A line this tool cannot read EXACTLY is never skipped: '
              'a partial fold is a board that has quietly lost an item.')
        return EXIT_REFUSED
    except (IOError, OSError) as exc:
        print('REFUSED — cannot read %s: %s' % (args.events, exc))
        return EXIT_REFUSED

    if args.anchor is not None and args.anchor != meta['anchor_digest']:
        # REFUSE WHOLE, NAMING BOTH. The subject moved under the taking, and this estate's
        # standing preference is to refuse rather than proceed on a changed subject. The
        # count is NOT offered as a reason either way: two prefixes of equal length can
        # differ, which is exactly the hole §1a's fix closes.
        print('REFUSED — THE ANCHOR DOES NOT MATCH, so this taking is about a DIFFERENT '
              'SUBJECT than the one that was anchored.')
        print('  anchored: %s:%s' % (ANCHOR_ALGO, args.anchor))
        print('  now:      %s:%s' % (ANCHOR_ALGO, meta['anchor_digest']))
        print('  at N=%d line(s). A LINE COUNT IS A ROLE — "however many lines there '
              'happen to be" — so an equal N is NOT agreement. The content digest is the '
              'coordinate and it says these are not the same [1..N].' % meta['anchor_n'])
        print('Nothing is folded. BOARD-GRAMMAR §1a: a removal inside the prefix '
              'invalidates the anchor LOUDLY.')
        return EXIT_REFUSED

    rc = EXIT_OK
    if args.ep:
        rc = print_item(board, args.ep)
    elif args.echo is not None:
        # THE SUBJECT IS VALIDATED HERE AND NOT BESIDE `--stale`'s SHAPE CHECK, because it
        # cannot be: resolving it needs the folded record, and the fold happens above. The
        # code it leaves with is still the ARGUMENT's — the record read cleanly and what
        # could not be resolved is the subject this caller named. `EXIT_REFUSED`'s own
        # contract sentence is "Nothing is folded", and everything IS folded here.
        try:
            rc = print_echo(board, events, args.echo)
        except BadArgument as bad:
            print('REFUSED — %s %r: %s' % (bad.option, bad.value, bad.reason))
            print('This is a BAD ARGUMENT and it leaves with %d, not %d. THE RECORD '
                  'FOLDED CLEANLY — the anchor below says over exactly which lines.'
                  % (EXIT_BAD_ARGUMENT, EXIT_REFUSED))
            rc = EXIT_BAD_ARGUMENT
    elif args.stale is not None:
        since = args.stale or max(e.date for e in events)
        print_stale(board, meta, since)
    else:
        print_board(board, meta)

    print('')
    print('positive control PASSED — ' + '; '.join(notes))
    print(anchor_text(meta))
    for notice in meta.get('glue_notices', ()):
        print('GLUE NOTICE ' + notice)
    for alarm in meta.get('glue_alarms', ()):
        print('GLUE ALARM ' + alarm)
    return rc


if __name__ == '__main__':
    sys.exit(main())
