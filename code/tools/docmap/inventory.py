#!/usr/bin/env python3
"""Mechanical document inventory for gov-os.

Reads every markdown file's own `<!-- doc: class=X status=Y ... -->` header and
reports the estate's true state. Nothing here is maintained by hand: the headers
are the record and this is a fold over them.

Usage:
    python3 tools/docmap/inventory.py            # the full table
    python3 tools/docmap/inventory.py --defects  # only what is wrong
    python3 tools/docmap/inventory.py --map      # emit DOC-MAP body (markdown)
"""
import os, re, sys, subprocess, tempfile, shutil

# Loaded BY PATH rather than by name, and `sys.path` is left alone: this module is a
# sibling script, and putting its directory on the import path of whatever process imports
# this one is an instrument reaching outside itself.
import importlib.util as _ilu
_spec = _ilu.spec_from_file_location(
    'govos_docmap_checkvocab',
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'checkvocab.py'))
checkvocab = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(checkvocab)

_board_spec = _ilu.spec_from_file_location(
    'govos_docmap_boardtool',
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 'board', 'board.py'))
boardtool = _ilu.module_from_spec(_board_spec)
_board_spec.loader.exec_module(boardtool)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKIP_DIRS = {'.git', 'reference', 'node_modules', '__pycache__', '.venv'}
HDR = re.compile(r'<!--\s*doc:\s*(.*?)\s*-->')
KV = re.compile(r'(\w[\w-]*)=(\S+)')

def walk():
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            if f.endswith('.md'):
                yield os.path.relpath(os.path.join(dp, f), ROOT)

def header(path):
    try:
        with open(os.path.join(ROOT, path), encoding='utf-8', errors='replace') as fh:
            head = ''.join([next(fh, '') for _ in range(6)])
    except Exception:
        return None
    m = HDR.search(head)
    return dict(KV.findall(m.group(1))) if m else None

def tracked():
    try:
        out = subprocess.run(['git', 'ls-files'], cwd=ROOT, capture_output=True, text=True, timeout=30)
        return set(out.stdout.split('\n'))
    except Exception:
        return None

# ---------------------------------------------------------------------------------------
# DEFECT 6 (EP-28W W2) — THE BOARD OF RECORD FOLDS.
#
# WHY THIS IS HERE AND NOT IN THE SUITE, ruled 2026-08-08: a suite asserts about CODE and
# this asserts about DATA. Four rows in `tests/test_board_tool.py` read the live
# `BOARD-EVENTS.log`, so a LAWFUL edit to the record reported as a code failure with the
# builder blameless — armB red on one tree while armA was green. A suite that reddens on
# data edits trains seats to read red as noise, which costs more than the rows are worth.
# The ASSERTION is valuable and stays: these are the only lines in the estate asserting
# that the board of record is READABLE, and they are what turned a silently broken file
# into a visible failure.
#
# WHAT IT ASSERTS AND WHAT IT REFUSES TO ASSERT. That the log FOLDS, using the board
# tool's own reader, and that a refusal is reported LOUDLY IN THE TOOL'S OWN WORDS.
# NOTHING ABOUT THE CONTENT — not an item count, not a state, not a line number. Content
# is data and data changes lawfully many times a day. `DEFECT 5` is HELD VACANT above.
#
# THE CONTROL, in the same invocation. Its finding is an ABSENCE — "no refusal" — so a
# structurally broken check returns exactly the clean zero a healthy one returns. It
# plants a known-present break into a scratch copy and requires the checker to find it,
# and a failed control prints UNINTERPRETABLE rather than a number.
#
# THE CONTROL'S TWO ARMS ARE SYNTHETIC, AND THAT IS A DECLARED DEPARTURE FROM EP-28W W2's
# LETTER, which says "a scratch COPY of the log". Derived, and raised in EP-28W's entry:
#   * the GREEN arm cannot be a copy of the live log, because the live log's
#     well-formedness is the very thing under measurement. A control whose pass depends on
#     the answer it is measuring is an observer inside the system it observes — and the
#     concrete cost is the wrong way round: on the ONE day the live log is broken, the
#     defect line would print UNINTERPRETABLE instead of reporting the break it exists to
#     report.
#   * the two arms must VARY EXACTLY ONE THING. A synthetic green arm beside a live-copy
#     red arm differs in two, so no divergence between them could be attributed.
# The plant is still made into a COPY and never into any live file, which is the clause
# the parenthetical in W2 exists to protect.
# ---------------------------------------------------------------------------------------

