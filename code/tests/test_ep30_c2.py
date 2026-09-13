"""EP-30-C2 — NO REPLAYED STATE: the fold changes how many entries land, never what any entry says.

THIS MODULE ESTABLISHES A MEASUREMENT OVER A VIEW NO COMMAND HAD EVER DRIVEN.
Before it landed, `grep -rln 'message_ledger' --include='*.py' .` (archive excluded) returned
`src/subsystems/comms.py` ALONE — the file that DEFINES the method and nothing that drives it —
while its sibling `queue_depth`, seven lines away in the same class, was driven by two test files.
That absence is this unit's red fact (board :1663), and it is why this is ESTABLISHMENT rather
than reconciliation: nothing here reconciles a disagreement, because nothing had ever asked.

THE LAW THIS IMPLEMENTS, in the ruling's own words (:1547): fold-world and non-fold-world derive
IDENTICAL `message_ledger` output — sends derivable ENTRY BY ENTRY with payloads byte-exact,
NEVER equal counts — and a run that stores only a count REDS the row. The owner ruled the run the
identifiable entity with its sends' kept contents and EVERY FINER TIER DERIVABLE (:1475).

THE TWO THINGS THAT MAKE THIS MEASUREMENT MEAN ANYTHING, both learned at the build hand and both
guarded by rows below rather than by this docstring:

1.  NON-VACUITY — THE FOLD MUST ACTUALLY FOLD. `gate.execute` blocks to durability, so ONE caller
    can NEVER fill a batch: a sequential workload at the shipped width reports `largest_batch == 1`
    and IS width 1 wearing a 16. A comparison run that way compares a configuration against itself
    and establishes nothing. The cure is EP-28C W6's, settled and accepted: concurrent submitters
    through a `threading.Barrier`, with NON-VACUITY rows asserting the widths actually differed in
    the variable under test, ASSERTED FIRST so a vacuous run fails loudly instead of passing
    quietly.

2.  DETERMINISM — THE ORDER CLAUSE MUST BE ABOUT THE FOLD. Concurrency buys non-vacuity and costs
    determinism: if the measured sends raced each other, their ledger order would differ between
    arms by THREAD SCHEDULING and the row would red for a reason that is not the fold. So the
    measured channel has exactly ONE sender issuing blocking sends (its order is fixed by
    construction), and the batches are filled by CONCURRENT FILLER records on unrelated identities.
    The measured sends therefore share their batches with other acts — which is precisely the
    condition :1547 legislates about — while their order remains a fact and not a race.

3.  DECLARATION — THE EXCLUSION SET IS FIXED, NAMED, AND FALSIFIABLE. The comparison excludes five
    run-artifact fields, and those five are DECLARED at `RUN_ARTIFACT_FIELDS` below rather than
    derived per run. A derivation taken from the very pair it is about to make comparable has its
    content decided by the thing it exists to judge, and driven it CAME OUT DIFFERENT ACROSS RUNS —
    five fields in 11 of 30 trials, three in the other 19, dropping `record_id` and `seq`. A5 went
    red in 0 of 30 NOT BECAUSE IT WAS SAFE: the derivation went narrow precisely in the runs where
    the control pair agreed on position, and in those same runs the measured arms agreed too, so
    THE NARROW SET WAS NEVER ONCE TESTED AGAINST A DISAGREEMENT. A safety that is a correlation is
    not a coverage. Ruled `:1714`.

    AND THE DECLARATION CARRIES ITS OWN FALSIFIER, because a declaration nobody can falsify is
    worse than the derivation it replaced — it can quietly exclude something substantive and no
    reader would ever see it. `test_A5_every_declared_exclusion_earns_its_place_by_varying_between_two_drives`
    drives a control pair AT ONE WIDTH and requires EVERY declared member to actually differ, with
    the two fields the law names asserted NOT to differ FIRST so the row fails loudly rather than
    passing vacuously.

4.  WARRANT — THE DRIVER ITSELF REFUSES AN EMPTY POPULATION. The ladder is three deep: acceptance
    rows guarded by red worlds, red worlds guarded by the plant-removed control, AND THE DRIVER BOTH
    LAYERS CALL GUARDED BY NOTHING. Handed two well-formed artifacts with empty ledgers, `--compare`
    reported `LENGTH left 0, right 0 -> SAME`, `A5 IDENTICAL ENTRY BY ENTRY`, `A6 BYTES EXACT IN
    BOTH WORLDS` and rc 0 — and that command is the driven object every A5 and A6 artifact names for
    a second hand to re-run. A COMPARISON OF NOTHING WITH NOTHING IS NOT A PASSING COMPARISON, IT IS
    AN ABSENT ONE. `refuse_empty_population` now refuses every population a verdict ranges over, on
    either artifact, before one line of either verdict is rendered, and the CLI exits `REFUSED_EXIT`
    — A THIRD CODE, because 0 would say IDENTICAL and 1 would make a comparison that never happened
    indistinguishable from one that failed. Ruled `:1750`.

    NOTHING ALREADY FILED WAS WRONG. Every landed artifact named a real population of four entries.
    THE EVIDENCE WAS GOOD AND ITS WARRANT WAS ABSENT, AND THOSE ARE DIFFERENT REPAIRS.

THE FILLERS CARRY DISTINCT ACCOUNT IDS ON PURPOSE. EP-28C W4e found two concurrent creates of ONE
identity producing TWO records; nothing here goes near that seam, and a filler that collided would
be measuring that finding instead of this one.

WHAT THIS MODULE MAY NOT DO: `src/subsystems/comms.py` is OUTSIDE THIS UNIT'S FENCE, deliberately.
If the measurement reds, that is a RAISE AND A FINDING — never a licence to edit the subject.
"""

import ast
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.blobs import BlobStore  # noqa: E402
from kernel.boot import build_kernel  # noqa: E402
from kernel.commit import BATCH_WIDTH_CAP  # noqa: E402
from subsystems.comms import CommsView  # noqa: E402

#: THE SHIPPED WIDTH, READ FROM THE KERNEL'S OWN CONSTANT AND NEVER SPELLED HERE. A literal 16
#: beside `commit.BATCH_WIDTH_CAP` would be a second copy of one fact, and this estate has found
#: that class four times in a week. If the cap moves, this module moves with it.
WIDTH_SHIPPED = BATCH_WIDTH_CAP
WIDTH_ONE = 1

#: THE MEASURED CHANNEL. One channel, one sender, so its ledger order is a fact.
CHANNEL = "ep30c2:measured"

#: THE SENT PAYLOADS — DISTINCT FROM EACH OTHER, WHICH IS A REQUIREMENT AND NOT A STYLE CHOICE.
#: Identical payloads make an entry-by-entry comparison pass under an implementation that returns
#: the SAME entry three times — a check that cannot fail, and the exact failure this unit exists to
#: exclude. Each string is its own length and its own bytes so a truncation, a repeat, or a
#: normalisation is visible in the comparison rather than absorbed by it.
MESSAGES = (
    "ALPHA-first-payload",
    "BRAVO-second-payload-which-is-longer",
    "CHARLIE-third",
)

#: FILLER SHAPE. Eight threads times four records is thirty-two submissions released together, which
#: is what makes a batch wider than one form at all. The rows assert the OUTCOME (`largest_batch`)
#: rather than trusting these numbers — a countable read from the run, never a hope about a shape.
FILLER_THREADS = 8
FILLER_EACH = 4

ENTITY = "ep30c2-p1"
PEER = "ep30c2-p2"
ROLE = "user-facing"

#: THE EXCLUSION SET. **DECLARED, NOT DERIVED** — five fields, named here, IDENTICAL EVERY RUN.
#:
#: WHAT EACH ONE IS, because a list of names is not a justification. `record_id` and `seq` are both
#: `len(events) + 1` at the append (`src/kernel/store.py`, the append path), so BOTH ARE PURE
#: FUNCTIONS OF ABSOLUTE POSITION IN THE RECORD STREAM — how many records landed before this one,
#: which the concurrent fillers decide and the fold does not. The three time fields are minted at
#: the append from the wall clock. **NONE OF THE FIVE IS A STATEMENT ABOUT WHAT THE ENTRY SAYS**,
#: which is the only thing `:1547` legislates about.
#:
#: WHY DECLARED. A set derived per run **from the very pair it is about to compare** has its content
#: decided by the thing it exists to judge. Driven, that derivation varied across runs — 5 fields in
#: 11 of 30 trials, 3 in the other 19 — and it was narrow **precisely when the control pair agreed
#: on position, which is when the measured arms agreed too.** A5's greenness rested on a correlation
#: between the control pair and the measured pair, never on coverage. Ruled `:1714`.
#:
#: WHAT THE DECLARATION MAKES IMPOSSIBLE, AND WHO ABSORBS IT. A sixth field varying between the two
#: worlds can no longer be absorbed silently into the exclusion set — it REDS A5, which is a finding
#: about the record. A field wrongly declared here is absorbed by
#: `test_A5_every_declared_exclusion_earns_its_place_by_varying_between_two_drives`, which requires
#: every member to be shown varying for a reason that is not the fold.
RUN_ARTIFACT_FIELDS = ("record_id", "seq", "record_time", "submission_time", "occurrence_time")

#: THIS MODULE'S OWN SOURCE, resolved against the file and never against cwd. The red-world direction
#: row reads it back to check a property of the rows themselves.
THIS_FILE = os.path.abspath(__file__)

#: THE TWO KEYS EVERY §4 ROW'S DOCSTRING CARRIES. §4 is DIFFERENTIAL, NEVER DIRECTIONAL: the verdict
#: MOVES when the plant is removed, and WHICH WAY is a property of the individual row. R3's plant
#: makes the calibration REFUSE, and refusing is R3 SUCCEEDING — the opposite polarity to R1 and R2,
#: which is why no clause can carry the direction and every row must state its own (`:1715`).
DIRECTION_KEYS = ("PLANT PRESENT", "PLANT REMOVED")


class Run:
    """ONE ARM: the world, what it was told to do, and WHAT IT ACTUALLY DID.

    `width_from_run` and `largest_batch` are read OFF THE COMMITTER AFTER THE FACT — never inferred
    from the command that started the arm. A run that believed it was at width 1 and was not would
    report the shipped width's result under the override's name, and `commit._calibration` refuses
    rather than falling back precisely so that cannot happen quietly. This class is where the
    refusal's guarantee is turned into a figure the close can quote.
    """

    def __init__(self, store, blobs, ledger, sent):
        gc = store.group_commit
        self.store, self.blobs, self.ledger, self.sent = store, blobs, ledger, sent
        self.width_from_run = gc.width
        self.largest_batch = gc.largest_batch
        self.batches = gc.batches
        self.members = gc.members

    def facts(self):
        return {
            "width_from_run": self.width_from_run,
            "largest_batch": self.largest_batch,
            "batches": self.batches,
            "members": self.members,
            "ledger_entries": len(self.ledger),
        }


def drive(width=None, root=None, prior_records=0):
    """THE DRIVER. One recorded workload, one world, one ledger.

    `width=None` leaves the committer exactly as `commit._calibration()` built it — which is how
    the A3/A4 arms exercise `GOVOS_COMMIT_WIDTH` as an ENVIRONMENT fact end to end. An explicit
    `width` sets the committer directly (EP-28C W6's pattern), which is how the rows below stay
    deterministic no matter what environment the suite is discovered under.

    `prior_records` APPENDS THAT MANY UNRELATED RECORDS BEFORE THE WORKLOAD, AND IT EXISTS FOR
    EXACTLY ONE ROW. The falsification row must show `record_id` and `seq` differing between two
    arms AT ONE WIDTH — otherwise those two names sit in a declared exclusion set with nothing
    behind them. Left to the scheduler that variation is a RACE: it comes from the fillers
    interleaving differently between two runs, and the derivation this declaration replaced saw it
    in only 11 of 30 trials. Shifting the stream by a known number of unrelated appends makes the
    same variation A CONSTRUCTION — 30 of 30 at the build hand — and a control whose answer is a
    fact is worth more than one whose answer is usually a fact.

    THE SHIFT MOVES POSITION AND NOTHING ELSE, and the row asserts that rather than trusting it:
    the extra acts are `CREATE-ACCOUNT` on identities the channel never names, so
    `message_ledger(CHANNEL)` filters them out entirely — same length, same actions, same payloads,
    different absolute position. That is precisely the shape of a RUN artifact, which is why it is
    the right instrument for proving one.
    """
    d = tempfile.mkdtemp(prefix="ep30c2-", dir=root)
    blobs = BlobStore(os.path.join(d, "blobs"))
    store, gate, _views = build_kernel(os.path.join(d, "record.jsonl"), blobs=blobs)
    if width is not None:
        store.group_commit.width = width

    for k in range(prior_records):
        gate.execute("CREATE-ACCOUNT", "SYSTEM",
                     {"account_id": "ep30c2-prior-%d" % k, "actor_class": "process"})

    gate.execute("CREATE-ACCOUNT", "SYSTEM", {"account_id": ENTITY, "actor_class": "process"})
    gate.execute("CREATE-ACCOUNT", "SYSTEM", {"account_id": PEER, "actor_class": "process"})
    gate.execute("COMMS-OPEN", ENTITY, {"channel": CHANNEL, "entity": ENTITY, "role": ROLE})

    # THE FILLERS. Released together by a barrier so their submissions OVERLAP; without overlap the
    # queue drains empty between blocking calls and every batch closes at width one.
    errors = []
    barrier = threading.Barrier(FILLER_THREADS + 1, timeout=60)

    def filler(i):
        try:
            barrier.wait()
            for k in range(FILLER_EACH):
                gate.execute("CREATE-ACCOUNT", "SYSTEM",
                             {"account_id": "ep30c2-fill-%d-%d" % (i, k), "actor_class": "process"})
        except BaseException as exc:                                 # noqa: BLE001 — reported below
            errors.append(repr(exc))
            barrier.abort()

    threads = [threading.Thread(target=filler, args=(i,), daemon=True)
               for i in range(FILLER_THREADS)]
    for t in threads:
        t.start()
    barrier.wait()

    # THE MEASURED SENDS — ONE THREAD, BLOCKING, SO THEIR ORDER IS CONSTRUCTION AND NOT SCHEDULING.
    sent = []
    for message in MESSAGES:
        rec = gate.execute("COMMS-SEND", ENTITY,
                           {"channel": CHANNEL, "message": message, "to": PEER})
        sent.append({"message": message, "message_hash": rec["payload"]["message_hash"]})
    gate.execute("COMMS-RECV", PEER,
                 {"channel": CHANNEL, "message_hash": sent[0]["message_hash"]})

    for t in threads:
        t.join(timeout=120)
    if errors:
        raise AssertionError("filler threads failed, so the arm is not the arm it claims: %r"
                             % (errors,))

    ledger = [dict(e) for e in CommsView(store).message_ledger(CHANNEL)]
    for e in ledger:
        e["payload"] = dict(e.get("payload") or {})
    return Run(store, blobs, ledger, sent)


