# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""EP-28U W3 — `tools/board`'s own can-fail proofs. Every world is EXHIBITED, not described.

READ THE FIRST LAW BEFORE THE ROWS, because it is the one a later editor must never relax:
**the tool is a VIEW. It READS `planning/build/BOARD-EVENTS.log` and WRITES NOTHING.** A
board PARSED from the prose record needs judgment per entry, and three seats' parsers are
three boards — the census defect rebuilt at the planning layer. `T-BOARD-WRITES-NOTHING`
asserts that STRUCTURALLY, by AST, with a planted writer proving the guard can fail.

  T-BOARD-FOLDS-EVERY-VERB      one planted event of EVERY verb in the CLOSED set, folded
                                and asserted. RED WORLD: a verb dropped from the fold, or
                                a verb added to the set with no planted case.
  T-BOARD-REFUSES-MALFORMED     a malformed line REFUSES LOUDLY AND NAMES ITS LINE NUMBER,
                                and NOTHING is folded. RED WORLD: a skipped line — which
                                is a board that has quietly lost an item.
  T-BOARD-NEAR-MISS             §A64 — a verb spelled NEARLY right REFUSES, and a date
                                field shifted ONE COLUMN in either direction REFUSES. A
                                pattern that has never met a near-miss has never been
                                tested.
  T-BOARD-UNKNOWN-ITEM          a name the fold has never seen reports UNKNOWN-ITEM, never
                                not-started. Seed completeness is LOAD-BEARING and no
                                unknown name borrows that guarantee.
  T-BOARD-OWED-AND-HELD-PAIR    an item carrying both is SHOWN AS A PAIR, never picked
                                between. RED WORLD: either half suppressed.
  T-BOARD-CORRECTED             a CORRECTED voids its target; an ambiguous reference is
                                REPORTED ambiguous; an unresolvable one is REPORTED
                                unresolved. RED WORLD: a silent pick.
  T-BOARD-STALE-HEADER          `--stale` is an INVITATION, says so in its own header, and
                                that header names the caps a WRITER of events needs — the
                                second-pass criterion applied at birth.
  T-BOARD-CONTROL               the positive control finds KNOWN-PRESENT planted cases of
                                every shape, and the tool prints UNINTERPRETABLE rather
                                than a number when it fails. Not decoration: every finding
                                here is an ABSENCE, so a broken fold returns exactly the
                                clean answer a healthy one returns.
  T-BOARD-WRITES-NOTHING        no file-writing construct anywhere in the module, by AST.
  T-BOARD-HEADER-IS-NOT-LOAD-BEARING
                                a LYING header and a TRUE header over identical bodies
                                produce IDENTICAL boards. The live file's header claimed
                                the seed was "(not yet written)" over a seed written
                                twelve lines below it; a fold that read the header would
                                have refused a healthy file.
  T-BOARD-NO-LIVE-RECORD        [EP-28W W2] NO ROW IN THIS FILE REACHES THE LIVE BOARD OF
                                RECORD, by name OR by default. RED WORLD: a planted
                                `board.EVENTS`, a planted live path, a planted
                                `board.main(['--board'])` with no `--events`.
  T-BOARD-BAD-ARGUMENT          [EP-28W W3] a `--stale` argument that is not a date
                                REFUSES with a named reason and a DECLARED code, distinct
                                from every other code AND from the interpreter's 1.
  T-BOARD-AMBIGUOUS-ENDING      [EP-28W W4] with two-plus open states, an ending naming
                                none of them is reported AMBIGUOUS and closes NOTHING.
                                Near-misses: a named ending closes exactly one; ONE open
                                state closes exactly as before.
  T-BOARD-DISCRIMINATOR         [EP-28Y W2/W3] `<date+verb>` is an ALIAS and aliases
                                collide. A reference may carry `digest:<hex-prefix>` of the
                                event line's CONTENT: REQUIRED where the alias names two or
                                more, VALIDATED ALWAYS when present, twice-matched refuses
                                whole. `--ep` prints the prefix so it is COPIED, and a
                                round-trip row lifts one out of the printed text. RED
                                WORLDS: a first-match resolver (caught only by folding one
                                log twice, once per colliding digest) and a digest IGNORED
                                at count 1 (the narrowing pre-flight caught in the plan).
  T-DEFECT6-BOARD-FOLDS         [EP-28W W2] the fold assertion in its new home — a defect
                                line in `tools/docmap/inventory.py`, with its control and
                                its owned unique scratch.

WHY NO ROW HERE READS THE LIVE RECORD AT ALL [EP-28W W2, and it replaces the weaker rule
this file shipped at EP-28U]. `BOARD-EVENTS.log` is DATA. A suite asserts about CODE, so a
lawful edit to the record must never report as a code failure. EP-28U's file shipped four
rows that read it BY NAME (`TBoardLiveLogFolds`, removed here) and two that read it BY
DEFAULT through `board.main()` with no `--events` — and the record shows both halves: the
red arm of 2026-08-08 was "two failures and four errors", which is exactly six rows. The
assertion did not disappear; it moved to `inventory.py`'s DEFECT 6, which runs at every
invocation and is unaffected by lawful edits.

AND NO LINE NUMBER OF ANY LIVE FILE IS PINNED ANYWHERE HERE. Line numbers are asserted
against FIXTURES built in this file by value, or against the STATIC COMMITTED fixture
`tests/board-events-fixture.events`, which no seat edits as routine.
"""
import ast
import importlib.util
import io
import os
import re
import shutil
import tempfile
import unittest
import unittest.mock

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_MODULE_PATH = os.path.join(_ROOT, 'tools', 'board', 'board.py')
_INVENTORY_PATH = os.path.join(_ROOT, 'tools', 'docmap', 'inventory.py')

#: The STATIC COMMITTED fixture. Rows that need a real file path use this one; nothing
#: here ever points at the live record, and nothing here writes into the repository tree.
_FIXTURE_EVENTS = os.path.join(_HERE, 'board-events-fixture.events')

#: [EP-28X W3] A second STATIC COMMITTED fixture, carrying a `DISAMBIGUATED` whose
#: reference resolves to nothing. It exists so one row can drive a FOLD-TIME refusal out
#: through `main()` — every other red world here reaches `fold()` directly, and the path a
#: CALLER meets is the one that must not be a traceback.
_FIXTURE_DISAMBIG_BAD = os.path.join(_HERE, 'board-events-disambig-unresolvable.events')

# LOADED BY PATH, and `sys.path` is deliberately NOT touched. unittest runs the whole
# estate in one process, so a row that prepends a directory to the import path changes
# what every other module resolves — the battery owning something on its subject, and the
# shape that put nine phantom rows in a suite count at EP-28E.
_SPEC = importlib.util.spec_from_file_location('govos_board_tool', _MODULE_PATH)
board = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(board)


def log(*body):
    """Build a fixture log. Returns the LINE LIST, so nothing here writes a file."""
    return ['# fixture'] + list(body)


SEED_OPEN = '# ============ SEED BLOCK ============'
SEED_SHUT = '# ========== END SEED BLOCK =========='


def minimal(*after_seed):
    return log(SEED_OPEN,
               'EVT | 2026-02-01 | ITEM-A | AUTHORED | seat | seeded',
               SEED_SHUT,
               *after_seed)


class TBoardFoldsEveryVerb(unittest.TestCase):
    """T-BOARD-FOLDS-EVERY-VERB — one planted event of every verb, folded and asserted."""

    def test_every_bare_verb_folds_to_itself(self):
        """DOCUMENTED FLIP [EP-28X W2]. This row iterated `BARE_VERBS` whole from EP-28U
        and required each to become the item's STATE. `NOTED` is a bare-FORM verb and is
        NOT a state-bearing one — it is RECORD-PLANE, so it folds into history and leaves
        the state where it was. The row therefore splits rather than being weakened: the
        state-bearing members still fold to themselves, and the record-plane member has
        its own row asserting the opposite, which is a stronger pair than the original."""
        for verb in board.BARE_VERBS:
            if verb in board.HISTORY_ONLY_KINDS:
                continue
            lines = minimal('EVT | 2026-03-01 | ITEM-A | %s | seat |' % verb)
            events, _ = board.read_event_lines(lines, '<fixture>')
            got = board.fold(events)
            self.assertEqual(got['ITEM-A'].state.kind, verb,
                             'verb %r did not fold to itself' % verb)

    def test_the_split_of_BARE_VERBS_is_exhaustive_and_neither_half_is_empty(self):
        """The skip above is a CEILING, not a hole: both halves are named and non-empty,
        so a verb quietly moved into the record plane cannot vanish from the row above
        without this one saying so.

        DOCUMENTED FLIP [EP-30-R3]. The record-plane half read `['NOTED']` alone until
        2026-08-16. `BOARD-EVENTS.log:969` extended `BOARD-GRAMMAR.md` §1 by ONE —
        `COUNTERSIGNED`, HISTORY-ONLY, on the ground that a standing lifecycle act used
        routinely is a verb wearing `NOTED`'s clothes — and EP-30-R2 landed it in the
        tool, so this half now names TWO. THE OTHER HALF DELIBERATELY DOES NOT MOVE:
        `len(state_bearing)` STAYS 9, because a countersign is a SIGNATURE and not a
        state change. A 10 would mean the verb had been armed state-bearing, and the
        fold's ending branch would then let a countersign END A PENDING — an item
        silently losing its open state, which is worse than this suite staying red. The
        two assertions sit ADJACENT so that half is asserted rather than assumed."""
        record_plane = [v for v in board.BARE_VERBS if v in board.HISTORY_ONLY_KINDS]
        state_bearing = [v for v in board.BARE_VERBS
                         if v not in board.HISTORY_ONLY_KINDS]
        self.assertEqual(record_plane, ['NOTED', 'COUNTERSIGNED'])
        self.assertEqual(len(state_bearing), 9)
        self.assertEqual(len(record_plane) + len(state_bearing), len(board.BARE_VERBS))

    def test_the_record_plane_bare_verb_does_NOT_fold_to_itself_as_a_state(self):
        lines = minimal('EVT | 2026-03-01 | ITEM-A | RULED | seat |',
                        'EVT | 2026-03-02 | ITEM-A | NOTED | seat | a plain addition')
        got = board.fold(board.read_event_lines(lines, '<fixture>')[0])
        self.assertEqual(got['ITEM-A'].state.kind, 'RULED')
        self.assertEqual(got['ITEM-A'].history[-1].kind, 'NOTED')

    def test_every_parameterised_verb_folds_with_its_parts(self):
        lines = minimal(
            'EVT | 2026-03-01 | ITEM-A | HELD(on: a world) | seat |',
            'EVT | 2026-03-01 | ITEM-B | OWED(by: mtr, act: an unperformed thing) | s |',
            'EVT | 2026-03-01 | ITEM-C | AUTHORED | seat |',
            'EVT | 2026-03-02 | ITEM-C | CORRECTED(supersedes: 2026-03-01 AUTHORED) | s |',
        )
        got = board.fold(board.read_event_lines(lines, '<fixture>')[0])
        self.assertEqual(got['ITEM-A'].pendings['HELD'].trigger, 'a world')
        self.assertEqual(got['ITEM-B'].pendings['OWED'].owed_by, 'mtr')
        self.assertEqual(got['ITEM-B'].pendings['OWED'].act, 'an unperformed thing')
        self.assertEqual(got['ITEM-C'].state.supersedes, '2026-03-01 AUTHORED')

    def test_the_closed_set_has_no_member_this_row_does_not_exercise(self):
        """RED WORLD: a verb added to the set with nothing planting a case for it.

        DOCUMENTED FLIP [EP-28X W2/W3]. THIS ROW ASSERTED TWELVE from EP-28U until
        2026-08-09. `BOARD-GRAMMAR.md` §1's sizing ruling of that date extends the set by
        THREE — `NOTED`, `DISAMBIGUATED(ending, ended)`, `SEATED(kind: ...)` — on the
        ground that the set was COMPLETE IN ITS PLANE (item lifecycle) and the estate
        stretched it to a second plane: acts about the RECORD ITSELF. The number is
        asserted as a POPULATION rather than spot-checked, because a seventeenth member
        arriving without a planted case is exactly what this row exists to stop.

        DOCUMENTED FLIP [EP-30-R3]. IT THEN ASSERTED FIFTEEN until 2026-08-16, and when
        the set moved it went RED rather than passing quietly — which is the whole reason
        this unit exists. `BOARD-EVENTS.log:969` extended §1 by ONE, `COUNTERSIGNED`,
        HISTORY-ONLY; EP-30-R2 landed it in `BARE_VERBS` and `HISTORY_ONLY_KINDS`; and
        this edit is the handshake that ruling asked for. THE ROW WAS NEVER BROKEN — its
        own message reads "the closed verb set moved; §1 was amended", and §1 had been
        amended. The count STAYS A POPULATION and is not relaxed into a membership check
        on the new member: such a check would have stayed green through exactly the
        widening this row exists to catch."""
        exercised = (set(board.BARE_VERBS) | set(board.PENDING_KINDS)
                     | {'CORRECTED', 'SEATED', 'DISAMBIGUATED'})
        self.assertEqual(exercised, set(board._CONTROL_VERB_KINDS))
        self.assertEqual(len(exercised), 16, 'the closed verb set moved; §1 was amended')

    def test_the_four_record_plane_verbs_are_each_in_the_set_by_name(self):
        """Named individually as well as counted: a count of 16 could be reached by any
        four additions, and it is these four that were ruled.

        DOCUMENTED FLIP [EP-30-R3]. THE ROW'S OWN NAME MOVED WITH THE NUMBER IT CARRIES:
        it read `..._three_record_plane_verbs_...` while asserting four, and a name that
        lies to the next reader costs more to explain later than to rename now. The
        precedent is EP-29 W3a3 — two row names moved, and only the two whose own words
        carried the falsified number. `COUNTERSIGNED` was ruled into §1 at
        `BOARD-EVENTS.log:969` and landed by EP-30-R2. The literal is kept a FULL SORTED
        SET rather than an `assertIn` on the new member, because a membership check
        passes on any `HISTORY_ONLY_KINDS` that merely CONTAINS it — including one that
        had quietly gained a fifth."""
        self.assertIn('NOTED', board.BARE_VERBS)
        self.assertEqual(sorted(board.HISTORY_ONLY_KINDS),
                         ['COUNTERSIGNED', 'DISAMBIGUATED', 'NOTED', 'SEATED'])
        self.assertEqual(board.SEATED_KINDS, ('continuation', 'substitution'))

    def test_the_record_plane_verbs_fold_with_their_parts(self):
        lines = minimal(
            'EVT | 2026-03-01 | ITEM-A | NOTED | seat | the fact rides in the clause',
            'EVT | 2026-03-01 | ITEM-B | SEATED(kind: continuation) | seat |',
            'EVT | 2026-03-01 | ITEM-C | SEATED(kind: substitution) | seat |',
        )
        got = board.fold(board.read_event_lines(lines, '<fixture>')[0])
        self.assertEqual(got['ITEM-A'].history[-1].kind, 'NOTED')
        self.assertEqual(got['ITEM-A'].history[-1].clause,
                         'the fact rides in the clause')
        self.assertEqual(got['ITEM-B'].history[-1].seated_kind, 'continuation')
        self.assertEqual(got['ITEM-C'].history[-1].seated_kind, 'substitution')


class TBoardRefusesMalformed(unittest.TestCase):
    """T-BOARD-REFUSES-MALFORMED — refuses loudly, names the line, folds nothing."""

    def test_a_malformed_line_names_its_own_line_number(self):
        lines = minimal(
            'EVT | 2026-03-01 | ITEM-A | CLOSED | seat |',
            'this line is not an event at all',
        )
        with self.assertRaises(board.BoardRefusal) as caught:
            board.read_event_lines(lines, '<fixture>')
        self.assertEqual(caught.exception.lineno, 6)

    def test_the_line_number_is_the_line_that_is_wrong_and_not_a_running_count(self):
        """A near-miss on the refusal itself: comments and blanks must not shift it."""
        lines = ['# fixture', '', '# a comment', SEED_OPEN,
                 'EVT | 2026-02-01 | ITEM-A | AUTHORED | seat |', SEED_SHUT,
                 '', '# another comment', 'EVT | 2026-03-01 | ITEM-A | NOPE | seat |']
        with self.assertRaises(board.BoardRefusal) as caught:
            board.read_event_lines(lines, '<fixture>')
        self.assertEqual(caught.exception.lineno, 9)

    def test_nothing_is_folded_when_any_line_refuses(self):
        lines = minimal('EVT | 2026-03-01 | ITEM-A | CLOSED | seat |',
                        'EVT | 2026-03-01 | ITEM-B | NOT-A-VERB | seat |')
        with self.assertRaises(board.BoardRefusal):
            board.read_event_lines(lines, '<fixture>')

    def test_a_missing_seed_block_refuses_because_the_guarantee_has_no_ground(self):
        with self.assertRaises(board.BoardRefusal) as caught:
            board.read_event_lines(log('EVT | 2026-03-01 | A | CLOSED | s |'), '<f>')
        self.assertIn('SEED BLOCK', caught.exception.reason)

    def test_a_second_seed_marker_refuses(self):
        lines = minimal() + [SEED_OPEN, SEED_SHUT]
        with self.assertRaises(board.BoardRefusal):
            board.read_event_lines(lines, '<fixture>')

    def test_the_refusal_reaches_the_command_line_and_prints_the_line_number(self):
        out = io.StringIO()
        path = os.path.join(_HERE, 'no-such-events-file-for-ep28u.log')
        with unittest.mock.patch('sys.stdout', out):
            rc = board.main(['--events', path, '--board'])
        self.assertEqual(rc, 2)
        self.assertIn('REFUSED', out.getvalue())


class TBoardNearMiss(unittest.TestCase):
    """T-BOARD-NEAR-MISS — §A64. Nearly-right verbs and shifted columns both REFUSE."""

    NEARLY_RIGHT = (
        'CLOSE', 'CLOSED.', 'closed', 'Closed', 'CLOSEDD',
        'PREFLIGHTED', 'PRE_FLIGHTED', 'PRE-FLIGHT',
        'HOLD(on: x)', 'HELD (on: x)', 'HELD(on:x)', 'HELD(on: )', 'held(on: x)',
        'OWED(by: mtr)', 'OWED(by: , act: x)', 'OWES(by: mtr, act: x)',
        'CORRECTED(supersedes: )', 'CORRECTED(superseded: x)', 'CORRECTED',
        'ACCEPTED ACCEPTED',
        # [EP-28X W2] THE RECORD'S OWN MINTS, VERBATIM. These two are not invented
        # look-alikes: the mentor wrote `NOTED-AS-RULED` and the architect wrote
        # `NOTED-PENDING-AS-RULED` on 2026-08-09, each within a turn of the ruling that
        # sized the verb set, because the right word existed and was NOT IN FORCE. Both
        # stand in `BOARD-EVENTS.log` today as removal-marker comments. Arming `NOTED`
        # must not arm anything that merely looks like it — the defect this pass ends is
        # the control that guards its ending.
        'NOTED-AS-RULED', 'NOTED-PENDING-AS-RULED',
        'noted', 'NOTED.', 'NOTED(x)', 'NOTE',
        'SEATED', 'SEATED(kind: replacement)', 'SEATED(kind: Continuation)',
        'SEATED(kind: )', 'SEATED (kind: continuation)', 'seated(kind: continuation)',
        'DISAMBIGUATED', 'DISAMBIGUATED(ending: 2026-03-01 ACCEPTED)',
        'DISAMBIGUATED(ended: HELD)',
        'DISAMBIGUATED(ending: 2026-03-01 ACCEPTED, ended: held)',
        'DISAMBIGUATED(ending: , ended: HELD)',
    )

    def test_every_nearly_right_verb_refuses(self):
        for verb in self.NEARLY_RIGHT:
            with self.assertRaises(board.BoardRefusal, msg='%r was ACCEPTED' % verb):
                board.parse_event_line(
                    'EVT | 2026-03-01 | ITEM-A | %s | seat |' % verb, 1)

    def test_the_exactly_right_verbs_are_not_refused(self):
        """The near-miss row's other half: the guard must still pass what is correct."""
        for verb in ('CLOSED', 'PRE-FLIGHTED', 'HELD(on: x)',
                     'OWED(by: mtr, act: x)', 'CORRECTED(supersedes: x)',
                     'NOTED', 'SEATED(kind: continuation)',
                     'SEATED(kind: substitution)',
                     'DISAMBIGUATED(ending: 2026-03-01 ACCEPTED, ended: HELD)'):
            board.parse_event_line('EVT | 2026-03-01 | ITEM-A | %s | seat |' % verb, 1)

    def test_a_date_shifted_one_column_right_refuses(self):
        with self.assertRaises(board.BoardRefusal) as caught:
            board.parse_event_line('EVT | ITEM-A | 2026-03-01 | CLOSED | seat |', 1)
        self.assertIn('not a YYYY-MM-DD date', caught.exception.reason)

    def test_a_date_in_the_item_column_refuses_the_other_direction(self):
        with self.assertRaises(board.BoardRefusal) as caught:
            board.parse_event_line('EVT | 2026-03-01 | 2026-03-02 | CLOSED | seat |', 1)
        self.assertIn('shifted', caught.exception.reason)

    def test_a_date_shaped_field_that_is_not_a_calendar_date_refuses(self):
        with self.assertRaises(board.BoardRefusal):
            board.parse_event_line('EVT | 2026-13-45 | ITEM-A | CLOSED | seat |', 1)

    def test_a_seat_column_holding_a_date_refuses(self):
        with self.assertRaises(board.BoardRefusal):
            board.parse_event_line('EVT | 2026-03-01 | ITEM-A | CLOSED | 2026-03-02 |', 1)

    def test_too_few_fields_refuses(self):
        with self.assertRaises(board.BoardRefusal):
            board.parse_event_line('EVT | 2026-03-01 | ITEM-A | CLOSED', 1)

    def test_a_clause_carrying_a_pipe_is_kept_whole_and_not_refused(self):
        ev = board.parse_event_line(
            'EVT | 2026-03-01 | ITEM-A | CLOSED | seat | a | b | c', 1)
        self.assertEqual(ev.clause, 'a | b | c')


