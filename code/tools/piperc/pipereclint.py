#!/usr/bin/env python3
"""pipereclint — name every place a shell script takes an exit status a PIPE CAN SWALLOW.

Discharges board OWED `:876` PIPE-SWALLOWED-RC under the closing condition at
`:1402` as amended by `:1403`, and under the shape ruled by finding `:1657`.

WHY A LINT AND NOT `set -o pipefail` IN THREE FILES

  `:1657` drove the mechanism in both directions and then went looking for the
  site and DID NOT FIND ONE: `arm.sh`, `arms.sh` and `run_arm.py` take their rcs
  directly after REDIRECTED commands, not piped ones. Applying pipefail there is
  a cure with nothing to cure — a green run wearing a repair. The OWED's own
  words offer "pipefail OR a lint on `$?` after a pipe", and the lint is the
  better half BECAUSE IT CHECKS THE PROPERTY OVER WHATEVER SCRIPTS EXIST rather
  than patching the three that exist today. The script set turns over faster
  than the duty does.

THE PROPERTY, stated so the code implements the property and not a pattern

  An exit status taken from a PIPELINE (two or more stages joined by `|` or
  `|&`) in a script that does NOT have `pipefail` in effect AT THAT POINT is the
  status of the LAST STAGE ONLY. A failing upstream stage is invisible.

  Three carriers take that status, and this lint separates them because they are
  not equally likely to be a defect:

    EXPLICIT-$?   `a | b` then `$?`. The OWED's literal shape. Someone wrote
                  code intending to read a status and got the wrong one.
    CAPTURE-RC    `V=$(a | b)` then `$?`. The pipeline is inside a command
                  substitution; the assignment's status IS the pipeline's, so
                  the swallow is identical and one level less visible.
    IMPLICIT-TEST `if a | b`, `while a | b`, `a | b && x`, `a | b || die`,
                  `! a | b`. No `$?` appears, but the status is TAKEN all the
                  same and swallowed all the same.

  PRIMARY  = EXPLICIT-$? + CAPTURE-RC. These drive the exit code.
  SECONDARY = IMPLICIT-TEST. Reported as named rows, counted separately, and
              NOT allowed to turn a run red on its own.

  The split is a decision this instrument's brief did not settle; it is made
  here so the lint can be CORRECT about the wider property without being LOUD
  about the common idiom. See §"DECIDED HERE" at the bottom of this docstring.

WHAT IS NOT A REPORT, AND WHY EACH ONE WOULD MAKE THE LINT LOUD RATHER THAN CORRECT

  * `$?` after a NON-piped command. Fine. Reporting it is noise.
  * `${PIPESTATUS[0]}` / `"${PIPESTATUS[@]}"` — an EXPLICIT correct read of a
    pipeline's stages. Reporting it would punish the cure.
  * `||` and `&&` are not pipes. `|&` IS one.
  * a `|` inside a quoted string (`awk -F' \\| '`), inside a comment, inside a
    `case` PATTERN (`A|B)`), or inside `(( x | y ))` is not a pipe.
  * a pipeline whose status nobody takes at all. Nothing was swallowed because
    nothing was read.
  * `set -e` is NOT a defence and is not treated as one. It does not make a
    pipeline's upstream failure visible.

  `pipefail` is tracked POSITIONALLY, not file-globally: `set -o pipefail` /
  `set -uo pipefail` / `set -euo pipefail` turn it ON for lines after it, and
  `set +o pipefail` turns it OFF again. Both directions are planted in the
  control.

EXIT CODES — an absence and a refusal are distinct outcomes
    0  CLEAN            — no PRIMARY rows in what was swept
    1  SWALLOW          — one or more PRIMARY rows, each printed with file:line
    2  INPUT REFUSAL    — nothing to sweep, or an unreadable target
    4  UNINTERPRETABLE  — the positive control FAILED; no verdict is offered

DECIDED HERE (not settled by the brief, stated so it can be overruled)
  1. IMPLICIT-TEST is reported but SECONDARY. The property covers it; the exit
     code does not, because `ps aux | grep -q x || fallback` is an idiom and a
     lint that reddens on it gets switched off, which is worse than silent.
  2. Heredoc BODIES are skipped entirely. `file-event.sh` carries PYTHON in one;
     linting it as shell would invent findings.
  3. `pipefail` in a `#!/bin/sh` script is reported as a NOTE, not a row: dash
     has no `pipefail`, so the defence may not exist at run time. A note names
     it without claiming a swallow this lint has not located.
"""

import os
import re
import shutil
import sys
import tempfile

EXIT_CLEAN = 0
EXIT_SWALLOW = 1
EXIT_INPUT_REFUSAL = 2
EXIT_UNINTERPRETABLE = 4

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures')

KIND_EXPLICIT = 'EXPLICIT-$?'
KIND_CAPTURE = 'CAPTURE-RC'
KIND_IMPLICIT = 'IMPLICIT-TEST'
PRIMARY_KINDS = (KIND_EXPLICIT, KIND_CAPTURE)

# Leading words that introduce a statement without being the command.
LEAD_KEYWORDS = ('if', 'elif', 'while', 'until', 'then', 'else', 'do', 'done',
                 'fi', 'esac', 'time', '!', '{', '}')
# Leading words that make the following pipeline's status a TEST.
COND_KEYWORDS = ('if', 'elif', 'while', 'until', '!')


