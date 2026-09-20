"""ENVIRONMENT-HYGIENE — the whole-ledger guard on the live guest image (archi :4152).

FRAME: systems-architecture · CORPUS-CLASS: maintenance ·
NON-GOAL: no offensive capability of any kind. Full declaration: SCOPE-STATEMENT.md.

WHY THIS EXISTS. `tests/test_ep29.py`'s W3b bracket takes a whole-guest `savevm` (tag
`w3b-preload-<digest>-<timestamp>`) before every kernel-module load. Nothing deleted them
for eight days and 186 accumulated, growing `<HOME>/gov-lab/gov-lab.qcow2` to 339G on
~8G of real content until the host root disk filled to 100% and broke the estate (archi
:4151, DISK-HYGIENE-LAW.md §4). W3b now retires its own snapshot on a green load; THIS guard
is the second half — it reds the ledger at every close when the environment is unhealthy, so
a recurrence is a failing test rather than a filled disk discovered by an outage.

THE FOUR RED CONDITIONS, every figure DRIVEN here (never asserted from memory):
  1. the image holds MORE THAN ONE internal snapshot          (`qemu-img info -U`)
  2. any snapshot tag is OLDER THAN 24h                        (its DATE from the same read)
  3. the file's DISK USAGE exceeds 100G, the owner's cap       (`du`, disk usage not apparent)
  4. root free is UNDER 30%, the owner's floor (:3006)         (`os.statvfs('/')`)

DISK USAGE, NOT APPARENT SIZE, on purpose. A healthy qcow2 is sparse: 5.2G allocated behind a
20-GiB virtual / 339-GiB file length. The owner's 100G cap is about blocks actually consumed,
so the figure is `du` (allocated), and the ballooned-but-not-yet-freed apparent length never
reds a healthy image.

SAFE ON A MACHINE WITHOUT THE GUEST. The whole guard SKIPs when the image path is absent, so
it never reds on a checkout that has no lab. `evaluate()` is a pure function of driven
figures, so the same logic backs both the live guard and the self-tests that prove each red
condition CAN fire — a check that cannot fail is not a check.
"""

import datetime
import os
import re
import shutil
import subprocess
import tempfile
import unittest

IMG = "<HOME>/gov-lab/gov-lab.qcow2"

MAX_SNAPSHOTS = 1                       # a healthy image holds at most one recovery point
MAX_SNAPSHOT_AGE_H = 24                 # DISK-HYGIENE-LAW.md §4: older than a day is stale
DU_CAP_BYTES = 100 * 1024 ** 3          # owner's cap: 100G on disk
MIN_ROOT_FREE_PCT = 30.0                # owner's floor (:3006): 30% free


