/* SPDX-License-Identifier: GPL-3.0-or-later
 * gov-os freestanding body. Copyright (C) Kelvin Chau.
 * Licensed under the GNU General Public License, version 3 or later.
 * See LICENSE and LICENSING.md at the public repository root. */
/* gov-os body — OUR virtio-net NIC driver on the metal (C7 P3b-6a), and its callable frame API for the
 * borrowed TCP worker's enclosure (C7 P3b-6b; design/54 §7 P3b-6a/6b; §5 L18). Hand-written and read whole
 * (design/47 §2 I3, §9): no opaque code, no borrowed code — the network device's TRANSPORT is ours (the
 * borrowed TCP stack is 6b's enclosed worker, never here). Guest-only; every boot is the nested qemu inside
 * the pinned guest (L11).
 *
 * WHAT THIS DOES, AND WHAT PROVES IT (6a). net_wire_selfcheck() drives the virtio-net device as its own
 * transport and proves it ON THE WIRE, not by inspecting itself:
 *   NIC-BRINGUP  the body's own driver finds the device on the PCI bus, negotiates it (legacy virtio:
 *                reset -> ACKNOWLEDGE -> DRIVER -> feature negotiation -> the RX and TX virtqueues ->
 *                DRIVER_OK), reads the MAC the device offers, and brings both rings up.
 *   WIRE-ROUNDTRIP  the driver TRANSMITS an address-resolution request for the guest gateway (10.0.2.2)
 *                and RECEIVES THE GATEWAY'S REPLY off the receive ring — a real round trip answered by
 *                an OUTSIDE party (qemu's SLIRP gateway), NEVER a loopback of our own bytes.
 *
 * THE CALLABLE FRAME API (6b, archi :4295 precision 4 — HOW, mechanical; the fence note pre-authorizes).
 * net_nic_bringup / net_send_frame / net_recv_frame expose the SAME transport as callable functions so the
 * body can serve the enclosed borrowed-TCP worker's two frame shapes (serve.c crosses to them; the frames
 * are the worker's, unmodified lwIP's own). This adds NO served shape to net.c and no new act — the frame
 * crossing + its trail row live in serve.c/enclosure.c (6b), not here. net_send_frame puts a worker frame
 * on the wire; net_recv_frame delivers one received frame (non-blocking poll, re-posting the buffer). The
 * self-check is re-expressed on this same API so 6a's behaviour is byte-identical (its serial unchanged).
 *
 * THE PROVER IS THE WIRE (STOP-condition d). SLIRP is not our code; under PLANT_NET_TX_DEAD the driver
 * genuinely puts no frame on the wire (net_send_frame does not publish/kick), so the gateway has nothing to
 * answer, the receive poll times out, and WIRE-ROUNDTRIP reds by a REAL mechanism (no frame -> no reply),
 * never a flag toggling a verdict.
 *
 * WHY STATIC IDENTITY-MAPPED DMA MEMORY. The body sits at 1 MiB and ends well beneath the canonical base
 * (0x400000), and the supervisor identity map is kept for [0, CANONICAL_BASE); so a static, page-aligned
 * region has virt == phys and is reachable by both the CPU and the device with no page-table work. The
 * driver ASSERTS each region is below the canonical base (phys_of): if the body ever grew past it, the
 * bring-up reds rather than handing the device an address it cannot reach — a check that can fail.
 */
#include "body.h"
#include "enclosure.h"   /* net_nic_bringup / net_send_frame / net_recv_frame prototypes (6b) */

/* ── Port I/O (each body unit keeps its own inline, matching serial.c/ata.c/idt.c/clock.c) ───────── */
static inline void outb(uint16_t port, uint8_t v)  { __asm__ volatile("outb %0, %1" : : "a"(v), "Nd"(port)); }
static inline uint8_t inb(uint16_t port)           { uint8_t r; __asm__ volatile("inb %1, %0" : "=a"(r) : "Nd"(port)); return r; }
static inline void outw(uint16_t port, uint16_t v) { __asm__ volatile("outw %0, %1" : : "a"(v), "Nd"(port)); }
static inline uint16_t inw(uint16_t port)          { uint16_t r; __asm__ volatile("inw %1, %0" : "=a"(r) : "Nd"(port)); return r; }
static inline void outl(uint16_t port, uint32_t v) { __asm__ volatile("outl %0, %1" : : "a"(v), "Nd"(port)); }
static inline uint32_t inl(uint16_t port)          { uint32_t r; __asm__ volatile("inl %1, %0" : "=a"(r) : "Nd"(port)); return r; }

