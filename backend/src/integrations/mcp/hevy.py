"""Hevy client — MCP-first per ADR-002, spawned as a stdio subprocess.

Sprint 1 design (see also docker-compose.yml note): the backend container has
nodejs installed and launches `npx -y hevy-mcp` on demand via the mcp Python
SDK. This is the standard MCP pattern (client spawns server) — a separate "MCP
container" is reserved for future HTTP/SSE transport use cases.

If the chrisdoc/hevy-mcp tool names differ from DEFAULT_TOOL_NAMES, override
them by passing `tool_names=` to McpHevyClient(...).
"""

from __future__ import annotations

import json
import os
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol

# Defaults — adjust on first contact with the real hevy-mcp if needed.
DEFAULT_TOOL_NAMES = {
    "list_workouts": "get-workouts",
    "get_workout": "get-workout",
    "workout_count": "get-workout-count",
    "list_exercise_templates": "get-exercise-templates",
}


@dataclass(slots=True)
class HevyExerciseDTO:
    title: str | None
    exercise_template_id: str | None
    order_index: int
    notes: str | None = None
    superset_id: str | None = None
    sets: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class HevyWorkoutDTO:
    """Normalized workout payload — what sync_hevy consumes."""

    hevy_id: str
    title: str | None
    description: str | None
    start_time: datetime
    end_time: datetime | None
    hevy_created_at: datetime | None
    hevy_updated_at: datetime | None
    raw: dict[str, Any]
    exercises: list[HevyExerciseDTO]


class HevyClient(Protocol):
    """Read-side Hevy interface consumed by sync_hevy.

    Implementations are async context managers — `async with client:` opens the
    underlying MCP session (or no-op for fakes).
    """

    async def __aenter__(self) -> HevyClient: ...

    async def __aexit__(self, *exc: object) -> None: ...

    async def list_workouts(
        self, *, page: int = 1, page_size: int = 50
    ) -> tuple[list[HevyWorkoutDTO], bool]:
        """Return (workouts, has_more)."""
        ...

    async def get_workout(self, hevy_id: str) -> HevyWorkoutDTO | None: ...

    async def list_exercise_templates(self) -> list[dict[str, Any]]: ...


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def normalize_workout(raw: dict[str, Any]) -> HevyWorkoutDTO:
    """Convert a raw Hevy workout payload into the internal DTO.

    Hevy schema (camelCase keys, ISO-8601 dates with trailing Z): id, title,
    description, startTime, endTime, createdAt, updatedAt, exercises[{title,
    exerciseTemplateId, notes, supersetId, sets[{weightKg, reps, rpe, type,
    distanceMeters, durationSeconds}]}].
    """
    exercises: list[HevyExerciseDTO] = []
    for idx, ex in enumerate(raw.get("exercises") or []):
        sets: list[dict[str, Any]] = []
        for s_idx, s in enumerate(ex.get("sets") or []):
            sets.append(
                {
                    "order_index": s_idx,
                    "set_type": s.get("type") or "normal",
                    "weight_kg": s.get("weightKg") or s.get("weight_kg"),
                    "reps": s.get("reps"),
                    "rpe": s.get("rpe"),
                    "distance_meters": s.get("distanceMeters") or s.get("distance_meters"),
                    "duration_seconds": s.get("durationSeconds") or s.get("duration_seconds"),
                }
            )
        exercises.append(
            HevyExerciseDTO(
                title=ex.get("title"),
                exercise_template_id=ex.get("exerciseTemplateId") or ex.get("exercise_template_id"),
                order_index=ex.get("index", idx),
                notes=ex.get("notes"),
                superset_id=ex.get("supersetId") or ex.get("superset_id"),
                sets=sets,
            )
        )

    start_time = _parse_dt(raw.get("startTime") or raw.get("start_time"))
    if start_time is None:
        raise ValueError(f"workout {raw.get('id')!r} missing startTime")

    return HevyWorkoutDTO(
        hevy_id=str(raw["id"]),
        title=raw.get("title"),
        description=raw.get("description"),
        start_time=start_time,
        end_time=_parse_dt(raw.get("endTime") or raw.get("end_time")),
        hevy_created_at=_parse_dt(raw.get("createdAt") or raw.get("created_at")),
        hevy_updated_at=_parse_dt(raw.get("updatedAt") or raw.get("updated_at")),
        raw=raw,
        exercises=exercises,
    )


