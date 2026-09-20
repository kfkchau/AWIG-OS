<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: systems-architecture (OS-textbook: system-call surface, process model, device model, bus transports; the seL4/gVisor/LKL/rump literature) · Vocabulary is OS-architecture (core, seam, act, kind of work, translator, bus, driver, request shape). NON-GOAL: no offensive capability — this seed fixes how Linux's derivable programs and drivers come to run unmodified on our definitive core with every effect a row; it attacks nothing. Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=SEED status=DRAFT supersedes=- superseded-by=- verified=2026-09-13 provenance=owner-archi chat 2026-09-13 (the evening dialogue after P3b-4d's close) -->

# GOV-OS — design 57: THE DERIVED SURFACE — Linux's programs and drivers on the definitive core (seed)

**A SEED, not a campaign paper: it fixes the shape so a campaign can be cut from it after C7 closes and beside or after C8 (design/56). Provenance: the owner's questions of 2026-09-13 evening ("can I use it like a Linux", "why would a desktop be more", "definitive vs derivative", "a single universal translator") and the architect's answers the same turn, corrected once on the translator's shape.**

## 1 — The owner's frame (his words, compressed as he said them)

Linux's hundreds of processes are derivative, grown by accretion, not conceptually modular; they are compositions of a few definitive kinds of work. Our architecture is definitive, so it can port and derive any of the derivable Linux processes, and the same for Linux's device infrastructure. The common service layer for drivers should be one universal thing that reuses as much of Linux's built stuff as possible, not built driver by driver.

## 2 — What C7 establishes (built or building; design/54)

The core performs TWELVE kinds of work (the record pen, a write-once file, a removal, the one-writer rule, the clock, the wait, entropy, threads, the one connection, the body read, the founding-pack read, memory) and answers exactly the measured request shapes of the one program it hosts (the interpreter: fifty), refusing every other shape by name; a borrowed program runs unmodified and unprivileged in an enclosure, every crossing a line of the body's own trail, the trail's digest one gate row (L18); drivers come in unmodified as enclosed workers through a translator of common services (design/47 §5; P7b, pending). Nothing above the seam changes.

## 3 — The definitive count, and the four kinds the twelve leave out

Linux's ~350 request shapes are variants of about SIXTEEN kinds. The twelve above, plus four the twelve deliberately exclude because one hosted program never needs them:

    K13  START A PROCESS and wait for its end      — the load act of design/56 (B1) is its governed form: SYSTEM loads a program from an image with a sealed rule set, one row; a process is a view of the entity (design/39)
    K14  DELIVER A SIGNAL to a process              — an act from one entity to another's incarnation, a row; refusal by rule like any act
    K15  A CHANNEL between two processes            — a pipe or a local socket pair; the same shape as the border's channel (design/51), inside one machine; a row per open, not per byte
    K16  WAIT ON MANY THINGS at once                — the wait act generalised to a set; no new effect, a shape of the existing wait

Everything a desktop's processes ask for is a derived shape of one of the sixteen. The measurement that turns this from a reading into a figure: trace a stock desktop from login for one minute in a fresh guest and map every distinct shape to a kind (P1 below).

## 4 — The derived surface, built once

Instead of measuring each program's shapes and serving them one by one (the C7 method, right for the one program the core exists for), the campaign builds the Linux request surface ONCE at the definitive level: one answer per kind, each Linux shape a derivation from it (the files family from the record pen / write-once / removal / body read; the memory family from memory; the thread family from threads; the socket family from the one connection generalised under a rule; the time family from the clock and the wait; the process/signal/pipe/poll families from K13–K16). The surface is declared as data (which shapes derive from which kind, with their argument forms), served by the core, and every effect stays a row because the kinds are the acts. A shape outside the declared surface is refused by name, as today. What is NOT built: Linux's kernel internals — no scheduler of theirs, no VFS of theirs, no network stack of theirs; those are where the accretion lives and nothing is recorded there.

## 4a — The construction on three axes (PROPOSED at the architect's hand, from the owner–architect chat of 2026-09-15 00:19–00:20; the owner asked "list those 16 (tag the 12) and identify how we can modularly construct them" and has not yet ruled on the answer; filed 2026-09-16 so it does not live only in chat)

