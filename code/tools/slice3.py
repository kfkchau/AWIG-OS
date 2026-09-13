#!/usr/bin/env python3
# gov-os countersign instrument: prints the §3 slice length and sha256-16
# of a plan file, heading-EXCLUDED through the separator plus one newline,
# per EP-SHAPE's published slice rule. Usage: python3 tools/slice3.py <plan.md>
import hashlib, sys
p = sys.argv[1]
lines = open(p, 'rb').read().split(b'\n')
h = next(i for i, l in enumerate(lines) if l.startswith(b'# 3'))
s = next(i for i, l in enumerate(lines) if i > h and l == b'---')
sl = b'\n'.join(lines[h + 1:s + 1]) + b'\n'
print(len(sl), hashlib.sha256(sl).hexdigest()[:16])
