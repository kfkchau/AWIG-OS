# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture ·
# Vocabulary is OS-architecture per OS textbooks and the seL4/gVisor literature.
# NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.
"""M2 custody: the DERIVED filesystem state the mount serves from (EP-25 W2).

WHAT THIS IS, said before the code because it is the whole difference between this
subsystem and the thing it refuses to be. The STORE is the definitive. The directory
tree, the inode table, the link counts, the sizes, the modes, the extended attributes
and the fd table are DERIVED CACHES of recorded decisions — every one of them
reconstructible by folding the record and nothing else. Serving a `stat` is consulting
a view. Serving a `read` is consulting a view plus a content-addressed blob the record
named. Serving a `write` is a gated decision whose durable append PRECEDES the reply.

THE WRONG REFERENCE THIS REFUSES: a passthrough filesystem with a log bolted on — the
record as a journal OF the filesystem instead of the filesystem as a VIEW of the record.
Nothing in this module calls the host filesystem to answer what a file contains, what a
directory holds, or what a mode is. The only host-filesystem reads are the content-
addressed blobs, fetched BY THE HASH THE RECORD CARRIES, which is the record answering
through a hash rather than the host answering through a path. Kill everything here,
replay the record alone, and the same filesystem comes back — that is T-CUSTODY-IS-
DERIVED, and it is the leg the journaling template dies on.

TWO FOLDS, ONE RULE. `CustodyState` is maintained INCREMENTALLY (an on-append listener),
because folding the whole record on every `getattr` would make the mount's cost track the
record's length — the defect design/36 ADDENDUM C rules a class. `fold()` is the same
derivation computed from scratch. They are one implementation reading two record sources
(the EP-24B rule: one fold, varied source, never two implementations that could diverge
in logic as well as in input), and SHADOW-DIFF asserts them equal continuously. The
incremental structure is therefore a pure acceleration under P2 and is proven so rather
than promised.

THE NAMESPACE IS HELD UNDER THREE INDEXES OF ONE FACT [EP-28E W2, design/36 ADDENDUM Q].
`names` answers "which inode is at this path". `kids` answers "which names are in this
directory". `paths` answers "which names is this inode reachable by". They are the SAME
binding set — a name bound to an inode — rendered by the key each read asks about, and
every one of them is written at a single chokepoint (`_bind` / `_unbind`) that `apply()`
calls wherever a name enters or leaves. There is no fourth structure and no second
implementation: a name cannot be in one index and absent from another, because entering
the namespace is one operation.

WHY THIS IS NOT THE THING EP-28E's PLAN NAMED AS ITS WRONG REFERENCE. "Cache the answer"
holds a computed ANSWER and needs invalidating, and an invalidation is a second opinion
about what the record says. Nothing here holds an answer: `children()` still computes its
list at every call, from state the fold maintains, and the fold is rebuilt from the record
alone by `fold()`. The test is the one design/36 ADDENDUM Q's ruling states — kill the
whole structure, replay the record, and it comes back identical — and it is
`snapshot()`-carried, so SHADOW-DIFF runs that comparison continuously instead of once.

WHY THE READS GOT FASTER AND WHAT THE PROPERTY ACTUALLY IS. Not "readdir is quick now".
The property is design/36 ADDENDUM Q §Q.4's: a derived answer costs its own dependencies.
Listing a directory holding one entry examines one entry, at any namespace size, because
the answer depends on that directory's entries and on nothing else. Before this, it
examined every name in the namespace — 96,002 of them to answer about one — which is the
measured defect ADDENDUM P found and ADDENDUM Q re-attributed to the namespace.

WHAT IS UNBOUNDED HERE, NAMED RATHER THAN LEFT TO BE FOUND: `snapshot()`, and only
`snapshot()`. It walks everything, and that is the rule OBEYED rather than waived — its
answer IS the whole namespace, so the whole namespace is its dependency. `nlink()` walked
the namespace twice until EP-28E W5 and now costs the one inode's bindings and, on a
directory, that one directory's entries. It was the third and last instance of the class on
a served read path, so the EP-28E W3 guard's defect ledger is EMPTY: no read here is
unbounded in something its answer does not depend on. An empty ledger is a claim, so the
guard is required to still catch a planted one (`tests/test_ep28e_w5.py`) rather than pass
by having nothing to iterate.
"""

import hashlib
import stat as statmod

#: The namespaces whose extended-attribute writes are PRESCRIPTIVE — they change what is
#: permitted rather than what is stored — and therefore record as LAW whichever syscall
#: carries them (design/10 §11.1b, ruled at EP-25 ADDENDUM 3). The syscall is transport;
#: the content decides the class. Data, in one place, because a reader has to be able to
#: see which attribute names are law-making without reading the mount.
LAW_XATTR_PREFIXES = ("security.", "system.posix_acl_")

#: Every action this subsystem appends, mapped to the recording class design/10 §6 assigns
#: it. THE TARGET'S OWN DECLARATION: the conformance harness reads this as data and holds
#: no vocabulary of its own, so the mount and the in-kernel module after it are judged by
#: the same instrument without either being rebuilt for it (tools/conformance README).
#: A record whose action is absent here fails check 2 as unclassified, which is the honest
#: outcome for an action nobody classified.
CUSTODY_CLASS_MAP = {
    # --- the custody grant and its release (design/10 §6, open/close rows) ---
    "FILE-OPEN": "DECISION",
    "FILE-CLOSE": "DECISION",
    # --- exclusivity over a byte range (design/10 §6, the fcntl/flock rows) ---
    "FILE-LOCK": "DECISION",
    "FILE-UNLOCK": "DECISION",
    # --- content (never sampled; full-fidelity to a content-addressed blob) ---
    "FILE-WRITE": "DECISION",
    "FILE-TRUNCATE": "DECISION",
    # --- namespace ---
    "FILE-CREATE": "DECISION",
    "FILE-MKDIR": "DECISION",
    "FILE-RMDIR": "DECISION",
    "FILE-LINK": "DECISION",
    "FILE-SYMLINK": "DECISION",
    "FILE-UNLINK": "DECISION",
    "FILE-RENAME": "DECISION",
    # --- metadata that amends a file's permission or attributes ---
    "FILE-PERM": "DECISION",
    "FILE-CHOWN": "DECISION",
    "FILE-TIMES": "DECISION",
    "FILE-XATTR-SET": "DECISION",
    "FILE-XATTR-REMOVE": "DECISION",
    # --- prescriptive attribute content: LAW, whichever syscall carried it ---
    "FILE-XATTR-LAW": "LAW",
    # --- the namespace's own rules ---
    "MOUNT": "LAW",
    "UNMOUNT": "LAW",
    # --- read traffic: the audit AGGREGATE is STREAM; the caller's bytes are always exact ---
    "FILE-READ-AGGREGATE": "STREAM",
    # --- identity at the port: a recorded mapping act, never a synchronized user table ---
    "MAP-UID": "DECISION",
    # --- a handle handed from one entity to another: the custody plane's only act whose
    # --- subject is a RELATION BETWEEN TWO PARTIES rather than a fact about a file (EP-30-C3)
    "FILE-CUSTODY-TRANSFER": "DECISION",
    # --- the assume's own safety catch ---
    "CUSTODY-HALT": "DECISION",
    # --- refusals the gate itself records (design/10 §11.1a class REFUSAL) ---
    "op-refused": "DECISION",
}

#: The actions the custody fold reacts to. A record outside this set cannot change what the
#: mount serves, which is why the store's own records (grants, laws, accounts) can share the
#: one stream without the filesystem noticing them (design/36 §5: one stream, class-tagged).
CUSTODY_ACTIONS = (
    "FILE-CREATE", "FILE-MKDIR", "FILE-SYMLINK", "FILE-WRITE", "FILE-TRUNCATE",
    "FILE-LINK", "FILE-UNLINK", "FILE-RMDIR", "FILE-RENAME", "FILE-PERM",
    "FILE-CHOWN", "FILE-TIMES", "FILE-XATTR-SET", "FILE-XATTR-REMOVE", "FILE-XATTR-LAW",
)

