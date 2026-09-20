# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: build-test ·
# Vocabulary is OS-architecture (INPUT, as-of, socket four-tuple, entity name) per the seL4/gVisor
# literature. NON-GOAL: no offensive capability of any kind — this proves a governed record reads a
# stale peer picture AS stale and never promotes a socket address into an identity, by function,
# against benign local state. Full declaration: SCOPE-STATEMENT.md.
"""P17 — HONEST STATE ACROSS THE BOUNDARY (B13), proven over existing mechanisms.

design/52 B13: "A stale picture of a peer reads as stale, and a four-tuple names a socket, never an
entity." This lands the two halves as regression tests (charter: every verification probe lands as a
regression test), each ABLE TO FAIL, each earned:

  A1  A STALE PICTURE READS AS STALE. A peer-state observation is a peer-origin INPUT (I7:
      source='peer', record_class='INPUT' — authority.peer_fact_admitted_class) carrying its as-of.
      Whether it "reads as stale" is a DERIVED property — the as-of of the observation against the
      latest superseding observation of the same peer (archi :3615 precision 1) — NEVER a stored
      'stale' flag on the row. Same discipline as crossing.py's staleness: compute the state, never
      store it (crossing.stale_crossings' docstring, P2; the latest-wins-per-object as_of read of
      pack_content:178-184). The SAME observation reads FRESH before it is superseded and STALE after
      — the verdict lives in the record set, not on the row.

  A2  A STALE-AS-CURRENT READ IS CAUGHT (positive control). A planted read that treats a superseded
      observation as the current confirmed fact is caught by the honest derivation (which marks it
      stale); the honest read of the same set returns the LATER observation as the current fact. The
      check discriminates — a genuinely-latest observation is not marked stale — so an empty result on
      an honest read is not a check that cannot fail (applying-these-rules R3).

  A3  A FOUR-TUPLE NAMES A SOCKET, NEVER AN ENTITY. A census over the RECORD's name-bearing slots
      (actor, object, target, from_body, any identity field — archi :3615 precision 2), run over the
      REAL estate's records (real socket acts recording addresses, a real receipt naming a body),
      finds NO socket four-tuple used as a body's NAME. A body's name is (bound key, genesis hash)
      (I11 / border.from_body_name); a four-tuple fails that shape. The four-tuples that DO appear sit
      in the socket ops' recorded-address (transport) slots, so the census's emptiness is EARNED, not
      vacuous. A planted promotion — a row putting a four-tuple where a (key, genesis) name belongs —
      is caught.

GREEN, over existing mechanisms. No new op/law/check kind, no pack edit, no bump, no founding move.
The socket ops and their recorded address, crossing.py's as-of/staleness, peer-origin INPUT (I7,
authority.py) and the body-name shape (I11, border.py) are READ and REUSED, never re-authored;
SPIKE-1's findings are cited (planning/evidence/SPIKE-1/FINDINGS.md:115-119), never edited.

Runner of record — PER-MODULE, isolation-clean (:3158):
    PYTHONPATH=src:tests python3 -m unittest tests.test_p17_honest_state -v
"""

import os
import sys
import tempfile
import unittest
from collections.abc import Mapping

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from kernel.compose import build_full_kernel                            # noqa: E402
from kernel import authority, border                                   # noqa: E402
from observe import classmap                                           # noqa: E402


# =============================================================================================
# The two shapes B13 keeps apart: a body's NAME vs a socket FOUR-TUPLE.
# =============================================================================================

def is_body_name(v):
    """A body's NAME is the pair (bound system key, genesis hash) — I11 / border.from_body_name
    (D08.42): a mapping carrying a `key` and a `genesis`, NO issuer, no real-world data. Nothing else
    is a body's name."""
    return isinstance(v, Mapping) and "key" in v and "genesis" in v


