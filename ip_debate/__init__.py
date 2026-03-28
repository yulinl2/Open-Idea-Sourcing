"""IP Debate / Reconstruction Test Pipeline.

This package is a **separate build track** from :mod:`open_idea_sourcing`
(the baseline novelty-evaluation pipeline).  Both packages live in the same
repository but carry **independent version numbers** so their release
cadences can evolve without coupling:

* ``open_idea_sourcing`` — baseline track, starts at v1.x
* ``ip_debate``          — debate / reconstruction track, starts at v0.x

To tell the two apart at a glance::

    import open_idea_sourcing   # baseline  — e.g. "1.3.0"
    import ip_debate            # debate    — e.g. "0.0.0"

Status: v0.0.0 scaffold — dev infra only, pipeline not yet built.
"""

__version__ = "0.0.0"
