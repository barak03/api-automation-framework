"""Authentication contract tests."""

import pytest

from api.booking_api import BookingApi
from api.client import ApiClient

pytestmark = pytest.mark.external


@pytest.mark.smoke
def test_valid_credentials_return_token(
    booking_api: BookingApi,
    api_client: ApiClient,
    api_credentials: tuple[str, str],
) -> None:
    username, password = api_credentials
    response = booking_api.authenticate(username, password)

    assert response.status_code == 200, api_client.format_exchange(response)
    token = response.json().get("token")
    assert isinstance(token, str) and token, "Expected a non-empty authentication token"


@pytest.mark.regression
def test_invalid_credentials_return_documented_reason(
    booking_api: BookingApi,
    api_client: ApiClient,
) -> None:
    response = booking_api.authenticate("invalid-user", "invalid-password")

    assert response.status_code == 200, api_client.format_exchange(response)
    assert response.json() == {"reason": "Bad credentials"}

