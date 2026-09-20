# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: test-tooling · OS-architecture
# vocabulary (record, committed tail, loader, recover ceremony, sidecar). NON-GOAL: no offensive
# capability of any kind — every test here asserts the CORRECT behaviour by function: a half-written
# final line no longer stops the loader and is kept aside for diagnosis, and a corruption of a
# COMMITTED record is refused rather than crashing the open or being silently dropped. Full
# declaration: SCOPE-STATEMENT.md.
"""EP-MAINT-OUTSIDE-6 — the committed tail (the record's framing made a stated contract).

F2 of the round-3 read (`ARCHI-READ-3.md` F2). Every test is written from the architect's read
DESCRIPTION and our OWN code (store.py's loader; erasure.py's recover ceremony) — NEVER from the
outside assessment harness (not read, not run, not a source; the plan's §7-f STOP and the wrong-
reference trap named in the EP's provenance header).

THE CONTRACT (from the plan §2): a record is COMMITTED when its line ends in a newline — the append
writes `json.dumps(record) + "\\n"` as one flushed unit (store.py:1242), so the closing newline is
the commit marker. An incomplete FINAL line (no closing newline — a crash mid-write) is NOT part of
the record: the store opens on the committed PREFIX, the incomplete bytes are kept ASIDE beside the
record (a sidecar; the record's bytes are never truncated or deleted) and a row states them. An
INTERIOR line that ends in a newline yet does not parse is corruption of a COMMITTED record: refused
at open and routed to the recover ceremony (`erasure.register_recover` / RECOVER_LAW), never silently
dropped. The comment at store.py:1196-1199 ("a partial line ... is dropped on reload") is made true.

Each acceptance carries its PLANT — the reversion or damage that makes the check RED (a channel is
proven by watching it refuse something):
  A1  truncation at EVERY byte offset of the final record opens on the committed prefix; PLANT: the
      bare `json.loads` the loader used to run raises on the truncated final line.
  A2  the set-aside bytes are kept (sidecar), a row states them, the record file is never truncated;
      PLANT: the record bytes must be byte-identical (a fix that truncated/deleted them reds).
  A3  an interior (committed) non-parsing line is refused at open and routed to recover; PLANT: a
      loader that opened-through or silently dropped it reds (the open must RAISE).
  A4  a committed record loads whole, unchanged (the common case; no regression).
  A5  no founding, no new op, the recover law reused not widened.
"""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from kernel.store import EventStore, ReaderCannotAppend, _split_committed_prefix  # noqa: E402
from kernel import erasure                                                        # noqa: E402


def _rec(i, note="cafe"):
    """A record line's committed BYTES (no newline). `note` may carry a multibyte char to prove the
    loader reads bytes, not text."""
    return json.dumps({"actor": "SYSTEM", "action": "CREATE-INFO", "object": str(i),
                       "note": note}, separators=(",", ":")).encode("utf-8")