class Refusal(Exception):
    def __init__(self, code, reason):
        super().__init__(reason)
        self.code = code
        self.reason = reason


class Row(object):
    __slots__ = ('path', 'line', 'kind', 'stages', 'detail', 'snippet')

    def __init__(self, path, line, kind, stages, detail, snippet):
        self.path = path
        self.line = line
        self.kind = kind
        self.stages = stages
        self.detail = detail
        self.snippet = snippet

    @property
    def primary(self):
        return self.kind in PRIMARY_KINDS

    def render(self):
        return '  %-4s %s:%d  %-13s %d-stage pipeline · %s\n         %s' % (
            'RC' if self.primary else '·', self.path, self.line, self.kind,
            self.stages, self.detail, self.snippet)


# ---------------------------------------------------------------------------
# LEXING — the whole difficulty of this instrument lives here.
# A `|` is a pipe only when it is a `|` the SHELL sees as a pipe.
# ---------------------------------------------------------------------------

def _quote_balance(text, state):
    """Carry quote state across source lines so a multi-line string is one unit.

    state is None, "'" or '"'. Returns the state at end of text."""
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if state == "'":
            if ch == "'":
                state = None
        elif state == '"':
            if ch == '\\':
                i += 1
            elif ch == '"':
                state = None
        else:
            if ch == '\\':
                i += 1
            elif ch in ('"', "'"):
                state = ch
            elif ch == '#' and (i == 0 or text[i - 1] in ' \t\n;&|('):
                # a comment runs to end of THIS source line only
                nl = text.find('\n', i)
                if nl < 0:
                    return state
                i = nl
        i += 1
    return state


HEREDOC = re.compile(r'<<-?\s*(?:(["\'])([A-Za-z_][A-Za-z0-9_]*)\1|([A-Za-z_][A-Za-z0-9_]*))')


def logical_lines(text):
    """-> [(lineno, text)]. Joins `\\` continuations and multi-line quotes.
    REMOVES heredoc bodies entirely (decision 2 in the module docstring)."""
    raw = text.split('\n')
    out = []
    i = 0
    while i < len(raw):
        start = i + 1
        buf = raw[i]
        i += 1
        # backslash continuation
        while buf.endswith('\\') and not buf.endswith('\\\\') and i < len(raw):
            buf = buf[:-1] + '\n' + raw[i]
            i += 1
        # unterminated quote -> keep eating source lines
        guard = 0
        while _quote_balance(buf, None) is not None and i < len(raw) and guard < 4000:
            buf = buf + '\n' + raw[i]
            i += 1
            guard += 1
        out.append((start, buf))
        # heredoc bodies: consume until each delimiter, contributing nothing
        masked_for_heredoc = _mask(buf, in_case=False, expect_pattern=False)[0]
        for m in HEREDOC.finditer(buf):
            if masked_for_heredoc[m.start()] != buf[m.start()]:
                continue  # the `<<` was itself quoted
            delim = m.group(2) or m.group(3)
            while i < len(raw) and raw[i].strip() != delim:
                i += 1
            if i < len(raw):
                i += 1  # the delimiter line itself
    return out


def _mask(text, in_case, expect_pattern):
    """-> (masked, pattern_end, subs)

    masked  : same length as text; every character the SHELL does not read as a
              top-level operator is replaced by a space, so operator-finding on
              `masked` cannot see a `|` in a string, a comment, a case pattern,
              a `$( )`, a backtick, a `(( ))` or a `[[ ]]`.
    pattern_end : index of the `)` closing a case pattern list, or None.
    subs    : [(start, end, inner)] for TOP-LEVEL `$( ... )` bodies — needed to
              see the pipeline inside `V=$(a | b)`.
    """
    n = len(text)
    masked = [' '] * n
    subs = []
    pattern_end = None
    q = None            # None | "'" | '"'
    paren = 0           # ( and $( depth
    dparen = 0          # (( )) depth
    dbrack = 0          # [[ ]] depth
    sub_starts = []
    i = 0
    while i < n:
        ch = text[i]
        two = text[i:i + 2]
        if q == "'":
            if ch == "'":
                q = None
            i += 1
            continue
        if q == '"':
            if ch == '\\':
                i += 2
                continue
            if ch == '"':
                q = None
            i += 1
            continue
        if ch == '\\':
            i += 2
            continue
        if ch in ('"', "'"):
            q = ch
            i += 1
            continue
        if ch == '#' and (i == 0 or text[i - 1] in ' \t\n;&|('):
            nl = text.find('\n', i)
            i = nl if nl >= 0 else n
            continue
        if two == '((':
            dparen += 1
            i += 2
            continue
        if two == '))' and dparen:
            dparen -= 1
            i += 2
            continue
        if two == '[[':
            dbrack += 1
            i += 2
            continue
        if two == ']]' and dbrack:
            dbrack -= 1
            i += 2
            continue
        if two == '$(' or (ch == '`'):
            if ch == '`':
                # backticks: find the closer, mask the body
                j = text.find('`', i + 1)
                j = n if j < 0 else j
                i = j + 1
                continue
            sub_starts.append(i + 2)
            paren += 1
            i += 2
            continue
        if ch == '(':
            paren += 1
            i += 1
            continue
        if ch == ')':
            if paren == 0:
                if in_case and expect_pattern and pattern_end is None:
                    pattern_end = i
            else:
                paren -= 1
                if sub_starts and paren == len(sub_starts) - 1:
                    s = sub_starts.pop()
                    subs.append((s, i, text[s:i]))
            i += 1
            continue
        if paren == 0 and dparen == 0 and dbrack == 0:
            masked[i] = ch
        i += 1
    out = ''.join(masked)
    if pattern_end is not None:
        out = ' ' * (pattern_end + 1) + out[pattern_end + 1:]
    return out, pattern_end, subs