/* A monotonic time source for the BOUNDED receive poll — read directly from the CPU, so it is
 * independent of the clock slice (net runs whether or not clock did). A dead wire times out; it never
 * hangs. */
static inline uint64_t net_rdtsc(void) {
    uint32_t lo, hi;
    __asm__ volatile("rdtsc" : "=a"(lo), "=d"(hi));
    return ((uint64_t)hi << 32) | lo;
}

/* A compiler barrier: the ring index/flag writes must reach memory before the device is notified, and
 * the used-ring read must not be hoisted. On x86 (TSO) a compiler barrier is the ordering we need. */
#define BARRIER() __asm__ volatile("" ::: "memory")

/* ── PCI configuration space, the 0xCF8/0xCFC mechanism ──────────────────────────────────────────── */
#define PCI_CONFIG_ADDR 0xCF8
#define PCI_CONFIG_DATA 0xCFC

static uint32_t pci_cfg_read32(uint8_t bus, uint8_t dev, uint8_t func, uint8_t off) {
    uint32_t addr = (1u << 31) | ((uint32_t)bus << 16) | ((uint32_t)dev << 11)
                  | ((uint32_t)func << 8) | (off & 0xFCu);
    outl(PCI_CONFIG_ADDR, addr);
    return inl(PCI_CONFIG_DATA);
}
static uint16_t pci_cfg_read16(uint8_t bus, uint8_t dev, uint8_t func, uint8_t off) {
    return (uint16_t)(pci_cfg_read32(bus, dev, func, off) >> ((off & 2u) * 8));
}
static void pci_cfg_write16(uint8_t bus, uint8_t dev, uint8_t func, uint8_t off, uint16_t val) {
    uint32_t cur = pci_cfg_read32(bus, dev, func, off & 0xFCu);
    unsigned shift = (off & 2u) * 8;
    cur = (cur & ~(0xFFFFu << shift)) | ((uint32_t)val << shift);
    uint32_t addr = (1u << 31) | ((uint32_t)bus << 16) | ((uint32_t)dev << 11)
                  | ((uint32_t)func << 8) | (off & 0xFCu);
    outl(PCI_CONFIG_ADDR, addr);
    outl(PCI_CONFIG_DATA, cur);
}

#define PCI_VENDOR_ID   0x00
#define PCI_DEVICE_ID   0x02
#define PCI_COMMAND     0x04
#define PCI_BAR0        0x10
#define PCI_CMD_IO      0x0001   /* respond to I/O space accesses */
#define PCI_CMD_MASTER  0x0004   /* the device may act as a bus master (DMA) */

/* The (transitional) virtio-net device: Red Hat vendor, legacy device id, Ethernet class. mgr's
 * pre-flight (:4246) proved `-device virtio-net-pci` presents exactly this on the guest's qemu. */
#define VIRTIO_VENDOR       0x1AF4
#define VIRTIO_NET_DEVICE   0x1000   /* legacy / transitional virtio-net */

/* ── Legacy virtio-pci register offsets, from the I/O BAR base (no MSI-X, so device config at 0x14) ── */
#define VIRTIO_DEVICE_FEATURES  0x00   /* RO 32: features the device offers */
#define VIRTIO_DRIVER_FEATURES  0x04   /* WO 32: features the driver accepts */
#define VIRTIO_QUEUE_PFN        0x08   /* RW 32: the queue's physical page-frame number */
#define VIRTIO_QUEUE_SIZE       0x0C   /* RO 16: the device-set size of the selected queue */
#define VIRTIO_QUEUE_SELECT     0x0E   /* WO 16: select the queue the size/PFN registers act on */
#define VIRTIO_QUEUE_NOTIFY     0x10   /* WO 16: tell the device this queue has new available buffers */
#define VIRTIO_DEVICE_STATUS    0x12   /* RW  8: the device-status handshake byte */
#define VIRTIO_ISR_STATUS       0x13   /* RO  8: reading it acknowledges/deasserts the device interrupt */
#define VIRTIO_NET_CFG_MAC      0x14   /* device-specific config: mac[6] (MSI-X disabled) */

