#!/usr/bin/env python3
"""PUSHSCAN — the release hygiene scan (EP-RELEASE-COPYOUT R8).

Reads the WHOLE push set — every tracked file of the public checkout at the
candidate commit — and REFUSES if any file's path or bytes carry something that
must never reach the public remote. It is fail-loud: it names the file and the
matched string, and exits non-zero, so a private string cannot be stripped
silently. STOP and raise if it refuses a real file (a private string is in the
push set; name it, do not strip).

It is a WIDER net than render.py's FORBIDDEN_OUTPUT (that guards one rendered
tree; this guards the whole repository about to be published). render.py is not
touched.

Refuses on:
  - <HOME>                     (this laptop's home path)
  - C:\\Users                         (a Windows home path)
  - <PROJECTS>                 (a seat transcript path)
  - a session-id .jsonl              (a uuid-named transcript file, path or content)
  - the local_<uuid> address form    (a routing handle)
  - the owner's email address
  - a FILE whose path is under planning/ prompt/ sessions/ .claude/  (estate-only trees)

Allowed and only COUNTED as INFO (archi :3239): a BARE relative document cite in a
comment/docstring/string — `planning/NN…`, `design/NN…`, `prompt/…`, `sessions/…`.
Rendered source cites private-repository documents by path as provenance (the same
stance as the private commit); that is not a laptop path, a transcript, an address or
an email, and `design/` is not a refuse pattern. INFO never raises the exit code.

Usage:
  pushscan.py --repo DIR [--ref REF]     scan every tracked file at REF (default HEAD)
  pushscan.py PATH [PATH ...]            scan these files (or dirs, recursively)

Exit 0 = clean; exit 1 = at least one refusal (each named); exit 2 = usage error.
"""
import os
import re
import subprocess
import sys

# The owner's email, assembled rather than written whole, so this scanner file
# does not itself carry the literal it hunts for.
_OWNER_EMAIL = ("kfkchau" + "@" + "gmail" + ".com").encode()

# (name, compiled-regex-over-bytes). Each must be able to fire; the planted
# control proves it does.
UUID = rb"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
# REFUSE — genuine private strings: a laptop-absolute path, a real seat transcript
# path, a session-id form, a routing handle, or the owner's email. Any of these in
# the push set is a leak and the scan exits non-zero.
CONTENT_RULES = [
    ("laptop home path <HOME>", re.compile(rb"<HOME>")),
    ("windows home path C:\\Users", re.compile(rb"C:\\Users")),
    ("seat transcript path <PROJECTS>", re.compile(rb"\<PROJECTS>")),
    ("session-id .jsonl", re.compile(UUID + rb"\.jsonl")),
    ("local_<uuid> address form", re.compile(rb"local_" + UUID)),
    ("owner email address", re.compile(re.escape(_OWNER_EMAIL))),
    # EP-RELEASE-TESTS: the five classes pushscan lacked, unifying its refusal set with the
    # eight private-literal classes of the tests/tools rendering (§5: add only the absent classes).
    # Each matches the PRIVATE FORM. repository_url is scoped to the PRIVATE forms (the ssh clone
    # form and the internal codename repo) so it never refuses the PUBLIC repo url.
    ("ssh invocation to the guest", re.compile(rb'(?:"ssh",\s*"-p",\s*"\d+"|\bssh\s+-p\s+\d+)')),
    ("private key path", re.compile(rb"~?/?\.ssh/[A-Za-z0-9_.-]+")),
    ("loopback with a port", re.compile(rb"127\.0\.0\.1:\d+")),
    ("guest user at loopback", re.compile(rb"[a-z][a-z0-9_-]*@127\.0\.0\.1")),
    ("private repository url", re.compile(rb"(?:git@github\.com:kfkchau/|github\.com/kfkchau/gov-os)")),
]
# INFO (archi :3239) — a BARE relative document cite inside a comment/docstring/
# string (`planning/NN…`, `design/NN…`, `prompt/…`, `sessions/…`) is ALLOWED and
# only COUNTED. Rendered source cites private-repository documents by path as
# provenance (the same stance as the private commit); this is not a leak of a laptop
# path, a transcript, an address or an email, and `design/` is NOT a refuse pattern.
# These are reported (count + file list) as INFO and never raise the exit code.
INFO_RULES = [
    ("doc cite planning/", re.compile(rb"(?:^|[^A-Za-z0-9_])planning/")),
    ("doc cite design/", re.compile(rb"(?:^|[^A-Za-z0-9_])design/")),
    ("doc cite prompt/", re.compile(rb"(?:^|[^A-Za-z0-9_])prompt/")),
    ("doc cite sessions/", re.compile(rb"(?:^|[^A-Za-z0-9_])sessions/")),
]
# A path whose first component is one of these must not be tracked in the public
# repo — a FILE actually located under an estate-only tree is a refusal (path-based,
# distinct from a bare relative cite in content above).
FORBIDDEN_TOP = {"planning", "prompt", "sessions", ".claude"}


