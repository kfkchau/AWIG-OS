"""EP-28C W4d — the guest baseline's dup member, and why it still cannot ship.

WHAT W4d ASKED FOR: `tools/conformance/baselines/ep21-ubuntu-guest/06-files.json`'s
`files.dup` member re-captured under relative reporting, never hand-edited, so the
absolute-fd class enumerates EMPTY across BOTH baseline directories.

WHAT THIS PASS FOUND, BY RUNNING IT: the re-capture is CORRECT about `dup` and it carries an
UNRELATED stock-target behaviour change with it, exactly as the previous pass reported. The
pin therefore stays, for the second time, and this file is the finding pinned so it cannot
rot into a note.

THE PROCEDURE, VERIFIED RATHER THAN INHERITED. AMENDMENT 8 §8.3 corrected W4d's own text —
the item said "re-captured IN THE GUEST" and the documented procedure is HOST-RUN, reaching
the guest over ssh — and marked the correction "not run by this seat" (§A45's extension). It
is run by THIS seat and the correction is true: `tools/conformance/targets/ep21-ubuntu-
guest.json` declares `transport.type = "ssh"` to `<LOOPBACK-PORT>`, the capture executes from
the host, and the manifest it produces carries the GUEST's kernel string rather than the
host's. That last fact is the one that settles it, and it is asserted below.

THE PROVENANCE QUESTION, ANSWERED FURTHER THAN IT WAS ASKED. AMENDMENT 8 §8.2 and the
mentor's ledger read the chown row as evidence that "the 2026-07-26 capture ran with a
privilege today's does not." **That reading is REFUTED by the two manifests, which cost one
read each:** both captures record `target_identity.euid_is_root = false` AND
`root_pass_identity.euid_is_root = true`, so both ran the same unprivileged pass with the
same privileged pass available, on a byte-identical guest kernel string, at the same harness
version. Privilege is not the discriminator.

**The variable is the guest user's SUPPLEMENTARY GROUP MEMBERSHIP.** The row's step 1 is
`chown("o.txt", -1, 4)` — change the GROUP to gid 4, which POSIX permits an unprivileged
owner to do for a group they belong to. Measured in the guest at this writing: `id -G`
returns `1000` alone, and gid 4 is `adm`, whose only member is `syslog`. So the call must be
EPERM today and must have been permitted on 2026-07-26, which requires the caller to have
been in gid 4 then. **The honest residue, per §A21's own residue clause: WHEN and WHY the
membership went is not derivable from what this seat holds, and inventing a boundary for the
window would be worse than the drift.** Two candidates checked and neither explains it — the
cloud-init seed (`~/gov-lab/user-data`, mtime 2026-07-14, predates the pin) declares the user
with no `groups:` key at all, and the two-guests hypothesis is refuted by reading
`m0-boot.sh` and `m3-boot.sh`, which drive the SAME disk on the SAME port.

THE TRAVELLING CONDITION (§8.2, the §A47 shape) is asserted rather than described: while the
provenance stands unruled, any conformance figure citing the files baseline states the chown
row's disputed-provenance status beside it. The row below reads the pinned artifact and reds
if the disputed steps stop being disputed — which is the condition ending, at which point
this file is deleted rather than widened.

THE RED WORLD IS CARRIED, NOT REBUILT: EP-28H exhibited the hand-edit double for this class
and it is cited rather than re-driven, because re-driving a red world another pass already
produced through the same instrument adds a run and no information.
"""

import json
import os
import subprocess
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from tools.conformance.harness import probe                        # noqa: E402

BASELINES = os.path.join(REPO, "tools", "conformance", "baselines")
GUEST = "ep21-ubuntu-guest"
HOST = "host-local"

#: The three steps AMENDMENT 8 §8.2's condition travels with. Data, so the scope of the
#: condition is readable and so it cannot silently widen to a fourth step.
DISPUTED_CHOWN_STEPS = (1, 5, 7)


def fd_returning_calls():
    """The calls that return a descriptor, read from the HARNESS'S OWN normalizer map.

    STRUCTURE, NEVER A VALUE PATTERN (charter §A51, and §A49's first instance by name). An
    enumeration of "integers that look like descriptors" returns 35 members in this baseline
    of which two are descriptors and the rest are byte counts and offsets — which is the
    exact error the four `"ret": 3` pins were grouped by. The set below is whatever the
    harness itself routes through `_n_fd`, so a call that joins the relative scheme joins
    this enumeration in the same commit."""
    return {name for name, (_fn, norm) in probe.CALLS.items() if norm is probe._n_fd}