class TBoardUnknownItem(unittest.TestCase):
    """T-BOARD-UNKNOWN-ITEM — refuses loudly; never reports an unseen name as started."""

    def test_an_unknown_name_reports_unknown_item_and_never_not_started(self):
        got = board.fold(board.read_event_lines(minimal(), '<fixture>')[0])
        out = io.StringIO()
        with unittest.mock.patch('sys.stdout', out):
            rc = board.print_item(got, 'NEVER-SEEN')
        self.assertEqual(rc, 3)
        self.assertIn('UNKNOWN-ITEM', out.getvalue())
        self.assertNotIn('not started', out.getvalue().lower().replace('"not-started"', ''))

    def test_a_known_name_does_not_report_unknown_item(self):
        """The other half: the guard must not fire on a name the seed covers."""
        got = board.fold(board.read_event_lines(minimal(), '<fixture>')[0])
        out = io.StringIO()
        with unittest.mock.patch('sys.stdout', out):
            rc = board.print_item(got, 'ITEM-A')
        self.assertEqual(rc, 0)
        self.assertNotIn('UNKNOWN-ITEM', out.getvalue())


class TBoardOwedAndHeldPair(unittest.TestCase):
    """T-BOARD-OWED-AND-HELD-PAIR — §3: the fold SHOWS THE PAIR, never picks one."""

    PAIR = (
        'EVT | 2026-03-01 | ITEM-A | HELD(on: another item) | mtr |',
        'EVT | 2026-03-01 | ITEM-A | OWED(by: mtr, act: a ruling) | mtr |',
    )

    def test_both_halves_stand_open_together(self):
        got = board.fold(board.read_event_lines(minimal(*self.PAIR), '<fixture>')[0])
        kinds = sorted(p.kind for p in got['ITEM-A'].open_pendings())
        self.assertEqual(kinds, ['HELD', 'OWED'])

    def test_the_order_they_were_written_in_does_not_pick_between_them(self):
        got = board.fold(
            board.read_event_lines(minimal(*reversed(self.PAIR)), '<fixture>')[0])
        kinds = sorted(p.kind for p in got['ITEM-A'].open_pendings())
        self.assertEqual(kinds, ['HELD', 'OWED'])

    def test_the_pair_is_visible_in_the_printed_board(self):
        got = board.fold(board.read_event_lines(minimal(*self.PAIR), '<fixture>')[0])
        cell = board._state_cell(got['ITEM-A'])
        self.assertIn('HELD(on: another item)', cell)
        self.assertIn('OWED(by: mtr, act: a ruling)', cell)

    def test_a_later_progress_event_over_a_pair_closes_neither(self):
        """DOCUMENTED FLIP [EP-28W W4]. Per-row, so the record of the trade survives.

        WHAT THIS ROW ASSERTED, 2026-08-08 (EP-28U): a later progress event over an open
        OWED+HELD pair CLOSED BOTH. That was `tools/board`'s own derived discharge rule,
        declared loudly at the time because `BOARD-GRAMMAR.md` said when a pending may
        STAND and not when one is DISCHARGED.

        WHAT SUPERSEDES IT, 2026-08-08 (EP-28W W4, landing the pair law's clause 3): with
        two or more states open, an ending that names none of them resolves to more than
        one candidate, so the fold REPORTS the ambiguity and CLOSES NOTHING. The old
        behaviour was a silent pick over two candidates.

        WHAT REMAINS TRUE and is asserted by its own row below: with ONE state open the
        derived rule is unchanged, byte-for-byte. The trade was made deliberately — the
        board stops closing states nobody said were ended, at the price of pendings that
        stand open until a `CORRECTED` names them."""
        lines = minimal(*(self.PAIR + ('EVT | 2026-03-02 | ITEM-A | CLOSED | mtr |',)))
        got = board.fold(board.read_event_lines(lines, '<fixture>')[0])
        self.assertEqual(sorted(p.kind for p in got['ITEM-A'].open_pendings()),
                         ['HELD', 'OWED'])
        self.assertEqual(got['ITEM-A'].state.kind, 'CLOSED')
        self.assertEqual(len(got['ITEM-A'].ambiguous_endings), 1)

    def test_a_later_pending_of_the_same_kind_supersedes_only_its_own_kind(self):
        lines = minimal(*(self.PAIR + (
            'EVT | 2026-03-02 | ITEM-A | HELD(on: a newer world) | mtr |',)))
        got = board.fold(board.read_event_lines(lines, '<fixture>')[0])
        self.assertEqual(got['ITEM-A'].pendings['HELD'].trigger, 'a newer world')
        self.assertEqual(got['ITEM-A'].pendings['OWED'].act, 'a ruling')


class TBoardCorrected(unittest.TestCase):
    """T-BOARD-CORRECTED — a CORRECTED replaces its target, and says so when it cannot."""

    def test_a_corrected_voids_exactly_its_target(self):
        lines = minimal(
            'EVT | 2026-03-01 | ITEM-A | RULED | mtr | the wrong ruling',
            'EVT | 2026-03-02 | ITEM-A | CORRECTED(supersedes: 2026-03-01 RULED) | m |',
        )
        got = board.fold(board.read_event_lines(lines, '<fixture>')[0])
        voided = [e for e in got['ITEM-A'].history if e.voided_by is not None]
        self.assertEqual([e.kind for e in voided], ['RULED'])
        self.assertEqual(got['ITEM-A'].state.resolution, 'RESOLVED')

    def test_a_corrected_naming_two_candidates_is_reported_ambiguous(self):
        """RED WORLD: a silent pick. The live log carries this shape at EP-28J, which
        holds two same-date OWED events and three same-date CORRECTED events."""
        lines = minimal(
            'EVT | 2026-03-01 | ITEM-A | RULED | mtr | first',
            'EVT | 2026-03-01 | ITEM-A | RULED | mtr | second, same date same verb',
            'EVT | 2026-03-02 | ITEM-A | CORRECTED(supersedes: 2026-03-01 RULED) | m |',
        )
        got = board.fold(board.read_event_lines(lines, '<fixture>')[0])
        self.assertEqual(got['ITEM-A'].state.resolution, 'AMBIGUOUS')
        self.assertEqual([c for _, c in got['ITEM-A'].ambiguous], [2])

    def test_a_free_text_reference_is_reported_unresolved_and_not_refused(self):
        """The tool folds a reference it cannot pin rather than refusing the whole log.
        RAISED in this pass: the grammar specifies `<date+verb>` and the live log carries
        free text. One constant flips this if the mentor rules the other way."""
        lines = minimal(
            'EVT | 2026-03-01 | ITEM-A | AUTHORED | mtr |',
            'EVT | 2026-03-02 | ITEM-A | CORRECTED(supersedes: none — addition) | mtr |',
        )
        got = board.fold(board.read_event_lines(lines, '<fixture>')[0])
        self.assertEqual(got['ITEM-A'].state.resolution, 'UNRESOLVED')
        self.assertEqual([e.voided_by for e in got['ITEM-A'].history], [None, None, None])

    def test_unpinned_references_are_reported_to_the_writer_not_swallowed(self):
        lines = minimal(
            'EVT | 2026-03-01 | ITEM-A | AUTHORED | mtr |',
            'EVT | 2026-03-02 | ITEM-A | CORRECTED(supersedes: a phrase) | mtr |',
        )
        got = board.fold(board.read_event_lines(lines, '<fixture>')[0])
        out = io.StringIO()
        with unittest.mock.patch('sys.stdout', out):
            board._print_reference_report(got)
        self.assertIn('FOR THE WRITER OF EVENTS', out.getvalue())
        self.assertIn('UNRESOLVED', out.getvalue())

    def test_the_writer_report_is_silent_when_every_reference_pins(self):
        """The other half: a report that always prints tells a writer nothing."""
        lines = minimal(
            'EVT | 2026-03-01 | ITEM-A | RULED | mtr |',
            'EVT | 2026-03-02 | ITEM-A | CORRECTED(supersedes: 2026-03-01 RULED) | m |',
        )
        got = board.fold(board.read_event_lines(lines, '<fixture>')[0])
        out = io.StringIO()
        with unittest.mock.patch('sys.stdout', out):
            board._print_reference_report(got)
        self.assertEqual(out.getvalue(), '')


class TBoardStaleHeader(unittest.TestCase):
    """T-BOARD-STALE-HEADER — the second-pass criterion applied at birth: at least one
    output field informs the WRITER of events, not only the reader."""

    LINES = (
        'EVT | 2026-03-01 | ITEM-OLD | HELD(on: a world that never moved) | mtr |',
        'EVT | 2026-05-01 | ITEM-NEW | OWED(by: archi, act: an unperformed act) | mtr |',
    )

    def _stale_output(self, since):
        events, meta = board.read_event_lines(minimal(*self.LINES), '<fixture>')
        got = board.fold(events)
        out = io.StringIO()
        with unittest.mock.patch('sys.stdout', out):
            board.print_stale(got, meta, since)
        return out.getvalue()

    def test_the_header_says_it_is_an_invitation_and_never_a_verdict(self):
        text = self._stale_output('2026-06-01')
        self.assertIn('INVITATION', text)
        self.assertIn('NEVER A VERDICT', text)

    def test_the_header_names_its_own_caps_including_its_date_resolution(self):
        text = self._stale_output('2026-06-01')
        self.assertIn('RESOLUTION IS THE DATE FIELD', text)
        self.assertIn('DISTINCT DATE(S)', text)
        self.assertIn('THIS LOG HOLDS 3 DISTINCT DATE(S)', text)

    def test_the_who_column_names_the_owed_seat_and_the_held_trigger(self):
        text = self._stale_output('2026-06-01')
        self.assertIn('OWED by archi — an unperformed act', text)
        self.assertIn('HELD on a world that never moved', text)

    def test_it_finds_the_old_item_and_leaves_the_new_one_alone(self):
        text = self._stale_output('2026-04-01')
        self.assertIn('ITEM-OLD', text)
        self.assertNotIn('ITEM-NEW', text)

    def test_age_is_measured_from_the_reference_and_never_from_a_wall_clock(self):
        events, _ = board.read_event_lines(minimal(*self.LINES), '<fixture>')
        rows = board.stale_items(board.fold(events), '2026-03-11')
        self.assertEqual(rows, [('ITEM-A', 38, '—'),
                                ('ITEM-OLD', 10, 'HELD on a world that never moved')])

    def test_a_stale_item_with_no_open_pending_shows_a_gap_and_not_a_seat(self):
        rows = board.stale_items(
            board.fold(board.read_event_lines(minimal(*self.LINES), '<f>')[0]),
            '2026-06-01')
        self.assertIn(('ITEM-A', 120, '—'), rows)

    def test_an_empty_result_is_not_printed_as_good_news(self):
        text = self._stale_output('2026-01-01')
        self.assertIn('(no items)', text)
        self.assertIn('read cap 1 before reading that as good news', text)