BOARD_EVENTS = os.path.join(ROOT, 'planning', 'build', 'BOARD-EVENTS.log')

#: OUTSIDE THE REPOSITORY, on purpose. `claude-git-autosync.sh` runs `git add -A` before
#: `git pull --rebase`, so an untracked file in the tree is conscripted into a commit and
#: the rebase then replaces its inode under a live writer. Uniqueness was never the
#: protection; location is.
SCRATCH_PARENT = '/tmp/govos-board'

_CONTROL_WELL_FORMED = """\
# synthetic — planted by DEFECT 6's control. Never the live record.
# ==================== SEED BLOCK ====================
EVT | 2026-02-01 | CTRL-DEFECT6 | AUTHORED | ctl | the seed
# ================== END SEED BLOCK ==================
EVT | 2026-03-01 | CTRL-DEFECT6 | CLOSED | ctl |
"""

#: The plant, and it is the EXACT break that took the board of record down on 2026-08-08:
#: a header comment QUOTING the seed marker's text becomes a second marker, and the tool
#: refuses the file whole. One string in a comment is the whole distance between a dead
#: board and a live one.
_CONTROL_PLANT = '# a comment quoting the SEED BLOCK marker, as the repaired header did\n'


def owned_scratch_dir(parent=SCRATCH_PARENT):
    """An OWNED directory, UNIQUE TO THIS INVOCATION, created or REFUSED — never shared.

    `mkdtemp` creates with `O_EXCL`, so a name collision FAILS LOUDLY rather than handing
    two invocations one directory. The atomicity does the enforcing, and its best property
    is that it makes the uniqueness SOURCE uncritical: a poor name scheme produces a loud
    refusal, never a silent share. A FIXED SHARED PATH IS A RED — this instrument runs at
    every invocation, builder arms run it, the manager re-takes it and the verifier re-runs
    it verbatim, and a POSITIVE CONTROL CLOBBERED MID-RUN CERTIFIES THE INSTRUMENT THAT
    JUST FAILED, which is worse than no control.
    """
    os.makedirs(parent, exist_ok=True)
    return tempfile.mkdtemp(prefix='inventory-defect6-', dir=parent)


def scratch_paths_are_unique(factory, count=3, parent=SCRATCH_PARENT):
    """Does `factory` hand out a DIFFERENT owned directory every time? (ok, detail).

    Written as a check over a FACTORY rather than as a statement about this module, so the
    same code can be driven with a fixed-path factory and REQUIRED TO FAIL. A property
    nothing can violate has not been tested.
    """
    made = []
    try:
        for _ in range(count):
            path = factory()
            if path in made:
                return False, 'a FIXED SHARED PATH was handed out twice: %s' % path
            if os.path.dirname(path.rstrip(os.sep)) != parent.rstrip(os.sep):
                return False, 'scratch landed outside %s: %s' % (parent, path)
            made.append(path)
    finally:
        for path in made:
            shutil.rmtree(path, ignore_errors=True)
    for path in made:
        if os.path.exists(path):
            return False, 'the creator did not remove its own scratch: %s' % path
    return True, '%d invocations, %d distinct owned directories, all removed' % (
        count, len(set(made)))


def _folds(path):
    """(ok, reason) for ONE events file, through the board tool's own reader."""
    try:
        events, _meta = boardtool.read_events(path)
        boardtool.fold(events)
    except boardtool.BoardRefusal as exc:
        return False, '%s:%d — %s' % (path, exc.lineno, exc.reason)
    except (OSError, ValueError) as exc:
        return False, '%s — %s: %s' % (path, type(exc).__name__, exc)
    return True, 'folds'


