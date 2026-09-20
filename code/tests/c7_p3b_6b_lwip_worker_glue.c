/* gov-os C7 P3b-6b — the BORROWED TCP worker's glue (design/54 §7 P3b-6b; A6/L5/L19).
 *
 * CONFIGURATION ONLY. Compiled with the UNMODIFIED lwIP 2.2.0 core + the stack's OWN example
 * (src/apps/lwiperf/lwiperf.c, UNMODIFIED — the prover, L19) into a static NO_SYS worker. Our glue is:
 *   - two frame functions: netif_linkoutput -> a SEND_FRAME crossing; pump_input -> a RECV_FRAME crossing
 *   - PBUF_RAM receive (the pre-flight's named sidestep; a supported mode, configuration not modification)
 *   - sys_now over the clock crossing (clock_gettime); LWIP_RAND seeded from the clock
 * plus main(): lwip_init, netif_add (OUR NIC on 10.0.2.15/24, gateway 10.0.2.2), the stack's OWN default
 * client to 10.0.2.2:5001, a bounded pump loop, exit_group. The frame crossings are body request numbers
 * served ONLY to this enclosure (serve.c, L18); on Linux they ENOSYS, so the worker runs ONLY on the body.
 *
 * This is a test fixture (content), NEVER an attested member; the built worker IMAGE is content, never a
 * signed member (§9 mechanism 3 / I3). The lwiperf client is the stack's own program — we never fabricate
 * the reply (L19); a broken crossing makes the client fail by a real mechanism.
 */
#include "lwip/init.h"
#include "lwip/netif.h"
#include "lwip/etharp.h"
#include "lwip/timeouts.h"
#include "lwip/ip4_addr.h"
#include "netif/ethernet.h"
#include "lwip/apps/lwiperf.h"

#include <stdint.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <stdlib.h>

/* ── the body request numbers this worker crosses on (served ONLY to the lwIP enclosure, serve.c) ──── */
#define REQ_SEND_FRAME 0x60000001UL
#define REQ_RECV_FRAME 0x60000002UL
#define REQ_WAIT       0x60000003UL

static inline long body_call3(long n, long a, long b, long c) {
    long r;
    __asm__ volatile("syscall" : "=a"(r) : "a"(n), "D"(a), "S"(b), "d"(c) : "rcx", "r11", "memory");
    return r;
}

/* ── OUR NIC on the metal: a fixed link address (SLIRP learns whatever source MAC our frames carry). ── */
static const uint8_t OUR_MAC[6] = {0x52, 0x54, 0x00, 0x6b, 0x06, 0x0b};

static struct netif g_netif;

/* the two frame functions — the ONLY glue between the borrowed stack and 6a's NIC (A6). */
static err_t netif_linkoutput(struct netif *n, struct pbuf *p) {
    (void)n;
    static uint8_t txbuf[1600];
    uint16_t len = 0;
    for (struct pbuf *q = p; q != NULL; q = q->next) {
        if ((uint32_t)len + q->len > sizeof(txbuf)) { break; }
        memcpy(txbuf + len, q->payload, q->len);
        len += q->len;
    }
    body_call3((long)REQ_SEND_FRAME, (long)(uintptr_t)txbuf, (long)len, 0);
    return ERR_OK;
}

static err_t my_netif_init(struct netif *n) {
    n->name[0] = 'e'; n->name[1] = 'n';
    n->output = etharp_output;          /* IP -> ARP -> linkoutput (lwIP's own) */
    n->linkoutput = netif_linkoutput;   /* our frame-out crossing               */
    n->mtu = 1500;
    n->hwaddr_len = 6;
    memcpy(n->hwaddr, OUR_MAC, 6);
    n->flags = NETIF_FLAG_BROADCAST | NETIF_FLAG_ETHARP | NETIF_FLAG_LINK_UP;
    return ERR_OK;
}

/* deliver one received frame from 6a's NIC into the stack (PBUF_RAM). Returns 1 iff a frame was fed. */
static int pump_input(struct netif *n) {
    static uint8_t rxbuf[1600];
    long len = body_call3((long)REQ_RECV_FRAME, (long)(uintptr_t)rxbuf, (long)sizeof(rxbuf), 0);
    if (len <= 0) { return 0; }
    struct pbuf *p = pbuf_alloc(PBUF_RAW, (u16_t)len, PBUF_RAM);
    if (p == NULL) { return 0; }
    pbuf_take(p, rxbuf, (u16_t)len);
    if (n->input(p, n) != ERR_OK) { pbuf_free(p); }
    return 1;
}

