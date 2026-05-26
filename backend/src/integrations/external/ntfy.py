"""Minimal ntfy.sh client — push notifications (US-006, NFR-OBS alerts).

ntfy is HTTP-based and dead simple: POST to https://ntfy.sh/<topic>. We use
httpx so it integrates with our async stack. Silent no-op if topic is not
configured (lets Sprint 0/1 dev run without an ntfy account).
"""

from __future__ import annotations

from typing import Literal

import httpx
import structlog

logger = structlog.get_logger(__name__)

NtfyPriority = Literal["min", "low", "default", "high", "max"]


async def notify(
    topic: str | None,
    message: str,
    *,
    title: str | None = None,
    priority: NtfyPriority = "default",
    tags: list[str] | None = None,
    base_url: str = "https://ntfy.sh",
    timeout: float = 5.0,
) -> bool:
    """Send a push notification. Returns True on success, False otherwise.

    `topic` is the public path component (e.g. "passion-frederick-2026").
    Choose a long, unguessable string — ntfy topics are public by design.
    """
    if not topic:
        logger.debug("ntfy_skip_no_topic", message=message)
        return False

    headers: dict[str, str] = {"Priority": str(priority)}
    if title:
        headers["Title"] = title
    if tags:
        headers["Tags"] = ",".join(tags)

    url = f"{base_url.rstrip('/')}/{topic}"
    try:
        async with httpx.AsyncClient(timeout=timeout) as http:
            response = await http.post(url, content=message.encode("utf-8"), headers=headers)
            response.raise_for_status()
        logger.info("ntfy_sent", topic=topic, priority=priority, status=response.status_code)
        return True
    except httpx.HTTPError as e:
        logger.warning("ntfy_failed", topic=topic, error=str(e))
        return False