Every kind is one cell of a matrix with three axes: what the act's OBJECT is (its root), which OPERATION it is, and whether it is on ONE thing or on MANY. Object roots: STAYS (durable content), WORKS (working content), TIME, OTHERS (other entities: self, peers, another computer, the world). Operations: PUT, TAKE, DROP, HOLD, WAIT, TELL.

     #   kind                          root     op         one/many   founded as
     1   append to the record          STAYS    PUT        one        ACT-KIND-01 record-pen
     2   write a whole file once       STAYS    PUT        one        ACT-KIND-02 atomic-write-once (PUT of a whole, not a tail)
     3   remove a file                 STAYS    DROP       one        ACT-KIND-03 remove
     4   read a file                   STAYS    TAKE       one        ACT-KIND-10 body-read
     5   read the founding pack        STAYS    TAKE       one        ACT-KIND-11 founding-pack-read
     6   obtain and release memory     WORKS    PUT/DROP   one        ACT-KIND-12 memory
     7   read the clock                TIME     TAKE       one        ACT-KIND-05 recording-clock
     8   wait a span                   TIME     WAIT       one        ACT-KIND-06 commit-window
     9   take unpredictability         OTHERS   TAKE       one        ACT-KIND-07 entropy (from the world)
    10   start more of oneself         OTHERS   PUT        one        ACT-KIND-08 concurrency (a thread: a new entity of self)
    11   be the one writer             OTHERS   HOLD       many       ACT-KIND-04 single-writer-lock (one claim among many)
    12   the one connection            OTHERS   PUT/TAKE   one        ACT-KIND-09 network-socket (bytes with another computer)
    13   start a process, wait its end OTHERS   PUT+WAIT   one        not founded — K13, the load act of design/56 B1 (a new entity, not self, with a sealed rule set)
    14   deliver a signal              OTHERS   TELL       one        not founded — K14, an act from one entity to another's incarnation
    15   a channel between processes   OTHERS   PUT/TAKE   one        not founded — K15, kind 12's shape on the same computer, one row per open
    16   wait on many things           TIME     WAIT       many       not founded — K16, kind 8 over a set

Cells left EMPTY ON PURPOSE are the refusals by name: TIME x PUT (set the clock), STAYS x HOLD (lock content beyond the writer mark), WORKS x TELL, STAYS x TELL. The construction: a request is (root, operation, one/many, argument form); every Linux request shape is a row in a table of derivations from one cell; the core matches the table and refuses the rest by name. The table is filled from P1's one-minute desktop trace, never from memory. Q3 (§9) stays open: whether that table is a founding-pack section or a sealed table beside the image. Cost if wrong: one addendum struck; nothing built on it yet.

## 5 — Drivers: one universal translator, per-bus transports

The common services every Linux driver expects — memory for its buffers, interrupts, timers, direct memory transfer, the device walk that finds a device and matches it to its driver, the registration calls — are ONE translator built once for all borrowed drivers (the owner's frame; the architect's earlier "per device class" was wrong and is corrected here). What varies is only the TRANSPORT a bus speaks: the guest's virtual-device bus (virtio), PCI, USB — three or four small pieces, each a definitive shape from which a whole family of drivers derives. Device discovery is a row; every device effect is a row; a refusal arrives in the driver's native failure language (design/47 §5, design/54 B7). The first case is the network device (P3b-6), the second the disk, then screen and input — all four present on the guest's virtual bus.

## 6 — The one design question that is the owner's before a screen

A screen and a mouse produce thousands of events a second. Governing every event as a row is the record's design and its bottleneck at once. The question, his: which device traffic is governed row by row (discovery, binding, opening, closing, every act that changes custody or permission) and which rides a FAST CHANNEL whose traffic is recorded in batches by digest (frames, pointer motion, audio samples). Until he rules, no graphical row is planned; the network and disk rows do not need it.

## 7 — What this makes possible and what it costs (Estimate, Medium; estate pace 3–5 closed rows/day)

    P1  SPIKE  trace a stock desktop from login in a fresh guest; the distinct shapes mapped to the sixteen kinds; the figure replaces §3's reading                    ½ day
    P2  SPIKE  link one virtio driver against an empty translator; count the services it needs — the translator's true size                                          ½ day
    P3  the universal translator + the virtio transport; the network driver as the first borrowed worker (folds P3b-6's device half)                                  4–6 rows
    P4  K13–K16 as acts (K13 = design/56 B1; the other three minted here), the founding rows                                                                           4–6 rows, YELLOW/RED (founding)
    P5  the derived surface as data + the core serving it; proven by a stock static, a dynamic and a threaded program AND by a stock shell starting a stock program   8–12 rows
    P6  disk, screen and input drivers through the translator                                                                                                          3–5 rows
    P7  one graphical program on the screen buffer with input (after §6 is ruled)                                                                                       3–5 rows
    P8  a display server and a toolkit window                                                                                                                          10–15 rows
    —   a full desktop (KDE): not estimated; hundreds of programs and their service managers; only after §6 and P8

## 8 — Invariants carried

Every effect a row; refusal by name beyond the declared surface; the borrowed program and driver unmodified; the core witnessed by code, everything else by acts (design/54 L2/I7); no Linux kernel internals inside the signed base; the twelve-plus-four kinds are the only acts the core performs.

## 9 — Open questions

    Q1  §6 — the fast channel for device traffic (owner).
    Q2  whether K13 (start a process) is served to borrowed programs at all, or only to gov-os's own loader — the desktop needs the former; the governance needs the load row either way (owner, with design/56 Q1).
    Q3  the surface as data: a founding pack section, or a sealed table beside the image? (architect; after P1's figure).
