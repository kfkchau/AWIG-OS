"""THE ERA PIN — the estate's one home for reading a repository path AS IT STOOD AT A
NAMED COMMIT [EP-28Z, 2026-08-12].

This is not a test file (the suite's discovery pattern is `test_*.py`); it is a library
the suite's files import, in the shape `tests/ep24b_differential.py` already established,
so there is ONE implementation of the era-pin act rather than the eighteen that had
accreted across ten files.

WHY IT EXISTS. Charter §A57 commands a founding pass to era-pin its predecessor's version
and diff rows. The clause states the DUTY and states no METHOD, so every pass that met it
re-derived the method from the instances — and the estate's own measurement at
HOW-NOT-WHAT (board :410, 2026-08-09) found the mechanism living in five test files with
no single home. THE WALK FOUND EIGHTEEN SITES ACROSS TEN FILES. The five were testimony
about one seat's taking, never the bound; this file is the bound's answer.

WHAT THE MECHANISM IS, stated so a later reader can falsify a claim of membership:

    obtaining the content of a REPOSITORY PATH as it stood AT A NAMED COMMIT, by
    spawning git with a <rev>:<path> blob reference.

    What the caller does with the bytes afterwards — json.loads, .decode(), exec into a
    module, write to a temp file — is the CALLER's business and is NOT the mechanism.
    That separation is why one home can serve ten files whose post-processing shares
    nothing.

WHAT IS NOT THE MECHANISM, each of these driven as a near-miss control in
`tests/test_ep28z.py` rather than merely asserted (§A64):

    * `git show REV` with no path        — a commit read, not a blob read
    * `git rev-parse` / `log` / `status` / `ls-files` / `diff` / `merge-base`
                                         — repository facts, not an era's bytes
    * `open(path)` against the live tree — the very thing an era pin exists to avoid

THE THREE MISSING-BLOB POLICIES ARE PARAMETERS AND NOT A DEFAULT, because the ten copy
sites did not agree and a silent choice would have changed nine of them:

    missing="raise"   CalledProcessError. The loud default. What `check=True` and
                      `check_output` already did at six sites.
    missing="skip"    unittest.SkipTest, carrying git's own stderr. What five sites did,
                      so a pin that stops resolving reports as a skip rather than a red.
    missing="assert"  AssertionError, carrying git's own stderr. What two sites did, so
                      an unresolvable pin lands as a FAIL rather than an ERROR.

A CAP, stated because it is the one thing this file cannot do for its callers: it makes
the READ uniform and it makes no claim at all about whether a caller's PIN is the right
commit. Choosing a pin by version number rather than by content is the estate's most
expensive known trap (board :410), it is a property of the constant and not of the read,
and nothing here can see it.
"""
import json
import os
import subprocess
import unittest

#: The repository root, derived from this file's own location. Every copy site computed
#: this for itself, ten times, in four spellings, all resolving to the same directory.
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: The founding pack's repo-relative path, named once so ten call sites stop spelling it.
PACK_PATH = "src/founding/founding-pack.json"

_POLICIES = ("raise", "skip", "assert")


def blob_at(rev, path, missing="raise"):
    """The bytes git stores for `path` at `rev`. BYTES, never text: a caller that hashes
    an era's blob must hash exactly what git holds, and a decode that normalises line
    endings would silently move that digest."""
    if missing not in _POLICIES:
        raise ValueError("missing must be one of %r, got %r" % (_POLICIES, missing))
    out = subprocess.run(["git", "show", "%s:%s" % (rev, path)],
                         cwd=REPO, capture_output=True)
    if out.returncode != 0:
        stderr = out.stderr.decode("utf-8", "replace")
        detail = "%s at %s does not resolve: %s" % (path, rev, stderr)
        if missing == "skip":
            raise unittest.SkipTest(detail)
        if missing == "assert":
            raise AssertionError(detail)
        raise subprocess.CalledProcessError(out.returncode,
                                            ["git", "show", "%s:%s" % (rev, path)],
                                            output=out.stdout, stderr=out.stderr)
    return out.stdout


def text_at(rev, path, missing="raise"):
    """`blob_at` decoded as UTF-8, explicitly. This replaces subprocess's `text=True` at
    the sites that used it; both are byte-equivalent here, and the equivalence is DRIVEN
    rather than assumed — `tests/test_ep28z.py` checks every pin this suite holds for a
    carriage return, which is the only input on which the two decodings differ."""
    return blob_at(rev, path, missing=missing).decode("utf-8")


def pack_at(rev, missing="raise"):
    """The founding pack as it stood at `rev`, parsed. The §A57 act itself: an era's own
    law, read out of git, never off the live tree."""
    return json.loads(text_at(rev, PACK_PATH, missing=missing))
