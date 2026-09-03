"""Cursor pagination as a consumer of roamhq.

Pins the x-fern-pagination modeling in fern/apis/roam/overrides.yml
(developer-ro-am). The spec says `cursor` goes in on the request, the server
hands back `nextCursor`, and the items live under a named array — for
/group.list that array is `groups`.

Fern's Python generator on this plan does not emit an auto-pager (SyncPager
exists in core/ but list methods return the response body). Callers paginate
by passing `cursor=` from `next_cursor`. If those three names drift, the
generated client silently stops paginating: page one looks complete.
"""

from __future__ import annotations

import httpx

from tests.conftest import FakeAPI, json_response

PAGE_1 = {
    "ok": True,
    "groups": [
        {"id": "g1", "name": "Engineering", "type": "standard"},
        {"id": "g2", "name": "Design", "type": "standard"},
    ],
    "nextCursor": "cursor-page-2",
}
PAGE_2 = {
    "ok": True,
    "groups": [
        {"id": "g3", "name": "Support", "type": "standard"},
    ],
    "nextCursor": None,
}


def _cursor(request: httpx.Request) -> str | None:
    return request.url.params.get("cursor")


def test_cursor_query_absent_on_first_page(api: FakeAPI) -> None:
    api.handle("GET", "/v1/group.list", lambda _r: json_response(200, PAGE_1))
    page = api.client().group.list()
    assert [g.id for g in page.groups] == ["g1", "g2"]
    assert page.next_cursor == "cursor-page-2"
    assert "cursor" not in api.seen[0].params


def test_cursor_from_next_cursor_fetches_second_page(api: FakeAPI) -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        cursor = _cursor(request)
        if cursor is None:
            return json_response(200, PAGE_1)
        if cursor == "cursor-page-2":
            return json_response(200, PAGE_2)
        raise AssertionError(f"unexpected cursor: {cursor!r}")

    api.handle("GET", "/v1/group.list", handle)
    c = api.client()
    page = c.group.list()
    assert [g.name for g in page.groups] == ["Engineering", "Design"]
    assert page.next_cursor == "cursor-page-2"

    page = c.group.list(cursor=page.next_cursor)
    assert [g.id for g in page.groups] == ["g3"]
    assert page.next_cursor is None

    assert len(api.seen) == 2
    assert "cursor" not in api.seen[0].params
    assert api.seen[1].params.get("cursor") == "cursor-page-2"


def test_limit_is_forwarded_as_query(api: FakeAPI) -> None:
    api.handle("GET", "/v1/group.list", lambda _r: json_response(200, PAGE_1))
    api.client().group.list(limit=2)
    assert api.seen[0].params.get("limit") == "2"
