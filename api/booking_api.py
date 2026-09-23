"""Endpoint-level helpers for Restful Booker."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import requests

from api.client import ApiClient


class BookingApi:
    """Expose domain operations without hiding HTTP responses from tests."""

    def __init__(self, client: ApiClient) -> None:
        self.client = client

    def health_check(self) -> requests.Response:
        return self.client.request("GET", "/ping")

    def authenticate(self, username: str, password: str) -> requests.Response:
        return self.client.request(
            "POST",
            "/auth",
            headers={"Accept": "application/json"},
            json={"username": username, "password": password},
        )

    def create_booking(self, payload: Mapping[str, Any]) -> requests.Response:
        return self.client.request(
            "POST",
            "/booking",
            headers={"Accept": "application/json"},
            json=payload,
        )

    def get_booking(self, booking_id: int) -> requests.Response:
        return self.client.request(
            "GET",
            f"/booking/{booking_id}",
            headers={"Accept": "application/json"},
        )

    def get_booking_ids(self, **filters: str) -> requests.Response:
        return self.client.request(
            "GET",
            "/booking",
            headers={"Accept": "application/json"},
            params=filters,
        )

    def update_booking(
        self,
        booking_id: int,
        payload: Mapping[str, Any],
        token: str | None = None,
    ) -> requests.Response:
        return self.client.request(
            "PUT",
            f"/booking/{booking_id}",
            headers=self._headers(token),
            json=payload,
        )

    def partial_update_booking(
        self,
        booking_id: int,
        payload: Mapping[str, Any],
        token: str | None = None,
    ) -> requests.Response:
        return self.client.request(
            "PATCH",
            f"/booking/{booking_id}",
            headers=self._headers(token),
            json=payload,
        )

    def delete_booking(
        self,
        booking_id: int,
        token: str | None = None,
    ) -> requests.Response:
        return self.client.request(
            "DELETE",
            f"/booking/{booking_id}",
            headers=self._headers(token),
        )

    @staticmethod
    def _headers(token: str | None) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if token is not None:
            headers["Cookie"] = f"token={token}"
        return headers