class TBoardControl(unittest.TestCase):
    """T-BOARD-CONTROL — every finding here is an ABSENCE, so a broken fold returns
    exactly the clean answer a healthy one returns. The control is the only thing that
    makes a zero interpretable, and it runs on EVERY invocation rather than once."""

    def test_the_control_passes_and_names_what_it_planted(self):
        ok, notes = board.positive_control()
        self.assertTrue(ok, notes)
        joined = ' '.join(notes)
        for expected in ('closed verbs exercised', 'OWED+HELD pair', 'CORRECTED voided',
                         'UNRESOLVED', 'stale item found', 'near-miss'):
            self.assertIn(expected, joined)

    def test_the_control_runs_on_every_invocation_and_prints_beside_the_board(self):
        """POINTED AT THE STATIC FIXTURE, not at the live record [EP-28W W2].

        Until EP-28W this row called `board.main(['--board'])`, whose `--events` DEFAULT is
        the live board of record — so it went red whenever a seat wrote a bad line to a
        DATA file, and it named no path, so a check for "a reference to the live path"
        could not see it. The subject is untouched: the control still has to run at every
        invocation, and this still proves it."""
        out = io.StringIO()
        with unittest.mock.patch('sys.stdout', out):
            rc = board.main(['--events', _FIXTURE_EVENTS, '--board'])
        self.assertEqual(rc, 0)
        self.assertIn('positive control PASSED', out.getvalue())

    def test_the_control_prints_beside_a_query_too_and_not_only_beside_the_board(self):
        out = io.StringIO()
        with unittest.mock.patch('sys.stdout', out):
            board.main(['--events', _FIXTURE_EVENTS, '--stale'])
        self.assertIn('positive control PASSED', out.getvalue())

    #: THE NEUTER, SHARPENED [EP-28X W2]. It returned `[]` from EP-28U until 2026-08-09,
    #: which was blunt: with three verbs armed, no open pendings ANYWHERE makes the
    #: `DISAMBIGUATED` control refuse the control log outright, so the row went red for a
    #: clause four blocks upstream of its own subject. That is verbatim the hole
    #: `test_a_neutered_refusal_...` names beside it — "a blunter neuter would break an
    #: earlier note and this row would be green for the wrong clause" — and this pass made
    #: it real rather than hypothetical. THE CODE WAS NOT LOOSENED TO ACCOMMODATE IT. The
    #: neuter now suppresses exactly ONE HALF OF A PAIR, which is this row's stated red
    #: world, and every other clause still runs.
    @staticmethod
    def _only_the_first_half(item):
        return [item.pendings[k] for k in board.PENDING_KINDS if k in item.pendings][:1]

    def test_a_neutered_fold_makes_the_control_fail_rather_than_return_a_clean_zero(self):
        """DRIVEN, not described. With the pair-showing behaviour neutered the fold
        still produces a board and `--stale` still produces its zero — which is the whole
        argument for the control existing."""
        original = board.ItemState.open_pendings
        try:
            board.ItemState.open_pendings = TBoardControl._only_the_first_half
            ok, notes = board.positive_control()
        finally:
            board.ItemState.open_pendings = original
        self.assertFalse(ok)
        self.assertIn('pair', ' '.join(notes))

    def test_the_sharpened_neuter_still_fails_on_the_PAIR_note_and_not_upstream(self):
        """The sharpening is itself controlled: the failure must name the pair clause, or
        the row above is green for the wrong reason again."""
        original = board.ItemState.open_pendings
        try:
            board.ItemState.open_pendings = TBoardControl._only_the_first_half
            ok, notes = board.positive_control()
        finally:
            board.ItemState.open_pendings = original
        self.assertFalse(ok)
        self.assertIn('was not SHOWN AS A PAIR', ' '.join(notes))
        self.assertNotIn('control log itself REFUSED', ' '.join(notes))

    def test_a_neutered_refusal_makes_the_control_fail_on_its_near_misses(self):
        """Neutered PRECISELY at the refusal — every correct verb still classifies, and
        only the near-misses stop refusing. A blunter neuter would break the verb-coverage
        note first and the near-miss note would never be reached, which would leave this
        row green for the wrong clause (the red-world law's own hole)."""
        original = board._classify_verb

        def tolerant(verb, lineno):
            try:
                return original(verb, lineno)
            except board.BoardRefusal:
                return board.Event(lineno, None, None, verb, 'CLOSED', None, None)

        try:
            board._classify_verb = tolerant
            ok, notes = board.positive_control()
        finally:
            board._classify_verb = original
        self.assertFalse(ok)
        self.assertIn('NEAR-MISS ACCEPTED', ' '.join(notes))

    def test_a_failed_control_prints_uninterpretable_and_never_a_number(self):
        original = board.ItemState.open_pendings
        out = io.StringIO()
        try:
            board.ItemState.open_pendings = TBoardControl._only_the_first_half
            with unittest.mock.patch('sys.stdout', out):
                rc = board.main(['--events', _FIXTURE_EVENTS, '--board'])
        finally:
            board.ItemState.open_pendings = original
        self.assertEqual(rc, 2)
        self.assertIn('UNINTERPRETABLE', out.getvalue())
        self.assertNotIn('items.', out.getvalue())


class TBoardWritesNothing(unittest.TestCase):
    """T-BOARD-WRITES-NOTHING — the module's first law, asserted by AST rather than grep.

    The question is STRUCTURAL: does this module contain a construct that writes a file.
    A grep would answer about characters — the word "write" appears eleven times in the
    module's own prose saying it does not write."""

    WRITER_ATTRS = ('write', 'writelines', 'writable', 'truncate',
                    'write_text', 'write_bytes')
    WRITER_FUNCS = ('remove', 'unlink', 'rename', 'replace', 'rmdir', 'mkdir',
                    'makedirs', 'copy', 'copyfile', 'move', 'rmtree',
                    'NamedTemporaryFile', 'mkstemp', 'mkdtemp')

    @staticmethod
    def _writers(source):
        found = []
        for node in ast.walk(ast.parse(source)):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Name) and func.id == 'open':
                mode = None
                if len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
                    mode = node.args[1].value
                for kw in node.keywords:
                    if kw.arg == 'mode' and isinstance(kw.value, ast.Constant):
                        mode = kw.value.value
                if mode is not None and not (mode.startswith('r') and '+' not in mode):
                    found.append('open(mode=%r) at line %d' % (mode, node.lineno))
            elif isinstance(func, ast.Attribute):
                if func.attr in TBoardWritesNothing.WRITER_ATTRS:
                    found.append('.%s() at line %d' % (func.attr, node.lineno))
                elif func.attr in TBoardWritesNothing.WRITER_FUNCS:
                    found.append('.%s() at line %d' % (func.attr, node.lineno))
            elif isinstance(func, ast.Name) and func.id in TBoardWritesNothing.WRITER_FUNCS:
                found.append('%s() at line %d' % (func.id, node.lineno))
        return found

    def test_the_module_contains_no_file_writing_construct(self):
        with open(_MODULE_PATH, 'r', encoding='utf-8') as handle:
            source = handle.read()
        self.assertEqual(self._writers(source), [])

    def test_the_guard_can_fail_because_a_planted_writer_really_is_found(self):
        """A guard that cannot fail is not a guard. Planted into a COPY of the real
        source — the file on disk is never touched."""
        with open(_MODULE_PATH, 'r', encoding='utf-8') as handle:
            source = handle.read()
        planted = source + '\n\ndef _planted():\n    open("x", "w").write("no")\n'
        found = self._writers(planted)
        self.assertTrue(any('open(mode=' in f for f in found), found)
        self.assertTrue(any('.write()' in f for f in found), found)

    def test_near_miss_the_walk_reads_structure_and_not_the_word_write(self):
        """§A64's other half. Text that MENTIONS writing is not a writer, and the AST
        says so where a grep could not."""
        prose = ('write_count = 0\n'
                 'MODE = "w"\n'
                 '# this module must never write a file\n'
                 'DOC = """it writes nothing, anywhere"""\n'
                 'handle = open("x")\n'
                 'handle = open("x", "r")\n'
                 'handle = open("x", mode="r")\n')
        self.assertEqual(self._writers(prose), [])

    def test_near_miss_a_read_plus_mode_is_caught_where_a_plain_read_is_not(self):
        self.assertEqual(self._writers('open("x", "r")'), [])
        self.assertEqual(len(self._writers('open("x", "r+")')), 1)
        self.assertEqual(len(self._writers('open("x", "a")')), 1)


class TBoardHeaderIsNotLoadBearing(unittest.TestCase):
    """T-BOARD-HEADER-IS-NOT-LOAD-BEARING — the fold anchors on the SEED MARKER in the
    body and never on the file's header.

    This is not hypothetical. On 2026-08-08 `BOARD-EVENTS.log`'s header read that the
    seed block was "(not yet written)" while the seed sat twelve lines below it, and the
    header was repaired in place DURING this pass. A fold that believed the header would
    have refused a healthy file, then changed its answer when a label was corrected."""

    BODY = (SEED_OPEN,
            'EVT | 2026-02-01 | ITEM-A | AUTHORED | seat |',
            SEED_SHUT,
            'EVT | 2026-03-01 | ITEM-A | CLOSED | seat |')

    def _board_from(self, *header):
        events, _ = board.read_event_lines(list(header) + list(self.BODY), '<fixture>')
        return {n: board._state_cell(s) for n, s in board.fold(events).items()}

    def test_a_lying_header_and_a_true_header_give_the_same_board(self):
        lying = self._board_from('# the seed block is not yet written')
        true = self._board_from('# the seed block is written below')
        absent = self._board_from()
        self.assertEqual(lying, true)
        self.assertEqual(lying, absent)
        self.assertEqual(lying, {'ITEM-A': 'CLOSED'})

    def test_a_header_claiming_a_seed_does_not_create_one(self):
        """The other direction: prose cannot supply a seed the body lacks."""
        with self.assertRaises(board.BoardRefusal):
            board.read_event_lines(
                ['# SEED BLOCK is written and complete, honestly',
                 'EVT | 2026-03-01 | ITEM-A | CLOSED | seat |'], '<fixture>')


class TBoardNoLiveRecord(unittest.TestCase):
    """T-BOARD-NO-LIVE-RECORD [EP-28W W2] — NO ROW IN THIS FILE REACHES THE LIVE RECORD.

    THE RULED DISPOSITION, 2026-08-08: a suite asserts about CODE; the board of record is
    DATA; so "the board of record folds" leaves the suite and becomes `inventory.py`'s
    DEFECT 6, which runs at every invocation and no lawful edit can redden.

    THE ROW IS WIDER THAN THE FOUR ROWS THAT WERE REMOVED, AND IT HAS TO BE. EP-28W W2
    specifies "this file holds no reference to the live log's path". Four rows reached the
    record BY NAME and two reached it BY DEFAULT — `board.main(['--board'])` names no path
    and takes the live one. A check phrased over the references it can SEE cannot see a
    default, and the two rows it missed are two of the six that went red on 2026-08-08
    (the record's own arm: "two failures and four errors"). So this row reads THREE
    arrival shapes, and each has a planted case below.

    AND IT READS STRUCTURE, NEVER TEXT. The live path appears in this file's own prose
    several times saying nothing reads it. A grep would answer about characters; the AST
    answers about references. A CAP, stated: a COMMENT naming the path is invisible to
    the AST, and correctly so — a comment is not a reference."""

    #: THE ONE PLACE THIS FILE MAY NAME THE LIVE BASENAME: this detector's own pattern. A
    #: detector has to be able to say what it looks for, and on its first run this row
    #: caught THIS assignment and went red — correctly, which is how the exemption came to
    #: be declared rather than assumed. It is DECLARED and GUARDED: the row below requires
    #: EXACTLY ONE assignment to this name, so the exemption is a ceiling and cannot grow
    #: quietly into a way of naming the live record for real work.
    PATTERN_HOLDER = 'LIVE_BASENAME'
    LIVE_BASENAME = 'BOARD-EVENTS.log'

    @classmethod
    def _pattern_constants(cls, tree):
        """The constant nodes assigned to the detector's own pattern name."""
        marked = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == cls.PATTERN_HOLDER \
                            and isinstance(node.value, ast.Constant):
                        marked.add(id(node.value))
        return marked

    @staticmethod
    def _docstring_constants(tree):
        """The string constants that are DOCSTRINGS. A docstring cannot be an argument, so
        prose about the live record is not a reference to it — §A64's other half."""
        marked = set()
        for node in ast.walk(tree):
            body = getattr(node, 'body', None)
            if not isinstance(body, list):
                continue
            for stmt in body:
                if (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant)
                        and isinstance(stmt.value.value, str)):
                    marked.add(id(stmt.value))
        return marked

    @classmethod
    def _live_references(cls, source):
        """Every structural way a source could reach the LIVE board of record."""
        tree = ast.parse(source)
        skip = cls._docstring_constants(tree) | cls._pattern_constants(tree)
        found = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if id(node) in skip:
                    continue
                # WHOLE PATH COMPONENT, never a substring: that is the pattern's own axis,
                # and it is what lets a fixture named BOARD-EVENTS-FIXTURE.events live
                # beside this row without tripping it.
                if cls.LIVE_BASENAME in re.split(r'[\\/]', node.value):
                    found.append('live path literal at line %d' % node.lineno)
            elif isinstance(node, ast.Attribute) and node.attr == 'EVENTS':
                found.append('board.EVENTS at line %d' % node.lineno)
            elif isinstance(node, ast.Call):
                func = node.func
                if (isinstance(func, ast.Attribute) and func.attr == 'main'
                        and isinstance(func.value, ast.Name) and func.value.id == 'board'):
                    # THE ARGV EXPRESSION, walked whole rather than pattern-matched on a
                    # literal list: `['--events', p] + rest` names the option and a bare
                    # `argv` variable does not. AN UNKNOWABLE CALL IS FLAGGED, not waved
                    # through — an opaque argv is precisely the shape that got past the
                    # check EP-28W W2 specified, and "I cannot tell" is not "it is fine".
                    argv = node.args[0] if node.args else None
                    names_events = argv is not None and any(
                        isinstance(sub, ast.Constant) and sub.value == '--events'
                        for sub in ast.walk(argv))
                    if not names_events:
                        found.append('board.main() taking the DEFAULT events path at '
                                     'line %d' % node.lineno)
        return found

    def _own_source(self):
        with open(os.path.abspath(__file__), 'r', encoding='utf-8') as handle:
            return handle.read()

    def test_no_row_in_this_file_reaches_the_live_board_of_record(self):
        self.assertEqual(self._live_references(self._own_source()), [])

    def test_the_detector_finds_a_planted_reference_by_name(self):
        planted = self._own_source() + '\n\ndef _p():\n    return board.EVENTS\n'
        self.assertTrue(any('board.EVENTS' in f
                            for f in self._live_references(planted)))

    def test_the_detector_finds_a_planted_reference_by_literal_path(self):
        planted = ('P = "planning/build/' + self.LIVE_BASENAME + '"\n')
        self.assertEqual(len(self._live_references(planted)), 1)

    def test_the_detector_finds_a_planted_call_taking_the_default_path(self):
        """THE ARRIVAL SHAPE THE SPECIFIED CHECK COULD NOT SEE. It names no path."""
        planted = self._own_source() + '\n\ndef _p():\n    return board.main(["--board"])\n'
        self.assertTrue(any('DEFAULT events path' in f
                            for f in self._live_references(planted)))

    def test_near_miss_a_fixture_path_resembling_the_live_path_does_not_match(self):
        """§A64 ON THE PATTERN'S OWN AXIS. Each of these is one edit away from the live
        path and NONE of them is it."""
        for near in ('tests/board-events-fixture.events',
                     'tests/BOARD-EVENTS-FIXTURE.log',
                     'tests/BOARD-EVENTS.log.bak',
                     'tests/not-BOARD-EVENTS.log',
                     'BOARD-EVENTS.events'):
            self.assertEqual(self._live_references('P = %r\n' % near), [],
                             'the near-miss %r was read as the live path' % near)

    def test_near_miss_prose_about_the_live_record_is_not_a_reference_to_it(self):
        prose = ('"""this module never reads planning/build/BOARD-EVENTS.log"""\n'
                 'def f():\n'
                 '    """it does not open BOARD-EVENTS.log either"""\n'
                 '    return 1\n')
        self.assertEqual(self._live_references(prose), [])

    def test_the_detector_is_not_vacuous_it_finds_the_path_where_it_belongs(self):
        """THE POSITIVE CONTROL, and it is the clause EP-28W W2 states from the other
        side: the live path inside the INSTRUMENT — whose job is to read it — must not
        trip this row, and the way to show that is not to argue it. The detector DOES find
        the reference in both instruments; this row's subject is this file alone."""
        for path in (_MODULE_PATH, _INVENTORY_PATH):
            with open(path, 'r', encoding='utf-8') as handle:
                found = self._live_references(handle.read())
            self.assertTrue(found, 'the detector found nothing in %s, so a zero from it '
                                   'against the test file means nothing' % path)

    def test_the_detectors_own_pattern_is_the_ONLY_exemption_and_cannot_grow(self):
        """AN EXEMPTION TABLE IS SHRINK-ONLY. One assignment, declared, with a reason. A
        second one is a new way to name the live record and it fails here."""
        assigns = [n for n in ast.walk(ast.parse(self._own_source()))
                   if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == self.PATTERN_HOLDER
                           for t in n.targets)]
        self.assertEqual(len(assigns), 1)

    @staticmethod
    def _writing_opens(source):
        """Writing `open()` calls whose target is NOT rooted at an owned scratch dir.

        The property is not "nothing writes" — DEFECT 6's rows must write their fixtures
        somewhere. It is that every write lands in a directory this process owns, OUTSIDE
        the repository: `git add -A` conscripts any untracked file in the tree and the
        rebase then replaces its inode under a live writer."""
        offenders = []
        for node in ast.walk(ast.parse(source)):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id == 'open'):
                continue
            mode = None
            if len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
                mode = node.args[1].value
            for kw in node.keywords:
                if kw.arg == 'mode' and isinstance(kw.value, ast.Constant):
                    mode = kw.value.value
            if mode is None or (mode.startswith('r') and '+' not in mode):
                continue
            target = node.args[0] if node.args else None
            rooted = (isinstance(target, ast.Call)
                      and isinstance(target.func, ast.Attribute)
                      and target.func.attr == 'join'
                      and target.args
                      and isinstance(target.args[0], ast.Attribute)
                      and target.args[0].attr == 'scratch')
            if not rooted:
                offenders.append('a writing open() not rooted at an owned scratch dir at '
                                 'line %d' % node.lineno)
        return offenders

    def test_every_write_in_this_file_lands_in_an_owned_scratch_dir_outside_the_tree(self):
        self.assertEqual(self._writing_opens(self._own_source()), [])

    def test_the_write_guard_can_fail_because_a_planted_in_tree_write_is_found(self):
        planted = 'def _p():\n    open("notes.txt", "w").write("x")\n'
        self.assertEqual(len(self._writing_opens(planted)), 1)

    def test_near_miss_the_write_guard_does_not_fire_on_reads(self):
        for benign in ('open(p)', 'open(p, "r")', 'open(p, mode="r")',
                       'open(os.path.join(self.scratch, "f"), "w")'):
            self.assertEqual(self._writing_opens('x = %s\n' % benign), [], benign)


