/* gov-os C7 P3b-6c slice (iii) — the SOCKET-ACT worker's glue (design/54 §5 L18/L19/I3; §7 P3b-6c slice iii).
 *
 * CONFIGURATION ONLY. Compiled with the UNMODIFIED lwIP 2.2.0 core (the same byte-for-byte source the 6b
 * worker links, I3) into a static NO_SYS worker. UNLIKE the 6b worker (which SELF-DRIVES lwiperf's own
 * client loop and only pumps frames), this worker is a PERSISTENT OP-SERVER: the ring-0 coroutine bridge
 * relays ONE socket-family op at a time (socket / ioctl(FIONBIO) / connect / getsockopt(SO_ERROR) / poll /
 * sendto / recvfrom / close) into a shared page in THIS enclosure's own map; the worker performs each op on
 * its PERSISTENT lwIP raw-API connection state (a tcp_pcb that lives across relays), pumps 6a's NIC to make
 * real progress on the wire, writes the op's answer + a WITNESS, and YIELDS (REQ_YIELD) back to the bridge.
 * The connection is opened, exchanged and closed by the STACK'S OWN raw TCP API driving OUR NIC — never a
 * fabricated reply (L19): a canned answer (the bridge skipping the worker) leaves the witness absent and
 * reds; a shape planted to fail reds by a REAL mechanism (no SYN on the wire, a starved heap, a dropped
 * frame). The lwIP core is byte-unmodified; our glue only configures + relays.
 *
 * This is a test fixture (content), NEVER an attested member; the built worker IMAGE is content, never a
 * signed member (§9 mechanism 3 / I3). Guest-only; every boot is the nested qemu inside the pinned guest.
 */
#include "lwip/init.h"
#include "lwip/netif.h"
#include "lwip/etharp.h"
#include "lwip/timeouts.h"
#include "lwip/ip4_addr.h"
#include "lwip/tcp.h"
#include "netif/ethernet.h"

#include <stdint.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <stdlib.h>

/* ── the body request numbers this worker crosses on (served ONLY to the lwIP enclosure, serve.c) ──── */
#define REQ_SEND_FRAME 0x60000001UL
#define REQ_RECV_FRAME 0x60000002UL
#define REQ_WAIT       0x60000003UL
#define REQ_YIELD      0x60000004UL   /* hand control back to the bridge; returns with the next relayed op */

static inline long body_call3(long n, long a, long b, long c) {
    long r;
    __asm__ volatile("syscall" : "=a"(r) : "a"(n), "D"(a), "S"(b), "d"(c) : "rcx", "r11", "memory");
    return r;
}

/* ── the shared relay page: a fixed USER VA the body maps into THIS enclosure's map (slice i, private half).
 * The body writes op+args+in-buffer before resuming the worker; the worker writes answer+witness+out-buffer
 * before yielding. ──────────────────────────────────────────────────────────────────────────────────── */
#define BRIDGE_SHARED_VA      0x20000000UL
#define SOCK_WITNESS_MAGIC    0x6c77495057334bULL   /* "lwIPP3K" — the worker reached the op (executed) */
#define SOCK_BUF_MAX          2048

/* the socket ops the bridge relays (slot->op) — one per measured socket-family shape. */
#define SOP_SOCKET    1UL   /* create a tcp_pcb; answer = the socket handle (fd), or -errno            */
#define SOP_IOCTL_NB  2UL   /* ioctl(FIONBIO,[1]): mark the connection non-blocking; answer 0          */
#define SOP_CONNECT   3UL   /* connect(sockaddr_in in buf): tcp_connect; answer 0 / -EINPROGRESS       */
#define SOP_GETSOERR  4UL   /* getsockopt(SO_ERROR): answer the connection error (0 == connected)      */
#define SOP_POLL      5UL   /* poll(events=a1): pump; answer the revents (POLLOUT|POLLIN|POLLERR)      */
#define SOP_SEND      6UL   /* sendto(buf,buflen): tcp_write+output; answer the bytes accepted         */
#define SOP_RECV      7UL   /* recvfrom(a1=max): pump; answer the bytes delivered into buf             */
#define SOP_CLOSE     8UL   /* close(): tcp_close; answer 0                                            */

/* poll revents (Linux values — the interpreter reads these back into its poll result). */
#define POLLIN_   0x001
#define POLLOUT_  0x004
#define POLLERR_  0x008
#define POLLHUP_  0x010

/* -errno answers, in the interpreter's raw-syscall band [-4095,-1]. */
#define EINPROGRESS_ (-115L)

struct sock_slot {
    volatile uint64_t op;         /* body -> worker: the relayed op                                  */
    volatile uint64_t a0, a1, a2; /* body -> worker: the op's scalar args (flags, max, events)        */
    volatile uint64_t answer;     /* worker -> body: the op's answer                                 */
    volatile uint64_t witness;    /* worker -> body: SOCK_WITNESS_MAGIC iff the worker executed       */
    volatile uint64_t buflen;     /* both ways: bytes in buf (sockaddr in / send data / recv data)   */
    volatile uint8_t  buf[SOCK_BUF_MAX];
};

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

