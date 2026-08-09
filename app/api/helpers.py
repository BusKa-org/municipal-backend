"""Small shared helpers for the HTTP controller layer."""

from typing import Any

__all__ = ["list_envelope"]


def list_envelope(items: Any) -> dict[str, Any]:
    """Wrap a sequence in the ``{"items": ..., "total": ...}`` list envelope."""
    return {"items": items, "total": len(items)}