def is_socket_four_tuple(v):
    """A socket FOUR-TUPLE is a TRANSPORT address — an endpoint the socket ops record ("127.0.0.1:0",
    "10.0.0.9:51000") or a full (local_host, local_port, peer_host, peer_port) tuple. Routable,
    reusable, OS-reassigned (SPIKE-1:64): it names a socket, never an entity. It is NOT a body name
    (a mapping of (key, genesis)) — the two shapes are disjoint by construction, which is exactly the
    line B13 holds."""
    if is_body_name(v):
        return False
    if isinstance(v, str):
        # host:port — the endpoint form the socket ops record as a transport fact. The host is an
        # internet address (dotted): requiring the dot keeps a governance object id ("grant:5",
        # "op:SOCKET-CONNECT", "account:web") from reading as a socket address.
        host, sep, port = v.rpartition(":")
        return bool(sep) and ("." in host) and port.isdigit()
    if isinstance(v, (tuple, list)):
        # (host, port) endpoint, or the full four-tuple (lhost, lport, phost, pport).
        if len(v) == 2 and isinstance(v[0], str) and isinstance(v[1], int) and not isinstance(v[1], bool):
            return True
        if len(v) == 4:
            return True
    return False


#: The RECORD slots that NAME a body/entity — where a (key, genesis) name belongs, never a four-tuple
#: (archi :3615 precision 2). Top-level identity slots + the payload slots that carry a body's name.
NAME_SLOTS_TOP = ("actor", "object", "target")
IDENTITY_PAYLOAD_KEYS = ("from_body", "entity", "willed_by", "willing_entity")


def _is_identity_key(k):
    return k in IDENTITY_PAYLOAD_KEYS or any(t in k.lower() for t in ("identity", "body_name"))


def four_tuples_in_name_slots(records):
    """THE PROMOTION CENSUS (B13, half 2). Every record slot that NAMES a body — actor/object/target
    at the top level, plus a payload identity field — holding a socket FOUR-TUPLE. EMPTY on any real
    world by construction: names are (key, genesis), and the four-tuples a record carries live in the
    socket ops' recorded-address (transport) slots, not in a name slot. ABLE TO FAIL: hand it a row
    that puts a four-tuple where a (key, genesis) name belongs and it fires (the EP-49A/border census
    discipline — read from the SET, catch the plant by I11's name shape). A pure predicate over any
    iterable of records; it appends nothing and decides nothing."""
    hits = []
    for r in records:
        for slot in NAME_SLOTS_TOP:
            if is_socket_four_tuple(r.get(slot)):
                hits.append((r.get("action"), slot, r.get(slot)))
        for k, v in (r.get("payload") or {}).items():
            if _is_identity_key(k) and is_socket_four_tuple(v):
                hits.append((r.get("action"), "payload." + k, v))
    return hits


#: The socket ops' recorded-address (TRANSPORT) slots — where a four-tuple LEGITIMATELY names a
#: socket. Used to prove the promotion census is non-vacuous: four-tuples are present as transport
#: facts while none names an entity.
TRANSPORT_PAYLOAD_KEYS = ("address", "target", "peer")


def transport_addresses(records):
    """Every socket four-tuple recorded as a TRANSPORT FACT — the address a SOCKET-BIND/CONNECT/ACCEPT
    carries in its payload. A four-tuple HERE names a socket, and that is correct (B13's other half).
    Its presence is what makes the promotion census's emptiness EARNED, not a quiet box."""
    out = []
    for r in records:
        p = r.get("payload") or {}
        for k in TRANSPORT_PAYLOAD_KEYS:
            if is_socket_four_tuple(p.get(k)):
                out.append((r.get("action"), k, p.get(k)))
    return out


# =============================================================================================
# The peer-state observation and the DERIVED staleness (B13, half 1). A peer-origin INPUT row;
# whether it reads as stale is computed from the record set, never stored (P2 / crossing.py).
# =============================================================================================