def tracked_files(repo, ref):
    if ref:
        out = subprocess.check_output(["git", "-C", repo, "ls-tree", "-r", "--name-only", ref], text=True)
    else:
        out = subprocess.check_output(["git", "-C", repo, "ls-files"], text=True)
    return [ln for ln in out.splitlines() if ln.strip()]


def blob_bytes(repo, ref, relpath):
    if ref:
        return subprocess.check_output(["git", "-C", repo, "show", "%s:%s" % (ref, relpath)])
    with open(os.path.join(repo, relpath), "rb") as fh:
        return fh.read()


def scan_one(relpath, data):
    """Return (refusals, infos): each a list of (reason, matched-string).
    Refusals raise the exit code; infos are only counted and listed."""
    refusals = []
    infos = []
    top = relpath.replace("\\", "/").split("/", 1)[0]
    if top in FORBIDDEN_TOP:
        refusals.append(("path under estate-only tree %s/" % top, relpath))
    if relpath.replace("\\", "/").endswith(".jsonl") and re.search(UUID, relpath.encode()):
        refusals.append(("session-id .jsonl filename", relpath))
    for reason, rx in CONTENT_RULES:
        m = rx.search(data)
        if m:
            refusals.append((reason, m.group(0).decode("utf-8", "replace")))
    for reason, rx in INFO_RULES:
        m = rx.search(data)
        if m:
            infos.append((reason, m.group(0).decode("utf-8", "replace")))
    return refusals, infos


def main(argv):
    repo = ref = None
    paths = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--repo":
            repo = argv[i + 1]; i += 2
        elif a == "--ref":
            ref = argv[i + 1]; i += 2
        else:
            paths.append(a); i += 1

    items = []  # (label, relpath, bytes)
    if repo:
        for rel in tracked_files(repo, ref):
            items.append((rel, rel, blob_bytes(repo, ref, rel)))
    for p in paths:
        if os.path.isdir(p):
            for r, ds, ns in os.walk(p):
                for n in sorted(ns):
                    fp = os.path.join(r, n)
                    items.append((fp, os.path.relpath(fp, p), open(fp, "rb").read()))
        elif os.path.isfile(p):
            items.append((p, os.path.basename(p), open(p, "rb").read()))
        else:
            sys.stderr.write("pushscan: not found: %s\n" % p); return 2
    if not items:
        sys.stderr.write("pushscan: nothing to scan (give --repo DIR or PATH...)\n"); return 2

    refusals = 0
    info_files = []  # (relpath, [(reason, matched), ...])
    for label, rel, data in items:
        r, info = scan_one(rel, data)
        for reason, matched in r:
            print("REFUSE %s: %s — %r" % (label, reason, matched))
            refusals += 1
        if info:
            info_files.append((rel, info))
    if info_files:
        print("\nINFO — bare relative document cites (ALLOWED, counted; archi :3239):")
        for rel, info in info_files:
            kinds = sorted({reason for reason, _ in info})
            print("  %s — %s" % (rel, ", ".join(kinds)))
        print("INFO total: %d file(s) carry a bare doc cite" % len(info_files))
    print("\npushscan: %d file(s) scanned, %d refusal(s), %d file(s) with doc-cite INFO"
          % (len(items), refusals, len(info_files)))
    print("CLEAN" if refusals == 0 else "REFUSED — a private string is in the push set; STOP and name it")
    return 1 if refusals else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