def board_folds_control():
    """Plant a KNOWN-PRESENT break into a scratch copy and require the checker to find it.

    Returns (ok, detail). Both arms are written into ONE owned directory unique to this
    invocation, and the creator removes it.
    """
    scratch = None
    try:
        scratch = owned_scratch_dir()
        green = os.path.join(scratch, 'well-formed.events')
        red = os.path.join(scratch, 'double-marker.events')
        with open(green, 'w', encoding='utf-8') as fh:
            fh.write(_CONTROL_WELL_FORMED)
        with open(red, 'w', encoding='utf-8') as fh:
            fh.write(_CONTROL_WELL_FORMED + _CONTROL_PLANT)

        ok, reason = _folds(green)
        if not ok:
            return False, 'the well-formed scratch copy did NOT fold: %s' % reason
        ok, reason = _folds(red)
        if ok:
            return False, 'the planted double marker was NOT caught — the checker cannot '\
                          'see the exact break that took the board down on 2026-08-08'
        if 'second SEED BLOCK marker' not in reason:
            return False, ('the planted copy refused for the WRONG CLAUSE, so the red '
                           'world proves nothing about this plant: %s' % reason)
        unique_ok, unique_detail = scratch_paths_are_unique(owned_scratch_dir)
        if not unique_ok:
            return False, 'scratch is not unique per invocation: %s' % unique_detail
        return True, ('planted double marker CAUGHT for its own clause, well-formed copy '
                      'folded, %s' % unique_detail)
    except OSError as exc:
        return False, 'the control could not create its own scratch: %s' % exc
    finally:
        if scratch:
            shutil.rmtree(scratch, ignore_errors=True)


def board_folds_report(events_path=BOARD_EVENTS):
    """The lines `inventory.py` prints for DEFECT 6. Never raises."""
    ok, detail = board_folds_control()
    lines = []
    if not ok:
        lines.append('DEFECT 6 — the board of record folds       : UNINTERPRETABLE')
        lines.append('    positive control FAILED — %s' % detail)
        lines.append('    a zero from a checker whose control fails is not a count')
        return lines, False
    folds, reason = _folds(events_path)
    if folds:
        lines.append('DEFECT 6 — the board of record folds       : 0')
    else:
        lines.append('DEFECT 6 — the board of record folds       : 1')
        lines.append('    THE BOARD OF RECORD DOES NOT FOLD. Every seat reading it by')
        lines.append('    hand is reading a file the instrument cannot read.')
        lines.append('    the tool\'s own refusal: %s' % reason)
    lines.append('    asserts only that it READS — nothing about its content, which is')
    lines.append('    DATA and changes lawfully many times a day')
    lines.append('    positive control PASSED — %s' % detail)
    return lines, folds


# ---------------------------------------------------------------------------------------
# DEFECT 7 (EP-33A, charter §A25) — BUILD-PROGRESS's APPEND-ONLY LAW, MECHANICALLY.
#
# §A25's open instance: "BUILD-PROGRESS's append-only law has no mechanical guard ... the one
# law in this estate that the seat writing it is also the seat enforcing it." The closed-
# instance template §A25 endorses is "a cheap mechanical count, checked by a seat other than
# the one it constrains" — this self-check is run by the manager and the verifier, not by the
# builder appending to BUILD-PROGRESS, so the applier is not its own check. The founding-guard's
# sibling: committed history append-only across a window, old content a PREFIX of new.
#
# WHAT IT ASSERTS. That every older committed revision of the log in the window is a byte-prefix
# of the next, and that HEAD's committed version is a prefix of the working tree. A pure append
# preserves the prefix; changing or removing an existing line breaks it, which is the exact
# accident the append-only law exists to prevent.
#
# THE CONTROL, in the same invocation (DEFECT 6's shape). Its finding is an ABSENCE — "no
# non-append" — so a structurally broken check returns the clean zero a healthy one returns. It
# feeds the predicate a lawful append and a planted rewrite and requires the append served and
# the rewrite CAUGHT; a failed control prints UNINTERPRETABLE rather than a number.
#
# HONEST CAP: the window is the last N committed revisions plus the working tree, so a rewrite
# older than the window is not re-caught by THIS run — it was catchable when it was recent, and
# each run guards its own window. Cheap enough to run every time is the property being kept.
# ---------------------------------------------------------------------------------------

