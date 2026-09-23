"""Small availability check for the system under test."""

from api.booking_api import BookingApi


def test_ping_confirms_api_is_available(booking_api: BookingApi) -> None:
    response = booking_api.health_check()

    assert response.status_code == 201, (
        "Expected Restful Booker GET /ping to return its documented 201 status, "
        f"but received {response.status_code}. Response body: {response.text[:300]!r}"
    )

