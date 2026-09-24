"""Shared HTTP transport with sanitized failure diagnostics."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests

_SENSITIVE_NAMES = {
    "authorization",
    "cookie",
    "password",
    "set-cookie",
    "token",
    "x-api-key",
}
_MASK = "***MASKED***"
_PREVIEW_LIMIT = 1_000


def _mask_data(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _MASK if str(key).lower() in _SENSITIVE_NAMES else _mask_data(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_mask_data(item) for item in value]
    return value


def _safe_headers(headers: Mapping[str, str]) -> dict[str, str]:
    return {
        key: _MASK if key.lower() in _SENSITIVE_NAMES else value
        for key, value in headers.items()
    }


def _safe_url(url: str) -> str:
    parts = urlsplit(url)
    safe_query = urlencode(
        [
            (key, _MASK if key.lower() in _SENSITIVE_NAMES else value)
            for key, value in parse_qsl(parts.query, keep_blank_values=True)
        ]
    )
    return urlunsplit((parts.scheme, parts.netloc, parts.path, safe_query, parts.fragment))


def _body_preview(body: Any, content_type: str = "") -> str:
    if body is None:
        return "<empty>"
    if isinstance(body, bytes):
        text = body.decode("utf-8", errors="replace")
    else:
        text = str(body)

    if "json" in content_type.lower() or text.lstrip().startswith(("{", "[")):
        try:
            text = json.dumps(_mask_data(json.loads(text)), sort_keys=True)
        except (TypeError, ValueError):
            pass
    return text[:_PREVIEW_LIMIT]


class ApiClient:
    """Small wrapper around a requests session for one API base URL."""

    def __init__(
        self,
        base_url: str,
        timeout: float,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()
        self.last_response: requests.Response | None = None

    def request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> requests.Response:
        """Send a request using the configured base URL and default timeout."""
        kwargs.setdefault("timeout", self.timeout)
        response = self.session.request(
            method=method,
            url=f"{self.base_url}/{path.lstrip('/')}",
            **kwargs,
        )
        self.last_response = response
        return response

    def reset_diagnostics(self) -> None:
        """Discard request state retained for a previous test."""
        self.last_response = None

    def format_exchange(self, response: requests.Response | None = None) -> str:
        """Format one HTTP exchange while masking credentials and tokens."""
        if response is None:
            response = self.last_response
        if response is None:
            return "No HTTP exchange was recorded."

        request = response.request
        request_headers = _safe_headers(request.headers)
        response_headers = _safe_headers(response.headers)
        request_content_type = request.headers.get("Content-Type", "")
        response_content_type = response.headers.get("Content-Type", "")

        return "\n".join(
            [
                f"Request: {request.method} {_safe_url(request.url)}",
                f"Request headers: {request_headers}",
                f"Request body: {_body_preview(request.body, request_content_type)}",
                f"Response status: {response.status_code}",
                f"Response headers: {response_headers}",
                f"Response body: {_body_preview(response.text, response_content_type)}",
            ]
        )

    def close(self) -> None:
        """Release connections owned by the underlying session."""
        self.session.close()

