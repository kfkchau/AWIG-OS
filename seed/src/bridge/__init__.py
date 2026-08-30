"""gov-os bridge — the depth stances that take a governed core from record-logic to a
real resource (design/16-BRIDGE). Stance 3 (M2) serves a core as a live resource in user
space (FUSE); stance 4 (M3) moves it below the syscall line. These adapters may use
non-core dependencies (e.g. fusepy/libfuse); the zero-dependency rule binds the core, not
the bridge adapters.
"""
