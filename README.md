# API Test Automation Framework

A small personal portfolio project demonstrating a maintainable Python API test
framework against the public
[Restful Booker](https://restful-booker.herokuapp.com/) service. The deliverable
is the automation framework, not a backend application.

## Cost constraint

The project must remain free to develop and run. It uses local Python tooling,
open-source packages, and the free public Restful Booker sandbox. Do not add paid
APIs, SaaS test platforms, cloud resources, or subscriptions.

## Current status

The Phase 2 core suite is implemented locally:

- 13 external API tests covering health, authentication, isolated booking CRUD,
  negative authorization behavior, filtering, and one full lifecycle.
- 2 local client tests covering explicit timeouts and sanitized diagnostics.
- Function-scoped owned-booking data with guarded, best-effort cleanup.
- Environment-configurable base URL, timeout, and demo credentials.

Phase 3 CI has not been added. Local stability was established first, as required
by the project roadmap.

## Requirements and setup

- Python 3.11 or newer
- Network access to `restful-booker.herokuapp.com`

Using `uv`:

```bash
uv sync --extra test
uv run python -m pytest
```

Using the standard library and pip:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[test]'
python -m pytest
```

No real secrets belong in this repository. Restful Booker publishes its demo
credentials in its documentation; the framework masks them in failure diagnostics.

## Configuration

| Environment variable | Default | Purpose |
| --- | --- | --- |
| `API_BASE_URL` | `https://restful-booker.herokuapp.com` | System-under-test URL |
| `API_REQUEST_TIMEOUT` | `10` | Per-request timeout in seconds; must be positive |
| `API_USERNAME` | Restful Booker demo username | Override authentication username |
| `API_PASSWORD` | Restful Booker demo password | Override authentication password |

Example:

```bash
API_REQUEST_TIMEOUT=15 uv run python -m pytest
```

## Architecture

- `api/client.py` owns URL construction, the shared HTTP session, explicit
  timeouts, and masked request/response diagnostics.
- `api/booking_api.py` provides small endpoint-level methods while returning the
  original `requests.Response` for transparent assertions.
- `tests/conftest.py` owns environment configuration, authentication, unique test
  data, owned-record creation/cleanup, and failure-report integration.
- `tests/test_auth.py` covers valid and invalid authentication.
- `tests/test_booking_crud.py` covers isolated CRUD, filtering, missing records,
  and unauthenticated mutations.
- `tests/test_booking_lifecycle.py` covers create -> retrieve -> update -> delete.
- `tests/test_client.py` verifies transport defaults and secret masking without
  making network calls.

This deliberately avoids a base-test hierarchy, automatic retries, and extra
dependencies. `requests` provides HTTP transport; `pytest` provides fixtures,
discovery, assertions, and reports.

## Isolation and cleanup

Every mutation test creates a booking with a unique lastname and uses only the ID
returned by that request. Teardown retrieves the record and checks that unique
marker before deleting it. This guard prevents a periodic service reset from
causing cleanup to delete another user's record that reused the same numeric ID.

Cleanup is best-effort. Network errors or already-deleted records do not replace or
hide the original test result. The framework has no blanket retries.

## Failure diagnostics

When a pytest test fails, the most recent HTTP exchange is attached to its report.
The diagnostic masks authorization, cookies, passwords, tokens, API keys, and
`Set-Cookie` values and limits body previews to 1,000 characters.

## Verified API contract

Checked on 2026-09-23 against the deployed API, its published documentation, and
the upstream `mwinteringham/restful-booker` route implementation.

| Operation | Expected behavior used by the suite |
| --- | --- |
| `GET /ping` | `201`, not the more usual `200` |
| `GET /booking` | `200` with booking-ID objects; supports filters |
| `GET /booking/{id}` | `200` when present and `404` when absent |
| `POST /booking` | `200` with `bookingid` and the submitted booking |
| `POST /auth` | `200` with a token for valid credentials; invalid credentials also return `200` with `Bad credentials` |
| `PUT/PATCH /booking/{id}` | `200` when authorized; `403` without authorization |
| `DELETE /booking/{id}` | `201` when authorized; `403` without authorization |

These expectations intentionally follow this API's behavior rather than generic
REST conventions.

## Latest verification

On 2026-09-23, the complete 15-test suite passed three consecutive runs:

```text
15 passed in 8.47s
15 passed in 8.25s
15 passed in 8.14s
```

Reproduce with:

```bash
uv run python -m pytest -q
```

## Known limitations

- This is a shared public sandbox with periodic resets and intentionally unusual
  behavior. An outage or reset can fail the external tests even when the framework
  is correct.
- Test data and authentication tokens are ephemeral and must not be reused between
  runs.
- The current suite is JSON-only and runs sequentially; parallel safety has not
  been claimed or tested.
- There is no CI workflow or generated HTML report yet.

