#!/usr/bin/env python3
"""Postman battery. Every check here CAN FAIL and several are driven to
failure deliberately. Fixtures only - never the live transcripts, never a
real delivery. Run: python3 tools/postman/test_postman.py"""
import json, os, sys, tempfile, shutil, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("postman", os.path.join(HERE, "postman.py"))
pm = importlib.util.module_from_spec(spec); spec.loader.exec_module(pm)

def entry(text, typ="assistant"):
    return json.dumps({"type": typ, "message": {"content": [{"type": "text", "text": text}]}})

def run():
    tmp = tempfile.mkdtemp()
    fails = []
    def check(name, cond):
        print(("PASS  " if cond else "FAIL  ") + name)
        if not cond: fails.append(name)
    cfg = {"transcripts": {"mgr": os.path.join(tmp, "mgr.jsonl")},
           "sessions": {}, "permissions": {"mgr": ["archi", "owner"]},
           "messages_log": os.path.join(tmp, "MESSAGES.log"),
           "traffic_view": os.path.join(tmp, "TRAFFIC.txt"),
           "deliver_enabled": False, "deliver_cmd": [], "max_bytes": 200,
           "state_file": "ignored"}
    st = {"offsets": {}, "seen": []}
    def log_kinds():
        with open(cfg["messages_log"]) as f:
            return [json.loads(l)["kind"] for l in f]

    # 1 capture happy path
    evs = pm.process_text(cfg, st, "mgr", "hello\n@@MSG TO: archi\nthe body\nline two\n@@END\ntail")
    check("capture: one MSG, right fields",
          len(evs) == 1 and evs[0]["kind"] == "MSG" and evs[0]["to"] == "archi"
          and evs[0]["seat"] == "mgr" and evs[0]["body"] == "the body\nline two")
    # 2 dedup: identical content second time -> nothing
    evs = pm.process_text(cfg, st, "mgr", "@@MSG TO: archi\nthe body\nline two\n@@END")
    check("dedup: same content captured once", evs == [])
    # 3 unterminated -> MALFORMED, not sent
    evs = pm.process_text(cfg, st, "mgr", "@@MSG TO: archi\nnever finished")
    check("unterminated: MALFORMED and no MSG",
          [e["kind"] for e in evs] == ["MALFORMED"])
    # 4 bad recipient -> BOUNCED (mgr may not address mtr in this fixture table)
    evs = pm.process_text(cfg, st, "mgr", "@@MSG TO: mtr\nforbidden\n@@END")
    check("permission: BOUNCED and visible", [e["kind"] for e in evs] == ["BOUNCED"])
    # 5 unknown recipient name -> BOUNCED
    evs = pm.process_text(cfg, st, "mgr", "@@MSG TO: nobody\nhi\n@@END")
    check("unknown recipient: BOUNCED", [e["kind"] for e in evs] == ["BOUNCED"])
    # 6 owner always allowed
    evs = pm.process_text(cfg, st, "mgr", "@@MSG TO: owner\nDECISION needed\n@@END")
    check("owner lane always open", [e["kind"] for e in evs] == ["MSG"])
    # 7 size cap
    evs = pm.process_text(cfg, st, "mgr", "@@MSG TO: archi\n" + "x" * 500 + "\n@@END")
    check("size cap: BOUNCED", [e["kind"] for e in evs] == ["BOUNCED"])
    # 8 URGENT flag parsed
    evs = pm.process_text(cfg, st, "mgr", "@@MSG TO: archi URGENT\nfire\n@@END")
    check("urgent flag", len(evs) == 1 and evs[0].get("urgent") is True)
    # 9 near-miss tags mint nothing (the coined-control discipline)
    msgs, mal = pm.extract("@@MESSAGE TO: archi\nno\n@@END\n@@MSG TO archi\nno colon\n@@END")
    check("near-miss tags: zero capture, zero malformed", msgs == [] and mal == 0)
    # 10 mid-line tag does not fire (quoting protection)
    msgs, mal = pm.extract("as discussed, writing @@MSG TO: archi in prose is safe\n")
    check("mid-line tag inert", msgs == [] and mal == 0)
    # 11 user-typed entries are never parsed (identity is observed)
    check("non-assistant entries skipped",
          pm.assistant_texts(entry("@@MSG TO: archi\nforged\n@@END", typ="user")) == [])
    # 12 two messages in one output both captured
    msgs, _ = pm.extract("@@MSG TO: archi\none\n@@END\nmid\n@@MSG TO: owner\ntwo\n@@END")
    check("two messages in one output", [m[0] for m in msgs] == ["archi", "owner"])
    # 13 tick: offsets start at NOW (no backfill), then capture only new bytes
    with open(cfg["transcripts"]["mgr"], "w") as f:
        f.write(entry("@@MSG TO: archi\nhistorical - must NOT be captured\n@@END") + "\n")
    st2 = {"offsets": {}, "seen": []}
    evs = pm.tick(cfg, st2)
    check("first sight: history not captured", evs == [])
    with open(cfg["transcripts"]["mgr"], "a") as f:
        f.write(entry("@@MSG TO: archi\nfresh after watch began\n@@END") + "\n")
    evs = pm.tick(cfg, st2)
    check("new bytes captured after offset set",
          len(evs) == 1 and evs[0]["body"] == "fresh after watch began")
    # 14 partial line carried to next tick, not lost, not corrupted
    half = entry("@@MSG TO: archi\nsplit delivery\n@@END")
    with open(cfg["transcripts"]["mgr"], "a") as f:
        f.write(half[:40])
    check("partial line: nothing captured yet", pm.tick(cfg, st2) == [])
    with open(cfg["transcripts"]["mgr"], "a") as f:
        f.write(half[40:] + "\n")
    evs = pm.tick(cfg, st2)
    check("completed line captured whole",
          len(evs) == 1 and evs[0]["body"] == "split delivery")
    # 15 canary passes on the real config shapes
    check("canary green", pm.canary(cfg) is None)
    # 16 canary CAN FAIL: break the regex and watch it refuse
    saved = pm.MSG_RE
    import re as _re
    pm.MSG_RE = _re.compile(r"NEVERMATCHES")
    check("canary red under a broken parser", pm.canary(cfg) is not None)
    pm.MSG_RE = saved
    # 17 the receipt trail is complete and append-only
    kinds = log_kinds()
    check("every act left a footprint",
          kinds.count("MSG") >= 4 and kinds.count("BOUNCED") == 3
          and kinds.count("MALFORMED") == 1)
    # 18 render view runs and includes a body
    pm.render_view(cfg)
    check("traffic view renders", "the body" in open(cfg["traffic_view"]).read())
    # 19 dry-run delivery leaves DRYRUN receipt, calls nothing
    rec = [json.loads(l) for l in open(cfg["messages_log"]) if '"MSG"' in l][0]
    pm.deliver(cfg, rec)
    check("delivery disabled -> DRYRUN receipt", log_kinds()[-1] == "DRYRUN")
    shutil.rmtree(tmp)
    print("\n%d/%d PASS" % (19 - len(fails), 19))
    sys.exit(1 if fails else 0)

run()