#define VIRTIO_STATUS_ACKNOWLEDGE  1
#define VIRTIO_STATUS_DRIVER       2
#define VIRTIO_STATUS_DRIVER_OK    4
#define VIRTIO_STATUS_FAILED    0x80

#define VIRTIO_NET_F_MAC   5   /* the device offers a MAC in its config — the only feature we accept */

/* ── The split virtqueue (legacy layout: desc | avail | pad-to-page | used) ──────────────────────── */
#define QSZ 256                       /* the size a legacy virtio-net queue reports; we assert it */
#define PAGE 4096u
#define QALIGN(x) (((x) + (PAGE - 1)) & ~(PAGE - 1))

struct vq_desc {                      /* one descriptor */
    uint64_t addr;                    /* physical address of the buffer */
    uint32_t len;                     /* buffer length */
    uint16_t flags;                   /* VQ_DESC_F_* */
    uint16_t next;                    /* chain link (unused: single-descriptor buffers) */
} __attribute__((packed));
#define VQ_DESC_F_NEXT   1
#define VQ_DESC_F_WRITE  2            /* the buffer is device-WRITABLE (a receive buffer) */

struct vq_avail {                     /* the driver -> device ring */
    uint16_t flags;
    uint16_t idx;
    uint16_t ring[QSZ];
    uint16_t used_event;              /* present in the ABI; used only with EVENT_IDX (not negotiated) */
} __attribute__((packed));
#define VQ_AVAIL_F_NO_INTERRUPT 1    /* the device need not interrupt us — we poll */

struct vq_used_elem { uint32_t id; uint32_t len; } __attribute__((packed));
struct vq_used {                      /* the device -> driver ring */
    uint16_t flags;
    uint16_t idx;
    struct vq_used_elem ring[QSZ];
    uint16_t avail_event;
} __attribute__((packed));

/* Each queue's memory is ONE static, page-aligned, 3-page region (desc = page 0, avail in page 1, used
 * page-aligned at page 2 — the legacy layout for QSZ=256). Static + page-aligned => virt == phys in the
 * identity-mapped low range, so the physical PFN the device wants is just (address >> 12). */
#define VQ_BYTES (3u * PAGE)
static uint8_t g_rxq[VQ_BYTES] __attribute__((aligned(PAGE)));
static uint8_t g_txq[VQ_BYTES] __attribute__((aligned(PAGE)));

/* Receive buffers (device-writable): the device writes a virtio_net_hdr then the frame. Static, so their
 * physical addresses are their own. Sixteen buffers, re-posted as consumed, sustains a short connection. */
#define RX_COUNT 16
#define RX_BUF   2048
static uint8_t g_rx_bufs[RX_COUNT][RX_BUF] __attribute__((aligned(PAGE)));

/* Transmit buffers: a virtio_net_hdr (zeroed) followed by the frame. A small ring reused round-robin;
 * the device consumes them well before we wrap for a short connection (used entries reclaimed lazily). */
#define TX_COUNT 16
static uint8_t g_tx_bufs[TX_COUNT][RX_BUF] __attribute__((aligned(PAGE)));

#define VIRTIO_NET_HDR_LEN 10        /* legacy, no MRG_RXBUF: {flags,gso_type,hdr_len,gso_size,csum_start,csum_offset} */

/* The addresses SLIRP hands a guest: our IP is the conventional 10.0.2.15, the gateway is 10.0.2.2. */
static const uint8_t OUR_IP[4] = {10, 0, 2, 15};
static const uint8_t GW_IP[4]  = {10, 0, 2, 2};

/* ── The device state (file-static), shared by the self-check and the callable frame API. ─────────── */
static int      g_net_up;                     /* the device is negotiated and both rings are live       */
static uint16_t g_iobase;                      /* the I/O BAR base                                       */
static uint8_t  g_dev;                         /* the PCI slot                                           */
static uint8_t  g_our_mac[6];                   /* the MAC the device offers                              */
static struct vq_desc  *g_rxd, *g_txd;
static struct vq_avail *g_rxa, *g_txa;
static struct vq_used  *g_rxu, *g_txu;
static uint16_t g_rx_seen;                      /* the next RX used-ring slot to consume                  */
static uint16_t g_rx_avail;                     /* the RX avail idx we have published                     */
static uint16_t g_tx_next;                      /* the next TX descriptor/avail slot to use               */
static uint16_t g_tx_pub;                       /* the TX avail idx we have published                     */