def observation(peer, state, as_of):
    """A peer-state observation, shaped as the peer-origin INPUT it is (I7): source='peer',
    record_class='INPUT' (the world's claim, never a decision the record authored — design/51 N4).
    It carries its AS-OF: the point at which it was observed. It carries NO staleness verdict — that
    is derived."""
    return {"action": "peer-state-changed", "object": peer, "target": None,
            "payload": {"source": "peer", "record_class": classmap.INPUT,
                        "act": "peer-state-changed", "state": state},
            "as_of": as_of}


def _as_of(o):
    return o["as_of"]


def current_picture(observations, as_of):
    """The record's CURRENT confirmed picture of every peer AS OF a point: latest-wins per peer among
    observations at or before `as_of`. This is crossing.py's pack_content shape (store.all(as_of) ->
    latest[object] = the newest row for it, :178-184) — the as-of read, reused, not re-authored."""
    latest = {}
    for o in sorted(observations, key=_as_of):
        if _as_of(o) <= as_of:
            latest[o["object"]] = o
    return latest


def reads_as_stale(observation_row, observations, as_of):
    """DERIVED, never stored (archi :3615 precision 1): this observation reads AS stale iff the current
    picture's latest observation of its peer is a LATER observation — the as-of of the observation
    against the latest superseding observation. Same discipline as crossing.crossings' 'superseded'
    state: a fact about the record set, computed here, held nowhere. An observation that IS the latest
    for its peer is an input NOT YET SUPERSEDED — it reads fresh."""
    latest = current_picture(observations, as_of).get(observation_row["object"])
    return latest is not None and _as_of(latest) > _as_of(observation_row)


# =============================================================================================
# A1 — A STALE PICTURE READS AS STALE
# =============================================================================================

class TestA1StaleReadsAsStale(unittest.TestCase):
    def test_a_peer_state_observation_is_a_peer_origin_INPUT_carrying_its_as_of(self):
        o1 = observation("peer:P", "connected", 1)
        # peer-origin INPUT, never a decision (I7 / design/51 N4): the estate's own admitted class and
        # the trust-failure census both agree it is honest.
        self.assertEqual(o1["payload"]["record_class"], authority.peer_fact_admitted_class())
        self.assertEqual(authority.peer_fact_admitted_class(), classmap.INPUT)
        self.assertEqual(authority.peer_facts_authored_as_decision([o1]), [])
        # it carries its as-of (WHEN observed) — an honest fact about the observation ...
        self.assertEqual(o1["as_of"], 1)
        # ... and it carries NO staleness verdict on the row: staleness is derived, never stored.
        self.assertNotIn("stale", o1)
        self.assertNotIn("superseded", o1)
        self.assertNotIn("stale", o1["payload"])
        self.assertNotIn("superseded", o1["payload"])

    def test_the_latest_observation_is_the_current_fact_and_reads_fresh(self):
        o1 = observation("peer:P", "connected", 1)
        obs = [o1]
        # the only observation is the current confirmed fact; nothing supersedes it -> reads fresh.
        self.assertIs(current_picture(obs, 1)["peer:P"], o1)
        self.assertFalse(reads_as_stale(o1, obs, 1))

    def test_a_superseded_observation_reads_AS_stale_derived_not_stored(self):
        o1 = observation("peer:P", "connected", 1)
        o2 = observation("peer:P", "closed-by-peer", 2)   # the peer moved; a later observation
        # BEFORE the later observation exists, o1 reads fresh (an input not yet superseded).
        self.assertFalse(reads_as_stale(o1, [o1], 1))
        # AFTER it lands, the SAME o1 reads AS stale — the verdict changed with the record set, not
        # with the row (o1 is byte-for-byte unchanged). This is the derivation, asserted.
        self.assertTrue(reads_as_stale(o1, [o1, o2], 2))
        self.assertNotIn("stale", o1)                     # the row never grew a flag
        self.assertNotIn("stale", o1["payload"])
        # the current confirmed fact is the LATER observation, never the superseded one promoted to
        # current (the honest peer picture: closed-by-peer, not the stale 'connected').
        self.assertIs(current_picture([o1, o2], 2)["peer:P"], o2)

    def test_staleness_keys_on_the_peer_a_different_peer_does_not_stale_this_one(self):
        o1 = observation("peer:P", "connected", 1)
        oQ = observation("peer:Q", "connected", 2)        # a LATER observation of ANOTHER peer
        obs = [o1, oQ]
        # o1 is still the latest for peer:P; peer:Q's later observation does not supersede it.
        self.assertFalse(reads_as_stale(o1, obs, 2))
        self.assertIs(current_picture(obs, 2)["peer:P"], o1)

    def test_a_peer_fact_authored_as_a_decision_is_caught_I7(self):
        # I7's shape held at observation scale: a peer's claim marked DECISION (a fact the box
        # decided rather than the world claimed) is caught; the honest INPUT observation is not.
        planted = {"payload": {"source": "peer", "record_class": "DECISION", "state": "connected"}}
        self.assertEqual(len(authority.peer_facts_authored_as_decision([planted])), 1)
        honest = observation("peer:P", "connected", 1)
        self.assertEqual(authority.peer_facts_authored_as_decision([honest]), [])


