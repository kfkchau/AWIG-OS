# Where AWIG OS stands

Dated 20 September 2026. If this page and the code disagree, the code is right and this page is out of date.

## What you can try today

Download this repository, open the `code` folder, and run:

    python3 seed_demo.py
    python3 check.py
    python3 run_public_suite.py

The first command starts from a written rulebook. It performs one action the rulebook allows and writes down what it did and which rule allowed it. It then attempts an action the rulebook forbids, refuses, and writes down the refusal and the reason. Then it deletes everything except that written record, rebuilds itself from the record alone, and shows that the rebuilt copy is identical to the original.

The second command runs sixteen checks: eight on the machinery, one of which deliberately breaks a value to prove the checks can fail, and eight that prove the tool which produced this folder refuses to ship eight kinds of private text.

The third command runs the program's own test suite. On a machine with nothing else installed it runs 170 test files, all of which pass, and skips 67, and every skipped test prints what it would need: a private file from the development repository, the build team's virtual machine, or a third-party package. Before it runs anything it recomputes the fingerprints of the three folders it runs against and refuses if one byte has moved, and it refuses an empty run.

Measured on 20 September 2026 on a Windows laptop under Debian in WSL 2 (Python 3.13.5), from a clean copy with nothing of ours installed: sixteen checks of sixteen; 170 test files run, 170 passed, 0 failed, 64 skipped naming what they need and 3 more that skip as they load; 2,779 test cases, none failed. The same again with the real locks installed (PyNaCl 1.6.2): the same figures. The build team ran the leak scan and the sixteen checks on its own render of the same commit and got the same. One timing case in `test_ep28c_w6.py` compares two runs field by field, and under a loaded whole run two runs can agree by chance on a clock reading; it failed that way twice from a git checkout on the same laptop and passed five times of five alone. Since 4.1 that case skips itself only when the coincidence is on one of the fields that may vary, and names them; a difference on any other field is still a hard failure.

**New in this copy: build the kernel and boot it.** On a Linux machine with `gcc`, `binutils`, Python 3 and `qemu-system-x86_64` installed, and nothing of ours installed:

    cd code/src/body
    ./build.sh . /tmp/awig-body
    qemu-system-x86_64 -cpu qemu64 -display none -no-reboot -m 256 -rtc base=utc -serial stdio -kernel /tmp/awig-body/body.img

What comes up is our own kernel with no Linux beneath it. It brings up its memory and proves each piece works, checks its own body, and prints each check as PASS or FAIL on the serial line. Add one word to the build, for example `./build.sh . /tmp/awig-body PLANT_WORKER_IMAGE_TAMPER`, and the matching check fails, which is how you know the checks can fail. This is the plain kernel. The full slice, the one that runs the standard Python interpreter as sealed content and opens a network connection only after its own record grants it, builds from the same script and takes two inputs from your own machine, named in [`THIRD-PARTY.md`](./THIRD-PARTY.md). Built and booted this way on 19 September 2026 on a Windows laptop under Debian in WSL 2 (gcc 14.2.0, QEMU 10.0.13), with nothing of ours installed: 120 lines on the serial line, every check PASS, the last line `BODY-HALT`. With no disk and no network card attached, the kernel says so itself (`DISK: ABSENT`, `NET: ABSENT`) and skips those acts.

To turn the real locks on, install one library, PyNaCl, the Python binding of libsodium (`pip install pynacl`). Everything below about keys depends on whether it is installed.

## What is in this code beyond the three commands

The same program, with more of it switched on. Some of it needs a Linux guest machine or a second machine to exercise, which is why those tests skip here.

- The written record is tamper-evident. Change one character of the history and the system can say where. It does this by comparing the history against the last checkpoint it saved.
- Accounts can hold keys. An account with a key cannot act without signing. Accounts without keys work exactly as before.
- With the library installed, signing and sealing are real cryptography, and the program seals its own signing key at startup. Without it, the keys are stand-ins of the right shape and any act that needs a real signature is refused rather than faked.
- The program checks its own code at startup and writes the fingerprint into the record.
- Nothing can be deleted. The only way anything leaves is a formal handover to another party, who signs a receipt. The rulebook decides the handover before any content moves.
- Stored content is locked so that only its intended readers can open it, and is checked against its bytes every time it is served.
- If the record is damaged, the system repairs it back to the last point that three independent checks agree on, or stops and asks.
- Network actions are governed. Opening, binding, listening, connecting, accepting and closing a socket are each a recorded decision citing a rule, and the live socket table is computed from those records.
- The border is governed. Something arriving from outside is a draft; the rulebook decides it before it has any effect; the reply seals exactly what was shown. Who sent it is established at the door, by a recorded identity, never by trusting the sender's own record.
- One row, one receipt, two bodies. A record sent from one machine is received by another as input; the receiver writes its own receipt in its own record; neither writes the other's. Shown between a host and a Linux guest over a real socket, in the development repository's test worlds.
- The firewall is rules in the record. Every filtering decision is a recorded act.
- The rulebook itself can only be changed through the same door as everything else. It has been changed fifty-five times that way since 24 July 2026.