OPS = (';;', '&&', '||', '|&', ';', '&', '|')


def _split_terms(text, masked):
    """Split a logical line into AND-OR TERMS on the masked operators, keeping the
    operator on each side. `|` and `|&` do NOT split — they join stages of ONE
    pipeline, which is the whole point.  -> [(start, end, op_before, op_after)]"""
    cuts = []
    i = 0
    n = len(masked)
    while i < n:
        if masked[i] == '\n':
            cuts.append((i, i + 1, '\n'))
            i += 1
            continue
        matched = None
        for op in OPS:
            if masked.startswith(op, i):
                matched = op
                break
        if matched is None:
            i += 1
            continue
        if matched in ('|', '|&'):
            # a pipe JOINS stages of one term; it never cuts one
            i += len(matched)
            continue
        if matched == '&' and i and masked[i - 1] in '><&':
            # `2>&1` / `>&2` — a redirection, not a background operator
            i += 1
            continue
        cuts.append((i, i + len(matched), matched))
        i += len(matched)
    terms = []
    pos = 0
    prev_op = None
    for s, e, op in cuts:
        terms.append((pos, s, prev_op, op))
        pos = e
        prev_op = op
    terms.append((pos, n, prev_op, None))
    return terms


def _stage_count(masked_slice):
    """How many pipeline stages does this term have? `||` is not a pipe.

    HONEST NOTE, from the mutation sweep: the `||` skip below is REDUNDANT in the
    current design, because `_split_terms` already CUT the line on `||` before
    this function ever sees it — the guard cannot be shown load-bearing by any
    mutation of itself alone. It is kept because the cut order in OPS is the thing
    actually holding `||` apart from `|`, and if that order is ever edited this
    guard is the second line of defence. It is documented rather than deleted so
    nobody later mistakes it for a proven control."""
    stages = 1
    i = 0
    n = len(masked_slice)
    while i < n:
        if masked_slice.startswith('||', i):
            i += 2
            continue
        if masked_slice[i] == '|':
            stages += 1
            i += 2 if masked_slice.startswith('|&', i) else 1
            continue
        i += 1
    return stages


SET_RE = re.compile(r'^\s*(set|shopt)\b(.*)$', re.S)
PIPESTATUS_RE = re.compile(r'\$\{?PIPESTATUS\b')
DOLLAR_Q_RE = re.compile(r'\$\?')
ASSIGN_SUB_RE = re.compile(r'^\s*(?:local\s+|declare\s+|export\s+|readonly\s+)?'
                           r'[A-Za-z_][A-Za-z0-9_]*=\$\(')


def _pipefail_delta(term_text):
    """-> True (on), False (off), or None (this statement says nothing about it)."""
    m = SET_RE.match(term_text)
    if not m or 'pipefail' not in m.group(2):
        return None
    toks = m.group(2).split()
    for idx, tok in enumerate(toks):
        if re.match(r'^[-+][A-Za-z]*o$', tok) and idx + 1 < len(toks) and toks[idx + 1] == 'pipefail':
            return tok[0] == '-'
    # `set -o pipefail` written as one token, or shopt forms
    if re.search(r'\+[A-Za-z]*o\s+pipefail', m.group(2)):
        return False
    return True


class Term(object):
    __slots__ = ('line', 'text', 'masked', 'stages', 'cond', 'capture',
                 'has_dollar_q', 'has_pipestatus', 'pipefail')

    def __init__(self, line, text, masked, stages, cond, capture):
        self.line = line
        self.text = text
        self.masked = masked
        self.stages = stages
        self.cond = cond
        self.capture = capture
        self.has_dollar_q = bool(DOLLAR_Q_RE.search(text))
        self.has_pipestatus = bool(PIPESTATUS_RE.search(text))
        self.pipefail = False


def parse(text):
    """-> ([Term], notes)   Terms in EXECUTION-FILE order, each carrying the
    pipefail state IN EFFECT AT ITS OWN POSITION."""
    notes = []
    terms = []
    pipefail = False
    in_case = 0
    expect_pattern = False
    for base, line in logical_lines(text):
        masked, pattern_end, subs = _mask(line, in_case > 0, expect_pattern)
        if pattern_end is not None:
            expect_pattern = False
        for s, e, op_before, op_after in _split_terms(line, masked):
            body = line[s:e]
            mbody = masked[s:e]
            if not body.strip():
                if op_after == ';;':
                    expect_pattern = True
                continue
            lineno = base + line.count('\n', 0, s)
            stripped = body.strip()
            words = stripped.split()
            head = words[0] if words else ''
            if head == 'case':
                in_case += 1
                expect_pattern = True
            elif head == 'esac' or stripped == 'esac':
                in_case = max(0, in_case - 1)
                expect_pattern = False

            delta = _pipefail_delta(stripped)

            cond = op_before in ('&&', '||') or op_after in ('&&', '||')
            lead = head
            k = 0
            while k < len(words) and words[k] in LEAD_KEYWORDS:
                if words[k] in COND_KEYWORDS:
                    cond = True
                k += 1
            lead = words[k] if k < len(words) else ''

            stages = _stage_count(mbody)
            capture = False
            if stages == 1:
                # `V=$(a | b)` — the pipeline is inside a top-level substitution
                for ss, se, inner in subs:
                    if s <= ss < e and ASSIGN_SUB_RE.match(stripped):
                        im, _, _ = _mask(inner, False, False)
                        inner_stages = _stage_count(im)
                        if inner_stages > 1:
                            stages = inner_stages
                            capture = True
                            break

            t = Term(lineno, stripped, mbody, stages, cond, capture)
            t.pipefail = pipefail
            terms.append(t)

            if delta is not None:
                pipefail = delta
            if op_after == ';;':
                expect_pattern = True
    return terms, notes