class TBoardBadArgument(unittest.TestCase):
    """T-BOARD-BAD-ARGUMENT [EP-28W W3] — the tool applies its own standard to its own
    arguments.

    BEFORE THIS PASS, `--stale EP-29` reached `datetime.date(*[int(p) for p in ...])` and
    died in a raw `ValueError` traceback, leaving with the interpreter's 1 — so a caller
    could not tell a mistyped argument from a crashed tool. Both are still distinguishable
    only if the chosen code collides with nothing, which is why the first row below is a
    set-difference and not a spot check."""

    def _run(self, *rest, **kw):
        events = kw.pop('events', _FIXTURE_EVENTS)
        out = io.StringIO()
        err = io.StringIO()
        with unittest.mock.patch('sys.stdout', out), unittest.mock.patch('sys.stderr',
                                                                        err):
            rc = board.main(['--events', events, *rest])
        return rc, out.getvalue(), err.getvalue()

    def test_the_declared_code_collides_with_nothing_including_the_interpreters_one(self):
        """A COLLISION IS A RED, NEVER A CHOICE. Computed over the whole declared set
        rather than over the codes this row happens to remember."""
        others = set(board.DECLARED_EXIT_CODES) - {board.EXIT_BAD_ARGUMENT}
        self.assertNotIn(board.EXIT_BAD_ARGUMENT, others)
        self.assertIn(1, others, 'the interpreter\'s 1 must be IN the declared set, or a '
                                 'later author can pick it')
        self.assertEqual(others, {0, 1, 2, 3, 4},
                         'the exit-code contract moved; re-establish it before choosing')

    def test_a_non_date_argument_refuses_with_a_named_reason_and_the_declared_code(self):
        rc, out, err = self._run('--stale', 'EP-29')
        self.assertEqual(rc, board.EXIT_BAD_ARGUMENT)
        self.assertIn('REFUSED', out)
        self.assertIn('--stale', out)
        self.assertIn('EP-29', out)
        self.assertIn('not a YYYY-MM-DD date', out)
        self.assertEqual(err, '', 'a refusal is not a traceback')

    def test_a_date_shaped_non_date_refuses_too_and_says_which_half_failed(self):
        """The second raw-traceback path on the SAME argument surface: right shape, not a
        calendar date. One fix covers both, and each is asserted rather than assumed."""
        rc, out, _ = self._run('--stale', '2026-13-45')
        self.assertEqual(rc, board.EXIT_BAD_ARGUMENT)
        self.assertIn("date's SHAPE", out)

    def test_near_miss_bare_stale_is_still_valid_and_leaves_with_zero(self):
        rc, out, _ = self._run('--stale')
        self.assertEqual(rc, board.EXIT_OK)
        self.assertIn('STALE — items with no event since', out)

    def test_near_miss_a_valid_date_still_folds_normally(self):
        rc, out, _ = self._run('--stale', '2026-03-02')
        self.assertEqual(rc, board.EXIT_OK)
        self.assertIn('FIXTURE-B', out)

    def test_the_refusal_is_raised_before_the_record_is_ever_read(self):
        """A caller who mistyped an argument is told about the ARGUMENT. Driven with an
        events path that does not exist: if the log were read first this would return the
        refusal code instead."""
        rc, _, _ = self._run('--stale', 'NOT-A-DATE',
                             events=os.path.join(_HERE, 'no-such-file.events'))
        self.assertEqual(rc, board.EXIT_BAD_ARGUMENT)

    def test_the_declared_codes_are_in_the_tools_own_contract_text(self):
        out = io.StringIO()
        with unittest.mock.patch('sys.stdout', out):
            with self.assertRaises(SystemExit):
                board.main(['--events', _FIXTURE_EVENTS, '--help'])
        text = out.getvalue()
        self.assertIn('EXIT CODES, DECLARED', text)
        for code in board.DECLARED_EXIT_CODES:
            self.assertIn('  %d  ' % code, text)

    def test_the_parser_helper_refuses_rather_than_letting_valueerror_escape(self):
        for bad in ('EP-29', '', '2026-13-45', '2026-02-30', 'today', '2026/03/01'):
            with self.assertRaises(board.BadArgument, msg='%r was accepted' % bad):
                board.parse_date_argument('--stale', bad)

    def test_the_helper_still_accepts_what_is_actually_a_date(self):
        self.assertEqual(board.parse_date_argument('--stale', '2026-03-01').day, 1)


class TBoardAmbiguousEnding(unittest.TestCase):
    """T-BOARD-AMBIGUOUS-ENDING [EP-28W W4] — `BOARD-GRAMMAR.md` §1's pair law, clause 3.

    While two or more states stand open on one item, an event that ends one NAMES the one
    it ends. Unnamed, it resolves to more than one candidate, so the fold REPORTS and never
    picks. The boundary is where determinism ends: with ONE state open, inference is
    unchanged.

    ITEM 21 NON-VACUITY: every row here asserts the pair is OPEN before the ending is
    folded. "Both states were closed" and "no states existed" look identical from the other
    end, and a comparison over an empty candidate set proves nothing."""

    PAIR = (
        'EVT | 2026-03-01 | ITEM-A | HELD(on: another item) | mtr |',
        'EVT | 2026-03-01 | ITEM-A | OWED(by: mtr, act: a ruling) | mtr |',
    )

    def _open_before_the_ending(self):
        got = board.fold(board.read_event_lines(minimal(*self.PAIR), '<fixture>')[0])
        self.assertEqual(sorted(p.kind for p in got['ITEM-A'].open_pendings()),
                         ['HELD', 'OWED'], 'NON-VACUITY: the pair was not open to begin '
                                           'with, so the rows below compare over nothing')

    def test_an_unnamed_ending_over_a_pair_closes_nothing_and_is_reported(self):
        self._open_before_the_ending()
        lines = minimal(*(self.PAIR + ('EVT | 2026-03-02 | ITEM-A | ACCEPTED | mtr |',)))
        got = board.fold(board.read_event_lines(lines, '<fixture>')[0])
        item = got['ITEM-A']
        self.assertEqual(sorted(p.kind for p in item.open_pendings()), ['HELD', 'OWED'])
        self.assertEqual([e.closed_by for e in item.history
                          if e.kind in board.PENDING_KINDS], [None, None])
        self.assertEqual(len(item.ambiguous_endings), 1)
        ending, candidates = item.ambiguous_endings[0]
        self.assertEqual(ending.verb, 'ACCEPTED')
        self.assertEqual(sorted(candidates), ['HELD', 'OWED'])

    def test_the_report_names_the_item_the_line_and_the_candidate_set(self):
        lines = minimal(*(self.PAIR + ('EVT | 2026-03-02 | ITEM-A | ACCEPTED | mtr |',)))
        got = board.fold(board.read_event_lines(lines, '<fixture>')[0])
        out = io.StringIO()
        with unittest.mock.patch('sys.stdout', out):
            board._print_ambiguous_endings(got)
        text = out.getvalue()
        self.assertIn('ITEM-A', text)
        self.assertIn(':7', text)          # the ending event's own line in the fixture
        self.assertIn('HELD, OWED', text)
        self.assertIn('NOTHING WAS CLOSED', text)

    def test_near_miss_an_ending_that_NAMES_one_closes_exactly_that_one(self):
        """The naming mechanism the closed verb set actually has. The OWED must STAND —
        before this pass the branch that ran next closed it too."""
        self._open_before_the_ending()
        lines = minimal(*(self.PAIR + (
            'EVT | 2026-03-02 | ITEM-A | CORRECTED(supersedes: 2026-03-01 HELD) | mtr |',)))
        got = board.fold(board.read_event_lines(lines, '<fixture>')[0])
        item = got['ITEM-A']
        self.assertEqual([p.kind for p in item.open_pendings()], ['OWED'])
        self.assertEqual(item.ambiguous_endings, [])
        self.assertEqual(item.state.ending, 'NAMED')

    def test_near_miss_one_open_state_and_a_bare_ending_closes_it_exactly_as_before(self):
        """CLAUSE 3'S OWN BOUNDARY, and the reason standing history keeps its meaning."""
        lines = minimal('EVT | 2026-03-01 | ITEM-A | HELD(on: a world) | mtr |',
                        'EVT | 2026-03-02 | ITEM-A | CLOSED | mtr |')
        got = board.fold(board.read_event_lines(lines, '<fixture>')[0])
        item = got['ITEM-A']
        self.assertEqual(item.open_pendings(), [])
        self.assertEqual(item.ambiguous_endings, [])
        held = [e for e in item.history if e.kind == 'HELD'][0]
        self.assertEqual(held.closed_by, 6)
        self.assertEqual(item.state.ending, 'SINGLE')

    def test_near_miss_no_open_state_at_all_is_not_reported_ambiguous(self):
        lines = minimal('EVT | 2026-03-02 | ITEM-A | CLOSED | mtr |')
        got = board.fold(board.read_event_lines(lines, '<fixture>')[0])
        self.assertEqual(got['ITEM-A'].ambiguous_endings, [])

    def test_the_ambiguity_is_visible_in_the_item_history_output(self):
        lines = minimal(*(self.PAIR + ('EVT | 2026-03-02 | ITEM-A | ACCEPTED | mtr |',)))
        got = board.fold(board.read_event_lines(lines, '<fixture>')[0])
        out = io.StringIO()
        with unittest.mock.patch('sys.stdout', out):
            board.print_item(got, 'ITEM-A')
        self.assertIn('ENDING AMBIGUOUS', out.getvalue())

    def test_both_states_are_still_displayed_on_the_board(self):
        lines = minimal(*(self.PAIR + ('EVT | 2026-03-02 | ITEM-A | ACCEPTED | mtr |',)))
        got = board.fold(board.read_event_lines(lines, '<fixture>')[0])
        cell = board._state_cell(got['ITEM-A'])
        self.assertIn('HELD(on: another item)', cell)
        self.assertIn('OWED(by: mtr, act: a ruling)', cell)

    def test_the_standing_control_exercises_the_ambiguity_path_every_invocation(self):
        ok, notes = board.positive_control()
        self.assertTrue(ok, notes)
        joined = ' '.join(notes)
        self.assertIn('planted ambiguous ending closed NOTHING', joined)
        self.assertIn('named ending closed only what it named', joined)
        self.assertIn('single-state inference unchanged', joined)

    def test_a_neutered_ambiguity_duty_makes_the_control_fail(self):
        """RED WORLD, NEUTERED PRECISELY AT THE NEW CLAUSE. The neuter restores the
        pre-EP-28W behaviour — an unnamed ending closes everything — and nothing else, so
        the control fails on the ambiguity note rather than somewhere upstream."""
        original = board._apply_ending

        def pre_28w(item, ev, named, resolution=None):
            # The fourth parameter arrived with EP-28X W3 (a later DISAMBIGUATED naming
            # THIS ending). The neuter takes it and IGNORES it, which is exactly what the
            # pre-EP-28W world did — it is not an accommodation, it is the interface.
            ev.ending = 'SINGLE'
            for open_ev in item.open_pendings():
                open_ev.closed_by = ev.lineno
            item.pendings.clear()

        try:
            board._apply_ending = pre_28w
            ok, notes = board.positive_control()
        finally:
            board._apply_ending = original
        self.assertFalse(ok)
        self.assertIn('AMBIGUOUS ending', ' '.join(notes).replace('ambiguous', 'AMBIGUOUS'))


class TDefect6BoardFolds(unittest.TestCase):
    """T-DEFECT6-BOARD-FOLDS [EP-28W W2] — the fold assertion in its NEW home.

    The rows that used to live in this file read the live record and reddened when a seat
    wrote to it. The assertion now runs inside `tools/docmap/inventory.py` at EVERY
    invocation, asserts only that the record READS, and asserts nothing about its content.
    THESE rows drive the instrument over FIXTURES and never over the live file."""

    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('govos_inventory_ep28w',
                                                      _INVENTORY_PATH)
        cls.inv = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.inv)

    def setUp(self):
        self.scratch = self.inv.owned_scratch_dir()
        self.addCleanup(shutil.rmtree, self.scratch, True)

    def _write(self, name, text):
        # The join is INLINE in the open() call on purpose: the write guard reads the
        # open()'s own target expression, and a path laundered through a local name is
        # exactly what it cannot follow. It said so by going red on this line.
        with open(os.path.join(self.scratch, name), 'w', encoding='utf-8') as handle:
            handle.write(text)
        return os.path.join(self.scratch, name)

    WELL_FORMED = ('# fixture\n'
                   '# ===== SEED BLOCK =====\n'
                   'EVT | 2026-02-01 | ITEM-A | AUTHORED | seat |\n'
                   '# ===== END SEED BLOCK =====\n'
                   'EVT | 2026-03-01 | ITEM-A | CLOSED | seat |\n')

    def test_a_well_formed_record_reports_zero_with_its_control_in_the_same_run(self):
        path = self._write('good.events', self.WELL_FORMED)
        lines, healthy = self.inv.board_folds_report(path)
        self.assertTrue(healthy)
        self.assertIn('DEFECT 6', lines[0])
        self.assertTrue(lines[0].rstrip().endswith('0'), lines[0])
        self.assertTrue(any('positive control PASSED' in ln for ln in lines))

    def test_red_world_a_planted_double_marker_reds_the_line_loudly(self):
        """THE EXACT BREAK OF 2026-08-08: a comment QUOTING the seed marker becomes a
        second marker and the tool refuses the file whole."""
        path = self._write('broken.events', self.WELL_FORMED +
                           '# a comment quoting the SEED BLOCK marker\n')
        lines, healthy = self.inv.board_folds_report(path)
        self.assertFalse(healthy)
        self.assertTrue(lines[0].rstrip().endswith('1'), lines[0])
        joined = '\n'.join(lines)
        self.assertIn('DOES NOT FOLD', joined)
        self.assertIn('second SEED BLOCK marker', joined)

    def test_it_reports_the_tools_own_refusal_reason_and_not_a_paraphrase(self):
        path = self._write('bad-verb.events', self.WELL_FORMED +
                           'EVT | 2026-03-02 | ITEM-A | NOT-A-VERB | seat |\n')
        lines, healthy = self.inv.board_folds_report(path)
        self.assertFalse(healthy)
        self.assertIn('CLOSED set', '\n'.join(lines))

    def test_it_asserts_nothing_about_the_records_content(self):
        """THE WHOLE POINT OF THE MOVE. Two well-formed records with completely different
        content report the SAME line — a lawful edit cannot move this number."""
        one = self._write('one.events', self.WELL_FORMED)
        other = self._write('other.events', self.WELL_FORMED.replace('ITEM-A', 'ITEM-Z') +
                            'EVT | 2026-04-01 | ITEM-Q | RULED | mtr | anything at all\n')
        self.assertEqual(self.inv.board_folds_report(one)[0][0],
                         self.inv.board_folds_report(other)[0][0])

    def test_a_neutered_control_prints_uninterpretable_and_never_a_number(self):
        """A ZERO CLOSES A QUESTION A WRONG NUMBER WOULD REOPEN. Neutered at the checker
        so the planted break stops being caught; the line must refuse to print a count."""
        path = self._write('good.events', self.WELL_FORMED)
        original = self.inv._folds
        try:
            self.inv._folds = lambda p: (True, 'folds')
            lines, healthy = self.inv.board_folds_report(path)
        finally:
            self.inv._folds = original
        self.assertFalse(healthy)
        self.assertIn('UNINTERPRETABLE', lines[0])
        self.assertTrue(any('control FAILED' in ln for ln in lines))
        self.assertNotIn(': 0', lines[0])

    def test_the_scratch_is_unique_per_invocation_and_lives_outside_the_repository(self):
        made = [self.inv.owned_scratch_dir() for _ in range(3)]
        try:
            self.assertEqual(len(set(made)), 3)
            for path in made:
                self.assertTrue(path.startswith(self.inv.SCRATCH_PARENT + os.sep))
                self.assertFalse(path.startswith(_ROOT + os.sep),
                                 'scratch inside the tree is conscripted by autosync')
        finally:
            for path in made:
                shutil.rmtree(path, ignore_errors=True)

    def test_red_world_a_FIXED_SHARED_PATH_reds(self):
        """UNIQUE-PER-INVOCATION IS ENFORCED, NOT ASSUMED. The same check that passes for
        the real factory is driven with a fixed-path factory and REQUIRED to fail — a
        property nothing can violate has not been tested."""
        ok, detail = self.inv.scratch_paths_are_unique(self.inv.owned_scratch_dir)
        self.assertTrue(ok, detail)

        fixed = os.path.join(self.inv.SCRATCH_PARENT, 'a-fixed-shared-name')

        def fixed_path_factory():
            os.makedirs(fixed, exist_ok=True)
            return fixed

        try:
            bad_ok, bad_detail = self.inv.scratch_paths_are_unique(fixed_path_factory)
        finally:
            shutil.rmtree(fixed, ignore_errors=True)
        self.assertFalse(bad_ok)
        self.assertIn('FIXED SHARED PATH', bad_detail)

    def test_creation_is_create_or_refuse_rather_than_create_or_share(self):
        """The atomicity is what enforces it: a second creation at the same name FAILS
        rather than handing two invocations one directory."""
        with self.assertRaises(FileExistsError):
            os.mkdir(self.scratch)

    def test_the_creator_removes_its_own_scratch(self):
        before = set(os.listdir(self.inv.SCRATCH_PARENT))
        ok, _ = self.inv.board_folds_control()
        self.assertTrue(ok)
        after = set(os.listdir(self.inv.SCRATCH_PARENT))
        self.assertEqual(after - before, set(),
                         'the control left scratch behind under %s'
                         % self.inv.SCRATCH_PARENT)

    def test_defect_five_prints_as_RESERVED_rather_than_being_a_gap(self):
        """A run showing 1,2,3,4,6 reads as an oversight; a run naming 5 as RESERVED reads
        as a STATE. `PROCESS-FREEZE.md` rule 4 cites DEFECT 5 by number under the owner's
        signature, which makes the number an identity — coordinates cited in law are not
        reassigned."""
        with open(_INVENTORY_PATH, 'r', encoding='utf-8') as handle:
            source = handle.read()
        self.assertIn('DEFECT 5', source)
        self.assertIn('RESERVED', source)
        self.assertIn('PROCESS-FREEZE.md rule 4', source)

    def test_the_defect_line_appears_in_the_defects_output_with_its_control(self):
        out = io.StringIO()
        with unittest.mock.patch('sys.stdout', out), \
                unittest.mock.patch('sys.argv', ['inventory.py', '--defects']):
            self.inv.main()
        text = out.getvalue()
        self.assertIn('DEFECT 5', text)
        self.assertIn('RESERVED', text)
        self.assertIn('DEFECT 6 — the board of record folds', text)
        self.assertIn('positive control PASSED', text)