/* the clock the stack reads (sys_now) and the seed for LWIP_RAND — both over the clock crossing. */
u32_t sys_now(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (u32_t)((uint64_t)ts.tv_sec * 1000u + (uint64_t)ts.tv_nsec / 1000000u);
}

/* the stack's OWN example is the prover; its report tells us the session finished (done or aborted). */
static volatile int g_report_fired;
static volatile int g_report_type = -1;
static volatile u32_t g_report_bytes;

static void report_cb(void *arg, enum lwiperf_report_type report_type,
                      const ip_addr_t *local_addr, u16_t local_port,
                      const ip_addr_t *remote_addr, u16_t remote_port,
                      u32_t bytes_transferred, u32_t ms_duration, u32_t bandwidth_kbitpsec) {
    (void)arg; (void)local_addr; (void)local_port; (void)remote_addr; (void)remote_port;
    (void)ms_duration; (void)bandwidth_kbitpsec;
    g_report_type = (int)report_type;
    g_report_bytes = bytes_transferred;
    g_report_fired = 1;
}

static void w2(const void *b, size_t n) { ssize_t r = write(2, b, n); (void)r; }
static void say(const char *s) { w2(s, strlen(s)); }
static void sayn(const char *s, unsigned long v) {
    char b[32]; int i = 0; w2(s, strlen(s));
    if (v == 0) { b[i++] = '0'; } else { char t[24]; int j = 0; while (v) { t[j++] = (char)('0' + v % 10); v /= 10; } while (j) { b[i++] = t[--j]; } }
    b[i++] = '\n'; w2(b, (size_t)i);
}

int main(void) {
#ifdef PLANT_LWIP_OVERREACH
    /* precision (a): a REAL request BEYOND the declared set — getpid (39) is not in the twenty. The body
     * refuses it BY NAME (native ENOSYS) and records a REFUSED row on the trail; the worker tolerates it
     * (glibc's own getpid caches nothing here) and continues. Demonstrates the gate refusing the real
     * worker, on the trail (never a flag). */
    long over = body_call3(39 /*getpid*/, 0, 0, 0);
    sayn("WORKER-OVERREACH-ANS=", (unsigned long)over);
#endif
    srand(sys_now() ^ 0x6b06);

    lwip_init();

    ip4_addr_t ip, mask, gw, remote;
    IP4_ADDR(&ip,     10, 0, 2, 15);
    IP4_ADDR(&mask,  255, 255, 255, 0);
    IP4_ADDR(&gw,     10, 0, 2, 2);
    IP4_ADDR(&remote, 10, 0, 2, 2);

    netif_add(&g_netif, &ip, &mask, &gw, NULL, my_netif_init, ethernet_input);
    netif_set_default(&g_netif);
    netif_set_up(&g_netif);
    netif_set_link_up(&g_netif);

    say("WORKER-UP\n");

    void *sess = lwiperf_start_tcp_client_default(&remote, report_cb, NULL);
    if (sess == NULL) { say("WORKER-CLIENT-START-FAIL\n"); _exit(1); }
    say("WORKER-CLIENT-STARTED\n");

    /* the bounded pump: drain RX into the stack, run its timers (which drive the client's send/poll), and
     * a short wait. Stop when the stack's OWN report fires — the session finished. The peer reads a bounded
     * amount then STOPS reading (window fills), so the client's own idle-poll timer ends the session
     * (ABORTED_LOCAL) with the pcb still valid; lwiperf is UNMODIFIED, our glue only pumps and reports. */
    unsigned long iters = 0, drained = 0;
    const unsigned long MAX_ITERS = 15000;   /* safety ceiling */
    while (!g_report_fired && iters < MAX_ITERS) {
        while (pump_input(&g_netif)) { drained++; }
        sys_check_timeouts();
        body_call3((long)REQ_WAIT, 2000000L /*2 ms*/, 0, 0);
        iters++;
    }

    sayn("WORKER-ITERS=", iters);
    sayn("WORKER-RX-DRAINED=", drained);
    sayn("WORKER-REPORT-TYPE=", (unsigned long)(long)g_report_type);
    sayn("WORKER-REPORT-BYTES=", (unsigned long)g_report_bytes);

    /* a real exchange occurred iff the stack's own session reported (established -> data -> teardown), by
     * a real remote party over our NIC. The report type is the stack's, not ours. */
    int ok = g_report_fired;
    say(ok ? "WORKER-DONE OK\n" : "WORKER-DONE NOCONN\n");
    _exit(ok ? 0 : 1);
    return 0;
}