#: The actions the LOCK fold reacts to, kept apart from CUSTODY_ACTIONS because they change
#: a different thing: the namespace fold answers what a file IS, the lock fold answers who
#: holds exclusivity over part of one. Neither is stored — both are folds of the record.
LOCK_ACTIONS = ("FILE-LOCK", "FILE-UNLOCK")

#: The actions that FOUND a node — the three whose records bring an identity into existence
#: rather than referring to one an earlier record founded. NAMED HERE, ONCE, because two
#: readers now need the same answer: the fold, which derives a formal name for exactly these,
#: and the kernel port's reply, which has to know whether the record it just appended founded
#: anything. A second copy of this tuple in the other file would be one computation duplicated
#: across a boundary by convention, which is the class §A52 exists to close — and the two
#: copies would drift the first time a fourth minting op arrived.
MINTING_ACTIONS = ("FILE-CREATE", "FILE-MKDIR", "FILE-SYMLINK")

#: The root's inode number. Named because it is load-bearing in two places at once: the
#: fold mints it, and BOTH PORTS have to recognise it as the one inode no record describes.
#: There is no FILE-CREATE behind the root — the mount exists before anything is created in
#: it — so the fold has nothing to say about who owns it, and each port answers that one
#: unrecorded question with the serving identity. A magic 1 in two files would be the same
#: fact stated twice, which is how the two stances start disagreeing about it.
#:
#: [EP-28C W4b, 2026-08-03 — THE ROOT IS RULED SUBSTRATE, and the ruling is stated where the
#: number lives.] `governed-state = f(LAW, DECISIONS, INPUTS)` does NOT hold for this inode:
#: it is in the state and in no decision, and `MOUNT` is not in CUSTODY_ACTIONS at all. Two
#: dispositions existed and the derivation picks one. (a) MOUNT mints it BY RECORD — which
#: needs every world already on disk to grow a record it does not have, so the fold would
#: need a FALLBACK for worlds without one, and a fallback standing behind an identity is the
#: exact shape this pass exists to delete. (b) The mount's own existence is SUBSTRATE — the
#: surface decisions are recorded ABOUT — exactly as the store's own persistence is substrate
#: under `design/36` ADDENDUM K, ruled rather than assumed. A record cannot describe the
#: container it is written into.
#: **(b) is RULED here by derivation and RAISED for the owner's word rather than accepted.**
#: It is not a sentence: `tests/test_ep28c_w4b.py` requires that a folded state hold EXACTLY
#: ONE identity with no covering record and that it be this one — a second reds.
#: And the C half makes the exclusion structural rather than merely convenient:
#: `govos_fill_super` mints the root BEFORE any crossing exists, so it CANNOT be told.
ROOT_INO = 1

#: WHERE A RENDERED IDENTITY LIVES, and why the floor is a power of two rather than a taste.
#: A derived identity is a PATH; POSIX's `st_ino` and the Linux VFS's `i_ino` need an
#: INTEGER; the integer is therefore a RENDERING of the identity and never the identity.
#: Renderings occupy [2**62, 2**63) and allocator-minted integers occupy the small numbers,
#: so the two spaces are disjoint BY CONSTRUCTION rather than by probability — a record file
#: written first by the stamping FUSE port and then by the deriving kernel port can never
#: have one kind collide with the other. Both fit `unsigned long` on the ports' architecture
#: and `long long` on the wire, which is what the module's `%lld` and `kstrtoul` need.
RENDER_FLOOR = 1 << 62

#: WHERE A FORMAL NAME LIVES, and why it is a BAND and not a bare `seq` (EP-28S).
#:
#: THE THREE SPACES, PAIRWISE DISJOINT BY CONSTRUCTION rather than by probability:
#:
#:     [1, 2**61)          allocator stamps — every world the FUSE port wrote
#:     [2**61, 2**62)      FORMAL NAMES — SEQ_FLOOR + the birth act's record coordinate
#:     [2**62, 2**63)      renderings of a recorded PATH identity — 62-bit digests
#:
#: WHY THE FORMAL NAME IS NOT THE BARE `seq`. An allocator stamp and a `seq` are BOTH small
#: positive integers, so a bare coordinate would be told from a stamp only by PROVENANCE —
#: by which allocator produced it — while `render_ino` is a PURE FUNCTION OF THE VALUE, which
#: is exactly the property that lets the C half PARSE what the brain rendered instead of
#: computing an answer of its own. A rendering that had to know who minted an integer could
#: not stay pure. Lifting the coordinate into its own band makes the value SELF-DESCRIBING
#: and leaves the rendering exactly as pure as it is today.
#:
#: A world recorded before this law keeps serving the numbers it always served: its stamps
#: sit in the first band and its path renderings in the third, and neither can be mistaken
#: for a formal name. That is what makes this pass PROSPECTIVE without a migration.
SEQ_FLOOR = 1 << 61

KIND_FILE = "file"
KIND_DIR = "dir"
KIND_LINK = "link"
#: A FIFO is a NAME AND A TYPE in this namespace and nothing more: its data path is the
#: kernel's own pipe, which never reaches a filesystem, so custody of a fifo is custody of
#: its existence, its type and its permission — all three recorded. A FIFO IS NOT A DEVICE
#: NODE: a device node names a driver by major/minor and is therefore a capability
#: reference, which is the device subsystem's (EP-29) and is refused here.
KIND_FIFO = "fifo"

#: What a FILE-CREATE record's `node_type` may say, mapped to this fold's kinds. A record
#: that carries none is a regular file — every create before the type was recorded was one.
NODE_KINDS = {"file": KIND_FILE, "fifo": KIND_FIFO}


def is_law_xattr(name):
    """Is this attribute name PRESCRIPTIVE content? (design/10 §11.1b.) A POSIX ACL or a
    security attribute is a rule with a one-file scope, so setting one is law-making."""
    return any(name.startswith(p) for p in LAW_XATTR_PREFIXES)


def _norm(path):
    """The namespace's canonical spelling of a path. The mount's root is '/'."""
    if not path or path == "/":
        return "/"
    return "/" + path.strip("/")


def parent_of(path):
    p = _norm(path)
    if p == "/":
        return None
    head = p.rsplit("/", 1)[0]
    return head or "/"


def basename(path):
    return _norm(path).rsplit("/", 1)[-1]


class Inode:
    """One inode's derived state. Nothing here is stored: every field is the latest value
    the record carries for this inode, and `nlink` is not a field at all — it is counted
    from the namespace, because a link count that is stored is a link count that can rot."""

    __slots__ = ("identity", "ino", "kind", "perm", "uid", "gid", "content_hash", "size",
                 "atime", "mtime", "ctime", "xattrs", "target")

    def __init__(self, identity, kind, perm, uid=0, gid=0, ctime=0.0):
        #: WHAT THE RECORD SAID, and WHAT THE PORTS SERVE, side by side and never confused
        #: (EP-28C W4b). `identity` is the value the RECORD names, and there are now THREE
        #: kinds of world in this one field (EP-28S): a FORMAL NAME — the birth act's own
        #: record coordinate, for anything founded at 1.18.0 or later and the only kind a
        #: new world mints; a PATH, for a world founded between 1.14.0 and 1.17.0 under the
        #: class-wide `param_defaults {"inode": "$path"}`; and a legacy integer for every
        #: world the stamping FUSE port wrote. The three occupy disjoint number bands after
        #: rendering, so one world can hold all three and no read is ambiguous — which is
        #: what makes the identity law PROSPECTIVE and needs no migration.
        #: SINCE EP-28O A RECORDED PATH ARRIVES IN THIS
        #: MODULE'S OWN CANONICAL SPELLING: the law resolves `$path` from the key `_norm`
        #: canonicalised, so a directory made as `/a/` records the identity `/a` and this
        #: fold binds it under `/a` — one spelling, one name, one identity. A record written
        #: BEFORE that pass carries the caller's spelling and is folded exactly as it always
        #: was, which is why every door below still calls `_norm`: an act stands under the
        #: law of its deciding time, spelling included. `ino` is its RENDERING: the integer
        #: POSIX's `st_ino` and the Linux VFS's `i_ino` insist on. The rendering is COMPUTED
        #: from the identity by one function and is not a second source of truth — delete
        #: it, recompute it, and it is the same number.
        self.identity = identity
        self.ino = render_ino(identity)
        self.kind = kind
        self.perm = perm
        self.uid = uid
        self.gid = gid
        self.content_hash = None
        self.size = 0
        self.atime = self.mtime = self.ctime = ctime
        self.xattrs = {}
        self.target = None

    def snapshot(self):
        """The comparable form. Times are deliberately EXCLUDED from the comparison shape:
        they are recorded values like any other, but two derivations of the same record
        produce the same times, so including them adds nothing a divergence could hide in,
        while EXCLUDING nothing else keeps the shape honest."""
        return {
            "ino": self.ino, "kind": self.kind, "perm": self.perm,
            "uid": self.uid, "gid": self.gid, "content_hash": self.content_hash,
            "size": self.size, "xattrs": dict(sorted(self.xattrs.items())),
            "target": self.target,
        }


