# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture (a board append-gate that decides a cited line's void
# state from the fold's structured field, not from a substring of its clause prose).
# NON-GOAL: no offensive capability. Full declaration: SCOPE-STATEMENT.md.
"""C7-MAINT-BOARD-VOID-CHECK — the file-event void guard reads the fold's STRUCTURED
void state (board.py `voided_by`, printed as the mark `<- VOID, superseded by line N`
in the cited line's OWN column of --ep) and NOT a bare substring `VOID` over the whole
display row.

THE DEFECT (mgr :4266): the guard grepped the cited AUTHORISED-BY line's WHOLE --ep
display for the word `VOID`, CLAUSE prose included. So a LIVE line whose clause merely
MENTIONS another line as "void" read as void ITSELF, and a lawful cite of it was refused
— which turned a lawful DISPATCHED (citing the live countersign :4257, whose clause said
"the :4243 freeze ... VOID") into a NOTED.

Both worlds are EXHIBITED against a TEMP board copy — never the live BOARD-EVENTS.log.
The real `tools/board/file-event.sh` is invoked (not a copy of its logic), pointed at the
temp board via its BOARD_LOG override, so the gate that ships is the gate under test.

  A1  LIVE line whose CLAUSE says "void"  -> ALLOWED  (the false refusal is gone; this is
                                                       the exact case that used to red)
  A2  TRULY voided line (voided_by set)   -> REFUSED  (the guard STILL CAN fail: it must
                                                       keep refusing a real void)

RED WORLD for A1: revert the guard to `grep -q 'VOID'` over the whole row — A1 goes red
because the clause's "void" is read as a state again.
RED WORLD for A2: loosen the guard so it stops reading the fold's void mark — A2 goes red
because a genuinely voided authority is let through.
"""
import os
import subprocess
import tempfile
import unittest

# REPO resolved REPO-RELATIVE from this file, never a home path (RELEASE-4 round 2, board :4642 (6)):
# tests/ sits directly under the repo root, so the parent of this file's directory IS the root.
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir))
GATE = os.path.join(REPO, 'tools', 'board', 'file-event.sh')

SEED_OPEN = '# ==================== SEED BLOCK ===================='
SEED_SHUT = '# ================== END SEED BLOCK =================='

# A minimal board that folds green. Physical line numbers are what the gate cites
# (board.py `lineno` == physical file line, comments and seed included), so they are
# fixed here and named in the tests:
#   line 1  SEED_OPEN
#   line 2  LIVE-PROSE  AUTHORED   (seed)
#   line 3  TRUE-VOID   AUTHORED   (seed)
#   line 4  SEED_SHUT
#   line 5  LIVE-PROSE  RULED      <- A1 cites :5 ; its CLAUSE contains the word VOID
#   line 6  TRUE-VOID   RULED      <- A2 cites :6 ; a CORRECTED below voids it
#   line 7  TRUE-VOID   CORRECTED(supersedes: 2026-01-03 RULED)  -> sets :6.voided_by
LIVE_PROSE_RULED_LINE = 5
TRUE_VOID_RULED_LINE = 6

BOARD_LINES = [
    SEED_OPEN,
    'EVT | 2026-01-01 | LIVE-PROSE | AUTHORED | seat | the seed',
    'EVT | 2026-01-01 | TRUE-VOID | AUTHORED | seat | the seed',
    SEED_SHUT,
    ('EVT | 2026-01-02 | LIVE-PROSE | RULED | archi | COUNTERSIGNED, hash-bound: the '
     ':99 freeze abc123 VOID, refused :100 — this clause NAMES another line void, but '
     'THIS line stands and authorises the dispatch'),
    'EVT | 2026-01-03 | TRUE-VOID | RULED | archi | a ruling that a CORRECTED will supersede',
    ('EVT | 2026-01-04 | TRUE-VOID | CORRECTED(supersedes: 2026-01-03 RULED) | archi | '
     'this supersedes the RULED above and marks it VOID by the fold'),
]


@unittest.skipUnless(
    os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools/board/file-event.sh")),
    "SKIP PRIVATE-SOURCE: needs tools/board/file-event.sh (absent in the render)")
