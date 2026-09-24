# API Test Automation Framework

A focused Python/pytest test framework for the public
[Restful Booker](https://restful-booker.herokuapp.com/) API. It is a personal
Software Automation Engineer portfolio project that demonstrates maintainable API
test design without hiding HTTP behavior behind a large abstraction layer.

## What the framework demonstrates

- A thin HTTP client with configurable timeouts and a shared session
- Endpoint-focused API helpers that return the original `requests.Response`
- Independent test data with unique identifiers and guarded, best-effort cleanup
- Positive, negative, CRUD, and end-to-end lifecycle coverage
- Sanitized request/response diagnostics on test failures
- Selective execution with smoke, regression, and external-test markers
- Separate CI signals for local framework quality and public-service tests

## Technologies

- Python 3.11+
- pytest
- requests
- Ruff
- GitHub Actions

## Project structure

```text
api-automation-framework/
├── .github/workflows/tests.yml  # local-quality and external API CI jobs
├── api/
│   ├── client.py                # HTTP transport and sanitized diagnostics
│   └── booking_api.py           # Restful Booker endpoint helpers
├── tests/
│   ├── conftest.py              # configuration, fixtures, cleanup, diagnostics
│   ├── test_auth.py
│   ├── test_booking_crud.py
│   ├── test_booking_lifecycle.py
│   ├── test_client.py           # local unit tests; no network required
│   └── test_health.py
├── pyproject.toml
├── uv.lock
└── README.md
```

## Test coverage

The external suite covers service health, valid and invalid authentication,
booking creation and retrieval, filtering, full and partial updates,
authorization failures, deletion, unknown IDs, and an owned-booking lifecycle.

Mutation tests create their own booking with a unique lastname and use only the ID
returned by the service. Cleanup confirms that unique marker before deleting, so a
public-service reset cannot cause the framework to delete another user's record.
The local client tests cover URL and timeout defaults, diagnostic-state reset, and
secret masking without making network requests.

## Setup

Python 3.11 or newer is required.

Using `uv`:

```bash
uv sync --extra test
```

Using `venv` and pip:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[test]'
```

## Running tests

Run lint and the complete suite:

```bash
uv run ruff check .
uv run python -m pytest
```

With an activated pip environment, omit the `uv run` prefix.

## Pytest markers

```bash
uv run python -m pytest -m smoke
uv run python -m pytest -m regression
uv run python -m pytest -m "not external"
uv run python -m pytest -m external
```

`external` identifies every test that communicates with Restful Booker. The
`not external` selection runs only deterministic local client tests.

## Failure diagnostics

The session-scoped client retains the latest HTTP response only for the current
test. An autouse fixture clears that state before every test, preventing a failure
before its first request from reporting a previous test's exchange.

When a test fails, pytest adds the latest request and response to the report.
Authorization headers, cookies, passwords, tokens, API keys, and `Set-Cookie`
values are masked, and body previews are limited to 1,000 characters.

## CI/CD

GitHub Actions runs on pushes and pull requests with Python 3.12. The workflow has
two clearly named jobs:

- **Local tests and lint** runs Ruff and `pytest -m "not external"`.
- **Restful Booker external tests** runs `pytest -m external` separately.

This separation makes local framework failures distinguishable from failures
caused by the public service or network.

## Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `API_BASE_URL` | `https://restful-booker.herokuapp.com` | System-under-test URL |
| `API_REQUEST_TIMEOUT` | `10` | Positive per-request timeout in seconds |
| `API_USERNAME` | Restful Booker demo username | Authentication username |
| `API_PASSWORD` | Restful Booker demo password | Authentication password |

The defaults are the API's published demo credentials, not private secrets. Use
environment variables for overrides and never commit a local `.env` file.

Example:

```bash
API_REQUEST_TIMEOUT=15 uv run python -m pytest -m external
```

## Limitations

Restful Booker is a shared public sandbox that can be unavailable, respond slowly,
or reset data while tests are running. Those conditions can fail the external
suite even when the local framework is healthy. Cleanup is deliberately
best-effort, the suite runs sequentially, and the framework currently targets the
service's JSON booking API only.