BUILD_PROGRESS = os.path.join(ROOT, 'planning', 'build', 'BUILD-PROGRESS_v3.md')


def is_append_over(old, new):
    """(ok, reason): is `old` a byte-prefix of `new`? Append-only means old content is
    UNCHANGED and new only adds to its end. Bytes in, so encoding cannot confuse the compare."""
    if new.startswith(old):
        return True, 'append-only: %d -> %d bytes, prefix intact' % (len(old), len(new))
    if len(new) < len(old) and old.startswith(new):
        return False, ('content SHRANK %d -> %d bytes: an existing line was REMOVED, not '
                       'appended' % (len(old), len(new)))
    n = min(len(old), len(new))
    i = 0
    while i < n and old[i] == new[i]:
        i += 1
    return False, 'content REWRITTEN at byte %d: an existing line was CHANGED, not appended' % i


_BP_CONTROL_BASE = b'EVT | seed line 1\nEVT | seed line 2\n'
_BP_CONTROL_APPEND = _BP_CONTROL_BASE + b'EVT | seed line 3 (appended)\n'
_BP_CONTROL_REWRITE = b'EVT | seed line 1\nEVT | REWRITTEN line 2\n'


def build_progress_control():
    """A lawful append must serve and a planted rewrite must be caught (ok, detail)."""
    ok_a, _ = is_append_over(_BP_CONTROL_BASE, _BP_CONTROL_APPEND)
    if not ok_a:
        return False, 'a lawful APPEND was reported a non-append — the guard rejects a real append'
    ok_r, reason_r = is_append_over(_BP_CONTROL_BASE, _BP_CONTROL_REWRITE)
    if ok_r:
        return False, ('a REWRITTEN line was reported append-only — the guard cannot see the '
                       'non-append edit it exists to catch')
    return True, 'lawful append served; planted rewrite CAUGHT (%s)' % reason_r


def _committed_blobs(relpath, limit):
    """[(short_hash, bytes)] for the last `limit` commits touching relpath, newest first."""
    out = subprocess.run(['git', 'log', '--format=%h', '-n', str(limit), '--', relpath],
                         cwd=ROOT, capture_output=True, timeout=30)
    blobs = []
    for h in [x for x in out.stdout.decode().split('\n') if x]:
        show = subprocess.run(['git', 'show', '%s:%s' % (h, relpath)],
                              cwd=ROOT, capture_output=True, timeout=30)
        if show.returncode == 0:
            blobs.append((h, show.stdout))
    return blobs


def build_progress_append_only_report(path=BUILD_PROGRESS, window=6):
    """The lines inventory.py prints for DEFECT 7. Never raises."""
    ok, detail = build_progress_control()
    lines = []
    if not ok:
        lines.append('DEFECT 7 — BUILD-PROGRESS append-only      : UNINTERPRETABLE')
        lines.append('    positive control FAILED — %s' % detail)
        lines.append('    a zero from a checker whose control fails is not a count')
        return lines, False
    breaks = []
    try:
        blobs = _committed_blobs(os.path.relpath(path, ROOT), window)
        for (h_new, b_new), (h_old, b_old) in zip(blobs, blobs[1:]):
            good, reason = is_append_over(b_old, b_new)
            if not good:
                breaks.append('%s -> %s: %s' % (h_old, h_new, reason))
        if blobs:
            with open(path, 'rb') as fh:
                work = fh.read()
            good, reason = is_append_over(blobs[0][1], work)
            if not good:
                breaks.append('%s -> working tree: %s' % (blobs[0][0], reason))
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        lines.append('DEFECT 7 — BUILD-PROGRESS append-only      : UNINTERPRETABLE')
        lines.append('    could not read committed history: %s: %s' % (type(exc).__name__, exc))
        return lines, False
    if breaks:
        lines.append('DEFECT 7 — BUILD-PROGRESS append-only      : %d' % len(breaks))
        lines.append('    A NON-APPEND EDIT is in committed history. The one law the seat')
        lines.append('    writing the log also enforces was broken — an existing line changed')
        lines.append('    or was removed, not appended.')
        for b in breaks:
            lines.append('    %s' % b)
    else:
        lines.append('DEFECT 7 — BUILD-PROGRESS append-only      : 0')
    lines.append('    old content a PREFIX of new across the last %d committed revisions and' % window)
    lines.append('    the working tree; a rewrite older than the window was caught when recent')
    lines.append('    positive control PASSED — %s' % detail)
    return lines, not breaks