class CustodyState:
    """The derived filesystem: namespace + inodes, folded from the record.

    Maintained incrementally when driven by `apply()`; rebuilt from nothing by `fold()`.
    The two are the same code — `apply()` IS the fold's per-record body — so shadow-diff
    compares one derivation against itself over two record sources, and a divergence can
    only mean the incremental copy missed a record, never that two implementations
    disagreed about what a record means."""

    def __init__(self):
        self.names = {}     # path -> ino  (the namespace; directories included)
        self.inodes = {}    # ino  -> Inode
        #: THE SAME BINDINGS UNDER THE KEY EACH READ ASKS ABOUT (EP-28E W2). Not a copy of
        #: an answer: a copy of the QUESTION's key. `names` is keyed by the path a lookup
        #: has; `kids` by the directory a listing has; `paths` by the inode a resolve has.
        #: Both are insertion-ordered dicts used as ordered sets — `{basename: None}` and
        #: `{path: None}` — because `path_of` returns the first name an inode was bound
        #: under and a set would not have a first.
        self.kids = {}      # parent path -> {basename: None}
        self.paths = {}     # ino         -> {path: None}
        self.next_ino = 2   # 1 is reserved for the root, minted below
        self.applied = 0    # records folded — the currency stamp
        # THE ROOT, AND THE ONE UNRECORDED IDENTITY IN THE WHOLE STATE. Its identity is the
        # number rather than a path, deliberately: no FILE-CREATE derived it, so there is no
        # `$path` behind it to render, and both ports and the module all know it as 1. That
        # is the substrate exclusion RULED at ROOT_INO above, expressed in the one line that
        # performs it. `render_ino(ROOT_INO)` is ROOT_INO, so the rendering law covers it
        # without a special case anywhere downstream.
        root = Inode(ROOT_INO, KIND_DIR, 0o755)
        self.inodes[root.ino] = root
        self._bind("/", root.ino)

    # ---- the namespace's one door ------------------------------------------------------
    def _bind(self, path, ino):
        """Enter ONE name into the namespace. THE ONLY PLACE A NAME IS EVER ADDED.

        The chokepoint exists for the reason the estate's enforcement always lives at
        one: the three indexes can only disagree if a name enters through a route that
        maintains some of them, and there is no such route. A future action that binds a
        name has to come through here, and if it does not, SHADOW-DIFF says so — the
        indexes are in `snapshot()`, so a served state that missed one stops matching the
        state replayed from the record.

        REBINDING AN OCCUPIED NAME DROPS THE PREVIOUS BINDING FIRST, which is what
        `names[dst] = names.pop(src)` did implicitly when a rename landed on an existing
        name: the inode that held `dst` loses that name and must lose it in `paths` too.
        Getting this wrong is the divergence shadow-diff would catch, which is the point
        of putting it where shadow-diff can see it rather than trusting the code."""
        prev = self.names.get(path)
        if prev is not None:
            if prev == ino:
                return
            self._forget(path, prev)
        self.names[path] = ino
        self.paths.setdefault(ino, {})[path] = None
        parent = parent_of(path)
        if parent is not None:
            self.kids.setdefault(parent, {})[basename(path)] = None

    def _unbind(self, path):
        """Remove ONE name from the namespace, returning the inode it named, or None."""
        ino = self.names.pop(path, None)
        if ino is None:
            return None
        self._forget(path, ino)
        return ino

    def _forget(self, path, ino):
        """Drop one (path, ino) binding from the two derived indexes. An index left holding
        an empty container would make an emptied directory indistinguishable from one that
        never existed in `snapshot()`, so the container goes when its last member does."""
        held = self.paths.get(ino)
        if held is not None:
            held.pop(path, None)
            if not held:
                del self.paths[ino]
        parent = parent_of(path)
        kin = self.kids.get(parent)
        if kin is not None:
            kin.pop(basename(path), None)
            if not kin:
                del self.kids[parent]

    # ---- the one fold body ------------------------------------------------------------
    def apply(self, e):
        """Fold ONE record. Everything the mount serves is decided here and nowhere else."""
        action = e.get("action")
        if action not in CUSTODY_ACTIONS:
            return
        p = e.get("payload") or {}
        ts = e.get("record_time")
        if action in MINTING_ACTIONS:
            path = _norm(p.get("path"))
            # WHAT NAMES THE THING THIS ACT FOUNDS (EP-28S). Two total cases, decided from
            # the RECORD and never from today's law:
            #
            #   the record NAMES an identity   -> that is what named it, and it keeps it
            #   the record NAMES NONE          -> the act's own coordinate names it
            #
            # THE DISCRIMINATOR IS THE RECORD'S OWN SHAPE, AND THAT IS DERIVED RATHER THAN
            # PREFERRED. An act stands under the law of its deciding time, which is why every
            # door in this file still calls `_norm`; reading TODAY's op definition to fold an
            # OLD record would judge a past act by a law it was never under. The record's
            # shape is what the deciding law actually produced, so it is the only honest
            # question to ask here — and it is why the founding's declaration cannot reach
            # this method and does not need to. `apply` takes a record and nothing else.
            #
            # THE TWO CASES CANNOT OVERLAP, and the founding is what makes that true rather
            # than luck. Up to 1.17.0 the three minting ops carried `param_defaults {"inode":
            # "$path"}` CLASS-WIDE, so every lawful birth record names an identity — and one
            # that named none never folded at all, because `render_ino(None)` refuses. From
            # 1.18.0 those ops declare `mints_from: record_coordinate`, take no `inode`
            # parameter and do not write one, so no birth record names an identity at all.
            # What was fatal became the signal.
            #
            # AND THE CALLER'S DOOR IS CLOSED BY THE PAYLOAD, NOT BY A REFUSAL — stated as
            # MEASURED rather than as expected, because the expected version was wrong. A
            # call still carrying `inode` is ADMITTED: this estate's envelope router does not
            # refuse an undeclared parameter for these ops, which `kernel_port.py` asserts in
            # shipped prose that it does. The value is simply dropped, because `payload_from`
            # no longer lists it. The property this fold needs holds either way — a caller
            # cannot put an identity into the record — but the reason is the payload
            # declaration, and writing the refusal here would be a second phantom citation in
            # the file that just repaired one. RAISED at EP-28S.
            identity = p.get("inode")
            if identity is None:
                identity = formal_name(e.get("seq"))
            kind = {"FILE-CREATE": KIND_FILE, "FILE-MKDIR": KIND_DIR,
                    "FILE-SYMLINK": KIND_LINK}[action]
            if action == "FILE-CREATE":
                # WHAT was created is read from the record, defaulting to a regular file: a
                # create that declared no type made one, which is what every create before
                # the type was recorded did. An unrecognised type is NOT guessed at — it
                # falls back to a regular file, and the record still says what was asked for.
                kind = NODE_KINDS.get(p.get("node_type") or "file", KIND_FILE)
            uid, gid = _creator(e)
            node = Inode(identity, kind, _perm(p.get("perm"), kind), uid, gid)
            ino = node.ino
            node.atime = node.mtime = node.ctime = ts
            if kind == KIND_LINK:
                node.target = p.get("target")
                node.size = len((p.get("target") or "").encode("utf-8"))
            # A RENDERING COLLISION REFUSES RATHER THAN OVERWRITING (EP-28C W4b). This is
            # `render_ino`'s stated cap turned into a detectable condition: two DISTINCT
            # identities arriving at one number would otherwise make the second node replace
            # the first in this table, silently, and one file's bytes would be served under
            # another file's name. Re-creating a path after unlinking it is NOT a collision —
            # same identity, same number, which is why the test is on the identity and not on
            # the key's mere presence.
            held = self.inodes.get(ino)
            if held is not None and held.identity != identity:
                raise UnrenderableIdentity(
                    "identities %r and %r both render to %d — the rendering's stated cap has "
                    "been reached in a live namespace, and the fold refuses rather than "
                    "serving one node under the other's number" % (held.identity, identity, ino))
            self.inodes[ino] = node
            self._bind(path, ino)
            # THE ALLOCATOR'S MARK, AND THE GUARD THAT USED TO SKIP HERE (EP-28C W4b).
            # This read `if isinstance(ino, int) and ino >= self.next_ino` and did NOTHING
            # for a derived identity — the mark stopped advancing, stopped tracking the
            # namespace, and NOTHING RED. A guard that reads as defensive and no-ops when its
            # assumption breaks is the class charter §A52 closes with its own last sentence.
            #
            # SO THE TWO CASES ARE TWO BRANCHES, AND THE DISCRIMINATOR IS A FLOOR RATHER
            # THAN A TYPE TEST — the number spaces are disjoint by construction, so "did an
            # allocator hand this out?" is decidable from the value alone. A number the
            # allocator never handed out POISONS the mark instead of leaving it stale, and
            # `mint_ino` refuses from here on citing what it can no longer promise. Stale is
            # the one thing a high-water mark must never be.
            #
            # THE FLOOR MOVED FROM `RENDER_FLOOR` TO `SEQ_FLOOR` (EP-28S) AND THE OLD ONE
            # WOULD NOW BE WRONG IN THE DANGEROUS DIRECTION. A formal name sits BELOW
            # `RENDER_FLOOR`, so the old test read it as allocator-minted and advanced the
            # mark to 2**61 + seq + 1 — a mark that then hands out "fresh" numbers inside the
            # formal-name band, which is the collision this pass exists to delete, rebuilt one
            # layer down by a guard nobody would have re-read. A formal name is not an
            # allocator's, so it poisons the mark exactly as a rendered path identity does.
            if ino < SEQ_FLOOR:
                if self.next_ino is not None and ino >= self.next_ino:
                    self.next_ino = ino + 1
            else:
                self.next_ino = None
        elif action in ("FILE-WRITE", "FILE-TRUNCATE"):
            node = self._node(p)
            if node is not None:
                node.content_hash = p.get("content_hash")
                # ABSENT means the record named no content length — an empty write — and that
                # is a MEANING, stated here rather than laundered through a coercion. PRESENT
                # and unreadable refuses (EP-28C W4b).
                node.size = 0 if p.get("length") is None else _num(p["length"], "length")
                node.mtime = node.ctime = ts
        elif action == "FILE-LINK":
            src = _norm(p.get("target_path"))
            if src in self.names:
                self._bind(_norm(p.get("new_path")), self.names[src])
        elif action in ("FILE-UNLINK", "FILE-RMDIR"):
            self._unbind(_norm(p.get("path")))
        elif action == "FILE-RENAME":
            src = _norm(p.get("path"))
            if src in self.names:
                dst = _norm(p.get("new_path"))
                # A rename over an existing name replaces it — the POSIX contract, and here
                # it is the namespace map doing exactly what the record said, no more. The
                # source is unbound BEFORE the destination is bound, which is the order
                # `names[dst] = names.pop(src)` had: a rename onto itself therefore leaves
                # and re-enters, exactly as it did.
                self._bind(dst, self._unbind(src))
        elif action == "FILE-PERM":
            node = self._node(p)
            if node is not None:
                node.perm = _perm(p.get("perm"), node.kind)
                node.ctime = ts
        elif action == "FILE-CHOWN":
            node = self._node(p)
            if node is not None:
                if p.get("uid") is not None:
                    node.uid = _num(p["uid"], "the chown's uid")
                if p.get("gid") is not None:
                    node.gid = _num(p["gid"], "the chown's gid")
                node.ctime = ts
        elif action == "FILE-TIMES":
            node = self._node(p)
            if node is not None:
                if p.get("atime") is not None:
                    node.atime = p["atime"]
                if p.get("mtime") is not None:
                    node.mtime = p["mtime"]
        elif action in ("FILE-XATTR-SET", "FILE-XATTR-LAW"):
            node = self._node(p)
            if node is not None:
                node.xattrs[p.get("name")] = p.get("value")
        elif action == "FILE-XATTR-REMOVE":
            node = self._node(p)
            if node is not None:
                node.xattrs.pop(p.get("name"), None)

    def _node(self, p):
        """Resolve the inode a metadata record names. The record carries the inode, so a
        rename between the write and the fold cannot misdirect it — the identity is what
        was recorded, never the path it happened to be reachable by."""
        identity = p.get("inode")
        if identity is None:
            return self.inodes.get(self.names.get(_norm(p.get("path"))))
        # RENDERED HERE TOO, and it is the same one function (EP-28C W4b). A record may name
        # the node by the identity the founding derived or by that identity's rendering — a
        # create carries the first, a later act through a port that holds an `i_ino` carries
        # the second — and `render_ino` is the map between them, so both resolve to one node.
        return self.inodes.get(render_ino(identity))

    # ---- the reads the mount serves ---------------------------------------------------
    def lookup(self, path):
        return self.inodes.get(self.names.get(_norm(path)))

    def exists(self, path):
        return _norm(path) in self.names

    def nlink(self, ino):
        """COUNTED, never stored. Directories carry the POSIX 2 + subdirectory convention.

        COSTS THE INODE'S OWN BINDINGS, AND ON A DIRECTORY THAT DIRECTORY'S OWN ENTRIES.
        Before EP-28E W5 this walked the whole namespace twice — once summing every binding
        to find the link count, and again filtering every name by parent to count
        subdirectories — to answer about one inode. It is the THIRD instance of the class
        `design/36` ADDENDUM Q names, and the last one on a served read path.

        THE TWO HALVES ARE NOT SYMMETRIC AND THE ASYMMETRY IS STATED RATHER THAN HIDDEN BY
        THE SPEEDUP. The link count is a LOOKUP: `paths` is keyed by inode and holds exactly
        the names bound to it, so the count is its size. The subdirectory count is a JOIN:
        `kids` holds BASENAMES, not kinds, so each entry is resolved back through `names` and
        `inodes` to ask whether it is a directory. That join is bounded by the one
        directory's entries — which is what the answer depends on, so it satisfies ADDENDUM
        Q §Q.4 — but it is a join per entry and not a single lookup.

        A REAL BEHAVIOUR CHANGE ON AN UNBOUND DIRECTORY INODE, reported as one. `FILE-RMDIR`
        removes the name and leaves the `Inode` in `inodes`, so `path_of` answers None. The
        scan then filtered on `parent_of(c) == None`, which is true for exactly one name —
        the ROOT — so it counted the root as a subdirectory of a directory that is not there
        and answered 3. This asks `kids[None]`, finds nothing, and answers 2. NEITHER NUMBER
        REACHES A CALLER: `records_fs.getattr` resolves through `names` or through an open
        descriptor, and a descriptor is only ever minted for a file; the replay leg iterates
        `names`. Both are asserted by driving them in `tests/test_ep28e_w5.py`, not claimed
        here — the W2 lesson, where an unreachability claim built from reading one branch was
        refuted by its own differential."""
        node = self.inodes.get(ino)
        n = len(self.paths.get(ino) or ())
        if node is not None and node.kind == KIND_DIR:
            path = self.path_of(ino)
            base = "" if path == "/" else path
            subdirs = 0
            for name in self.kids.get(path) or ():
                child = self.inodes.get(self.names.get(base + "/" + name))
                if child is not None and child.kind == KIND_DIR:
                    subdirs += 1
            return 2 + subdirs
        return n

    def path_of(self, ino):
        """A path this inode is reachable by, or None. COSTS THE INODE'S OWN NAMES.

        WHICH path, for an inode with several — and this is a REAL behaviour change from the
        namespace scan that stood here before, stated as one rather than glossed. The scan
        returned the first match in `names` KEY order; this returns the first in BINDING
        order. The two differ whenever a path key is REUSED — bound to one inode, then
        rebound to another — because a reused key keeps its original position in `names`
        while its binding is new.

        THAT IS REACHABLE THROUGH THE PORT, and the first version of this docstring claimed
        it was not. `FILE-LINK` onto an occupied name is refused with EEXIST, which is what
        that claim was built on; but `FILE-RENAME` over an existing FILE is ordinary POSIX
        and is permitted, so hard-linking a file to a fresh name and then renaming that name
        over another existing name produces exactly the divergent shape. Found by the
        differential in `tests/test_ep28e_w2.py`, not by reading, and the corrected claim is
        the one below.

        NO CALLER CAN OBSERVE IT, and that is where the guarantee actually lives. `path_of`
        has exactly three callers — `nlink`'s directory branch, `_fill_lookup`'s parent, and
        `_fill_readdir`'s subject. A DIRECTORY always has exactly one name (a hard link to
        one is EPERM and a rename moves rather than duplicates), so for a directory there is
        no tie to break. Handed a hard-linked FILE's inode instead, all three still answer
        identically whichever name comes back: a file's `children` is empty and a lookup
        beneath a file is ENOENT, by either path. Asserted per caller in the differential.

        AND ALIGNING THE TWO ORDERS WAS CONSIDERED AND IS REFUSED. Popping a reused key
        before rebinding it would make `names` order equal binding order and the two
        implementations exactly equal — at the cost of changing `names` INSERTION ORDER,
        which `bridge/replay_snapshot.py` depends on by taking `matches[-1]` to find the
        newest recorded path. That trades an unobservable difference for an observable one in
        the conformance harness's replay leg. Storing a name-insertion counter instead would
        add structure whose only job is reproducing a tie-break no read asks about, which the
        minimality gate refuses."""
        for path in self.paths.get(ino) or ():
            return path
        return None

    def children(self, path):
        """The names directly inside this directory. COSTS THIS DIRECTORY'S ENTRIES.

        `sorted` is kept because `readdir`'s output order is part of what the conformance
        harness compares; what is gone is the namespace walk that used to feed it."""
        return sorted(self.kids.get(_norm(path)) or ())

    def mode(self, node):
        bits = {KIND_DIR: statmod.S_IFDIR, KIND_LINK: statmod.S_IFLNK,
                KIND_FIFO: statmod.S_IFIFO}.get(node.kind, statmod.S_IFREG)
        if node.kind == KIND_LINK:
            # A SYMLINK'S PERMISSION BITS ARE ALWAYS 0777 ON LINUX and are not consulted for
            # anything: the target's permissions decide access, so the link's own mode is a
            # constant the kernel reports rather than a value anybody set. Recording a mode for
            # a symlink would be recording a decision nobody made; reporting anything else at
            # the port is an ABI divergence, which the conformance harness caught on the
            # symlink, readlink, stat and chown rows at once.
            return bits | 0o777
        return bits | (node.perm & 0o7777)

    # ---- the comparable shape (shadow-diff, replay invariance) ------------------------
    def snapshot(self):
        """Everything this state serves, in one comparable structure. This is what
        shadow-diff compares and what the conformance harness's replay leg reads.

        THE TWO INDEXES ARE IN HERE ON PURPOSE, and it is what makes EP-28E W2 a derivation
        rather than a cache. Shadow-diff compares this structure against the same structure
        rebuilt by folding the record from nothing, continuously — so "kill it and replay
        and it comes back identical" is not a test that ran once, it is a condition the
        mount holds itself to and halts on. An incremental bind that missed an index shows
        up here as a divergence and stops the assume.

        ORDER IS DELIBERATELY NOT COMPARED — both sides are rendered sorted, as `names`
        already was. Two runs of one fold over one record sequence produce the same order,
        so comparing it would add no divergence anyone could hide in, while a difference in
        MEMBERSHIP is exactly what a missed bind produces."""
        return {
            "names": dict(sorted(self.names.items())),
            "inodes": {str(i): self.inodes[i].snapshot() for i in sorted(self.inodes)},
            "kids": {p: sorted(self.kids[p]) for p in sorted(self.kids, key=str)},
            "paths": {str(i): sorted(self.paths[i]) for i in sorted(self.paths, key=str)},
        }