/* phys_of: a static buffer's physical address IS its virtual address (identity map, low range). The
 * driver hands the device a physical address, so this must hold — assert it, so a body that outgrew the
 * canonical base reds the bring-up instead of feeding the device an unreachable address (a real guard). */
static uint64_t phys_of(const void *p, int *ok) {
    uint64_t a = (uint64_t)(uintptr_t)p;
    if (a >= CANONICAL_BASE) { *ok = 0; }   /* above the identity-mapped range: virt != phys */
    return a;
}

static void put_mac(const uint8_t *m) {
    static const char h[] = "0123456789abcdef";
    for (int i = 0; i < 6; i++) {
        if (i) { serial_putc(':'); }
        serial_putc(h[(m[i] >> 4) & 0xF]);
        serial_putc(h[m[i] & 0xF]);
    }
}

static int mac_eq(const uint8_t *a, const uint8_t *b) {
    for (int i = 0; i < 6; i++) { if (a[i] != b[i]) { return 0; } }
    return 1;
}

/* Find the virtio-net device on PCI bus 0 (function 0 of each slot). Returns 1 and sets *dev when found. */
static int pci_find_virtio_net(uint8_t *dev_out) {
    for (uint8_t dev = 0; dev < 32; dev++) {
        uint16_t vendor = pci_cfg_read16(0, dev, 0, PCI_VENDOR_ID);
        if (vendor != VIRTIO_VENDOR) { continue; }
        uint16_t device = pci_cfg_read16(0, dev, 0, PCI_DEVICE_ID);
        if (device == VIRTIO_NET_DEVICE) { *dev_out = dev; return 1; }
    }
    return 0;
}

/* Configure one split virtqueue: select it, confirm the device's size, zero the region, publish the PFN,
 * and hand back the desc/avail/used pointers within the region. Returns 0 on success. */
static int vq_setup(uint16_t iobase, uint16_t index, uint8_t *region,
                    struct vq_desc **desc, struct vq_avail **avail, struct vq_used **used) {
    outw(iobase + VIRTIO_QUEUE_SELECT, index);
    uint16_t qsz = inw(iobase + VIRTIO_QUEUE_SIZE);
    if (qsz == 0 || qsz > QSZ) { return -1; }   /* the device asks for a size we did not size for */

    for (unsigned i = 0; i < VQ_BYTES; i++) { region[i] = 0; }
    *desc  = (struct vq_desc  *)(region + 0);
    *avail = (struct vq_avail *)(region + 16u * qsz);
    *used  = (struct vq_used  *)(region + QALIGN(16u * qsz + 6u + 2u * qsz));

    int ok = 1;
    uint64_t phys = phys_of(region, &ok);
    if (!ok) { return -1; }
    outw(iobase + VIRTIO_QUEUE_SELECT, index);
    outl(iobase + VIRTIO_QUEUE_PFN, (uint32_t)(phys / PAGE));
    return 0;
}

/* ── C7 P3b-6a/6b — THE NIC BRING-UP (callable). Full legacy virtio handshake: reset, ACKNOWLEDGE,
 * DRIVER, feature negotiation (accept only VIRTIO_NET_F_MAC), the RX+TX virtqueues, post the receive
 * buffers, DRIVER_OK. Fills the file-static device state and reads the offered MAC into *mac_out.
 * Returns 0 (up), 1 (device present, bring-up failed), 2 (no virtio-net device attached). Idempotent:
 * a full reset each call, so both the self-check and the enclosure driver get a clean device. */