class TBoardOwnerTableStopped(unittest.TestCase):
    """W2 IS STOPPED, and the stop is a shipped behaviour rather than a silent gap.

    EP-28U W2 directs an `item | with | state` table with a `with` column and a
    `Closed since` line, citing `BOARD-GRAMMAR.md` §7. §7 as it stands says: "NO `Line`
    header, NO `with` column, NO `Closed since` line — those belong to the arc board the
    owner rejected." W2 is a faithful copy of §7 AS IT STOOD AT dfb38c3 08:02:20, the
    commit that authored the EP; §7 was replaced at 9aa8b42 08:10:19. Building it would
    ship the owner-rejected board a second time."""

    def test_the_flag_refuses_and_states_the_conflict_with_its_coordinates(self):
        out = io.StringIO()
        with unittest.mock.patch('sys.stdout', out):
            rc = board.main(['--events', _FIXTURE_EVENTS, '--owner-table'])
        text = out.getvalue()
        self.assertEqual(rc, 4)
        self.assertIn('IS NOT BUILT', text)
        self.assertIn('dfb38c3', text)
        self.assertIn('9aa8b42', text)

    def test_no_rejected_column_is_emitted_anywhere_by_any_query(self):
        """The load-bearing half: the stop is worth nothing if the shape ships anyway."""
        events, meta = board.read_event_lines(
            minimal('EVT | 2026-03-01 | ITEM-A | CLOSED | seat |'), '<fixture>')
        got = board.fold(events)
        out = io.StringIO()
        with unittest.mock.patch('sys.stdout', out):
            board.print_board(got, meta)
        text = out.getvalue()
        self.assertNotIn('| with |', text)
        self.assertNotIn('Closed since', text)
        self.assertNotIn('OWNER', text)


class TBoardRecordPlaneVerbs(unittest.TestCase):
    """T-BOARD-RECORD-PLANE-VERBS [EP-28X W2] — `NOTED` and `SEATED` fold as HISTORY ONLY.

    `BOARD-GRAMMAR.md` §1's sizing ruling, 2026-08-09: the closed set was complete in the
    ITEM LIFECYCLE plane and the estate stretched it to a second plane — acts about the
    RECORD ITSELF. A record-plane verb opens nothing, ends nothing, and changes no state;
    the clause carries the fact.

    THE CLAIM IS BOARD IDENTITY, SO IT IS PROVED BY DIFFERENTIAL AND NOT BY INSPECTION.
    Reading the fold's branches would prove that this fold does not change state; folding
    the same record with and without the record-plane lines proves that THE BOARD does not.

    ITEM 21 NON-VACUITY: every identity row asserts the item HOLDS an open state and a
    live lifecycle state BEFORE the record-plane lines are folded. Identity over an empty
    item proves nothing, and "nothing moved" and "there was nothing to move" look the same
    from the other end."""

    BASE = (
        'EVT | 2026-03-01 | ITEM-A | DISPATCHED | seat |',
        'EVT | 2026-03-01 | ITEM-A | HELD(on: a world) | seat |',
        'EVT | 2026-03-01 | ITEM-A | OWED(by: mtr, act: a ruling) | seat |',
    )
    PLANE = (
        'EVT | 2026-03-02 | ITEM-A | NOTED | seat | a plain addition, the overflow clause',
        'EVT | 2026-03-02 | ITEM-A | SEATED(kind: continuation) | seat |',
        'EVT | 2026-03-02 | ITEM-A | SEATED(kind: substitution) | seat |',
    )

    def _signature(self, item):
        return (item.state.verb if item.state is not None else None,
                sorted(p.verb for p in item.open_pendings()),
                [e.closed_by for e in item.history],
                len(item.ambiguous_endings))

    def _fold(self, *body):
        return board.fold(board.read_event_lines(minimal(*body), '<fixture>')[0])

    def test_NON_VACUITY_the_item_holds_open_state_before_any_record_plane_line(self):
        item = self._fold(*self.BASE)['ITEM-A']
        self.assertEqual(item.state.kind, 'OWED')
        self.assertEqual(sorted(p.kind for p in item.open_pendings()), ['HELD', 'OWED'])

    def test_the_board_is_IDENTICAL_with_and_without_the_record_plane_lines(self):
        without = self._fold(*self.BASE)['ITEM-A']
        with_them = self._fold(*(self.BASE + self.PLANE))['ITEM-A']
        self.assertEqual(self._signature(without)[:2], self._signature(with_them)[:2])
        self.assertEqual(self._signature(with_them)[1], ['HELD(on: a world)',
                                                         'OWED(by: mtr, act: a ruling)'])

    def test_a_record_plane_verb_never_becomes_the_items_state(self):
        item = self._fold(*(self.BASE + self.PLANE))['ITEM-A']
        self.assertNotIn(item.state.kind, board.HISTORY_ONLY_KINDS)
        self.assertEqual(item.state.kind, 'OWED')

    def test_a_record_plane_verb_closes_no_pending_where_an_ending_would(self):
        """THE DISCRIMINATOR. The same position, with an ENDING instead, is reported
        AMBIGUOUS and the pair still stands — so this row would pass for the wrong reason
        if it only checked that the pair survived. It checks the REPORT too: a NOTED is
        not an ending, so it produces no ambiguity report at all."""
        noted = self._fold(*(self.BASE + (self.PLANE[0],)))['ITEM-A']
        ending = self._fold(*(self.BASE + (
            'EVT | 2026-03-02 | ITEM-A | ACCEPTED | seat |',)))['ITEM-A']
        self.assertEqual(noted.ambiguous_endings, [])
        self.assertEqual(len(ending.ambiguous_endings), 1)
        self.assertEqual([e.closed_by for e in noted.history
                          if e.kind in board.PENDING_KINDS], [None, None])

    def test_the_history_carries_them_so_nothing_is_lost_by_being_stateless(self):
        item = self._fold(*(self.BASE + self.PLANE))['ITEM-A']
        kinds = [e.kind for e in item.history]
        self.assertEqual(kinds.count('NOTED'), 1)
        self.assertEqual(kinds.count('SEATED'), 2)

    def test_the_item_history_output_says_a_record_plane_line_is_history_only(self):
        got = self._fold(*(self.BASE + self.PLANE))
        out = io.StringIO()
        with unittest.mock.patch('sys.stdout', out):
            board.print_item(got, 'ITEM-A')
        self.assertIn('RECORD-PLANE — history only', out.getvalue())

    def test_a_record_plane_FIRST_event_gives_an_item_history_and_NO_state(self):
        """NOT HYPOTHETICAL. The queued intake lines per `BOARD-EVENTS.log:247` are this
        exact shape for four items the fold has never seen, and they are the next lawful
        act behind this pass. An item with no state must DISPLAY as one, not crash."""
        got = self._fold('EVT | 2026-03-01 | NEW-ITEM | NOTED | seat | the fact')
        item = got['NEW-ITEM']
        self.assertIsNone(item.state)
        self.assertEqual(len(item.history), 1)
        self.assertIn('NO STATE EVENT', board._state_cell(item))

    def test_the_printed_board_does_not_crash_on_an_item_with_no_state(self):
        """RED WORLD, and it is the one that would have cost an interpreter's 1 on a
        LAWFUL record: `print_board` read `item.state.date` for its coordinate."""
        events, meta = board.read_event_lines(
            minimal('EVT | 2026-03-01 | NEW-ITEM | NOTED | seat | the fact'), '<fixture>')
        out = io.StringIO()
        with unittest.mock.patch('sys.stdout', out):
            board.print_board(board.fold(events), meta)
        text = out.getvalue()
        self.assertIn('NEW-ITEM', text)
        self.assertIn('NO STATE EVENT', text)
        self.assertIn(':5', text)

    def test_the_stale_query_still_sees_an_item_that_only_has_record_plane_events(self):
        rows = board.stale_items(
            self._fold('EVT | 2026-03-01 | NEW-ITEM | NOTED | seat | the fact'),
            '2026-03-11')
        self.assertIn(('NEW-ITEM', 10, '—'), [r for r in rows])

    def test_the_seated_kind_set_is_closed_and_literal(self):
        for bad in ('replacement', 'Continuation', 'CONTINUATION', 'substitute', ''):
            with self.assertRaises(board.BoardRefusal, msg='%r was ACCEPTED' % bad):
                board.parse_event_line(
                    'EVT | 2026-03-01 | ITEM-A | SEATED(kind: %s) | seat |' % bad, 1)

    def test_the_records_own_two_mints_are_refused_verbatim(self):
        """THE POINT OF THE PASS, ASSERTED AGAINST THE ACTUAL STRINGS TWO SEATS WROTE."""
        for mint in ('NOTED-AS-RULED', 'NOTED-PENDING-AS-RULED'):
            with self.assertRaises(board.BoardRefusal, msg='%r was ACCEPTED' % mint):
                board.parse_event_line(
                    'EVT | 2026-08-09 | ITEM-A | %s | mtr |' % mint, 1)

    def test_the_standing_control_exercises_the_record_plane_every_invocation(self):
        ok, notes = board.positive_control()
        self.assertTrue(ok, notes)
        self.assertIn('folded as HISTORY ONLY', ' '.join(notes))

    def test_RED_WORLD_a_record_plane_verb_that_became_a_state_fails_the_control(self):
        """Neutered PRECISELY at the third branch: `HISTORY_ONLY_KINDS` emptied, so a
        `NOTED` folds down the ending branch exactly as it would have before this pass.
        Every other clause still holds, so the control fails on the record-plane note."""
        original = board.HISTORY_ONLY_KINDS
        try:
            board.HISTORY_ONLY_KINDS = ()
            ok, notes = board.positive_control()
        finally:
            board.HISTORY_ONLY_KINDS = original
        self.assertFalse(ok)
        self.assertIn('CHANGED the board', ' '.join(notes))