def analyze(path, text):
    """-> (rows, notes). The property, applied. Nothing here is a pattern match
    on a line; every row is a status TAKEN from a pipeline with pipefail off."""
    rows = []
    notes = []
    terms, extra = parse(text)
    notes.extend(extra)

    first = text.split('\n', 1)[0]
    if first.startswith('#!') and re.search(r'\b(sh|dash)\s*$', first) and 'pipefail' in text:
        notes.append('%s:1  NOTE — shebang is %r and the file sets pipefail. dash has no '
                     'pipefail; the defence may not exist at run time.' % (path, first.strip()))

    for idx, t in enumerate(terms):
        # (1) the status is TAKEN IMPLICITLY by this term being a test
        if t.stages > 1 and t.cond and not t.pipefail:
            rows.append(Row(path, t.line, KIND_IMPLICIT, t.stages,
                            'status consumed as a TEST (if/while/&&/||/!) with pipefail NOT '
                            'in effect — only the LAST stage can fail visibly',
                            _snip(t.text)))
        # (2) the status is TAKEN by a following `$?`
        if not t.has_dollar_q:
            continue
        if t.has_pipestatus:
            continue
        if idx == 0:
            continue
        prev = terms[idx - 1]
        if prev.stages < 2:
            continue
        if prev.pipefail:
            continue
        if prev.has_pipestatus:
            continue
        kind = KIND_CAPTURE if prev.capture else KIND_EXPLICIT
        if kind == KIND_CAPTURE:
            detail = ('`$?` reads a command substitution whose body is a pipeline; the '
                      'assignment carries the pipeline status and pipefail is NOT in effect')
        else:
            detail = ('`$?` reads the pipeline on the preceding statement and pipefail is '
                      'NOT in effect — a failing upstream stage is invisible')
        rows.append(Row(path, prev.line, kind, prev.stages, detail, _snip(prev.text)))
    rows.sort(key=lambda r: (r.path, r.line, r.kind))
    return rows, notes


def _snip(s, width=96):
    s = ' '.join(s.split())
    return s if len(s) <= width else s[:width - 1] + '…'


# ---------------------------------------------------------------------------
# POSITIVE CONTROL — INSIDE the check, on EVERY invocation, BOTH DIRECTIONS.
# A guard proven once can rot (:1402/:1403). Synthetic fixtures only; the
# control creates its own directory and removes nothing it did not create.
# ---------------------------------------------------------------------------

# THE LOUD ARM. Each entry: (line-marker, expected kind, why this MUST be reported).
_LOUD_SCRIPT = """\
#!/usr/bin/env bash
set -u
# L1 EXPLICIT: two stages, $? on the next line, pipefail never set
grep needle haystack.txt | wc -l
rc=$?
# L2 EXPLICIT: three stages
cat a.txt | sort | uniq -c
echo "rc was $?"
# L3 CAPTURE: the pipe lives inside the command substitution
VAL=$(cat a.txt | tail -1)
rc2=$?
# L4 IMPLICIT: pipeline as an if-condition
if cat a.txt | grep -q needle; then
  echo found
fi
# L5 IMPLICIT: pipeline on the left of ||
cat a.txt | grep -q needle || echo missing
# L6 EXPLICIT: |& is a pipe
make 2>&1 |& tee build.log
rc3=$?
set -o pipefail
# (quiet region — covered by the quiet arm, not asserted here)
cat a.txt | wc -l
rc4=$?
set +o pipefail
# L7 EXPLICIT: pipefail was turned back OFF, so this one swallows again
cat a.txt | wc -l
rc5=$?
"""

_LOUD_EXPECT = [
    (4, KIND_EXPLICIT, 'L1 two-stage pipeline, `$?` on the next line, pipefail never set'),
    (7, KIND_EXPLICIT, 'L2 three-stage pipeline read by `$?` inside a double-quoted string'),
    (10, KIND_CAPTURE, 'L3 the pipeline is INSIDE $( ), so the assignment carries its status'),
    (13, KIND_IMPLICIT, 'L4 pipeline consumed as an if-condition — status taken, no `$?`'),
    (17, KIND_IMPLICIT, 'L5 pipeline on the LEFT of `||` — status taken, no `$?`'),
    (19, KIND_EXPLICIT, 'L6 `|&` IS a pipe (bash 2>&1| shorthand) and must not be missed'),
    (27, KIND_EXPLICIT, 'L7 pipefail was turned back OFF by `set +o pipefail` — positional '
                        'tracking, not file-global, is what catches this'),
]

