"""Brain orchestrator graph (LangGraph).

Implements the think -> plan -> execute -> reflect loop. One action per cycle
for safety and budget control (see Flow 4). Triggered periodically by Celery
Beat or by events.
"""

from __future__ import annotations


def build_brain_graph():
    """Construct and compile the LangGraph state graph.

    TODO(sprint-2): define nodes (think, plan, route, execute, reflect),
    edges, and compile with the BrainState schema.
    """
    raise NotImplementedError("Implement in sprint 2 (US-001..007, Flow 4)")