u32_t sys_now(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (u32_t)((uint64_t)ts.tv_sec * 1000u + (uint64_t)ts.tv_nsec / 1000000u);
}

/* one pump step: drain RX into the stack, run the stack's timers (which drive TCP send/retransmit/poll),
 * a short bounded wait. Returns the number of frames drained. */
static int pump_once(void) {
    int drained = 0;
    while (pump_input(&g_netif)) { drained++; }
    sys_check_timeouts();
    body_call3((long)REQ_WAIT, 2000000L /*2 ms*/, 0, 0);
    return drained;
}

/* ── the persistent connection state (lives across relays) ─────────────────────────────────────────── */
static struct tcp_pcb *g_pcb;
static volatile int g_connected;        /* the connected_cb fired */
static volatile int g_conn_err;         /* an lwIP err_t on failure (0 == none) */
static volatile int g_peer_fin;         /* the peer closed (recv_cb NULL pbuf) */
static uint8_t  g_rx[4096];             /* received bytes not yet handed up */
static volatile uint32_t g_rxlen;

/* ── serial witness (fd 2 -> serve.c routes SYS_write to the serial line, so the worker's execution is
 * witnessed on the boot serial too). ─────────────────────────────────────────────────────────────── */
static void w2(const void *b, unsigned long n) { ssize_t r = write(2, b, n); (void)r; }
static void say(const char *s) { w2(s, (unsigned long)strlen(s)); }
static void sayhex(const char *lbl, uint64_t v) {
    char b[96]; unsigned i = 0;
    while (lbl[i]) { b[i] = lbl[i]; i++; }
    b[i++] = '0'; b[i++] = 'x';
    for (int s = 60; s >= 0; s -= 4) { unsigned d = (unsigned)((v >> s) & 0xF); b[i++] = (char)(d < 10 ? '0' + d : 'a' + d - 10); }
    b[i++] = '\n';
    w2(b, i);
}

/* ── the lwIP raw-API callbacks (the stack's own; our glue only records) ───────────────────────────── */
static err_t connected_cb(void *arg, struct tcp_pcb *tpcb, err_t err) {
    (void)arg; (void)tpcb;
    if (err == ERR_OK) { g_connected = 1; } else { g_conn_err = (int)err; }
    return ERR_OK;
}
static err_t recv_cb(void *arg, struct tcp_pcb *tpcb, struct pbuf *p, err_t err) {
    (void)arg;
    if (p == NULL) { g_peer_fin = 1; return ERR_OK; }        /* the peer's FIN */
    if (err != ERR_OK) { if (p) pbuf_free(p); return err; }
    uint16_t off = 0;
    for (struct pbuf *q = p; q != NULL; q = q->next) {
        uint16_t c = q->len;
        if (g_rxlen + c > sizeof(g_rx)) { c = (uint16_t)(sizeof(g_rx) - g_rxlen); }
        if (c) { memcpy(g_rx + g_rxlen, q->payload, c); g_rxlen += c; off += c; }
    }
    tcp_recved(tpcb, off);
    pbuf_free(p);
    return ERR_OK;
}
static void err_cb(void *arg, err_t err) { (void)arg; g_conn_err = (int)err; g_pcb = NULL; }

/* ── the op handlers (one per relayed socket-family shape) ─────────────────────────────────────────── */
static uint64_t do_socket(void) {
    g_pcb = tcp_new_ip_type(IPADDR_TYPE_V4);
    if (g_pcb == NULL) { return (uint64_t)(-105L) /*-ENOBUFS*/; }
    tcp_arg(g_pcb, NULL);
    tcp_recv(g_pcb, recv_cb);
    tcp_err(g_pcb, err_cb);
    return 500;  /* a high socket handle (clear of the interpreter's real fds) — used for connect/send/…/close */
}

static uint64_t do_connect(volatile struct sock_slot *slot) {
    if (g_pcb == NULL) { return (uint64_t)(-9L) /*-EBADF*/; }
    /* the interpreter's sockaddr_in (16 bytes): family(2) port(2, net order) addr(4) zero(8). */
    if (slot->buflen < 8) { return (uint64_t)(-22L) /*-EINVAL*/; }
    uint16_t port = (uint16_t)((slot->buf[2] << 8) | slot->buf[3]);
    ip4_addr_t remote;
    IP4_ADDR(&remote, slot->buf[4], slot->buf[5], slot->buf[6], slot->buf[7]);
    g_connected = 0; g_conn_err = 0;
    err_t e = tcp_connect(g_pcb, &remote, port, connected_cb);
    if (e != ERR_OK) { return (uint64_t)(-115L); }
    /* pump the SYN out and drive the handshake. Bounded: a dead wire returns, never hangs. */
    for (int i = 0; i < 400 && !g_connected && g_conn_err == 0; i++) { pump_once(); }
    if (g_connected) { return 0; }
    if (g_conn_err != 0) { return (uint64_t)(-111L) /*-ECONNREFUSED*/; }
    return (uint64_t)EINPROGRESS_;   /* still handshaking (a later poll/getsockopt completes it) */
}