# ---- THE COMPARISON ------------------------------------------------------------------------

#: THE EXCLUSION SET IS **DECLARED** AT `RUN_ARTIFACT_FIELDS` AND THE FUNCTION BELOW DOES NOT DECIDE
#: IT. That inversion is this cycle's whole change and it is worth stating where the old derivation
#: stood: `fields_that_vary` USED to produce the set, from the very pair the comparison was about to
#: judge; it now only REPORTS what varied, and its single caller is the row that tries to FALSIFY the
#: declaration. A function that answers a question is safe; the same function answering it ABOUT
#: ITSELF was the defect (`:1714`).


def fields_that_vary(left, right):
    """Field names differing at ANY entry between two ledgers. **A MEASUREMENT, NOT A DECISION.**

    ITS ONE CALLER IS THE FALSIFICATION ROW, AND IT MUST NEVER REGAIN THE OTHER JOB. Wired back
    into the comparison it would restore the exact structure ruled out: an exclusion set whose
    content is decided by the pair it exists to make comparable, going narrow precisely when that
    pair agrees — and therefore never once tested against a disagreement.

    Callers pass LEDGERS, not `Run` objects, so the row can hand it any two entry lists. A length
    disagreement is invisible here by construction (`zip` truncates) and the row asserts equal
    length before reading this at all — an absence that is a property of the instrument is stated
    where the instrument is, never left for a reader to discover.
    """
    varied = set()
    for ea, eb in zip(left, right):
        for key in set(ea) | set(eb):
            if ea.get(key) != eb.get(key):
                varied.add(key)
    return varied


def _is_red_world_row(name):
    """`test_R<digit>…` — a §4 red-world row, AND THE DIGIT IS LOAD-BEARING.

    THE FIRST FORM OF THIS PREDICATE WAS `startswith("test_R")` AND IT SWEPT IN THE ROW THAT
    ENFORCES §4, which is a check ABOUT red worlds and carries no plant of its own. A letter is a
    naming coincidence; §4 names FIVE red worlds R1–R5, so the population is rows carrying a
    RED-WORLD NUMBER. A row merely starting with the letter does not, and it is excluded for a
    reason rather than by being renamed around the checker — which was the other available fix and
    would have left the predicate wrong.

    THIS DOCSTRING PREDICTED R5 BEFORE R5 EXISTED, AND THE PREDICTION IS RECORDED BECAUSE IT HELD:
    it read *a fifth red world lands inside it automatically*, and when §4 gained R5 at `:1750` this
    predicate swept the new rows in with no edit at all. The count in the sentence above is the only
    thing that moved — WHICH IS THE COST A LITERAL COUNT CHARGES EVERY TIME THE THING IT COUNTS
    GROWS, and it is charged here rather than hidden.
    """
    return name.startswith("test_R") and name[6:7].isdigit()


def red_world_rows(source):
    """Every §4 red-world row in a module source, by name — the population, read from the source.

    AST AND NEVER A GREP. A pattern over prose would count this docstring's own mention of the row
    prefix, which is the self-matching class this estate has now paid for in a `grep -v` that could
    not exclude itself and in an R4 control that found its own coined token.
    """
    return [node.name for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.FunctionDef) and _is_red_world_row(node.name)]


def rows_missing_a_direction_block(source):
    """Red-world rows whose docstring does not state BOTH sides of its differential."""
    missing = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.FunctionDef) and _is_red_world_row(node.name):
            doc = ast.get_docstring(node) or ""
            if not all(key in doc for key in DIRECTION_KEYS):
                missing.append(node.name)
    return missing


def rows_comparing_a_returncode_to_a_symbol(source):
    """Rows asserting a CHILD PROCESS's `returncode` against a NAME instead of against a literal.

    **A CONSTANT SHARED BY THE CHECK AND THE CHECKED IS NOT A CHECK** (`:1793`). R5's row runs the
    driver as a child process FROM THIS SAME SOURCE FILE, so an assertion naming `REFUSED_EXIT`
    compares the constant WITH ITSELF: move it and the driver and the assertion move together. Driven
    before the repair — constant set to 1, driver exits 1 MEANING DIVERGENT — the row read `OK`.

    THE LITERAL IS THEREFORE LOAD-BEARING, AND IT LOOKS EXACTLY LIKE A MAGIC NUMBER A LATER HAND
    WOULD HELPFULLY REPLACE WITH THE SYMBOL. That replacement IS the defect, and it would land
    silently because every row would still pass. This is the guard that makes it loud.

    AST AND NEVER A GREP, for this module's standing reason: a token search cannot separate a
    subject from its description. A grep for `compare_entrywise` inside `_compare` returns one hit
    and THE HIT IS A COMMENT SAYING THE FUNCTION IS NOT CALLED.
    """
    hits = []
    for node in ast.walk(ast.parse(source)):
        if not (isinstance(node, ast.FunctionDef) and node.name.startswith("test")):
            continue
        for call in ast.walk(node):
            if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
                    and call.func.attr == "assertEqual" and len(call.args) >= 2):
                continue
            observed, expected = call.args[0], call.args[1]
            if (isinstance(observed, ast.Attribute) and observed.attr == "returncode"
                    and not isinstance(expected, ast.Constant)):
                hits.append(node.name)
    return hits


class EmptyPopulation(ValueError):
    """R5's REFUSAL. A `ValueError` **SUBCLASS** AND NOT A BARE ONE, AND THE SUBCLASSING IS THE POINT.

    `__main__` must tell a refusal from every other failure, and `json.JSONDecodeError` IS ITSELF A
    `ValueError` — so a bare `except ValueError` around the driver would catch a MALFORMED artifact
    and report it as an EMPTY POPULATION. **A refusal that can misname its own cause is the exact
    shape this row exists to remove, arriving inside the row's own repair**, which is why the
    catchable type is narrowed to one thing rather than to a base class that happens to include it.
    """


#: **THE DRIVER'S THIRD EXIT CODE, AND THE THIRD STATE IS THE WHOLE OF R5.** `0` means IDENTICAL and
#: `1` means DIVERGENT. Without a third, REFUSED has to borrow one of them, and a second hand reading
#: only the code could not tell a comparison that FAILED from one that NEVER HAPPENED — which is the
#: conflation this row exists to break, re-created in the instrument while being removed from the
#: prose. **AN ABSENT COMPARISON IS NOT A PASSING COMPARISON AND IT IS NOT A FAILING ONE EITHER.**
REFUSED_EXIT = 2


def refuse_empty_population(what, side, population):
    """R5. **A VERDICT OVER AN EMPTY POPULATION IS ABSENT, NOT PASSING — SO THE DRIVER REFUSES.**

    THE LADDER WAS THREE DEEP AND ONLY TWO RUNGS WERE GUARDED (`:1750`). The acceptance rows are
    guarded by red worlds; the red worlds are guarded by the plant-removed control added at `:1706`
    because R1 passed vacuously; **and the driver both layers call was guarded by nothing.** Handed
    two well-formed artifacts with empty ledgers it reported `LENGTH left 0, right 0 -> SAME`,
    `A5 IDENTICAL ENTRY BY ENTRY`, `A6 BYTES EXACT IN BOTH WORLDS` and **rc 0**.

    **THE RULE IS OVER POPULATIONS AND NOT OVER THE LEDGER, AND THAT GENERALISATION WAS DRIVEN
    RATHER THAN REASONED.** §4 states R5's drive as *two artifacts whose LEDGERS are empty* — one
    instance — and writing the guard from the instance in front of the author is the named defect
    `:1715` already cost this plan two cycles. So each population a verdict ranges over was driven
    EMPTY WITH EVERY OTHER POPULATION THAT CAN INDEPENDENTLY BE FULL, at the build hand, and the
    sizes travel as literals `(ledger, sent, hashes)` because **HOW MANY OTHERS STAY FULL IS A FACT
    OF THE DEPENDENCY STRUCTURE AND NEVER THREE-MINUS-ONE**:

        LEDGER EMPTY, SENT FULL      (0, 2, 0)  A5 renders IDENTICAL over nothing; A6 is real.
                                     ONE other full, never two — the COMMS-SEND hashes are DERIVED
                                     from the ledger, so emptying it empties them, BY CONSTRUCTION
        SENT EMPTY, LEDGER FULL      (3, 0, 2)  A5 is real; A6 renders BYTES EXACT over nothing
        LEDGER HOLDS NO COMMS-SEND   (2, 2, 0)  both lists full, yet the cross-world line compares
                                     [] to [] and prints SAME

    HISTORICAL, KEPT VISIBLE RATHER THAN QUIETLY FIXED (`:1820`). This paragraph read *EMPTY WITH
    THE OTHERS FULL … all three are independently reachable*, written from §4's clause of the same
    shape. **BOTH WERE WITHDRAWN AS UNSATISFIABLE FOR THE LEDGER POPULATION** — a population claim
    about populations, asserted without reading their dependency structure. THE SUBSTANCE WAS ALWAYS
    MET and every landed verdict stands; the LITERAL FORM was unsatisfiable, and this module carried
    the withdrawn wording for a cycle after the plan withdrew it, so a close obeying §9 item 8 would
    have had to quote a clause the plan had already retracted.

    **A LEDGER-ONLY GUARD LEAVES THE SECOND AND THIRD PRINTING GREEN VERDICTS OVER NOTHING.** That
    is the same defect one population over, which is precisely how this row's own subject arrived.

    `what` and `side` are carried into the message because a refusal that does not say WHICH
    population was empty on WHICH artifact sends the reader back to the files to find out — and a
    reason nobody can act on is not a named reason.
    """
    if len(population) == 0:
        raise EmptyPopulation(
            "REFUSES rather than reporting a verdict over nothing: the %s population is EMPTY on "
            "the %s artifact. A COMPARISON OF NOTHING WITH NOTHING IS NOT A PASSING COMPARISON, "
            "IT IS AN ABSENT ONE." % (what, side))


def diverge_entrywise(left, right, exclude=()):
    """THE COMPARISON'S STRUCTURED FORM: `(index, field, left_value, right_value)` per divergence,
    with a length disagreement carried as index `None` and field `"LENGTH"`.

    THIS EXISTS BECAUSE R1 HAD TO ASSERT ON FORMATTED PROSE AND THEREFORE ASSERTED ALMOST NOTHING.
    A row that must prove *the entries at the swapped positions moved, by payload, in order* needs
    the VALUES the comparison saw, not a rendering of them; `d.startswith("ENTRY 0:")` is satisfied
    by any field at entry 0, which is how R1 came to pass with its plant removed (`:1706`).

    `compare_entrywise` renders this and its output is BYTE-FOR-BYTE what it always was, so every
    existing caller's contract is untouched — this is a second view of one computation, never a
    second computation.

    **R5's GUARD LIVES HERE, AT THE ROOT, AND `compare_entrywise` INHERITS IT.** The two are one
    computation and its rendering, so a refusal placed in both would be a second copy of one rule —
    the class this estate has now found four times in a week. Placed here it covers every caller of
    either: A5, A7, R1 and R2 all reach this function, and **this is the comparison BOTH LAYERS
    CALL** that §4's R5 bracket names.

    **EMPTY INPUT AND EMPTY OUTPUT ARE OPPOSITE FACTS AND THE WORD `empty` CARRIES BOTH.** An empty
    RETURN still means IDENTICAL and that contract is unchanged. What refuses is an empty
    ARGUMENT — a comparison with nothing to compare, which never had a verdict to report.
    """
    refuse_empty_population("left ledger entries", "left", left)
    refuse_empty_population("right ledger entries", "right", right)
    divergences = []
    if len(left) != len(right):
        divergences.append((None, "LENGTH", len(left), len(right)))
    for i, (ea, eb) in enumerate(zip(left, right)):
        for key in sorted((set(ea) | set(eb)) - set(exclude)):
            va, vb = ea.get(key), eb.get(key)
            if va != vb:
                divergences.append((i, key, va, vb))
    return divergences


