/* SPDX-License-Identifier: GPL-3.0-or-later
 * gov-os freestanding body. Copyright (C) Kelvin Chau.
 * Licensed under the GNU General Public License, version 3 or later.
 * See LICENSE and LICENSING.md at the public repository root. */
/* gov-os body — the five record acts, self-checked on the metal (C7 P3b-2; A1/A2).
 *
 * disk_selfcheck() performs each of the five record acts on the body's OWN disk and proves each is
 * FUNCTIONAL, not merely present — writing and reading back through the block device, so a PASS
 * means the bytes actually rode the disk. Each act prints CHECK <ACT>: PASS/FAIL on the serial
 * line; a planted fault (a -D flag, see build.sh) reds exactly its act — the check can fail (A2).
 *
 *   record-pen         append a record, read it back equal; the append-only guard REFUSES an
 *                      in-place overwrite of the record, and the head survives it
 *   atomic-write-once  a blob written once, read back durable; a SECOND write to the same id is
 *                      refused and does NOT corrupt the first bytes (write-once)
 *   remove             a blob removed and gone; a remove of the RECORD is refused (blobs only)
 *   body-read          a walk that enumerates exactly the body's own present files
 *   founding-pack-read  the pack read from the disk, its crc equal to the recorded pack's
 *
 * disk_verify_persisted() runs on a REBOOT (a record already present): it reads record #0 and the
 * write-once blob back from disk and confirms they survived the reboot — durability across an
 * actual reboot, the state a fast no-reboot loop never visits (§A33). Read whole; guest-only.
 */
#include "body.h"
#include "disk.h"

/* C7 P3b-5a-ii — the /rec/ namespace acts' body-side proof lives in serve.c; the DISK phase (this file,
 * called by kmain) is where the record disk is mounted fresh, so it drives the NS self-check here. It
 * prints its OWN CHECK NS-A2/A3/A4/A5 + NS-ACTS lines and its result is kept SEPARATE from ACTS (the
 * five P3b-2 record acts), so this addition does not couple the P3b-2 aggregate to the namespace acts. */
int serve_ns_selfcheck(void);

/* The fixed self-check payloads — shared by the fresh self-check and the reboot verification so the
 * two boots compare against the same known bytes. */
const char DISK_RECORD0[]     = "{\"actor\":\"BODY\",\"action\":\"record-pen\",\"object\":\"self-check\",\"seq\":0}";
const char DISK_BLOB_SELF_A[] = "gov-os body write-once blob self-a: durable, written exactly once.";

static int check_record_pen(void) {
    uint32_t n = str_len(DISK_RECORD0);
    uint32_t start = 0;
    if (fs_record_append((const uint8_t *)DISK_RECORD0, n, &start) != 0) { return 0; }

    uint8_t back[256]; uint32_t blen = 0;
    int equal = (fs_record_read(start, back, sizeof(back), &blen) == 0)
                && blen == n && mem_eq(back, DISK_RECORD0, n);

    /* the append-only guard REFUSES an in-place overwrite of the record (off 0 is not the tail). */
    uint32_t dummy = 0;
    int refused = (fs_record_write_at(0, (const uint8_t *)"X", 1, &dummy) != 0);

    /* and the record head is UNCHANGED after the refused overwrite. */
    uint8_t head[256]; uint32_t hlen = 0;
    int head_intact = (fs_record_read(start, head, sizeof(head), &hlen) == 0)
                      && hlen == n && mem_eq(head, DISK_RECORD0, n);

    return equal && refused && head_intact;
}

