#!/usr/bin/env python3
# gov-os POSTMAN - the script that replaced the AI hub. Owner-ruled 2026-08-26
# in the architect chat ("build this now"), design dialogue same chat.
# NO AI ANYWHERE IN THIS FILE. It watches session transcripts, captures
# messages written in the @@MSG grammar, appends them to an append-only
# message log, renders the owner's traffic view, and (when enabled and
# tested) delivers by starting a turn at the addressee session.
#
# THE FOUR LAWS THIS SCRIPT EMBODIES:
#  1. IDENTITY IS OBSERVED, NEVER CLAIMED - the sender is whichever session's
#     transcript file the message was found in. There is no FROM field.
#  2. THE LOG IS APPEND-ONLY - state (delivered? bounced?) is never written
#     into an existing line; it is a NEW receipt line, and current state is
#     computed by reading.
#  3. THE POSTMAN HAS NO OPINIONS BUT ALWAYS LEAVES FOOTPRINTS - every act
#     (captured, bounced, malformed, delivered, failed) is a visible line.
#  4. IT FAILS LOUDLY OR NOT AT ALL - the startup canary must find a planted
#     message in a fixture and must NOT match a coined tag, or it refuses
#     to run.
#  5. THE READER NEVER WAITS FOR THE DOORBELL - capture runs every tick;
#     deliveries run in one background worker. A wake storm can delay other
#     wakes, never the record. (Added 2026-08-27 after a 10-minute capture
#     lag under an URGENT storm, owner-ordered "fix all these now".)
#  6. NEVER TWO WRITERS ON ONE IDENTITY - a seat whose transcript changed
#     within quiet_seconds is mid-turn; its doorbell DEFERS (receipted)
#     until quiet. (The two-writers hazard, driven live 2026-08-26 23:46.)
import json, os, re, sys, time, hashlib, subprocess, argparse, threading, queue

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HERE, "postman.config.json")

MSG_RE = re.compile(
    r"^@@MSG TO: ([A-Za-z][A-Za-z0-9_-]*)( URGENT)?[ \t]*\n(.*?)^@@END[ \t]*$",
    re.M | re.S)
START_RE = re.compile(r"^@@MSG TO:", re.M)

def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)

def state_path(cfg):
    return os.path.join(HERE, cfg.get("state_file", "postman.state.json"))

def load_state(cfg):
    p = state_path(cfg)
    if os.path.exists(p):
        with open(p) as f:
            return json.load(f)
    return {"offsets": {}, "seen": []}

def seed_seen_from_log(cfg, st):
    """mtr's cure (:2389): THE LOG IS THE DELIVERY, so an MSG id already
    standing on it may never be appended again - whatever the state file
    remembers. Seeding seen from the log at startup makes the log itself
    the dedup authority; a state rollback can no longer duplicate."""
    try:
        with open(cfg["messages_log"]) as f:
            for line in f:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if r.get("kind") == "MSG" and r.get("id") and r["id"] not in st["seen"]:
                    st["seen"].append(r["id"])
        st["seen"] = st["seen"][-5000:]
    except FileNotFoundError:
        pass

def save_state(cfg, st):
    p = state_path(cfg)
    tmp = p + ".tmp"
    with open(tmp, "w") as f:
        json.dump(st, f, indent=1)
    os.replace(tmp, p)   # atomic install, per the estate's own discipline

_APPEND_LOCK = threading.Lock()   # reader and delivery worker both append