def compare_entrywise(left, right, exclude=()):
    """ENTRY BY ENTRY, IN ORDER. Returns a list of divergences; EMPTY MEANS IDENTICAL.

    THIS FUNCTION IS THE ROW. It is written to be DRIVEN AGAINST DIVERGENCES rather than asserted
    about: R1 hands it a pair differing only in ORDER, R2 a pair differing in ONE PAYLOAD BYTE at
    equal count, and A7 a count-only stand-in — and it must name each. A comparison never seen
    failing has established nothing; it has only observed that an implementation agrees with itself.

    LENGTH IS REPORTED AND THEN THE COMMON PREFIX IS STILL WALKED, because stopping at the length
    turns an entry-by-entry check into a count check the moment the counts disagree — which is the
    precise shape :1547 legislates against.

    THE `exclude` DEFAULT IS EMPTY AND CALLING IT BARE IS A DECISION, NOT AN ABSENCE OF ONE. Two
    arms come from two `drive()` calls, so the run-artifact fields diverge at EVERY entry whatever
    the plant did; a caller that does not name an exclusion set is comparing clocks. Ruled `:1706`
    after R1 did exactly that.
    """
    divergences = []
    for i, key, va, vb in diverge_entrywise(left, right, exclude):
        if i is None:
            divergences.append("LENGTH: left has %d entries, right has %d" % (va, vb))
        else:
            divergences.append("ENTRY %d: field %r differs — left %r, right %r"
                               % (i, key, va, vb))
    return divergences


def search_py_tree(root, terms):
    """A1's SEARCH SHAPE AS A FUNCTION, so R4 can drive it over a PLANTED tree as well as the real one.

    R4 asserts that an absence is a fact about the TREE and not about the QUERY. Proving that needs
    the query pointed at something whose answer is known by construction, and the only way to build
    one is to plant the token — which must never happen inside this repository: a planted `.py` left
    behind would red R4 for every later hand, and a `.py` written into `tests/` is outside this
    unit's fence besides. So the shape is factored out and the plant lives in a temporary tree.
    """
    hits = {term: [] for term in terms}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in (".git", "archive")]
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            path = os.path.join(dirpath, fn)
            try:
                with open(path, encoding="utf-8", errors="replace") as fh:
                    body = fh.read()
            except OSError:
                continue
            for term in terms:
                if term in body:
                    hits[term].append(path)
    return hits


@contextlib.contextmanager
def count_only_message_ledger():
    """A7's STAND-IN: a `message_ledger` that keeps ONLY A COUNT and derives the ledger from it.

    IN-PROCESS AND REVERTED ON EXIT. `src/subsystems/comms.py` is outside this unit's fence and is
    never edited — the demonstration swaps the bound method for the duration of one `with` block and
    restores it, so the tree the suite runs against is byte-identical before and after. That is the
    plan's "revert the stand-in" honoured literally, and it is stronger than a revert: there is
    never a moment at which the file on disk is wrong.

    WHAT IT MODELS: an implementation that satisfies the WEAK reading of "no replayed state changes"
    — it gets the COUNT right and every entry identical — and violates the owner's, under which
    every finer tier is derivable. `:1547` requires such a run to RED, and this is the stand-in the
    requirement is measured against.
    """
    original = CommsView.message_ledger

    def counted(self, channel, as_of=None):
        entries = original(self, channel, as_of)
        count = len(entries)
        stub = {"action": "COMMS-SEND", "payload": {"channel": channel}}
        return [dict(stub, payload=dict(stub["payload"])) for _ in range(count)]

    CommsView.message_ledger = counted
    try:
        yield
    finally:
        CommsView.message_ledger = original


# ---- THE ROWS -----------------------------------------------------------------------------


class LedgerAcrossBothWidthsCase(unittest.TestCase):
    """A5/A6 and their non-vacuity guards, over one workload driven at both widths."""

    @classmethod
    def setUpClass(cls):
        cls.root = tempfile.mkdtemp(prefix="ep30c2-case-")
        # INTERLEAVED, shipped first: a second arm meets a warmer page cache, and the same
        # discipline EP-28C holds its measurement rows to is applied here so the two do not diverge
        # in method.
        cls.shipped = drive(width=WIDTH_SHIPPED, root=cls.root)
        cls.one = drive(width=WIDTH_ONE, root=cls.root)
        # THE FALSIFICATION PAIR, AND ITS JOB IS THE OPPOSITE OF THE PAIR THAT STOOD HERE. The old
        # control pair PRODUCED the exclusion set; this one TRIES TO BREAK IT. Both arms run at ONE
        # width, so nothing they differ in can be evidence about the fold, and they differ by a
        # KNOWN POSITIONAL SHIFT rather than by whatever the scheduler happened to do — the
        # derivation that shift replaces saw `record_id`/`seq` vary in only 11 of 30 trials, and a
        # control that is usually right is a control that is sometimes absent.
        cls.control_a = drive(width=WIDTH_ONE, root=cls.root, prior_records=0)
        cls.control_b = drive(width=WIDTH_ONE, root=cls.root, prior_records=1)

    @classmethod
    def tearDownClass(cls):
        for run in (cls.shipped, cls.one, cls.control_a, cls.control_b):
            try:
                run.store.close()
            except Exception:                                        # noqa: BLE001
                pass

    # ---- NON-VACUITY, ASSERTED BEFORE ANY EQUALITY ------------------------------------------

    def test_NON_VACUITY_1_the_shipped_arm_actually_folded(self):
        """THE CLAUSE THE REST OF THIS MODULE STANDS ON.

        `gate.execute` blocks to durability, so a SEQUENTIAL workload at width 16 reports
        `largest_batch == 1` and is width 1 in every respect that matters. Without this row the
        equality below would be an agreement between two runs of ONE configuration."""
        self.assertGreater(
            self.shipped.largest_batch, 1,
            "the shipped-width arm never formed a batch wider than one, so the two arms did not "
            "differ in the variable under test and every comparison below is vacuous — it would "
            "be width 1 against width 1 (facts: %r)" % (self.shipped.facts(),))

    def test_NON_VACUITY_2_the_width_one_arm_never_folded(self):
        self.assertEqual(
            self.one.largest_batch, 1,
            "the width-1 arm formed a batch wider than one, so the override did not take and the "
            "arms are not the two widths they claim to be (facts: %r)" % (self.one.facts(),))
        self.assertEqual(
            self.one.batches, self.one.members,
            "at width 1 every batch holds exactly one member, so batches and members must agree")

    def test_NON_VACUITY_3_each_arm_ran_at_the_width_it_claims_read_from_the_run(self):
        """The width is read OFF THE COMMITTER, never inferred from the call that started the arm."""
        self.assertEqual(self.shipped.width_from_run, WIDTH_SHIPPED)
        self.assertEqual(self.one.width_from_run, WIDTH_ONE)

    def test_NON_VACUITY_4_the_ledger_is_not_empty_and_holds_every_act(self):
        """An identity between two empty ledgers is an identity about nothing."""
        for name, run in (("shipped", self.shipped), ("width-1", self.one)):
            actions = [e["action"] for e in run.ledger]
            self.assertEqual(actions, ["COMMS-SEND"] * len(MESSAGES) + ["COMMS-RECV"],
                             "%s: the ledger does not hold the workload that was recorded" % name)

    def test_NON_VACUITY_5_the_sent_payloads_were_distinct_from_each_other(self):
        """Identical payloads would make an entry-by-entry comparison pass under an implementation
        that returned the same entry three times."""
        hashes = [s["message_hash"] for s in self.shipped.sent]
        self.assertEqual(len(set(hashes)), len(MESSAGES),
                         "the sends were not distinct, so the comparison below cannot fail on "
                         "content and this whole module would be a check that cannot fail")

    # ---- A5 — THE COMPARISON, ENTRY BY ENTRY ------------------------------------------------

    def test_A5_the_two_worlds_derive_an_identical_ledger_entry_by_entry(self):
        """A5. Same length, same order, same action per entry, same payload per entry — and then
        EVERY OTHER FIELD TOO, over the DECLARED exclusion set at `RUN_ARTIFACT_FIELDS`.

        THE LAW'S OWN CLAUSE IS ASSERTED WITH NO EXCLUSION SET AT ALL, and that ordering is the
        structural protection: length, order, action and payload are held before any field is
        excluded from anything, so no error in the declaration can lower this row below `:1547`.
        The declared set governs only the EXTRA strictness beyond the law — the eleven remaining
        fields of the envelope, which nothing before this unit ever compared.
        """
        self.assertEqual(len(self.shipped.ledger), len(self.one.ledger),
                         "the two worlds derived different numbers of entries")
        for i, (a, b) in enumerate(zip(self.shipped.ledger, self.one.ledger)):
            self.assertEqual(a["action"], b["action"], "entry %d: action differs" % i)
            self.assertEqual(a["payload"], b["payload"], "entry %d: payload differs" % i)
        self.assertEqual(
            compare_entrywise(self.shipped.ledger, self.one.ledger,
                              exclude=RUN_ARTIFACT_FIELDS), [],
            "the fold changed what a record says")

    def test_A5_the_declared_exclusion_set_never_covers_the_two_fields_the_law_names(self):
        """THE GUARD ON THE DECLARATION, AND IT GUARDS A LITERAL ON PURPOSE.

        `RUN_ARTIFACT_FIELDS` is a tuple in this file, so a later hand widening it by one name
        would silently lower every comparison in this module. A declaration is EDITABLE in a way a
        derivation is not, and that is the cost the declaration pays for being stable — so the cost
        gets a guard rather than a note. `action` and `payload` are the two fields `:1547` names by
        their own words, and neither may ever be excluded from anything here.
        """
        self.assertNotIn("action", RUN_ARTIFACT_FIELDS,
                         "the declared exclusion set covers `action`, which the law names")
        self.assertNotIn("payload", RUN_ARTIFACT_FIELDS,
                         "the declared exclusion set covers `payload`, which the law names")

    def test_A5_every_declared_exclusion_earns_its_place_by_varying_between_two_drives(self):
        """THE ROW THAT MAKES THE DECLARATION FALSIFIABLE. Without it a declaration is WORSE than
        the derivation it replaced — it could quietly exclude something substantive and no reader
        would ever see it, whereas a bad derivation at least changes shape between runs.

        THE PAIR IS AT ONE WIDTH, so nothing it differs in can be evidence about the fold, and it
        differs by a KNOWN POSITIONAL SHIFT (`prior_records`) rather than by scheduling luck. Every
        declared member must be shown ACTUALLY DIFFERING between those two arms: a member that does
        not vary is excluding something substantive under cover of a list.

        THE CONTROL IS ASSERTED FIRST, which is R1's repair applied to a new row rather than
        rediscovered later. A `fields_that_vary` that reported EVERY field would satisfy the
        positive half for any declaration whatever — including one covering `action` and `payload`
        — so the two fields the law names are asserted NOT to vary before a single declared member
        is asked about. A vacuous run fails loudly here instead of passing quietly below.
        """
        a, b = self.control_a, self.control_b

        # ---- THE PAIR IS THE PAIR IT CLAIMS TO BE: one width, one shape, one difference.
        self.assertEqual(a.width_from_run, b.width_from_run,
                         "the falsification pair ran at two different widths, so anything varying "
                         "between them could be evidence about the fold and proves nothing about "
                         "a run artifact")
        self.assertEqual(len(a.ledger), len(b.ledger),
                         "the falsification pair derived different numbers of entries, and "
                         "`fields_that_vary` truncates at the shorter — the reading below would be "
                         "over a prefix while reading as though it were over the whole")

        varied = fields_that_vary(a.ledger, b.ledger)

        # ---- THE CONTROL, FIRST. The instrument must be able to report a field as UNCHANGED.
        self.assertNotIn("action", varied,
                         "the control pair varied in `action` — the shift was supposed to move "
                         "POSITION and nothing else, so this instrument cannot distinguish a run "
                         "artifact from a substantive change and the row below asserts nothing")
        self.assertNotIn("payload", varied,
                         "the control pair varied in `payload` — same defect, and this is the "
                         "field `:1547` legislates about by name")

        # ---- EVERY DECLARED MEMBER, ONE AT A TIME, NAMED IN ITS OWN FAILURE.
        for field in RUN_ARTIFACT_FIELDS:
            self.assertIn(field, varied,
                          "%r is declared a run artifact and did NOT vary between two arms at one "
                          "width — it is excluding something substantive under cover of a list. "
                          "Varied: %r" % (field, sorted(varied)))

        # ---- AND NOTHING BEYOND THE DECLARATION. A sixth varying field is a finding about the
        # record, not a licence to widen the tuple — the same verdict the derived set used to
        # swallow silently, which is the whole reason the set is declared.
        self.assertEqual(varied, set(RUN_ARTIFACT_FIELDS),
                         "the control pair varied in a field the declaration does not name: %r"
                         % (sorted(varied - set(RUN_ARTIFACT_FIELDS)),))

    # ---- A6 — PAYLOAD BYTES, EXACT ----------------------------------------------------------

    def test_A6_every_send_resolves_to_the_bytes_that_were_sent_in_both_worlds(self):
        """A6, DERIVED AGAINST THE ARCHITECTURE RATHER THAN ASSUMED ABOUT IT.

        `COMMS-SEND`'s payload does NOT carry the message: it carries `message_hash`, and the bytes
        live CONTENT-ADDRESSED in the blob store. The owner's ruling — the bytes kept exactly as
        sent, every finer tier derivable — is therefore implemented AS content addressing, and the
        byte assertion belongs where the bytes are. Comparing payload dicts alone would assert only
        that two hashes match; this resolves each hash and compares the BYTES."""
        for name, run in (("shipped", self.shipped), ("width-1", self.one)):
            sends = [e for e in run.ledger if e["action"] == "COMMS-SEND"]
            self.assertEqual(len(sends), len(MESSAGES))
            for i, (entry, message) in enumerate(zip(sends, MESSAGES)):
                digest = entry["payload"]["message_hash"]
                self.assertTrue(run.blobs.has(digest),
                                "%s entry %d: the ledger names a blob the store does not hold, so "
                                "the contents are not derivable at all" % (name, i))
                self.assertEqual(run.blobs.get(digest), message.encode(),
                                 "%s entry %d: the kept bytes are not the sent bytes" % (name, i))

    def test_A6_the_two_worlds_name_the_same_bytes_for_each_send(self):
        s_hashes = [e["payload"]["message_hash"] for e in self.shipped.ledger
                    if e["action"] == "COMMS-SEND"]
        o_hashes = [e["payload"]["message_hash"] for e in self.one.ledger
                    if e["action"] == "COMMS-SEND"]
        self.assertEqual(s_hashes, o_hashes)

    # ---- A7 — THE COUNT-ONLY IMPLEMENTATION REDS --------------------------------------------

    def test_A7_a_count_only_implementation_REDS_the_comparison(self):
        """A7, AND IT IS THE ROW THAT MAKES THE REST MEAN ANYTHING.

        `:1547` requires that a run storing only a COUNT reds the row. A comparison never seen
        failing has established nothing — it has only observed that the current implementation
        agrees with itself. This drives the real comparison against a stand-in that gets the count
        exactly right and the contents wrong, and REQUIRES a divergence naming an entry."""
        with count_only_message_ledger():
            counted = [dict(e, payload=dict(e.get("payload") or {}))
                       for e in CommsView(self.one.store).message_ledger(CHANNEL)]
        self.assertEqual(len(counted), len(self.one.ledger),
                         "the stand-in must get the COUNT right, or it reds for the wrong reason "
                         "and demonstrates nothing about content")
        divergences = compare_entrywise(self.shipped.ledger, counted, exclude=RUN_ARTIFACT_FIELDS)
        self.assertNotEqual(divergences, [],
                            "THE COMPARISON PASSED A COUNT-ONLY IMPLEMENTATION: it cannot fail and "
                            "has established nothing (S5)")
        self.assertTrue(any("ENTRY " in d for d in divergences),
                        "the comparison reported a divergence but named no entry, so it is a count "
                        "check wearing an entry-by-entry name: %r" % (divergences,))

    def test_A7_the_stand_in_is_reverted_and_the_live_view_is_the_real_one(self):
        """The stand-in is a demonstration, not a change."""
        live = [dict(e) for e in CommsView(self.one.store).message_ledger(CHANNEL)]
        self.assertEqual([e["action"] for e in live],
                         ["COMMS-SEND"] * len(MESSAGES) + ["COMMS-RECV"])
        self.assertEqual(dict(live[0]["payload"])["message_hash"],
                         self.one.sent[0]["message_hash"])