# ---------------------------------------------------------------------------------------
# DEFECT 8 (EP-33A, charter §A25) — CLAUDE.md JOINED TO THE DOC-MAP SELF-CHECK.
#
# §A25's other open instance: "CLAUDE.md orients every session and is checked by nothing."
# CLAUDE.md carries a header and is in the map today — but the generic walk covers it ONLY
# WHILE it has a header: strip the header and CLAUDE.md drops silently into the no-header set,
# which --defects never prints, and it is "checked by nothing" again in the exact failure mode
# §A25 named. This makes the coverage UNCONDITIONAL: the orienting document is asserted headered
# AND mapped, so its falling out of either is a defect rather than a silence.
#
# HONEST CAP (§A36): this proves CLAUDE.md is COVERED, never that its CONTENT is current — the
# tool reads headers, not prose. The stale-content class §A25 also observed is item 22's
# (the DOC-MAP diff-check), EP-33B's, not this guard's.
# ---------------------------------------------------------------------------------------

CLAUDE_MD = os.path.join(ROOT, 'CLAUDE.md')


def claude_md_covered(claude_text, docmap_text):
    """(ok, reason): does CLAUDE.md carry a doc header AND appear in the DOC-MAP?"""
    if not HDR.search(claude_text[:4000]):
        return False, ('CLAUDE.md carries no <!-- doc: --> header — the orienting document has '
                       'fallen out of the header set and is checked by nothing')
    if 'CLAUDE.md' not in docmap_text:
        return False, 'CLAUDE.md is absent from DOC-MAP_v3.md — mapped by nothing'
    return True, 'CLAUDE.md is headered and present in DOC-MAP_v3.md'


def claude_md_control():
    """A headerless copy and an unmapped copy must both be caught (ok, detail)."""
    ok_bad, _ = claude_md_covered('# no header here\n', 'CLAUDE.md')
    if ok_bad:
        return False, 'a headerless CLAUDE.md was reported covered — a lost header is invisible'
    ok_unmapped, _ = claude_md_covered('<!-- doc: class=VIEW status=LIVE -->\n', '')
    if ok_unmapped:
        return False, 'an unmapped CLAUDE.md was reported covered — a missing map entry is invisible'
    return True, 'a headerless copy and an unmapped copy both CAUGHT'


