"""Independent booking CRUD and negative contract tests."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from api.booking_api import BookingApi
from api.client import ApiClient

pytestmark = [pytest.mark.external, pytest.mark.regression]


def _assert_status(response, expected: int, api_client: ApiClient) -> None:
    assert response.status_code == expected, api_client.format_exchange(response)


@pytest.mark.smoke
def test_create_booking_returns_id_and_submitted_data(
    owned_booking: dict[str, Any],
) -> None:
    body = owned_booking["response"].json()

    assert body["bookingid"] == owned_booking["id"]
    assert body["booking"] == owned_booking["payload"]


def test_get_owned_booking_returns_submitted_data(
    owned_booking: dict[str, Any],
    booking_api: BookingApi,
    api_client: ApiClient,
) -> None:
    response = booking_api.get_booking(owned_booking["id"])

    _assert_status(response, 200, api_client)
    assert response.json() == owned_booking["payload"]


def test_filter_by_unique_lastname_includes_owned_booking(
    owned_booking: dict[str, Any],
    booking_api: BookingApi,
    api_client: ApiClient,
) -> None:
    response = booking_api.get_booking_ids(
        lastname=owned_booking["payload"]["lastname"]
    )

    _assert_status(response, 200, api_client)
    returned_ids = {item["bookingid"] for item in response.json()}
    assert owned_booking["id"] in returned_ids


def test_full_update_replaces_owned_booking(
    owned_booking: dict[str, Any],
    booking_api: BookingApi,
    api_client: ApiClient,
    auth_token: str,
) -> None:
    updated_payload = deepcopy(owned_booking["payload"])
    updated_payload.update(firstname="Updated", totalprice=225, depositpaid=False)

    response = booking_api.update_booking(
        owned_booking["id"], updated_payload, auth_token
    )

    _assert_status(response, 200, api_client)
    assert response.json() == updated_payload
    stored = booking_api.get_booking(owned_booking["id"])
    _assert_status(stored, 200, api_client)
    assert stored.json() == updated_payload


def test_partial_update_changes_only_requested_fields(
    owned_booking: dict[str, Any],
    booking_api: BookingApi,
    api_client: ApiClient,
    auth_token: str,
) -> None:
    changes = {"firstname": "Patched", "depositpaid": False}

    response = booking_api.partial_update_booking(
        owned_booking["id"], changes, auth_token
    )

    _assert_status(response, 200, api_client)
    expected = {**owned_booking["payload"], **changes}
    assert response.json() == expected

    stored = booking_api.get_booking(owned_booking["id"])
    _assert_status(stored, 200, api_client)
    stored_body = stored.json()
    assert stored_body["firstname"] == changes["firstname"]
    assert stored_body["depositpaid"] == changes["depositpaid"]
    unchanged_fields = set(owned_booking["payload"]) - set(changes)
    for field in unchanged_fields:
        assert stored_body[field] == owned_booking["payload"][field]


def test_update_without_authentication_is_forbidden(
    owned_booking: dict[str, Any],
    booking_api: BookingApi,
    api_client: ApiClient,
) -> None:
    response = booking_api.update_booking(
        owned_booking["id"], owned_booking["payload"]
    )

    _assert_status(response, 403, api_client)


def test_delete_without_authentication_is_forbidden(
    owned_booking: dict[str, Any],
    booking_api: BookingApi,
    api_client: ApiClient,
) -> None:
    response = booking_api.delete_booking(owned_booking["id"])

    _assert_status(response, 403, api_client)


def test_delete_owned_booking_makes_it_unavailable(
    owned_booking: dict[str, Any],
    booking_api: BookingApi,
    api_client: ApiClient,
    auth_token: str,
) -> None:
    response = booking_api.delete_booking(owned_booking["id"], auth_token)

    _assert_status(response, 201, api_client)
    retrieval = booking_api.get_booking(owned_booking["id"])
    _assert_status(retrieval, 404, api_client)


def test_unknown_booking_returns_not_found(
    booking_api: BookingApi,
    api_client: ApiClient,
) -> None:
    response = booking_api.get_booking(2_147_483_647)

    _assert_status(response, 404, api_client)