class RedWorldsCase(unittest.TestCase):
    """R1, R2, R4 — the comparison and the absence shown FAILING. R3 and R5 each stand on their own
    below, in classes of their own, because each needs a fixture this one does not build.

    EVERY ROW IN THIS CLASS DRIVES ITS PLANT-REMOVED CONTROL AND ASSERTS BOTH SIDES (§4, S5b):

        THE ROW'S VERDICT **MOVES** WHEN THE PLANT IS REMOVED.
        WHICH WAY IT MOVES IS STATED BY THE ROW, NEVER BY THIS DOCSTRING.

    DIFFERENTIAL, NEVER DIRECTIONAL, AND THAT DISTINCTION WAS PAID FOR (`:1715`). A clause here
    reading *with the plant the row FAILS, plant removed it PASSES* is true of every row in THIS
    class and FALSE of R3 below, whose plant makes the calibration REFUSE — and refusing is R3
    SUCCEEDING. A generalisation written from the instances in front of the author, extended to
    rows whose polarity was never checked, is how a control clause comes to describe only half its
    population. So each row carries its own `PLANT PRESENT` / `PLANT REMOVED` block, and
    `RedWorldDirectionCase` below holds that as a property rather than a habit.

    THE CLAUSE EXISTS BECAUSE R1 PASSED WITH ITS PLANT REMOVED (`:1706`), and the shape of that
    failure is worth stating where it happened rather than only in the plan. R1 called
    `compare_entrywise` BARE. Its two ledgers come from two `drive()` calls, so `record_time`,
    `submission_time` and `occurrence_time` diverged at every entry no matter what the plant did,
    and its three assertions asked only: divergences non-empty · something names `ENTRY 0` · nothing
    names `LENGTH`. All three were satisfied by clocks. NOT ONE READ PAYLOAD OR ORDER.

    A RED WORLD IS ITSELF A CHECK, AND THIS MODULE'S WHOLE DISCIPLINE IS THAT A CHECK NEVER SHOWN
    FAILING PROVES NOTHING. That discipline was applied to the acceptance rows and never once to the
    rows that prove them — the stop set guarded A5 and left A5's guard unguarded.
    """

    @classmethod
    def setUpClass(cls):
        cls.root = tempfile.mkdtemp(prefix="ep30c2-red-")
        cls.shipped = drive(width=WIDTH_SHIPPED, root=cls.root)
        cls.one = drive(width=WIDTH_ONE, root=cls.root)
        # NO CONTROL PAIR IS DRIVEN HERE ANY MORE, AND ITS ABSENCE IS THE CHANGE. Two extra arms
        # used to run in this class for the sole purpose of DERIVING the exclusion set, so each
        # TestCase carried its own derivation and the two could — and did — come out different.
        # The set is now DECLARED at `RUN_ARTIFACT_FIELDS`, so every row in this module excludes
        # THE SAME FIVE NAMES whatever else moves. Two classes deriving one law separately is a
        # second copy of a fact, which is the class this estate has found four times in a week.

    @classmethod
    def tearDownClass(cls):
        for run in (cls.shipped, cls.one):
            try:
                run.store.close()
            except Exception:                                        # noqa: BLE001
                pass

    def unplanted(self):
        """The width-1 ledger copied and NOT touched — the plant-removed arm every row below uses."""
        return [dict(e, payload=dict(e["payload"])) for e in self.one.ledger]

    def test_R1_the_comparison_FAILS_on_order_at_equal_count(self):
        """R1. Swap two entries in one ledger — counts stay equal — and the comparison must name
        the POSITION. A comparison that passes here is a count comparison wearing an
        entry-by-entry name.

            PLANT PRESENT  : the comparison FAILS — 2 divergences, both `payload`, at the two
                             swapped positions, each carrying the value that moved
            PLANT REMOVED  : the comparison PASSES — zero divergences

        R1 ASSERTS ORDER OR IT ASSERTS NOTHING, so every assertion below reads THE THING THE PLANT
        MOVED: the entries at the swapped positions, BY PAYLOAD, IN ORDER. The exclusion set is
        NAMED and DECLARED — never bare, never derived from this very pair — because two arms from
        two drives differ in their clocks at every entry and a bare comparison here measures the
        clock. It was DERIVED until `:1714`, and a derivation that went narrow in exactly the runs
        where the arms agreed is why it no longer is.
        """
        baseline = self.unplanted()
        planted = self.unplanted()
        planted[0], planted[1] = planted[1], planted[0]

        # ---- THE PLANT IS VISIBLE AT ALL. Swapping two entries that say the same thing moves
        # nothing, and a row planted that way could not fail whatever the comparison did.
        self.assertNotEqual(baseline[0]["payload"], baseline[1]["payload"],
                            "the two swapped entries carry the same payload, so the plant moves "
                            "nothing and this red world cannot fail")
        self.assertEqual(planted[0]["payload"], baseline[1]["payload"],
                         "the plant did not put entry 1's payload at position 0")
        self.assertEqual(planted[1]["payload"], baseline[0]["payload"],
                         "the plant did not put entry 0's payload at position 1")
        self.assertEqual(len(planted), len(self.shipped.ledger),
                         "the plant must leave the counts equal or it reds for the wrong reason")

        # ---- PLANT REMOVED, ASSERTED FIRST (§4, S5b). A vacuous red world must fail LOUDLY here
        # rather than pass quietly below, which is the discipline the NON-VACUITY rows already hold.
        without_plant = compare_entrywise(self.shipped.ledger, baseline, exclude=RUN_ARTIFACT_FIELDS)
        self.assertEqual(
            without_plant, [],
            "R1 PASSES WITH ITS PLANT REMOVED: the comparison it claims to be proving already "
            "diverges without any plant, so this row was never measuring the plant and its verdict "
            "with the plant present is void (S5b). Exclusion set %r; divergences %r"
            % (sorted(RUN_ARTIFACT_FIELDS), without_plant))

        # ---- WITH THE PLANT: the comparison must fail AT THE SWAPPED POSITIONS, ON PAYLOAD.
        with_plant = diverge_entrywise(self.shipped.ledger, planted, exclude=RUN_ARTIFACT_FIELDS)
        self.assertNotEqual(with_plant, [], "the comparison passed a reordered ledger")
        self.assertNotIn("LENGTH", [field for _i, field, _a, _b in with_plant],
                         "this red world must fail on ORDER, not on count")

        moved = [(i, va, vb) for i, field, va, vb in with_plant if field == "payload"]
        self.assertEqual(
            [i for i, _va, _vb in moved], [0, 1],
            "the comparison did not name BOTH swapped positions on payload — it named %r, so it is "
            "not reading the thing the plant moved: %r"
            % ([i for i, _va, _vb in moved], compare_entrywise(
                self.shipped.ledger, planted, exclude=RUN_ARTIFACT_FIELDS)))
        # BY PAYLOAD, IN ORDER: at position 0 the comparison saw the unmoved left against the entry
        # that moved IN, and at position 1 the mirror. Asserting the VALUES is what makes this row
        # about order; asserting that a message merely mentions position 0 is what made it vacuous.
        self.assertEqual(moved[0][1], self.shipped.ledger[0]["payload"])
        self.assertEqual(moved[0][2], baseline[1]["payload"])
        self.assertEqual(moved[1][1], self.shipped.ledger[1]["payload"])
        self.assertEqual(moved[1][2], baseline[0]["payload"])

    def test_R2_the_comparison_FAILS_on_one_payload_byte_at_equal_count(self):
        """R2. One byte of one payload, counts equal — the exact shape :1547 legislates against,
        exhibited rather than asserted.

            PLANT PRESENT  : the comparison FAILS — one divergence, `payload` at entry 0, carrying
                             the altered digest against the original
            PLANT REMOVED  : the comparison PASSES — zero divergences
        """
        baseline = self.unplanted()
        planted = self.unplanted()
        digest = planted[0]["payload"]["message_hash"]
        flipped = digest[:-1] + ("0" if digest[-1] != "0" else "1")
        planted[0]["payload"]["message_hash"] = flipped
        self.assertEqual(len(planted), len(self.shipped.ledger))

        # PLANT REMOVED, ASSERTED FIRST (§4, S5b). R2's own assertion below already discriminated —
        # a clock divergence cannot name the field `payload` — so this row was never vacuous the way
        # R1 was. The control is driven anyway because §4 requires it PER ROW, and because "it
        # happens to discriminate" and "it was shown to discriminate" are two different states.
        # THE EXCLUSION SET IS NAMED HERE FOR THE SAME REASON IT IS NAMED IN R1: without it the
        # plant-removed arm reports the clocks and no control could ever read empty.
        without_plant = compare_entrywise(self.shipped.ledger, baseline, exclude=RUN_ARTIFACT_FIELDS)
        self.assertEqual(without_plant, [],
                         "R2 PASSES WITH ITS PLANT REMOVED (S5b): exclusion set %r, divergences %r"
                         % (sorted(RUN_ARTIFACT_FIELDS), without_plant))

        divergences = compare_entrywise(self.shipped.ledger, planted, exclude=RUN_ARTIFACT_FIELDS)
        self.assertNotEqual(divergences, [], "the comparison passed an altered payload")
        self.assertTrue(any(d.startswith("ENTRY 0:") and "payload" in d for d in divergences),
                        "the comparison failed but did not name the entry: %r" % (divergences,))
        # AND THE ALTERED BYTE IS WHAT IT NAMED — the value, not merely the position and field.
        named = [(i, va, vb) for i, field, va, vb in
                 diverge_entrywise(self.shipped.ledger, planted, exclude=RUN_ARTIFACT_FIELDS)
                 if field == "payload"]
        self.assertEqual([i for i, _va, _vb in named], [0],
                         "one payload was altered and the comparison named %r entries"
                         % ([i for i, _va, _vb in named],))
        self.assertEqual(named[0][2]["message_hash"], flipped)
        self.assertEqual(named[0][1]["message_hash"], digest)

    def test_R2_the_byte_assertion_FAILS_on_the_same_alteration(self):
        """A6's half of R2: the altered hash must stop resolving to the sent bytes.

            PLANT PRESENT  : the byte assertion FAILS — the altered digest resolves to nothing,
                             so the store cannot hand back the bytes it names
            PLANT REMOVED  : the byte assertion PASSES — the unaltered digest resolves to exactly
                             the bytes that were sent

        BOTH SIDES ARE HELD IN THIS ONE ROW because the plant is a value rather than a world: the
        altered digest and the original are two arguments to one call, so nothing has to be set up
        and torn down to move between them.
        """
        digest = self.one.sent[0]["message_hash"]
        flipped = digest[:-1] + ("0" if digest[-1] != "0" else "1")
        self.assertNotEqual(flipped, digest)
        self.assertFalse(self.one.blobs.has(flipped),
                         "an altered digest still resolved, so the byte assertion cannot fail")
        self.assertEqual(self.one.blobs.get(digest), MESSAGES[0].encode(),
                         "the control half: the UNaltered digest must still resolve exactly")

    def test_R4_the_absence_control_can_fail(self):
        """R4. The absence in A1 is a fact about the TREE, not about the query: the same search
        shape finds a term that is certainly present and finds nothing for a coined one.

            PLANT PRESENT  : the search FINDS the coined token — held by the synthetic-tree row
                             below, because the plant may never be written into this repository
            PLANT REMOVED  : the search finds NOTHING for the coined token while still finding the
                             present term — this repository is the plant-removed tree, and that is
                             what this row holds
        """
        root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
        # THE COINED TOKEN IS ASSEMBLED AT RUNTIME AND NEVER WRITTEN WHOLE. Spelled as one literal
        # it appears in THIS file, the search finds it here, and the row fails — a searcher firing
        # on itself, which is this estate's own named class arriving inside the control that exists
        # to prove a search can report an absence. Driven at the build hand, not reasoned about.
        coined = "zzq_coined_" + "token_that_no_file_holds"
        hits = search_py_tree(root, ("queue_depth", coined))
        self.assertNotEqual(hits["queue_depth"], [],
                            "the search found nothing for a term that is certainly present, so its "
                            "empty answers say nothing about the tree")
        self.assertEqual(hits[coined], [],
                         "a coined token was found, so the search cannot report an absence")

    def test_R4_the_search_shape_finds_a_planted_token_and_stops_when_it_is_removed(self):
        """R4's PLANT-REMOVED CONTROL (§4, S5b), and it is driven over a SYNTHETIC TREE ON PURPOSE.

            PLANT PRESENT  : the search FINDS the planted token, and the present term with it
            PLANT REMOVED  : the search finds NOTHING for either, once the planted file is deleted

        R4 above proves the search fires (`queue_depth`) and reports an absence (the coined token).
        What it does NOT show is the coined half moving between the two states — and §4 requires
        every red world to exhibit exactly that: the verdict MOVES when the plant is removed.
        Showing it needs the token planted somewhere the search will reach.

        THE PLANT NEVER GOES IN THIS REPOSITORY. A `.py` written into the tree would red R4 for
        every later hand if it survived, and `tests/` is not this unit's fence to write into
        besides. So the same search shape is pointed at a temporary tree whose answer is known by
        construction, which is what makes this a control rather than a second reading of R4.
        """
        coined = "zzq_coined_" + "token_that_no_file_holds"
        tmp = tempfile.mkdtemp(prefix="ep30c2-r4-")
        planted_path = os.path.join(tmp, "planted_module.py")
        with open(planted_path, "w", encoding="utf-8") as fh:
            fh.write("PRESENT = 'queue_depth'\nPLANTED = '%s'\n" % coined)

        with_plant = search_py_tree(tmp, ("queue_depth", coined))
        self.assertEqual(with_plant[coined], [planted_path],
                         "WITH THE PLANT the search did not find the token, so it cannot fail and "
                         "R4's absence says nothing about the tree")
        self.assertEqual(with_plant["queue_depth"], [planted_path],
                         "the control tree's present-term half did not fire either")

        os.remove(planted_path)
        without_plant = search_py_tree(tmp, ("queue_depth", coined))
        self.assertEqual(without_plant[coined], [],
                         "PLANT REMOVED and the search still reported the token, so its answer is "
                         "not a fact about the tree it walked")
        self.assertEqual(without_plant["queue_depth"], [],
                         "PLANT REMOVED and the present-term half still reported a hit")


