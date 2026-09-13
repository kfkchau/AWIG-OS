# Where AWIG OS stands

Dated 13 September 2026. If this page and the code disagree, the code is right and this page is out of date.

## What you can try today

Download this repository, open the `code` folder, and run:

    python3 seed_demo.py
    python3 check.py
    python3 run_public_suite.py

The first command starts from a written rulebook. It performs one action the rulebook allows and writes down what it did and which rule allowed it. It then attempts an action the rulebook forbids, refuses, and writes down the refusal and the reason. Then it deletes everything except that written record, rebuilds itself from the record alone, and shows that the rebuilt copy is identical to the original.

The second command runs sixteen checks: eight on the machinery, one of which deliberately breaks a value to prove the checks can fail, and eight that prove the tool which produced this folder refuses to ship eight kinds of private text.

The third command runs the program's own test suite, which ships with this release for the first time. On a machine with nothing else installed it runs 94 test files and skips 65, and every skipped test prints what it would need: a private file from the development repository, a Linux guest machine, or a third-party filesystem package. It prints the fingerprints of the three folders it ran against, so a result can be matched to the exact code.

On the Linux machine this release was cut on (Python 3.12.3): 94 run, 94 passed, 0 failed, 65 skipped; sixteen checks of sixteen. One further test is skipped in this copy because it could fail by chance (an assertion over the record's text collides with timestamp and hash digits about one time in six); it is repaired in the private repository and returns in the next copy; the skip row names the defect and the repair. This release we also ran it more seriously on Windows, under Debian in WSL 2 (Python 3.13.5). That run found a test that measures how the disk batches writes, which that platform does not do, so it now skips there and says why; and it showed one timing test that fails when the whole suite runs at once and passes on its own. Neither is a broken promise of the code, both are named in the test output, and the timing test is addressed in the next release. If you run it on WSL 2 today, expect 94 of 94, or 93 if the timing test trips. Windows on its own refuses with one sentence, because it cannot prove a write has reached the disk, and points you to WSL. Needs Python 3 and nothing else.

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
- The rulebook itself can only be changed through the same door as everything else. It has been changed fifty times that way since 24 July 2026.

How we know: on the private Linux machine, at the campaign 5 grade of 9 September 2026, 145 test files with 3,899 tests, all passing, run one file at a time. Ninety-four of those test files run here in the third command; the rest are the 65 that skip, each naming what it needs. Any test count you see from us names the machine it ran on.

## Built since this copy was cut, in the private repository

- Several machines, each keeping its own record, with the stage each machine holds derived from its own rules.
- The kernel. The build has reached its last stage: a bare-metal kernel body that boots in a virtual machine into 64-bit mode on its own page tables, lays out its memory, and answers system calls. It does not yet run a program of its own; that is the unit being built now.

These are not in this code. They arrive in a later public copy.

## Designed on paper, not built

- The AI team that is meant to work inside it. The box exists in this code; it is empty.
- Running on its own hardware without Linux underneath.

## What is not true yet

Read this before trusting it with anything that matters.

- **The locks are real when you install them.** Nothing is installed by default, and by default the keys are stand-ins of the right shape, as before. Install the named library and signing and sealing are real cryptography. Either way, whoever holds the disk or administers the running machine can read what it holds. In the build team's exact words, which appear in every page that mentions keys:

> Real cryptography is in this code and is off until you turn it on. Install the one vetted library it names and every key is real: signatures, key wrapping and sealed content are done by that library, never by our own code, and the signing seed never touches the disk. Install nothing, and the code runs exactly as the previous release did, with keys that are stand-ins of the right shape; anything that asks for a real signature is then refused rather than faked, so a real key can never quietly become a stand-in. Two limits stay true in both states: a reader who has the disk can read the sealed bytes of the secrets store, and an administrator of the running machine can read the program's memory, where the keys that open sealed content live. Protect the disk and the machine by other means; this code does not.

- **One machine, one user.** Every speed figure we publish comes from one computer with one user at a time.
- **The record can be wrong while every view of it is right.** Once, two things created at the same instant produced two entries for one act. The checks run from the record outward, never the other way.
- **A known defect: rename and replay.** Some programs save a file by writing a new one and renaming it over the old. The record then holds two entries for one file and the rebuild merges them. This is why the demo stops at `git add` and never reaches `git commit`. Renaming a folder with contents, and renaming one of two names for the same file, were also wrong and are repaired in this code.
- **An outside AI reviewer has tested it twice.** What it found is in the section below. The written list of things still to try has not all been attempted.
- **An administrator can edit the file.** Someone with full rights on the machine can change the record. The chain will show where. It cannot stop them.
- **The two watchdogs have only been tested on one machine.** Two components check each other's saved states. Whether they stay independent on two separate machines is later work.

## Found by an outside reader, an AI

Between 8 and 9 September 2026 I ran an independent security review of the previous public copy of this code: an AI reviewer, separate from the AI team that builds the system, with its own tests, twice. The build team was given its findings and nothing else, not its test programs and not its harness, so that the repairs came from our own reading of our own code at the line named, and every repair is tested from our own description of the correct behaviour. That separation is deliberate and it stays: the review will keep running against each public copy, independently of the build, to cover more of the ground each time.

Nothing they found breaks a promise made in the current round of work. Everything real that they found is older than that round, in parts of the program that round did not touch. The first report gave us eleven such items and six that were already written on this page or are the way the program is meant to work. The second report gave us twelve more, and the reviewer's own description of them is right: each part is correct on its own, and what is missing is the agreement between parts. Measuring one of the first items on a real mounted filesystem, rather than inside a test, turned up two further items of our own.

The ones that matter most, in plain words:

- A handover removed the content before the rulebook had decided whether the handover was allowed. Now the decision comes first, is written down, and only then does the content leave.
- A write the rulebook refused could still be read back through the mounted filesystem for as long as the operating system kept a copy of it. The mount now sends every read to the record instead of keeping a copy. That has a price, and the price is real: a program that maps a file into memory for shared writing is refused by the operating system; a program that writes and reads through two open handles before saving sees what was last saved, not its own unsaved write; and a second program reading a file after another program's refused write sees what was last saved, never the refused bytes. We measured all three on a real mount and kept the measurements.
- A permission that a later rule had overturned still counted when a new action asked for it. One check now decides what is still in force, and every part of the program that grants or holds something asks it.
- Two copies of the program could open the same record at once and each write the same entry number. The record was given a one-writer rule. A third round, below, found that rule could still be beaten. The repair is made in the private repository and ships at the next release; the code in this copy still checks a process-id file.
- Stored content was trusted by its name and not by its bytes. It is now checked against its bytes each time, and a missing item is refused rather than served as an empty file.
- A file created on the mount was written down as belonging to the administrator, whatever account created it. It is now written down as belonging to the account that created it.

The rest are smaller and are listed, one line each, with their repair, in the private repository's build record. The repairs are in this code, with the tests that prove them.

On 13 September I ran a third round, the same way, on this public copy. It found four things. The one-writer rule above could be beaten by racing real processes, so two writers got in. A half-written last line in the record stopped the program from opening instead of being set aside. A value the record could not write down came back as an error instead of a refusal, and left the record refusing everything after it. And the shipped test runner would have passed an empty test folder. All four are repaired and tested in the private repository and ship at the next release. Until then this copy carries them, and this page says so.

## What you can and cannot check from here

The commit numbers in `code/RENDER-STAMP.json` and `code/FREEZE.txt` belong to the private repository. You cannot look them up from here. Treat them as stamps. What you can check is the three tags on this repository, `milestone-0-seed`, `c4-close` and `c5-close`, the sixteen checks, and the shipped test suite with its printed fingerprints.

## If you want to know more

Email kelvin@rootrebuilder.org, or open an issue on this repository. Questions, criticism and a stranger's run of the three commands are all welcome; say which machine you ran on.

---

© Kelvin Chau, 2026 · This document: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
Part of the [AWIG OS](./README.md) project.