def append_record(cfg, rec):
    """One JSON object per line, append-only, fdatasync before return."""
    rec["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    path = cfg["messages_log"]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    line = json.dumps(rec, ensure_ascii=False)
    with _APPEND_LOCK:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        try:
            os.write(fd, (line + "\n").encode())
            os.fdatasync(fd)
        finally:
            os.close(fd)
    return rec

def assistant_texts(jsonl_line):
    """All text strings from one transcript entry IF it is assistant output.
    Tree-walk keeps this tolerant of format drift; the canary keeps drift loud."""
    try:
        obj = json.loads(jsonl_line)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return []
    if not isinstance(obj, dict) or obj.get("type") != "assistant":
        return []
    out = []
    def walk(x):
        if isinstance(x, dict):
            for k, v in x.items():
                if k == "text" and isinstance(v, str):
                    out.append(v)
                else:
                    walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(obj)
    return out

def msg_id(seat, body):
    return hashlib.sha256((seat + "\x00" + body).encode()).hexdigest()[:16]

def extract(text):
    """-> (messages, malformed_count). A start tag with no @@END in the same
    output is MALFORMED and not sent - the author must see it did not go."""
    msgs = [(m.group(1), bool(m.group(2)), m.group(3).rstrip("\n"))
            for m in MSG_RE.finditer(text)]
    malformed = len(START_RE.findall(text)) - len(msgs)
    return msgs, malformed

def process_text(cfg, st, seat, text):
    """Capture every message in one block of assistant text. Pure record acts."""
    events = []
    msgs, malformed = extract(text)
    for _ in range(malformed):
        events.append(append_record(cfg, {
            "kind": "MALFORMED", "seat": seat,
            "note": "start tag with no @@END in the same output; NOT sent"}))
    for to, urgent, body in msgs:
        mid = msg_id(seat, body)
        if mid in st["seen"]:
            continue                       # idempotent: dedup by content
        st["seen"] = (st["seen"] + [mid])[-5000:]
        allowed = cfg["permissions"].get(seat, [])
        if to not in allowed and to != "owner":
            events.append(append_record(cfg, {
                "kind": "BOUNCED", "id": mid, "seat": seat, "to": to,
                "note": "recipient not in permission table", "body": body}))
            continue
        if len(body) > cfg.get("max_bytes", 20000):
            events.append(append_record(cfg, {
                "kind": "BOUNCED", "id": mid, "seat": seat, "to": to,
                "note": "over size cap"}))
            continue
        events.append(append_record(cfg, {
            "kind": "MSG", "id": mid, "seat": seat, "to": to,
            "urgent": urgent, "body": body}))
    return events

def deliver(cfg, rec):
    """Start a turn at the addressee. DISABLED until the owner's live test;
    dry-run leaves the receipt trail so the pipeline is provable end to end."""
    to = rec["to"]
    sid = cfg["sessions"].get(to)
    if not cfg.get("deliver_enabled", False):
        append_record(cfg, {"kind": "DRYRUN", "id": rec["id"], "to": to,
                            "note": "delivery disabled pending the owner's live test"})
        return
    if not sid:
        append_record(cfg, {"kind": "FAILED", "id": rec["id"], "to": to,
                            "note": "no session id configured"})
        return
    text = ("POSTMAN DELIVERY msg %s from %s (verify against %s):\n%s"
            % (rec["id"], rec["seat"], cfg["messages_log"], rec["body"]))
    cmd = [w.replace("{session}", sid) for w in cfg["deliver_cmd"]]
    cmd = [w.replace("{message}", text) for w in cmd]
    try:
        # claude --resume resolves sessions PER PROJECT FOLDER, so the
        # subprocess must run at the repo regardless of the service's cwd.
        r = subprocess.run(cmd, capture_output=True, timeout=cfg.get("deliver_timeout", 300),
                           cwd=cfg.get("deliver_cwd") or os.path.dirname(cfg["messages_log"]))
        kind = "DELIVERED" if r.returncode == 0 else "FAILED"
        note = (r.stderr or r.stdout or b"")[-200:].decode("utf-8", "replace")
        append_record(cfg, {"kind": kind, "id": rec["id"], "to": to, "rc": r.returncode,
                            **({"note": note} if kind == "FAILED" else {})})
    except Exception as e:
        append_record(cfg, {"kind": "FAILED", "id": rec["id"], "to": to, "note": str(e)[:200]})

def _quiet_wait(cfg, rec):
    """LAW 6, the two-writers guard: never ring a seat whose transcript was
    written within quiet_seconds - a live turn may hold that identity, and a
    second writer under one name puts contradictions on the record. Defers
    with a receipt; after defer_max_seconds it delivers anyway, receipted."""
    path = cfg.get("transcripts", {}).get(rec["to"])
    if not path or not os.path.exists(path):
        return
    quiet = cfg.get("quiet_seconds", 10)
    limit = cfg.get("defer_max_seconds", 900)
    start = time.time()
    deferred = False
    while time.time() - os.path.getmtime(path) < quiet:
        if time.time() - start > limit:
            append_record(cfg, {"kind": "DEFER-EXPIRED", "id": rec["id"],
                                "to": rec["to"], "note":
                                "seat never went quiet in defer_max_seconds; delivering anyway"})
            return
        if not deferred:
            deferred = True
            append_record(cfg, {"kind": "DEFERRED", "id": rec["id"],
                                "to": rec["to"], "note":
                                "addressee transcript active; two-writers guard holding the wake"})
        time.sleep(2)

def delivery_worker(cfg, q, dirty):
    """LAW 5: one background worker rings doorbells so the reader never
    blocks. Deliveries stay serialized among themselves (one worker) - two
    concurrent resumes are never minted by the postman itself."""
    while True:
        rec = q.get()
        try:
            _quiet_wait(cfg, rec)
            deliver(cfg, rec)
        except Exception as e:
            try:
                append_record(cfg, {"kind": "FAILED", "id": rec.get("id"),
                                    "to": rec.get("to"),
                                    "note": ("worker: " + str(e))[:200]})
            except Exception:
                pass
        dirty.set()
        q.task_done()

def requeue_undelivered(cfg, q):
    """A restart between capture and delivery used to orphan the wake (the
    09:11 restart ate two). THE LOG IS THE QUEUE'S DURABLE FORM: at startup,
    any MSG with no terminal receipt (DELIVERED/FAILED/DRYRUN/BOUNCED)
    re-queues. Receipts make this idempotent - a delivered message can
    never re-ring."""
    msgs, terminal = {}, set()
    try:
        with open(cfg["messages_log"]) as f:
            for line in f:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if r.get("kind") == "MSG":
                    msgs.setdefault(r["id"], r)
                elif r.get("kind") in ("DELIVERED", "FAILED", "DRYRUN", "BOUNCED"):
                    terminal.add(r.get("id"))
    except FileNotFoundError:
        return
    for mid, rec in msgs.items():
        if mid not in terminal and rec.get("to") in cfg.get("sessions", {}):
            append_record(cfg, {"kind": "REQUEUED", "id": mid, "to": rec["to"],
                                "note": "captured but never delivered (restart window); re-queued at startup"})
            q.put(rec)

def idle_wake_check(cfg, st, q):
    """Owner-ordered 2026-08-27 morning: WHEN ALL SEATS ARE QUIET, WAKE THEM.
    If every watched transcript has been silent for idle_wake_minutes, ring
    every seat that has a doorbell with the standing drain order. Cooldown =
    the same interval, so one round of wakes cannot storm. 0/absent = off."""
    mins = cfg.get("idle_wake_minutes", 0)
    if not mins or not cfg.get("sessions"):
        return
    now = time.time()
    if now - st.get("last_idle_wake", 0) < mins * 60:
        return
    for path in cfg["transcripts"].values():
        if os.path.exists(path) and now - os.path.getmtime(path) < mins * 60:
            return                       # somebody is (or was recently) working
    st["last_idle_wake"] = now
    for seat in cfg["sessions"]:
        wid = "idlewake-" + time.strftime("%H%M%S")
        append_record(cfg, {"kind": "IDLE-WAKE", "id": wid, "to": seat,
                            "note": "all seats quiet %dm; standing drain order sent" % mins})
        q.put({"id": wid, "seat": "postman", "to": seat, "urgent": True,
               "body": ("IDLE WAKE - every seat has been quiet for %d minutes. "
                        "Drain planning/comms/MESSAGES.log for lines TO: your seat "
                        "past your last-acted id, advance whatever your seat holds "
                        "(closes, walks, dispatches), file what you finish. If "
                        "nothing stands at your desk, end the turn briefly. Do not "
                        "reply to this wake unless you acted." % mins)})

def render_view(cfg):
    """The owner's reading view - a COMPUTED VIEW, regenerated whole (views
    may be rewritten; the log may not)."""
    out = ["# TRAFFIC - computed view of %s\n# newest last; this file is "
           "regenerated, never authoritative\n" % cfg["messages_log"]]
    try:
        with open(cfg["messages_log"]) as f:
            for line in f:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if r["kind"] == "MSG":
                    out.append("--- %s  %s -> %s%s  [%s]\n%s\n" % (
                        r["ts"], r["seat"], r["to"],
                        " URGENT" if r.get("urgent") else "", r["id"], r["body"]))
                else:
                    out.append("... %s  %s %s\n" % (r["ts"], r["kind"],
                               json.dumps({k: v for k, v in r.items()
                                           if k not in ("kind", "ts", "body")})))
    except FileNotFoundError:
        out.append("(no traffic yet)\n")
    tmp = cfg["traffic_view"] + ".tmp"
    with open(tmp, "w") as f:
        f.write("\n".join(out))
    os.replace(tmp, cfg["traffic_view"])
    # THE OWNER'S PAGE - a browser tab that refreshes itself. No JSON, no
    # terminal: newest messages on top, full text, receipts one line.
    html = ["<!doctype html><meta http-equiv=refresh content=5><meta charset=utf-8>",
            "<title>gov-os comms</title><body style='font:15px/1.5 sans-serif;max-width:60em;margin:2em auto;background:#111;color:#ddd'>",
            "<h2 style='color:#fff'>Estate comms — live, newest first</h2>"]
    # OWNER'S SCOREBOARD (2026-08-27, his tracking demand): number every
    # message, mark answered/awaiting (a later message naming the id), and
    # show each seat's debts so chaos has a ledger.
    msgs, receipts = [], {}
    try:
        with open(cfg["messages_log"]) as f:
            for n, line in enumerate(f, 1):
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                r["_n"] = n
                if r["kind"] == "MSG":
                    msgs.append(r)
                elif r.get("id"):
                    receipts.setdefault(r["id"], []).append(r)
    except FileNotFoundError:
        pass
    answered = set()
    for m in msgs:
        for prior in msgs:
            if prior["_n"] < m["_n"] and prior["id"][:8] in m["body"]:
                answered.add(prior["id"])
    per = {}
    for m in msgs:
        s = per.setdefault(m.get("seat", "?"), {"sent": 0, "await": 0, "fail": 0})
        s["sent"] += 1
        recs = receipts.get(m["id"], [])
        if m["to"] != "owner" and m["id"] not in answered:
            s["await"] += 1
        if any(x["kind"] == "FAILED" for x in recs) and not any(x["kind"] == "DELIVERED" for x in recs):
            s["fail"] += 1
    html.append("<div style='border:1px solid #666;border-radius:8px;padding:.8em;margin:1em 0;background:#1a1a1a'>"
                "<b style='color:#fff'>SCOREBOARD</b> — sent / <span style='color:#fc6'>awaiting reply</span> / <span style='color:#f66'>undelivered</span><br>"
                + " &nbsp; ".join("<b style='color:#8cf'>%s</b> %d / <span style='color:#fc6'>%d</span> / <span style='color:#f66'>%d</span>"
                                  % (k, v["sent"], v["await"], v["fail"]) for k, v in sorted(per.items()))
                + "<br><span style='color:#888;font-size:13px'>every message carries #number and id — a reply opens by naming the id it answers</span></div>")
    blocks = []
    try:
        with open(cfg["messages_log"]) as f:
            for line in f:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                t = r.get("ts", "")[11:19]
                if r["kind"] == "MSG":
                    esc = (r["body"].replace("&", "&amp;").replace("<", "&lt;"))
                    blocks.append(
                        "<div style='border:1px solid #444;border-radius:8px;padding:1em;margin:1em 0'>"
                        "<b style='color:#8cf'>%s → %s</b> <span style='color:#888'>%s%s</span>"
                        "<pre style='white-space:pre-wrap;font:inherit;margin:.5em 0 0'>%s</pre></div>"
                        % (r.get("seat", "?"), r.get("to", "?"), t,
                           " · URGENT" if r.get("urgent") else "", esc))
                else:
                    blocks.append("<div style='color:#7a7;font-size:13px;margin:.2em 0'>%s %s → %s %s</div>"
                                  % (t, r["kind"], r.get("to", ""), (r.get("note", "") or "")[:90]))
    except FileNotFoundError:
        pass
    html += reversed(blocks)
    tmp2 = cfg["traffic_view"] + ".html.tmp"
    with open(tmp2, "w") as f:
        f.write("\n".join(html))
    os.replace(tmp2, cfg["traffic_view"] + ".html")

def canary(cfg):
    """Refuse to run unless the parser proves it can both FIND and NOT-FIND."""
    planted = json.dumps({"type": "assistant", "message": {"content": [
        {"type": "text", "text": "prose\n@@MSG TO: mgr\ncanary body\n@@END\ntail"}]}})
    texts = assistant_texts(planted)
    msgs, _ = extract("\n".join(texts))
    if len(msgs) != 1 or msgs[0][0] != "mgr" or msgs[0][2] != "canary body":
        return "canary FAILED: planted message not captured (transcript format drift?)"
    coined = json.dumps({"type": "assistant", "message": {"content": [
        {"type": "text", "text": "@@MESSAGE TO: mgr\nnot the tag\n@@FIN"}]}})
    m2, _ = extract("\n".join(assistant_texts(coined)))
    if m2:
        return "canary FAILED: coined near-miss tag matched; parser too loose"
    user_quote = json.dumps({"type": "user", "message": {"content": [
        {"type": "text", "text": "@@MSG TO: mgr\nquoted by a human\n@@END"}]}})
    if assistant_texts(user_quote):
        return "canary FAILED: non-assistant entry parsed as assistant"
    return None

def tick(cfg, st):
    """One pass over every watched transcript: read only the new bytes."""
    events = []
    for seat, path in cfg["transcripts"].items():
        if not os.path.exists(path):
            continue
        size = os.path.getsize(path)
        off = st["offsets"].get(path)
        if off is None:
            st["offsets"][path] = size      # first sight: start at NOW, never backfill
            continue
        if size <= off:
            st["offsets"][path] = min(off, size)
            continue
        with open(path, "rb") as f:
            f.seek(off)
            chunk = f.read(size - off)
        # only consume complete lines; carry a partial line to the next tick
        cut = chunk.rfind(b"\n")
        if cut == -1:
            continue
        st["offsets"][path] = off + cut + 1
        for raw in chunk[:cut].split(b"\n"):
            texts = assistant_texts(raw.decode("utf-8", "replace"))
            if texts:
                events += process_text(cfg, st, seat, "\n".join(texts))
    return events

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true", help="one tick, then exit")
    ap.add_argument("--render", action="store_true", help="render the view, then exit")
    a = ap.parse_args()
    cfg = load_config()
    err = canary(cfg)
    if err:
        print(err, file=sys.stderr)
        sys.exit(3)
    if a.render:
        render_view(cfg); return
    st = load_state(cfg)
    seed_seen_from_log(cfg, st)
    q = queue.Queue()
    dirty = threading.Event()
    if not a.once:
        threading.Thread(target=delivery_worker, args=(cfg, q, dirty),
                         daemon=True).start()
        requeue_undelivered(cfg, q)
    cfg_mtime = os.path.getmtime(CONFIG_PATH)
    while True:
        # ONCE-AND-FOR-ALL (owner-ordered 2026-08-27 00:35): config reloads
        # itself on change - no restart is ever needed for a config edit.
        # Only mutable knobs refresh; transcripts/log paths stay pinned to
        # the running instance so offsets never dangle mid-flight.
        try:
            m = os.path.getmtime(CONFIG_PATH)
            if m != cfg_mtime:
                cfg_mtime = m
                fresh = load_config()
                # every knob born AFTER this list must be added here or its
                # config edits silently never land (driven 2026-08-27 16:10:
                # idle_wake_minutes was missing and a 15:48 tune never took)
                for k in ("sessions", "permissions", "deliver_enabled",
                          "deliver_cmd", "deliver_cwd", "deliver_timeout",
                          "quiet_seconds", "defer_max_seconds",
                          "poll_seconds", "max_bytes", "idle_wake_minutes"):
                    if k in fresh:
                        cfg[k] = fresh[k]
                    else:
                        cfg.pop(k, None)
        except (OSError, json.JSONDecodeError):
            pass    # a half-written config never kills the carrier
        evs = tick(cfg, st)
        if not a.once:
            idle_wake_check(cfg, st, q)
        # capture is durable BEFORE any delivery: a kill mid-wake can no
        # longer roll the offsets back and re-capture (the duplicate class
        # observed at the 2026-08-26 23:51 restart).
        save_state(cfg, st)
        for e in evs:
            if e["kind"] == "MSG":
                # EVERY message rings its addressee (owner-confirmed 2026-08-27:
                # "I saw the postman sending to chats - why not now"). URGENT is
                # a priority marker in the grammar, never a delivery gate - the
                # protocol doc said urgent-only and the doc was wrong, not this.
                if a.once:
                    deliver(cfg, e)     # --once stays synchronous for the battery
                else:
                    q.put(e)
        if evs or dirty.is_set():
            dirty.clear()
            render_view(cfg)
        if a.once:
            break
        time.sleep(cfg.get("poll_seconds", 2))

if __name__ == "__main__":
    main()