# =============================================================================================
# A2 — A STALE-AS-CURRENT READ IS CAUGHT (positive control; the check can fail)
# =============================================================================================

class TestA2StaleAsCurrentCaught(unittest.TestCase):
    def setUp(self):
        self.o1 = observation("peer:P", "connected", 1)
        self.o2 = observation("peer:P", "closed-by-peer", 2)
        self.obs = [self.o1, self.o2]

    def test_a_planted_read_presenting_a_superseded_observation_as_current_is_caught(self):
        # A BROKEN reader that always returns the FIRST observation as "the current confirmed fact",
        # ignoring supersession — the exact promotion B13's first half forbids.
        def planted_current(observations):
            return observations[0]

        presented = planted_current(self.obs)
        # the honest derivation CATCHES it: what the planted read calls current reads AS stale.
        self.assertTrue(reads_as_stale(presented, self.obs, 2))

    def test_the_honest_read_returns_the_later_observation_and_is_not_stale(self):
        # the honest reader returns the current picture's latest — and THAT does not read as stale.
        honest_current = current_picture(self.obs, 2)["peer:P"]
        self.assertIs(honest_current, self.o2)
        self.assertFalse(reads_as_stale(honest_current, self.obs, 2))

    def test_the_check_discriminates_stale_from_current(self):
        # the same check that fires on the superseded o1 stays quiet on the current o2 — able to fail
        # AND able to pass, so an empty result on an honest read is not a check that cannot fail.
        self.assertTrue(reads_as_stale(self.o1, self.obs, 2))    # superseded -> caught
        self.assertFalse(reads_as_stale(self.o2, self.obs, 2))   # current    -> clean


# =============================================================================================
# A3 — A FOUR-TUPLE NAMES A SOCKET, NEVER AN ENTITY (census over the REAL estate)
# =============================================================================================

