#!/usr/bin/env bash
# gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: maintenance ·
# NON-GOAL: no offensive capability. Full declaration: SCOPE-STATEMENT.md.
#
# DISK-HYGIENE — routine, automatic reclamation of NO-IMPACT space.
# Owner ruling 2026-09-13 (first-party, emergency): the disk filled to 100%
# and broke the estate, and it had happened before; file management hygiene is
# now LAW and runs on a timer, not by anyone remembering. Definitive:
# planning/method/DISK-HYGIENE-LAW.md.
#
# It deletes ONLY regenerable junk. It NEVER touches: the repo / the record,
# any archive folder, the Backups, reference/, or the live guest image
# (gov-lab.qcow2). It is idempotent and safe to run at any time.
set -u
LOG="${GOVOS_HYGIENE_LOG:-<HOME>/Documents/Claude/apps/gov-os/planning/method/DISK-HYGIENE-DELETIONS.log}"
ts() { date -u +%Y-%m-%dT%H:%M:%SZ; }
free_now() { df -h / | awk 'NR==2{print $4}'; }

{
  echo "=== HYGIENE RUN $(ts) — before: $(free_now) free ==="

  # 1. regenerable user caches (gnome-software, tracker, thumbnails, pip/npm)
  rm -rf ~/.cache/* 2>/dev/null && echo "cleared ~/.cache/*"

  # 2. trash
  rm -rf ~/.local/share/Trash/* 2>/dev/null && echo "emptied Trash"

  # 3. this user's temp older than a day, EXCEPT the live claude scratch
  find /tmp -maxdepth 1 -user "$(id -un)" ! -name 'claude-*' -mtime +0 \
       -exec rm -rf {} + 2>/dev/null && echo "pruned /tmp (mine, >1d, not claude-*)"
  find /var/tmp -maxdepth 1 -user "$(id -un)" -mtime +1 \
       -exec rm -rf {} + 2>/dev/null && echo "pruned /var/tmp (mine, >1d)"

  # 4. stale qemu OVERLAY images only — never gov-lab.qcow2 (the live guest),
  #    and only when unheld by any running process.
  for f in <HOME>/gov-lab/overlay*.qcow2; do
    [ -e "$f" ] || continue
    if ! fuser "$f" >/dev/null 2>&1; then
      sz=$(du -h "$f" | cut -f1); rm -f "$f" && echo "deleted stale overlay $f ($sz, unheld)"
    fi
  done

  # 5. system journal to a 200M cap (needs root; non-interactive only, never stalls)
  sudo -n journalctl --vacuum-size=200M 2>&1 | tail -1 || echo "journal vacuum skipped (no passwordless root)"

  echo "after: $(free_now) free"
  # WARN (not act) if the live guest image has ballooned — its reclamation needs
  # the guest idle/off and is the OWNER's call; this script never touches it.
  if [ -e <HOME>/gov-lab/gov-lab.qcow2 ]; then
    g=$(du -h <HOME>/gov-lab/gov-lab.qcow2 | cut -f1)
    # snapshot count is the balloon's real cause (archi :4151); read-only via -U
    # (force-share) so it is safe while the guest runs and never touches the image.
    if command -v qemu-img >/dev/null 2>&1; then
      snaps=$(qemu-img info -U <HOME>/gov-lab/gov-lab.qcow2 2>/dev/null | grep -c w3b-preload)
    else
      snaps="?"
    fi
    echo "NOTE: live guest image gov-lab.qcow2 = $g, $snaps w3b-preload snapshot(s) (reclamation is the owner's; not touched)"
  fi
} >> "$LOG" 2>&1