def absolute_fd_members(baseline):
    """Every step that ALLOCATED a descriptor and did not report it relatively.

    A step whose `errno` is set allocated nothing, so it is not a member — including it
    would inflate the class with refusals and make an empty class unreachable."""
    fdcalls = fd_returning_calls()
    out = []
    d = os.path.join(BASELINES, baseline)
    for name in sorted(os.listdir(d)):
        if not name.endswith(".json") or name == "MANIFEST.json":
            continue
        with open(os.path.join(d, name), encoding="utf-8") as fh:
            doc = json.load(fh)
        for row_id, row in (doc.get("rows") or {}).items():
            for step in row.get("steps") or []:
                if step.get("call") not in fdcalls or step.get("errno") is not None:
                    continue
                ret = step.get("ret")
                if not (isinstance(ret, str) and ret.startswith("fd#")):
                    out.append({"file": name, "row": row_id, "i": step.get("i"),
                                "call": step.get("call"), "ret": ret})
    return out


def manifest(baseline):
    with open(os.path.join(BASELINES, baseline, "MANIFEST.json"), encoding="utf-8") as fh:
        return json.load(fh)


class TheEnumerationReadsStructureCase(unittest.TestCase):
    """NON-VACUITY for the enumeration itself: an empty class and an enumeration that looked
    at nothing are the same output (§A38), so the subject is proven first."""

    def test_the_fd_returning_call_set_is_not_empty_and_is_read_from_the_harness(self):
        calls = fd_returning_calls()
        self.assertTrue(calls, "no call routes through the relative-fd normalizer, so the "
                               "enumeration below examines nothing")
        for expected in ("open", "dup", "dup2"):
            self.assertIn(expected, calls,
                          "%r stopped reporting descriptors relatively — the class this "
                          "file enumerates has changed shape" % expected)

    def test_both_baseline_directories_hold_fd_returning_steps_to_enumerate_over(self):
        fdcalls = fd_returning_calls()
        for baseline in (GUEST, HOST):
            seen = 0
            d = os.path.join(BASELINES, baseline)
            for name in sorted(os.listdir(d)):
                if not name.endswith(".json") or name == "MANIFEST.json":
                    continue
                with open(os.path.join(d, name), encoding="utf-8") as fh:
                    doc = json.load(fh)
                for row in (doc.get("rows") or {}).values():
                    seen += sum(1 for s in row.get("steps") or []
                                if s.get("call") in fdcalls)
            self.assertGreater(seen, 0,
                               "%s holds no descriptor-returning step at all, so 'the class "
                               "is empty here' would be true for the wrong reason" % baseline)


class TheAbsoluteFdClassCase(unittest.TestCase):
    """The class, enumerated, and its members NAMED rather than counted."""

    def test_the_host_side_is_EMPTY_which_is_what_EP_28H_already_closed(self):
        self.assertEqual(absolute_fd_members(HOST), [],
                         "the host-local baseline grew an absolute descriptor back")

    def test_THE_EXPIRY_the_guest_side_still_holds_exactly_the_two_dup2_members(self):
        """W4d's subject, pinned with its own expiry (§A47 and its extension: the discharge
        changes the ARTIFACT, so the expiry reads the artifact).

        When the guest re-capture ships, this row goes RED and the file is deleted rather
        than widened. It is deliberately not written as `assertEqual(members, [])` with a
        skip: a row that passes today by being skipped is the note this rule replaces."""
        members = absolute_fd_members(GUEST)
        self.assertEqual([(m["row"], m["i"], m["call"]) for m in members],
                         [("files.dup", 6, "dup2"), ("files.dup", 9, "dup2")],
                         "EXPIRED or MOVED: the guest baseline's absolute-fd class is no "
                         "longer exactly the two dup2 steps W4d was sent for. If it is now "
                         "empty the re-capture shipped — delete this file and discharge "
                         "the carry.")
        self.assertEqual(sorted(m["ret"] for m in members), [3, 200],
                         "the two members no longer carry the raw integers that made them "
                         "members")


