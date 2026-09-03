"""429 handling and Retry-After.

Pins the rate-limit modeling in fern/apis/roam/overlays.yml
(developer-ro-am), which attaches a documented 429 response with a
Retry-After header to every operation.

The contract in docs/guides/sdks.md is specific: a 429 is retried, not
thrown, and the wait comes from Retry-After rather than from the client's
own backoff guess. Those are two separate claims, so this suite checks
the delay value and not just the retry count — exponential backoff would
also produce a second request.

Timers are real. Fern's Python retrier applies no jitter on the
Retry-After path, so Retry-After: 2 is a two-second sleep. Default
exponential backoff for the first retry is ~1s, so 2s is what separates
"honored the server" from "guessed and got lucky".
"""

from __future__ import annotations

import time

import httpx
import pytest

from roamhq.errors import BadRequestError, TooManyRequestsError
from tests.conftest import FakeAPI, json_response

RATELIMITED = {"ok": False, "error": "ratelimited"}
OK_ONE_GROUP = {
    "ok": True,
    "groups": [{"id": "g1", "name": "Engineering", "type": "standard"}],
    "nextCursor": None,
}


def always_429(counter: list[int]) -> object:
    def handle(_request: httpx.Request) -> httpx.Response:
        counter[0] += 1
        return json_response(429, RATELIMITED, {"Retry-After": "2"})

    return handle


def test_retry_after_honors_header_exactly(api: FakeAPI) -> None:
    attempts = [0]

    def handle(_request: httpx.Request) -> httpx.Response:
        attempts[0] += 1
        if attempts[0] == 1:
            return json_response(429, RATELIMITED, {"Retry-After": "2"})
        return json_response(200, OK_ONE_GROUP)

    api.handle("GET", "/v1/group.list", handle)
    start = time.monotonic()
    page = api.client().group.list()
    elapsed = time.monotonic() - start
    assert attempts[0] == 2
    assert [g.id for g in page.groups] == ["g1"]
    assert 2.0 <= elapsed < 3.0, f"elapsed = {elapsed}s, want ~2s from Retry-After"


def test_retry_exhaustion_throws_too_many_requests(api: FakeAPI) -> None:
    n = [0]
    api.handle("GET", "/v1/group.list", always_429(n))
    with pytest.raises(TooManyRequestsError) as exc:
        api.client().group.list()
    # Default max_retries=2 is a cap on retries, not total HTTP calls:
    # attempt 0 plus two retries = 3 requests.
    assert n[0] == 3
    assert exc.value.status_code == 429


def test_max_retries_zero_does_not_retry(api: FakeAPI) -> None:
    n = [0]
    api.handle("GET", "/v1/group.list", always_429(n))
    with pytest.raises(TooManyRequestsError):
        api.client().group.list(request_options={"max_retries": 0})
    assert n[0] == 1


def test_retry_surfaces_parsed_error_envelope(api: FakeAPI) -> None:
    n = [0]
    api.handle("GET", "/v1/group.list", always_429(n))
    with pytest.raises(TooManyRequestsError) as exc:
        api.client().group.list(request_options={"max_retries": 0})
    assert exc.value.status_code == 429
    assert exc.value.body is not None
    assert exc.value.body.error == "ratelimited"


def test_does_not_retry_400(api: FakeAPI) -> None:
    n = [0]

    def handle(_request: httpx.Request) -> httpx.Response:
        n[0] += 1
        return json_response(400, {"ok": False, "error": "invalid_arguments"})

    api.handle("GET", "/v1/group.list", handle)
    with pytest.raises(BadRequestError):
        api.client().group.list()
    assert n[0] == 1