/* ── C7 P7b — THE DEVICE-DISCOVERY EMITTER (design/54 §7 P7b; §3 B7 second half + B10; archi :4605) ──
 * At bring-up the body records ONE discovery row per device it performs over the settled three-device
 * list (block, network, clock; Q4 :3919), each an append riding the EXISTING record-pen act
 * (fs_record_append — no new act kind, ACT_KINDS stays 12), its payload naming the identity the body
 * EXPORTS at bring-up:
 *   block    ata_present's verdict (present/absent)
 *   network  net_wire_selfcheck's class (PASS/ABSENT/FAIL) + the MAC net_nic_bringup exports —
 *            NEVER the file-static PCI vendor/device id / slot / BAR (net.c keeps pci_find_virtio_net,
 *            g_dev, g_iobase and the pci_cfg_read helpers file-static and never exports them to kmain;
 *            re-probing them would edit a driver or add a PARALLEL probe — the precision, archi :4605)
 *   clock    rtc_read's presence (a plausible calendar time) + clock_epoch_seconds' epoch
 * Each row is appended, READ BACK from the record equal (it actually rode the disk — L19, a real
 * probe, never a fabricated event) and printed for the acceptance to trace to the real probe results.
 * This lives BESIDE check_record_pen in the boot member: the device DRIVERS ata.c/clock.c/net.c are
 * BYTE-UNCHANGED (only a boot-time append is added, here — never in the drivers); no new src/body
 * file, so ATTESTED stays 88.
 *
 * PLANT_DISCOVERY_PHANTOM (A1 near-miss — a check that CAN fail): the network row records a PHANTOM
 * present (class=PASS) even when the probe found the NIC ABSENT — so a boot with no NIC records a row
 * whose identity DISAGREES with the real net class, and the acceptance's trace check reds. A REAL
 * divergence between the recorded identity and the probe, never a flag toggling a verdict. */
static const char DD_HEX[] = "0123456789abcdef";

static uint32_t dd_put_str(uint8_t *buf, uint32_t pos, const char *s) {
    uint32_t n = str_len(s);
    for (uint32_t i = 0; i < n; i++) { buf[pos + i] = (uint8_t)s[i]; }
    return pos + n;
}
static uint32_t dd_put_hex32(uint8_t *buf, uint32_t pos, uint32_t v) {
    buf[pos++] = '0'; buf[pos++] = 'x';
    for (int i = 7; i >= 0; i--) { buf[pos++] = (uint8_t)DD_HEX[(v >> (i * 4)) & 0xF]; }
    return pos;
}
static uint32_t dd_put_hex64(uint8_t *buf, uint32_t pos, uint64_t v) {
    buf[pos++] = '0'; buf[pos++] = 'x';
    for (int i = 15; i >= 0; i--) { buf[pos++] = (uint8_t)DD_HEX[(v >> (i * 4)) & 0xF]; }
    return pos;
}
static uint32_t dd_put_mac(uint8_t *buf, uint32_t pos, const uint8_t mac[6]) {
    for (int i = 0; i < 6; i++) {
        if (i) { buf[pos++] = ':'; }
        buf[pos++] = (uint8_t)DD_HEX[(mac[i] >> 4) & 0xF];
        buf[pos++] = (uint8_t)DD_HEX[mac[i] & 0xF];
    }
    return pos;
}

/* append one discovery-row payload, read it back from the record equal (it rode the disk — L19), and
 * print the row AS READ BACK (so the serial IS the record read-back the acceptance traces). 1 iff the
 * append succeeded and the read-back is byte-equal. */
static int dd_emit_row(const uint8_t *payload, uint32_t n) {
    uint32_t start = 0;
    if (fs_record_append(payload, n, &start) != 0) {
        serial_puts("DEVICE-DISCOVERY: [append-FAIL]\n");
        return 0;
    }
    uint8_t back[256]; uint32_t blen = 0;
    int equal = (fs_record_read(start, back, sizeof(back), &blen) == 0)
                && blen == n && mem_eq(back, payload, n);
    serial_puts("DEVICE-DISCOVERY: ");
    for (uint32_t i = 0; i < blen; i++) { serial_putc((char)back[i]); }
    serial_puts(equal ? " [readback=ok]\n" : " [readback=FAIL]\n");
    return equal;
}