# THE QUIET ARM. Every one of these is a NEAR-MISS: it looks like the defect and is not.
#
# EVERY near-miss is written so that its `$?` sits in a REPORTING POSITION — the
# statement it reads is the one immediately before it. That is not decoration. A
# near-miss whose `$?` could never have produced a row is silent for the wrong
# reason, and its silence proves nothing about the rule it claims to test. The
# first draft of this fixture had exactly that defect in its case-pattern row:
# a mutation that deleted the case-pattern rule ENTIRELY still passed the control,
# because a `grep` stood between the pattern and the `$?`. `_QUIET_TWINS` below
# now proves the position of every one of them, so that failure cannot recur.
#
# Each near-miss uses its OWN filename (q1.txt, q2.txt, ...) so the twin harness
# can rewrite exactly one of them without ambiguity.
_QUIET_SCRIPT = """\
#!/usr/bin/env bash
set -u
# pipefail is deliberately NOT set at the top. Q2 turns it on for itself and off
# again, so every OTHER near-miss here runs with pipefail OFF and its silence is
# caused by the LEXING rule it names and never by a blanket defence.
# Q1 near-miss: `$?` after a NON-piped command. Reporting it makes the lint loud.
grep needle q1.txt > out.txt
rc=$?
# Q2 near-miss: a real pipeline, but pipefail IS in effect right here
set -o pipefail
cat q2.txt | wc -l
rc=$?
set +o pipefail
# Q3 near-miss: PIPESTATUS read BESIDE `$?` in one statement — the diagnostic idiom
cat q3.txt | wc -l
echo "rc=$? stages=${PIPESTATUS[*]}"
# Q4 near-miss: `${PIPESTATUS[0]}` is the EXPLICIT CORRECT read of a stage
cat q4.txt | wc -l
first=${PIPESTATUS[0]}
# Q5 near-miss: `||` is NOT a pipe
grep needle q5.txt || true
rc=$?
# Q6 near-miss: `&&` is NOT a pipe
grep needle q6.txt && true
rc=$?
# Q7 near-miss: the `|` is inside a SINGLE-quoted string
awk -F' \\| ' '{print $3}' q7.txt > out.txt
rc=$?
# Q8 near-miss: the `|` is inside a DOUBLE-quoted string
echo "left|right" > q8.txt
rc=$?
# Q9 near-miss: the `|` is in a TRAILING COMMENT on the very statement read
grep needle q9.txt > out.txt # cat a.txt | wc -l
rc=$?
# Q10 near-miss: `|` as case-pattern ALTERNATION on the very statement read
case "$V" in
  DISPATCHED|CLOSED|STOPPED|OWED)
    rc=$?
    ;;
esac
# Q11 near-miss: a NON-piped statement stands between the pipeline and the `$?`
cat q11.txt | wc -l
echo spacer
rc=$?
# Q12 near-miss: a pipeline whose status NOBODY takes — nothing was swallowed
cat q12.txt | wc -l
# Q13 near-miss: `|` as bitwise-or inside (( ))
(( MASK = 4 | 2 ))
rc=$?
# Q14 near-miss: a heredoc body carrying another language
python3 - <<'PY'
HEREDOC_BODY_MARKER = 1 | 2
PY
rc=$?
# Q15 near-miss: `set -e` is NOT a defence, and a NON-piped `$?` is still not a row
set -e
grep needle q15.txt > out.txt
rc=$?
"""

_QUIET_WHY = [
    'Q1  `$?` after a NON-piped command',
    'Q2  a real pipeline WITH `set -o pipefail` in effect right at it',
    'Q3  `${PIPESTATUS[*]}` read BESIDE `$?` in one statement — the diagnostic idiom',
    'Q4  `${PIPESTATUS[0]}` — the explicit correct read of a stage',
    'Q5  `||` is not a pipe',
    'Q6  `&&` is not a pipe',
    'Q7  a `|` inside a SINGLE-quoted string (`awk -F\' \\| \'`)',
    'Q8  a `|` inside a DOUBLE-quoted string',
    'Q9  a `|` inside a TRAILING COMMENT on the statement read',
    'Q10 a `|` as case-pattern ALTERNATION on the statement read',
    'Q11 a non-piped statement standing between the pipeline and the `$?`',
    'Q12 a pipeline whose status nobody takes',
    'Q13 a `|` as bitwise-or inside (( ))',
    'Q14 a `|` inside a HEREDOC body written in another language',
    'Q15 `set -e` present — not a defence, and not a row either',
]