How we know: at the close of campaign 7 the whole estate's standing tests ran 194 of 199 green; the five that were red were known before the campaign and none was the kernel's. Any test count you see from us names the machine it ran on.

## The kernel, new in this copy

Until this copy, everything above ran on Linux. Campaign 7 wrote the kernel underneath it, from a blank page, and closed on 19 September 2026. In plain words:

- The machine boots into our own kernel in a virtual machine, with no Linux beneath it.
- Before its first act it checks its own body, its record chain, its constitution and its keys, and writes down that two separate witnesses agreed it woke sane. One witness alone cannot write that row.
- The kernel and the interpreter it carries are pinned in the record by their fingerprints. Change one byte of either and the machine refuses to start, and each of those refusals was tested by planting the change.
- The kernel's own definition is rows in the record. The code is derived from them at build; delete it and regenerate it and the same bytes come back.
- It runs the standard Python interpreter, unmodified, as sealed content, and runs the gate on it.
- It opens a network connection only after its own record grants it: the grant row first, then the socket. On a refusal there is no socket, and the refusal is a row. The network code it borrows runs unmodified inside an enclosure; every device it finds and every device effect is a row.
- Nothing above the kernel changed. The same acts run on Linux and on our kernel through one declared seam.

**The numbers, the same acts under both, each with its run.** Rows written per second: Linux 696.8 (5,000 rows), our kernel 181.8 (200 rows). One decision under one rule: Linux 5.99 microseconds, our kernel 204. Verifying a record of one million rows ran under Linux only (534.8 seconds of processor time over a 518 MB record); our kernel, whose record as built holds 2,048 entries in 8 MiB, ran the same acts at its own size (739 rows, 0.906 seconds) and is never presented as the million's equal. The figure that is equal on both, and does not depend on the record's size: the proof that localises a change is 347 bytes on each, and verifies true on each. Our kernel appends at 2 MiB of memory and fails at 1 MiB, printing its own failure; a clean boot needs 3 MiB. All figures: the build team's Linux machine and its nested virtual machine, 19 September 2026, campaign 7's review. The comparison tool ships in `code/tools/sidebyside`; the evidence it was run on does not, so from this copy a stranger can run the Linux half and read the kernel's figures, not reproduce the pair.

It is slower than Linux, and it is narrow by design: it is the record's own body, never a desktop. Its limits as built are 2,048 record entries, an 8 MiB record and a 64 MiB data region.

## What comes next

Named as work the build side has committed to, not as things you can use. Each entry closes when a stranger can check it; no dates.

- **What is being built now, and what follows, in order:** [`ROADMAP.md`](./ROADMAP.md). Two lines run in parallel today: every program born as an actor by one recorded act, and the one-file installer that boots a real computer from a USB stick and touches no disk.
- **Beside the installer, the side-by-side stretch:** the same acts on Linux and on our kernel, both records compared byte for byte, before the real record moves onto the kernel.
- **Carried from the outside reviews:** an effect that happened with no row after a crash shown as unknown, never as done; destroying content as a recorded act with a receipt, where the law requires it; more than one holder of a stage of governance over one scope; the second public test run with the real locks installed.

## Designed on paper, not built

- The AI team that is meant to work inside it. The room has two doors, built and tested between two machines, and nobody living in it.
- Every program born on the record with its rules sealed at load (being built now; see [`ROADMAP.md`](./ROADMAP.md)).
- Running on real hardware (the installer, being built now; see [`ROADMAP.md`](./ROADMAP.md)).

## What is not true yet

Read this before trusting it with anything that matters.

- **The locks are real when you install them.** Nothing is installed by default, and by default the keys are stand-ins of the right shape, as before. Install the named library and signing and sealing are real cryptography. Either way, whoever holds the disk or administers the running machine can read what it holds. In the build team's exact words, which appear in every page that mentions keys:

> Real cryptography is in this code and is off until you turn it on. Install the one vetted library it names and every key is real: signatures, key wrapping and sealed content are done by that library, never by our own code, and the signing seed never touches the disk. Install nothing, and the code runs exactly as the previous release did, with keys that are stand-ins of the right shape; anything that asks for a real signature is then refused rather than faked, so a real key can never quietly become a stand-in. Two limits stay true in both states: a reader who has the disk can read the sealed bytes of the secrets store, and an administrator of the running machine can read the program's memory, where the keys that open sealed content live. Protect the disk and the machine by other means; this code does not.

