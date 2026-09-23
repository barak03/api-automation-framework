"""Shared pytest configuration and owned-record lifecycle fixtures."""

from __future__ import annotations

import os
from collections.abc import Callable, Iterator
from typing import Any
from uuid import uuid4

import pytest
import requests

from api.booking_api import BookingApi
from api.client import ApiClient


DEFAULT_BASE_URL = "https://restful-booker.herokuapp.com"
DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "password123"
BookingFactory = Callable[[dict[str, Any]], tuple[int, requests.Response]]


def _request_timeout() -> float:
    raw_value = os.getenv("API_REQUEST_TIMEOUT", str(DEFAULT_TIMEOUT_SECONDS))
    try:
        timeout = float(raw_value)
    except ValueError as error:
        raise pytest.UsageError("API_REQUEST_TIMEOUT must be a number") from error

    if timeout <= 0:
        raise pytest.UsageError("API_REQUEST_TIMEOUT must be greater than zero")
    return timeout


def _assert_status(
    response: requests.Response,
    expected_status: int,
    client: ApiClient,
) -> None:
    assert response.status_code == expected_status, client.format_exchange(response)


@pytest.fixture(scope="session")
def api_client() -> Iterator[ApiClient]:
    client = ApiClient(
        base_url=os.getenv("API_BASE_URL", DEFAULT_BASE_URL),
        timeout=_request_timeout(),
    )
    yield client
    client.close()


@pytest.fixture(scope="session")
def booking_api(api_client: ApiClient) -> BookingApi:
    return BookingApi(api_client)


@pytest.fixture
def booking_payload() -> dict[str, Any]:
    unique_suffix = uuid4().hex[:12]
    return {
        "firstname": "Portfolio",
        "lastname": f"Test-{unique_suffix}",
        "totalprice": 175,
        "depositpaid": True,
        "bookingdates": {
            "checkin": "2030-04-10",
            "checkout": "2030-04-14",
        },
        "additionalneeds": "Breakfast",
    }


@pytest.fixture
def auth_token(booking_api: BookingApi, api_client: ApiClient) -> str:
    response = booking_api.authenticate(
        username=os.getenv("API_USERNAME", DEFAULT_USERNAME),
        password=os.getenv("API_PASSWORD", DEFAULT_PASSWORD),
    )
    _assert_status(response, 200, api_client)
    body = response.json()
    token = body.get("token")
    assert isinstance(token, str) and token, "Expected authentication to return a token"
    return token


@pytest.fixture
def booking_factory(
    booking_api: BookingApi,
    api_client: ApiClient,
    auth_token: str,
) -> Iterator[BookingFactory]:
    owned_bookings: dict[int, str] = {}

    def create(payload: dict[str, Any]) -> tuple[int, requests.Response]:
        response = booking_api.create_booking(payload)
        _assert_status(response, 200, api_client)
        body = response.json()
        booking_id = body.get("bookingid")
        assert isinstance(booking_id, int), "Create response did not contain a numeric bookingid"
        assert body.get("booking") == payload, "Create response did not echo the submitted booking"
        owned_bookings[booking_id] = str(payload["lastname"])
        return booking_id, response

    yield create

    # Confirm the unique marker before deleting so a service reset cannot make
    # cleanup remove a different user's record that reused the same numeric ID.
    for booking_id, expected_lastname in reversed(owned_bookings.items()):
        try:
            response = booking_api.get_booking(booking_id)
            if response.status_code != 200:
                continue
            if response.json().get("lastname") != expected_lastname:
                continue
            booking_api.delete_booking(booking_id, auth_token)
        except (requests.RequestException, ValueError):
            # Cleanup is best-effort and must not hide the original test result.
            continue


@pytest.fixture
def owned_booking(
    booking_factory: BookingFactory,
    booking_payload: dict[str, Any],
) -> dict[str, Any]:
    booking_id, response = booking_factory(booking_payload)
    return {"id": booking_id, "payload": booking_payload, "response": response}


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[Any]):
    outcome = yield
    report = outcome.get_result()
    if report.failed:
        client = item.funcargs.get("api_client")
        if isinstance(client, ApiClient):
            report.sections.append(
                ("last HTTP exchange (sanitized)", client.format_exchange())
            )