int disk_record_device_discovery(int block_present, int net_class,
                                 const uint8_t net_mac[6], int net_mac_valid,
                                 int clock_present, uint64_t clock_epoch) {
    uint8_t buf[256];
    uint32_t pos;
    int ok = 1, count = 0;

    /* ── block: ata_present's verdict (present/absent) ── */
    pos = dd_put_str(buf, 0, "device-discovery device=block present=");
    pos = dd_put_hex32(buf, pos, (uint32_t)(block_present ? 1 : 0));
    ok &= dd_emit_row(buf, pos); count++;

    /* ── network: the wire self-check's class + the exported MAC (never the file-static PCI id) ── */
    {
        int cls = net_class;          /* 0 PASS, 1 FAIL, 2 ABSENT (net_wire_selfcheck's return) */
#ifdef PLANT_DISCOVERY_PHANTOM
        cls = 0;                      /* THE PLANT: record PRESENT (PASS) whatever the probe found */
#endif
        pos = dd_put_str(buf, 0, "device-discovery device=network class=");
        pos = dd_put_str(buf, pos, cls == 0 ? "PASS" : (cls == 2 ? "ABSENT" : "FAIL"));
        if (cls == 0 && net_mac_valid) {
            pos = dd_put_str(buf, pos, " mac=");
            pos = dd_put_mac(buf, pos, net_mac);
        }
        ok &= dd_emit_row(buf, pos); count++;
    }

    /* ── clock: rtc_read's presence + clock_epoch_seconds' epoch ── */
    pos = dd_put_str(buf, 0, "device-discovery device=clock present=");
    pos = dd_put_hex32(buf, pos, (uint32_t)(clock_present ? 1 : 0));
    pos = dd_put_str(buf, pos, " epoch=");
    pos = dd_put_hex64(buf, pos, clock_epoch);
    ok &= dd_emit_row(buf, pos); count++;

    serial_puts("DEVICE-DISCOVERY-COUNT: 0x");
    serial_puthex32((uint32_t)count);
    serial_puts("\n");
    return ok && (count == 3);
}

/* ── C7 P5 — THE SEALED-ARTIFACT ROWS (design/54 §3 B6; §5 L18/L19/L2/L14/L9; §7 P5; countersign archi
 * :4622, RE-MINT on :4620 READING 2 — the core self-attest runs in the REAL boot pipeline, not a test rig) ──
 * At bring-up the body names BOTH sealed released artifacts it runs on — its OWN core image (the body's own
 * released image, STAGED BY THE PIPELINE build.sh as a verbatim copy core.img and carried as a boot-time
 * multiboot module beside the sealed interpreter, read through the direct map exactly as the interpreter
 * image is — so the SAME production invocation every B6 boot uses carries and self-checks it, L9: our own
 * kernel, read whole) and the INTERPRETER (the sealed image) — by hash in ONE
 * record row EACH on its OWN record disk, each an fs_record_append riding the EXISTING record-pen act (no
 * 13th act kind; ROWS_ACT_COUNT stays 12). At EVERY LATER boot it RE-HASHES each artifact and compares TO
 * ITS ROW — the record is the reference, never a compiled-in constant (the core cannot carry its own
 * expected hash inside the bytes being hashed; archi :4615 rider 1). A REAL planted byte change in EITHER
 * artifact's module bytes (the PLANT_WORKER_IMAGE_TAMPER class — a real byte, never a flag; L19) makes the
 * re-hash disagree with the row and reds the boot attestation, each way independently; a clean boot passes.
 *
 * This is the body's OWN record-disk row (L18 — the body cannot sign into the estate's chain, so B6's
 * "record row … part of the body check" is a row the freestanding body reads at boot); the estate's
 * off-body attestation set is untouched. The on-metal hash reuses the EXISTING sha256 primitive (declared
 * extern here — the enclosure.c form; no new src/body header, so ATTESTED stays 88; archi :4615 rider 2).
 *
 * Runs ONLY when a CORE module is present — the RELEASED B6 configuration the pipeline stages (a 2-module
 * boot: -initrd sealed.img,core.img, both build.sh artifacts). Every existing 0/1-module boot (the other
 * production configs) leaves it inert — no row written, no re-check, existing boots byte-unchanged (A5). */
extern void sha256(const uint8_t *data, uint32_t len, uint8_t out[32]);

static const char SA_CORE_PREFIX[]   = "sealed-artifact artifact=core sha256=";
static const char SA_INTERP_PREFIX[] = "sealed-artifact artifact=interpreter sha256=";

static uint32_t sa_put_hex(uint8_t *buf, uint32_t pos, const uint8_t *d, uint32_t n) {
    for (uint32_t i = 0; i < n; i++) {
        buf[pos++] = (uint8_t)DD_HEX[(d[i] >> 4) & 0xF];
        buf[pos++] = (uint8_t)DD_HEX[d[i] & 0xF];
    }
    return pos;
}

/* Scan the fixed append-only record for the FIRST row that begins with `prefix`; on a hit, copy the 64 hex
 * chars that follow into out_hex[64] and return 1; else 0. A bounded walk over the record entries (each a
 * 16-byte RECK header + payload, sector-granular — disk.h): fs_record_read yields the payload length, and
 * the next entry sits span = ceil((16 + len)/512) sectors on. */