static uint64_t do_getsoerr(void) {
    if (g_connected) { return 0; }
    if (g_conn_err != 0) { return (uint64_t)111UL /*ECONNREFUSED as SO_ERROR value*/; }
    return (uint64_t)115UL /*EINPROGRESS as SO_ERROR value*/;
}

static uint64_t do_poll(void) {
    pump_once();
    uint64_t re = 0;
    if (g_conn_err != 0) { re |= POLLERR_; }
    if (g_connected)     { re |= POLLOUT_; }
    if (g_rxlen > 0)     { re |= POLLIN_; }
    if (g_peer_fin)      { re |= POLLHUP_; }
    return re;
}

static uint64_t do_send(volatile struct sock_slot *slot) {
    if (g_pcb == NULL) { return (uint64_t)(-9L); }
    uint32_t n = (uint32_t)slot->buflen;
    if (n > SOCK_BUF_MAX) { n = SOCK_BUF_MAX; }
    static uint8_t sb[SOCK_BUF_MAX];
    for (uint32_t i = 0; i < n; i++) { sb[i] = slot->buf[i]; }
    err_t e = tcp_write(g_pcb, sb, (u16_t)n, TCP_WRITE_FLAG_COPY);
    if (e != ERR_OK) { return (uint64_t)(-105L) /*-ENOBUFS: the send buffer is full*/; }
    tcp_output(g_pcb);
    for (int i = 0; i < 40; i++) { pump_once(); }   /* let the data go out + acks come back */
    return n;
}

static uint64_t do_recv(volatile struct sock_slot *slot) {
    uint32_t max = (uint32_t)slot->a1;
    if (max > SOCK_BUF_MAX) { max = SOCK_BUF_MAX; }
    /* pump until data arrives, the peer closes, or a bounded budget elapses. */
    for (int i = 0; i < 400 && g_rxlen == 0 && !g_peer_fin && g_conn_err == 0; i++) { pump_once(); }
    uint32_t n = g_rxlen;
    if (n > max) { n = max; }
    for (uint32_t i = 0; i < n; i++) { slot->buf[i] = g_rx[i]; }
    slot->buflen = n;
    /* shift any remainder down (bounded connection, so this is the simple case). */
    if (n < g_rxlen) { memmove(g_rx, g_rx + n, g_rxlen - n); g_rxlen -= n; } else { g_rxlen = 0; }
    return n;   /* 0 == EOF/no-data-yet (a real recv returns 0 on a clean peer close) */
}

static uint64_t do_close(void) {
    if (g_pcb != NULL) {
        tcp_recv(g_pcb, NULL);
        err_t e = tcp_close(g_pcb);
        if (e != ERR_OK) { tcp_abort(g_pcb); }
        g_pcb = NULL;
        for (int i = 0; i < 40; i++) { pump_once(); }   /* let the FIN/RST go out */
    }
    return 0;
}

int main(void) {
    srand(sys_now() ^ 0x6b06);
    lwip_init();

    ip4_addr_t ip, mask, gw;
    IP4_ADDR(&ip,     10, 0, 2, 15);
    IP4_ADDR(&mask,  255, 255, 255, 0);
    IP4_ADDR(&gw,     10, 0, 2, 2);
    netif_add(&g_netif, &ip, &mask, &gw, NULL, my_netif_init, ethernet_input);
    netif_set_default(&g_netif);
    netif_set_up(&g_netif);
    netif_set_link_up(&g_netif);
    say("SOCKW-UP\n");

    volatile struct sock_slot *slot = (volatile struct sock_slot *)(uintptr_t)BRIDGE_SHARED_VA;

    /* THE OP-SERVER LOOP: perform the relayed op on the PERSISTENT connection, answer + witness, yield. The
     * first entry carries the first op (SOP_SOCKET) already in the slot; each yield returns with the next. */
    for (;;) {
        uint64_t op = slot->op;
        uint64_t ans;
        switch (op) {
            case SOP_SOCKET:   ans = do_socket();        break;
            case SOP_IOCTL_NB: ans = 0;                  break;   /* raw API is inherently non-blocking */
            case SOP_CONNECT:  ans = do_connect(slot);   break;
            case SOP_GETSOERR: ans = do_getsoerr();      break;
            case SOP_POLL:     ans = do_poll();          break;
            case SOP_SEND:     ans = do_send(slot);      break;
            case SOP_RECV:     ans = do_recv(slot);      break;
            case SOP_CLOSE:    ans = do_close();          break;
            default:           ans = (uint64_t)(-38L);   break;   /* -ENOSYS: an op we do not serve */
        }
        sayhex("SOCKW-OP=", op);
        sayhex("SOCKW-ANS=", ans);
        slot->answer  = ans;
        slot->witness = SOCK_WITNESS_MAGIC;
        body_call3((long)REQ_YIELD, 0, 0, 0);   /* hand back to the bridge; returns with the next op */
    }
    return 0;
}