- **The kernel runs in a virtual machine only, and the day-to-day record does not run on it yet.** The kernel boots alone, with no Linux beneath it, and runs the same acts; the record that matters still runs on the Linux-hosted governing layer until the side-by-side stretch agrees whole and the move is taken. No real hardware yet, one processor, a small set of devices.
- **One machine, one user.** Every speed figure we publish comes from one computer with one user at a time.
- **The record can be wrong while every view of it is right.** Once, two things created at the same instant produced two entries for one act. The checks run from the record outward, never the other way.
- **A known defect: rename and replay.** Some programs save a file by writing a new one and renaming it over the old. The record then holds two entries for one file and the rebuild merges them. This is why the filmed demo of August, running real `git` on a Linux mount of the record, stops at `git add` and never reaches `git commit`; the seed demo in `code/` runs no `git`. Renaming a folder with contents, and renaming one of two names for the same file, were also wrong and are repaired in this code.
- **An outside AI reviewer has tested it three times.** What it found is in the section below. The written list of things still to try has not all been attempted.
- **An administrator can edit the file.** Someone with full rights on the machine can change the record. The chain will show where. It cannot stop them.
- **The two watchdogs have only been tested on one machine.** Two components check each other's saved states. Whether they stay independent on two separate machines is later work.

## Found by an outside reader, an AI

Between 8 and 9 September 2026 I ran an independent security review of the previous public copy of this code: an AI reviewer, separate from the AI team that builds the system, with its own tests, twice. The build team was given its findings and nothing else, not its test programs and not its harness, so that the repairs came from our own reading of our own code at the line named, and every repair is tested from our own description of the correct behaviour. That separation is deliberate and it stays: the review will keep running against each public copy, independently of the build, to cover more of the ground each time.

Nothing they found breaks a promise made in the current round of work. Everything real that they found is older than that round, in parts of the program that round did not touch. The first report gave us eleven such items and six that were already written on this page or are the way the program is meant to work. The second report gave us twelve more, and the reviewer's own description of them is right: each part is correct on its own, and what is missing is the agreement between parts. Measuring one of the first items on a real mounted filesystem, rather than inside a test, turned up two further items of our own.

The ones that matter most, in plain words:

- A handover removed the content before the rulebook had decided whether the handover was allowed. Now the decision comes first, is written down, and only then does the content leave.
- A write the rulebook refused could still be read back through the mounted filesystem for as long as the operating system kept a copy of it. The mount now sends every read to the record instead of keeping a copy. That has a price, and the price is real: a program that maps a file into memory for shared writing is refused by the operating system; a program that writes and reads through two open handles before saving sees what was last saved, not its own unsaved write; and a second program reading a file after another program's refused write sees what was last saved, never the refused bytes. We measured all three on a real mount and kept the measurements.
- A permission that a later rule had overturned still counted when a new action asked for it. One check now decides what is still in force, and every part of the program that grants or holds something asks it.
- Two copies of the program could open the same record at once and each write the same entry number. One writer holds the pen: every change enters through one gate that cites a rule, onto one append-only record, and everything else the system shows is computed from that record. The record takes one writer at a time: an operating-system lock held for the writer's lifetime, raced in its test by ten real processes; a second copy of the program opened over the same record in one process reads but cannot write. The released code before this repair checked a pid file instead.
- Stored content was trusted by its name and not by its bytes. It is now checked against its bytes each time, and a missing item is refused rather than served as an empty file.
- A file created on the mount was written down as belonging to the administrator, whatever account created it. It is now written down as belonging to the account that created it.

The rest are smaller and are listed, one line each, with their repair, in the private repository's build record. The repairs are in this code, with the tests that prove them.

On 13 September I ran a third round, the same way, on the previous public copy. It found four things. The one-writer rule above could be beaten by racing real processes, so two writers got in. A half-written last line in the record stopped the program from opening instead of being set aside. A value the record could not write down came back as an error instead of a refusal, and left the record refusing everything after it. And the shipped test runner would have passed an empty test folder. All four are repaired in this copy, with the tests that prove them. The review keeps running.

## What you can and cannot check from here

The commit numbers in `code/RENDER-STAMP.json` and `code/FREEZE.txt` belong to the private repository. You cannot look them up from here. Treat them as stamps. What you can check is the four tags on this repository, `milestone-0-seed`, `c4-close`, `c5-close` and `c7-close`, the sixteen checks, and the shipped test suite with its printed fingerprints.

## If you want to know more

Email kelvin@rootrebuilder.org, or open an issue on this repository. Questions, criticism and a stranger's run of the three commands are all welcome; say which machine you ran on.

---

© Kelvin Chau, 2026 · This document: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
Part of the [AWIG OS](./README.md) project.