static int sa_find_row(const char *prefix, char out_hex[64]) {
    struct bfs_entry *e = fs_find("record");
    if (!e) { return 0; }
    uint32_t plen = str_len(prefix);
    uint32_t base = e->start_sector;
    uint32_t end  = base + e->length / SECTOR_SIZE;
    uint8_t buf[256]; uint32_t blen = 0;
    for (uint32_t sec = base, guard = 0; sec < end && guard < 4096u; guard++) {
        if (fs_record_read(sec, buf, sizeof(buf), &blen) != 0) { break; }
        if (blen >= plen + 64u && mem_eq(buf, prefix, plen)) {
            for (uint32_t i = 0; i < 64u; i++) { out_hex[i] = (char)buf[plen + i]; }
            return 1;
        }
        uint32_t span = (uint32_t)((sizeof(struct bfs_rechdr) + blen + SECTOR_SIZE - 1u) / SECTOR_SIZE);
        if (span == 0u) { break; }
        sec += span;
    }
    return 0;
}

/* BRING-UP: append ONE sealed-artifact row (prefix + 64 hex of the digest), read it back equal (it rode the
 * disk — L19), and print the row AS READ BACK. 1 iff appended + read-back byte-equal. */
static int sa_write_row(const char *prefix, const uint8_t digest[32]) {
    uint8_t buf[256];
    uint32_t pos = dd_put_str(buf, 0, prefix);
    pos = sa_put_hex(buf, pos, digest, 32);
    uint32_t start = 0;
    if (fs_record_append(buf, pos, &start) != 0) {
        serial_puts("SEALED-ARTIFACT: [append-FAIL]\n");
        return 0;
    }
    uint8_t back[256]; uint32_t blen = 0;
    int equal = (fs_record_read(start, back, sizeof(back), &blen) == 0)
                && blen == pos && mem_eq(back, buf, pos);
    serial_puts("SEALED-ARTIFACT WROTE: ");
    for (uint32_t i = 0; i < blen; i++) { serial_putc((char)back[i]); }
    serial_puts(equal ? " [readback=ok]\n" : " [readback=FAIL]\n");
    return equal;
}

/* EVERY LATER BOOT: read the stored row's 64 hex, hex-format the fresh digest, compare; print the verdict
 * with both hashes so the acceptance traces the re-check. 1 iff the fresh digest equals the row (PASS). */
static int sa_recheck_row(const char *name, const char *prefix, const uint8_t digest[32]) {
    char stored[64];
    if (!sa_find_row(prefix, stored)) {
        serial_puts("SEALED-ARTIFACT "); serial_puts(name);
        serial_puts(": FAIL (no row on the record)\n");
        return 0;
    }
    uint8_t fresh[64];
    (void)sa_put_hex(fresh, 0, digest, 32);            /* writes exactly 64 hex chars */
    int match = mem_eq(fresh, stored, 64);
    serial_puts("SEALED-ARTIFACT "); serial_puts(name);
    if (match) {
        serial_puts(": PASS (sha256=");
        for (int i = 0; i < 64; i++) { serial_putc(stored[i]); }
        serial_puts(" matches its row)\n");
    } else {
        serial_puts(": FAIL (row=");
        for (int i = 0; i < 64; i++) { serial_putc(stored[i]); }
        serial_puts(" got=");
        for (int i = 0; i < 64; i++) { serial_putc((char)fresh[i]); }
        serial_puts(")\n");
    }
    return match;
}

int disk_record_sealed_artifacts(uint64_t core_phys, uint64_t core_len,
                                 uint64_t interp_phys, uint64_t interp_len) {
    /* only in the released configuration where BOTH sealed artifacts are present as modules — otherwise
     * inert (an existing 0/1-module boot writes no row and re-checks nothing; existing boots unchanged). */
    if (core_phys == 0 || core_len == 0 || interp_phys == 0 || interp_len == 0) {
        return 1;
    }
    uint8_t core_dig[32], interp_dig[32];
    sha256((const uint8_t *)phys_to_virt(core_phys),   (uint32_t)core_len,   core_dig);
    sha256((const uint8_t *)phys_to_virt(interp_phys), (uint32_t)interp_len, interp_dig);

    char probe[64];
    int have = sa_find_row(SA_CORE_PREFIX, probe);   /* the two rows are written together; core presence == both */
    int ok;
    if (!have) {
        /* BRING-UP (A1): name each sealed artifact by hash in ONE record-pen row. */
        int c = sa_write_row(SA_CORE_PREFIX,   core_dig);
        int i = sa_write_row(SA_INTERP_PREFIX, interp_dig);
        serial_puts("SEALED-ARTIFACT-COUNT: 0x00000002\n");
        ok = c && i;
    } else {
        /* EVERY LATER BOOT (A2): re-hash each artifact and compare TO ITS ROW; a tampered byte reds. */
        int c = sa_recheck_row("CORE",   SA_CORE_PREFIX,   core_dig);
        int i = sa_recheck_row("INTERP", SA_INTERP_PREFIX, interp_dig);
        ok = c && i;
    }
    return ok;
}