class WidthOverrideCase(unittest.TestCase):
    """R3 — the override REFUSES rather than falling back."""

    def test_R3_an_unreadable_width_REFUSES_and_gives_the_reason(self):
        """R3, AND S4 IS WHAT IT GUARDS. If `GOVOS_COMMIT_WIDTH` fell back to the shipped width
        instead of refusing, the A4 arm would have been measuring fold-world under
        non-fold-world's name for this unit's whole life.

            PLANT PRESENT  : the calibration REFUSES with its reason — AND REFUSING IS THIS ROW
                             SUCCEEDING, which is the polarity no §4 clause can carry (`:1715`)
            PLANT REMOVED  : the calibration ACCEPTS and returns the width — held by the control
                             row below

        R3'S DIRECTION IS THE OPPOSITE OF R1'S AND R2'S AND THAT IS WHY EACH ROW STATES ITS OWN.
        A clause reading *with the plant the row FAILS* describes R1 and R2 exactly and describes
        this row backwards; it stood for two cycles because it was written from the two rows in
        front of its author and generalised to four.
        """
        from kernel import commit as commit_mod
        saved = os.environ.get(commit_mod.WIDTH_ENV)
        os.environ[commit_mod.WIDTH_ENV] = "not-a-number"
        try:
            with self.assertRaises(ValueError) as caught:
                commit_mod._calibration()
            self.assertIn("REFUSES rather than falling back", str(caught.exception))
        finally:
            if saved is None:
                os.environ.pop(commit_mod.WIDTH_ENV, None)
            else:
                os.environ[commit_mod.WIDTH_ENV] = saved

    def test_R3_the_refusal_control_a_readable_width_is_accepted(self):
        """THE CONTROL, AND IT IS R3's PLANT-REMOVED ARM (§4, S5b) — named as such rather than left
        to be recognised.

            PLANT PRESENT  : the calibration REFUSES — held by the unreadable-width row above
            PLANT REMOVED  : the calibration ACCEPTS and returns the width — held HERE

        R3's plant is the unreadable `GOVOS_COMMIT_WIDTH`. A refusal that fires on everything proves
        nothing about the unreadable case, which is the same defect as a comparison that diverges
        without a plant, arriving at a different row."""
        from kernel import commit as commit_mod
        saved = os.environ.get(commit_mod.WIDTH_ENV)
        os.environ[commit_mod.WIDTH_ENV] = "1"
        try:
            width, _window = commit_mod._calibration()
            self.assertEqual(width, 1)
        finally:
            if saved is None:
                os.environ.pop(commit_mod.WIDTH_ENV, None)
            else:
                os.environ[commit_mod.WIDTH_ENV] = saved

    def test_R3_a_width_below_one_REFUSES(self):
        """R3's SECOND PLANT: a width that PARSES and is out of range, which the first plant cannot
        reach — `not-a-number` never gets past the read, so nothing in this class would otherwise
        show the range check firing at all.

            PLANT PRESENT  : the calibration REFUSES a width below one — REFUSING IS SUCCEEDING
            PLANT REMOVED  : the calibration ACCEPTS a readable in-range width — held by the
                             control row above, which is the plant-removed arm for both plants
        """
        from kernel import commit as commit_mod
        saved = os.environ.get(commit_mod.WIDTH_ENV)
        os.environ[commit_mod.WIDTH_ENV] = "0"
        try:
            with self.assertRaises(ValueError):
                commit_mod._calibration()
        finally:
            if saved is None:
                os.environ.pop(commit_mod.WIDTH_ENV, None)
            else:
                os.environ[commit_mod.WIDTH_ENV] = saved


