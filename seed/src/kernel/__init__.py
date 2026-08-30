"""gov-os kernel — the foundation (record + gate + views).

The spine every governed subsystem rides on. Ported from the estate's proving code
(pwc-app/src/core, src/domain) into the gov-os canonical envelope
(design/11-RECORD-SHAPES.md, names per design/20-CANONICAL-GLOSSARY.md).

One definitive (the record), one write path (the gate), all current state computed
(views). Nothing stored that can be derived; a crash loses only caches; recovery is
recompute.
"""
