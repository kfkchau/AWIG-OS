/* gov-os C7 P3b-6b — lwipopts.h for the BORROWED TCP worker (design/54 §7 P3b-6b; A6).
 *
 * CONFIGURATION ONLY (A6 / L5 / L19): this file and the glue are OURS and named; the lwIP 2.2.0 SOURCE is
 * UNMODIFIED. Pinned to mgr's dispatch pre-flight (planning/evidence/C7-P3b-6b-PREFLIGHT/
 * DISPATCH-PREFLIGHT-MGR.md §2, the warning-clean static NO_SYS=1 recipe). NO_SYS=1, raw API only, the
 * receive path is PBUF_RAM (the pre-flight's named sidestep of the .so's PBUF_POOL element mismatch — a
 * supported mode, configuration, not modification). This is a test fixture (content), NEVER an attested
 * member.
 */
#ifndef LWIPOPTS_H
#define LWIPOPTS_H

#define NO_SYS 1
#define SYS_LIGHTWEIGHT_PROT 0
#define LWIP_NETCONN 0
#define LWIP_SOCKET 0
#define LWIP_TIMERS 1
#define MEM_LIBC_MALLOC 0
#define MEMP_MEM_MALLOC 1
#define MEM_ALIGNMENT 4
#define MEM_SIZE (48 * 1024)
#define LWIP_ARP 1
#define LWIP_ETHERNET 1
#define LWIP_IPV4 1
#define LWIP_IPV6 0
#define LWIP_ICMP 1
#define LWIP_RAW 0
#define LWIP_DHCP 0
#define LWIP_AUTOIP 0
#define LWIP_DNS 0
#define LWIP_UDP 1
#define LWIP_TCP 1
#define TCP_MSS 1460
#define TCP_WND (4 * TCP_MSS)
#define TCP_SND_BUF (4 * TCP_MSS)
#define MEMP_NUM_TCP_PCB 5
#define MEMP_NUM_TCP_SEG 16
#define PBUF_POOL_SIZE 8
#define PBUF_POOL_BUFSIZE 1536
#define LWIP_RAND() ((u32_t)rand())
#define LWIP_STATS 1
#define MEM_STATS 1
#define LWIP_STATS_DISPLAY 1
#define LWIP_NETIF_STATUS_CALLBACK 0
#define LWIP_NETIF_LINK_CALLBACK 0
#define LWIP_LWIPERF 1
#define LWIP_DEBUG 0

#endif /* LWIPOPTS_H */
