# AWIG OS: the code

This folder is the working code of AWIG OS, produced from the private source at one named point in its history. It is generated, stamped and checked, and never edited by hand. To change AWIG OS, change the source and regenerate this folder. To check that this folder is what it says it is, read `RENDER-STAMP.json` and run the check described below.

## What is here

    src/                the operating-system code
    src/founding/       founding-pack.json, the rulebook every world starts from
    seed_demo.py        one rule, one action allowed, one refused, one rebuild from the record
    check.py            eight checks of the machinery, each in a fresh temporary world
    RENDER-STAMP.json   the source commit, the generator's fingerprint, and a fingerprint of every file
    FREEZE.txt          the same in one line
    LICENSE             GPLv3 for the code; LICENSE-APACHE for future tools; LICENSE-DOCS (CC BY 4.0) for documents
    LICENSING.md        what those licences mean, in plain words

## Run it

    python3 seed_demo.py      # builds one world in a temporary folder and shows every step
    python3 check.py          # the eight checks; check 6 must say no, on purpose

Needs Linux and Python 3. Nothing to install. On Windows, run it under WSL. The program refuses to write a record it cannot prove has reached the disk, and Windows cannot give that proof, so on Windows both scripts stop with one sentence saying so. Everything printed is worked out during the run. The record file is the only thing kept, and every state shown is rebuilt from it.

## Two settings you can change

    AWIGOS_COMMIT_WIDTH        how many records are written to disk in one batch (1 = no batching)
    AWIGOS_COMMIT_WINDOW_MS    how long to wait for a batch to fill

The code also accepts the older `GOVOS_` names for the same settings. New writing uses `AWIGOS_`.

## What this code does, and what it does not

- Every action goes through one door and is written down with the rule that allowed or refused it. Every current state is worked out from the record; nothing is stored that could be worked out. Delete everything except the record, rebuild, and the fingerprints match.
- The record is tamper-evident. A keyed account signs its actions. The program checks its own code at startup. Nothing can be deleted; the only removal is a handover with a signed receipt. A damaged record is repaired back to a sound point under three checks, never by cutting history off. Stored content is locked to its readers.
- **The locks are real when you install them.** Nothing is installed by default, and by default the keys are stand-ins of the right shape, as before. Install the one vetted library this code names (PyNaCl, which carries libsodium) and every key is real: signatures, key wrapping and sealed content are done by that library, never by our own code, and the signing seed never touches the disk. Install nothing, and the code runs exactly as the previous release did; anything that asks for a real signature is then refused rather than faked, so a real key can never quietly become a stand-in. Two limits stay true in both states: a reader who has the disk can read the sealed bytes of the secrets store, and an administrator of the running machine can read the program's memory, where the keys that open sealed content live. Protect the disk and the machine by other means; this code does not.
- The two components that check each other's saved states have only been tested on one machine. Two separate machines is later work.

## Kernel

**The build method and the active kernel route.** gov-os is built record-first. The kernel's definition lives as rows in the record; the running code is derived from those rows at build, and at every waking the built code is checked against the rows by hash — if they disagree, the first act is refused. Two kernels can carry one definition. The active route today is the Python kernel under a Linux carrier, which runs the full estate; beside it stands the freestanding C body, which boots with no Linux beneath it and closed campaign 7: the same acts run under both performers, the numbers read side by side. Nothing above the seam knows which performer is beneath it.

**Why a kernel of our own, and not seL4 or Linux.** Because the claim is about the record, not the scheduler. seL4 proves isolation; Linux provides everything; neither makes the record the only truth. gov-os needs a core whose only writable surface is the record's declared acts — append, write-once, one writer — and where every device effect and every device discovery is a row. Carving that out of Linux means carrying millions of lines that can act without becoming rows; proving it on seL4 means the record law living as a guest on someone else's object model. A small core of our own, read whole and signed, keeps the trusted base enumerable — source files a person can read in a sitting. Linux still serves, where it serves best: as an enclosed driver worker, its crossings declared, refused in its own language, and recorded.

## How this folder was made

A program in the source repository reads the source at one commit and writes this folder: it adds the licence header to every file, replaces the project's internal name in comments, and adds the newer setting names. It refuses to produce any file that carries a private path or lacks the header, and it records a fingerprint of every file it writes. A second program proves this folder can be regenerated byte for byte, carries no internal name beyond the few listed below, and has a header on every file. The source repository's own tests are run against this folder, file by file, to prove it is the same program.

The program that writes this folder, `tools/release/render.py`, is itself shipped here at the same commit, as source you can read; the list of which tests run in this folder and which are skipped is not taken from that shipped copy but written fresh by the release tool whose fingerprint `RENDER-STAMP.json` records, so `run_public_suite.py` is the list a reader runs.

A few names keep the internal codename on purpose, because they are addresses and constants that other software depends on, and renaming them would silently break it. The check counts each one to prove none moved: `govos_fill_super` and `govos_call_lock` (entry points of the guest kernel module), the departure marker `b"\x00gov-os:content-departed-by-handover\x00"` (the bytes a handover leaves in place of removed content), the setting names `GOVOS_COMMIT_WIDTH`, `GOVOS_COMMIT_WINDOW_MS` and `GOVOS_MSG_MAX`, and the guest paths `govosfs` and `/dev/govos-ctl`.

Every fingerprint in `RENDER-STAMP.json` is taken over the file's bytes with Unix line endings. The repository pins those line endings on download, so the fingerprints match on every platform.

## What you can and cannot check from here

The commit named in `RENDER-STAMP.json` and `FREEZE.txt` belongs to the private source repository. You cannot look it up from here, and `git` will tell you so. Treat it as a stamp. The anchor you can check is the public tag on this repository. People holding the private copy verified the source before publication, which is not the same as you being able to verify it, and saying so is better than leaving you to find out.

The comments in the code also mention documents from the private repository, with names like `design/16` or `planning/build`. They are the same kind of stamp: the address where a decision was written down, left in place so the reasoning has a home. They are not files in this folder and cannot be opened from here.

What you can check is the rest, and the rest is most of it: that the code runs, that the record rebuilds to an identical fingerprint, that the eight checks pass, and that `FREEZE.txt` names the rulebook version this folder actually carries, which is what check 8 is for.

## Licence

Code under GPLv3, tools under Apache 2.0, documents under CC BY 4.0. See `LICENSING.md`. Copyright (C) 2026 Kelvin Chau and AWIG OS contributors.