int net_nic_bringup(uint8_t mac_out[6]) {
    g_net_up = 0;
    g_rx_seen = 0; g_rx_avail = 0; g_tx_next = 0; g_tx_pub = 0;

    if (!pci_find_virtio_net(&g_dev)) { return 2; }

    /* Enable I/O space + bus-master DMA, and read the I/O BAR base. */
    uint16_t cmd = pci_cfg_read16(0, g_dev, 0, PCI_COMMAND);
    pci_cfg_write16(0, g_dev, 0, PCI_COMMAND, cmd | PCI_CMD_IO | PCI_CMD_MASTER);
    uint32_t bar0 = pci_cfg_read32(0, g_dev, 0, PCI_BAR0);
    g_iobase = (uint16_t)(bar0 & ~0x3u);   /* bit 0 flags an I/O BAR; mask the low bits */

    /* Legacy device handshake: reset, then ACKNOWLEDGE + DRIVER. */
    outb(g_iobase + VIRTIO_DEVICE_STATUS, 0);
    outb(g_iobase + VIRTIO_DEVICE_STATUS, VIRTIO_STATUS_ACKNOWLEDGE);
    outb(g_iobase + VIRTIO_DEVICE_STATUS, VIRTIO_STATUS_ACKNOWLEDGE | VIRTIO_STATUS_DRIVER);

    /* Feature negotiation: accept ONLY VIRTIO_NET_F_MAC (so the device serves its MAC in config). */
    uint32_t features = inl(g_iobase + VIRTIO_DEVICE_FEATURES);
    uint32_t accept = features & (1u << VIRTIO_NET_F_MAC);
    outl(g_iobase + VIRTIO_DRIVER_FEATURES, accept);
    int have_mac_feature = (accept & (1u << VIRTIO_NET_F_MAC)) != 0;

    /* Bring up the receive queue (0) and the transmit queue (1). */
    int q_ok = (vq_setup(g_iobase, 0, g_rxq, &g_rxd, &g_rxa, &g_rxu) == 0)
             && (vq_setup(g_iobase, 1, g_txq, &g_txd, &g_txa, &g_txu) == 0);

    /* The MAC the device offers (config at 0x14 when MSI-X is disabled). */
    for (int i = 0; i < 6; i++) { g_our_mac[i] = inb(g_iobase + VIRTIO_NET_CFG_MAC + i); }
    int mac_ok = have_mac_feature;
    { int any = 0; for (int i = 0; i < 6; i++) { if (g_our_mac[i]) { any = 1; } } if (!any) { mac_ok = 0; } }

    /* Post the receive buffers into the RX descriptors and make them available. */
    int fill_ok = q_ok;
    if (q_ok) {
        g_rxa->flags = VQ_AVAIL_F_NO_INTERRUPT;
        g_txa->flags = VQ_AVAIL_F_NO_INTERRUPT;
        for (int i = 0; i < RX_COUNT; i++) {
            int ok = 1;
            g_rxd[i].addr = phys_of(g_rx_bufs[i], &ok);
            g_rxd[i].len = RX_BUF;
            g_rxd[i].flags = VQ_DESC_F_WRITE;   /* device-writable: it deposits a received frame here */
            g_rxd[i].next = 0;
            g_rxa->ring[i] = (uint16_t)i;
            if (!ok) { fill_ok = 0; }
        }
        BARRIER();
        g_rxa->idx = RX_COUNT;
        g_rx_avail = RX_COUNT;
    }

    if (mac_out) { for (int i = 0; i < 6; i++) { mac_out[i] = g_our_mac[i]; } }

    if (!(q_ok && mac_ok && fill_ok)) { return 1; }

    /* DRIVER_OK: the device is live. Tell it the receive buffers are ready. */
    outb(g_iobase + VIRTIO_DEVICE_STATUS,
         VIRTIO_STATUS_ACKNOWLEDGE | VIRTIO_STATUS_DRIVER | VIRTIO_STATUS_DRIVER_OK);
    BARRIER();
    outw(g_iobase + VIRTIO_QUEUE_NOTIFY, 0);    /* the receive queue has available buffers */
    g_net_up = 1;
    return 0;
}

/* ── C7 P3b-6b — PUT ONE FRAME ON THE WIRE (callable). Copies the caller's Ethernet frame after a zeroed
 * virtio_net_hdr into a transmit buffer, publishes it and kicks the transmit queue. Returns 0 on success,
 * -1 if the device is not up, the frame is too large, or the buffer is unreachable. Under PLANT_NET_TX_DEAD
 * the frame is staged but NOT published/kicked — no frame leaves the NIC (the 6a wire-round-trip reds by a
 * real mechanism, no frame -> no reply). NO served shape and no trail row here — those are serve.c's (6b). */
