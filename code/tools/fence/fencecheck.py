#!/usr/bin/env python3
"""fencecheck — refuse a close whose CHANGED SET names a file outside the unit's DECLARED fence.

Discharges board OWED `:1157` FENCE-IS-THE-FILE-NOT-THE-RANGE, under the closing
condition at `:1402` as amended by `:1403`.

THE TWO SIDES

  DECLARED   §5 of a plan file under `planning/exec/`. The section runs from a line
             beginning `# 5 ` to the next line beginning `# 6 `. EP-SHAPE.md line 31
             specifies §5's CONTENT ("the complete set of paths the builder may
             modify, exact") and NOT its FORM, so the indented block the live plans
             use is CONVENTION, NOT LAW. THIS PARSER THEREFORE REFUSES RATHER THAN
             GUESSES: no indented block, or a block whose lines do not look like
             paths, is a NAMED PARSE REFUSAL with its own exit code — never a
             silently empty declared set. An empty declared set would make every
             changed file a violation, which is a check that cannot pass, and this
             instrument exists to catch exactly that shape.

  CHANGED    COMMIT HISTORY over a COMMIT RANGE. Never `git diff`, never
             `git status`. Autosync commits every two minutes, so the working tree
             reads clean for every unit after two minutes — the tree is green by
             construction and cannot answer this question at all on this machine
             (`:1681` claim 3, walked into and caught by hand).
             The window is `<start-sha>..<end-sha>`, never a time string:
             `git log --since` reads LOCAL time while the estate records UTC, and a
             UTC figure returned 148 commits over a true window of 11 (`:1681`
             claim 4). Taking SHAs dissolves that trap rather than documenting it,
             and a time window passed here is REFUSED by name.

THE EXCLUSIONS ARE BY LITERAL NAME, NEVER BY PATTERN — EP-SHAPE's FENCE
DISCRIMINATION bracket. A pattern such as `planning/build/*` would silently swallow
a real violation elsewhere under `planning/build/`, and the positive control below
plants exactly that case so a pattern regression cannot pass quietly.

THE ANSWER IS A NAMED ROW, NEVER A COUNT (`:837`, the `:10` form). Every violation
prints its offending PATH.

EXIT CODES — parse failure and fence violation are DISTINCT outcomes:
    0  CONFORM             — no changed path outside the declared fence
    1  FENCE VIOLATION     — one or more named rows
    2  PARSE REFUSAL       — §5 could not be read as a declared set
    3  INPUT REFUSAL       — a time window, or a malformed range
    4  UNINTERPRETABLE     — the positive control FAILED; no verdict is offered
    5  ENVIRONMENT         — git unavailable, or the range does not resolve
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

# ---------------------------------------------------------------------------
# The exclusion list. THREE LITERAL NAMES. Not a pattern, not a prefix, not a glob.
# ---------------------------------------------------------------------------
LEDGER_DUTY = (
    'planning/build/BUILD-PROGRESS_v3.md',
    'planning/build/DISPATCH-LEDGER.md',
)
RECORD_PLANE = (
    'planning/build/BOARD-EVENTS.log',
)
EXCLUDED_BY_NAME = LEDGER_DUTY + RECORD_PLANE

EXIT_CONFORM = 0
EXIT_VIOLATION = 1
EXIT_PARSE_REFUSAL = 2
EXIT_INPUT_REFUSAL = 3
EXIT_UNINTERPRETABLE = 4
EXIT_ENVIRONMENT = 5

SEC5 = re.compile(r'^# 5 ')
SEC6 = re.compile(r'^# 6 ')
PATH_CHARS = re.compile(r'^[A-Za-z0-9._/+-]+$')
TIME_SHAPED = re.compile(r'\d{4}-\d{2}-\d{2}|\bago\b|\byesterday\b|\btoday\b|\d+\s*(day|hour|minute|week|month)')
TIME_FLAGS = ('--since', '--until', '--after', '--before', '--since-as-filter')

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures')


class Refusal(Exception):
    """A named refusal. Carries its own exit code so a caller cannot flatten two outcomes."""

    def __init__(self, code, reason):
        super().__init__(reason)
        self.code = code
        self.reason = reason


# ---------------------------------------------------------------------------
# DECLARED SIDE
# ---------------------------------------------------------------------------

def parse_declared(text, label='<plan>'):
    """§5 -> a list of declared paths, or a Refusal(EXIT_PARSE_REFUSAL) naming the failure.

    Refuses rather than guesses. Every refusal names the plan and the reason, because a
    parse failure reported as an empty set becomes a violation on every changed file, and
    a check whose failure mode looks like its finding is not a check.
    """
    lines = text.splitlines()
    starts = [i for i, ln in enumerate(lines) if SEC5.match(ln)]
    if not starts:
        raise Refusal(EXIT_PARSE_REFUSAL,
                      '%s — no line begins "# 5 "; §5 was not found' % label)
    if len(starts) > 1:
        raise Refusal(EXIT_PARSE_REFUSAL,
                      '%s — %d lines begin "# 5 " (lines %s); §5 is ambiguous'
                      % (label, len(starts), ', '.join(str(i + 1) for i in starts)))
    start = starts[0]
    ends = [i for i in range(start + 1, len(lines)) if SEC6.match(lines[i])]
    if not ends:
        raise Refusal(EXIT_PARSE_REFUSAL,
                      '%s — §5 opens at line %d and no line begins "# 6 "; the section '
                      'is unterminated and its extent is unknown' % (label, start + 1))
    body = lines[start + 1:ends[0]]

    # The FIRST contiguous run of indented (4+ space) non-blank lines, leading blanks skipped.
    runs, current = [], []
    for offset, raw in enumerate(body):
        indented = raw.strip() != '' and raw.startswith('    ')
        if indented:
            current.append((start + 2 + offset, raw.strip()))
        elif current:
            runs.append(current)
            current = []
    if current:
        runs.append(current)

    if not runs:
        raise Refusal(EXIT_PARSE_REFUSAL,
                      '%s — §5 yields NO indented block. EP-SHAPE line 31 specifies §5\'s '
                      'content and not its form, so this parser refuses rather than reading '
                      'the prose as paths' % label)
    if len(runs) > 1:
        where = '; '.join('lines %d-%d' % (r[0][0], r[-1][0]) for r in runs)
        raise Refusal(EXIT_PARSE_REFUSAL,
                      '%s — §5 yields %d separate indented blocks (%s); which one is the '
                      'declared set is a guess and this parser does not guess'
                      % (label, len(runs), where))

    declared, seen = [], set()
    for lineno, value in runs[0]:
        why = _not_a_path(value)
        if why:
            raise Refusal(EXIT_PARSE_REFUSAL,
                          '%s:%d — §5\'s indented block holds a line that does not look '
                          'like a path (%s): %r' % (label, lineno, why, value))
        if value in seen:
            raise Refusal(EXIT_PARSE_REFUSAL,
                          '%s:%d — §5 declares %r twice' % (label, lineno, value))
        seen.add(value)
        declared.append(value)
    return declared


def _not_a_path(value):
    """Why this string is not a path, or None. Stated as a reason so refusals are readable."""
    if ' ' in value or '\t' in value:
        return 'contains whitespace'
    if value[0] in '-*#>|`':
        return 'opens with a markdown marker %r' % value[0]
    if not PATH_CHARS.match(value):
        bad = sorted({c for c in value if not PATH_CHARS.match(c)})
        return 'holds characters outside a path charset: %s' % ' '.join(repr(c) for c in bad)
    if value.startswith('/'):
        return 'is absolute; §5 declares repo-relative paths'
    if value.endswith('/'):
        return None
    if '.' not in os.path.basename(value):
        return 'is neither a directory (no trailing "/") nor a file (no suffix)'
    return None


# ---------------------------------------------------------------------------
# CHANGED SIDE
# ---------------------------------------------------------------------------

def validate_range(rng, argv=None):
    """Refuse a time window BY NAME before git ever sees it."""
    for flag in (argv or []):
        for banned in TIME_FLAGS:
            if flag == banned or flag.startswith(banned + '='):
                raise Refusal(EXIT_INPUT_REFUSAL,
                              'REFUSED: %s is a TIME WINDOW. git log reads LOCAL time while '
                              'this estate records UTC; a UTC figure once returned 148 commits '
                              'over a true window of 11 (:1681 claim 4). Pass a commit range '
                              '<start-sha>..<end-sha> instead.' % banned)
    if rng is None:
        raise Refusal(EXIT_INPUT_REFUSAL, 'REFUSED: no --range given; the changed set has no window')
    if TIME_SHAPED.search(rng):
        raise Refusal(EXIT_INPUT_REFUSAL,
                      'REFUSED: --range %r is TIME-SHAPED. The window is a COMMIT RANGE, never '
                      'a time string — git log reads LOCAL time while this estate records UTC '
                      '(:1681 claim 4). Pass <start-sha>..<end-sha>.' % rng)
    if '..' not in rng:
        raise Refusal(EXIT_INPUT_REFUSAL,
                      'REFUSED: --range %r is not a commit range; expected <start-sha>..<end-sha>'
                      % rng)
    start, _, end = rng.partition('..')
    if not start:
        raise Refusal(EXIT_INPUT_REFUSAL,
                      'REFUSED: --range %r has no start commit' % rng)
    return start, (end or 'HEAD')


def _git(args, cwd):
    proc = subprocess.run(['git'] + args, cwd=cwd, capture_output=True, text=True)
    return proc


def resolve(rev, cwd):
    proc = _git(['rev-parse', '--verify', '%s^{commit}' % rev], cwd)
    if proc.returncode != 0:
        raise Refusal(EXIT_ENVIRONMENT,
                      'REFUSED: %r does not resolve to a commit in %s — %s'
                      % (rev, cwd, proc.stderr.strip()))
    return proc.stdout.strip()


def changed_paths(start, end, cwd):
    """The changed set, FROM COMMIT HISTORY. Never the working tree."""
    proc = _git(['log', '%s..%s' % (start, end), '--name-only', '--format='], cwd)
    if proc.returncode != 0:
        raise Refusal(EXIT_ENVIRONMENT,
                      'REFUSED: git log over %s..%s failed — %s' % (start, end, proc.stderr.strip()))
    return sorted({ln.strip() for ln in proc.stdout.splitlines() if ln.strip()})


# ---------------------------------------------------------------------------
# THE COMPARISON
# ---------------------------------------------------------------------------

def covers(changed, declared_entry):
    """Does one declared entry cover one changed path? Trailing "/" means directory."""
    if declared_entry.endswith('/'):
        return changed.startswith(declared_entry)
    return changed == declared_entry


def classify(changed_set, declared):
    """-> (violations, matched, excluded). violations are NAMED ROWS, never a count."""
    violations, matched, excluded = [], [], []
    for path in changed_set:
        if path in EXCLUDED_BY_NAME:
            excluded.append(path)
            continue
        hit = next((d for d in declared if covers(path, d)), None)
        if hit is None:
            violations.append(path)
        else:
            matched.append((path, hit))
    return violations, matched, excluded


def violation_rows(lines):
    """The NAMED ROWS printed under the violation banner — never rows from elsewhere.

    Written as its own function because the control was once asserting that a planted path
    appeared ANYWHERE in the output, which the `excluded:` listing satisfied. A membership
    test whose answer does not depend on WHERE the row is printed is a check that cannot
    fail, and this instrument exists to refuse exactly that shape.
    """
    rows, inside = [], False
    for ln in lines:
        if ln.startswith('FENCE VIOLATION'):
            inside = True
            continue
        if inside:
            if ln.startswith('    ') and ln.strip():
                rows.append(ln.strip())
            else:
                break
    return rows


def check(plan_path, start, end, cwd, plan_text=None):
    """-> (exit_code, lines, facts). Raises Refusal for parse/input/environment outcomes."""
    label = plan_path
    if plan_text is None:
        with open(plan_path, encoding='utf-8') as fh:
            plan_text = fh.read()
    declared = parse_declared(plan_text, label)
    start_sha, end_sha = resolve(start, cwd), resolve(end, cwd)
    changed = changed_paths(start_sha, end_sha, cwd)
    if not changed:
        # A CONFORM printed over an empty changed set is silence for the wrong reason, and it
        # is indistinguishable from a correct pass. That is `:1402`'s class exactly — a guard
        # whose failure looks like its success — and `:1681` claim 5's narrowing control is
        # the same observation from the other side. The window is refused, not passed.
        raise Refusal(EXIT_INPUT_REFUSAL,
                      'REFUSED: %s..%s names NO changed paths. A fence check over an empty '
                      'changed set CANNOT FAIL, so a CONFORM from it would carry no '
                      'information — re-take the window rather than read this as a pass.'
                      % (start_sha[:12], end_sha[:12]))
    violations, matched, excluded = classify(changed, declared)

    out = []
    out.append('PLAN            : %s' % label)
    out.append('WINDOW          : %s..%s   (COMMIT RANGE from history — never git diff,')
    out[-1] = out[-1] % (start_sha[:12], end_sha[:12])
    out.append('                  which is green by construction under two-minute autosync)')
    out.append('MATCH RULE      : a declared entry ending "/" covers every path beneath it;')
    out.append('                  a bare-file entry matches EXACTLY and covers nothing beneath')
    out.append('EXCLUDED BY NAME: (literal names, never a pattern — EP-SHAPE FENCE DISCRIMINATION)')
    for name in LEDGER_DUTY:
        out.append('                  %s   [ledger duty]' % name)
    for name in RECORD_PLANE:
        out.append('                  %s   [record plane]' % name)
    out.append('')
    out.append('DECLARED (§5)   : %d' % len(declared))
    for d in declared:
        out.append('    %s%s' % (d, '   [directory]' if d.endswith('/') else ''))
    out.append('CHANGED         : %d path(s) over the range' % len(changed))
    out.append('    inside fence : %d' % len(matched))
    for path, hit in matched:
        out.append('        %s   <- %s' % (path, hit))
    out.append('    excluded     : %d' % len(excluded))
    for path in excluded:
        out.append('        %s' % path)
    out.append('')
    facts = {'declared': declared, 'changed': changed, 'violations': violations,
             'matched': matched, 'excluded': excluded}
    if violations:
        out.append('FENCE VIOLATION — %d path(s) OUTSIDE the declared fence:' % len(violations))
        for path in violations:
            out.append('    %s' % path)
        out.append('THE CLOSE IS REFUSED.')
        return EXIT_VIOLATION, out, facts
    out.append('CONFORM — no changed path lies outside the declared fence.')
    if not matched:
        # A CONFORM in which NOT ONE declared member was touched is a pass the fence did no
        # work for. It is lawful — a window can hold only excluded names — but it is silence
        # for a different reason than a real pass, and the two must not read alike.
        out.append('    NOTE: NOT ONE declared member was touched in this window. The fence')
        out.append('    did no work for this pass — every changed path was an excluded name.')
        out.append('    Read this as "nothing to judge", never as "the unit stayed in bounds".')
    return EXIT_CONFORM, out, facts


# ---------------------------------------------------------------------------
# POSITIVE CONTROL — runs INSIDE the check, on EVERY invocation, BOTH DIRECTIONS
# ---------------------------------------------------------------------------

_PLAN_HEAD = '# 5 — FENCE — the complete set of paths the builder may modify\n\n'
_PLAN_TAIL = ('\n**THE LEDGER DUTY IS NOT A FENCE MEMBER** and is deliberately absent, per\n'
              "EP-SHAPE's FENCE DISCRIMINATION bracket.\n\n"
              '# 6 — MUST NOT TOUCH\n\nnothing\n')

_PLAN_GREEN = _PLAN_HEAD + (
    '    tests/test_fixture.py\n'
    '    planning/evidence/FIXTURE/\n'
    '    DOC-MAP_v3.md\n'
) + _PLAN_TAIL

_PLAN_NO_BLOCK = _PLAN_HEAD + (
    'The builder may modify the fixture test and its evidence directory.\n'
) + _PLAN_TAIL

_PLAN_NOT_PATHS = _PLAN_HEAD + (
    '    the fixture test and its evidence directory\n'
) + _PLAN_TAIL

_PLAN_UNTERMINATED = _PLAN_HEAD + '    tests/test_fixture.py\n\nprose and then nothing\n'

# The QUIET arm: every one of these is either a declared member or an excluded name.
_QUIET = [
    'tests/test_fixture.py',
    'planning/evidence/FIXTURE/run.md',
    'DOC-MAP_v3.md',
    'planning/build/BUILD-PROGRESS_v3.md',
    'planning/build/DISPATCH-LEDGER.md',
    'planning/build/BOARD-EVENTS.log',
]

# The LOUD arm: five NEAR-MISSES and one clean positive. Each row names why it is a near miss.
#
# `tests/test_fixture.py.bak` is the TRUE prefix near-miss and it was added only after the
# mutation harness proved the row below it caught nothing: `test_fixture_extra.py` does NOT
# start with `test_fixture.py`, so a bare-file entry mutated to match by PREFIX survived a
# control that claimed to be testing exactly that. The row that fails to discriminate is
# kept beside the one that does, because both are plausible authoring mistakes.
_LOUD = [
    ('tests/test_fixture.py.bak',
     'near-miss: STARTS WITH the declared BARE FILE tests/test_fixture.py — a bare entry '
     'matched by prefix instead of exactly would swallow this row'),
    ('tests/test_fixture_extra.py',
     'near-miss: one character-run off the declared bare file tests/test_fixture.py'),
    ('planning/evidence/FIXTURE-SIBLING/x.md',
     'near-miss: SIBLING of the declared directory; its prefix matches without the "/"'),
    ('planning/evidence/FIXTURE.md',
     'near-miss: shares the declared directory\'s prefix but is not a member of it'),
    ('planning/build/OTHER-NOTES.md',
     'near-miss: under planning/build/ but NOT one of the three excluded NAMES — a '
     'pattern exclusion would swallow this row silently'),
    ('src/kernel/engine.py',
     'clean positive: plainly outside'),
]


def _owned_fixture_dir(parent=FIXTURES):
    """An OWNED directory UNIQUE TO THIS INVOCATION. mkdtemp uses O_EXCL, so a name
    collision FAILS LOUDLY rather than handing two invocations one directory. A control
    clobbered mid-run certifies the instrument that just failed, which is worse than none."""
    os.makedirs(parent, exist_ok=True)
    return tempfile.mkdtemp(prefix='fencecheck-control-', dir=parent)


def _write(root, rel, body='x\n'):
    full = os.path.join(root, rel)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as fh:
        fh.write(body)


def _commit(repo, message):
    _git(['add', '-A'], repo)
    proc = _git(['-c', 'user.email=control@fencecheck', '-c', 'user.name=fencecheck control',
                 '-c', 'commit.gpgsign=false', 'commit', '-q', '-m', message], repo)
    if proc.returncode != 0:
        raise Refusal(EXIT_UNINTERPRETABLE, 'the control could not commit: %s' % proc.stderr.strip())
    return _git(['rev-parse', 'HEAD'], repo).stdout.strip()


def control():
    """Drive this instrument against fixtures whose answers are known FIRST. -> (ok, detail).

    BOTH DIRECTIONS. The check is required to REFUSE the wrong thing AND to STAY QUIET on
    the right one — a check that is merely loud is not a guard (:1403).
    """
    scratch = None
    try:
        scratch = _owned_fixture_dir()
        repo = os.path.join(scratch, 'repo')
        os.makedirs(repo)
        if _git(['init', '-q', '-b', 'main'], repo).returncode != 0:
            return False, 'the control could not init its own git repo'
        _write(repo, 'seed.txt')
        base = _commit(repo, 'base')

        plan = os.path.join(scratch, 'PLAN-GREEN.md')
        with open(plan, 'w', encoding='utf-8') as fh:
            fh.write(_PLAN_GREEN)

        # --- direction 1: STAY QUIET on the right thing -------------------------------
        for rel in _QUIET:
            _write(repo, rel, 'quiet\n')
        quiet_sha = _commit(repo, 'quiet arm')
        try:
            code, lines, facts = check(plan, base, quiet_sha, repo)
        except Refusal as exc:
            if exc.code == EXIT_INPUT_REFUSAL and 'NO changed paths' in exc.reason:
                return False, ('the QUIET arm judged 0 changed path(s) though it committed %d — '
                               'the CHANGED side is not reading COMMIT HISTORY. A working-tree '
                               'read is green by construction under two-minute autosync '
                               '(:1681 claim 3) and cannot answer this question at all'
                               % len(_QUIET))
            raise
        if code != EXIT_CONFORM:
            return False, ('the QUIET arm was REFUSED (exit %d) though every path in it is a '
                           'declared member or an excluded name — the check is loud, not a '
                           'guard: %s' % (code, ' | '.join(lines[-3:])))
        # A SILENT arm over an EMPTY changed set is silence for the wrong reason, and it is
        # precisely the git-diff-is-green-by-construction defect (:1681 claim 3) arriving
        # inside this instrument. The arm must be shown to have HAD something to judge.
        if len(facts['changed']) != len(_QUIET):
            return False, ('the QUIET arm judged %d changed path(s), not the %d it planted — '
                           'silence over an empty or partial changed set is a check that '
                           'cannot fail, which is the defect this instrument exists to catch'
                           % (len(facts['changed']), len(_QUIET)))
        if len(facts['matched']) != 3:
            return False, ('the QUIET arm matched %d declared member(s), not 3 — it went quiet '
                           'without the fence doing any work' % len(facts['matched']))
        if sorted(facts['excluded']) != sorted(EXCLUDED_BY_NAME):
            return False, ('the QUIET arm excluded %s, not the three names' % facts['excluded'])
        header = lines[:lines.index('')]
        for name, tag in ([(n, 'ledger duty') for n in LEDGER_DUTY] +
                          [(n, 'record plane') for n in RECORD_PLANE]):
            if not any(name in ln and tag in ln for ln in header):
                return False, ('the run HEADER does not print %s as [%s], so the exclusion '
                               'list is assumed by the reader rather than visible to them'
                               % (name, tag))

        if any('NOT ONE declared member' in ln for ln in lines):
            return False, ('the QUIET arm printed the did-no-work NOTE though it matched %d '
                           'declared members — the note fires when it should not'
                           % len(facts['matched']))

        # --- direction 1b: a CONFORM that did NO FENCE WORK must SAY SO ----------------
        for rel in EXCLUDED_BY_NAME:
            _write(repo, rel, 'ledger only\n')
        ledger_sha = _commit(repo, 'ledger-only arm')
        code, lines, facts = check(plan, quiet_sha, ledger_sha, repo)
        if code != EXIT_CONFORM:
            return False, ('the LEDGER-ONLY arm was refused (exit %d) though it touched only '
                           'the three excluded names' % code)
        if facts['matched']:
            return False, 'the LEDGER-ONLY arm matched a declared member it never wrote'
        if not any('NOT ONE declared member' in ln for ln in lines):
            return False, ('the LEDGER-ONLY arm printed a bare CONFORM without saying the '
                           'fence did no work — a pass over nothing reads identically to a '
                           'pass over something, which is :1402\'s class exactly')

        # --- direction 2: REFUSE the wrong thing, by NAMED ROW ------------------------
        for rel, _why in _LOUD:
            _write(repo, rel, 'loud\n')
        loud_sha = _commit(repo, 'loud arm')
        code, lines, facts = check(plan, ledger_sha, loud_sha, repo)
        if code != EXIT_VIOLATION:
            return False, ('the LOUD arm was NOT refused (exit %d) though it plants %d paths '
                           'outside the fence' % (code, len(_LOUD)))
        rows = violation_rows(lines)
        for rel, why in _LOUD:
            if rel not in rows:
                return False, ('the planted path %s was NOT reported as a NAMED ROW under the '
                               'violation banner (%s)' % (rel, why))
        if len(rows) != len(_LOUD):
            return False, ('the LOUD arm printed %d violation row(s), not the %d planted — a '
                           'row was swallowed or an extra was invented: %s'
                           % (len(rows), len(_LOUD), rows))
        leaked = [r for r in rows if r in _QUIET]
        if leaked:
            return False, 'a quiet-arm path leaked into the violation rows: %s' % leaked

        # --- direction 3: PARSE REFUSAL is a DISTINCT OUTCOME, not a violation --------
        if EXIT_PARSE_REFUSAL == EXIT_VIOLATION:
            return False, 'parse refusal and fence violation share an exit code'
        for name, text, want in (('no indented block', _PLAN_NO_BLOCK, 'NO indented block'),
                                 ('prose in the block', _PLAN_NOT_PATHS, 'does not look like a path'),
                                 ('unterminated §5', _PLAN_UNTERMINATED, 'unterminated')):
            bad = os.path.join(scratch, 'PLAN-%s.md' % name.replace(' ', '-'))
            with open(bad, 'w', encoding='utf-8') as fh:
                fh.write(text)
            try:
                code, _, _ = check(bad, base, loud_sha, repo)
            except Refusal as exc:
                if exc.code != EXIT_PARSE_REFUSAL:
                    return False, ('the %s fixture refused with exit %d, not the parse code %d'
                                   % (name, exc.code, EXIT_PARSE_REFUSAL))
                if want not in exc.reason:
                    return False, ('the %s fixture refused for the WRONG CLAUSE, so the red '
                                   'world proves nothing about this plant: %s' % (name, exc.reason))
            else:
                return False, ('the %s fixture was NOT refused (exit %d) — an unreadable §5 '
                               'silently became a declared set' % (name, code))

        # --- direction 4: a well-formed §5 that declares NOTHING is still a refusal ----
        empty = os.path.join(scratch, 'PLAN-EMPTY.md')
        with open(empty, 'w', encoding='utf-8') as fh:
            fh.write(_PLAN_HEAD + '\n' + _PLAN_TAIL.lstrip('\n'))
        try:
            check(empty, base, loud_sha, repo)
        except Refusal as exc:
            if exc.code != EXIT_PARSE_REFUSAL:
                return False, 'the empty-§5 fixture refused with exit %d' % exc.code
        else:
            return False, ('an EMPTY §5 produced a verdict — every changed file would read as a '
                           'violation, which is a check that cannot pass')

        # --- direction 5: an EMPTY WINDOW is refused, never passed ---------------------
        try:
            check(plan, base, base, repo)
        except Refusal as exc:
            if exc.code != EXIT_INPUT_REFUSAL:
                return False, 'the empty window refused with exit %d' % exc.code
            if 'CANNOT FAIL' not in exc.reason:
                return False, ('the empty window refused for the WRONG CLAUSE: %s' % exc.reason)
        else:
            return False, ('an EMPTY window produced a verdict — a fence check over zero '
                           'changed paths cannot fail, and a CONFORM from it is silence '
                           'mistaken for a pass')

        # --- direction 6: a TIME WINDOW is refused by name ----------------------------
        for bad_window in ('2026-08-19..2026-08-20', '10 hours ago', '--since'):
            try:
                if bad_window == '--since':
                    validate_range(base + '..' + loud_sha, argv=['--since=2026-08-19'])
                else:
                    validate_range(bad_window)
            except Refusal as exc:
                if exc.code != EXIT_INPUT_REFUSAL:
                    return False, 'time window %r refused with exit %d' % (bad_window, exc.code)
            else:
                return False, ('the time window %r was ACCEPTED — the local-vs-UTC trap at '
                               ':1681 claim 4 is open' % bad_window)

        # --- direction 7: the control's own scratch is unique per invocation ----------
        made = []
        try:
            for _ in range(3):
                made.append(_owned_fixture_dir())
            if len(set(made)) != 3:
                return False, 'a FIXED SHARED PATH was handed out twice'
            if any(os.path.dirname(p.rstrip(os.sep)) != FIXTURES.rstrip(os.sep) for p in made):
                return False, 'control scratch landed outside %s' % FIXTURES
        finally:
            for p in made:
                shutil.rmtree(p, ignore_errors=True)

        return True, ('QUIET arm SILENT over %d right paths it actually judged (3 declared '
                      'members MATCHED + the 3 excluded NAMES, each printed in the header with '
                      'its tag) — silence over an empty changed set is refused, and the '
                      'did-no-work NOTE stayed OFF; a LEDGER-ONLY arm CONFORMED but SAID the '
                      'fence did no work; LOUD arm '
                      'REFUSED with all %d planted paths as NAMED ROWS UNDER THE VIOLATION '
                      'BANNER and no others, including 5 NEAR-MISSES (a path PREFIXED BY a '
                      'declared bare file, a character-run off it, a SIBLING of a declared '
                      'directory, a PREFIX of one, and a planning/build/ file that is not one '
                      'of the three excluded NAMES — that row is the pattern-vs-name regression '
                      'detector); 3 unreadable §5 fixtures '
                      'and 1 empty §5 each REFUSED with exit %d FOR THEIR OWN CLAUSE, distinct '
                      'from the violation code %d; 3 time windows REFUSED with exit %d; '
                      '3 invocations, 3 distinct owned fixture directories, all removed'
                      % (len(_QUIET), len(_LOUD), EXIT_PARSE_REFUSAL, EXIT_VIOLATION,
                         EXIT_INPUT_REFUSAL))
    except Refusal as exc:
        return False, 'the control itself refused: %s' % exc.reason
    except OSError as exc:
        return False, 'the control could not create its own fixtures: %s' % exc
    finally:
        if scratch:
            shutil.rmtree(scratch, ignore_errors=True)


# ---------------------------------------------------------------------------

def repo_root(start=None):
    proc = _git(['rev-parse', '--show-toplevel'], start or os.path.dirname(os.path.abspath(__file__)))
    if proc.returncode != 0:
        raise Refusal(EXIT_ENVIRONMENT, 'not inside a git work tree')
    return proc.stdout.strip()


USAGE = """usage:
  fencecheck.py --plan <planning/exec/EP-XX.md> --range <start-sha>..[<end-sha>]
  fencecheck.py --parse-census <plan.md> [<plan.md> ...]
  fencecheck.py --control-only