def _creator(e):
    """WHO OWNS A FILE, DERIVED — from the COVERING DECISION, and from nothing else.

    THE RULE THIS OBEYS (design/10 §11.4b, OWNER-RULED 2026-07-29). The owner of a thing
    is the actor at the head of the recorded delegation chain on the covering decision.
    One rule, no branch. THERE IS NO OWNERSHIP FIELD — a field would be a frozen copy of
    the creating decision — so this function takes NO payload argument at all. That is
    not a tidy-up: the argument was the place a default could live, and removing it is
    what makes the class untestable-away rather than caught once. A fold that reads an
    ownership attribute is the defect whether or not its value is currently right.

    IT IS ALSO TRUE OF THE OP DEFINITIONS AND NOT ONLY OF THIS CODE, which is what makes
    the removal safe rather than merely principled. FILE-CREATE, FILE-MKDIR and
    FILE-SYMLINK — the three actions that reach this function — declare no `uid` and no
    `gid` parameter and carry neither in `payload_from` (founding 1.12.0), and the
    envelope router refuses a call supplying a parameter the definition did not declare.
    So a create record CANNOT carry an ownership attribute, and the branch that read one
    was answering a question the founding makes unaskable.


    THE DEFECT THIS CLOSES, and where it was found is the point. Until EP-28 this fold
    read an inode's owner from the create record's PAYLOAD, which carries none: the
    creating uid lives in the record's PROVENANCE, where the port put it as the
    kernel-asserted evidence it is. So every created file folded back as owned by root,
    and no leg of the instrument could see it. The ABI leg could not, because EP-25's
    mount answered `stat` with `node.uid or os.getuid()` — a server-wide fallback that
    made every unrecorded owner read as whoever was running the mount, which happened to
    be the creator. The recording leg could not, because the record is complete and
    correct — nothing is missing from it. And the replay leg could not, because
    `replay_snapshot` compares type, permission, link count, size and content hash, and
    never compared ownership at all.

    IT SURFACED THE MOMENT THE SUBSYSTEM WENT BELOW THE SYSCALL LINE, because the kernel
    reports real per-inode ownership and has no server-wide uid to fall back to: kill the
    derived state, replay, and files came back owned by root instead of by the actor who
    created them. That is T-CUSTODY-IS-DERIVED doing exactly the job design/36 K1 gives
    it, on the first world it was pointed at.

    THE FIX IS A DERIVATION AND NOT AN ADDITION, which is why no founding bump is taken.
    The minimality gate asks whether a `uid` payload field is unbreakdownable or derivable
    from what exists; it is derivable, because the record already carries the asserting
    uid, and adding the field would store a second copy of a fact the record holds — the
    frozen-copy defect one layer down. K6 says the kernel-asserted uid is EVIDENCE and
    the acting actor is derived from it; ownership is derived from it too. And because
    the evidence was always in the record, THIS FIX REACHES BACKWARD: worlds recorded by
    EP-25's mount become owner-derivable without being rewritten.

    A CHOWN IS A DIFFERENT THING AND IS NOT THIS FUNCTION'S BUSINESS. `FILE-CHOWN` is a
    recorded ownership-TRANSFER decision, and its payload uid is that decision's own
    CONTENT rather than a stored field on the file — the fold applies it where the record
    says it happened (see `apply`). What §11.4b removes is a default standing behind a
    create; it does not remove the ability to record that ownership changed hands.

    HONEST CAP, named rather than assumed. §11.4b says the owner is the ACTOR at the head
    of the delegation chain; what this returns is the kernel-asserted uid the port
    recorded as EVIDENCE (K6), which is the port's rendering of that actor and is what a
    numeric `st_uid` at the syscall boundary has to be. Where the two could differ — a
    recorded delegation whose head is a different actor from the one that ran — resolving
    the actor back to a uid would need a reverse fold over the MAP-UID acts. That refinement
    is RAISED, not taken here.
    """
    prov = e.get("provenance") or {}
    # A PROVENANCE THAT NAMES NO UID IS A RECORD THAT DOES NOT SAY WHO, and 0 is the answer
    # for exactly that: the system acted (`store._append_one` defaults `source: "system"` and
    # carries no uid for engine-originated records). It is written as a branch rather than as
    # a coercion because the two cases are different questions: "the record is silent" and
    # "the record states something unreadable". The second now refuses (EP-28C W4b).
    uid = 0 if prov.get("uid") is None else _num(prov["uid"], "the asserted uid")
    gid = 0 if prov.get("gid") is None else _num(prov["gid"], "the asserted gid")
    return uid, gid