class EmptyPopulationCase(unittest.TestCase):
    """R5 — THE DRIVER REFUSES AN EMPTY POPULATION, EXHIBITED RATHER THAN STATED.

    THE LADDER IS THREE DEEP AND THIS MODULE BUILT TWO RUNGS (`:1750`). Acceptance rows are guarded
    by red worlds. Red worlds are guarded by the plant-removed control added at `:1706` because R1
    passed vacuously. **AND THE DRIVER BOTH LAYERS CALL WAS GUARDED BY NOTHING** — handed two
    well-formed artifacts with empty ledgers it returned `LENGTH left 0, right 0 -> SAME`,
    `A5 IDENTICAL ENTRY BY ENTRY`, `A6 BYTES EXACT IN BOTH WORLDS`, **rc 0**, and that command is
    the driven object every A5 and A6 artifact names for a second hand to re-run.

    **NOTHING ALREADY FILED IS WRONG, AND THE SCOPE STATEMENT IS PART OF THE ROW.** Every landed
    artifact named a real population of four entries and every verdict on them stands. **THE
    EVIDENCE IS GOOD AND ITS WARRANT WAS ABSENT, AND THOSE ARE DIFFERENT REPAIRS** — this class
    repairs the warrant and touches no verdict.

    THE ARTIFACTS HERE ARE SYNTHETIC AND KNOWN BY CONSTRUCTION, for R4's reason exactly: proving a
    driver's treatment of an EMPTY population needs a population whose emptiness is a fact of the
    fixture rather than an outcome of a run, and a kernel drive can only ever produce a full one.

    **WELL-FORMED HERE MEANS WELL-FORMED FOR THIS DRIVER — carrying every field the driver reads —
    AND THE CONTROL PROVES IT BY THE DRIVER ACCEPTING THE PAIR.** The envelope fields A5's
    in-process row compares (`record_id`, `seq`, the three time fields and the rest) are NOT read by
    `_compare` and are NOT carried here. That cap is stated rather than left for a reader to
    discover, because an unstated absence in a fixture is how a strawman passes for a subject.
    """

    #: DISTINCT FROM EACH OTHER, for the reason `MESSAGES` at the top of this module is distinct.
    SENT_MESSAGES = ("ALPHA-first-payload", "BRAVO-second-payload-which-is-longer")

    @classmethod
    def artifact(cls, ledger_actions=("COMMS-SEND", "COMMS-SEND", "COMMS-RECV"), with_sent=True):
        """One well-formed-for-this-driver artifact. Every population is set by an argument, so a
        row can empty EXACTLY ONE — and how many of the rest stay full is a fact of the dependency
        structure, never three-minus-one: the COMMS-SEND hashes are derived FROM the ledger, so
        emptying the ledger empties them too. The sizes this produces are pinned as literals by
        `test_R5_the_COMMAND_refuses_all_three_populations_at_the_third_exit_code`.

        HISTORICAL (`:1820`): this docstring read *leave the other two full*, withdrawn with §4's
        clause of the same shape as unsatisfiable for the ledger population."""
        import hashlib
        messages = cls.SENT_MESSAGES if with_sent else ()
        digest = "sha256:" + hashlib.sha256(cls.SENT_MESSAGES[0].encode()).hexdigest()
        return {
            "driver": "tests/test_ep30_c2.py --emit-ledger",
            "env_GOVOS_COMMIT_WIDTH": "<unset>",
            "run_facts": {"width_from_run": WIDTH_SHIPPED, "largest_batch": 9,
                          "batches": 4, "members": 36, "ledger_entries": len(ledger_actions)},
            "sent": [{"message": m,
                      "message_hash": "sha256:" + hashlib.sha256(m.encode()).hexdigest()}
                     for m in messages],
            "ledger": [{"action": action, "payload": {"channel": CHANNEL, "message_hash": digest}}
                       for action in ledger_actions],
        }

    def write_pair(self, doc):
        """The same artifact on both sides, written to a fresh temporary directory."""
        d = tempfile.mkdtemp(prefix="ep30c2-r5-")
        paths = []
        for side in ("left", "right"):
            path = os.path.join(d, "%s.json" % side)
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(doc, fh, indent=2)
            paths.append(path)
        return paths

    def drive_compare(self, left, right):
        """THE LITERAL COMMAND §4 NAMES, run as a child process so the EXIT CODE is a real one.

        `GOVOS_COMMIT_WIDTH` is scrubbed from the child's environment. `_compare` reads two files
        and builds no kernel, so the variable cannot change its answer — it is removed so the row's
        result does not depend on what the suite was invoked under, which is the same discipline
        `DocMapCase` applies to cwd.
        """
        env = dict(os.environ)
        env.pop("GOVOS_COMMIT_WIDTH", None)
        return subprocess.run([sys.executable, THIS_FILE, "--compare", left, right],
                              capture_output=True, text=True, env=env, timeout=180)

    def test_R5_the_driver_REFUSES_two_well_formed_artifacts_whose_ledgers_are_empty(self):
        """R5, AS THE LITERAL `--compare` COMMAND AND NOT AS AN IN-PROCESS STAND-IN.

            PLANT PRESENT  : the driver REFUSES — exit 2, `REFUSED:` on stderr naming the empty
                             population and its side, and NOT ONE VERDICT LINE on stdout.
                             REFUSING IS THIS ROW SUCCEEDING — R3's polarity, the opposite of R1's,
                             which is why every row states its own (`:1715`)
            PLANT REMOVED  : the driver ACCEPTS — exit 0, both verdicts rendered over real
                             populations

        THE ROW DRIVES THE COMMAND BECAUSE THE COMMAND IS THE DRIVEN OBJECT. §9 requires every
        verdict to name the literal command or module path driven, and calls a fixture drive
        reported as the command the breach. An in-process call to `_compare` would prove the guard
        and prove NOTHING about the exit code a second hand actually reads.
        """
        full = self.artifact()
        planted = self.artifact(ledger_actions=())

        # ---- THE PLANT IS THE ONLY DIFFERENCE, ASSERTED AND NOT ASSUMED. A row whose two arms
        # differ in more than the plant cannot attribute the movement to the plant.
        self.assertEqual(planted["ledger"], [], "the plant did not empty the ledger")
        self.assertNotEqual(full["ledger"], [], "the plant-removed arm has an empty ledger too, so "
                                                "there is no differential to observe")
        for key in ("driver", "env_GOVOS_COMMIT_WIDTH", "sent"):
            self.assertEqual(full[key], planted[key],
                             "the two arms differ in %r as well as in the plant" % key)

        # ---- PLANT REMOVED, ASSERTED FIRST (§4, S5b). A vacuous red world fails LOUDLY here.
        left, right = self.write_pair(full)
        without = self.drive_compare(left, right)
        self.assertEqual(without.returncode, 0,
                         "R5's PLANT-REMOVED ARM DID NOT PASS: the driver refused or diverged over "
                         "an artifact with EVERY population full, so this row is not measuring the "
                         "plant and its verdict with the plant present is void (S5b). "
                         "stdout %r stderr %r"
                         % (without.stdout, without.stderr))
        self.assertIn("A5 VERDICT    : IDENTICAL ENTRY BY ENTRY", without.stdout)
        self.assertIn("A6 VERDICT    : BYTES EXACT IN BOTH WORLDS", without.stdout)
        self.assertNotIn("REFUSED", without.stderr,
                         "the driver refused a pair with every population full, so its refusal "
                         "fires on everything and says nothing about emptiness")

        # ---- PLANT PRESENT: the ledgers are empty and the driver must REFUSE.
        left, right = self.write_pair(planted)
        with_plant = self.drive_compare(left, right)

        # ---- THE LITERAL, AND THE SYMBOL IS REFUSED HERE ON PURPOSE (`:1793`). This line read
        # `REFUSED_EXIT`, WHICH THE DRIVER ALSO READS — and this row runs the driver as a CHILD
        # PROCESS FROM THIS SAME SOURCE FILE, so the assertion was comparing the constant WITH
        # ITSELF. Set it to 1 and the child exits 1, MEANING DIVERGENT, while this line still
        # passed, because both sides moved together. DRIVEN BEFORE THE REPAIR: with the constant at
        # 1 the row read `OK`. **A CONSTANT SHARED BY THE CHECK AND THE CHECKED IS NOT A CHECK**,
        # and the check written to hold the third state could not fail on the third state.
        #
        # ONE SIDE CARRIES THE LITERAL AND IT IS THIS ONE. The symbol is pinned separately by
        # `test_the_refusal_exit_code_is_a_third_state_and_the_other_two_are_occupied`, and the two
        # fail on DIFFERENT mutations: this line reds when the constant MOVES, that row reds when
        # the constant and the driver DRIFT APART.
        self.assertEqual(with_plant.returncode, 2,
                         "the driver did not refuse two artifacts whose ledgers are EMPTY — it "
                         "returned %d. A COMPARISON OF NOTHING WITH NOTHING IS NOT A PASSING "
                         "COMPARISON, IT IS AN ABSENT ONE. stdout %r stderr %r"
                         % (with_plant.returncode, with_plant.stdout, with_plant.stderr))
        self.assertIn("REFUSED:", with_plant.stderr)
        self.assertIn("A5 ledger entries", with_plant.stderr,
                      "the driver refused without naming WHICH population was empty: %r"
                      % (with_plant.stderr,))
        self.assertIn("left", with_plant.stderr,
                      "the refusal did not name the side it found empty: %r" % (with_plant.stderr,))

        # ---- AND IT REFUSED INSTEAD OF REPORTING, NOT AS WELL AS. A verdict printed beside a
        # refusal is the absent comparison still wearing a passing name.
        for verdict in ("A5 VERDICT", "A6 VERDICT", "LENGTH        :"):
            self.assertNotIn(verdict, with_plant.stdout,
                             "the driver rendered %r before refusing, so a redirected drive would "
                             "capture a partial verdict: %r" % (verdict, with_plant.stdout))

    def test_the_refusal_exit_code_is_a_third_state_and_the_other_two_are_occupied(self):
        """THE SECOND HALF OF R5's EXIT-CODE PAIR. The row above pins the code the driver ACTUALLY
        RETURNS; this row pins the SYMBOL and shows the other two codes are genuinely taken.

        **A CONSTANT SHARED BY THE CHECK AND THE CHECKED IS NOT A CHECK** (`:1793`). `REFUSED_EXIT`
        is read by the driver, and the row above runs that driver as a CHILD PROCESS FROM THIS SAME
        SOURCE — so an assertion naming the symbol compared the constant with itself. Driven against
        the pre-repair source with the constant set to 1, the driver exited 1, MEANING DIVERGENT,
        and the row still read `OK`. The two halves now fail on DIFFERENT mutations: the literal
        above reds when the constant MOVES, and this row reds when the constant and the driver DRIFT
        APART — a driver hard-coded to `sys.exit(2)` with `REFUSED_EXIT` left at 0 satisfies the
        literal and reds here.

        **WHY `DISTINCT FROM 0 AND 1` IS DRIVEN RATHER THAN WRITTEN AS TWO `assertNotEqual` LINES,
        AND THE DIFFERENCE IS THIS DOCUMENT'S WHOLE SUBJECT.** `assertNotEqual(REFUSED_EXIT, 0)`
        standing beside `assertEqual(REFUSED_EXIT, 2)` IS A COROLLARY OF IT: it cannot fail unless
        the line above it has already failed. Two checks that cannot fail, added to the row created
        to remove a check that cannot fail, would be the FIFTH instance of this document's one shape
        rather than the end of it. The claim `2 IS A THIRD STATE` is falsifiable only if `0` AND `1`
        ARE SHOWN OCCUPIED BY THE TWO VERDICTS, so both are OBSERVED FROM DRIVES. A later hand
        moving DIVERGENT onto 2 reds this row while `REFUSED_EXIT == 2` still passes.

        **AND DISTINCTNESS IS THEREFORE NOT WRITTEN AS A FOURTH ASSERTION.** Given the three below
        it could not fail, and this row will not ship the defect it exists to remove. It is a
        CONCLUSION FROM THE THREE, stated here rather than performed as a check that cannot fail.

        NAMED WITHOUT A RED-WORLD NUMBER, DELIBERATELY. `_is_red_world_row` sweeps `test_R<digit>`
        and §4's differential clause then requires a PLANT PRESENT / PLANT REMOVED block. THIS ROW
        CARRIES NO PLANT — it is a pin, not a differential — so it takes the cure `test_S5b…`
        already established in this module: name the row for what it enforces, rather than weaken
        the predicate until the row slips out.
        """
        # ---- THE SYMBOL. Reds when the constant moves, whatever the driver then exits.
        self.assertEqual(REFUSED_EXIT, 2,
                         "the refusal exit code moved. The row above pins the code the driver "
                         "ACTUALLY RETURNS to the literal 2, so this constant and that driver now "
                         "disagree and one of the two is wrong")

        # ---- AND THE VERDICT REGISTER, OBSERVED RATHER THAN ASSUMED. BOTH artifacts keep EVERY
        # population full, so neither drive can reach the refusal path at all: what these two
        # measure is where the two VERDICTS live, and nothing else.
        full = self.artifact()
        differs = self.artifact(ledger_actions=("COMMS-SEND", "COMMS-RECV", "COMMS-SEND"))
        self.assertNotEqual(full["ledger"], differs["ledger"],
                            "the two artifacts are identical, so the DIVERGENT drive below cannot "
                            "diverge and would measure the IDENTICAL path a second time")

        d = tempfile.mkdtemp(prefix="ep30c2-codes-")

        def written(name, doc):
            path = os.path.join(d, name)
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(doc, fh, indent=2)
            return path

        identical = self.drive_compare(written("same-left.json", full),
                                       written("same-right.json", full))
        divergent = self.drive_compare(written("diff-left.json", full),
                                       written("diff-right.json", differs))

        self.assertEqual(identical.returncode, 0,
                         "0 is not the code an IDENTICAL comparison returns, so `REFUSED_EXIT` "
                         "differing from 0 says nothing about the verdict register. "
                         "stdout %r stderr %r" % (identical.stdout, identical.stderr))
        self.assertEqual(divergent.returncode, 1,
                         "1 is not the code a DIVERGENT comparison returns, so `REFUSED_EXIT` "
                         "differing from 1 says nothing about the verdict register. "
                         "stdout %r stderr %r" % (divergent.stdout, divergent.stderr))

    def test_the_returncode_assertions_carry_literals_so_one_constant_cannot_move_both_sides(self):
        """THE GUARD THAT KEEPS THIS REPAIR FROM BEING TIDIED AWAY, per the charter's rule that
        every verification probe lands as a regression test.

        The literal `2` above was established as load-bearing by DRIVING a mutation: with
        `REFUSED_EXIT` set to 1 the pre-repair row read `OK` while the driver exited 1, MEANING
        DIVERGENT. **That mutation was a build-time probe and a probe that does not land is a fact
        about one afternoon.** The literal looks like a magic number, the symbol looks tidier, and
        the tidying would restore the defect WITH EVERY ROW STILL GREEN.

        THE CONTROL IS THE HALF THAT MAKES THIS MEAN ANYTHING, AND IT RUNS FIRST, IN BOTH
        DIRECTIONS. A checker that never reports anything returns `[]` over this module and passes
        while asserting nothing — the defect A1 carries a control for and the one this estate meets
        most often.
        """
        # ---- THE CONTROL, ON SEEDED SOURCE, BOTH WAYS.
        symbol = ("class Seeded:\n"
                  "    def test_seeded_compares_a_returncode_to_a_symbol(self):\n"
                  "        self.assertEqual(proc.returncode, REFUSED_EXIT)\n")
        self.assertEqual(rows_comparing_a_returncode_to_a_symbol(symbol),
                         ["test_seeded_compares_a_returncode_to_a_symbol"],
                         "the checker did not report an assertion comparing a returncode to a "
                         "NAME, so its empty answer over this module says nothing")
        self.assertEqual(
            rows_comparing_a_returncode_to_a_symbol(symbol.replace("REFUSED_EXIT", "2")), [],
            "the checker reported an assertion that DOES carry a literal, so it cannot pass at all")

        # ---- AND THE ASSERTION ITSELF, OVER THIS MODULE'S OWN SOURCE.
        with open(THIS_FILE, encoding="utf-8") as fh:
            offenders = rows_comparing_a_returncode_to_a_symbol(fh.read())
        self.assertEqual(offenders, [],
                         "these rows assert a child process's exit code against a NAME this module "
                         "ALSO hands the driver, so the check and the checked share one constant "
                         "and moving it moves both sides together: %r" % (offenders,))

    def test_R5_every_population_a_verdict_ranges_over_is_refused_when_it_is_empty(self):
        """R5's RULE IS OVER POPULATIONS, NOT OVER THE LEDGER, AND EACH ONE IS DRIVEN EMPTY WITH
        EVERY OTHER POPULATION THAT CAN INDEPENDENTLY BE FULL.

            PLANT PRESENT  : the driver REFUSES and names THAT population — for each of the three,
                             emptied ONE AT A TIME, every other population that CAN independently
                             be full left full. REFUSING IS THIS ROW SUCCEEDING, R3's polarity
            PLANT REMOVED  : the driver ACCEPTS the same artifact with every population full and
                             returns 0

        §4 STATES R5's DRIVE AS ONE INSTANCE — *two artifacts whose LEDGERS are empty*. Writing the
        guard from the instance in front of the author is the named defect that cost this plan two
        cycles at `:1715`, so the other populations were driven rather than reasoned about: a full
        `sent` beside an empty ledger, a full ledger beside an empty `sent`, and a ledger of
        `COMMS-RECV` alone whose cross-world hash line compared `[]` to `[]` and printed SAME while
        both other populations were full.

        **HOW MANY OTHERS STAY FULL IS A FACT OF THE DEPENDENCY STRUCTURE AND NEVER
        THREE-MINUS-ONE.** The COMMS-SEND hashes are derived FROM the ledger, so the first plant
        leaves ONE other full and no fixture can make it two. The sizes are pinned as literals —
        `(0, 2, 0) · (3, 0, 2) · (2, 2, 0)` — by
        `test_R5_the_COMMAND_refuses_all_three_populations_at_the_third_exit_code`, which drives
        these same three plants and asserts each triple before the refusal it is checking.

        HISTORICAL, KEPT VISIBLE (`:1820`): this docstring read *EACH ONE IS DRIVEN EMPTY WITH THE
        OTHERS FULL*, *the other two stay full*, and *ALL THREE ARE INDEPENDENTLY REACHABLE*, all
        three withdrawn with §4's clause of the same shape. This row's verdicts all stand — the
        substance was met — and the withdrawn form is recorded rather than erased because §9 item 8
        makes this block's own words the close's words.

        **A LEDGER-ONLY GUARD WOULD LEAVE TWO OF THE THREE PRINTING GREEN VERDICTS OVER NOTHING** —
        the same defect one population over, which is exactly how this row's subject arrived.
        """
        # ---- THE CONTROL, FIRST: every population full, and the driver returns a verdict.
        #
        # `_compare` PRINTS, so its stdout is captured rather than let out into the suite's own
        # output — a row that writes a green A5 VERDICT into the runner's stream puts a taken-row
        # rendering where a reader scanning for one would find it. CAPTURED AND THEN ASSERTED ON,
        # never merely discarded: the control's job is to show the verdicts WERE rendered, so
        # swallowing them would trade one silent absence for another.
        full = self.artifact()
        rendered = io.StringIO()
        with contextlib.redirect_stdout(rendered):
            code = _compare(*self.write_pair(full))
        self.assertEqual(code, 0,
                         "the driver refused or diverged over an artifact with every population "
                         "full, so its refusal fires on everything and discriminates nothing")
        self.assertIn("A5 VERDICT    : IDENTICAL ENTRY BY ENTRY", rendered.getvalue())
        self.assertIn("A6 VERDICT    : BYTES EXACT IN BOTH WORLDS", rendered.getvalue())

        plants = (
            ("A5 ledger entries",
             self.artifact(ledger_actions=()),
             "the ledger is empty and A5 still rendered a verdict"),
            ("A6 sent messages",
             self.artifact(with_sent=False),
             "`sent` is empty and A6 still rendered BYTES EXACT over nothing"),
            ("A6 COMMS-SEND hashes in the ledger",
             self.artifact(ledger_actions=("COMMS-RECV", "COMMS-RECV")),
             "the ledger holds no COMMS-SEND and the cross-world line still compared [] to []"),
        )
        for population, doc, why in plants:
            left, right = self.write_pair(doc)
            with self.assertRaises(EmptyPopulation, msg=why) as caught:
                _compare(left, right)
            self.assertIn(population, str(caught.exception),
                          "the driver refused but named %r rather than the population that was "
                          "actually empty (%r)" % (str(caught.exception), population))

    def test_R5_the_COMMAND_refuses_all_three_populations_at_the_third_exit_code(self):
        """R5's THREE POPULATIONS AT THE COMMAND LINE, WHERE AN EXIT CODE EXISTS TO BE READ.

            PLANT PRESENT  : for EACH of the three populations, emptied one at a time, the
                             literal `--compare` command REFUSES — exit 2, `REFUSED:` on
                             stderr naming THAT population and the side it found empty, and
                             NOT ONE VERDICT LINE on stdout. REFUSING IS THIS ROW SUCCEEDING,
                             R3's polarity and the opposite of R1's (`:1715`)
            PLANT REMOVED  : the same command over the same artifact with every population
                             full ACCEPTS — exit 0, both verdicts rendered

        WHAT THIS HOLDS THAT THE TWO ROWS ABOVE DO NOT, AND IT IS THE WHOLE OF ITS WARRANT.
        `test_R5_the_driver_REFUSES_two_well_formed_artifacts_whose_ledgers_are_empty` drives
        the COMMAND and reads exit 2 — FOR ONE POPULATION.
        `test_R5_every_population_a_verdict_ranges_over_is_refused_when_it_is_empty` reaches
        all three — IN PROCESS, where `_compare` raises and there is no exit code to read, and
        where nothing captures stdout. **SO THE SECOND AND THIRD POPULATIONS HAD NEVER BEEN
        SHOWN REACHING THE THIRD EXIT STATE, AND NOTHING ANYWHERE ASSERTED THAT THEY RENDER NO
        VERDICT BEFORE REFUSING.** A refusal that fired after the A5 block was printed, or that
        left `__main__` by another path, reds in neither row above and leaves a redirected
        drive holding a partial verdict — which reads as a taken row. §4 requires the refusal
        to fire *before one line of either verdict is rendered*, and that requirement was
        carried for one population out of three.

        **THE `OTHER TWO FULL` CLAIM HOLDS FOR TWO OF THE THREE AND CANNOT HOLD FOR THE
        FIRST.** The COMMS-SEND hashes are derived FROM the ledger, so emptying the ledger
        empties them too, BY CONSTRUCTION and not by an accident of the fixture. §4's *each is
        exhibited empty with the other two full* is unsatisfiable for the ledger population,
        and this row asserts the population sizes it actually produces rather than restating a
        claim the arithmetic forbids. RAISED, not improvised around: the numbers are pinned
        here so the disagreement stays visible if the clause is ever read as satisfied.
        """
        # ---- THE THREE POPULATIONS, WITH THE SIZES THIS FIXTURE ACTUALLY PRODUCES. Written as
        # a table so the `others full` claim is a checked figure and never a sentence.
        #
        #     plant kwargs                              ledger  sent  hashes   others full
        #     ledger_actions=()                              0     2       0             1
        #     with_sent=False                                3     0       2             2
        #     ledger_actions=("COMMS-RECV","COMMS-RECV")     2     2       0             2
        plants = (
            ("A5 ledger entries", dict(ledger_actions=()), (0, 2, 0)),
            ("A6 sent messages", dict(with_sent=False), (3, 0, 2)),
            ("A6 COMMS-SEND hashes in the ledger",
             dict(ledger_actions=("COMMS-RECV", "COMMS-RECV")), (2, 2, 0)),
        )

        def sizes(doc):
            return (len(doc["ledger"]), len(doc["sent"]),
                    len([e for e in doc["ledger"] if e["action"] == "COMMS-SEND"]))

        # ---- PLANT REMOVED, ASSERTED FIRST (§4, S5b). A vacuous red world fails LOUDLY here,
        # and this arm is the one that proves the command accepts anything at all.
        full = self.artifact()
        self.assertTrue(all(n > 0 for n in sizes(full)),
                        "the plant-removed arm has an empty population of its own, so the "
                        "refusals below cannot be attributed to the plants: %r" % (sizes(full),))
        without = self.drive_compare(*self.write_pair(full))
        self.assertEqual(without.returncode, 0,
                         "R5's PLANT-REMOVED ARM DID NOT PASS: the command refused or diverged "
                         "over an artifact with every population full, so its refusal fires on "
                         "everything and this row is not measuring the plants (S5b). "
                         "stdout %r stderr %r" % (without.stdout, without.stderr))
        self.assertIn("A5 VERDICT    : IDENTICAL ENTRY BY ENTRY", without.stdout)
        self.assertIn("A6 VERDICT    : BYTES EXACT IN BOTH WORLDS", without.stdout)

        # ---- PLANT PRESENT, ONE POPULATION AT A TIME.
        for population, kwargs, expected_sizes in plants:
            doc = self.artifact(**kwargs)
            self.assertEqual(sizes(doc), expected_sizes,
                             "the %r plant did not produce the population sizes this row pins, "
                             "so the `others full` figure it reports is not the one it drove"
                             % (population,))
            with_plant = self.drive_compare(*self.write_pair(doc))

            # THE LITERAL `2`, NEVER `REFUSED_EXIT`. The child process is this same source
            # file, so a symbol here would be the constant compared with itself (`:1793`), and
            # `rows_comparing_a_returncode_to_a_symbol` reds this module if it is ever tidied.
            self.assertEqual(with_plant.returncode, 2,
                             "the command did not refuse an artifact whose %r population is "
                             "EMPTY — it returned %d. A COMPARISON OF NOTHING WITH NOTHING IS "
                             "NOT A PASSING COMPARISON, IT IS AN ABSENT ONE. stdout %r stderr %r"
                             % (population, with_plant.returncode,
                                with_plant.stdout, with_plant.stderr))
            self.assertIn("REFUSED:", with_plant.stderr)
            self.assertIn(population, with_plant.stderr,
                          "the command refused but named a population other than the one that "
                          "was actually empty (%r): %r" % (population, with_plant.stderr))
            self.assertIn("left", with_plant.stderr,
                          "the refusal did not name the side it found empty: %r"
                          % (with_plant.stderr,))

            # ---- AND IT REFUSED INSTEAD OF REPORTING, NOT AS WELL AS — for EVERY population,
            # which is the half no row above carried for the second and third.
            for verdict in ("A5 VERDICT", "A6 VERDICT", "LENGTH        :"):
                self.assertNotIn(verdict, with_plant.stdout,
                                 "the command rendered %r before refusing on %r, so a "
                                 "redirected drive would capture a partial verdict: %r"
                                 % (verdict, population, with_plant.stdout))

    def test_R5_the_comparison_both_layers_call_REFUSES_an_empty_population(self):
        """R5 AT THE ROOT. §4's R5 bracket names `compare_entrywise` — the function the acceptance
        rows AND the red worlds both call — and it had the same defect in its own currency:
        `compare_entrywise([], [])` returned `[]`, and an empty return MEANS IDENTICAL.

            PLANT PRESENT  : the comparison REFUSES an empty argument, on either side or both, and
                             names the side — REFUSING IS THIS ROW SUCCEEDING
            PLANT REMOVED  : the comparison over two NON-EMPTY ledgers returns its verdict
                             normally, and an identical pair still returns `[]` meaning IDENTICAL

        **EMPTY INPUT AND EMPTY OUTPUT ARE OPPOSITE FACTS THAT ONE WORD CARRIES.** The control half
        below is what keeps the repair from having quietly broken the contract every A5 row stands
        on: `[]` returned still means the two ledgers agree.
        """
        entry = {"action": "COMMS-SEND", "payload": {"channel": CHANNEL, "message_hash": "sha256:x"}}

        # ---- PLANT REMOVED, ASSERTED FIRST. The verdict contract is unchanged.
        self.assertEqual(compare_entrywise([entry], [dict(entry)]), [],
                         "an identical non-empty pair no longer returns [] — the repair changed "
                         "what a verdict means, not merely when one is refused")
        self.assertEqual(diverge_entrywise([entry], [dict(entry)]), [])
        self.assertNotEqual(compare_entrywise([entry], [{"action": "COMMS-RECV", "payload": {}}]),
                            [], "the comparison stopped discriminating a real divergence")

        # ---- PLANT PRESENT: an empty argument on either side, and both.
        for left, right, side in (([], [entry], "left"), ([entry], [], "right"), ([], [], "left")):
            for fn in (compare_entrywise, diverge_entrywise):
                with self.assertRaises(EmptyPopulation,
                                       msg="%s compared %d against %d entries without refusing"
                                           % (fn.__name__, len(left), len(right))) as caught:
                    fn(list(left), list(right))
                self.assertIn(side, str(caught.exception),
                              "%s refused but named the wrong side: %r"
                              % (fn.__name__, str(caught.exception)))