int net_send_frame(const void *frame, uint32_t len) {
    if (!g_net_up || frame == 0) { return -1; }
    if (len == 0 || len > RX_BUF - VIRTIO_NET_HDR_LEN) { return -1; }

    /* reclaim any completed TX descriptors (the device returns them on the used ring). */
    BARRIER();
    /* (no per-descriptor bookkeeping needed beyond wrap: the used ring drains on its own) */

    uint16_t slot = (uint16_t)(g_tx_next % TX_COUNT);
    uint8_t *buf = g_tx_bufs[slot];
    for (int i = 0; i < VIRTIO_NET_HDR_LEN; i++) { buf[i] = 0; }   /* virtio_net_hdr: no offload */
    const uint8_t *src = (const uint8_t *)frame;
    for (uint32_t i = 0; i < len; i++) { buf[VIRTIO_NET_HDR_LEN + i] = src[i]; }

    int ok = 1;
    g_txd[slot].addr = phys_of(buf, &ok);
    g_txd[slot].len = VIRTIO_NET_HDR_LEN + len;
    g_txd[slot].flags = 0;                          /* device-READABLE: the frame we send */
    g_txd[slot].next = 0;
    if (!ok) { return -1; }
    g_txa->ring[g_tx_pub % QSZ] = slot;
    g_tx_next++;

#ifndef PLANT_NET_TX_DEAD
    BARRIER();
    g_tx_pub++;
    g_txa->idx = g_tx_pub;
    BARRIER();
    outw(g_iobase + VIRTIO_QUEUE_NOTIFY, 1);
#else
    /* PLANT_NET_TX_DEAD (6a A2 near-miss): do NOT publish or kick — no frame leaves the NIC. */
    (void)0;
#endif
    return 0;
}

/* ── C7 P3b-6b — DELIVER ONE RECEIVED FRAME (callable, non-blocking). Polls the receive used ring; if a
 * frame is present, copies it (past the legacy virtio_net_hdr) into `out` (up to `max`), re-posts the
 * buffer to the device, and returns the frame length. Returns 0 if no frame is waiting, -1 if the device
 * is not up. NO served shape and no trail row here — those are serve.c's (6b). */
int net_recv_frame(void *out, uint32_t max) {
    if (!g_net_up || out == 0) { return -1; }
    BARRIER();
    uint16_t used_idx = *(volatile uint16_t *)&g_rxu->idx;
    if (g_rx_seen == used_idx) { return 0; }

    struct vq_used_elem e = g_rxu->ring[g_rx_seen % QSZ];
    uint32_t id = e.id % RX_COUNT;
    const uint8_t *buf = g_rx_bufs[id];
    uint32_t total = e.len;
    uint32_t flen = 0;
    if (total > VIRTIO_NET_HDR_LEN) {
        flen = total - VIRTIO_NET_HDR_LEN;
        if (flen > max) { flen = max; }
        const uint8_t *frame = buf + VIRTIO_NET_HDR_LEN;
        uint8_t *o = (uint8_t *)out;
        for (uint32_t i = 0; i < flen; i++) { o[i] = frame[i]; }
    }
    g_rx_seen++;

    /* re-post this receive buffer to the device (device-writable) so the ring keeps draining. */
    g_rxd[id].addr = (uint64_t)(uintptr_t)buf;
    g_rxd[id].len = RX_BUF;
    g_rxd[id].flags = VQ_DESC_F_WRITE;
    g_rxd[id].next = 0;
    g_rxa->ring[g_rx_avail % QSZ] = (uint16_t)id;
    BARRIER();
    g_rx_avail++;
    g_rxa->idx = g_rx_avail;
    BARRIER();
    outw(g_iobase + VIRTIO_QUEUE_NOTIFY, 0);
    return (int)flen;
}

/* Build the ARP request frame (Ethernet + ARP, all multi-byte fields big-endian) into `out` AFTER no
 * virtio_net_hdr (net_send_frame adds it). Returns the frame length. */
static uint32_t build_arp_request(uint8_t *out, const uint8_t *our_mac) {
    uint8_t *eth = out;
    for (int i = 0; i < 6; i++) { eth[i] = 0xFF; }               /* dst: broadcast */
    for (int i = 0; i < 6; i++) { eth[6 + i] = our_mac[i]; }     /* src: us */
    eth[12] = 0x08; eth[13] = 0x06;                              /* ethertype: ARP */

    uint8_t *arp = eth + 14;
    arp[0] = 0x00; arp[1] = 0x01;                                /* htype: Ethernet */
    arp[2] = 0x08; arp[3] = 0x00;                                /* ptype: IPv4 */
    arp[4] = 6;    arp[5] = 4;                                   /* hlen, plen */
    arp[6] = 0x00; arp[7] = 0x01;                                /* oper: request */
    for (int i = 0; i < 6; i++) { arp[8 + i] = our_mac[i]; }     /* sender hardware addr */
    for (int i = 0; i < 4; i++) { arp[14 + i] = OUR_IP[i]; }     /* sender protocol addr */
    for (int i = 0; i < 6; i++) { arp[18 + i] = 0x00; }          /* target hardware addr: unknown */
    for (int i = 0; i < 4; i++) { arp[24 + i] = GW_IP[i]; }      /* target protocol addr: the gateway */
    return 14 + 28;                                              /* 42 */
}