class UnparseableRecordValue(ValueError):
    """A value the record or the wire STATES could not be read as the number it claims to be.

    THIS CLASS REPLACES A SILENT ZERO (charter §A52, EP-28C W4b). `custody._int` used to
    answer 0 for anything `int()` refused, so a non-numeric identity became the single key 0
    and a whole namespace collapsed onto it with nothing red. **A parse that returns a
    default on failure converts a TYPE error into a DATA error, and a data error at an
    identity site collapses a namespace.** ABSENCE is a DIFFERENT answer and is handled at
    each call site, in the open, by whoever knows what absence means there."""


class UnrenderableIdentity(ValueError):
    """An identity that cannot be rendered as a POSIX inode number."""


class IdentityNotInFold(LookupError):
    """A rendered inode number naming no identity this fold holds. The POSIX answer is
    ESTALE — the handle you hold no longer names anything — which is the truth rather than a
    guess, and it is why this refuses instead of falling back to the path."""


class AllocatorNotTracking(RuntimeError):
    """The allocator's high-water mark stopped tracking the namespace, so it can no longer
    promise a fresh number. RAISED rather than answered (EP-28C W4b): the mark's whole
    contract is non-collision, and a mark that has not seen every identity cannot make it."""


def _num(v, field):
    """Read a number the record or the wire STATES. NO DEFAULT ON FAILURE, EVER.

    This is §A52's Python half in five lines. There is no `except: return 0` here and there
    must not be: a caller that knows what an ABSENT value means says so at its own site, in
    the open, and a value that is PRESENT and unreadable refuses and names itself."""
    try:
        return int(v)
    except (TypeError, ValueError) as exc:
        raise UnparseableRecordValue(
            "the record states %r for %s and it is not a number — this refuses rather than "
            "answering 0, because a parse that defaults on failure turns a type error into a "
            "data error, and at an identity site that collapses a namespace" % (v, field)
        ) from exc