class RedWorldDirectionCase(unittest.TestCase):
    """§4's DIFFERENTIAL CLAUSE HELD AS A PROPERTY OF THE ROWS, not as a habit of the author.

    §4 requires the row's verdict to MOVE when its plant is removed, and requires THE ROW TO STATE
    WHICH WAY FOR ITSELF — because the direction is a property of the individual row and never of
    the clause. R3's plant makes the calibration REFUSE, which is R3 SUCCEEDING, the opposite of
    R1's and R2's polarity; a clause that carried a direction described half its population
    backwards for two cycles (`:1715`).

    A REQUIREMENT ON DOCSTRINGS THAT NOTHING CHECKS IS A CONVENTION, AND A CONVENTION IS WHAT THIS
    ESTATE ALREADY KNOWS DOES NOT HOLD. This row makes it mechanical: a red world landing later
    without its two sides stated reds here, by name, the moment it is written.
    """

    @classmethod
    def setUpClass(cls):
        with open(THIS_FILE, encoding="utf-8") as fh:
            cls.source = fh.read()

    def test_S5b_every_red_world_row_states_which_way_its_verdict_moves(self):
        """NAMED FOR THE STOP IT SERVES AND NOT FOR THE ROWS IT READS. A `test_R…` name would put
        this row inside its own population — it carries no plant, so it would red itself — and the
        cure is to name it for S5b, which is what it enforces, rather than to weaken the predicate
        until the row slips out."""
        # ---- THE CONTROL, FIRST, AND IT IS THE HALF THAT MAKES THE ASSERTION MEAN ANYTHING. A
        # checker that never reports a missing block returns [] over any source and passes over
        # this file while asserting nothing. Seeded with a red-world row that has no block, it must
        # name exactly that row.
        seeded = ("class Seeded:\n"
                  "    def test_R0_seeded_with_no_direction_block(self):\n"
                  "        '''a red world that never says which way its verdict moves'''\n")
        self.assertEqual(rows_missing_a_direction_block(seeded),
                         ["test_R0_seeded_with_no_direction_block"],
                         "the checker did not report a row whose block is missing, so its empty "
                         "answer over this module says nothing")
        self.assertEqual(rows_missing_a_direction_block(
            seeded.replace("moves'''", "moves\n\n        PLANT PRESENT : x\n        PLANT REMOVED : y\n        '''")),
            [], "the checker reported a row whose block IS present, so it cannot pass at all")

        # ---- THE POPULATION IS NOT EMPTY, AND IT COVERS EVERY RED WORLD §4 NAMES. A file whose
        # rows had all been renamed would give the checker nothing to walk and it would read green.
        #
        # THIS LIST IS LITERAL AND THAT IS A KNOWN COST, PAID DELIBERATELY. `:1751` ruled a literal
        # enumeration carrying a general rule a defect, and removed one from §9's close format for
        # exactly that reason — a row added after the list sits outside the list while inside the
        # rule. THE JOB HERE IS DIFFERENT: this list is the row's ANCHOR AGAINST VACUITY, and an
        # anchor derived from the very rows it is meant to vouch for would vouch for nothing. So it
        # stays literal, it is EXTERNAL to the module's rows on purpose, and it is amended by hand
        # whenever §4 gains a red world — R5 arrived at `:1750` and this line moved with it.
        found = red_world_rows(self.source)
        self.assertNotEqual(found, [], "this module declares no red-world rows at all")
        for red_world in ("test_R1", "test_R2", "test_R3", "test_R4", "test_R5"):
            self.assertTrue(any(name.startswith(red_world) for name in found),
                            "%s has no row in this module, and §4 names five red worlds: %r"
                            % (red_world, found))

        # ---- AND THE ASSERTION ITSELF.
        missing = rows_missing_a_direction_block(self.source)
        self.assertEqual(missing, [],
                         "these red-world rows do not state which way their verdict moves, so §4's "
                         "differential is carried by nothing: %r" % (missing,))