static int check_atomic_write_once(void) {
    uint32_t n = str_len(DISK_BLOB_SELF_A);
    int w1 = fs_blob_write_once("self-a", (const uint8_t *)DISK_BLOB_SELF_A, n);

    uint8_t back[128]; uint32_t blen = 0;
    struct bfs_entry *e = fs_find("self-a");
    int durable = e != 0 && fs_read_entry(e, back, sizeof(back), &blen) == 0
                  && blen == n && mem_eq(back, DISK_BLOB_SELF_A, n);

    /* a SECOND write to the same id must be refused and must NOT corrupt the first bytes. */
    const char *other = "SECOND WRITE — must be refused, must not corrupt the first blob's bytes.";
    int w2 = fs_blob_write_once("self-a", (const uint8_t *)other, str_len(other));

    uint8_t back2[128]; uint32_t blen2 = 0;
    struct bfs_entry *e2 = fs_find("self-a");
    int intact = e2 != 0 && fs_read_entry(e2, back2, sizeof(back2), &blen2) == 0
                 && blen2 == n && mem_eq(back2, DISK_BLOB_SELF_A, n);

    return w1 == 0 && durable && w2 != 0 && intact;
}

static int check_remove(void) {
    const char *z = "gov-os body removable blob self-b — the handover removal tail.";
    int w = fs_blob_write_once("self-b", (const uint8_t *)z, str_len(z));
    int present_before = (fs_find("self-b") != 0);
    int rm = fs_remove("self-b");
    int gone = (fs_find("self-b") == 0);
    /* remove applies to blobs, NEVER the record: a remove of the record is refused. */
    int record_refused = (fs_remove("record") != 0);
    return w == 0 && present_before && rm == 0 && gone && record_refused;
}

/* C7-MAINT-BODY-READ-CHECK — the body's present-files walk is checked against the CURRENT disk layout
 * AS DATA (L14: a pin guards a PROPERTY not a location). The record disk carries, beyond the always-present
 * `record` + `founding-pack` and the self-check's own runtime `self-a` (self-b removed): the OPTIONAL CONTENT
 * src/body/mkdisk.py stages — the gov-os gate blobs + the guest test key (C7 P3b-4g, mkdisk GATE_MODULES +
 * "syskey"), the named module to run (C7 P3b-5b-i, "runmod"), and the whole-tree archive (C7 P3b-5a-iii,
 * "govtree"). A clean boot with ANY subset of that content staged reads the disk honestly; an entry OUTSIDE
 * this known set still trips `unexpected` and reds the check (the guard stays able to fail). THESE NAMES ARE
 * DERIVED FROM mkdisk.py, not hand-counted — tests/test_c7_maint_body_read_check.py binds this list to
 * mkdisk.py's staged names as data, so a staging change reds until this list re-points. */
#define BODY_READ_WALK_MAX 16   /* >= record + founding-pack + 8 gate + syskey + runmod + govtree + self-a */

static int body_read_is_staged_content(const char *nm) {
    /* the optional content mkdisk.py can stage on the record disk — accepted (present, not unexpected). */
    return fs_name_eq(nm, "ker_init.py")   || fs_name_eq(nm, "keys.py")
        || fs_name_eq(nm, "crypto.py")     || fs_name_eq(nm, "canonical.py")
        || fs_name_eq(nm, "signer.py")     || fs_name_eq(nm, "brg_init.py")
        || fs_name_eq(nm, "host_seam.py")  || fs_name_eq(nm, "syskey")
        || fs_name_eq(nm, "runmod")        || fs_name_eq(nm, "govtree");
}