class TFileEventVoidGuard(unittest.TestCase):
    """T-FILE-EVENT-VOID-GUARD — the void guard reads the fold's structured void mark,
    not a clause substring, and it refuses a real void in BOTH directions."""

    def _temp_board(self, tmpdir):
        path = os.path.join(tmpdir, 'temp-board.events')
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(BOARD_LINES) + '\n')
        return path

    def _run_gate(self, board_path, tmpdir, citing_line):
        """Write the citing EVT line to a body file and run the REAL gate against the
        TEMP board via BOARD_LOG. Returns (returncode, stdout+stderr)."""
        body = os.path.join(tmpdir, 'body.evt')
        with open(body, 'w', encoding='utf-8') as fh:
            fh.write(citing_line + '\n')
        env = dict(os.environ, BOARD_LOG=board_path)
        proc = subprocess.run(['bash', GATE, body], env=env,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              text=True)
        return proc.returncode, proc.stdout

    def test_the_temp_board_folds_green_before_any_cite(self):
        """The plants are a valid board — otherwise a refusal below could be the board,
        not the guard. Fold it standalone first."""
        with tempfile.TemporaryDirectory() as tmp:
            board_path = self._temp_board(tmp)
            proc = subprocess.run(
                ['python3', os.path.join(REPO, 'tools', 'board', 'board.py'),
                 '--events', board_path, '--board'],
                cwd=REPO, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.assertEqual(proc.returncode, 0)

    def test_A1_a_live_line_whose_prose_says_void_is_allowed(self):
        """A LIVE RULED line whose clause contains the word 'void' (of another line) is
        NOT treated as void. A DISPATCHED citing it passes the void guard and FILES."""
        with tempfile.TemporaryDirectory() as tmp:
            board_path = self._temp_board(tmp)
            citing = ('EVT | 2026-01-05 | LIVE-PROSE | DISPATCHED | mgr | proceeding on '
                      'the live countersign AUTHORISED-BY: :%d' % LIVE_PROSE_RULED_LINE)
            rc, out = self._run_gate(board_path, tmp, citing)
            # The void guard must NOT fire on a line whose only 'void' is in its clause.
            self.assertNotIn('is marked VOID by the fold', out,
                             'void guard fired on a LIVE line — read clause prose as a '
                             'state (the :4266 defect). Output:\n' + out)
            self.assertNotEqual(rc, 11,
                                'exit 11 is the void refusal — must not fire for A1')
            # And the lawful dispatch now lands: the false refusal is gone end-to-end.
            self.assertIn('FILED', out,
                          'the lawful DISPATCHED should FILE once the false void '
                          'refusal is removed. Output:\n' + out)
            self.assertEqual(rc, 0, 'A1 should file cleanly. Output:\n' + out)

    def test_A2_a_truly_voided_line_is_still_refused(self):
        """A line the fold actually marks voided (voided_by set by the CORRECTED) is
        STILL refused as an AUTHORISED-BY. The guard can fail — it refuses a real void."""
        with tempfile.TemporaryDirectory() as tmp:
            board_path = self._temp_board(tmp)
            citing = ('EVT | 2026-01-06 | TRUE-VOID | DISPATCHED | mgr | proceeding on a '
                      'superseded ruling AUTHORISED-BY: :%d' % TRUE_VOID_RULED_LINE)
            rc, out = self._run_gate(board_path, tmp, citing)
            self.assertEqual(rc, 11,
                             'a cite of a truly-voided line must be refused with exit 11. '
                             'Output:\n' + out)
            self.assertIn('is marked VOID by the fold', out,
                          'the void refusal message must name the fold as the authority. '
                          'Output:\n' + out)
            # The temp board is untouched by a refusal (nothing appended past line 7).
            with open(board_path, encoding='utf-8') as fh:
                self.assertEqual(len(fh.read().rstrip('\n').split('\n')),
                                 len(BOARD_LINES),
                                 'a refused cite must not append to the board')

    def test_the_two_worlds_are_the_same_word_read_two_ways(self):
        """The discriminator: both cited lines' displays contain the token 'VOID'. Only
        A2's carries it in the fold's MARK column. This proves A1 and A2 are not just two
        arbitrary lines — they are the same substring resolved by column, which is the
        whole fix."""
        with tempfile.TemporaryDirectory() as tmp:
            board_path = self._temp_board(tmp)
            ep_live = subprocess.run(
                ['python3', os.path.join(REPO, 'tools', 'board', 'board.py'),
                 '--events', board_path, '--ep', 'LIVE-PROSE'],
                cwd=REPO, stdout=subprocess.PIPE, text=True).stdout
            ep_void = subprocess.run(
                ['python3', os.path.join(REPO, 'tools', 'board', 'board.py'),
                 '--events', board_path, '--ep', 'TRUE-VOID'],
                cwd=REPO, stdout=subprocess.PIPE, text=True).stdout
            # Both displays contain the bare word VOID (the old grep matched both) ...
            self.assertIn('VOID', ep_live)
            self.assertIn('VOID', ep_void)
            # ... but ONLY the truly-voided line carries the fold's structured mark.
            self.assertNotIn('<- VOID, superseded by line', ep_live,
                             'LIVE line must NOT carry the fold void mark')
            self.assertIn('<- VOID, superseded by line', ep_void,
                          'the voided line MUST carry the fold void mark')


if __name__ == '__main__':
    unittest.main()
