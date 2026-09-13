<!-- gov-os provenance · FRAME: systems-architecture · CORPUS-CLASS: build-planning · Full declaration: SCOPE-STATEMENT.md. -->
<!-- doc: class=CANON status=LIVE supersedes=- superseded-by=- verified=2026-08-27 -->
# THE POSTMAN — complete setup map

Law lives in `planning/method/POSTMAN-PROTOCOL.md`. This file is the
component map: what each piece is, where it lives, every parameter.

## The system in one line
Seats write `@@MSG TO: <seat> [URGENT] … @@END` as the FINAL text of a
turn → the script scrapes it into an append-only log → receipts record
every act → URGENT rings the addressee (CLI resume) → the owner reads
everything in a self-refreshing page. No AI carries anything.

## Components

| file | role |
|---|---|
| `postman.py` | the carrier daemon. Six laws in its header. Flags: `--once` (single tick, battery), `--render` (rebuild views, exit). Config hot-reloads — never restart for config changes |
| `postman.config.json` | all parameters (table below) |
| `postman.state.json` | memory: byte offsets per transcript + seen message ids (re-seeded from the log at startup — the log is the dedup authority) |
| `postman.service` | user systemd unit. `systemctl --user status postman` |
| `test_postman.py` | 19-check battery incl. driven-to-failure controls. Run after ANY edit to postman.py |
| `../transport/push_gate.py` + `push-allowlist.txt` | gate on the app's send tool (display copies only; see protocol) |
| `../../planning/comms/MESSAGES.log` | THE DELIVERY TRUTH. Append-only, script-written only |
| `../../planning/comms/TRAFFIC.txt` | owner's plain-text view (computed) |
| `../../planning/comms/TRAFFIC.txt.html` | owner's live page — open in a browser, refreshes itself every 5 s, newest first |

## Every config parameter

| key | meaning |
|---|---|
| `transcripts` | seat → transcript path. THE IDENTITY MAP — re-drive on any reseat |
| `sessions` | seat → session UUID (= transcript filename). Who can be doorbell-woken; remove a row to silence a seat's doorbell (FAILED receipts, visible) |
| `permissions` | who may address whom; violations BOUNCE |
| `deliver_enabled` | doorbell master switch |
| `deliver_cwd` | repo root — resume resolves sessions per folder |
| `deliver_cmd` | the wake command (`claude --resume {session} -p …`) |
| `deliver_timeout` | seconds a woken turn may run (1800) |
| `quiet_seconds` | two-writers guard: seat must be this quiet before a wake (10) |
| `defer_max_seconds` | guard stops deferring after this, delivers receipted (900) |
| `idle_wake_minutes` | all-seats-quiet heartbeat; 0 = off |
| `poll_seconds` | capture tick (2) |
| `max_bytes` | per-message size cap |

## Hard-won platform caps (details in the protocol's honest caps)
Turn-final text only is guaranteed captured · grammar is live in code
fences · app and CLI hold SEPARATE logins (`claude login` re-auths the
carrier) · woken turns: no compound bash, no app pen, and anything they
spawn DIES at turn exit (dispatch only from app-run turns) · chat
windows never repaint headless turns — the page is the display ·
DELIVERED receipts land when the woken turn exits.
