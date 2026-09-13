#!/usr/bin/env python3
"""Compute an EP plan's section-3 slice digest (heading-excluded, through
the separator plus one newline) - the countersign walk's own instrument,
so the walk never copies an author's digest. Usage: s3digest.py <plan.md>"""
import hashlib, sys
lines = open(sys.argv[1], 'rb').read().split(b'\n')
h = next(i for i, l in enumerate(lines) if l.startswith(b'# 3'))
s = next(i for i, l in enumerate(lines) if i > h and l == b'---')
sl = b'\n'.join(lines[h + 1:s + 1]) + b'\n'
print(len(sl), hashlib.sha256(sl).hexdigest()[:16])
