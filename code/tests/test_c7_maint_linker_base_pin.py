# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: build-tooling · machine register.
# The body's canonical program base 0x400000 is stated in TWO source places -- the C header's
# CANONICAL_BASE (src/body/body.h) and the linker script's ASSERT base literal (src/body/linker.ld),
# whose own comment says it "mirrors body.h:71 CANONICAL_BASE". A linker script cannot include the C
# header, so nothing holds the two equal: either can move alone and the drift is silent until a
# boot-time collision. This test reads BOTH literals from their source files by shape (a regex over
# each file's own text, never a hand-typed copy of the number) and asserts them equal.
# NON-GOAL: no offensive capability; it reads two source literals and compares them, no boot, no src edit.
# Validate by reading/running, never by attack. Full declaration: SCOPE-STATEMENT.md.
"""C7-MAINT-LINKER-BASE-PIN acceptance -- the body's canonical program base held equal at its two
sources (design/54 §5 L14; §7 P3b-4m/L20; archi :4486; GREEN, no countersign as :4254 / :4268).

A1  the CANONICAL_BASE literal (body.h) and the ASSERT base literal (linker.ld) are each read from
    source by shape and asserted equal -- a plain collection + run is green.
A2  either literal moved alone reds it -- the plant mutates one literal in an in-memory COPY of the
    file text (never the real source) in BOTH directions and shows the same comparison red each way.
A3  nothing else moves -- this is a test under tests/, reading src/body read-only; no src edit, no
    founding, ATTESTED unchanged, ACT_KINDS 12, no boot.
"""

import os
import re
import unittest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BODY_H = os.path.join(_REPO_ROOT, "src", "body", "body.h")
_LINKER_LD = os.path.join(_REPO_ROOT, "src", "body", "linker.ld")

# body.h states it as a #define with a `ull` suffix: `#define CANONICAL_BASE   0x400000ull`
_HEADER_RE = re.compile(r"#define\s+CANONICAL_BASE\s+(0[xX][0-9a-fA-F]+)")
# linker.ld states it inside the ASSERT, no suffix: `ASSERT(_bss_end < 0x400000,`
_LINKER_RE = re.compile(r"ASSERT\(\s*_bss_end\s*<\s*(0[xX][0-9a-fA-F]+)\s*,")


def _read(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def _extract_one(pattern, text, what):
    """Read the base literal from the file's own text by shape. Fail LOUD if the shape moves --
    a source pin reads the number from the source, it never falls back to a hand-typed copy (L14)."""
    hits = pattern.findall(text)
    if len(hits) != 1:
        raise AssertionError(
            "%s: expected exactly ONE base literal by shape, found %d (%r) -- the source shape moved; "
            "re-read the literal from the file, do not retype the number" % (what, len(hits), hits)
        )
    return hits[0]


def _header_base(text):
    return _extract_one(_HEADER_RE, text, "body.h CANONICAL_BASE")


def _linker_base(text):
    return _extract_one(_LINKER_RE, text, "linker.ld ASSERT base")


def _assert_bases_equal(header_text, linker_text):
    """THE PIN. Reads both literals by shape and asserts their integer values equal. Raises
    AssertionError on drift. A1 calls it over the real source; the A2 plant calls it over mutated
    in-memory copies to prove it CAN red -- one comparison, exercised both ways."""
    hb = _header_base(header_text)
    lb = _linker_base(linker_text)
    if int(hb, 16) != int(lb, 16):
        raise AssertionError(
            "canonical program base DRIFTED: body.h CANONICAL_BASE=%s, linker.ld ASSERT base=%s -- "
            "the linker script literal must mirror body.h:71 (the body image must stay below the "
            "program base)" % (hb, lb)
        )
    return int(hb, 16)


class TestC7MaintLinkerBasePin(unittest.TestCase):
    def test_a1_two_literals_read_from_source_and_equal(self):
        """A1 -- both literals read from source by shape, asserted equal."""
        header_text = _read(_BODY_H)
        linker_text = _read(_LINKER_LD)
        base = _assert_bases_equal(header_text, linker_text)
        # the two literals as read (for the evidence log)
        self.assertEqual(_header_base(header_text).lower(), "0x400000")
        self.assertEqual(_linker_base(linker_text).lower(), "0x400000")
        self.assertEqual(base, 0x400000)

    def test_a2_header_moved_alone_reds(self):
        """A2 direction 1 -- body.h's literal changed while linker.ld's stands -> reds."""
        header_text = _read(_BODY_H)
        linker_text = _read(_LINKER_LD)
        # mutate the header literal in an in-memory COPY only; the real file is untouched
        mutated_header = header_text.replace("CANONICAL_BASE   0x400000ull",
                                             "CANONICAL_BASE   0x500000ull")
        self.assertNotEqual(mutated_header, header_text,
                            "plant setup failed: header literal string not found to mutate")
        with self.assertRaises(AssertionError):
            _assert_bases_equal(mutated_header, linker_text)

    def test_a2_linker_moved_alone_reds(self):
        """A2 direction 2 -- linker.ld's literal changed while body.h's stands -> reds."""
        header_text = _read(_BODY_H)
        linker_text = _read(_LINKER_LD)
        # mutate the linker literal in an in-memory COPY only; the real file is untouched
        mutated_linker = linker_text.replace("ASSERT(_bss_end < 0x400000,",
                                             "ASSERT(_bss_end < 0x500000,")
        self.assertNotEqual(mutated_linker, linker_text,
                            "plant setup failed: linker literal string not found to mutate")
        with self.assertRaises(AssertionError):
            _assert_bases_equal(header_text, mutated_linker)


if __name__ == "__main__":
    unittest.main()