# THE TWIN HARNESS — the answer to "is this near-miss silent for the RIGHT reason?"
#
# For each near-miss, ONE substitution turns the protected construct into a REAL
# pipeline read by the SAME `$?`. The lint must then REPORT it. If it does not,
# that near-miss was never in a reporting position and its silence in the quiet
# arm was free — a check that cannot fail. Each `old` must occur EXACTLY ONCE or
# the twin is stale and the control says so instead of silently no-op'ing.
_QUIET_TWINS = [
    ('Q1', 'grep needle q1.txt > out.txt', 'grep needle q1.txt | cat > out.txt'),
    ('Q3', 'echo "rc=$? stages=${PIPESTATUS[*]}"', 'echo "rc=$?"'),
    ('Q4', 'first=${PIPESTATUS[0]}', 'first=$?'),
    ('Q5', 'grep needle q5.txt || true', 'grep needle q5.txt | true'),
    ('Q6', 'grep needle q6.txt && true', 'grep needle q6.txt | true'),
    ('Q7', "awk -F' \\| ' '{print $3}' q7.txt > out.txt", "awk '{print $3}' q7.txt | cat > out.txt"),
    ('Q8', 'echo "left|right" > q8.txt', 'echo left | cat > q8.txt'),
    ('Q9', 'grep needle q9.txt > out.txt # cat a.txt | wc -l', 'grep needle q9.txt | wc -l'),
    ('Q10', 'DISPATCHED|CLOSED|STOPPED|OWED)\n    rc=$?',
            'DISPATCHED|CLOSED|STOPPED|OWED)\n    cat q10.txt | wc -l\n    rc=$?'),
    ('Q11', 'cat q11.txt | wc -l\necho spacer\nrc=$?', 'cat q11.txt | wc -l\nrc=$?'),
    ('Q12', 'cat q12.txt | wc -l\n', 'cat q12.txt | wc -l\nrc=$?\n'),
    ('Q13', '(( MASK = 4 | 2 ))', 'echo 4 | cat'),
    ('Q15', 'grep needle q15.txt > out.txt', 'grep needle q15.txt | cat > out.txt'),
]
# Q2 and Q14 are proved by their own directions below rather than by a twin:
# Q2's silence is caused by pipefail (direction 8 removes the pipefail line and
# requires the row to appear); Q14's is caused by heredoc-body removal, which is
# a STRUCTURAL fact asserted directly (direction 9) because no `$?` can be placed
# inside a heredoc body to test it from the outside.
_HEREDOC_MARKER = 'HEREDOC_BODY_MARKER'


def _owned_fixture_dir(parent=FIXTURES):
    """A directory UNIQUE TO THIS INVOCATION. mkdtemp uses O_EXCL, so a collision
    FAILS LOUDLY rather than handing two invocations one directory. A control
    clobbered mid-run certifies the instrument that just failed."""
    os.makedirs(parent, exist_ok=True)
    return tempfile.mkdtemp(prefix='pipereclint-control-', dir=parent)