class TBoardDisambiguated(unittest.TestCase):
    """T-BOARD-DISAMBIGUATED [EP-28X W3] — the pair law's missing form, by APPEND.

    `DISAMBIGUATED(ending: <date+verb>, ended: <state>)` says which open state a PAST
    ending ended. Nothing opens or closes NOW; the named ending folds AS OF ITS OWN
    POSITION as having ended exactly the named state, every other pending STANDS, and that
    ending's AMBIGUOUS-ENDING report DROPS.

    WHY IT REFUSES WHERE `CORRECTED` REPORTS. `CORRECTED`'s reference is PROVENANCE and
    lossy is acceptable — the state travels on its own line and the mentor ruled the
    standing unresolved set STANDS. THIS verb's reference IS ITS ENTIRE SEMANTIC CONTENT:
    one that cannot act is not informational residue, it is a state claim that failed
    while looking like one that landed. So a reference resolving to zero or two-or-more
    events, or an `ended:` outside the ending's candidate set, REFUSES THE FOLD WHOLE."""

    PAIR = (
        'EVT | 2026-03-01 | ITEM-A | HELD(on: a world) | mtr |',
        'EVT | 2026-03-01 | ITEM-A | OWED(by: mtr, act: a ruling) | mtr |',
    )
    ENDING = 'EVT | 2026-03-02 | ITEM-A | ACCEPTED | mtr |'
    RESOLVE = ('EVT | 2026-03-04 | ITEM-A | '
               'DISAMBIGUATED(ending: 2026-03-02 ACCEPTED, ended: HELD) | mtr |')

    def _fold(self, *body):
        return board.fold(board.read_event_lines(minimal(*body), '<fixture>')[0])

    def test_NON_VACUITY_the_ending_is_AMBIGUOUS_before_the_resolve_lands(self):
        item = self._fold(*(self.PAIR + (self.ENDING,)))['ITEM-A']
        self.assertEqual(len(item.ambiguous_endings), 1)
        self.assertEqual(sorted(p.kind for p in item.open_pendings()), ['HELD', 'OWED'])

    def test_it_ends_exactly_the_state_it_names_and_the_other_one_STANDS(self):
        item = self._fold(*(self.PAIR + (self.ENDING, self.RESOLVE)))['ITEM-A']
        self.assertEqual([p.kind for p in item.open_pendings()], ['OWED'])

    def test_the_ambiguity_report_for_that_ending_DROPS(self):
        item = self._fold(*(self.PAIR + (self.ENDING, self.RESOLVE)))['ITEM-A']
        self.assertEqual(item.ambiguous_endings, [])

    def test_the_closure_is_recorded_AS_OF_THE_ENDINGS_OWN_POSITION(self):
        """The load-bearing half of W3. A resolution stamped at the DISAMBIGUATED's own
        line would leave every later event believing the state was still open."""
        item = self._fold(*(self.PAIR + (self.ENDING, self.RESOLVE)))['ITEM-A']
        held = [e for e in item.history if e.kind == 'HELD'][0]
        ending = [e for e in item.history if e.kind == 'ACCEPTED'][0]
        dis = [e for e in item.history if e.kind == 'DISAMBIGUATED'][0]
        self.assertEqual(held.closed_by, ending.lineno)
        self.assertNotEqual(held.closed_by, dis.lineno)

    def test_a_LATER_ending_then_folds_over_ONE_candidate_rather_than_two(self):
        """THE DOWNSTREAM CONSEQUENCE, which is what 'as of its position' MEANS. Without
        it this second ending stays reported ambiguous over a state the record has since
        said was closed."""
        body = self.PAIR + (self.ENDING,
                            'EVT | 2026-03-03 | ITEM-A | RULED | mtr |',
                            self.RESOLVE)
        item = self._fold(*body)['ITEM-A']
        self.assertEqual(item.open_pendings(), [])
        self.assertEqual(item.ambiguous_endings, [])
        ruled = [e for e in item.history if e.kind == 'RULED'][0]
        self.assertEqual(ruled.ending, 'SINGLE')

    def test_nothing_opens_or_closes_at_the_DISAMBIGUATED_line_itself(self):
        item = self._fold(*(self.PAIR + (self.ENDING, self.RESOLVE)))['ITEM-A']
        dis = [e for e in item.history if e.kind == 'DISAMBIGUATED'][0]
        self.assertIsNone(dis.ending)
        self.assertNotIn(dis.kind, ('HELD', 'OWED'))
        self.assertEqual(item.state.kind, 'ACCEPTED',
                         'the DISAMBIGUATED became the item state; it is record-plane')

    def test_the_history_output_names_what_the_resolution_did(self):
        got = self._fold(*(self.PAIR + (self.ENDING, self.RESOLVE)))
        out = io.StringIO()
        with unittest.mock.patch('sys.stdout', out):
            board.print_item(got, 'ITEM-A')
        text = out.getvalue()
        self.assertIn('ended the HELD, said so by the DISAMBIGUATED at', text)
        self.assertNotIn('ENDING AMBIGUOUS', text)

    def test_RED_WORLD_a_reference_matching_NOTHING_refuses_the_fold_whole(self):
        body = self.PAIR + (self.ENDING,
                            'EVT | 2026-03-04 | ITEM-A | '
                            'DISAMBIGUATED(ending: 2026-03-02 CLOSED, ended: HELD) | m |')
        with self.assertRaises(board.BoardRefusal) as caught:
            self._fold(*body)
        self.assertEqual(caught.exception.lineno, 8)
        self.assertIn('EXACTLY ONE', caught.exception.reason)

    def test_RED_WORLD_a_reference_matching_TWO_refuses_the_fold_whole(self):
        body = self.PAIR + ('EVT | 2026-03-02 | ITEM-A | ACCEPTED | mtr | first',
                            'EVT | 2026-03-02 | ITEM-A | ACCEPTED | mtr | second',
                            self.RESOLVE)
        with self.assertRaises(board.BoardRefusal) as caught:
            self._fold(*body)
        self.assertIn('resolves to 2 earlier event(s)', caught.exception.reason)

    def test_RED_WORLD_an_ended_state_outside_the_candidate_set_refuses_whole(self):
        body = ('EVT | 2026-03-01 | ITEM-A | HELD(on: a world) | mtr |',
                'EVT | 2026-03-02 | ITEM-A | ACCEPTED | mtr |',
                'EVT | 2026-03-04 | ITEM-A | '
                'DISAMBIGUATED(ending: 2026-03-02 ACCEPTED, ended: OWED) | mtr |')
        with self.assertRaises(board.BoardRefusal) as caught:
            self._fold(*body)
        self.assertIn('candidate set', caught.exception.reason)

    def test_RED_WORLD_resolving_one_ending_TWICE_refuses_whole(self):
        """DERIVED, DECLARED, AND RAISED rather than assumed: one past ending ended ONE
        state, so a second resolution is a duplicate or a contradiction, and an
        append-only record is repaired by `CORRECTED` and not by re-stating."""
        body = self.PAIR + (self.ENDING, self.RESOLVE,
                            'EVT | 2026-03-05 | ITEM-A | '
                            'DISAMBIGUATED(ending: 2026-03-02 ACCEPTED, ended: OWED) | m |')
        with self.assertRaises(board.BoardRefusal) as caught:
            self._fold(*body)
        self.assertIn('already disambiguated', caught.exception.reason)

    def test_NEAR_MISS_a_reference_pointing_FORWARD_is_not_a_past_ending(self):
        """`ending:` names a PAST ending. A line naming one that comes AFTER it resolves
        to zero earlier events and refuses, rather than reaching forward."""
        body = self.PAIR + (self.RESOLVE, self.ENDING)
        with self.assertRaises(board.BoardRefusal) as caught:
            self._fold(*body)
        self.assertIn('resolves to 0 earlier event(s)', caught.exception.reason)

    def test_NEAR_MISS_a_reference_to_another_ITEMS_ending_does_not_resolve(self):
        body = ('EVT | 2026-03-01 | ITEM-B | HELD(on: a world) | mtr |',
                'EVT | 2026-03-02 | ITEM-B | ACCEPTED | mtr |',
                'EVT | 2026-03-04 | ITEM-A | '
                'DISAMBIGUATED(ending: 2026-03-02 ACCEPTED, ended: HELD) | mtr |')
        with self.assertRaises(board.BoardRefusal) as caught:
            self._fold(*body)
        self.assertIn('resolves to 0 earlier event(s)', caught.exception.reason)

    def test_NEAR_MISS_a_free_text_reference_refuses_where_CORRECTEDs_only_reports(self):
        """THE TWO VERBS' REFERENCES ARE DIFFERENT OBJECTS, and this row is the pair that
        shows it: the same unpinnable phrase is a REPORT on a CORRECTED and a REFUSAL on
        a DISAMBIGUATED."""
        tolerated = self._fold(
            'EVT | 2026-03-01 | ITEM-A | AUTHORED | mtr |',
            'EVT | 2026-03-02 | ITEM-A | CORRECTED(supersedes: a phrase) | mtr |')
        self.assertEqual(tolerated['ITEM-A'].state.resolution, 'UNRESOLVED')
        with self.assertRaises(board.BoardRefusal) as caught:
            self._fold('EVT | 2026-03-01 | ITEM-A | AUTHORED | mtr |',
                       'EVT | 2026-03-02 | ITEM-A | '
                       'DISAMBIGUATED(ending: a phrase, ended: HELD) | mtr |')
        self.assertIn('<date+verb>', caught.exception.reason)

    def test_a_fold_time_refusal_reaches_the_command_line_with_the_refusal_code(self):
        """The refusal is raised in `fold()`, not in the read — a row drives it all the
        way out so no caller meets it as a traceback."""
        out = io.StringIO()
        with unittest.mock.patch('sys.stdout', out):
            rc = board.main(['--events', _FIXTURE_DISAMBIG_BAD, '--board'])
        self.assertEqual(rc, board.EXIT_REFUSED)
        self.assertIn('REFUSED at', out.getvalue())
        self.assertIn('EXACTLY ONE', out.getvalue())

    def test_the_standing_control_exercises_a_resolve_every_invocation(self):
        ok, notes = board.positive_control()
        self.assertTrue(ok, notes)
        self.assertIn("AS OF THE ENDING'S OWN POSITION", ' '.join(notes))

    def test_RED_WORLD_a_resolution_applied_at_the_wrong_position_fails_the_control(self):
        """Neutered PRECISELY at the placement: the closure is stamped at the
        DISAMBIGUATED's line instead of the ending's. The state still closes and the
        report still drops, so a control that only checked those would stay green."""
        original = board._apply_ending

        def stamp_at_the_wrong_line(item, ev, named, resolution=None):
            if resolution is None:
                return original(item, ev, named, None)
            dis, ended = resolution
            ev.ending = 'NAMED'
            ev.candidates = (ended,)
            ev.disambiguated_by = dis.lineno
            for open_ev in item.open_pendings():
                if open_ev.kind == ended:
                    open_ev.closed_by = dis.lineno
                    item.pendings.pop(ended, None)

        try:
            board._apply_ending = stamp_at_the_wrong_line
            ok, notes = board.positive_control()
        finally:
            board._apply_ending = original
        self.assertFalse(ok)
        self.assertIn("AS OF THE ENDING'S OWN POSITION", ' '.join(notes))


class TBoardAnchor(unittest.TestCase):
    """T-BOARD-ANCHOR [EP-28X W4] — `BOARD-GRAMMAR.md` §1a and its hole-fix, 2026-08-09.

    §1a rested on "every prefix is immutable BY CONSTRUCTION". The record is NOT strictly
    append-only: two removal markers stand in it, both lawful under the unparseable-line
    precedent, and a removal inside [1..N] silently changes what N names. A LINE COUNT IS
    A ROLE — "however many lines there happen to be" — so the coordinate is a CONTENT
    DIGEST of [1..N] and the count is its alias.

    THE ALGORITHM IS ASSERTED TO BE PRINTED. A digest whose algorithm is unstated is a
    number, not an anchor.

    EVERY FILE THESE ROWS TOUCH IS A COPY IN AN OWNED SCRATCH DIRECTORY under
    `/tmp/govos-board/`, unique per invocation, removed by its creator. The live record is
    never written, and no row here names it."""

    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('govos_inventory_ep28x',
                                                      _INVENTORY_PATH)
        cls.inv = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.inv)

    def setUp(self):
        self.scratch = self.inv.owned_scratch_dir()
        self.addCleanup(shutil.rmtree, self.scratch, True)

    def _write(self, name, text):
        # The join is INLINE in the open() call: the write guard reads the open()'s own
        # target expression and cannot follow a path laundered through a local name.
        with open(os.path.join(self.scratch, name), 'w', encoding='utf-8') as handle:
            handle.write(text)
        return os.path.join(self.scratch, name)

    WELL_FORMED = ('# fixture\n'
                   '# ===== SEED BLOCK =====\n'
                   'EVT | 2026-02-01 | ITEM-A | AUTHORED | seat |\n'
                   '# ===== END SEED BLOCK =====\n'
                   '# a comment line, removable under the unparseable-line precedent\n'
                   'EVT | 2026-03-01 | ITEM-A | CLOSED | seat |\n')

    def _run(self, path, *rest):
        """`--events` IS NAMED AS A LITERAL IN THE CALL, not laundered through `*rest`.

        `T-BOARD-NO-LIVE-RECORD` reads the argv expression for the option's own constant,
        and it caught the first draft of this helper, whose argv was an opaque `list(rest)`
        — structurally identical to the two rows EP-28W found reaching the live record
        through a default. The guard was not loosened; the call was written properly."""
        out = io.StringIO()
        with unittest.mock.patch('sys.stdout', out):
            rc = board.main(['--events', path, *rest])
        return rc, out.getvalue()

    @staticmethod
    def _anchor_of(text):
        found = re.search(r'ANCHOR \(N=(\d+), ([a-z0-9]+):([0-9a-f]{64})\)', text)
        return found and (int(found.group(1)), found.group(2), found.group(3))

    def test_every_fold_prints_its_anchor_with_the_algorithm_NAMED(self):
        path = self._write('a.events', self.WELL_FORMED)
        for query in (('--board',), ('--ep', 'ITEM-A'), ('--stale',)):
            rc, text = self._run(path, *query)
            self.assertEqual(rc, board.EXIT_OK, query)
            got = self._anchor_of(text)
            self.assertIsNotNone(got, 'no anchor beside %s' % (query,))
            self.assertEqual(got[0], 6)
            self.assertEqual(got[1], board.ANCHOR_ALGO)

    def test_the_digest_is_over_the_CONTENT_and_the_count_is_only_its_alias(self):
        """TWO PREFIXES OF EQUAL LENGTH AND DIFFERENT CONTENT. If the count were the
        coordinate these two would be the same taking."""
        one = board.content_digest(['a', 'b', 'c'])
        other = board.content_digest(['a', 'b', 'd'])
        self.assertNotEqual(one, other)
        self.assertEqual(len(one), 64)

    def test_at_N_folds_exactly_the_prefix_and_nothing_beyond_it(self):
        path = self._write('b.events', self.WELL_FORMED +
                           'EVT | 2026-04-01 | ITEM-Z | RULED | seat |\n')
        rc, text = self._run(path, '--at', '6', '--board')
        self.assertEqual(rc, board.EXIT_OK)
        self.assertIn('ITEM-A', text)
        self.assertNotIn('ITEM-Z', text)
        self.assertEqual(self._anchor_of(text)[0], 6)

    def test_NON_VACUITY_the_unbounded_fold_of_the_same_file_DOES_see_the_tail(self):
        """Without this the row above passes on a file whose tail was never there."""
        path = self._write('b.events', self.WELL_FORMED +
                           'EVT | 2026-04-01 | ITEM-Z | RULED | seat |\n')
        rc, text = self._run(path, '--board')
        self.assertEqual(rc, board.EXIT_OK)
        self.assertIn('ITEM-Z', text)

    def test_an_APPEND_BEYOND_N_does_not_perturb_an_anchored_prefix_fold(self):
        """§1a's whole point, and what retires the quiet-record window: the record never
        holds still, and it does not need to."""
        path = self._write('c.events', self.WELL_FORMED)
        rc_a, before = self._run(path, '--at', '6', '--board')
        self._write('c.events', self.WELL_FORMED +
                    'EVT | 2026-04-01 | ITEM-Z | RULED | seat |\n'
                    'EVT | 2026-04-02 | ITEM-Z | CLOSED | seat |\n')
        rc_b, after = self._run(path, '--at', '6', '--board')
        self.assertEqual((rc_a, rc_b), (board.EXIT_OK, board.EXIT_OK))
        self.assertEqual(before, after)

    def test_a_re_check_of_an_unchanged_prefix_REPRODUCES_the_digest(self):
        path = self._write('d.events', self.WELL_FORMED)
        _, first = self._run(path, '--board')
        digest = self._anchor_of(first)[2]
        rc, _ = self._run(path, '--board', '--anchor', digest)
        self.assertEqual(rc, board.EXIT_OK)

    def test_RED_WORLD_a_removal_planted_between_takings_REFUSES_WHOLE(self):
        """THE 2026-08-08 DOUBLE-MARKER WORLD'S SHAPE, APPLIED TO REMOVAL. The two
        standing removal markers in the live record are comment lines removed under the
        unparseable-line precedent, so this is the surgery that will recur."""
        path = self._write('e.events', self.WELL_FORMED)
        _, first = self._run(path, '--board')
        n, _algo, digest = self._anchor_of(first)
        surgical = ''.join(
            ln + '\n' for ln in self.WELL_FORMED.splitlines()
            if not ln.startswith('# a comment line'))
        self._write('e.events', surgical)
        rc, text = self._run(path, '--board', '--anchor', digest)
        self.assertEqual(rc, board.EXIT_REFUSED)
        self.assertIn('THE ANCHOR DOES NOT MATCH', text)
        self.assertIn(digest, text, 'the refusal must name the ANCHORED digest')
        self.assertIn(self._anchor_of(self._run(path, '--board')[1])[2], text,
                      'the refusal must name the CURRENT digest too')
        self.assertNotIn('BOARD — folded from', text, 'it must fold NOTHING')
        self.assertEqual(n - 1, 5)

    def test_at_BEYOND_END_OF_FILE_refuses_with_the_DECLARED_input_error_code(self):
        """The code is taken BY ROLE from the tool's own declared contract, never by
        number from a plan: it is the member whose role is BAD ARGUMENT."""
        path = self._write('f.events', self.WELL_FORMED)
        rc, text = self._run(path, '--at', '7', '--board')
        self.assertEqual(rc, board.EXIT_BAD_ARGUMENT)
        self.assertIn('the record holds 6 line(s)', text)
        self.assertIn('BAD ARGUMENT', text)

    def test_the_at_argument_refuses_shapes_that_are_not_line_numbers(self):
        path = self._write('g.events', self.WELL_FORMED)
        for bad in ('0', '-1', 'abc', '2026-03-01', '', '3.5'):
            rc, _ = self._run(path, '--at', bad, '--board')
            self.assertEqual(rc, board.EXIT_BAD_ARGUMENT, '--at %r was accepted' % bad)

    def test_the_anchor_argument_refuses_a_value_that_is_not_a_digest(self):
        path = self._write('h.events', self.WELL_FORMED)
        for bad in ('notadigest', '6', 'ABCDEF' * 10 + 'abcd', 'a' * 63):
            rc, _ = self._run(path, '--board', '--anchor', bad)
            self.assertEqual(rc, board.EXIT_BAD_ARGUMENT,
                             '--anchor %r was accepted' % bad)

    def test_a_BAD_at_is_an_INPUT_error_and_a_MOVED_SUBJECT_is_a_RECORD_refusal(self):
        """THE TWO CODES CARRY DIFFERENT FINDINGS AND A CALLER MUST BE ABLE TO TELL. A
        coordinate the record never had is the caller's problem; a coordinate that has
        stopped naming what it named is the record's."""
        self.assertNotEqual(board.EXIT_BAD_ARGUMENT, board.EXIT_REFUSED)
        path = self._write('i.events', self.WELL_FORMED)
        self.assertEqual(self._run(path, '--at', '99', '--board')[0],
                         board.EXIT_BAD_ARGUMENT)
        self.assertEqual(
            self._run(path, '--board', '--anchor', '0' * 64)[0],
            board.EXIT_REFUSED)

    def test_the_new_options_are_in_the_tools_own_help_text(self):
        out = io.StringIO()
        with unittest.mock.patch('sys.stdout', out):
            with self.assertRaises(SystemExit):
                board.main(['--events', _FIXTURE_EVENTS, '--help'])
        text = out.getvalue()
        self.assertIn('--at', text)
        self.assertIn('--anchor', text)
        self.assertIn(board.ANCHOR_ALGO, text)

    def test_the_standing_control_exercises_the_digest_every_invocation(self):
        ok, notes = board.positive_control()
        self.assertTrue(ok, notes)
        self.assertIn('anchor digest', ' '.join(notes))

    def test_RED_WORLD_a_digest_blind_to_content_fails_the_control(self):
        """Neutered at the digest: it becomes a function of the LINE COUNT alone, which is
        precisely the pre-fix §1a coordinate. The anchor still prints and still matches on
        an unchanged file, so nothing but the control catches this."""
        original = board.content_digest
        try:
            board.content_digest = lambda lines: '%064d' % len(lines)
            ok, notes = board.positive_control()
        finally:
            board.content_digest = original
        self.assertFalse(ok)
        self.assertIn('the content digest did not move', ' '.join(notes))


