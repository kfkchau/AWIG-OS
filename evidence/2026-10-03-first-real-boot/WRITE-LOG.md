# The stick that booted: the write log

This note ties the image published as test stick 1 to the stick the film shows booting. The film's own provenance is in `PROVENANCE.md`; this adds the image side, from the author's write log.

## The image

| | |
|---|---|
| Built from | private commit `85d953f9`, 3 October 2026 |
| Size | 103,809,024 bytes |
| SHA-256 | `1f16d486b42787f9fb57fae847129fb030f0765496e4d36469ebbbd2ed923a95` |

The file in `test-stick/` has this hash once unpacked.

## The sticks

Three sticks were written from that image at the author's hand on 3 October 2026 with the project's own write tool, and each was read back whole and compared equal to the image (the tool prints READBACK-MATCH):

1. CBM Flash Disk, 1 GB, silver and yellow. **This is the stick in the film.** The project's board record of that day notes the laptop's firmware listing it for boot by serial `04114200B1702500`; the write log itself does not carry the serial. This write printed no WRITTEN line; its read-back, equal to the image whole, is what shows it complete. The event below fired during this write.
2. Generic, 15 GB, XTEK.
3. SanDisk Cruzer, blue.

One event is on the log and is kept here as the log kept it: a fourth stick plugged in while write 1 was in progress showed as CHANGED/UNREADABLE in the tool's check of other disks, because its own arrival moved its bytes. It was not written to and is not one of the three.

## What this lets a stranger check

Hash the published image: it equals the hash above. The write log says that image was written to the silver and yellow stick and read back equal; the board record of the day says the firmware listed that stick for boot by its serial. The film shows the boot. The log is the author's; the hash is anyone's to verify.