class TheTravellingConditionCase(unittest.TestCase):
    """AMENDMENT 8 §8.2's interim condition, asserted so it cannot rot into a note."""

    def test_the_three_chown_steps_the_condition_travels_with_are_still_the_pinned_ones(self):
        with open(os.path.join(BASELINES, GUEST, "06-files.json"), encoding="utf-8") as fh:
            row = json.load(fh)["rows"]["files.chown"]
        steps = {s["i"]: s for s in row["steps"]}
        for i in DISPUTED_CHOWN_STEPS:
            self.assertIn(i, steps)
            self.assertIsNone(steps[i]["errno"],
                              "step %d of files.chown no longer records a SUCCESS, so the "
                              "disputed-provenance condition has ended — delete it from "
                              "every citation that carries it" % i)
            self.assertIn(steps[i]["call"], ("chown", "lchown", "fchown"))

    def test_the_two_captures_ran_at_the_SAME_privilege_which_refutes_the_first_reading(self):
        """The provenance answer, read from the pinned artifact itself. This costs one file
        read and it retires a hypothesis that was heading for its own instrument pass."""
        m = manifest(GUEST)
        self.assertIs(m["target_identity"]["euid_is_root"], False,
                      "the pinned guest capture's ordinary pass ran privileged after all — "
                      "the privilege reading is back in play")
        self.assertIs(m["root_pass_identity"]["euid_is_root"], True,
                      "the pinned guest capture has no privileged pass, so 'both captures "
                      "had the same privilege available' is not established")
        self.assertEqual(m["target_identity"]["uname"]["release"], "6.8.0-134-generic",
                         "the pinned capture was taken on a kernel that is not the pin")


class TheProcedureIsHostRunCase(unittest.TestCase):
    """§A45's extension discharged: the description is written by a seat that RAN it."""

    def test_the_target_declares_an_ssh_transport_which_is_what_host_run_means(self):
        with open(os.path.join(REPO, "tools", "conformance", "targets",
                               "%s.json" % GUEST), encoding="utf-8") as fh:
            spec = json.load(fh)
        self.assertEqual(spec["transport"]["type"], "ssh")
        self.assertEqual(spec["transport"]["port"], 2222)
        self.assertEqual(spec["kind"], "stock")

    def test_the_pinned_manifest_carries_the_GUESTS_kernel_and_not_this_HOSTS(self):
        """The falsifiable half. A capture run inside the guest could not reach the guest
        over a host port; a capture run on the host that did NOT reach the guest would
        record the host's kernel. The pinned manifest records the guest's, so the capture
        crossed — and that is what 'host-run, over ssh' actually asserts."""
        import platform
        captured = manifest(GUEST)["target_identity"]["uname"]["release"]
        self.assertNotEqual(captured, platform.release(),
                            "the pinned guest baseline records THIS host's kernel, which "
                            "means it never reached the guest")
        self.assertEqual(captured, "6.8.0-134-generic")


class TheGroupMembershipIsTheVariableCase(unittest.TestCase):
    """The variable named, measured in the guest, and skipped honestly when the guest is
    not up — a row that silently passes without its subject is the shape §A39 refuses."""

    SSH = ["<SSH-INVOCATION>", "-o", "StrictHostKeyChecking=no",
           "-o", "UserKnownHostsFile=/dev/null", "-o", "ConnectTimeout=8",
           "-i", os.path.expanduser("<KEYPATH>"), "<GUEST>"]

    def _guest(self, cmd):
        try:
            r = subprocess.run(self.SSH + [cmd], capture_output=True, text=True, timeout=30)
        except (OSError, subprocess.SubprocessError) as exc:        # noqa: BLE001
            self.skipTest("the guest is not reachable from this box (%s) — this row states "
                          "a fact ABOUT the guest and declines to state it without one"
                          % exc)
        if r.returncode != 0:
            self.skipTest("the guest is not reachable (%s)" % (r.stderr.strip()[:120],))
        return r.stdout.strip()

    def test_the_guest_user_is_in_no_group_that_would_permit_the_pinned_chown(self):
        groups = self._guest("id -G").split()
        self.assertTrue(groups, "the guest returned no group list")
        self.assertNotIn("4", groups,
                         "the guest user IS in gid 4 now, so today's capture should record "
                         "the chown SUCCEEDING and the drift has reversed — re-take the "
                         "comparison before citing this file")

    def test_gid_4_is_a_real_group_the_row_could_have_been_permitted_by(self):
        """Non-vacuity for the row above: 'not a member of gid 4' says nothing if gid 4
        does not exist on this guest."""
        line = self._guest("getent group 4 || true")
        self.assertTrue(line, "gid 4 does not exist in the guest, so membership in it "
                              "cannot be the variable")
        self.assertTrue(line.startswith("adm:"), "gid 4 is not adm: %r" % line)


if __name__ == "__main__":
    unittest.main()
