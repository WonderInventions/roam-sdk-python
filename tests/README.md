# Contract tests

Hand-written tests that pin generated client behavior. HTTP is faked with
`httpx.MockTransport` against `https://api.ro.am/v1`. An unhandled request
fails the test rather than hitting the network.

| File | What it pins |
| --- | --- |
| `webhook_verify_test.py` | Hand-written Standard Webhooks verifier (`whsec_` HMAC). |
| `pagination_test.py` | `cursor` query param and `nextCursor` → `next_cursor` on `/group.list`. |
| `version_header_test.py` | `Roam-Version` absent by default, sent when pinned. |
| `retry_test.py` | 429 retried, `Retry-After` honored, 400 not retried. |

Python list methods return the response body (no auto-pager on this Fern
plan). Callers pass `cursor=` from `next_cursor` themselves.
