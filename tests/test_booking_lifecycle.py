"""End-to-end lifecycle coverage for one owned booking."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from api.booking_api import BookingApi
from api.client import ApiClient


def test_owned_booking_lifecycle(
    booking_factory,
    booking_payload: dict[str, Any],
    booking_api: BookingApi,
    api_client: ApiClient,
    auth_token: str,
) -> None:
    booking_id, _ = booking_factory(booking_payload)

    retrieved = booking_api.get_booking(booking_id)
    assert retrieved.status_code == 200, api_client.format_exchange(retrieved)
    assert retrieved.json() == booking_payload

    updated_payload = deepcopy(booking_payload)
    updated_payload.update(firstname="Lifecycle", totalprice=300)
    updated = booking_api.update_booking(booking_id, updated_payload, auth_token)
    assert updated.status_code == 200, api_client.format_exchange(updated)
    assert updated.json() == updated_payload

    deleted = booking_api.delete_booking(booking_id, auth_token)
    assert deleted.status_code == 201, api_client.format_exchange(deleted)

    missing = booking_api.get_booking(booking_id)
    assert missing.status_code == 404, api_client.format_exchange(missing)