def _int(v):
    """RETAINED AS A NAME, DELETED AS A BEHAVIOUR (EP-28C W4b), and the residue is named here
    rather than in an entry that rots.

    This function was the Python half of charter §A52's defect: `except (TypeError,
    ValueError): return 0`. Its body is gone. The NAME survives for exactly one caller —
    `src/bridge/records_fs.py:172`, the FUSE port's MAP-UID fold — which is OUTSIDE this
    pass's scope fence, so removing the call there is not this seat's act. **The alias
    delegates to `_num`, so the silent zero is gone for that caller too**, and it is not a
    second parse site: one body, one refusal, reached by two names.

    RAISED: the alias dies when the FUSE port's own pass converts `records_fs.py:172`. A name
    kept for one out-of-fence caller is a note with an expiry, and this docstring is it."""
    return _num(v, "a value read through the retired `_int` name")


def formal_name(seq):
    """THE FORMAL NAME OF THE THING A BIRTH ACT FOUNDS, derived from that act's own position
    in the record and from nothing else (EP-28S; founding 1.18.0's `mints_from`).

    THE DERIVATION, because the shape is the deliverable. Every CANDIDATE FIELD of an act is
    CONTENT, and content repeats: a path is handed back the moment a rename or an unlink
    frees it, so two births separated in time derive one identity and the fold binds ONE node
    for TWO files. The one thing about an act that cannot repeat is WHERE IT SITS IN THE
    RECORD. `seq` is minted inside the store's own write lock, one position per record, never
    reissued (`store.py:810`) — so this map is INJECTIVE BY CONSTRUCTION, with no digest and
    no birthday bound beneath it.

    IT IS A RETURN, NOT AN INVENTION, and the estate had the sound regime running the whole
    time. The FUSE port identified nodes by ALLOCATION ORDER — a private counter — and a
    counter cannot collide. That regime was replaced class-wide at 1.14.0 by a derivation
    from the PATH, which is not stable under rename. This restores allocation order and takes
    its source from the record instead of from a counter that dies with the process while the
    records citing it do not.

    THE COORDINATE IS READ AND NEVER DEFAULTED. A birth act whose coordinate is absent or
    unreadable REFUSES here, through the module's one parse door: a fold that answered 0 for
    an unreadable coordinate would collapse every such act onto one identity, which is the
    §A52 shape this estate closes rather than manages.

    THE BAND'S OWN CEILING IS A REFUSAL RATHER THAN A WRAP. A coordinate at or above
    `SEQ_FLOOR` would render into the digest space and stop being distinguishable from a
    path's rendering; a record store would have to hold 2**61 records to reach it, and the
    answer at that point is a refusal that names itself, never an integer that quietly means
    something else."""
    n = _num(seq, "the birth act's record coordinate")
    if n < 1:
        raise UnrenderableIdentity(
            "a birth act states record coordinate %r — a coordinate is a POSITION in the "
            "record and positions start at 1, so this names no act and cannot name what one "
            "founds" % (seq,))
    if n >= SEQ_FLOOR:
        raise UnrenderableIdentity(
            "a birth act states record coordinate %d, which has reached the formal-name "
            "band's own ceiling %d — beyond it a formal name would be indistinguishable from "
            "a rendered path identity, and this refuses rather than serving one space's "
            "number inside another's" % (n, SEQ_FLOOR))
    return SEQ_FLOOR + n


def render_ino(identity):
    """THE ONE PLACE AN IDENTITY BECOMES A NUMBER, in this estate, in either language.

    THE DERIVATION, because the shape is the deliverable and not the arithmetic. The PATH is
    the identity — the founding derives it (`param_defaults {"inode": "$path"}`, class-wide
    at 1.14.0) and every consumer in this file and in `records_fs.py` treats the value
    OPAQUELY. Exactly two mechanisms insist on an integer and neither insistence is this
    estate's choice: POSIX's `st_ino`, and the Linux VFS's `unsigned long i_ino`. So the
    integer is a RENDERING at a mechanism boundary, and this performs it.

    IT IS A PURE FUNCTION OF THE IDENTITY. It allocates nothing, holds no state, and replays
    identically in any process — which is what lets the C half PARSE what this computed
    instead of computing an answer of its own. **That is charter §A52's fix at its root: the
    boundary is crossed by a shared DERIVATION rather than by two independent
    interpretations.** The module never renders; it only reads what the brain rendered.

    AN IDENTITY ALREADY RECORDED AS AN INTEGER RENDERS AS ITSELF, and that is a property
    rather than a compatibility hack: every world recorded by the stamping FUSE port carries
    integer identities, and this is the identity map on them, so those worlds serve the
    numbers they always served. `RENDER_FLOOR` and `SEQ_FLOOR` keep the three spaces apart.

    AND SINCE EP-28S A FORMAL NAME IS ITS OWN RENDERING, which is the property that makes
    resolution INJECTIVE rather than merely unlikely to collide. `formal_name` returns an
    integer, this is the identity map on integers, so identity and rendering are ONE VALUE
    for every world founded at 1.18.0 or later — there is nothing for a render-to-identity
    lookback to be ambiguous about, because there is no lookback.

    THE HONEST CAP, stated where it cannot rot, AND ITS SCOPE IS NOW BOUNDED. A rendering of
    a recorded PATH is a 62-bit digest of a string, so two distinct path identities CAN in
    principle render alike. Measured: 200,000 synthetic paths, zero collisions; the birthday
    bound at a namespace of N is about N**2 / 2**63. It is NOT left to probability —
    `CustodyState.apply` REFUSES with `UnrenderableIdentity` when it meets two identities
    rendering to one number, so a collision reds at the fold rather than quietly serving one
    file's bytes under another file's name. **THE NAME IN THIS PARAGRAPH USED TO BE
    `render_bind`, WHICH HAS NEVER EXISTED IN THIS TREE.** It was cited here as shipped
    source and twice in EP-28P as an existing precedent, with an acceptance criterion resting
    on it — a fabricated name carrying a design decision. The MECHANISM was always real and
    always in `apply`; only the name was fiction, and a citation that resolves to nothing is
    prose pretending to be a reference. Repaired at EP-28S under the citation-class rule: an
    identifier cited as an existing precedent must RESOLVE, and `tests/test_ep28s.py` resolves
    this one mechanically so it cannot rot back.

    THE CAP DOES NOT REACH A WORLD FOUNDED AT 1.18.0 OR LATER, and the distinction is stated
    rather than left to be inferred: such a world mints no string identities at all, so no
    two of its identities share a rendering and the digest space it never enters cannot
    collide. The cap SURVIVES for every world already recorded under path identity, which is
    what makes this pass prospective.

    AND THE ONE THING THIS MUST NEVER BE is Python's own `hash()`, which is randomized per
    process: a rendering that changed between two runs of the same brain would give one file
    two inode numbers across a restart. Named because it is the nearest wrong reference."""
    if isinstance(identity, bool) or identity is None:
        raise UnrenderableIdentity(
            "%r is not an identity — a rendering has nothing to render" % (identity,))
    if isinstance(identity, int):
        return identity
    if not isinstance(identity, str):
        raise UnrenderableIdentity(
            "%r is neither a recorded integer nor a recorded path, so this estate holds no "
            "derivation that turns it into an inode number" % (identity,))
    if _norm(identity) == "/":
        return ROOT_INO
    digest = hashlib.blake2b(identity.encode("utf-8"), digest_size=8).digest()
    return RENDER_FLOOR + (int.from_bytes(digest, "big") % RENDER_FLOOR)


