# AWIG OS — the rendered code (campaign-4 completed tree)

This folder is a **rendering** of AWIG OS's source at one named commit. It is
generated, stamped and checked; it is never edited by hand. If you want to
change AWIG OS, change the source and re-render; if you want to check that
this folder is what it says it is, read `RENDER-STAMP.json` and run the
check described below.

## What is here

    src/                the operating-system code: kernel, bridge, subsystems, founding
    src/founding/       founding-pack.json — the constitution every world is founded from
    seed_demo.py        one rule, one act allowed, one act refused citing its rule, one
                        kill-and-replay with matching hashes (python3 seed_demo.py)
    check.py            the seed check battery: eight readings of the machinery, each in
                        a fresh temporary world (python3 check.py; exit 0 = all green)
    RENDER-STAMP.json   the source commit, the renderer's hash, every file's sha256
    FREEZE.txt          the same in one line
    LICENSE             GPLv3 (the core) · LICENSE-APACHE (the ring) · LICENSE-DOCS (CC BY 4.0)
    LICENSING.md        the licensing map in plain language — the licence is this
                        project's first rule

## Run it

    python3 seed_demo.py      # writes one world under a temp dir and shows every step
    python3 check.py          # the battery; check 6 is the control that must say no

Linux, Python 3 standard library only, no dependencies. On Windows, run it
under WSL: the store needs the Linux durability barrier (fdatasync) and refuses
to append a record it cannot prove reached the disk; on a platform without it
both scripts stop with one sentence saying so. Everything printed is computed in
the run; the record written is the only durable thing, and every state shown
is derived from it.

## Environment overrides

    AWIGOS_COMMIT_WIDTH        group-commit width (1 = no batching)
    AWIGOS_COMMIT_WINDOW_MS    group-commit window

The code reads the `AWIGOS_` name first and the estate's internal `GOVOS_`
name second, so either works. New writing uses `AWIGOS_`.

## What this claims, and what it does not

- Every act crosses one gate and is recorded citing the rule that allowed or
  refused it. Every current state is computed from the record; nothing is
  stored that could be derived. Kill everything derived, replay, and the
  hashes match.
- The record is chained and sealed; a keyed account's acts carry its
  signature; the machine attests its own code at boot; there is no delete in
  the vocabulary; a damaged record recovers to a sound point under a triple
  check and never truncates; content at rest is sealed to its readers.
- **Honest cap, stated plainly:** Every key in this release is a stand-in of
  the right shape, not real cryptography. A reader of the whole record on disk
  can derive an open key and unseal content. Real cryptographic key material
  under the whole key family is the next unit. Protect the disk by other means
  (full-disk encryption) until it lands.
- The two witnesses that check each other's checkpoints are proven blind
  within one machine only; two separate bodies are later work.

## How this folder was made

`tools/release/render.py` in the source repository reads `src/` at one commit
and writes this folder: the per-file licence header from `LICENSING.md` §4;
the project's name in comments and docstrings; the additive environment
alias. It refuses to emit any file carrying a private path or lacking the
header, and it stamps every output. `tools/release/check.py` proves the
folder regenerates byte-identically, carries no internal name beyond the
named interface identifiers of the guest kernel module, and has a header on
every file. The source repository's own test ledger runs against this
folder, module by module, to prove it is the same program.

A handful of identifiers keep the estate's internal codename on purpose,
because they are wire and record constants a rename would silently break, and
the check counts each one to prove none moved: `govos_fill_super` and
`govos_call_lock` (the guest kernel-module entry points), the departure marker
`b"\x00gov-os:content-departed-by-handover\x00"` (the record byte-string a
verified handover leaves in place of removed content), the environment
fallbacks `GOVOS_COMMIT_WIDTH`, `GOVOS_COMMIT_WINDOW_MS` and `GOVOS_MSG_MAX`
under the shared `GOVOS_` prefix, and the guest paths `govosfs` and
`/dev/govos-ctl`. These are addresses and constants, not the project's name;
changing them would change what the bytes mean, so they are left exactly as
they are.

Every sha256 in `RENDER-STAMP.json` is taken over each file's bytes with Unix
(LF) line endings; the repository's `.gitattributes` pins LF on checkout, so
the stamp verifies to the same digest on every platform.

The commit named in `RENDER-STAMP.json` and `FREEZE.txt` is a commit in the
estate's own repository, which is private, so treat that commit as a
provenance stamp rather than something you can check. `git cat-file` on it
inside this clone fails, and it should: the object is not here and never was.
The anchor you can hold is the public release tag on this repository, not that
commit. The source identity was verified before publication by hands holding
the private copy, which is not the same thing as you being able to verify it,
and saying so is better than leaving you to find out.

You will also find, in the code's comments and docstrings, references to the
estate's own design and planning documents — paths like `design/16` or
`planning/build`. These are provenance references of the same kind as that
commit: pointers into the private repository where a decision was written down,
left in place so the reasoning keeps an address. They are not files in this
folder and `git` cannot resolve them here, and that is on purpose — read them
the way you read the commit, a stamp of where a thing came from rather than
something you can open from here.

What you can check from here is the rest, and the rest is most of it: that the
code runs, that the record replays to an identical fingerprint, that the eight
checks pass, and that `FREEZE.txt` names the founding version this folder
actually carries, which is check 8's whole job.

## Licence

Code under GPLv3, tools under Apache 2.0, documents under CC BY 4.0 —
see `LICENSING.md`. Copyright (C) 2026 Kelvin Chau and AWIG OS contributors.
