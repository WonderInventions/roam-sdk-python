"""The Roam-Version request header.

Pins x-fern-global-headers in fern/apis/roam/overrides.yml and the matching
headers: block in fern/apis/roam/generators.yml (developer-ro-am).

Two halves matter, and the second is the easy one to lose. Sending the
header when the caller asks for a pin is obvious. Not sending it otherwise
is the subtle part: Roam falls back to the version stamped on the
credential when the header is absent, so a client that always sent
something — an empty string, or a baked-in default — would silently
override every integration's pin.
"""

from __future__ import annotations

from tests.conftest import TOKEN, FakeAPI, json_response

PINNED = "2026-07-23"
OTHER = "2026-01-15"

EMPTY = {"ok": True, "groups": [], "nextCursor": None}


def test_roam_version_absent_when_not_pinned(api: FakeAPI) -> None:
    api.handle("GET", "/v1/group.list", lambda _r: json_response(200, EMPTY))
    api.client().group.list()
    assert api.seen[0].headers.get("Roam-Version") in (None, "")


def test_roam_version_sent_when_set_on_client(api: FakeAPI) -> None:
    api.handle("GET", "/v1/group.list", lambda _r: json_response(200, EMPTY))
    api.client(roam_version=PINNED).group.list()
    assert api.seen[0].headers.get("Roam-Version") == PINNED


def test_roam_version_sent_when_set_on_request(api: FakeAPI) -> None:
    api.handle("GET", "/v1/group.list", lambda _r: json_response(200, EMPTY))
    api.client().group.list(
        request_options={"additional_headers": {"Roam-Version": PINNED}}
    )
    assert api.seen[0].headers.get("Roam-Version") == PINNED


def test_roam_version_per_request_overrides_client(api: FakeAPI) -> None:
    api.handle("GET", "/v1/group.list", lambda _r: json_response(200, EMPTY))
    api.client(roam_version=PINNED).group.list(
        request_options={"additional_headers": {"Roam-Version": OTHER}}
    )
    assert api.seen[0].headers.get("Roam-Version") == OTHER


def test_roam_version_client_pin_kept_when_not_overridden(api: FakeAPI) -> None:
    api.handle("GET", "/v1/group.list", lambda _r: json_response(200, EMPTY))
    c = api.client(roam_version=PINNED)
    c.group.list(request_options={"additional_headers": {"Roam-Version": OTHER}})
    c.group.list()
    assert api.seen[0].headers.get("Roam-Version") == OTHER
    assert api.seen[1].headers.get("Roam-Version") == PINNED


def test_roam_version_still_sends_bearer_auth(api: FakeAPI) -> None:
    api.handle("GET", "/v1/group.list", lambda _r: json_response(200, EMPTY))
    api.client(roam_version=PINNED).group.list()
    assert api.seen[0].headers.get("Authorization") == f"Bearer {TOKEN}"