def claude_md_join_report(claude_path=CLAUDE_MD, docmap_text=None):
    """The lines inventory.py prints for DEFECT 8. Never raises."""
    ok, detail = claude_md_control()
    lines = []
    if not ok:
        lines.append('DEFECT 8 — CLAUDE.md under the self-check   : UNINTERPRETABLE')
        lines.append('    positive control FAILED — %s' % detail)
        return lines, False
    try:
        with open(claude_path, encoding='utf-8', errors='replace') as fh:
            claude_text = fh.read()
    except OSError as exc:
        lines.append('DEFECT 8 — CLAUDE.md under the self-check   : 1')
        lines.append('    CLAUDE.md could not be read: %s' % exc)
        lines.append('    positive control PASSED — %s' % detail)
        return lines, False
    if docmap_text is None:
        try:
            with open(os.path.join(ROOT, 'DOC-MAP_v3.md'), encoding='utf-8') as fh:
                docmap_text = fh.read()
        except OSError:
            docmap_text = ''
    good, reason = claude_md_covered(claude_text, docmap_text)
    lines.append('DEFECT 8 — CLAUDE.md under the self-check   : %d' % (0 if good else 1))
    if not good:
        lines.append('    %s' % reason)
    lines.append('    the orienting document is asserted headered AND mapped, so it cannot fall')
    lines.append('    silently out of the header set into "checked by nothing" (charter §A25)')
    lines.append('    HONEST CAP: proves it is COVERED, not that its CONTENT is current (§A36)')
    lines.append('    positive control PASSED — %s' % detail)
    return lines, good


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else '--all'
    docs, noheader = [], []
    for p in sorted(walk()):
        h = header(p)
        (docs.append((p, h)) if h else noheader.append(p))

    try:
        docmap = open(os.path.join(ROOT, 'DOC-MAP_v3.md'), encoding='utf-8').read()
    except Exception:
        docmap = ''

    live_unmapped, archived_live, unverified = [], [], []
    for p, h in docs:
        st = h.get('status', '?').upper()
        canon = os.path.basename(p).replace('_v3.md', '.md')
        if st == 'LIVE':
            if 'archive' in p.split(os.sep):
                archived_live.append(p)
            elif canon not in docmap and os.path.basename(p) not in docmap:
                live_unmapped.append(p)
        if 'verified' not in h:
            unverified.append(p)

    if mode == '--eps':
        eps=[]
        for p2,h in docs:
            b=os.path.basename(p2)
            if p2.startswith('planning/exec/') and b.startswith('EP-'):
                eps.append((b.replace('.md',''), p2, h))
        def key(t):
            m=re.match(r'EP-(\d+)([A-Z]*)', t[0]); return (int(m.group(1)), m.group(2)) if m else (999,'')
        print('| EP | file | status | verified |')
        print('|---|---|---|---|')
        for name,p2,h in sorted(eps,key=key):
            print(f"| **{name}** | `{p2}` | {h.get('status','?')} | {h.get('verified','—')} |")
        return

    if mode == '--map':
        print('| document | class | status | verified |')
        print('|---|---|---|---|')
        for p, h in docs:
            print(f"| `{p}` | {h.get('class','?')} | {h.get('status','?')} | {h.get('verified','—')} |")
        return

    print(f"DOCUMENTS WITH A HEADER : {len(docs)}")
    print(f"MARKDOWN WITHOUT ONE    : {len(noheader)}")
    by = {}
    for _, h in docs:
        by[h.get('status', '?').upper()] = by.get(h.get('status', '?').upper(), 0) + 1
    print("BY STATUS               :", ', '.join(f"{k}={v}" for k, v in sorted(by.items())))
    print()
    print(f"DEFECT 1 — LIVE but absent from DOC-MAP_v3 : {len(live_unmapped)}")
    for p in live_unmapped: print("   ", p)
    print(f"DEFECT 2 — under archive/ but status=LIVE  : {len(archived_live)}")
    for p in archived_live: print("   ", p)
    print(f"DEFECT 3 — header carries no verified= date: {len(unverified)}")
    for p in unverified[:12]: print("   ", p)
    if len(unverified) > 12: print(f"    … and {len(unverified)-12} more")
    # DEFECT 4 (EP-28V) — the check vocabulary the ENGINE declares against the check
    # vocabulary design/28 §5 AUTHORS. Set-diffed both directions; §5 is never generated
    # from the code. Its finding is an ABSENCE, so it carries a positive control on every
    # run and reports UNINTERPRETABLE rather than a zero when that control fails.
    for line in checkvocab.report()[0]:
        print(line)
    # DEFECT 5 is RESERVED, not missing. It is commissioned by PROCESS-FREEZE.md rule 4
    # (CANON diff with no matching EVT line) and the owner signed that text naming the
    # number, which makes the number an IDENTITY rather than a role — coordinates cited in
    # law are not reassigned. A run printing 1,2,3,4,6 reads as an oversight; a run
    # printing this line reads as a state.
    print("DEFECT 5 — CANON diff with no EVT line     : RESERVED — commissioned by "
          "PROCESS-FREEZE.md rule 4, UNBUILT")
    for line in board_folds_report()[0]:
        print(line)
    for line in build_progress_append_only_report()[0]:
        print(line)
    for line in claude_md_join_report()[0]:
        print(line)
    if mode != '--defects':
        print(f"\nNO HEADER AT ALL ({len(noheader)}):")
        for p in noheader[:20]: print("   ", p)
        if len(noheader) > 20: print(f"    … and {len(noheader)-20} more")

if __name__ == '__main__':
    main()
