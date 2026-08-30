"""Every refusal cites its governing rule.

Ported from pwc-app/src/core/errors.js. A refusal is never a bare failure: it names
the LAW record it refused under (design 02 §1.2; audit guarantee "Explanation").
"""


class OpError(Exception):
    """A rule-cited refusal. `rule` is the LAW id (or root-rule id) that refused."""

    def __init__(self, rule, message):
        super().__init__(f"[{rule}] {message}")
        self.rule = rule
        self.message = message