class TestA3FourTupleNamesASocket(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="p17-a3-")
        self.store, self.gate, self.views, self.blobs, self.subs = build_full_kernel(
            os.path.join(self.dir, "record.jsonl"), os.path.join(self.dir, "blobs"),
            os.path.join(self.dir, "vault"))
        # an established entity to open sockets by, and the six wire acts recording their addresses
        # (four-tuples) as TRANSPORT FACTS in the socket ops' payload (the recorded address).
        self.gate.execute("CREATE-ACCOUNT", "owner", {"account_id": "web", "actor_class": "human"})
        self.gate.execute("SOCKET-OPEN", "web", {"entity": "web", "socket": "s1", "family": "inet"})
        self.gate.execute("SOCKET-BIND", "web", {"socket": "s1", "address": "127.0.0.1:0"})
        self.gate.execute("SOCKET-LISTEN", "web", {"socket": "s1"})
        self.gate.execute("SOCKET-CONNECT", "web", {"socket": "s1", "target": "93.184.216.34:443"})
        self.gate.execute("SOCKET-ACCEPT", "web", {"socket": "s1", "peer": "10.0.0.9:51000"})
        # a real RECEIPT: a body's NAME (bound key, genesis hash) lives in a name slot (from_body),
        # the (key, genesis) shape, NOT a four-tuple.
        a_row = {"action": "BORDER-SUBMIT", "object": "peer", "target": None,
                 "payload": {"kind": "border-submit", "want": "read /x"}}
        self.fb = border.from_body_name("ed25519-pub:sender", border.genesis_hash(self.store))
        border.record_receipt(self.gate, border.content_id(a_row), self.fb, "ed25519-sig:z")
        self.records = self.store.all()

    def test_no_four_tuple_names_a_body_in_the_real_estate(self):
        # THE CENSUS IS EMPTY: not one name-bearing slot in the whole record holds a four-tuple.
        self.assertEqual(four_tuples_in_name_slots(self.records), [])

    def test_the_emptiness_is_earned_four_tuples_are_present_as_transport_facts(self):
        # the socket ops DID record addresses (four-tuples) — in their transport slots. So the census
        # above is empty because names are names, not because the estate has no four-tuples at all.
        present = transport_addresses(self.records)
        self.assertTrue(present, "no transport four-tuple recorded — the empty census is vacuous")
        # every one of them is a four-tuple naming a SOCKET (the bind/connect/accept addresses).
        for _act, _slot, v in present:
            self.assertTrue(is_socket_four_tuple(v))

    def test_the_receipts_from_body_is_a_key_genesis_name_never_a_four_tuple(self):
        # the one name slot that carries a federated body name holds the (key, genesis) shape ...
        self.assertTrue(is_body_name(self.fb))
        # ... and that shape is NOT a four-tuple: the two are disjoint (the line B13 holds).
        self.assertFalse(is_socket_four_tuple(self.fb))

    def test_RW_PROMOTION_a_four_tuple_in_a_name_slot_is_caught(self):
        # THE PLANT (able to fail): a four-tuple put where a (key, genesis) name belongs — in each of
        # the name-bearing slots the census reads. Every one is caught.
        plants = [
            {"action": "RECEIPT", "object": "x", "target": None,
             "payload": {"kind": "receipt", "from_body": "127.0.0.1:443"}},        # a name slot
            {"action": "SOCKET-OPEN", "object": ("127.0.0.1", 5000, "1.2.3.4", 443),
             "payload": {}},                                                        # object as name
            {"action": "BORDER-SUBMIT", "object": "x", "target": None,
             "payload": {"entity": "10.0.0.9:51000"}},                             # entity as name
            {"actor": "192.168.1.5:22", "action": "X", "object": "y", "payload": {}},  # actor as name
        ]
        for p in plants:
            self.assertTrue(four_tuples_in_name_slots([p]),
                            "a four-tuple promoted to a name went uncaught: " + str(p))

    def test_the_census_discriminates_honest_names_and_transport_facts_pass(self):
        # an honest receipt (from_body a (key, genesis) name) is NOT caught ...
        honest_receipt = {"action": "RECEIPT", "object": "x", "target": None,
                          "payload": {"kind": "receipt", "from_body": self.fb}}
        self.assertEqual(four_tuples_in_name_slots([honest_receipt]), [])
        # ... nor is a socket record carrying its address in a TRANSPORT slot (a four-tuple naming a
        # socket, which is correct — the census fires only on a four-tuple naming a BODY).
        socket_rec = {"action": "SOCKET-CONNECT", "object": "s1", "target": None,
                      "payload": {"socket": "s1", "target": "93.184.216.34:443"}}
        self.assertEqual(four_tuples_in_name_slots([socket_rec]), [])


if __name__ == "__main__":
    unittest.main()