def parse_ino(text):
    """THE ONE PLACE THE PYTHON HALF READS AN IDENTITY OFF THE WIRE.

    §A52's countable is why this is a named function with one body rather than `int(...)` at
    thirteen call sites: *count the places a value is PARSED; one is a boundary, two is a
    convention wearing a boundary's name.* Its twin is `parse_ino` in
    `planning/vm/govosfs/govosfs.c`, and after EP-28C W4b the two read what ONE derivation
    produced instead of each interpreting the wire on its own."""
    n = _num(text, "an inode number on the wire")
    if n <= 0:
        raise UnparseableRecordValue(
            "the wire states inode %r — zero and negative are not identities, and answering "
            "0 for an unreadable one is precisely the collapse this refuses" % (text,))
    return n


def mint_ino(state):
    """The allocator's one door: the next integer identity a STAMPING port may use.

    IT REFUSES IN A NAMESPACE IT CANNOT TRACK (EP-28C W4b — this is `apply`'s old guard made
    to RED rather than SKIP). The guard read `isinstance(ino, int) and ino >= next_ino` and
    SILENTLY DID NOTHING when the identity was derived: the mark stopped advancing, stopped
    tracking the namespace, and nothing announced it. A mark that has not seen every identity
    cannot promise non-collision, so `apply` sets it to None the moment a derived identity
    enters and this refuses from then on. Stale is the one thing it must never be."""
    if state.next_ino is None:
        raise AllocatorNotTracking(
            "this namespace holds identities the record DERIVED, which the allocator's "
            "high-water mark never saw — so it cannot promise a fresh number and refuses "
            "rather than handing out one that may already be taken. A port serving a world "
            "of derived identities does not stamp: the founding derives the identity and "
            "`render_ino` renders it at the boundary that needs a number")
    n = state.next_ino
    state.next_ino = n + 1
    return n


def _perm(v, kind):
    """A recorded permission, in whatever spelling the record carries it. Octal strings are
    what the founding's files ops have always recorded ('644'); an int is accepted because a
    future recorder may write one, and a missing value takes the kind's conventional default
    rather than zero — a mode of 0 on a directory is an unusable directory, and inventing a
    usable default here would hide a recorder that forgot to record one."""
    if v is None:
        return 0o755 if kind == KIND_DIR else 0o644
    if isinstance(v, int):
        return v & 0o7777
    try:
        return int(str(v), 8) & 0o7777
    except ValueError:
        return 0o755 if kind == KIND_DIR else 0o644


def fold(records):
    """The custody state derived from a record sequence and NOTHING ELSE. This is the
    function T-CUSTODY-IS-DERIVED runs after killing every derived structure: hand it the
    append-only record, get the filesystem back."""
    st = CustodyState()
    for e in records:
        st.apply(e)
        st.applied += 1
    return st


# =====================================================================================
# WHO HOLDS EXCLUSIVITY (EP-25 ADDENDUM 9 C1) — a fold, never a lock table
# =====================================================================================

def _overlaps(a_start, a_len, b_start, b_len):
    """POSIX byte ranges, with the POSIX meaning of length 0: to the end of the file,
    however far that moves. So a zero length is an OPEN interval, not an empty one — the
    one arithmetic mistake that would silently make whole-file locks stop conflicting."""
    a_end = None if not a_len else a_start + a_len
    b_end = None if not b_len else b_start + b_len
    if a_end is not None and b_start >= a_end:
        return False
    if b_end is not None and a_start >= b_end:
        return False
    return True


class Lock:
    """One granted lock, as the record described it. Nothing is stored: every field came
    off a FILE-LOCK record and the whole table is thrown away and re-derived by folding."""

    __slots__ = ("owner", "ltype", "start", "length", "path")

    def __init__(self, owner, ltype, start, length, path):
        self.owner, self.ltype = owner, ltype
        self.start, self.length, self.path = start, length, path

    @property
    def exclusive(self):
        return self.ltype == "write"

    def snapshot(self):
        return {"owner": self.owner, "ltype": self.ltype, "start": self.start,
                "length": self.length, "path": self.path}


class LockTable:
    """Who holds exclusivity over which bytes — DERIVED by folding the lock decisions, by
    the same `apply` body a whole-record fold uses (`fold_locks`), so the running table and
    a table rebuilt from the record are one derivation over two sources. That is the EP-24B
    one-fold rule, and it is why a lock cannot exist here without its record: the mount's
    on-append listener is the ONLY thing that adds an entry, and the listener fires after
    the gate's durable append.

    ITS LIFETIME IS THE MOUNT'S, and that is derived rather than chosen. A POSIX lock is
    held by a process through an open file, and a FUSE mount going down takes every
    descriptor on it with it — so a mount that comes back up comes back to a world where
    nobody holds anything. The record still carries the whole history (who locked what,
    who was refused, when each was released); what does not survive is the CLAIM, because
    the claimant did not survive either. An unbalanced FILE-LOCK in the record therefore
    reads as "the mount went down while this was held", which is what happened. This is
    the same class as the fd table, and it is raised rather than assumed: a mount-session
    record would let the fold say so in the record instead of in this docstring.

    HONEST CAP, stated where it lives: this fold does not SPLIT ranges. Unlocking part of
    a held range drops the overlapping lock rather than leaving the remainder held, and a
    second lock by the same owner over an overlapping range replaces the first. POSIX
    splits and merges; a caller that relies on partial release gets a wider release than
    it asked for, which errs toward refusing nobody rather than toward refusing wrongly.
    """

    def __init__(self):
        self.held = {}       # ino -> [Lock]
        self.applied = 0

    def apply(self, e):
        action = e.get("action")
        if action not in LOCK_ACTIONS:
            return
        p = e.get("payload") or {}
        ino = p.get("inode")
        owner = p.get("owner")
        # POSIX'S OWN DEFAULTS, NAMED. An absent `start` is byte 0 and an absent `length` is
        # "to the end of the file, however far it moves" — which `_overlaps` reads as an open
        # interval. Both are MEANINGS the standard gives to absence, so they are written here
        # as branches; a start or a length the record STATES and cannot be read now refuses.
        start = 0 if p.get("start") is None else _num(p["start"], "the lock's start")
        length = 0 if p.get("length") is None else _num(p["length"], "the lock's length")
        rest = [lk for lk in self.held.get(ino, [])
                if not (lk.owner == owner and _overlaps(lk.start, lk.length, start, length))]
        if action == "FILE-LOCK":
            rest.append(Lock(owner, p.get("ltype"), start, length, p.get("path")))
        if rest:
            self.held[ino] = rest
        else:
            self.held.pop(ino, None)
        self.applied += 1

    # ---- the reads the port serves ---------------------------------------------------
    def conflict(self, ino, owner, ltype, start, length):
        """The lock that stops this one, or None. POSIX exclusion, stated once: a lock
        conflicts with another when they overlap, have DIFFERENT owners, and at least one
        of them is exclusive. A holder never conflicts with itself — which is why F_GETLK
        on your own lock answers F_UNLCK, and why re-locking your own range is not a
        refusal."""
        for lk in self.held.get(ino, []):
            if lk.owner == owner:
                continue
            if not _overlaps(lk.start, lk.length, start, length):
                continue
            if lk.exclusive or ltype == "write":
                return lk
        return None

    def held_by(self, ino, owner):
        return [lk for lk in self.held.get(ino, []) if lk.owner == owner]

    def snapshot(self):
        return {str(i): [lk.snapshot() for lk in sorted(self.held[i], key=lambda l: (l.start, str(l.owner)))]
                for i in sorted(self.held, key=str)}