class DocMapCase(unittest.TestCase):
    """A8's AMENDED assertion, as a regression row rather than a one-time reading.

    THE ROW A8 NOW ASKS FOR: *no `.md` this unit touched is missing from the map*. The row it USED
    to ask for — that `tests/test_ep30_c2.py` appears in DEFECT 1 and then does not — CANNOT OCCUR:
    `inventory.py::walk` filters to `.md` AT SOURCE, so a `.py` file never enters its population and
    the predicted transition was a check that could not fail (ruled `:1676`, found by this unit's
    first builder). What replaces it is a claim that CAN be false, and this row is where it is held.

    THE TOUCHED SET IS THIS UNIT'S OWN MANIFEST, frozen deliberately: `DOC-MAP_v3.md` is fence and
    stays byte-unmoved, and the two ledger files are the standing duty every unit writes. Deriving
    the set from the tree would make the row a fact about the tree instead of about this unit.
    """

    #: THE `.md` PATHS THIS UNIT TOUCHES — fence member first, then the standing ledger duty.
    TOUCHED = (
        "DOC-MAP_v3.md",
        "planning/build/BUILD-PROGRESS_v3.md",
        "planning/build/DISPATCH-LEDGER.md",
    )

    @classmethod
    def setUpClass(cls):
        # RESOLVED AGAINST THIS FILE, NEVER AGAINST cwd. A row whose answer depends on where the
        # runner was invoked reds for a reason that is not its subject.
        root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
        with open(os.path.join(root, "DOC-MAP_v3.md"), encoding="utf-8") as fh:
            cls.docmap = fh.read()

    def test_A8_no_md_this_unit_touched_is_missing_from_the_map(self):
        for path in self.TOUCHED:
            self.assertIn(path, self.docmap,
                          "%s is a .md this unit touched and the map does not name it" % path)

    def test_A8_the_map_lookup_can_report_an_absence(self):
        """THE CONTROL, AND IT IS THE HALF THAT MAKES THE ROW ABOVE MEAN ANYTHING.

        `DOC-MAP_v3.md` is fifty thousand bytes of paths. A substring lookup against it will say
        `present` to a great many strings, so a row built only from the positive direction is a
        check that cannot fail — this estate's most recurring defect, and the one A1/R4 already pay
        a whole red world to exclude for `grep`. The same discipline is owed here.

        TWO DIRECTIONS OF ABSENCE, because they fail differently:

        1.  A COINED PATH — assembled at runtime and never written whole in any file, so this row
            cannot find itself the way R4's first drive did. Proves the lookup discriminates at all.
        2.  A NEAR MISS of a path that IS mapped — `_v4` beside a mapped `_v3`. Proves the lookup is
            not matching loosely, which a coined token alone would never catch.
        """
        coined = "zzq_coined_" + "path_no_map_holds.md"
        self.assertNotIn(coined, self.docmap,
                         "a coined path was found in the map, so the lookup cannot report an "
                         "absence and the row above asserts nothing")
        for mapped in self.TOUCHED:
            near_miss = mapped.replace("_v3.md", "_v4.md")
            if near_miss == mapped:
                continue
            self.assertNotIn(near_miss, self.docmap,
                             "%r was found, so the lookup is matching loosely and 'present' is not "
                             "evidence that the exact path is mapped" % near_miss)


def _emit():
    """A3/A4's driver mode: derive `message_ledger` for the measured channel and print it whole.

    The width is whatever `commit._calibration()` read from the ENVIRONMENT — this mode exists so
    the two arms exercise `GOVOS_COMMIT_WIDTH` end to end as a real environment fact, and it prints
    `width_from_run` and `largest_batch` READ OFF THE COMMITTER so the close can state the width the
    arm ACTUALLY ran at rather than the width the command asked for.
    """
    run = drive(width=None)
    print(json.dumps({
        "driver": "tests/test_ep30_c2.py --emit-ledger",
        "env_GOVOS_COMMIT_WIDTH": os.environ.get("GOVOS_COMMIT_WIDTH", "<unset>"),
        "run_facts": run.facts(),
        "sent": run.sent,
        "ledger": run.ledger,
    }, indent=2, default=str))


def _compare(path_a, path_b):
    """A5/A6 OVER THE EMITTED ARTIFACTS THEMSELVES, not only over in-process arms.

    The suite's A5 row compares EVERY field bar a derived exclusion set; this compares the clause
    :1547 states in its own words — same length, same order, same action per entry, same payload per
    entry — over the two files A3 and A4 actually produced. Both are worth having: the in-process
    row is stricter, and this one is checkable by a second hand against artifacts on disk.

    A6 IS RECOMPUTED HERE FROM THE ARTIFACT ALONE. `message_hash` is `sha256:` over the sent bytes,
    so hashing the recorded message independently and matching the ledger's reference proves the
    ledger names EXACTLY those bytes — a byte-exactness proof that travels with the evidence and
    needs no surviving blob store.
    """
    import hashlib
    # READ UNDER `with`, AND THE CHANGE IS THIS ROW'S OWN DOING. These two lines were
    # `json.load(open(...))` and leaked a file handle each. Nothing had ever noticed because NO ROW
    # HAD EVER CALLED THIS FUNCTION IN PROCESS — it ran only as a command, where interpreter exit
    # collected the handles. R5's in-process row is the first caller, and it turned a silent leak
    # into SIXTEEN `ResourceWarning` lines in the suite's own output: zero before this unit's edit,
    # sixteen after, both counted at the build hand. A row that adds noise to the instrument it is
    # repairing has repaired half of something.
    with open(path_a, encoding="utf-8") as fh:
        a = json.load(fh)
    with open(path_b, encoding="utf-8") as fh:
        b = json.load(fh)

    # ---- R5. EVERY POPULATION A VERDICT RANGES OVER IS REFUSED IF IT IS EMPTY, **BEFORE ONE LINE
    # OF EITHER VERDICT IS RENDERED**. Ordering first is the same discipline the NON-VACUITY rows
    # and R1's plant-removed control already hold: a driver that printed half an A5 and then refused
    # would leave a redirected drive holding a partial verdict, which reads as a taken row.
    #
    # THIS FUNCTION DOES NOT CALL `compare_entrywise`, SO IT DOES NOT INHERIT THAT GUARD. It carries
    # its own comparison inline — two implementations of one clause, which predates this row and is
    # not this row's to merge. Naming the fact here is cheaper than a reader deducing it from a
    # refusal that fires in the suite and not at the command line.
    send_hashes = [[e["payload"].get("message_hash") for e in doc["ledger"]
                    if e["action"] == "COMMS-SEND"] for doc in (a, b)]
    for side, doc, hashes in (("left", a, send_hashes[0]), ("right", b, send_hashes[1])):
        refuse_empty_population("A5 ledger entries", side, doc["ledger"])
        refuse_empty_population("A6 sent messages", side, doc["sent"])
        refuse_empty_population("A6 COMMS-SEND hashes in the ledger", side, hashes)

    out = []
    out.append("A5 — ENTRY-BY-ENTRY COMPARISON OF THE TWO EMITTED LEDGERS")
    out.append("  left  : %s   width_from_run=%s largest_batch=%s"
               % (path_a, a["run_facts"]["width_from_run"], a["run_facts"]["largest_batch"]))
    out.append("  right : %s   width_from_run=%s largest_batch=%s"
               % (path_b, b["run_facts"]["width_from_run"], b["run_facts"]["largest_batch"]))
    la, lb = a["ledger"], b["ledger"]
    out.append("  LENGTH        : left %d, right %d  -> %s"
               % (len(la), len(lb), "SAME" if len(la) == len(lb) else "DIFFER"))
    same = len(la) == len(lb)
    for i, (ea, eb) in enumerate(zip(la, lb)):
        ok_a = ea["action"] == eb["action"]
        ok_p = ea["payload"] == eb["payload"]
        same = same and ok_a and ok_p
        out.append("  ENTRY %d       : action %s (%s) | payload %s"
                   % (i, ea["action"], "SAME" if ok_a else "DIFFER",
                      "SAME" if ok_p else "DIFFER"))
    out.append("  A5 VERDICT    : %s" % ("IDENTICAL ENTRY BY ENTRY" if same else "DIVERGENT"))
    out.append("")
    out.append("A6 — PAYLOAD BYTES, RECOMPUTED INDEPENDENTLY FROM THE SENT MESSAGE")
    bytes_ok = True
    for side, doc in (("left", a), ("right", b)):
        for s in doc["sent"]:
            recomputed = "sha256:" + hashlib.sha256(s["message"].encode()).hexdigest()
            hit = recomputed == s["message_hash"]
            bytes_ok = bytes_ok and hit
            out.append("  %-5s %-40r -> %s  %s"
                       % (side, s["message"], s["message_hash"], "BYTE-EXACT" if hit else "DIFFER"))
    # COMPUTED ONCE, ABOVE, WHERE IT IS REFUSED IF EMPTY. It used to be derived here and nowhere
    # else; hoisting it moves NO OUTPUT — the rendered lines below are byte-for-byte what they were,
    # so every landed A5-COMPARISON artifact remains reproducible in form.
    cross = send_hashes[0] == send_hashes[1]
    bytes_ok = bytes_ok and cross
    out.append("  BOTH WORLDS NAME THE SAME BYTES PER SEND : %s" % ("SAME" if cross else "DIFFER"))
    out.append("  A6 VERDICT    : %s" % ("BYTES EXACT IN BOTH WORLDS" if bytes_ok else "DIVERGENT"))
    print("\n".join(out))
    return 0 if (same and bytes_ok) else 1


if __name__ == "__main__":
    if "--emit-ledger" in sys.argv:
        _emit()
    elif "--compare" in sys.argv:
        i = sys.argv.index("--compare")
        try:
            sys.exit(_compare(sys.argv[i + 1], sys.argv[i + 2]))
        except EmptyPopulation as refusal:
            # R5. THE REFUSAL IS A THIRD STATE AND IT GETS A THIRD CODE — never 0, which would say
            # IDENTICAL, and never 1, which would say DIVERGENT and make a comparison that never
            # happened indistinguishable from one that failed.
            #
            # ON stderr, DELIBERATELY. A drive redirected to an evidence path must capture NOTHING
            # rather than a reason wearing a verdict's place: the row path stays empty, the refusal
            # is on the operator's terminal, and no artifact can be mistaken for a taken row.
            print("REFUSED: %s" % refusal, file=sys.stderr)
            sys.exit(REFUSED_EXIT)
    else:
        unittest.main()