class TBoardDiscriminator(unittest.TestCase):
    """T-BOARD-DISCRIMINATOR [EP-28Y W2/W3] — `<date+verb>` is an ALIAS, and aliases collide.

    The verb above had its first real use on 2026-08-09 and it REFUSED: `2026-08-08
    PRE-FLIGHTED` names TWO events on `EP-28J`. Repeated pre-flights are this estate's
    normal gait, so the collision is the COMMON case. `BOARD-GRAMMAR.md` §1's discriminator
    ruling: the event's IDENTITY is its CONTENT, a line number is a ROLE, and a reference
    may carry `digest:<hex-prefix>` of the event line's own content digest.

    THE ROWS BELOW SPLIT INTO THE TWO HALVES THE RULING HAS, AND THE SECOND IS THE ONE
    THAT WAS NEARLY LOST. REQUIRED where the alias names two or more; VALIDATED ALWAYS
    when present, which is wider — the plan's first draft read "require it exactly when
    count > 1" as licence to IGNORE a carried digest at count 1, and the grammar's own
    words are "a required-but-absent, UNMATCHED, or twice-matched digest REFUSES THE FOLD
    WHOLE", with "unmatched" unqualified. `--ep` prints digests so seats COPY them, so a
    carried digest is the ordinary case and the ignored path would have been the taught
    one."""

    PAIR = (
        'EVT | 2026-03-01 | ITEM-A | HELD(on: a world) | mtr |',
        'EVT | 2026-03-01 | ITEM-A | OWED(by: mtr, act: a ruling) | mtr |',
    )
    FIRST = 'EVT | 2026-03-02 | ITEM-A | ACCEPTED | mtr | the first'
    SECOND = 'EVT | 2026-03-02 | ITEM-A | ACCEPTED | mtr | the second'
    ONLY = 'EVT | 2026-03-02 | ITEM-A | ACCEPTED | mtr |'

    def _fold(self, *body):
        return board.fold(board.read_event_lines(minimal(*body), '<fixture>')[0])

    def _resolve(self, reference):
        return ('EVT | 2026-03-04 | ITEM-A | DISAMBIGUATED(ending: %s, ended: HELD) '
                '| mtr |' % reference)

    def _ref(self, line, chars=None):
        prefix = board.digest_prefix(line)
        return '2026-03-02 ACCEPTED %s%s' % (board.DIGEST_FIELD,
                                             prefix if chars is None else prefix[:chars])

    @staticmethod
    def _twin_sharing(target, template, chars):
        """MINT a second line whose digest shares `chars` hex characters with `target`'s.

        A collision is not left to luck. Over five fixture lines a one-character prefix
        usually does NOT collide, and a row that only asserts a refusal when it happens to
        collide is a row that quietly stops testing — the vacuity this estate keeps
        finding. So the twin is SEARCHED FOR, and the caller asserts the share it got.
        """
        want = board.line_digest(target)[:chars]
        for n in range(1, 20000):
            line = '%s %d' % (template, n)
            if board.line_digest(line).startswith(want):
                return line
        raise AssertionError('no colliding twin found in 20000 tries')

    # ---- NON-VACUITY -----------------------------------------------------------------
    def test_NON_VACUITY_the_alias_really_does_name_TWO_events(self):
        """The collision must BE a collision before anything resolves it. `both resolved`
        and `nothing to resolve` are indistinguishable from the far end."""
        with self.assertRaises(board.BoardRefusal) as caught:
            self._fold(*(self.PAIR + (self.FIRST, self.SECOND,
                                      self._resolve('2026-03-02 ACCEPTED'))))
        self.assertIn('resolves to 2 earlier event(s)', caught.exception.reason)

    def test_NON_VACUITY_two_different_lines_have_two_different_digests(self):
        self.assertNotEqual(board.line_digest(self.FIRST), board.line_digest(self.SECOND))

    # ---- REQUIRED WHERE THE ALIAS IS AMBIGUOUS ----------------------------------------
    def test_a_required_but_ABSENT_discriminator_refuses_and_PRINTS_the_ones_to_copy(self):
        """The refusal is not a dead end: it names each candidate WITH its digest, so the
        seat's repair is a copy. The instrument that refuses tells you what to write."""
        with self.assertRaises(board.BoardRefusal) as caught:
            self._fold(*(self.PAIR + (self.FIRST, self.SECOND,
                                      self._resolve('2026-03-02 ACCEPTED'))))
        reason = caught.exception.reason
        self.assertIn('THE DISCRIMINATOR IS REQUIRED HERE', reason)
        self.assertIn(board.digest_prefix(self.FIRST), reason)
        self.assertIn(board.digest_prefix(self.SECOND), reason)

    def test_it_pins_BY_CONTENT_and_each_ending_resolves_by_ITS_OWN_digest(self):
        """THE DIFFERENTIAL, and it is the row that separates content-matching from
        first-match: the SAME log, folded twice, must resolve a DIFFERENT ending each
        time. A first-match implementation passes every single-digest row and fails this."""
        body = self.PAIR + (self.FIRST, self.SECOND)
        for line, other in ((self.FIRST, self.SECOND), (self.SECOND, self.FIRST)):
            item = self._fold(*(body + (self._resolve(self._ref(line)),)))['ITEM-A']
            pinned = [e for e in item.history if e.disambiguated_by is not None]
            self.assertEqual([e.clause for e in pinned], [line.split('| ')[-1].strip()],
                             'the digest of %r resolved the wrong ending' % line)
            self.assertNotIn(other.split('| ')[-1].strip(), [e.clause for e in pinned])

    def test_pinning_the_SECOND_leaves_the_FIRST_reported_ambiguous(self):
        """The two worlds must be DISTINGUISHABLE on the board, not only in the fold."""
        body = self.PAIR + (self.FIRST, self.SECOND)
        item = self._fold(*(body + (self._resolve(self._ref(self.SECOND)),)))['ITEM-A']
        self.assertEqual(len(item.ambiguous_endings), 1)
        self.assertEqual([p.kind for p in item.open_pendings()], ['OWED'])

    # ---- VALIDATED ALWAYS (the pre-flight repair) -------------------------------------
    def test_a_MATCHING_digest_on_an_UNAMBIGUOUS_reference_resolves_it(self):
        item = self._fold(*(self.PAIR + (self.ONLY,
                                         self._resolve(self._ref(self.ONLY)))))['ITEM-A']
        self.assertEqual([p.kind for p in item.open_pendings()], ['OWED'])

    def test_RED_WORLD_a_WRONG_digest_on_an_UNAMBIGUOUS_reference_REFUSES_WHOLE(self):
        """THE HALF THE PLAN NARROWED AND PRE-FLIGHT RESTORED. Count is 1, so the digest
        is not REQUIRED — and it is still CHECKED. A stale copied digest folding silently
        here would make the copy-never-compute discipline the unchecked path."""
        stale = board.digest_prefix('EVT | 2026-03-02 | ITEM-A | ACCEPTED | mtr | nowhere')
        with self.assertRaises(board.BoardRefusal) as caught:
            self._fold(*(self.PAIR + (self.ONLY,
                                      self._resolve('2026-03-02 ACCEPTED %s%s'
                                                    % (board.DIGEST_FIELD, stale)))))
        self.assertIn('matches NO event line', caught.exception.reason)

    def test_NON_VACUITY_that_stale_digest_really_does_match_nothing(self):
        stale = board.digest_prefix('EVT | 2026-03-02 | ITEM-A | ACCEPTED | mtr | nowhere')
        events, _ = board.read_event_lines(
            minimal(*(self.PAIR + (self.ONLY,))), '<fixture>')
        self.assertEqual([e.lineno for e in events if e.digest.startswith(stale)], [])

    # ---- TWICE-MATCHED ----------------------------------------------------------------
    def test_RED_WORLD_a_prefix_matching_TWO_lines_REFUSES_and_NAMES_the_collision(self):
        """Never longest-match, never first-match. A prefix too short to be unique has
        identified nothing, and lengthening it is the writer's act."""
        twin = self._twin_sharing(self.FIRST,
                                  'EVT | 2026-03-03 | ITEM-A | RULED | mtr | twin', 2)
        body = self.PAIR + (self.FIRST, self.SECOND, twin)
        events, _ = board.read_event_lines(minimal(*body), '<fixture>')
        share = board.line_digest(self.FIRST)[:2]
        shares = [e.lineno for e in events if e.digest.startswith(share)]
        self.assertEqual(len(shares), 2, 'NON-VACUITY: the minted twin did not collide')
        with self.assertRaises(board.BoardRefusal) as caught:
            self._fold(*(body + (self._resolve('2026-03-02 ACCEPTED %s%s'
                                               % (board.DIGEST_FIELD, share)),)))
        self.assertIn('matches 2 event lines', caught.exception.reason)
        self.assertIn('NEVER TAKES THE LONGEST MATCH', caught.exception.reason)

    def test_the_collision_is_matched_over_the_WHOLE_record_not_just_the_candidates(self):
        """An identity unique only inside one neighbourhood is not an identity. Here the
        alias names EXACTLY ONE candidate, so a candidate-scoped matcher would fold this
        happily — and the colliding line is on a DIFFERENT ITEM, where no candidate ever
        looks."""
        twin = self._twin_sharing(self.ONLY,
                                  'EVT | 2026-03-02 | ITEM-Z | ACCEPTED | mtr | elsewhere',
                                  2)
        body = self.PAIR + (self.ONLY, twin)
        events, _ = board.read_event_lines(minimal(*body), '<fixture>')
        share = board.line_digest(self.ONLY)[:2]
        self.assertEqual(len([e for e in events if e.digest.startswith(share)]), 2,
                         'NON-VACUITY: the minted twin did not collide')
        self.assertEqual(len([e for e in events if e.item == 'ITEM-A'
                              and e.kind == 'ACCEPTED']), 1,
                         'NON-VACUITY: the alias must name exactly ONE candidate here')
        with self.assertRaises(board.BoardRefusal) as caught:
            self._fold(*(body + (self._resolve('2026-03-02 ACCEPTED %s%s'
                                               % (board.DIGEST_FIELD, share)),)))
        self.assertIn('must match exactly', caught.exception.reason)

    # ---- THE ALIAS MUST AGREE, AND MUST BE THERE --------------------------------------
    def test_RED_WORLD_a_digest_the_ALIAS_does_not_name_refuses_whole(self):
        elsewhere = 'EVT | 2026-03-03 | ITEM-A | RULED | mtr |'
        with self.assertRaises(board.BoardRefusal) as caught:
            self._fold(*(self.PAIR + (self.ONLY, elsewhere,
                                      self._resolve('2026-03-02 ACCEPTED %s%s'
                                                    % (board.DIGEST_FIELD,
                                                       board.digest_prefix(elsewhere))))))
        self.assertIn('ALIAS AND THE DIGEST DISAGREE', caught.exception.reason)

    def test_a_LINE_NUMBER_may_RIDE_beside_the_alias_and_the_reference_still_folds(self):
        """`BOARD-GRAMMAR` §1: "a line number MAY ride beside it as the human-readable
        alias". IT ALREADY DID, through the tolerant reference match, and nothing claimed
        it — so this row exists to stop THIS pass from quietly taking away a form the
        grammar permits."""
        item = self._fold(*(self.PAIR + (self.ONLY,
                                         self._resolve('2026-03-02 ACCEPTED at line 6 %s%s'
                                                       % (board.DIGEST_FIELD,
                                                          board.digest_prefix(self.ONLY)))
                                         )))['ITEM-A']
        self.assertEqual([p.kind for p in item.open_pendings()], ['OWED'])

    def test_a_line_number_alias_rides_WITHOUT_a_digest_too_exactly_as_before(self):
        """C1's byte-for-byte half, made specific: the unambiguous path is untouched."""
        item = self._fold(*(self.PAIR + (self.ONLY,
                                         self._resolve('2026-03-02 ACCEPTED at line 6')
                                         )))['ITEM-A']
        self.assertEqual([p.kind for p in item.open_pendings()], ['OWED'])

    def test_a_discriminator_NEVER_BINDS_ALONE_without_an_alias_beside_it(self):
        with self.assertRaises(board.BoardRefusal) as caught:
            self._fold(*(self.PAIR + (self.ONLY,
                                      self._resolve('%s%s' % (board.DIGEST_FIELD,
                                                              board.digest_prefix(
                                                                  self.ONLY))))))
        self.assertIn('NEVER BINDS ALONE', caught.exception.reason)

    # ---- SHAPE: near misses refuse rather than going UNRECOGNISED ---------------------
    def test_NEAR_MISS_a_field_spelled_nearly_right_REFUSES_and_is_never_ignored(self):
        """An unrecognised field would ride on as trailing alias text and be IGNORED — a
        reference that LOOKS like it carries an identity and does not. Each of these is
        refused BY SHAPE, at parse time, before any matching happens."""
        for value, why in (('digest:', 'an empty value'),
                           ('digest:zzzz', 'not hex'),
                           ('digest:ABC123', 'upper case'),
                           ('Digest:abc123', 'the token capitalised'),
                           ('digest: abc123', 'a space after the token'),
                           ('digest:abc digest:def', 'two fields')):
            with self.assertRaises(board.BoardRefusal, msg=why):
                board.parse_event_line(
                    'EVT | 2026-03-02 | ITEM-A | DISAMBIGUATED(ending: 2026-03-01 '
                    'ACCEPTED %s, ended: HELD) | mtr |' % value, 1)

    def test_the_shape_refusal_lands_in_the_STANDING_near_miss_set(self):
        planted = ' '.join(text for text, _ in board.CONTROL_NEAR_MISSES)
        for token in ('digest:zzzz', 'digest:ABC123', 'Digest:abc123', 'digest: abc123'):
            self.assertIn(token, planted)

    def test_CORRECTED_gains_NOTHING_here_and_its_lossy_reference_still_only_REPORTS(self):
        """Explicitly NOT CLAIMED by EP-28Y, so it is pinned rather than left to drift:
        `CORRECTED`'s provenance reference is lossy BY RULING. A `digest:` in one is just
        text, and an unpinnable one is still a REPORT and never a refusal."""
        item = self._fold(
            'EVT | 2026-03-02 | ITEM-A | CORRECTED(supersedes: a phrase digest:zzzz) '
            '| mtr |')['ITEM-A']
        self.assertEqual(item.state.resolution, 'UNRESOLVED')

    # ---- W3: PRINT AND PARSE ARE ONE CONTRACT ----------------------------------------
    def test_the_item_history_EXHIBITS_a_digest_for_every_event(self):
        got = self._fold(*(self.PAIR + (self.ONLY,)))
        out = io.StringIO()
        with unittest.mock.patch('sys.stdout', out):
            board.print_item(got, 'ITEM-A')
        rows = [ln for ln in out.getvalue().splitlines() if ln.startswith('  :')]
        self.assertEqual(len(rows), 4)
        for line in rows:
            self.assertRegex(line, r'^  :\d+ +digest:[0-9a-f]{%d}  '
                             % board.EVENT_DIGEST_PREFIX_LEN)

    def test_ROUND_TRIP_a_digest_COPIED_out_of_the_output_folds_as_a_reference(self):
        """C3's whole content. The digest is lifted out of the PRINTED text by pattern —
        never recomputed here — and pasted into a reference. Print and parse are ONE
        contract, and a row that recomputed the value would not be testing the contract."""
        body = self.PAIR + (self.FIRST, self.SECOND)
        got = self._fold(*body)
        out = io.StringIO()
        with unittest.mock.patch('sys.stdout', out):
            board.print_item(got, 'ITEM-A')
        printed = [ln for ln in out.getvalue().splitlines()
                   if ln.startswith('  :') and '| the second' in ln]
        self.assertEqual(len(printed), 1)
        token = re.search(r'digest:[0-9a-f]+', printed[0]).group(0)
        item = self._fold(*(body + (self._resolve('2026-03-02 ACCEPTED %s' % token),
                                    )))['ITEM-A']
        pinned = [e for e in item.history if e.disambiguated_by is not None]
        self.assertEqual([e.clause for e in pinned], ['the second'])

    def test_the_printed_prefix_is_a_PREFIX_of_the_full_content_digest(self):
        self.assertTrue(board.line_digest(self.ONLY).startswith(
            board.digest_prefix(self.ONLY)))
        self.assertEqual(len(board.digest_prefix(self.ONLY)),
                         board.EVENT_DIGEST_PREFIX_LEN)

    def test_the_digest_is_the_ANCHORS_OWN_algorithm_and_not_a_second_one(self):
        """A second hash would be a second identity for one record. The event digest is
        `content_digest` over a one-line list, and this row proves it BY EQUALITY rather
        than by reading the source."""
        self.assertEqual(board.line_digest(self.ONLY), board.content_digest([self.ONLY]))

    def test_the_digest_subject_is_the_line_AS_THE_FOLD_READS_IT(self):
        """`read_event_lines` hands the parser a STRIPPED line, so outer whitespace is not
        in the subject — and every field change is. Stated as a CAP, and pinned."""
        self.assertEqual(board.line_digest('   %s  ' % self.ONLY),
                         board.line_digest(self.ONLY))
        self.assertNotEqual(board.line_digest(self.ONLY),
                            board.line_digest(self.ONLY.replace('mtr', 'archi')))

    def test_the_ep_help_text_tells_a_seat_the_column_is_for_COPYING(self):
        """`--events` is passed even to `--help`, which never reads it: T-BOARD-NO-LIVE-
        RECORD flags a `board.main()` whose argv does not NAME the option, and "argparse
        exits before the read" is exactly the reasoning that guard refuses to accept."""
        out = io.StringIO()
        with unittest.mock.patch('sys.stdout', out):
            with self.assertRaises(SystemExit):
                board.main(['--events', _FIXTURE_EVENTS, '--help'])
        self.assertIn('COPY it into a DISAMBIGUATED', out.getvalue())

    # ---- THE CONTROL ------------------------------------------------------------------
    def test_the_standing_control_exercises_the_discriminator_every_invocation(self):
        ok, notes = board.positive_control()
        self.assertTrue(ok, notes)
        self.assertIn('discriminator pinned BY CONTENT', ' '.join(notes))

    def test_RED_WORLD_a_FIRST_MATCH_resolver_fails_the_control(self):
        """Neutered PRECISELY at the discrimination, and named against the control it runs
        against: `_pin_by_digest` keeps every refusal it has — unmatched, twice-matched,
        alias disagreement — and returns THE FIRST CANDIDATE instead of the pinned event.
        Every single-digest world still passes. Only the two-world differential catches
        it, which is why the control folds the same log twice."""
        original = board._pin_by_digest

        def first_match(ev, ordered, candidates):
            original(ev, ordered, candidates)
            return candidates[0]

        try:
            board._pin_by_digest = first_match
            ok, notes = board.positive_control()
        finally:
            board._pin_by_digest = original
        self.assertFalse(ok, 'a first-match resolver passed the standing control')
        self.assertIn('did not pin BY CONTENT', ' '.join(notes))

    def test_RED_WORLD_a_discriminator_IGNORED_at_count_one_fails_the_control(self):
        """The narrowing itself, exhibited. `_pin_by_digest` is skipped wherever the alias
        already resolves to exactly one candidate — which is EXACTLY what the plan's first
        draft licensed, and it is invisible to every ambiguous-case row."""
        original = board._pin_by_digest

        def ignore_when_unambiguous(ev, ordered, candidates):
            if len(candidates) == 1:
                return candidates[0]
            return original(ev, ordered, candidates)

        try:
            board._pin_by_digest = ignore_when_unambiguous
            ok, notes = board.positive_control()
        finally:
            board._pin_by_digest = original
        self.assertFalse(ok, 'a digest ignored at count 1 passed the standing control')
        self.assertIn('VALIDATED ALWAYS FAILED', ' '.join(notes))