def fold_locks(records):
    """Exclusivity derived from a record sequence and nothing else — the same `apply` body
    the running table uses, so the two can be compared and a divergence can only mean a
    record was missed, never that two implementations disagreed about what a record means."""
    lt = LockTable()
    for e in records:
        lt.apply(e)
    return lt


# =====================================================================================
# WHO HOLDS THIS HANDLE NOW (EP-30-C3) — a fold, never a stored holder field
# =====================================================================================

#: The actions the CUSTODY-TRANSFER fold reacts to, kept apart from `CUSTODY_ACTIONS` and
#: `LOCK_ACTIONS` for the reason those two are kept apart from each other: each answers a
#: DIFFERENT question. The namespace fold answers what a file IS. The lock fold answers who
#: holds exclusivity over part of one. THIS fold answers WHO HOLDS THE HANDLE NOW — a
#: relation between two ENTITIES, which is the one question the custody plane could not ask
#: before this pass. Fifteen FILE-* actions and two lock actions, and not one of them was a
#: transfer between parties.
#:
#: ONE MEMBER, AND THE SINGULARITY IS DERIVED RATHER THAN PROVISIONAL [EP-30-E1, board :888].
#: The establishment drove eighteen formulations and found that the check vocabulary is not
#: the constraint — THE RECORD SHAPE IS: a current holding is expressible under
#: latest-seq-wins when the state is written as an AMENDING DECLARATION OF THE SAME ACTION,
#: and is blind when it is written as a separate revoking act. So a handover AMENDS this one
#: action and never mints a second verb to undo it. A `FILE-CUSTODY-UNTRANSFER` beside it
#: would be exactly the separate-act shape :888 measured going blind.
CUSTODY_TRANSFER_ACTIONS = ("FILE-CUSTODY-TRANSFER",)


def transferred_device(e):
    """THE DEVICE IDENTITY A TRANSFER RECORD CARRIES — READ OFF THE RECORD, NEVER DERIVED.

    This is a one-line function on purpose, and the purpose is the whole of EP-30's own
    clause: *custody transfers move things BY FORMAL NAME — device identity inherited from
    EP-29's landing, never re-derived channel-side.* A derivation here — from the handle, from
    the path, from anything the channel can see — would be a SECOND answer to a question
    `BIND-DEVICE` already answered, and two derivations of one identity are two answers waiting
    to disagree. Worse, they would disagree INVISIBLY: each side would be internally consistent
    and every round-trip green, which is the shape the estate's guards cannot see (the record
    holding an act nobody performed, one layer down).

    IT IS A NAMED FUNCTION RATHER THAN AN INLINE `p.get("device")` FOR ONE REASON, and it is
    the same reason `parse_ino` is a named function: it makes the site COUNTABLE. Charter §A52's
    countable — *count the places a value is derived; one is a boundary, two is a convention
    wearing a boundary's name* — cannot be applied to an expression scattered across call sites.
    Naming it means a channel-side derivation has to REPLACE something that exists, and a test
    can plant that replacement and watch the comparison go red (`tests/test_ep30_c3.py`, R2).
    """
    return (e.get("payload") or {}).get("device")


class HandleCustody:
    """Who holds each open handle — DERIVED by folding the transfer decisions, latest-wins.

    NOTHING HERE IS STORED, and the sentence means something narrower and stronger than it
    usually does in this file. `holders` is not a stored holder FIELD: it is this fold's
    working structure, in exactly the sense `LockTable.held` and `CustodyState.names` are —
    thrown away and rebuilt from the record by `fold_custody`, with no field on any Inode and
    no attribute on any file recording who holds anything. THE TEST OF THE DIFFERENCE IS
    MECHANICAL AND IT IS DRIVEN: kill this structure, replay the record alone, and the same
    answer comes back. A stored holder field cannot pass that test, which is why R3 plants one
    and watches the replay half diverge.

    LATEST-WINS BY RECORD ORDER, STATED RATHER THAN DEFENDED. `apply` overwrites, so the last
    transfer of a handle folded is the one in force. The order is the RECORD's — every caller
    reaches this fold through a store that yields in `seq` order, exactly as `fold_locks` does,
    and neither fold sorts. A seq comparison here would be structure whose only job is
    defending against a caller that hands records out of order, and no such caller exists; the
    minimality gate refuses it. What is NOT refused is saying so: if one ever arrives, this
    docstring is the thing that was wrong, not a silent behaviour.

    WHY THE DEVICE TRAVELS IN THE FOLD AND IS NOT LOOKED UP. The holder and the device the
    handle stands on came off ONE record, and keeping them together is what lets A4 compare
    entry by entry against the binding that founded the device. Re-fetching the device by
    handle at read time would ask a second question of a second record and lose the pairing
    the transfer itself asserted.
    """

    __slots__ = ("holders", "applied")

    def __init__(self):
        self.holders = {}      # handle -> {"entity": ..., "device": ..., "from_entity": ...}
        self.applied = 0

    def apply(self, e):
        """Fold ONE record. The whole of who-holds-what is decided here and nowhere else."""
        if e.get("action") not in CUSTODY_TRANSFER_ACTIONS:
            return
        p = e.get("payload") or {}
        handle = p.get("handle")
        if handle is None:
            # A transfer naming no handle transfers nothing and is not folded. It is not an
            # ERROR here: the founding declares `handle` required, so a record without one
            # cannot arrive through the door — and a fold that refused would be answering a
            # question the door already closed, in the wrong place.
            return
        self.holders[handle] = {
            "entity": p.get("to_entity"),
            "device": transferred_device(e),
            "from_entity": p.get("from_entity"),
        }
        self.applied += 1

    # ---- the reads the port serves ---------------------------------------------------
    def holder_of(self, handle):
        """WHICH ENTITY HOLDS THIS HANDLE NOW, or None if no transfer names it.

        None is a real answer and not a failure: a handle that was opened and never handed
        over has no transfer record, so this fold has nothing to say about it. Answering the
        opener would be this fold inventing a holder the record never named — `FILE-OPEN`
        declares no entity, which is a REAL GAP and it is RAISED in the close rather than
        papered over here."""
        held = self.holders.get(handle)
        return None if held is None else held["entity"]

    def device_of(self, handle):
        """The device identity the transfer of this handle CARRIED. Read, never derived."""
        held = self.holders.get(handle)
        return None if held is None else held["device"]

    def snapshot(self):
        """The comparable form — what a replay is compared against, entry by entry."""
        return {h: dict(sorted(self.holders[h].items())) for h in sorted(self.holders, key=str)}


def fold_custody(records):
    """Who holds every handle, derived from a record sequence and NOTHING ELSE.

    The same `apply` body the running fold uses, so the two are one derivation over two
    sources and a divergence can only mean a record was missed — never that two
    implementations disagreed about what a record means (the EP-24B one-fold rule). This is
    the function A5's second half runs after throwing the first fold away."""
    hc = HandleCustody()
    for e in records:
        hc.apply(e)
    return hc