static int check_body_read(void) {
    /* after write-once (self-a present) and remove (self-b gone): record, founding-pack, self-a are the
     * body's OWN required files; any staged content (gate/runmod/govtree) is accepted; anything else is
     * UNEXPECTED and reds the check (L14 — the location re-points to the current layout, the property held).
     * (C7 P3b-5a-ii: fs_walk surfaces full-width path names.) */
#ifdef PLANT_BODY_READ_GHOST
    /* the plant: a GHOST entry (a name in no expected set) is staged on the disk — the walk surfaces it,
     * the check trips `unexpected` and reds. This proves the unexpected-entry refusal can still fail (A1/A3). */
    fs_blob_write_once("ghost-entry", (const uint8_t *)"g", 1);
#endif
    char names[BODY_READ_WALK_MAX][BFS_NAME_MAX];
    int c = fs_walk(names, BODY_READ_WALK_MAX);
    int has_record = 0, has_pack = 0, has_self_a = 0, has_self_b = 0, unexpected = 0;
    for (int i = 0; i < c; i++) {
        if (fs_name_eq(names[i], "record")) { has_record = 1; }
        else if (fs_name_eq(names[i], "founding-pack")) { has_pack = 1; }
        else if (fs_name_eq(names[i], "self-a")) { has_self_a = 1; }
        else if (fs_name_eq(names[i], "self-b")) { has_self_b = 1; }
        else if (body_read_is_staged_content(names[i])) { /* known staged content — accepted */ }
        else { unexpected = 1; }
    }
    return has_record && has_pack && has_self_a && !has_self_b && !unexpected;
}

static int check_founding_pack_read(void) {
    uint32_t plen = 0, pcrc = 0; int match = 0;
    int r = fs_founding_pack_read(&plen, &pcrc, &match);
    /* print for the acceptance cross-check against the real founding-pack.json's length + crc. */
    serial_puts("PACK: len=0x"); serial_puthex32(plen);
    serial_puts(" crc=0x"); serial_puthex32(pcrc); serial_puts("\n");
    return r == 0 && match;
}

int disk_selfcheck(void) {
    int rp = check_record_pen();
    int wo = check_atomic_write_once();
    int rm = check_remove();
    int br = check_body_read();
    int fp = check_founding_pack_read();

    serial_puts(rp ? "CHECK RECORD-PEN: PASS\n"        : "CHECK RECORD-PEN: FAIL\n");
    serial_puts(wo ? "CHECK ATOMIC-WRITE-ONCE: PASS\n" : "CHECK ATOMIC-WRITE-ONCE: FAIL\n");
    serial_puts(rm ? "CHECK REMOVE: PASS\n"            : "CHECK REMOVE: FAIL\n");
    serial_puts(br ? "CHECK BODY-READ: PASS\n"         : "CHECK BODY-READ: FAIL\n");
    serial_puts(fp ? "CHECK FOUNDING-PACK-READ: PASS\n": "CHECK FOUNDING-PACK-READ: FAIL\n");

    /* C7 P3b-5a-ii — the /rec/ namespace acts at caller-named paths (A2-A5), on the freshly-mounted
     * record disk. Prints its own CHECK NS-* + NS-ACTS lines; NOT folded into the ACTS return above. */
    (void)serve_ns_selfcheck();

    return rp && wo && rm && br && fp;
}

int disk_verify_persisted(void) {
    /* the REBOOT path: a prior boot appended record #0 and wrote self-a; confirm they survived. */
    struct bfs_entry *rec = fs_find("record");
    uint8_t back[256]; uint32_t blen = 0;
    int rok = rec != 0
              && fs_record_read(rec->start_sector, back, sizeof(back), &blen) == 0
              && blen == str_len(DISK_RECORD0) && mem_eq(back, DISK_RECORD0, blen);

    struct bfs_entry *e = fs_find("self-a");
    uint8_t b2[128]; uint32_t l2 = 0;
    int bok = e != 0 && fs_read_entry(e, b2, sizeof(b2), &l2) == 0
              && l2 == str_len(DISK_BLOB_SELF_A) && mem_eq(b2, DISK_BLOB_SELF_A, l2);

    serial_puts(rok ? "PERSISTED: RECORD OK\n" : "PERSISTED: RECORD FAIL\n");
    serial_puts(bok ? "PERSISTED: BLOB OK\n"   : "PERSISTED: BLOB FAIL\n");
    return rok && bok;
}