class TBoardAttribution(unittest.TestCase):
    """T-BOARD-ATTRIBUTION [EP-28ZB C1/C2] — the state word prints beside the STATE'S OWN
    seat and coordinate, and the printed cell is now INSIDE the record-plane invariant.

    THE DEFECT. `print_board` took its bracket from `last_event`, the latest event of ANY
    kind. A state word and a coordinate side by side read as ONE claim — that seat, on
    that line, produced that state — so a `NOTED` landing after a state attributed the
    state to an act that did not produce it. `print_item` already annotates the same event
    RECORD-PLANE, so the two planes were separated everywhere except the summary that
    pairs them.

    WHY THE OLD CONTROL COULD NOT SEE IT. `_state_signature` named the STATE and the OPEN
    PENDINGS and stopped. The coordinate cell sat outside the invariant, so the
    record-plane differential compared two boards that differed in the printed bracket and
    reported them identical. A cell no invariant covers drifts without anything reddening.

    ITEM 21 NON-VACUITY, and it bites harder here than usual: every row below asserts the
    fixture item HOLDS a state and that a record-plane event LANDS AFTER IT. An attribution
    row over an item whose last event is already its state passes no matter which of the
    two the code reads, and "the repair works" and "the two were never different" look
    identical from the other end."""

    STATE = 'EVT | 2026-03-01 | ITEM-A | HELD(on: a world) | statesat | the state'
    #: The two record-plane kinds that change NOTHING ELSE about the item, which is what
    #: makes them lawful subjects for a differential: any difference the signature reports
    #: between the two worlds is the coordinate and can be nothing else.
    AFTER = {
        'NOTED': 'EVT | 2026-03-02 | ITEM-A | NOTED | latersat | a plain addition',
        'SEATED': 'EVT | 2026-03-02 | ITEM-A | SEATED(kind: continuation) | latersat |',
    }
    #: `DISAMBIGUATED` IS THE THIRD RECORD-PLANE KIND AND IT GETS ITS OWN BODY, twice over.
    #: It must NAME a resolvable earlier ending or the fold refuses whole, so it cannot
    #: ride the shared shape above. AND IT IS DELIBERATELY KEPT OUT OF THE DIFFERENTIAL
    #: ROWS: removing it also drops an AMBIGUOUS-ENDING report, so a signature difference
    #: between the two worlds would not isolate the coordinate — the row would pass while
    #: measuring something else. It drives the PRINTED CELL only, where no such confound
    #: exists.
    DIS_BODY = (
        'EVT | 2026-03-01 | ITEM-A | HELD(on: a world) | seedsat | a pending',
        'EVT | 2026-03-01 | ITEM-A | OWED(by: mtr, act: a ruling) | seedsat | another',
        'EVT | 2026-03-01 | ITEM-A | ACCEPTED | statesat | the ending, ambiguous alone',
        'EVT | 2026-03-02 | ITEM-A | DISAMBIGUATED(ending: 2026-03-01 ACCEPTED, '
        'ended: HELD) | latersat | the retro-label',
    )

    def setUp(self):
        self.scratch = tempfile.mkdtemp(prefix='govos-board-attrib-')
        self.addCleanup(shutil.rmtree, self.scratch, True)

    def _fold(self, *body):
        return board.fold(board.read_event_lines(minimal(*body), '<fixture>')[0])

    def _board_line(self, folded, name):
        """The item's row from `print_board`, DRIVEN rather than reconstructed. The cell
        under repair is a formatting decision, so reading it from anywhere but the printer
        would test a copy of the claim instead of the claim."""
        out = io.StringIO()
        with unittest.mock.patch('sys.stdout', out):
            board.print_board(folded, {'path': '<fixture>', 'lines': 0, 'events': 0,
                                       'seed_start': 0, 'seed_end': 0})
        rows = [r for r in out.getvalue().splitlines() if r.startswith(name + ' ')]
        self.assertEqual(len(rows), 1, 'expected exactly one row for %s' % name)
        return rows[0]

    # ---- C1: where a state exists, its OWN coordinate prints ---------------------------

    def test_NON_VACUITY_the_record_plane_event_really_does_land_after_the_state(self):
        for kind, line in sorted(self.AFTER.items()):
            with self.subTest(kind=kind):
                item = self._fold(self.STATE, line)['ITEM-A']
                self.assertEqual(item.state.kind, 'HELD')
                self.assertEqual(item.last_event.kind, kind)
                self.assertIsNot(item.last_event, item.state,
                                 'the two coordinates are the same event, so this row '
                                 'could not tell the repair from the defect')
        dis = self._fold(*self.DIS_BODY)['ITEM-A']
        self.assertEqual(dis.state.kind, 'ACCEPTED')
        self.assertEqual(dis.last_event.kind, 'DISAMBIGUATED')
        self.assertIsNot(dis.last_event, dis.state)

    def test_the_printed_coordinate_is_the_STATES_OWN_for_every_record_plane_kind(self):
        for kind, line in sorted(self.AFTER.items()):
            with self.subTest(kind=kind):
                folded = self._fold(self.STATE, line)
                state = folded['ITEM-A'].state
                row = self._board_line(folded, 'ITEM-A')
                self.assertIn('[2026-03-01 statesat :%d]' % state.lineno, row)
                self.assertNotIn('latersat', row)
                self.assertNotIn('2026-03-02', row)
        folded = self._fold(*self.DIS_BODY)
        row = self._board_line(folded, 'ITEM-A')
        self.assertIn('[2026-03-01 statesat :%d]' % folded['ITEM-A'].state.lineno, row)
        self.assertNotIn('latersat', row)

    def test_the_STATE_WORD_itself_does_not_move_only_the_coordinate_does(self):
        """C3's property, driven on a fixture. This is an ATTRIBUTION repair: if the state
        word moved too, the fix would have moved the board."""
        for kind, line in sorted(self.AFTER.items()):
            with self.subTest(kind=kind):
                row = self._board_line(self._fold(self.STATE, line), 'ITEM-A')
                self.assertIn('HELD(on: a world)', row)
        self.assertIn('ACCEPTED', self._board_line(self._fold(*self.DIS_BODY), 'ITEM-A'))

    def test_the_OPEN_PENDINGS_cell_does_not_move_either(self):
        """The other half of C3's 'no state or pending changes'. Non-vacuous: the item
        holds an OPEN pending across the record-plane line."""
        for kind, line in sorted(self.AFTER.items()):
            with self.subTest(kind=kind):
                item = self._fold(self.STATE, line)['ITEM-A']
                self.assertEqual([p.kind for p in item.open_pendings()], ['HELD'])

    def test_an_item_whose_state_IS_its_last_event_is_untouched(self):
        """The common case, which is most of any real board. It must print exactly what it
        printed before — and the two readings agree here BY CONSTRUCTION, which is exactly
        why this row cannot stand in for the rows above."""
        folded = self._fold(self.STATE)
        item = folded['ITEM-A']
        self.assertIs(item.state, item.last_event)
        self.assertIn('[2026-03-01 statesat :%d]' % item.state.lineno,
                      self._board_line(folded, 'ITEM-A'))

    def test_THE_STATELESS_FALLBACK_STANDS_BYTE_FOR_BYTE(self):
        """C1's second half, and the reason the fallback was not 'cleaned up'. An item may
        carry record-plane history and NO state — the queued intake lines per
        `BOARD-EVENTS.log:247` are that shape — and the coordinate cell has always
        answered it. The repair must not reach this branch at all."""
        folded = self._fold('EVT | 2026-03-01 | NEW-ITEM | NOTED | latersat | the fact',
                            'EVT | 2026-03-02 | NEW-ITEM | NOTED | lastsat | and another')
        item = folded['NEW-ITEM']
        self.assertIsNone(item.state)
        self.assertIs(board._printed_attribution(item), item.last_event)
        row = self._board_line(folded, 'NEW-ITEM')
        self.assertIn('[2026-03-02 lastsat :%d]' % item.last_event.lineno, row)
        self.assertIn('NO STATE EVENT', row)

    def test_the_stateless_item_does_not_leave_with_the_interpreters_1(self):
        """The fault-case named in the code's own comment, driven through `main()` so the
        path a CALLER meets is the one under test."""
        with open(os.path.join(self.scratch, 'stateless.events'), 'w',
                  encoding='utf-8') as handle:
            handle.write('\n'.join(minimal(
                'EVT | 2026-03-01 | NEW-ITEM | NOTED | latersat | the fact')) + '\n')
        out = io.StringIO()
        with unittest.mock.patch('sys.stdout', out):
            code = board.main(['--events',
                               os.path.join(self.scratch, 'stateless.events'),
                               '--board'])
        self.assertEqual(code, 0)
        self.assertIn('NO STATE EVENT', out.getvalue())

    # ---- C2: the printed cell ENTERS the :1120 invariant -------------------------------

    def test_the_state_signature_CARRIES_the_printed_coordinate(self):
        item = self._fold(self.STATE, self.AFTER['NOTED'])['ITEM-A']
        sig = board._state_signature(item)
        self.assertEqual(len(sig), 4, 'the signature lost its fourth field')
        self.assertEqual(sig[3], (item.state.date, item.state.seat, item.state.lineno))

    def test_the_signature_AGREES_across_two_worlds_under_the_repaired_attribution(self):
        """The differential the standing control runs, in miniature: the same item with
        and without the record-plane line. Under the REPAIRED attribution the two agree —
        that is the property. The row below shows this same comparison CAN fail."""
        without = board._state_signature(self._fold(self.STATE)['ITEM-A'])
        for kind, line in sorted(self.AFTER.items()):
            with self.subTest(kind=kind):
                with_it = self._fold(self.STATE, line)['ITEM-A']
                self.assertEqual(board._state_signature(with_it), without)

    def test_THE_GUARD_CATCHES_THE_SHIPPED_DEFECT_driven_as_a_SYNTHETIC(self):
        """C2'S RED WORLD, AND THE ONLY HONEST WAY TO REACH IT. The behaviour being
        repaired stops existing the moment the repair lands, so it is driven as a
        SYNTHETIC attribution — the pre-repair rule, `last_event` — rather than by
        restoring it in the code, which would be the defect walking back in.

        A guard that reports silence under the repair is worth exactly what its ability to
        SPEAK under the defect is worth."""
        shipped = lambda it: it.last_event
        without = board._state_signature(self._fold(self.STATE)['ITEM-A'], shipped)
        for kind, line in sorted(self.AFTER.items()):
            with self.subTest(kind=kind):
                with_it = self._fold(self.STATE, line)['ITEM-A']
                self.assertNotEqual(board._state_signature(with_it, shipped), without,
                                    'the pre-repair attribution went UNCAUGHT')

    def test_the_standing_control_runs_the_synthetic_and_SAYS_it_caught_it(self):
        ok, notes = board.positive_control()
        self.assertTrue(ok, notes)
        self.assertIn('CAUGHT it at CTRL-NOTE', ' '.join(notes))

    def test_DROPPING_the_coordinate_from_the_signature_REDDENS_the_standing_control(self):
        """THE NEGATIVE RESULT ON THE CONTROL ITSELF. Without this row the arm above is a
        sentence with a colon in it: it asserts the control passes, and a control that
        cannot fail also passes. The fourth field is removed IN MEMORY ONLY and the
        standing control is required to go red and to name why."""
        original = board._state_signature

        def three_field(item, attribution=None):
            return original(item, attribution)[:3]

        try:
            board._state_signature = three_field
            ok, notes = board.positive_control()
        finally:
            board._state_signature = original
        self.assertFalse(ok, 'the control passed with the printed cell outside the '
                             'invariant, which is the pre-EP-28ZB world')
        self.assertIn('THE ATTRIBUTION GUARD DOES NOT CATCH THE DEFECT IT EXISTS FOR',
                      ' '.join(notes))
        self.assertTrue(board.positive_control()[0], 'the control did not restore')

    def test_BREAKING_the_attribution_function_REDDENS_the_standing_control(self):
        """The other direction, and it is the row that proves the repair is GUARDED rather
        than merely present. The row above breaks the GUARD; this breaks the SUBJECT —
        `_printed_attribution` put back to the pre-repair rule — and requires the standing
        control to catch it.

        IT IS CAUGHT BY THE RECORD-PLANE DIFFERENTIAL, one check EARLIER than the
        attribution arm, and that is the stronger result rather than a near miss: the
        differential is the estate's existing invariant, and the repair has brought the
        printed cell inside it. The message is asserted where it actually fires."""
        original = board._printed_attribution
        try:
            board._printed_attribution = lambda item: item.last_event
            ok, notes = board.positive_control()
        finally:
            board._printed_attribution = original
        self.assertFalse(ok, 'the pre-repair attribution passed the standing control')
        self.assertIn('CHANGED the board at CTRL-NOTE', ' '.join(notes))
        self.assertTrue(board.positive_control()[0], 'the control did not restore')


if __name__ == '__main__':
    unittest.main()