def control():
    """Drive this lint against fixtures whose answers were known FIRST.

    BOTH DIRECTIONS: it must REFUSE the wrong thing AND STAY QUIET on the right
    one. A check that is merely loud is not a guard.  -> (ok, detail)"""
    scratch = None
    try:
        scratch = _owned_fixture_dir()
        loud_path = os.path.join(scratch, 'loud.sh')
        quiet_path = os.path.join(scratch, 'quiet.sh')
        with open(loud_path, 'w', encoding='utf-8') as fh:
            fh.write(_LOUD_SCRIPT)
        with open(quiet_path, 'w', encoding='utf-8') as fh:
            fh.write(_QUIET_SCRIPT)

        # --- direction 1: REFUSE the wrong thing, EXACTLY -----------------------
        rows, _ = analyze('loud.sh', _LOUD_SCRIPT)
        got = sorted((r.line, r.kind) for r in rows)
        want = sorted((ln, kind) for ln, kind, _ in _LOUD_EXPECT)
        if got != want:
            missing = [w for w in want if w not in got]
            extra = [g for g in got if g not in want]
            parts = []
            if missing:
                labels = {(ln, k): why for ln, k, why in _LOUD_EXPECT}
                parts.append('MISSED %s' % '; '.join('line %d %s (%s)' % (ln, k, labels[(ln, k)])
                                                     for ln, k in missing))
            if extra:
                parts.append('INVENTED %s' % '; '.join('line %d %s' % g for g in extra))
            return False, 'the LOUD arm did not match its known answer — ' + ' | '.join(parts)

        primaries = [r for r in rows if r.primary]
        if len(primaries) != 5:
            return False, ('the LOUD arm produced %d PRIMARY rows, not the 5 planted — the '
                           'primary/secondary split is not holding' % len(primaries))

        # --- direction 2: STAY QUIET on the right thing -------------------------
        qrows, _ = analyze('quiet.sh', _QUIET_SCRIPT)
        if qrows:
            return False, ('the QUIET arm reported %d row(s) over %d planted NEAR-MISSES — a '
                           'lint that is merely loud is not a guard. First offender: %s:%d %s'
                           % (len(qrows), len(_QUIET_WHY), qrows[0].path, qrows[0].line,
                              qrows[0].kind))

        # --- direction 3: the quiet arm must not be quiet BY ACCIDENT -----------
        # It must actually have parsed pipelines. If the lexer silently saw no
        # pipes at all, direction 2 would pass for the wrong reason — a check
        # that cannot fail. Assert the lexer FOUND the pipelines it then cleared.
        qterms, _ = parse(_QUIET_SCRIPT)
        piped = [t for t in qterms if t.stages > 1]
        if len(piped) < 5:
            return False, ('the QUIET arm is silent BY ACCIDENT: the lexer found only %d '
                           'pipeline(s) in a fixture that plants at least 5 real ones. '
                           'Silence from a parser that saw nothing is not a pass' % len(piped))
        if not any(t.pipefail for t in piped):
            return False, ('the QUIET arm never observed pipefail IN EFFECT on any pipeline, '
                           'so its silence cannot be attributed to the pipefail rule')

        # --- direction 4: the pipefail tracker must move BOTH ways --------------
        lterms, _ = parse(_LOUD_SCRIPT)
        seq = [t.pipefail for t in lterms]
        if not (False in seq and True in seq):
            return False, ('the pipefail tracker never took both values across the LOUD arm, '
                           'which plants `set -o pipefail` AND `set +o pipefail`')
        on_idx = seq.index(True)
        if True not in seq[on_idx:] or False not in seq[on_idx:]:
            return False, 'the pipefail tracker never went back OFF after `set +o pipefail`'

        # --- direction 5: a MUTATION must break the lint ------------------------
        # If deleting the pipe from the L1 fixture still yields the same rows, the
        # detector is not reading the pipe at all.
        mutated = _LOUD_SCRIPT.replace('grep needle haystack.txt | wc -l',
                                       'grep needle haystack.txt > wc.out', 1)
        mrows, _ = analyze('mutant.sh', mutated)
        if any(r.line == 4 for r in mrows):
            return False, ('MUTATION SURVIVED: removing the `|` from the L1 fixture left its '
                           'row standing, so the row is not caused by the pipe')

        # --- direction 6: EVERY near-miss is silent for the RIGHT reason ---------
        # The twin harness. Without this, a near-miss whose `$?` could never have
        # produced a row passes the quiet arm for free. That happened in the first
        # draft (the case-pattern row), and a mutation deleting the case-pattern
        # rule ENTIRELY survived the control. This direction is that repair.
        for label, old, new in _QUIET_TWINS:
            hits = _QUIET_SCRIPT.count(old)
            if hits != 1:
                return False, ('twin %s is STALE: its anchor occurs %d times in the quiet '
                               'fixture, not once, so the substitution is not the one it '
                               'names' % (label, hits))
            twin = _QUIET_SCRIPT.replace(old, new, 1)
            trows, _ = analyze('twin-%s.sh' % label, twin)
            if not trows:
                return False, ('twin %s reported NOTHING. Turning that near-miss into a REAL '
                               'pipeline read by the SAME `$?` must produce a row; it did not, '
                               'so the near-miss was never in a reporting position and its '
                               'silence in the quiet arm proves nothing about %s'
                               % (label, dict((w.split()[0], w) for w in _QUIET_WHY).get(label, label)))

        # --- direction 7: Q2's silence is caused by PIPEFAIL, not by luck --------
        pf_anchor = 'set -o pipefail\ncat q2.txt | wc -l'
        if _QUIET_SCRIPT.count(pf_anchor) != 1:
            return False, 'twin Q2 is STALE: its anchor does not occur exactly once'
        no_pf = _QUIET_SCRIPT.replace(pf_anchor, 'cat q2.txt | wc -l', 1)
        pfrows, _ = analyze('twin-Q2.sh', no_pf)
        if not any('q2.txt' in r.snippet and r.kind == KIND_EXPLICIT for r in pfrows):
            return False, ('twin Q2 reported nothing over q2.txt once its `set -o pipefail` was '
                           'removed. Q2\'s silence in the quiet arm is therefore NOT '
                           'attributable to pipefail')

        # --- direction 8: the heredoc BODY is removed, structurally --------------
        hterms, _ = parse(_QUIET_SCRIPT)
        if any(_HEREDOC_MARKER in t.text for t in hterms):
            return False, ('the heredoc BODY was parsed as shell — %s appeared as a statement. '
                           'file-event.sh carries PYTHON in a heredoc and linting it as shell '
                           'invents findings' % _HEREDOC_MARKER)
        if _HEREDOC_MARKER not in _QUIET_SCRIPT:
            return False, ('the heredoc direction is vacuous: the marker is not in the fixture '
                           'at all, so its absence from the terms proves nothing')

        # --- direction 9: owned scratch is unique per invocation -----------------
        made = []
        try:
            for _ in range(3):
                made.append(_owned_fixture_dir())
            if len(set(made)) != 3:
                return False, 'two control invocations were handed one fixture directory'
            if any(os.path.dirname(p.rstrip(os.sep)) != FIXTURES.rstrip(os.sep) for p in made):
                return False, 'control scratch landed outside %s' % FIXTURES
        finally:
            for p in made:
                shutil.rmtree(p, ignore_errors=True)

        return True, ('LOUD arm reported EXACTLY the %d planted rows and no others (%d PRIMARY '
                      '— 4 EXPLICIT-$? incl. a `|&` and one AFTER `set +o pipefail`, 1 '
                      'CAPTURE-RC inside $( ) — and 2 SECONDARY IMPLICIT-TEST); QUIET arm '
                      'SILENT over %d planted NEAR-MISSES [%s]; the quiet arm is NOT silent by '
                      'accident (the lexer found %d real pipelines there and cleared them, %d '
                      'of them by pipefail); the pipefail tracker went OFF->ON->OFF across the '
                      'loud arm; MUTATION CHECK — deleting the `|` from L1 removed its row, so '
                      'the row is caused by the pipe and not by the `$?`; TWIN HARNESS — each '
                      'of %d near-misses turned into a REAL pipeline read by the SAME `$?` DID '
                      'produce a row, so every one of them sits in a REPORTING POSITION and its '
                      'silence is caused by the rule it names; Q2 went LOUD over q2.txt when its '
                      '`set -o pipefail` line was removed, so its silence is pipefail\'s doing; '
                      'the heredoc BODY never appeared as a statement and the marker proving '
                      'that is present in the fixture; 3 invocations, 3 distinct owned fixture '
                      'directories under tools/piperc/fixtures/, all removed'
                      % (len(_LOUD_EXPECT), len(primaries), len(_QUIET_WHY),
                         '; '.join(_QUIET_WHY), len(piped),
                         sum(1 for t in piped if t.pipefail), len(_QUIET_TWINS)))
    except OSError as exc:
        return False, 'the control could not create its own fixtures: %s' % exc
    finally:
        if scratch:
            shutil.rmtree(scratch, ignore_errors=True)


