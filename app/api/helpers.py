"""Small shared helpers for the HTTP controller layer.

These exist purely to remove repetition from the controllers. They are
deliberately faithful to the hand-written code they replace -- neither of
them adds validation, coercion or error handling.
"""

from typing import Any

from flask import request

__all__ = ["json_body", "list_envelope"]


def json_body() -> Any:
    """Parsed JSON request body, falling back to an empty dict.

    Equivalent to the ``request.get_json(silent=True) or {}`` that was
    repeated across the controllers, including its quirks:

    - a missing, unparseable or non-JSON body yields ``{}`` rather than
      raising, so callers cannot tell those cases apart;
    - any *falsy* parsed value -- ``{}``, ``[]``, ``0``, ``""``, ``null`` --
      also collapses to ``{}``;
    - any *truthy* non-object value, such as a non-empty list, is returned
      unchanged and reaches the caller's schema as-is.

    The return type is intentionally ``Any``: this does not guarantee a dict.
    Coercing non-objects to ``{}`` would change the responses that routes
    currently produce for such payloads.
    """
    return request.get_json(silent=True) or {}


def list_envelope(items: Any) -> dict[str, Any]:
    """Wrap a sequence in the ``{"items": ..., "total": ...}`` list envelope.

    ``total`` is the length of ``items``, matching the hand-written envelope
    it replaces. This describes the payload only; callers still pass the
    result through their own response schema where they did before.
    """
    return {"items": items, "total": len(items)}