def evaluate(snapshots, du_bytes, root_free_pct, now,
             max_snapshots=MAX_SNAPSHOTS, max_age_h=MAX_SNAPSHOT_AGE_H,
             du_cap_bytes=DU_CAP_BYTES, min_free_pct=MIN_ROOT_FREE_PCT):
    """Return the list of red findings (empty == healthy).

    Pure: `snapshots` is [(tag, datetime), ...], `du_bytes`/`root_free_pct` are driven
    numbers, `now` is a datetime. No I/O, so the self-tests can drive each condition to red
    without a guest, and the live guard drives the same function with real figures."""
    reds = []
    if len(snapshots) > max_snapshots:
        reds.append("SNAPSHOTS: %d internal snapshot(s) (> %d allowed): %r"
                    % (len(snapshots), max_snapshots, [t for t, _ in snapshots]))
    stale = [(t, dt) for t, dt in snapshots
             if (now - dt).total_seconds() > max_age_h * 3600]
    if stale:
        reds.append("STALE-SNAPSHOT: %d tag(s) older than %dh: %r"
                    % (len(stale), max_age_h,
                       [(t, dt.isoformat(), round((now - dt).total_seconds() / 3600, 1))
                        for t, dt in stale]))
    if du_bytes > du_cap_bytes:
        reds.append("DU-SIZE: image is %.1f GiB on disk (> %d GiB owner cap)"
                    % (du_bytes / 1024 ** 3, du_cap_bytes // 1024 ** 3))
    if root_free_pct < min_free_pct:
        reds.append("ROOT-FREE: root is %.1f%% free (< %.0f%% owner floor, :3006)"
                    % (root_free_pct, min_free_pct))
    return reds


def parse_snapshots(info_text):
    """Parse the 'Snapshot list' section of `qemu-img info -U` output into
    [(tag, naive-local-datetime), ...]. Returns [] when there is no snapshot section.

    qemu prints the DATE in the host's LOCAL wall-clock, so the parsed datetime is naive
    local and is compared against `datetime.datetime.now()` (also naive local)."""
    rows = []
    in_section = False
    for ln in info_text.splitlines():
        stripped = ln.strip()
        if stripped.startswith("Snapshot list:"):
            in_section = True
            continue
        if not in_section:
            continue
        if stripped.startswith("ID") and "TAG" in stripped:
            continue                                            # the column header
        toks = stripped.split()
        m = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", ln)
        if not toks or not toks[0].isdigit() or m is None:
            break                                               # left the snapshot section
        tag = toks[1]
        dt = datetime.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
        rows.append((tag, dt))
    return rows


def _qemu_info(path):
    """`qemu-img info -U` (force-share, so it reads while the guest runs)."""
    return subprocess.run(["qemu-img", "info", "-U", path],
                          capture_output=True, text=True, timeout=120)


def _du_bytes(path):
    """Disk usage (allocated blocks) in bytes — `du -B1`, NOT apparent size."""
    r = subprocess.run(["du", "-B1", path], capture_output=True, text=True, timeout=120)
    return int(r.stdout.split()[0])


def _root_free_pct():
    """Root free as a percentage, driven from os.statvfs('/')."""
    st = os.statvfs("/")
    return 100.0 * st.f_bavail / st.f_blocks


class TheLiveGuestImageEnvironmentIsHealthy(unittest.TestCase):
    """The ledger guard proper: drive the four real figures against the live image and red
    if any is out of bounds. SKIPs when there is no guest image on this machine."""

    def test_the_live_guest_image_is_within_every_owner_bound(self):
        if not os.path.exists(IMG):
            self.skipTest("no guest image at %s — nothing to guard on this machine" % IMG)
        if shutil.which("qemu-img") is None:
            self.skipTest("qemu-img not installed — cannot read the image's snapshots")

        info = _qemu_info(IMG)
        self.assertEqual(info.returncode, 0,
                         "qemu-img info -U failed: %r" % (info.stderr or "")[-300:])
        snaps = parse_snapshots(info.stdout)
        du_bytes = _du_bytes(IMG)
        free_pct = _root_free_pct()

        # DRIVEN FIGURES, printed so the row's evidence is the numbers themselves.
        print("ENV-GUEST-IMAGE: snapshots=%d %r  du=%.2fGiB  root_free=%.1f%%"
              % (len(snaps), [t for t, _ in snaps], du_bytes / 1024 ** 3, free_pct))

        reds = evaluate(snaps, du_bytes, free_pct, datetime.datetime.now())
        if reds:
            self.fail(
                "GUEST-IMAGE ENVIRONMENT UNHEALTHY:\n  " + "\n  ".join(reds)
                + "\nFIX: delete stale w3b-preload snapshots with "
                  "`planning/vm/lab/m3-monitor.py delete <tag>`; compacting or replacing "
                  "the image itself is the owner's (DISK-HYGIENE-LAW.md §3).")


class EachRedConditionCanActuallyFire(unittest.TestCase):
    """A check that cannot fail is not a check. Each condition is driven to red — three
    through the pure evaluator, and the snapshot COUNT additionally through a REAL scratch
    qcow2 and the REAL `qemu-img`, so the parse itself is exercised end to end. The scratch
    file lives in a temp dir and is never `gov-lab.qcow2`."""

    def _now(self):
        return datetime.datetime(2026, 9, 13, 12, 0, 0)

    def test_more_than_one_snapshot_reds_via_real_qemu_img(self):
        if shutil.which("qemu-img") is None:
            self.skipTest("qemu-img not installed")
        with tempfile.TemporaryDirectory() as d:
            img = os.path.join(d, "scratch.qcow2")
            subprocess.run(["qemu-img", "create", "-f", "qcow2", img, "8M"],
                           capture_output=True, check=True, timeout=60)
            for tag in ("w3b-preload-aaaaaaaa-0101000000",
                        "w3b-preload-bbbbbbbb-0101000001"):
                subprocess.run(["qemu-img", "snapshot", "-c", tag, img],
                               capture_output=True, check=True, timeout=60)
            snaps = parse_snapshots(_qemu_info(img).stdout)
            self.assertEqual(len(snaps), 2, "the real qemu-img parse should see two tags")
            reds = evaluate(snaps, du_bytes=1, root_free_pct=90.0, now=datetime.datetime.now())
            self.assertTrue(any(r.startswith("SNAPSHOTS:") for r in reds), reds)

    def test_a_snapshot_older_than_24h_reds(self):
        now = self._now()
        old = now - datetime.timedelta(hours=25)
        reds = evaluate([("w3b-preload-x-0101", old)], du_bytes=1, root_free_pct=90.0, now=now)
        self.assertTrue(any(r.startswith("STALE-SNAPSHOT:") for r in reds), reds)

    def test_a_fresh_single_snapshot_does_not_red(self):
        now = self._now()
        fresh = now - datetime.timedelta(hours=2)
        self.assertEqual(
            evaluate([("w3b-preload-x-0101", fresh)], du_bytes=5 * 1024 ** 3,
                     root_free_pct=76.0, now=now), [])

    def test_disk_usage_over_100G_reds(self):
        reds = evaluate([], du_bytes=101 * 1024 ** 3, root_free_pct=90.0,
                        now=self._now())
        self.assertTrue(any(r.startswith("DU-SIZE:") for r in reds), reds)

    def test_root_free_under_30pct_reds(self):
        reds = evaluate([], du_bytes=1, root_free_pct=29.0, now=self._now())
        self.assertTrue(any(r.startswith("ROOT-FREE:") for r in reds), reds)

    def test_a_healthy_image_passes(self):
        # 0 snapshots, well under cap, well over floor — the current live shape.
        self.assertEqual(evaluate([], du_bytes=5 * 1024 ** 3, root_free_pct=76.0,
                                  now=self._now()), [])

    def test_the_boundaries_are_exclusive_as_worded(self):
        now = self._now()
        # exactly one snapshot is allowed; exactly at the cap / floor is NOT red.
        self.assertEqual(evaluate([("t", now)], du_bytes=DU_CAP_BYTES,
                                  root_free_pct=MIN_ROOT_FREE_PCT, now=now), [])
        # one byte over the cap, and a hair under the floor, both red.
        self.assertEqual(len(evaluate([], du_bytes=DU_CAP_BYTES + 1,
                                      root_free_pct=MIN_ROOT_FREE_PCT - 0.1, now=now)), 2)


if __name__ == "__main__":
    unittest.main()
