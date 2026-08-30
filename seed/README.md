# AWIG OS: the seed

A working model of a governed operating system, built the way an accountant
builds a ledger: the record of what happened is the only thing kept, and every
current state is computed from it. What it models is the governing layer: rules
in force, acts decided against those rules and citing them, and the one record
both land in. Nothing in this folder schedules a process or allocates a device.
It is the smallest piece of the system that runs.

Repository: [github.com/kfkchau/AWIG-OS](https://github.com/kfkchau/AWIG-OS).
Internal name: govos.

## Run it

Two files, stock Python 3. Nothing to install, nothing to configure.

**Run them from the folder that holds this README**, whatever that folder is
called and however you came by it: a clone, a zip, a tarball, a copy handed to
you on disk.

```
python3 seed_demo.py
python3 check.py
```

That is the whole instruction. Two commands, no arguments, no options.

If you do not have the files yet, `git clone https://github.com/kfkchau/AWIG-OS.git`
fetches them; in that clone this folder is `seed/`, so `cd AWIG-OS/seed` puts you
where the two commands work. Both filenames above are relative, so what matters is
the folder you are standing in, not what it is called: a copy of this folder under
any other name runs exactly the same. To run from somewhere else instead, give the
full path: `python3 /path/to/this/folder/seed_demo.py` works from any directory.

The two files are independent. Either runs on its own, in either order, as often
as you like, and neither reads anything the other wrote. Together they took
between 2.2 and 2.7 seconds across five cold runs on the machine this was cut
on, measured with `time` at the shell, so Python's own start-up is inside those
figures; the demo also prints a wall-clock line of its own, which counts only
its own execution and reads lower. A number of your own near the band is the
expected result and not a discrepancy.

Everything they record goes into a fresh temporary directory. The only thing
either writes next to itself is `__pycache__`, Python's own compiled cache, one
beside each of the three packages under `src/`, which Python writes for any
program it runs. Nothing else on your machine is touched. `check.py` removes its
temporary directories as it goes; `seed_demo.py` leaves one behind per run on
purpose, so you can read the record it built. It says where, and deleting it is
safe. The names are random, so runs accumulate and nothing distinguishes today's
from an older one; on Linux `rm -rf /tmp/awig-seed-*` clears them all.

**What a pass looks like.** `seed_demo.py` ends with `IDENTICAL. The world came
back, hash for hash.` `check.py` ends with `OK` under `Ran 8 tests`, and then
prints its own exit code in words. Both exit 0 when they pass and 1 when they do
not, so `echo $?` after either one is a second opinion on what you just read.

## What you will see

`seed_demo.py` prints four things, in order.

1. **A rule**, read back out of the record the system just founded itself into.
   Not out of the source code. The line it was read from is printed first, as
   raw bytes off the file, so every field shown underneath can be found inside
   it. The constitution is data, it is recorded like everything else, and it is
   readable back the same way.
2. **An act allowed**, citing that rule by name. One record is appended. The
   state that follows from it is then computed and shown.
3. **A second act refused**, citing the same rule. The refusal is itself a
   record, appended like any other, carrying the rule it was refused under and
   the reason. A no costs a record exactly as a yes does, and the world does not
   move.
4. **The replay.** The derived world is fingerprinted. That fingerprint is
   `sha256` over a length-prefixed, type-tagged byte encoding of those readings
   and not over JSON: every value is tagged by its type, a length or count is
   written in front of every string and every collection, strings are normalised
   to Unicode NFC first, mapping keys are sorted by their own encoded bytes so
   that key order cannot change the hash, and each derived entry's `seq` is
   dropped before encoding because that is the record's order rather than the
   world's state. That sentence gives the shape and not the grammar, which is
   the limit worth stating plainly: the exact byte form of each type is the
   table at the top of `src/kernel/canonical.py`, and recomputing one of these
   fingerprints by hand needs that table rather than this paragraph. Then the
   working directory is deleted, with only the record file carried out. A new
   kernel is built from that file alone and the world is fingerprinted again.
   The two fingerprints are printed next to each other.

`check.py` runs eight readings of the same machinery, each in its own fresh
directory, without reading the demo. Seven confirm the behaviour above. Check 6
is a control: it changes one recorded value on a copy and requires the
fingerprint to come back different, because a check that cannot report a
difference has not checked anything.

## What this shows, and what it claims

It shows one rule in force, one act allowed under it, one act refused under it,
and a world that returns identical from its record after being destroyed. Every
number and hash you see was computed during your run.

The claim stops there. Nothing here is a benchmark, and the demo exercises the
record, the gate and the replay rather than the whole of what those modules
carry.

## The code you are running

`src/` holds the engine, byte for byte as it is written upstream. It was chosen
by tracing what a run of the demo actually imports and opens, not by anyone
picking files, then proved by copying that set alone to a clean directory and
running both commands there. Anything the run did not touch is not here.

The version this folder was cut at is in `FREEZE.txt`, and the demo prints it
before anything else. What that founding and that commit identify is the engine:
the eighteen files under `src/` are byte-identical to the development repository
at the named commit.

That repository is private, so treat the commit hash as a provenance stamp rather
than something you can check. `git cat-file` on it inside this clone fails, and it
should: the object is not here and never was. That identity was verified before
publication by hands holding the private copy, which is not the same thing as you
being able to verify it, and saying so is better than leaving you to find out.

What you can check from here is the rest, and the rest is most of it: that the code
runs, that the record replays to an identical fingerprint, that the eight checks
pass, and that `FREEZE.txt` names the founding version this folder actually
carries, which is check 8's whole job.

The commit does not identify the wrapper around the engine. `FREEZE.txt`, this
README and `seed_demo.py` have all been written since the commit they name, and
that is not an untidiness someone could go and fix: a file cannot contain the hash
of the commit that records it, so the commit stamped inside any of these three is
necessarily earlier than the commit carrying them. The engine is the part the line
pins, and it is the part the line can pin.

## Platforms

Verified on Linux, on the machine this was cut on, and the demo prints the
system it is running on so your own run says which one it was. On Windows, run
it under WSL.

Python 3.12.3 is the version it was verified running on, and the only one. It
imports nothing outside the standard library, and every file in it parses under
Python 3.8's syntax rules, so **3.8 is the stated minimum** and a version older
than that is the one thing likely to stop it. `python3 --version` tells you
yours.

## Licence

The engine under `src/` is the project's core and is GPLv3. The binding text sits
beside this README as `LICENSE`, the verbatim GNU General Public License version 3,
the same text the repository root carries. One level up from this folder,
`LICENSING.md` is the licensing map for every layer of the project, and the other
`LICENSE` files beside it hold the texts for the layers this folder does not
contain. Where this paragraph and those texts differ, the texts govern. What is
here is the real source of what runs, so what you read is what executed.