class McpHevyClient:
    """Hevy client backed by chrisdoc/hevy-mcp spawned as a stdio subprocess."""

    def __init__(
        self,
        api_key: str,
        *,
        command: str = "npx",
        args: list[str] | None = None,
        tool_names: dict[str, str] | None = None,
    ) -> None:
        self._api_key = api_key
        self._command = command
        self._args = args if args is not None else ["-y", "hevy-mcp"]
        self._tool_names = {**DEFAULT_TOOL_NAMES, **(tool_names or {})}
        self._stack = AsyncExitStack()
        self._session: Any = None

    async def __aenter__(self) -> McpHevyClient:
        # Import here so unit-test paths never import the MCP transport.
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        params = StdioServerParameters(
            command=self._command,
            args=self._args,
            env={**os.environ, "HEVY_API_KEY": self._api_key},
        )
        read, write = await self._stack.enter_async_context(stdio_client(params))
        self._session = await self._stack.enter_async_context(ClientSession(read, write))
        await self._session.initialize()
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self._stack.aclose()
        self._session = None

    def _decode_tool_result(self, result: Any) -> Any:
        """MCP returns CallToolResult; we expect a single JSON text content block."""
        for block in getattr(result, "content", []):
            text = getattr(block, "text", None)
            if text:
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return text
        return None

    async def _call(self, key: str, args: dict[str, Any] | None = None) -> Any:
        if self._session is None:
            raise RuntimeError("McpHevyClient must be used as async context manager")
        result = await self._session.call_tool(self._tool_names[key], args or {})
        return self._decode_tool_result(result)

    async def list_workouts(
        self, *, page: int = 1, page_size: int = 50
    ) -> tuple[list[HevyWorkoutDTO], bool]:
        payload = await self._call("list_workouts", {"page": page, "pageSize": page_size})
        if isinstance(payload, dict):
            items = payload.get("workouts") or payload.get("items") or []
            has_more = bool(payload.get("hasMore") or payload.get("has_more"))
        else:
            items = payload or []
            has_more = len(items) >= page_size
        return [normalize_workout(w) for w in items], has_more

    async def get_workout(self, hevy_id: str) -> HevyWorkoutDTO | None:
        payload = await self._call("get_workout", {"workoutId": hevy_id})
        if not payload:
            return None
        if isinstance(payload, dict) and "id" not in payload:
            payload = payload.get("workout", {})
        return normalize_workout(payload)

    async def list_exercise_templates(self) -> list[dict[str, Any]]:
        payload = await self._call("list_exercise_templates")
        if isinstance(payload, dict):
            payload = payload.get("templates") or payload.get("items") or []
        return [
            {
                "hevy_id": str(t["id"]),
                "title": t.get("title", ""),
                "primary_muscle_group": t.get("primaryMuscleGroup")
                or t.get("primary_muscle_group"),
                "secondary_muscle_groups": t.get("secondaryMuscleGroups")
                or t.get("secondary_muscle_groups"),
                "equipment": t.get("equipment"),
                "exercise_type": t.get("exerciseType") or t.get("exercise_type"),
            }
            for t in (payload or [])
        ]


class FakeHevyClient:
    """Deterministic Hevy stub for unit + BDD tests (no nodejs / no network)."""

    def __init__(
        self,
        workouts: list[HevyWorkoutDTO] | None = None,
        templates: list[dict[str, Any]] | None = None,
    ) -> None:
        self.workouts = workouts or []
        self.templates = templates or []
        self.call_log: list[tuple[str, dict[str, Any]]] = []

    async def __aenter__(self) -> FakeHevyClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        return None

    async def list_workouts(
        self, *, page: int = 1, page_size: int = 50
    ) -> tuple[list[HevyWorkoutDTO], bool]:
        self.call_log.append(("list_workouts", {"page": page, "page_size": page_size}))
        start = (page - 1) * page_size
        items = self.workouts[start : start + page_size]
        has_more = (start + page_size) < len(self.workouts)
        return items, has_more

    async def get_workout(self, hevy_id: str) -> HevyWorkoutDTO | None:
        self.call_log.append(("get_workout", {"hevy_id": hevy_id}))
        for w in self.workouts:
            if w.hevy_id == hevy_id:
                return w
        return None

    async def list_exercise_templates(self) -> list[dict[str, Any]]:
        self.call_log.append(("list_exercise_templates", {}))
        return list(self.templates)