/* Is `frame` (Ethernet, length `len`) an ARP REPLY for the gateway 10.0.2.2? If so, copy the sender
 * hardware address (the gateway's MAC) into gw_mac and return 1. A REQUEST we never receive; a reply for
 * 10.0.2.2 can only have been generated by the outside party that answered us. */
static int is_gateway_arp_reply(const uint8_t *frame, uint32_t len, uint8_t *gw_mac) {
    if (len < 14 + 28) { return 0; }
    if (!(frame[12] == 0x08 && frame[13] == 0x06)) { return 0; }   /* ethertype ARP */
    const uint8_t *arp = frame + 14;
    if (!(arp[0] == 0x00 && arp[1] == 0x01)) { return 0; }         /* htype Ethernet */
    if (!(arp[2] == 0x08 && arp[3] == 0x00)) { return 0; }         /* ptype IPv4 */
    if (!(arp[6] == 0x00 && arp[7] == 0x02)) { return 0; }         /* oper REPLY */
    for (int i = 0; i < 4; i++) { if (arp[14 + i] != GW_IP[i]) { return 0; } }  /* sender IP == gateway */
    for (int i = 0; i < 6; i++) { gw_mac[i] = arp[8 + i]; }        /* sender hardware addr == gw_mac */
    return 1;
}

/* THE RING-0 WIRE SELF-CHECK (C7 P3b-6a). Returns 0 (round trip proven), 1 (device present, round trip
 * failed), 2 (no virtio-net device attached — skip). Re-expressed on the callable frame API; its serial
 * output and behaviour are byte-identical to before (6a stays green). */
int net_wire_selfcheck(void) {
    uint8_t our_mac[6];
    int st = net_nic_bringup(our_mac);
    if (st == 2) {
        serial_puts("NET: ABSENT (no virtio-net device; the wire round trip is skipped)\n");
        return 2;
    }
    serial_puts("NET: virtio-net at pci 0:"); serial_puthex32(g_dev);
    serial_puts(" iobase=0x"); serial_puthex32(g_iobase); serial_puts("\n");

    int bringup = (st == 0);
    serial_puts(bringup ? "CHECK NIC-BRINGUP: PASS\n" : "CHECK NIC-BRINGUP: FAIL\n");
    if (bringup) { serial_puts("OUR-MAC: "); put_mac(our_mac); serial_puts("\n"); }

    /* The wire round trip — attempted only once the device and both rings are up. */
    uint8_t gw_mac[6] = {0};
    int got_reply = 0;
    if (bringup) {
        uint8_t arp[64];
        uint32_t tx_len = build_arp_request(arp, our_mac);
        net_send_frame(arp, tx_len);   /* under PLANT_NET_TX_DEAD this stages but does not kick */

        uint8_t rx[RX_BUF];
        uint64_t start = net_rdtsc();
        while (!got_reply) {
            int n = net_recv_frame(rx, sizeof(rx));
            if (n > 0) {
                if (is_gateway_arp_reply(rx, (uint32_t)n, gw_mac)) { got_reply = 1; }
            } else if (n == 0) {
                if (net_rdtsc() - start > 8000000000ull) { break; }   /* ~a few seconds of TSC; then FAIL */
            } else {
                break;
            }
        }
        (void)inb(g_iobase + VIRTIO_ISR_STATUS);   /* deassert any pending device interrupt (we polled) */
    }

    /* The reply's sender hardware address must be the GATEWAY's, not our own — proof it came off the wire
     * and is not our own bytes echoed back. */
    int roundtrip = got_reply && !mac_eq(gw_mac, our_mac);
    serial_puts(roundtrip ? "CHECK WIRE-ROUNDTRIP: PASS\n" : "CHECK WIRE-ROUNDTRIP: FAIL\n");
    if (got_reply) { serial_puts("GW-MAC: "); put_mac(gw_mac); serial_puts("\n"); }

    int all = bringup && roundtrip;
    serial_puts(all ? "NET: PASS\n" : "NET: FAIL\n");
    return all ? 0 : 1;
}
