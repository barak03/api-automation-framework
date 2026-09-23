"""Local checks for transport defaults and safe diagnostics."""

from unittest.mock import Mock

import requests

from api.client import ApiClient


def test_request_uses_configured_base_url_and_timeout() -> None:
    session = Mock(spec=requests.Session)
    session.request.return_value = requests.Response()
    client = ApiClient("https://example.test/", timeout=4.5, session=session)

    client.request("GET", "/ping")

    session.request.assert_called_once_with(
        method="GET",
        url="https://example.test/ping",
        timeout=4.5,
    )


def test_diagnostics_mask_credentials_in_4xx_exchange() -> None:
    request = requests.Request(
        "POST",
        "https://example.test/auth?token=query-secret",
        headers={
            "Authorization": "Bearer header-secret",
            "Cookie": "token=cookie-secret",
            "Content-Type": "application/json",
        },
        json={"username": "admin", "password": "body-secret"},
    ).prepare()
    response = requests.Response()
    response.status_code = 403
    response.headers["Content-Type"] = "application/json"
    response.headers["Set-Cookie"] = "token=response-cookie-secret"
    response._content = b'{"token": "response-secret", "reason": "denied"}'
    response.request = request

    diagnostic = ApiClient("https://example.test", timeout=1).format_exchange(response)

    assert "***MASKED***" in diagnostic
    for secret in (
        "query-secret",
        "header-secret",
        "cookie-secret",
        "body-secret",
        "response-cookie-secret",
        "response-secret",
    ):
        assert secret not in diagnostic
    assert "Response status: 403" in diagnostic

