"""Hevy MCP client (wraps the hevy-mcp Node.js server).

Implements the consumption side of ADR-002 (MCP-first). Used by the sync job
(Flow 1) with idempotent UPSERT by hevy_id.
"""

from __future__ import annotations


class HevyClient:
    async def get_workout_events(self, since: str | None) -> list[dict]:
        """Fetch workout events from Hevy since a timestamp (incremental sync).

        TODO(sprint-2): connect to hevy-mcp, call its tools, normalize output.
        """
        raise NotImplementedError("Implement in sprint 2 (US-008, Flow 1)")
