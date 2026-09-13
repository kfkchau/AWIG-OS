#!/usr/bin/env python3
"""control_mutations — prove `fencecheck.py`'s positive control CAN FAIL.

A control that has only ever passed is a check that cannot fail, which is this estate's
signature defect (`:1402`: A GUARD WHOSE FAILURE LOOKS EXACTLY LIKE ITS SUCCESS IS NOT A
GUARD). `fencecheck.py --control-only` prints `positive control PASSED` on every run; this
harness asks the question that line cannot answer by itself — WOULD IT SAY ANYTHING ELSE?

METHOD. Copy `fencecheck.py` into an owned throwaway directory, apply ONE named mutation
by literal string replacement, run the COPY's own `--control-only`, and REQUIRE:
    exit code 4 (UNINTERPRETABLE) and the line `positive control FAILED`.
Each mutation is a defect a future hand could plausibly introduce, and each is required to
fail FOR ITS OWN CLAUSE — a mutation that fails for the wrong reason proves nothing about
the mutation, only that something broke.

The live `fencecheck.py` is never modified. Copies are created under
`tools/fence/fixtures/` and removed by their creator.

Exit: 0 every mutation was caught for its own clause · 1 a mutation SURVIVED or was
      caught for the wrong clause · 2 the harness could not run.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, 'fencecheck.py')
FIXTURES = os.path.join(HERE, 'fixtures')

# (name, find, replace, the clause the control must name when it fails)
MUTATIONS = [
    ('EXCLUSION BECOMES A PATTERN',
     "        if path in EXCLUDED_BY_NAME:",
     "        if path.startswith('planning/build/'):",
     'planning/build/OTHER-NOTES.md'),

    ('BARE-FILE ENTRY MATCHES BY PREFIX',
     "    return changed == declared_entry",
     "    return changed.startswith(declared_entry)",
     'tests/test_fixture.py.bak'),

    ('UNREADABLE §5 RETURNS AN EMPTY SET INSTEAD OF REFUSING',
     "        raise Refusal(EXIT_PARSE_REFUSAL,\n"
     "                      '%s — §5 yields NO indented block.",
     "        return []  # MUTANT\n"
     "        raise Refusal(EXIT_PARSE_REFUSAL,\n"
     "                      '%s — §5 yields NO indented block.",
     'was NOT refused'),

    ('CHANGED SET TAKEN FROM THE WORKING TREE, NOT COMMIT HISTORY',
     "    proc = _git(['log', '%s..%s' % (start, end), '--name-only', '--format='], cwd)",
     "    proc = _git(['diff', '--name-only'], cwd)",
     'not reading COMMIT HISTORY'),

    ('THE TIME-WINDOW GUARD IS REMOVED',
     "    if TIME_SHAPED.search(rng):",
     "    if False:",
     'was ACCEPTED'),

    ('THE ANSWER BECOMES A COUNT INSTEAD OF NAMED ROWS',
     "        for path in violations:\n            out.append('    %s' % path)",
     "        out.append('    (%d rows)' % len(violations))",
     'NOT reported as a NAMED ROW'),

    ('VIOLATION ROWS READ FROM ANYWHERE IN THE OUTPUT, NOT THE VIOLATION SECTION',
     "    rows, inside = [], False",
     "    return [ln.strip() for ln in lines if ln.startswith('    ') and ln.strip()]\n"
     "    rows, inside = [], False",
     'violation row(s), not the 6 planted'),

    ('AN EMPTY CHANGED SET READS AS CONFORM INSTEAD OF REFUSING',
     "    if not changed:",
     "    if False:",
     'EMPTY window produced a verdict'),

    ('A CONFORM THAT DID NO FENCE WORK STOPS SAYING SO',
     "    if not matched:",
     "    if False:",
     'bare CONFORM without saying the fence did no work'),

    ('THE DID-NO-WORK NOTE FIRES ON EVERY CONFORM',
     "    if not matched:",
     "    if True:",
     'printed the did-no-work NOTE though it matched'),

    ('PARSE REFUSAL AND FENCE VIOLATION SHARE AN EXIT CODE',
     "EXIT_PARSE_REFUSAL = 2",
     "EXIT_PARSE_REFUSAL = 1",
     'share an exit code'),

    ('THE QUIET ARM STOPS PRINTING THE EXCLUSION LIST',
     "    for name in RECORD_PLANE:\n        out.append('                  %s   [record plane]' % name)",
     "    pass",
     'HEADER does not print planning/build/BOARD-EVENTS.log'),
]


def run_mutant(name, find, replace, clause, source_text):
    scratch = tempfile.mkdtemp(prefix='fencecheck-mutant-', dir=FIXTURES)
    try:
        if source_text.count(find) != 1:
            return False, ('the mutation anchor appears %d times, not once — the harness is '
                           'stale against fencecheck.py' % source_text.count(find))
        mutant_path = os.path.join(scratch, 'fencecheck.py')
        with open(mutant_path, 'w', encoding='utf-8') as fh:
            fh.write(source_text.replace(find, replace))
        proc = subprocess.run([sys.executable, mutant_path, '--control-only'],
                              capture_output=True, text=True, cwd=HERE)
        out = proc.stdout + proc.stderr
        if 'positive control FAILED' not in out:
            return False, ('the mutant SURVIVED — its control still passed. exit=%d\n        %s'
                           % (proc.returncode, out.strip().splitlines()[-1][:200] if out.strip() else '(no output)'))
        if proc.returncode != 4:
            return False, ('the mutant\'s control failed but the tool exited %d, not 4 '
                           '(UNINTERPRETABLE) — a failed control did not suppress the verdict'
                           % proc.returncode)
        detail = next((ln for ln in out.splitlines() if 'positive control FAILED' in ln), '')
        if clause not in detail:
            return False, ('the mutant was caught for the WRONG CLAUSE, so this red world '
                           'proves nothing about this mutation.\n        wanted: %s\n'
                           '        got   : %s' % (clause, detail.strip()[:240]))
        return True, detail.split('positive control FAILED — ')[-1].strip()[:150]
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def main():
    if not os.path.exists(SOURCE):
        print('REFUSED: %s not found' % SOURCE)
        return 2
    os.makedirs(FIXTURES, exist_ok=True)
    with open(SOURCE, encoding='utf-8') as fh:
        source_text = fh.read()

    print('MUTATION HARNESS — can fencecheck.py\'s positive control FAIL?')
    print('subject: %s' % SOURCE)
    print('required of every mutant: exit 4 AND "positive control FAILED" naming its own clause')
    print()

    # BASELINE: the UNMUTATED copy must PASS, or a mutant's failure means nothing.
    baseline = tempfile.mkdtemp(prefix='fencecheck-baseline-', dir=FIXTURES)
    try:
        base_path = os.path.join(baseline, 'fencecheck.py')
        shutil.copyfile(SOURCE, base_path)
        proc = subprocess.run([sys.executable, base_path, '--control-only'],
                              capture_output=True, text=True, cwd=HERE)
        if proc.returncode != 0 or 'positive control PASSED' not in proc.stdout:
            print('  BASELINE FAILED — the UNMUTATED copy does not pass its own control '
                  '(exit %d). Every mutant below would be uninterpretable.' % proc.returncode)
            print(proc.stdout[-800:])
            return 1
        print('  BASELINE   unmutated copy PASSES its own control (exit 0)')
    finally:
        shutil.rmtree(baseline, ignore_errors=True)
    print()

    survived = 0
    for name, find, replace, clause in MUTATIONS:
        ok, detail = run_mutant(name, find, replace, clause, source_text)
        print('  %-8s %s' % ('CAUGHT' if ok else 'ESCAPED', name))
        print('           %s' % detail)
        if not ok:
            survived += 1
    print()
    if survived:
        print('MUTATION HARNESS FAILED — %d of %d mutation(s) survived or misfired.'
              % (survived, len(MUTATIONS)))
        return 1
    print('MUTATION HARNESS PASSED — all %d mutations CAUGHT, each for its own clause, and '
          'the unmutated baseline passes.' % len(MUTATIONS))
    print('THE HONEST CAP: a control shown to fail for %d reasons has been shown capable of '
          'failing for %d reasons. It is a floor, not a proof.'
          % (len(MUTATIONS), len(MUTATIONS)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