# ---------------------------------------------------------------------------

SKIP_DIRS = ('.git', 'archive', 'reference', 'node_modules', '__pycache__')
SKIP_LITERAL = (os.path.join('tools', 'piperc', 'fixtures'),)


def collect(targets, root):
    """-> [(display, abspath)]. `tools/piperc/fixtures/` is excluded BY LITERAL
    NAME: it holds planted defects and reporting them would be the lint marking
    its own homework."""
    found = []
    for t in targets:
        full = t if os.path.isabs(t) else os.path.join(root, t)
        if os.path.isfile(full):
            found.append((t, full))
            continue
        if not os.path.isdir(full):
            raise Refusal(EXIT_INPUT_REFUSAL, 'REFUSED: not a file or directory: %s' % t)
        for dirpath, dirnames, filenames in os.walk(full):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            rel = os.path.relpath(dirpath, root)
            if any(rel == s or rel.startswith(s + os.sep) for s in SKIP_LITERAL):
                dirnames[:] = []
                continue
            for fn in sorted(filenames):
                if fn.endswith('.sh') or fn.endswith('.bash'):
                    ap = os.path.join(dirpath, fn)
                    found.append((os.path.relpath(ap, root), ap))
    seen = set()
    out = []
    for disp, ap in found:
        if ap in seen:
            continue
        seen.add(ap)
        out.append((disp, ap))
    return sorted(out)


USAGE = """usage:
  pipereclint.py <file.sh|dir> [<file.sh|dir> ...]
  pipereclint.py --control-only

Reports every exit status taken from a PIPELINE where `pipefail` is not in
effect at that point, as NAMED ROWS with file:line. `tools/piperc/fixtures/`
is excluded by literal name (it holds the control's planted defects).

Exit: 0 clean · 1 swallow (PRIMARY rows) · 2 input refusal ·
      4 control failed (UNINTERPRETABLE)"""


def repo_root():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(os.path.dirname(here))


def main(argv):
    args = argv[1:]
    tail = ['']
    ok, detail = control()
    if ok:
        tail.append('positive control PASSED — %s' % detail)
    else:
        tail.append('positive control FAILED — %s' % detail)
        tail.append('a verdict from a lint whose control fails is not a verdict')

    def finish(code, lines):
        for ln in lines:
            print(ln)
        for ln in tail:
            print(ln)
        return EXIT_UNINTERPRETABLE if not ok else code

    if args and args[0] in ('-h', '--help'):
        return finish(EXIT_INPUT_REFUSAL, [USAGE])
    if args and args[0] == '--control-only':
        return finish(EXIT_CLEAN, ['CONTROL ONLY — nothing swept.'])
    if not args:
        return finish(EXIT_INPUT_REFUSAL, ['REFUSED: no target named.', '', USAGE])

    root = repo_root()
    try:
        targets = collect(args, root)
    except Refusal as exc:
        return finish(exc.code, [exc.reason])
    if not targets:
        return finish(EXIT_INPUT_REFUSAL,
                      ['REFUSED: the named target(s) contain no .sh/.bash file — %s' % ', '.join(args),
                       'An empty sweep reported as CLEAN is a check that cannot fail.'])

    rows = []
    notes = []
    unreadable = []
    for disp, ap in targets:
        try:
            with open(ap, encoding='utf-8', errors='replace') as fh:
                text = fh.read()
        except OSError as exc:
            unreadable.append('%s — %s' % (disp, exc))
            continue
        r, n = analyze(disp, text)
        rows.extend(r)
        notes.extend(n)

    primary = [r for r in rows if r.primary]
    secondary = [r for r in rows if not r.primary]

    out = ['PIPE-RC LINT — an exit status taken from a pipeline with pipefail NOT in effect',
           'reads the LAST STAGE ONLY. board OWED :876, shape ruled by :1657.', '']
    out.append('SWEPT — %d shell file(s) MATCHING *.sh AND *.bash ONLY; every other '
               'carrier EXCLUDED, including shell inside a python string, a systemd '
               'unit, a Makefile recipe, a CI step, or an extensionless file:'
               % len(targets))
    for disp, _ in targets:
        out.append('    %s' % disp)
    if unreadable:
        out.append('')
        out.append('UNREADABLE — reported, never counted as clean:')
        for u in unreadable:
            out.append('    %s' % u)
    out.append('')

    if primary:
        out.append('PRIMARY — %d status(es) a pipe can swallow  [these set the exit code]'
                   % len(primary))
        for r in primary:
            out.append(r.render())
    else:
        out.append('PRIMARY — none IN *.sh AND *.bash, which is the only population this '
                   'answer covers. No `$?` and no `$( )` capture reads a pipeline with '
                   'pipefail off anywhere in the swept set. THIS IS NOT A STATEMENT ABOUT '
                   'THE TREE — carriers outside those two extensions were never examined, '
                   'and board :2018 owns the unlocated site among them.')
    out.append('')
    if secondary:
        out.append('SECONDARY — %d pipeline status(es) taken as a TEST  [reported, not red]'
                   % len(secondary))
        for r in secondary:
            out.append(r.render())
    else:
        out.append('SECONDARY — none.')
    if notes:
        out.append('')
        out.append('NOTES')
        for n in notes:
            out.append('    %s' % n)

    return finish(EXIT_SWALLOW if primary else EXIT_CLEAN, out)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
