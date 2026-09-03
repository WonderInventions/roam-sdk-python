"""HTTP is faked at httpx.MockTransport against https://api.ro.am/v1.

An unhandled request fails the test rather than hitting the network —
same idea as msw's onUnhandledRequest: "error".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional
from urllib.parse import urlparse

import httpx
import pytest

from roamhq import RoamClient

BASE_HOST = "api.ro.am"
BASE_PATH_PREFIX = "/v1"
TOKEN = "rmk-test-token"


@dataclass
class SeenReq:
    method: str
    path: str
    params: dict[str, str]
    headers: httpx.Headers


Handler = Callable[[httpx.Request], httpx.Response]


@dataclass
class FakeAPI:
    """Intercepts at httpx.Client so URL construction, auth, and retries run."""

    seen: list[SeenReq] = field(default_factory=list)
    _handlers: dict[str, Handler] = field(default_factory=dict)

    def handle(self, method: str, path: str, handler: Handler) -> None:
        self._handlers[f"{method.upper()} {path}"] = handler

    def _handler(self, request: httpx.Request) -> httpx.Response:
        parsed = urlparse(str(request.url))
        if parsed.scheme != "https" or parsed.hostname != BASE_HOST:
            pytest.fail(f"unhandled request (wrong host): {request.url}")
        path = parsed.path
        key = f"{request.method.upper()} {path}"
        handler = self._handlers.get(key)
        if handler is None:
            pytest.fail(f"unhandled request: {request.method} {request.url}")
        params = dict(request.url.params)
        self.seen.append(
            SeenReq(
                method=request.method.upper(),
                path=path,
                params=params,
                headers=request.headers,
            )
        )
        return handler(request)

    def client(self, **kwargs: object) -> RoamClient:
        transport = httpx.MockTransport(self._handler)
        httpx_client = httpx.Client(transport=transport)
        return RoamClient(
            token=TOKEN,
            httpx_client=httpx_client,
            **kwargs,  # type: ignore[arg-type]
        )


def json_response(
    status: int,
    body: object,
    headers: Optional[dict[str, str]] = None,
) -> httpx.Response:
    hdrs = {"content-type": "application/json"}
    if headers:
        hdrs.update(headers)
    return httpx.Response(status, json=body, headers=hdrs)


@pytest.fixture
def api() -> FakeAPI:
    return FakeAPI()