The window is a COMMIT RANGE. A time window is REFUSED (exit 3).
Exit: 0 conform · 1 fence violation · 2 parse refusal · 3 input refusal ·
      4 control failed (UNINTERPRETABLE) · 5 environment"""


def main(argv):
    args = argv[1:]
    tail = []

    ok, detail = control()
    tail.append('')
    if ok:
        tail.append('positive control PASSED — %s' % detail)
    else:
        tail.append('positive control FAILED — %s' % detail)
        tail.append('a verdict from a checker whose control fails is not a verdict')

    def finish(code, lines):
        for ln in lines:
            print(ln)
        for ln in tail:
            print(ln)
        return EXIT_UNINTERPRETABLE if not ok else code

    if not args or args[0] in ('-h', '--help'):
        return finish(EXIT_INPUT_REFUSAL, [USAGE])

    try:
        root = repo_root()
        if args[0] == '--control-only':
            return finish(EXIT_CONFORM, ['CONTROL ONLY — no plan checked.'])

        if args[0] == '--parse-census':
            plans = args[1:]
            if not plans:
                raise Refusal(EXIT_INPUT_REFUSAL, 'REFUSED: --parse-census names no plan')
            lines = ['PARSE CENSUS — does §5 yield a declared set under this parser?', '']
            worst = EXIT_CONFORM
            for p in plans:
                full = p if os.path.isabs(p) else os.path.join(root, p)
                try:
                    with open(full, encoding='utf-8') as fh:
                        declared = parse_declared(fh.read(), p)
                except Refusal as exc:
                    lines.append('  REFUSED  %s' % p)
                    lines.append('           %s' % exc.reason)
                    worst = EXIT_PARSE_REFUSAL
                except OSError as exc:
                    lines.append('  REFUSED  %s — %s' % (p, exc))
                    worst = EXIT_PARSE_REFUSAL
                else:
                    lines.append('  CONFORM  %s — %d declared path(s)' % (p, len(declared)))
                    for d in declared:
                        lines.append('               %s%s' % (d, '   [directory]' if d.endswith('/') else ''))
            return finish(worst, lines)

        plan = rng = None
        i = 0
        while i < len(args):
            if args[i] == '--plan' and i + 1 < len(args):
                plan = args[i + 1]; i += 2
            elif args[i] == '--range' and i + 1 < len(args):
                rng = args[i + 1]; i += 2
            else:
                validate_range(rng, argv=[args[i]])
                raise Refusal(EXIT_INPUT_REFUSAL, 'REFUSED: unknown argument %r\n%s' % (args[i], USAGE))
        if plan is None:
            raise Refusal(EXIT_INPUT_REFUSAL, 'REFUSED: no --plan given\n%s' % USAGE)
        start, end = validate_range(rng, argv=args)
        full = plan if os.path.isabs(plan) else os.path.join(root, plan)
        code, lines, _ = check(full, start, end, root,
                               plan_text=open(full, encoding='utf-8').read())
        return finish(code, lines)
    except Refusal as exc:
        return finish(exc.code, [exc.reason])
    except OSError as exc:
        return finish(EXIT_ENVIRONMENT, ['REFUSED: %s' % exc])


if __name__ == '__main__':
    sys.exit(main(sys.argv))