class CommittedTail(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "record.jsonl")

    def _write(self, raw_bytes):
        with open(self.path, "wb") as f:
            f.write(raw_bytes)

    # -- A1 ----------------------------------------------------------------------------------------
    def test_a1_truncation_at_every_byte_offset_opens_on_committed_prefix(self):
        # A record file whose LAST line is truncated at EACH byte offset (0..len, and the newline
        # itself) OPENS on the committed prefix — never raises out of the constructor. The committed
        # prefix (two whole records) loads; the incomplete tail is absent from `self.events`.
        prefix = _rec(0) + b"\n" + _rec(1) + b"\n"
        final = _rec(2)                                   # the final record's bytes, not yet committed
        # cut == 0: no tail (file ends at the last newline). cut in 1..len: a partial final line.
        for cut in range(0, len(final) + 1):
            body = prefix + final[:cut]
            self._write(body)
            store = EventStore(self.path)                 # MUST NOT raise, at any offset
            self.assertEqual(len(store.events), 2,
                             "opens on the committed prefix (2 records) at cut=%d" % cut)
            self.assertEqual([e["object"] for e in store.events], ["0", "1"],
                             "the committed records loaded whole, in order, at cut=%d" % cut)
            with open(self.path, "rb") as f:              # the record file's bytes are UNCHANGED
                self.assertEqual(f.read(), body, "the record file is never truncated (cut=%d)" % cut)
        # and the newline-terminated whole file opens with all three
        self._write(prefix + final + b"\n")
        self.assertEqual(len(EventStore(self.path).events), 3)

    def test_a1_plant_bare_json_loads_raises_on_a_truncated_final_line(self):
        # THE PLANT (the check can fail): the loader USED TO run `json.loads(line.strip())` over
        # every non-blank line, INCLUDING an unterminated final one. Reconstruct that exact behaviour
        # and show it RAISES on a genuinely partial final line — the constructor crash F2 names. The
        # committed-tail loader OPENS on the same bytes.
        body = _rec(0) + b"\n" + _rec(1)[:12]             # a partial final line (invalid JSON fragment)
        self._write(body)

        def _bare_loader(raw):                            # what store.py:606-609 did before this unit
            events = []
            for line in raw.decode("utf-8").splitlines():
                s = line.strip()
                if s:
                    events.append(json.loads(s))          # raises on the partial fragment
            return events
        with self.assertRaises(ValueError):
            _bare_loader(body)
        # the committed-tail loader opens on the committed prefix instead of raising
        store = EventStore(self.path)
        self.assertEqual([e["object"] for e in store.events], ["0"])
        self.assertIsNotNone(store.set_aside_tail)

    # -- A2 ----------------------------------------------------------------------------------------
    def test_a2_set_aside_bytes_kept_row_states_them_record_never_truncated(self):
        # The incomplete tail bytes are kept ASIDE beside the record (a sidecar, never over the
        # record file); a row on the opened store STATES what was set aside (byte offset + length +
        # sidecar path); the record file's bytes are UNCHANGED (never truncated, never deleted).
        prefix = _rec(0) + b"\n"
        final = _rec(1)
        tail_bytes = final[:9]                            # a partial final line
        body = prefix + tail_bytes
        self._write(body)
        store = EventStore(self.path)

        # the row states what was set aside
        row = store.set_aside_tail
        self.assertIsNotNone(row, "a row states the set-aside")
        self.assertEqual(row["offset"], len(prefix), "the tail began right after the last newline")
        self.assertEqual(row["length"], len(tail_bytes), "the row states the tail's byte length")

        # the set-aside BYTES are kept, byte-identical, in the sidecar
        with open(row["sidecar"], "rb") as f:
            self.assertEqual(f.read(), tail_bytes, "the incomplete bytes are kept aside intact")
        self.assertNotEqual(os.path.abspath(row["sidecar"]), os.path.abspath(self.path),
                            "the sidecar is a DIFFERENT file, never the record")

        # PLANT: the record file is never truncated or deleted — its bytes are exactly what was
        # written. A fix that truncated the record to the committed prefix, or deleted it, reds here.
        self.assertTrue(os.path.exists(self.path), "the record file still exists")
        with open(self.path, "rb") as f:
            self.assertEqual(f.read(), body, "the record file's bytes are unchanged")

    def test_a2_byte_mode_survives_a_tail_truncated_mid_multibyte(self):
        # The loader reads the file as BYTES and finds the committed prefix by the newline byte, so
        # it never has to DECODE the incomplete tail. This makes it robust even where the tail is
        # truncated mid-multibyte-character — a tail no text-mode reader could decode. (The production
        # appender writes ensure_ascii JSON, so a real record file is pure ASCII and this can't arise
        # from it; the loader must not ASSUME that — design for the stretch, not the intent.) PLANT:
        # text-mode decode of the same bytes raises, where the byte-mode loader opens on the prefix.
        prefix = _rec(0) + b"\n"
        final = json.dumps({"actor": "SYSTEM", "action": "CREATE-INFO", "object": "1", "note": "café"},
                           separators=(",", ":"), ensure_ascii=False).encode("utf-8")  # raw 0xC3 0xA9
        seq = final.index(b"\xc3\xa9")                     # where the 2-byte char sits in the record
        tail_bytes = final[:seq + 1]                       # cut ONE byte into it -> an invalid utf-8 tail
        body = prefix + tail_bytes
        self._write(body)

        with self.assertRaises(UnicodeDecodeError):        # a text-mode reader would raise on this tail
            body.decode("utf-8")
        store = EventStore(self.path)                      # the byte-mode loader opens regardless
        self.assertEqual([e["object"] for e in store.events], ["0"])
        with open(store.set_aside_tail["sidecar"], "rb") as f:
            self.assertEqual(f.read(), tail_bytes, "the undecodable bytes are kept aside intact")

    # -- A3 ----------------------------------------------------------------------------------------
    def test_a3_interior_corruption_refused_and_routed_to_recover(self):
        # An INTERIOR line (ends in a newline — a committed record) that does not parse is corruption
        # of a committed record. It is REFUSED at open (the constructor raises) and ROUTED to the
        # recover ceremony: the refusal names register_recover / RECOVER_LAW and carries the break
        # location. It is NOT silently skipped and NOT opened-through.
        body = _rec(0) + b"\n" + b'{"actor":"broken", NOT VALID JSON\n' + _rec(2) + b"\n"
        self._write(body)
        with self.assertRaises(erasure.LoadInteriorCorruption) as cm:
            EventStore(self.path)
        exc = cm.exception
        self.assertEqual(exc.line_index, 1, "the break location names the corrupt committed line")
        self.assertEqual(exc.recover_law, erasure.RECOVER_LAW, "cites the recover law, reused")
        self.assertEqual(exc.recover_op, erasure.RECOVER_OP)
        self.assertIn("register_recover", str(exc), "the refusal routes to the recover ceremony")
        # the record file is untouched by the refusal
        with open(self.path, "rb") as f:
            self.assertEqual(f.read(), body)

    def test_a3_plant_interior_corruption_is_not_silently_dropped(self):
        # THE PLANT (the check can fail): a loader that silently dropped the unparseable interior
        # line would OPEN with the two sound records and no error. Prove the refusal is real — the
        # open RAISES rather than returning a partial store. (A skip-and-continue loader would make
        # `EventStore(...)` return, and this assertRaises would fail.)
        body = _rec(0) + b"\n" + b'garbage-not-json\n' + _rec(2) + b"\n"
        self._write(body)
        with self.assertRaises(erasure.LoadInteriorCorruption):
            EventStore(self.path)                          # never opens-partial over an interior break

    def test_a3_committed_final_corrupt_line_is_refused_not_set_aside(self):
        # The committed/incomplete distinction is by the NEWLINE, not by parseability. A FINAL line
        # that ENDS in a newline but does not parse is a committed record that is corrupt -> refused
        # and routed to recover, NOT mistaken for an incomplete tail and set aside.
        body = _rec(0) + b"\n" + b'{"final": corrupt-but-terminated}\n'
        self._write(body)
        with self.assertRaises(erasure.LoadInteriorCorruption):
            EventStore(self.path)

    # -- A4 ----------------------------------------------------------------------------------------
    def test_a4_committed_record_loads_whole_unchanged(self):
        # The common case: a store written through the sanctioned appender (every line newline-
        # terminated) reloads byte-for-byte, with NO set-aside and NO refusal. The round-trip law
        # holds exactly as before this unit.
        s1 = EventStore(self.path)
        for i in range(10):
            s1._append({"actor": "SYSTEM", "action": "A" if i % 2 else "B", "object": str(i)})
        s2 = EventStore(self.path)                         # reload
        self.assertEqual(s1.all(), s2.all(), "the record replays identically")
        self.assertIsNone(s2.set_aside_tail, "a fully committed record sets nothing aside")
        self.assertEqual(len(s2.events), 10)

    def test_a4_split_helper_is_exact_on_the_boundaries(self):
        # The committed-prefix split, stated directly: a newline-terminated file has no tail; a file
        # ending mid-line yields the prefix up to the last newline and the trailing bytes; a file
        # with no newline at all is entirely an incomplete tail; the empty file is empty.
        self.assertEqual(_split_committed_prefix(b""), (b"", b"", 0))
        self.assertEqual(_split_committed_prefix(b"a\nb\n"), (b"a\nb\n", b"", 4))
        self.assertEqual(_split_committed_prefix(b"a\nb"), (b"a\n", b"b", 2))
        self.assertEqual(_split_committed_prefix(b"abc"), (b"", b"abc", 0))

    def test_a4_empty_file_and_lone_partial_first_line(self):
        # Edge cases that must open: an empty record file (0 events, nothing set aside), and a file
        # that is ONLY an unterminated first line — a crash before the first newline — opens empty
        # with the whole partial line kept aside.
        self._write(b"")
        s = EventStore(self.path)
        self.assertEqual(len(s.events), 0)
        self.assertIsNone(s.set_aside_tail)
        lone = _rec(0)[:10]                                # a partial first line, no newline
        self._write(lone)
        s2 = EventStore(self.path)
        self.assertEqual(len(s2.events), 0)
        self.assertEqual(s2.set_aside_tail["offset"], 0)
        self.assertEqual(s2.set_aside_tail["length"], len(lone))

    # -- A5 ----------------------------------------------------------------------------------------
    def test_a5_recover_law_reused_not_widened_no_new_op(self):
        # The interior-corruption route REUSES the recover law and mints NO op: RECOVER_OP_META is
        # unchanged (its rules are exactly [RECOVER_LAW]), and the route function only builds a named
        # refusal — it registers nothing and cites the existing law/op.
        self.assertEqual(erasure.RECOVER_OP_META["rules"], [erasure.RECOVER_LAW],
                         "the recover law is reused, never widened")
        exc = erasure.interior_corruption_at_load(self.path, 3, b"partial", ValueError("boom"))
        self.assertIsInstance(exc, erasure.LoadInteriorCorruption)
        self.assertEqual(exc.recover_op, erasure.RECOVER_OP)   # cites the existing op, mints none
        self.assertEqual(exc.line_index, 3)
        self.assertEqual(exc.byte_length, len(b"partial"))

    # -- OUTSIDE-5 non-weakening --------------------------------------------------------------------
    def test_outside_5_reader_demotion_is_not_weakened(self):
        # This unit changes the loader's corrupt-line handling only. OUTSIDE-5's reader demotion is
        # untouched: a second same-process open over a live-writer record is still a READER, still
        # computes views, still refuses append BY NAME — and my change adds NO spurious set-aside on
        # a properly terminated record.
        writer = EventStore(self.path, lock=True)
        try:
            writer._append({"actor": "SYSTEM", "action": "CREATE-INFO", "object": "x"})
            self.assertFalse(getattr(writer, "_reader", False), "the first open is the writer")
            reader = EventStore(self.path, lock=True)      # second open -> a reader
            try:
                self.assertTrue(getattr(reader, "_reader", False), "the second open is demoted to a reader")
                self.assertEqual(len(reader.events), len(writer.events), "the reader computes the record")
                self.assertIsNone(reader.set_aside_tail, "a terminated record sets nothing aside")
                with self.assertRaises(ReaderCannotAppend):
                    reader._append({"actor": "SYSTEM", "action": "X", "object": "y", "rule_cited": "R"})
            finally:
                reader.close()
        finally:
            writer.close()


if __name__ == "__main__":
    unittest.main()
